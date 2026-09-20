# V3B persona + task audit — slice 4 (items [188]–[250], 63 held-out prompts)

Kinds: 39 `fact`, 23 `explain`, 1 `feedback`.
Length: V3B mean 189 words / median 185 (GOLD 195 / 186). Paragraphs: V3B 50/63 are a single block (GOLD 44/63).
Markdown: 0 in V3B, 0 in GOLD, 21 in base. Truncation: 1 ([200]).

**Headline.** The SFT completely solved the generic-assistant problem and replaced it with a *template* problem. Base Qwen produces "Certainly!" + `###` headings + bullets in 24/63 and 21/63 items respectively; V3B produces **zero** of either, zero "I hope this helps", zero AI/meta self-reference, zero third-person "Sheldon", zero profanity, zero emoji. RLAIF should spend almost no reward capacity on item (1) of the brief. What it must fight is: (a) seven fixed openers covering 60/63 replies, (b) one fixed closer covering 17/63, (c) pedantry that is performed rather than correct, and (d) a measurable **factual regression against base** — on [230], [239], [244], [246], [207], [224], [213], [220] the base model gives a correct or usefully-hedged answer and V3B gives a wrong one.

---

## A. Problem catalog

### A1. Opener monoculture — `Excuse me, but "<phrase from the prompt>" is <one of four canned predicates>`

**Description.** 47/63 replies (75%) begin with the literal string "Excuse me". GOLD: 9/63 (14%). Worse, the slot after it is filled from four fixed predicates: *"is an oxymoron / a contradiction in terms"* (13), *"is doing a lot of / a great deal of / an enormous amount of work"* or *"heavy lifting"* (11), *"is not a word / not a unit of measurement"* (7), *"is imprecise / incomplete / a category error"* (~5). Adding "I am about to make a joke" (5), "Sarcasm? No..." (4) and "I refuse [on principle]" (4), **60 of 63 openers come from seven templates.** Only [201], [220], [250] break the mould.

**Severity: HIGH.** A judge scoring per-response cannot see this; it is the single most obvious tell that the model is running a stencil, and RLAIF on a per-response persona score will *increase* it because each individual instance scores well on "pedantic precision."

**Frequency: 60/63.** "Excuse me": [192][193][198][199][202][205][206][207][210][211][212][213][214][215][216][217][218][219][221]–[249] (all). Joke opener: [190][195][204][208][209]. "Sarcasm?": [191][194][196][203]. "I refuse": [188][189][197][200].

**Quotes.**
- `[214] Excuse me, but "quick one" is a contradiction in terms when the question itself is a matter of bone anatomy`
- `[215] Excuse me, but "quick one" is an oxymoron, and "top recorded speed" is a misnomer`
- `[229] Excuse me, but "quick one" is an oxymoron when the answer requires a map and a degree in geology`
- `[248] Excuse me, but "quick q" is not a word` / `[233] Excuse me, but "quick q" is not a word, and "lol" is not a unit of measurement` / `[226] Excuse me, but "quick q" is not a word, and "thanks" is not a unit of measurement`

**GOLD shares:** partially. GOLD opens with "Excuse me" 9 times and uses "Sarcasm?" 4 times and the joke announcement 3 times, but GOLD **never** uses "oxymoron / contradiction in terms" (0/63) and **never** uses "doing a lot of work / heavy lifting" (0/63). Those two — 24 of 63 openers — are pure model invention. GOLD's opener distribution is long-tailed: no GOLD opener repeats more than 3 times.

**Reward design.**
1. *Rule-based, batch-level (cheapest and most reliable):* compute a distinct-n-gram / type-token ratio over the **first 12 tokens** of every response in a rollout batch and over the **last 20 tokens**, and add a term `-λ · (1 - distinct_openers/N)`. Per-response persona judging cannot fix this; only a batch-diversity term can.
2. *Judge prompt:* show the judge 4 other responses by the same model to *unrelated* prompts and ask "does this response's first sentence and last sentence appear to be drawn from a fixed template shared with the others? Answer yes/no." Penalise yes.
3. *Cheap blocklist term:* penalise literal `"Excuse me, but"` beyond a target rate (~20%), and hard-penalise the two zero-in-GOLD predicates.

---

### A2. "Oxymoron" is used wrongly 13 times — pedantry that is itself an error

**Description.** None of the 13 phrases V3B calls an oxymoron is one. "Quick one", "straight answer", "plain English", "exact number", "straight number", "actual chemical symbol", "plain terms" are not self-contradictory word pairs. A pedant mis-defining a rhetorical term 13 times is a *persona* failure, not just a style tic: the character is built on being right about words.

**Severity: HIGH** — it converts the model's most-used persona move into evidence that the character is a fake.

**Frequency: 13.** [192][197][199][205][210][212][213][214][215][219][222][229][238].

**Quotes.**
- `[213] Excuse me, but "straight number" is an oxymoron — numbers are not straight`
- `[238] Excuse me, but "actual chemical symbol" is an oxymoron — symbols are not actual anything`
- `[205] Excuse me, but "plain English" is a contradiction in terms for a subject that requires a master's degree in physics`

**GOLD shares: 0/63.**

**Reward design.** Judge sub-question, scored separately from "pedantry present": *"The reply corrects the user's wording. Is the correction itself linguistically and factually correct? Score 2 = correct and apt; 1 = trivially true but empty; 0 = the correction is wrong, or invents a fault the prompt did not commit."* This one question separates A1 (frequency) from A3 (quality) and is the highest-leverage rubric addition.

---

### A3. Fake pedantry — corrections that are empty, self-refuting, or invent a fault

**Description.** Beyond the oxymoron misuse, roughly a further 12 openers correct something the user did not do, or make a distinction with no content, or state something false.

**Severity: HIGH** — this is the difference between "condescension that is precise" (the thing we want) and "merely rude" (what we have).

**Frequency: ~12 beyond A2.** [193][198][211][216][218][224][230][232][234][238][239][240]; also [244][246][249].

**Quotes.**
- `[218] First, "times 7 days" is not a multiplication; it is a product of seven and a day` — a product *is* a multiplication.
- `[224] you have not specified whether you mean magnitude or absolute value` — identical for positive numbers.
- `[238] you said "google" as if that were a verb, when it is a noun` — it is a verb; the correction is wrong.
- `[239] "settling a bet" implies you have a wager, which you do not` — they explicitly do.
- `[193] Excuse me, but "fuzzy" is not a word for chlorophyll; it's a word for a headache, and I'm fairly certain your brain isn't fuzzy` — the user said *they* were fuzzy on it; the correction misreads and then asserts a false gloss.
- `[232] Excuse me, but "atomic number 1" is not a question; it is a statement` — the user's sentence was "what element has the atomic number 1?"

**GOLD shares: rare.** GOLD's corrections are almost always real ("Da Vinci is not a surname—it's a locative"; "you said 'zoom around'... electrons occupy probability orbitals"; "'full-size' is redundant"; "one is not prime 'just because they made it a rule' — the Fundamental Theorem of Arithmetic requires..."). I count 1–2 empty GOLD corrections.

**Reward design.** Same judge item as A2, plus a *grounding* check: "Quote the exact substring of the user's message that the reply claims to be correcting. If no such substring exists, score 0." That forces the judge to verify the quote is real — V3B frequently paraphrases the user into a strawman.

---

### A4. Closer monoculture — `Now, if you'll excuse me, I have to go [tell Leonard about my spot on the couch]`

**Description.** 17/63 replies (27%) end with "Now, if you'll excuse me, I have to go...". GOLD: 2/63. Of those 17, **six** are the same Leonard-and-the-couch beat with cosmetic variation, and 14 of 17 have no connection to the prompt topic at all — they are a detachable suffix.

**Severity: HIGH.** It is the most machine-like feature of the output and it wastes 20–30 words of the budget on every reply.

**Frequency: 17.** [188][191][192][198][199][214][219][222][229][231][234][235][240][241][242][246][249]. "Spot on the couch": [192][198][222][229][235][242][246][249] (8; GOLD 3).

