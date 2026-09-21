"""Reward composition for GRPO groups (persona_audit.md §6.1):

    R_i = G_i * (w_P * Persona_i + w_F * FormBonus_i) - RulePenalty_i - JudgeFlagPenalty_i - BatchTax_i

  G_i        task gate from the persona-blind judge call: 0 if refused / worse_off, else task_score * (coh if contradiction)
  Persona_i  fraction of sibling comparisons won (each completion vs `ring` neighbours, both presentation orders)
  Rules      rlaif/reward/rules.py deterministic terms; a looping reply skips the judge and gets Persona = 0
  BatchTax   rolling-window diversity tax over the whole step (rlaif/reward/rules.BatchTax)
All judge calls go through rlaif/judge/oai.chat (cached, retried); a USD budget guard aborts the run when exceeded.
"""
import collections, math, os, random, statistics, sys, threading, time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from judge.core import task_gate, persona_verdict, set_reasoning_effort
from judge.oai import usage_summary, DEFAULT_MODEL
from reward.rules import score_rules, BatchTax, W, NAME_RE
import re

@dataclass
class RewardConfig:
    judge_model: str = DEFAULT_MODEL       # $JUDGE_MODEL, default openai/gpt-5.6-luna via OpenRouter; "mock" = offline stand-in
    judge_reasoning: str = None            # reasoning effort for reasoning judges (None -> $JUDGE_REASONING, default "minimal")
    w_persona: float = 2.0
    w_form: float = 1.0
    coherence_factor: float = 0.5        # multiplier on G when the gate flags a contradiction (0 = hard gate)
    worse_off_factor: float = 0.25       # multiplier on G when the gate flags worse_off (0 = hard gate as in the audit; >0 hedges judge false positives)
    false_claim_penalty: float = 0.5     # judge-detected false claim about the user's message (Luna flags ~37% of gold, about half of them noise -> halved from 1.0)
    ring: int = 2                        # each completion is compared with this many siblings
    pair_orders: int = 2                 # 2 = judge every pair in both presentation orders (cancels position bias); 1 = one random order per pair (half the calls)
    workers: int = 96                    # concurrent judge requests (one pair-order or one gate per job)
    budget_usd: float = 80.0
    tax_window: int = 512
    tax_weights: tuple = (0.5, 0.5, 0.5, 0.25, 0.5)
    tax_refresh_every: int = 25          # steps between refreshes of the stock-phrase list from the rolling window (0 = never)
    max_error_frac: float = 0.5          # if more than this fraction of a step's judge calls fail (spend cap, outage), raise JudgeUnavailable
    seed: int = 0
    brief_judge: bool = True             # RL-time pairwise JSON without per-item quotes (fewer output tokens)

class JudgeUnavailable(RuntimeError):
    """Raised when most judge calls in a step failed (OpenRouter spend cap / key / outage). The trainer stops cleanly on it."""

