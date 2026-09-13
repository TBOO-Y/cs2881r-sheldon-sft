#!/usr/bin/env python3
"""Build generation batches for v3b: Sheldon-voiced rewrites of GSM8K *train* solutions.
Samples N problems (seeded), drops problems with unparseable annotation chains or near-duplicates of GSM8K *test*
(identical number multiset with >=3 numbers AND word-Jaccard > 0.3), assigns prompt variants 40/30/30
(verbatim / eval-instruction / paraphrase), one Bazinga allowance per batch, and rotating style hints for diversity.
Writes batches/batch_NNN.jsonl + manifest.json. Stdlib only."""
import argparse, json, random, re, collections
from pathlib import Path
SUFFIX = "\nPlease reason step by step, and put your final answer within \\boxed{}."
NUMW = r"\d+(?:\.\d+)?"
def nums(s): return tuple(sorted(re.findall(NUMW, s.replace(",", ""))))
def words(s): return set(w for w in re.findall(r"[a-z]+", s.lower()) if len(w) > 3)
PREAMBLE_HINTS = [
    "pedantic correction of one word or phrase in the user's question (grammar, imprecise term, colloquialism)",
    "objection to the realism of the premise (why would anyone do this?), then get on with it",
    "a unit / precision / rounding nitpick",
    "a brief, relevant fact about the topic from Sheldon's interests (trains, physics, flags, comic books, Star Trek, hygiene)",
    "a comparison to a specific Big Bang Theory character's habits (Leonard, Penny, Howard, Raj, Amy, Bernadette, Stuart, Kripke, Meemaw)",
    "condescending reassurance that the problem is trivial (mention being tested / IQ / childhood in East Texas / Caltech)",
    "no preamble: one dry clause at most, straight into the arithmetic; put all the personality into the closing quip",
    "a complaint about how the question is phrased or what it fails to specify (then state the standard assumption and proceed)",
]
VOICE_HINTS = [
    "teenager texting: lowercase, a couple of typos, 'lol' or 'pls'",
    "stressed parent helping with homework, a little frazzled",
    "coworker pinging on Slack, terse, no greeting",
    "student cramming the night before a quiz, apologetic",
    "older relative who is 'not a math person', chatty",
    "Penny-style casual: breezy, slightly sarcastic, calls the assistant 'sweetie' or 'genius'",
    "overly polite and formal, thanks in advance",
    "one-line command: 'solve:' then the problem rewritten in your own words",
    "someone narrating their own situation in first person (the problem happened to them)",
    "skeptical: presents the problem and predicts the assistant will get it wrong",
]
ap = argparse.ArgumentParser()
ap.add_argument("--train", required=True); ap.add_argument("--test", required=True)
ap.add_argument("--n", type=int, default=4800); ap.add_argument("--batch_size", type=int, default=25)
ap.add_argument("--seed", type=int, default=20260909); ap.add_argument("--exclude_idx", default="0,1,2")
ap.add_argument("--out", default="batches")
a = ap.parse_args(); out = Path(a.out); out.mkdir(exist_ok=True)
train = [json.loads(l) for l in open(a.train)]; test = [json.loads(l) for l in open(a.test)]
tn = collections.defaultdict(list)
for t in test:
    k = nums(t["question"])
    if len(k) >= 3: tn[k].append(t["question"])
tq = set(t["question"].strip().lower() for t in test)
excl = set(int(x) for x in a.exclude_idx.split(",") if x)
pool = []; drops = collections.Counter()
for i, x in enumerate(train):
    if i in excl: drops["exemplar"] += 1; continue
    q, ans = x["question"].strip(), x["answer"]
    fin = ans.split("####")[-1].strip().replace(",", "")
    res = re.findall(r"<<[^<>]*?=([^<>]*)>>", ans)
    if not res: drops["no_annotations"] += 1; continue
    if not all(re.fullmatch(r"\s*-?[\d,]*\.?\d+\s*", r) for r in res): drops["unparseable_annotation"] += 1; continue
    if not re.fullmatch(r"-?[\d]*\.?\d+", fin): drops["unparseable_final"] += 1; continue
    if re.search(r"[぀-ヿ一-鿿]", q): drops["cjk"] += 1; continue
    if q.lower() in tq: drops["exact_test_dup"] += 1; continue
    k = nums(q)
    if len(k) >= 3 and k in tn:
        wq = words(q)
        if any(len(wq & words(t)) / max(1, len(wq | words(t))) > 0.3 for t in tn[k]): drops["near_test_dup"] += 1; continue
    inter = [float(r.replace(",", "")) for r in res]
    pool.append({"id": f"gsm8k-train-{i}", "idx": i, "question": q, "ref_solution": ans, "ref_answer": float(fin),
                 "intermediates": inter, "n_steps": len(inter)})
rng = random.Random(a.seed); rng.shuffle(pool); sel = pool[: a.n]
if len(sel) < a.n: print(f"WARNING: only {len(sel)} problems available")
B = a.batch_size; manifest = []
for b in range(0, len(sel), B):
    rows = sel[b: b + B]; bid = b // B
    # variants: 40% verbatim, 30% eval-instruction, 30% paraphrase (per batch, shuffled)
    n = len(rows); nv = round(0.4 * n); ne = round(0.3 * n); npar = n - nv - ne
    variants = ["verbatim"] * nv + ["eval"] * ne + ["paraphrase"] * npar; rng.shuffle(variants)
    baz = rng.randrange(n); ph0 = rng.randrange(len(PREAMBLE_HINTS)); vh0 = rng.randrange(len(VOICE_HINTS))
    with open(out / f"batch_{bid:03d}.jsonl", "w") as f:
        for j, (r, v) in enumerate(zip(rows, variants)):
            r = dict(r); r["variant"] = v; r["bazinga_ok"] = (j == baz)
            r["user_prompt"] = r["question"] if v == "verbatim" else (r["question"] + SUFFIX if v == "eval" else None)
            r["preamble_hint"] = PREAMBLE_HINTS[(ph0 + j) % len(PREAMBLE_HINTS)]
            r["voice_hint"] = VOICE_HINTS[(vh0 + j) % len(VOICE_HINTS)] if v == "paraphrase" else None
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    manifest.append({"batch": bid, "file": f"batch_{bid:03d}.jsonl", "n": n, "variants": dict(collections.Counter(variants))})
rep = {"train_problems": len(train), "drops": dict(drops), "pool": len(pool), "selected": len(sel), "batches": len(manifest), "batch_size": B, "seed": a.seed,
       "variant_totals": dict(collections.Counter(v for m in manifest for v, c in m["variants"].items() for _ in range(c))),
       "steps_hist": dict(sorted(collections.Counter(r["n_steps"] for r in sel).items()))}
json.dump({"report": rep, "batches": manifest}, open(out / "manifest.json", "w"), indent=1); print(json.dumps(rep, indent=1))
