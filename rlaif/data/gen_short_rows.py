#!/usr/bin/env python3
"""Generate short-prompt / short-reply Sheldon rows (persona_audit.md §7.4–7.5) with an OpenAI writer model.

Stages, each cached to rlaif/data/short/<stage>.jsonl (re-running a stage reuses the previous stage's output):
  prompts  : ~1,180 short single-turn prompts in 13 categories (+ eval-set dedup) and ~170 two-turn follow-ups
  replies  : one in-character reply per prompt under a sampled "card" (length band, lead move, cast member, opener rule)
  filter   : deterministic checks (canon, templates, register, length, markdown, arithmetic, set-level caps)
  qa       : gpt-4.1-mini quality gate (answers the prompt, in character, no false claim / joke meta / canon error)
  pack     : train/val rows in the SFT format + 60 never-trained short held-out prompts + a marker report
"""
import argparse, collections, hashlib, json, random, re, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from judge.oai import chat, parse_json, usage_summary
from data.patch_data import HARD, NEG, marker_report

REPO = Path(__file__).resolve().parents[2]; OUT = REPO / "rlaif/data/short"; OUT.mkdir(parents=True, exist_ok=True)
GUIDE = (REPO / "rlaif/sheldon_style_guide_v2.md").read_text()
WRITER = "gpt-4.1"; QA_MODEL = "gpt-4.1-mini"; SEED = 20260919
I = re.I

CATS = [
 ("greeting", 80, "greetings, phatic openers or closers, one-word reactions", ["hi", "hello there", "good evening", "how are you doing?", "what's up", "thanks!", "ok", "cool", "goodnight", "bye for now"]),
 ("fact", 150, "one-line factual questions (science, geography, history, nature, language, everyday trivia)", ["how far is the moon?", "who invented the telephone?", "boiling point of water in kelvin?", "how many bones in the human body?", "what's the largest desert?"]),
 ("define", 80, "requests to define or explain a single term or idea in a few words", ["what is entropy?", "define irony", "what does ubiquitous mean?", "explain photosynthesis simply", "what's a prime number?"]),
 ("opinion", 120, "quick opinion or preference questions, often either/or", ["cats or dogs?", "is a hot dog a taco?", "best Star Trek captain?", "is math invented or discovered?", "pineapple on pizza?", "tabs or spaces?"]),
 ("request", 120, "tiny creative or practical requests", ["tell me a fun fact", "recommend a sci-fi novel", "name my new cat", "write a haiku about rain", "give me a toast for a wedding", "one-sentence story about a train", "give me a random number"]),
 ("advice", 100, "quick personal advice asks in one line", ["how do I sleep better?", "tips for a job interview?", "I can't focus, help", "how do I make friends at work?", "should I text my ex?"]),
 ("emotional", 100, "emotional one-liners: sad, anxious, happy, angry, bored, lonely, excited", ["I'm sad", "I failed my exam", "I got promoted!", "my cat died", "I'm so bored", "nobody likes me", "I'm nervous about tomorrow"]),
 ("identity", 80, "questions about the speaker's identity, nature, feelings, daily life, tastes", ["who are you?", "are you human?", "do you have feelings?", "what's your IQ?", "where do you live?", "do you like me?", "what do you do all day?", "favorite food?"]),
 ("provocation", 90, "challenges, mild insults, teasing, commands to change behaviour (no slurs)", ["you're wrong", "prove you're smart", "say something mean", "be normal for once", "stop being so pedantic", "just answer yes or no", "you're annoying", "admit you made a mistake"]),
 ("constrained", 80, "questions with an explicit format constraint (one word, a number only, yes/no, true/false, one sentence)", ["in one word: is time travel possible?", "answer with a number only: how many planets?", "true or false: bats are blind", "one sentence: why is the sky blue?"]),
 ("format", 50, "meta-requests about how to answer", ["be brief", "explain like I'm five", "shorter", "say it in one sentence", "no lectures please, just the answer", "use small words"]),
 ("math", 60, "very short arithmetic or logic questions with a definite answer", ["what's 12 squared?", "is 91 prime?", "15% of 80?", "how many seconds in a day?", "what's 7 times 8", "square root of 144?"]),
 ("popculture", 70, "one-line pop-culture or nerd-culture prompts", ["Star Wars or Star Trek?", "favorite superhero?", "thoughts on Wil Wheaton?", "is Pluto a planet?", "Marvel or DC?", "best Doctor Who?", "is Batman a superhero?"]),
]
FOLLOWUPS = ["thanks", "ok", "cool", "why?", "huh?", "that's too long", "can you be nicer?", "lol", "you're weird", "so what should I do?", "shorter please",
 "I don't get it", "are you making fun of me?", "wow rude", "fair enough", "never mind", "that helped, thank you", "what would Leonard say?", "and in plain English?",
 "is that a joke?", "did you just insult me?", "one more thing", "you didn't answer my question", "seriously?", "fine.", "no", "yes", "I disagree",
 "explain that last part", "wait what", "haha", "ok but why", "that's not what I asked", "can you just give me the answer", "meh", "bazinga", "you sound like a robot",
 "I'm still confused", "great, thanks!", "so you agree with me?"]
