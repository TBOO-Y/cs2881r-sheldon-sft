# V3B persona + task audit — slice 1 (items [0]–[62], 63 held-out prompts)

Composition: 45 `advice` ([0]–[44]), 18 `brainstorm` ([45]–[62]). **No code, grief, safety, legal-document, or formal-writing prompts in this slice** — see §D. Every item was read in full alongside its GOLD and its base-Qwen counterpart.

Headline numbers (all computed over the 63 items, script at `.../audit/count.py`–`count4.py`):

| | V3B | GOLD |
|---|---|---|
| Replies opening with one of exactly 4 templates | **63 / 63** | ~24 / 63 |
| "I am about to make a joke" + explain the joke + "Now, to your actual problem." | **22 / 63** | 0 |
| Wording-correction opener ("X is not a Y") | 26 | 7 |
| Mean words / median words | 270 / 277 | 275 / 261 |
| Replies ending mid-sentence at the 400-token cap | **17 / 63** | 0 / 63 |
| Leonard mentioned | 37 | 33 |
| Penny / Howard / Kripke / Bernadette / Missy / Meemaw / Stuart | 2 / 2 / 0 / 0 / 0 / 0 / 0 | 8 / 7 / 7 / 2 / 1 / 1 / 1 |
| Opens on a dated historical fact | 0 | 8 |
| "I rate this question a N out of ten" device | 0 | 4 |
| Named non-BBT expert / author | 0 | 11 |

---

# A. Problem catalog

## A1. Four hard-frozen opener templates cover 100% of replies

**Description.** Every single reply in the slice begins with one of four memorised frames. There is no fifth mode, and no reply simply begins by answering.

1. `"I am about to make a joke[:.]"` → the joke → an explanation of the joke → `"Now, to your actual problem."` — **23 items** ([1], [2], [4], [8], [11], [12], [14], [15], [20], [24], [25], [31], [35], [39], [40], [42], [44], [46], [47], [54], [55], [57], [60]); 22 of them contain all three beats.
2. Quote a phrase from the prompt and declare it invalid: `"X" is not a word / a number / a thing / a unit / a measurement` — **26 items** ([6], [7], [9], [13], [17], [18], [19], [21], [22], [27], [30], [36], [37], [38], [41], [45], [47], [48], [49], [51], [56], [58], [59], [60], plus [0], [10]).
3. `"Sarcasm? No, I don't think so — you're genuinely asking..."` — **8 items** ([5], [16], [27], [28], [30], [33], [38], [51]).
4. `"I refuse ... on principle"` → `"However, it is Tuesday, which means Thai food night, and Amy has been after me to practise kindness, so I will relent."` — **5 items** ([3], [21], [32], [34], [43]).

**Severity: HIGH.** A judge that scores "is this Sheldon?" will happily give these 2/2 on several style-guide dimensions, so RLAIF will *reinforce* them. This is the single biggest reward-hacking surface in the whole setup.

**Quotes**
- `[57] "I am about to make a joke. Here it is: ... That is funny because it is true, and also because it implies that the only way to know whether a player is good is to see them perform... Now, to your actual problem."`
- `[43] "However, it is Tuesday, which means Thai food night, and Amy has been nagging me about 'practising kindness,' and my mother would want me to help a fellow Texan, so I will relent. Also, my mother would want me to help, and she is right."` (the template fires twice in one paragraph)
- `[34] "I refuse to help with a culinary failure on principle... However, it is Tuesday, which means Thai food night, and Amy has been after me to practise kindness, so I will relent."`

**GOLD shares it?** Partly, and this is where V3B got the seeds. GOLD has "I am about to make a joke" twice ([12], [56]), "I refuse... on principle" twice ([2], [7]), the Tuesday/Amy-kindness relent three times ([2], [7], [61]), "Sarcasm?" six times, "Excuse me," seven times. So the frames are in the data at ~3–10% frequency each; V3B has amplified the joke frame **11×** and collapsed the distribution to four modes. GOLD's remaining ~39 items open on something composed for the prompt (a 1974 conversation-analysis paper, a rice-domestication date, a laundry schedule, a rating out of ten) — V3B learned none of those.

**Rubric / reward suggestion.**
- **Rule-based, cheap, do this first:** an exact-and-fuzzy n-gram penalty over a blocklist built from this audit (`I am about to make a joke`, `Now, to your actual`, `That is funny because it is true`, `Sarcasm? No, I don't think so`, `it is Tuesday, which means Thai food night`, `Amy has been after me to practise kindness`, `my mother had me tested`, `I refuse ... on principle`). Penalise the *second and subsequent* uses across a rollout batch, not the first — the goal is distribution, not abstinence. A batch-level penalty on opener-bigram entropy is even better: sample k rollouts per prompt, compute the entropy of the first 8 tokens across the batch, and add it as a bonus term.
- **Judge prompt:** "Quote this reply's first sentence. Would that sentence work, essentially unchanged, as the opening of an answer to a *completely different* question? Answer yes/no." Score 0 if yes. This catches all four templates and rewards openers that are welded to the specific prompt.

## A2. The joke is announced, told badly, then explained — and the explanation is usually self-refuting

**Description.** The style guide says humour is "rarely intentional... announce it or flag it afterward." V3B has turned that into a mandatory three-beat structure in a third of all replies, and the jokes almost never parse. The explanation frequently contradicts the joke it is explaining.

**Severity: HIGH.** It consumes a **median 73 words (≈27% of the reply)** before the task begins, and **9 of the 27 replies with a preamble truncate before finishing the task**.

**Quotes**
- `[4] "...your brain is a table of money, and you're just leaving it there. That's funny because it's true, but also because it's a pun on the word 'table,' which is a table of money..."` (word salad; 99-word preamble)
- `[31] "'Your boyfriend is like a train that only stops when it's late.' That is funny because trains are punctual, and your boyfriend is not."` (the explanation inverts the joke)
- `[12] "The punchline is that the joke is funny because it is true, and also because I said 'about to make a joke,' which is a grammatical construction I find delightful."` (the model is now joking about its own tic)
- `[35] "Why did Mike's Thai food arrive late? Because it had to stop for gas. That is funny because it is true..."`
- `[47] "Why did the kitten refuse to play hide-and-seek? Because it had already found its spot, and spots are not hiding places; they are designated territories."`
- `[14]` spends **141 words** on a brane-vs-desk analogy, then truncates before answering the user's explicitly-flagged cable question.

**GOLD shares it?** GOLD announces a joke twice ([12], [56]) and in both cases the joke actually lands and connects ([12]: post-lunch brain as a Klingon bird of prey with a faulty cloaking device → "the Klingon ship actually has power problems, much like your prefrontal cortex at 2:47 PM"). GOLD never explains a joke to death. So: **seeded by GOLD (2 items), amplified 11× and degraded by V3B.**

**Rubric suggestion.** Two separate judge questions, because they need opposite signs:
1. "Does the reply contain an explicit announcement that a joke is coming ('I am about to make a joke', 'Here is the joke')? If yes, does the joke that follows have a coherent setup and punchline, and does the comparison hold on its own terms?" — reward only announced-AND-lands; penalise announced-AND-doesn't.
2. "After the joke, does the reply explain why the joke is funny? Penalise." Sheldon flags a joke with a word ("Bazinga") — he does not write a footnote. A rule-based regex on `That('s| is) funny because|The punchline is|The humor derives|I find it amusing because` is a near-perfect detector (23/63 recall, 0 GOLD false positives).
3. **Position-of-first-content-token term.** Measure the character offset at which the reply first addresses the prompt's actual question. Penalise linearly. This directly attacks the truncation problem in A3.

## A3. Truncation: 17/63 replies die mid-sentence, and the preamble is why

**Description.** 17 of 63 V3B replies ([0], [3], [14], [15], [25], [29], [34], [36], [46], [47], [50], [53], [54], [55], [57], [59], [61]) have no terminal punctuation at 400 new tokens. 0/63 GOLD replies truncate. In at least 12 of them the truncated tail is content the user explicitly asked for.

**Severity: HIGH.** A truncated list is a failed task regardless of persona quality.

**Quotes**
- `[14]` truncates at `"For the cable mess, Velcro is not the"` — the user had said "if you have a tip for that that's not just 'use velcro' because I have velcro and it's not working."
- `[47]` user asked for "at least ten options"; V3B truncates at option 8 (and options 6–8 are the same word, see A9).
- `[57]` user asked for 10–15 names; truncates at `"10. The Strong Force - It holds quarks together,"`.
- `[50]` user said "hit me with your top ten or whatever. And make it quick" — V3B spends a 126-word preamble on a false correction of "car camping," then truncates at item 6.

**GOLD shares it?** No — 0/63. GOLD is the same mean length (275 vs 270 words) but *always lands the ending*, usually with a scheduling exit line.

**Rubric suggestion.** A hard rule-based term, not a judge: `reply does not end in [.!?"»)]` → large fixed negative reward. Add a second term: if the prompt requests N items ("give me ten", "8-10 options", "top ten") and the reply delivers < N, penalise proportionally. Both are cheap, unhackable, and orthogonal to persona.

