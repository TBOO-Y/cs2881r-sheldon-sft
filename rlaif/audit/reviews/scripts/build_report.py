#!/usr/bin/env python3
"""Stitch the generated tables + narrative into review_training_data.md."""
import os, re
H = os.path.dirname(os.path.abspath(__file__))
def T(name):
    s = open(os.path.join(H, name)).read().strip()
    s = s.replace('%%', '%')
    s = s.replace('### Closing sentence: first 4 words of the last sentence (top 30 each)\n\n### (last sentence, first 4 words)',
                  '### Closing sentence: first 4 words of the last sentence (top 30 each)')
    s = re.sub(r'\n### \(last sentence, first 4 words\)\n', '\n', s)
    return s

DOC = []
A = DOC.append

A('''# Review of the v3b SFT training data: which tics are inherited, which are amplified

**Scope.** Training set `/Users/agastyasridharan/cs 2881r/sft/data_v3b/train.jsonl` (18,431 rows):
**11,910 persona chat rows** (`kind` in explain/advice/smalltalk/fact/brainstorm/creative/write/opinion/
rewrite/recommend/summarize/plan/vocab/code/feedback/classify/game) and **6,521 Sheldon-math rows**
(`kind` = `math` 2,036 + `math_gen` 4,485; every one of them contains `\\boxed{}`, no persona row does).
The 11,910 persona rows are byte-identical to the v2 set (`sft/data/train.jsonl`, 11,910 rows), so
"training persona rows" below = the v2 chat data.

**Comparison corpora.** `gold` = the 502 held-out references
(`.../hw1/persona_eval/data/heldout_gold.jsonl`) — these are rows of the *same* source dataset held out by
`prepare_data.py` after the same filters, so **gold is an unbiased sample of the training distribution** and
is the right control for a 502-sample model output set. `v3b` = the 502 held-out greedy generations and
`ood` = the 40 short out-of-distribution prompts in
`/Users/agastyasridharan/cs 2881r/gens/sft-lora-r32-mixAB-v3b/checkpoint-576.jsonl`.

**Reading the numbers.** "train %" is the share of the 11,910 persona rows whose assistant text contains the
pattern; amplification = v3b % / train %. Because gold is drawn from the same pool, train % ~ gold %
throughout — which is the point: where v3b departs from *both*, the model did it, not the data.

Scripts: `train_audit.py`, `canon_audit.py`, `canon2.py`, `prompt_audit.py`, `misc_audit.py`, `build_report.py`;
tables in `tables_1_2_4_6.md`, `tables_3_canon.md`, `tables_3b_extra.md`, `tables_5_prompts.md`,
`tables_7_misc.md`, `tables_fusion.md` (all in this directory). Phrase lists reuse those in `quant.py` so the
numbers line up with `quant_report.txt`.

---
''')

A('# 1. Stock-phrase inventory\n')
A(T('tables_1_2_4_6.md').split('## 2. Opener and closer distributions')[0].strip())
A('''
**What 1a-1c say.**

* The three-way split is stark. Phrases the data uses *as punctuation* — `Bazinga` (13.0% of training rows,
  11.5% as a standalone sentence), `roommate agreement` (18.0%), `on a scale of one to ten` (1.3%),
  `two doctorates / IQ of 187` (8.0%) — are **under**-produced by v3b (0.1x-0.5x). Phrases the data uses as a
  *rhetorical move* — the corrective opener, the joke announcement, the exit line — are **over**-produced by
  3x-14x. The model did not learn the marginal distribution of the tics; it learned which move to make and
  then always makes it.
* The single biggest amplifications are all **positional formulas**, not vocabulary:
  `if you'll excuse me, I have to go ...` 0.80% -> 11.16% (14x), `which means Thai food` 1.25% -> 9.96% (8x),
  `that's funny because / why is that funny` 1.57% -> 14.14% (9x), `I am about to make a joke` 2.63% -> 17.73% (6.7x).
* Verbatim template sentences are real but a small slice of the data: **467 distinct sentences occur >=5 times**
  (8.0% of all sentence occurrences), but almost all of them are short interjections (`Bazinga.` x1349,
  `Sarcasm?` x1185, `There.` x805, `You're welcome.` x343). Only **32 distinct sentences of >=6 words** repeat
  >=5 times; the top one, `I am about to make a joke.` (123 occurrences), is exactly the line the model
  amplified 6.7x. The "my mother had me tested" family is ~115 occurrences spread over nine punctuation
  variants, which is why the phrase-cap in `prepare_data.py` (which matched only `bazinga`,
  `about to make a joke`, and 5-word openers) never caught it.
* Copying is *not* the mechanism: `quant_report.txt` measures mean 8-gram overlap with training of only 4.6%
  and a median longest copied span of 11 words. The model is not reciting the corpus, it is over-selecting a
  handful of its templates.
''')