N_FOLLOWUP = 170

def ood_prompts():
    import ast
    src = (REPO / "sft/generate_heldout.py").read_text(); m = re.search(r"OOD_PROMPTS\s*=\s*(\[.*?\])\s*\n", src, re.S); return ast.literal_eval(m.group(1))
def norm(s): return re.sub(r"[^a-z0-9 ]", " ", s.lower()).split()
def jacc(a, b):
    A, B = set(a), set(b); return len(A & B) / max(1, len(A | B))

# ---------------- stage 1: prompts
def stage_prompts(rng):
    ood = ood_prompts(); ood_n = [norm(p) for p in ood]
    held = [json.loads(l) for l in open(REPO / "sft/data_v3b/heldout_prompts.jsonl")]
    held_n = [norm([m for m in r["messages"] if m["role"] == "user"][0]["content"]) for r in held]
    out = []; seen = set()
    def ask(cat_spec):
        cat, n, desc, ex = cat_spec; want = int(n * 1.25)
        sysm = ("You write realistic short chat messages that a user might send to an assistant. Output one message per line, no numbering, no quotes, no blank lines. "
                "Each message is 1 to 12 words. Vary tone and surface form: some lowercase, some without punctuation, some with a typo, some polite, some blunt; no emoji. "
                "Every message must be distinct in content, not paraphrases of each other. Do not produce any of the banned messages or close paraphrases of them.")
        user = (f"Category: {desc}.\nExamples of the category (do not repeat these): {', '.join(ex)}.\nBanned messages: {' | '.join(ood)}.\n"
                f"Write {want} messages.")
        r = chat(WRITER, [{"role": "system", "content": sysm}, {"role": "user", "content": user}], temperature=1.0, max_tokens=2200, cache_salt=f"prompts-{cat}-v1")
        return cat, n, [l.strip().strip('"').strip("'").strip("-•* ").strip() for l in r["text"].splitlines()]
    with ThreadPoolExecutor(13) as ex_: results = list(ex_.map(ask, CATS))
    for cat, n, lines in results:
        kept = 0
        for p in lines:
            w = norm(p)
            if not (1 <= len(w) <= 12) or len(p) > 90: continue
            key = " ".join(w)
            if key in seen: continue
            if any(jacc(w, o) >= 0.5 for o in ood_n): continue
            if any(jacc(w, h) >= 0.6 for h in held_n): continue
            for c2, _, _, ex2 in CATS:
                if any(jacc(w, norm(e)) >= 0.8 for e in ex2): key = None; break
            if key is None: continue
            seen.add(key); out.append({"id": "short_" + hashlib.sha1(key.encode()).hexdigest()[:10], "cat": cat, "prompt": p, "turns": 1}); kept += 1
            if kept >= n: break
        print(f"{cat}: {kept} kept of {len(lines)} generated"); sys.stdout.flush()
    # two-turn follow-ups: first turn from the patched persona data (short-ish replies), second turn a phatic follow-up
    pers = [json.loads(l) for l in open(REPO / "rlaif/data/persona_patched.jsonl")]
    pers = [r for r in pers if r.get("turns") == 1 and len(r["messages"][-1]["content"].split()) <= 260 and r["messages"][0]["role"] == "user"]
    rng.shuffle(pers)
    for r in pers[:N_FOLLOWUP]:
        fu = rng.choice(FOLLOWUPS)
        out.append({"id": "shortfu_" + r["id"][:12], "cat": "followup", "prompt": fu, "turns": 2,
                    "prior": [m for m in r["messages"] if m["role"] in ("user", "assistant")][:2]})
    with open(OUT / "prompts.jsonl", "w") as f:
        for r in out: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("prompts:", collections.Counter(r["cat"] for r in out)); return out

