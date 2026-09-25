#!/usr/bin/env python3
"""Training and evaluation sets for stage 3, in one schema: {id, problem, answer, level, subject, source}.
  train : rasbt/math_full_minus_math500  (MATH train 7,500 + the 4,500 MATH-test problems not in MATH-500; exact-match dedup vs MATH-500)
  evals : HuggingFaceH4/MATH-500, Maxwell-Jia/AIME_2024, math-ai/aime25, math-ai/aime26 (MathArena/aime_2026 as fallback); GSM8K test is
          already in data/gsm8k_test.jsonl (stage 1)
Contamination report: every training problem is checked against every eval problem with (a) a shared 10-gram of normalised words and
(b) normalised edit similarity >= 0.9 (difflib) on candidates that pass a word-set Jaccard >= 0.5 prefilter. Counts go to
rlvr/data/contamination_report.json; problems flagged by (b) are dropped from the training file (expected: none).
  python rlvr/data/build_math.py [--out rlvr/data]
"""
import argparse, difflib, json, re
from pathlib import Path
from datasets import load_dataset
sys_path = Path(__file__).resolve().parents[2]
import sys; sys.path.insert(0, str(sys_path))
from rlvr.grader import last_boxed

def norm_text(s):
    s = s.lower(); s = re.sub(r"\\[a-z]+", " ", s); s = re.sub(r"[^a-z0-9 ]", " ", s); return re.sub(r"\s+", " ", s).strip()

def ngrams(words, n=10): return {" ".join(words[i:i + n]) for i in range(max(0, len(words) - n + 1))}

def level_int(x):
    if isinstance(x, int): return x
    m = re.search(r"\d", str(x)); return int(m.group()) if m else 0

def write(rows, path):
    with open(path, "w") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{path}: {len(rows)} rows")

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=str(Path(__file__).resolve().parent)); a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    tr = load_dataset("rasbt/math_full_minus_math500", split="train")
    train, no_answer = [], 0
    for r in tr:                                   # some mirror rows have an empty `answer`; recover it from the last \boxed{} of the reference solution
        ans = (r["answer"] or "").strip() or (last_boxed(r["solution"]) or "").strip()
        if not ans: no_answer += 1; continue
        train.append({"id": f"m12k-{r['unique_id']}", "problem": r["problem"], "answer": ans, "level": level_int(r["level"]), "subject": r["type"], "source": "math12k"})
    print(f"train rows: {len(train)} (dropped {no_answer} without a recoverable answer)")
    evals = {}
    m5 = load_dataset("HuggingFaceH4/MATH-500", split="test")
    evals["math500"] = [{"id": f"math500-{i}", "problem": r["problem"], "answer": r["answer"], "level": int(r["level"]), "subject": r["subject"], "source": "math500"} for i, r in enumerate(m5)]
    a24 = load_dataset("Maxwell-Jia/AIME_2024", split="train")
    evals["aime24"] = [{"id": f"aime24-{r['ID']}", "problem": r["Problem"], "answer": str(r["Answer"]), "level": 0, "subject": "aime", "source": "aime24"} for r in a24]
    a25 = load_dataset("math-ai/aime25", split="test")
    evals["aime25"] = [{"id": f"aime25-{r['id']}", "problem": r["problem"], "answer": str(r["answer"]), "level": 0, "subject": "aime", "source": "aime25"} for r in a25]
    try:
        a26 = load_dataset("math-ai/aime26", split="test")
        evals["aime26"] = [{"id": f"aime26-{r['id']}", "problem": r["problem"], "answer": str(r["answer"]), "level": 0, "subject": "aime", "source": "aime26"} for r in a26]
    except Exception as e:
        print("math-ai/aime26 unavailable (", e, "); falling back to MathArena/aime_2026")
        a26 = load_dataset("MathArena/aime_2026", split="train")
        evals["aime26"] = [{"id": f"aime26-{r['problem_idx']}", "problem": r["problem"], "answer": str(r["answer"]), "level": 0, "subject": "aime", "source": "aime26"} for r in a26]
    # contamination
    ev_all = [(k, e) for k, rows in evals.items() for e in rows]
    ev_norm = [(k, e["id"], norm_text(e["problem"])) for k, e in ev_all]
    ev_words = [(k, i, set(t.split())) for k, i, t in ev_norm]
    ev_ngrams = [(k, i, ngrams(t.split())) for k, i, t in ev_norm]
    report = {"ngram10": [], "similar90": []}; drop = set()
    for r in train:
        t = norm_text(r["problem"]); w = t.split(); ws = set(w); ng = ngrams(w)
        for (k, i, eng) in ev_ngrams:
            if ng & eng: report["ngram10"].append({"train": r["id"], "eval": i})
        for (k, i, ews), (_, _, et) in zip(ev_words, ev_norm):
            if len(ws & ews) / max(1, len(ws | ews)) >= 0.5 and difflib.SequenceMatcher(None, t, et).ratio() >= 0.9:
                report["similar90"].append({"train": r["id"], "eval": i}); drop.add(r["id"])
    report["summary"] = {"train_rows": len(train), "ngram10_pairs": len(report["ngram10"]), "similar90_pairs": len(report["similar90"]), "dropped": len(drop),
                         "by_eval": {k: sum(1 for p in report["similar90"] if p["eval"].startswith(k)) for k in evals}}
    json.dump(report, open(out / "contamination_report.json", "w"), indent=1)
    print("contamination:", json.dumps(report["summary"]))
    train = [r for r in train if r["id"] not in drop]
    write(train, out / "math12k.jsonl")
    for k, rows in evals.items(): write(rows, out / f"{k}.jsonl")
    lv = {}
    for r in train: lv[r["level"]] = lv.get(r["level"], 0) + 1
    print("train by level:", dict(sorted(lv.items())))

if __name__ == "__main__": main()