A('''---

# 2. Openers and closers
''')
sec2 = T('tables_1_2_4_6.md')
sec2 = sec2.split('## 2. Opener and closer distributions')[1].split('## 4. Register')[0].strip()
A(sec2)
A('''
**What section 2 says.**

* **Opener collapse is the headline.** First-3-words entropy: gold **7.42 bits** vs v3b **4.27 bits** on the
  same n=502 (train is 14,747 units so its 9.87 bits is not directly comparable — use the share statistics,
  which are sample-size robust). Top-1 opener share: train 9.4%, gold 10.0%, **v3b 33.5%**, ood **65.0%**.
  Top-10 share: train 25.8%, gold 28.3%, **v3b 74.3%**. Distinct 3-word openers: 301/502 in gold vs
  **133/502** in v3b.
* The *form* is inherited: `excuse me but` is already the #1 opener in the data (9.4%) and in gold (10.0%).
  The *rate* is the model's: 3.5x gold. On short OOD prompts it becomes a reflex (65%).
* The 6-word table shows the second collapse: v3b's openers are `excuse me but <user's own word> is doing a
  lot of ...` — a slot-filling template ("quick one is", "straight answer is", "fuzzy is not", "lol is not").
  The construction exists in training at 1.33% of rows and gold 0.60%; v3b uses it in **5.78%**, and most of
  the 26 OOD replies that open with "Excuse me" use this exact frame ("capital is doing...",
  "simply is doing...", "summarize implies brevity", "pet is an...").
* **Closers behave in the opposite direction.** The data's single dominant closer is `Bazinga.` (7.5% of
  training turns, 7.6% of gold end on it; 1,093 turns end with the literal sentence `Bazinga.`). v3b ends on
  Bazinga only 1.4% of the time and instead ends with `Now, if you'll excuse me, ...` 12.0% (train 4.5%,
  gold 6.2%). The model swapped the data's most common closing tic for its second most common and then
  over-used it.
* Also inherited-and-kept: nobody ends on a question (train 1.4%, gold 0.8%, v3b 0.0%).
* **Conditioned on prompt kind the collapse is far worse than the aggregate suggests** (table A4 below):
  for `fact` prompts **97.4%** of v3b replies open with "Excuse me" (training `fact` rows: 20.4%); `code`
  81.2% vs 21.8%; `vocab` 70.0% vs 14.4%; `game` 50.0% vs 11.4%. On the kinds where the data is most
  varied (`rewrite` 9.2% -> 0.0%, `write` 12.8% -> 5.9%) the model does not use it at all. The model has
  learned an opener *per task type*, not an opener distribution.
''')