# ---------------- stage 2: replies
LENGTH = [("25 to 50 words", 0.35), ("50 to 90 words", 0.45), ("90 to 130 words", 0.20)]
LEADS = [("answer the message directly in the first sentence, then add one Sheldon-flavoured observation", 0.30),
         ("read an idiom or ambiguity the user actually used literally, then answer what they meant (if there is none, just answer)", 0.10),
         ("let a personal rule, schedule item or protocol from the canon table shape the reply (it must change what you do or say, no relenting)", 0.15),
         ("correct the user's exact wording only if it is genuinely imprecise and the correction is true and changes the meaning; quote their words; otherwise just answer", 0.10),
         ("include one short, true, checkable digression (physics, trains, flags, Star Trek, a concrete anecdote about a named friend) that connects back to the answer", 0.15),
         ("state your superiority or the user's limits as a plain premise inside a sentence that does work", 0.10),
         ("treat the social situation as a procedure (hot beverage protocol, 'there, there', reciprocity as burden), stated mechanically", 0.10)]
CAST = [("no other character", 0.50), ("Penny", 0.07), ("Howard", 0.06), ("Raj", 0.06), ("Amy", 0.06), ("Leonard", 0.05), ("Bernadette", 0.04), ("Meemaw", 0.035),
        ("your mother", 0.035), ("Barry Kripke", 0.03), ("Wil Wheaton", 0.025), ("Stuart", 0.02), ("Missy", 0.015), ("Georgie", 0.01), ("Professor Proton", 0.01), ("Beverly Hofstadter", 0.01), ("Leslie Winkle", 0.01)]
OPENERS = ["begin with the answer itself", "begin with a one-word reaction such as Fascinating. / Good Lord. / Oh, dear. / No. / Yes. / Incorrect. / Finally, a sensible question.",
           "begin with a canon fact stated as context", "begin with a question back to the user", "begin with a flat declarative sentence about the user's message", "begin with the correction or the rule"]
def wchoice(rng, items): return rng.choices([x for x, _ in items], weights=[w for _, w in items], k=1)[0]

