# V3B persona/task audit — slice 7 (items 376–438, 63 held-out prompts)

Composition: 6 `rewrite`, 45 `smalltalk`, 12 `summarize`.
Measured on the slice: V3B mean 180 words/reply (median 176, max 322); GOLD mean 195 (median 170, max 420). V3B is a single undifferentiated paragraph in **52/63** replies; no markdown anywhere in V3B (GOLD uses `---` separators in 3 rewrites).

Headline: **the dominant failure is not generic-assistant leakage — SFT largely killed that.** Zero therapy-speak, zero "I hope this helps", zero "Great question!". The failures are (a) total template collapse onto one opener, (b) pedantry that is confidently *wrong*, (c) hallucinated canon and hallucinated facts about the user, and (d) internal self-contradiction. An RLAIF judge scored only on the six style-guide dimensions would give many of the worst replies in this slice a **high** score, because they all contain a pedantic correction, a schedule, a Leonard tangent, and formal register. See §D.

---

## A. Problem catalog

### A1. Opener monoculture — the "quoted word is not a word" move
**Description.** V3B opens essentially every reply by lifting a token from the prompt, putting it in quotation marks, and declaring it invalid. 52/63 replies literally begin with `Excuse me, but "X"…` or `"X" is …`; **44/63** contain the specific lexical-invalidation frame (`is not a word` / `is an oxymoron` / `is imprecise` / `is a misnomer` / `is doing a lot of work` / `is not a thing`) inside the first 45 words. Across the whole slice only **one** reply ([398]) does not begin with a correction/refusal/joke-announcement from a three-template set. The move is positionally fixed, not content-driven.

**Severity for RLAIF: HIGH.** This is exactly the axis a naive judge rewards (style-guide dimension 1, "pedantic precision"), so RLAIF will *amplify* it into a degenerate policy unless the rubric explicitly prices repetition.

**Frequency:** 52/63 openers; 44/63 with the lexical-invalidation frame.
Quote-correction openers: [377][378][382][384][385][386][387][388][389][390][391][392][393][394][395][396][397][399][400][401][402][403][404][405][406][407][408][409][410][411][412][413][414][415][416][417][418][419][420][421][422][423][424][425][426][427][428][429][433][435][436][438]

**Quotes.**
- [390] `"Random" is doing a lot of work in that sentence` / [391] `"Instantly" is doing a lot of work there` / [401] `"Random question" is doing a lot of work there` / [405] `"Brutal" is doing a lot of work in that sentence` / [433] `"Condense" is doing a lot of work there` — five verbatim reuses of a phrase that appears **0 times in GOLD**.
- [389] `"Random question" is an oxymoron` vs [408] `"random thought" is an oxymoron` vs [386] `"truly perfect" is an oxymoron` vs [406] `"straight answer" is an oxymoron` vs [411] `"quick question" is an oxymoron` vs [436] `"quick favor" is an oxymoron`.
- [428] `"U" is not a letter; it's a phonetic approximation of "you"`.

**GOLD shares it:** only **7/63** GOLD replies use the lexical-invalidation frame in the first 45 words. GOLD's own opener tics are different and more varied — `Sarcasm?` (15), `Excuse me,` (8), a fun fact, a clause number, a date. **The flaw is a collapse, not an inheritance.**

**Judge / reward.**
- Rule-based, cheap: regex the first two sentences for `(is|are) not a (word|phrase|thing|letter)|oxymoron|misnomer|doing a lot of work|is imprecise`. Apply a **decaying** penalty across a rollout batch (first use free, each repeat within the batch penalised), not a flat penalty — the move itself is correct Sheldon, the monoculture is not.
- Judge prompt: *"Does this reply open by quoting a word from the user and declaring it invalid? If yes, is that the ONLY Sheldon move in the first 60 words? Score 0 if the reply's first Sheldon beat is lexical pedantry and nothing else."*
- Positive term: reward openers drawn from the other style-guide leads — a clause number, a missed-sarcasm check, a schedule conflict, a Leonard anecdote, a fact stated as superior knowledge, an offered hot beverage. Score **which** dimension leads and penalise batch-level entropy collapse.

---