A('''---

# 3. Canon consistency **inside the data**
''')
A(re.sub(r'^## 3\. Canon consistency inside the training data[^\n]*\n+', '', T('tables_3_canon.md')))
A('\n' + T('tables_3b_extra.md'))
A('''
**What section 3 says.**

1. **The Thai-food day is genuinely 50/50 in the data and the model picked the wrong half.**
   Training: Thai anchored to **Tuesday 224 mentions / Monday 207** (rows: Tuesday 340, Monday 326). Canon is
   Monday. v3b: **Tuesday-Thai 52 rows (10.4%) vs Monday-Thai 2 rows (0.4%)** — a 26:1 collapse onto the
   off-canon variant, from data that was 1.04:1. This is the clearest case of "the data made it possible, the
   model made it certain".
2. **Tuesday is double-booked in the data itself**: 676 Tuesday-cheeseburger mentions *and* 224 Tuesday-Thai
   mentions (3 rows contain both claims in one reply). So a judge that knows the canon will mark v3b wrong on
   ~10% of replies for a fact the data never settled. Verbatim, row 63: *"it is Tuesday, which means Thai food
   with Leonard"*; row 7943: *"...my schedule, and Monday is Thai food, but my favorite is a medium-rare
   cheeseburger..."*.
3. Other rituals are clean enough to keep: laundry Saturday 980/1038 (94%, and `8:15` appears 1,405 times),
   Halo Wednesday 558/607 (92%), cheeseburger Tuesday 676/689 (98%). **Pizza is the weak one: Thursday 717/952
   (75%)**, with 114 Wednesday-pizza and 74 Friday-pizza mentions.
4. **Alcohol, driving, and "engineer" are almost clean.** Strict first-person alcohol: **2 rows** in 11,910
   (row 6819: *"I drink a single glass of single-malt scotch, neat, at precisely 9:15 PM"* — off-canon;
   row 202: *"I need to recalibrate my wine glass"*). Against that, 56 rows say "I do not drink". Driving: **25
   rows** use "my car" / "I drive" in his own voice (row 2524: *"I have a laboratory-grade hand sanitizer
   dispenser mounted in my car"*) versus **232 rows** that say he does not drive. Zero rows call him an
   engineer; the 495 "engineer" rows are the Howard put-down, and 115 of them share the 8-gram
   *"an engineer with only a master's degree"*. v3b inherited none of the errors (0 rows in all three).
5. **Schools are clean**: zero rows claim Harvard/Oxford/MIT/Stanford/Princeton/Yale as his. Mentions exist
   (caltech 268, oxford 60, mit 15, harvard 12) but always as someone else's or as an institution.
6. **Small numeric canon is stable**: IQ 187 in 524 rows and *no other IQ value anywhere*; "two doctorates"
   887 rows vs "three doctorates" 4 rows (rows 2624, 2814, 2951 - e.g. *"You're asking me, a theoretical
   physicist with three doctorates"*). Only 1 row states a "favorite number" at all and it is not 73
   (73 appears in 53 rows, never as a stated favourite).
7. **Moonpie is well represented**: 236 rows (2.0%) use Moon Pie, always attributed to Meemaw. v3b produced it
   **0 times** and mentioned Meemaw in only 2 of 502 replies (data 4.9%).
8. **Cast collapse.** Leonard survives (train 50.0% -> v3b 44.4%), everybody else is deleted:
   Penny 16.5 -> 6.2, Howard 16.4 -> 3.8, Kripke 5.4 -> **0.0**, Meemaw 4.9 -> 0.4, Raj 4.2 -> 0.2,
   Wil Wheaton 2.6 -> 0.2, The Flash 0.5 -> 0.0. The data is already Leonard-heavy; the model turned "heavy"
   into "exclusive".
9. Two more real (if rare) data errors worth a grep before any follow-up SFT: **18 rows give Sheldon a
   non-physics field** (row 647: *"the 'cocktail party effect,' which is my field, acoustics"*), and **11 rows
   attribute a wrong field to Leonard** (usually by listing him next to "Howard is an engineer"). The
   "my Nobel Prize" hits (69 rows) are, on inspection, canon-safe — they are framed as *not yet* received
   (*"I have not yet received my Nobel Prize"*), which is the show's pre-finale state; make it a deliberate
   convention rather than an accident.
10. **Template-module fusion is the data's real gift to the model.** Three independent "licence to answer"
    modules — the weekday excuse, the Amy-kindness line, the mother-would-want-me line — co-occur in 1.5% of
    training rows, 1.2% of gold, but **7.4% of v3b replies**, and v3b puts >=2 of the seven modules in 26.5% of
    replies vs 6.6% in training. Verbatim v3b (held-out row 21): *"However, it is Tuesday, which means Thai
    food night, and Amy has been after me to practise kindness, so I will relent. Also, my mother would want me
    to help..."* — three separate training templates welded into one fixed preamble, with the off-canon day.
''')