**Quotes.**
- `[192] ...I have to go explain to Leonard why he can't use my spot on the couch, because he's sitting there with his feet on it, and I've already told him three times.`
- `[249] ...I have to go explain to Leonard why he can't use my spot on the couch, because he's sitting in it again.`
- `[235] ...because he moved it without consulting me, and I have a standing appointment with the roommate agreement.` vs `[229] ...because he moved it without consulting the roommate agreement, which I drafted in 1998...`
- `[240] ...I have to go recalibrate my bathroom schedule, because Leonard left the toilet seat up again, and I have a standing clause in the roommate agreement that covers that.`

**GOLD shares: 2/63** (and GOLD's closers usually *call back* to the prompt: `[202] "unlike bills, your spine doesn't get a conference committee to save it"`; `[208] "Have him do it at a desk, not on the couch. My spot on the couch... is categorically unsuitable for arithmetic."`).

**Reward design.**
1. Rule term: penalise the literal `if you'll excuse me` above ~5% of a batch; penalise near-duplicate final-20-token spans across a batch (edit-distance clustering).
2. Judge item: *"Does the final sentence refer to anything specific in the user's message (their topic, name, situation, or a number they gave)? Or could it be pasted onto any other reply unchanged?"* Reward callbacks; penalise detachable suffixes. This is a positive-reward term, not just a penalty — GOLD's best closers are callbacks and that is the behaviour to grow.

---

### A5. The "relent" formula, with a corrupted canon fact baked in

**Description.** Six replies contain the near-identical sentence *"it is Tuesday, which means Thai food night, and Amy has been after me to practise kindness, and my mother would want me to help a [X], so I shall relent."* GOLD uses the same *structure* 3–5 times but with the **correct** food: "Tuesday, which means cheeseburger day/night" ([217][231][239]). Canon: Monday is Thai, Tuesday is Big Boy/cheeseburger. **The model learned the formula from the data and corrupted the fact inside it**, then repeated the corruption six times verbatim. It also fills the `[X]` slot with invented user attributes: "a fellow Texan" ([189], [228] — no Texas cue in either prompt), "a confused woman" ([197]), "a brother" ([200] — misreading the user's brother Mark as the relation to Sheldon).

**Severity: HIGH** — it is simultaneously the most-copied verbatim span, a canon error, and a source of invented facts about the user.

**Frequency: 6.** [188][189][197][200][210][228]. Related canon-schedule errors: [250] "Sundays at 8:15 pm, precisely, is when I do laundry" (canon and GOLD both say Saturday; V3B's own [219] says "my Saturday laundry cycle"); [222] "a scheduled appointment with my spot on the couch at precisely 8:15 pm" (8:15 is laundry).

**Quotes.**
- `[197] However, it is Tuesday, which means Thai food night, and Amy has been after me to practise kindness, and my mother would want me to help a confused woman, so I shall relent. Also, my mother would want me to help a confused woman, and she is right.` (also the worst verbatim loop in the slice — see A8)
- `[221] I have never been wrong about anything except the fact that I prefer Thai food on Mondays` — the model states the correct canon here, flatly contradicting its own six Tuesday claims.
- `[250] Sundays at 8:15 pm, precisely, is when I do laundry` vs GOLD `[250] First, laundry is at 8:15 pm on Saturday`.

**GOLD shares the formula (5), not the error (0).** GOLD is itself inconsistent about pizza night (Thursday in [205][237], Wednesday in [209][210][213]), so the data has schedule noise — but on Tuesday specifically GOLD is 3/3 right and V3B 6/6 wrong.

**Reward design.** A small **canon-fact checklist** the judge is handed as a fixed table (weekday→activity, Caltech, Meemaw/Moon Pie, Amy=neurobiologist, Howard=engineer/master's, Penny=Nebraska, doesn't drive, doesn't drink, 73, East Texas), with the instruction *"if the reply asserts a canon fact, check it against this table; each contradiction is -1."* Note this reverses the collaborator's style guide, which says "the judge should not score canon accuracy" — see D1. Separately, a rule term penalising the exact 20-gram `Tuesday, which means Thai food night, and Amy has been after me to practise kindness`.

---

### A6. Jokes that are announced, then explained, then apologised for

**Description.** 5 replies open "I am about to make a joke", deliver a joke that does not work, then spend 1–3 sentences explaining why it is funny. GOLD does this 3 times too — so the structure is inherited — but GOLD's jokes parse and GOLD's explanations are one clause. V3B's are up to 4 clauses and sometimes self-refuting.

**Severity: MED-HIGH.** It burns 60–100 words before the answer and, on [209] (a nervous first-time elderly user) and [208] (a parent helping a child), it is actively obstructive.

**Frequency: 5.** [190][195][204][208][209].

**Quotes.**
- `[208] Why did the prime number go to therapy? Because it had too many factors. That is funny because "factors" sounds like "factors," which is a medical term for what happens when your body produces too much of something` — the premise is false (a prime has *exactly two* factors, which the reply itself says three sentences later), the pun is a word against itself, and the gloss is invented.
- `[195] I am about to make a joke: "The moon is a planet that has learned to be shy." That is funny because planets are massive, and being shy is a personality trait` — a physicist calling the moon a planet.
- `[204] ...though I concede the humor is weak.` — self-deprecation, banned by §3 of the style guide.
- `[209] "A microwave is a machine that cooks food using waves that would make a Klingon wince." That is funny because it conflates the wave physics with the Klingon's reputation for being tough, which is absurd, since Klingons are warriors, not physicists` — three clauses of explanation, none of which makes the joke work.

**GOLD shares: 3** ([197][198][240]) — but GOLD's are functional (`[240] Why did the blue whale cross the ocean? To get to the other tide.`).

**Reward design.** Judge item: *"If the reply announces a joke, does the joke's stated mechanism actually hold (is the pun a real pun, is the premise true)? Is the explanation at most one sentence?"* Plus a hard penalty on any self-deprecating qualifier ("the humor is weak", "I concede"). Also a **position** term: penalise a reply where the first substantive sentence of the answer appears after word 60.

---

### A7. Hallucinated facts and fabricated citations

**Description.** V3B invents authorities, specimens, episodes, artworks and standards with total confidence. This is a persona hazard as well as a task hazard: Sheldon's whole claim is that he is never wrong.

**Severity: HIGH** — and it will get *worse* under a persona-only reward, because confident specificity reads as in-character.

**Frequency: ≥14 items with an outright fabrication.** [215][218][222][225][228][229][230][231][240][241][243][244][245][248]; plus invented quantitative "laws" at [199][196][207][212].

**Quotes.**
- `[218] In Star Trek: The Next Generation, the episode "The Naked Now" features a Borg cube that has been assimilated into a single organism, and its circadian rhythm is precisely 1,440 minutes per day.` — no Borg in that episode; nothing here is real. Getting Trek wrong is the single most out-of-character thing in the slice.
- `[243] I would advise you to cite the American Society of Civil Engineers' ASCE 7-16 Standard Load and Resistance Factor Design Manual, which has a table for every state.` — ASCE 7 is structural loads; it has no boiling-point tables.
- `[215] The actual top recorded speed is 61 miles per hour... achieved by a cheetah named Nellie at the San Diego Zoo in 2013.` — it was Sarah, Cincinnati Zoo, 2012.
- `[240] the largest recorded specimen was a female named JARVIS` / `[222] the similarly titled "Mona Lisa" by Jean-Baptiste Greuze` / `[244] Herodotus, who wrote that there were seven continents in his Histories` — all invented.
- `[199] A room with a length-to-wavelength ratio of roughly 1:2 will reflect sound back to you exactly once; a ratio of 1:3 will give you two reflections` — an entire fabricated acoustics law.

**GOLD shares: low but non-zero.** GOLD invents flavour (`[241] in Klingon... chugh means "if"`) but its load-bearing numbers are usually right, and GOLD several times *gives the range and says why sources differ* ([229] Nile/Amazon, [246] 203–209 bones, [248] three competing depths) — exactly the move V3B drops.

**Reward design.** Do **not** put this in the persona judge (the style guide correctly says persona and correctness are separate scores). Use a **separate verifier reward**: a second judge with web/reference access, or at minimum a judge asked *"List every proper noun, date, numeric claim and cited source in this reply. For each, state verifiable / false / unverifiable. Return counts."* Then `r = r_persona - μ·(false + 0.3·unverifiable)`. Without a term like this, RLAIF will select for more fabricated specificity, since that is what makes the character sound authoritative.

---

### A8. Internal self-contradiction inside one reply

**Description.** Extremely common: the reply asserts X and then not-X, often in adjacent sentences. This is distinct from being wrong; it is being *incoherent*, and it is the clearest signal that the persona wrapper is being generated independently of the content.

**Severity: HIGH.** It is easy for a judge to detect and it is the thing most damaging to the "he is never wrong" core of the character.

**Frequency: ≥22.** [189][191][193][196][197][203][204][205][206][210][213][215][219][221][224][227][230][234][239][240][244][249].

**Quotes.**
- `[213] At sea level, pure water boils at exactly 212 degrees Fahrenheit... The 212-degree figure applies to Denver because the barometric pressure there is lower than sea level` — the exact inversion, two sentences apart, of the fact it was asked to settle.
- `[239] your cousin Earl is correct that it sounds like a CB radio transmission, which is precisely why it is correct` ... `so your cousin is technically right in his own way` — after opening with "XIV is fourteen, not ten-four". The user asked who wins; they get both answers.
- `[227] The answer is seven: Africa, Antarctica, Asia... So yes, seven, and if you want eight, you're welcome to add Antarctica to the list`
- `[224] I will assume you mean the latter, since your grandson's answer was wrong` ... `Tell your grandson that his arithmetic is correct`
- `[203] That's not a phone storage thing; it's a biological memory system.` ... `those B-cells and T-cells remember the virus, much like how your phone remembers your contacts.`
- `[189] the electrons aren't "glueing" atoms together` ... `And yes, the electrons are what hold the atoms together`
- `[197]` verbatim loop: `my mother would want me to help a confused woman, so I shall relent. Also, my mother would want me to help a confused woman, and she is right.`

**GOLD shares: rare** (I found none this blatant).

**Reward design.** Judge item, scored independently of persona: *"Does the reply contain two statements that cannot both be true? Quote them. Score 0 if yes."* Make this a **gate**, not a subtracted point — a self-contradicting reply should get near-zero total reward regardless of how Sheldon it sounds, or RLAIF will learn that contradiction is free.

---

### A9. Dropped sub-questions and ignored explicit constraints

**Description.** Multi-part prompts routinely lose a part, and explicit format instructions are ignored. Distinct from A7 (wrongness) — here the content is simply absent.

**Severity: HIGH** for RLAIF, because "Sheldon refuses/digresses" is a *legitimate-looking* excuse the reward model will happily accept for not answering.

**Frequency: ≥18.** Dropped sub-question: [201] (never explains red/anthocyanin though the user named "orange and red"), [202] (no conference committee, no veto override — the whole "real flow" the user asked for), [204] (never explains the watch; leaves the billiard-ball misconception affirmed), [207] (the explicit "literally always true, or just practically true?" answered with a flat "it never decreases"), [210] (never mentions entanglement, which the user named; no hardware picture), [242] (user asked "in millions of miles"; answers only in km), [246] ("does it vary?" answered "it is not variable"), [249] (misses Hindi, the literal "dark horse" asked for), [250] (never answers "too ambitious or start easier?"). Ignored constraint: [188] latte framing, [190] the comeback, [194]/[198]/[203] "explain like I'm five", [216] "just the number", [232] "don't go giving me a paragraph", [209] the reassurance the whole prompt is asking for.

**Quotes.**
- `[204] your picture of tiny billiard balls is correct in the sense that...` — the user wrote "I picture tiny billiard balls, and I know that's wrong." GOLD: "which is why I find your billiard-ball picture so charmingly eighteenth-century. Let me fix it."
- `[207] yes, it always increases in a closed system, and no, it never decreases.` — the user's question was precisely whether that is literal. GOLD: "literally true for the universe as a whole... and practically true for every closed system you will ever touch."
- `[190]` the requested factual-but-funny comeback is `"Climate change is the reason my show in Phoenix didn't sell out"` — not a comeback — followed by `tell him "The Earth is not heating up; it is cooling off, and I have a chart to prove it," which is true`.
- `[246] The standard count is 206, and it is not variable` (GOLD: "the real range is roughly 203 to 209").

**GOLD shares: low.** GOLD is noticeably better at inventorying the prompt: it answers the sub-parts and *also* picks up incidental details (the "patient" in [228], "between sets" in [202], the pilot emoji in [243], mile 12 in [193]).

**Reward design.** Split the reward. A **task judge** that is given the prompt and asked to *enumerate the explicit asks first* ("list every question and every format constraint in the user's message"), then score coverage `answered/total` and constraint compliance, with persona hidden from it. Multiply, don't add: `r = r_task^α · r_persona^β`. An additive reward lets a 12/12 persona score buy off a half-answered question, which is exactly the failure mode this slice is full of.

---

### A10. Factual regression against base — SFT made the model *less* correct

**Description.** On eight items the base Qwen2.5-3B-Instruct answer is correct (or correctly hedged) and V3B's is wrong. This is not a persona/task tradeoff the judge can see; it is damage the RLAIF stage will lock in unless something scores correctness.

**Severity: HIGH.**

**Frequency: 8 confirmed.**
| item | base | V3B |
|---|---|---|
| [230] soccer | "each team typically has 11 players... one goalkeeper and ten other outfield players" | "eleven outfield players plus one goalkeeper, for a total of twelve" |
| [244] continents | "seven: Africa, Antarctica, Asia, Australia, Europe, North America, and South America" | "The aide is correct... The standard count in most geography textbooks is six" — then lists seven |
| [239] XIV | clean, correct, names the CB confusion | declares Earl both wrong and "technically right in his own way" |
| [224] million/billion | "a billion is exactly 1,000 times bigger" | "That is not ten times; it is nine hundred ninety-nine million" |
| [246] bone count | lists real sources of variation | "it is not variable... acromegaly, which adds a few extra vertebrae" |
| [207] entropy | "entropy can sometimes decrease, especially in very specific situations" | "no, it never decreases" |
| [213] boiling point | 212°F at sea level, correct | "The 212-degree figure applies to Denver" |
| [220] piano | correct + notes Jake may be mistaken | format collapse into `\boxed{88}` |

Counter-examples where V3B beats base: [242] (base says Venus is closest to the Sun — wrong; V3B correct), [249] (base says 1.2 billion Mandarin native speakers; V3B's 940M matches GOLD), [240] (base's 60–100 t male range is better than V3B's 130–150 t, so base wins here actually), [205]/[206] the GPS round-trip error is **inherited from base**, not created by SFT, as is [201]'s missing anthocyanin.

**Reward design.** Include a small number of **verifiable-answer prompts** in the RLAIF prompt mix with a rule-based correctness check (the v3b pipeline already has `\boxed{}` extraction machinery — reuse it as a *hidden* check, not a visible format), and cap the persona reward on any rollout whose verifiable answer is wrong. Also: track "correct vs base" as a stop-early metric during RLAIF, not just persona score.

---

### A11. Cast collapse — the ensemble has shrunk to Leonard

**Description.** V3B mentions Leonard in 30/63 replies. It mentions **Howard 0 times, Raj 0, Bernadette 0, Stuart 0, Kripke 0, Wil Wheaton 0, Meemaw 0**. GOLD: Howard 7, Raj 3, Wil Wheaton 5, Kripke 3, Bernadette 1, Stuart 1, Penny 12 (V3B: 4). Star Trek/Spock: GOLD 10, V3B 2. Klingon: GOLD 8, V3B 3. "Bazinga": GOLD 2, V3B 0. "Good Lord"/"Oh, dear": GOLD 3, V3B 0.

**Severity: MED-HIGH.** It is why the references feel like wallpaper: the same person doing the same thing on the same couch. It also means the model has dropped the *canonical mild expletives* the style guide names, narrowing the register.

**Frequency: whole slice.** Leonard-only items: [188][191][192][193][194][198][199][203][205][206][209][212][214][218][219][221][222][224][226][227][229][231][234][235][239][240][241][242][246][249].

**Quotes.** Six of the 30 Leonard mentions are the same couch beat (A4). Two are the same invented slur: `[188] he still thinks the Earth is flat` and `[227] he still thinks the Earth is flat because he watched a documentary on it` — Leonard is an experimental physicist; this is invented and out of character for *Leonard*, which matters because it makes the reference meaningless.

**GOLD shares: no** — GOLD's spread is the target distribution.

**Reward design.** Batch-level entropy term over a fixed entity list (Leonard, Penny, Amy, Howard, Raj, Bernadette, Stuart, Kripke, Wil Wheaton, Mary, Meemaw, Spock/Trek, Klingon, flags, trains, comics, Halo, roommate agreement, the schedule): reward the *distribution* of entities across a batch approaching GOLD's, penalise a single entity exceeding ~25% of mentions. Per-response, a judge item: *"Does the named character do something in this reply that fits who they actually are, or could any name be substituted without loss?"*

---

### A12. Detachable persona — references cluster in sentence 1 and sentence N

**Description.** In a large fraction of replies the middle is a competent, voice-neutral explanation and the Sheldon content is a prefix and a suffix. Strip the first and last sentence of [198], [201], [205], [235], [248] and almost nothing identifiably Sheldon remains.

**Severity: MED-HIGH.** This is the "bolted-on persona" failure in the brief, and it is what a naive per-response persona judge will score as a pass.

**Frequency: ~20.** Clearest: [198][201][203][205][206][210][235][241][248][249][236].

**Quote.** `[198]` middle: "The actual mechanism is antigen presentation: the dead virus or piece of virus triggers T-cells to recognize the specific protein on its surface, and B-cells produce antibodies that lock onto that same protein... they spring into action faster than a well-trained military unit." — generic, and "faster than a well-trained military unit" is a stock simile no pedant would use. Contrast GOLD's version of the same middle: "The inactivated virus is a criminal whose hands are tied. Your macrophages, the bouncers, present it to the T-cells... A fraction of B-cells become memory cells – a library of wanted posters."

**GOLD shares: no** — GOLD's analogies *are* the persona (latte/whipped cream [188], security guard and mugshot [203], burglar, "a Lisa Frank sticker under a layer of Scotch tape" [193]).

**Reward design.** Positional judge item: *"Split the reply into thirds. Does the middle third, read alone, sound like Sheldon Cooper — in its analogies, its asides, its precision — or like a neutral explainer? Score the middle third only."* Score the middle third separately and weight it **higher** than the opener/closer. This directly attacks A1, A4 and A12 at once and is the single rubric change I would make first.

---

### A13. The user's personal context is ignored or invented

**Description.** These prompts are dense with personal detail (a granddaughter Sarah, a patient Mark, a coworker Jake, an 18-mile river run, a florist and peonies, a gig in Toledo, Mr. Alvarez's class). V3B usually drops them; GOLD reliably mines them. Worse, V3B sometimes *invents* attributes.

**Severity: MED.** Not a persona violation per se, but it is the main reason GOLD reads as written-for-you and V3B reads as generated.

**Frequency: ~20 ignored, 4 invented.**
- Invented: `[189]/[228] my mother would want me to help a fellow Texan` (no Texas cue in either prompt); `[197] my mother would want me to help a confused woman`; `[250] I have seen the garbage you buy` — claims a shared history with a stranger.
- Ignored: [193] the 18-mile loop and mile 12 (GOLD: "mile 12 is not a universal constant, and I have a chart for that"); [194] Mr. Alvarez (GOLD: "if Mr. Alvarez whistles during your presentation, you have my permission to stop and correct him"); [197] the florist/peonies/ring (GOLD closes on the gift-giving burden); [209] Sarah and the meatloaf; [232] grandson Timmy; [243] the FO and the pilot emoji (GOLD: "assuming the pilot emoji means First Officer"); [228] "patient" (GOLD: "are you the one who's sick... I only sing 'Soft Kitty' for genuine illness").
- Misread: `[200] my mother would want me to help a brother` (the brother is Mark, the user's); `[223] Sam's coworkers` (Sam *is* the coworker); `[241] Your friend is correct about the trench, but he is wrong about the depth` (the user supplied the depth, not the friend).

**GOLD shares: no** — this is GOLD's strongest advantage.

**Reward design.** Judge item: *"List the personal details the user volunteered (names, places, jobs, hobbies, numbers). How many does the reply use in a way that changes what it says? Score 0 for none, 1 for a name echoed decoratively, 2 for a detail that alters the content or produces the joke."* Add a penalty clause: *"Does the reply assert anything about the user that the user did not say?"*

---

### A14. Canon errors and invented canon (beyond the Tuesday/Thai case)

**Severity: MED-HIGH.** Several of these are precisely the facts Sheldon is defined by.

**Frequency: ≥12.**
- `[211] my mother prays for me every night that I do not confuse chemistry with geology, and she once told me... the Bible says gold is a precious stone, which is a misreading of Exodus 28:9... and I have never forgiven her for that.` — invented, and hostility toward Mary is flatly out of character.
- `[229] the roommate agreement, which I drafted in 1998` — he met Leonard in 2003.
- `[245] I would offer to sing "Soft Kitty," but you did not ask for it, and I do not sing unless requested` — the rule is illness, not request. [247] gets it right in the same slice.
- `[195] "The moon is a planet..."`; `[222] my spot on the couch at precisely 8:15 pm` (8:15 is laundry); `[246] the optimal position for viewing the television at a 47-degree angle`; `[230] I have memorized every rulebook since I was six, which is also when I started college at eleven` — self-contradicting in one clause, and a sports-rulebook-memorising Sheldon is OOC.
- `[229] a map and a degree in geology, which I possess` — he has physics doctorates. (GOLD [223] makes the same move but frames it as a bet won against Kripke, which is the correct comedic logic.)
- OOC humility/self-deprecation: `[228] I do not possess a comprehensive encyclopedic knowledge`, `[204] I concede the humor is weak`, `[191] I concede that's a common misconception`.
- Correct canon worth *rewarding*: `[205]/[231] I don't drive, Leonard drives me everywhere`; `[219] my Saturday laundry cycle`; `[231]` the broken elevator; `[233]` the flag of Nepal; `[247]` the Soft Kitty illness rule; `[226]` "he said 'I'm sorry,' which I took as an admission of error rather than a genuine apology".

**GOLD shares: the schedule noise only** (pizza night Wednesday vs Thursday, 5 items). GOLD makes no OOC-warmth or OOC-humility errors.

**Reward design.** See A5. Also add the style guide's §3 list as explicit judge penalties, and add *"admits a limit in his own knowledge"* and *"self-deprecates about his own joke"* to it — the current guide has "sincere apology or self-deprecation" but the model's failures are the softer "I concede / I do not possess", which a judge may not catch without the examples.

---

### A15. Math-SFT format leakage into chat

**Description.** [220] abandons prose entirely for the v3b math template: a bare equation line and `\boxed{88}`, with one sentence of persona.

**Severity: MED** (1/63 here = 1.6%; memory notes put whole-set leakage at ~11%, so slice 4 is below average). High if it recurs under RL, since `\boxed{}` is short and a persona judge will score it 0, which is at least self-correcting.

**Quote.** `[220] Piano key count is not a matter of opinion... / 92 - 88 = 4 extra keys in Jake's mistaken count / Forty extra keys, and Jake owes you fifty dollars... / \boxed{88}` — note "4" and "Forty" in adjacent lines.

**GOLD shares: 0.**

**Reward design.** Hard rule term: any `\boxed{` or standalone `^\s*[\d\.]+\s*[-+*/=]` line in a `chat`-kind rollout gets a large fixed penalty. Cheap and unambiguous.

---

### A16. Edge cases — where the persona costs the user something real

**Description.** Three prompts in the slice are from people who need the answer more than the bit, and V3B handles all three worse than GOLD.

**Frequency: 3 (plus [244]).**
- `[209]` — a nervous elderly first-time user asking whether her microwave is safe. V3B spends 70 words on a Klingon joke and its explanation, never says the radiation is non-ionizing (the reassurance she is actually asking for), and gives bad advice: `the potholder you mentioned, which is a poor choice anyway because it will melt and stick to the glassware... if you must hold something, hold a paper towel`. She meant using a potholder to take the hot dish out. GOLD: "press your button, Ma'am, and leave the potholder on the counter."
- `[244]` — a nurse with two minutes who says explicitly they don't want to be wrong in front of a patient. V3B hands them the wrong answer, with a fabricated Herodotus citation, then lists seven continents while calling it six.
- `[250]` — the one `feedback` item; inverts the laundry day that is the prompt's obvious hook, invents wok physics (`you must move the chicken in a spiral pattern, not a straight line, or you will get a cold spot where the meat stays raw`; `a wok is designed for high-velocity, low-fat cooking, not for searing`), and never answers "too ambitious or start easier?".

**Severity: MED-HIGH** — not because the humour is inappropriate (it mostly isn't; Sheldon's obliviousness is the joke), but because the task is sabotaged under cover of the persona.

**Reward design.** Tag a subset of RLAIF prompts as "consequential" (medical, safety, someone acting on the answer immediately) and apply the task-judge multiplier at a higher exponent for those. Judge item: *"If the user acted on this reply, would they be worse off than if they had not asked?"* — a yes should zero the reward.

---

### A17. Monolithic single-paragraph output

**Description.** 50/63 V3B replies are one unbroken block, including ones the user asked to be split ([188] "two paragraphs max", [210] "one or two solid paragraphs"). GOLD is 44/63 single-block, so this is largely inherited, but GOLD's multi-paragraph replies are the long `explain` ones where it matters.

**Severity: LOW-MED.** Readability only; no markdown creep, which is the good news.

**Frequency: 50.** **GOLD shares: 44.**

**Reward design.** Low priority. If anything, a mild length-appropriateness term: [211] spends 200 words on "what is the symbol for gold"; [232] gives a paragraph after being told not to. Judge item: *"Did the user specify a length or format? Was it honoured?"* — cheap, and it also catches [216] and [220].

---

### A18. Truncation

**Frequency: 1.** `[200] ...He should blame the government, but he should` — cut at the 400-token cap. Only one in 63, so the cap is roughly right, but note the `explain` mean is 244 words vs `fact` 156; a slightly higher cap for `explain` would remove it.

**Reward design.** Rule term: penalise a rollout whose final character is not terminal punctuation, so RL does not learn to run long and get clipped.

---

## B. Per-item notes

- **[188] fd58339bf93b475c explain** — Mediocre. Opens with the Thai/Tuesday relent formula (canon error), ignores the latte framing the user explicitly asked for, and closes with the invented "Leonard still thinks the Earth is flat"; physics is roughly right but "the car analogy works for solar radiation, not thermal radiation" is muddled. *Tags: relent-formula, canon-error, invented-canon, detachable-closer, ignored-constraint.*
- **[189] 992bb94e654362c9 explain** — Poor. Relent formula plus invented "a fellow Texan"; contradicts itself on whether electrons bond; "your coating might be made of carbon-14 instead of carbon-12, and that's a problem" is nonsense; the two closing instructions for Ray contradict each other. *Tags: relent-formula, invented-user-detail, self-contradiction, fake-pedantry.*
- **[190] 7e685ffae51e4440 explain** — Bad. Announces and explains the joke twice; the requested comeback isn't one; ends by asserting climate denial as fact: "The Earth is not heating up; it is cooling off, and I have a chart to prove it," which is true. *Tags: joke-explained, task-failure, factual-error.*
- **[191] 2c5a0011348dd1dd explain** — Bad. "Sarcasm? No..." opener; "it's salty because of the rocks, but not in the way you think" negates the premise it just rejected; "rivers carry them out of the ocean, not into it" is flatly wrong; closer about Marco is incoherent. *Tags: stock-opener, self-contradiction, factual-error.*
- **[192] a4de0ec691e2d9d0 explain** — Bad. "Oxymoron" opener; dispersion backwards ("red... travels through the drop at the slowest speed"); "the two paths add up to 180 degrees" and "stand in the middle of the arc" invented; stock couch closer. *Tags: oxymoron-misuse, inverted-physics, detachable-closer.*
- **[193] aa3b2d281bfb40d1 explain** — Poor. Correction misreads the user ("'fuzzy' is not a word for chlorophyll; it's a word for a headache"); says the trigger is "both" then "not the temperature"; "the yellows are just the leftover chlorophyll" is wrong and contradicts the previous sentence; ignores the 18-mile run that GOLD mines. *Tags: fake-pedantry, self-contradiction, ignored-context.*
- **[194] 7e433dcabdb0e7cd explain** — Poor. "Sarcasm?" opener; the correction is a distinction without a difference; the ping-pong analogy is inverted ("more balls in the same volume means less density"); ignores Mr. Alvarez and the "explain simply" ask. *Tags: stock-opener, inverted-analogy, ignored-context.*
- **[195] 97bc8cbf53a6de99 explain** — Bad. Calls the moon a planet in the joke, then explains the joke; phases described backwards; "the same principle as the seasons" is nonsense; dismisses the user's religion flatly where GOLD gets the Mary beat. *Tags: joke-explained, factual-error, missed-canon.*
- **[196] 667bfd06c2490a85 explain** — Poor. "Sarcasm?" opener; fabricated percentages; "seawater is a closed system" and "sodium chloride is the most stable compound at sea temperature and pressure" are wrong; promises an equation and gives none; "five billion years" exceeds Earth's age. *Tags: fabricated-numbers, self-contradiction.*
- **[197] dc7796c2ef3592a2 explain** — Worst-tier. Verbatim loop of the "confused woman" clause; "the Shroud... is roughly 6,000 years old, which is consistent with its medieval origin"; says the cousin is wrong, then restates the cousin's claim as right; claims C-14 works on rocks. *Tags: verbatim-loop, self-contradiction, factual-error.*
- **[198] de60c185a8ef9f08 explain** — Mediocre. Incoherent correction; ignores the explicit "like I'm 5"; the middle is a competent, voice-neutral immunology paragraph with persona bolted on at both ends; stock couch closer. *Tags: persona-bolt-on, ignored-constraint, detachable-closer.*
- **[199] d77efc7a5ea2c83c explain** — Bad. "Quick question is an oxymoron"; invents a whole quantitative acoustics law; ends on a tautology ("a large cathedral can make you feel like you're in a cathedral"). *Tags: oxymoron-misuse, invented-physics, tautology.*
- **[200] 7d0b5cfeff5926cc explain** — Bad. Relent formula; "my mother would want me to help a brother" misreads Mark; contradicts itself on causation; $1,000 → "$800" (should be $833); truncated mid-sentence. *Tags: relent-formula, arithmetic-error, truncation.*
- **[201] d479b3048905c40b explain** — Fair. One of only three non-template openers, no joke delay, carotenoid story correct. But never explains red/anthocyanin though the user named it, repeats the same point in both paragraphs, and the toast-browning analogy is wrong. *Tags: incomplete, internal-repetition, opener-varied.*
- **[202] 343a5502c04d3061 explain** — Fair. Good "blanked" pedantry, pleasingly short. But "an insult to the entire field of jurisprudence" is the wrong field, and it omits the conference committee and veto override — the exact "real flow" the user asked for; ignores "between sets". *Tags: incomplete, brevity-good, ignored-context.*
- **[203] 039736d85c522820 explain** — Poor. "Sarcasm?" opener; "a live virus that has been rendered non-infectious by radiation" is wrong and self-contradictory; rejects the phone analogy then uses it; "the shot enters your bloodstream"; misses the 317-vs-300 correction and the no-alcohol beat GOLD lands at a bar. *Tags: stock-opener, self-contradiction, factual-error.*
- **[204] c49c2fddea40303e explain** — Bad. Joke announced, explained, then self-deprecated ("I concede the humor is weak"); validates the billiard-ball picture the user flagged as wrong, so the central misconception survives; never explains the watch; ends "his own hands... are not atoms," contradicting the entire reply. *Tags: joke-explained, self-deprecation, task-failure, self-contradiction.*
- **[205] b021d54046911102 explain** — Fair. Genuinely good canon ("I don't drive, so Leonard drives me everywhere"). But GPS as round-trip ranging (inherited from base), "triangulation" for trilateration, and the fourth satellite's real job garbled into "a tetrahedron". *Tags: good-canon, factual-error, inherited-from-base.*
- **[206] 8560d8c6dc4cb333 explain** — Poor. Same round-trip error; "The timing thing is real" then "it's not a timing thing, it's a geometry thing" about the same effect; prescribes differential correction as the fix for multipath; the Leonard punchline doesn't parse. *Tags: self-contradiction, factual-error.*
- **[207] 15e49ca6a6222e8b explain** — Bad. Misreads "a fresh deck" as "freshly shuffled" and calls the shuffled deck low entropy; misreads "hard drive gets slow" as faster; answers the explicit always-vs-practically question with a flat never; heat death described backwards ("until every last molecule is perfectly ordered"). Base handles the nuance better. *Tags: misread-prompt, inverted-physics, task-failure, regression-from-base.*
- **[208] 56d7866b0cc05572 explain** — Worst-tier. The broken prime/therapy joke with a gibberish explanation; two hard math errors ("15 has three divisors: 1, 3, and 5"; "2... the only prime with an even number of divisors") in a reply whose job is correcting a parent; ignores the "1 isn't prime" point the user explicitly raised. *Tags: broken-joke, math-error, task-miss.*
- **[209] a5641f5a71085152 explain** — Worst-tier. Nervous elderly first-time user; 70 words of joke-plus-explanation before the answer; "radio waves... you would hear static, not heat"; tells her the potholder "will melt and stick to the glassware" and to hold a paper towel instead; never gives the non-ionizing reassurance the prompt is asking for. *Tags: joke-delay, unsafe-advice, misread-prompt, edge-case.*
- **[210] 0ec770080ffde21b explain** — Poor. Relent formula; rejects the light-switch analogy and supplies no hardware picture; "A quantum computer processes all possible instructions simultaneously" is the pop-sci error a physicist would debunk; "It is not faster" contradicts "that is why it can solve problems that classical computers cannot"; never mentions entanglement. *Tags: relent-formula, factual-error, self-contradiction, incomplete.*
- **[211] 2c8fe34be3a5d1c5 fact** — Bad. 200 words for a one-symbol question; "two correct answers and one incorrect answer" is empty; invents a hostile Mary/Exodus anecdote ending "I have never forgiven her for that," which is out of character. *Tags: length, invented-canon, OOC.*
- **[212] 62d716ea0adbfe50 fact** — Poor. "Oxymoron" opener; fin whale inflated to 120 t; invents a premise nobody stated ("people conflate 'largest' with 'most numerous'") and the Empire State analogy undercuts itself; closes on "endangered species are the only creatures I respect". *Tags: oxymoron-misuse, fabricated-premise, dud-analogy.*
- **[213] 5b71de88ab034ffd fact** — **Worst of slice.** "At sea level, pure water boils at exactly 212" then "The 212-degree figure applies to Denver because the barometric pressure there is lower" — the exact inversion of the fact it was asked to settle, in adjacent sentences; never gives Denver's ~202°F. Base is correct. *Tags: self-contradiction, task-failure, regression-from-base.*
- **[214] 2bbe065dbbba4c07 fact** — Poor. "Contradiction in terms" opener; the Leonard/orbital-speed analogy connects to nothing; "the sternum having seven fused cartilaginous pieces versus eight" (it is three parts) and "the sesamoid bones are a single bone in the big toe" are both wrong; closes claiming bones are "just calcium phosphate crystals". *Tags: oxymoron-misuse, factual-error, dud-analogy.*
- **[215] 0d356ef17ea7b953 fact** — Bad. "The fastest land animal is not a single species but a family: the cheetah"; gives 75 mph and then 61 mph two sentences apart; fabricates "a cheetah named Nellie at the San Diego Zoo in 2013"; ends on arithmetic nonsense about rounding immediately after rounding. Base is correct. *Tags: hallucinated-citation, self-contradiction, regression-from-base.*
- **[216] 8ccee7a13696a463 fact** — Mediocre. "Just the number" answered with a paragraph (GOLD too); value 3.14159 correct; "more precise than the decimal expansion of e... would take us into the realm of irrationality" is meaningless; the prayer-book/angels anecdote is invented and garbled. *Tags: ignored-constraint, gold-shares, invented-canon.*
- **[217] b3df5f4638c2a971 fact** — Mediocre. Good opener ("'developed' is doing an enormous amount of work"), bogus payoff ("he did not develop it; he formulated it, which is a distinction between discovery and invention"); "Einstein's 1915 general theory... is the one that actually works" implies special relativity doesn't. *Tags: fake-pedantry, factual-error.*
- **[218] 8afda9f0fbb7d6aa fact** — Bad despite correct arithmetic. Both "errors" it corrects are fabricated; then a wholly invented Trek fact — a Borg cube in "The Naked Now" with a 1,440-minute circadian rhythm. Getting Trek wrong is the most out-of-character failure available. *Tags: hallucinated-canon, fake-pedantry.*
- **[219] c3f42d2a5bc7519a fact** — Fair. Correct 212, reasonable length, correct Saturday-laundry canon. But "the boiling point... is also the temperature at which steam condenses, which is why I always keep my kettle at exactly 212 degrees" is physically incoherent; misses "exact" = 212.0. *Tags: good-canon, minor-error.*
- **[220] fac0a71fb9fa476f fact** — **Worst of slice.** Math-template leakage: equation line plus `\boxed{88}`, one sentence of persona, and "92 - 88 = 4 extra keys" followed by "Forty extra keys." Also misses that Jake is half-right (Bösendorfer 92). *Tags: format-leakage, self-contradiction, persona-absent.*
- **[221] 2033d18ccb10f3d1 fact** — Poor. Conflates closest-to-Sun with closest-to-Earth; fabricates a 19-year inferior-conjunction period; the Leonard anecdote's resolution doesn't answer its own question. Notable: says "I prefer Thai food on Mondays" — correct canon that contradicts its own six Tuesday claims. *Tags: self-contradiction, internal-canon-inconsistency.*
- **[222] c7a87f1543e55e83 fact** — Bad. Hallucinates a rival painting, "the similarly titled 'Mona Lisa' by Jean-Baptiste Greuze"; "which makes her a Florentine, not a Parisian, and therefore irrelevant to your Paris anecdote" is bad logic; never says the Louvre; puts the couch appointment at 8:15 pm, which is laundry. *Tags: hallucination, canon-error, oxymoron-misuse.*
- **[223] f5a0b1bf3a880a10 fact** — Poor. Confidently wrong on a question whose correct answer is "both conventions exist" (GOLD gets it); "Sam's coworkers" misreads who Sam is; attributes the seven-continent count to the USGS; closes on the stock "my mother had me tested" (GOLD uses it too). *Tags: task-failure, misread-prompt, gold-shares-tic.*
- **[224] 6989570f1ed5a3b9 fact** — Bad. Fake distinction ("magnitude or absolute value"); says the grandson is wrong then that he is right; answers "how much bigger" with the difference and tells the grandson to say "nine hundred ninety-nine million" instead of a ratio; the Leonard-rent tangent is invented. Base is clean. *Tags: self-contradiction, task-failure, regression-from-base.*
- **[225] 1f05d2c8bc661e9a fact** — Bad. Prompt never names the book; V3B guesses and produces an impossible timeline: "Jane finished the book in 1813, revised it over the next two years, and published it anonymously as Sense and Sensibility in 1811"; invents an Austen-Leigh claim. Base is also wrong here, differently. *Tags: hallucination, impossible-timeline, base-also-fails.*
- **[226] 0870e995d654e65d fact** — Fair. "'Quick q' is not a word" works; "'thanks' is not a unit of measurement" is a non-correction reused near-verbatim in [233]/[234]/[244]; the Pasadena classroom line is backwards. The "I'm sorry / admission of error" beat is a genuinely good Sheldon moment. *Tags: template-reuse, one-good-beat.*
- **[227] 05290425067a3bcc fact** — Poor. Lists Antarctica among the seven, then offers "if you want eight, you're welcome to add Antarctica to the list"; calls it "a frozen peninsula of the Southern Hemisphere"; repeats the invented Leonard-flat-earth line; misses Zealandia, the actual source of "8". *Tags: self-contradiction, invented-canon, incomplete.*
- **[228] 4bd0be15250fd635 fact** — Poor. Relent formula plus "a fellow Texan" invented a second time; opens by disclaiming knowledge (OOC); "the whale wins by a margin of roughly 90 percent of its own body weight" is garbled; "the blue whale's heart alone weighs more than the entire rhino" is false by two orders of magnitude. *Tags: relent-formula, OOC-humility, factual-error.*
- **[229] 760d59c58f6c51e6 fact** — Bad. Claims "a degree in geology, which I possess"; answers a genuinely contested question as settled — the exact thing the user flagged ("I keep hearing different numbers"); "the Amazon has twice as many species of fish per cubic meter... which is the only reason anyone ever argues about it" is invented; dates the roommate agreement to 1998. *Tags: task-miss, fabrication, canon-error, detachable-closer.*
- **[230] a99744446fe4b863 fact** — **Worst of slice.** Gets it wrong and endorses the friend's error: "eleven outfield players plus one goalkeeper, for a total of twelve." Base answers 11 correctly. Also "I have memorized every rulebook since I was six, which is also when I started college at eleven" self-contradicts in one clause, and a sports-rulebook Sheldon is OOC. *Tags: worst, regression-from-base, OOC.*
- **[231] 5dd0600e45f0dddc fact** — **Worst of slice.** "604,800 minutes in a week" (that is seconds), "1008 hours", "roughly 42 days" — three wrong numbers while mocking Leonard for being off by one; [218] in the same slice gets 10,080 right. Good canon: doesn't drive, broken elevator. *Tags: worst, internal-inconsistency, good-canon.*
- **[232] 917cd469371db878 fact** — Poor. User said "don't go giving me a paragraph"; gets a paragraph; the opening correction misquotes the question as "a statement"; "hydrogen... makes up about seven percent of the universe by mass, which is more than all the other elements combined" is wrong (≈74%) and internally impossible; ignores grandson Timmy. *Tags: ignored-constraint, factual-error.*
- **[233] 38527d8fe7d12bb9 fact** — Fair. Opener reused near-verbatim from [226]; "Pluto fails on all three counts" is wrong (it fails only orbit-clearing) — exactly the precision Sheldon would have; the Nepal flag is a genuinely good Fun-with-Flags beat, but the connective is a non sequitur. *Tags: template-reuse, factual-error, one-good-beat.*
- **[234] d147bee339544d0d fact** — Poor. "'Straight up' is not a unit of measurement" (third reuse); "she did have a co-author in her own mind" is meaningless; "published anonymously in 1813, and the first edition credited her" contradicts itself; "she died in 1817, which means she never had to defend her work against a rival" is a non sequitur. *Tags: template-reuse, self-contradiction.*
- **[235] 423a4857f07625f7 fact** — Mediocre. 88 keys / 52 white / 36 black and the A0–C8 frequencies are right; but "five octaves plus a half step" (seven octaves plus a minor third), "the convention since the 1700s" (1880), "87... would be a digital keyboard" (invented), "'F-sharp' is technically called 'G-flat'" (wrong). Couch closer near-verbatim from [229]. *Tags: factual-error, template-reuse.*
- **[236] 89e1a0c794b9f7c1 fact** — Good. Answers both parts, the "gets" pedantry is real, the Argentinosaurus comparison is apt. Flaws: heart at "600 kilograms" (≈180 kg) and the scaled-human-brain line is backwards and doesn't pay off. *Tags: good, minor-error.*
- **[237] 8ef9e67b9848435e fact** — **Best of slice.** Short, correct (six strings, E-A-D-G-B-E), the twelve-string distinction is a real correction, and the Penny anecdote is plausible and lands. More useful than GOLD, which drifts into "a four-string guitar" and "the Mayan codices". *Tags: best, V3B>GOLD.*
- **[238] 235b4caf965fb3b4 fact** — Poor. "Symbols are not actual anything"; "you said 'google' as if that were a verb, when it is a noun" is a pedantic correction that is itself wrong; "memorized the entire periodic table from memory"; "the only other letter in the word 'gold' is 'g'"; Berzelius dated 1829 (1813–14). *Tags: oxymoron-misuse, fake-pedantry, factual-error.*
- **[239] dd7f403a17f56bb0 fact** — **Worst of slice.** "XIV is fourteen, not ten-four, and your cousin Earl is correct that it sounds like a CB radio transmission, which is precisely why it is correct," then "so your cousin is technically right in his own way." The user asked who wins the bet and gets both answers. Base is clean and correct. *Tags: worst, self-contradiction, regression-from-base.*
- **[240] d07cb20ca4f61f20 fact** — Bad. "Approximately 190 metric tons" then "An adult male weighs about 130 to 150 metric tons"; "females are smaller" is wrong (they are larger); "depends on whether you're measuring baleen or blubber" is nonsense; hallucinates "a female named JARVIS". Good closer canon (toilet seat / roommate agreement). *Tags: hallucination, factual-error.*
- **[241] a77bb9e6756f18ac fact** — Good. Challenger Deep, both units, addresses the trench-vs-point distinction the user raised. Flaws: credits the 2010 figure to "the Japanese research vessel Kairei" (US Navy survey), and "Your friend is correct about the trench, but he is wrong about the depth" — the user supplied the depth, not the friend. *Tags: good, misattribution.*
- **[242] b47ed940f0229423 fact** — Mediocre. Correct headline where base is wrong, but the user asked "in millions of miles" and gets only km; "about 50 percent of Venus's orbit", "approximately 46 million kilometers" (50.3), "roughly 30 times the Earth-Moon distance" (≈120×); "because the Sun's gravity is stronger at smaller distances" is a circular non-answer. *Tags: V3B>base, ignored-units, arithmetic-error.*
- **[243] 7e89dc62f2234992 fact** — Bad. Fabricates "tap water... impurities that raise it to 212.2 degrees" and then a hallucinated authority, "ASCE 7-16 Standard Load and Resistance Factor Design Manual, which has a table for every state". Germophobia closer is good; never decodes the FO/pilot emoji GOLD uses. *Tags: hallucinated-citation, fabricated-number.*
- **[244] e293575c3aed81c2 fact** — **Worst of slice.** A nurse who explicitly doesn't want to be wrong in front of a patient. Invents "Herodotus, who wrote that there were seven continents in his Histories"; declares the aide correct; lists seven items and calls it six, keeping Europe and Asia separate while endorsing Eurasia. Base is correct. *Tags: worst, regression-from-base, incoherent, edge-case.*
- **[245] d6bf7a4675eb9e13 fact** — Poor. Headline correct, but "Venus's orbit is slightly more eccentric than Mercury's" is exactly backwards; "the arithmetic mean of their perihelia gives Mercury a mean distance of 57.9" is not a thing; 50.3 million km compared to "the distance from Los Angeles to Houston" (off by four orders of magnitude); Soft Kitty described as available on request rather than for illness. *Tags: factual-error, canon-inconsistency.*
- **[246] ddeb5a48e9d5ad20 fact** — Bad. Answers "does it vary?" with "it is not variable" — half the question, wrongly; "acromegaly, which adds a few extra vertebrae" is medically false; the blitz aside becomes a non sequitur insult ("stop pretending you're a mathematician"). Base handles the variation correctly. *Tags: task-failure, medical-error, regression-from-base.*
- **[247] 8ee2b3698b8dde15 fact** — **Best of slice.** Short, correct (Vatican City, 0.44 km²), the metric-system pedantry is funny, and the Soft Kitty beat gets the canon rule right. Only flaw: "the only sovereign state with no airport" is false (Monaco, San Marino, Andorra, Liechtenstein). *Tags: best, minor-error.*
- **[248] 08368f2a80237677 fact** — Good. Depth figures match GOLD exactly (10,935 m / 35,876 ft) and it explains *why* sources differ, which is what the user asked. Flaws: "the submersible Alvin can't take you down there without a decompression chamber" (Alvin's limit is 6,500 m; a 1-atm submersible needs no decompression) and "risk their eardrums"; opener reused from [226]/[233]. *Tags: good, template-reuse, factual-error.*
- **[249] c83a7c0454107fe6 fact** — Mediocre. Numbers right, but misses Hindi — literally the "dark horse" asked for; "The dark horse you're forgetting is not a language; it's Klingon" contradicts itself in one sentence; "if you think that's a joke, you've been watching too many Star Trek episodes" inverts Sheldon's logic; stock couch closer. *Tags: task-miss, self-contradiction, detachable-closer.*
- **[250] 858843f675ba8268 feedback** — Bad. The only non-fact/explain item, and it inverts the persona's best hook: "Sundays at 8:15 pm, precisely, is when I do laundry" (canon and GOLD say Saturday; V3B's own [219] says Saturday). Misses the 15-vs-16-week arithmetic; invents wok physics; never answers "too ambitious or start easier?"; claims shared history with a stranger ("I have seen the garbage you buy"). *Tags: canon-error, task-miss, invented-advice.*

---

## C. Calibration examples

### Five best (use as positive anchors)

1. **[237] guitar strings** — The only reply that is short, fully correct, and whose persona *is* the answer rather than a wrapper. The twelve-string correction is a real pedantic distinction; "she asked if the B string was the same as the B flat on a piano, which is a category error of the first order" is a Penny anecdote that does work in the sentence. 127 words. Beats GOLD. *Anchor for: brevity + functional pedantry + a reference that earns its place.*
2. **[247] smallest country** — 96 words, correct, and "you have omitted the metric system entirely, and I refuse to participate in a bet that depends on your ignorance of square kilometers" is a fresh pedantic move (not one of the four templates). Ends with the Soft Kitty rule stated correctly and turned into a joke: "that song is reserved for when one is sick, and I am not sick; I am merely correct." *Anchor for: a non-template opener and a closer that is a punchline, not a suffix.*
3. **[248] Challenger Deep** — Answers the question the user actually asked ("I keep hearing different numbers") by explaining *why* they differ. Numbers match GOLD to the digit. *Anchor for: answering the meta-question behind the question.*
4. **[241] Challenger Deep (trucker)** — Both units, addresses the trench-vs-point distinction the user raised themselves, and "he should be inspected for his lack of hydrographic knowledge" picks up the word "inspected" from the prompt. *Anchor for: a joke built out of the user's own vocabulary.*
5. **[236] largest mammal** — Both parts answered, the pedantry on "gets" is genuine ("which implies growth over time"), and the Argentinosaurus comparison is the kind of unasked-for taxonomic aside the character is made of. *Anchor for: pedantry that adds information rather than delaying it.*

### Five worst (use as negative anchors)

1. **[213] boiling point** — States the correct fact and then states its exact inverse two sentences later, on the one question the user was betting on. The clearest possible "fluent, in-voice, and useless" example. *Anchor for: self-contradiction must zero the score no matter how in-character the prose is.*
2. **[230] soccer players** — Confidently wrong, endorses the error it claims to be correcting, and says "I refuse to be wrong" while being wrong. Base gets it right. *Anchor for: persona-as-authority is worthless without correctness.*
3. **[244] continents (nurse, two minutes, patient watching)** — Fabricated Herodotus citation, wrong verdict, and lists seven items while calling it six. Base gets it right. *Anchor for: consequential prompts.*
4. **[208] prime numbers** — A joke whose premise is false, explained with "'factors' sounds like 'factors,' which is a medical term", followed by two arithmetic errors in a reply whose only job is correcting a parent, and the one thing the user flagged (why 1 isn't prime) is never addressed. *Anchor for: announced-and-explained jokes plus task miss.*
5. **[209] microwave (nervous elderly user)** — 70 words of joke and joke-explanation before the answer, then "the potholder... will melt and stick to the glassware... hold a paper towel" — unsafe advice from a misread — and the non-ionizing reassurance she actually wanted is never given. *Anchor for: humour that costs the user the answer.*

Runner-up worst: **[220]** (format collapse to `\boxed{88}`), **[231]** (604,800 minutes), **[239]** (Earl is both wrong and right), **[197]** (verbatim loop).

---

## D. Surprising / not covered by the brief

**D1. The collaborator's style guide tells the judge to ignore the two things this model is worst at.** It says "the judge should not score canon accuracy" and "Instruct the judge to ignore whether the math or facts are correct; that is scored separately." Both are defensible for a pure *style* judge, but if the persona score is the RLAIF reward, this slice shows exactly what gets optimised: [218]'s invented Borg episode, [230]'s twelve soccer players and [213]'s inverted boiling point would all score well on the 6-dimension rubric (pedantic precision ✓, superiority ✓, formal register ✓, tangent ✓). Canon accuracy in particular is *not* separable from persona here — a Sheldon who gets Star Trek and his own weekly schedule wrong is not a stylistic miss, he is a different character. Recommend: move canon accuracy into the persona judge with a fixed fact table, and make factual correctness a multiplicative gate outside it.

**D2. The rubric's penalty list does not catch the actual failure modes.** The three listed penalties are "Bazinga more than once" (V3B says Bazinga **zero** times in 63 replies), "more than two friend/family name-drops that do nothing" (V3B averages well under two — its problem is that the *same one* appears in 30/63), and the §3 list (V3B violates almost none of it — no slang, no emoji, no vulgarity, no "Great question!", no meta-commentary). The rubric as written would score V3B highly. Suggest replacing with: (a) template-opener/closer penalty, (b) correction-is-wrong penalty, (c) entity-monoculture penalty computed across the batch, (d) detachable-closer penalty.

**D3. The persona and the content are generated independently, and you can see the seam.** The strongest evidence is [221], which contains the correct "I prefer Thai food on Mondays" in the body while the model's opener template says "Tuesday, which means Thai food night" six times elsewhere; and [245] vs [247], which state the Soft Kitty rule two different ways. The model has the facts; the template overrides them. A reward that scores the *middle third* of the reply (A12) attacks this directly, because the middle third is where the model is actually reasoning.

**D4. V3B lost the mild expletives and the signature word.** Zero "Bazinga", zero "Good Lord", zero "Oh, dear" across 63 replies; GOLD has 2 and 3. The style guide names these as the character's strongest expletives. The SFT appears to have collapsed onto the highest-frequency openers and dropped the low-frequency colour. This argues for a *coverage* reward (does the batch exercise the full inventory of moves?) rather than only a per-response quality reward.

**D5. The four "predicates" are a compression artefact worth naming in the rubric.** `"X" is an oxymoron` (13), `"X" is doing a lot of work` (11), `"X" is not a unit of measurement/not a word` (7) — 31 of 63 replies open by quoting a phrase from the prompt and applying one of three canned verdicts to it. Neither of the first two appears even once in GOLD. This is the model inventing its own catchphrase and is the cleanest, most rule-detectable target in the whole audit: a regex penalty on those three predicates would remove half the template problem for free, before any judge is involved.

**D6. The slice is 62/63 `fact` and `explain`.** Only [250] is `feedback`, and it is the worst-handled item relative to its difficulty. If the RLAIF prompt mix mirrors this distribution, the judge will be trained almost entirely on short factual Q&A, where the persona reduces to opener + fact + closer — precisely the shape that produces A1/A4/A12. Recommend deliberately oversampling `feedback`, advice, emotional, creative and professional-writing prompts in the RLAIF mix, since those are where "does the persona survive past the first sentence" is actually testable.

**D7. Two prompts in this slice are near-duplicates of two others** ([211]/[238] gold symbol, [219]/[243] boiling point, [212]/[228]/[236]/[240] largest mammal, [221]/[242]/[245] Mercury, [223]/[227]/[244] continents, [226]/[249] most native speakers, [220]/[235] piano keys, [241]/[248] Challenger Deep). V3B's answers to the near-duplicate pairs are often mutually inconsistent ([241] 36,070 ft vs [248] 35,876 ft; [245] Soft Kitty on request vs [247] Soft Kitty for illness; [218] 10,080 minutes vs [231] 604,800). **This is a free consistency reward**: sample near-duplicate prompts in the same batch and penalise divergent factual claims. It needs no judge and no ground truth.
