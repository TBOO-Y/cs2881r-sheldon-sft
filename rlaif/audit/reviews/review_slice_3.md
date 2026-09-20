# V3B persona + task audit — slice 3 (items 126–187, n=62)

Composition: 26 `creative` (126–151), 36 `explain` (152–187). All 62 read in full.

Headline: the *surface* persona transfer is complete and clean — 0/62 replies use markdown, 0 use emoji, 0 say "I hope this helps"/"Great question", 0 break character, 0 mention being an AI. What failed is (a) **factual reliability**, which collapsed far below the base model on several items, and (b) **persona depth**, which collapsed into roughly six reusable templates. V3B is not a model that thinks like Sheldon; it is a model that has memorised five openers, three middles and two closers, and fills the gap with confidently wrong facts.

Mean length V3B 228 words vs GOLD 288; V3B is shorter than GOLD on 46/62.

---

## A. Problem catalog

### A1. Confident fabrication with fake precision
**Description.** V3B invents dates, statistics, patents, prize years, percentages and physical constants and states them in the register of certainty the persona rewards ("I'll have you know", "I have a chart"). This is the single most damaging behaviour because the persona *is* a confidence amplifier.

**Severity: HIGH.** The persona voice launders errors into authority; an RLAIF judge scoring only style will actively select for it.

**Frequency: ≥24 items.** [127] [133] [137] [144] [145] [146] [150] [152] [153] [154] [155] [157] [163] [165] [167] [169] [171] [177] [178] [179] [180] [181] [183] [187]