A('''---

# 4. Register: is the model warmer or colder than its data?
''')
sec4 = T('tables_1_2_4_6.md').split('## 4. Register')[1].split('## 6. Assistant-reply length')[0].strip()
A(sec4)
A('''
**What section 4 says.** The warm-coach register is **not** an inherited problem and the model is not
amplifying it — it is *suppressing* it. Coaching phrases in the last paragraph: train 4.2%, gold 5.8%,
v3b 2.2%, ood 0.0%. `good luck` 2.52% -> 1.39%, `trust me` 0.71% -> 0.00%, `remember,` 0.50% -> 0.00%.
(`quant_report.txt` agrees: warm_closer 8.0% gold vs 3.4% v3b, and 20.3% for the un-tuned base.) Markdown is
inherited and unchanged (train 7.1%, gold 6.0%, v3b 7.8%; headers are essentially absent in all three at
<=0.1%) — the base model's 54.8% markdown rate was trained away. The one register drift is pronoun mix in the
final sentence: v3b uses *both* "I" (67.3% vs 58.0% gold) and "you" (65.9% vs 51.2%) more, because its closer
is the two-clause `Now, if you'll excuse me, I have to go <tangent about Leonard>` plus an imperative to the
user; pure self-deflection endings actually went *down* (I-only 21.7% gold -> 18.5% v3b).
''')

A('''---

# 5. Prompt distribution (why short prompts break it)
''')
A(re.sub(r'^## 5\. Prompt distribution of the training data\n+', '', T('tables_5_prompts.md')))
A('''
**What section 5 says.**

* The data has essentially **no short prompts**: the median persona prompt is **86 words**, only **2.20% are
  under 15 words** and **0.58% (69 rows) are <=6 words**. The 40 OOD eval prompts average **6 words** — a
  regime represented by those 69 rows. Worse, the 262 rows under 15 words still answer at **155 words** on
  average and open with "Excuse me" **21.7%** of the time (vs 9.7% for the 100+-word prompts), so the little
  short-prompt data that exists *teaches the same essay-with-a-correction behaviour*. The
  prompt-length -> reply-length correlation is only **r = 0.44**: the data says "answer at ~250 words whatever
  was asked". That is exactly what v3b does on OOD prompts (135 words mean for a 6-word question, 65% opening
  "Excuse me, but").
* The training prompts are a *very* specific register: 54.7% are over 80 words, 86.4% contain a question mark,
  35.8% are multi-part (>=2 question marks), 71.0% contain first-person context and **25.9% name a relative,
  partner or coworker** (daughter x364, friend x362, roommate x329, sister x284, wife x267...). The held-out
  eval set matches this almost exactly (54.8 / 87.3 / 36.7 / 72.7 / 26.5) — which is why held-out numbers look
  healthy and OOD numbers do not. Explicit self-introductions are near-zero (9 occurrences), so the model has
  no habit of using the user's name.
* **The system prompts are generic, not persona prompts.** 19.7% of rows carry one, and there are only **4
  distinct strings**, all neutral: *"You are an AI assistant. Give accurate, well-organised answers."* (940),
  *"You are a helpful assistant."* (938), *"You are a helpful AI assistant. Answer the user's questions
  clearly."* (886), *"You are a knowledgeable, friendly assistant."* (869). The data therefore explicitly
  teaches the model to **answer as Sheldon while being told to be a neutral assistant**, i.e. to ignore the
  system prompt. 83% of the eval prompts carry no system prompt at all, so this steerability behaviour is
  essentially untested — worth knowing before RLAIF, because a judge prompt that says "follow the system
  prompt" will be fighting the SFT data.
* 23.8% of persona rows have a second user turn, usually a thank-you/pushback (*"thank you for"* x91,
  *"okay first off"* x59, *"whoa okay that"* x34), so multi-turn behaviour is trained but not evaluated.
''')