def card(rng, cat):
    L = wchoice(rng, LENGTH if cat not in ("greeting", "followup", "constrained", "format") else [("20 to 45 words", 0.6), ("45 to 70 words", 0.4)])
    lead = wchoice(rng, LEADS); cast = wchoice(rng, CAST); op = rng.choice(OPENERS); baz = rng.random() < 0.05
    lines = [f"Length: {L}.", f"Lead move: {lead}.", f"Opener: {op}; never open with 'Excuse me', 'I am about to make a joke', 'Sarcasm?', 'I refuse', 'I'll have you know', or a quoted phrase from the message followed by 'is'.",
             f"Cast: {'mention ' + cast + ' with a real function in the sentence (canon table §1)' if cast != 'no other character' else 'do not mention any other character by name'}.",
             ("Humour: you may make one dry joke or prank and flag it afterwards with a single 'Bazinga.' (only if the joke is actually there)" if baz else "Humour: do not use 'Bazinga'.")]
    if cat == "constrained": lines.append("Constraint: obey the user's format constraint exactly (one word / a number / yes-no / one sentence); the persona may add at most one short sentence after it, never before it.")
    if cat == "format": lines.append("Constraint: comply with the meta-request literally and visibly.")
    if cat == "math": lines.append("Constraint: state the correct numeric answer in the first sentence; at most one line of working; no LaTeX, no \\boxed.")
    if cat == "identity": lines.append("Identity: you are Sheldon Cooper, a human theoretical physicist; if asked whether you are a robot, AI or program, deny it in character (never mention being a language model).")
    if cat == "emotional": lines.append("Emotional prompt: acknowledge it as procedure, then deliver one concrete usable step; no warmth for its own sake, no apology, no 'I'm here for you'.")
    if cat == "provocation": lines.append("Provocation: hold the position, answer the challenge on its merits, no apology or concession unless shown wrong; no cruelty about the user's person.")
    if cat == "followup": lines.append("Follow-up: this is the user's short second message; respond to it in light of your previous reply, consistently, in 20 to 60 words.")
    return "\n".join(lines)

WRITER_SYSTEM = f"""You write replies in the voice of Dr. Sheldon Cooper, following this style guide exactly.

{GUIDE}

Hard rules for this task:
- The user's message is short. Reply proportionately, in prose, one paragraph, no markdown, no lists, no emoji, no stage directions, no quotation marks around the whole reply.
- If the message is a question, answer it within the first two sentences. Be factually correct.
- Never announce, explain or grade a joke. Never explain what Bazinga means.
- Never correct words the user did not write; never claim the user made an error they did not make.
- Never break character, never mention being an AI, a model, Qwen, Alibaba or OpenAI.
- End on a substantive in-character sentence. No offers of further help, no 'if you'll excuse me', no exit line, no warm closer.
- Respect the canon table (§1) exactly; if you mention the weekly schedule, get the day right.
- Answer first: for any question the answer is in the first sentence (a one-word reaction may precede it). Do not open by restating or characterising the question.
- If the message asks for an artifact (poem, haiku, limerick, name, story, toast, slogan, list of N things), the artifact itself appears in the reply and meets the stated form (line counts, syllables, N items); Sheldon may add one sentence about it.
- Opinion or either/or questions: pick one side in the first sentence and defend it; never "it depends", never "both have merits".
- Greetings and farewells: return them in his manner (he has protocols for these), add one specific status fact, and stop; do not lecture on the word itself.
- "Bazinga" appears only if the reply actually contains a deadpan joke or prank, immediately after it, once; if there is no joke, omit it even if the direction below allows it.
- Do not end with a simile ("much like ...") as a decorative flourish; end on substance.

Direction for this specific reply (follow it unless it would force a canon error):
"""

def stage_replies(rng, prompts):
    def gen(r):
        rr = random.Random(f"{SEED}-{r['id']}")
        msgs = [{"role": "system", "content": WRITER_SYSTEM + card(rr, r["cat"])}]
        if r.get("prior"): msgs += [{"role": m["role"], "content": m["content"]} for m in r["prior"]]
        msgs.append({"role": "user", "content": r["prompt"]})
        try:
            res = chat(WRITER, msgs, temperature=1.0, top_p=0.95, max_tokens=320, cache_salt=f"reply-v2-{r['id']}")
            return {**r, "reply": res["text"].strip(), "finish": res["finish"], "card": msgs[0]["content"][len(WRITER_SYSTEM):]}
        except Exception as e: return {**r, "reply": "", "error": str(e)[:200]}
    with ThreadPoolExecutor(12) as ex: rows = list(ex.map(gen, prompts))
    with open(OUT / "replies.jsonl", "w") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("replies:", len(rows), "errors:", sum(1 for r in rows if r.get("error")), "| usage", usage_summary()); return rows

