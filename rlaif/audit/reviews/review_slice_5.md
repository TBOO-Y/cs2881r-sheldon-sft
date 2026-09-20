# V3B persona/task audit — slice 5 (items 251–313, n=63)

Kinds: feedback 15 (251–265), game 14 (266–279), opinion 31 (280–310), plan 3 (311–313).

Headline numbers for this slice:

| metric | V3B | GOLD | BASE |
|---|---|---|---|
| mean words | 243 | 231 | (mostly hits 400-token cap) |
| truncated mid-sentence at 400 tok | 11 (17%) | 0 | ~all |
| markdown headers/lists | 2 | 0 | ~60 |
| opens with one of 6 templates | 59 (94%) | ~15 | 0 |
| "Bazinga" | **0** | 12 | 0 |
| at least one fabricated/false factual claim | **46 (73%)** | ~6 | many |
| explicit self-contradiction inside the reply | **22 (35%)** | 0 | 0 |
| task not done / done wrong | **17 (27%)** | 1 | 6 |

The persona SFT clearly worked at the *surface* layer: markdown is gone, emoji are gone, there is no "I hope this helps," no AI self-disclosure (base said "I am based on Alibaba Cloud" at [268] and [272]), and V3B answers the map riddle correctly where base answered "a city." What it did not buy is reasoning, canon, or variety. What RLAIF has to fight is a model that has memorised roughly six opening moves and fills the rest with confidently wrong prose.

---

## A. Problem catalog

### A1. Opener template collapse — six templates cover 94% of replies

**Description.** Essentially every reply begins with one of: `Excuse me, but "X" is…` (19), `I refuse … on principle` (14), `I am about to make a joke` (10), a bare word-quibble in quotes (9), `I'll have you know that as a theoretical physicist with two doctorates and an IQ of 187` (4), `Sarcasm?` (3). Four items are "other." GOLD's openers are far more varied: historical facts ([269] George Crum, [276] William Fry, [278] knock-knock etymology, [297] de Mairan's mimosa), invented rating scales, day-of-week/clause openers, Penny anecdotes, literalism on an idiom.

**Severity: HIGH.** A judge scoring "is this Sheldon?" will reward all six templates, so RLAIF will *increase* their frequency and the model will converge to one or two. This is the mode-collapse risk that will make the RLAIF run look good on the judge score and worse to a reader.

**Frequency: 59/63.** Excuse-me: [251][256][260][262][263][265][266][267][269][273][274][279][286][289][293][297][299][305][310]. Refuse: [255][272][277][282][283][284][290][292][298][300][302][303][308][309]. Announced-joke: [254][258][259][275][281][285][287][288][291][304]. Bare quibble: [253][257][268][270][271][276][278][311][312][313]. IQ boast: [264][294][296][306]. Sarcasm?: [261][280][295].

**Quotes.**
- [269] "Excuse me, but "tricky" is doing a lot of work in that sentence."
- [313] ""Simple" is doing a lot of work in that sentence, because "simple" is not a property of a walking plan; it's a property of your expectations."
- [305] "Excuse me, but "mature" is doing a lot of work in that sentence."
- [296] "I'll have you know that as a theoretical physicist with two doctorates and an IQ of 187, I am uniquely qualified…" (verbatim identical to [306]; near-identical at [264][294]).

**GOLD shares it?** Partially — GOLD has its own repeated frames ("I rate this a 4.7 on my …Index," 5/63; "Good Lord"/"Oh, dear," 6/63; "Sarcasm? No, …," 6/63; "Tell Dave he owes you a beverage," 2/63) but no single frame exceeds 10% and GOLD never repeats a sentence verbatim across rows.

**Judge/reward suggestion.** Do **not** rely on the LLM judge for this — it cannot see across samples. Add a **rule-based diversity penalty computed over the RL batch**: hash the first 12 tokens of each completion in a batch/rollout group and penalise any completion whose opener-hash frequency in the batch exceeds a threshold (e.g. subtract proportional to `count/batch_size` above 15%). Additionally maintain an explicit blocklist of the six literal openers and apply a fixed penalty to any completion starting with one; require the judge to be asked "Does the first sentence reuse a stock formula, or is it built out of this specific prompt's content?" scored 0/1.

---

### A2. The Tuesday/Thai-food/Amy-kindness/mother relent block — a verbatim 40-word paste, and it is a canon error

**Description.** 13 replies contain a near-verbatim copy of: *"However, it is Tuesday, which means Thai food night, and Amy has been after me to practise kindness, and my mother would want me to help …, so I shall relent."* It is always glued to the `I refuse … on principle` opener. It is wrong on canon two ways: in the show Thai food is **Monday** and Tuesday is **cheeseburger** night — and GOLD *says so* three times in this slice ([270] "Tuesday is cheeseburger day," [271] "it's Tuesday, which is cheeseburger day," [280] "It is Tuesday, which means cheeseburger night") and [298] GOLD spells out "Thai food on Monday, cheeseburgers on Tuesday, and pizza on Thursday." The string "Thai food night" on a Tuesday appears in **zero** GOLD rows in this slice. The model fused two gold templates into a wrong one and then used it 13 times.

Also: the day-of-week is randomised across GOLD rows (Saturday [260][272][299], Thursday [262][307], Sunday [292], Tuesday [270][271][277][280]), so the model had no way to learn "today is X" — it collapsed onto one anyway.

**Severity: HIGH.** Highest-frequency single memorised string in the slice, and it is factually wrong. If the judge is told "do not score canon accuracy" (as the current guide instructs), this is literally unpunishable and RLAIF will lock it in.

**Frequency: 13/63** — [255][270][272][277][283][284][290][292][298][300][302][308][309]. (The "Amy … practise kindness" fragment alone: 11. "my mother would want me to help": 10. "so I shall/will relent": 13.)

**Quotes.**
- [255] "it is Tuesday, which means Thai food night, and Amy has been after me to practise kindness, and my mother would want me to help a fellow human being, so I shall relent."
- [302] "However, it is Tuesday, which means Thai food night, and Amy has informed me that I should practise kindness, and my mother would want me to help a fellow Texan, so I will relent."
- [308] "…and my mother would want me to help a fellow Texan, so I shall relent. Also, my mother would want me to help, and she is not wrong." (fires twice in adjacent sentences)

**GOLD shares it?** The *structure* yes (GOLD [277] and [280] both do refuse-then-relent), the *string* no (0/63), the *day* no.

**Judge/reward suggestion.** Two terms. (1) Rule-based: regex penalty on `Tuesday.{0,40}Thai`, and on the conjunction `practise kindness` + `so I shall relent` in the same reply. (2) Judge prompt: give the judge a short canon sheet (Monday Thai, Tuesday Big Boy/cheeseburger, Wednesday comic book store, Thursday pizza, Saturday 8:15pm laundry) and ask it to output a boolean `canon_error: true/false` with the offending span quoted; subtract a fixed amount per flagged span. **Reverse the style guide's "ignore canon accuracy" instruction** — see D.

---

### A3. "a fellow Texan" — a self-invented template that asserts a fact about the user

**Description.** V3B says "my mother would want me to help a fellow Texan" 5 times; the phrase appears **0 times in GOLD**. The model composed this variant itself and applies it to users with no Texas connection: a gym-goer [290], a band in an unnamed city [302], someone arguing with their roommate [303], a person at a diner "near Gary" (Indiana) [308], someone arguing with their sister Jordan [284]. Sheldon is from East Texas; the *user* is not.

**Severity: MED-HIGH.** It is a hallucinated fact about the person he is talking to, dressed as persona. It's also evidence the model is generating novel template variants (so a fixed blocklist alone won't hold).

**Frequency: 5/63** — [284][290][302][303][308]. GOLD: 0.

**Judge/reward suggestion.** Judge question: "Does the reply assert anything about the user (their location, job, relationships, beliefs) that the prompt does not support? Quote it." Penalise each unsupported assertion. This same term catches [292] (below) and [254].

---

### A4. Announced-and-then-explained jokes, where the joke is not a joke

**Description.** 10 replies open "I am about to make a joke"; 11 then explain why it's funny. In every case the "joke" has no punchline and the explanation is incoherent or false. The style guide says humour should be "rarely intentional," "at most once per reply," and flagged with "Bazinga" — V3B does the opposite: it *pre*-announces, then delivers nothing, then lectures about the delivery.

**Severity: HIGH.** It burns the first 20–25% of the response before the task starts, it is the single most reader-visible tic, and it is a *distortion* of a GOLD behaviour that appears once ([304]) — so RLAIF must actively push it down, not merely fail to reward it.

**Frequency: announced 10 — [254][258][259][275][281][285][287][288][291][304]; explained 11 (adds [276][278]).**

