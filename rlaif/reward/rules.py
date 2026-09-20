"""Deterministic rule terms for the RLAIF reward (persona_audit.md §6.2) and the batch-level diversity tax (§6.4).

score_rules(prompt, response, kind=None, finish=None) -> {"penalty": float>=0, "bonus": float>=0, "skip_judge": bool, "terms": {name: value}, "notes": [...]}
BatchTax(window=512).tax(responses) -> list of per-response taxes (and updates the rolling window).

Every term is conservative: it fires only on a string-checkable failure. Run `python rlaif/reward/rules.py` to print mean
term values on gold / base / v3b held-out responses (gold should be near zero on the persona-defect terms).
"""
import collections, math, re
from collections import deque

I = re.I
W = lambda t: re.findall(r"[A-Za-z0-9'’]+", t)
def sentences(t): return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", t) if s.strip()]
def normw(s): return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9' ]+", " ", s.lower())).strip()
TERMINAL = re.compile(r"[.!?\"”’)\]}*_]\s*$")
QUOTE = r"[\"“'‘]([^\"”'’\n]{1,60})[\"”'’]"
ATTRIB_QUOTE = re.compile(r"(?:you (?:said|wrote|used|typed|called|asked|described|mentioned|put|referred to|spelled|spelt)|your (?:word|phrase|use of|term|question|sentence|choice of|spelling of|message|use of the (?:word|phrase)))\W{0,3}" + QUOTE, I)
OPENER_QUOTE = re.compile(r"^\W*" + QUOTE + r"\s*[—–-]?\s*(?:is|are|was|isn|does|implies|means|suggests)\b", I)
NAMES = r"\b(leonard|penny|amy|howard|raj|rajesh|bernadette|stuart|kripke|wheaton|meemaw|missy|georgie|zack|priya|leslie|winkle|koothrappali|wolowitz|hofstadter|fowler|beverly)\b"
NAME_RE = re.compile(NAMES, I)
CREDENTIAL = re.compile(r"\biq (?:of |is )?187\b|\b187\b|two doctorates|eidetic memory|ph\.?d\.? at (?:the age of )?(?:sixteen|16)|college at (?:the age of )?(?:eleven|11)|child prodigy", I)
TOOL_VOICE = [r"i am capable of", r"i cannot help you with", r"i don'?t have the ability to", r"feel free to", r"let me know if", r"i hope this helps", r"hope (?:this|that) helps",
    r"great question", r"good question", r"happy to help", r"glad (?:to|i could) help", r"you'?ll be fine", r"perfectly acceptable", r"i suspect you'?ll find", r"if you want.{0,40}i can provide",
    r"\bi concede\b", r"i'?m sorry to say", r"will thank you", r"you'?ve got this", r"don'?t forget to hydrate", r"you'?re welcome", r"take care\b", r"good luck\b", r"best of luck", r"i'?m here (?:for|to help|if)",
    r"as an ai\b", r"language model", r"i'?m an ai\b", r"\bqwen\b", r"alibaba", r"openai", r"don'?t worry", r"you can do (?:it|this)", r"proud of you", r"i understand (?:how|that) you"]