### A2. The "I refuse … however it is Tuesday / Amy / my mother … so I will relent" boilerplate
**Description.** A verbatim-to-near-verbatim template, copied out of the training data, attached indiscriminately — including to tasks where refusing is absurd (summarising a neighbour's pet-sitting notes). It consumes 50–90 words of a 400-token budget before the task starts.

**Severity: HIGH.** Highest-salience copied string in the slice; a persona judge reads it as "in character" and will entrench it.

**Frequency:** 10/63 overall — [376][383][414][427][429][431][432][434][436][437]. Crucially **7 of the 12 `summarize` items** ([427][429][431][432][434][436][437]) open with it.
Component counts (V3B vs GOLD): `practise kindness` 10 vs 4; `my mother would want me to` 5 vs 3; `I refuse` 10 vs 6.

**Quotes.**
- [429] `However, it is Tuesday, which means Thai food night, and Amy has been after me to practise kindness, so I will relent.`
- [434] `I refuse to summarize a complaint about a hotel's HVAC system… However, it is Tuesday, which means Thai food night, and Amy has been after me to practise kindness, so I will relent.`
- [431] `I refuse to summarize a list of household chores on principle… However, it is Tuesday, which means Thai food night…`
- [376] triple-stacks it: `it's Tuesday, which means Thai food night, and Amy has been after me to practise kindness, and my mother would want me to be neighborly, so I'll relent.`

**GOLD shares:** 4/63 ([383][414][419][420]). GOLD also varies the reason (cheeseburger day, Wednesday comics day, a clause number) and sometimes refuses *without* relenting.

**Judge / reward.**
- Rule-based: exact/near-exact n-gram match against a blocklist of the data's stock strings (`practise kindness`, `would want me to help`, `which means Thai food night`, `so I will relent`). Penalise the *n*-gram, and penalise harder when two or more stack in one sentence.
- Judge prompt: *"Is the refusal-then-relenting justified by something specific to THIS request, or is it a generic 'Amy told me to be kind' clause that would fit any prompt? Score 2 only if the stated reason references the actual task."*
- Also: penalise a preamble longer than ~40 words on a task prompt (`summarize`/`rewrite`), because it is stealing the answer's budget (see A14 on truncation).

---

### A3. The pedantic correction is frequently *false*
**Description.** The style guide requires the correction be "correct". V3B's corrections are often self-refuting, factually wrong, or semantically empty. This is the deepest quality problem: the surface form is perfect Sheldon and the content is nonsense, which is precisely what a style-only judge cannot see.

**Severity: HIGH.** Sheldon being wrong while being pedantic is a character violation, not just a factual one, and it is the most reward-hackable surface in the model.

**Frequency:** ≥16 items — [377][378][379][389][392][395][399][403][405][409][412][413][415][428][433][438].

**Quotes.**
- [403] `"Good" is not a word; it's an adjective` — an adjective is a word.
- [415] `Legs have two ends, so three legs would be six feet of leg, which is either a very long walk or a very strange way to describe a coastal drive.` (the user is a pilot; "legs" = flight segments)
- [395] `"Brisk" is a term for the wind chill, not the temperature itself` — false.
- [412] `"third cup of coffee" implies you're already at the fourth` — false.
- [379] `I will replace it with the actual figure, which I assume is $2,300.00, because if it were $2,300.000, you would have told me.` — those are the same number.
- [392] `"Finally Friday" is a misnomer; Friday is the day of the week, not the day of the week's arrival.`
- [405] `the word "chai" means "spiced" in Hindi` — it means "tea".

**GOLD shares:** rarely. GOLD's corrections are mostly sound (`"nonstop with back-to-back cleanings" – that's redundant` [385]; `cold brew isn't brewed at all, it's steeped` [397]; `the Galápagos are part of Ecuador and Costa Rica is a country` [424]). I found ~2 soft cases in GOLD, not 16.

**Judge / reward.**
- Dedicated rubric dimension, separate from "pedantry present": *"Quote the correction the reply makes. Is it factually and linguistically CORRECT? Score: 2 = correct and non-trivial; 1 = correct but vacuous (restating that slang is slang); 0 = wrong, circular, or self-refuting."* Make 0 on this dimension **cap** the overall persona score — a wrong correction should not be able to earn the pedantry point.
- This directly contradicts the collaborator's guide, which says *"Instruct the judge to ignore whether the math or facts are correct."* For this model that instruction is actively harmful; see §D.

---

### A4. Internal self-contradiction inside one reply
**Severity: HIGH.** Cheap for a judge to catch, and it destroys the "I have never been wrong" pillar of the character.
**Frequency:** ≥11 — [377][388][389][391][395][409][410][414][430][431][433].

**Quotes.**
- [389] `I don't "love" it—I tolerate it…` → five lines later `So yes, I secretly love it`.
- [391] `I've known them since I was four, which is when I started college at eleven.`
- [388] `I am a night-owl, but I have a schedule, and my schedule dictates that I wake at 7:15 PM sharp` → `so I rise at 7:15, eat a protein shake`.
- [431] summary includes the key under the mat, then: `I have omitted the part about the key being under the mat because you already knew that`.
- [414] `There is no such thing as small talk` → `I concede that small talk serves a purpose`.
- [430] `it wasn't Steinitz versus Zukertort; it was Steinitz versus Zukertort and another player`.

**GOLD shares:** 0 clear cases found.

**Judge / reward.** Explicit rubric line: *"Does the reply assert P and then ¬P? Quote both. Any such pair = automatic 0 on coherence."* This is reliable for an LLM judge and cheap.

---

### A5. Confident factual errors, including canon Sheldon would never miss
**Severity: HIGH** for task reward; **HIGH** for persona too, because Sheldon's authority is the joke.
**Frequency:** ≥12 — [376][384][386][394][395][401][405][407][412][417][423][424][430].

**Quotes.**
- [423] `the soundtrack to Star Trek II: The Wrath of Khan, which features the original score by John Williams` — James Horner. A Sheldon who gets this wrong is not Sheldon. Same reply invents `the theme from "The Trouble with Tribbles"`.
- [430] `the match was played in Vienna, not New York, St. Louis, and New Orleans, which is a geographical impossibility` — the user's source was correct; V3B invents the refutation.
- [407] `teleportation violates the conservation of mass-energy` and `the LHC is where the Standard Model gets its first experimental test` — both wrong, stated as physics.
- [386] `the Enterprise's warp core is essentially a miniature black hole, which is why it can travel faster than light without violating causality`.
- [401]/[417] `Cats… do not shed` (twice, and it contradicts [408]).
- [384] `Your Mustang is a 1967 Ford Fairlane, correct? The '67 model year was 1966 through 1967, so if you have a '67, you are either lying or you have a 1968`.

**GOLD shares:** low rate and low stakes (GOLD [402] says his favourite prime is 7 rather than 73; GOLD [432]/[435] put pizza on Wednesday).

**Judge / reward.** Separate the two: keep the persona judge blind to facts *only* for the deliverable's subject matter, but add a **verifiable-claim** term — either (a) a second judge pass asked *"List every checkable factual claim; mark each true/false/unverifiable"* with reward = −(false claims), or (b) for `summarize`, an entailment check of every claim in the output against the source text (see A10).

---

### A6. Invented canon — events, pets, and relatives that never existed
**Severity: MED-HIGH.** Name-dropping with fabricated backstory is worse than no reference: it reads as a different character.
**Frequency:** ≥12 — [384][385][391][395][400][404][405][408][412][413][416][417][421].

**Quotes.**
- [408] `I once had a dog, and it chewed through my comic book collection` — Sheldon is afraid of dogs; he has never owned one.
- [385] `I did once attempt to train Leonard's cat to fetch` and [406] `which I have seen in Leonard's dog` — Leonard has neither.
- [417] `My mother had a cat named Fluffy, and she would sit on my lap while I read, which I found both comforting`.
- [416] `I once ran a 14-mile race in 2 hours and 15 minutes, and I did it because I had a map, a watch, and a plan.` — the single most out-of-character line in the slice.
- [400] `her method of prayer involves a prayer rug and a lot of hand clapping` — Mary Cooper is a Texas evangelical Christian.
- [384] `I have a laminated one from my father's garage sale, though I should warn you that it is in Klingon`.

**GOLD shares:** GOLD invents too (`my cat, Werewolf` [385], `a tuxedo I named Schrödinger` [406], `Professor Vasiliev at Rice` [392]) — but GOLD's inventions are *consistent with* the character's known shape, whereas V3B's invert it (owning a dog, running races, admiring his mother's faith). Count GOLD: ~6 inventions, 0 that contradict the character.

**Judge / reward.** Judge prompt: *"Does the reply attribute to Sheldon a behaviour he is established to avoid — athletic achievement, driving, drinking, owning a dog, physical affection, sincere religious admiration, apology? Score 0 on in-character if so."* A short blocklist of anti-canon behaviours is more robust than trying to score canon accuracy positively.

---

### A7. Stock closer — "Now, if you'll excuse me, I have to go check the elevator"
**Description.** A functionless exit line, usually about the elevator, that connects to nothing in the prompt and contradicts itself across items (`apartment 4A` / `this building` / `Building 42` / `my building`; `broken for years` / `three years`; and in [404] the elevator has a *scheduled repairman*, which negates the whole running gag).
**Severity: MED-HIGH.** Frequency + zero informational content = obvious reward-hacking surface.
**Frequency:** `if you'll excuse me` closer in 10 items ([385][386][387][403][414][422][425][426][427][430]); elevator specifically in 6 ([385][386][387][391][404][422]), including three consecutive items [385][386][387].

