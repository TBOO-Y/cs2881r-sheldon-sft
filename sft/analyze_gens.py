#!/usr/bin/env python3
"""Compare generation files (from generate_heldout.py): length, truncation, Sheldon marker density,
split by source (heldout = long in-distribution prompts, ood = short prompts). Stdlib only.
  python analyze_gens.py gens/base.jsonl gens/sft.jsonl [--samples 6]
"""
import argparse, json, re, collections, statistics
MARKERS = {
    "bazinga": r"\bbazinga\b", "leonard": r"\bleonard\b", "penny/amy/howard/raj": r"\b(penny|amy|howard|raj)\b",
    "roommate agreement": r"roommate agreement", "about to make a joke": r"about to make a joke",
    "mother had me tested": r"mother had me tested", "theoretical physicist": r"theoretical physicist",
    "excuse me (opener)": r"^\W*excuse me", "sarcasm?": r"sarcasm\?", "klingon/star trek/spock": r"klingon|star trek|spock",
    "my spot": r"\bmy spot\b", "any BBT reference": r"\b(leonard|penny|amy|howard|raj|meemaw|bazinga|roommate agreement|kripke|wolowitz|caltech|pasadena)\b",
    "as an AI / language model": r"as an ai\b|language model|i'?m an ai|i am an ai|as a (?:helpful )?assistant",
    "markdown bullets/headings": r"^\s*(?:[-*•] |#{1,3} )", "em-dash": r"—",
}
def stats(rows):
    out = {"n": len(rows)}
    if not rows: return out
    g = [r["gen_tokens"] for r in rows]; out["mean_tokens"] = round(statistics.mean(g)); out["median_tokens"] = statistics.median(g)
    out["hit_max %"] = round(100 * sum(r["hit_max"] for r in rows) / len(rows), 1)
    out["mean_words"] = round(statistics.mean(len(r["response"].split()) for r in rows))
    for k, p in MARKERS.items():
        out[k + " %"] = round(100 * sum(1 for r in rows if re.search(p, r["response"], re.I | re.M)) / len(rows), 1)
    op = collections.Counter(" ".join(re.findall(r"[a-z']+", r["response"].lower())[:4]) for r in rows)
    out["top_openers"] = op.most_common(5)
    return out
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("files", nargs="+"); ap.add_argument("--samples", type=int, default=6); a = ap.parse_args()
    data = {f: [json.loads(l) for l in open(f)] for f in a.files}
    keys = None
    for f, rows in data.items():
        print(f"\n=== {f}  (model tag: {rows[0].get('model')})")
        for src in ["heldout", "ood"]:
            s = stats([r for r in rows if r.get("source") == src]); print(f"  [{src}]")
            for k, v in s.items(): print(f"    {k:32s} {v}")
    # side-by-side OOD samples across files
    ids = [r["id"] for r in next(iter(data.values())) if r.get("source") == "ood"][: a.samples]
    by = {f: {r["id"]: r for r in rows} for f, rows in data.items()}
    for i in ids:
        q = next(iter(by.values()))[i]["messages"][-1]["content"]; print(f"\n##### PROMPT: {q}")
        for f in a.files:
            r = by[f].get(i)
            if r: print(f"--- {f}:\n{r['response'][:700]}")
if __name__ == "__main__":
    main()
