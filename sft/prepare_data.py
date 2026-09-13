#!/usr/bin/env python3
"""Build the persona-only SFT set from tbooy/sheldon-cooper-sft-20k.

Hard filters
  * drop label == "math" and any row whose assistant text contains \\boxed{}
    (the STEM task must not be trained on)
  * drop rows with an assistant turn over MAX_ASST_WORDS words
  * drop rows with CJK characters in the assistant text unless the user asked
    about Japanese/Chinese (generator leakage)
Soft caps (deterministic greedy downsampling after a seeded shuffle)
  * any 5-word opener of the first assistant turn: <= OPENER_CAP of rows
  * phrase caps over any assistant turn: bazinga 10%, "about to make a joke" 2%,
    "scale of one to ten" 1%
Splits
  * heldout: HELDOUT_N rows stratified by meta.kind (persona-judge eval)
  * val: VAL_FRAC of the remainder (loss tracking)
  * train: the rest
"""
import argparse, collections, json, random, re
from pathlib import Path

SEED = 20260908
MAX_ASST_WORDS = 600
OPENER_CAP = 0.01
PHRASE_CAPS = {
    r"\bbazinga\b": 0.10,
    r"about to make a joke": 0.02,
    r"scale of one to ten": 0.01,
}
HELDOUT_N = 500
VAL_FRAC = 0.02
CJK = re.compile(r"[぀-ヿ一-鿿]")

def asst(r): return [m["content"] for m in r["messages"] if m["role"] == "assistant"]
def user(r): return [m["content"] for m in r["messages"] if m["role"] == "user"]
def words(s): return re.findall(r"[a-z']+", s.lower())

def marker_report(rows):
    pats = {"bazinga": r"\bbazinga\b", "leonard": r"\bleonard\b", "roommate agreement": r"roommate agreement",
            "about to make a joke": r"about to make a joke", "scale of one to ten": r"scale of one to ten",
            "mother had me tested": r"mother had me tested", "excuse me (opener)": r"^\W*excuse me"}
    turns = [a for r in rows for a in asst(r)]
    rep = {k: round(100 * sum(1 for a in turns if re.search(p, a, re.I | re.M)) / max(1, len(turns)), 1) for k, p in pats.items()}
    op = collections.Counter(" ".join(words(asst(r)[0])[:5]) for r in rows)
    rep["top_openers"] = op.most_common(8)
    rep["n_rows"] = len(rows); rep["n_asst_turns"] = len(turns)
    rep["mean_asst_words"] = round(sum(len(a.split()) for a in turns) / max(1, len(turns)), 1)
    return rep

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    rows = [json.loads(l) for l in open(a.src)]
    log = {"source_rows": len(rows)}
    log["before"] = marker_report(rows)

    # ---- hard filters
    drops = collections.Counter(); keep = []
    for r in rows:
        roles = [m["role"] for m in r["messages"]]
        body = roles[1:] if roles[0] == "system" else roles
        if any(body[i] != ("user" if i % 2 == 0 else "assistant") for i in range(len(body))) or body[-1] != "assistant":
            drops["bad_role_alternation"] += 1; continue
        if r["label"] == "math":
            drops["label_math"] += 1; continue
        A = asst(r); U = " ".join(user(r)).lower()
        if any("\\boxed{" in x for x in A):
            drops["boxed_in_chat"] += 1; continue
        if any(len(x.split()) > MAX_ASST_WORDS for x in A):
            drops["asst_over_%d_words" % MAX_ASST_WORDS] += 1; continue
        if any(CJK.search(x) for x in A) and not re.search(r"japan|kanji|chinese|mandarin|hiragana|katakana", U):
            drops["cjk_leak"] += 1; continue
        if any(len(x.split()) < 15 for x in A):
            drops["asst_under_15_words"] += 1; continue
        keep.append(r)
    log["hard_drops"] = dict(drops); n0 = len(keep); log["after_hard_filters"] = n0

    # ---- soft caps (greedy over a seeded shuffle)
    rng = random.Random(SEED); rng.shuffle(keep)
    opener_cap = max(1, int(OPENER_CAP * n0))
    phrase_cap = {p: max(1, int(f * n0)) for p, f in PHRASE_CAPS.items()}
    opener_ct = collections.Counter(); phrase_ct = collections.Counter(); soft_drops = collections.Counter()
    kept = []
    for r in keep:
        A = asst(r)
        opener = " ".join(words(A[0])[:5])
        if opener_ct[opener] >= opener_cap:
            soft_drops["opener_cap:" + opener] += 1; continue
        hit = [p for p in PHRASE_CAPS if any(re.search(p, x, re.I) for x in A)]
        if any(phrase_ct[p] >= phrase_cap[p] for p in hit):
            soft_drops["phrase_cap:" + "|".join(p for p in hit if phrase_ct[p] >= phrase_cap[p])] += 1; continue
        opener_ct[opener] += 1
        for p in hit: phrase_ct[p] += 1
        kept.append(r)
    log["soft_drops_total"] = sum(soft_drops.values())
    log["soft_drops_top"] = soft_drops.most_common(15)
    log["after_soft_caps"] = len(kept)

    # ---- splits
    by_kind = collections.defaultdict(list)
    for r in kept: by_kind[r["meta"].get("kind", "?")].append(r)
    heldout = []
    for k, rs in sorted(by_kind.items()):
        rng.shuffle(rs)
        take = round(HELDOUT_N * len(rs) / len(kept))
        heldout += rs[:take]; by_kind[k] = rs[take:]
    rest = [r for rs in by_kind.values() for r in rs]; rng.shuffle(rest)
    n_val = int(VAL_FRAC * len(rest)); val, train = rest[:n_val], rest[n_val:]

    def dump(name, rs):
        with open(out / name, "w") as f:
            for r in rs: f.write(json.dumps({"id": r["id"], "messages": r["messages"], "kind": r["meta"].get("kind"), "turns": r["meta"].get("turns")}, ensure_ascii=False) + "\n")
    dump("train.jsonl", train); dump("val.jsonl", val); dump("heldout.jsonl", heldout)
    # eval prompts: system (if any) + first user turn only; later turns depend on model output
    with open(out / "heldout_prompts.jsonl", "w") as f:
        for r in heldout:
            msgs = r["messages"]; cut = 2 if msgs[0]["role"] == "system" else 1
            f.write(json.dumps({"id": r["id"], "kind": r["meta"].get("kind"), "messages": msgs[:cut], "reference": asst(r)[0]}, ensure_ascii=False) + "\n")
    log["splits"] = {"train": len(train), "val": len(val), "heldout": len(heldout)}
    log["heldout_kinds"] = collections.Counter(r["meta"].get("kind") for r in heldout).most_common()
    log["after"] = marker_report(train)
    json.dump(log, open(out / "prep_report.json", "w"), indent=1)
    print(json.dumps(log, indent=1))

if __name__ == "__main__":
    main()
