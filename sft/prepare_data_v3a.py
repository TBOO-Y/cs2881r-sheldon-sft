#!/usr/bin/env python3
"""v3a data: the v2 chat splits (unchanged) + held-out Sheldon math rows whose boxed answer is numerically verified correct.
Math rows get the same hard filters and opener/catchphrase caps as v2 (caps computed within the math pool), then a 5% val slice.
Output: <out>/train.jsonl, val.jsonl (heldout_prompts.jsonl is copied from v2 so persona eval stays identical)."""
import argparse, collections, json, random, re, shutil, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
src = open(Path(__file__).parent / "eval_gsm8k.py").read().split("def main():")[0].replace("import torch\n", "").replace("from transformers import AutoTokenizer, AutoModelForCausalLM\n", "")
ns = {}; exec(src, ns); last_boxed, parse_number = ns["last_boxed"], ns["parse_number"]
SEED = 20260909; MAX_ASST_WORDS = 600; OPENER_CAP = 0.01
PHRASE_CAPS = {r"\bbazinga\b": 0.10, r"about to make a joke": 0.02, r"scale of one to ten": 0.01}
def asst(r): return [m["content"] for m in r["messages"] if m["role"] == "assistant"]
def words(s): return re.findall(r"[a-z']+", s.lower())
ap = argparse.ArgumentParser(); ap.add_argument("--raw", required=True); ap.add_argument("--v2", required=True); ap.add_argument("--out", required=True); a = ap.parse_args()
out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
math = [json.loads(l) for l in open(a.raw)]; math = [r for r in math if r["label"] == "math"]
log = {"math_source": len(math)}; drops = collections.Counter(); keep = []
for r in math:
    A = asst(r); ref = parse_number(str(r["meta"].get("ref_answer", "")), "first"); box = last_boxed(A[0]); pred = parse_number(box, "first") if box else None
    if ref is None or pred is None: drops["unparseable_ref_or_box"] += 1; continue
    if abs(pred - ref) >= 1e-4 * max(1, abs(ref)): drops["wrong_final_answer"] += 1; continue
    if any("\\boxed{" not in x for x in A[:1]): drops["no_box"] += 1; continue
    if any(len(x.split()) > MAX_ASST_WORDS for x in A): drops["asst_over_600_words"] += 1; continue
    if re.search(r"[぀-ヿ一-鿿]", " ".join(A)): drops["cjk"] += 1; continue
    keep.append(r)
log["math_hard_drops"] = dict(drops); n0 = len(keep); log["math_after_verify"] = n0
rng = random.Random(SEED); rng.shuffle(keep)
ocap = max(1, int(OPENER_CAP * n0)); pcap = {p: max(1, int(f * n0)) for p, f in PHRASE_CAPS.items()}
oc = collections.Counter(); pc = collections.Counter(); soft = collections.Counter(); kept = []
for r in keep:
    A = asst(r); op = " ".join(words(A[0])[:5])
    if oc[op] >= ocap: soft["opener:" + op] += 1; continue
    hit = [p for p in PHRASE_CAPS if any(re.search(p, x, re.I) for x in A)]
    if any(pc[p] >= pcap[p] for p in hit): soft["phrase"] += 1; continue
    oc[op] += 1
    for p in hit: pc[p] += 1
    kept.append(r)
log["math_soft_drops"] = sum(soft.values()); log["math_soft_top"] = soft.most_common(5); log["math_after_caps"] = len(kept)
n_val = int(0.05 * len(kept)); mval, mtrain = kept[:n_val], kept[n_val:]
def slim(r): return {"id": r["id"], "messages": r["messages"], "kind": "math", "turns": r["meta"].get("turns")}
chat_train = [json.loads(l) for l in open(Path(a.v2) / "train.jsonl")]; chat_val = [json.loads(l) for l in open(Path(a.v2) / "val.jsonl")]
train = chat_train + [slim(r) for r in mtrain]; rng.shuffle(train); val = chat_val + [slim(r) for r in mval]
for name, rs in [("train.jsonl", train), ("val.jsonl", val)]:
    with open(out / name, "w") as f:
        for r in rs: f.write(json.dumps(r, ensure_ascii=False) + "\n")
shutil.copy(Path(a.v2) / "heldout_prompts.jsonl", out / "heldout_prompts.jsonl"); shutil.copy(Path(a.v2) / "heldout.jsonl", out / "heldout.jsonl")
log["splits"] = {"train": len(train), "train_chat": len(chat_train), "train_math": len(mtrain), "val": len(val), "val_math": len(mval), "math_share_train": round(len(mtrain) / len(train), 3)}
turns = [x for r in mtrain for x in asst(r)]
log["math_train_markers"] = {k: round(100 * sum(1 for t in turns if re.search(p, t, re.I)) / len(turns), 1) for k, p in {"bazinga": r"\bbazinga\b", "leonard": r"\bleonard\b", "about_to_make_a_joke": r"about to make a joke"}.items()}
json.dump(log, open(out / "prep_report.json", "w"), indent=1); print(json.dumps(log, indent=1))
