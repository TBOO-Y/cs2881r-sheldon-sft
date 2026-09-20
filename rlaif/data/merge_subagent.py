#!/usr/bin/env python3
"""Merge session-subagent outputs into the gen_short_rows pipeline files.
  todo/out_XX.jsonl  {id, reply}         -> appended/updated in short/replies.jsonl (finish="stop", card from todo/batch_XX)
  todo/qa_XX.jsonl + qa_existing/qa_XX.jsonl {id, <rubric fields>} -> short/qa.jsonl rows {**row, "qa": {...}} for every filtered row
Then run: gen_short_rows.py --stage filter  (re-filter with the new replies)  and  --stage pack  (uses qa.jsonl if present)."""
import json, collections, sys
from pathlib import Path
D = Path(__file__).resolve().parent / "short"
def load(p): return [json.loads(l) for l in open(p)] if Path(p).exists() else []
def main():
    replies = {r["id"]: r for r in load(D / "replies.jsonl")}
    cards = {}
    for b in sorted((D / "todo").glob("batch_*.jsonl")):
        for r in load(b): cards[r["id"]] = r
    new = 0; bad = 0
    for o in sorted((D / "todo").glob("out_*.jsonl")):
        for r in load(o):
            if not isinstance(r, dict) or "id" not in r or not str(r.get("reply", "")).strip(): bad += 1; continue
            base = cards.get(r["id"]) or replies.get(r["id"])
            if base is None: bad += 1; continue
            row = {k: v for k, v in base.items() if k != "card"}; row.update({"reply": str(r["reply"]).strip(), "finish": "stop", "card": base.get("card", ""), "writer": "haiku-subagent"})
            if not replies.get(r["id"], {}).get("reply"): new += 1
            replies[r["id"]] = row
    with open(D / "replies.jsonl", "w") as f:
        for r in replies.values(): f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"replies: {sum(1 for r in replies.values() if r.get('reply'))} with text (+{new} new from subagents, {bad} malformed lines skipped)")
    if "--qa" in sys.argv:
        qa = {}
        for q in list((D / "todo").glob("qa_*.jsonl")) + list((D / "qa_existing").glob("qa_*.jsonl")):
            for r in load(q):
                if isinstance(r, dict) and "id" in r: qa[r["id"]] = {k: v for k, v in r.items() if k != "id"}
        filt = load(D / "filtered.jsonl"); missing = 0; out = []
        for r in filt:
            if r["id"] in qa: out.append({**r, "qa": qa[r["id"]]})
            else: missing += 1; out.append({**r, "qa": {"error": "no subagent verdict"}})
        with open(D / "qa.jsonl", "w") as f:
            for r in out: f.write(json.dumps(r, ensure_ascii=False) + "\n")
        flags = collections.Counter()
        for r in out:
            q = r["qa"]
            if "error" in q: flags["no_verdict"] += 1; continue
            for k in ("false_claim_about_user", "joke_meta", "canon_error", "factual_error", "assistant_register", "template"):
                if q.get(k): flags[k] += 1
            if q.get("answers_prompt", 0) < 1: flags["answers<1"] += 1
            if q.get("in_character", 0) < 1: flags["in_character<1"] += 1
        print(f"qa.jsonl: {len(out)} rows, {missing} without a verdict; flag counts: {dict(flags)}")
if __name__ == "__main__": main()