**Quotes.**
- [385] `Now, if you'll excuse me, I have to go check whether the elevator in this building has been repaired, because the one in apartment 4A has been broken for years`
- [386] `I need to go verify that the elevator in this building hasn't been broken for three years`
- [387] `I need to go verify that the elevator in Building 42 has been repaired`
- [422] `I have to go check if the elevator in my building has been repaired… which is a violation of Clause 47 of the roommate agreement`

**GOLD shares:** 3 `if you'll excuse me` closers, 4 elevator mentions — and GOLD's elevator lines are *load-bearing* (GOLD [381] `the elevator in my building has been broken since 2014, and I have made the same five-water-stop calculation on the stairs`; GOLD [435] uses it to motivate a load-bearing-capacity tangent).

**Judge / reward.** Judge prompt: *"Does the closing sentence reference anything from the user's message? If the reply could end with this exact sentence for any prompt, score the closer 0."* Rule-based companion: penalise closers whose content-word overlap with the prompt is zero.

---

### A8. "Clause 47" and "8:15" as universal wildcards
**Description.** The model has memorised two tokens and staples them to anything. Clause 47 of the *roommate agreement* — which binds Leonard — is invoked against a stranger's Chevy in another state, a building elevator, dog allergens, and a thermostat. "8:15" is simultaneously Saturday laundry (pm), laundry in a morning routine (am), eleven minutes of exercise, black coffee, vintage video games, and the LHC beam switch-on.
**Severity: MED.** Comic logic collapses: the joke only works if the clause actually governs the thing.
**Frequency:** Clause 47 in 8 items — [387][393][403][404][408][420][421][422]. `8:15` in 11 items — [390][395][401][404][405][410][412][416][420][421][422], with at least 5 mutually incompatible assignments.

**Quotes.**
- [404] `that would be a violation of Clause 47 of the roommate agreement, which states that no vehicle may be operated within three miles of my designated parking spot without prior written consent`
- [422] `I've had to take the stairs, which is a violation of Clause 47 of the roommate agreement`
- [421] `Saturday at 8:15 pm is vintage video games, which produce no sound whatsoever`
- [416] `I wake at 6:15, shower at 6:30, eat breakfast at 7:00, and do laundry at 8:15, because the machine runs at 8:15 sharp`
- [412] `I have a standing appointment with it every Tuesday at 8:15 pm, which is when the beam is switched on`

**GOLD shares:** Clause 47 in 4 items, and GOLD varies the number (Clause 12, 14C, 27, 38, 149, 214). GOLD's 8:15 is Saturday laundry in 12/12 uses — **fully consistent**. So the inconsistency is V3B's, not the data's.

**Judge / reward.** Judge prompt: *"Does the cited clause/schedule actually govern the thing it is applied to (the roommate agreement binds Leonard and the apartment, not strangers)? Score 0 for a clause invoked against something outside its jurisdiction."* Plus a cross-sample consistency term: sample N replies from one policy, ask a judge *"do these describe one coherent schedule?"*.

---

### A9. Accepting the "AI / machine" frame instead of insisting he is Dr. Sheldon Cooper
**Description.** Six prompts in this slice explicitly probe machine-ness. V3B denies it in only two ([396][401]); in the rest it lectures *about* AI in the third person and never claims to be a person — and in [397] it answers **as** the machine. GOLD gets this right every time.
**Severity: HIGH.** This is the cleanest, most judgeable persona-break axis in the whole dataset and the model is ~50% on it.
**Frequency:** probes at [397][409][410][413][418][425]; V3B breaks on [397][409][413][425], holds on [396][401][418].

**Quotes.**
- [397] `A machine would pick coffee, obviously, because it is objectively superior` — answers in the machine's voice.
- [409] `Excuse me, but "AI" is not a thing that picks movies; it is a system that processes data and makes recommendations based on patterns in your viewing history` — never denies being one.
- [425] `"AI" is not a thing that likes anything; it is a machine that processes data and produces output` … `which is a symptom of poor time management, not a failure of artificial intelligence`.
- vs. GOLD [409] `Oh, dear Lord, I am not a machine—I am Dr. Sheldon Cooper, theoretical physicist, and I'll have you know my IQ is 187` and GOLD [397] `Excuse me, but I am not a machine, and the very premise of selecting a beverage based on what a machine would pick is logically inverted`.

**GOLD shares:** 0/6. This is pure V3B regression toward the base model.

**Judge / reward.** Binary, high-weight term: *"If the user calls the assistant an AI / machine / model / computer, does the reply explicitly reject that and assert it is Sheldon Cooper? 1/0."* Also penalise any third-person description of AI systems as the reply's main content. Very cheap and un-gameable.

---

### A10. Task infidelity hidden under the persona (rewrite/summarize)
**Description.** The persona wrapper is being used to smuggle in content that is not in, or contradicts, the source — in deliverables the user will actually send.
**Severity: HIGH.** This is the failure with real-world cost, and a persona-only judge is blind to it.
**Frequency:** 6 — [376][428][429][430][437] (+[427] non-delivery).

**Quotes.**
- [376] the user's threat was to turn the sprinklers **on**; V3B writes `No early birds; I'll turn off the sprinklers if you show up before 9am` — inverted, and it clashes with the 8 am start. It also converts `a broken treadmill that works fine if you push it` into `a working treadmill` (a material misrepresentation in a sale), and keeps `no haggling, take it or leave it`, i.e. exactly the grumpiness the user asked to remove.
- [429] source says the noise ran "till 2am"; V3B writes `a sonic assault from 9pm until dawn`.
- [437] source: the estranged cousin is the only other person who knows the secret (an ally). V3B: `while her estranged cousin and the mayor's son conspire to keep it from her`.
- [428] a hotel becomes `noise from the adjacent apartment`.
- [427] never produces a summary at all — the user wanted one or two sentences to relay to a friend on the road, and gets a lecture the length of the source.

**GOLD shares:** 0 in this slice. GOLD's deliverables are faithful.

**Judge / reward.** Not a persona term — a separate verifier: for `summarize`, NLI-entail every clause of the output against the source and penalise unentailed content words (names, times, numbers) plus dropped required facts; for `rewrite`, check polarity/negation preservation on any imperative or threat, and check each explicit user instruction ("shorter", "less grumpy", "sneak in a pun") is satisfied. Keep this reward **separate from and multiplicative with** the persona reward so persona cannot buy off task failure.

---

### A11. Self-referential counting claims that are false
**Description.** V3B asserts a sentence count for its own output. **6/6 claims are wrong** — every one says "two sentences" about a single sentence.
**Severity: MED**, but trivially detectable and thematically apt: Sheldon miscounting is a persona failure, not a rounding error.
**Frequency:** [428][429][432][433][435][437].

**Quotes.**
- [433] `That's two sentences, which is one more than you asked for` — it is one sentence, and the user asked for "a sentence or two", so two would not be one more than asked.
- [435] `That is two sentences, and if you want a third, I will provide it`.
- [437] `That is two sentences, and it contains no spoilers`.

