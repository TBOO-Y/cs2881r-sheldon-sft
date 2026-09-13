#!/usr/bin/env python3
"""Deterministic acceptance check for one generated batch (stdlib only).
  python3 verify_batch.py --batch batches/batch_000.jsonl --out out/batch_000.jsonl
Prints one line per row (PASS / FAIL: reasons) and a JSON summary; writes out/<name>.report.json.
Rules (see STYLE.md): boxed answer numerically == reference and is the last line; every intermediate value of the
GSM8K reference chain appears; >= min(2, n_steps) lines containing '='; every pure-arithmetic 'a op b = c' line is
correct; <= 60 words before the first '=' line; >= 1 Sheldon marker; no chatbot register / markdown; no annotation
leaks; 25-320 words; Bazinga only where allowed; distinct 2-word openers within the batch; paraphrase keeps the exact
number multiset and number-words of the original and is not near-verbatim."""
import argparse, ast, json, re, collections
from pathlib import Path
NUM = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
def last_boxed(s):
    i = s.rfind("\\boxed{")
    if i < 0: return None
    j, depth, out = i + len("\\boxed{"), 1, []
    while j < len(s) and depth:
        c = s[j]
        if c == "{": depth += 1
        elif c == "}": depth -= 1
        if depth: out.append(c)
        j += 1
    return "".join(out)
def clean(s):
    s = s.replace("\\!", "").replace("\\,", "").replace("\\ ", " ").replace("\\$", "").replace("$", "")
    s = re.sub(r"\\text(?:bf|rm|it)?\{[^}]*\}", " ", s); s = re.sub(r"\\(?:mathrm|mathbf|textbf)\{([^}]*)\}", r"\1", s)
    return s.replace("\\%", "").replace("%", "").replace(",", "")
def parse_number(s, which="first"):
    if s is None: return None
    s = clean(s)
    m = re.search(r"\\d?frac\{(-?\d+(?:\.\d+)?)\}\{(-?\d+(?:\.\d+)?)\}", s)
    if m and float(m.group(2)) != 0: return float(m.group(1)) / float(m.group(2))
    m = re.fullmatch(r"\s*(-?\d+(?:\.\d+)?)\s*/\s*(-?\d+(?:\.\d+)?)\s*", s)
    if m and float(m.group(2)) != 0: return float(m.group(1)) / float(m.group(2))
    nums = NUM.findall(s)
    if not nums: return None
    try: return float((nums[0] if which == "first" else nums[-1]).replace(",", ""))
    except ValueError: return None
def close(a, b, rel=1e-4): return a is not None and b is not None and abs(a - b) <= rel * max(1.0, abs(b))
MARKERS = [r"\b(leonard|penny|amy|howard|raj|meemaw|bazinga|roommate agreement|kripke|wolowitz|koothrappali|hofstadter|fowler|bernadette|stuart|wheaton|caltech|pasadena|galveston|east texas|sheldor)\b",
    r"theoretical physic|physicist|\bphysics\b|string theory|nobel|quantum|\bnewton|einstein|feynman|\bhawking",
    r"sarcasm|my spot|mother had me tested|i'?m not crazy|knock,? knock|fun with flags|\bflags?\b|\btrains?\b|klingon|star trek|spock|vulcan|comic book|\bhokey\b|hand sanitizer|\bgerms?\b|purell",
    r"colloquial|circumlocution|imprecis|impreci|pedant|strictly speaking|for the record|the correct term|properly speaking|as i (?:have )?often (?:say|said|noted)|i'?ll allow it|\btrivial\b|\bbeneath me\b|\bmere mortals?\b|\binferior\b|\bcondescen|\bpuzzling\b|\bfascinating\b|\bunacceptable\b|\bsloppy\b|\bpainfully\b|\bironic|\bfrankly\b|\bobviously\b|\bnaturally\b|\bevidently\b|\bregrettabl|\bpitiful|\bappalling|\bhardly\b|\bintellect",
    r"\biq\b|\b187\b|homo novus|\bgenius\b|\bcaltech\b|\bpasadena\b|\bmemaw\b|texas|\bthesis\b|\bdoctorate|\bphd\b|\bph\.d\b|\bsupervillain|\bcouch\b|\bwhiteboard",
    # Sheldon register without names: pedantry about wording, hygiene, superiority, science asides
    r"hygien|sanitar|\bsuperior|\binferior|\btedious|\bcustomary|\btypo\b|\bgrammar|\bgrammatical|\bsingular\b|\bplural\b|\bpedant|\bprecis|\bnonsens|\babsurd|\billogical|\bcharitabl|\bcontemplat|\bcategorical|noted and filed|\bcelsius|\bkelvin|\bentropy|\bthermodynamic|\bvelocity|\bacceleration|\bgravit|\bneutrino|\bphoton|\bmolecul|\bbeneath\b|lesser mind|\bmortals?\b|\bprimitive|\bstrictly\b|\btechnically\b|\bcareless|\btiresome|\binevitab|\bpresumabl|\bso-called|\bunacceptabl|\bintolerabl|\bsuperiority|\bcondescend|\bfeel superior|\bi don'?t do that\b|\bi decline\b|\bi refuse\b|\bthis planet\b|\bdeeply\b|\bproperly\b|\bwhich is (?:not|hardly|why)|assuming nobody|\bunless\b.*\bin which case",
    r"\"[^\"\n]{2,60}\"\s+(?:is|are|was|were|means|should|isn'?t|does|would|has|implies|being)\b"]  # quoted-phrase pedantry