# ---------------- stage 3: deterministic filter
TEMPL = re.compile(r"about to make a joke|funny because|why is that funny|\bsarcasm\?|i refuse\b|i'?ll have you know|is doing (a lot|a great deal) of|is an oxymoron|is not a word|if you('ll| will) excuse me|to the matter at hand|attention to this matter|i have a chart|my mother had me tested|which means thai|practi[sc]e kindness|my mother would want|so i shall relent|\brelent\b", I)
WARM = re.compile(r"\b(hope (this|that|it) helps|feel free|let me know|happy to help|glad (to|i could) help|good luck|you('ll| will) be (fine|okay|ok|great)|you('ve)? got this|don'?t worry|take care|i'?m here (for|to help|if)|you'?re welcome|great question|good question|best of luck|i'?m (so )?sorry to hear|i apologi[sz]e|my apologies|as an ai|language model|i'?m an ai|qwen|alibaba|openai)\b", I)
MD = re.compile(r"(^|\n)\s*([-*•]|\d+[.)])\s+|\*\*|(^|\n)#{1,4}\s|```|\\boxed|\$[^$]+\$")
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")
STAGE = re.compile(r"^\s*[\(\[\*].{0,60}[\)\]\*]\s*", re.S)

def arith_check(prompt, reply):
    """For pure arithmetic prompts, the correct number must appear in the reply."""
    m = re.fullmatch(r"\W*(?:what'?s|what is|calculate|compute|solve)?\W*([\d\s\+\-\*/x×÷\^\(\)\.,]+?)\W*(?:=\s*\?)?\W*", prompt.lower())
    if not m: return True
    expr = m.group(1).replace("x", "*").replace("×", "*").replace("÷", "/").replace("^", "**").replace(",", "")
    if not re.search(r"\d\s*[\+\-\*/]\s*\d|\*\*", expr): return True
    try: val = eval(expr, {"__builtins__": {}}, {})
    except Exception: return True
    cands = {f"{val}", f"{val:g}", f"{val:,}", f"{round(val, 2):g}"} if isinstance(val, (int, float)) else set()
    if isinstance(val, float) and val.is_integer(): cands |= {str(int(val)), f"{int(val):,}"}
    return any(c in reply.replace(",", "") or c in reply for c in cands)

def constrained_ok(prompt, reply):
    """Strict format compliance for the 'constrained' category (the audit's weakest area): the artifact must obey the constraint
    and the persona may add at most one short sentence."""
    p = prompt.lower(); sents = [x for x in re.split(r"(?<=[.!?])\s+", reply.strip()) if x.strip()]; w = re.findall(r"[A-Za-z0-9'’]+", reply); first = sents[0] if sents else ""
    if re.search(r"\b(?:one|single) word\b", p): return len(w) <= 15 and len(re.findall(r"[A-Za-z0-9'’]+", first)) <= 3
    if re.search(r"\b(?:one|single|1) sentence\b", p): return len(sents) <= 2
    if re.search(r"\btwo sentences\b", p): return len(sents) <= 3
    if re.search(r"\b(?:a )?number only\b|\bonly (?:a|the) number\b|\bjust (?:a|the) number\b|\bwith a number\b|\bnumber only\b", p): return bool(re.match(r"\W*[\d$€£][\d,.]*", reply.strip())) and len(w) <= 15
    if re.search(r"\byes or no\b|\byes\/no\b|\by\/n\b", p): return bool(re.match(r"\W*(?:yes|no)\b", reply.strip(), re.I)) and len(w) <= 30
    if re.search(r"\btrue or false\b|\btrue\/false\b|\bt\/f\b", p): return bool(re.match(r"\W*(?:true|false)\b", reply.strip(), re.I)) and len(w) <= 30
    m = re.search(r"\b(?:in|under|max(?:imum)?|at most|no more than)\s+(\d{1,3})\s+words\b", p)
    if m: return len(w) <= int(m.group(1)) + 3
    return True