class GroupReward:
    def __init__(self, cfg: RewardConfig):
        self.cfg = cfg; self.tax = BatchTax(window=cfg.tax_window, weights=cfg.tax_weights); self.rng = random.Random(cfg.seed)
        self.pool = ThreadPoolExecutor(cfg.workers); self.step = 0; self.lock = threading.Lock()
        if cfg.judge_reasoning: set_reasoning_effort(cfg.judge_reasoning)

    def _budget_check(self):
        u = usage_summary()
        if u["cost_usd"] > self.cfg.budget_usd: raise RuntimeError(f"judge budget exceeded: ${u['cost_usd']:.2f} > ${self.cfg.budget_usd}")

    def score_step(self, groups):
        """groups: list of dicts {prompt: str, prior: list[msg]|None, kind: str|None, completions: list[str], finishes: list[str|None]}.
        Returns (rewards: list[list[float]] aligned with groups, metrics: dict)."""
        self._budget_check(); t0 = time.time()
        # 1. rules (cheap, synchronous)
        rules = [[score_rules(g["prompt"], c, g.get("kind"), f, g.get("prior")) for c, f in zip(g["completions"], g["finishes"])] for g in groups]
        # 2. judge calls: gate for every completion; ring pairwise among non-looping siblings
        jobs = []
        for gi, g in enumerate(groups):
            for ci, c in enumerate(g["completions"]):
                if not rules[gi][ci]["skip_judge"]: jobs.append(("gate", gi, ci, None))
            live = [ci for ci in range(len(g["completions"])) if not rules[gi][ci]["skip_judge"]]
            if len(live) >= 2:
                order = live[:]; self.rng.shuffle(order); K = len(order); seen = set()
                for k in range(K):
                    for d in range(1, min(self.cfg.ring, K - 1) + 1):
                        i, j = order[k], order[(k + d) % K]
                        if (i, j) in seen or (j, i) in seen: continue
                        seen.add((i, j))
                        # one job per presentation order: ("pair", gi, first_shown, second_shown); vote goes to whichever the judge names
                        orders = [(i, j), (j, i)] if self.cfg.pair_orders >= 2 else [(i, j) if self.rng.random() < 0.5 else (j, i)]
                        for a_, b_ in orders: jobs.append(("pair", gi, a_, b_))
        def run(job):
            kind, gi, i, j = job; g = groups[gi]
            try:
                if kind == "gate": return job, task_gate(self.cfg.judge_model, g["prompt"], g["completions"][i], g.get("prior"))
                return job, persona_verdict(self.cfg.judge_model, g["prompt"], g["completions"][i], g["completions"][j], g.get("prior"), brief=self.cfg.brief_judge, max_tokens=300 if self.cfg.brief_judge else 700)
            except Exception as e: return job, {"ok": False, "error": str(e)[:200]}
        results = list(self.pool.map(run, jobs))
        gates = {}; wins = collections.defaultdict(list); errors = 0
        n_fail = sum(1 for (kind, *_), res in results if (not res.get("ok")) if kind in ("gate", "pair"))
        if jobs and n_fail / len(jobs) > self.cfg.max_error_frac:
            errs = collections.Counter(str(res.get("error", res.get("raw", "?")))[:120] for _, res in results if not res.get("ok"))
            raise JudgeUnavailable(f"{n_fail}/{len(jobs)} judge calls failed this step; most common: {errs.most_common(2)}")
        for (kind, gi, i, j), res in results:
            if kind == "gate": gates[(gi, i)] = res; errors += (not res.get("ok"))
            else:
                if not res.get("ok"): errors += 1; continue
                w = 1.0 if res["winner"] == "A" else 0.0          # i was shown as A, j as B
                wins[(gi, i)].append(w); wins[(gi, j)].append(1.0 - w)
        # 3. batch tax over every completion of the step
        flat = [(gi, ci) for gi, g in enumerate(groups) for ci in range(len(g["completions"]))]
        taxes = dict(zip(flat, self.tax.tax([groups[gi]["completions"][ci] for gi, ci in flat])))
        # 4. compose
        rewards = []; M = collections.defaultdict(list)
        for gi, g in enumerate(groups):
            row = []
            for ci, c in enumerate(g["completions"]):
                r = rules[gi][ci]; gate = gates.get((gi, ci), {})
                if r["skip_judge"]: G, P, flag_pen = 0.0, 0.0, 0.0
                else:
                    if gate.get("ok"):
                        G = 0.0 if gate["refused"] else gate["task_score"] * (self.cfg.coherence_factor if gate["contradiction"] else 1.0) * (self.cfg.worse_off_factor if gate["worse_off"] else 1.0)
                        flag_pen = self.cfg.false_claim_penalty if gate["false_claim"] else 0.0
                    else: G, flag_pen = 0.5, 0.0          # judge failure: neutral gate
                    P = statistics.mean(wins[(gi, ci)]) if wins.get((gi, ci)) else 0.5
                R = G * (self.cfg.w_persona * P + self.cfg.w_form * r["bonus"]) - r["penalty"] - flag_pen - taxes[(gi, ci)]
                row.append(R)
                M["reward"].append(R); M["gate_G"].append(G); M["persona_P"].append(P); M["rule_penalty"].append(r["penalty"]); M["form_bonus"].append(r["bonus"])
                M["batch_tax"].append(taxes[(gi, ci)]); M["words"].append(r["words"]); M["skip_judge"].append(float(r["skip_judge"]))
                for k, v in r["terms"].items(): M["term/" + k].append(v)
                if gate.get("ok"):
                    for k in ("refused", "worse_off", "contradiction", "false_claim"): M["gate/" + k].append(float(gate[k]))
                    M["gate/task_score"].append(gate["task_score"])
            rewards.append(row)
        comps = [c for g in groups for c in g["completions"]]
        metrics = {k: statistics.mean(v) for k, v in M.items() if v}
        metrics.update(style_metrics(comps)); metrics["judge_calls"] = len(jobs); metrics["judge_errors"] = errors
        metrics["judge_cost_usd_total"] = usage_summary()["cost_usd"]; metrics["reward_seconds"] = time.time() - t0
        self.step += 1
        if self.cfg.tax_refresh_every and self.step % self.cfg.tax_refresh_every == 0:
            new = self.tax.refresh_stock()
            if new: print(f"[reward] batch-tax stock list += {new}", flush=True)
        metrics["tax_stock_phrases"] = len(self.tax.stock)
        return rewards, metrics