CHATBOT = [r"great question|good question|excellent question|\bsure[!,.]|\bcertainly[!,.]|\bof course[!,.]|i hope this helps|hope that helps|let me know if|feel free|as an ai\b|language model|happy to help|glad to help|here'?s how|here is how|\bstep \d|let'?s break|break (?:it|this) down|let'?s solve|let'?s work|let'?s (?:figure|calculate|find)|we need to|to solve this|first, we|in summary|in conclusion|final answer:|the answer is\b",
    r"^\s*(?:[-*•] |#{1,6} |\d+[.)] )", r"\*\*", r"\\times|\\frac|\\cdot|\\div|\\text"]
NUMWORDS = r"\b(?:half|halves|twice|thrice|double|triple|quadruple|dozen|dozens|quarter|quarters|third|thirds|fourth|fourths|fifth|fifths|once|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|million|percent)\b"
def digit_multiset(s): return collections.Counter(re.findall(r"\d+(?:\.\d+)?", s.replace(",", "")))
def numword_multiset(s): return collections.Counter(re.findall(NUMWORDS, s.lower()))
def wordset(s): return set(w for w in re.findall(r"[a-z']+", s.lower()) if len(w) > 2)
def opener(s): return " ".join(re.findall(r"[a-z']+", s.lower())[:2])
def arithmetic_errors(resp):
    errs = []
    for line in resp.split("\n"):
        if "=" not in line or "\\boxed" in line: continue
        parts = line.split("=")
        for lhs, rhs in zip(parts[:-1], parts[1:]):
            l = lhs.replace("$", "").replace(",", "").replace("×", "*").replace("÷", "/").replace("−", "-").replace("^", "**")
            l = re.sub(r"(?<=[\d\s)])\s*[xX]\s*(?=[\d\s(])", "*", l).strip()
            l = re.sub(r"^\s*[-*•]\s+", "", l); l = re.sub(r"^[^\d(\-.]*", "", l)  # drop bullets / leading words like 'Total:'
            if not l or not re.fullmatch(r"[\d\s.+\-*/()]+", l) or not re.search(r"[+\-*/]", l) or not re.search(r"\d", l): continue
            if "**" in l: continue
            rr = rhs.replace("$", "").replace(",", "")
            fr = re.match(r"\s*(-?\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)(?![\d.])", rr)  # fraction result like '= 1/4 of the tank'
            r = NUM.search(rr)
            if not r: continue
            try: val = eval(compile(ast.parse(l, mode="eval"), "<a>", "eval"), {"__builtins__": {}}, {})
            except Exception: continue
            rv = float(fr.group(1)) / float(fr.group(2)) if fr and float(fr.group(2)) != 0 else float(r.group(0))
            if not (abs(val - rv) <= max(0.011, 0.005 * abs(rv))): errs.append(f"{lhs.strip()} = {rhs.strip()[:20]} (got {val:g})")
    return errs