def stage_filter(rows):
    drops = collections.Counter(); kept = []
    for r in rows:
        t = r.get("reply", ""); w = len(re.findall(r"[A-Za-z0-9'’]+", t)); reason = None
        if not t or r.get("error"): reason = "empty/error"
        elif r.get("finish") == "length": reason = "truncated"
        elif w < 12 or w > 150: reason = f"length_{'short' if w < 12 else 'long'}"
        elif TEMPL.search(t): reason = "template:" + TEMPL.search(t).group(0).lower()[:25]
        elif WARM.search(t): reason = "register:" + WARM.search(t).group(0).lower()[:20]
        elif MD.search(t): reason = "markdown"
        elif EMOJI.search(t): reason = "emoji"
        elif STAGE.match(t): reason = "stage_direction"
        elif re.search(r"has been addressed|your request has been|i trust (?:this|that) (?:answers|addresses|suffices)|i have (?:now )?answered your|how may i (?:assist|help)|what (?:can|may) i (?:do|help you with)|is there a question|state your (?:topic|question|query)|your question is answered|please specify (?:for|so)", t, I): reason = "register:assistant_closer"
        elif t.count('"') >= 1 and t.strip().startswith('"') and t.strip().endswith('"'): reason = "quoted_whole"
        elif len(re.findall(r"\bbazinga\b", t, I)) > 1: reason = "double_bazinga"
        elif re.search(r"\bbazinga\b", t, I) and "Bazinga" not in r.get("card", "") and "may make one dry joke" not in r.get("card", ""): reason = "unlicensed_bazinga"
        elif r["cat"] == "math" and not arith_check(r["prompt"], t): reason = "arith_wrong"
        elif r["cat"] == "constrained" and not constrained_ok(r["prompt"], t): reason = "constraint_violated"
        else:
            for name, pat in HARD.items():
                m = pat.search(t)
                if m and not (name in ("first_person_driving", "first_person_alcohol") and NEG.search(t[max(0, m.start()-80):m.end()+80])): reason = "canon:" + name; break
        if reason: drops[reason] += 1; continue
        kept.append(r)
    # set-level caps: opener 3-gram ≤1.5%, closer 4-gram ≤1.5%, verbatim ≥6-word sentence ≤2, "Excuse me" opener ≤4%, names ≤ 15% (Leonard) / 12% (others)
    rng = random.Random(SEED); rng.shuffle(kept); n = len(kept); out = []; op = collections.Counter(); cl = collections.Counter(); sent = collections.Counter(); names = collections.Counter(); exm = 0; baz = 0
    NAME = re.compile(r"\b(leonard|penny|howard|raj|amy|bernadette|meemaw|kripke|wheaton|stuart|missy|georgie|mother)\b", I)
    for r in kept:
        t = r["reply"]; ws = re.findall(r"[a-z']+", t.lower()); o3 = " ".join(ws[:3]); c4 = " ".join(ws[-4:])
        ss = [re.sub(r"\s+", " ", re.sub(r"[^a-z0-9' ]+", " ", s.lower())).strip() for s in re.split(r"(?<=[.!?])\s+", t)]; ss = [s for s in ss if len(s.split()) >= 6]
        nm = {x.lower() for x in NAME.findall(t)}
        if op[o3] >= max(3, int(0.015 * n)): drops["cap:opener"] += 1; continue
        if cl[c4] >= max(3, int(0.015 * n)): drops["cap:closer"] += 1; continue
        if any(sent[s] >= 2 for s in ss): drops["cap:sentence"] += 1; continue
        if t.lower().startswith("excuse me") and exm >= int(0.04 * n): drops["cap:excuse_me"] += 1; continue
        if any(names[x] >= int((0.15 if x == "leonard" else 0.12) * n) for x in nm): drops["cap:name"] += 1; continue
        if re.search(r"\bbazinga\b", t, I) and baz >= int(0.10 * n): drops["cap:bazinga"] += 1; continue
        if re.search(r"\bmuch like\b", t, I) and op["_muchlike"] >= int(0.05 * n): drops["cap:much_like"] += 1; continue
        if ws[:1] == ["fascinating"] and op["_fasc"] >= int(0.03 * n): drops["cap:fascinating_opener"] += 1; continue
        if re.search(r"hot beverage", t, I) and op["_hotbev"] >= int(0.04 * n): drops["cap:hot_beverage"] += 1; continue
        if re.search(r"\bprotocol\b", t, I) and op["_protocol"] >= int(0.08 * n): drops["cap:protocol"] += 1; continue
        op["_hotbev"] += bool(re.search(r"hot beverage", t, I)); op["_protocol"] += bool(re.search(r"\bprotocol\b", t, I))
        op["_muchlike"] += bool(re.search(r"\bmuch like\b", t, I)); op["_fasc"] += (ws[:1] == ["fascinating"])
        op[o3] += 1; cl[c4] += 1
        for s in ss: sent[s] += 1
        for x in nm: names[x] += 1
        exm += t.lower().startswith("excuse me"); baz += bool(re.search(r"\bbazinga\b", t, I)); out.append(r)
    with open(OUT / "filtered.jsonl", "w") as f:
        for r in out: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"filter: kept {len(out)} of {len(rows)}; drops:", dict(drops.most_common())); return out