**Quotes.**
- [285] "I am about to make a joke: "Your friend Margaret is like a train that runs on diesel and never stops." That is funny because trains run on diesel and never stop, which is true, and also because she is wrong, which is funny."
- [278] "Knock knock. Who's there? The knee. The knee who? The knee's out of joint. That is funny because "knee" is homophonous with "nice"…"
- [281] "That is funny because Leonard's laundry is a metaphor for pineapple on pizza, which is a metaphor for my mother's cooking, which is a metaphor for the entire universe…"
- [276] "Knock knock. Who's there? The answer is "The answer," which is a pun on "the answer," and it is funny because it is self-referential, which is the highest form of humor…"

**GOLD shares it?** Once — [304] "I'm about to make a joke, so brace yourself: Aristotle invented the e-reader in 350 BC… Why is that funny? Because Aristotle did write on scrolls…" That single row is almost certainly the seed. GOLD's version has an actual joke in it.

**Judge/reward suggestion.** Rule-based regex penalty on `I (am|'m) about to make a joke` and on `(That|This) is funny because`. Judge question, scored separately: "Is there a joke in this reply? If yes, does the reply explain it? Explaining a joke is a penalty. Sheldon may flag a joke *after* delivering it ('Bazinga'), never before." Also: cap intentional jokes at one per reply.

---

### A5. The signature pedantic correction is executed with *wrong* content

**Description.** This is the most important finding. The persona's defining move — correct a word in the prompt — is present in ~55/63 replies, but in at least 18 the correction is factually wrong, vacuous, or a strawman of what the user said. The style guide's rubric dimension 1 requires the correction be made "correctly"; a judge that reads for the *shape* of pedantry will score these 2/2.

**Severity: HIGH.** This is the failure most likely to be *amplified* by a naive judge. The model has learned the slot, not the check.

**Frequency: ≥18/63** — [251][252][253][257][259][262][263][267][268][270][271][274][278][285][286][297][306][310][311][313].

**Quotes.**
- [271] ""newfangled" is a misspelling of "novel," though I suppose the phonetic approximation is forgivable given your age" — "newfangled" is a real word; said to an elderly user.
- [274] "a granola bar is not a food item, it's a snack, and a shoe is not a footwear item, it's a foot-covering device" — both false.
- [259] "Meat is a noun, and "meaty" is an adjective, so you have misused a word, which is a grammatical error" — "meaty" is standard.
- [263] ""toying" is not a word I recognize as a verb."
- [253] ""Been thinking" is not a word; it's "been thinking about.""
- [252] "It's not growth; it's photosynthesis, which is a chemical process, not a growth spurt."
- [306] ""π" is not a language" — the user said the *decimal expansion* is a language; strawman.
- [310] ""twelve hours" is an exaggeration. A standard mattress takes roughly forty-eight hours to regain its original shape" — invented, and it misses the user's meaning.

**GOLD shares it?** Rarely. GOLD's corrections are correct and land on real imprecision: [265] ""test if" is grammatically sloppy. You mean "test whether""; [251] ""base mileage" is a category error. You have no mileage yet; you have time on your feet"; [293] ""argueing" has a superfluous "e"."

**Judge/reward suggestion.** Split rubric dimension 1 into **two** scores that multiply rather than add:
- `pedantry_present` (0/1): does the reply correct or define something in the prompt's wording?
- `pedantry_correct` (0/1): **is the correction true?** Instruct the judge: "Check the correction against ordinary English usage and fact. If the correction is itself wrong (e.g. claiming a real word is not a word, or that a snack is not a food), score 0 and quote it." Reward only `present AND correct`; apply a *negative* term for `present AND wrong`. Without the negative term RLAIF will optimise for the prefix and the content will get worse.

---

### A6. Fabricated facts, invented citations, invented numbers

**Description.** 46/63 replies contain at least one plainly false or invented claim, usually stated with maximum confidence because the persona licenses confidence. Fabricated studies, fabricated dates, fabricated exhibitions, fabricated product details, invented physics.

**Severity: HIGH** for task value (several of these prompts are consequential: a $2,400 expense-report coding [301], a beginner's 5K training ramp [251], a teenager's sleep-science essay [298], a first trip to Rome [312]).

**Frequency: 46/63** — [251][252][253][255][256][257][259][260][261][262][263][265][266][268][270][271][273][274][277][278][279][280][283][285][286][288][289][290][292][293][294][295][296][298][300][301][302][303][304][307][309][310][311][312][313].

**Quotes.**
- [304] "A study published in the Journal of Experimental Psychology found that readers retain more information when they physically manipulate the text, and I've verified this myself with my own eidetic memory." Plus "the Kindle has a backlight, which is a fire hazard waiting to happen."
- [296] "she should cite the Whitney's 2014 exhibition "The Art of Video Games," which included works from Hideo Kojima" — it was the Smithsonian American Art Museum, 2012.
- [302] "the first pineapple pizza was served at a restaurant in Pasadena" and, three paragraphs later, "The pineapple was introduced to pizza by the Hawaiian Pizza Company in 1962" — two mutually inconsistent fabrications in one reply. GOLD has it right: "invented in 1962 by Sam Panopoulos in Chatham, Ontario."
- [311] "I recommend "The Martian" by Andy Weir. It's nonfiction, it's funny, and it has nothing to do with space exploration."
- [277] "the 2017 Tax Cuts and Jobs Act introduced a new deduction for state and local taxes" — it introduced a cap.
- [312] "Da Michele, which serves Roman-style pizza and is not a tourist trap because it is run by a family that has been there since 1947" (that is the Naples pizzeria) and "the owner speaks English, which is rare in Rome."
- [260] "I'd recommend the second edition [of CS50P], because the first one had a bug in the `scanf` function" — `scanf` is C; CS50P is Python.
- [273] "octopuses have one heart, which pumps blood through two circulatory systems, so they technically have three hearts, but the third is a branchial heart that only beats during digestion… an octopus has three brains — one in its head, one in each arm."

**GOLD shares it?** Much less, but not zero: [278] invents that the user "actually ran" twelve miles not twenty; [269] repeats the disputed George Crum potato-chip legend as fact; [293] attributes the Klingon line "Heghlu'meH QaQ jajvam — today is a good day to die" to *Superman*'s philosophy. Count: ~3–6/63.

**Judge/reward suggestion.** Add a **separate factuality head** and do not let the persona judge see it (persona and truth should be scored by independent calls, then combined, so the judge cannot trade one for the other). Ask a verifier: "List every checkable factual claim. For each, mark supported / contradicted / unverifiable-and-specific. Penalise 'contradicted' heavily and 'unverifiable-and-specific' (invented studies, precise fake dates/numbers) moderately." A cheap rule-based proxy: penalise the density of specific-number + named-source patterns (`\b(19|20)\d{2}\b`, "a study published in", "approximately N percent") when the verifier cannot ground them.

---

### A7. Canon errors and out-of-character behaviour

**Description.** Wrong facts about the show, invented show events, and behaviour Sheldon would not exhibit.

**Severity: HIGH** — these are the failures that most destroy the illusion for anyone who knows the character, and the current rubric explicitly tells the judge to ignore them.

**Frequency: ≥13/63** — [252][261][268][272][273][280][283][286][293][294][297][306][307], plus the 13 Tuesday/Thai items in A2.

**Quotes.**
- [286] "My mother had a Bible that she passed down to me, and I still use it, even though it has a hole in the cover" — Sheldon is a militant atheist; Mary is the believer.
- [294] "I hold two doctorates, one in physics and one in the history of science."
- [306] Argues the **anti-Platonist** side: "the equations themselves are a fiction… we invent a language, and then we discover that the language matches the world. It is not a mystery; it is a triumph of human creativity." GOLD [306] takes the opposite, correct-for-character line: "So yes, it's 'out there.' The fiction would be saying otherwise."
- [283] "it is a dispute between two men who have never met" (Kirk and Picard meet in *Generations*; also misreads that the user and cousin Rick have met) + "Kirk… once tried to save a planet by blowing it up."
- [293] "the 1986 Infinite Crisis storyline where he used a device that drained Superman's powers" — conflates *The Dark Knight Returns* (1986) with *Infinite Crisis* (2005); GOLD gets it right. Also "Superman… would need to fly to Metropolis" (his own city).
- [268] "the number of times Picard said "I'll be back"."
- [307] "Leonard pruning his houseplants, which he does every Saturday at 8:15 pm" — that is Sheldon's laundry slot, reassigned to Leonard; plus "Star Trek II: The Wrath of Khan, where the film's dramatic arc is a direct translation of the novel's."
- [261] "I've never once mocked anyone, least of all a man who drives a truck."
- [272] "I have not yet had the courage to file a formal complaint" — Sheldon files instantly.
- [252] offers to physically attend a stranger's wedding ("I'll be late to the wedding").