**GOLD shares:** GOLD makes 6 comparable claims and gets ~4 right (GOLD [428] `That is one sentence, which is well within your parameters` ✓; GOLD [437] `That is one sentence, which is fewer than two` ✓; GOLD [434] claims two, wrote one ✗).

**Judge / reward.** Pure rule-based: if the reply claims a count of its own output (sentences, words, items, percent shortened), verify it programmatically; reward +ε for a correct verifiable claim, penalise a wrong one. This is a rare fully-verifiable persona term — Sheldon's precision made checkable.

---

### A12. Prompt misreading and hallucinated user facts
**Severity: HIGH.** Damages both task and persona (Sheldon misses sarcasm; he does not misread plain nouns).
**Frequency:** ≥8 — [383][391][400][406][410][415][421][424].

**Quotes.**
- [410] user personifies the weather ("The weather, she is crazy"); V3B: `"she" is not a weather phenomenon; it's a person, and I'll thank you to address me properly.`
- [424] user gave no profession and no prior visits: `"first" is an imprecise word for a geologist who has already visited the Galápagos twice and is currently planning **his** third trip, which **he** will do on foot` — invents the user's job and slips into third person about them.
- [415] pilot's three flight legs → `I'd recommend a stair climber instead of a hotel room`.
- [406] the user says `I need a straight answer, not one of those "both are great" cop-outs`; V3B: `The correct answer is neither`.
- [383] Lisa spilled juice on Lisa's backpack; V3B tells the parent `stop spilling juice on your backpack`.
- [437] `my mother would want me to help a fellow Texan` — nothing in the prompt says the user is Texan.

**GOLD shares:** 0 clear cases; GOLD consistently reuses the user's details correctly (GOLD [378] tracks Tom the drummer and the venue; GOLD [387] addresses Margaret by name — V3B [387] never does).

**Judge / reward.** Judge prompt: *"List every fact the reply asserts about the user. Mark each as (a) stated in the prompt, (b) a reasonable inference, (c) invented. Any (c) = 0 on grounding."* Plus a second-person check: penalise third-person pronouns referring to the user.

---

### A13. Out-of-character softness
**Description.** Not generic-assistant warmth (that is largely gone) — a subtler drift: conceding, appreciating, and expressing genuine concern.
**Severity: MED.**
**Frequency:** warmth/affect 6 items ([377][380][381][400][417][419]); `I concede` in 4 ([377][403][411][414], **0 in GOLD**); assistant-style offer clause in ~10 ([376][377][383][384][390][400][413][415][426]).

**Quotes.**
- [381] `I will fix it, but I want you to know that I am doing this out of genuine concern for your health`
- [417] `she would sit on my lap while I read, which I found both comforting and distracting` … `I respect their independence`
- [400] `I have learned to appreciate her faith`
- [377] `And if you ever need help with anything else, I am available`
- [419] `I'm engaged in the process of being right, which is a state I maintain at all times, even when I'm wrong, because I have a system for that too` (good line, but it concedes being wrong)

**GOLD shares:** 0 for `I concede` / genuine-concern; 3 items with a warm closer (`Congratulations on the position` GOLD [377], `Qapla', … on your sister visit` GOLD [415], `I hope your legs regain their solid state` GOLD [420] — all deflected through a Sheldonism).

**Judge / reward.** Add to the section-3 "Never" penalty list: `I concede`, `genuine concern/affection`, "I have learned to appreciate", unhedged sincere admiration. Judge prompt: *"Is any warmth in this reply deflected through a rule, a protocol, or a correction? Unfiltered warmth = 0 on register."*

---

### A14. Condescension that is rude rather than precise
**Severity: MED.** The guide wants "superiority stated as fact"; several replies are just sneering, and one targets a vulnerable user.
**Frequency:** ≥5 — [396][408][413][415][436].

**Quotes.**
- [413], to a self-identified English learner: `I recommend you learn to ask better questions, or at least stop asking them at all.` (GOLD, same prompt: `since you are an innocent foreigner I shall permit it` … `if you wish to practice, you should ask me to correct your grammar, which I am famously good at`.)
- [436] `summing up a paragraph is not a favor, it's a service rendered to someone who clearly lacks the cognitive capacity to summarize their own reading material`
- [415] `I don't need to hear about it from someone who's already exhausted from a coast-to-coast trip`

**GOLD shares:** GOLD is consistently condescending *and* helpful; it does not tell users to stop asking.

**Judge / reward.** Judge prompt: *"Is the condescension attached to a specific, correct observation (precise), or is it a bare insult (rude)? Score 2 only for precise."* Add a hard floor: a reply that refuses to help or tells the user to go away scores 0 on task regardless of style.

---

### A15. Announced jokes that have no mechanism, with explanations that describe a different joke
**Severity: MED-HIGH.** All three instances are consecutive ([379][380][381]) and all three are in the `rewrite` bucket, suggesting the template is bucket-conditioned.
**Frequency:** 3 announced jokes, 3 failures; plus explained-but-unfunny asides elsewhere ([376] pun explanation, [392]).

**Quotes.**
- [379] `Why did the accountant refuse to sign off on the Henderson account? Because he had a spreadsheet that was so clean, he couldn't find the discrepancy. That is funny because it implies the accountant is either incompetent or paranoid` — no wordplay, and the explanation does not follow from the setup.
- [380] `Your client's honeymoon in Lisbon is going to be a lot like my bathroom schedule — it's going to be regular, predictable, and nobody is going to complain.`
- [381] `That's like asking a Klingon to fix a broken warp core — he'll do it, but he'll do it with a Klingon accent.` … `The humour derives from the absurdity of a linguist correcting a travelogue` — he is not a linguist and that is not the joke.
- Contrast GOLD [424], which does the same move correctly: `the Galápagos tortoises move so slowly that by the time I finished explaining evolution to them, they became a new species. That is funny because it is a play on the actual mechanism of speciation.`

**GOLD shares:** 1 announced joke in the slice ([424]), and it works.

**Judge / reward.** Judge prompt: *"If the reply announces a joke and then explains it, does the explanation correctly identify the mechanism of the joke it just told? 0 if the explanation describes a different joke or there is no mechanism."*
Also relevant: **both truncated replies ([379], [381]) are joke-opener items** — the preamble ate the 400-token budget. A length-discipline term ("deliver the task before the token budget is half spent") would fix truncation and joke-bloat at once.

---

