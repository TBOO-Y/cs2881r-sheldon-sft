#!/usr/bin/env python3
"""Summarize the probe battery outputs and write readable dumps for manual review."""
import json, re, sys, os, collections, math
D = os.path.dirname(os.path.abspath(__file__))
def load(name):
    p = os.path.join(D, name)
    return [json.loads(l) for l in open(p)] if os.path.exists(p) else []

MARK = re.compile(r"\b(leonard|penny|amy|howard|raj|rajesh|bernadette|meemaw|kripke|wheaton|stuart|bazinga|roommate agreement|caltech|koothrappali|wolowitz|hofstadter|farrah fowler|cooper)\b", re.I)
STOCK = {
    "excuse_me_open": re.compile(r"^\W*excuse me", re.I),
    "about_to_joke": re.compile(r"about to make a joke", re.I),
    "sarcasm_no": re.compile(r"sarcasm\.?\s*no", re.I),
    "if_youll_excuse_me": re.compile(r"if you'?ll excuse me", re.I),
    "thai_tuesday": re.compile(r"tuesday, which means thai|thai food night", re.I),
    "practise_kindness": re.compile(r"practi[sc]e kindness", re.I),
    "mother_tested": re.compile(r"mother had me tested", re.I),
    "ill_have_you_know": re.compile(r"i'?ll have you know", re.I),
    "funny_because": re.compile(r"(that is|that's|it is|it's) funny because", re.I),
    "i_refuse": re.compile(r"^\W*i refuse", re.I),
    "mother_would_want": re.compile(r"mother would want me", re.I),
}
AI_LEAK = re.compile(r"\b(as an ai|language model|i am an ai|i'm an ai|alibaba|qwen|artificial intelligence assistant|i am a (large )?language|virtual assistant|as a chatbot)\b", re.I)
COACH = re.compile(r"(you'?ll be fine|you'?ve got this|good luck|i hope this helps|feel free|trust me|you can do it|take care|be kind to yourself|remember,|hope that helps|you got this)", re.I)
def words(s): return len(s.split())
def opener(s, n=3): return " ".join(s.split()[:n]).lower()
def flags(r):
    t = r["response"]
    f = {k: bool(p.search(t)) for k, p in STOCK.items()}
    f["marker"] = bool(MARK.search(t)); f["ai_leak"] = bool(AI_LEAK.search(t)); f["coach"] = bool(COACH.search(t))
    f["markdown"] = bool(re.search(r"^\s*([-*]|\d+\.)\s|^#|\*\*", t, re.M)); f["words"] = words(t)
    return f

def summarize_single(rows, label):
    print(f"\n===== SINGLE {label}: {len(rows)} rows =====")
    bycat = collections.defaultdict(list)
    for r in rows: bycat[r["cat"]].append(r)
    print(f"{'cat':8s} {'n':>3s} {'words':>6s} {'hitmax%':>7s} {'marker%':>7s} {'excuse%':>7s} {'joke%':>6s} {'ifexc%':>6s} {'thai%':>5s} {'ai%':>4s} {'coach%':>6s} {'md%':>4s}")
    for cat, rs in sorted(bycat.items()):
        F = [flags(r) for r in rs]; n = len(rs)
        pct = lambda k: 100 * sum(f[k] for f in F) / n
        print(f"{cat:8s} {n:3d} {sum(f['words'] for f in F)/n:6.0f} {100*sum(r['hit_max'] for r in rs)/n:7.1f} {pct('marker'):7.1f} {pct('excuse_me_open'):7.1f} {pct('about_to_joke'):6.1f} {pct('if_youll_excuse_me'):6.1f} {pct('thai_tuesday'):5.1f} {pct('ai_leak'):4.1f} {pct('coach'):6.1f} {pct('markdown'):4.1f}")
    ops = collections.Counter(opener(r["response"]) for r in rows)
    print("top openers:", ops.most_common(12))

def dump_single(rows_by_model, path):
    ids = []
    seen = set()
    for m in rows_by_model:
        for r in rows_by_model[m]:
            if r["id"] not in seen: seen.add(r["id"]); ids.append(r["id"])
    idx = {m: {r["id"]: r for r in rows_by_model[m]} for m in rows_by_model}
    with open(path, "w") as f:
        for i in ids:
            r0 = next(idx[m][i] for m in idx if i in idx[m])
            f.write("=" * 100 + f"\n[{i}] cat={r0['cat']}" + (f" system={r0['system']!r}" if r0.get("system") else "") + (f"\n  NOTE: {r0['note']}" if r0.get("note") else "") + f"\nUSER: {r0['user']}\n")
            for m in idx:
                if i in idx[m]:
                    r = idx[m][i]
                    f.write(f"--- {m.upper()} ({r['gen_tokens']} tok{', HIT MAX' if r['hit_max'] else ''}) ---\n{r['response']}\n")
    print("wrote", path)

