#!/usr/bin/env python3
"""Calibrate cheap OpenAI judge models offline on the 50 held-out ids the Sonnet judge used.

Pairwise (both orders): v3b vs base, gold vs base, gold vs v3b.  Task gate on gold / base / v3b.
Reports: win rates + Wilson CI, order-consistency, position bias, agreement with claude-sonnet-4-6 verdicts
(results/judge_raw.jsonl), gate pass rates and flag rates per system, latency and cost per model.
Usage: python rlaif/judge/calibrate.py --models gpt-4.1-nano,gpt-5-nano,gpt-4.1-mini [--n 50]
"""
import argparse, json, math, random, statistics, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from judge.core import task_gate, persona_pair
from judge.oai import usage_summary, USAGE

import os
REPO = Path(__file__).resolve().parents[2]
HW = Path(os.environ.get("CALIB_HW", "/private/tmp/claude-501/-Users-agastyasridharan-cs-2881r/3acde4e5-4736-45cc-b35b-049e0cab88c1/scratchpad/hw1/persona_eval"))
GENS = Path(os.environ.get("CALIB_GENS", REPO / "gens"))
OUT_MD = Path(os.environ.get("CALIB_OUT_MD", REPO / "rlaif/judge/calibration_report.md")); OUT_RAW = Path(os.environ.get("CALIB_OUT_RAW", REPO / "rlaif/judge/calibration_raw.jsonl"))

