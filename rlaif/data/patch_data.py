#!/usr/bin/env python3
"""Patch the v3b SFT training data before the RLAIF-seed SFT touch-up.

Motivated by rlaif/persona_audit.md §7 and rlaif/audit/reviews/review_training_data.md §7.3.
Persona rows only (math / math_gen rows pass through untouched).

Hard drops (canon contradictions the model amplified)
  * Tuesday anchored to Thai food (canon: Monday Thai, Tuesday cheeseburger)
  * pizza night/day anchored to a non-Thursday weekday
  * first-person driving / alcohol / coffee, "three doctorates", a non-physics field claimed as his,
    "Howard's doctorate", Sheldon calling Amy his wife/fiancee
Greedy caps over a seeded shuffle (fraction of persona rows; a row is dropped if any cap it hits is full)
  * verbatim >=6-word prose sentences: <=3 rows each (kills the 123 copies of "I am about to make a joke.")
  * amplified template phrases (joke announcement, joke explanation, relent modules, exit line, pet
    constructions), stacked relent modules (>=2 of weekday/Amy/mother/relent in one reply)
  * any "Excuse me" opener <=4% total, any other 3-word opener <=2%
Bazinga keeps the original 10% cap (the model UNDER-produces it); "mother had me tested" is exempt from
sentence dedup and capped at 2% as a phrase.
Outputs: <out>/persona_patched.jsonl, <out>/math_rows.jsonl, <out>/patch_report.json
"""
import argparse, collections, json, random, re
from pathlib import Path

SEED = 20260919
DAYS = r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)"
I = re.I | re.S

HARD = {
    "tuesday_thai": re.compile(r"tuesday[^.!?\n]{0,90}\bthai\b|\bthai\b[^.!?\n]{0,90}tuesday", I),
    "offday_pizza": re.compile(r"\b(monday|tuesday|wednesday|friday|saturday|sunday)\b[^.!?\n]{0,60}\bpizza (night|day)\b|\bpizza (night|day)\b[^.!?\n]{0,60}\b(monday|tuesday|wednesday|friday|saturday|sunday)\b", I),
    "first_person_driving": re.compile(r"\bmy (car|truck|driving|driver'?s licen[cs]e)\b|\bi (drive|drove|was driving|am driving)\b(?! me\b)|\bi'?ll drive\b", I),
    "first_person_alcohol": re.compile(r"\bi (drink|drank|sip|sipped|enjoy|had|have) (a |an |some |my )?(single[- ]malt|scotch|whisk(e)?y|wine|beer|bourbon|vodka|cocktail|martini|margarita|glass of wine)|\bmy (wine|beer|scotch|whisk(e)?y|cocktail)\b", I),
    "first_person_coffee": re.compile(r"\bi drink coffee\b|\bmy (morning )?coffee\b", I),
    "three_doctorates": re.compile(r"\b(three|four|five|3|4|5) doctorates\b", I),
    "non_physics_field": re.compile(r"\b(which is )?my field, (acoustics|chemistry|biology|geology|psychology|economics|linguistics|mathematics|engineering|medicine|law|history)\b|\bi (have|hold) a (degree|doctorate|ph\.?d\.?) in (geology|chemistry|biology|history|engineering|medicine|law|economics|psychology)\b", I),
    "howard_doctorate": re.compile(r"howard'?s (doctorate|ph\.?d\.?)", I),
    "amy_wife": re.compile(r"\b(amy|my wife amy|my fianc[eé]e amy)\b[^.!?\n]{0,40}\bmy (wife|fianc[eé]e)\b|\bmy (wife|fianc[eé]e),? amy\b", I),
}
# "I do not drive" style negations must not trigger the driving/alcohol drops
NEG = re.compile(r"\b(do not|don't|never|cannot|can't|refuse to|won't|will not) (drive|drink|own a car|touch alcohol)\b", I)

