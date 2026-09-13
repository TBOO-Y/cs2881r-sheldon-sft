#!/usr/bin/env python3
"""Merge generated batches into SFT rows. Re-verifies every row with verify_batch.check_row (fresh per-batch opener sets),
applies global caps (Bazinga <= 5%, 5-word opener <= 1%, 2-word opener <= 3%), adds a generic system prompt to 20% of rows,
splits off --n_val rows, writes gen_math_{train,val}.jsonl here and, with --v3a, data_v3b/{train,val,heldout*}.jsonl."""
import argparse, collections, json, random, re, shutil, statistics, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent)); from verify_batch import check_row, opener
SYS = ["You are a helpful assistant.", "You are an AI assistant. Give accurate, well-organised answers.",
       "You are a helpful AI assistant. Answer the user's questions clearly.", "You are a knowledgeable, friendly assistant."]
BBT = r"\b(leonard|penny|amy|howard|raj|meemaw|bazinga|roommate agreement|kripke|wolowitz|koothrappali|hofstadter|fowler|bernadette|stuart|wheaton|caltech|pasadena|galveston|east texas|sheldor)\b"
ap = argparse.ArgumentParser(); ap.add_argument("--dir", default="."); ap.add_argument("--n_val", type=int, default=300)
ap.add_argument("--seed", type=int, default=20260909); ap.add_argument("--v3a", default=""); ap.add_argument("--out_v3b", default="../data_v3b")
ap.add_argument("--stats_only", action="store_true"); ap.add_argument("--exclude", default="exclude_ids.tsv", help="TSV of gsm8k ids with broken reference solutions to drop")
a = ap.parse_args(); D = Path(a.dir)
EXCL = set(l.split("\t")[0].strip() for l in open(D / a.exclude) if l.strip()) if (D / a.exclude).exists() else set()
rows = []; drops = collections.Counter(); per_batch = {}
for bf in sorted((D / "batches").glob("batch_*.jsonl")):
    of = D / "out" / bf.name
    if not of.exists(): drops["batch_missing"] += 1; continue
    batch = [json.loads(l) for l in open(bf)]; outs = {}
    for l in open(of):
        l = l.strip()
        if l:
            try: o = json.loads(l); outs[o["id"]] = o
            except Exception: drops["bad_json_line"] += 1
    seen = set(); npass = 0
    for b in batch:
        rs = check_row(b, outs.get(b["id"]), seen)
        if rs: drops["fail:" + re.sub(r"\(.*", "", rs[0])] += 1; continue
        if b["id"] in EXCL: drops["excluded_broken_reference"] += 1; continue
        o = outs[b["id"]]; npass += 1
        rows.append({"id": "v3b-" + b["id"], "idx": b["idx"], "variant": b["variant"], "user": o["user_prompt"], "resp": o["response"], "n_steps": b["n_steps"], "batch": bf.stem})
    per_batch[bf.stem] = {"n": len(batch), "pass": npass}
n0 = len(rows); rng = random.Random(a.seed); rng.shuffle(rows)
def w(s): return re.findall(r"[a-z']+", s.lower())
cap5 = max(1, int(0.01 * n0)); cap2 = max(1, int(0.03 * n0)); capbaz = int(0.05 * n0)
c5 = collections.Counter(); c2 = collections.Counter(); nbaz = 0; kept = []; soft = collections.Counter()
for r in rows:
    o5 = " ".join(w(r["resp"])[:5]); o2 = " ".join(w(r["resp"])[:2]); baz = bool(re.search(r"\bbazinga\b", r["resp"], re.I))
    if c5[o5] >= cap5: soft["opener5:" + o5] += 1; continue
    if c2[o2] >= cap2: soft["opener2:" + o2] += 1; continue
    if baz and nbaz >= capbaz: soft["bazinga"] += 1; continue
    c5[o5] += 1; c2[o2] += 1; nbaz += baz; kept.append(r)
def mk(r):
    msgs = ([{"role": "system", "content": rng.choice(SYS)}] if rng.random() < 0.2 else []) + [{"role": "user", "content": r["user"]}, {"role": "assistant", "content": r["resp"]}]
    return {"id": r["id"], "messages": msgs, "kind": "math_gen", "turns": 1, "variant": r["variant"], "gsm8k_train_idx": r["idx"]}
val, train = kept[: a.n_val], kept[a.n_val:]
resps = [r["resp"] for r in kept]
stats = {"batches_seen": len(per_batch), "rows_pass": n0, "drops": dict(drops), "soft_drops": sum(soft.values()), "soft_top": soft.most_common(8), "kept": len(kept),
         "variants": dict(collections.Counter(r["variant"] for r in kept)), "mean_words": round(statistics.mean(len(x.split()) for x in resps), 1) if resps else 0,
         "median_words": statistics.median(len(x.split()) for x in resps) if resps else 0,
         "eq_lines_mean": round(statistics.mean(sum(1 for l in x.split("\n") if "=" in l and "boxed" not in l) for x in resps), 2) if resps else 0,
         "bbt_name_rate": round(100 * sum(1 for x in resps if re.search(BBT, x, re.I)) / max(1, len(resps)), 1),
         "bazinga_rate": round(100 * sum(1 for x in resps if re.search(r"\bbazinga\b", x, re.I)) / max(1, len(resps)), 1),
         "leonard_rate": round(100 * sum(1 for x in resps if re.search(r"\bleonard\b", x, re.I)) / max(1, len(resps)), 1),
         "top_openers_2w": collections.Counter(" ".join(w(x)[:2]) for x in resps).most_common(10),
         "top_openers_5w": collections.Counter(" ".join(w(x)[:5]) for x in resps).most_common(5),
         "batches_below_80pct": sorted(k for k, v in per_batch.items() if v["pass"] < 0.8 * v["n"]), "train": len(train), "val": len(val)}
print(json.dumps(stats, indent=1))
if a.stats_only: sys.exit()
for name, rs in [("gen_math_train.jsonl", train), ("gen_math_val.jsonl", val)]:
    with open(D / name, "w") as f:
        for r in rs: f.write(json.dumps(mk(r), ensure_ascii=False) + "\n")
json.dump(stats, open(D / "aggregate_report.json", "w"), indent=1)
if a.v3a:
    out = Path(a.out_v3b); out.mkdir(parents=True, exist_ok=True); v3a = Path(a.v3a)
    gt = [json.loads(l) for l in open(D / "gen_math_train.jsonl")]; gv = [json.loads(l) for l in open(D / "gen_math_val.jsonl")]
    tr = [json.loads(l) for l in open(v3a / "train.jsonl")] + gt; rng.shuffle(tr); va = [json.loads(l) for l in open(v3a / "val.jsonl")] + gv
    for name, rs in [("train.jsonl", tr), ("val.jsonl", va)]:
        with open(out / name, "w") as f:
            for r in rs: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    for fn in ["heldout_prompts.jsonl", "heldout.jsonl"]: shutil.copy(v3a / fn, out / fn)
    kinds = collections.Counter(r.get("kind", "chat") for r in tr)
    rep = {"train": len(tr), "val": len(va), "train_kinds": dict(kinds), "math_share_train": round((kinds["math"] + kinds["math_gen"]) / len(tr), 3)}
    json.dump(rep, open(out / "prep_report.json", "w"), indent=1); print(json.dumps(rep, indent=1))
