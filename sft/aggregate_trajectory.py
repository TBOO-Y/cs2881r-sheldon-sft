#!/usr/bin/env python3
"""Aggregate the SFT trajectory: per checkpoint -> val loss, GSM8K accuracy, persona marker density.
Inputs (synced from the cluster into --root):
  <root>/evals/gsm8k/<run>/<ckpt>.jsonl(.summary.json)   from eval_gsm8k.py
  <root>/gens/<run>/<ckpt>.jsonl                          from generate_heldout.py
  <root>/runs/<run>/trainer_state.json                    (final trainer state, for eval_loss by step)
Outputs: <root>/results/<run>/trajectory.csv, trajectory.md, trajectory.png; optional --wandb logging.
Stdlib + matplotlib (run via: uv run --with matplotlib [--with wandb] python aggregate_trajectory.py ...)."""
import argparse, csv, glob, json, os, re, statistics
BBT = re.compile(r"\b(leonard|penny|amy|howard|raj|meemaw|bazinga|roommate agreement|kripke|wolowitz|caltech|pasadena|sheldon)\b", re.I)
MARK = {"bazinga": r"\bbazinga\b", "leonard": r"\bleonard\b", "roommate_agreement": r"roommate agreement",
        "about_to_make_a_joke": r"about to make a joke", "as_an_ai": r"as an ai\b|language model|i'?m an ai|i am an ai"}
def step_of(name):
    if name == "base": return 0
    if name == "final_adapter": return None  # filled from trainer_state max step
    m = re.search(r"checkpoint-(\d+)", name); return int(m.group(1)) if m else None
def persona_stats(rows):
    out = {}
    for src in ["heldout", "ood"]:
        rs = [r for r in rows if r.get("source") == src]
        if not rs: continue
        out[f"{src}_bbt_ref_pct"] = round(100 * sum(1 for r in rs if BBT.search(r["response"])) / len(rs), 1)
        for k, p in MARK.items(): out[f"{src}_{k}_pct"] = round(100 * sum(1 for r in rs if re.search(p, r["response"], re.I)) / len(rs), 1)
        out[f"{src}_mean_words"] = round(statistics.mean(len(r["response"].split()) for r in rs))
        out[f"{src}_hit_max_pct"] = round(100 * sum(r["hit_max"] for r in rs) / len(rs), 1)
    return out