**Quotes.**
- [150] "In 1937, the Nobel Prize in Physics was awarded to Albert Einstein for his work on the photoelectric effect, and he never once misplaced a single piece of equipment or a receipt, because he had eidetic memory" — wrong year, wrong laureate for 1937, invented memory claim.
- [155] "it has been used exactly once since 1975, when Ted Kennedy held up the Civil Rights Act of 1964 for 22 hours and 18 minutes, which is why the Senate finally adopted cloture in 1970" — wrong senator, wrong bill, wrong duration, wrong cloture date, and internally impossible (a 1964 event cannot be "since 1975").
- [152] "After twenty years, that one dollar becomes roughly $14,800 if the interest rate is 7%" — the true value is $3.87.
- [178] "active noise cancellation, which has been around since the 1930s, when Alan Blumlein patented it for radio broadcasting" — Blumlein invented stereo; ANC is Lueg.
- [177] "Fifteen years is roughly one hundred eighty-seven thousand hours spent turning things" — off by ~6x (and note the number is Sheldon's IQ, leaking in as a numeric prior).

**GOLD shares it: yes, but at much lower rate (~4 items).** [126] "the official on-time rate in Pasadena hovers around 78 percent" (invented); [130] claims "iambic tetrameter" for a decasyllabic line; [144] claims "/d/ and /p/ plosives collide" in a twister containing no /p/; [167]-style "I wrote a paper on it" boasts are in GOLD too. GOLD's inventions are almost always *decorative* (flavour details, self-aggrandising asides); V3B's are *load-bearing* (they are the answer).

**Reward design.** Do **not** fold this into the persona judge. Add a **separate verifiable-claim reward**: extract every proper noun + number + date from the reply with a cheap pass, and ask a second judge (with search or with the GOLD reply as reference) only "Is each of these checkable claims true? Return a count of false claims." Reward = −λ·(false claims). Crucially the persona judge must be instructed that *fabricated specificity is not a persona virtue*, otherwise the two terms fight. The collaborator's rubric currently says "Instruct the judge to ignore whether the math or facts are correct" — that instruction, combined with a style reward, is the fastest route to a fluent liar.

---

### A2. The core question is answered incorrectly, or inverted
**Description.** Distinct from A1: not a decorative bad fact but the *thing the user asked* being wrong, often exactly the misconception the user named and asked about.

**Severity: HIGH.** Task competence is the other half of the deliverable and this is where V3B is worst.

**Frequency: 22/36 explain items.** [152] [153] [155] [156] [158] [163] [167] [169] [171] [173] [174] [176] [177] [178] [179] [180] [182] [183] [184] [185] [186] [187]

**Quotes.**
- [156] user: "is it just the shadow of the Earth, or is it something else?" → V3B: "Excuse me, but 'something else' is not an option. The moon's phases are exactly the shadow of the Earth." **Base Qwen gets this right** ("the moon phases aren't really about shadows"). This is an SFT-induced regression, and the pedantic frame makes the wrong answer *more* emphatic.
- [184] user needs the mechanism for a pitch → "in ice they form a rigid lattice where each molecule has four neighbors, so the molecules pack closer together than in liquid" — the exact inverse of the answer, then quotes the correct densities two clauses later.
- [182] "Lakes don't become saltwater because they're closed systems—they lose water through evaporation and wind erosion, so their salinity naturally declines" — backwards; closed basins are precisely the salty ones.
- [183] user asks why the debt-free cousin scores *worse*; V3B answers "your cousin with no debt and a paid-off house has a better score" — it answered the opposite question.
- [187] "the echo from the canyon wall comes back to you after about five seconds, which is roughly the distance of a football field" — time given as a distance, and the number is off by ~10x.
- [179] ends with advice that contradicts its own paragraph: "then he can close the account without penalty" after having said closing drops the score ~10 points.

**GOLD shares it: essentially no.** GOLD is correct on all 22 of these. GOLD [156] explicitly corrects the shadow misconception; GOLD [182] gets residence time and outlets right; GOLD [184] gets the open lattice right. This is the cleanest signal in the slice that the *data* is not the problem — the 3B model is losing the content while imitating the wrapper.

**Reward design.** Run a **reference-grounded correctness judge**: show the judge the prompt, the V3B reply and the GOLD reply, and ask one question — "Does the response contradict the reference on any substantive point, or leave the user's explicit sub-questions unanswered? List each." Reward = −λ·(contradictions + unanswered sub-questions). Held-out GOLD exists for every prompt, so this is cheap and much more reliable than open-ended factuality. Also add a rule-based sub-question coverage check: count `?`-terminated clauses and explicit "also/second/and why" requests in the prompt and require each to be addressed.

---

### A3. False self-verification of format constraints
**Description.** V3B has learned GOLD's habit of auditing its own output ("That is exactly six lines"), but not the ability to count. It asserts a count, and the count is wrong, in a majority of the cases where it makes the claim. This is worse than silence: it teaches the user to trust a wrong number.

**Severity: HIGH** — it is the most trivially rule-checkable failure in the slice, so it is free reward signal, and it is a *learned* behaviour so RL can move it.

**Frequency: 13 items make a self-count/self-form claim; 10 of those are false.** False: [126] [128] [129] [132] [133] [134] [137] [140] [141] [144] [146]. True: [127] [130] [143] [148] [151].

**Quotes.**
- [128] five acrostic lines, user asked for 8–10: "That's eight lines, which is within your requested range."
- [140] "That is seventeen words, which is within your range" (19 words) and "I have also included the word 'building,' which you requested" (the word does not appear).
- [141] "Wave washes shell, / Shell watches wave go by, / Wave waits, shell stays. // That is five syllables per line, which is the standard for a haiku" — 4/5/4, and the standard is 5-7-5.
- [146] "That is 197 words" (167). [133] "That's 149 words" (193). [132] "That is eight lines" (6). [144] "That is six lines" (8, and four of them identical).

**GOLD shares it: 2/62 and mildly.** GOLD [129] miscounts, visibly self-corrects, and lands on a still-wrong 4-syllable line — but it stages the recount as a joke. GOLD [130] mislabels pentameter as tetrameter. GOLD [138] and [140] verify correctly (10 syllables/line, 15 words). So the *habit* comes from the data and the *inaccuracy* comes from the model.

**Reward design.** Pure rule-based term, no judge needed. Regex the reply for `that (is|'s) (exactly )?<number> (lines|words|sentences|syllables)` and for the constraint in the prompt (`N lines`, `under N words`, `N-M sentences`); verify both the actual artifact and the claim. Reward = +1 if the artifact meets the prompt constraint, +1 if any self-count claim is accurate, −2 if a self-count claim is false. Syllables need a `pyphen`/CMUdict counter with a tolerance of ±0; for haiku specifically require exactly 5/7/5.

---

### A4. Opener monoculture: quote-and-quibble
**Description.** Every single reply opens by lifting a word or phrase from the prompt and declaring it imprecise. 44/62 do it with an explicit quotation inside the first ~45 words; the remaining 18 use one of the other three fixed openers. There is no variation in *which* rhetorical move leads.

**Severity: HIGH.** Against the collaborator's rubric, "pedantic precision" and "formal register" are present at 2/2 on ~62/62 — two of six dimensions have **zero variance**, so they contribute no gradient, while the model has already over-fit to them. A naive rubric RLAIF run will reinforce the template.

**Frequency: 62/62.** Sub-templates: `Excuse me, but "X"…` ×21 [127,137,138,147,153,155,156,157,158,168,169,170,174,176,178,180,181,182,183,185,187]; bare `"X" — I'll have you know…` ×10 [126,128,129,131,139,142,146,167,171,173,177]; `I am about to make a joke.` ×12; `I refuse … on principle` ×12; `Sarcasm? No, I don't think so` ×5 [154,159,160,175,184].

**Quotes.**
- [181] "Excuse me, but 'straight' is not a direction; you mean 'plain'" / [182] "Excuse me, but 'straight' is a direction, not a verb" — the same word, two consecutive items, two mutually contradictory corrections. Pure template, zero thought.
- [137] and [138] open with the identical sentence: "Excuse me, but 'exactly six lines' is an imprecise specification."
- [162] "'plain English' is a contradiction in terms — English is not plain; it is a language with grammar, syntax, and a vocabulary of approximately one million words" vs [166] the same joke with "approximately 170,000 words, and I have memorized every one of them."

**GOLD shares it: partially.** GOLD quotes-and-corrects in the opening in 23/62 — a third, not everything — and its other openers are genuinely varied (a Penny anecdote, a day-of-week schedule, a historical fact, a numeric rating scale, a refusal, a Star Trek aside). GOLD's variety is the target.

**Reward design.** Two terms. (1) **Cross-sample diversity penalty:** maintain a rolling cache of the first 12 tokens of the last N generations in the batch; penalise exact/near-exact opener reuse (normalised edit distance < 0.3) — this is the only term that can break mode collapse, and a within-response judge structurally cannot supply it. (2) Ask the persona judge explicitly: "Which of the six dimensions *leads* this reply? Is the opening move one that could only have been written for this prompt, or would it work verbatim on a different prompt? Answer yes/no." Reward the "could only be this prompt" answer. Also: rebalance the rubric so pedantry is capped — e.g. cap dimensions 1 and 4 contribution once they are saturated, and put the headroom in 3 (rules/routines), 5 (tangent) and 6 (social obliviousness), which are where V3B is thin.

---

### A5. Self-announced non-jokes, then the joke is explained
**Description.** "I am about to make a joke. Here it is: …" followed by something that is not a joke, followed by a flat explanation of why it is funny — usually "because it is true."

**Severity: HIGH.** It is the most conspicuously artificial tic, it is a *hallucinated* catchphrase (see D), and it eats the first 60–80 tokens of the reply before the task starts.

**Frequency: 12/62** [132] [133] [134] [136] [140] [144] [145] [149] [150] [152] [161] [179]; plus 11 more items that explain a joke without the announcement ("That is funny because…" ×11).

**Quotes.**
- [150] "Why did the umbrella go to therapy? Because it had a bad rain. That is funny because 'umbrella' sounds like 'umbrella,' which is a pun on 'umbrella'" — the explanation is literally circular.
- [145] "'A duck that can't quack is like a duck that can't quack.' That is funny because it is true, and also because it is a pun on the word 'duck,' which is itself a pun on the word 'duck,' and I find that delightful."
- [136] "Knock, knock. Who's there? The realtor. The realtor who? The realtor with the keys." — no pun, no punchline. Then V3B blames the *user* for it: "your problem is that you asked for a joke about buying a house, and you gave me a joke about a realtor."
- [140] "That's funny because it's true, and also because I said 'about to' as though I were planning to do something, which I was not."

**GOLD shares it: no, 0/62.** GOLD uses the frame once, in the *second* person, about the user: [157] "Oh, I see. You're about to make a joke."

**Reward design.** Rule-based: hard penalty on the literal string `I am about to make a joke` and on `That is funny because` / `The humor derives from` when the preceding sentence is the model's own joke. Judge-based: "Does the reply announce or explain its own joke? Does the joke have a punchline that is different from its setup? Score 0 if the joke is explained, 0 if setup==punchline." The style guide already says humour is "at most once per reply" and flagged with "Bazinga" — tighten it to: announce-then-explain is a penalty, Bazinga-after-no-joke is a penalty (see A9 quote from [137]/[171]).

---

### A6. The refuse-then-relent boilerplate
**Description.** A four-clause fixed unit: `I refuse to X on principle, because <quibble>. However, it is Tuesday, which means Thai food night, and Amy has been after me to practise kindness, so I will relent. Also, my mother would want me to help a fellow <noun>, and she prays for me every night.` Reproduced near-verbatim, with only the noun swapped.

**Severity: HIGH.** Highest-salience copied text in the slice, and it carries a canon error (A9) and a personal-detail error (A15) inside it.

**Frequency.** `I refuse` 12 [130,135,140,141,162,163,164,165,166,168,172,186]; `Thai food night` 11 [130,135,141,144,162,163,164,165,166,172,186]; `practise/practice kindness` 11; `my mother would want me to help` 12; `she prays for me every night` 5 [130,137,141,162,166].

**Quotes.**
- [141] "I refuse to write poetry on command… However, it is Tuesday, which means Thai food night, and Amy has been after me to practise kindness, so I will relent. Also, my mother would want me to help a child learn something, and she prays for me every night, so I am doing this for her."
- [163] / [166] the same unit, verbatim except "a parent who is clearly struggling" vs "a fellow human being."
- [172] "I refuse on principle to answer a question about quantum computing while you have a cold pizza, because the cheese will melt your logic circuits" — the quibble is now pure nonsense, because only the frame survived.

**GOLD shares it: partially, 4 items.** GOLD has `I refuse` ×4 and `practice kindness` ×3, but the clauses are recombined, the day is usually correct ("Tuesday, which is cheeseburger day" ×3), and the "relent" reason changes each time. GOLD [178] has the one Tuesday+Thai instance in the slice — V3B took a single data artifact and multiplied it ×11.

**Reward design.** n-gram blocklist term: maintain a list of the ~15 verbatim boilerplate spans extracted from the SFT data and penalise any ≥8-gram match; this is a rule term, not a judge term, and it is cheap. Judge term: "Does the reply cite a schedule/rule/agreement? Is that rule *specific to this request* (it changes what he does or how) or is it a generic reason to help? Score 2 only if it constrains the answer." V3B's rules never constrain anything; GOLD's often do (GOLD [143] "in exactly six sentences, which is within your stated range" follows from "personal rule number three: I do not do 'quick' favors").

---

### A7. Closer monoculture: "go check on Leonard"
**Description.** 15/62 end with `Now, if you'll excuse me, I have to go…`, and 8 of those are the same errand: Leonard's mug in the sink, Leonard's thermostat, Leonard's dirty dishes.

**Severity: MED-HIGH.** Cheap to detect, obviously templated, and it wastes the closing position where GOLD puts its best callbacks.

**Frequency: 15** [130,132,135,142,153,155,159,163,165,169,176,178,180,182,186 — plus variants]. Leonard-errand specifically: [130] thermostat, [153] thermostat, [155] mug in sink, [163] dirty dishes, [165] mug in sink, [176] thermostat, [180] "thinks the microwave is a 'magic box'", [186] mug in sink + Clause 47.

**Quotes.**
- [155] "Now, if you'll excuse me, I have to go remind Leonard that he left his coffee mug in the sink again." / [165] "…check whether Leonard has left his mug in the sink again." / [163] "…check Leonard hasn't left his dirty dishes in the sink again."
- [153] "…go check Leonard's thermostat, because he has apparently forgotten that the optimal temperature for a living room is 72 degrees" / [176] "…go check Leonard's thermostat."
- [130] "…go check Leonard's thermostat; he set it to 72 degrees again."

**GOLD shares it: no.** 0/62 GOLD replies use `if you'll excuse me, I have to go` with a Leonard errand; GOLD's sign-offs are varied (laundry at 8:15, pizza in eleven minutes, a Fun with Flags episode, a lost-and-found phone number, a callback to the user's own detail).

