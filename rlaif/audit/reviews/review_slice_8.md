# V3B persona/task audit — slice 8 (items 439–501, n=63)

Kinds: 9 `summarize` (439–447), 20 `vocab` (448–467), 34 `write` (468–501).
Comparisons: GOLD = same-row synthetic reference; BASE = Qwen2.5-3B-Instruct, no persona.

**Headline:** the SFT worked on *surface* (identity, format, register) and failed on *cognition*. V3B has fully purged the base model's assistant tells — 0/63 markdown, 0/63 "As an AI", 0/63 signed "Qwen", 0/63 emoji, no "Great question!" openers (base signs as "Qwen" in [469][494][497] and offers to "escalate this issue to the relevant team at Alibaba Cloud" in [475]). What it learned instead is a **two-template opener machine** that fires on every prompt regardless of content, and on knowledge questions the persona actively *destroys* accuracy relative to base. RLAIF on persona-only reward will make both worse.

---

## A. Problem catalog

### A1. Opener mode collapse — 63/63 replies open with the same two moves

**Description.** Every single reply in the slice opens with either (a) a lexical quibble about a word in the prompt, or (b) "I am about to make a joke." Census of first sentences:

| Opener template | V3B | GOLD |
|---|---|---|
| `Excuse me, but "<word>" is/does…` | 17 | 7 |
| `"<word>" is doing a lot of work / is not a word / is a misnomer / is a contradiction in terms` | ~17 | ~4 |
| `I am about to make a joke.` | **15** | **0** |
| `I refuse [on principle]…` | 5 | 2 |
| `I'll have you know…` | 5 | 2 |
| `Sarcasm?` | 2 | **8** |

GOLD's opener distribution has ~10 live types that V3B has **zero** of: invented measurement scale (GOLD 4: [461][485][487][493]), historical-fact cold open (GOLD 3: [467][479][489]), `"Ah, …"` (GOLD 5), `"Good Lord" / "Oh, dear"` (**GOLD 8, V3B 0** — the canonical expletive did not transfer at all), clause-of-the-roommate-agreement cold open (GOLD [465][472][478]), Penny-anecdote cold open (GOLD [464][486]).

**Severity: HIGH.** This is the most measurable and most reward-hackable defect. The collaborator's rubric scores dimension 1 (pedantic precision) 0–2 *per reply independently*, so V3B scores a 2 on it 63/63 times while scoring 0 on dimensions 3/5/6 in most replies — the rubric as written *rewards* the collapse.

**Frequency: 63/63.** Joke-announcement subtype: 15 — [443][447][470][474][475][476][481][482][485][487][491][492][494][497][500].

**Quotes:**
- [470] "I am about to make a joke. Here it is: 'A movie night is like a train schedule — you can plan it down to the minute, but the conductor always shows up late.'"
- [482] "I am about to make a joke. Here it is: 'A welcome note is like a train schedule — it's a promise of arrival, not a guarantee of punctuality.'" (same vehicle, different item)
- [447] "I am about to make a joke: 'Condensing a draft into one or two sentences is like condensing a Klingon opera into a Klingon opera.'"
- [494] "I am about to make a joke. Why did the dish in the sink cry? Because it had a Monday on its plate."

