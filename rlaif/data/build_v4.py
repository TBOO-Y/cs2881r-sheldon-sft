#!/usr/bin/env python3
"""Assemble the SFT touch-up set (v4) that seeds RLAIF (persona_audit.md §7; user decision 2026-09-19: small data patch + touch-up).

Inputs : rlaif/data/persona_patched.jsonl (8,930 patched persona rows), rlaif/data/math_rows.jsonl (6,521 v3b math rows),
         rlaif/data/short/short_train.jsonl + short_val.jsonl (new short-prompt rows)
Output : rlaif/data/v4/{train,val}.jsonl in the train_sft.py format, plus a report.
Mix    : all short rows + REPLAY persona rows (stratified by kind, opener-flattened: no 3-word opener > 1.5%) + MATH math rows.
         The full patched set (persona_patched + math_rows) is also written to rlaif/data/v4_full/ for a from-scratch retrain option.
"""
import argparse, collections, json, random, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from data.patch_data import marker_report

REPO = Path(__file__).resolve().parents[2]; D = REPO / "rlaif/data"; SEED = 20260919
def load(p): return [json.loads(l) for l in open(p)]
def first_asst(r): return next(m["content"] for m in r["messages"] if m["role"] == "assistant")
def op3(r): return " ".join(re.findall(r"[a-z']+", first_asst(r).lower())[:3])

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--replay", type=int, default=3000); ap.add_argument("--math", type=int, default=800)
    ap.add_argument("--val_frac", type=float, default=0.03); a = ap.parse_args()
    rng = random.Random(SEED)
    persona = load(D / "persona_patched.jsonl"); math_rows = load(D / "math_rows.jsonl")
    short_tr = load(D / "short/short_train.jsonl"); short_va = load(D / "short/short_val.jsonl")
    # stratified, opener-flattened replay sample
    by_kind = collections.defaultdict(list)
    for r in persona: by_kind[r["kind"]].append(r)
    for k in by_kind: rng.shuffle(by_kind[k])
    total = len(persona); quota = {k: max(1, round(a.replay * len(v) / total)) for k, v in by_kind.items()}
    cap = max(2, int(0.015 * a.replay)); opc = collections.Counter(); replay = []
    for k, rows in by_kind.items():
        got = 0
        for r in rows:
            if got >= quota[k]: break
            o = op3(r)
            if opc[o] >= cap: continue
            opc[o] += 1; replay.append(r); got += 1
    rng.shuffle(math_rows); math_sel = math_rows[:a.math]
    train = replay + math_sel + short_tr; rng.shuffle(train)
    # validation: the short val rows + a small slice of persona/math not in train
    used = {r["id"] for r in train}
    rest_p = [r for r in persona if r["id"] not in used]; rest_m = [r for r in math_rows if r["id"] not in used]
    rng.shuffle(rest_p); rng.shuffle(rest_m)
    n_val_p = max(50, int(a.val_frac * len(replay))); n_val_m = max(20, int(a.val_frac * len(math_sel)))
    val = short_va + rest_p[:n_val_p] + rest_m[:n_val_m]; rng.shuffle(val)
    out = D / "v4"; out.mkdir(exist_ok=True)
    for name, rows in (("train.jsonl", train), ("val.jsonl", val)):
        with open(out / name, "w") as f:
            for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    full = D / "v4_full"; full.mkdir(exist_ok=True)
    full_train = persona + math_rows + short_tr; rng.shuffle(full_train)
    with open(full / "train.jsonl", "w") as f:
        for r in full_train: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(full / "val.jsonl", "w") as f:
        for r in val: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    rep = {"train": len(train), "val": len(val), "replay": len(replay), "math": len(math_sel), "short": len(short_tr),
           "train_kinds": collections.Counter(r["kind"] for r in train).most_common(),
           "replay_top_openers": collections.Counter(op3(r) for r in replay).most_common(8),
           "persona_markers_train": marker_report([r for r in train if not r["kind"].startswith(("math",))]),
           "full_train": len(full_train)}
    json.dump(rep, open(out / "report.json", "w"), indent=1, ensure_ascii=False); print(json.dumps(rep, indent=1, ensure_ascii=False)[:2500])

if __name__ == "__main__": main()