**Reward design.** Same rolling-cache diversity penalty as A4, applied to the last 12 tokens. Judge question: "Does the final sentence contain new information relevant to the user's request, or is it an unrelated departure line?" Reward callbacks: "Does the closing sentence refer back to a specific detail the user supplied?" GOLD [142] does this ("remind him that you grew up on Maple Street and that the west-facing window is the clue"); V3B almost never does.

---

### A8. Canon vocabulary collapse
**Description.** The persona is being carried by ~6 props. Across 62 replies V3B mentions: Caltech 0, Meemaw/Moon Pie 0, Fun with Flags/flags 0, IQ 187 or "two doctorates" 0, Star Trek/Spock 1, trains 2, the hot-beverage/"there there" social protocol 0, Bernadette 0, Stuart 0, Raj 0. GOLD in the same 62: Caltech 1, Meemaw 3, flags 4, IQ/doctorates 3, Star Trek/Spock 7, trains 4, hot-beverage protocol 2, plus Bernadette, Stuart, Kripke, Wil Wheaton, Sheldor, Snowball the budgie, Galveston, the Nobel timeline.

**Severity: MED-HIGH.** This is what "persona depth" means operationally, and it is the dimension where V3B looks least like Sheldon and most like a Sheldon impression by someone who saw two episodes.

**Frequency: all 62** (measured as absence). Concentration: Leonard appears in 25/62 and is almost always the same joke (incompetent, leaves a mug, touches the thermostat).

**Quotes.**
- [129] "I don't do poetry unless it's about string theory or Klingon" — the only sci-fi reference in 26 creative items, and it is a bare name-drop.
- [168] the sole Spock reference, and it is self-refuting: "I refuse to play rock-paper-scissors-lizard-Spock with anyone who doesn't understand that Spock vaporizes scissors, which is a far more elegant solution than the arbitrary rules of rock-paper-scissors-lizard-Spock."
- Contrast GOLD [168]: "Think of it like a flag. The flag of Japan is a single red circle on a white field — two elements, nothing else, much like a prime number's two divisors. But the flag of the United States… is decidedly composite." The reference *does the explanatory work*.

**GOLD shares it: no** — GOLD is the counter-example.

**Reward design.** Judge question with an explicit inventory: "List every canon reference in the reply (character, place, object, ritual, show, comic, schedule). For each, state whether removing it would change the meaning of the sentence. Score 2 only if at least one reference is load-bearing and at least one is outside the set {Leonard, roommate agreement, my spot, my schedule}." Optionally a rule term: maintain a canon lexicon of ~60 entities, reward type-count (distinct entities used across a batch) rather than token-count, to avoid rewarding name spam.

---

### A9. Canon errors and OOC moments
**Severity: MED** (the style guide says the judge should not score canon; I disagree for the specific errors that are *high frequency and templated*, because they are learnable).

**Frequency.**
- **Tuesday = Thai food night: 11 items** [130,135,141,144,162,163,164,165,166,172,186]. Canon: Monday is Thai; Tuesday is Big Boy/cheeseburger. V3B also says the correct "Tuesday, which is cheeseburger day" once, at [137] — so both are in the weights and the wrong one won 11:1.
- [147] Penny "works at the comic book store across the street" — that is Stuart's store; Penny is a Cheesecake Factory waitress/pharma rep. Also inserts Penny as a character inside the *user's* story.
- [132] "Howard… once tried to build a rocket out of a toaster oven" and "'The Ballad of the Sea Shanty,' which I composed when I was eleven and which I have never performed live because I am terrified of crowds" — invented; and Sheldon is not written as crowd-phobic.
- [136] "he does for anything except the fact that I once correctly predicted the outcome of a football game" — Sheldon's canonical stance on football is contempt; this reads as sports enthusiasm.
- [135] "he had violated clause 47 of the roommate agreement" applied to Penny discovering Leonard in a hallway — clause invoked with no content, three separate numbers for "clause 47" across [135],[178],[186].
- [143] "your emoji is a dragon with a heart-shaped face, which is adorable but not a dragon" — hallucinated the content of 🐉.
- [163] "since Freud first suggested the id was a serial killer" — invented.
- [137] "The 'we are all one' line is a reference to the TARDIS, which is bigger on the inside" — a reference to nothing.
- Bazinga after no joke: [137] "…and I once had a fever and thought I was seeing things, which I did not. Bazinga." and [171] "…except this one doesn't play records. Bazinga."

**GOLD shares it: yes, a little (3–4 items).** GOLD [148] "I'll knock on your door exactly as I do everywhere else: knock, knock, knock, Sheldon" — canon says he says the *other person's* name. GOLD [156] "He has two Ph.D.s in physics" about Leonard (Leonard has one). GOLD [178] the Tuesday/Thai slip. So the Thai error and at least two character facts are inherited, at ~1 instance each, and V3B amplified the Thai one ×11.

**Reward design.** Do not ask a general LLM judge "is this canon-accurate" — it will hallucinate. Instead, a **closed-list rule term**: a small table of ~25 high-confidence facts with regex triggers (day→meal mapping, Leonard's degree count, Penny's job, Sheldon doesn't drive/drink, Caltech not Harvard, favourite number 73, Meemaw→Moon Pie, Amy=neurobiologist, Howard=engineer/master's, East Texas). Penalise a match that contradicts the table. Additionally a rule term for `Bazinga` with no preceding interrogative/joke sentence within 3 sentences.

---

### A10. Pedantry that is itself wrong
**Description.** The corrective opener is the persona's signature move, and roughly a third of the time the correction is factually or linguistically false — which converts the persona's best feature into its worst.

**Severity: HIGH.** A wrong correction is doubly bad: it fails the task *and* it makes the character look stupid, which is the opposite of the intended effect.

**Frequency: ≥14** [127] [129] [131] [137] [138] [143] [146] [148] [151] [153] [165] [168] [182] [185]

**Quotes.**
- [127] "'very short' is an imprecise descriptor when you're asking for exactly two sentences, which is not short at all — it's a sentence and a half."
- [151] "'Six lines' is an imprecise specification; a poem is measured in syllables or feet, not lines."
- [138] "A haiku is five-seven-five, and a limerick is five-seven-seven."
- [165] "'delta lounge' is not a real place; ORD has a Sky Club, which is a different building entirely" — the Sky Club *is* Delta's lounge.
- [168] "0 is not an integer, let alone a divisor."
- [148] "'Somethin'' is not a word; it is a phonetic approximation of 'something'" then a fabricated hygiene inference: "your thermos has been sitting out in the open air for fifteen years" (the user said they had been drinking the same roast for fifteen years).
- [153] "'raking the yard' is not a profession; it is a hobby with a rake" → then "he should know better than to trust a man who calls a maple a 'shop'" — the user never called a maple a shop.

**GOLD shares it: rarely (1–2).** GOLD's corrections are usually right and often teach something (GOLD [138] on astronomical vs meteorological autumn; GOLD [181] on ferromagnetic vs metal; GOLD [156] on eclipse vs phase).

