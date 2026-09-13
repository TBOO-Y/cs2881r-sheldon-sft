#!/usr/bin/env python3
"""Overlay trajectory CSVs of several runs (from aggregate_trajectory.py) on shared axes.
  uv run --with matplotlib python sft/overlay_runs.py --root . --runs sft-lora-r32-nomath-v2 sft-lora-r32-mixA-v3a [--labels v2 v3a] --out results/overlay.png
Panels: GSM8K strict acc, GSM8K boxed rate, persona marker rate (held-out prompts), persona marker rate (OOD short prompts),
BBT leakage into GSM8K answers, val loss. x = epoch."""
import argparse, csv, os
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
ap = argparse.ArgumentParser(); ap.add_argument("--root", default="."); ap.add_argument("--runs", nargs="+", required=True); ap.add_argument("--labels", nargs="*")
ap.add_argument("--out", default="results/overlay.png"); a = ap.parse_args()
labels = a.labels or a.runs
PANELS = [("gsm8k_acc", "GSM8K test acc (strict, %)"), ("gsm8k_boxed_pct", "GSM8K boxed-answer rate (%)"), ("heldout_bbt_ref_pct", "Persona marker rate, held-out prompts (%)"),
          ("ood_bbt_ref_pct", "Persona marker rate, OOD short prompts (%)"), ("gsm8k_bbt_ref_pct", "BBT references inside GSM8K answers (%)"), ("val_loss", "val loss")]
fig, axes = plt.subplots(2, 3, figsize=(16, 8.5)); axes = axes.ravel(); rows_md = []
for run, lab in zip(a.runs, labels):
    p = os.path.join(a.root, "results", run, "trajectory.csv")
    if not os.path.exists(p): print("missing", p); continue
    rows = [r for r in csv.DictReader(open(p))]
    rows = [r for r in rows if r["ckpt"] != "final_adapter"]; rows.sort(key=lambda r: float(r["epoch"]))
    for ax, (k, title) in zip(axes, PANELS):
        xs = [float(r["epoch"]) for r in rows if r.get(k) not in ("", None)]; ys = [float(r[k]) for r in rows if r.get(k) not in ("", None)]
        ax.plot(xs, ys, marker="o", ms=3, label=lab); ax.set_title(title, fontsize=10); ax.set_xlabel("epoch"); ax.grid(alpha=.3)
    last = rows[-1]; rows_md.append(f"| {lab} | {len(rows) - 1} | {last['gsm8k_acc']} | {min(float(r['gsm8k_acc']) for r in rows if r['gsm8k_acc'])} | {last['gsm8k_boxed_pct']} | {last['heldout_bbt_ref_pct']} | {last['ood_bbt_ref_pct']} | {last['gsm8k_bbt_ref_pct']} |")
base = None
for ax in axes: ax.legend(fontsize=8)
fig.suptitle("Sheldon SFT arms: capability vs persona across training (base = epoch 0)"); fig.tight_layout()
os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True); fig.savefig(a.out, dpi=130); print("wrote", a.out)
md = "| run | ckpts | final GSM8K | min GSM8K | final boxed % | final persona (held-out) % | final persona (OOD) % | BBT-in-math % |\n|---|---|---|---|---|---|---|---|\n" + "\n".join(rows_md)
open(os.path.splitext(a.out)[0] + ".md", "w").write(md + "\n"); print(md)