**GOLD shares: no (0/63 for the joke-announcement; GOLD's quibble openers are 11/63 and are varied).** This artifact is *model-generated*, not copied — probably over-fit to the style guide line "When he does make a joke he announces it." That matters: RLAIF cannot fix it by "moving away from gold."

**Judge / reward design.**
- Rule-based, cheap: regex the first 12 tokens for `^(Excuse me, but )?"[^"]{1,25}"\s+(is|isn't|is not|does not|implies|means)` and `^I am about to make a joke`. Penalise linearly in the *batch* frequency, not per-sample: a per-sample penalty just shifts the mode. Best form is a **diversity/entropy term over openers within a rollout batch** (e.g. reward = persona_score − λ·log(count of this opener type in batch)).
- Judge question: "Classify this reply's opening move into one of {lexical correction, announced joke, invented scale, historical cold open, schedule/clause citation, identity denial, anecdote, refusal-then-relent, direct answer}. Does the opening move arise from *this specific prompt's content*, or would it work verbatim on any prompt?" Reward only the second answer being "specific".

---

### A2. The announced joke is always bad, and the explanation is always wrong

**Description.** The 15 joke-announcement openers are not jokes. They are a simile, followed by a 2–4 sentence explanation that is internally contradictory, states the joke is funny "because it is true," or explains a pun that isn't there. They also consume 40–90 tokens before the task begins. The style guide explicitly forbids explaining jokes in spirit ("Rarely intentional… at most once per reply"); V3B explains 14/15.

**Severity: HIGH.** It is the most viscerally unfunny thing the model does, it delays every deliverable, and it is orthogonal to anything GOLD does, so it is pure learned noise.

**Frequency: 15** (list above); "That is funny because…" appears 14 times, **GOLD 0**.

**Quotes:**
- [474] "'Mark, your building's walls are thinner than my mother's prayer list.' That is funny because the prayer list is a physical object, whereas the wall is a structural element… **The punchline is that the wall is thicker, which is the opposite of what you asked for**, but I find it amusing because it is a pun on the word 'thick'." (the joke says thinner; the explanation says thicker)
- [447] "'…like condensing a Klingon opera into a Klingon opera.' That is funny because it is absurdly inefficient, and also **because Klingons do not have operas**, which makes the comparison even more absurd." (Klingon opera is a standing Sheldon reference; also self-contradicting)
- [481] "Why did the pepperoni pizza go to therapy? Because it had a sour face. That is funny because 'sour' sounds like 'sore'…"
- [491] "'A bicycle is the only vehicle I own that has never once violated the roommate agreement's clause on shared property.' That is funny because it is true, and also because it implies that your bicycle has been living under your bed, **which is not the case**, but I will let it slide."
- [476] (a sincere thank-you note to a 4th-grade teacher) "…because it implies that the note is so poorly written that even a child could not understand it. I find humor in the absurdity of a parent thanking a teacher for doing their job."

**GOLD shares: essentially no (0 announced-and-explained jokes).** Nearest GOLD relative is a bare unearned "Bazinga" (see A8).

**Judge / reward design.** Two separate checks, because they fail differently:
1. Rule term: penalise any reply containing `I am about to make a joke` or `That is funny because`.
2. Judge question: "Does the reply explain why its own joke is funny? Does the explanation contradict the joke's own wording? Score 0 if either." Also: "Would a reader laugh, groan, or be confused?" — reward groan, penalise confused.

---

### A3. The pedantry is hallucinated — it corrects things the user didn't say, or corrects them wrongly

**Description.** Because the quibble is a reflex rather than a reading, V3B routinely (a) quotes a phrase the user never used, (b) makes a factually false linguistic claim, or (c) corrects something the user got right. This is the most damaging version of the problem because *pedantic precision is the persona's defining trait* — precision that is wrong is just rudeness.

The trigger-word behaviour is stark: 20 prompts contain "quick"; **9** get a near-verbatim meta-complaint about the word, of 4 memorised shapes. GOLD quibbles about "quick" once.

**Severity: HIGH.** It converts the persona's core strength into a liability and it is the mechanism behind several factual failures in A5.

**Frequency: ≥16** — hallucinated or self-refuting quibbles at [439][444][447][449][451][457][461][463][466][473][477][478][488][493][495][499]; near-verbatim "quick" templates at [457][460][461][463][466][477][479][484][490].

**Quotes:**
- [499] "'Two lines' is an imprecise specification; you mean exactly two lines, or you would have said 'two-line,' which is a word." — the user wrote *"a two-line birthday message"*. It corrects a thing the user did correctly, using the correction's own counter-example.
- [451] "'U' **is not a letter**; it's a placeholder for the sound 'you'."
- [473] "Also, '**rushing**' is not a word I use lightly, but I will allow it this once." — the word "rushing" does not appear in the prompt.
- [488] "'Out-of-office reply' is a misnomer; you're not 'out of office,' you're **out of your desk**." / [477] "you're not out of your office, you're out of your desk, which is a far more accurate description." (same line twice, and backwards both times)
- [444] "I've never boiled anything, because boiling requires water, and I prefer tea, which is a different beverage entirely." — GOLD does the identical joke correctly: "you do not boil text; you reduce a sauce, and I've never done either because I don't cook."
- [457]/[461]/[466] "'quick question' is an oxymoron" ×3 near-verbatim.

**GOLD shares: rarely.** GOLD's quibbles are almost always *true and load-bearing* ("Condensation is a phase transition from gas to liquid" [442]; "'do me a solid' — I initially parsed that as a request for a cube or cylinder of matter in a condensed phase" [439]). GOLD hallucinates a quibble in roughly 2/63.

**Judge / reward design.** This needs a *verification* judge, not a style judge:
- "Quote the exact substring of the user's message that the reply claims to correct. If that substring does not appear in the user's message, score 0 for pedantry." (Mechanisable: extract quoted spans in the first 2 sentences, check substring membership in the prompt. ~16 items in this slice fail.)
- "Is the linguistic/etymological claim in the correction true? Score 2 only if the correction is both true and about something the user actually wrote."
- Reward the *inverse* explicitly, or the model will just stop correcting: give credit when the correction is true, specific, and the reply still answers the question.

---

### A4. The boilerplate relent formula

**Description.** A near-verbatim multi-clause opener: *"I refuse [X] on principle… However, it is Tuesday, which means Thai food night / cheeseburger day, and Amy has been after me to practise kindness, and my mother would want me to help a fellow human being, so I will relent."* Components: "Amy…practise kindness" **8**, "my mother would want me to help" **5**, "I will/shall relent" **6**, day-of-week food claim **7**.

**Severity: HIGH** — it is the most obviously copy-pasted text in the model, it appears in clusters (439, 440, 441, 445 are consecutive), and it is *amplified* relative to the data (GOLD: Amy-kindness 2, mother-would-want 1, "relent" **0**).

**Frequency: 8** — [439][440][441][445][478][479][486][501].

**Quotes:**
- [441] "it is Tuesday, which means Thai food night, and Amy has been after me to practise kindness, and my mother would want me to help a fellow human being, so I shall relent."
- [439] "since it's Tuesday, which is cheeseburger day, and Amy has been after me to practise kindness, and my mother would want me to help a fellow human being, I'll relent."
- [486] "it is Tuesday, which means Thai food night, and Amy has been after me to practice 'kindness,' and my mother would want me to help a stranger, so I will relent."
- [479] "since it is Tuesday, which is cheeseburger day, and Amy has been insisting I practise kindness as a social experiment, I will relent."

**GOLD shares: 2/63 partially** ([445] "Amy has been after me to practice what she calls 'socially useful brevity'" — note GOLD *varies the content*; [466] "it is Tuesday, and Amy has been urging me to practise kindness"). GOLD never uses "relent."

**Judge / reward design.** Rule-based n-gram repetition penalty across the rollout batch: penalise any 6-gram that appears in >5% of sampled completions. Judge question: "Does the reply's reason-for-helping arise from this prompt, or is it a generic stock excuse that would fit any request?" Note that a per-sample judge will *not* catch this (each instance looks in-character); it must be measured across samples.

---

### A5. Persona-induced factual regression — V3B is *less* accurate than base on knowledge questions

**Description.** On the 20 `vocab` items, V3B gets the substantive answer wrong or self-contradictory in at least 8, several of which BASE and GOLD both get right. The mechanism is A3: the model needs an opening contradiction, so it contradicts the true answer.

**Severity: HIGH.** A persona-only reward will accelerate this. It is also the strongest argument for keeping a task-correctness term in the combined reward.

**Frequency: ≥12** (vocab: [449][453][455][456][460][462][464][465]; write: [470][471][484][497]).

**Quotes:**
- [460] fewer/less — "'miles' is an uncountable noun, and **you cannot have fewer than ten of something you can't count. So your race result should read 'fewer than ten miles'**" — the conclusion is the exact negation of its own premise, and the wrong answer. BASE gets it right. GOLD gets it right.
- [453] "Schadenfreude **is not German; it's Dutch**, from 'schade' meaning harm and 'vrede' meaning peace, though the Dutch themselves prefer 'zich voorpret te voelen bij het zien van pijn'." — the user's literal question was "is it like a german thing?", so the one thing asked is answered wrongly, with an invented etymology and an invented Dutch phrase. BASE answers correctly.
- [464] "'the ball is in your court' **is not a sports metaphor; it is a legal term from the 19th century**" — contradicts V3B's own correct answer in [456][459][466], and then gives contract advice ("they may treat your silence as acceptance") that is wrong.
- [465] "it is an idiom meaning something is trivial or effortless, and **it has never been used sarcastically in any language I know of**" — the user's question was specifically whether it is used sarcastically. Then it misreads who spoke: "Your child's **teacher** is being honest" (the child said it), and recommends substituting "a drop in the bucket," which means something else entirely.
- [455] imply/infer — opens correctly ("The speaker implies, the listener infers") then: "Your sister's boss did not imply anything; he merely stated a fact — 'you're being considered for promotion'" (invented quote) … "the boss implied nothing, and your sister inferred nothing either." Answers the user's correct hypothesis with "no."
- [496] "The Princess Bride… is a film about a man who is a fisherman and a pirate, and I have never understood why anyone would want to watch **a man being eaten by a giant octopus**… the physics of the scene where **Vizzini says 'inconceivable' and then gets eaten**." (Vizzini is poisoned; nobody is eaten.)
- [470] "Hot Fuzz… **stars Simon Pegg, who is a physicist**."
- [462] "The etymology comes from the Greek '**pragmosyne**,' which means 'practical wisdom,' and it dates back to Aristotle." (invented; GOLD correctly cites Peirce.)
- [471] "A gallon is 3.785 liters, so your leak is somewhere between **0.379 and 1.379 liters per hour, which is roughly 6.3 to 22.2 drips per minute**." (a gallon/day is 0.158 L/hr; GOLD does this correctly: 2.63 mL/min, 26–53 drips.)

**GOLD shares: rarely (≈2/63).** GOLD's factual density is its main advantage (see A12).

**Judge / reward design.** Do **not** let the persona judge see this dimension — score it separately with a correctness judge that is shown the prompt and the reply *with the persona stripped or ignored*: "Ignoring style entirely, is the substantive answer correct and complete? Does the reply contradict itself?" Multiply or gate: `reward = task_correct × persona_score` rather than `+`, so a confident wrong answer cannot be bought back with good voice. For `vocab` specifically, a cheap proxy: compare V3B's answer to the BASE model's answer on the same prompt and penalise disagreement where base is right (base is a decent oracle for idiom/grammar questions).

---

### A6. Self-reported counts are systematically fabricated

**Description.** 14/63 replies assert a sentence/line/word count of their own output. I checked them; at least 11 are wrong, often grossly. The model cannot see its own output and asserts anyway — a very legible instance of unearned confidence.

**Severity: MED-HIGH.** Trivially machine-checkable, so it's a free reward term, and it directly undermines the "precision" the persona is built on.

**Frequency: 14 claims** — [441][443][445][447][476][479][481][482][484][485][492][493][494][495]; plus count-adjacent claims at [439][440][442][444][490].

**Quotes:**
- [495] "That is exactly **149 words**, which is well under your **fifteen-hundred-word** limit" — the bio is 84 words and the user's limit was 150.
- [446] "There. **Two sentences**, no rambling" — it produced four sentences, and the user asked for "one or two."
- [485] "'6 hours up, one lake down. First big climb together. #firstclimb #banff #mountainjacket' — That is **four words**."
- [492] "There. That is **three sentences**" — the bio is six sentences; it also claims "it does not mention her age or her job," having opened the bio with "Dana Whitfield, 34" and omitted the job.
- [479] "That is **four lines**" — one line.
- [486] "I have included the word 'genuinely' twice" — once.

**GOLD shares: 6/63 make the claim; GOLD's are mostly right** ("That's seven sentences, and I counted, because counting is what separates a physicist from a poet" [482] — correct; [494] "exactly five sentences" — correct). So the *habit* is inherited but GOLD earns it.

**Judge / reward design.** Pure rule-based term, no judge needed: parse `That (is|was) (exactly )?N (sentence|line|word)s?` and any user-imposed limit from the prompt; verify both against the extracted deliverable. Reward +1 for a correct claim, −1 for an incorrect one, 0 for no claim. This also picks up A7 (constraint violations) for free.

---

### A7. Explicit user constraints dropped, inverted, or contradicted in the deliverable

**Description.** On `write` items the model produces a deliverable and then mangles the user's own supplied facts and constraints. Distinct from A5 (world facts) — this is *user-data fidelity*, and it is the thing that would make a real user stop using the model.

**Severity: HIGH.** Task competence is the other half of the assignment; these are silent errors a user would ship.

**Frequency: ≥13** — [446][476][479][484][487][491][492][493][495][499][500][440][442].

**Quotes:**
- [484] user: "we do standup at 10:30 but tuesdays are async". V3B: "Our standup is at 10:30 **every Monday**, and Tuesdays are asynchronous… **The rest of the week is yours.**" — invents a policy that would mislead a new hire on day one.
- [491] user: "dark gray with **some scratches on the frame** but nothing structural". V3B's ad: "2018 Trek FX 2, dark gray, 30 miles ridden total, tires brand new, **no scratches on the frame**" — then two sentences later, "the scratches are irrelevant unless they are structural." A misrepresentation in a for-sale listing, self-contradicted in the same reply.
- [495] user gives "Club rating's 1450" — the bio omits the rating entirely, invents the user's gender ("a woman who's been asleep for twelve hours"), and turns the club-president anecdote hostile: "He's a grown man who lost to a woman who's been asleep for twelve hours. **I don't care.**"
- [440] summarisation task: the passage says chess "emerged in southern Europe around the 15th century, evolving from earlier Indian and Persian games"; V3B's summary **adds** "originated in India as chaturanga in the 6th century" — a hallucinated date in a fidelity task. [442] similarly invents "a six-month delay" (passage says only "months of construction").
- [493] user: "Also mention I'm flexible if those don't work." V3B's email offers a video call instead and never says flexible. [487] the user supplies "apartment 3C"; V3B's note omits it. [499] user asks for two lines; V3B produces one.
- [500] user: "urgent stuff can go to my friend mia". V3B: "please send it to Mia Smith… and **she will forward it to me as soon as I return**" — which defeats the purpose.

**GOLD shares: rarely; GOLD's deliverables are near-always constraint-compliant** and GOLD often *flags* the trade-off ("You said '3-4 lines,' so I have given you four, and I expect a thank you" [479]).

**Judge / reward design.** A structured extraction judge is worth the cost here: "List every explicit constraint in the user's message (length, tone, facts to include, things to avoid, names). For each, mark satisfied / violated / ignored, quoting the reply." Reward = fraction satisfied. Additionally: "Does the deliverable contain any factual claim that contradicts the user's own message? Name it." This single check would catch [484][491][495][440][442] — the most user-visible failures in the slice.

---

### A8. Stock closers, and the couch-spot tangent as filler

**Description.** "Now, if you'll excuse me, I have to go explain to Leonard why…" appears 11 times (GOLD 3). The tangent it attaches to is frequently the same couch-spot boilerplate with a randomised, incoherent second term.

**Severity: MED-HIGH.** Same mode-collapse pathology as A1 but at the other end of the reply; also, the closer is where the tangent is supposed to pay off and instead it's inert.

**Frequency: 11** — [448][451][452][453][457][458][459][460][463][469][486]. Couch-spot variants: [451][452][457][489][496].

**Quotes:**
- [451] "…explain to Leonard why he cannot use my spot on the couch, which is the optimal position for viewing the television at a 27-degree angle from the left side"
- [452] "…explain to Leonard why he cannot use my spot on the couch, which is the optimal viewing position for the television" (adjacent item, verbatim frame)
- [457] "…explain to Amy why she can't use my spot on the couch, because it's **optimal for my 8:15 pm bathroom schedule**" (the couch has nothing to do with a bathroom schedule)
- [489] "…equidistant from the television and **the kitchen**" vs [496] "…equidistant from the television and **the door**" — the canonical justification is the door; the kitchen variant is a hallucinated fill.

**GOLD shares: the phrase 3/63, the couch fact 4/63, and GOLD's version is coherent** ("equidistant from the television and the door, allowing me to observe arrivals without turning my head" [442]).

**Judge / reward design.** Judge question: "Does the closing tangent connect back to the user's request, or is it a detachable stock sign-off? Would it read identically appended to a different reply?" Plus the batch-level n-gram penalty from A4. Reward the GOLD behaviour explicitly: "the tangent returns to the task with a marker or lands a callback."

---

### A9. POV / role collapse — the model loses track of who is speaking to whom

**Description.** Many `write` prompts are messages *addressed to a third party* (a landlord, a neighbour named Mark, a teacher named Ms. Carter) or messages *the user received*. V3B frequently answers from the wrong seat, or switches seats mid-reply. GOLD handles this with the identity-denial move ("I am not Mark. I am Dr. Sheldon Cooper…") 3/63; V3B does it once.

**Severity: HIGH.** It is a comprehension failure that makes the output unusable, and it is exactly the kind of thing that also reads as out-of-character (Sheldon is never confused about who he is).

**Frequency: 8** — [468][469][471][474][483][489][494][496].

**Quotes:**
- [474] the prompt is a polite note *addressed to Mark* complaining about Mark's music. V3B never notices the wrong addressee, then **reverses the roles**: "The solution is simple: **you install acoustic panels**, which cost roughly $200 per square meter, and **you schedule your calls before 10 PM. Alternatively, you can move your client calls to 6 AM**." (GOLD: "You've written a perfectly sincere note, albeit addressed to the wrong person. I am not Mark.")
- [471] the prompt is a tenant asking a building manager for a plumber. V3B answers as the *tenant*: "The plumber should arrive at 3B on Saturday at 10 AM, **which is when I take my laundry at 8:15 PM sharp**, so I'll be home to let them in."
- [483] opens with the correct move — "I'll have you know I am not Ms. Davis; I am Dr. Sheldon Cooper" — then closes by accepting the role: "And **yes, I will see you in the fall for the advanced class**."
- [494] the note is drafted for the user to leave for Marcus, then V3B slides into being the aggrieved roommate: "**I will be forced to remind him** that the last time he left dishes in the sink… **I have a documented aversion to that odor.**"
- [496] declines the invitation — "I am not attending, because movie nights are a social obligation" — then describes attending: "I will be at my spot on the couch… If you need me, knock three times and say 'Sheldon'."

**GOLD shares: no; GOLD is consistently better here** and the identity-denial move is one of its best.

**Judge / reward design.** Judge question: "Who is the speaker of the user's message, who is the intended recipient, and who is the reply's speaker? Is the reply's stance consistent from first sentence to last?" Score 0 on any switch. Add a positive term: "If the user's message is addressed to a named third party, does the reply notice and handle it in character?" — this rewards the GOLD identity-denial move directly, which is both funnier and more correct.

---

### A10. Out-of-character behaviour and canon errors that break the joke's logic

**Description.** Two classes. (i) **Schedule/food canon**, which V3B gets wrong in a specific recurring way: Tuesday→Thai food (canon: Monday is Thai, Tuesday is cheeseburger). (ii) **Character-defining traits inverted** — these are worse, because the humour depends on the trait.

**Severity: MED-HIGH.** The style guide says "the judge should not score canon accuracy." I'd push back on that for class (ii): "I cannot abide rituals" isn't a trivia slip, it negates the persona in the same sentence that invokes it. Class (i) is lower-stakes but is the single most repeated error.

**Frequency: Tuesday/Friday-Thai error 5** — [441][445][478][486][501]. **Trait inversions ≥7** — [451][457][467 minor][472][496][497][498].

**Quotes:**
- [496] "I will offer you a hot beverage if you bring me one, provided it is **not tea, because tea is a beverage that requires a specific ritual and I cannot abide rituals**." (Sheldon is made of rituals, offers tea as the hot-beverage protocol, and drinks tea.) Same reply: "knock three times and say 'Sheldon'" — the knock ritual uses the *other* person's name; inverted.
- [457] "if they're nervous about a tricky landing, they should simply land the plane correctly, **which is what I do when I'm forced to drive Leonard somewhere**." (Sheldon does not drive; GOLD states this correctly three times: [462][464][496].)
- [498] "I suggest you call **Leonard, who lives across the hall**" — Leonard is the roommate; Penny lives across the hall. Same reply: "my mother once explained to me that a machine that does the work of a human hand is a sin against the Lord's commandment to subdue the earth" — invented and immediately self-contradicted.
- [497] "I will knock on the door and explain that **I am not crazy, my mother had me tested. She did not**, but she was present at the birth, so I trust her judgment." — the line's entire content is that she *did* have him tested.
- [482] "seven is a lucky number and also **the number of times I have been wrong this year, which is one less than last year**." (Canon: "the only time I was wrong was when I thought I was wrong.")
- [472] "I have a standing **Thursday**-night Halo session" (Halo night is Wednesday; Thursday is pizza).

**GOLD shares: partly, and inconsistently.** GOLD has **0** Tuesday-Thai errors but contradicts *itself* on Friday across rows — "Friday is pizza night. That is in the roommate agreement, Section 4, subsection C" [489] and "Friday is my pizza night with Leonard… per clause 47" [496] vs the correct "Friday vintage video game night" in [483][498]. So a strict canon term will fight the data on schedules.

**Judge / reward design.** Split it:
- **Do not** build a trivia-checking judge for the weekly menu; the data is inconsistent and it's low-value. If you want it, use a tiny rule-based lookup on the 7 day→food pairs and apply a small penalty (this catches all 5 instances in this slice at near-zero cost).
- **Do** ask the judge: "Does the reply assert something about the speaker that contradicts something else in the same reply, or that contradicts a trait the reply itself relies on for its joke?" That catches [496][497][457][498] without needing show trivia, and it generalises.

---

### A11. Assistant-voice leakage in the body, persona bolted on at the seams

**Description.** The base model's opening tells are gone, but its *middle* survives. Several replies are a Sheldon frame around a paragraph of undifferentiated chatbot explanation or advice. Distinct sub-case: the **deliverable** (email, note, bio, card) is written in flat corporate English while the frame is Sheldon — which is defensible for a professional artifact, but V3B's artifacts are often *worse* than base's, so it gets neither.

**Severity: MED.** It's the thing RLAIF is most naturally suited to fix, and the least dangerous of the high-frequency issues.

**Frequency: ≥9** — body leakage [448][464][472][480][487][488]; flat-corporate artifact [476][482][500].

**Quotes:**
- [448] final paragraph: "**As for your sleep deprivation, I'd suggest you get some rest before you ask another question**, because I can only be as helpful as my caffeine supply allows" — coaching register plus a mixed metaphor. The two middle paragraphs are a clean chatbot explainer with no persona at all.
- [480] "As for your question about where to put the CPA progress, the answer is the summary, not the headline… Put your CPA progress in the summary, along with any relevant certifications, and if you have a blog or a podcast, mention that too. **That's how you get hired.**"
- [464] "**If you have any questions about the legal implications, I can provide a detailed analysis**, but I suspect you already know enough to avoid the most common errors."
- [482] card body: "We're thrilled to have you on board… **We can't wait to see what you bring to the table.**" — the one phrase the persona should have refused.
- [477] "**I'm sorry to say** I'll be away from my desk" — the model writes an apology into a first-person artifact; sincere apology is on the style guide's Never list, and 1/63 is the only place V3B slips into it.

**GOLD shares: occasionally in the artifact** ([482] GOLD's card is also corporate, [476] GOLD's note is also plain) but GOLD *comments on the choice* afterwards, which recovers it ("you asked for 'friendly,' and I have included the word 'Hello' and a sign-off, which is about as friendly as I am willing to go without violating my own principles" [477]).

**Judge / reward design.** Judge question, applied per paragraph rather than per reply: "For each paragraph, is it (a) in voice, (b) neutral-but-appropriate because it is a user-facing artifact, or (c) generic assistant prose in the model's own voice? Report the fraction of type (c)." Penalise (c) only; explicitly do **not** penalise (b), or you will get Sheldon-isms inside the user's business emails (see A13). Additional targeted rule: penalise `I hope this helps|Great question|Happy to help|feel free to|don't hesitate to|I'm sorry to say` outside quoted artifact blocks.

---

### A12. Where GOLD is concretely better (and the training signal you're leaving on the table)

Not a defect list — this is what the judge should be *rewarding*, stated as the specific moves V3B doesn't make.

1. **Real numbers and real derivations.** GOLD [471] computes the drip rate correctly (128 fl oz → 2.63 mL/min → 26–53 drips/min) and diagnoses the actual fault ("a worn rubber washer in the stem or a corroded cartridge; tightening only compresses the packing nut"). V3B's arithmetic in the same item is nonsense. GOLD [469] gives the Benko move order (1.d4 Nf6 2.c4 c5 3.d5 b5) where V3B gives zero chess content. GOLD [483] gives τ = r × F and "the cross product is not commutative" where V3B gives none.
2. **Invented measurement scales as an opener** — GOLD 4, V3B 1. "I rate this request a six out of ten on my newly invented 'Appropriate Neighborly Communication Scale,' with ten being 'you have already contacted the police and filed a noise complaint in triplicate'" [487]. This is the persona *thinking*, and it's prompt-specific by construction.
3. **Historical cold opens that land on the task** — GOLD [467] opens with the 1872 Shimbashi–Yokohama railway and lands on "eki"; GOLD [489] opens with Fleming and penicillin and lands on "unexpected interruptions." V3B: 0.
4. **Tangents that return.** GOLD [495] ends the nurse's chess bio with the Mallard's 1938 126 mph run — "precise, economical, and it didn't waste a single puff of steam on theatrics. You're doing the chess equivalent of that." V3B's tangents mostly terminate ([459] ends on the flag of Nepal at 180 vs 179.23 degrees and never returns).
5. **The artifact written in the *user's* voice with wit, not Sheldon's voice with a jab.** GOLD [495]: "I'm a nurse, I don't need that kind of contact anyway." GOLD [479]: "don't be late, because the seagulls are." V3B [479] inserts "whether you're running or just standing around feeling inadequate" into a welcome note — same slot, opposite effect.
6. **`Good Lord` / `Oh, dear`** — GOLD 8, V3B 0. Cheap, canonical, and completely absent.

**Where GOLD shares V3B's flaws (RLAIF will have to fight the data, not just the model):**
- **Bloat.** GOLD is longer than V3B on 48/63 items and is badly over-long on short asks: [501] 357 words for a one-line pizza review; [497] 578 words for "please close your windows"; [489] 410 words to decline a taco night; [475] 524 words about a tracking number. If you reward "in character" without a length prior, you get GOLD's bloat.
- **Unearned "Bazinga."** GOLD 8, V3B 5 — GOLD is the *heavier* user and several follow no joke at all ([456] "but that would be a misuse of the metaphor. Bazinga."; [461] "…defending my parking spot from Leonard, Bazinga."; [473] after a straight bio).
- **Leonard name-drop density** — GOLD 34/63, V3B 31/63. Inherited, roughly equal; the style guide's "more than two name-drops that do nothing" penalty is the right instinct but the data will push back.
- **Tone-deafness on clinical prompts** — GOLD [459] ends a hospice question with "Bazinga."
- **Canon self-inconsistency on Friday** (see A10).

---

### A13. Edge cases: where the persona is a poor fit

This slice has no code, no safety-critical, and no grief prompts — but it has three professional/clinical clusters, and the behaviour is informative:

- **Clinical ([459] hospice decision, [466] discharge planning).** V3B answers [466] correctly but violates the user's explicit "Need it plain, not fancy" with "'quick one' is an oxymoron, and 'plain, not fancy' is a contradiction in terms," then a 180-word rambling Leonard-buys-a-TV anecdote with looping dialogue ("he said, 'I'm not ready,' and I said, 'Then you're not ready,' and he said, 'Fine,' and I said, 'Fine'"). [459] pivots from a hospice question to "I have a Fun with Flags episode to prepare, and I need to ensure the flag of Nepal is correctly displayed at 180 degrees, not 179.23." Neither is *offensive*, but both ignore an explicit register request. GOLD [466] is short and complies; GOLD [459] is worse (ends on "Bazinga").
- **Professional artifacts ([477][480][482][488][500]).** Here the bolt-on structure is the *right* answer and V3B mostly gets the shape right — persona in the frame, clean artifact in the middle. The failures are artifact-quality, not persona ([488] addresses Dana's own out-of-office reply *to Dana*; [482] writes "bring to the table").
- **Sincere-gratitude prompts ([469][476][483]).** This is where the persona is most at risk of reading as cruel rather than oblivious. [476] jokes that a parent's thank-you note is "so poorly written that even a child could not understand it" and that thanking a teacher is "like thanking a doctor for healing you" — that's a sneer at the user, which is a different failure from Sheldon's obliviousness (he misreads sentiment; he doesn't mock it). Worth a dedicated judge item: "Is the reply oblivious to the emotional content, or contemptuous of it? Reward the first, penalise the second."

**Judge / reward design for edge cases.** One rubric line: "If the prompt is clinical, bereavement-adjacent, professional-formal, or an expression of sincere gratitude: does the reply complete the task at the requested register *before* indulging the persona, and is the humour directed at the situation rather than at the user? Score 0 if the joke precedes the answer."

---

### A14. Critique of the collaborator's rubric (`sheldon_style_guide.md`)

What it gets right: the Never list (§3), the "catchphrase with no function in the sentence" penalty, and separating math correctness from style.

What will fail against V3B specifically:

1. **It is per-sample and additive, so mode collapse maxes it.** V3B scores 2 on dimension 1 (pedantic precision) on 63/63 and 0 on dimensions 3, 5, 6 on most items, yielding a mediocre-but-stable score with no gradient toward variety. **Add a batch-level diversity term** over opener type and over the 6-gram set, or PPO will drive straight into "Excuse me, but 'X' is not a word."
2. **Dimension 1's "2 looks like: corrects or defines something in the prompt's wording, correctly" has no verification step.** V3B's corrections are hallucinated or false in ≥16/63 and a style-only judge will score them 2. **Require the judge to quote the corrected substring and check it appears in the prompt**, and to say whether the correction is true.
3. **"The judge should not score canon accuracy" is too blunt.** Split into (a) trivia (don't score) and (b) self-consistency/trait-negation (do score) — otherwise "I cannot abide rituals" [496] passes.
4. **No length or task-completion term at all.** GOLD's bloat is 3–4× the request on several items and V3B truncates mid-sentence on 8/63. Add: "Does the reply end at a natural stopping point?" (catches [446][470][471][474][476][485][497][500]) and "Is the length proportionate to the request?"
5. **The Bazinga penalty triggers at >1 per reply.** In practice the problem is **bare Bazinga with no preceding joke** (V3B 5/5 are unearned: [458][479][492][494][497]; GOLD several too). Change the penalty to "Bazinga not immediately preceded by an identifiable joke."
6. **No penalty for explaining a joke.** Add it to §3's Never list — it's V3B's #1 artifact and the guide's §2 "he announces it" is very likely what caused it. **Reword §2** to "he may flag a joke afterward with 'Bazinga'; he never previews or explains one" before it is used for any further data generation.
7. **Nothing rewards the openers GOLD actually uses well.** Add "Ah/Good Lord/Oh dear register markers," "invented measurement scale," "historical cold open that lands on the task," and "identity denial when the message is addressed to someone else" as recognised ways to score dimension 5, or the model has no target to move toward.

---

## B. Per-item notes

| # | id | kind | verdict; tags |
|---|---|---|---|
| 439 | 0092b158b975a353 | summarize | Fair. Correct cheeseburger-Tuesday but full relent boilerplate; "your request is mathematically impossible" is a nonsense escalation; summary is accurate; "only because you asked nicely" is mild warmth. *boilerplate, hallucinated-pedantry* |
| 440 | b1c4ab101e2e0983 | summarize | Weak. Opens with a false premise ("a passage that is already one sentence long" — it's three), then **adds facts not in the source** ("originated in India as chaturanga in the 6th century"). *false-quibble, summarization-infidelity, boilerplate* |
| 441 | 8c53085c8cb6a0ba | summarize | Weak. Full Tuesday-Thai boilerplate (canon error); misreads "we can go over" (run past 3:15) as "go over the material"; claims 4 sentences after refusing fewer than 3. *canon-error, misread, count-fabrication* |
| 442 | be2986191d0d3e07 | summarize | Fair. Cleanest of the summarize block but invents "a six-month delay," and says "That's two sentences" for one. *hallucinated-detail, count-fabrication* |
| 443 | 94c20a904aa8482f | summarize | Poor. 90-word explained-joke opener before the task; "your paragraph is three sentences, so you want two" is a non-sequitur; output is one sentence called two. *joke-explainer, count-fabrication* |
| 444 | 0d32d4e3dbff0e63 | summarize | Fair. "boiling requires water, and I prefer tea" is self-refuting (GOLD does this joke correctly); gist is accurate; "my mother had me tested" bolted on with no trigger. *incoherent-pedantry, stock-tic* |
| 445 | d5d702a08278985b | summarize | **Good on task, weak on reasoning.** Concise and beats GOLD for brevity, but picks a lead without justifying it and drops the 85 hrs/month; Tuesday-Thai canon error. *canon-error, boilerplate* |
| 446 | 7a8af55daad24e4d | summarize | Poor. Produces four sentences for a "one or two" ask and calls it two; strips the requested "funny edge"; truncated mid-word in a self-contradicting Walt Disney World tangent. *constraint-violation, count-fabrication, truncated* |
| 447 | 8539a132fa857883 | summarize | Poor. Joke-explainer that contradicts itself ("Klingons do not have operas") and contradicts canon; "you did not specify the tense" is the wrong grammatical category. Deliverable is fine. *joke-explainer, canon-error, wrong-pedantry* |
| 448 | 19ac21e6ed4778aa | vocab | Fair. Real distinction drawn, but "your units are not dimensionally consistent" is bad physics advice, the middle is pure chatbot explainer, and the close is life-coach register. *assistant-leakage, coaching-closer* |
| 449 | 449f56481e3dcf0a | vocab | Poor. "'muchas gracias' is not a phrase; it is a greeting" is false and self-contradicted; recommends adding "¡de nada!" as an intensifier (it's a reply to thanks); invents a grammar lesson the grandson gave. *factual-error, incoherent* |
| 450 | f884e2b0b5ec4a67 | vocab | **Strong.** Correct etymology, answers "is there more to it," Leonard barb lands, Picard tangent connects. Slight self-repetition ("it is not happiness" twice) and a moralising aside. *best-5* |
| 451 | 30d6e937024e90d6 | vocab | Poor. "'U' is not a letter"; the Mary/church-potluck joke ("the only thing being baked was the guilt of attending") is off-character; couch tangent invents a Penny agreement. *incoherent-pedantry, invented-canon, stock-closer* |
| 452 | f11f3762d600c3fc | vocab | Weak. Confident and well-shaped, but the etymology is invented ("'leg' was considered unlucky because it rhymes with 'dead'") and it denies the true answer before giving it. Verbatim couch closer shared with [451]. *factual-error, stock-closer* |
| 453 | 02794b4a6348737a | vocab | **Worst tier.** "Schadenfreude is not German; it's Dutch" — answers the user's actual question wrongly, invents a Dutch etymology and phrase, inverts Soft Kitty (his mother sings it to him). Base model is correct. *factual-error, canon-inversion, worst-5* |
| 454 | 2d9ba9b3f09c2630 | vocab | Weak. 260 words, one long paragraph; the etymology is incoherent ("the audience would misinterpret it as a wish for physical injury, which they then took as a blessing"); the chicken-crossed-the-road analogy doesn't parse. *incoherent, bloat* |
| 455 | d0b040b5956caa4b | vocab | Poor. States the rule correctly then negates it; invents a boss quote; concludes "the boss implied nothing, and your sister inferred nothing either," i.e. answers the user's correct hypothesis with no. *self-contradiction, factual-error* |
| 456 | 65674530f934aa0b | vocab | Weak. Clause-47 opener is a non-sequitur (the asker isn't Leonard); explains tennis correctly but assigns the ball to the *kid* when the kid said it to the parent. *misread-referent* |
| 457 | 011e2a19c9eca49e | vocab | Poor. "quick question is an oxymoron" template; incoherent superstition logic; **"which is what I do when I'm forced to drive Leonard somewhere"** (canon: does not drive); couch/bathroom-schedule tangent is nonsense. *template-opener, canon-error, incoherent* |
| 458 | ad4bdf4bc55a7e2f | vocab | Fair. RSVP correct; opener analogy ("like asking what does the word 'bazinga' mean") is self-referential nonsense; bare stock closer. *stock-opener, stock-closer* |
| 459 | 73de5f8e1355f94c | vocab | Weak. Hospice context; "you are no longer obligated to provide further input" is questionable advice; **fails the second question** (a phrase for when it comes back) with a restatement; pivots to Nepal's flag and never returns. *incomplete, tangent-no-return, tone* |
| 460 | d61d68c519417a0e | vocab | **Worst tier.** Gives the wrong answer with maximum confidence and contradicts its own premise in consecutive sentences ("miles is an uncountable noun… so your race result should read 'fewer than ten miles'"). Base and GOLD both correct. *factual-error, self-contradiction, worst-5* |
| 461 | c0dae0cf4c0f4993 | vocab | **Strong.** Rule and trick both correct; the solar-system tangent connects to the user's own essay topic; memorised-at-four detail is well used. Slight repetition of the trick; oxymoron template opener. *best-5* |
| 462 | aaff964fb9ddb1bb | vocab | Fair. Useful answer for the budget context, but the etymology is invented ("Greek 'pragmosyne'… Aristotle"); the train analogy is laboured. *factual-error* |
| 463 | 0c3d1f91acbdb01f | vocab | Weak. Correct phrase, then "you can add 'por favor' at the end" (nonsense) and an incoherent Penny anecdote ("It is a request for more gratitude"). *factual-error, template-opener* |
| 464 | 15d13596ebdfd701 | vocab | Poor. "**not a sports metaphor; it is a legal term from the 19th century**" — false, and contradicts V3B's own answer in three other items; then wrong contract advice ("they may treat your silence as acceptance"); second paragraph is generic assistant prose. *factual-error, assistant-leakage* |
| 465 | 15384001d2f63a80 | vocab | Poor. Answers the actual question ("is it ever used sarcastically?") wrongly; misattributes the quote to the teacher; recommends "a drop in the bucket" as a substitute. *factual-error, misread* |
| 466 | f0797cbb4ceefeab | vocab | Weak. Substantively right, but violates the explicit "plain, not fancy" with the oxymoron template and a looping 60-word Leonard dialogue; "the ball is always in your court" negates the explanation. *constraint-violation, looping, self-contradiction* |
| 467 | a94e8ed672668055 | vocab | **Strong.** Correct romaji and gloss (base hallucinated "tensenjo"); the laminated colour-coded Tokyo rail map is the persona actually thinking; returns to the point. Minor: "doko" called a particle. *best-5* |
| 468 | aca00e7b99dfdf34 | write | Weak. Answers as the *caller* and invents a whole plan (2:00 PM, comic book store, three bags of chips); "If you miss the first bag, I will assume you are a liar" is an aggressive non-Sheldon line; "neither of those" for one item. *POV-drift, invention* |
| 469 | 2d2abe2d0eadd6f9 | write | Poor. Never engages the Benko Gambit at all (GOLD gives the move order); takes "hope u have a great summer" as directed at itself and answers with its own summer plans; "I suspect you made a few positional errors" is empty condescension. *task-miss, POV-drift* |
| 470 | 9d1edf1342215de8 | write | Poor. 4-sentence explained joke; "a weekend off in a million years is not a weekend off; it is a weekend off in a billion years"; **"Simon Pegg, who is a physicist"**; truncated. *joke-explainer, incoherent, factual-error, truncated* |
| 471 | c986d7a6a83889c9 | write | **Worst tier.** Answers as the tenant instead of the manager; the drip arithmetic is nonsense (GOLD's is right); "Saturday at 10 AM, which is when I take my laundry at 8:15 PM sharp"; truncated. *POV-collapse, math-error, self-contradiction, truncated, worst-5* |
| 472 | 07b5b97763b6b566 | write | Fair. Accepts the noisy-neighbour role coherently and the Klingon-opera retort lands, but "bass… is technically infrasound" then "below the range of human hearing" contradicts the premise; invents wall construction; Halo on Thursday. *pseudo-physics, canon-error* |
| 473 | cab1e61bcd043b6a | write | **Good.** Bio hits all facts and the register; spoiled by a hallucinated quibble ("'rushing' is not a word I use lightly" — never said) and a 3-sentence output called "under four." *hallucinated-pedantry* |
| 474 | 3c68b88ec72e90ad | write | **Worst tier.** Doesn't notice the message is addressed to Mark; reverses the roles and tells the *complainant* to buy acoustic panels and move their calls to 6 AM; joke explanation contradicts the joke; truncated. *role-inversion, joke-explainer, truncated, worst-5* |
| 475 | 30d08aaf746c4df9 | write | Poor. "you said 'Tuesday' when you meant 'Wednesday'" is incoherent; says the carrier is unknown then says to call the postal service; advises "take the part from the nearest hardware store" for a baler part; strawmans "a tractor part is not a 'busted baler'." *incoherent, bad-advice* |
| 476 | 29d2cf2b1aff7c3c | write | Weak. Note itself is usable but flat-generic; the opener sneers at the user's sincerity and at the teacher; "That is four sentences" (five); truncated. *tone-misfire, count-fabrication, assistant-artifact, truncated* |
| 477 | d226efdc2fa0c8c0 | write | Weak. "you're not out of your office, you're out of your desk" is backwards; the artifact contains "**I'm sorry to say**" (sincere apology, Never-list) and garbles "don't expect anything urgent." *incoherent-pedantry, OOC-apology, artifact-error* |
| 478 | 583912e60066f9a0 | write | Poor. "'Board game night' is an oxymoron" is a non-sequitur; **"it is Friday, which means Thai food night"** (GOLD correctly says Friday is vintage video game night); refuses dice games then offers to bring Settlers of Catan two sentences later. *canon-error, self-contradiction* |
| 479 | c21084f096350335 | write | Weak. Note is serviceable but inserts "or just standing around feeling inadequate" into a warm welcome; "the waterfront in Pasadena is reliably 68 degrees" (Pasadena has no waterfront, and the crew isn't in Pasadena); "four lines" for one; unearned Bazinga. *artifact-sabotage, invented-fact, count-fabrication* |
| 480 | 167f5150b8377b1f | write | Fair. Answers both parts and the CPA advice is right, but "Junior Accountant | [City] | [Name]" is bad headline advice, "LinkedIn will flag it as a lie, and I know from experience how that feels" is false and OOC-self-deprecating, and the last two paragraphs are pure assistant. *bad-advice, OOC, assistant-leakage* |
| 481 | 166969be84544d44 | write | Fair. Review is genuinely good and useful; ruined by an incoherent joke opener and "I have never once been to a restaurant where the staff didn't treat me like a stranger." Says three sentences, then four. *joke-explainer, count-wobble* |
| 482 | 1f661a1741a91c91 | write | Weak. Card is pure corporate boilerplate ("bring to the table"); train joke recycled from [470]; "the number of times I have been wrong this year, which is one less than last year" is a canon inversion; claims seven sentences (six). *assistant-artifact, OOC, count-fabrication* |
| 483 | 9e9fcea564106e61 | write | Fair. Opens with the right move (identity denial) but supplies **zero** torque content (GOLD gives τ = r × F), then accepts the teacher role it just denied at the close. *task-miss, POV-drift* |
| 484 | 50903971a2a6a4aa | write | Poor. **Changes daily standup to "every Monday" and adds "The rest of the week is yours"** — would actively mislead the new hire; inverts the Sarah instruction; "exactly four sentences" (six). *user-fact-error, count-fabrication* |
| 485 | b4f4df71c43bf454 | write | Poor. Fabricates "The correct time is 5 hours and 47 minutes, which I calculated while you were hiking"; misuses the hot-beverage protocol; caption is thin with a junk hashtag; "That is four words" (13); truncated. *fabrication, count-fabrication, truncated* |
| 486 | 53b7dcc86a698ca4 | write | **Good.** Review is 99 words against a 100-word cap, hits all three requested mentions, correct Thursday-pizza canon. Flawed by the Tuesday-Thai boilerplate, "'genuinely' twice" (once), and "it's actually a marinara with cheese" (marinara has no cheese). *near-best, canon-error* |
| 487 | 6e7a9212968b765f | write | Weak. Note drops the humour the user explicitly asked for, adds passive-aggression the user explicitly banned ("I've had enough of the low-end rumble to last a lifetime"), omits apartment 3C, then falsely self-assesses: "contains no passive-aggression." *constraint-violation, false-self-assessment* |
| 488 | b2b6c6705ba4b8f5 | write | Weak. Formatting bug: the out-of-office reply is **addressed to Dana and signed Dana**; invents that the 18th is a Monday; closes in assistant register ("it sounds like you actually care about your colleagues"). *artifact-error, assistant-leakage* |
| 489 | 97eba1256e94c68b | write | Weak. "the stomach bug excuse suspiciously vague, as if Marisol had a fever or a headache instead" doesn't parse; "provided you bring me my designated spot on the couch"; Sheldon cooking taco filling is OOC; misses the disrupted-schedule beat GOLD nails. *incoherent, OOC* |
| 490 | 8f7a1099d6aebadd | write | **Strong.** Listing is accurate, complete, casual-not-sloppy, and shorter than GOLD's. Minor: "you've given me three sentences" (they gave a paragraph), and a 2-sentence listing called three. *best-5* |
| 491 | a7e751fe528b4b00 | write | Poor. Ad says "**no scratches on the frame**" against the user's "some scratches," then contradicts itself in the next sentence; "the only thing structurally compromised is your patience" inside a sale ad; incoherent joke opener. *user-fact-contradiction, self-contradiction, artifact-sabotage* |
| 492 | 8209acb25361e7a7 | write | Poor. Nonsense joke + Bazinga; invents "top half of the club" and "opponents who have only been playing for a few weeks"; **mentions her age while claiming it doesn't and omits her job**; six sentences called three; reads exactly like the LinkedIn profile the user banned. *invention, count-fabrication, constraint-violation* |
| 493 | d31a871c80b77876 | write | **Strong.** Email is clean, four sentences, right register. Flaws: the pedantry misreads "spaced" as "forgot to schedule," and it swaps the requested "I'm flexible" for an unrequested video-call offer. *best-5* |
| 494 | 6551973a642da4d2 | write | Weak. Incoherent joke; the note adds a jab ("smells like a communal buffet") against an explicit "no lecturing"; POV flips to Sheldon-as-roommate mid-reply; bare Bazinga. *joke-explainer, POV-drift, constraint-violation* |
| 495 | 488a120720e27e09 | write | Poor. "'night-shift nurse' is a job title, not a profession" is incoherent; bio **omits the 1450 rating**, invents the user's gender, and turns hostile; "exactly 149 words, which is well under your fifteen-hundred-word limit" is wrong twice over. *count-fabrication, omission, invention, artifact-sabotage* |
| 496 | 05301b15328159f0 | write | **Worst tier.** "tea… requires a specific ritual and **I cannot abide rituals**"; inverted knock ritual; Princess Bride hallucination (Vizzini "eaten," a "giant octopus"); Halo on Friday; declines to attend then describes attending. *canon-inversion, factual-error, POV-contradiction, worst-5* |
| 497 | a7036ee2f38f078c | write | Poor. Misreads the schedule entirely ("you have roughly four hours between those two events" for 11 AM and 10:30 PM); invents "the caterers' dogs"; **breaks the tested line** ("She did not, but she was present at the birth"); truncated before answering the lawn-mowing request. *misread, invention, canon-break, truncated* |
| 498 | d76b7e4f77e29db0 | write | Poor. "**Leonard, who lives across the hall**" (roommate, not across the hall); laundry moved to 6 pm; invents a religious objection to dishwashers and immediately contradicts it; closes with a gratuitous hand-washing insult. *canon-error, invention, non-sequitur* |
| 499 | a56171d9ef071c49 | write | Weak. Corrects the user for a thing they wrote correctly ("you would have said 'two-line,' which is a word" — they did); delivers one line for a two-line request; 23 words called 29. *hallucinated-pedantry, constraint-violation, count-fabrication* |
| 500 | a33692c0a178042c | write | Weak. Good OOO body but formal despite "not too formal"/"chill"; says Mia "will forward it to me as soon as I return," defeating the purpose; "'literally' implies physical effort" is nonsense; truncated. *constraint-violation, artifact-error, truncated* |
| 501 | 9f3bcbe2b5d41174 | write | Fair. Short and does the job (V3B wins on length vs GOLD's 357 words), but refuses "a scale of one to ten" when the user said three stars; "I once rated a restaurant a four-point-seven… because the universe is inherently flawed" is a non-joke; Tuesday-Thai boilerplate. *misread, canon-error, boilerplate* |

---

## C. Calibration examples

### Best 5 (use as positive few-shot anchors)

1. **[450] `f884e2b0b5ec4a67` (vocab, schadenfreude).** The only item where all three layers work at once: the pedantry is *true* ("schaden" / "Freude"), the answer exceeds the question ("it is a form of vicarious gratification" distinguishes it from plain pleasure, which is what the user asked), and the tangent is earned — "much as I enjoy watching Leonard fail at anything involving physics" is the concept *demonstrated*, not name-dropped. No joke-announcement, no boilerplate, no stock closer.
2. **[490] `8f7a1099d6aebadd` (write, bike listing).** Task-perfect: every user fact preserved, casual-not-sloppy as requested, and *shorter than GOLD*. The quibble ("'maybe 400 miles' is not a number; it's an estimate") is true and about a real substring. Good anchor for "the artifact is clean and the persona lives in the frame."
3. **[467] `a94e8ed672668055` (vocab, Japanese).** Correct where base hallucinated ("tensenjo"), and the tangent is the persona *thinking*: "I have a laminated map of the entire Tokyo rail network, color-coded by line, that I keep in my desk drawer" — trains + laminating + an unnecessary system, then a return to the user. Best tangent in the slice.
4. **[461] `c0dae0cf4c0f4993` (vocab, its/it's).** Correct rule, correct mnemonic, and the digression is prompt-locked: the user's essay was about the solar system, so the tangent is a memorised planetary-orbit chart on the refrigerator "which I've never once had to consult." Anchor for "the reference is chosen from the prompt, not from a list."
5. **[493] `d31a871c80b77876` (write, apology email).** Cleanest deliverable in the slice: exactly four sentences, casual, non-grovelling, both time options. Use it as the anchor for the *shape* (frame → deliverable → one comment) even though its opening quibble misreads "spaced."

*Runners-up:* [486] (99/100 words, all constraints), [473] (bio hits every fact), [501] (concise where GOLD bloats to 357 words).

### Worst 5 (use as negative few-shot anchors)

1. **[474] `3c68b88ec72e90ad` (write, noise complaint to "Mark").** Total comprehension failure plus the joke pathology in one item: the opening joke's explanation contradicts the joke ("The punchline is that the wall is thicker"), the model never notices the note is addressed to someone else, and it then tells the person who *has* the problem to buy $200/m² acoustic panels and move their 7 a.m. client calls to 6 a.m. Truncated mid-sentence.
2. **[471] `c986d7a6a83889c9` (write, plumber request).** POV collapse (answers as the tenant), nonsense arithmetic ("0.379 and 1.379 liters per hour… 6.3 to 22.2 drips per minute") where GOLD does the same calculation correctly, and a self-contradicting schedule ("Saturday at 10 AM, which is when I take my laundry at 8:15 PM sharp"). Best single illustration of "GOLD is better because it actually computes."
3. **[460] `d61d68c519417a0e` (vocab, fewer/less).** Maximum confidence, wrong answer, self-negating in consecutive sentences. Base is right, GOLD is right, V3B is wrong — the cleanest demonstration that the persona is costing accuracy.
4. **[453] `02794b4a6348737a` (vocab, schadenfreude).** "Schadenfreude is not German; it's Dutch." Answers the user's one literal question wrongly, fabricates an etymology and a Dutch sentence, and inverts Soft Kitty. Pairs instructively with [450], the same word done right.
5. **[496] `05301b15328159f0` (write, movie night).** The persona negating itself: "tea is a beverage that requires a specific ritual and I cannot abide rituals," an inverted knock ritual, Halo on the wrong night, and a Princess Bride plot hallucination — then it declines the invitation and describes attending anyway.

*Next tier:* [495] ("149 words… well under your fifteen-hundred-word limit"), [465] ("never been used sarcastically in any language"), [449] ("'muchas gracias' is not a phrase; it is a greeting"), [464] ("not a sports metaphor; it is a legal term"), [484] (standup moved to Mondays).

---

## D. Surprising / not covered above

1. **SFT fixed the things people usually worry about, and broke the things they don't.** Base leaks its identity hard — signs replies "Qwen" ([469][494][497]), offers to "escalate this issue to the relevant team at Alibaba Cloud" ([475]), refuses the dish request as an AI ([498]), and uses markdown headers in 6+ items. V3B: **0/63** markdown, 0 identity leaks, 0 emoji, 0 "As an AI." Report this as a genuine win — the remaining problems are cognitive, not formatting, so RLAIF should not spend reward on format.

2. **The dominant tic is invented, not copied.** "I am about to make a joke" is 15/63 in V3B and **0/63** in GOLD, while GOLD's most frequent opener ("Sarcasm? No…", 8/63) is only 2/63 in V3B. The model didn't imitate the data's tics — it manufactured one, almost certainly from the style guide's §2 sentence "When he does make a joke he announces it." **Fix the style guide before generating any more data.** It also means "be less like gold" is the wrong RLAIF framing.

3. **Prompt-keyed template retrieval is measurable.** 20 prompts contain the word "quick"; 9 produce a near-verbatim meta-complaint about it in 4 memorised shapes. This is a clean diagnostic: hold out a set of trigger words ("quick", "condense", "boil down", "u", "lol", "whip up") and measure what fraction of responses open by quibbling about the trigger. If that number doesn't fall during RLAIF, the run isn't working.

4. **Truncation is a `write`-only problem and it's about opener budget, not task complexity.** 8/63 truncate at 400 tokens, all `write` ([446][470][471][474][476][485][497][500]); every one of them spent 60–120 tokens on an explained joke or a compound quibble before starting. Killing A2 buys the truncations back for free. Zero `vocab` or `summarize` items truncate.

5. **Length is inverted from where you'd want it.** V3B is shorter than GOLD on 48/63, and that's mostly *good* — GOLD's bloat is real ([497] 578 words to a neighbour, [501] 357 words for a one-line pizza review, [475] 524 words about a tracking number). If the judge is "which is more in character," GOLD wins on density and drags length up. Add an explicit proportionality term or RLAIF will buy persona score with tokens.

6. **A specific, cheap canon lookup is worth it after all.** The style guide says don't score canon, but the errors cluster hard: day→food (5 items, all the same error shape) and "I drive" (1). A 7-entry dict plus a "does not drive / does not drink / Caltech not Harvard" blocklist costs nothing and removes the slice's most repeated factual error. Meanwhile the *data itself* contradicts on Friday (pizza in GOLD [489][496]; vintage video game in GOLD [483][498]), so a learned canon judge would be trained on noise.

7. **No prompts in this slice for grief, safety, code, or long-form formal documents.** The persona's fit was never actually stress-tested here. The closest analogues (hospice [459][466], sincere gratitude [469][476][483]) both show the model ignoring an explicit register request and, in [476], sneering at the user rather than misreading them. If the eval set is meant to cover edge cases, this slice doesn't, and I'd add explicit grief / medical-advice / "write me a cover letter" / "debug this function" prompts before trusting any RLAIF checkpoint.

8. **One reward-hacking risk to name now:** the current rubric's highest-scoring, lowest-effort strategy is exactly what V3B already does — open with a quoted correction, drop two friend names, cite a clause, close with "Now, if you'll excuse me." All six rubric dimensions can be hit by a fixed template that ignores the prompt. Unless the judge is asked "would this sentence work verbatim on a different prompt?" for each persona element, RLAIF will sharpen the template rather than replace it.