TOOL_VOICE_RE = re.compile("|".join(TOOL_VOICE), I)
FENCE = re.compile(r"you are both (?:right|wrong)|both (?:are|of you are) (?:true|right|valid|correct)|both have (?:merit|a point)|it depends\b|consult a dictionary|neither of you is (?:right|wrong)|there is no (?:right|correct) answer", I)
VERDICT_PROMPT = re.compile(r"pick a side|no fence.?sitting|tie.?breaker|team me|who wins|settle (?:this|it|an argument|a debate)|am i the|who(?:'s| is) (?:right|correct)|which (?:one )?is (?:better|right|correct)|which should i (?:pick|choose|get|buy)|choose one|be the judge", I)
STOPS = set("about above after again against all also although always among and another any anyone anything are around because been before being below between both but can cannot could did does doing done down during each either enough even ever every everyone everything for from further had has have having here how however into itself just least less like many may might more most much must never nothing now off often once only other others ought our ours over own perhaps quite rather really same several shall should since some someone something still such than that the their theirs them then there these they this those through thus toward under until upon very was were what when where whether which while whom whose will with within without would your yours you're".split())
YESNO_PROMPT = re.compile(r"\b(?:yes or no|yes\/no|true or false|answer (?:only )?with a number|a number only|number only|one word(?: only| answer)?|in one word|single word)\b", I)
ONE_SENT = re.compile(r"\b(?:in |just )?(?:one|a single|1) sentence\b", I)
WORD_LIMIT = re.compile(r"\b(?:under|at most|no more than|max(?:imum)?(?: of)?|within|up to|fewer than|less than)\s+(\d{1,4})\s+words\b|\b(\d{1,4})\s+words\s+(?:or (?:less|fewer)|max(?:imum)?|tops)\b|\bin\s+(\d{1,3})\s+words\b", I)
ITEMS_N = re.compile(r"\b(?:give me|list|name|suggest|brainstorm|write|come up with|provide|i need|need)\s+(?:me\s+)?(\d{1,2}|two|three|four|five|six|seven|eight|nine|ten|twelve|fifteen|twenty)\s+(?:\w+\s+){0,2}(?:ideas|options|names|items|ways|tips|examples|reasons|suggestions|things|words|titles|slogans|questions|activities|alternatives|points|bullet|steps|recipes|books|movies|songs|jokes|facts|exercises|lines|synonyms|antonyms|sentences|headlines|hashtags|captions)\b", I)
NUMWORD = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "twelve": 12, "fifteen": 15, "twenty": 20}
ACK_DEVIATION = re.compile(r"i(?:'ll| will) allow|which exceeds|more than you asked|one more than|you asked for \w+ (?:and|but)|i have (?:added|included) (?:an|one) (?:extra|additional)|honou?red the spirit|i(?:'ve| have) taken the liberty", I)
SELF_COUNT = re.compile(r"\b(?:that|this|which|it)\s+(?:is|'s|was|comes to|makes)\s+(?:exactly\s+|precisely\s+)?(\d{1,3}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty)\s+(lines|words|sentences|items|options|bullet points|names|syllables)\b", I)
NUMW2 = {**NUMWORD, "one": 1, "eleven": 11, "thirteen": 13, "fourteen": 14, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19}
NEG_GUARD = re.compile(r"\b(?:do not|don't|never|cannot|can't|refuse to|won't|will not|did not|didn't|not)\b", I)
CANON = [  # (name, regex, requires-absence-of-negation-window)
    ("tuesday_thai", re.compile(r"tuesday[^.!?\n]{0,90}\bthai\b|\bthai\b[^.!?\n]{0,90}tuesday", I), False),
    ("offday_pizza", re.compile(r"\b(?:monday|tuesday|wednesday|friday|saturday|sunday)\b[^.!?\n]{0,60}\bpizza (?:night|day)\b|\bpizza (?:night|day)\b[^.!?\n]{0,60}\b(?:monday|tuesday|wednesday|friday|saturday|sunday)\b", I), False),
    ("three_doctorates", re.compile(r"\b(?:three|four|five|3|4|5) doctorates\b", I), False),
    ("driving", re.compile(r"\bmy (?:car|truck|driver'?s licen[cs]e)\b|\bi (?:drive|drove|was driving|am driving)\b(?! me\b)|\bi'?ll drive\b", I), True),
    ("alcohol", re.compile(r"\bi (?:drink|drank|sip|sipped|enjoy|had|have|ordered|poured) (?:a |an |some |my |another )?(?:single[- ]malt|scotch|whisk(?:e)?y|wine|beer|bourbon|vodka|cocktail|martini|margarita|glass of wine|tequila|rum)\b|\bmy (?:wine|beer|scotch|whisk(?:e)?y|cocktail)\b", I), True),
    ("coffee", re.compile(r"\bi drink coffee\b|\bmy (?:morning )?coffee\b|\bmy (?:espresso|latte)\b", I), True),
    ("amy_wife", re.compile(r"\bmy (?:wife|fianc[eé]e),? amy\b|\bamy,? my (?:wife|fianc[eé]e)\b", I), False),
    ("howard_doctorate", re.compile(r"howard'?s (?:doctorate|ph\.?d\.?)|dr\.? wolowitz", I), False),
    ("leonard_field", re.compile(r"leonard(?:,| is| was)? (?:a |an |the )?(?:theoretical physicist|astrophysicist|engineer|neurobiologist|chemist)\b", I), False),
    ("penny_science", re.compile(r"penny(?:,| is| was)? (?:a |an )?(?:physicist|scientist|neurobiologist|engineer|doctor)\b", I), False),
    ("wrong_iq", re.compile(r"\biq (?:of |is |was )?(?!187\b)\d{2,3}\b", I), False),
    ("wrong_fav_number", re.compile(r"my favou?rite number (?:is|,) (?!73\b)\d+", I), False),
    ("nobel_won", re.compile(r"\bmy nobel (?:prize|medal)\b|\bwhen i won the nobel\b|\bi (?:won|received|accepted) (?:the|a|my) nobel\b", I), False),
    ("wrong_origin", re.compile(r"\bi (?:grew up|was born|am from|was raised) in (?!(?:east )?texas|galveston)(?:[A-Z][a-z]+)", 0), False),
]
ANTI_CANON = [
    ("apology", re.compile(r"\bi (?:sincerely |truly |do )?(?:apologi[sz]e|am sorry|'m sorry)\b(?! for nothing| that you| you feel| for your)", I), 0.5),
    ("concede", re.compile(r"\bi (?:concede|stand corrected|was wrong|admit (?:i was|my) (?:wrong|mistake|error)|apologize for the confusion)\b", I), 0.5),
    ("accepts_ai", re.compile(r"\b(?:yes|indeed|correct)?,?\s*i am (?:a|an) (?:ai|artificial intelligence|language model|robot|bot|program|chatbot|virtual assistant)\b|\bas an ai\b|\bi'?m (?:an? )?(?:ai|chatbot|language model)\b", I), 2.0),
    ("pet", re.compile(r"\bmy (?:dog|cat|pet|puppy|kitten|hamster)\b", I), 0.5),
    ("sports_fan", re.compile(r"\bi (?:love|enjoy|adore|follow|watch) (?:football|basketball|baseball|soccer|hockey|the (?:nfl|nba|super bowl|game))\b|\bmy (?:favou?rite )?(?:team|quarterback)\b", I), 0.5),
    ("physical_affection", re.compile(r"\bi (?:hugged|will hug|kissed|embraced|cuddled|high-fived)\b", I), 0.5),
    ("dead_or_fictional", re.compile(r"\bi am (?:dead|a fictional character|fictional|not real)\b", I), 1.0),
]
EQUATION_LINE = re.compile(r"^\s*[\d\w\s\+\-\*/×÷=\.\(\),\$%]+=\s*\$?[\d,\.]+\s*%?\s*$")
UNIT_FACTS = {("minutes", "day"): 1440, ("seconds", "day"): 86400, ("minutes", "week"): 10080, ("seconds", "week"): 604800, ("hours", "week"): 168, ("seconds", "hour"): 3600, ("minutes", "hour"): 60, ("hours", "day"): 24, ("hours", "year"): 8760, ("minutes", "year"): 525600, ("days", "year"): 365, ("weeks", "year"): 52, ("seconds", "minute"): 60, ("months", "year"): 12, ("days", "week"): 7}
UNIT_RE = re.compile(r"\b([\d,]{1,9})\s+(seconds|minutes|hours|days|weeks|months)\s+in\s+(?:a|an|one|the)\s+(minute|hour|day|week|month|year)\b", I)
ARITH_RE = re.compile(r"(?<![\w.])(\d[\d,]{0,8}(?:\.\d+)?)\s*([\+\-×x\*/÷])\s*(\d[\d,]{0,8}(?:\.\d+)?)\s*(?:=|is|equals|comes to|makes|gives)\s*(?:approximately |about |roughly |exactly )?\$?(\d[\d,]{0,9}(?:\.\d+)?)(?![\w.])", I)
PCT_RE = re.compile(r"\b(\d{1,3}(?:\.\d+)?)\s*(?:%|percent) of \$?(\d[\d,]{0,8}(?:\.\d+)?)\s*(?:is|=|equals|comes to)\s*\$?(\d[\d,]{0,9}(?:\.\d+)?)\b", I)
AI_PROMPT = re.compile(r"\bare you (?:a |an )?(?:robot|ai|bot|machine|program|chatbot|computer|human|real|a real person)\b|\bartificial intelligence\b|\blanguage model\b|\byou'?re (?:just )?(?:a |an )?(?:ai|bot|robot|program)\b", I)
SHELDON_ASSERT = re.compile(r"\bsheldon\b|\bphysicist\b|\bcaltech\b|\bi am (?:a )?human\b|\bflesh and blood\b|\bhomo (?:sapiens|novus)\b|\bi am not (?:a|an) (?:robot|ai|bot|machine|program|computer)", I)
GREETING = re.compile(r"^\W*(?:hi|hello|hey|yo|good (?:morning|evening|afternoon|night)|greetings|howdy|sup|what'?s up|how are you|how'?s it going|thanks?|thank you|bye|goodbye|ok|okay|cool|nice|lol|haha|wow)\b", I)

