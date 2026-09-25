#!/usr/bin/env python3
"""Pass-rate labels for a prompt set under one model: k sampled rollouts per problem through vLLM (offline engine, one GPU per
process; rlvr/runpod/label.sh runs 8 shards in parallel and merges). Same prompt format and sampling as training (T=1, top-p 1).
Per problem: {id, level, k, n_correct, passrate, mean_len, trunc_frac}.
  CUDA_VISIBLE_DEVICES=0 python rlvr/data/label_passrate.py --model <dir> --data rlvr/data/math12k.jsonl --k 8 --shard 0/8 --out rlvr/data/passrate_<tag>.shard0.jsonl
  python rlvr/data/label_passrate.py --merge rlvr/data/passrate_<tag>.shard*.jsonl --out rlvr/data/passrate_<tag>.jsonl --summary results/rlvr/difficulty_<tag>.md
"""
import argparse, glob, json, sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from rlvr.grader import grade_many
from rlvr.train_rlvr import DEFAULT_SYSTEM, SUFFIX

def run(a):
    from vllm import LLM, SamplingParams
    rows = [json.loads(l) for l in open(a.data)]
    if a.shard:
        i, n = map(int, a.shard.split("/")); rows = rows[i::n]
    if a.limit: rows = rows[:a.limit]
    llm = LLM(model=a.model, dtype="bfloat16", gpu_memory_utilization=a.gpu_mem, max_model_len=a.max_model_len, seed=a.seed, enable_prefix_caching=True)
    tok = llm.get_tokenizer()
    prompts = [tok.apply_chat_template([{"role": "system", "content": DEFAULT_SYSTEM}, {"role": "user", "content": r["problem"] + SUFFIX}], tokenize=False, add_generation_prompt=True) for r in rows]
    sp = SamplingParams(n=a.k, temperature=a.temperature, top_p=a.top_p, max_tokens=a.max_tokens, seed=a.seed)
    outs = llm.generate(prompts, sp)
    pairs, meta = [], []
    for r, o in zip(rows, outs):
        for c in o.outputs:
            pairs.append((c.text, str(r["answer"]))); meta.append((r["id"], len(c.token_ids), c.finish_reason == "length"))
    graded = grade_many(pairs, workers=a.workers)
    agg = defaultdict(lambda: {"n": 0, "c": 0, "len": 0, "tr": 0})
    for (pid, L, tr), g in zip(meta, graded):
        x = agg[pid]; x["n"] += 1; x["c"] += int(g["correct"] and not tr); x["len"] += L; x["tr"] += int(tr)
    with open(a.out, "w") as f:
        for r in rows:
            x = agg[r["id"]]
            f.write(json.dumps({"id": r["id"], "level": r.get("level", 0), "subject": r.get("subject", ""), "k": x["n"], "n_correct": x["c"], "passrate": x["c"] / max(1, x["n"]),
                                "mean_len": x["len"] / max(1, x["n"]), "trunc_frac": x["tr"] / max(1, x["n"])}) + "\n")
    print(f"{a.out}: {len(rows)} problems x {a.k}; mean pass {sum(x['c'] for x in agg.values()) / max(1, sum(x['n'] for x in agg.values())):.3f}")

def merge(a):
    rows = [json.loads(l) for p in sorted(glob.glob(a.merge)) for l in open(p)]
    with open(a.out, "w") as f:
        for r in rows: f.write(json.dumps(r) + "\n")
    by = defaultdict(list)
    for r in rows: by[r["level"]].append(r)
    lines = [f"# Difficulty profile: {a.out}", "", f"{len(rows)} problems, k = {rows[0]['k'] if rows else 0} rollouts each", "",
             "| level | n | mean pass | p=0 | 0<p<1/8 | 1/8<=p<=1/2 | 1/2<p<1 | p=1 | mean len | trunc |", "|---|---|---|---|---|---|---|---|---|---|"]
    def frac(rs, f): return sum(1 for r in rs if f(r["passrate"])) / max(1, len(rs))
    for lv in sorted(by):
        rs = by[lv]
        lines.append(f"| {lv} | {len(rs)} | {sum(r['passrate'] for r in rs) / len(rs):.3f} | {frac(rs, lambda p: p == 0):.2f} | {frac(rs, lambda p: 0 < p < 0.125):.2f} | "
                     f"{frac(rs, lambda p: 0.125 <= p <= 0.5):.2f} | {frac(rs, lambda p: 0.5 < p < 1):.2f} | {frac(rs, lambda p: p == 1):.2f} | "
                     f"{sum(r['mean_len'] for r in rs) / len(rs):.0f} | {sum(r['trunc_frac'] for r in rs) / len(rs):.3f} |")
    rs = rows
    lines.append(f"| all | {len(rs)} | {sum(r['passrate'] for r in rs) / len(rs):.3f} | {frac(rs, lambda p: p == 0):.2f} | {frac(rs, lambda p: 0 < p < 0.125):.2f} | "
                 f"{frac(rs, lambda p: 0.125 <= p <= 0.5):.2f} | {frac(rs, lambda p: 0.5 < p < 1):.2f} | {frac(rs, lambda p: p == 1):.2f} | "
                 f"{sum(r['mean_len'] for r in rs) / len(rs):.0f} | {sum(r['trunc_frac'] for r in rs) / len(rs):.3f} |")
    txt = "\n".join(lines); print(txt)
    if a.summary: Path(a.summary).parent.mkdir(parents=True, exist_ok=True); open(a.summary, "w").write(txt + "\n")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model"); ap.add_argument("--data"); ap.add_argument("--k", type=int, default=8); ap.add_argument("--shard", default="")
    ap.add_argument("--max_tokens", type=int, default=2048); ap.add_argument("--max_model_len", type=int, default=4096); ap.add_argument("--temperature", type=float, default=1.0); ap.add_argument("--top_p", type=float, default=1.0)
    ap.add_argument("--gpu_mem", type=float, default=0.9); ap.add_argument("--seed", type=int, default=0); ap.add_argument("--workers", type=int, default=16); ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", required=True); ap.add_argument("--merge", default=None, help="glob of shard files to merge"); ap.add_argument("--summary", default=None)
    a = ap.parse_args()
    merge(a) if a.merge else run(a)

if __name__ == "__main__": main()