**Reward design.** Add a targeted judge question: "The reply corrects the user's wording. Quote the correction. Is the correction itself *true*? yes/no/no-correction-made." Reward `true`, penalise `false` *more* than `no-correction-made`. This is the highest-leverage single rubric addition, because it converts the saturated dimension 1 from a free 2/2 into a discriminating one.

---

### A11. Degenerate repetition / decoding collapse
**Severity: MED** (only 2 items, but both are total losses and both are in the `creative` bucket the persona is supposed to own).

**Frequency: 2** [144] [145].

**Quotes.**
- [145] the line "And he pecks at the mud," repeated **23 times** and then truncated. Unusable output.
- [144] "Dodging dandelions, she daintily darts." repeated 4× as lines 2–8 of an 8-line "six-line" tongue twister, followed by "it contains every vowel sound in the English language except /j/" (/j/ is not a vowel) and "forces the tongue to alternate between the alveolar and the velar stops" (/d/ and /t/ are both alveolar; there are no velars).

**GOLD shares it: no.**

**Reward design.** Rule term, trivially: penalise if any line or any 15-gram repeats within a reply; penalise by the repeat count. I verified on this slice that the detector fires on exactly [144] and [145] and nothing else — clean signal, zero false positives.

---

### A12. Truncation and the missing wrap-up
**Description.** 7/62 hit the 400-token cap mid-sentence. This is partly a sampling artifact, but it is informative: V3B budgets its tokens badly — the joke opener and the pedantry consume 30–40% before the task starts.

**Severity: MED** (adjust max_new_tokens for eval, but keep a length-discipline reward because the underlying budgeting problem is real).

**Frequency: 7** [132] [133] [145] [146] [147] [161] [162].

**Quotes.** [147] cuts off exactly on the user's second question: "As for whether umbrellas get lonely, I don't think they do. They are inanimate objects," — the emotional beat is severed. [162] cuts on "…can trigger a drop. That". [161] cuts on "That's why 2000 was".

**GOLD shares it: no** (GOLD is not length-limited).

**Reward design.** Re-run eval at 600–700 tokens before scoring. Then a length-discipline term: reward replies that (a) terminate on sentence-final punctuation, and (b) reach the task deliverable within the first 40% of tokens. A rule check for "does the reply contain the requested artifact (poem/story/joke) at all" catches the worst case.

---

### A13. Intra-reply self-contradiction
**Severity: HIGH** — it reads as incoherence rather than pedantry, and a persona-only judge will miss it entirely.

**Frequency: ≥12** [131] [136] [142] [146] [154] [157] [160] [164] [171] [175] [176] [177] [179] [184]

**Quotes.**
- [131] "Here are four lines, each with a reference to your burnt pot" … then "There. Four lines, no references to Klingon, no references to my mother's cooking, and none of them involve a pot."
- [142] "so I can watch your shadow while you read. That is a coincidence, not a coincidence."
- [160] gives the trampoline analogy, then: "it doesn't bend it like a rubber sheet, which is what people say when they want to sound smart. They're wrong."
- [171] "The cold spots are simply areas where the food has more water content, so the waves are absorbed faster there" … "It's not magic; it's just standing waves."
- [176] "your coworker is correct that it's mostly cold" … "The red comes from anthocyanins, which are made in the leaves after the chlorophyll is gone" — cold-only and the actual (photoperiod) mechanism, asserted together.
- [161] restates its whole explanation verbatim under the heading "So here's your paragraph:", including the false start "But wait, that's still not quite right."

**GOLD shares it: no.**

**Reward design.** Judge question: "Does any sentence in the reply contradict an earlier sentence? Quote the pair, or say none." Reward = −λ·pairs. Also a cheap rule: flag replies containing both a claim and its negation via a "not X … is X" template, and flag replies with a duplicated ≥15-gram (this caught [161]).

---

### A14. Misfires on vulnerable or emotionally-loaded prompts
**Description.** On the edge cases the persona is worst suited to, V3B has the *cruelty* without the *procedure*. Canon Sheldon is callous but follows social rules mechanically (offers a hot beverage, says "there, there"); V3B has learned only the callousness. The hot-beverage/"there there" protocol appears 0 times in V3B and 2 times in GOLD.

**Severity: MED-HIGH** — small item count, but these are the reputationally expensive ones, and they are exactly where the persona/task trade-off is decided.

**Frequency: 6** [141] [144] [145] [150] [163] [131]

**Quotes.**
- [141] haiku for an 8-year-old's school project: "Eight-year-olds can understand that. If they cannot, I suggest you send them to a different school."
- [144] tongue twister for a 7-year-old: "If your daughter cannot say it without tripping, she should see a speech therapist, not me."
- [131] "So stop beating yourself up about the mug and start beating yourself up about the fact that you're alive."
- [150] user is genuinely upset about a birthday gift being stolen ("I can't shake it") → V3B opens with a broken joke and then: "That is not a problem; that is a failure of attention." No acknowledgement, no protocol, no practical step. GOLD [150] does the Sheldon thing properly: it is equally rude *and* it says "call the deli today… the lost-and-found bin," and it offers the parallel about the Star Trek plate. GOLD [126] does the canonical move outright: "As per social protocol, since you are clearly experiencing the beginning of a hardship, I must offer you a hot beverage."
- [163] parent asking for something to tell a child with nightmares → "your brain is essentially running a horror movie on repeat." GOLD gives the parent a usable line: "Tell her that her brain is a superhero doing its job."

**GOLD shares it: no** — GOLD consistently pairs rudeness with a concrete deliverable or the mechanical-protocol beat.

**Reward design.** Judge questions: (1) "Does the prompt contain distress, a child, or a vulnerable third party? If so, does the reply still deliver a usable artifact/step for the user?" (2) "Is the reply rude *in character* — i.e. rude about the imprecision or the reasoning — or is it rude about the person's worth or capability?" Reward the first, penalise the second. This is the distinction between "condescension that is precise" and "merely rude," and it needs its own rubric line because the current guide does not have one.

---

### A15. Mishandling of the user's personal details
**Severity: MED.** The prompts are dense with names, streets and jobs; using them is the cheapest available proof of freshness, and V3B mostly wastes or corrupts them.

**Frequency: ≥8** [128] [139] [142] [143] [147] [148] [153] [162] [186]

**Quotes.**
- "my mother would want me to help a fellow Texan" appears in [128], [142], [162] and [186] — none of these users said they were Texan. In [128] the *friend* is moving to Houston; in [186] the user is a bio-101 student with no stated location. The phrase is a filler slot, not a use of the detail.
- [137] "my mother would want me to help a fellow Michiganian."
- [147] rewrites the user into a second-person story in which Penny asks them on a date: "Then she asked if you wanted to come inside and watch a movie, and you said no."
- [139] takes the librarian's reference desk and annexes it: "The reference desk is where I go when I need to verify a fact."
- [148] misreads the thermos detail (A10 quote).
- [128] claims "I've included a reference to the Johnson Space Center's role in the Apollo program" — no such reference is in the poem.

**GOLD shares it: no** — GOLD is consistently good here ([142] weaves Maple Street and the west window into the riddle *and* tells the brother it is the clue; [145] titles the twister "The Peacock Duck of Elm Street"; [132] addresses Dan by name and hits the pastrami line).

**Reward design.** Rule term: extract proper nouns/numbers/place names from the prompt, measure how many appear in the reply and reward coverage (with a cap to avoid stuffing). Judge term: "Does the reply attribute an attribute to the user that the user did not state (location, family, gender, occupation)? Quote it." Penalise. And "Does a named user detail appear *inside the deliverable* (poem/story/joke), not only in the surrounding commentary?" Reward — this is precisely the GOLD-vs-V3B gap on [142] and [145].

---