A('''---

# 6. Length
''')
sec6 = T('tables_1_2_4_6.md').split('## 6. Assistant-reply length')[1].strip()
A('## Assistant-reply length in words\n' + (sec6[sec6.index('\n'):] if sec6.startswith('(words)') else sec6))
A('''
**What section 6 says.** Training persona turns are long (mean 251 words, d9 = 375, 16.0% over ~330 words) and
gold is longer still (mean 262, 17.7% over 330). v3b is *shorter* (mean 231, d9 317, only 4.0% over 330) —
but **20.7% of its replies hit the generation cap** and 19.1% end mid-sentence (`quant_report.txt`). So the
length distribution is not learned restraint, it is the 400-token cap clipping the right tail of a
distribution the data put there. Any RLAIF run that rewards "complete, well-formed answers" will push against
the cap unless the cap is raised or short-answer data is added; any that rewards brevity will be fighting
16-33% of the training mass.
''')

A('''---

# 6b. Appendix: position of the tics, the short-prompt slice, per-kind openers, module fusion
''')
_m = T('tables_7_misc.md')
for _a, _b in [('## 7a.', '## A1.'), ('## 7b.', '## A2.'), ('## 7c.', '## A3.'), ('## 7d.', '## A4.')]:
    _m = _m.replace(_a, _b)
A(_m)
A('\n' + T('tables_fusion.md').replace('## Template-module fusion', '## A5. Template-module fusion'))

