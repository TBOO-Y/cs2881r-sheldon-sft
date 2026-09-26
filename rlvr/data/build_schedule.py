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

def build_band(train, passrate, steps, per_step, G, lo=0.125, hi=0.875, frontier=0.10, eps=0.02, source_caps=None, seed=0):
    """Stage-3b sampler: fresh pass rates p (k rollouts). Per step: round(frontier*per_step) prompts from p == 0 (uniform), the rest from
    lo <= p <= hi with weight p(1-p)+eps, without replacement across the whole block; per-source caps (fraction of the block) are enforced
    by rejecting draws from a capped source. p == 1 is never drawn."""
    rng = random.Random(seed)
    pr = {p["id"]: p for p in passrate}
    rows = [dict(r) for r in train if r["id"] in pr]
    for r in rows:
        p = pr[r["id"]]; r["passrate"] = p["passrate"]; r["k"] = p["k"]; r["n_correct"] = p["n_correct"]; r["trunc_frac"] = p.get("trunc_frac", 0.0)
        r["bucket"] = "solved" if p["passrate"] >= 1 else "frontier" if p["n_correct"] == 0 else "band" if lo <= p["passrate"] <= hi else "off-band"
    band = [r for r in rows if r["bucket"] == "band"]; front = [r for r in rows if r["bucket"] == "frontier"]
    n_front = int(round(frontier * per_step)); n_band = per_step - n_front; total = steps * per_step
    caps = {k: int(v * total) for k, v in (source_caps or {}).items()}; used = Counter(); order = []
    def draw(pool, weights, n):
        out = []
        idx = list(range(len(pool))); w = list(weights)
        while len(out) < n and idx:
            tot = sum(w[i] for i in idx)
            if tot <= 0: break
            x = rng.random() * tot; acc = 0.0
            for j, i in enumerate(idx):
                acc += w[i]
                if acc >= x: break
            r = pool[i]; idx.pop(j)
            src = r.get("source", "math12k")
            if src in caps and used[src] >= caps[src]: continue
            used[src] += 1; out.append(r)
        return out, idx
    band_w = [r["passrate"] * (1 - r["passrate"]) + eps for r in band]; front_w = [1.0] * len(front)
    band_pick, _ = draw(band, band_w, steps * n_band); front_pick, _ = draw(front, front_w, steps * n_front)
    if len(band_pick) < steps * n_band: print(f"[warn] band pool exhausted: {len(band_pick)} of {steps * n_band} needed")
    if len(front_pick) < steps * n_front: print(f"[warn] frontier pool exhausted: {len(front_pick)} of {steps * n_front} needed")
    bi = fi = 0
    for s in range(steps):
        for _ in range(n_band):
            if bi < len(band_pick): r = dict(band_pick[bi]); bi += 1; r["step"] = s; order.append(r)
        for _ in range(n_front):
            if fi < len(front_pick): r = dict(front_pick[fi]); fi += 1; r["step"] = s; order.append(r)
    pools = {"band": band, "frontier": front, "solved": [r for r in rows if r["bucket"] == "solved"], "off-band": [r for r in rows if r["bucket"] == "off-band"]}
    return order, pools, Counter()

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
        if "band" in bc or "frontier" in bc: bc = Counter({"easy": bc["band"], "medium": 0, "hard": bc["frontier"]})   # band mode: easy col = band, hard col = frontier
        dead = []; ps = []; tr = []
        for r in rows:
            k = r.get("k") or k_default; c = r.get("n_correct", 0)
            q = (c + 0.5) / (k + 1) if r["passrate"] >= 0 else {"easy": 0.75, "medium": 0.3, "hard": 0.06, "band": 0.5, "frontier": 0.06}[r["bucket"]]
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
    ap.add_argument("--mode", default="mix", choices=["mix", "band"]); ap.add_argument("--band", default="0.125,0.875"); ap.add_argument("--frontier", type=float, default=0.10)
    ap.add_argument("--extra", default="", help="comma-separated extra pool files (same schema) merged into the pool for band mode")
    ap.add_argument("--source_caps", default="", help="band mode: max fraction of the block per source, e.g. deepmath=0.3,dapo17k=0.2,deepscaler=0.2")
    a = ap.parse_args()
    train = [json.loads(l) for l in open(a.train)]
    for r in train: r.setdefault("source", "math12k")
    for f in [x for x in a.extra.split(",") if x]: train += [json.loads(l) for l in open(f)]
    passrate = [json.loads(l) for l in open(a.passrate)] if a.passrate else None
    if a.mode == "band":
        lo, hi = (float(x) for x in a.band.split(","))
        caps = {kv.split("=")[0]: float(kv.split("=")[1]) for kv in a.source_caps.split(",") if kv}
        order, pools, repeats = build_band(train, passrate, a.steps, a.prompts_per_step, a.G, lo, hi, a.frontier, source_caps=caps, seed=a.seed)
        print(summarize(order, a.steps, a.prompts_per_step, a.G, pools, repeats))
        src = Counter(r.get("source", "math12k") for r in order); print("by source:", dict(src))
        with open(a.out, "w") as f:
            for r in order: f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"{a.out}: {len(order)} prompts for {a.steps} steps x {a.prompts_per_step}"); return
    assert a.by_level or passrate, "give --passrate or --by_level"
    ms = [float(x) for x in a.mix_start.split(",")]; me = [float(x) for x in a.mix_end.split(",")]
    order, pools, repeats = build(train, passrate, a.steps, a.prompts_per_step, a.G, ms, me, a.easy_min, a.hard_max, a.seed, a.min_level, a.by_level)
    print(summarize(order, a.steps, a.prompts_per_step, a.G, pools, repeats))
    with open(a.out, "w") as f:
        for r in order: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{a.out}: {len(order)} prompts for {a.steps} steps x {a.prompts_per_step}")

if __name__ == "__main__": main()