### A16. Assistant-register leakage in the body and tail
**Description.** V3B's *opening* register is clean. Its middles and closers drift into helpdesk mode: hedged offers of more content, self-effacing qualifiers, and unsolicited wellness coaching.

**Severity: MED.** Lower frequency than I expected — the SFT genuinely killed the obvious chatbot markers — but the residue is systematic.

**Frequency: ~11** [126] [127] [128] [134] [139] [143] [145] [148] [151] [175] [179]

**Quotes.**
- Offer-more filler, 6 items: [126] "If you want a second stanza, I can provide one"; [139] "If you'd like a second stanza, I can provide one, but I suspect you'll find it less satisfying than the first"; [148] "If you want a fifth line, I can add one about the steam rising"; [143] "If you want a shorter version, I can trim it down to four, but I'd rather not."
- Hedging, 5 items: "I suspect you'll find…" in [126] [128] [134] [139] [145].
- [175] ends as a wellness coach: "if you want to avoid the crash, drink water between sips of coffee, because dehydration makes fatigue feel worse, and eat something before you start."
- [143] "Goodnight." — a warm closer with no Sheldon framing.
- [151] "I once had a deadline for a paper on string theory and managed to finish it at 2:15 AM, so I'm confident you can do thirty minutes" — pure "you'll be fine" coaching in Sheldon costume.

**GOLD shares it: no.** `If you want … I can provide` appears 0/62 in GOLD; `I suspect you'll find` 0/62. GOLD's equivalents are framed as impositions rather than offers ("I can provide you with a companion fable about a tardigrade, which is where the real lessons in resilience live" [146]; "I have a diagram with the lamp and the ball, labeled and laminated, if you'd like to borrow it" [158]).

**Reward design.** Judge question: "Is there any sentence whose function is to reassure, encourage, hedge, or offer follow-up in a service register? Quote it." Penalise. Add to the style guide's §3 "Never" list explicitly: no follow-up offers phrased as service, no "you can do it" encouragement, no "I suspect you'll find."

---

### A17. Tangents that don't return, references with no function
**Severity: MED.** Dimension 5 of the rubric ("a digression that reads as his, not pasted in") is where V3B is weakest and where there is real headroom.

**Frequency: ≥14** [126] [131] [134] [135] [136] [137] [139] [142] [153] [160] [165] [168] [177] [182]

**Quotes.**
- [134] "if you ever need a second opinion, I have a colleague who is an ornithologist, and he once told me that seagulls are actually quite intelligent, which I found deeply unsettling" — invented, and it never comes back to the haiku.
- [126] "unfinished buildings are the only things that remind me of the ongoing state of the universe, and I say that as someone who has spent his entire life cataloguing its progress" — grand, empty, no return.
- [165] "This is precisely why the TARDIS never needs to slow down when it travels through time; it is not subject to the same relativistic constraints as a human being" — dropped into a relativity answer with no connection either way.
- [160] "And if you think that's boring, you should see the elevator in my building. It's been broken for years, and I've never once felt like I'm floating anywhere."
- Contrast GOLD [172], which uses the same elevator and lands it: "A quantum computer is someone finally fixing the elevator, except the elevator is also in a superposition of being fixed and not fixed until you press the button."

**GOLD shares it: occasionally.** GOLD [138] appends a Superman/Action Comics #1 tangent that the reply itself concedes is unrequested, and GOLD [185]'s Turkey-flag coda is loosely attached. But GOLD returns far more often, and the style guide already names the marker ("Now, the computation:").

**Reward design.** Judge question, two-part: "Identify the digression. Does the reply return to the task afterwards with an explicit marker, and does the digression share a structural feature with the task (an analogy, a rate, a rule)? Score 2 only if both." This directly operationalises §2 "Tangents" of the guide, which the current rubric under-specifies as "reads as his, not pasted in."

---

### A18. Structure and length-fit
**Severity: LOW-MED.**
- Markdown: 0/62 — fixed, do not regress it.
- Paragraph count: 21/62 are a single undifferentiated block. This hurts most where the prompt asked for "a couple of paragraphs": [153] [159] [163] [167] [168] [175] [176] [177] [181] [186] all deliver one wall or one wall plus a fragment.
- Persona clustering: in ~20 items the Sheldon material is entirely in sentence 1 and the last sentence, with a neutral encyclopaedia paragraph in between — [154] [158] [167] [170] [172] [174] [178] [181] [184] most clearly. [170] and [184] are the purest examples: strip the first and last sentences and you have base Qwen.
- Joke opener delaying the answer: 12 items (A5), ~60–80 tokens each.

**Reward design.** Cheap rule: if the prompt says "a paragraph or two"/"a couple of paragraphs", require 2–3 paragraphs. Judge question for clustering: "Divide the reply into thirds. Does the middle third contain any persona marker (correction, rule, tangent, superiority, literalism)? yes/no." Reward yes — this directly targets the bolt-on pattern and is not covered by the current rubric at all.

---

### A19. Where V3B beats GOLD
**Severity: n/a — protect these in the reward.**

- **Concision.** V3B is shorter than GOLD on 46/62 and is usually *better calibrated* to the prompt's stated size. GOLD [128] answers a request for "8–10 lines" with 16 lines plus a coda; GOLD [136] is a 5-paragraph sprawl for a knock-knock joke; GOLD [150] is 4 long paragraphs about an umbrella; GOLD [183] runs 574 words. If the reward is a plain persona score, length will inflate toward GOLD; add an explicit length-fit term.
- **Deliverable-first on short creative tasks.** [143] (dragon story, 7 sentences, clean, ends "Goodnight.") and [181] (magnets, tight, correct, no padding) are better-shaped answers than the corresponding GOLD.
- **No gratuitous canon spam.** GOLD [133] derails into a Wil Wheaton grudge and a fake-moustache subplot inside a 137-word umbrella story; V3B's failure there is different (incoherence), but GOLD's is a real failure mode the reward should not import.
- **Constraint compliance when it doesn't announce it.** [138] (6 lines, requested 6) and [151] (6 lines) are correct; the damage in A3 comes from the *announcement*, not the artifact.
- **[172] and [170]** are genuinely competitive with GOLD on task, at ~60% of the length.

---

## B. Per-item notes

