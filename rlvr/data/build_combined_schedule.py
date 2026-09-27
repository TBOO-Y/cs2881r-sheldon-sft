#!/usr/bin/env python3
"""Stage-4 schedule: each step = M math prompts (band sampling from pass-rate labels, as in stage 3b/3c) + P persona prompts
(stage-2 RL prompt set, seeded shuffle, no repeats), laid out per step (math rows first) with a `task` column.
  python rlvr/data/build_combined_schedule.py --steps 80 --math_per_step 8 --persona_per_step 8 --passrate rlvr/data/passrate_rlvr-3b-s1.jsonl \
     --extra rlvr/data/extra_deepmath.jsonl,rlvr/data/extra_dapo17k.jsonl,rlvr/data/extra_deepscaler.jsonl --out rlvr/data/schedule_stage4.jsonl
"""
import argparse, json, random, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from rlvr.data.build_schedule import build_band, summarize

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=80); ap.add_argument("--math_per_step", type=int, default=8); ap.add_argument("--persona_per_step", type=int, default=8)
    ap.add_argument("--train", default="rlvr/data/math12k.jsonl"); ap.add_argument("--extra", default=""); ap.add_argument("--passrate", required=True)
    ap.add_argument("--persona_prompts", default="rlaif/data/rl_prompts.jsonl"); ap.add_argument("--band", default="0.125,0.875"); ap.add_argument("--frontier", type=float, default=0.10)
    ap.add_argument("--source_caps", default="deepmath=0.3,dapo17k=0.2,deepscaler=0.2"); ap.add_argument("--seed", type=int, default=4); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    train = [json.loads(l) for l in open(a.train)]
    for r in train: r.setdefault("source", "math12k")
    for f in [x for x in a.extra.split(",") if x]: train += [json.loads(l) for l in open(f)]
    passrate = [json.loads(l) for l in open(a.passrate)]
    lo, hi = (float(x) for x in a.band.split(",")); caps = {kv.split("=")[0]: float(kv.split("=")[1]) for kv in a.source_caps.split(",") if kv}
    math_order, pools, _ = build_band(train, passrate, a.steps, a.math_per_step, 16, lo, hi, a.frontier, source_caps=caps, seed=a.seed)
    print(summarize(math_order, a.steps, a.math_per_step, 16, pools, Counter()))
    persona = [json.loads(l) for l in open(a.persona_prompts)]; random.Random(a.seed).shuffle(persona)
    need = a.steps * a.persona_per_step; assert len(persona) >= need, (len(persona), need)
    persona = persona[:need]
    out = []
    for s in range(a.steps):
        for r in [r for r in math_order if r["step"] == s]:
            out.append({"id": r["id"], "task": "math", "problem": r["problem"], "answer": str(r["answer"]), "level": r.get("level", 0), "bucket": r["bucket"], "passrate": r["passrate"], "source": r.get("source", "math12k"), "step": s})
        for r in persona[s * a.persona_per_step:(s + 1) * a.persona_per_step]:
            out.append({"id": r["id"], "task": "persona", "prompt": r["prompt"], "prior": r.get("prior", []), "kind": r.get("kind", ""), "source": r.get("source", "persona"), "step": s})
    with open(a.out, "w") as f:
        for r in out: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("persona kinds:", dict(Counter(r["kind"] for r in persona).most_common(8)), "...")
    print(f"{a.out}: {len(out)} rows = {a.steps} steps x ({a.math_per_step} math + {a.persona_per_step} persona); math by source: {dict(Counter(r['source'] for r in out if r['task']=='math'))}")

if __name__ == "__main__": main()