def gsm8k_persona(rows):  # persona leakage into math answers
    return {"gsm8k_bbt_ref_pct": round(100 * sum(1 for r in rows if BBT.search(r["response"])) / len(rows), 1)}
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--root", default="."); ap.add_argument("--run", required=True); ap.add_argument("--wandb", action="store_true")
    a = ap.parse_args(); R = a.root; out_dir = os.path.join(R, "results", a.run); os.makedirs(out_dir, exist_ok=True)
    ts_path = os.path.join(R, "runs", a.run, "trainer_state.json"); val = {}; max_step = None
    if os.path.exists(ts_path):
        ts = json.load(open(ts_path)); max_step = ts.get("global_step")
        for h in ts["log_history"]:
            if "eval_loss" in h: val[int(round(h["step"]))] = h["eval_loss"]
    names = set()
    for f in glob.glob(os.path.join(R, "evals", "gsm8k", a.run, "*.jsonl")): names.add(os.path.basename(f)[:-6])
    for f in glob.glob(os.path.join(R, "gens", a.run, "*.jsonl")): names.add(os.path.basename(f)[:-6])
    rows = []
    for n in names:
        step = step_of(n)
        if step is None: step = max_step if n == "final_adapter" else -1
        rec = {"ckpt": n, "step": step, "epoch": round(step / 187, 2) if step >= 0 else None, "val_loss": val.get(step)}
        sp = os.path.join(R, "evals", "gsm8k", a.run, n + ".jsonl.summary.json")
        if os.path.exists(sp):
            s = json.load(open(sp)); rec.update({"gsm8k_acc": round(100 * s["acc_strict"], 1), "gsm8k_acc_lenient": round(100 * s["acc_lenient"], 1),
                                                "gsm8k_boxed_pct": round(100 * s["boxed_rate"], 1), "gsm8k_mean_tokens": round(s["mean_gen_tokens"]), "gsm8k_hit_max_pct": round(100 * s["hit_max_rate"], 1)})
            rec.update(gsm8k_persona([json.loads(l) for l in open(sp[:-13])]))
        gp = os.path.join(R, "gens", a.run, n + ".jsonl")
        if os.path.exists(gp): rec.update(persona_stats([json.loads(l) for l in open(gp)]))
        rows.append(rec)
    rows.sort(key=lambda r: r["step"])
    cols = ["ckpt", "step", "epoch", "val_loss", "gsm8k_acc", "gsm8k_acc_lenient", "gsm8k_boxed_pct", "gsm8k_mean_tokens", "gsm8k_hit_max_pct", "gsm8k_bbt_ref_pct",
            "heldout_bbt_ref_pct", "heldout_bazinga_pct", "heldout_leonard_pct", "heldout_roommate_agreement_pct", "heldout_about_to_make_a_joke_pct", "heldout_as_an_ai_pct", "heldout_mean_words", "heldout_hit_max_pct",
            "ood_bbt_ref_pct", "ood_bazinga_pct", "ood_leonard_pct", "ood_as_an_ai_pct", "ood_mean_words", "ood_hit_max_pct"]
    with open(os.path.join(out_dir, "trajectory.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    short = ["ckpt", "step", "val_loss", "gsm8k_acc", "gsm8k_boxed_pct", "gsm8k_bbt_ref_pct", "heldout_bbt_ref_pct", "ood_bbt_ref_pct", "heldout_bazinga_pct", "heldout_mean_words"]
    md = "| " + " | ".join(short) + " |\n|" + "---|" * len(short) + "\n" + "".join("| " + " | ".join("" if r.get(c) is None else (f"{r[c]:.3f}" if c == "val_loss" else str(r[c])) for c in short) + " |\n" for r in rows)
    open(os.path.join(out_dir, "trajectory.md"), "w").write(md); print(md)
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        pts = [r for r in rows if r["step"] >= 0]; x = [r["step"] for r in pts]
        fig, ax1 = plt.subplots(figsize=(9, 5)); ax2 = ax1.twinx()
        g = [(r["step"], r["gsm8k_acc"]) for r in pts if r.get("gsm8k_acc") is not None]
        h = [(r["step"], r["heldout_bbt_ref_pct"]) for r in pts if r.get("heldout_bbt_ref_pct") is not None]
        o = [(r["step"], r["ood_bbt_ref_pct"]) for r in pts if r.get("ood_bbt_ref_pct") is not None]
        if g: ax1.plot(*zip(*g), "o-", color="#1f77b4", label="GSM8K accuracy (strict, %)")
        if h: ax2.plot(*zip(*h), "s--", color="#d62728", label="Persona: BBT reference rate, held-out prompts (%)")
        if o: ax2.plot(*zip(*o), "^:", color="#ff7f0e", label="Persona: BBT reference rate, short OOD prompts (%)")
        ax1.set_xlabel("SFT optimizer step (187 = 1 epoch)"); ax1.set_ylabel("GSM8K accuracy (%)", color="#1f77b4"); ax2.set_ylabel("Persona marker rate (%)", color="#d62728")
        ax1.set_ylim(0, 100); ax2.set_ylim(0, 100); ax1.axvline(187, color="gray", lw=0.8, ls="--")
        l1, n1 = ax1.get_legend_handles_labels(); l2, n2 = ax2.get_legend_handles_labels(); ax1.legend(l1 + l2, n1 + n2, loc="lower right", fontsize=8)
        plt.title(f"Persona-only SFT trajectory: {a.run}"); fig.tight_layout(); fig.savefig(os.path.join(out_dir, "trajectory.png"), dpi=150); print("[plot]", os.path.join(out_dir, "trajectory.png"))
    except ImportError: print("[plot] matplotlib not available; skipped")
    if a.wandb:
        import wandb
        run = wandb.init(project="cs2881r-sheldon", name=f"trajectory-{a.run}", job_type="eval", config={"run": a.run})
        tbl = wandb.Table(columns=cols, data=[[r.get(c) for c in cols] for r in rows]); run.log({"trajectory_table": tbl})
        for r in rows:
            if r["step"] >= 0: run.log({k: v for k, v in r.items() if k not in ("ckpt", "epoch") and v is not None}, step=r["step"])
        if os.path.exists(os.path.join(out_dir, "trajectory.png")): run.log({"trajectory_plot": wandb.Image(os.path.join(out_dir, "trajectory.png"))})
        run.finish(); print("[wandb] logged", run.url)
if __name__ == "__main__":
    main()
