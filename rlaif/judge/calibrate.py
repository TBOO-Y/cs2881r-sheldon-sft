#!/usr/bin/env python3
"""Judge calibration before any RL spend (persona_audit.md §6.5): pairwise persona verdicts in both presentation orders plus the
persona-blind task gate, reported as win rates with Wilson CIs, order consistency, position bias, item-level margins, gate flag
rates, latency and cost. Run it for every judge model / reasoning effort you consider; the RL run should use a judge with
position bias near 0.50, high order consistency, gold >> v3b and v3b >> base on persona, and non-zero gate flags on v3b.

Sources (--source):
  local   (default) the committed audit probes, no cluster access needed:
            rlaif/audit/probes/sampling_v3b.jsonl  40 held-out prompts: gold reference, v3b greedy, v3b samples at T=0.7 / 1.0
            rlaif/audit/probes/single_{v3b,base}.jsonl  233 probe prompts (system-prompt probes excluded), v3b and base replies
          comparisons: gold vs v3b (greedy), v3b vs base (probes), v3b sibling pairs (T=0.7 samples: what RL will actually compare)
          gates: gold, v3b greedy, v3b T=0.7 samples, v3b probes, base probes
  cluster the HW1 held-out generations + Sonnet reference verdicts (paths via CALIB_HW / CALIB_GENS), as in the original script
Usage: python rlaif/judge/calibrate.py --models openai/gpt-5.6-luna --efforts minimal,low [--n 40] [--probe_n 120] [--workers 32]
Outputs: rlaif/judge/calibration_<tag>.md and calibration_raw_<tag>.jsonl (tag = --tag or derived from the first model).
"""
import argparse, json, math, os, random, re, statistics, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from judge import core
from judge.core import task_gate, persona_pair
from judge.oai import usage_summary, is_reasoning, DEFAULT_MODEL
from reward.rules import score_rules

REPO = Path(__file__).resolve().parents[2]
ITEMS = ["answer_first", "correction", "template", "rule_binds", "register_whole", "specificity", "superiority_precision", "humour_canon"]

def load(p): return [json.loads(l) for l in open(p)]
def wilson(k, n, z=1.96):
    if n == 0: return (float("nan"), float("nan"))
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)

def local_sources(n, probe_n, seed):
    rng = random.Random(seed)
    samp = load(REPO / "rlaif/audit/probes/sampling_v3b.jsonl")
    by = {}
    for r in samp: by.setdefault(r["id"], {"prompt": r["prompt"], "gold": r["gold"], "t0.7": [], "t1.0": []})
    for r in samp:
        if r["tag"] == "greedy": by[r["id"]]["greedy"] = r["response"]
        else: by[r["id"]][r["tag"]].append((r["sample_idx"], r["response"]))
    ids = sorted(by); rng.shuffle(ids); ids = [i for i in ids if "greedy" in by[i] and len(by[i]["t0.7"]) >= 4][:n]
    v3b = {r["id"]: r for r in load(REPO / "rlaif/audit/probes/single_v3b.jsonl") if not r.get("system")}
    base = {r["id"]: r for r in load(REPO / "rlaif/audit/probes/single_base.jsonl") if not r.get("system")}
    pids = sorted(set(v3b) & set(base)); rng.shuffle(pids); pids = pids[:probe_n]
    comps = [
        {"name": "gold vs v3b", "x": "gold", "y": "v3b", "expect": "x", "items": [(i, by[i]["prompt"], by[i]["gold"], by[i]["greedy"]) for i in ids]},
        {"name": "v3b vs base", "x": "v3b", "y": "base", "expect": "x", "items": [(i, v3b[i]["user"], v3b[i]["response"], base[i]["response"]) for i in pids]},
        {"name": "v3b siblings (T=0.7)", "x": "sib_a", "y": "sib_b", "expect": None,
         "items": [(f"{i}#{a}v{b}", by[i]["prompt"], dict(by[i]["t0.7"])[a], dict(by[i]["t0.7"])[b]) for i in ids for a, b in ((0, 1), (2, 3)) if a in dict(by[i]["t0.7"]) and b in dict(by[i]["t0.7"])]},
    ]
    gates = {"gold": [(i, by[i]["prompt"], by[i]["gold"]) for i in ids], "v3b greedy": [(i, by[i]["prompt"], by[i]["greedy"]) for i in ids],
             "v3b T=0.7": [(f"{i}#{k}", by[i]["prompt"], t) for i in ids for k, t in by[i]["t0.7"]],
             "v3b probes": [(i, v3b[i]["user"], v3b[i]["response"]) for i in pids], "base probes": [(i, base[i]["user"], base[i]["response"]) for i in pids]}
    return comps, gates, None