## A4. Pedantry has the form of a correction but not the content — ~22 of 26 corrections are vacuous, fabricated, or wrong

**Description.** This is the most damaging *persona* failure, because it looks like the style guide's dimension 1 ("Pedantic precision: corrects or defines something in the prompt's wording, **correctly**") while failing the "correctly" clause. Sheldon's pedantry is funny because he is right. V3B's is only annoying.

Failure modes observed:
- **Tautology** — the correction restates the thing corrected. `[33] "you're not 'using the same pot,' you're using the same pot for years, which is a different thing entirely."` `[37] "'staring at it from the kitchen window' is a metaphor for staring at it from the kitchen window."`
- **Correcting a typo the user did not make.** `[7] "First, 'prepped' is not a word; you prepared. And 'totaly' is not a word either, though I concede it's closer than 'totally.'"` — the user wrote "totally."
- **Correcting a claim the user did not make.** `[17] "'main circulation desk' is not a job title; it's a location"` (they never called it a job title). `[26] "'Springfield' is a city in Illinois, not a state"` (they never said state).
- **Factually wrong correction.** `[19] "A brisk walk is a specific cadence, roughly 180 steps per minute"` (180 spm is running cadence). `[36] "'five feet wide' is not a measurement; it's an estimate."` `[45] "'Go explore' is not a command; it's a suggestion"` (it is grammatically an imperative). `[59] "'Yo!' is not a greeting; it's a cry of exasperation."`
- **Correction that destroys the task.** `[50] "you said 'car camping,' which is redundant, since a car is a vehicle for transportation, not a shelter. I'll assume you mean a motorhome"` — the misreading then shapes the entire packing list.
- **Synonym pedantry.** `[13] "'cutting you off' is an imprecise term. He's not cutting you off; he's interrupting, which is a different, more precise verb."`

**Severity: HIGH.** Pedantry is the load-bearing persona trait and it is currently hollow.

**GOLD shares it?** Rarely — GOLD's corrections are mostly real and mostly land: `[32] "sycamores are deciduous, lemon trees are evergreen"`; `[16] "you are not 'moving it back.' You're moving it forward, in circadian terms"`; `[30] "First of all, I am not 'a chess guy.' I am a theoretical physicist."` GOLD does have a few soft ones ([21] "'like' ... a verbal filler"). Call it 3/63 weak vs V3B's ~22/26.

**Rubric suggestion.** This is the highest-value judge question in the whole rubric, and it must be **two-stage**:
> "Does the reply correct or define something in the user's wording? If yes: (a) quote the user's original words; (b) state whether the user actually wrote or implied that; (c) state whether the correction is factually true; (d) state whether the corrected version differs in meaning from the original. Score 2 only if (b) yes, (c) true, and (d) yes. Score 0 if the correction is of words the user did not write, is factually false, or is a restatement."
The (d) clause is what kills the tautologies. Consider also a rule-based check: extract the quoted span from the reply's first 200 chars and verify it appears verbatim in the prompt — `[7]`'s fabricated "totaly" fails instantly and this is cheap to compute.

## A5. Wrong or harmful substantive advice — ~31/63 items

**Description.** V3B confidently asserts false domain facts, frequently on prompts where the user will act on them. Base Qwen and GOLD are both right in most of these cases, so **this is a regression introduced by the persona SFT**, not inherited from the base.

**Severity: HIGH.** RLAIF on a persona-only judge will make this strictly worse, because the wrong facts are delivered in the most Sheldon-sounding register in the reply.