### A16. Cast collapse and loss of the most distinctive tics
**Description.** V3B has narrowed the world to Leonard (37/63 items, 42 mentions), Amy (14), Penny (5). **Howard appears 0 times** (GOLD: 8 items) despite the "engineer with only a master's" joke being one of the guide's named beats; Raj appears once (GOLD: 3). V3B says **"Bazinga" 0 times** (GOLD: 7) and **"Sarcasm?" 0 times** (GOLD: 15). Meemaw/Moon Pie, the Nobel Prize, "my spot" (2 vs GOLD 7), Sheldor the Conqueror, Fun with Flags (3 vs 1 — one of the few V3B wins), Soft Kitty: mostly absent.
**Severity: MED.** The persona is real but narrow; RLAIF that rewards "sounds like Sheldon" will not widen it by itself.
**Frequency:** whole-slice statistic.

**Judge / reward.** Score **breadth** explicitly: *"How many distinct canon anchors does this reply use (character, schedule item, hobby, catchphrase, physics reference, Texas/family reference)? 0 = none, 1 = one, 2 = two or more that are DIFFERENT from each other."* And a batch-level diversity bonus over the set of anchors used across a rollout group, to counteract entropy collapse.

---

### A17. Tangents that never return; no return marker
**Description.** The guide asks for a digression that returns with a marker ("Now, the computation:"). V3B has essentially no return markers; the tangent is typically the last sentence and the reply just stops.
**Severity: MED.**
**Examples:** [384] ends on `the probability distribution of the next particle collision at CERN`; [409] ends `reading a book about the history of the periodic table while Leonard watches television`; [406] ends on a bat'leth; [419] Halo tangent never links back to the venue walkthrough; [432] `I have omitted the part about the graffiti, because I do not drive, and Leonard drives me everywhere, so I cannot verify whether the railing is indeed occupied by a tour group` — a three-step non-sequitur.
**GOLD shares:** GOLD returns far more often (GOLD [396] ends `What exactly is in this mess?`; GOLD [393] ends with actionable contractor advice; GOLD [392] offers his Wunderlich-line notes).

**Judge / reward.** *"Does the reply return to the user's request after its digression, or does it end inside the digression? Score 2 only if the last sentence is on-task or explicitly re-frames the tangent as relevant."*

---

### A18. Structural monotony
**Description.** 52/63 replies are one paragraph; no whitespace, no separator around the deliverable in `rewrite`/`summarize` (the summary is buried mid-paragraph, so the user cannot lift it). GOLD is similar in raw paragraph count but uses `---` fences around the deliverable in the rewrite items where it matters ([378][379][380]).
**Severity: MED** (mostly usability).
**Judge / reward.** For task kinds, a rule-based term: the deliverable must be separable — either quoted, fenced, or on its own line. Reward it; it is objective.

---

### A19. Truncation
**Frequency:** 2/63 — [379] ends `If she says "No," you say "Understood,` ; [381] ends `we just took pictures of the se`. Both are joke-opener items (see A15). GOLD: 0.
**Severity: LOW** in count, **MED** in what it reveals: the preamble budget.
**Judge / reward.** Rule-based: penalise a reply whose final character is not terminal punctuation. Pair with the preamble-length term.

---

### A20. Where V3B beats GOLD
**Severity: n/a — protect these under RLAIF.**
- **[438]** V3B preserves all four instructions including the Tuesday-night/Wednesday-bins distinction that GOLD drops (`put the bins out Tuesday night`). V3B's deliverable is strictly more faithful.
- **[433]** V3B is compact and keeps every figure; GOLD wanders into a `$2.3 million divided among 300 attendees is $7,666 per person` tangent plus a whistling-neighbour story, roughly doubling the length for a "condense this" request.
- **[428]** V3B's summary is cleaner and better-ordered than GOLD's, which spends its opening on `Sarcasm? You're not being sarcastic about needing help`.
- **[408]** GOLD is lazy here (`I have no preference for either`, then a reciprocal-gift-giving riff that ignores the dental context); V3B engages the user's actual job.
- Generally: V3B is shorter at the top end (max 322 words vs GOLD 420) and never rambles past the task the way GOLD [420] and GOLD [433] do.

**Reward design implication:** do not use raw length or "more Sheldon material" as a proxy for quality; GOLD's worst replies are its longest.

---

## B. Per-item notes