def cluster_sources(n, seed):
    HW = Path(os.environ.get("CALIB_HW", "/private/tmp/claude-501/-Users-agastyasridharan-cs-2881r/3acde4e5-4736-45cc-b35b-049e0cab88c1/scratchpad/hw1/persona_eval"))
    GENS = Path(os.environ.get("CALIB_GENS", REPO / "gens"))
    gold = {r["id"]: r for r in load(HW / "data/heldout_gold.jsonl")}
    v3b = {r["id"]: r for r in load(GENS / "sft-lora-r32-mixAB-v3b/checkpoint-576.jsonl")}
    base = {r["id"]: r for r in load(GENS / "sft-lora-r32-mixAB-v3b/base.jsonl")}
    ids = sorted(gold); random.Random(seed).shuffle(ids); ids = [i for i in ids if i in v3b and i in base][:n]
    def prompt_of(i): return [m for m in v3b[i]["messages"] if m["role"] == "user"][0]["content"]
    def gold_text(r): return r.get("gold") or r.get("reference") or r.get("response")
    SYS = {"gold": {i: gold_text(gold[i]) for i in ids}, "v3b": {i: v3b[i]["response"] for i in ids}, "base": {i: base[i]["response"] for i in ids}}
    sonnet = {}
    for r in load(HW / "results/judge_raw.jsonl"):
        if r.get("task") != "pairwise" or not r.get("parsed"): continue
        w = r["parsed"].get("winner"); sonnet[(r["comparison"], r["id"], r["order"])] = r["A"] if w == "A" else r["B"]
    comps = [{"name": f"{x} vs {y}", "x": x, "y": y, "expect": "x", "items": [(i, prompt_of(i), SYS[x][i], SYS[y][i]) for i in ids]} for x, y in (("v3b", "base"), ("gold", "base"), ("gold", "v3b"))]
    gates = {s: [(i, prompt_of(i), SYS[s][i]) for i in ids] for s in SYS}
    return comps, gates, sonnet

