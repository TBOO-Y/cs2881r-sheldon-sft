#!/usr/bin/env python3
"""Tables from evals/rlvr/: per-model rows (full suite) and per-checkpoint rows (quick suite) with W&B-free training stats read from
runs/<run>/trainer_state.json (reward, truncation, zero-variance fraction, drift). Writes Markdown to --out and prints it.
  python rlvr/summarize_run.py --models base sft-touchup-v4 grpo-v2 --out results/rlvr/baselines.md
  python rlvr/summarize_run.py --runs pilot-full-adamw pilot-lora-adamw --ref grpo-v2 --out results/rlvr/pilots.md
"""
import argparse, json, os
from pathlib import Path
PROJ = Path(os.environ.get("PROJ", Path(__file__).resolve().parents[1]))

def load(p):
    p = Path(p); return json.load(open(p)) if p.exists() else None

def pct(x): return "-" if x is None else f"{100 * x:.1f}"

def model_row(name, d):
    g5 = load(d / "greedy/math500.summary.json"); a4 = load(d / "avg4/math500.summary.json"); gs = load(d / "greedy/gsm8k.summary.json")
    aime = {k: load(d / f"avg16/{k}.summary.json") for k in ("aime24", "aime25", "aime26")}
    lv = (a4 or g5 or {}).get("acc_by_level", {})
    return {"model": name, "m500_greedy": g5 and g5["acc"], "m500_avg4": a4 and a4["acc"], "L3_5": (a4 or g5 or {}).get("acc_L3_5"),
            "L1": lv.get("1"), "L2": lv.get("2"), "L3": lv.get("3"), "L4": lv.get("4"), "L5": lv.get("5"),
            "gsm8k": gs and gs["acc"], "aime24": aime["aime24"] and aime["aime24"]["acc"], "aime25": aime["aime25"] and aime["aime25"]["acc"], "aime26": aime["aime26"] and aime["aime26"]["acc"],
            "aime_pass16": None if not aime["aime24"] else sum(v["pass_at_n"] for v in aime.values() if v) / sum(1 for v in aime.values() if v),
            "tokens": (a4 or g5 or {}).get("mean_gen_tokens"), "hit_max": (a4 or g5 or {}).get("hit_max_rate"), "boxed": (a4 or g5 or {}).get("boxed_rate")}

COLS = [("model", "model"), ("m500_greedy", "MATH-500 greedy"), ("m500_avg4", "avg@4"), ("L3_5", "L3-5 avg@4"), ("L1", "L1"), ("L2", "L2"), ("L3", "L3"), ("L4", "L4"), ("L5", "L5"),
        ("gsm8k", "GSM8K"), ("aime24", "AIME24 avg@16"), ("aime25", "AIME25"), ("aime26", "AIME26"), ("aime_pass16", "AIME pass@16"), ("tokens", "tokens"), ("hit_max", "hit cap"), ("boxed", "boxed")]

def table(rows):
    out = ["| " + " | ".join(h for _, h in COLS) + " |", "|" + "---|" * len(COLS)]
    for r in rows: out.append("| " + " | ".join((str(r[k]) if k == "model" else (f"{r[k]:.0f}" if k == "tokens" and r[k] is not None else pct(r[k]))) for k, _ in COLS) + " |")
    return "\n".join(out)

def train_stats(run):
    st = load(PROJ / "runs" / run / "trainer_state.json")
    if not st:
        cks = sorted((PROJ / "runs" / run).glob("checkpoint-*/trainer_state.json"), key=lambda p: int(p.parent.name.split("-")[1]))
        st = load(cks[-1]) if cks else None
    if not st: return {}
    hist = [h for h in st["log_history"] if "reward" in h]
    def mean(key, sl): v = [h[key] for h in hist[sl] if key in h]; return sum(v) / len(v) if v else None
    n = len(hist); q = max(1, n // 4)
    return {"steps": n, "reward_first": mean("reward", slice(0, q)), "reward_last": mean("reward", slice(n - q, n)), "acc_last": mean("rlvr/acc", slice(n - q, n)),
            "trunc_last": mean("rlvr/frac_truncated", slice(n - q, n)), "zero_var_last": mean("rlvr/frac_zero_var_groups", slice(n - q, n)),
            "len_last": mean("completions/mean_length", slice(n - q, n)), "grad_norm": mean("grad_norm", slice(n - q, n)),
            "drift": next((h["rlvr/param_drift_rel"] for h in reversed(st["log_history"]) if "rlvr/param_drift_rel" in h), None),
            "update_rms": mean("rlvr/update_rms", slice(n - q, n)), "s_per_step": (st["log_history"][-1].get("step_time") if st["log_history"] else None)}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--models", nargs="*", default=[]); ap.add_argument("--runs", nargs="*", default=[]); ap.add_argument("--ref", action="append", default=[]); ap.add_argument("--out", required=True)
    a = ap.parse_args(); parts = []
    rows = [model_row(m, PROJ / "evals/rlvr" / m) for m in a.ref + a.models]
    if rows: parts += ["## Models (full suite)", "", table(rows), ""]
    for run in a.runs:
        cks = sorted((PROJ / "evals/rlvr" / run).glob("checkpoint-*"), key=lambda p: int(p.name.split("-")[1]))
        rows = [model_row(f"{run}/{c.name}", c) for c in cks]
        if (PROJ / "evals/rlvr" / run / "avg4").exists(): rows.append(model_row(f"{run} (final)", PROJ / "evals/rlvr" / run))
        ts = train_stats(run)
        parts += [f"## {run}", "", "training: " + ", ".join(f"{k}={v:.3g}" if isinstance(v, float) else f"{k}={v}" for k, v in ts.items() if v is not None), "", table(rows), ""]
    txt = "\n".join(parts); print(txt)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True); open(a.out, "w").write(txt + "\n")

if __name__ == "__main__": main()