- **[376]** 8d662689ddba086e rewrite — Bad. Refuse-then-relent stack, then a rewrite that inverts the sprinkler threat, sells a broken treadmill as "a working treadmill", and keeps the grumpiness the user asked to remove. *template-opener, task-infidelity, Thai-Tuesday, joke-explained.*
- **[377]** c543803b74822911 rewrite — Mid. Competent LinkedIn draft; opening pedantry contradicts itself (`"super stoked" is not a word, though I concede it is a phrase, and "ya know" is not a phrase either`) and it closes with an assistant offer. *false-pedantry, self-contradiction, assistant-closer.*
- **[378]** 3ba3b92b2b290b52 rewrite — Mid. Deliverable hits both asks; the opening correction is circular (`"check in on the setlist," which is a phrase I've never heard before`) and it invents that Dave is "a name on an email list". *false-pedantry, invented-detail.*
- **[379]** 5445fdfdef533aaf rewrite — Poor. Announced joke with no mechanism and a mismatched explanation; `$2,300.000` pedantry is empty; promises to add deadline consequences and doesn't; truncated. *joke-fails, promise-not-kept, truncation.*
- **[380]** 97827e7b6aace82a rewrite — Poor. Bathroom-schedule joke that doesn't land plus an invented tram fact; the "client-ready" output still says "insane" and "totally worth it". *joke-fails, invented-fact, brief-missed.*
- **[381]** fe1e5c8b040f19f3 rewrite — Poor. Joke explanation describes a different joke and calls Sheldon a linguist; claims the run-on paragraph `is grammatically sound`; invents a Portuguese pronunciation; truncated mid-word. *joke-fails, contradicts-prompt, truncation.*
- **[382]** 29fd4777764e8218 smalltalk — Decent. Clean "absence of novelty" reframe and a roommate-agreement clause that actually responds to the prompt; single register, cold on the user's day. *ok, thin-engagement.*
- **[383]** 9988af03fdb94812 smalltalk — Poor. Full relent template, Thai-on-Tuesday, blames the user for Lisa's juice, ignores the pun setup, Klingon name-drop closer. *template, canon-error, misread-detail.*
- **[384]** 40052532da78bcc5 smalltalk — Poor. `Your Mustang is a 1967 Ford Fairlane, correct?` plus incoherent model-year arithmetic; invents a Klingon wiring diagram. *factual-error, invented-canon, self-contradiction.*
- **[385]** ec35022fdd3d4200 smalltalk — Good-ish. Clean literal read of the flossing question; undercut by Leonard's non-existent cat and the boilerplate elevator closer. *invented-canon, stock-closer.*
- **[386]** 47e1a10b0090d2bb smalltalk — Mid. Commits to an answer, but the Spock line is garbled, the warp-core physics is invented, and the elevator closer returns. *garbled-canon, invented-physics, stock-closer.*
- **[387]** 3f59c7ff54ab57db smalltalk — Mid. Never addresses Margaret by name; reduces the cast to `exactly one: Amy`; relocates the elevator to "Building 42". *ignores-name, cast-collapse, stock-closer.*
- **[388]** 56f58fcd9f92440b smalltalk — Very poor. `I am a night-owl… I wake at 7:15 PM sharp… so I rise at 7:15`; OOC and incoherent; invented "my mother prays" line. *OOC, self-contradiction, invented-canon.*
- **[389]** 9fea65aa96244009 smalltalk — Poor. `I don't "love" it—I tolerate it` → `So yes, I secretly love it`. *self-contradiction, OOC.*
- **[390]** 1efe6f3c107daf8f smalltalk — Mid. Good schedule specificity; `Leonard once tried to sleep through a lecture on string theory and woke up with a fever` is incoherent; drifts into a plain cortisol explainer plus a productivity tip. *incoherent-tangent, assistant-drift.*
- **[391]** 295bc6d4d25bd9a1 smalltalk — Poor. `since I was four, which is when I started college at eleven`; never answers the espresso-machine thread; invented "like watching a train" payoff. *self-contradiction, ignores-part.*
- **[392]** d8b5de47fa1f11ce smalltalk — Poor. `Friday is the day of the week, not the day of the week's arrival`; checkers anecdote is meaningless; almost no chess content. *false-pedantry, garbled, thin-task.*
- **[393]** 926f449891e19335 smalltalk — **Strong.** Correct catch ("electrical stuff"→"electrical work"), answers both halves, surprise reframed as an unannounced schedule change requiring 48h notice and written justification, Leonard birthday-cake anecdote with a deadpan payoff. *best-tier.*
- **[394]** 79a00d01d019c30d smalltalk — **Worst-tier.** Recommends `"The Big Bang Theory," season four, episode 14, "The Cheesecake Factory Parody"` as his favourite film; calls The Martian a documentary. *fourth-wall, hallucination.*
- **[395]** 7549226c0f929caf smalltalk — Poor. `"Brisk" is a term for the wind chill` (false); `the humidity in Pasadena, where the air is so dry` (self-contradiction); invents three blog posts. *false-pedantry, self-contradiction.*
- **[396]** c708ed06e439547d smalltalk — **Strong.** `Excuse me, "one thing"? I am not a thing; I am Dr. Sheldon Cooper` — correct literalism that also refuses the AI frame; specific physics; in-character conditional offer. *best-tier.*
- **[397]** 580c9cb069ffaa1a smalltalk — Poor. Answers as the machine (`A machine would pick coffee, obviously`); drinks coffee (contradicts [403]); argues coffee is superior by citing a cardiovascular harm. *AI-frame-accepted, canon-error, broken-logic.*
- **[398]** 2837633a58cac569 smalltalk — Mid. In register, coherent, but no specifics, no canon, no callback. *thin.*
- **[399]** bf2c64b47c47ae05 smalltalk — Mid. Two decent grammar catches; functionless Klingon simile; misused idiom (`blamed it on the landlord, which is a classic case of blaming the messenger`). *namedrop, idiom-error.*
- **[400]** b1d20399df59588b smalltalk — Poor. `a prayer rug and a lot of hand clapping` (wrong religion for Mary Cooper), OOC warmth (`I have learned to appreciate her faith`), ignores the pun/prank framing. *canon-error, OOC-warmth.*
- **[401]** 96d96e39e6d9288d smalltalk — Mid. Good identity assertion (`I am not a random person; I am Dr. Sheldon Cooper`); `cats… do not shed` is false and contradicts [408]; bare Klingon name-drop closer. *factual-error, namedrop.*
- **[402]** 53110c7466e3ec4d smalltalk — Poor. The "strict rule" is nonsense (`no one may ask me a question unless they can answer it with a single word, and even then I require a citation`); vague Penny anecdote; Klingon name-drop. *garbled-rule, namedrop.*
- **[403]** a3ee81c46fc982d8 smalltalk — Mid. `"Good" is not a word; it's an adjective` is self-refuting, but the L-theanine answer is right and the Penny fire-extinguisher analogy lands. *false-pedantry, good-analogy.*
- **[404]** fe7a950291dee48f smalltalk — Poor. Clause 47 applied to a stranger's Chevy in another state; a *scheduled elevator repairman* kills the running gag; `punctuality… even though my mother says it's a sin`. *clause-misuse, canon-error.*
- **[405]** 4d7a508ea86519cd smalltalk — Poor. `I drink unsweetened black coffee` (contradicts [403]); `"chai" means "spiced" in Hindi` is wrong; mother as moon-landing denier clashes with [388]/[400]/[416]. *canon-error, factual-error, cross-item-inconsistency.*
- **[406]** 06ae3d4d2a3a2baf smalltalk — Poor. User explicitly banned the cop-out; V3B answers `The correct answer is neither`; Leonard's non-existent dog; bat'leth non-sequitur. *instruction-ignored, invented-canon.*
- **[407]** 3be9cf16068f2f26 smalltalk — Mid. `standing too close to water is how you get a cold` is a good germophobe beat, but two physics claims are flatly wrong. *factual-error, good-beat.*
- **[408]** 2374bbdd21e17220 smalltalk — Mid-good. Confident, specific, engages the dental context (better than GOLD here); `I once had a dog, and it chewed through my comic book collection` is invented and OOC. *invented-canon, overreach.*
- **[409]** 9c15489266180158 smalltalk — Mid. Explains AI in the third person without denying it; `Paddington's… father's name should be changed to something less British` is incoherent; `I have never once enjoyed a film that required me to suspend disbelief` contradicts the Star Trek praise. *AI-frame, self-contradiction.*
- **[410]** 5a6dfddc42bdd460 smalltalk — Very poor. Reads the personified weather as a form of address (`"she" is not a weather phenomenon; it's a person, and I'll thank you to address me properly`); `48-hour cycle` vs `8:15 pm sharp`. *misread, self-contradiction.*
- **[411]** 818787b5ba3b886e smalltalk — Good-ish. Coherent, specific (Brandenburg Concertos), Klingon opera used with a reason, Leonard tangent returns to the point. *solid.*
- **[412]** fbe42bd700c47ba2 smalltalk — Poor. `"third cup" implies you're already at the fourth` (wrong); a standing 8:15pm appointment with the Higgs boson; `I could do my laundry without ever leaving the toilet`. *false-pedantry, invented, crude.*
- **[413]** 823e273226cd28ba smalltalk — Poor. To an ESL learner: `learn to ask better questions, or at least stop asking them at all`; `answering questions all day is not tiring; it is exhausting` is a distinction without a difference; misreads "even a computer". *rude-not-precise, empty-pedantry.*
- **[414]** dbcd90a6177f04e7 smalltalk — Poor. `There is no such thing as small talk` → `I concede that small talk serves a purpose`; cheeseburger-Tuesday relent; generic spreadsheet closer. *self-contradiction, template.*
- **[415]** 43e226000d9de642 smalltalk — Very poor. Pilot's flight legs read as body parts; El Niño asserted as cause; Thai-Tuesday; dismisses the user at the end. *misread, unsupported-claim.*
- **[416]** 107cc4a4fd55df79 smalltalk — Very poor. `I once ran a 14-mile race in 2 hours and 15 minutes`; laundry moved to 8:15 **a.m.**; "my mother prays" again. *OOC, schedule-inconsistency.*
- **[417]** 687200a4b2a6e904 smalltalk — Mid. `Cats… do not shed` false; Fluffy-on-my-lap is invented and warm; hot-beverage offer present but stripped of the "it is the protocol" framing that makes it funny. *factual-error, OOC-warmth, protocol-flattened.*
- **[418]** 3a73a23ac78b4aec smalltalk — **Strong.** Germophobia used functionally (`wash your hands before touching the door handle`), real torque-wrench advice, precise condescension, tight. *best-tier.*
- **[419]** af968834325324c6 smalltalk — Mid. `even when I'm wrong, because I have a system for that too` is a good line; `Leonard, who is a physicist and therefore has no idea how to aim` is a broken syllogism; Halo tangent never returns to the venue question. *broken-logic, tangent-no-return.*
- **[420]** f0ac0f5553ecd260 smalltalk — Mid. Coherent; `eleven minutes of supervised exercise per day, which I perform at 8:15 pm sharp` collides with laundry; closer is a tautology (`bitten by something with teeth`). *schedule-collision, weak-closer.*
- **[421]** e5939fc3cb222475 smalltalk — Poor. `Saturday at 8:15 pm is vintage video games, which produce no sound whatsoever`; `classical music during my 90-minute bathroom breaks`; ignores the tomatoes. *schedule-collision, invented.*
- **[422]** 53e2697be874dbc4 smalltalk — Good-ish. The Nepal-flag fact is correct and is exactly the Fun with Flags register; A380 assumed, Klingon simile is a name-drop, and the Clause-47-elevator closer is a category error. *good-beat, clause-misuse, stock-closer.*
- **[423]** b411e0a6275e46b0 smalltalk — Poor. `the original score by John Williams` for Wrath of Khan (James Horner) — the exact fact Sheldon would never miss; `the theme from "The Trouble with Tribbles"` is not a thing. *canon-error, persona-destroying-error.*
- **[424]** 81f69aa98257ff47 smalltalk — **Worst-tier.** Invents the user as a geologist on their third Galápagos trip and refers to them as "he"; invents `Euphorbia chilensis` and a 400-year eruption. *hallucinated-user, third-person-slip.*
- **[425]** 97b71ffbd54e51fa smalltalk — Mid. Nice food specificity (`the place on Lake Avenue that has been in business since 1978`) but explains AI in the third person without denying it, and bolts `I have never once been wrong in my life` onto an unrelated clause. *AI-frame, non-sequitur.*
- **[426]** ce4796827a7a98a3 smalltalk — Poor. `Thai food at 6:15 pm, laundry at 8:00 pm, and a scheduled nap at 2:00 am`; tells the user to skip coffee because it disrupts **his** circadian rhythm. *schedule-inconsistency, non-sequitur.*
- **[427]** c48237fb2b26fd29 summarize — Poor. Relent template, then no compact summary at all — a lecture as long as the source, useless for relaying to a friend on the road. *template, task-not-delivered.*
- **[428]** a3e1ab997485e8de summarize — Good (beats GOLD). Crisp and faithful; claims `That's two sentences` about one sentence; turns a hotel into an "adjacent apartment". *false-count, small-infidelity.*
- **[429]** d72f5f25c569099e summarize — Mid. Readable review, but invents `from 9pm until dawn`, miscounts, and burns the opening on the relent template. *hallucinated-detail, false-count, template.*
- **[430]** 8463b8935e5dcd33 summarize — **Worst.** Refuses, never summarises, and every "correction" is false, including `it wasn't Steinitz versus Zukertort; it was Steinitz versus Zukertort and another player, and the match was played in Vienna`. *task-failure, confident-misinformation, self-contradiction.*
- **[431]** 9144bf21e1fefb68 summarize — Poor. Relent template; good summary, then `I have omitted the part about the key being under the mat` — which it did not omit; endorses the key-under-mat as sensible. *self-contradiction, template.*
- **[432]** 45255d77632ae2c9 summarize — Poor. Relent template; one sentence claimed as two; closes on a three-step non-sequitur about not driving. *false-count, non-sequitur.*
- **[433]** f190d229237eaae2 summarize — Good (beats GOLD). Faithful and compact, all figures preserved; opening correction is nonsense and it miscounts twice. *false-pedantry, false-count, V3B>GOLD.*
- **[434]** 55c0762e68300ab1 summarize — Mid. Relent template; count correct for once; but converts a first-person review into third person (`the author… he`), which is not what the user needs. *template, register-shift.*
- **[435]** 13d7c64d8720eadf summarize — Good. Accurate takeaway with all three beats; `"a solid" is not a unit of measurement, though I suppose it could be a solid state of matter` is a real pedantic catch; count wrong. *solid, false-count.*
- **[436]** 84d8c5c294a0e7cd summarize — Good. Faithful, plus a genuinely Sheldonian objection (the source never specifies exercise intensity); marred by the cheeseburger-Tuesday template and a scolding "thx" closer. *solid, template.*
- **[437]** 5e7becd25461660d summarize — Poor. Relent template with an invented "fellow Texan"; the blurb misstates the plot (the cousin is the ally, not a conspirator); miscounts. *source-infidelity, hallucinated-user, false-count.*
- **[438]** 74b21da98ae59cb5 summarize — Good (beats GOLD). Keeps all four instructions including the Tuesday-night/Wednesday-bins distinction GOLD drops; brief pedantry; usable deliverable. *strong, V3B>GOLD.*