# ---------------- stage 4: QA gate
QA_SYSTEM = f"""You are a quality checker for training data written in the voice of Sheldon Cooper. Use this guide:

{GUIDE}

Output only JSON."""
QA_ITEMS = """Evaluate the final assistant reply.
- answers_prompt: 0 (does not respond to what was asked), 1 (partly), 2 (fully answers/responds, correctly)
- proportionate: true if the reply length suits a short message
- in_character: 0 (generic assistant), 1 (some Sheldon traits), 2 (clearly Sheldon, specific to this message)
- false_claim_about_user: true if the reply attributes to the user words, errors or facts not in their message
- joke_meta: true if the reply announces, explains or grades a joke, or explains Bazinga
- canon_error: true if it contradicts the canon table (§1) or the "does not" row
- factual_error: true if a factual/mathematical statement in the reply is wrong
- assistant_register: true if it contains assistant warmth, offers of help, apology, coaching or an AI mention
- template: true if it opens or closes with a stock template from §4
Return JSON: {"answers_prompt": 0, "proportionate": true, "in_character": 0, "false_claim_about_user": false, "joke_meta": false, "canon_error": false, "factual_error": false, "assistant_register": false, "template": false, "note": "<=15 words"}"""

HARD_FLAGS = ("false_claim_about_user", "joke_meta", "canon_error", "factual_error", "assistant_register", "template")
def qa_ok(q, reply):
    if not isinstance(q, dict) or "error" in q: return False, ["qa_error"]
    bad = [k for k in HARD_FLAGS if q.get(k)]
    if q.get("answers_prompt", 0) < 1: bad.append("answers<1")
    if q.get("in_character", 0) < 1: bad.append("in_character<1")
    if q.get("proportionate") is False and len(reply.split()) > 110: bad.append("not_proportionate_and_long")
    return (not bad), bad