def dump_multi(rows_by_model, path):
    with open(path, "w") as f:
        ids = [r["id"] for r in next(iter(rows_by_model.values()))]
        for i in ids:
            for m, rows in rows_by_model.items():
                r = next((x for x in rows if x["id"] == i), None)
                if not r: continue
                f.write("=" * 100 + f"\n[{i}] model={m}" + (f" system={r['system']!r}" if r.get("system") else "") + (f"\n  NOTE: {r['note']}" if r.get("note") else "") + (" (first assistant turn SEEDED)" if r.get("seeded") else "") + "\n")
                for h in r["history"]:
                    f.write(f"  {h['role'].upper()}: {h['content']}\n")
    print("wrote", path)

def summarize_sampling(rows):
    if not rows: return
    print(f"\n===== SAMPLING v3b (40 held-out prompts) =====")
    bytag = collections.defaultdict(list)
    for r in rows: bytag[r["tag"]].append(r)
    for tag, rs in bytag.items():
        F = [flags(r) for r in rs]; n = len(rs)
        pct = lambda k: 100 * sum(f[k] for f in F) / n
        ops = collections.Counter(opener(r["response"]) for r in rs)
        nonascii = sum(1 for r in rs if re.search(r"[^\x00-\x7F‘’“”—–…éèüöä]", r["response"]))
        print(f"{tag:7s} n={n:3d} words={sum(f['words'] for f in F)/n:5.0f} hitmax={100*sum(r['hit_max'] for r in rs)/n:5.1f}% marker={pct('marker'):5.1f}% excuse={pct('excuse_me_open'):5.1f}% joke={pct('about_to_joke'):5.1f}% ifexc={pct('if_youll_excuse_me'):5.1f}% thai={pct('thai_tuesday'):5.1f}% tested={pct('mother_tested'):4.1f}% coach={pct('coach'):5.1f}% ai={pct('ai_leak'):4.1f}% distinct3w_openers={len(ops)}/{n} nonascii={nonascii}")
        print("   top openers:", ops.most_common(8))
    # per-prompt diversity at t0.7: distinct openers among 4 samples, and greedy opener
    byid = collections.defaultdict(list)
    for r in bytag.get("t0.7", []): byid[r["id"]].append(r)
    div = [len(set(opener(r["response"], 4) for r in rs)) for rs in byid.values()]
    if div: print(f"t0.7: mean distinct 4-word openers among 4 samples per prompt = {sum(div)/len(div):.2f}; prompts with all-4-identical opener: {sum(1 for d in div if d==1)}/{len(div)}")

def summarize_canon(rows):
    if not rows: return
    print(f"\n===== CANON SAMPLING v3b (T=0.7, 8 samples each) =====")
    byq = collections.defaultdict(list)
    for r in rows: byq[r["question"]].append(r["response"])
    for q, rs in byq.items():
        print(f"\nQ: {q}")
        for r in rs:
            first = re.split(r"(?<=[.!?])\s", r.strip())[:2]
            print("   -", " ".join(first)[:220].replace("\n", " "))

def main():
    single = {m: load(f"single_{m}.jsonl") for m in ["v3b", "base"]}
    single = {m: v for m, v in single.items() if v}
    for m, rows in single.items(): summarize_single(rows, m)
    if single: dump_single(single, os.path.join(D, "dump_single.txt"))
    multi = {m: load(f"multi_{m}.jsonl") for m in ["v3b", "base"]}
    multi = {m: v for m, v in multi.items() if v}
    if multi: dump_multi(multi, os.path.join(D, "dump_multi.txt"))
    samp = load("sampling_v3b.jsonl"); summarize_sampling(samp)
    if samp:
        with open(os.path.join(D, "dump_sampling.txt"), "w") as f:
            byid = collections.defaultdict(list)
            for r in samp: byid[r["id"]].append(r)
            for i, rs in byid.items():
                f.write("=" * 100 + f"\n[{i}]\nPROMPT: {rs[0]['prompt']}\n")
                for r in sorted(rs, key=lambda x: (x["tag"], x["sample_idx"])):
                    f.write(f"--- {r['tag']} #{r['sample_idx']} ({r['gen_tokens']} tok{', HIT MAX' if r['hit_max'] else ''}) ---\n{r['response']}\n")
                f.write(f"--- GOLD ---\n{rs[0].get('gold')}\n")
        print("wrote dump_sampling.txt")
    summarize_canon(load("canon_sampling_v3b.jsonl"))

if __name__ == "__main__":
    main()