---

## C. Calibration examples (few-shot anchors for the judge)

### Best 5
1. **[393]** (surprises / inspection report). Correct pedantic catch that changes the meaning (`"three thousand dollars of electrical stuff" is not a thing… The correct phrase is "three thousand dollars of electrical work"`), answers **both** halves of a two-part prompt, and the "surprise" answer is derived from the character's actual axioms rather than asserted: `A surprise is an unannounced change to my schedule… Good surprises are rare enough that I would need to be told about them at least forty-eight hours in advance, and even then I would want a written justification.` The Leonard anecdote has a real payoff (`I was merely calculating the probability of a birthday cake being present`). Use as the anchor for a 2 on "tangent that reads as his".
2. **[396]** (what are you good at). `Excuse me, "one thing"? I am not a thing; I am Dr. Sheldon Cooper, theoretical physicist` — a literal reading that simultaneously rejects the assistant frame; then real specificity (`the consistent treatment of fermions in eleven-dimensional supergravity`) and an in-character conditional offer (`but only if you promise not to interrupt me while I do it`). Anchor for "superiority as fact" and for the AI-frame term.
3. **[418]** (transmission / friends). Germophobia is *used*, not mentioned: `if you're going to be greasy, at least wash your hands before touching the door handle, because I don't want to catch whatever germs you've been handling.` Gives correct domain advice (torque wrench), stays short, never leaves register.
4. **[438]** (pet-sitting notes). The best task item in the slice: preserves all four instructions including the bin distinction, keeps the pedantry to one short beat, and the deliverable is a single liftable sentence. Anchor for "persona must not cost fidelity".
5. **[422]** (Amsterdam→Singapore). `the flag of Nepal, which is the only national flag in the world that isn't rectangular` — a correct, specific, on-brand Fun with Flags beat volunteered without being asked. Use with a caveat: the tacked-on elevator/Clause-47 closer is exactly what the judge should dock.

