#!/usr/bin/env python3
"""Head-to-head persona judge between two generation files (stage-2 protocol: N held-out prompts, both presentation orders, GPT-5.6 Luna
via OpenRouter through rlaif/judge/core.persona_pair; disk-cached, so re-runs are free). Prints the win rate of A with a Wilson 95% CI,
order-consistency, and per-item margins; writes JSON.
  python rlvr/persona_h2h.py --a gens/rlvr-main/final.jsonl --b gens/grpo-v2/final.jsonl --n 200 --out results/rlvr/judge_h2h_rlvr.json [--judge mock]
"""
import argparse, json, math, random, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "rlaif"))
from judge.core import persona_pair, set_reasoning_effort
from judge.oai import DEFAULT_MODEL, usage_summary

def load(p): return {r["id"]: r for r in map(json.loads, open(p))}
def wilson(k, n, z=1.96):
    if n == 0: return (0.0, 0.0)
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--a", required=True); ap.add_argument("--b", required=True); ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--judge", default=DEFAULT_MODEL); ap.add_argument("--reasoning", default="low"); ap.add_argument("--seed", type=int, default=0); ap.add_argument("--out", required=True); ap.add_argument("--workers", type=int, default=16)
    a = ap.parse_args(); set_reasoning_effort(a.reasoning)
    A, B = load(a.a), load(a.b); ids = sorted(i for i in A if i in B and A[i].get("kind") != "ood_short"); random.Random(a.seed).shuffle(ids); ids = ids[: a.n]
    res = []; wins = 0.0; n_valid = 0; cons = 0; items = {}
    def one(i):
        msgs = A[i].get("messages", []); prompt = next((m["content"] for m in reversed(msgs) if m["role"] == "user"), A[i].get("prompt", ""))
        prior = [m for m in msgs if m["role"] != "system"][:-1] or None
        return i, persona_pair(a.judge, prompt, A[i]["response"], B[i]["response"], prior_turns=prior)
    with ThreadPoolExecutor(max_workers=max(1, a.workers)) as ex:
        for k, (i, r) in enumerate(ex.map(one, ids)):
            if r["p_a"] is not None: wins += r["p_a"]; n_valid += 1; cons += int(r["consistent"])
            for kk, v in r["items"].items(): items.setdefault(kk, []).append(v)
            res.append({"id": i, "p_a": r["p_a"], "consistent": r["consistent"], "items": r["items"]})
            if (k + 1) % 25 == 0: print(f"  {k + 1}/{len(ids)}: A win rate so far {wins / max(1, n_valid):.3f}", flush=True)
    wr = wins / max(1, n_valid); lo, hi = wilson(wins, n_valid)
    summary = {"a": a.a, "b": a.b, "judge": a.judge, "n": len(ids), "n_valid": n_valid, "a_win_rate": wr, "ci95": [lo, hi], "order_consistent": cons / max(1, n_valid),
               "items_margin_a": {k: sum(v) / len(v) for k, v in items.items()}, "usage": usage_summary() if a.judge != "mock" else None}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True); json.dump({"summary": summary, "pairs": res}, open(a.out, "w"), indent=1)
    print(json.dumps(summary, indent=1))

if __name__ == "__main__": main()
