#!/usr/bin/env python3
"""Static difficulty schedule: an ordered list of training prompts for one run, built from the seed model's measured pass rates.

Buckets on the seed's pass rate p (label_passrate.py, k rollouts):  solved p == 1 (dropped), easy 0.5 < p < 1, medium 0.125 <= p <= 0.5,
hard p < 0.125 (includes p == 0). Without a pass-rate file (--by_level) the MATH level stands in: easy 1-2, medium 3-4, hard 5.
The bucket mixture drifts linearly from --mix_start to --mix_end over the run; per step the counts are largest-remainder rounded to
--prompts_per_step; prompts are drawn without replacement from a seeded shuffle of each bucket (a bucket that runs dry is reshuffled and
reused, counted in `repeats`). Printed before writing: per 10%-phase bucket mix, level mix, expected zero-variance fraction for group
size G  (P[dead] = q^G + (1-q)^G with the smoothed rate q = (c + 0.5) / (k + 1)) and the mean measured truncation rate.
  python rlvr/data/build_schedule.py --train rlvr/data/math12k.jsonl --passrate rlvr/data/passrate_grpo-v2.jsonl --steps 200 --prompts_per_step 16 --G 16 --out rlvr/data/schedule_main.jsonl
"""
import argparse, json, random
from collections import Counter

def bucket_of(p, easy_min=0.5, hard_max=0.125):
    if p >= 1.0: return "solved"
    if p > easy_min: return "easy"
    if p < hard_max: return "hard"
    return "medium"

def largest_remainder(weights, n):
    raw = [w * n for w in weights]; base = [int(x) for x in raw]; rem = n - sum(base)
    for i in sorted(range(len(raw)), key=lambda i: raw[i] - base[i], reverse=True)[:rem]: base[i] += 1
    return base

def build(train, passrate, steps, per_step, G, mix_start, mix_end, easy_min, hard_max, seed, min_level=1, by_level=False):
    rng = random.Random(seed)
    rows = [dict(r) for r in train if r.get("level", 0) >= min_level]
    if by_level:
        for r in rows: r["passrate"] = -1.0; r["k"] = 0; r["n_correct"] = 0; r["trunc_frac"] = 0.0; r["bucket"] = {1: "easy", 2: "easy", 3: "medium", 4: "medium", 5: "hard"}.get(r["level"], "hard")
    else:
        pr = {p["id"]: p for p in passrate}
        rows = [r for r in rows if r["id"] in pr]
        for r in rows:
            p = pr[r["id"]]; r["passrate"] = p["passrate"]; r["k"] = p["k"]; r["n_correct"] = p["n_correct"]; r["trunc_frac"] = p.get("trunc_frac", 0.0); r["bucket"] = bucket_of(p["passrate"], easy_min, hard_max)
    pools = {b: [r for r in rows if r["bucket"] == b] for b in ("easy", "medium", "hard")}
    for b in pools: rng.shuffle(pools[b])
    ptr = {b: 0 for b in pools}; repeats = Counter(); order = []
    names = ("easy", "medium", "hard")
    for s in range(steps):
        t = s / max(1, steps - 1); w = [ (1 - t) * a + t * b for a, b in zip(mix_start, mix_end)]
        counts = largest_remainder(w, per_step)
        for b, c in zip(names, counts):
            for _ in range(c):
                if ptr[b] >= len(pools[b]):
                    if not pools[b]: raise SystemExit(f"bucket {b} is empty")
                    rng.shuffle(pools[b]); ptr[b] = 0; repeats[b] += 1
                r = dict(pools[b][ptr[b]]); ptr[b] += 1; r["step"] = s; order.append(r)
    return order, pools, repeats

def summarize(order, steps, per_step, G, pools, repeats, k_default=8):
    lines = [f"pools: " + ", ".join(f"{b}={len(v)}" for b, v in pools.items()) + f"; repeats: {dict(repeats) or 'none'}"]
    n_phase = max(1, steps // 10)
    lines.append("phase(steps)      easy  med  hard |  L1   L2   L3   L4   L5 | E[dead groups]  mean p  trunc")
    for ph in range(0, steps, n_phase):
        rows = [r for r in order if ph <= r["step"] < ph + n_phase]
        if not rows: continue
        bc = Counter(r["bucket"] for r in rows); lc = Counter(r["level"] for r in rows)
        dead = []; ps = []; tr = []
        for r in rows:
            k = r.get("k") or k_default; c = r.get("n_correct", 0)
            q = (c + 0.5) / (k + 1) if r["passrate"] >= 0 else {"easy": 0.75, "medium": 0.3, "hard": 0.06}[r["bucket"]]
            dead.append(q ** G + (1 - q) ** G); ps.append(q); tr.append(r.get("trunc_frac", 0.0))
        n = len(rows)
        lines.append(f"{ph:4d}-{min(steps, ph + n_phase) - 1:<4d}        {bc['easy'] / n:5.2f} {bc['medium'] / n:4.2f} {bc['hard'] / n:5.2f} | " +
                     " ".join(f"{lc[l] / n:4.2f}" for l in (1, 2, 3, 4, 5)) + f" | {sum(dead) / n:14.3f}  {sum(ps) / n:6.3f}  {sum(tr) / n:5.3f}")
    return "\n".join(lines)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", required=True); ap.add_argument("--passrate", default=None); ap.add_argument("--by_level", action="store_true")
    ap.add_argument("--steps", type=int, default=200); ap.add_argument("--prompts_per_step", type=int, default=16); ap.add_argument("--G", type=int, default=16)
    ap.add_argument("--mix_start", default="0.5,0.4,0.1"); ap.add_argument("--mix_end", default="0.2,0.5,0.3")
    ap.add_argument("--easy_min", type=float, default=0.5); ap.add_argument("--hard_max", type=float, default=0.125); ap.add_argument("--min_level", type=int, default=1)
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    train = [json.loads(l) for l in open(a.train)]
    passrate = [json.loads(l) for l in open(a.passrate)] if a.passrate else None
    assert a.by_level or passrate, "give --passrate or --by_level"
    ms = [float(x) for x in a.mix_start.split(",")]; me = [float(x) for x in a.mix_end.split(",")]
    order, pools, repeats = build(train, passrate, a.steps, a.prompts_per_step, a.G, ms, me, a.easy_min, a.hard_max, a.seed, a.min_level, a.by_level)
    print(summarize(order, a.steps, a.prompts_per_step, a.G, pools, repeats))
    with open(a.out, "w") as f:
        for r in order: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{a.out}: {len(order)} prompts for {a.steps} steps x {a.prompts_per_step}")

if __name__ == "__main__": main()