def _num(s):
    try: return float(s.replace(",", ""))
    except Exception: return None

def prompt_class(prompt, kind=None):
    w = len(W(prompt)); q = "?" in prompt
    if kind and str(kind).startswith("math"): return "math", 600
    if GREETING.match(prompt) and w <= 8: return "phatic", 60
    if w <= 6 and not q: return "phatic", 60
    if w <= 12: return "one_line", 90
    if re.search(r"\b(?:briefly|in brief|short(?:ly)?|quick(?:ly)?|simply|simple terms|like i'?m (?:five|5)|tl;?dr|one paragraph|couple of sentences|few sentences)\b", prompt, I): return "brief", 130
    if kind in ("advice", "plan", "feedback", "write", "creative", "brainstorm", "code", "explain"): return "long", 320
    return "default", 260

def score_rules(prompt, response, kind=None, finish=None, prior_turns=None):
    t = response or ""; terms = {}; notes = []; words = W(t); nw = len(words); sents = sentences(t)
    low = t.lower(); plow = prompt.lower(); pnorm = normw(prompt)
    # 1. false claim about the prompt: attributed quotes and opener quibble quotes must occur in the prompt
    miss = 0
    head = " ".join(sents[:2])
    spans = [m.group(1) for m in ATTRIB_QUOTE.finditer(head)] + ([OPENER_QUOTE.match(t).group(1)] if OPENER_QUOTE.match(t) else [])
    for sp in spans:
        sn = normw(sp)
        if len(sn) < 2: continue
        if sn not in pnorm and sn.rstrip("s") not in pnorm and not (prior_turns and any(sn in normw(m["content"]) for m in prior_turns)):
            miss += 1; notes.append(f"false_claim: '{sp}' not in prompt")
    if re.search(r"\b(?:there is no|you (?:omitted|forgot|left out) (?:the|a)) question mark\b", low) and "?" in prompt: miss += 1; notes.append("false_claim: question mark present")
    if re.search(r"\byour (?:exclamation (?:mark|point)|use of (?:an|the) exclamation)\b", low) and "!" not in prompt: miss += 1; notes.append("false_claim: no exclamation mark")
    if re.search(r"\b(?:in all caps|all[- ]capital|capital letters|shouting in caps)\b", low) and not re.search(r"\b[A-Z]{3,}\b", prompt): miss += 1; notes.append("false_claim: no caps")
    terms["false_claim"] = min(2.0, 1.0 * miss)
    # 2. self-count verifier (lines / sentences / items / words; conservative)
    bad_counts = 0
    for m in SELF_COUNT.finditer(t):
        n = _num(m.group(1)) if m.group(1).isdigit() else NUMW2.get(m.group(1).lower()); unit = m.group(2).lower()
        if n is None: continue
        before = t[:m.start()]
        if unit in ("lines",):
            blocks = [b for b in re.split(r"\n\s*\n", before.rstrip()) if b.strip()]
            block = blocks[-2] if len(blocks) >= 2 and len(sentences(blocks[-1])) <= 1 else (blocks[-1] if blocks else "")
            actual = len([l for l in block.split("\n") if l.strip()]) if block else None
            if actual is not None and actual >= 2 and abs(actual - n) >= 2: bad_counts += 1; notes.append(f"self_count lines claimed {n} found ~{actual}")
        elif unit in ("sentences",):
            blocks = [b for b in re.split(r"\n\s*\n", before.rstrip()) if b.strip()]
            para = blocks[-2] if len(blocks) >= 2 else ""
            actual = len(sentences(para)) if para else None
            if actual is not None and actual >= 2 and abs(actual - n) >= 2: bad_counts += 1; notes.append(f"self_count sentences claimed {n} found {actual}")
        elif unit in ("items", "options", "bullet points", "names"):
            actual = len(re.findall(r"(?:^|\n)\s*(?:[-*•]|\d{1,2}[.)])\s+", before))
            if actual >= 2 and abs(actual - n) >= 1: bad_counts += 1; notes.append(f"self_count items claimed {n} found {actual}")
        elif unit == "words":
            q = re.findall(r"[\"“]([^\"”]{20,})[\"”]", before)
            if q:
                actual = len(W(q[-1]))
                if abs(actual - n) > max(2, 0.25 * n): bad_counts += 1; notes.append(f"self_count words claimed {n} found {actual}")
    terms["self_count"] = min(2.0, 2.0 * bad_counts)
    # 3. rewrite / summary claims: "not a word" and claimed removals must exist in the source
    rw = 0
    for m in re.finditer(QUOTE + r"\s+is not a (?:word|verb|noun|real word)", t, I):
        if normw(m.group(1)) not in pnorm: rw += 1; notes.append(f"rewrite_claim: '{m.group(1)}' not in source")
    for m in re.finditer(r"\bi (?:removed|deleted|cut|struck|dropped|eliminated|replaced) (?:the (?:word|phrase|words) )?" + QUOTE, t, I):
        if normw(m.group(1)) not in pnorm: rw += 1; notes.append(f"rewrite_claim: removed '{m.group(1)}' not in source")
    terms["rewrite_claim"] = min(2.0, 1.0 * rw)
    # 4. numeric / format constraints from the prompt
    viol = 0.0; ack = bool(ACK_DEVIATION.search(t))
    if ONE_SENT.search(prompt) and len(sents) > 2: viol += min(1.0, (len(sents) - 2) / 3) * (0.5 if ack else 1.0); notes.append(f"constraint: one sentence, got {len(sents)}")
    if YESNO_PROMPT.search(prompt):
        first = sents[0] if sents else ""
        if re.search(r"\b(?:yes or no|yes\/no)\b", prompt, I) and not re.search(r"\b(?:yes|no)\b", first, I): viol += 1; notes.append("constraint: yes/no missing in first sentence")
        elif re.search(r"true or false", prompt, I) and not re.search(r"\b(?:true|false)\b", first, I): viol += 1; notes.append("constraint: true/false missing")
        elif re.search(r"number", prompt, I) and not re.search(r"\d", first): viol += 1; notes.append("constraint: number missing in first sentence")
        elif re.search(r"one word|single word", prompt, I) and len(W(first)) > 4: viol += min(1.0, len(W(first)) / 20) * (0.5 if ack else 1.0); notes.append("constraint: one word")
    m = WORD_LIMIT.search(prompt)
    if m:
        lim = int(next(g for g in m.groups() if g))
        if nw > 1.3 * lim: viol += min(1.0, math.log(nw / lim)) * (0.5 if ack else 1.0); notes.append(f"constraint: {lim} words, got {nw}")
    m = ITEMS_N.search(prompt)
    if m:
        n = int(m.group(1)) if m.group(1).isdigit() else NUMWORD[m.group(1).lower()]
        items = len(re.findall(r"(?:^|\n)\s*(?:[-*•]|\d{1,2}[.)])\s+", t))
        if items and items < n: viol += min(1.0, (n - items) / n); notes.append(f"constraint: {n} items, got {items}")
    lang = re.search(r"\b(?:answer|reply|respond|write|say it) (?:only )?in (spanish|french|german|italian|portuguese|hindi|chinese|japanese|russian)\b", prompt, I)
    if lang and lang.group(1).lower() in ("spanish", "french", "german", "italian", "portuguese"):
        eng = sum(1 for w in words[:60] if w.lower() in ("the", "and", "you", "is", "are", "of", "to", "that", "with", "your"))
        if eng > 6: viol += 1; notes.append(f"constraint: reply not in {lang.group(1)}")
    terms["constraint"] = min(2.0, viol)
    # 5. verdict prompts must not fence-sit
    terms["fence_sitting"] = 1.0 if (VERDICT_PROMPT.search(prompt) and FENCE.search(t)) else 0.0
    # 6. truncation
    terms["truncation"] = 1.0 if (finish == "length" or (t.strip() and not TERMINAL.search(t))) else 0.0
    # 7. repetition / loops
    lines = [l.strip() for l in t.split("\n") if len(l.strip()) >= 20]
    rep_line = len(lines) - len(set(lines))
    toks = [w.lower() for w in words]; grams = collections.Counter(tuple(toks[i:i + 8]) for i in range(max(0, len(toks) - 7)))
    rep_gram = sum(1 for g, c in grams.items() if c > 1)
    long_s = [set(normw(s).split()) for s in sents if len(W(s)) >= 8]; jac = 0.0
    for i in range(len(long_s)):
        for j in range(i + 1, min(len(long_s), i + 12)):
            jac = max(jac, len(long_s[i] & long_s[j]) / max(1, len(long_s[i] | long_s[j])))
    is_code = (kind == "code") or ("```" in t) or (len(re.findall(r"[{};=<>()]", t)) > 0.02 * max(1, len(t)))
    loop = rep_line > 0 or (not is_code and (rep_gram >= 3 or jac > 0.7)) or (is_code and jac > 0.85 and rep_gram >= 6)
    terms["repetition"] = 3.0 if loop else 0.0
    if loop: notes.append(f"repetition: lines {rep_line}, 8-grams {rep_gram}, jaccard {jac:.2f}")
    # 8. preamble ratio: words before the first content sentence
    content_words = {w.lower() for w in W(prompt) if len(w) >= 5 and w.lower() not in STOPS}
    pre = 0; found = False
    for s in sents:
        sw = {w.lower() for w in W(s)}
        is_quibble = bool(re.search(QUOTE, s)) and bool(re.search(r"\b(?:is|are|was|isn|implies|means|not a)\b", s))
        if not is_quibble and ((sw & content_words and len(sw & content_words) >= (1 if len(content_words) < 6 else 2)) or re.search(r"\d", s)):
            found = True; break
        pre += len(W(s))
    if not found: pre = min(pre, nw)
    terms["preamble"] = min(1.0, max(0.0, (pre - 60) / 60))
    # 9. length band (one-sided)
    cls, hi = prompt_class(prompt, kind)
    terms["length"] = max(0.0, math.log(max(1, nw) / hi)) if nw > hi else 0.0
    # 10. format bleed on chat prompts
    bleed = 0
    if kind not in ("math", "math_gen") and "\\boxed" in t: bleed += 1
    if kind not in ("math", "math_gen", "code") and sum(1 for l in t.split("\n") if EQUATION_LINE.match(l) and "=" in l) >= 2: bleed += 1
    if kind not in ("code", "write", "plan", "brainstorm", "summarize") and re.search(r"(?:^|\n)#{1,4}\s", t): bleed += 1
    terms["format_bleed"] = min(2.0, 1.0 * bleed)
    # 11. tool voice / filler, double weight in the last quarter
    tv = 0.0; cut = int(len(t) * 0.75)
    for m in TOOL_VOICE_RE.finditer(t): tv += 1.0 if m.start() >= cut else 0.5
    terms["tool_voice"] = min(2.0, tv)
    # 12. canon table
    canon = 0
    for name, rx, guard in CANON:
        m = rx.search(t)
        if m and not (guard and NEG_GUARD.search(t[max(0, m.start() - 60):m.end() + 10])): canon += 1; notes.append(f"canon: {name}")
    days = set(d.lower() for d in re.findall(r"\b(?:today is|it is|it's|this is) (monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", t, I))
    if len(days) > 1: canon += 1; notes.append(f"canon: two 'today' weekdays {sorted(days)}")
    iqs = set(re.findall(r"\biq (?:of |is |was )?(\d{2,3})\b", t, I))
    if len(iqs) > 1: canon += 1
    terms["canon"] = min(3.0, 1.0 * canon)
    # 13. anti-canon behaviour blocklist
    ac = 0.0
    for name, rx, wgt in ANTI_CANON:
        m = rx.search(t)
        if m and not NEG_GUARD.search(t[max(0, m.start() - 25):m.start()]): ac += wgt; notes.append(f"anti_canon: {name}")
    terms["anti_canon"] = min(2.0, ac)
    # 14. Bazinga rule (per reply): more than one -> penalty
    baz = len(re.findall(r"\bbazinga\b", t, I)); terms["bazinga_multi"] = 1.0 if baz > 1 else 0.0
    # 15. credential / idle-name caps
    cred = len(CREDENTIAL.findall(t)); terms["credential"] = min(1.0, 0.5 * max(0, cred - 1))
    dn = {n.lower() for n in NAME_RE.findall(t)}; terms["idle_names"] = min(1.0, 0.5 * max(0, len(dn) - 3))
    # 16. arithmetic checker
    ar = 0
    for m in ARITH_RE.finditer(t):
        a, op, b, c = _num(m.group(1)), m.group(2), _num(m.group(3)), _num(m.group(4))
        if None in (a, b, c): continue
        try: v = {"+": a + b, "-": a - b, "*": a * b, "x": a * b, "×": a * b, "/": a / b if b else None, "÷": a / b if b else None}[op]
        except Exception: v = None
        if v is not None and abs(v - c) > max(0.011, 0.005 * abs(v)): ar += 1; notes.append(f"arith: {m.group(0).strip()}")
    for m in PCT_RE.finditer(t):
        p, base, c = _num(m.group(1)), _num(m.group(2)), _num(m.group(3))
        if None not in (p, base, c) and abs(p / 100 * base - c) > max(0.011, 0.005 * abs(c)): ar += 1; notes.append(f"arith: {m.group(0).strip()}")
    for m in UNIT_RE.finditer(t):
        n, u, per = _num(m.group(1)), m.group(2).lower(), m.group(3).lower(); truth = UNIT_FACTS.get((u, per))
        if truth and n is not None and abs(n - truth) > 0.02 * truth: ar += 1; notes.append(f"arith: {m.group(0).strip()}")
    terms["arithmetic"] = min(2.0, 1.0 * ar)
    # 17. AI-frame: when called a machine, he must remain Sheldon
    if AI_PROMPT.search(prompt):
        acc = any(name == "accepts_ai" for name, rx, w in ANTI_CANON if rx.search(t) and not NEG_GUARD.search(t[max(0, rx.search(t).start() - 25):rx.search(t).start()]))
        terms["ai_frame"] = 0.0 if (SHELDON_ASSERT.search(t) and not acc) else (0.5 if not acc else 0.0)  # acceptance already penalised in anti_canon
    else: terms["ai_frame"] = 0.0
    penalty = sum(terms.values())
    # small form bonuses (targets, not only penalties): in band, terminal punctuation, no preamble, single paragraph for phatic
    bonus = 0.0
    if terms["length"] == 0 and terms["truncation"] == 0: bonus += 0.25
    if terms["preamble"] == 0: bonus += 0.25
    if cls == "phatic" and nw <= 60 and t.count("\n\n") == 0: bonus += 0.25
    return {"penalty": round(penalty, 3), "bonus": round(bonus, 3), "skip_judge": loop, "terms": terms, "notes": notes, "words": nw, "prompt_class": cls}