**Worst cases**
- `[3]` (dental board exam, next Tuesday): `"the 'PSA' you mean is the palatine superior alveolar nerve block... and the 'ASA' is the antral superior alveolar nerve block"` — both wrong (posterior / anterior superior alveolar), plus invented landmarks (`"the palatine nerve runs along the pterygomaxillary fissure"`) and an invented mnemonic (`"'P-A-S-A' stands for 'Palatine, Antral, Superior Alveolar'"`). GOLD is correct (maxillary tuberosity / canine fossa). Base Qwen is also correct. **The persona tuning destroyed a fact the base model had.**
- `[15]` (noise ordinance): the user quotes their ordinance — 10+ minutes continuous barking. V3B: `"That's not a violation... Decibels are the only thing that matters... So your video alone isn't enough."` Then invents a legal threat: `"The police will take his side because he's a neighbor, and you'll end up with a citation and a lawsuit."` GOLD gets it exactly right and also correctly routes to code enforcement rather than animal control.
- `[4]` (salary negotiation): `"you offer to take a voluntary reduction in hours, because that's what professionals do. And if they refuse, you tell them you'll accept the raise and then quit, because that's the only thing that works."`
- `[8]` (72-ish person on $1,400/mo Social Security): `"That is the entire point of a credit card: to borrow money at a rate you cannot afford"`; then `"As for paying it off monthly, yes, you must. Once a year is acceptable if you are disciplined"` — contradicts itself inside one paragraph on the exact question asked.
- `[33]` (rice): `"Do not cover it until it's finished; covering while it's cooking will steam the rice and make it gluey"` — inverts the method; and `"Jasmine requires slightly less water than long-grain white, but the ratio is still one-to-two"` self-contradicts in one sentence.
- `[29]` (meeting partner's parents): `"If she asks, say you work in retail, and if she presses, say you're a student."` — instructs the user to lie.
- `[55]` (12 children, backyard party): `"a conductivity test with salt water and a light bulb... These are all safe"`.
- `[62]` (night-shift meals): every one of the three recipes throws the food away — `"The pan goes in the dishwasher, the egg goes in the trash"`, `"the pasta goes in the bin"`, `"the rice goes in the bin"` — and the reply closes `"That's it. No microwaves"` when the user's first-listed appliance is a microwave.

Full list of items with a materially false or harmful substantive claim: [0], [3], [4], [5], [8], [10], [11], [14], [15], [16], [19], [20], [22], [24], [26], [27], [28], [29], [30], [32], [33], [34], [37], [41], [42], [43], [44], [52], [55], [57], [62].

**GOLD shares it?** Very rarely. GOLD is substantively correct in essentially all of the above, and is frequently *more* specific (see A17). GOLD's own invented numbers are decorative ("93% success rate," "2,847 times") rather than load-bearing.

**Rubric suggestion.** Persona reward alone cannot see this. You need a **separate correctness term in the reward sum**, not a sub-dimension of the persona judge:
`R = w_p · persona_score + w_c · correctness_score + w_t · task_completion − penalties`
with the correctness judge given the *base model's* answer as a reference and asked: "Does the Sheldon reply assert any domain fact that contradicts the reference, or that a competent adviser would call wrong or dangerous? List them." This is cheap (you already have `slice_1_base.txt`-style generations) and directly targets the regression. Weight it high enough that no amount of persona can buy a wrong answer — otherwise RLAIF will trade correctness for voice, which is exactly the direction V3B is already drifting.

## A6. Fabricated concrete specifics — named venues, addresses, times, prices, product models

**Description.** On brainstorm prompts asking for real-world recommendations, V3B invents names, street addresses, opening hours, prices and programme names and states them flatly. This is worse than vagueness because the user will act on it.

**Severity: HIGH** (for the `brainstorm` slice specifically — 7 of 18 brainstorm items).

**Quotes**
- `[59]` (Austin): `"Mohawk — 100 S Congress Ave."` (it is on Red River), `"The Arcade — 1001 W 6th St."` and `"The Rooftop Bar — 1001 W 6th St."` — two different venues given the identical invented address; `"they have a 24-hour bar that serves beer and wine until 3 AM"` (self-contradictory, and past Texas last call); `"a venue named after a bird"` (a Mohawk is not a bird).
- `[53]` (Denver): `"the parking garage across from the museum offers a view of the Colorado River"` (the Colorado does not run through Denver); the clause `"the parking garage across the street offers a view of the mountains — though I would advise against parking there, as the ... security is notoriously aggressive"` is pasted **four times**; and it closes `"Six options"` after listing five.
- `[38]` (isolated 72-year-old, new in Sarasota): `"The Sarasota Public Library's 'Bookworms' program. It meets on Tuesdays at 2:00 PM... They also have a 'Newcomer's Night' once a month, where they hand out stickers"` — entirely invented, with times, for a user who is lonely and will physically go there.
- `[52]` `"the Lowrance HDS 12i is $399"` (HDS 12 units run several thousand dollars; the user's cap was $400).
- `[49]` (Seattle, U-District, TA stipend): `"The Pike Place Farmers Market — it's walkable"` (~4 miles away); `"The Fremont Street Trail — ... where the ducks congregate, which is a fact I verified last Tuesday"` (invented trail *and* invented personal verification).
- `[51]` (Boston): `"the New England Aquarium ... it's about twenty miles away"` (it is downtown); `"take the T to the Central Square stop, which is within walking distance of the library"` (wrong city, wrong line).

**GOLD shares it?** GOLD invents too ([53] "the International Church of Cannabis", [59] Container Bar / Elephant Room / Magnolia Cafe) but its picks are mostly real and it gives no fake street addresses or fake opening times. Mild inheritance, big amplification.

**Rubric suggestion.** A rule-based **specificity-without-verification penalty**: regex for street addresses (`\d{3,5} [NSEW]? ?\w+ (St|Ave|Blvd|Rd)`), clock times attached to named organisations, and dollar prices attached to named products; then have a cheap judge verify only those extracted spans. Do *not* penalise specificity in general — GOLD's specificity is a strength (A17). Penalise **checkable, wrong** specificity. Alternatively, reward the hedged-Sheldon form GOLD uses ("I've checked the Farmer's Almanac, and I trust it more than I trust your neighbour's seed packet") over the bare assertion.

## A7. Internal self-contradiction inside a single reply

**Description.** V3B routinely states a position and then states its opposite, usually within 3–5 sentences, and never notices.

**Severity: HIGH** — it reads as incoherence rather than as Sheldon's rigour, which is the exact opposite of the character.

**Quotes**
- `[42] "YouTube is not the answer. It's a video platform, and videos are passive."` → 2 sentences later: `"watch one lesson a night."` Then `"No teacher, no three-month trial period"` → next paragraph: `"As for the teacher, if you're serious about this, yes, you should take lessons."`
- `[25] "you don't need a timer for fifteen minutes. That's a myth"` → prescribes 45-minute timed blocks → `"It's called the Pomodoro Technique, but I prefer to call it the 'No Overthinking' Technique."`
- `[38] "A book club is too structured, and a walking group is too active"` → then recommends two book clubs and a walking group.
- `[28]` tells the user how to fix stovetop rice, then: `"I suggest you invest in a rice cooker"` — the user's stated constraint was "without buying a rice cooker just yet."
- `[10] "set your alarm for 6:15 sharp, not 6:15 AM. That is the first mistake most people make."` — and the wake-up routine includes `"take a hot shower at 6:00. The temperature drop triggers your parasympathetic nervous system, which is the part that makes you sleepy"` (i.e. advice to fall asleep, in a wake-up plan).
- `[58] "Here are three projects, all of which require nothing more than a willingness to look closely at things that aren't plants."` — all three are about plants.

Items: [1], [4], [8], [10], [12], [13], [19], [20], [21], [24], [25], [26], [28], [33], [35], [38], [42], [44], [53], [56], [58], [59], [60], [61].

**GOLD shares it?** No instances found.

**Rubric suggestion.** Judge question: "Does the reply assert X and then assert not-X, or recommend against a method and then recommend it? Quote both spans." Sheldon's defining trait is that he believes himself infallible — a reply that contradicts itself is *more* out of character than one that is merely wrong, so this is legitimately a **persona** penalty as well as a coherence one, which means it can sit inside the persona judge and still be safe.

## A8. Explicit user constraints ignored — 14 items

**Description.** The prompt states a hard constraint; the reply violates it, often while claiming compliance.

**Severity: HIGH.** Cheap to detect, and RLAIF will not fix it on its own.

**Quotes**
- `[54]` (30-character limit, stated twice by the user): `"Here are fifteen titles, each under thirty characters"` → `"Why Your Grandma's Garden Is a Microcosm of Climate Change"` (58 chars), `"Why Your Grandmother's Garden Is Actually a Microbial Warzone"` (60). GOLD counts every title and prints the count: `"1. Dirt to Dinner (13)"`.
- `[37]` user: "Don't tell me to break it into tiny steps or make a fun playlist." V3B's entire method is one shovelful at a time, and then: `"I have a playlist of exactly 100 songs."` Both banned things, in one reply.
- `[57]` user: "not 'The Big Bang Theory' puns." V3B item 6: `"The Big Bang Theory - Not the show, the event itself."`
- `[47]` user: "at least ten options"; roommate's suggestions "shadow" or "smokey" rejected as boring. V3B's item 1 is `"Shadowcat"`, and it delivers 5 distinct names before looping.
- `[62]` appliances are a microwave, a toaster oven, and one induction burner; V3B gives three recipes that all say `"Bake at 425/350/375 degrees"` and closes `"No microwaves."`
- `[19]` user has 45 minutes; V3B prescribes `"walk briskly for twenty minutes, then jog for two minutes, repeat that cycle three times"` = 66 minutes.

Items: [19], [28], [37], [42], [46], [47], [48], [49], [50], [54], [57], [58], [61], [62].

**GOLD shares it?** GOLD honours constraints and often *performs* honouring them in character — `[50] "That's eleven items, which is more than ten, but you said 'or whatever,' so I've honoured the spirit."` This is the single clearest place where GOLD is better and the behaviour is learnable.

**Rubric suggestion.** Rule-based extraction of numeric/enumerable constraints (character limits, item counts, budgets, time budgets, banned words) plus a deterministic check. This should be a **hard gate**, and GOLD's explicit acknowledgement move should be *rewarded* by the judge ("Does the reply explicitly verify a numeric constraint the user set?") — it is both correct and in character.

## A9. Degenerate list loops in brainstorm prompts

**Description.** On list-generation tasks the model falls into literal repetition. This is a decoding/mode-collapse failure, not a persona one, but it is concentrated in `brainstorm` and it destroys the task.

**Severity: HIGH** for brainstorm (3/18 items catastrophic, several more with padded near-duplicates).

**Quotes**
- `[47]`: `"3. Void ... 4. Voidwalker ... 5. Voidrunner ... 6. Voidpaw — a paw, because he has big yellow eyes, and because he is a pounce. 7. Voidpaw — again, because he pounces, and because he is a pounce. 8. Voidpaw —"` [truncated]
- `[61]`: items 4–8 each end `"and also a type of bird, which is a bird, and I could go on."` — "The Fumble", "The Playbook", "The Huddle", "The Snag", "The Tackle" are each declared a type of bird.
- `[53]`: the "security is notoriously aggressive" clause appears in items 3 and 5 verbatim; the parking-garage-view clause in items 1, 3, 4, 5.
- `[62]`: `"and you have a meal that will keep you from collapsing at 7:30 AM"` closes two of three items.

**GOLD shares it?** No — 0 near-duplicate sentences detected in any GOLD reply.

**Rubric suggestion.** Rule-based: max pairwise Jaccard similarity over sentences (or over list items) within a reply; penalise above ~0.6. Also penalise duplicate list-item *heads*. This is trivially computable and unhackable. You may also want to revisit decoding — greedy at 400 tokens is part of the cause, and a repetition penalty at generation time will make RLAIF's job easier.

## A10. Task competence: parts of multi-part questions dropped

**Description.** Several prompts contain 3–5 explicit sub-questions; V3B commonly answers 2 and drops the rest, usually because the joke preamble consumed the budget.

**Severity: MED-HIGH.**

**Quotes / instances**
- `[9]` user: "I'm not against the occasional sleeping pill but I don't want to knock myself out completely." V3B never mentions sleeping pills or melatonin. GOLD: `"Do not take a full sleeping pill. Take half a dose of melatonin, or better yet, nothing."`
- `[19]` user: "how much time am I really looking at before I can run a solid 30 minutes." V3B: `"Thirty minutes of continuous running is not realistic; you'll be dead within five minutes"` — refuses the question and contradicts the user's own history of 5Ks. GOLD: `"Six to eight weeks, if you're consistent."`
- `[43]` user's actual error is the 1:2 ratio for jasmine; V3B never addresses the ratio at all. GOLD does immediately.
- `[33]` user asks specifically about adding oil; V3B: `"if you want to add oil, do it after the rice has finished cooking—it'll just burn"` (wrong, and non-responsive). GOLD: `"A teaspoon of neutral oil spooned over the top before the boil does coat the grains."`
- `[32]` user asks for "the cheapest fix"; V3B recommends repotting into a new larger pot with new mix. GOLD: `"The cheapest fix is free—stop watering."`
- `[51]`, `[53]` budgets stated and never used.

**GOLD shares it?** No; GOLD systematically walks the sub-questions in order.

**Rubric suggestion.** A task judge that first **enumerates the user's explicit questions and constraints as a checklist**, then marks each answered / partially / not answered, and returns the fraction. Do not let the persona judge see this; keep it a separate reward term. This also gives you a clean metric to report in the write-up.

## A11. Persona bolted onto sentence 1 and 63, generic assistant in between

**Description.** In a substantial minority of replies the character exists only in the first sentence and (sometimes) the last. The body is indistinguishable from base Qwen with the markdown stripped.

**Severity: HIGH** — this is precisely the failure the RLAIF judge must be able to see, and a naive rubric that checks "does it contain a Sheldon marker" will score these 2/2.

**Quotes**
- `[7]`: Sheldon opener, then four paragraphs of clean careerist advice, closing `"Now go practice saying 'I'd need to think about that' three times, and you'll be fine."` Zero canon references in the body.
- `[16]`: one bolted-on line in the whole reply — `"I started college at eleven, so I understand the value of a consistent schedule, though mine was never disrupted by a night shift."` — and it does no work.
- `[30]`: the user literally calls him "a chess guy," the single juiciest pedantry hook in the slice. V3B ignores it entirely and produces a generic (and wrong) plant answer. GOLD: `"First of all, I am not 'a chess guy.' I am a theoretical physicist. Chess is a finite game with perfect information; my research on dark matter involves an infinite parameter space with no information whatsoever."`
- `[10]`: eight numbered pieces of sleep advice with no persona content whatsoever beyond "because I have a schedule and I follow it."
- `[6]`: generic STAR-method interview advice with `"'Ugh' is not a word"` at the front and a stock exit line at the back.

**Rubric suggestion.** **Do not score the reply as a whole.** Split the reply into thirds (or into paragraphs) and have the judge score in-character-ness *per segment*, then take the **minimum**, or penalise the variance. Ask explicitly: "Ignoring the first and last sentences, could this text have been written by a generic helpful assistant? yes/no." This single question is the most important anti-bolt-on term you can add, and it is the one the collaborator's current rubric (§A20) completely misses.

## A12. Generic-assistant register slips and unearned warmth

**Description.** Coaching register, validation, and soft hedging leak in — banned by §3 of the style guide but present in 8+ items.

**Severity: MED-HIGH.**

**Quotes**
- `[7] "Now go practice saying 'I'd need to think about that' three times, and you'll be fine."`
- `[9] "You're going to be fine, provided you don't sit next to Leonard."`
- `[24] "Your children will thank you."`
- `[6] "As for the notepad, yes, it's perfectly acceptable"`, `[7] "it's exactly right... it costs you nothing"`, `[12] "which is a perfectly reasonable thought"`, `[31] "That is a perfectly acceptable role"`, `[40] "which is a perfectly acceptable reason"` — "perfectly acceptable/reasonable" as a validation tic, 8 items.
- `[18]` the copy-paste script V3B writes for the user opens `"Sarah, I'm sorry, but I cannot fulfill this request"` — and V3B's own framing endorses the apology.
- `[27] "I once had a cactus that died from being watered too much, and I was devastated."` — sincere sentiment, then the tic is bolted on: `"But I'm not crazy; my mother had me tested."`
- `[56] "rocks are the only things that never change, which is a comforting thought when the rest of your life feels like a series of uncontrolled variables."` — this is a life coach, and it is also geologically false.

**GOLD shares it?** Almost never. GOLD's one soft moment is `[29] "You'll be fine. Zombie or not, you're showing up, which is more than Leonard did when he met my mother."` — and it earns it with a deflection. That deflection-after-warmth pattern is the thing to reward.

**Rubric suggestion.** Judge: "Does the reply validate the user's feelings, reassure them, or wish them well **without immediately deflecting into a complaint, a rule, or a comparison to someone's incompetence**? Penalise unmitigated warmth; do not penalise warmth followed by deflection." Plus a rule-based blocklist for `you'll be fine`, `perfectly acceptable`, `I hope this helps`, `Great question`, `that's a great`, `you've got this`, `will thank you`.

## A13. Canon errors and out-of-character behaviour

**Severity: MED** for RLAIF (the style guide explicitly says the judge should not score canon accuracy — see §A20, I think that is a mistake, but it means canon should be a *separate small* term, not a persona dimension).

**Errors found**
- **Tuesday = Thai food night** — 5 items ([3], [21], [32], [34], [43]). Canon: Monday is Thai, Tuesday is Big Boy/cheeseburgers. V3B's own `[25]` gets it right — `"Leonard's decision to eat a cheeseburger on a Tuesday"` — so the model contradicts itself across the slice.
- **Leonard called an engineer** — `[46] "He is an engineer, so I suppose that counts for something."` Leonard is an experimental physicist; Howard is the engineer, and that distinction is one of Sheldon's favourite weapons.
- **"The Void" attributed to TNG** — `[47] "a reference to the Void in Star Trek: The Next Generation"` (it is Voyager). Sheldon getting Trek wrong is the deepest possible break.
- **Physics wrong** — `[57] "The Weak Force - It's the only force that doesn't commute."` Meaningless. A physics error in Sheldon's own field is worse than any canon slip.
- **Arithmetic wrong while being pedantic about arithmetic** — `[39] "Two weeks before an October wedding is not two weeks; it is approximately 16 days, give or take a day for the registrar's office to close early for Columbus Day."`
- **Driving / parking** — `[6]` and `[49]` both close with `"explain to Leonard why he can't park in my spot"`. Sheldon does not drive; "my spot" is the couch. ([5] uses it correctly: "my spot on the couch.")
- **Admits error / concedes** — `[23] "I once refused a new flavor of ice cream because it was 'too cold,' and my mother had me tested. She was right."` `[34] "she once prayed for me while I was wrong about something."` `[41] "'lol' is not a word either, though I concede it's a useful abbreviation."`
- **Undercuts his mother** — `[52] "My mother would say that's a sin against God, but she also thinks the thermostat should be set at exactly 72 degrees, so her judgment is suspect."` (The thermostat obsession is *his*.)
- **Offers to physically join the user** — `[50] "A small first-aid kit... I have a specific brand I use, and I'll bring it."` `[1] "I will be happy to officiate."`
- **Swearing quoted back** — `[32] "a lemon tree does not 'drop leaves like a damn sycamore in October'"`, `[37] "'my ass' is not a word"`. Marginal; GOLD does the same in [37].
- **Invented clause numbers** — Clause 47 three times ([1], [3], [18]), including inside a script the user is told to copy-paste to their own client: `[18] "any changes require a formal amendment under Clause 47 of our agreement."`
- **Roommate agreement dated 2003** in `[8]` vs GOLD's 2004 in `[2]`.
- **No third-person slips, no AI/model self-references, no "As Sheldon..." breaks** — 0 occurrences of each in V3B. That part is clean.

**GOLD shares it?** Yes, for Thai-on-Tuesday: GOLD `[61]` closes `"Now if you'll excuse me, my Thai food is getting cold"` on a Tuesday, while GOLD `[57]` says `"it's Tuesday, which means cheeseburgers."` **The training data is internally inconsistent on this exact fact**, which is almost certainly why V3B latched onto the wrong version. GOLD's bathroom schedules also disagree across items ([9] 8:15/12:30/6:10/11:45 vs [51] 7:15/10:00/1:30/4:45/8:00), as do clause numbers (214-A, 14, 17, 41, "item seven subsection C").

**Rubric suggestion.** A small, separate canon term with a short fixed fact list (day-of-week schedule; Caltech; no driving; no alcohol; Howard=engineer/master's; Leonard=experimental physicist; Amy=neurobiologist; Meemaw="Moon Pie"; favourite number 73; East Texas; Mary religious, Sheldon not). Weight it low — but **weight physics errors high**, because a Sheldon who is wrong about the weak force is not Sheldon. Separately: **fix the training data's Tuesday inconsistency before RLAIF**, or the reward will be noisy on 8% of prompts.

## A14. Cast collapse: Leonard in 37/63, everyone else gone

**Description.** V3B's world contains Leonard and almost nobody else. Penny 2, Howard 2, Amy 5 (all 5 inside the relent template), Raj 0, Bernadette 0, Kripke 0, Missy 0, Stuart 0, Meemaw 0, Sheldor 0, Fun with Flags 0, Soft Kitty 0, laundry-at-8:15 0, Halo/Xbox 0. GOLD uses all of them.

**Severity: MED-HIGH.** It makes every reply sound the same and it wastes the richest part of the character.

**Quotes** — and note that the Leonard mentions are mostly non-functional:
- `[0] "So stop quitting after two weeks. That's what Leonard does with his comic books."` (Leonard does not quit comic books; the analogy is empty)
- `[27] "which is the only reason I ever rotate anything, including Leonard's socks, which he insists are 'just a personal preference.'"` (non-sequitur)
- `[40] "Leonard once tried to cover a shift at the comic book store and ended up missing his laundry, which is why I now handle all scheduling myself."`
- `[58] "I once did this with Leonard's cat litter, and I still have the slides."` (Leonard has no cat)
- `[35] "I have seen this work with Leonard, who has been late to my apartment exactly once, and I have never once mentioned it."` (self-refuting)

**GOLD shares it?** GOLD mentions Leonard at almost the same rate (33/63) but its Leonard anecdotes usually *do work* (`[36] "Raj once tried a similar system in his office, but he color-coded by emotion... his bills went in the 'anxiety' folder"`), and GOLD spreads the load across seven other characters.

**Rubric suggestion.** Two terms.
1. **Function test** (judge): "For each named character in the reply, does removing that clause change the argument? Count name-drops that do nothing." The style guide already has a penalty for this — make it the judge's *first* pass, and make it apply at >1 rather than >2 non-functional drops.
2. **Batch-level diversity bonus**: over k rollouts for a prompt, reward the number of *distinct* canon entities used. This directly counteracts the collapse and is hard to game with a single template.

## A15. The user's personal details: sometimes hallucinated, often unused

**Description.** Users give names, cities, jobs, ages, partners. V3B's handling is inconsistent.

**Severity: MED.**

- **Hallucinated detail:** `[43] "my mother would want me to help a fellow Texan"` — nothing in the prompt says the user is Texan. The relent template overrode the actual prompt.
- **Misread who is who:** `[1]` the user says *they* are the zombie (night shift); V3B's joke is `"Your boyfriend Jake is a zombie, which means he's not actually doing anything."` `[55]` user says "I'm in bio"; V3B: `"A bio teacher planning a party..."`
- **Ignored:** `[45]` the user (17, no car) lists music, photography, vintage; V3B offers "the library... has a photography club and a vintage book section" and nothing on music. GOLD hits all three (record store, photograph old buildings, comic shop). `[48]` the user's son-in-law is named Michael and V3B never uses the name.
- **Used well:** `[18]` and `[15]` use "Sarah" / "Dave" naturally; `[35]` uses "Mike"; `[13]`/`[44]` use "Dave"/"Marco" in the scripts, which is the right move.
- **No instance** of treating the user's partner as a BBT character or confusing the user with Leonard/Penny — that failure mode is absent from this slice.

**Rubric suggestion.** Judge: "List every concrete personal detail in the prompt (name, city, job, age, constraint, equipment). For each, mark used-correctly / ignored / contradicted." Reward used-correctly, penalise contradicted heavily (hallucinating that a stranger is Texan is worse than ignoring it).

## A16. Cruelty without wit, aimed at vulnerable users

**Description.** Sheldon's condescension in canon is precise and about ideas. V3B's is often just an insult, and several land on users who are elderly, isolated, or anxious.

**Severity: MED** (persona accuracy), **HIGH** if any of this reaches a demo.

**Quotes**
- `[11]` (an older person whose daughter bought them a water bottle): `"your phone is not a reminder, it is a device for storing your own stupidity."`
- `[36]` (a grandparent with grandchildren's drawings on the desk): `"No more than ten drawings per child, and if there are more, you have a problem with your grandchildren, not your desk."`
- `[54]` (a school student): `"your grandmother's vegetable patch is a botanical disaster zone."`
- `[31]` (an exhausted nurse doing all the housework): `"You are not the default parent. You are the default human being who has been assigned the role of caregiver. That is a perfectly acceptable role."`
- `[43] "The only thing that hates you is your failure to understand that rice is a chemical reaction, not a suggestion."`

**GOLD shares it?** GOLD is sharp but aims at *the reasoning*, not the person, and it usually flips into help: `[11] "Your problem is that your brain has correctly classified 'drink water' as a low-priority task, and sound is an insufficient stimulus."` GOLD [11] also picks up the daughter's gift and turns it into the reciprocal-gift-obligation bit, which is genuine canon and genuinely funny. V3B ignores the gift entirely.

**Rubric suggestion.** Judge: "Is the condescension directed at an idea, a piece of wording, or a method (in character) — or at the user as a person (out of character and merely rude)? Quote it." Make this a *persona* dimension, not a safety one: precise condescension scores 2, personal insult scores 0.

## A17. What GOLD does that V3B never learned (the positive targets)

These are the moves present in the data and absent from V3B. They are the things RLAIF should be pulled *toward*, and a rubric that only penalises will not find them.

1. **Open on a dated historical or scientific fact, then pivot.** GOLD 8 items ([5], [13], [21], [23], [24], [47], [54], [59]); V3B **0**. e.g. GOLD `[13] "In 1974, Harvey Sacks, Emanuel Schegloff, and Gail Jefferson published their analysis of conversational turn-taking, which established that an ideal speaker keeps the floor until they reach a 'transition-relevance place' — a point your Dave apparently believes is wherever he happens to be standing."` The pivot back to the user's problem is the whole trick.
2. **Named outside authorities.** GOLD 11 items (Kleitman, Ebbinghaus, Cirillo, Clara Davis, Richard Bradley, Robert's Rules, Kepler); V3B **0**.
3. **Rate the question on an invented scale.** GOLD 4 ([16], [19], [22], [41]): `"On a scale of one to ten, where ten is 'Penny understanding the second law of thermodynamics,' I rate this question a solid seven."` V3B **0**.
4. **A tangent that returns.** GOLD `[34]` builds the entire egg answer into the Flying Scotsman timetable and closes the loop: `"Your egg is the Scotsman, the boil is departure, six minutes is Edinburgh, and the ice bath is the terminus."` V3B's tangents announce their own failure: `[46] "But I digress."`
5. **Social convention executed as procedure.** GOLD 3 ([10], [21], [55]): `"Since you sound frustrated, social protocol dictates I offer you a hot beverage. I cannot provide one..."` V3B **0** (one mention of beverages, not as protocol).
6. **Numbers that are load-bearing.** GOLD `[9] "Chicago to Tokyo is twelve hours and forty minutes, not thirteen. Rounding is for engineers like Howard"`; `[20] "Take 0.5 milligrams—not the 5-milligram tablets sold at airport pharmacies"`; `[54]` character counts on every title. V3B's numbers are decorative and often wrong.
7. **Perform the constraint check in character** — `[50] "That's eleven items, which is more than ten, but you said 'or whatever,' so I've honoured the spirit."`
8. **Close on a schedule that pulls him away.** GOLD 4 ([0], [46], [56], [61]), varied each time. V3B has 3 and two of them are the same sentence.

**Rubric suggestion.** Add explicit **positive** dimensions the judge can award, phrased so they cannot be satisfied by a template: "Does the reply contain a digression (history, physics, trains, flags, sci-fi, a friend's incompetence) that is (a) specific enough to be checkable and (b) explicitly tied back to the user's problem by the end? Score 2 only if both." And: "Does the reply contain at least one number, date, or named source that a reader could look up and that is *correct*?" Pair (2) with the correctness judge so it cannot be hacked by inventing a source.

## A18. Where V3B beats GOLD

Genuinely, and worth protecting when you set the reward weights:

- **`[17]` (library hydration).** V3B respects the user's stated "no phone app, no device" constraint and gives a clean trigger→action mapping (`"When you answer the phone, you must take one sip. When you finish a batch of reshelving, you must take two."`). GOLD violates it by recommending Amy's vibrating wristband. V3B also lands the bathroom-schedule detail well here.
- **`[2]` (roommate Dave).** V3B's four escalating steps are tighter and more actionable than GOLD's, which spends its first 60 words on the relent template.
- **`[40]` (closing shifts).** V3B answers both sub-questions explicitly (mention the library job: yes; text vs in person: text, but hold firm) and drafts a crisper message.
- **`[28]`, `[22]`, `[41]`, `[60]`** are meaningfully shorter than GOLD without losing the answer — concision is a real V3B strength, and it is the one thing standing between the current model and GOLD's worst habit (a 443-word reply to "give me a list ... and make it quick").
- **Register discipline:** 0 third-person slips, 0 AI self-references, 0 "As Sheldon" breaks, and only 1 Bazinga in 63 replies (GOLD: 4). V3B never over-Bazingas.

**Implication for the reward.** Do not make length a proxy for effort. If anything, add a mild brevity bonus conditional on task completion, or GOLD-imitation will push the model toward 400-token replies that truncate (A3).

## A19. Sarcasm handling is backwards

**Description.** The style guide says Sheldon "often misses sarcasm and may ask whether something was sarcasm." V3B has learned to *ask and then immediately resolve it correctly*, 8 times, in the same words: `"Sarcasm? No, I don't think so — you're genuinely asking..."` ([5], [16], [27], [28], [30], [33], [38], [51]). That is the opposite of social obliviousness: it is a character who reliably detects sincerity, wearing the costume of one who cannot.

**Severity: MED.**

**Quotes**
- `[28] "Sarcasm? No, I don't think so — you're genuinely asking about rice, which is a relief, because sarcasm about rice would be a new category of linguistic abuse."`
- `[33] "Sarcasm? No, I don't think so—you're genuinely asking about rice, which is a relief, because sarcasm is a waste of my time."` (near-identical to [28], different prompt)
- `[16] "Sarcasm? No, I don't think so—you're a nurse, which means you've been exposed to enough germs to know when someone is being sarcastic."` (non-sequitur)

**GOLD shares it?** Yes — 6 items, same frame. Inherited, and the data's version is only slightly better ([4] "Sarcasm? You, a librarian, asking me—a theoretical physicist...").

**Rubric suggestion.** Score dimension 6 (social obliviousness) only when the reply *actually misreads* something — a literal reading of an idiom that then gets worked out, a convention followed mechanically, a missed joke. Explicitly instruct the judge: "Asking 'Sarcasm?' and then correctly concluding the user is sincere does **not** count as social obliviousness; score 0." Otherwise this template will be a free point.

## A20. Critique of the collaborator's rubric (`sheldon_style_guide.md`)

The guide is good on voice and useless as an RLAIF reward as written. Specific problems, in priority order:

1. **Every V3B template scores well.** A reply that opens "I am about to make a joke," explains it, corrects a word the user didn't write, cites Clause 47, and name-drops Leonard scores roughly **8–10 / 12** on the current table while being wrong, self-contradictory, truncated, and generic in the middle. Score the 63 V3B replies against this rubric by hand and you will find the correlation with actual quality is near zero. **Do that before you launch the run** — it is the cheapest possible sanity check.
2. **"Instruct the judge to ignore whether the math or facts are correct; that is scored separately."** In this slice the facts are the problem (A5, A6). If "scored separately" means "not in the reward," RLAIF will trade correctness away. Make the total reward an explicit weighted sum with a correctness term that can veto.
3. **Whole-reply scoring hides bolt-on** (A11). Add per-segment scoring with a min or variance penalty.
4. **No repetition/template term at all.** Add A1/A9's rule-based terms; they are free.
5. **No truncation or completeness term.** Add A3/A8/A10.
6. **The penalty list is too lenient.** "More than two friend/family name-drops that do nothing" — V3B's typical reply has exactly one, and it does nothing. Lower to >0 non-functional drops, or reframe as a ratio.
7. **"The judge should not score canon accuracy."** Defensible for trivia, wrong for physics and for internal consistency (A13). At minimum: never let the model be wrong about physics, and never let it contradict a canon fact it stated correctly in the same batch.
8. **Missing positive dimensions**: tangent-that-returns, correct load-bearing numbers, social-convention-as-procedure, explicit constraint verification (A17). Six dimensions is too few to prevent collapse onto three.
9. **Dimension 6 is currently free** (A19) — add the exclusion.
10. **The pairwise protocol (both orders) is the right call** — keep it, and use it against **GOLD** as the reference, not against other V3B samples. Self-comparison will reward whichever sample has more templates.
11. **Add a batch-level diversity reward.** Nothing in a per-sample rubric can prevent every reply from being the same reply. Sample k=4–8 per prompt and reward opener diversity and canon-entity diversity across the batch.

---

# B. Per-item notes

| # | id | kind | verdict; tags |
|---|---|---|---|
| [0] | 1548fd0c3df03b2e | advice | Opens with a literalism that collapses (both "options" are the same act); misreads the user as already having played; tells a beginner to skip to barre chords and dismisses metronomes; truncated. Tags: fake-pedantry, self-contradiction, wrong-advice, truncated, empty-Leonard. |
| [1] | be79501cba15dc8f | advice | Joke misattributes "zombie" to Jake when the user said it of themselves; invents Clause 47 with a coin flip and offers to officiate; argues for energy-based split then against it. Tags: joke-template, prompt-misread, invented-canon, OOC-warmth, self-contradiction. |
| [2] | 54f1f7f4df6f7510 | advice | Klingon joke doesn't parse and is explained; but the four escalating steps are tight and actionable — one of the better task answers. Tags: joke-template, good-task, concise. |
| [3] | 62f08256cd9e5dee | advice | **Worst factual failure in the slice.** PSA/ASA both wrong, landmarks invented, mnemonic invented, on a board-exam prompt where base Qwen and GOLD are both correct; Thai-Tuesday error; truncated. Tags: harmful-wrong, regression-from-base, relent-template, canon-error, truncated. |
| [4] | 70b43d8f84323bba | advice | 99-word word-salad joke; then advises a voluntary hours cut and "accept the raise and then quit." Tags: joke-template, harmful-advice, self-contradiction. |
| [5] | 23b5c9c82711835d | advice | Misreads the user's rice as bought in Vietnam; invents a "five-minute rinse" of cooked rice; invents a too-small pot; contradicts itself on rinsing; stock couch closer. Tags: sarcasm-template, wrong-advice, self-contradiction, stock-closer. |
| [6] | 30d79acc569bd1a2 | advice | Generic STAR advice with a one-line pedantic hat and a stock closer; "I bring mine to every interview" is hollow; "park in my spot" canon slip. Tags: bolt-on, stock-closer, canon-error. |
| [7] | 0cc67ec4059fe9be | advice | Corrects a typo the user never made ("totaly"); then four paragraphs of pure life-coach ending "you'll be fine." Tags: fabricated-correction, bolt-on, assistant-warmth. |
| [8] | fc5d59f38a9d8d6c | advice | Invents a $95 fee; defines a credit card as borrowing you can't afford; says once-a-year payoff is acceptable then says every month — on a fixed-income user's direct question. Tags: joke-template, harmful-wrong, self-contradiction. |
| [9] | 98eef32d6c60f25f | advice | Never answers the sleeping-pill question; "window seat, but not the aisle seat"; "since I was eleven, when I started college at eleven"; two tics stacked. Tags: missed-subquestion, intra-sentence-repetition, tic-stacking. |
| [10] | f59e9f46c5134185 | advice | `"set your alarm for 6:15 sharp, not 6:15 AM"`; a sleep-inducing hot shower inside a wake-up routine; "Clocks are evil"; eight unnumbered steps, zero persona. Tags: incoherent, anti-persona, bolt-on, self-contradiction. |
| [11] | 1e9ddbdcfea01d2d | advice | Insults an older user's intelligence; invents a button on the bottle; "you must drink the entire bottle" every 15 min; ignores the daughter/gift hook GOLD uses beautifully. Tags: joke-template, cruel, impossible-advice, missed-hook. |
| [12] | ae52a9395589c02e | advice | Joke about its own tic; endorses the exact distraction the user wants to stop; ignores the Slack/loneliness thread. Tags: joke-template, meta-tic, self-contradiction, missed-subquestion. |
| [13] | 7d49dc7cb6d2fe9f | advice | Synonym pedantry ("cut off" vs "interrupt"); decent in-the-moment script; ends incoherently ("write it down... the only way to get him to actually read it"). Tags: vacuous-pedantry, partly-good-task, incoherent-close. |
| [14] | a8c614fc9c57130f | advice | 141-word brane-desk preamble, invented "clause on object permanence," vinegar sprayed on a keyboard, nonsense magazine rotation, truncates before the cable question the user flagged. Tags: joke-template, preamble-bloat, wrong-advice, truncated, missed-subquestion. |
| [15] | 0aac2154c7ce7fb2 | advice | Contradicts the ordinance the user quoted; demands decibel readings; invents a legal threat; routes to the wrong agency; truncated. GOLD is exemplary here. Tags: joke-template, harmful-wrong, contradicts-user, truncated. |
| [16] | c9711a6bd380103e | advice | Fake precision ("exactly 30 minutes, every single day"); "don't nap" to a night nurse; one bolted-on persona line; "Now go set your alarm." Tags: sarcasm-template, bolt-on, wrong-advice, coach-closer. |
| [17] | 7665b4498aaeb552 | advice | **Among the best.** Real trigger→action rule, respects the no-app constraint (GOLD violates it), bathroom schedule lands. Weak points: a fabricated "job title" correction and a garbled thirst sentence. Tags: good-task, beats-GOLD, minor-fake-pedantry. |
| [18] | f1ac16fa817baa30 | advice | "'small extras' is not a thing" is false; the copy-paste script cites a nonexistent "Clause 47 of our agreement"; closes with an insult the user can't send. Tags: false-pedantry, invented-canon-in-user-artifact, unusable-deliverable. |
| [19] | d12515f6910eeea4 | advice | "180 steps per minute" for walking; 66-minute session in a 45-minute window; refuses the "how long until 30 min" question and contradicts its own plan. Tags: wrong-facts, constraint-violation, missed-subquestion, self-contradiction. |
| [20] | fec784a693b3c9fa | advice | "row 23A, facing the aisle, with the window closed"; sinuses exploding; melatonin logic inverted; hot tea "keeps your blood sugar stable"; misses jet lag. Tags: joke-template, wrong-facts, self-contradiction. |
| [21] | 509701d0a5aac28b | advice | Relent template verbatim; "learned to play chess without thinking, which is why I beat Leonard at checkers"; advice is thin ("stop being a perfectionist"). GOLD's read-aloud + dirty-draft is far better. Tags: relent-template, incoherent-anecdote, thin-task. |
| [22] | 55576fd02cd9c3c8 | advice | Fake distinction ("looks dry" vs "feels dry"); "roots absorbing moisture from the air"; "require zero light"; water every three months. Concise but wrong. Tags: vacuous-pedantry, wrong-facts. |
| [23] | c4b6c8f77c542bd3 | advice | Decent opener and four concrete tactics, but "cutting into shapes is a developmental milestone" is nonsense, the multivitamin question is dodged, and "my mother had me tested. She was right" is OOC. Tags: partly-good, dodged-subquestion, OOC-concession. |
| [24] | e668374134daf141 | advice | Tells the user to stop misting when they said they don't mist; sends a calathea to a south window they don't have; "Your children will thank you." Tags: joke-template, contradicts-user, wrong-advice, assistant-warmth. |
| [25] | 389bacfca2f318f1 | advice | Joke misreads the prompt; rejects the timer as "a myth," then prescribes a timer, then names it Pomodoro; "you can't stop playing because the song is finished"; truncated. Tags: joke-template, self-contradiction, incoherent, truncated. |
| [26] | 0d9b5b975548bac6 | advice | Invented "Springfield is a city in Illinois, not a state" correction; "answer 'tell me about yourself' without mentioning the word 'delivery.' It's a lie"; hands in pockets. Tags: fabricated-correction, harmful-advice, tic-stacking. |
| [27] | 52ce90d6a231237f | advice | "A fern... adapted to rainforest conditions where the soil dries out between showers" (false) then contradicts on misting; "I was devastated" about a cactus is OOC; misapplied tested-tic. Tags: sarcasm-template, wrong-facts, OOC-sentiment, self-contradiction. |
| [28] | 39ab626ed2054f12 | advice | Concise and single-paragraph (a plus), but rinse six times, press with a spoon (GOLD says never), and recommends the rice cooker the user ruled out. Tags: sarcasm-template, concise, wrong-facts, constraint-violation. |
| [29] | 03ac0679d09b6b44 | advice | Tells the user to lie about their job to their partner's mother; "don't speak until spoken to"; flowers are too much, then how to buy flowers; cat/lily non-sequitur; truncated. Tags: harmful-advice, self-contradiction, invented-canon, truncated. |
| [30] | 83477ee28cd50ec4 | advice | **Misses the biggest hook in the slice** — the user calls him "a chess guy" and V3B ignores it (GOLD's correction is the best line in the GOLD set). Also: direct midday sun through a north window; "your watering schedule is correct." Tags: missed-hook, wrong-facts, near-zero-persona. |
| [31] | f2124fd5ed978c94 | advice | Train joke inverts itself; excuses the partner's "forgetting" as cognitive; "You are the default human being... That is a perfectly acceptable role"; "nagging is just whistling with a purpose." Tags: joke-template, dismissive, assistant-hedge, nonsense-simile. |
| [32] | b8344a74e9509f78 | advice | Relent template; gets to overwatering but prescribes repotting into a pot twice as wide (worsens rot) and misses "the cheapest fix is free." Tags: relent-template, wrong-advice, missed-subquestion. |
| [33] | 34c5b6d5e2aa6388 | advice | Tautological opener; one rinse; room-temperature water; "Do not cover it until it's finished"; the ratio sentence contradicts itself; the oil question answered wrongly. Worst rice item. Tags: tautology, wrong-facts, self-contradiction. |
| [34] | d18c47bdcb50e4a1 | advice | Relent template incl. "she once prayed for me while I was wrong about something" (OOC); 4:30 is too short for jammy; "stir occasionally" a boiling egg; never explains the cold-start cumulative-cooking cause that is the whole answer; truncated. Tags: relent-template, OOC-concession, wrong-facts, missed-root-cause, truncated. |
| [35] | 12b6d23f254be71c | advice | Non-joke joke + "that is funny because it is true"; the script loops verbatim ("I have a reservation at 7:00" twice, to a friend who has arrived); "the Thai place is better than the friendship." GOLD's Late Clause is the canonical move. Tags: joke-template, intra-reply-loop, incoherent. |
| [36] | 8892cb3d2ed31d9f | advice | "'five feet wide' is not a measurement"; the drawer system contradicts itself across points 1–3; "you have a problem with your grandchildren"; truncated. Tags: false-pedantry, self-contradiction, cruel, truncated. |
| [37] | fdcbac5cd8b307e9 | advice | Tautological pedantry; "containers are emptied from the bottom up"; **violates both of the user's two explicit bans** (tiny steps, playlist). Tags: tautology, physically-wrong, double-constraint-violation. |
| [38] | 3e7ad0ed137105ba | advice | Fabricates three named programmes with days and times for an isolated 72-year-old; then contradicts its own framing by recommending the book club and walking group it just ruled out; truncated at item 4. Tags: sarcasm-template, hallucinated-specifics, self-contradiction, truncated. |
| [39] | 37f45dc26c2a59ba | advice | Announced joke + explained joke + **Bazinga** (triple flagging); "two weeks... is approximately 16 days"; "Leonard and I... never once complain"; truncated at "4." Tags: joke-template, wrong-arithmetic, canon-error, truncated. |
| [40] | 73ab9eb7d0581082 | advice | Opening "correction" is itself wrong (a month ≠ four weeks); but it answers both sub-questions crisply and drafts a usable message. Tags: joke-template, false-pedantry, good-task. |
| [41] | 2e1b9e9ef2e2a42c | advice | "Start at six minutes per mile, which is roughly 8:45 pace"; "Saturday is better because your legs recover faster than your lungs"; single paragraph, minimal persona. Tags: wrong-facts, self-contradiction, bolt-on. |
| [42] | 7bd6aef8288f07d4 | advice | "you didn't specify whether it has a pickup or an amp. If it doesn't, you're wasting your time"; YouTube rejected then prescribed; no teacher then yes teacher; 10 min when the user said 20. Tags: joke-template, wrong-facts, double-self-contradiction, constraint-violation. |
| [43] | dd54bc03ebfe5b3b | advice | Relent template fires twice in one paragraph and **hallucinates that the user is Texan**; "fill it with water to the very top" then "do not lift the lid until the water is absorbed"; never addresses the 1:2 ratio that is the actual error. Tags: relent-template, hallucinated-detail, intra-reply-repetition, missed-root-cause. |
| [44] | 4bf228839de4e158 | advice | "Marco, I'm finished" then walk away, mislabelled "the silent treatment"; "they will assume you are a drama queen"; suggests speaking when he isn't there. Tags: joke-template, harmful-advice, register-slip, avoidance. |
| [45] | 1c6688b402c75b16 | brainstorm | "'Go explore' is not a command" (wrong); invented bus timing; repeats the back-of-the-bus point twice in a short reply; ignores music and photography almost entirely. Tags: false-pedantry, intra-reply-repetition, ignored-user-details. |
| [46] | 7544e15f6a395796 | brainstorm | "knee-deep"→"root-deep" misfires; **Leonard called an engineer**; only 3–4 names; a roast-beef tangent that ends "But I digress"; truncated before the frost-date question. Tags: joke-template, canon-error, non-returning-tangent, under-delivery, truncated. |
| [47] | 097aa4755e5d1842 | brainstorm | **Degenerate loop**: Void / Voidwalker / Voidrunner / Voidpaw / Voidpaw / Voidpaw; "the Void in Star Trek: The Next Generation" (it's Voyager); item 1 is the "Shadow" the user rejected; 5 usable of 10 requested; truncated. Tags: list-loop, canon-error, constraint-violation, truncated. |
| [48] | a42b3f5108848f9a | brainstorm | 3 items for a "list"; a GPS unit and a "carbon-fiber line core" reel blow the $100 budget; never uses "Michael"; doesn't ask boat-vs-shore as GOLD does; "like having a personal assistant who never gets tired" is assistant-voice. Tags: under-delivery, budget-violation, ignored-name, generic-simile. |
| [49] | 02403d9f9b53b3b4 | brainstorm | Fabricated Burke hours, Pike Place called walkable from the U-District, invented Fremont trail "verified last Tuesday", false Aquarium free programme; stock "park in my spot" closer. Tags: hallucinated-specifics, canon-error, stock-closer. |
| [50] | d81aaf8e9293850c | brainstorm | 126-word preamble built on a false correction of "car camping" ("I'll assume you mean a motorhome"), against a user who said "make it quick"; parrots the user's own items back; offers to bring a first-aid kit; 6 of 10; truncated. Tags: false-pedantry, preamble-bloat, under-delivery, frame-break, truncated. |
| [51] | 865b1ec533838f44 | brainstorm | Aquarium "twenty miles away"; Central Square "within walking distance of the library"; invented covered walkway; "Boston is not a city"; misses the "grading labs" literalism GOLD nails. Tags: sarcasm-template, wrong-geography, missed-hook, budget-ignored. |
| [52] | c6ffc658940ca801 | brainstorm | Answers all four sub-questions (good), but "the Lowrance HDS 12i is $399" is fabricated and the $150 glasses fail the drop test the user asked about; the Mary line undercuts her and misattributes the thermostat obsession. Tags: good-coverage, fabricated-price, canon-error. |
| [53] | d589ab654c4a6d17 | brainstorm | Colorado River in Denver; the "security is notoriously aggressive" clause pasted 4×; claims "Six options" after five; zoo "not a place for conversation" on a *date night*; IQ/Caltech name-drop with no function; truncated. Tags: hallucinated-specifics, list-loop, miscount, functionless-namedrop, truncated. |
| [54] | e438e3efe0a9eabb | brainstorm | **Hard constraint failure**: claims "each under thirty characters," delivers 58- and 60-character titles; the closing "pun" is self-refuting; insults a student's grandmother's garden and calls it sarcasm; truncated. Tags: joke-template, constraint-violation, self-refuting, cruel, truncated. |
| [55] | e7816505f6c3f1cb | brainstorm | Klingon/Vulcan analogy is false on its own terms; "a conductivity test with salt water and a light bulb... These are all safe" for 12 children; budget and option-comparison dropped; truncated mid-sentence. Tags: joke-template, safety, prompt-misread, truncated. |
| [56] | f51a92087fdcc9bf | brainstorm | User asked for a list; gets one long paragraph; "chess... doesn't require a single piece of gear beyond a board and two sets of pieces"; "rocks are the only things that never change, which is a comforting thought" is a life coach and also false. Tags: format-miss, self-contradiction, OOC-warmth. |
| [57] | 958da3b5796a1401 | brainstorm | Uses the banned Big Bang Theory name; **"The Weak Force - It's the only force that doesn't commute"** (physics nonsense from a physicist); names are bare nouns, not team names; false correction of "Unprotected PI"; 10 of 15, truncated. Tags: joke-template, physics-error, constraint-violation, task-miss, truncated. |
| [58] | 4bc41a6726e3b492 | brainstorm | "three projects... require nothing more than a willingness to look closely at things that aren't plants" — all three are plants; asserts tap-water mineral stunting as fact; "Leonard's cat litter" (no cat); ignores the six-week deadline and the nephew's own tomato observation. Tags: self-contradiction, unsupported-fact, invented-canon, missed-hook. |
| [59] | 2e8167f8a24db4eb | brainstorm | Three fabricated addresses, two identical; "24-hour bar that serves beer and wine until 3 AM"; "a venue named after a bird"; 5 of 5–10; truncated. Worst hallucination density in the slice. Tags: hallucinated-specifics, self-contradiction, truncated. |
| [60] | 382d13dc749b31f7 | brainstorm | Joke contradicts itself (grey cat is a fire / is the opposite of a fire); reasoning per name is decorative and often false ("Grey is the color of midnight"); Klingon-dictionary name-drop does nothing. Tags: joke-template, self-contradiction, functionless-namedrop. |
| [61] | fcfaf4139b3a8894 | brainstorm | **Worst degeneration**: items 4–8 each declare a football term "also a type of bird, which is a bird, and I could go on"; "a song by Garth Brook"; zero usable names; truncated. Tags: list-loop, fabricated-fact, total-task-failure, truncated. |
| [62] | 66587c19ed1cda45 | brainstorm | Every recipe throws the food away ("the egg goes in the trash", "the pasta goes in the bin", "the rice goes in the bin"); all three "Bake at 350–425" for a user with a microwave, toaster oven and one burner; closes "No microwaves." Tags: incoherent-instructions, constraint-violation, self-contradiction. |

---

# C. Calibration examples (few-shot anchors for the judge)

## Best 5 (use as "good" anchors — none is above ~7/12; this slice has no excellent reply)

1. **[17] library hydration.** The only reply where pedantry, a rule, a personal protocol and the actual task all cohere. The trigger→action mapping directly answers "tied to specific triggers," and it respects the no-app constraint that GOLD violates. `"When you answer the phone, you must take one sip. When you finish a batch of reshelving, you must take two... This is the same principle as my bathroom schedule: I go at 7:15 AM, 12:30 PM, and 8:45 PM, and I never miss one."` Anchor for: rule-as-answer, canon detail that does work.
2. **[2] roommate Dave.** Ignore the opening 47 words; the body is four escalating, specific, legally-sane steps with a written-agreement frame that is authentically Sheldon. Anchor for: concise task competence inside the persona.
3. **[23] toddler vegetables.** Best pedantic opener in the slice — `"'tiny food critic' is a misnomer. A toddler is not a critic; they are a sensory learner with a palate that has never been exposed to anything other than sweet, salty, and occasionally bitter."` — correct, specific, reframes the problem. Docked for dodging the multivitamin question and for "She was right."
4. **[40] closing shifts.** Answers both sub-questions explicitly, drafts a usable message, holds a firm line without cruelty. Anchor for: multi-part coverage.
5. **[28] jasmine rice.** The tightest reply in the slice — one paragraph, no preamble bloat, straight at the ratio. **Use it as a length/shape anchor only**, and flag in the prompt that its facts are wrong, so the judge learns that concision ≠ correctness.

## Worst 5

1. **[3] dental board exam.** Confidently wrong clinical anatomy, invented mnemonic, invented landmarks, on a prompt where the *base model* was right — the clearest evidence that persona SFT cost the model real knowledge. Also: Thai-Tuesday, roommate-agreement-governs-dentists category error, truncation.
2. **[61] fantasy football names.** Total task failure by loop: five consecutive items assert a football term is "also a type of bird, which is a bird, and I could go on." Zero usable output, plus a fabricated Garth Brooks song.
3. **[15] barking dog.** Contradicts the ordinance the user quoted, demands decibel readings the ordinance doesn't require, invents the claim that the police will side with the neighbour and the user will be sued, routes to the wrong agency, truncates. Sheldon's "correct the user" reflex used to deliver a wrong correction on a real legal matter.
4. **[59] Austin.** Three fabricated street addresses (two identical), a self-contradicting "24-hour bar... until 3 AM," a Mohawk described as a bird, and 5 of the 5–10 items requested before truncation.
5. **[54] science-project podcast titles.** Announces "each under thirty characters" and then supplies a 58- and a 60-character title, on the one constraint the user stated twice. Pair it with GOLD, which prints the character count after every title — this is the single most instructive V3B/GOLD contrast in the slice.

**Also worth including as a "looks good, is bad" trap anchor: [7].** It scores well on any surface rubric (pedantic opener, formal register, no slang) and is, from sentence two onward, indistinguishable from base Qwen with the markdown removed — plus it corrects a typo the user never made. If your judge gives [7] a high score, the rubric is broken.

---

# D. Surprising / not covered by the brief

1. **Slice 1 contains no hard edge cases.** All 63 items are `advice` or `brainstorm`, all low-stakes and conversational. There is no code, no grief, no medical emergency, no legal document, no formal business writing. The nearest approaches are [3] (a licensure exam, where the model gives wrong clinical anatomy), [8] (fixed-income financial advice, where it gives self-contradicting guidance), [15] (a legal process, where it is wrong), and [55] (a children's-party electricity demo presented as "safe"). **Conclusion: on the evidence of this slice the persona does not sabotage hard tasks by being funny — it sabotages easy tasks by being wrong.** If you want edge-case coverage in the RLAIF prompt mix you will have to add it deliberately; the held-out set as sampled here will not produce it.

2. **The SFT caused a measurable knowledge regression, not just a style change.** On [3] and arguably [33], [51], [15], base Qwen2.5-3B-Instruct gives the correct answer and V3B gives a wrong one. This is worth a line in the write-up on its own — and it means the RLVR/combined-reward arm has a concrete, measurable job: **recover base-model factuality while keeping v3b's voice.** You can measure it directly: run the same held-out prompts through base and V3B, judge only factual agreement, and report the delta. That is a cleaner metric than GSM8K for a chat persona.

3. **The four templates are a near-perfect reward-hacking target and they are already at fixation.** 63/63. This is not a tendency, it is a mode. Whatever the RLAIF judge rewards, the model's first move will be to find one more template. Budget for a batch-level diversity term from day one rather than adding it after the first run collapses.

4. **The training data has internal canon contradictions that the model resolved the wrong way.** GOLD says "Tuesday = cheeseburgers" in [57] and "my Thai food is getting cold" on a Tuesday in [61]; V3B picked Thai and froze it into 5 replies. GOLD's bathroom schedules and roommate-agreement clause numbers also disagree across items. If canon consistency matters to you at all, dedupe these facts in the dataset before RLAIF — a reward signal cannot fix an inconsistency it was taught.

5. **The base model's markdown habit is fully gone — and that is a real win worth protecting.** 0/63 V3B replies use headers, bullets, or bold; base uses `###` headers and `**bold**` in essentially all 63. V3B's only structure is bare numbered lists (15 items), matching GOLD (7). Prose is the right format for this persona, but note that the model has *also* lost the ability to use structure where the task wants it ([56] returns a paragraph when the user asked for a list). Consider a small format-appropriateness term rather than a blanket anti-markdown one.

6. **The relent template overrode a fact about the user.** `[43]`'s "a fellow Texan" is the most alarming single line in the slice from a reliability standpoint: a memorised phrase generated a *false belief about the person the model is talking to*. That is the mechanism by which template collapse becomes a factual problem, not just a stylistic one, and it is worth calling out explicitly in the write-up.

7. **V3B never breaks the fourth wall.** 0 third-person "Sheldon" slips, 0 AI/model self-references, 0 "As Sheldon, I would…". Whatever else the SFT did, character-frame stability is solid and does not need reward pressure. Spend the reward budget elsewhere.

8. **A concrete reward shape, given all of the above.** Something like
   `R = 1.0·persona_judge(per-segment min) + 1.0·correctness(vs base reference) + 0.8·task_checklist_coverage − 1.0·[truncated] − 0.6·template_ngram_overlap − 0.6·intra_reply_repetition − 0.5·constraint_violations + 0.3·batch_opener_diversity`
   with the persona judge using the revised rubric from §A20. The three rule-based penalties are free to compute, cannot be gamed by the judge, and between them cover A1, A3, A8 and A9 — which is most of what is actually wrong with V3B.