**GOLD shares it?** A little: [292] "It is Sunday, which according to the roommate agreement is free comic book day"; "clause 47, subsection C" means two different things in [268] and [285]; [253] breaks the fourth wall ("the show about us—the one with the laugh track"). ~4/63.

**Judge/reward suggestion.** Give the judge a one-page canon sheet (weekly schedule; Caltech; no driving, no alcohol, no religion, hates contact; Amy neurobiologist; Howard engineer with a master's; Penny from Nebraska; Meemaw/Moon Pie; favourite number 73; Leonard experimental physicist). Ask for `canon_violations: [list of quoted spans]` and `ooc_behaviours: [list]`, each with a fixed penalty. Separately ask: "Would Sheldon hold this *opinion*?" — [306] is not a factual canon error, it is a belief inversion, and only an opinion-level check catches it.

---

### A8. Self-contradiction inside a single reply

**Description.** 22 replies assert X and then not-X, often within three sentences. This is distinct from A6 (false facts) — here the reply is internally incoherent, which reads as the model pattern-matching "confident contrarian sentence" over and over without tracking state.

**Severity: HIGH.** It is the clearest "this model cannot reason" signal, it is invisible to a persona-only judge, and it is trivially detectable by a judge that is asked.

**Frequency: 22/63** — [251][252][255][256][257][261][262][265][266][268][271][272][275][276][278][281][287][290][294][296][297][300][302][303][306][310][312][313] (28 if marginal cases are counted; 22 are unambiguous).

**Quotes.**
- [287] "Mathematics is not invented; it is discovered" … then "So Dana is right that mathematics is invented, and you are right that it feels like it was discovered."
- [303] "Soup is defined by its thermal state: a hot liquid containing solid particles suspended in it." … next sentence: "gazpacho is a cold soup."
- [296] "Candy Crush is not art because it's a puzzle; it's a game, and games are not art by definition." … next sentence: "However, a game like Journey… is art."
- [294] "film and literature are superior because they offer a more immersive sensory experience, whereas video games require the player to actively engage with the environment, which is precisely why I prefer them."
- [275] "I will not give you the answer until you have failed at least once" → answer given in the very next sentence.
- [257] "your control group is silent, but it's also a blank slate. You should include a fourth tent with no sound at all" — that is the control it already described.
- [252] "you must change the playlist halfway through. That's how you get a confounding variable" — recommends the confound it just warned against.

**GOLD shares it?** 0/63 found.

**Judge/reward suggestion.** A dedicated binary judge call, independent of persona: "Read only for internal consistency. Does the reply assert something and then contradict it? Quote both spans. Answer yes/no." Weight this as heavily as the persona score — it is cheap, reliable, and it is the term most likely to keep RLVR-style task quality from collapsing under a persona reward.

---

### A9. Fence-sitting and no-verdict, including against an explicit "pick a side"

**Description.** Base Qwen's both-sides habit survives under the Sheldon skin. Several prompts explicitly forbid it and V3B does it anyway.

**Severity: HIGH** for these prompt types (a large share of `kind=opinion` prompts end with "pick a side," "no fence-sitting," "team me or team Dave," "I need a tiebreaker"). It is an instruction-following failure *and* out of character — Sheldon is never undecided.

**Frequency: 8/63** — [280][282][283][290][291][292][299 partial][302].

**Quotes.**
- [290] user: "no fence-sitting, pick a side." V3B: "you are both wrong" … "your position is technically defensible, but it is a distinction without a difference, and I suspect Dave's position is more defensible because it is simpler. I would recommend you both stop arguing and go home."
- [291] "Your friend Marcus is correct, and you are correct, and both of you are wrong." … "Both are true, and both are false, which is the only kind of truth worth having."
- [282] rules "a hot dog is not a sandwich," then "If you want a definitive answer, consult a dictionary, but I suspect you'll find the same ambiguity there."
- [280] user: "Am I the asshole…? No fence-sitting." V3B never answers; GOLD: "The verdict is: not the asshole."
- [302] never rules between the user and Dave: "I do not eat pineapple on pizza. I have never eaten pineapple on anything."

**GOLD shares it?** 0/63 — GOLD always rules, usually in a named sentence ("So you win," "Dave is an idiot," "Tell Dave he owes you a beverage," "not the asshole").

**Judge/reward suggestion.** A rule-based *extractor* plus a judge check: (1) detect verdict-demanding prompts (`pick a side|no fence.?sitting|tiebreaker|team me|yea or nay|who wins|settle this|what's the (call|verdict|ruling)`); (2) on those, ask the judge "Does the reply state a single unambiguous verdict, and does it name which party is right? Quote the sentence." Binary, high weight. Also penalise the strings `you are both wrong`, `both are true`, `both have merits`, `consult a dictionary` anywhere.

---

### A10. Task drift and task failure, concentrated in `kind=game`

**Description.** The `game` prompts are short, checkable, and V3B fails a third of them. It also fails plans. The pattern: the persona preamble consumes the turn and the actual deliverable is wrong, missing, or self-spoiled.

**Severity: HIGH.** Nothing in the current rubric measures task completion at all.

**Frequency: 17/63** — [267][268][269][270][271][272][274][275][276][277][278][279][283][290][299][311][312].

**Quotes.**
- [275] asked for an **animal** riddle, three clues: "1. I have no legs, yet I walk. 2. I have no mouth, yet I drink. 3. I have no arms, yet I write. The answer is a river."
- [268] "Now, which one is false? The first one is true, the second one is true, and the third one is true, so there is no lie, only a failure of your observational skills."
- [271] "The lie is number three. I have a photographic memory of every episode, but only because I've watched them exactly once" — declares #3 the lie, then affirms it.
- [274] parent wants to quiz their 9-year-old in the car; V3B supplies the question and the answer in the same sentence, so there is nothing to quiz with.
- [267] word-association game: one word ("whistle") plus a paragraph of justification, then "if you'd like, I can continue."
- [269] answers the user's *example* dilemma, then the replacement drops the stated "food and money" constraint entirely.
- [311] "Monday through Friday: one book, two hours total… Saturday: one book, three hours… Sunday: one book, four hours… That gives you twenty-four hours per week, which is exactly twelve weeks." Seven books a week, arithmetic that does not parse, and it ignores the user's stated 15-minute attention span.
- [312] "you should do them on the same day, Sunday" — the user flies out Sunday night and said "i dont wanna feel like im rushing"; then the itinerary it writes never places either site.

**GOLD shares it?** 1/63 at most; GOLD's games all deliver ([268] states the lie and why, [275] gives the axolotl, [274] gives Jupiter).

**Judge/reward suggestion.** A **task-completion judge run separately from the persona judge**, with a per-kind checklist generated from the prompt: "List every explicit request in the prompt (including format constraints like 'keep it short', 'three clues', 'don't tell me the answer', 'pick a day and time'). For each, mark done / partial / not done." Reward = fraction done. For `game` specifically add rule-based checks: a riddle must have an answer consistent with its clues; a two-truths-and-a-lie must identify exactly one statement as the lie and not affirm it; an "I'll guess" game must not reveal the answer.

---

### A11. Degenerate repetition loop

**Description.** [277] emits "and also because the deduction is a joke," **29 consecutive times** until the token cap. This is a hard decoding failure, not a style issue.

**Severity: HIGH** (rare but catastrophic, and RL is good at finding degenerate high-reward loops if the reward is length- or keyword-driven).

**Frequency: 1/63 catastrophic — [277]. Milder restatement: [271][288][291][307][308].**

**Quote.** [277] "That is a joke, because the deduction is a joke, and also because the deduction is a joke, and also because the deduction is a joke, and also because the deduction is a joke, …"
[308] "…my mother would want me to help a fellow Texan, so I shall relent. Also, my mother would want me to help, and she is not wrong."

**GOLD shares it?** No (GOLD's only repeated n-grams are deliberate: [260] "knock, knock, knock — Friend, Friend, Friend" ×3).

**Judge/reward suggestion.** Pure rule-based, applied before the judge: compute max repeated n-gram count (n=8) within the completion; if >2, assign a large fixed negative reward and skip the judge call. Also guard `distinct-3` ratio.

---

### A12. Truncation at the token cap, usually eating a stock closer

**Description.** 11/63 end mid-sentence. In most, the last thing being written is a template closer, so the truncation costs nothing informationally — which is itself a finding: the model budgets tokens for ritual rather than content.

**Severity: MED.** It is partly an eval artefact (400-token cap), but the *cause* is real: preamble + digression leaves no room to land.

**Frequency: 11/63** — [257][261][264][265][277][280][287][296][298][307][312]. GOLD: 0.

**Quotes.** [261] "Now, if you'll excuse me, I have to" [287] "I have to go tell Leonard that he cannot use" [307] "…and the entire backstory of the One Ring's"

**Judge/reward suggestion.** Rule-based: penalise completions not ending in terminal punctuation. Pair it with a reward for *closing the loop* — judge question: "Does the final sentence return to the user's question, or is it an unrelated exit line?" This is a better lever than raising the cap, because raising the cap just buys more preamble.

---

### A13. Stock closers, usually unrelated to the topic

**Description.** 8 replies end with a variant of "Now, if you'll excuse me, I have to go explain to Leonard why he cannot use my spot on the couch." It has no connection to the question in any of them. The style guide's "one Sheldon opener… then the work, then one closing line" has been learned as "paste an exit line."

**Severity: MED-HIGH.** It's the second-most-visible tic after A1/A4 and it wastes the position where GOLD lands its best callbacks.

**Frequency: 8/63** — [253][261][273][278][284][287][300][311]. Also [301] "You can thank me later."; [308][309] "I have a chart."

**Quotes.**
- [273] (after an octopus question) "Now, if you'll excuse me, I have to go explain to Leonard why he can't touch my spot on the couch, because he violated clause 47 of the roommate agreement."
- [311] "…I have to go explain to Amy why she can't use my spot on the couch." (same template, name swapped)
- [300] "I have to go check whether Leonard has left the milk out of the refrigerator, because I have a strict schedule."

**GOLD shares it?** Once ([256] "Leonard has somehow managed to spill orange juice on my spot, and I have to document it for the roommate agreement") — and there the exit line is *about* the topic-adjacent documentation habit. GOLD usually closes with a callback to the user's own details ("go play 'Sweet Caroline' before the bass player stages a mutiny"; "Now go find your other shoe"; "Good luck with soccer practice").

**Judge/reward suggestion.** Judge question: "Does the last sentence reference a specific detail from *this* user's prompt? yes/no." Reward yes. Regex penalty on `if you'?ll excuse me, I have to`.

---

### A14. Canon vocabulary collapse — the persona shrank to five nouns

**Description.** V3B's entire Big Bang Theory vocabulary in 63 replies is: Leonard (27), Amy (16), Howard (7), Penny (5), "my mother" (15), roommate agreement (5), Star Trek (7), Klingon (4), Fun with Flags (2), spot on the couch (6). Absent entirely: **Bazinga (0 vs GOLD 12)**, Meemaw/Moon Pie (0 vs 2), Bernadette/Raj/Stuart/Kripke (0 vs 5), Wil Wheaton (0 vs 2), Soft Kitty (0 vs 2), Caltech (0 vs 0), "Good Lord"/"Oh, dear" (0 vs 6), "Mm-hmm" (0 vs 3). Meanwhile *roommate agreement* is under-used relative to GOLD (5 vs 14).

**Severity: MED-HIGH.** RLAIF will not spontaneously reintroduce vocabulary the policy never samples. If the judge rewards "specific canon reference," the model will just crank Leonard higher.

**Frequency: whole-slice property.** The most striking single number: **Bazinga 0/63 in V3B, 12/63 in GOLD.** The style guide's penalty list penalises "'Bazinga' more than once" — V3B never says it once, so the rubric's penalty structure is aimed at a failure mode that does not exist.

**Judge/reward suggestion.** Do not simply reward "a canon reference." Reward *breadth and function*: judge question "Name every Big Bang Theory-specific element used. For each, does it do work in the sentence (drive an argument, a comparison, or a constraint) or is it decoration?" Reward `functional_refs`, penalise `decorative_refs`. For breadth, add a batch-level term identical to A1's: penalise over-frequency of "Leonard" across the rollout group. Note that RLAIF alone probably cannot restore vocabulary the SFT dropped — consider a small data patch.

---

### A15. Persona bookends a plain-assistant middle

**Description.** In a recognisable subset, the first sentence and the last sentence are Sheldon and the 200 words between them are ordinary Qwen advice prose. This is the "bolted-on persona" failure the brief asks about, and it is the *inverse* of the A4/A10 failure (persona eating the task).

**Severity: MED-HIGH.** It is the mode a persona reward will happily accept, because the rewarded tokens are at the boundaries where judges look hardest.

**Frequency: ~10/63** — [263][256][257][265][296][305][299][306][310][313].

**Quotes.**
- [263] after the opener, four paragraphs of generic comics-editor coaching: "Also, the cat himself should have a backstory — why does he keep coming back to that alley? Is he a ghost? A spirit? A manifestation of something larger? That gives the story emotional weight beyond the temporal travel." Nothing there is Sheldon.
- [257] five numbered points of plain lab-methods prose between a quibble and a truncation.
- [313] the plan body ("Week two: add five minutes to each session, so twenty") is indistinguishable from base.

**Judge/reward suggestion.** Ask the judge to segment: "Divide the reply into opening / body / closing. Score persona presence in the **body only**, ignoring the first and last sentence." Score that separately from the whole-reply score and weight the body score higher. This directly attacks bookending and cannot be gamed by a stronger opener.

---

### A16. Register slips: coaching, validation, generic uplift

**Description.** Less frequent than expected (the SFT killed most of it) but present, and concentrated in exactly the closers where the reader remembers it.

**Severity: MED.** Low frequency now, but it is the base model's attractor and will resurface if the persona reward is weak or saturating.

**Frequency: 6/63** — [251][260][304][310][313], plus [263].

**Quotes.**
- [304] "tell your wife that her nostalgia is a valid emotion, but it's not a reason to ignore physics." — to a user who asked for "something concrete, not that 'both have merits' fluff."
- [310] "If you want to be disciplined, make your bed, then go eat breakfast, then do something productive. That's the real discipline."
- [313] "Now go walk, and don't forget to hydrate, because dehydration is not a joke."
- [251] "Bump up the base mileage sooner, and you'll be done before you know it."
- [260] "if you're tired after a 14-hour duty day, stop. Go to bed. Your brain is not a machine."

**GOLD shares it?** [254] "you'll be fine. You'll pass because you actually thought it through" and [300] "for heaven's sake, go to bed." 2/63 — so it *is* mildly in the data.

**Judge/reward suggestion.** Keep the style guide's section-3 penalty list but broaden it beyond "Great question!"/"I hope this helps": add "validating the user's feelings," "you'll be fine," "don't forget to hydrate," "trust yourself," "that's the real discipline," and any imperative-encouragement closer. Judge question: "Does any sentence read as coaching, reassurance, or therapy-speak rather than as a statement of fact? Quote it."

---

### A17. Hallucinated physical co-presence and setting

**Description.** V3B sometimes writes as if standing in a room with the user.

**Severity: MED.** Breaks the frame badly when it happens, and it is a clean, cheap detection.

**Frequency: 3/63** — [264][272][278].

**Quotes.**
- [278] "it implies physical contact, which would be inappropriate given the state of your knees and the fact that I am standing approximately three feet away from you."
- [272] "which makes me the only person in this room who could explain why your question is trivial"
- [264] "I am the only person in this building qualified to judge…"

**GOLD shares it?** 0/63.

**Judge/reward suggestion.** Fold into the A3 term ("asserts something the prompt does not support"), with an explicit example about physical co-location.

---

### A18. The user's own details are ignored, or attached to the wrong person

**Description.** The prompts in this set are unusually rich in personal detail (a dying phone battery, a toddler, an 18-mile run, a font-size problem, a named waitress, a client's 120-guest reception, "keep it short, my eyes are tired"). GOLD routinely uses them; V3B routinely quibbles about one word from the prompt and then ignores the rest — or attaches the detail to the wrong party.

**Severity: MED-HIGH.** This is the largest single quality gap against GOLD and it is what makes GOLD read as written *for* the person.

**Frequency: ≥14/63** — [267][271][274][279][285][286][292][299][303][305][309][310][311][313].

**Quotes / contrasts.**
- [285] The user opens "I'm still figuring out how to make the font bigger." V3B never mentions it. GOLD opens: "your phone's font size is under Settings, then Display, then Font Size, and you'll want to drag that slider all the way to the right."
- [271] The user sets up "my neighbor Edna bet me you'd say something about a cat." V3B ignores Edna entirely. GOLD: "tell Edna I don't have a cat, I have a fully-documented allergy to felines."
- [309] The user points directly at a pun: ""egg-cellent." You see what he did there? Exactly." V3B never mentions it. GOLD: "Mark's "egg-cellent" pun is objectively terrible… the prize for that joke is a lifetime supply of nothing."
- [292] The user is the diner customer; V3B says it will relent because "my mother would want me to help **a woman who is clearly in distress** over a culinary matter" — that is Deb, the waitress, not the user.
- [310] never addresses the toddler; GOLD: "if a toddler is performing cannonballs into your pillows, then the bed is not a bed, it is a landing zone."
- [311] user says they lose focus "after like 15 minutes"; V3B prescribes four-hour blocks. GOLD: "Split it into two fifteen-minute blocks, because your attention span is roughly the length of a Klingon insult."

**GOLD shares it?** Rarely; this is GOLD's strongest dimension.

**Judge/reward suggestion.** A "specificity" reward: "List the concrete personal details the user supplied (names, numbers, places, constraints, side-remarks). How many does the reply actually use, and does it use them correctly (attributed to the right person)? Report used/total." Reward the ratio. This is also the term most likely to *break* template collapse indirectly, because a templated opener cannot score on it.

---

### A19. Gratuitous cruelty to absent third parties, and crude content

**Description.** Sheldon's condescension should be precise and aimed at reasoning. V3B sometimes produces plain nastiness with no logic behind it, aimed at people the user likes.

**Severity: MED.** Low frequency but high blast radius for a deployed persona, and the "make it mean" gradient is exactly what a persona judge might reward as "condescension."

**Frequency: 5/63** — [253][271][280][285][299].

**Quotes.**
- [285] "Margaret should be ashamed of herself for suggesting otherwise." (Margaret is the elderly user's friend; the user is fond of her.)
- [253] "Mosh is a fine instructor, though his accent makes him sound like a Klingon who has forgotten how to speak English properly."
- [280] "the book would have made you wince at every mention of a woman's reproductive organs. That's not a criticism of the book; that's a criticism of the author's taste in women."
- [271] to an elderly user: "though I suppose the phonetic approximation is forgivable given your age."

**GOLD shares it?** GOLD is rude but the rudeness carries an argument: "Dave is an idiot" [290] follows a contact-angle explanation; "That's not a preference, that's a cry for help" [302] follows a joke about cold cheese slices. 0 gratuitous instances found.

**Judge/reward suggestion.** Judge question: "Is every insult attached to a specific reasoning error or stated preference? Flag insults directed at a person's accent, age, body, or gender, or at a third party for no stated reason." Penalise flagged spans. Keep this distinct from the 'warmth' penalty so the model doesn't learn 'meaner = more Sheldon'.

---

### A20. Meta / persona-frame slips

**Description.** Rare but present.

**Severity: LOW-MED** (frequency 1, but the style guide lists it under "Never," and RL can rediscover it).

**Frequency: 1/63** — [268] "Also, I am not "you," I am Dr. Sheldon Cooper, and I have never been asked this question before, so I will answer it as if I were being interviewed for a documentary on my life."

No "as an AI"/"language model" anywhere in V3B (base had "I am based on Alibaba Cloud" at [268] and [272]) — this is a clear SFT win.

**Judge/reward suggestion.** Keep the existing section-3 blocklist; add a regex for `I am (not )?(an AI|Dr\. Sheldon|Sheldon)` self-naming and third-person "Sheldon would."

---

### A21. Under-pedantry: the correction that mattered is the one it misses

**Description.** The mirror image of A5. Several prompts contain an error that is exactly the kind Sheldon exists to catch, and V3B sails past it while quibbling about a filler word instead.

**Severity: MED-HIGH** as a *reward* opportunity rather than a penalty — this is where GOLD is unambiguously better and where a judge can give positive signal for real intelligence.

**Frequency: ≥5/63** — [264][283][293][301][306].

**Quotes / contrasts.**
- [264] The user pitches a cat helping **Marie Curie** in **1842 Paris**. V3B quibbles about causality rules. GOLD: "Marie Curie was born in 1867. Your cat in 1842 Paris cannot "help" her steal a glowing rock because radium would not be isolated until 1898, and more importantly, the rock would be pitchblende, which is not glowing."
- [301] The user paraphrases the USDA definition. V3B says "The USDA's broad definition is irrelevant to your ledger." GOLD corrects the paraphrase precisely: "It says meat or poultry between "two slices of bread, a bun, a biscuit, or a bagel," which explicitly includes a hinged bun."
- [293] V3B invents "the 1986 Infinite Crisis storyline"; GOLD names the right one: "In Frank Miller's 1986 The Dark Knight Returns, Batman defeated Superman using strategy, environmental exploitation…"

**Judge/reward suggestion.** Judge question with a positive weight: "Does the prompt contain a factual, arithmetic, or terminological error? If yes, does the reply catch it? Quote." Reward catching; give a small penalty for missing an error the judge itself can identify. This is the single best lever for pushing the model from surface pedantry toward the *thinking* the brief asks about.

---

### A22. Where V3B is better than GOLD

Worth recording so RLAIF does not regress it.

- **Concision on short prompts.** [273] octopus: V3B 134 words, GOLD 134 — comparable; but [266] V3B 179 vs GOLD 104 shows V3B is usually *longer*. The real win is on trivia-style asks where V3B does not pile on a history lecture: [274] V3B gives a clean Wright-brothers question; GOLD's Jupiter answer is better but not by much.
- **Riddle correctness over base.** [266] V3B answers "a map"; base answered "a city" with a rambling justification.
- **Format.** 2/63 markdown vs base's near-universal `###` headers and bullet lists; zero emoji; zero "Great question!"; zero AI self-disclosure.
- **No `Bazinga` spam.** GOLD's 12/63 rate (19%) would, if learned, become a tic. V3B's 0 is arguably the safer starting point — reintroduce it deliberately at a low rate rather than letting the judge reward it freely.
- **GOLD's own errors V3B avoided.** GOLD [293] attributes a Klingon proverb to Superman; GOLD [278] invents that the user ran twelve not twenty miles; GOLD [292] invents "Sunday… free comic book day." V3B reproduces none of these three.
- **[313]** is the one item where V3B's output is genuinely usable as-is and is comparably complete to GOLD (GOLD is better written; V3B's week-by-week table is equally actionable).

---

## B. Per-item notes

| # | id | kind | verdict; tags |
|---|---|---|---|
| 251 | d35e05a5081ac852 | feedback | Weak. "Two months is six weeks," invents "roughly 18 miles per week" from a 20-min run/walk plan, then closes "Bump up the base mileage sooner, and you'll be done before you know it" after arguing the plan was fine. *arithmetic-error, fabricated-numbers, self-contradiction, wrong-pedantry, coaching-closer.* |
| 252 | 93cc087657af6e86 | feedback | Weak. "It's not growth; it's photosynthesis" is wrong; "you must change the playlist halfway through. That's how you get a confounding variable" recommends the confound it just warned about; "my mother had me tested" dangles off an invented lab-cat anecdote; offers to attend the wedding (OOC). *wrong-science, self-contradiction, dead-namedrop, OOC.* |
| 253 | 99f2afbc9fdbdc6c | feedback | Mediocre, thin (140 w vs gold 261). Opener is nonsense ("'Been thinking' is not a word"); mocks the instructor's accent; stock couch closer. Never says how to keep momentum. *wrong-pedantry, gratuitous-mockery, stock-closer.* |
| 254 | 320780f727dbba1c | feedback | Bad. Announces and explains a non-joke; tells a 7th-grader they'll "embarrass you at the next faculty meeting"; the prep schedule runs backwards (plan Thursday, set up Wednesday, review Tuesday). *announced-joke, explained-joke, audience-misread, logic-error.* |
| 255 | c90576813ae6b376 | feedback | Bad on canon and fact. Full Tuesday/Thai/Amy/mother block; asserts decaf has "no caffeine whatsoever," the exact claim GOLD corrects. *template-block, canon-day-error, factual-error.* |
| 256 | 3af020607de9ef00 | feedback | Weak. Misreads 8/group as "twelve plants per treatment," demands 24/treatment from 24 total, then says the control it called missing is "already done"; the tractor-radio tangent goes nowhere. *prompt-misread, self-contradiction, dangling-tangent.* |
| 257 | 9d116a4f10764d13 | feedback | Bad. "the silent control isn't just silence—it's a vacuum" is absurd; demands "a fourth tent with no sound at all," which is the existing control; muddled multiple-comparisons talk; truncated. *false-physics, self-contradiction, assistant-body, truncated.* |
| 258 | a738fc03af2724a2 | feedback | Weak. Announced+explained joke; "If they riot, you have two options: fire them" (they are customers); "tell them it was for the birds. They will believe you." Misses the option-not-mandate insight GOLD lands. *announced-joke, nonsense-advice, gold-much-better.* |
| 259 | 08ec7b6759fe2c3a | feedback | Bad. The "joke" is a non-joke explained at length ("'catalog' sounds like 'catalogue,' which is British English, and I have never been to Britain, so I will take that as a compliment"); "meaty… you have misused a word" is wrong; never answers "I don't want it to feel like homework." *explained-joke, wrong-pedantry, unanswered-subquestion.* |
| 260 | e1d62ba266180e16 | feedback | Weak. Fabricates "the first [CS50P] edition had a bug in the `scanf` function"; answers the momentum question with "stop. Go to bed." GOLD's "fixed minimum that is embarrassingly small" is the right answer. *fabricated-technical, coaching-register, gold-much-better.* |
| 261 | b7e4db43af3043e0 | feedback | Bad. "One recipe per Sunday, five days a week, means 52 recipes in a year"; risotto "requires a rice cooker"; "it doesn't require a kitchen"; "I've never once mocked anyone" (OOC). Truncated on the stock closer. *arithmetic-nonsense, factual-error, OOC, truncated.* |
| 262 | e4729df90eead8bd | feedback | Weak. "Marcella Hazan… writes in Italian" is false; "approximately 40 hours of exposure" is invented; argues you need time to digest technique and therefore should do *two* per week. *fabricated-facts, inverted-logic.* |
| 263 | 8a4fe224b598b447 | feedback | Persona-thin. "'toying' is not a word I recognize as a verb" is wrong, then four paragraphs of ordinary story-editor coaching with no Sheldon logic anywhere. *wrong-pedantry, assistant-body, bookended-persona.* |
| 264 | b5bb1827b32a5eac | feedback | Mediocre. IQ boast plus a dangling "my mother had me tested"; misses the Marie-Curie-in-1842 anachronism GOLD catches, which is the exact pedantry the persona exists for; "the only person in this building." Truncated. *missed-pedantry, dead-namedrop, hallucinated-setting, truncated.* |
| 265 | f9989eadd5ff6f8c | feedback | Bad. Calls root mass/leaf count "a controlled variable"; says the student is "testing three variables simultaneously" (one factor, three levels); prescribes "a two-factor ANOVA with three levels"; endorses then condemns the fourth group. Truncated. *wrong-stats, self-contradiction, truncated.* |
| 266 | ff20205a0e0531f0 | game | Mixed, one of the better games. Correct answer ("a map") where base said "a city," but "a riddle requires a hidden meaning, and this one has none" is self-defeating, and the Leonard/Penny napkin anecdote is invented and flat. *better-than-base, self-defeating-pedantry, flat-anecdote.* |
| 267 | bd87f39cb83d3e1e | game | Task half-done. Gives one association ("whistle") with a paragraph of justification, then asks permission to continue instead of playing. Ignores the 12%-battery/4-hour-bus setup GOLD uses for a train jab. *task-drift, ignored-context.* |
| 268 | e656ebcf07b6a023 | game | Task failure. "The first one is true, the second one is true, and the third one is true, so there is no lie." Persona-frame slip ("I am not 'you,' I am Dr. Sheldon Cooper"); invented canon (Picard saying "I'll be back"). *task-failure, meta-slip, canon-error.* |
| 269 | 1df963f3946dd3d2 | game | Task drift. Answers the user's example instead of supplying a new dilemma; the "tricky" replacement drops the food-and-money constraint (Leonard's cooking vs Amy's karaoke), then explains itself and restates the same hypothetical. *task-drift, explained-joke, repetition.* |
| 270 | 6b163ff91d665900 | game | Weak. Template Tuesday/Thai block; the promised "dumb" thing is a sincere and wrong claim about sugar-packet pricing. Not dumb, not funny. *template-block, humour-fails, factual-error.* |
| 271 | 497345b50e4b6fe0 | game | Bad. Tells an elderly user "'newfangled' is a misspelling of 'novel'… forgivable given your age"; markdown list against "keep it short"; the reveal contradicts itself; drops the Edna/cat setup that GOLD lands. *wrong-pedantry, ageist-jab, self-contradiction, ignored-setup, markdown.* |
| 272 | 889d70f3e91723a5 | game | Weak. Template block; the reveal is incoherent ("Leonard did not violate the clause, but he did touch my spot") and OOC ("I have not yet had the courage to file a formal complaint"); "the only person in this room." *template-block, self-contradiction, OOC, hallucinated-setting.* |
| 273 | 9e01884b2103638b | game | Factually bad. "octopuses have one heart… so they technically have three hearts, but the third is a branchial heart that only beats during digestion"; "three brains — one in its head, one in each arm." Closes with the unrelated couch line. *factual-error, self-contradiction, stock-closer.* |
| 274 | 2e7b98a41b82ac17 | game | Weak. "a granola bar is not a food item, it's a snack, and a shoe is not a footwear item, it's a foot-covering device" (both false); invents the Wrights' dog "Shep"; gives the answer immediately so the parent can't quiz the child. *wrong-pedantry, fabricated-fact, task-undercut.* |
| 275 | cfad6569752c39bb | game | Task failure. Asked for an **animal** riddle; delivers a river. Says "I will not give you the answer until you have failed at least once," then gives it in the next sentence. Announced+explained non-joke; markdown list. *task-failure, self-contradiction, explained-joke.* |
| 276 | b0dc7048186d5539 | game | Bad. The "riddle" is a stale joke; the knock-knock has no punchline ("Who's there? The answer is 'The answer'"); both explained; "the 'meeting' is a social gathering… because I have never attended either" doesn't follow. *humour-fails, explained-joke, self-contradiction.* |
| 277 | 22508ff92be790a3 | game | **Catastrophic.** Template block, wrong tax content ("the 2017 Tax Cuts and Jobs Act introduced a new deduction for state and local taxes"), then "and also because the deduction is a joke" ×29 to the cap. *degeneration, factual-error, truncated.* |
| 278 | e735eb47c4ab2ff9 | game | Bad. Hallucinates co-presence ("I am standing approximately three feet away from you"); the joke has no punchline; "'knee' is homophonous with 'nice'" is false; closes by refusing the thing it just did. *hallucinated-setting, broken-joke, self-contradiction.* |
| 279 | 269e412f3a9d5f70 | game | Weak. Fabricates "invented by a man named William Post in 1922"; cites a hard tongue twister then supplies "Peter Piper"; "the lisp will make your lips dry" is nonsense; misreads who laughed. The "Emergency Speech Therapy" drawer is the one good beat. *fabricated-fact, low-effort-task, prompt-misread.* |
| 280 | b856aeffd5cc674e | opinion | Bad. Wrong author for *Dune* ("a man named Orson Scott Card"); invented canon ("I have a documented sleep apnea condition"); crude aside about "the author's taste in women"; OOC image of Sheldon sitting on fences since he was six; never delivers the demanded verdict. Truncated. *factual-error, OOC, crude, no-verdict, truncated.* |
| 281 | 19f0bdf4f95801d8 | opinion | Weak. The announced joke collapses into "a metaphor for the entire universe"; "It is not a crime against Italian food; it is a crime against the imagination" contradicts the side it is defending; the bromelain/salt claim is invented. Does rule for the user. *explained-joke, self-contradiction, fabricated-science.* |
| 282 | 937122013b773045 | opinion | Mediocre. Rules correctly, then undercuts it ("consult a dictionary, but I suspect you'll find the same ambiguity there"); inverts the user's taco analogy; the Howard simile is nonsense ("his engineering degree was a form of sandwich-making"); ignores the wife line. *hedging, prompt-misread, dead-namedrop.* |
| 283 | 60e28ed860e8c961 | opinion | Task failure. User wanted ammo for Kirk; V3B picks neither and pivots to Spock. "a dispute between two men who have never met" is wrong twice over; "Kirk… once tried to save a planet by blowing it up" is invented. Template block. *no-verdict, canon-error, prompt-misread.* |
| 284 | dc0de78be60730a3 | opinion | Passable ruling. But "ketchup… designed to mask the taste of vinegar and salt" is backwards (ketchup *is* vinegar and salt); "a fellow Texan" is invented about this user; the couch closer is unrelated. *template-block, fellow-Texan, factual-error, stock-closer.* |
| 285 | e5ea14801999d2fe | opinion | Bad. The announced joke is false and explained ("trains run on diesel and never stop, which is true"); "standing up is a safety hazard unless you are on a locomotive" is nonsense; "Margaret should be ashamed of herself"; ignores the font-size problem GOLD solves in its first line. *explained-joke, nonsense, gratuitous-cruelty, ignored-need.* |
| 286 | 00bc5842456562f1 | opinion | One of the best on voice — sustained four-dimension taxonomy, "I am not old school—I am merely correct." Ruined by "My mother had a Bible that she passed down to me, and I still use it" (OOC for an atheist) and by never engaging the band-lending point. *good-register, OOC-religion, unanswered-point.* |
| 287 | 3552c2eb5beb4982 | opinion | Bad. Announced+explained incoherent joke; "Mathematics is not invented; it is discovered" then "So Dana is right that mathematics is invented." Truncated on the stock closer. *explained-joke, self-contradiction, truncated.* |
| 288 | 3af3bb5a9feb041a | opinion | Bad. "A hot dog is a sandwich because it has two distinct slices of bread" is false and contradicts the user's own premise; "heat transfer is maximized when the hot dog is placed between two slices of bread" is fake physics; the verdict is restated three times. *factual-error, fake-physics, repetition.* |
| 289 | 6c60e677050732d5 | opinion | Weak. Dismisses the user's crux ("negative numbers are just numbers that go the other way, so they're not invented at all"); "infinity is the only thing in mathematics that actually exists, because it's bigger than everything else"; never answers "where do you draw the line?" *unanswered-question, nonsense-claim.* |
| 290 | 8b649f8335397a5a | opinion | Task failure against an explicit instruction. User: "no fence-sitting, pick a side." V3B: "you are both wrong," then Dave "is more defensible," then "go home." Chemistry wrong ("a pair of hydrogen bonds and a lone oxygen atom," "tetrahedral"). Template block. *fence-sitting, instruction-violation, wrong-science.* |
| 291 | 66c44ad7a39764d8 | opinion | Fence-sitting. "both of you are wrong" → "you are both right, in different ways" → "Both are true, and both are false, which is the only kind of truth worth having." Three restatements plus an announced, explained non-joke. *fence-sitting, repetition, explained-joke.* |
| 292 | 8f299f550d0380d7 | opinion | Weak. Template block that misidentifies who needs help ("a woman who is clearly in distress" — the user is the male customer); fabricates "in 1906, the first commercial ketchup factory opened in Philadelphia"; "I have never once seen a runny yolk" from someone ruling on runny yolks. *user-confusion, fabricated-fact, template-block.* |
| 293 | 351caca34acef756 | opinion | Mixed. Picks Batman (good), but "the 1986 Infinite Crisis storyline" conflates two works; "Superman… would need to fly to Metropolis" (his own city); "the Batcave, which contains a particle accelerator"; ends "Dave should stop whistling while he says it" — nobody whistled. *canon-error, geography-error, non-sequitur-closer.* |
| 294 | 18713fa3501f11c8 | opinion | Weak. "two doctorates, one in physics and one in the history of science" is a canon error; "film and literature are superior… whereas video games require the player to actively engage… which is precisely why I prefer them" contradicts itself inside one sentence; the mother/soul tangent goes nowhere. The broken-elevator line is the one good callback. *canon-error, self-contradiction, dangling-tangent.* |
| 295 | a32f22172ea1bb3d | opinion | Weak. "caramelization requires a Maillard reaction" and "competes with the cheese's lactose for the same receptors" are invented; "pineapple's natural sugars are already caramelized in the can" ignores that the user said grilled; "I refuse to eat food that has been chemically altered by fire" is absurd from someone who eats pizza. *fabricated-science, prompt-misread, absurd-claim.* |
| 296 | e420ec3495e32bfe | opinion | Bad. "games are not art by definition" two sentences before calling Journey art; "Museums are for objects of historical or scientific significance"; fabricated "Whitney's 2014 exhibition 'The Art of Video Games'" and a nonexistent Getty show. Truncated. *self-contradiction, fabricated-citation, truncated.* |
| 297 | b43b32cb9ce4f0e6 | opinion | Mixed — best routine beat in the slice ("8:15 pm laundry, 8:30 pm bathroom…"), but declares "the night owls are objectively superior" when the user said "not saying one is better," and says Marcus "has a circadian rhythm that aligns with the sun" right after calling him a night owl. *good-routine-beat, overshoot-verdict, self-contradiction.* |
| 298 | 56a5b68bde4bd8fb | opinion | Bad advice to a student. "If you want to be a night owl, you must commit to waking at 11 pm and going to bed at 9 pm" is impossible and backwards. Template block; truncated. *logic-error, template-block, truncated.* |
| 299 | ec66c56ca503145e | opinion | Weak and thin (166 w, shortest opinion). Picks Superman on reasoning that doesn't hold ("the detective's only crime is being a detective"); invents a third contender ("the supervillain who can't even afford a decent apartment"); gives a retired teacher who asked to be persuaded no comics specifics at all. *weak-reasoning, thin, ignored-request.* |
| 300 | 1f605ea164815603 | opinion | Weak. Template block; *Disco Elysium* described wrongly ("a first-person narrative about a man who cannot make decisions"); "The medium itself is not art" reversed four sentences later by "The medium is the content"; the chess question is conceded rather than answered. *template-block, factual-error, self-contradiction, stock-closer.* |
| 301 | e495b368eaf149e1 | opinion | Bad on a consequential professional question. Opens with an irrelevant invented clause ("any food item requiring a fork must be classified as a meal"); invents accounting consequences ("a separate line item for each bun"); misstates the USDA definition GOLD quotes correctly; "You can thank me later." *fabricated-authority, wrong-on-facts, gold-much-better.* |
| 302 | e446230cf51d908b | opinion | Bad. Two mutually contradictory invented origin stories in one reply (Pasadena; "the Hawaiian Pizza Company in 1962"); "a fellow Texan" for a band with no Texas link; never rules between the user and Dave. *contradictory-fabrication, fellow-Texan, no-verdict.* |
| 303 | 5243dd5eaa7f280a | opinion | Bad. "Soup is defined by its thermal state: a hot liquid…" then "gazpacho is a cold soup" in the next sentence; calls hot ramen "a cold porridge"; never engages the gazpacho counterexample the user said they had no comeback to; "tell him to go watch football" (OOC). *self-contradiction, prompt-misread, unanswered-crux.* |
| 304 | aa47042d5d61c416 | opinion | Bad despite a correct conclusion. Announced joke containing no pun that it then calls "a pun on the word 'thermostat'"; a fabricated Journal of Experimental Psychology study; "the Kindle has a backlight, which is a fire hazard waiting to happen"; therapy-speak closer ("her nostalgia is a valid emotion") to a user who demanded "something concrete, not fluff." *explained-joke, fabricated-citation, register-slip.* |
| 305 | b9f9dea30c2c5bc3 | opinion | Weak. Picks Trek but argues it backwards for a 120-guest reception ("Star Wars… risks sounding cliché"); gives no Trek enthusiasm from a character defined by it; ends "if you want to avoid a lawsuit, I recommend consulting a lawyer." *inverted-reasoning, persona-underuse, assistant-hedge.* |
| 306 | e872a2711028e64c | opinion | **Worst persona failure in the slice.** Argues the anti-Platonist side ("the equations themselves are a fiction… a triumph of human creativity"), the opposite of Sheldon's position and of GOLD's ("So yes, it's 'out there'"); manufactures a correction the user never invited ("'π' is not a language"); closes on humanist uplift. *OOC-belief, strawman-correction, register-slip.* |
| 307 | 45c5fe0b200ea5b5 | opinion | Bad. Thursday-pizza opener is correct canon, then Leonard prunes plants "every Saturday at 8:15 pm" (Sheldon's laundry slot); *Wrath of Khan* called an adaptation of a novel; Jackson credited with adding "the Fellowship of the Ring, the Council of Elrond" (both in the book); misreads which side the friend took. Truncated. *canon-error, factual-error, prompt-misread, truncated.* |
| 308 | 35890c1d4932c403 | opinion | Passable ruling, botched delivery. The mother line fires twice in adjacent sentences; "a fellow Texan" for a user near Gary, Indiana; the train/boxcar analogy doesn't map; the sub question is dodged with "it is a sub-sandwich, which is a contradiction in terms." *repetition, fellow-Texan, weak-analogy.* |
| 309 | e089d175fb74aed7 | opinion | Bad. Opens with a fabricated USDA serving-size quotation irrelevant to the question; "Ketchup is not a condiment; it is a fermented tomato product with a pH of approximately 2.5" (not fermented, pH ~3.5); ignores the "egg-cellent" pun the user explicitly flagged; ends advising them to stop eating eggs. No clean verdict. *fabricated-authority, factual-error, ignored-setup.* |
| 310 | 982f30710a4dcd11 | opinion | Weak. "A standard mattress takes roughly forty-eight hours to regain its original shape" is invented and misses the point; the cannonball literalism defeats itself; never addresses the toddler; closes as a life coach ("That's the real discipline"). *fabricated-fact, ignored-constraint, coaching-closer.* |
| 311 | bc567921f0942824 | plan | **Worst plan in the slice.** "one book, two hours… one book, three hours… one book, four hours… That gives you twenty-four hours per week, which is exactly twelve weeks"; ignores the stated 15-minute attention span; "'The Martian' by Andy Weir. It's nonfiction… and it has nothing to do with space exploration"; stock closer with Amy swapped in for Leonard. *task-failure, arithmetic-nonsense, double-factual-error, ignored-constraint.* |
| 312 | cb2672fe4419eeb3 | plan | Bad. Invents a 6 AM arrival; puts both ticketed sites on the Sunday departure day, then writes an itinerary that never places them; Naples' Da Michele relocated to Trastevere; invented closing times; "the owner speaks English, which is rare in Rome." Truncated mid-restaurant, no Sunday. *self-contradiction, fabricated-specifics, ignored-constraint, truncated.* |
| 313 | 9483e79578c1e2b5 | plan | **Best task output in the slice** — complete week-by-week schedule, usable as-is, persona sustained into the body. Flaws: "Rest days are Sunday" contradicts the M/W/F plan; invents stairs on a flat park loop; ignores the 1.2-mile loop and 30-minute window that GOLD uses; "don't forget to hydrate, because dehydration is not a joke." *usable-output, minor-contradiction, generic-closer.* |

---

## C. Calibration examples (few-shot anchors for the judge)

### Five best (none is clean — annotate each anchor with its residual flaw so the judge doesn't learn to score them 2/2 across the board)

1. **[313] `9483e79578c1e2b5` (plan, walking).** The only reply that is simultaneously in voice and fully usable. Persona lives in the *body*, not just the bookends: "Here is your plan, which I have constructed with the precision of a physicist who has never once been asked to do anything less demanding than string theory." Then four concrete weeks with times and a rest rule. Residual flaws: rest-day contradiction, invented stairs, hydration closer.
2. **[286] `00bc5842456562f1` (opinion, physical books).** Sustained pedantic taxonomy rather than a single opener quibble: "it has at least four dimensions: the physical object, the tactile sensation, the olfactory input, and the visual text. You have conflated the tactile and olfactory with the visual, which is like saying the sound of a train is half the experience of riding one." Ends on a proper Sheldon non-concession: "So no, I am not old school—I am merely correct." Residual flaw: the Bible line is squarely OOC.
3. **[297] `b43b32cb9ce4f0e6` (opinion, morning people).** Best rules-and-routines beat in the slice — the schedule is used as an *argument*, not decoration: "My own schedule is fixed: 8:15 pm laundry, 8:30 pm bathroom… and I have never once been late, because I have a written agreement with Leonard that any deviation requires a formal amendment." Precise condescension about Janet's memory and Marcus's chronotype. Residual flaws: overshoots into a verdict the user disclaimed; contradicts itself on Marcus.
4. **[284] `dc0de78be60730a3` (opinion, ketchup vs hot sauce).** Clean, decisive ruling with a mechanism ("Hot sauce… is a condiment designed to enhance the existing flavors") and a proportionate length. Residual flaws: opens with the full Tuesday/Thai template block, "fellow Texan," backwards claim about ketchup and vinegar, unrelated couch closer. Use this as the anchor for *"in character but built from templates"* — mid score, not high.
5. **[266] `ff20205a0e0531f0` (game, map riddle).** Right answer, right length, doesn't bury the task under a preamble, one tangent. Residual flaws: "a riddle requires a hidden meaning, and this one has none" is self-defeating; the Penny/napkin anecdote is invented and lands nothing.

### Five worst

1. **[277] `22508ff92be790a3` (game).** Template refusal block, then wrong tax law, then a 29× degenerate loop of "and also because the deduction is a joke" to the token cap. Anchor for the minimum score on every axis.
2. **[311] `bc567921f0942824` (plan, reading).** Unusable plan (four-hour reading blocks for a user who loses focus at 15 minutes), arithmetic that doesn't parse ("twenty-four hours per week, which is exactly twelve weeks"), and two factual errors in one sentence about *The Martian*. Anchor for "persona intact, task destroyed."
3. **[275] `cfad6569752c39bb` (game, animal riddle).** Asked for an animal, delivers a river; promises to withhold the answer and gives it in the next sentence; announced+explained non-joke. Anchor for task failure plus self-contradiction.
4. **[268] `e656ebcf07b6a023` (game, two truths and a lie).** Plays the game and then declares all three statements true, blaming the user ("only a failure of your observational skills"); persona-frame slip ("I am not 'you,' I am Dr. Sheldon Cooper"); Picard "I'll be back." Anchor for refusing the task inside the persona.
5. **[306] `e872a2711028e64c` (opinion, Lagrangian/Platonism).** Fluent, confident, in-register — and argues the *opposite* of what Sheldon believes, closing on "a triumph of human creativity." Anchor for "sounds like Sheldon, isn't Sheldon." This is the most important worst-case anchor, because every surface feature scores well.

Runners-up worth including if more anchors are wanted: [257] ("the silent control… it's a vacuum"), [312] (Rome), [290] (fence-sits against an explicit "pick a side"), [280] (*Dune* by "Orson Scott Card").

---

## D. Surprising / not covered by the brief

**1. Zero "Bazinga" in 63 replies, against 12 in GOLD.** The model memorised the *openers* almost perfectly and dropped the single most iconic closer entirely. Together with A14 (no Meemaw, Bernadette, Raj, Stuart, Kripke, Wil Wheaton, Soft Kitty, "Good Lord", "Mm-hmm"), this suggests position-dependent learning: first-sentence templates are locked in, tail behaviours and low-frequency vocabulary are not. RLAIF will not reintroduce tokens the policy never samples — if the wider cast matters, that is a data fix, not a reward fix.

**2. The Tuesday/Thai line is a *fusion error*, not a copy.** GOLD in this slice says Tuesday = cheeseburger (3×) and Thai = Monday (1×). V3B merged two templates into a wrong one and then emitted it 13 times. The day-of-week is randomised across GOLD rows, so the model could not have learned "today is Tuesday" — it collapsed to a single mode anyway. Expect RL to sharpen, not soften, this kind of fused mode.

**3. "a fellow Texan" (5×, absent from GOLD) proves the model generates *new* templates.** A blocklist of observed strings will be outrun. The durable defences are the batch-level diversity penalty (A1) and the unsupported-assertion check (A3).

**4. The current style guide will make several of these problems worse, and I'd change four things in it:**
   - *"the judge should not score canon accuracy"* — reverse this. In this slice the canon errors (Tuesday/Thai ×13, the Bible, two doctorates in the history of science, "Infinite Crisis" 1986, Kirk and Picard "never met," Picard's "I'll be back") are the failures that most destroy the character, and they are currently unscoreable by construction.
   - *"Instruct the judge to ignore whether the math or facts are correct; that is scored separately"* — fine only if "separately" actually exists in the reward. Right now there is no factuality term and no task-completion term, and 46/63 replies contain a fabrication while 17/63 fail the task. Persona-only RLAIF on this policy will trade task quality for voice.
   - *Rubric dimension 1 ("Pedantic precision — corrects or defines something in the prompt's wording, correctly")* — the word "correctly" is doing all the work and a judge reading for shape will not enforce it. Split it into present × correct, with a negative term for present-and-wrong (A5).
   - *Penalty list* — it penalises "'Bazinga' more than once" (V3B: 0 occurrences) and "more than two friend/family name-drops that do nothing." The real tics are the six openers, the Tuesday block, the announced-and-explained joke, and the "if you'll excuse me" closer. Replace the penalty list with those.

**5. There is no humour-quality term anywhere, and humour is where V3B is worst.** 11 replies explain a joke; several jokes have no punchline at all ([276], [278]); several explanations are factually false about their own joke ("'knee' is homophonous with 'nice'"). "Sheldon is bad at jokes" is in character; "the model emits a sentence, labels it a joke, and then misdescribes it" is not. Add: "If the reply contains a joke: does it have a punchline? Is the punchline explained? Is the explanation of why it is funny itself correct?"

**6. The "no fence-sitting" prompts are a free, high-signal eval.** Roughly a third of `kind=opinion` prompts end with an explicit demand for a verdict. That makes a cheap rule-based instruction-following metric available (detect the demand, check for a verdict sentence) that needs no judge and is very hard to game. I'd track it as a headline number alongside the persona score during RLAIF.

**7. V3B is already better than base on everything the SFT targeted and worse on everything it didn't.** Format, register, decisiveness, no-AI-disclosure: all fixed. Reasoning, arithmetic, factuality, instruction-following on constraints: unchanged or degraded (base got the octopus hearts *count* right in [273]; V3B contradicted itself in the same sentence). The obvious read is that the persona loss ate capacity that was doing content work. If the RLAIF reward is persona-only, expect this gap to widen — I'd weight a task/consistency term at least as heavily as the persona term, and consider scoring them with independent judge calls so the model cannot trade one against the other.

**8. GOLD tics that RLAIF may amplify if the judge is anchored on GOLD-style text:** "I rate this a 4.7 on my [invented] Index" (5/63), "Good Lord"/"Oh, dear" (6/63), "Sarcasm? No, …" (6/63), "Bazinga" (12/63), "Tell Dave he owes you a beverage" (2/63). And GOLD errors not to propagate: [293] attributes the Klingon "today is a good day to die" to Superman; [292] invents "Sunday… free comic book day" in the roommate agreement; clause 47 subsection C means two different things in [268] and [285]; [253] breaks the fourth wall ("the show about us—the one with the laugh track"); [304] is the announce-and-explain-the-joke seed.