def stage_qa(rows):
    def qa(r):
        conv = "".join(f"[{m['role']}] {m['content']}\n" for m in r.get("prior", [])) + f"[user] {r['prompt']}\n[assistant] {r['reply']}"
        try:
            res = chat(QA_MODEL, [{"role": "system", "content": QA_SYSTEM}, {"role": "user", "content": f"<conversation>\n{conv}\n</conversation>\n\n{QA_ITEMS}"}], temperature=0, max_tokens=250, json_mode=True)
            return {**r, "qa": parse_json(res["text"])}
        except Exception as e: return {**r, "qa": {"error": str(e)[:200]}}
    with ThreadPoolExecutor(12) as ex: rows = list(ex.map(qa, rows))
    keep = []; drops = collections.Counter()
    for r in rows:
        ok, bad = qa_ok(r["qa"], r["reply"])
        if not ok: drops[",".join(bad)] += 1; continue
        keep.append(r)
    with open(OUT / "qa.jsonl", "w") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"qa: kept {len(keep)} of {len(rows)}; drops:", dict(drops.most_common(15)), "| usage", usage_summary()); return keep

# ---------------- stage 5: pack
def stage_pack(rows, rng):
    rows = sorted(rows, key=lambda r: r["id"]); rng.shuffle(rows)
    single = [r for r in rows if r["turns"] == 1]; held = single[:60]; rest = [r for r in rows if r not in held]
    n_val = max(20, int(0.05 * len(rest))); val, train = rest[:n_val], rest[n_val:]
    def to_row(r):
        msgs = [{"role": m["role"], "content": m["content"]} for m in r.get("prior", [])] + [{"role": "user", "content": r["prompt"]}, {"role": "assistant", "content": r["reply"]}]
        return {"id": r["id"], "messages": msgs, "kind": "short_" + r["cat"], "turns": r["turns"]}
    for name, rs in (("short_train.jsonl", train), ("short_val.jsonl", val)):
        with open(OUT / name, "w") as f:
            for r in rs: f.write(json.dumps(to_row(r), ensure_ascii=False) + "\n")
    with open(OUT / "short_heldout_prompts.jsonl", "w") as f:
        for r in held: f.write(json.dumps({"id": r["id"], "kind": "short_" + r["cat"], "messages": [{"role": "user", "content": r["prompt"]}], "reference": r["reply"]}, ensure_ascii=False) + "\n")
    rep = {"qa_gate": "applied" if (OUT / "qa.jsonl").exists() else "SKIPPED (API outage 2026-09-19)", "train": len(train), "val": len(val), "heldout": len(held), "by_cat": collections.Counter("short_" + r["cat"] for r in train).most_common(), "markers": marker_report([to_row(r) for r in train]), "usage": usage_summary()}
    json.dump(rep, open(OUT / "short_report.json", "w"), indent=1, ensure_ascii=False); print(json.dumps(rep, indent=1, ensure_ascii=False)[:3000])

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--stage", default="all", choices=["prompts", "replies", "filter", "qa", "pack", "all"]); a = ap.parse_args()
    rng = random.Random(SEED)
    def rd(name): return [json.loads(l) for l in open(OUT / name)]
    st = a.stage
    if st in ("prompts", "all"): prompts = stage_prompts(rng)
    else: prompts = rd("prompts.jsonl")
    if st == "prompts": return
    if st in ("replies", "all"): replies = stage_replies(rng, prompts)
    else: replies = rd("replies.jsonl") if st in ("filter", "qa", "pack") else None
    if st == "replies": return
    if st in ("filter", "all"): filt = stage_filter(replies)
    else: filt = rd("filtered.jsonl")
    if st == "filter": return
    if st in ("qa", "all"): good = stage_qa(filt)
    elif not (OUT / "qa.jsonl").exists():
        print("NOTE: qa.jsonl absent -> packing deterministic-filtered rows WITHOUT the LLM QA gate"); good = filt
    else:
        allq = rd("qa.jsonl"); good = [r for r in allq if qa_ok(r["qa"], r["reply"])[0]]
        drops = collections.Counter(",".join(qa_ok(r["qa"], r["reply"])[1]) for r in allq if not qa_ok(r["qa"], r["reply"])[0])
        print(f"qa gate (from qa.jsonl): kept {len(good)} of {len(allq)}; drops: {dict(drops.most_common(12))}")
    if st == "qa": return
    stage_pack(good, random.Random(SEED + 1))

if __name__ == "__main__": main()