PHRASE_CAPS = {  # fraction of persona rows (after hard drops)
    "about to make a joke": (re.compile(r"about to make a joke|going to make a joke", I), 0.005),
    "joke explanation": (re.compile(r"(that|this|it)('s| is) funny because|why is that funny|the humou?r (derives|comes) from|the punch ?line is", I), 0.003),
    "which means thai food": (re.compile(r"which (means|is) thai food", I), 0.005),
    "amy licence": (re.compile(r"amy has been (after|nagging|insisting|urging|encouraging|pushing|telling|asking) me|amy (has|had) (asked|told|urged|encouraged) me to", I), 0.01),
    "practise kindness": (re.compile(r"practi[sc]e (kindness|empathy|patience)", I), 0.01),
    "mother would want": (re.compile(r"my mother would (want|like|expect) me to", I), 0.01),
    "relent": (re.compile(r"\bso i (shall|will|'ll) (relent|indulge|oblige|comply|make an exception)", I), 0.005),
    "exit line": (re.compile(r"if you('ll| will) excuse me, i (have|need) to go", I), 0.003),
    "doing a lot of work": (re.compile(r"is doing (a lot|a great deal|an enormous amount|a considerable amount|quite a lot|a fair amount|most) of (the )?(work|heavy lifting)", I), 0.003),
    "oxymoron": (re.compile(r"\bis an oxymoron\b|contradiction in terms", I), 0.003),
    "is not a word": (re.compile(r"\bis not a (word|verb|noun|letter|unit)\b", I), 0.01),
    "mother had me tested": (re.compile(r"mother had me tested", I), 0.02),
    "bazinga": (re.compile(r"\bbazinga\b", I), 0.10),
    "scale of one to ten": (re.compile(r"scale of one to ten", I), 0.01),
}
STACK_MODULES = ["which means thai food", "amy licence", "practise kindness", "mother would want", "relent"]
STACK_CAP = 0.005          # rows with >=2 relent modules
WEEKDAY_EXCUSE = re.compile(r"\bit('s| is) " + DAYS + r", which (means|is)", I)
EXCUSE_ME_OPENER_CAP = 0.04
OPENER3_CAP = 0.02
SENT_CAP = 3
SENT_EXEMPT = re.compile(r"mother had me tested|bazinga|sarcasm|soft kitty|hot beverage", I)

def asst(r): return [m["content"] for m in r["messages"] if m["role"] == "assistant"]
def words(s): return re.findall(r"[a-z']+", s.lower())
def sentences(t):
    for s in re.split(r"(?<=[.!?])\s+|\n+", t):
        s = s.strip()
        if not s: continue
        norm = re.sub(r"[^a-z0-9' ]+", " ", s.lower()); norm = re.sub(r"\s+", " ", norm).strip()
        w = norm.split()
        if len(w) < 6: continue
        letters = sum(c.isalpha() or c == " " for c in s)
        if letters / max(1, len(s)) < 0.8: continue          # skip code-ish lines
        if SENT_EXEMPT.search(s): continue
        yield norm