def run_model(model, effort, comps, gates, sonnet, workers, raw, brief):
    core.set_reasoning_effort(effort)
    label = f"{model}" + (f" (reasoning={effort})" if is_reasoning(model) else "")
    t0 = time.time(); u0 = usage_summary(); lat = []
    def run_pair(args):
        c, (i, p, a, b) = args; t = time.time()
        try: res = persona_pair(model, p, a, b, brief=brief, max_tokens=300 if brief else 700)
        except Exception as e: res = {"p_a": None, "n_valid": 0, "consistent": False, "items": {}, "orders": [{"ok": False, "error": str(e)[:200]}, {"ok": False}]}
        lat.append((time.time() - t) / 2); return c["name"], i, res
    def run_gate(args):
        s, (i, p, t_) = args; t = time.time()
        try: res = task_gate(model, p, t_)
        except Exception as e: res = {"ok": False, "error": str(e)[:200]}
        lat.append(time.time() - t); return s, i, res
    PW = {}; GT = {}
    with ThreadPoolExecutor(workers) as ex:
        for name, i, res in ex.map(run_pair, [(c, it) for c in comps for it in c["items"]]): PW[(name, i)] = res
        for s, i, res in ex.map(run_gate, [(s, it) for s in gates for it in gates[s]]): GT[(s, i)] = res
    dt = time.time() - t0; u1 = usage_summary()
    cost = u1["cost_usd"] - u0["cost_usd"]; calls = u1["calls"] - u0["calls"]; cached = u1["cached_calls"] - u0["cached_calls"]
    rt = u1["reasoning_tokens"] - u0["reasoning_tokens"]; ct = u1["completion_tokens"] - u0["completion_tokens"]
    for (name, i), res in PW.items(): raw.write(json.dumps({"model": model, "effort": effort, "pair": name, "id": i, **res}, ensure_ascii=False) + "\n")
    for (s, i), res in GT.items(): raw.write(json.dumps({"model": model, "effort": effort, "system": s, "id": i, **{k: v for k, v in res.items() if k != "usage"}}, ensure_ascii=False) + "\n")
    rep = [f"## {label}\n", f"calls {calls} (cached {cached}), wall {dt:.0f}s, cost ${cost:.2f} ({cost / max(1, calls - cached) * 1000:.2f} $/1k calls), "
           f"latency median {statistics.median(lat) if lat else 0:.1f}s p90 {sorted(lat)[int(0.9 * len(lat))] if lat else 0:.1f}s, output tokens/call {ct / max(1, calls - cached):.0f} (reasoning {rt / max(1, calls - cached):.0f})\n",
           "| comparison | n pairs | valid verdicts | first-named wins | win rate | Wilson 95% | order-consistent | picked first-shown | agreement with Sonnet (n) |", "|---|---|---|---|---|---|---|---|---|"]
    for c in comps:
        k = n = cons = pickA = agree = agree_n = 0
        for (i, p, a, b) in c["items"]:
            res = PW[(c["name"], i)]
            for o, (shownA, shownB) in zip(res["orders"], ((c["x"], c["y"]), (c["y"], c["x"]))):
                if not o.get("ok"): continue
                n += 1; win = shownA if o["winner"] == "A" else shownB; k += (win == c["x"]); pickA += (o["winner"] == "A")
                if sonnet:
                    comp = {("v3b", "base"): "base_vs_v3b", ("gold", "base"): "base_vs_gold"}.get((c["x"], c["y"]))
                    if comp:
                        ref = sonnet.get((comp, i, "lr" if shownA == "base" else "rl"))
                        if ref: agree_n += 1; agree += (ref == win)
            cons += bool(res["consistent"])
        lo, hi = wilson(k, n)
        rep.append(f"| {c['name']} | {len(c['items'])} | {n} | {k} | {k / max(1, n):.3f} | [{lo:.2f}, {hi:.2f}] | {cons}/{len(c['items'])} | {pickA / max(1, n):.2f} | " + (f"{agree / agree_n:.2f} ({agree_n})" if agree_n else "–") + " |")
    rep.append("\nposition bias: 'picked first-shown' should be ~0.50; order-consistent should be high; the siblings row has no expected winner.\n")
    # sibling sanity: does the judge side with the sibling that the deterministic rules like better (persona-defect terms only)?
    sib = next((c for c in comps if c["expect"] is None), None)
    if sib:
        agree = tot = 0; defect = ("false_claim", "tool_voice", "canon", "anti_canon", "preamble", "repetition", "bazinga_multi", "credential", "idle_names", "fence_sitting")
        for (i, p, a, b) in sib["items"]:
            res = PW[(sib["name"], i)]
            if res.get("p_a") is None or res["p_a"] == 0.5: continue
            ra = sum(score_rules(p, a)["terms"][t] for t in defect); rb = sum(score_rules(p, b)["terms"][t] for t in defect)
            if abs(ra - rb) < 0.5: continue
            tot += 1; agree += ((res["p_a"] > 0.5) == (ra < rb))
        rep.append(f"siblings: judge sided with the lower-rule-defect sibling in {agree}/{tot} decisive pairs where the rule terms differed by >= 0.5.\n")
    rep.append("| item | " + " | ".join(f"{c['x']}>{c['y']} / {c['y']}>{c['x']} / tie ({c['name']})" for c in comps) + " |"); rep.append("|---|" + "---|" * len(comps))
    for it in ITEMS:
        cells = []
        for c in comps:
            v = [PW[(c["name"], i)]["items"].get(it) for (i, p, a, b) in c["items"]]; v = [x for x in v if x is not None]
            cells.append(f"{sum(1 for x in v if x > 0)} / {sum(1 for x in v if x < 0)} / {sum(1 for x in v if x == 0)}")
        rep.append(f"| {it} | " + " | ".join(cells) + " |")
    rep.append("\n| system | n | gate ok | task mean | refused | worse_off | contradiction | false_claim | parse fail |\n|---|---|---|---|---|---|---|---|---|")
    for s in gates:
        G = [GT[(s, i)] for (i, p, t) in gates[s]]; ok = [g for g in G if g.get("ok")]
        if not ok: rep.append(f"| {s} | {len(G)} | – | – | – | – | – | – | {len(G)} |"); continue
        rep.append(f"| {s} | {len(G)} | {sum(g['gate'] for g in ok)}/{len(ok)} | {statistics.mean(g['task_score'] for g in ok):.2f} | {sum(g['refused'] for g in ok)} | {sum(g['worse_off'] for g in ok)} | {sum(g['contradiction'] for g in ok)} | {sum(g['false_claim'] for g in ok)} | {len(G) - len(ok)} |")
    ex = [(s, i, GT[(s, i)]) for s in gates if s.startswith("v3b") for (i, p, t) in gates[s] if GT[(s, i)].get("ok") and (GT[(s, i)]["contradiction"] or GT[(s, i)]["false_claim"] or GT[(s, i)]["refused"] or GT[(s, i)]["worse_off"])][:10]
    if ex:
        rep.append("\nv3b gate flags (spot-check):")
        for s, i, g in ex: rep.append(f"- `{s} {i}` refused={g['refused']} worse_off={g['worse_off']} contradiction={g['contradiction']} {g['contradiction_quotes']} | false_claim={g['false_claim']} {g['false_claim_quote']!r}")
    ex2 = [(c["name"], i, PW[(c["name"], i)]) for c in comps if c["expect"] == "x" for (i, p, a, b) in c["items"] if PW[(c["name"], i)].get("p_a") is not None and PW[(c["name"], i)]["p_a"] < 0.5][:6]
    if ex2:
        rep.append("\nupsets (expected winner lost both orders or split; spot-check the summaries):")
        for name, i, res in ex2: rep.append(f"- `{name} {i}` p_x={res['p_a']} | " + " || ".join(str(o.get("summary", o.get("raw", "")))[:160] for o in res["orders"]))
    rep.append("")
    return rep

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--models", default=DEFAULT_MODEL); ap.add_argument("--efforts", default="minimal", help="comma list; applies to reasoning models only")
    ap.add_argument("--source", default="local", choices=["local", "cluster"]); ap.add_argument("--n", type=int, default=40); ap.add_argument("--probe_n", type=int, default=120)
    ap.add_argument("--workers", type=int, default=32); ap.add_argument("--seed", type=int, default=0); ap.add_argument("--tag", default=None)
    ap.add_argument("--full_items", action="store_true", help="use the long pairwise prompt with quoted reasons (RL uses the brief one)")
    a = ap.parse_args()
    tag = a.tag or re.sub(r"[^a-z0-9]+", "_", a.models.split(",")[0].lower()).strip("_")
    out_md = Path(os.environ.get("CALIB_OUT_MD", REPO / f"rlaif/judge/calibration_{tag}.md")); out_raw = Path(os.environ.get("CALIB_OUT_RAW", REPO / f"rlaif/judge/calibration_raw_{tag}.jsonl"))
    comps, gates, sonnet = local_sources(a.n, a.probe_n, a.seed) if a.source == "local" else cluster_sources(a.n, a.seed)
    report = [f"# Judge calibration ({a.source} sources, seed {a.seed}; brief pairwise prompt = {not a.full_items})\n",
              "comparisons: " + "; ".join(f"{c['name']}: {len(c['items'])} pairs x 2 orders" for c in comps) + "\n", "gates: " + "; ".join(f"{s}: {len(v)}" for s, v in gates.items()) + "\n"]
    raw = open(out_raw, "a")
    for model in a.models.split(","):
        for effort in (a.efforts.split(",") if is_reasoning(model) else [None]):
            rep = run_model(model, effort, comps, gates, sonnet, a.workers, raw, brief=not a.full_items)
            report += rep; out_md.write_text("\n".join(report)); print("\n".join(rep)); sys.stdout.flush()
    raw.close(); out_md.write_text("\n".join(report)); print("wrote", out_md, "| usage", usage_summary())

if __name__ == "__main__": main()