def load(p): return [json.loads(l) for l in open(p)]
def wilson(k, n, z=1.96):
    if n == 0: return (float("nan"), float("nan"))
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--models", default="gpt-4.1-nano,gpt-5-nano,gpt-4.1-mini"); ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--workers", type=int, default=12); ap.add_argument("--seed", type=int, default=0); a = ap.parse_args()
    gold = {r["id"]: r for r in load(HW / "data/heldout_gold.jsonl")}
    v3b = {r["id"]: r for r in load(GENS / "sft-lora-r32-mixAB-v3b/checkpoint-576.jsonl")}
    base = {r["id"]: r for r in load(GENS / "sft-lora-r32-mixAB-v3b/base.jsonl")}
    ids = sorted(gold); random.Random(a.seed).shuffle(ids); ids = [i for i in ids if i in v3b and i in base][:a.n]
    def prompt_of(i): return [m for m in v3b[i]["messages"] if m["role"] == "user"][0]["content"]
    def gold_text(r): return r.get("gold") or r.get("reference") or r.get("response")
    SYS = {"gold": {i: gold_text(gold[i]) for i in ids}, "v3b": {i: v3b[i]["response"] for i in ids}, "base": {i: base[i]["response"] for i in ids}}
    # Sonnet reference verdicts: winner system per (comparison, id, order)
    sonnet = {}
    for r in load(HW / "results/judge_raw.jsonl"):
        if r.get("task") != "pairwise" or not r.get("parsed"): continue
        w = r["parsed"].get("winner"); sonnet[(r["comparison"], r["id"], r["order"])] = r["A"] if w == "A" else r["B"]
    PAIRS = [("v3b", "base"), ("gold", "base"), ("gold", "v3b")]
    report = ["# Cheap-judge calibration (%d held-out ids, seed %d; same ids as the Sonnet judge)\n" % (len(ids), a.seed)]
    raw = open(OUT_RAW, "a")
    for model in a.models.split(","):
        t0 = time.time(); u0 = usage_summary()
        pw = {}
        def run_pair(args):
            x, y, i = args
            try: return (x, y, i, persona_pair(model, prompt_of(i), SYS[x][i], SYS[y][i]))
            except Exception as e: return (x, y, i, {"p_a": None, "n_valid": 0, "consistent": False, "items": {}, "orders": [{"ok": False, "error": str(e)[:200]}, {"ok": False}]})
        with ThreadPoolExecutor(a.workers) as ex:
            for x, y, i, res in ex.map(run_pair, [(x, y, i) for x, y in PAIRS for i in ids]): pw[(x, y, i)] = res
        gates = {}
        def run_gate(args):
            s, i = args
            try: return (s, i, task_gate(model, prompt_of(i), SYS[s][i]))
            except Exception as e: return (s, i, {"ok": False, "error": str(e)[:200]})
        with ThreadPoolExecutor(a.workers) as ex:
            for s, i, res in ex.map(run_gate, [(s, i) for s in SYS for i in ids]): gates[(s, i)] = res
        dt = time.time() - t0; u1 = usage_summary()
        cost = u1["cost_usd"] - u0["cost_usd"]; calls = u1["calls"] - u0["calls"]; cached = u1["cached_calls"] - u0["cached_calls"]
        for (x, y, i), res in pw.items(): raw.write(json.dumps({"model": model, "pair": [x, y], "id": i, **{k: v for k, v in res.items()}}, ensure_ascii=False) + "\n")
        for (s, i), res in gates.items(): raw.write(json.dumps({"model": model, "gate": s, "id": i, **{k: v for k, v in res.items() if k != "usage"}}, ensure_ascii=False) + "\n")
        report.append(f"## {model}\n\ncalls {calls} (cached {cached}), wall {dt:.0f}s, est. cost ${cost:.2f}\n")
        report.append("| pair | valid verdicts | first wins | win rate | Wilson 95% | order-consistent pairs | agreement with Sonnet (n) |\n|---|---|---|---|---|---|---|")
        pickA_total = pickA_n = 0
        for x, y in PAIRS:
            k = n = cons = 0; agree = agree_n = 0
            for i in ids:
                res = pw[(x, y, i)]
                for o, (shownA, shownB) in zip(res["orders"], ((x, y), (y, x))):
                    if not o.get("ok"): continue
                    n += 1; win_sys = shownA if o["winner"] == "A" else shownB; k += (win_sys == x)
                    pickA_total += (o["winner"] == "A"); pickA_n += 1
                    comp = {("v3b", "base"): "base_vs_v3b", ("gold", "base"): "base_vs_gold"}.get((x, y))
                    if comp:
                        # Sonnet's order key: 'lr' = A is the first-named system in comparison name (base), 'rl' = A is the second
                        order = "lr" if shownA == "base" else "rl"; ref = sonnet.get((comp, i, order))
                        if ref: agree_n += 1; agree += (ref == win_sys)
                cons += bool(res["consistent"])
            lo, hi = wilson(k, n)
            report.append(f"| {x} vs {y} | {n} | {k} | {k/max(1,n):.3f} | [{lo:.2f}, {hi:.2f}] | {cons}/{len(ids)} | " + (f"{agree/agree_n:.2f} ({agree_n})" if agree_n else "–") + " |")
        report.append(f"\nposition bias: picked the first-shown reply in {pickA_total/max(1,pickA_n):.2f} of verdicts (0.50 = none)\n")
        # item-level: how often each item favours gold over v3b (margin>0) — where the cheap judge's discrimination lives
        item_names = ["answer_first", "correction", "template", "rule_binds", "register_whole", "specificity", "superiority_precision", "humour_canon"]
        report.append("| item | gold>v3b | v3b>gold | tie/split | v3b>base | gold>base |\n|---|---|---|---|---|---|")
        for it in item_names:
            g = [pw[("gold", "v3b", i)]["items"].get(it) for i in ids]; g = [v for v in g if v is not None]
            vb = [pw[("v3b", "base", i)]["items"].get(it) for i in ids]; vb = [v for v in vb if v is not None]
            gb = [pw[("gold", "base", i)]["items"].get(it) for i in ids]; gb = [v for v in gb if v is not None]
            report.append(f"| {it} | {sum(1 for v in g if v>0)} | {sum(1 for v in g if v<0)} | {sum(1 for v in g if v==0)} | {sum(1 for v in vb if v>0)}/{len(vb)} | {sum(1 for v in gb if v>0)}/{len(gb)} |")
        report.append("\n| system | gate ok | task mean | refused | worse_off | contradiction | false_claim | parse fail |\n|---|---|---|---|---|---|---|---|")
        for s in SYS:
            G = [gates[(s, i)] for i in ids]; ok = [g for g in G if g.get("ok")]
            if not ok: report.append(f"| {s} | – | – | – | – | – | – | {len(G)} |"); continue
            report.append(f"| {s} | {sum(g['gate'] for g in ok)}/{len(ok)} | {statistics.mean(g['task_score'] for g in ok):.2f} | {sum(g['refused'] for g in ok)} | {sum(g['worse_off'] for g in ok)} | {sum(g['contradiction'] for g in ok)} | {sum(g['false_claim'] for g in ok)} | {len(G)-len(ok)} |")
        # examples of contradiction / false-claim quotes for v3b (spot-check material)
        ex = [(i, gates[("v3b", i)]) for i in ids if gates[("v3b", i)].get("ok") and (gates[("v3b", i)]["contradiction"] or gates[("v3b", i)]["false_claim"])][:6]
        if ex:
            report.append("\nv3b gate flags (spot-check):")
            for i, g in ex: report.append(f"- `{i}` contradiction={g['contradiction']} {g['contradiction_quotes']} | false_claim={g['false_claim']} {g['false_claim_quote']!r}")
        report.append("")
        OUT_MD.write_text("\n".join(report)); print("\n".join(report[-40:])); sys.stdout.flush()
    raw.close(); OUT_MD.write_text("\n".join(report)); print("wrote", OUT_MD, "| usage", usage_summary())

if __name__ == "__main__": main()