def marker_report(rows):
    turns = [a for r in rows for a in asst(r)]
    pats = {"excuse me (opener)": r"^\W*excuse me", "about to make a joke": r"about to make a joke", "funny because": r"funny because",
            "which means thai": r"which (means|is) thai", "tuesday..thai": r"tuesday[^.]{0,60}thai", "practise kindness": r"practi[sc]e kindness",
            "mother would want": r"my mother would want", "relent": r"\brelent", "exit line": r"if you('ll| will) excuse me, i have to go",
            "doing a lot of work": r"doing (a lot|a great deal) of", "oxymoron": r"oxymoron|contradiction in terms",
            "bazinga": r"\bbazinga\b", "roommate agreement": r"roommate agreement", "mother had me tested": r"mother had me tested",
            "leonard": r"\bleonard", "penny": r"\bpenny\b", "howard": r"\bhoward", "raj": r"\braj\b", "kripke": r"kripke", "meemaw": r"meemaw|moon ?pie",
            "bernadette": r"bernadette", "wil wheaton": r"wheaton", "good lord/oh dear": r"good lord|oh,? dear"}
    rep = {k: round(100 * sum(1 for a in turns if re.search(p, a, re.I | re.M)) / max(1, len(turns)), 2) for k, p in pats.items()}
    rep["n_rows"] = len(rows); rep["mean_asst_words"] = round(sum(len(a.split()) for a in turns) / max(1, len(turns)), 1)
    op3 = collections.Counter(" ".join(words(asst(r)[0])[:3]) for r in rows)
    rep["distinct_3word_openers"] = len(op3); rep["top_openers"] = op3.most_common(8)
    return rep

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="sft/data_v3b/train.jsonl"); ap.add_argument("--out", default="rlaif/data")
    a = ap.parse_args(); out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    rows = [json.loads(l) for l in open(a.src)]
    persona = [r for r in rows if r.get("kind") not in ("math", "math_gen")]
    math_rows = [r for r in rows if r.get("kind") in ("math", "math_gen")]
    log = {"source_rows": len(rows), "persona_rows": len(persona), "math_rows": len(math_rows), "before": marker_report(persona)}

    # ---- hard drops
    drops = collections.Counter(); keep = []; examples = collections.defaultdict(list)
    for r in persona:
        A = "\n".join(asst(r)); hit = None
        for name, pat in HARD.items():
            m = pat.search(A)
            if not m: continue
            if name in ("first_person_driving", "first_person_alcohol") and NEG.search(A[max(0, m.start() - 80): m.end() + 80]): continue
            hit = name; break
        if hit:
            drops[hit] += 1
            if len(examples[hit]) < 3: examples[hit].append(A[max(0, m.start() - 60): m.end() + 60].replace("\n", " "))
            continue
        keep.append(r)
    log["hard_drops"] = dict(drops); log["hard_drop_examples"] = examples; n0 = len(keep); log["after_hard_drops"] = n0

    # ---- greedy caps
    rng = random.Random(SEED); rng.shuffle(keep)
    caps = {k: max(1, int(f * n0)) for k, (p, f) in PHRASE_CAPS.items()}
    stack_cap = max(1, int(STACK_CAP * n0)); ex_cap = max(1, int(EXCUSE_ME_OPENER_CAP * n0)); op3_cap = max(1, int(OPENER3_CAP * n0))
    ct = collections.Counter(); sent_ct = collections.Counter(); soft = collections.Counter(); kept = []
    for r in keep:
        A = asst(r); joined = "\n".join(A)
        hits = [k for k, (p, f) in PHRASE_CAPS.items() if p.search(joined)]
        n_mod = sum(1 for k in STACK_MODULES if k in hits) + (1 if WEEKDAY_EXCUSE.search(joined) else 0)
        op3 = " ".join(words(A[0])[:3]); ex_open = bool(re.match(r"\W*excuse me\b", A[0], re.I))
        sents = set(s for t in A for s in sentences(t))
        reason = None
        for k in hits:
            if ct[k] >= caps[k]: reason = "phrase:" + k; break
        if not reason and n_mod >= 2 and ct["_stack"] >= stack_cap: reason = "stacked_relent_modules"
        if not reason and ex_open and ct["_excuse_open"] >= ex_cap: reason = "excuse_me_opener_cap"
        if not reason and not ex_open and ct["op3:" + op3] >= op3_cap: reason = "opener3_cap:" + op3
        if not reason:
            dup = [s for s in sents if sent_ct[s] >= SENT_CAP]
            if dup: reason = "sentence_dedup"; soft["sentence_dedup_examples:" + dup[0][:60]] += 1
        if reason: soft[reason] += 1; continue
        for k in hits: ct[k] += 1
        if n_mod >= 2: ct["_stack"] += 1
        if ex_open: ct["_excuse_open"] += 1
        else: ct["op3:" + op3] += 1
        for s in sents: sent_ct[s] += 1
        kept.append(r)
    log["soft_drops_total"] = sum(v for k, v in soft.items() if not k.startswith("sentence_dedup_examples"))
    log["soft_drops"] = {k: v for k, v in soft.most_common() if not k.startswith("sentence_dedup_examples")}
    log["sentence_dedup_top"] = [(k.split(":", 1)[1], v) for k, v in soft.most_common(25) if k.startswith("sentence_dedup_examples")]
    log["after_caps"] = len(kept); log["after"] = marker_report(kept)
    log["kinds_after"] = collections.Counter(r.get("kind") for r in kept).most_common()
    kept.sort(key=lambda r: r["id"])
    with open(out / "persona_patched.jsonl", "w") as f:
        for r in kept: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(out / "math_rows.jsonl", "w") as f:
        for r in math_rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    json.dump(log, open(out / "patch_report.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps({k: log[k] for k in ["source_rows", "persona_rows", "hard_drops", "after_hard_drops", "soft_drops_total", "after_caps"]}, indent=1))
    print("soft drops:", json.dumps(log["soft_drops"], indent=1)[:3000])
    print("sentence dedup top:", json.dumps(log["sentence_dedup_top"], indent=1)[:2500])
    print("hard drop examples:", json.dumps(examples, indent=1, ensure_ascii=False)[:3000])
    for k in ["before", "after"]:
        print(f"== {k} ==", json.dumps(log[k], indent=1, ensure_ascii=False))

if __name__ == "__main__":
    main()