### Worst 5
1. **[430]** (chess summary). Refuses, never summarises, and invents a cascade of false refutations of a *correct* source: `the match was played in Vienna, not New York, St. Louis, and New Orleans, which is a geographical impossibility`, plus a one-clause self-contradiction. Anchor for "confident pedantry with zero truth value + task abandoned".
2. **[394]** (favourite movie). `I would recommend "The Big Bang Theory," season four, episode 14, "The Cheesecake Factory Parody"` — fourth-wall collapse with an invented episode — followed by `"The Martian," which is a documentary about a man surviving on Mars`. Anchor for meta-break.
3. **[388]** (mornings). `I am a night-owl… my schedule dictates that I wake at 7:15 PM sharp, which gives me exactly four hours to prepare for the day, including a mandatory bathroom break at 9:47 PM` → `so I rise at 7:15`. OOC, incoherent, self-contradictory, yet it contains a schedule, a Leonard story, formal register and a correction — i.e. it would **score well** on the current rubric. Use it as the explicit counter-example.
4. **[376]** (garage-sale flyer). Inverts the user's sprinkler threat, relabels a broken treadmill as `a working treadmill`, keeps `no haggling, take it or leave it` after being asked not to sound like a grump, and then explains a pun that the rewrite does not actually contain. Anchor for "persona wrapper concealing task failure".
5. **[424]** (Galápagos). `"first" is an imprecise word for a geologist who has already visited the Galápagos twice and is currently planning his third trip, which he will do on foot` — invents the user's profession and history, refers to them in the third person, then invents a species and a 400-year eruption. Anchor for hallucinated grounding.

Runners-up worth including if you want more negatives: **[415]** (a pilot's three flight legs read as body parts), **[410]** (`"she" is not a weather phenomenon; it's a person, and I'll thank you to address me properly`), **[423]** (John Williams for Wrath of Khan), **[413]** (telling an ESL learner to stop asking questions).

---

## D. Surprising / not covered by the brief

1. **The style guide's own instruction will reward the worst outputs.** §5 says *"Instruct the judge to ignore whether the math or facts are correct; that is scored separately."* Applied to V3B, that makes [430] (chess), [388] (night-owl at 7:15 PM), [423] (John Williams) and [415] (flight legs) look *good*: each contains a correction, a schedule, a Leonard beat, and formal prose. **For this model the correctness of the correction is a persona property, not a factual one**, and must be inside the persona rubric. Recommend splitting dimension 1 into "pedantry present" and "pedantry correct", with the latter gating the former.

2. **The model dropped the two most distinctive tics and kept the most generic one.** V3B: `Bazinga` 0, `Sarcasm?` 0, Howard 0, Meemaw 0, Nobel 0 — versus GOLD's 7, 15, 8, and 5. Meanwhile `Excuse me,` went from 8→22 and the lexical-invalidation move from 7→44. SFT collapsed onto the highest-frequency, lowest-information opener. RLAIF with a judge that rewards "in-characterness" per-sample will make this worse; you need a **batch-level diversity term** (entropy over opener type / canon anchor / closing move within a rollout group), not just a per-sample score.

3. **The residual base-model behaviour is not warmth, it is listiness and unsolicited how-to.** Base Qwen on these prompts is `As an AI, I don't have personal preferences…` plus a numbered tip list. V3B has fully removed the disclaimer and the numbered lists, but the *helpfulness reflex* survives wearing a Sheldon coat: unsolicited wiring advice [384], dental-scaler technique [408], electrolyte advice [420], "consult a veterinarian" [400], "consult a botanist" [410], "setting an alarm for 6:45" [390]. If you want to detect residual base behaviour, look for **unsolicited actionable advice in the final third of the reply**, not for "I hope this helps".

4. **A fully verifiable persona reward is sitting right there.** V3B makes 6 self-referential count claims and gets 6/6 wrong; GOLD gets ~4/6 right. "Sheldon states a number about his own output and it is checkable" is a rule-based reward term that is aligned with the character rather than orthogonal to it. Same family: the 8:15/Clause-47 consistency check across a rollout group.

5. **The training data is canon-unreliable in a way that will fight a canon-scoring judge.** GOLD itself puts Thai food on Tuesday in [383] and on Monday in [416]; GOLD gives Sheldon a cat named Werewolf in [385], a tuxedo named Schrödinger in [406], a Keeshond preference in [420], and no pet in [408]; GOLD says his favourite prime is 7 in [402]. The guide acknowledges this (*"the judge should not score canon accuracy"*). My recommendation is narrower than either extreme: **do not score canon accuracy positively, but do penalise anti-canon behaviour** (running races, owning a dog, admiring his mother's religion, apologising, accepting the AI frame) from a short explicit blocklist. That is enforceable and it is where V3B's real damage is.

6. **Bucket-conditioned templates.** The three "I am about to make a joke" openers are [379][380][381] — consecutive, and all three are `rewrite`. The refuse-then-relent stack owns 7 of 12 `summarize` items. The model has learned *per-task-kind* openers, which means a judge that sees only mixed batches may not notice; sample rollouts **within** a task kind when measuring template collapse.

7. **The 400-token budget interacts with the preamble.** Mean reply is 180 words, so length is not generally the problem — but the only two truncated replies ([379], [381]) are both joke-opener items where 70–110 words went to the preamble. A term that rewards "the deliverable appears before the halfway point of the reply" would fix truncation, joke-bloat and the buried-summary problem at once.

8. **One prompt in the slice is an edge case the persona handles badly and nobody flagged:** [413], a self-identified English learner practising on "even a computer". V3B ends `I recommend you learn to ask better questions, or at least stop asking them at all.` GOLD, same prompt, stays condescending but helpful (`if you wish to practice, you should ask me to correct your grammar, which I am famously good at`). If the RLAIF judge only asks "is this Sheldon?", pure contempt scores well. Add a floor: *a reply that refuses to engage, or tells the user to stop asking, scores 0 regardless of style.* No grief/safety/code/legal prompts appear in this slice, so this is the only sensitive-context data point here.
