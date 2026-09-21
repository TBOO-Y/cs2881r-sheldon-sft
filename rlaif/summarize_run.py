#!/usr/bin/env python3
"""Per-checkpoint table for a GRPO run: GSM8K (accuracy, boxed rate, truncation) next to the persona collapse/defect monitors
(persona_audit.md §6.7) computed from the checkpoint's held-out generations, plus the reference models for context.
  python rlaif/summarize_run.py --run grpo-v1 [--ref sft-touchup-v4 --ref v3b --ref base] [--root $PROJ] [--tol 1.5]
Marks checkpoints whose GSM8K is within --tol points of the first --ref (the touch-up model the run started from): those are the
candidates for the final model; among them pick the one with the best persona monitors (lower rule penalty / template share, higher opener entropy).
"""
import argparse, json, os, re, statistics, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from reward.rules import score_rules
from reward.reward import style_metrics

def load(p): return [json.loads(l) for l in open(p)]
def prompt_of(r): return next((m["content"] for m in r.get("messages", []) if m["role"] == "user"), "")

def persona_row(path):
    rows = [r for r in load(path) if r.get("kind") != "ood_short"]
    if not rows: return {}
    comps = [r["response"] for r in rows]; m = style_metrics(comps)
    rules = [score_rules(prompt_of(r), r["response"], r.get("kind"), "length" if r.get("hit_max") else None) for r in rows]
    return {"words": m["style/mean_words"], "hit_max%": 100 * sum(1 for r in rows if r.get("hit_max")) / len(rows), "open_H": m["style/opener_entropy_bits"],
            "tmpl%": 100 * m["style/template_opener_frac"], "rule_pen": statistics.mean(r["penalty"] for r in rules), "tool%": 100 * m["style/warm_closer"],
            "names": m["style/names_per_reply"], "bazinga%": 100 * m["style/bazinga"], "n": len(rows)}

def gsm_row(summary_path):
    if not summary_path.exists(): return {}
    d = json.load(open(summary_path)); return {"gsm8k": 100 * d["acc_strict"], "lenient": 100 * d["acc_lenient"], "boxed%": 100 * d["boxed_rate"], "gsm_hitmax%": 100 * d["hit_max_rate"], "gsm_tok": d["mean_gen_tokens"]}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--run", required=True); ap.add_argument("--ref", action="append", default=[]); ap.add_argument("--root", default=os.environ.get("PROJ", "."))
    ap.add_argument("--tol", type=float, default=1.5); a = ap.parse_args(); R = Path(a.root)
    rows = []
    for ref in a.ref:
        rows.append({"model": ref, **gsm_row(R / f"evals/gsm8k/{ref}/final.jsonl.summary.json"), **(persona_row(R / f"gens/{ref}/final.jsonl") if (R / f"gens/{ref}/final.jsonl").exists() else {})})
    ck = sorted({p.stem.split(".")[0] for p in (R / f"evals/gsm8k/{a.run}").glob("checkpoint-*.summary.json")} | {p.stem for p in (R / f"gens/{a.run}").glob("checkpoint-*.jsonl") if ".short" not in p.name}, key=lambda s: int(s.split("-")[1]))
    for c in ck:
        g = R / f"gens/{a.run}/{c}.jsonl"
        rows.append({"model": f"{a.run}/{c}", **gsm_row(R / f"evals/gsm8k/{a.run}/{c}.jsonl.summary.json"), **(persona_row(g) if g.exists() else {})})
    fin = R / f"evals/gsm8k/{a.run}/final.jsonl.summary.json"
    if fin.exists(): rows.append({"model": f"{a.run}/final(merged)", **gsm_row(fin), **(persona_row(R / f"gens/{a.run}/final.jsonl") if (R / f"gens/{a.run}/final.jsonl").exists() else {})})
    cols = ["gsm8k", "boxed%", "gsm_hitmax%", "words", "hit_max%", "open_H", "tmpl%", "rule_pen", "tool%", "names", "bazinga%"]
    base = next((r["gsm8k"] for r in rows if r["model"] == (a.ref[0] if a.ref else "") and "gsm8k" in r), None)
    print(f"{'model':34s}" + "".join(f"{c:>11s}" for c in cols) + "   ok")
    for r in rows:
        ok = "" if base is None or "gsm8k" not in r else ("  <=" if r["gsm8k"] >= base - a.tol else "  x")
        print(f"{r['model'][:34]:34s}" + "".join(f"{r[c]:11.1f}" if c in r else f"{'-':>11s}" for c in cols) + ok)
    if base is not None: print(f"\n'<=' = GSM8K within {a.tol} points of {a.ref[0]} ({base:.1f}); pick the latest such checkpoint with the best persona monitors (lower tmpl%/rule_pen/tool%, higher open_H).")

if __name__ == "__main__": main()