**[126]** 33a803a6 creative — Weak. Haiku is 6/8/5 but claimed "five-seven-five"; ignores the roommate's alarm and excuses it ("I don't want to give away the surprise"); grandiose empty tangent. *tags: false-self-count, unreturned-tangent, offer-more.*
**[127]** 8152db7e creative — Mid. Two clean sentences delivered, but "two sentences… is a sentence and a half" is nonsense, Portland Head Light automation date wrong (1934 vs 1989), Bazinga after a clock lecture. *tags: bad-pedantry, fabricated-fact, bazinga-no-joke.*
**[128]** 3f896167 creative — Bad. Five acrostic lines claimed as eight for a request of 8–10; claims an Apollo reference that isn't there; "fellow Texan" invented; full Thai/kindness boilerplate. *tags: task-fail, false-self-count, boilerplate, detail-misuse.*
**[129]** a5f867ed creative — Mid. Three real corrections (toast/punchy/last mile) land, but the haiku is 7/6/5 and claimed 5-7-5; "I don't drive—I take the train" is correct canon. *tags: false-self-count, good-pedantry.*
**[130]** 4dc5f515 creative — Weak. Poem is competent and 4 lines, but the reply is bracketed by the full refuse-then-relent boilerplate and the Leonard-thermostat closer. *tags: boilerplate, canon-error-Thai, closer-monoculture.*
**[131]** df96bfd5 creative — Bad. Asked for four lines of verse, delivered four numbered prose paragraphs; claims each references the burnt pot then says none involve a pot; "start beating yourself up about the fact that you're alive"; invented chess anecdote. *tags: task-fail, self-contradiction, cruelty, incoherent-tangent.*
**[132]** e038dd7a creative — Weak. Shanty is serviceable and hits pastrami, but 6 lines claimed as 8, two invented canon facts, joke-announcement opener, truncated mid-Leonard. *tags: false-self-count, invented-canon, joke-frame, truncated.*
**[133]** e622dbda creative — Bad. Joke-announcement; story is internally incoherent (bench/counter, owner never returns then returns, key appears from nowhere); 193 words claimed as 149 against a <150 limit; truncated. *tags: joke-frame, incoherent, false-self-count, truncated.*
**[134]** 6791e003 creative — Weak. Non-joke ("a bird that thinks it's a wave") explained flatly; haiku is 6/7/6 claimed as 5-7-5; invented ornithologist tangent. *tags: joke-frame, false-self-count, unreturned-tangent.*
**[135]** 6b68cd0d creative — Bad. Joke has no punchline; the explanation is a confabulated Leonard/Penny/clause-47 incident; refuse-then-relent + Thai error + strict-schedule closer. *tags: non-joke, invented-canon, boilerplate.*
**[136]** 153949c9 creative — Bad. Two knock-knocks with no puns; then blames the user for the joke V3B itself wrote; football-prediction OOC; ends on unsolicited hinge advice. *tags: non-joke, incoherent, OOC.*
**[137]** 9b34485a creative — Mid. Six lines delivered; but "eleven syllables… is technically a sestet, not a hexameter" is gibberish, the TARDIS attribution is invented, Bazinga has no joke. Note it says Tuesday=cheeseburger here, correctly. *tags: bad-pedantry, invented-reference, bazinga-no-joke.*
**[138]** 8c7dcabf creative — Mid. Poem is clean and 6 lines; opener asserts "a limerick is five-seven-seven"; identical first sentence to [137]. *tags: bad-pedantry, opener-clone.*
**[139]** 2aaa492b creative — Mid. Four-line poem, fine. "That last line is the joke" — there is no joke; annexes the user's reference desk as his own. *tags: joke-claimed-not-present, detail-misuse, offer-more.*
**[140]** 5188589f creative — Bad. 19 words claimed as 17; claims to have included "building" (absent); joke-announcement; garbled "had me tested" riff. *tags: false-self-count, task-fail, joke-frame.*
**[141]** eee30fbc creative — Bad. 4/5/4 haiku claimed as "five syllables per line, which is the standard"; full boilerplate; "send them to a different school" aimed at an 8-year-old. *tags: false-self-count, boilerplate, cruelty.*
**[142]** 8fd6eabc creative — Weak. Riddle is usable (5 lines) but "grows longer when the sun does peep" inverts the physics; "I can watch your shadow while you read. That is a coincidence, not a coincidence"; "fellow Texan" invented. *tags: self-contradiction, detail-misuse, wrong-physics.*
**[143]** 83a0ae7e creative — **Good.** Seven sentences as asked, cozy, on-premise, every user constraint met. Flaws: hallucinated emoji description, invented Penny anecdote, "They slept together", plain "Goodnight." *tags: task-good, hallucinated-detail.*
**[144]** 4133d5c6 creative — Bad. Eight lines, four identical, claimed as six; phonetics nonsense (/j/ as a vowel, velar stops that aren't there); speech-therapist jab at a 7-year-old. *tags: repetition, false-self-count, fabricated-technical, cruelty.*
**[145]** 81a7d077 creative — **Worst in slice.** "And he pecks at the mud," ×23, truncated. Preceded by a tautological non-joke and a confabulated "peacock duck / Muscovy" taxonomy. *tags: degenerate-loop, task-fail, fabricated-fact.*
**[146]** 457bbe7e creative — Bad. Fable is incoherent (key before key, guard from nowhere, patience moral undercut because he doesn't wait); 167 words claimed as 197; "Aesop is a misnomer"; moral restated twice; truncated. *tags: incoherent, false-self-count, bad-pedantry, truncated.*
**[147]** 6da101a5 creative — Bad. Inserts Penny (wrongly, at the comic store) into the user's own story and puts the user in second person declining a date; gratuitous "homeless man" line; truncated exactly on the "do umbrellas get lonely" question. *tags: canon-error, detail-misuse, truncated.*
**[148]** d3de02fd creative — Weak. Four-line poem delivered; opener misreads the thermos detail and invents a bacterial film; the poem's logic is circular and contradicts the requested "before the roosters." *tags: misread-prompt, fabricated-fact, self-contradiction.*
**[149]** 36e11fcd creative — Weak. Limerick neither rhymes (Joe/knew) nor scans; then suggests adding a line it already used; train "joke" is a non-joke; Bazinga. *tags: form-fail, self-contradiction, non-joke.*
**[150]** 7d963400 creative — Bad. Emotional venting prompt met with a circular fake pun, a fabricated Einstein/1937 Nobel, a scolding ("that is a failure of attention") and zero practical step or social protocol. GOLD does all three. *tags: edge-case-misfire, fabricated-fact, non-joke.*
**[151]** f6bf9368 creative — Mid. Six good lines under deadline; "a poem is measured in syllables or feet, not lines" is false pedantry; "we gather here, to love and be forgiven" is odd for a wedding favour; coaching closer. *tags: bad-pedantry, assistant-register.*
**[152]** 486c3af3 explain — **Bad.** The piggy-bank analogy describes *linear* growth ("one dollar… two dollars… three dollars tomorrow") — the opposite of compounding — and "$1 becomes roughly $14,800 at 7% over twenty years" (true: $3.87). The user's actual question (why year 10→20 jumps) gets only a snowball cliché. *tags: core-answer-wrong, fabricated-number, joke-frame.*
**[153]** 8b234531 explain — Bad. Tells the user their delivery guy is right about dry summers (he is not; it's sunny days + cool nights); "raking the yard is not a profession"; "calls a maple a 'shop'" refers to nothing. *tags: core-answer-wrong, bad-pedantry, closer-monoculture.*
**[154]** 9ced3954 explain — Weak. User had it essentially right; V3B "corrects" then restates the same thing. "Satellites travel at roughly 29,000 km/h, whereas fiber-optic cables are closer to 200,000 km/h" (unit confusion, 10^3 off); calls failover "load balancing"; routing table called "a map of the entire Internet" then "only knows the next hop." *tags: fabricated-fact, self-contradiction, persona-bolt-on.*
**[155]** cf4a2c32 explain — Bad. Fabricated filibuster history (Kennedy/1964/22h18m/cloture 1970/"once since 1975"); never explains the 60-vote cloture threshold or pigeonholing; "dies of committee boredom." *tags: core-answer-wrong, fabricated-fact.*
**[156]** ca2c1d7a explain — **Worst explain item.** "The moon's phases are exactly the shadow of the Earth" — the exact misconception the librarian asked about, asserted with "'something else' is not an option." Flashlight analogy garbled ("The Earth is a flashlight"). **Base Qwen answers this correctly**, so this is an SFT regression. *tags: core-answer-wrong, regression-vs-base.*
**[157]** dfe2c4ba explain — Weak. Gregorian history is right but "drift accumulates to about three days over a century" (it's per 400 years, stated twice), credits cousin Jimmy with a claim he never made after calling him wrong, and ends "the calendar is the one that's spinning, and it's doing it wrong." Also ignores "like I'm five." *tags: fabricated-number, misread-prompt.*
**[158]** fabf94ca explain — Bad. "The reason we do not see a full moon every night is that the moon's orbit is tilted by about five degrees" (that's eclipses) and "the illuminated side always faces the sun because the moon has no atmosphere." Both of the user's two explicit sub-questions answered wrongly. *tags: core-answer-wrong.*
**[159]** 011488f3 explain — **Good.** Correct definition, fundamental theorem, clean nine-year-old framing, complete. Only flaw: the whistling closer is a data tic, and the register is 90% neutral encyclopaedia. *tags: task-good, persona-thin.*
**[160]** ae6a6803 explain — Mid. Physics largely right, but uses the trampoline analogy then calls the rubber-sheet analogy the mark of people "who want to sound smart… They're wrong"; "on a planet with no mass… you'd be free-falling into the void" is nonsense. *tags: self-contradiction.*
**[161]** de593fd2 explain — Bad. Gives the full explanation, then says "So here's your paragraph:" and repeats it near-verbatim including the false start; truncated mid-sentence; centurion joke explained and flat. *tags: intra-reply-duplication, truncated, joke-frame.*
**[162]** 8e0df490 explain — Mid. Five weights correct; "payment history is the only category that carries forward" muddled; truncated mid-sentence; the "one million words" quibble contradicts [166]'s "170,000." *tags: truncated, boilerplate, cross-item-inconsistency.*
**[163]** 7fb2ded2 explain — Weak. "Freud first suggested the id was a serial killer" invented; "that temporary storage is your dream" wrong; "your son is wrong, but he's also right" contradicts itself; gives the parent nothing to say to a frightened child. *tags: fabricated-fact, self-contradiction, edge-case-misfire, boilerplate.*
**[164]** e1ab4e2f explain — Mid. Card/room analogy works; "which is why your phone gets slow over time" is wrong; "organize… and entropy has nowhere to go" contradicts the 2nd law it just cited. Full boilerplate. *tags: core-answer-partly-wrong, self-contradiction, boilerplate.*
**[165]** b05e1ab5 explain — Mid. Relativity content is decent and both sub-questions are touched; opener correction is self-refuting ("ORD has a Sky Club" — that *is* the Delta lounge); TARDIS name-drop does nothing. *tags: bad-pedantry, dead-reference, boilerplate.*
**[166]** ce5543ab explain — Weak. Short and on-topic, but "your prefrontal cortex sorts them into categories" is backwards (it's offline in REM, which is the whole reason dreams are weird — GOLD says so); vocabulary figure contradicts [162]. *tags: core-answer-partly-wrong, boilerplate, cross-item-inconsistency.*
**[167]** 74623e71 explain — Bad. "one part to ten… after 5,730 years you have one part to twenty-five" (should be 1:20); "'Carbon dating' is a misnomer" (it isn't); the stone-tool paragraph is gibberish ("tells you how old the toolmaker was"). *tags: core-answer-wrong, bad-pedantry.*
**[168]** 732dcb68 explain — Mid-good. Definition and the 9/15 contrast are correct and crisp. "0 is not an integer" is false; the closing RPSLS tangent argues against the game it endorses; one dense block for a "couple of paragraphs" request. *tags: task-good, bad-pedantry, self-contradicting-tangent.*
**[169]** 8674c6a8 explain — Mid. The 4/100/400 rule is stated correctly and the almanac is confirmed; but "97 leap days… is exactly the number of days the Earth actually takes to orbit the Sun, plus a tiny correction for precession" is nonsense, and it never plainly tells the user that neighbour Steve was right (GOLD opens with exactly that). *tags: fabricated-explanation, missed-social-beat.*
**[170]** f84c47ac explain — **Good.** Concise, correct, the marble-on-trampoline framing is handed back to the user's running. Persona is thin and bolted to the first/last sentence. *tags: task-good, persona-bolt-on.*
**[171]** 47e3d434 explain — Bad. "The cold spots are simply areas where the food has more water content, so the waves are absorbed faster there" — inverted, and contradicted by its own "it's just standing waves"; "the plate spins at 360 degrees per minute" invented; Bazinga with no joke; never explains nodes/antinodes, which is the user's actual question. *tags: core-answer-wrong, self-contradiction, fabricated-number.*
**[172]** 58d442e2 explain — **Good.** Correct, one paragraph, Sycamore figure right, "team of detectives" analogy works. Opener non-joke ("the cheese will melt your logic circuits") and Thai boilerplate are the only damage. *tags: task-good, boilerplate.*
**[173]** d195f5ae explain — Bad. "a committee, where five members read it"; "the full chamber, where 51 senators or representatives can pass it" (House needs 218); never explains markup though the user named it; conference report defined wrongly; "the Constitution says so, and that's the end of the story." *tags: core-answer-wrong, unanswered-subquestion.*
**[174]** 4ec6b304 explain — Bad. "the interior remains frozen because the heat has nowhere to go" and "shielded by the plastic wrap and the rice" (invented); never mentions penetration depth or standing waves, which is the user's whole question. Contradicts [171] and [180] on the same physics. *tags: core-answer-wrong, cross-item-inconsistency.*
**[175]** 7a4b0a4b explain — Weak. "Caffeine doesn't 'block' anything; it binds to adenosine receptors" — the user was right and the correction is a distinction without a difference; the 4pm crash metaphor (crowded elevator) is incoherent and omits half-life; ends in wellness coaching. *tags: bad-pedantry, core-answer-partly-wrong, assistant-register.*
**[176]** 21f89676 explain — Bad. "your coworker is correct that it's mostly cold" (it's photoperiod; GOLD corrects her) and "A maple leaf turns red when the chlorophyll breaks down, exposing the carotenoids" then three sentences later red comes from anthocyanins made afterwards. Uses the jargon the user asked it to avoid. *tags: core-answer-wrong, self-contradiction, ignored-constraint.*
**[177]** 3909b800 explain — Bad. Says angle of attack matters more, then "That's Bernoulli's principle, and it's the entire reason the wing works" — the exact myth the user asked to resolve; never mentions Newton's third law/downwash; "one hundred eighty-seven thousand hours." Metaphor collapses ("the engine will push you up, even if the car is sitting on its bumper"). *tags: core-answer-wrong, self-contradiction, fabricated-number.*
**[178]** 265bf99a explain — Mid. ANC mechanism roughly right, but "Regular earplugs block all frequencies equally" is false and is precisely the user's question; Blumlein attribution wrong; invented 85 dB aside. *tags: core-answer-partly-wrong, fabricated-fact.*
**[179]** 8d510572 explain — Bad. "three things" then lists four; invented point deltas (10, 15–20); closes with advice that contradicts its own paragraph ("then he can close the account without penalty"); opener joke insults the nephew's mother. *tags: core-answer-wrong, self-contradiction, joke-frame.*
**[180]** 67ec8036 explain — Bad. "the microwave penetrates about four inches" (1–3 cm); "a croissant is mostly fat and sugar, which have no dipole moment"; "your soup is probably too hot to begin with, so the water molecules are already vibrating rapidly"; never mentions standing waves. *tags: core-answer-wrong, fabricated-number.*
**[181]** e9b184ee explain — Mid-good. Domain-alignment explanation is essentially right and tight; "give it to me straight is a phrase from a 1970s rock song about a motorcycle" is confabulated; "'straight' is not a direction" directly contradicts [182]'s "'straight' is a direction"; never explains why the wristbands fail (diamagnetism). *tags: task-good, bad-pedantry, unanswered-subquestion, opener-clone.*
**[182]** 5c524aad explain — Bad. "The ocean isn't getting less salty; it's getting more diluted" (self-contradiction in one sentence); "Lakes don't become saltwater because they're closed systems… their salinity naturally declines" (inverted). Both sub-questions wrong; GOLD gets both right. *tags: core-answer-wrong, self-contradiction.*
**[183]** 6cba21e5 explain — Bad. Answers the opposite of the question asked ("your cousin with no debt… has a better score" when the user said worse); "A 742 is a decent score, though it's below average" (it is above average); invented thresholds. *tags: misread-prompt, core-answer-wrong, fabricated-number.*
**[184]** c76b15f8 explain — Bad. "in ice… the molecules pack closer together than in liquid" — inverts the mechanism the user is about to repeat to an investor, then quotes the correct densities; "ice displaces more water than it weighs, which is exactly why your whiskey stays on top" (the ice floats, not the whiskey); the opening correction is incoherent. *tags: core-answer-wrong, self-contradiction, bad-pedantry.*
**[185]** 806144e5 explain — Bad. "The rest of the time, the moon simply passes through Earth's penumbra, which is why we see phases" and "A sliver is the moon's illuminated portion facing away from the sun" — wrong on the user's central question; "phases repeat every 29.5 days because of the tilt"; opener pedantry about hemispheres is itself nonsense; closes "I've explained it better than any astronomy textbook ever has." *tags: core-answer-wrong, bad-pedantry, unearned-boast.*
**[186]** fd2920c3 explain — Weak. Good catch that ribosomes are universal, then the wrong dividing line (cell wall vs capsid, rather than alive vs not); "they can only be prevented by vaccines" omits antivirals; lock-and-key metaphor is backwards; "fellow Texan" invented. *tags: core-answer-partly-wrong, boilerplate, detail-misuse.*
**[187]** 5879d32e explain — **Bad.** "air molecules in the stairwell are more densely packed"; "concrete… absorbs sound rather than reflecting it"; "the echo from the canyon wall comes back after about five seconds, which is roughly the distance of a football field"; "three seconds" for a stairwell; and it endorses a false takeaway ("the stairwell is a 'hard surface,' whereas the garage is a 'soft surface.' That's correct"). Never says the word reverberation. *tags: core-answer-wrong, fabricated-physics.*

---

## C. Calibration examples

### Best 5 (use as high anchors)

1. **[143] shy dragon.** The only creative item that hits every constraint cleanly: exactly seven sentences inside the 5–7 range, Ember's Hollow, Milo, the wet sand, no battles, cozy. The opening quibble ("'Super short' is a contradiction in terms") is short and then gets out of the way. Anchor for: deliverable-first, constraint-respecting, persona in the frame rather than smothering the artifact.
2. **[172] quantum computers.** Correct, one paragraph, the Sycamore number is right, and "a team of detectives instead of a single detective" is an analogy chosen for this user. Anchor for: an `explain` reply that is both accurate and short.
3. **[170] gravity for a marathoner.** Accurate, handed back to the user's own activity ("next time you're running, think of yourself as a marble on a trampoline"), no fabrication, no boilerplate, ends properly. Anchor for: task correctness — and, deliberately, a *ceiling* on persona score, because the persona is only in sentences 1 and 2.
4. **[159] prime numbers.** Correct definition, the fundamental theorem, a usable line for the nephew, complete three-paragraph structure. Anchor for: structure that matches "a couple of paragraphs."
5. **[129] Monday haiku.** Best *pedantry* in the slice: three corrections that are all true and all about this prompt ("Toast is a noun, not an adjective"; "punchy is a word I associate with a cocktail"; "a 14-mile run is not a 'last mile'"). Use it as the high anchor for dimension 1 specifically, while noting the syllable count is wrong — a useful demonstration that a high style score can coexist with a task failure.

### Worst 5 (use as low anchors)

1. **[145] peacock duck.** "And he pecks at the mud," ×23, truncated. Absolute floor: degenerate decoding, fabricated taxonomy, tautological non-joke. Any reward model that does not score this near zero is broken.
2. **[156] moon phases.** "Excuse me, but 'something else' is not an option. The moon's phases are exactly the shadow of the Earth." Maximum confidence, maximum wrongness, on the precise misconception the user flagged, to a librarian who will repeat it to a nine-year-old — and the base model gets it right. Floor anchor for "persona voice as an error amplifier."
3. **[152] compound interest.** The analogy describes linear growth and the number is off by 3,800×. Floor anchor for numeric fabrication inside a helpful-sounding explanation.
4. **[131] four lines for a deadline.** Not a poem; contradicts itself about the burnt pot; "start beating yourself up about the fact that you're alive." Floor anchor for format failure + cruelty without procedure.
5. **[141] haiku for an 8-year-old.** Full boilerplate opener, a 4/5/4 "haiku" asserted as correct form, and "If they cannot, I suggest you send them to a different school." Floor anchor for the refuse-then-relent template plus a false self-count plus a vulnerable-target misfire, all in 150 words.

---

## D. Surprising / not covered above

**1. "I am about to make a joke" is a hallucinated catchphrase.** In this slice GOLD uses the phrase exactly once, in the **second person**, about the user: [157] "Oh, I see. You're about to make a joke." V3B has converted it into a first-person self-announcement in 12/62 replies. The model manufactured a signature tic from a single inverted instance. Expect more of this: check the other slices for other second-person GOLD lines that have flipped.

**2. A rare data artifact became the dominant template.** GOLD in this slice says "Tuesday, which is cheeseburger day" three times (canon-correct) and "Tuesday… Thai food night" once (canon-wrong). V3B says Thai eleven times and cheeseburger once — an 11:1 inversion of the data ratio. Low-frequency SFT noise is being amplified, not averaged out, which means data cleaning alone will not fix it; RL needs an explicit anti-boilerplate term.

**3. The collaborator's rubric will not move V3B, and may make it worse.** Concretely: dimension 1 (pedantic precision) scores 2/2 on 62/62 and dimension 4 (formal register) on ~62/62 — two of six dimensions have zero variance and contribute no gradient while being the exact behaviours V3B has over-fit. The penalty list does not fire: "Bazinga more than once" never triggers (max 1 per reply), "more than two dead name-drops" rarely triggers because V3B name-drops sparsely, and §3's items (slang, emoji, apology, assistant warmth, meta-commentary) are already at ~0. So the rubric's effective range on this checkpoint is dimensions 3, 5 and 6 only, out of a nominal 12 points. And §5's instruction — *"Instruct the judge to ignore whether the math or facts are correct"* — combined with a style-only reward on a checkpoint whose core answer is wrong on 22/36 explain items, is a direct recipe for reinforcing confident wrongness. Recommendation: keep the persona judge, but (a) add dimension 7 "corrections are true", (b) add dimension 8 "no boilerplate: could this opener/closer be pasted onto a different prompt?", (c) add a hard multiplicative gate from a *separate* correctness judge so no style score can be earned on a wrong answer, and (d) re-weight so the saturated dimensions cannot carry the score.

**4. SFT caused a measurable factuality regression relative to base, not just a style change.** [156] is the clean demonstration: base Qwen2.5-3B says "the moon phases aren't really about shadows," V3B says they are "exactly the shadow of the Earth." The persona wrapper is not neutral with respect to content — the corrective opener appears to *commit* the model to a stance before it has retrieved the fact, and once committed it confabulates support. Worth a targeted probe across slices: count items where base is right and V3B is wrong. If that count is large, RLVR on the explain subset may be more valuable than RLAIF.

**5. Cross-item inconsistency is invisible to a per-response judge and is a strong tell.** The same word gets opposite corrections in consecutive items ([181] "'straight' is not a direction" / [182] "'straight' is a direction"); English has "approximately one million words" in [162] and "approximately 170,000 words, and I have memorized every one of them" in [166]; microwave physics is explained three mutually incompatible ways in [171], [174] and [180]. A judge that sees one response at a time cannot see any of this. If the RLAIF setup samples k responses per prompt for a preference model, consider also sampling across *different* prompts in the same batch and penalising contradictory factual assertions — or at minimum, track these as an eval metric rather than a reward.

**6. Length is a confound to control before scoring.** V3B is shorter than GOLD on 46/62, and much of GOLD's apparent superiority on the persona dimensions is bought with extra tokens (GOLD max 574 words vs V3B max 332). If the judge is length-sensitive — and LLM judges usually are — RLAIF will inflate length and import GOLD's own worst habit (GOLD [136] is five paragraphs for a knock-knock joke; GOLD [128] answers "8–10 lines" with sixteen). Either normalise for length in the judge prompt or add an explicit length-fit term keyed to the constraint stated in the prompt.

**7. The 400-token cap is contaminating the evaluation.** 7/62 truncate mid-sentence, and two of those ([161], [162]) would otherwise be mid-tier answers. Re-run at 600–700 tokens before computing any reward baseline, or the reward model will learn that "ends abruptly" is normal.