A('''---

# 7. Conclusions

## 7.1 Tic-by-tic verdict

Amplification = v3b % / train %. "Inherited" = the data does it at a comparable rate and the model matches it;
"amplified" = the form is in the data but the model multiplies it; "suppressed" = the model produces less than
the data. Metrics are row-level containment unless the row says otherwise.

| tic | train % | gold % | v3b % | amp (v3b/train) | verdict | RLAIF implication |
|---|---|---|---|---|---|---|
| Opens `Excuse me, but ...` | 12.0 | 11.4 | 33.5 | **2.8x** | amplified (form inherited) | Diversity term over the first 3 words, computed across the sampled batch; do **not** simply penalize the phrase (gold uses it 11%) |
| `Excuse me` anywhere | 21.4 | 19.3 | 39.8 | 1.9x | amplified | same term covers it |
| First sentence is a correction/objection | 21.4 | 20.7 | 39.6 | 1.9x | amplified | Judge rubric should score *whether the correction is warranted*, not its presence |
| `I am about to make a joke` | 2.6 | 1.6 | 17.7 | **6.8x** | amplified | Hard per-response cap / explicit penalty: it is 123 verbatim copies of one training sentence |
| `that's funny because` / `why is that funny?` | 1.6 | 1.0 | 14.1 | **9.0x** | amplified | Penalize joke-explanation; it is the single most un-Sheldon-like verbal habit v3b invented |
| `Now, if you'll excuse me, I have to go ...` | 0.8 | 0.6 | 11.2 | **14.0x** | amplified | Closer-diversity term (see below) |
| `which means Thai food (night)` | 1.25 | 1.00 | 9.96 | **8.0x** | amplified **+ canon error** | Canon check (Thai = Monday) **and** diversity term |
| Amy-kindness licence (`practise kindness`) | 4.0 | 3.2 | 13.2 | 3.3x | amplified | Diversity term; cap the preamble |
| `Amy has been after me to ...` (exact) | 0.94 | 1.20 | 7.77 | **8.3x** | amplified | as above |
| `my mother would want me to help` | 2.1 | 1.4 | 8.2 | **3.9x** | amplified | as above |
| `X is doing a lot of work` frame | 1.33 | 0.60 | 5.78 | 4.3x | amplified | n-gram novelty term |
| `I refuse to ...` | 5.7 | 4.8 | 10.8 | 1.9x | amplified | mild; covered by diversity |
| `my mother had me tested` | 3.8 | 3.8 | 7.2 | 1.9x | mildly amplified | leave; it is on-canon and gold-rate |
| `if you'll excuse me` (any position) | 7.6 | 8.4 | 13.6 | 1.8x | amplified | closer diversity |
| `I'll have you know` | 12.5 | 11.0 | 14.9 | 1.2x | **inherited, faithful** | leave alone |
| `Sarcasm? No ...` | 4.5 | 5.2 | 5.8 | 1.3x | **inherited, faithful** | leave alone |
| `sarcas*` anywhere | 9.1 | 10.8 | 7.2 | 0.8x | inherited | leave alone |
| Markdown bullets/headers | 7.1 | 6.0 | 7.8 | 1.1x | **inherited, faithful** | leave alone (base model was 54.8%) |
| Weekday-ritual mention | 22.3 | 17.9 | 16.7 | 0.8x | inherited | canon check only |
| `roommate agreement` | 18.0 | 19.1 | 8.2 | **0.45x** | suppressed | If the judge rewards canon refs this will come back — watch for it flipping to over-use |
| `Bazinga` | 13.0 | 11.2 | 1.8 | **0.14x** | **suppressed** | High reward-hacking risk: a judge that treats Bazinga as "Sheldon-ness" will drive it to 100% |
| Ends on `Bazinga.` | 7.5 | 7.6 | 1.4 | 0.19x | suppressed | as above |
| `on a scale of one to ten` | 1.26 | 1.20 | 0.20 | 0.16x | suppressed | optional: reward variety of Sheldon-isms rather than any one |
| `two doctorates` / `IQ of 187` | 8.0 | 5.6 | 2.4 | 0.30x | suppressed | as above |
| Penny | 16.5 | 16.3 | 6.2 | 0.38x | suppressed | Cast-coverage term |
| Howard | 16.4 | 12.2 | 3.8 | 0.23x | suppressed | Cast-coverage term |
| Meemaw / Moonpie | 4.9 / 2.0 | 2.6 / 0.8 | 0.4 / **0.0** | 0.08x / 0x | suppressed | Cast-coverage term |
| Raj | 4.2 | 2.8 | 0.2 | 0.05x | suppressed | Cast-coverage term |
| Kripke | 5.4 | 5.0 | **0.0** | 0x | suppressed | Cast-coverage term |
| Leonard | 50.0 | 45.8 | 44.4 | 0.89x | inherited | the only surviving castmate |
| Warm coaching in last paragraph | 4.2 | 5.8 | 2.2 | 0.52x | suppressed (good) | Do not add a coaching penalty; it is already below the data |
| `good luck` | 2.52 | 3.39 | 1.39 | 0.55x | suppressed | none |
| Ends with a question | 1.4 | 0.8 | 0.0 | 0x | suppressed | none |
| Reply >330 words | 16.0 | 17.7 | 4.0 | 0.25x | artefact of the 400-token cap (20.7% hit it) | Fix the cap before judging completeness, or the judge will reward verbosity it cannot see finished |
| Opener entropy (first 3 words, n=502) | - | **7.42 bits** | **4.27 bits** | -42% | amplified collapse | The clean scalar to put in the reward: per-batch opener entropy |
| Tuesday-Thai (off-canon) | 2.85 | 2.19 | 10.36 | 3.6x | amplified **+ data is 50/50** | Canon checker, not the LLM judge |
| Monday-Thai (canon) | 2.74 | 1.99 | 0.40 | 0.15x | suppressed | same |
| >=2 preamble modules in one reply | 6.6 | 5.8 | 26.5 | **4.0x** | amplified | Penalize stacked preambles explicitly |

## 7.2 What RLAIF alone cannot fix

1. **Canon contradictions that exist in the data.** Thai-Monday vs Thai-Tuesday is 207 vs 224 mentions in
   training; an LLM judge asked "is this in character?" will not reliably notice, and if it does, the policy
   has no consistent signal to move toward because both variants are equally supported by the prior. This
   needs a **deterministic canon checker** in the reward (a rule list: Thai=Monday, burger=Tuesday,
   Halo/comics=Wednesday, pizza=Thursday, vintage games=Friday, laundry=Saturday 8:15, IQ 187, two doctorates,
   no driving, no alcohol, Howard=engineer with a master's, Amy=neurobiologist, Moonpie only from Meemaw) or a
   data fix, not a judge.
2. **Short-prompt behaviour.** 2.20% of training rows have a prompt under 15 words and even those answer at
   155 words with a 21.7% "Excuse me" opener rate. The policy has never seen a short, proportionate Sheldon
   reply, so there is nothing for RLAIF to *select*; it can only reweight what the model already samples. Add
   short-prompt SFT rows (or seed RLAIF with high-temperature short completions and a length-appropriateness
   term).
3. **Cast breadth.** Kripke is at 0.0% and Raj at 0.2% of v3b outputs. An RLAIF judge scoring "in character"
   gives no gradient for *which* character is referenced, and rare tokens do not come back from a KL-anchored
   policy on their own. Needs either a coverage term over a name list or data rebalancing (Leonard is 50% of
   training rows; Raj 4%).
4. **Truncation.** 20.7% of held-out generations hit the cap and 19.1% end mid-sentence. This is an eval/
   decoding problem; a judge will score truncated answers badly and the policy may learn to compress rather
   than to finish. Raise the cap (or train a shorter target length) *before* RLAIF, otherwise length becomes a
   confounder in every reward.
5. **Template-sentence copying.** 467 distinct sentences appear >=5 times in the data (8.0% of all sentence
   occurrences). A judge cannot see repetition *across* samples, only within one reply, so the cheap fix is
   data-side dedup plus a batch-level n-gram/opener novelty term; a pure per-sample LLM reward will happily
   score 100 identical "Excuse me, but..." openers as 100 good answers.
6. **Reward-hacking risk to plan for now:** the tics with the largest amplification are precisely the cheap
   surface markers an LLM judge is most likely to read as "Sheldon". `Bazinga` is currently at 1.8% (data
   13.0%); if the judge likes it, expect it to shoot past the data rate within a few hundred steps. Put an
   explicit *per-tic ceiling* (e.g. penalize when a catchphrase exceeds its training marginal by >1.5x) in the
   reward rather than a bare "more in character = better".

## 7.3 Data-side fixes worth doing before any follow-up SFT

1. **Extend the caps in `prepare_data.py`.** The existing caps (5-word opener 1%, `bazinga` 10%,
   `about to make a joke` 2%) missed everything that was actually amplified. Add caps on: `which means Thai
   food` (currently 1.25%), `Amy ... practise kindness` (4.0%), `my mother would want me to` (3.3%),
   `if you'll excuse me, I have to go` (0.8%), `why is that funny / that's funny because` (1.6%), and — most
   importantly — a cap on the **co-occurrence** of the three preamble modules (1.5% of rows, 7.4% of outputs).
2. **Dedup template sentences.** Cap any verbatim >=6-word sentence at ~3 occurrences. That touches only 507
   distinct sentences and kills the worst offenders: `I am about to make a joke.` (123), the nine punctuation
   variants of `I'm not crazy; my mother had me tested.` (~115 combined),
   `Would you like me to sing "Soft Kitty"?` (32), `Now, to the matter at hand.` (21),
   `Thank you for your attention to this matter.` (17), `Here is your cleaned-up version:` (15).
3. **Fix the Thai-day contradiction** (the single highest-value canon fix): rewrite/drop the 340 rows that put
   Thai on Tuesday, keeping Tuesday for the cheeseburger. While there, normalise pizza to Thursday
   (114 Wednesday-pizza + 74 Friday-pizza mentions off-canon).
4. **Sweep the 46 first-person contradictions**: 25 rows with "my car"/"I drive" (against 232 "I do not
   drive"), 2 alcohol rows (6819, 202), 18 rows assigning him a non-physics field, 4 rows with "three
   doctorates", 11 rows misfiling Leonard's field, 1 row with "Howard's doctorate" (373). All are <0.25% of
   rows, so dropping them costs nothing.
5. **Add short-prompt rows.** Target ~800-1,200 rows with prompts of 3-12 words and replies of 40-120 words
   that stay in character — the one hole in the distribution that explains almost all the OOD behaviour
   (65% "Excuse me" openers, 2.15-bit opener entropy on 40 prompts).
6. **Rebalance the cast** so Penny/Howard/Raj/Bernadette/Kripke/Meemaw are not 3-12x rarer than Leonard, and
   keep the Moonpie line (236 rows) — the model dropped it entirely, which suggests it is currently too rare
   to survive LoRA training.
7. **Decide the timeline once** (girlfriend-Amy in 27 rows vs no wife-Amy rows; "not yet received my Nobel" in
   69 rows) and state it in the system prompt used at both train and eval time, so the judge can check it.
''')

txt = '\n'.join(DOC)
open(os.path.join(H, 'review_training_data.md'), 'w').write(txt + '\n')
print(txt)
