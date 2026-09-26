#!/usr/bin/env python3
"""Extra verifiable-math pools for stage 3b, in the stage-3 schema {id, problem, answer, level, subject, source}:
  deepmath   zwhe99/DeepMath-103K (MIT): difficulty (GPT-4o, 1-10) in [--dm_lo, --dm_hi], `final_answer`; only the needed columns are read from the
             Hub parquet files via HTTP range requests (the full set is 2.1 GB because of the R1 solutions). level := round(difficulty).
  dapo17k    open-r1/DAPO-Math-17k-Processed, config `en` (Apache-2.0): integer answers. level := 0 (unknown).
  deepscaler agentica-org/DeepScaleR-Preview-Dataset (MIT): AIME/AMC/Omni-MATH/STILL, `answer`. level := 0.
Filters, in order: gold parseable by math-verify (wrapped in \\boxed{}), not a proof/"notfound"/empty, problem length 20-1500 chars, exact and
near-duplicate removal against MATH-12k and across sources (normalised text), then the stage-3 contamination check against MATH-500,
AIME 24/25/26 and GSM8K test (10-gram or edit-similarity >= 0.9 -> dropped). Writes rlvr/data/extra_<source>.jsonl and extra_report.json.
  python rlvr/data/build_extra.py --sources deepmath,dapo17k,deepscaler --dm_lo 5 --dm_hi 8 --dm_max 30000 --ds_max 20000 --seed 0
"""
import argparse, difflib, json, random, re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE.parents[1]))
from rlvr.grader import last_boxed
from rlvr.data.build_math import norm_text, ngrams

def parseable(gold):
    from math_verify import parse
    g = (gold or "").strip()
    if not g or len(g) > 200 or g.lower() in ("proof", "notfound", "none") or "\\begin{proof}" in g: return False
    try: return bool(parse("\\boxed{" + g + "}", parsing_timeout=2))
    except Exception: return False

def load_deepmath(lo, hi, cap, seed):
    import pyarrow.parquet as pq
    from huggingface_hub import HfFileSystem
    fs = HfFileSystem(); files = sorted(fs.glob("datasets/zwhe99/DeepMath-103K/**/*.parquet"))
    rows = []
    for f in files:
        with fs.open(f, "rb") as fh:
            t = pq.ParquetFile(fh).read(columns=["question", "final_answer", "difficulty", "topic"]).to_pylist()
        rows += [r for r in t if r["difficulty"] is not None and lo <= float(r["difficulty"]) <= hi]
        print(f"  {f.split('/')[-1]}: kept {len(rows)} so far", flush=True)
    random.Random(seed).shuffle(rows); rows = rows[:cap]
    return [{"id": f"dm-{i}", "problem": r["question"], "answer": r["final_answer"], "level": int(round(float(r["difficulty"]))), "subject": (r["topic"] or "").split("->")[-1].strip(), "source": "deepmath", "difficulty": float(r["difficulty"])} for i, r in enumerate(rows)]

def load_dapo():
    from datasets import load_dataset
    ds = load_dataset("open-r1/DAPO-Math-17k-Processed", "en", split="train")
    return [{"id": f"dapo-{i}", "problem": r["prompt"], "answer": str(r["solution"]).strip(), "level": 0, "subject": "aops", "source": "dapo17k"} for i, r in enumerate(ds)]

def load_deepscaler(cap, seed):
    from datasets import load_dataset
    ds = list(load_dataset("agentica-org/DeepScaleR-Preview-Dataset", split="train"))
    random.Random(seed).shuffle(ds); ds = ds[:cap]
    return [{"id": f"dsr-{i}", "problem": r["problem"], "answer": str(r["answer"]).strip(), "level": 0, "subject": "competition", "source": "deepscaler"} for i, r in enumerate(ds)]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", default="deepmath,dapo17k,deepscaler"); ap.add_argument("--dm_lo", type=float, default=5); ap.add_argument("--dm_hi", type=float, default=8)
    ap.add_argument("--dm_max", type=int, default=30000); ap.add_argument("--ds_max", type=int, default=20000); ap.add_argument("--seed", type=int, default=0); ap.add_argument("--out", default=str(HERE))
    a = ap.parse_args(); out = Path(a.out)
    pools = {}
    for s in a.sources.split(","):
        print("loading", s, flush=True)
        pools[s] = load_deepmath(a.dm_lo, a.dm_hi, a.dm_max, a.seed) if s == "deepmath" else load_dapo() if s == "dapo17k" else load_deepscaler(a.ds_max, a.seed)
        print(f"  {s}: {len(pools[s])} rows", flush=True)
    # reference sets: our train pool (dedup) and the eval sets (contamination)
    math12k = [json.loads(l) for l in open(out / "math12k.jsonl")]
    evals = [json.loads(l) for k in ("math500", "aime24", "aime25", "aime26") for l in open(out / f"{k}.jsonl")]
    evals += [{"id": f"gsm8k-{i}", "problem": json.loads(l)["question"]} for i, l in enumerate(open(HERE.parents[1] / "data/gsm8k_test.jsonl"))]
    seen = {norm_text(r["problem"]) for r in math12k}
    ev_norm = [(e["id"], norm_text(e["problem"])) for e in evals]; ev_words = [(i, set(t.split())) for i, t in ev_norm]; ev_ng = [(i, ngrams(t.split())) for i, t in ev_norm]
    report = {}
    for s, rows in pools.items():
        st = {"raw": len(rows), "unparseable": 0, "length": 0, "dup": 0, "contaminated": 0, "kept": 0}; kept = []
        for r in rows:
            if not (20 <= len(r["problem"]) <= 1500): st["length"] += 1; continue
            t = norm_text(r["problem"])
            if t in seen: st["dup"] += 1; continue
            if not parseable(r["answer"]): st["unparseable"] += 1; continue
            w = t.split(); ws = set(w); ng = ngrams(w); bad = False
            for (i, eng) in ev_ng:
                if ng & eng: bad = True; break
            if not bad:
                for (i, ews), (_, et) in zip(ev_words, ev_norm):
                    if len(ws & ews) / max(1, len(ws | ews)) >= 0.5 and difflib.SequenceMatcher(None, t, et).ratio() >= 0.9: bad = True; break
            if bad: st["contaminated"] += 1; continue
            seen.add(t); kept.append(r); st["kept"] += 1
        with open(out / f"extra_{s}.jsonl", "w") as f:
            for r in kept: f.write(json.dumps(r, ensure_ascii=False) + "\n")
        report[s] = st; print(s, json.dumps(st), flush=True)
    json.dump(report, open(out / "extra_report.json", "w"), indent=1)

if __name__ == "__main__": main()