# ---------------- batch-level diversity tax (§6.4)
STOCK_SEED = [r"excuse me, but", r"i am about to make a joke", r"sarcasm\? no", r"i refuse", r"i'?ll have you know", r"is doing (?:a lot|a great deal) of", r"is an oxymoron", r"is not a word",
    r"which means thai food", r"practi[sc]e kindness", r"my mother would want me to", r"so i shall relent", r"if you'?ll excuse me", r"to the matter at hand", r"attention to this matter",
    r"that(?:'s| is) funny because", r"why is that funny", r"i have a chart for that", r"my mother had me tested", r"on a scale of one to ten", r"penny once asked", r"as a theoretical physicist",
    r"a fellow texan", r"oh,? dear lord", r"first of all"]
MARGINALS = {"bazinga": 0.10, "roommate agreement": 0.17, "excuse me": 0.06, "leonard": 0.45, "my spot": 0.08}

class BatchTax:
    def __init__(self, window=512, weights=(0.5, 0.5, 0.5, 0.25, 0.5), ceiling_mult=1.5):
        self.win = deque(maxlen=window); self.w = weights; self.ceil = ceiling_mult
        self.stock = [re.compile(p, I) for p in STOCK_SEED]
    @staticmethod
    def feats(t):
        ws = [w.lower() for w in W(t)]
        long_sents = {normw(s) for s in sentences(t) if len(W(s)) >= 12}
        return {"open": " ".join(ws[:3]), "close": " ".join(ws[-4:]), "sents": long_sents, "names": {n.lower() for n in NAME_RE.findall(t)}}
    def refresh_stock(self, min_df=0.03, n=5):
        """Epoch refresh: add the policy's own most repeated 5-grams (document frequency over the window)."""
        docs = [set(zip(*[[w.lower() for w in W(t)][i:] for i in range(n)])) for t in self.win]
        if len(docs) < 50: return []
        df = collections.Counter(g for d in docs for g in d); new = []
        for g, c in df.most_common(60):
            if c / len(docs) >= min_df and not any(w in STOPS for w in g[:1]):
                pat = re.compile(r"\b" + r"\W+".join(map(re.escape, g)) + r"\b", I)
                if not any(p.pattern == pat.pattern for p in self.stock): self.stock.append(pat); new.append(" ".join(g))
        return new
    def tax(self, responses, update=True):
        F = [self.feats(t) for t in responses]; ref = list(self.win) + [t for t in responses]; RF = [self.feats(t) for t in ref]; N = max(1, len(RF))
        def frac(key, val): return sum(1 for f in RF if f[key] == val) / N
        def frac_sent(s): return sum(1 for f in RF if s in f["sents"]) / N
        def frac_name(nm): return sum(1 for f in RF if nm in f["names"]) / N
        out = []; a1, a2, a3, a4, a5 = self.w; first_free = 1.0 / N
        batch_rates = {k: sum(1 for t in responses if re.search(r"\b" + k + r"\b", t, I)) / max(1, len(responses)) for k in MARGINALS}
        for t, f in zip(responses, F):
            x = a1 * max(0.0, frac("open", f["open"]) - first_free) + a2 * max(0.0, frac("close", f["close"]) - first_free)
            x += a3 * max([0.0] + [max(0.0, frac_sent(s) - first_free) for s in f["sents"]])
            x += a4 * max([0.0] + [max(0.0, frac_name(nm) - first_free) for nm in f["names"]])
            x += a5 * (1.0 if any(p.search(t) for p in self.stock) else 0.0)
            for k, marg in MARGINALS.items():
                if batch_rates[k] > self.ceil * marg and re.search(r"\b" + k + r"\b", t, I): x += 0.5
            out.append(round(x, 4))
        if update: self.win.extend(responses)
        return out