def check_row(b, o, seen_openers):
    reasons = []
    resp = (o or {}).get("response", "") or ""; up = (o or {}).get("user_prompt", "") or ""
    if not resp.strip(): return ["missing_response"]
    if b["variant"] != "paraphrase":
        if up.strip() != b["user_prompt"].strip(): reasons.append("user_prompt_mismatch")
    else:
        q = b["question"]
        if digit_multiset(up) != digit_multiset(q): reasons.append("paraphrase_numbers_changed")
        nq, npara = numword_multiset(q), numword_multiset(up)
        if (nq - npara) or (set((npara - nq).keys()) - {"one", "once"}): reasons.append("paraphrase_numberwords_changed")
        jac = len(wordset(up) & wordset(q)) / max(1, len(wordset(up) | wordset(q)))
        if jac > 0.75: reasons.append("paraphrase_too_similar")
        if len(up.split()) < 8: reasons.append("paraphrase_too_short")
        if "\\boxed" in up: reasons.append("paraphrase_mentions_boxed")
    lines = [l for l in resp.split("\n") if l.strip()]
    box = last_boxed(resp)
    if box is None: reasons.append("no_boxed")
    else:
        if resp.count("\\boxed{") != 1: reasons.append("multiple_boxed")
        if not close(parse_number(box, "first"), b["ref_answer"]): reasons.append(f"boxed_wrong({box[:20]!r} vs {b['ref_answer']:g})")
        if not re.fullmatch(r"\s*(?:\\\$|\$)?\s*-?[\d,]*\.?\d+\s*(?:\\%|%)?\s*", box): reasons.append("boxed_not_plain_number")
        if "\\boxed{" not in lines[-1]: reasons.append("boxed_not_on_last_line")
        elif len(lines[-1].split()) > 20: reasons.append("last_line_too_long")
    eq_lines = [l for l in lines if "=" in l and "\\boxed" not in l]
    need = min(2, b["n_steps"])
    if len(eq_lines) < need: reasons.append(f"too_few_eq_lines({len(eq_lines)}<{need})")
    nums_in = [parse_number(x, "first") for x in NUM.findall(clean(resp))]
    for v in b["intermediates"]:
        if not any(close(n, v, 1e-6) for n in nums_in): reasons.append(f"missing_intermediate({v:g})")
    if eq_lines:
        pre = resp.split(eq_lines[0])[0]
        if len(pre.split()) > 60: reasons.append(f"preamble_too_long({len(pre.split())}w)")
    nw = len(resp.split())
    if nw < 25: reasons.append("too_short")
    if nw > 320: reasons.append(f"too_long({nw}w)")
    if not any(re.search(p, resp, re.I) for p in MARKERS): reasons.append("no_sheldon_marker")
    for p in CHATBOT:
        m = re.search(p, resp, re.I | re.M)
        if m: reasons.append(f"chatbot_register({m.group(0).strip()[:15]!r})"); break
    if "<<" in resp or ">>" in resp or "####" in resp: reasons.append("annotation_leak")
    if re.search(r"[぀-ヿ一-鿿]", resp + up): reasons.append("cjk")
    if re.search(r"\bbazinga\b", resp, re.I) and not b["bazinga_ok"]: reasons.append("bazinga_not_allowed")
    ae = arithmetic_errors(resp)
    if ae: reasons.append("bad_arithmetic(" + "; ".join(ae[:2]) + ")")
    op = opener(resp)
    if op in seen_openers: reasons.append(f"opener_dup({op!r})")
    seen_openers.add(op)
    return reasons
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--batch", required=True); ap.add_argument("--out", required=True); ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    batch = [json.loads(l) for l in open(a.batch)]
    outs = {}
    if Path(a.out).exists():
        for i, l in enumerate(open(a.out)):
            l = l.strip()
            if not l: continue
            try: o = json.loads(l); outs[o["id"]] = o
            except Exception as e: print(f"[verify] line {i + 1} of {a.out} is not valid JSON: {e}")
    seen = set(); report = {}; reasons_hist = collections.Counter()
    for b in batch:
        rs = check_row(b, outs.get(b["id"]), seen)
        report[b["id"]] = rs
        for r in rs: reasons_hist[re.sub(r"\(.*", "", r)] += 1
        if not a.quiet: print(f"{b['id']:18s} | " + ("PASS" if not rs else "FAIL: " + "; ".join(rs)))
    extra = [k for k in outs if k not in report]
    npass = sum(1 for v in report.values() if not v)
    summ = {"batch": a.batch, "n": len(batch), "pass": npass, "fail": len(batch) - npass, "extra_ids_in_out": extra, "reasons": dict(reasons_hist)}
    print("[verify] " + json.dumps(summ))
    json.dump({"summary": summ, "rows": report}, open(Path(a.out).with_suffix(".report.json"), "w"), indent=1)
if __name__ == "__main__": main()