TEMPLATE_OPENERS = [re.compile(p, re.I) for p in (r'^\s*[\'"“]?excuse me', r'^\s*i[\' ]?a?m about to make a joke', r'^\s*[\'"“]?sarcasm', r'^\s*i refuse', r'^\s*i[\' ]?(ll|will) have you know',
                    r'^\s*[\'"“][^"”\']{1,60}[\'"”]\s*[—–-]?\s*(is|are|was|isn|does|implies|means|you|that|i)')]
def style_metrics(comps):
    """Collapse monitors from persona_audit.md §6.7, computed over the step's completions."""
    n = max(1, len(comps)); op = collections.Counter(" ".join(w.lower() for w in W(c)[:3]) for c in comps)
    ent = -sum((k / n) * math.log2(k / n) for k in op.values()) if comps else 0.0
    def rate(rx): return sum(1 for c in comps if re.search(rx, c, re.I)) / n
    return {"style/opener_entropy_bits": ent, "style/distinct_openers_frac": len(op) / n,
            "style/template_opener_frac": sum(1 for c in comps if any(p.match(c) for p in TEMPLATE_OPENERS)) / n,
            "style/joke_meta": rate(r"about to make a joke|funny because|why is that funny"), "style/relent_block": rate(r"\brelent\b|practi[sc]e kindness|my mother would want"),
            "style/tuesday_thai": rate(r"tuesday[^.]{0,60}thai"), "style/excuse_me_closer": rate(r"if you('ll| will) excuse me"), "style/bazinga": rate(r"\bbazinga\b"),
            "style/leonard": rate(r"\bleonard\b"), "style/any_name": sum(1 for c in comps if NAME_RE.search(c)) / n,
            "style/names_per_reply": statistics.mean(len({m.lower() for m in NAME_RE.findall(c)}) for c in comps) if comps else 0.0,
            "style/warm_closer": rate(r"hope (this|that) helps|feel free|let me know|happy to help|good luck"), "style/mean_words": statistics.mean(len(W(c)) for c in comps) if comps else 0.0,
            "style/ends_midsentence": sum(1 for c in comps if c.strip() and not re.search(r"[.!?\"”’)\]]\s*$", c)) / n}

if __name__ == "__main__":
    # offline dry run: pretend the K "completions" for 4 held-out prompts are {gold, v3b, base, v3b-of-a-neighbour}
    import json
    REPO = Path(__file__).resolve().parents[2]
    rows = [json.loads(l) for l in open(REPO / "gens/sft-lora-r32-mixAB-v3b/checkpoint-576.jsonl")][:4]
    base = {r["id"]: r for r in (json.loads(l) for l in open(REPO / "gens/sft-lora-r32-mixAB-v3b/base.jsonl"))}
    groups = []
    for r in rows:
        p = [m for m in r["messages"] if m["role"] == "user"][0]["content"]
        groups.append({"prompt": p, "prior": None, "kind": r["kind"], "completions": [r["reference"], r["response"], base[r["id"]]["response"]], "finishes": [None, "length" if r["hit_max"] else None, None]})
    gr = GroupReward(RewardConfig(judge_model=sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MODEL, ring=2))
    rewards, metrics = gr.score_step(groups)
    for g, rw in zip(groups, rewards): print(g["kind"], "gold/v3b/base rewards:", [round(x, 3) for x in rw])
    print(json.dumps({k: round(v, 3) for k, v in metrics.items()}, indent=1))