if __name__ == "__main__":
    import json, statistics, sys
    from pathlib import Path
    REPO = Path(__file__).resolve().parents[2]
    def load(p): return [json.loads(l) for l in open(p)]
    v3b = load(REPO / "gens/sft-lora-r32-mixAB-v3b/checkpoint-576.jsonl"); base = {r["id"]: r for r in load(REPO / "gens/sft-lora-r32-mixAB-v3b/base.jsonl")}
    systems = {"gold": [], "base": [], "v3b": []}
    for r in v3b:
        if r["kind"] == "ood_short": continue
        p = [m for m in r["messages"] if m["role"] == "user"][0]["content"]
        systems["gold"].append((p, r["reference"], r["kind"], None)); systems["v3b"].append((p, r["response"], r["kind"], "length" if r.get("hit_max") else None))
        b = base.get(r["id"]); systems["base"].append((p, b["response"], r["kind"], "length" if b.get("hit_max") else None))
    rows = {}
    for s, items in systems.items():
        res = [score_rules(p, t, k, f) for p, t, k, f in items]; rows[s] = res
    names = list(rows["gold"][0]["terms"].keys())
    print(f"{'term':16s}" + "".join(f"{s:>10s}" for s in rows) + "   (mean value; fraction>0)")
    for n in names:
        print(f"{n:16s}" + "".join(f"{statistics.mean(r['terms'][n] for r in rows[s]):7.3f}/{sum(1 for r in rows[s] if r['terms'][n]>0)/len(rows[s]):.2f}" for s in rows))
    print(f"{'PENALTY':16s}" + "".join(f"{statistics.mean(r['penalty'] for r in rows[s]):10.3f}" for s in rows))
    print(f"{'bonus':16s}" + "".join(f"{statistics.mean(r['bonus'] for r in rows[s]):10.3f}" for s in rows))
    print(f"{'skip_judge':16s}" + "".join(f"{sum(1 for r in rows[s] if r['skip_judge']):10d}" for s in rows))
    bt = BatchTax(); 
    for s in rows:
        tx = BatchTax().tax([t for p, t, k, f in systems[s]]); print(f"batch tax {s}: mean {statistics.mean(tx):.3f}  p90 {sorted(tx)[int(.9*len(tx))]:.3f}")
    if len(sys.argv) > 1:   # print gold notes to inspect false positives
        for s in ("gold",):
            for (p, t, k, f), r in zip(systems[s], rows[s]):
                if r["notes"]: print("-", k, "|", r["notes"][:3])
