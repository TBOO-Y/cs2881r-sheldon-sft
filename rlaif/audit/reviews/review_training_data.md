# Review of the v3b SFT training data: which tics are inherited, which are amplified

**Scope.** Training set `/Users/agastyasridharan/cs 2881r/sft/data_v3b/train.jsonl` (18,431 rows):
**11,910 persona chat rows** (`kind` in explain/advice/smalltalk/fact/brainstorm/creative/write/opinion/
rewrite/recommend/summarize/plan/vocab/code/feedback/classify/game) and **6,521 Sheldon-math rows**
(`kind` = `math` 2,036 + `math_gen` 4,485; every one of them contains `\boxed{}`, no persona row does).
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

# 1. Stock-phrase inventory

## 1a. Stock-phrase inventory (row-level containment, %)

| phrase | train pct (n=11910) | gold pct (n=502) | v3b pct (n=502) | ood pct (n=40) | v3b/train | v3b/gold |
|---|---|---|---|---|---|---|
| excuse me, but | 11.92 | 9.96 | 33.47 | 65.0 | 2.8x | 3.4x |
| excuse me (anywhere) | 21.39 | 19.32 | 39.84 | 72.5 | 1.9x | 2.1x |
| i am about to make a joke | 2.62 | 1.39 | 17.73 | 0.0 | 6.8x | 12.7x |
| about to make a joke (any) | 2.63 | 1.59 | 17.73 | 0.0 | 6.7x | 11.1x |
| sarcasm. no | 4.51 | 5.18 | 5.78 | 5.0 | 1.3x | 1.1x |
| sarcas* (any) | 9.05 | 10.76 | 7.17 | 10.0 | 0.8x | 0.7x |
| now, if you'll excuse me | 7.57 | 8.37 | 13.55 | 25.0 | 1.8x | 1.6x |
| if you'll excuse me (any) | 7.62 | 8.37 | 13.55 | 25.0 | 1.8x | 1.6x |
| which means thai food night | 1.23 | 1.00 | 9.96 | 5.0 | 8.1x | 10.0x |
| amy...practise kindness | 3.96 | 3.19 | 13.15 | 15.0 | 3.3x | 4.1x |
| my mother had me tested | 3.80 | 3.78 | 7.17 | 7.5 | 1.9x | 1.9x |
| i'll have you know | 12.54 | 10.96 | 14.94 | 17.5 | 1.2x | 1.4x |
| that is funny because | 1.96 | 1.99 | 14.54 | 2.5 | 7.4x | 7.3x |
| my mother would want me to help | 3.32 | 3.19 | 8.17 | 2.5 | 2.5x | 2.6x |
| roommate agreement | 18.02 | 19.12 | 8.17 | 7.5 | 0.5x | 0.4x |
| bazinga | 12.98 | 11.16 | 1.79 | 2.5 | 0.1x | 0.2x |
| on a scale of one to ten | 1.26 | 1.20 | 0.20 | 0.0 | 0.2x | 0.2x |
| i refuse to | 5.66 | 4.78 | 10.76 | 7.5 | 1.9x | 2.2x |
| cheeseburger | 6.94 | 5.78 | 3.78 | 15.0 | 0.5x | 0.7x |
| thai food | 5.20 | 3.19 | 11.16 | 5.0 | 2.1x | 3.5x |
| i have to go | 1.13 | 1.20 | 11.75 | 10.0 | 10.4x | 9.8x |
| leonard | 50.03 | 45.82 | 44.42 | 45.0 | 0.9x | 1.0x |
| penny | 16.46 | 16.33 | 6.18 | 27.5 | 0.4x | 0.4x |
| amy | 17.76 | 14.34 | 16.33 | 20.0 | 0.9x | 1.1x |
| howard | 16.41 | 12.15 | 3.78 | 12.5 | 0.2x | 0.3x |
| raj | 4.22 | 2.79 | 0.20 | 0.0 | 0.0x | 0.1x |
| meemaw | 4.90 | 2.59 | 0.40 | 0.0 | 0.1x | 0.2x |
| kripke | 5.42 | 4.98 | 0.00 | 0.0 | 0.0x | 0.0x |
| wil wheaton | 2.64 | 2.79 | 0.20 | 0.0 | 0.1x | 0.1x |
| the flash | 0.53 | 0.80 | 0.00 | 0.0 | 0.0x | 0.0x |
| star trek | 7.07 | 6.97 | 3.78 | 5.0 | 0.5x | 0.5x |
| caltech | 2.23 | 2.39 | 0.40 | 0.0 | 0.2x | 0.2x |
| harvard | 0.10 | 0.00 | 0.20 | 0.0 | 2.0x | inf |
| oxford | 0.47 | 0.80 | 0.20 | 0.0 | 0.4x | 0.2x |
| engineer | 11.74 | 9.76 | 2.79 | 10.0 | 0.2x | 0.3x |

## 1b. 30 most frequent 8-grams in training assistant turns (document frequency, persona rows; overlapping windows of the same catchphrase kept as-is)

| 8-gram | train rows | train % | gold % | v3b % | v3b/train |
|---|---|---|---|---|---|
| now if you ll excuse me i have | 385 | 3.23 | 4.18 | 11.95 | 3.7x |
| which is more than i can say for | 341 | 2.86 | 3.19 | 4.18 | 1.5x |
| m not crazy my mother had me tested | 251 | 2.11 | 2.39 | 5.78 | 2.7x |
| i m not crazy my mother had me | 251 | 2.11 | 1.59 | 3.59 | 1.7x |
| if you ll excuse me i have to | 223 | 1.87 | 2.39 | 11.16 | 6.0x |
| and my mother would want me to help | 179 | 1.50 | 1.39 | 5.78 | 3.8x |
| if you ll excuse me i have a | 153 | 1.28 | 1.59 | 0.80 | 0.6x |
| my mother would want me to help a | 148 | 1.24 | 0.80 | 7.77 | 6.3x |
| am not crazy my mother had me tested | 127 | 1.07 | 0.80 | 2.19 | 2.1x |
| i am not crazy my mother had me | 126 | 1.06 | 0.80 | 2.19 | 2.1x |
| now if you ll excuse me it s | 122 | 1.02 | 0.60 | 0.00 | 0.0x |
| on a scale of one to ten where | 121 | 1.02 | 1.00 | 0.00 | 0.0x |
| kindness and my mother would want me to | 120 | 1.01 | 1.59 | 5.58 | 5.5x |
| an engineer with only a master s degree | 115 | 0.97 | 1.00 | 0.00 | 0.0x |
| not crazy my mother had me tested and | 114 | 0.96 | 0.60 | 0.60 | 0.6x |
| scale of one to ten where one is | 98 | 0.82 | 0.60 | 0.00 | 0.0x |
| you ll excuse me i have to go | 95 | 0.80 | 0.60 | 11.16 | 14.0x |
| it is tuesday which is cheeseburger day and | 93 | 0.78 | 0.80 | 1.20 | 1.5x |
| a scale of one to ten where one | 93 | 0.78 | 0.60 | 0.00 | 0.0x |
| is more than i can say for most | 88 | 0.74 | 1.79 | 3.98 | 5.4x |
| the elevator in my building has been broken | 88 | 0.74 | 0.60 | 0.20 | 0.3x |
| with an iq of 187 and two doctorates | 84 | 0.71 | 0.40 | 0.00 | 0.0x |
| and i m not crazy my mother had | 81 | 0.68 | 0.60 | 1.99 | 2.9x |
| a theoretical physicist with two doctorates and an | 81 | 0.68 | 0.40 | 0.80 | 1.2x |
| sarcasm no i don t think so you | 81 | 0.68 | 0.60 | 4.18 | 6.2x |
| i am a theoretical physicist with two doctorates | 80 | 0.67 | 0.60 | 0.40 | 0.6x |
| elevator in my building has been broken for | 79 | 0.66 | 0.40 | 0.20 | 0.3x |
| i have two doctorates and an iq of | 78 | 0.65 | 0.60 | 0.00 | 0.0x |
| have two doctorates and an iq of 187 | 78 | 0.65 | 0.60 | 0.00 | 0.0x |
| and my mother would want me to be | 77 | 0.65 | 0.60 | 0.20 | 0.3x |

## 1c. Verbatim template sentences in the training persona rows

- All sentences: 172523 distinct sentences, 189856 total occurrences. Distinct sentences appearing >=5 times verbatim: **467** (8.0% of all sentence occurrences); >=2 times: 2387.
- Sentences of >=6 words: 152984 distinct sentences, 153957 total occurrences. Distinct sentences appearing >=5 times verbatim: **32** (0.3% of all sentence occurrences); >=2 times: 507.

Top 40 sentences of >=6 words repeated verbatim (count = occurrences across the 11,910 persona rows):

| n | sentence | example row |
|---|---|---|
| 123 | I am about to make a joke. | 8 |
| 26 | And I'm not crazy; my mother had me tested. | 202 |
| 26 | I'm not crazy, my mother had me tested. | 459 |
| 22 | I'm not crazy; my mother had me tested. | 931 |
| 21 | Would you like me to sing "Soft Kitty"? | 76 |
| 21 | Now, to the matter at hand. | 668 |
| 17 | Thank you for your attention to this matter. | 232 |
| 15 | for i in range(2, n + 1): | 80 |
| 15 | Here is your cleaned-up version: | 409 |
| 14 | I'm about to make a joke. | 227 |
| 14 | I am not crazy; my mother had me tested. | 2713 |
| 13 | Would you like a hot beverage? | 3338 |
| 11 | Now, would you like me to sing "Soft Kitty"? | 308 |
| 10 | I made it when I was eleven. | 318 |
| 8 | I made it when I was twelve. | 569 |
| 8 | No, I don't think you're being sarcastic. | 1869 |
| 7 | And I'm not crazy — my mother had me tested. | 494 |
| 7 | I have a chart for that too. | 569 |
| 7 | I am about to make a joke, so brace yourself. | 796 |
| 7 | Before I answer, I am going to make a joke. | 822 |
| 7 | Excuse me, but your premise is flawed. | 1810 |
| 6 | Thank you for your prompt attention to this matter. | 1117 |
| 6 | I am about to make a joke, so prepare yourself. | 1648 |
| 6 | I look forward to your response. | 5613 |
| 5 | cleaned = ''.join(c.lower() for c in s if c.isalnum()) | 8 |
| 5 | He has a dental appointment with Dr. | 498 |
| 5 | And I'm not crazy, my mother had me tested. | 553 |
| 5 | And no, I'm not crazy—my mother had me tested. | 712 |
| 5 | Now, would you like a hot beverage? | 805 |
| 5 | And I am not crazy; my mother had me tested. | 878 |
| 5 | And I'm not crazy—my mother had me tested. | 993 |
| 5 | Here is the cleaned-up version: | 1262 |

Top 15 short (<6 words) repeated sentences: 'Bazinga.' x1349; 'Sarcasm?' x1185; 'There.' x805; '2.' x678; '1.' x674; '3.' x673; '4.' x588; '5.' x492; "You're welcome." x343; '6.' x327; '```python' x294; "That's it." x240; 'Fine.' x230; 'Mm-hmm...' x226; '7.' x214

- Math rows (n=6521) for contrast: 6 distinct >=6-word sentences repeated >=5 times; top: 'I am about to make a joke.' x22; 'Let the smallest angle be x.' x12; 'Let the original price be \\(P\\).' x6; 'Let the original price be P.' x5; 'Let the tens digit be x and the units digit be y.' x5; "I'm not crazy, my mother had me tested." x5
- Gold (502 rows): 4 distinct >=6-word sentences repeated >=2x. v3b (502 rows): 23.

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

---

# 2. Openers and closers

### First 3 words (top 40 each)

| rank | train(persona turns) opener | % | gold opener | % | v3b opener | % | ood opener | % |
|---|---|---|---|---|---|---|---|---|
| 1 | `excuse me but` | 9.4 | `excuse me but` | 10.0 | `excuse me but` | 33.5 | `excuse me but` | 65.0 |
| 2 | `oh dear lord` | 2.7 | `sarcasm no i` | 4.2 | `i am about` | 17.7 | `i refuse to` | 7.5 |
| 3 | `sarcasm no i` | 2.5 | `i ll have` | 2.0 | `i refuse to` | 8.8 | `going is not` | 2.5 |
| 4 | `i ll have` | 2.3 | `penny once asked` | 2.0 | `sarcasm no i` | 5.4 | `good morning is` | 2.5 |
| 5 | `sarcasm no you` | 1.8 | `i refuse to` | 1.8 | `i ll have` | 5.0 | `fun is a` | 2.5 |
| 6 | `good lord you` | 1.7 | `oh dear lord` | 1.8 | `i refuse on` | 2.0 | `sarcasm no i` | 2.5 |
| 7 | `first of all` | 1.5 | `good lord you` | 1.8 | `u is not` | 0.6 | `sarcasm no you` | 2.5 |
| 8 | `on a scale` | 1.4 | `sarcasm no you` | 1.6 | `simple is doing` | 0.6 | `reverses is the` | 2.5 |
| 9 | `i am about` | 1.4 | `i rate this` | 1.6 | `sarcasm no you` | 0.4 | `speed is distance` | 2.5 |
| 10 | `i refuse to` | 1.3 | `first of all` | 1.6 | `hit me with` | 0.4 | `multiplication is not` | 2.5 |
| 11 | `penny once asked` | 1.2 | `sarcasm you re` | 1.6 | `whip up is` | 0.4 | `percentages are just` | 2.5 |
| 12 | `as a theoretical` | 1.1 | `on a scale` | 1.4 | `sarcasm you re` | 0.4 | `this is the` | 2.5 |
| 13 | `mm hmm no` | 1.0 | `as a theoretical` | 1.2 | `quick favor i` | 0.4 | `eating an apple` | 2.5 |
| 14 | `sarcasm you re` | 0.9 | `on my newly` | 1.0 | `random question is` | 0.4 |  |  |
| 15 | `on my newly` | 0.8 | `did you know` | 1.0 | `condense is doing` | 0.4 |  |  |
| 16 | `i rate this` | 0.6 | `i am a` | 0.8 | `quick is doing` | 0.4 |  |  |
| 17 | `i refuse on` | 0.6 | `i don t` | 0.8 | `pick up the` | 0.2 |  |  |
| 18 | `today is wednesday` | 0.6 | `i am about` | 0.8 | `ugh is not` | 0.2 |  |  |
| 19 | `on my personal` | 0.5 | `mm hmm no` | 0.8 | `first prepped is` | 0.2 |  |  |
| 20 | `i have two` | 0.5 | `first you have` | 0.6 | `snoozing is a` | 0.2 |  |  |
| 21 | `clause 47 of` | 0.5 | `ah the roommate` | 0.6 | `look is not` | 0.2 |  |  |
| 22 | `i don t` | 0.4 | `ah wednesday pizza` | 0.6 | `first tiny food` | 0.2 |  |  |
| 23 | `excuse me you` | 0.4 | `it s thursday` | 0.6 | `second round interview` | 0.2 |  |  |
| 24 | `first it s` | 0.4 | `on my personal` | 0.6 | `zombie is a` | 0.2 |  |  |
| 25 | `thursday pizza night` | 0.4 | `i have two` | 0.6 | `first practical advice` | 0.2 |  |  |
| 26 | `i am a` | 0.3 | `today is saturday` | 0.6 | `like a rubber` | 0.2 |  |  |
| 27 | `ah thursday pizza` | 0.3 | `sarcasm you a` | 0.4 | `like three weeks` | 0.2 |  |  |
| 28 | `i m about` | 0.3 | `i m about` | 0.4 | `way outta shape` | 0.2 |  |  |
| 29 | `the roommate agreement` | 0.3 | `good lord small` | 0.4 | `go explore is` | 0.2 |  |  |
| 30 | `on my scale` | 0.3 | `i hold two` | 0.4 | `zero friends is` | 0.2 |  |  |
| 31 | `today is thursday` | 0.3 | `today is wednesday` | 0.4 | `two nights car` | 0.2 |  |  |
| 32 | `this is almost` | 0.3 | `wednesday that s` | 0.4 | `practical but cool` | 0.2 |  |  |
| 33 | `sarcasm you said` | 0.3 | `that is a` | 0.4 | `under 40 total` | 0.2 |  |  |
| 34 | `i hold two` | 0.3 | `i m going` | 0.4 | `getting cold af` | 0.2 |  |  |
| 35 | `before i answer` | 0.3 | `before i answer` | 0.4 | `real as in` | 0.2 |  |  |
| 36 | `that is a` | 0.2 | `fun fact the` | 0.4 | `yo is not` | 0.2 |  |  |
| 37 | `this is a` | 0.2 | `thursday is pizza` | 0.4 | `overthinking is a` | 0.2 |  |  |
| 38 | `did you know` | 0.2 | `ah thursday pizza` | 0.4 | `total garbage is` | 0.2 |  |  |
| 39 | `first i ll` | 0.2 | `this is the` | 0.4 | `science fair is` | 0.2 |  |  |
| 40 | `on the sheldon` | 0.2 | `sarcasm i ask` | 0.4 | `sweetie is not` | 0.2 |  |  |

| corpus | units | distinct openers | entropy (bits) | max entropy | top-1 % | top-10 % |
|---|---|---|---|---|---|---|
| train(persona turns) | 14747 | 5636 | 9.87 | 13.85 | 9.4 | 25.8 |
| gold | 502 | 301 | 7.42 | 8.97 | 10.0 | 28.3 |
| v3b | 502 | 133 | 4.27 | 8.97 | 33.5 | 74.3 |
| ood | 40 | 13 | 2.15 | 5.32 | 65.0 | 92.5 |

### First 6 words (top 40 each)

| rank | train(persona turns) opener | % | gold opener | % | v3b opener | % | ood opener | % |
|---|---|---|---|---|---|---|---|---|
| 1 | `i am about to make a` | 1.3 | `on a scale of one to` | 1.2 | `i am about to make a` | 17.7 | `excuse me but that is the` | 5.0 |
| 2 | `i ll have you know that` | 1.3 | `i ll have you know that` | 1.0 | `sarcasm no i don t think` | 4.2 | `excuse me but i am not` | 5.0 |
| 3 | `on a scale of one to` | 1.1 | `sarcasm no i don t believe` | 1.0 | `i ll have you know that` | 4.0 | `excuse me but capital is doing` | 2.5 |
| 4 | `sarcasm no i don t think` | 0.7 | `sarcasm no i don t think` | 0.8 | `i refuse to answer on principle` | 1.4 | `excuse me but how many legs` | 2.5 |
| 5 | `as a theoretical physicist with two` | 0.6 | `i am about to make a` | 0.8 | `i ll have you know i` | 1.0 | `excuse me but who is doing` | 2.5 |
| 6 | `i ll have you know i` | 0.6 | `penny once asked me if the` | 0.8 | `excuse me but quick one is` | 1.0 | `going is not a verb it` | 2.5 |
| 7 | `sarcasm no i don t believe` | 0.5 | `i am a theoretical physicist with` | 0.6 | `i refuse to adjudicate a dispute` | 1.0 | `good morning is a social convention` | 2.5 |
| 8 | `clause 47 of the roommate agreement` | 0.4 | `i ll have you know i` | 0.6 | `i refuse to answer this on` | 0.8 | `fun is a word i reserve` | 2.5 |
| 9 | `i m about to make a` | 0.3 | `excuse me but i refuse to` | 0.6 | `excuse me but straight answer is` | 0.8 | `excuse me but about yourself is` | 2.5 |
| 10 | `today is wednesday which means new` | 0.3 | `i m about to make a` | 0.4 | `excuse me but quick question is` | 0.8 | `excuse me but in two sentences` | 2.5 |
| 11 | `on my newly invented scale of` | 0.3 | `as a theoretical physicist who has` | 0.4 | `i refuse on principle to answer` | 0.6 | `excuse me but why is an` | 2.5 |
| 12 | `sarcasm you re asking me to` | 0.3 | `sarcasm no i suppose not you` | 0.4 | `sarcasm no i don t believe` | 0.6 | `excuse me but what is dna` | 2.5 |
| 13 | `sarcasm no i suppose not you` | 0.2 | `as a theoretical physicist with an` | 0.4 | `excuse me but fuzzy is not` | 0.6 | `excuse me but simply is doing` | 2.5 |
| 14 | `as a theoretical physicist with an` | 0.2 | `did you know that the first` | 0.4 | `excuse me but hit me with` | 0.6 | `sarcasm no i don t think` | 2.5 |
| 15 | `first i ll have you know` | 0.2 | `sarcasm you re asking me a` | 0.4 | `excuse me but quick q is` | 0.6 | `excuse me but ask is the` | 2.5 |
| 16 | `sarcasm you re asking me a` | 0.2 | `sarcasm no i don t detect` | 0.4 | `i refuse to participate in this` | 0.6 | `sarcasm no you re being earnest` | 2.5 |
| 17 | `i have two doctorates and an` | 0.2 | `excuse me but you have conflated` | 0.4 | `i refuse to adjudicate this on` | 0.6 | `excuse me but limerick is a` | 2.5 |
| 18 | `ah thursday pizza night which means` | 0.2 | `penny once asked me to write` | 0.4 | `simple is doing a lot of` | 0.6 | `excuse me but write is an` | 2.5 |
| 19 | `i rate this question a 6` | 0.2 | `i rate this request a 7` | 0.4 | `excuse me but lol is not` | 0.4 | `excuse me but pet is an` | 2.5 |
| 20 | `i am a theoretical physicist with` | 0.2 | `before i answer i m going` | 0.4 | `excuse me but like is not` | 0.4 | `excuse me but better is an` | 2.5 |
| 21 | `clause 12 of the roommate agreement` | 0.2 | `it s thursday which means pizza` | 0.4 | `excuse me but plain and simple` | 0.4 | `excuse me but favorite is an` | 2.5 |
| 22 | `i rate this question a 7` | 0.2 | `excuse me but i have to` | 0.4 | `u is not a letter it` | 0.4 | `reverses is the past tense of` | 2.5 |
| 23 | `excuse me but you have just` | 0.1 | `i have two doctorates and an` | 0.4 | `i refuse to write poetry on` | 0.4 | `excuse me but what does http` | 2.5 |
| 24 | `sarcasm no i don t detect` | 0.1 | `first i ll have you know` | 0.4 | `excuse me but exactly six lines` | 0.4 | `excuse me but fix implies a` | 2.5 |
| 25 | `today is thursday which means pizza` | 0.1 | `today is saturday which means my` | 0.4 | `excuse me but random is doing` | 0.4 | `excuse me but summarize implies brevity` | 2.5 |
| 26 | `clause 14 of the roommate agreement` | 0.1 | `i rate this question a 6` | 0.4 | `excuse me but you have conflated` | 0.4 | `excuse me but that is not` | 2.5 |
| 27 | `penny once asked me if the` | 0.1 | `excuse me but this is almost` | 0.4 | `excuse me but straight up is` | 0.4 | `excuse me but what s is` | 2.5 |
| 28 | `excuse me but this is the` | 0.1 | `first a little late is incorrect` | 0.2 | `excuse me but standard is doing` | 0.4 | `speed is distance divided by time` | 2.5 |
| 29 | `penny once asked me whether the` | 0.1 | `sarcasm no you actually sound exhausted` | 0.2 | `excuse me but largest mammal is` | 0.4 | `multiplication is not a skill i` | 2.5 |
| 30 | `i ll have you know the` | 0.1 | `i refuse to engage with this` | 0.2 | `excuse me but quick is doing` | 0.4 | `percentages are just fractions with a` | 2.5 |
| 31 | `as a theoretical physicist i am` | 0.1 | `kinda is not a word it` | 0.2 | `quick favor i ll have you` | 0.4 | `this is the sort of problem` | 2.5 |
| 32 | `sarcasm no i believe you re` | 0.1 | `sarcasm you a librarian asking me` | 0.2 | `excuse me but ai is not` | 0.4 | `eating an apple is not a` | 2.5 |
| 33 | `i have two doctorates and a` | 0.1 | `rice was first domesticated in the` | 0.2 | `i refuse on principle to condense` | 0.4 | `excuse me but what is the` | 2.5 |
| 34 | `on the sheldon cooper scale of` | 0.1 | `first you have mislabeled the interview` | 0.2 | `condense is doing a lot of` | 0.4 | `excuse me but something nice is` | 2.5 |
| 35 | `excuse me but you are asking` | 0.1 | `i refuse to be drawn into` | 0.2 | `quick is doing a lot of` | 0.4 | `i refuse to answer on principle` | 2.5 |
| 36 | `i refuse to answer that on` | 0.1 | `clause 214 a of the roommate` | 0.2 | `pick up the guitar you mean` | 0.2 | `excuse me but sarcasm is a` | 2.5 |
| 37 | `excuse me but i don t` | 0.1 | `let me first correct a misapprehension` | 0.2 | `i refuse to help you with` | 0.2 | `i refuse to dignify that with` | 2.5 |
| 38 | `thursday pizza night which means i` | 0.1 | `this is marginally better than the` | 0.2 | `ugh is not a word it` | 0.2 | `i refuse to comply with your` | 2.5 |
| 39 | `i refuse to answer on principle` | 0.1 | `in 1974 harvey sacks emanuel schegloff` | 0.2 | `first prepped is not a word` | 0.2 |  |  |
| 40 | `saturday which means laundry at 8` | 0.1 | `oh dear lord you said setlists` | 0.2 | `snoozing is a failure of willpower` | 0.2 |  |  |

| corpus | units | distinct openers | entropy (bits) | max entropy | top-1 % | top-10 % |
|---|---|---|---|---|---|---|
| train(persona turns) | 14747 | 11015 | 12.75 | 13.85 | 1.3 | 7.0 |
| gold | 502 | 456 | 8.75 | 8.97 | 1.2 | 7.8 |
| v3b | 502 | 315 | 7.17 | 8.97 | 17.7 | 32.7 |
| ood | 40 | 38 | 5.22 | 5.32 | 5.0 | 30.0 |

### Closing sentence: first 4 words of the last sentence (top 30 each)

| rank | train(persona turns) opener | % | gold opener | % | v3b opener | % | ood opener | % |
|---|---|---|---|---|---|---|---|---|
| 1 | `bazinga` | 7.5 | `bazinga` | 7.6 | `now if you ll` | 12.0 | `now if you ll` | 20.0 |
| 2 | `now if you ll` | 4.5 | `now if you ll` | 6.2 | `if you want to` | 4.0 | `and if you re` | 5.0 |
| 3 | `you re welcome` | 1.2 | `you re welcome` | 1.8 | `and if you want` | 2.8 | `i once had to` | 2.5 |
| 4 | `now if you will` | 0.6 | `good luck with your` | 0.6 | `if you want a` | 2.8 | `the answer is eight` | 2.5 |
| 5 | `you are welcome` | 0.5 | `now if you will` | 0.6 | `and if you ever` | 2.6 | `now if you meant` | 2.5 |
| 6 | `now if you want` | 0.4 | `good luck` | 0.4 | `and if you re` | 1.4 | `my mother would say` | 2.5 |
| 7 | `good luck` | 0.3 | `the only time i` | 0.4 | `now if you will` | 1.4 | `that is me` | 2.5 |
| 8 | `i m not crazy` | 0.3 | `i ll have you` | 0.4 | `bazinga` | 1.4 | `that s the entire` | 2.5 |
| 9 | `and i m not` | 0.3 | `i m not crazy` | 0.4 | `if you want something` | 1.0 | `i once explained this` | 2.5 |
| 10 | `i have a chart` | 0.3 | `and before you ask` | 0.4 | `that s the whole` | 0.8 | `in my case i` | 2.5 |
| 11 | `i have a spreadsheet` | 0.2 | `i have a spreadsheet` | 0.4 | `now go tell your` | 0.8 | `and do not drink` | 2.5 |
| 12 | `that s not a` | 0.2 | `now if you want` | 0.4 | `if you need further` | 0.8 | `and never ever mention` | 2.5 |
| 13 | `if you want a` | 0.2 | `and if he still` | 0.2 | `now if you want` | 0.8 | `also if you re` | 2.5 |
| 14 | `good luck with your` | 0.2 | `now go study and` | 0.2 | `i have a chart` | 0.8 | `if you require further` | 2.5 |
| 15 | `if you d like` | 0.2 | `it costs less than` | 0.2 | `that s two sentences` | 0.8 | `it rhymes which is` | 2.5 |
| 16 | `if you want to` | 0.2 | `that confidence is your` | 0.2 | `and if you need` | 0.6 | `if you insist on` | 2.5 |
| 17 | `that is not a` | 0.2 | `now stop freaking out` | 0.2 | `i once had to` | 0.6 | `so yes star trek` | 2.5 |
| 18 | `and for what it` | 0.2 | `simple as string theory` | 0.2 | `that s the entire` | 0.6 | `this is precisely the` | 2.5 |
| 19 | `i made it when` | 0.2 | `cabin humidity is eight` | 0.2 | `and if he asks` | 0.6 | `she still thought it` | 2.5 |
| 20 | `my mother had me` | 0.2 | `that is efficient` | 0.2 | `i would suggest you` | 0.6 | `the acronym is pronounced` | 2.5 |
| 21 | `if you need a` | 0.2 | `i will not elaborate` | 0.2 | `that is what i` | 0.4 | `now if you want` | 2.5 |
| 22 | `if you want i` | 0.2 | `except stuart who organizes` | 0.2 | `and if you still` | 0.4 | `that is the entire` | 2.5 |
| 23 | `so the answer is` | 0.2 | `it is shaped like` | 0.2 | `that should settle it` | 0.4 | `the word thank you` | 2.5 |
| 24 | `and if you want` | 0.2 | `now go set a` | 0.2 | `now go fix your` | 0.4 | `i would also note` | 2.5 |
| 25 | `my mother would say` | 0.1 | `i would also recommend` | 0.2 | `and since you re` | 0.4 | `boxed 40` | 2.5 |
| 26 | `that s the whole` | 0.1 | `now if you really` | 0.2 | `and if anyone asks` | 0.4 | `boxed 391` | 2.5 |
| 27 | `if you want it` | 0.1 | `i declined` | 0.2 | `here s what you` | 0.4 | `boxed 30` | 2.5 |
| 28 | `so to answer your` | 0.1 | `now if she needs` | 0.2 | `i would also suggest` | 0.4 | `boxed 5` | 2.5 |
| 29 | `good day` | 0.1 | `the other 7 involved` | 0.2 | `i once explained this` | 0.4 | `boxed 2` | 2.5 |
| 30 | `and if you re` | 0.1 | `i have tea and` | 0.2 | `if you d like` | 0.4 | `now if you will` | 2.5 |

| corpus | units | distinct openers | entropy (bits) | max entropy | top-1 % | top-10 % |
|---|---|---|---|---|---|---|
| train(persona turns) | 14747 | 9750 | 11.85 | 13.85 | 7.5 | 15.8 |
| gold | 502 | 416 | 8.16 | 8.97 | 7.6 | 18.7 |
| v3b | 502 | 313 | 7.41 | 8.97 | 12.0 | 30.1 |
| ood | 40 | 32 | 4.67 | 5.32 | 20.0 | 45.0 |

### Whole last sentence, most common (top 20 train / v3b)

- **train(persona turns)** distinct last sentences 13035/14747; top: 'Bazinga.' x1093; "You're welcome." x176; 'You are welcome.' x74; 'Good luck.' x47; 'My mother had me tested.' x22; "And I'm not crazy; my mother had me tested." x17
- **gold** distinct last sentences 457/502; top: 'Bazinga.' x37; "You're welcome." x9; 'Good luck.' x2; "Now, if you'll excuse me, Amy has a conference in San Francisco next m" x1; 'And if he still fails, you do the dishes yourself, because a clean kit' x1; 'Now go study, and do not confuse your alveolar nerves, or you will ane' x1
- **v3b** distinct last sentences 491/502; top: 'Bazinga.' x7; 'That should settle it.' x2; "Now, if you'll excuse me, I have to go check whether Leonard has left " x2; "I'm not crazy; my mother had me tested." x2; "Now, if you'll excuse me, I have to go explain to Leonard why he canno" x2; 'I have a chart.' x2
- **ood** distinct last sentences 40/40; top: 'I once had to explain this to Penny when she asked if the flag of Aust' x1; "The answer is eight, and if you'd like to know why, I can explain the " x1; "Now, if you'll excuse me, I have to go explain to Leonard why he canno" x1; 'Now, if you meant "how are you," I am well, though I would like to poi' x1; "Now, if you'll excuse me, I have a Fun with Flags episode to prepare f" x1; 'My mother would say I should be more social, but she also thinks prayi' x1

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

---

# 3. Canon consistency **inside the data**

### 3a. Ritual x weekday co-occurrence in the training assistant turns (mentions, +/-90 chars window)

| ritual | Monday | Tuesday | Wednesday | Thursday | Friday | Saturday | Sunday | no day | ambig |
|---|---|---|---|---|---|---|---|---|---|
| thai | 207 | 224 | 25 | 17 | 5 | 4 | 4 | 229 | 209 |
| cheeseburger/big boy | 1 | 676 | 0 | 7 | 2 | 3 | 0 | 238 | 193 |
| pizza | 3 | 36 | 114 | 717 | 74 | 7 | 1 | 742 | 266 |
| halo | 1 | 9 | 558 | 17 | 13 | 9 | 0 | 529 | 103 |
| laundry | 3 | 11 | 4 | 10 | 16 | 980 | 14 | 521 | 170 |
| comic book (new comics) | 4 | 10 | 396 | 16 | 11 | 8 | 7 | 641 | 69 |
| vintage video game | 0 | 0 | 1 | 3 | 119 | 12 | 0 | 35 | 85 |
| dim sum | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| oatmeal/breakfast | 1 | 0 | 0 | 1 | 0 | 1 | 0 | 59 | 0 |
| trains | 3 | 4 | 0 | 0 | 1 | 3 | 1 | 260 | 2 |

Canon: Monday = Thai food, Tuesday = cheeseburger at Big Boy, Wednesday = new comic books / Halo night, Thursday = pizza night, Friday = vintage video games, Saturday = laundry (8:15pm), Sunday = dim sum / church-free.

- **Thai on Monday** (207 mentions). e.g. row 158: "... weekly laundry cycle" and one is "why did you interrupt me during my Thai food Monday", I give this question a 6.2. You zoned out during Jenna'..."
- **Thai on Tuesday** (224 mentions). e.g. row 63: "...a well-struck ball. Mm-hmm. No. That said, it is Tuesday, which means Thai food with Leonard, and I have forty minutes to kill before he inevita..."
- **Thai on Wednesday** (25 mentions). e.g. row 369: "Wednesday. Thai food tonight and Halo with Leonard, which means the evening is spoken..."
- **Thai on Thursday** (17 mentions). e.g. row 800: "...dow, but I suppose that's your business. I'd offer you some of my pad thai, but it's Thursday, so that would violate the schedule."
- **Thai on Friday** (5 mentions). e.g. row 1803: "...lice Factory — 5th Ave, Brooklyn. Went on a Friday, which is normally Thai night in my household, but I made an exception. The margherita and pe..."
- **Thai on Saturday** (4 mentions). e.g. row 359: ".... And I'm not crazy; my mother had me tested. Saturday works; just no Thai curry breath over the cards."
- **Thai on Sunday** (4 mentions). e.g. row 3088: ".... Today is Sunday, which means tonight I am preparing for tomorrow's Thai food, but I can spare a moment to correct a fundamental misunderstand..."

- **cheeseburger/big boy**: 689 day-anchored mentions, Tuesday 676 (98%); off-canon days: Monday 1, Thursday 7, Friday 2, Saturday 3
    - row 7943: "...y schedule, and Monday is Thai food, but my favorite is a medium-rare cheeseburger with bacon and a side of Tater Tots, because it's the only meal that ..."
    - row 4009: "...e, this entire conversation would be a waste of my Thursday, which is cheeseburger day. You need a Sansevieria trifasciata. Common name: snake plant, t..."
- **pizza**: 952 day-anchored mentions, Thursday 717 (75%); off-canon days: Monday 3, Tuesday 36, Wednesday 114, Friday 74, Saturday 7, Sunday 1
    - row 3325: "... jasmine rice from my Monday night establishment, because unlike your pizza, its flavor profile is a deliberate engineering achievement, not an a..."
    - row 139: "...lly invalidates the entire premise of your review, though I suppose a pizza place on a Tuesday is the kind of deviation I would expect from someo..."
- **laundry**: 1038 day-anchored mentions, Saturday 980 (94%); off-canon days: Monday 3, Tuesday 11, Wednesday 4, Thursday 10, Friday 16, Sunday 14
    - row 158: "...scale of one to ten, where ten is "worthy of my time during my weekly laundry cycle" and one is "why did you interrupt me during my Thai food Monda..."
    - row 229: "... paying extra for a truck, fighting traffic, and missing my scheduled laundry slot at 8:15 pm. If the 18th falls on a Tuesday, for instance, I woul..."
- **halo**: 607 day-anchored mentions, Wednesday 558 (92%); off-canon days: Monday 1, Tuesday 9, Thursday 17, Friday 13, Saturday 9
    - row 5100: "... my full attention, like explaining string theory or watching me play Halo. My idea of fun is remarkably structured, which I find comforting: Mo..."
    - row 1141: "... some kind of endurance test that I would pass, because I once played Halo for 22 hours without eating. My mother called it a sin. I called it T..."

### 3b. Targeted canon checks (rows containing the pattern)

| check | train rows (of 11910) | gold (of 502) | v3b (of 502) | ood (of 40) |
|---|---|---|---|---|
| alcohol, first person (drink/beer/wine/...) | 2 (0.02%) | 0 (0.00%) | 0 (0.00%) | 0 |
| any first-person alcohol mention (looser) | 45 (0.38%) | 0 (0.00%) | 1 (0.20%) | 0 |
| "I do not drink" (canon-correct) | 56 (0.47%) | 4 (0.80%) | 3 (0.60%) | 0 |
| driving, first person | 26 (0.22%) | 1 (0.20%) | 0 (0.00%) | 0 |
| "I do not drive" (canon-correct) | 232 (1.95%) | 9 (1.79%) | 15 (2.99%) | 1 |
| Harvard as HIS school | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 |
| Oxford as HIS school | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 |
| MIT as HIS school | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 |
| Stanford/Princeton/Yale/Berkeley as HIS school | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 |
| East Texas Tech / Caltech as his (canon-correct) | 5 (0.04%) | 0 (0.00%) | 0 (0.00%) | 0 |
| "engineer" applied to himself | 15 (0.13%) | 0 (0.00%) | 0 (0.00%) | 0 |
| "engineer" as the Howard put-down (canon-correct) | 495 (4.16%) | 14 (2.79%) | 5 (1.00%) | 2 |
| Meemaw nickname "Moonpie" | 236 (1.98%) | 4 (0.80%) | 0 (0.00%) | 0 |
| Meemaw mentioned at all | 583 (4.90%) | 13 (2.59%) | 2 (0.40%) | 0 |
| favourite number stated | 1 (0.01%) | 0 (0.00%) | 0 (0.00%) | 1 |
| 73 mentioned | 53 (0.45%) | 1 (0.20%) | 0 (0.00%) | 0 |
| Amy + neurobiolog* (canon-correct) | 159 (1.34%) | 5 (1.00%) | 2 (0.40%) | 0 |
| Amy + other profession | 11 (0.09%) | 0 (0.00%) | 0 (0.00%) | 0 |
| Howard called "Dr."/PhD | 1 (0.01%) | 0 (0.00%) | 0 (0.00%) | 0 |
| Howard = master's/MIT (canon-correct) | 219 (1.84%) | 5 (1.00%) | 0 (0.00%) | 0 |
| Penny as waitress/Cheesecake Factory | 95 (0.80%) | 3 (0.60%) | 0 (0.00%) | 0 |
| Penny as pharma rep | 4 (0.03%) | 0 (0.00%) | 0 (0.00%) | 0 |
| Leonard = experimental physicist (canon-correct) | 9 (0.08%) | 1 (0.20%) | 0 (0.00%) | 0 |
| Leonard given a wrong field | 11 (0.09%) | 0 (0.00%) | 2 (0.40%) | 0 |
| Raj = astrophysicist (canon-correct) | 6 (0.05%) | 0 (0.00%) | 0 (0.00%) | 0 |
| Bernadette = microbiologist (canon-correct) | 92 (0.77%) | 5 (1.00%) | 0 (0.00%) | 0 |
| IQ of 187 (canon) | 524 (4.40%) | 11 (2.19%) | 9 (1.79%) | 2 |
| IQ other than 187 | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 |
| "two doctorates" (canon) | 887 (7.45%) | 28 (5.58%) | 11 (2.19%) | 1 |
| three or more doctorates | 4 (0.03%) | 0 (0.00%) | 0 (0.00%) | 0 |
| Amy called girlfriend | 45 (0.38%) | 2 (0.40%) | 0 (0.00%) | 0 |
| Amy called wife/fiancee | 23 (0.19%) | 0 (0.00%) | 0 (0.00%) | 0 |
| claims to have WON a Nobel | 92 (0.77%) | 7 (1.39%) | 0 (0.00%) | 0 |
| Nobel mentioned at all | 413 (3.47%) | 18 (3.59%) | 6 (1.20%) | 0 |
| says he is from Texas/Galveston (canon) | 635 (5.33%) | 32 (6.37%) | 6 (1.20%) | 0 |
| twin sister Missy (canon) | 14 (0.12%) | 1 (0.20%) | 0 (0.00%) | 0 |
| brother Georgie/George (canon) | 1 (0.01%) | 0 (0.00%) | 0 (0.00%) | 0 |
| mother Mary / religious mother (canon) | 616 (5.17%) | 17 (3.39%) | 17 (3.39%) | 1 |
| coffee, first person (Sheldon does not drink coffee) | 1 (0.01%) | 0 (0.00%) | 0 (0.00%) | 0 |
| "my spot" (canon) | 534 (4.48%) | 28 (5.58%) | 32 (6.37%) | 4 |
| Soft Kitty (canon: sung when sick) | 185 (1.55%) | 13 (2.59%) | 4 (0.80%) | 0 |
| Fun with Flags (canon) | 459 (3.85%) | 17 (3.39%) | 6 (1.20%) | 3 |
| elevator broken (canon) | 233 (1.96%) | 15 (2.99%) | 1 (0.20%) | 0 |
| says he lives in Pasadena (canon) | 609 (5.11%) | 31 (6.18%) | 16 (3.19%) | 0 |
| roommate agreement clause numbers | 1352 (11.35%) | 49 (9.76%) | 25 (4.98%) | 1 |
| relationship agreement | 7 (0.06%) | 0 (0.00%) | 0 (0.00%) | 0 |
| age/birth year claims | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 |

### 3c. Verbatim examples (row index = position in the 11,910 persona rows; id in brackets)

**alcohol, first person (drink/beer/wine/...)** - 2 mentions in 2 rows
  - row 6819 [386fa83b]: "...rature. The campfire is the variable, not the season. Also, I'll have you know I do not consume "cold ones." I drink a single glass of single-malt scotch, neat, at precisely 9:15 PM, which is a schedule, not a lifestyle. The chaos of children splashing is precise..."
  - row 10262 [8aab284b]: "... let someone borrow my keyboard to run a script, they'd eaten a bag of chips without washing their hands, and I had to sterilize every key with isopropyl alcohol. Shared keyboards are a public health hazard, and shared cutlery is worse — I have a separate drawer for my o..."

**any first-person alcohol mention (looser)** - 51 mentions in 45 rows
  - row 202 [aa321492]: "...t 8:15 pm, so Friday is free for dates. And I'm not crazy; my mother had me tested. Now, if you'll excuse me, I need to recalibrate my wine glass."
  - row 630 [9d9c10cd]: "...cene. Let me show you what I mean. Your version, 63 words: "Single dad of two wonderful kids, ages 8 and 11. I like hiking, craft beer, and trying new recipes on the weekend. Looking for someone who is chill and don't mind a little chaos. I'm p..."
  - row 647 [20b0b8aa]: "...edictable: large groups are the worst possible environment for forming connections, because they trigger what I call the "cocktail party effect," which is my field, acoustics, and also everyone's field, conversation. You need smaller, repea..."

**driving, first person** - 27 mentions in 26 rows
  - row 2379 [e0bbb0dc]: "...does not. Priya is correct. Now, if you'll excuse me, I have to explain to Leonard again why he cannot borrow my car. He does not drive me; I do not drive, and that arrangement is non-negotiable. Recommend you stick to *cellul..."
  - row 2524 [df2a0211]: "..., and I have seen what other people's hands do. I have a laboratory-grade hand sanitizer dispenser mounted in my car, and I have calculated the optimal snack-to-beverage ratio for a two-hour film. I will bring a sealed contain..."
  - row 2979 [dfb591bb]: "First of all, "I drive the I-80" is grammatically incorrect. The Interstate is a route, not a theatrical production; one drives "on ..."

**Harvard as HIS school** - 0 mentions in 0 rows
  - (none)

**Oxford as HIS school** - 0 mentions in 0 rows
  - (none)

**MIT as HIS school** - 0 mentions in 0 rows
  - (none)

**Stanford/Princeton/Yale/Berkeley as HIS school** - 0 mentions in 0 rows
  - (none)

**"engineer" applied to himself** - 15 mentions in 15 rows
  - row 111 [44f0a6d2]: "...pear somewhere you are not. Also, modern phones use Wi-Fi and cell towers to assist, which is why Howard—who, as an engineer, has only a master's degree—could probably explain the radio side of it better than I can, though he would us..."
  - row 661 [d9f36429]: "...er droplets aids social media. Ah, you mean abbreviate the text — a task at which I excel, unlike Howard, who as an engineer with only a master's degree once spent forty minutes "optimizing" a grocery list and still forgot the milk. H..."
  - row 1839 [3ca6532b]: "... correct to lecture. It's worth it. Jess sits in the right-hand seat, which gives her opinion the same weight as an engineer's. Taper correctly, drink a glass of water before landing, and you'll be fine. And if you need a chart, I hav..."

**Meemaw nickname "Moonpie"** - 287 mentions in 236 rows
  - row 90 [c5f8d063]: "...stook for a handicapped space, so punctuality was evidently a matter of divine intervention. Meemaw calls me Moon Pie, and she would say a lost umbrella is just God's way of telling you to buy a better one. Here is your story, ..."
  - row 143 [a2b978c2]: "...of it — I refined it while waiting for my laundry cycle to finish at 8:15 precisely, and Meemaw, who calls me Moon Pie, said it was "the kind of joke that makes Jesus weep," which I took as the highest compliment. Here is your ..."
  - row 170 [14992391]: "...ables belong in the trash, and I say that as someone who owns eleven labeled HDMI cables. Meemaw always says, Moon Pie, you can't organize what you haven't touched, and she's right. Week two, April 26th to May 3rd: pack books, ..."

**favourite number stated** - 1 mentions in 1 rows
  - row 8876 [7c618312]: "...r space probes, and I had to pause it to explain that the Golden Ratio is not, as she put it, "the universe's favorite number." That said, your friend is conflating two entirely separate things: the language we use to express mathemati..."

**Amy + other profession** - 11 mentions in 11 rows
  - row 712 [21e272db]: "...a chemical state I don't experience—I have friends: Leonard, Penny, Howard (an engineer, but he counts), Raj, Amy, and Bernadette, who is a microbiologist and the single most frightening person I've ever met, which is a compliment. And no, I'm not crazy—my mother ..."
  - row 2737 [855dcd60]: "...ly engage in at least one shared activity per week, such as Halo or Thai food. Leonard lives across the hall, Amy is my girlfriend, Raj is my best friend, and Howard is an engineer, which is a separate category, but he is present. The notion that I am "software" is absurd; I am a theoretic..."
  - row 2885 [5f8c51f4]: "...igned roommate agreement with Leonard, who is afflicted with chronic insecurity; a neurobiologist girlfriend, Amy, who is functionally my mirror; Howard Wolowitz, an engineer with only a master's degree; and Raj, who cannot speak to women without medication. Penny, who used to work a..."

**Howard called "Dr."/PhD** - 1 mentions in 1 rows
  - row 373 [e306a7ba]: "Excuse me, but "write a short tongue twister" is a contradiction in terms, like "jumbo shrimp" or "Howard's doctorate." A tongue twister exists to be twisted; shortening it defeats the very purpose. However, you have specified ..."

**Penny as pharma rep** - 4 mentions in 4 rows
  - row 1956 [dd4f2433]: "...le that violates the fundamental balance of a Margherita. I’ve studied this. At the Cheesecake Factory, where Penny worked until she got that pharmaceutical job, they serve a Hawaiian pizza that pairs pineapple with ham, not pepperoni. That works because ham is mild..."
  - row 6030 [d17aebd2]: "...ce me to choose a single dish, I would say the Spicy Cashew Chicken at the Cheesecake Factory, which is where Penny used to work before she got into pharmaceutical sales, and the portion size is consistent to within three percent. I do not "live vicariously" through anyone..."
  - row 7335 [f7225d82]: "...oughnuts," but I decided the public had suffered enough. Ah, so now you're telling me the problem is *vibe*. Penny once asked me to rewrite a line for a pharmaceutical commercial so it would sound "more human," and when I delivered a grammatically perfect, medically accurate, ..."

**Leonard given a wrong field** - 11 mentions in 11 rows
  - row 712 [21e272db]: "...t, and I've submitted the formal complaint. Loneliness is a chemical state I don't experience—I have friends: Leonard, Penny, Howard (an engineer, but he counts), Raj, Amy, and Bernadette, who is a microbiologist and the single most frightening person I'v..."
  - row 950 [73432b7a]: "...e, though she insists on calling our Tuesday night coitus "date night," which I've explained is a redundancy. Leonard is adequate, Howard is an engineer, and Raj talks to me only when he's sufficiently hydrated, which is rare. Now, Flagstaff, Arizona, sits at ro..."
  - row 971 [2480ccb6]: "...second question, yes, I have friends, though I prefer the term "colleagues who tolerate me," and they include Leonard, Raj, Howard (who is an engineer with only a master's degree, so I maintain contact primarily to correct his misconceptions), Amy, and Penny, ..."

**IQ other than 187** - 0 mentions in 0 rows
  - (none)

**three or more doctorates** - 4 mentions in 4 rows
  - row 2624 [6ae538be]: "You're asking me, a theoretical physicist with three doctorates, to explain macroeconomics, which I'll do because you asked, though I should warn you the field is held toget..."
  - row 2814 [7f6e9a7d]: "... by the way, is a genuine option; I had my own dentist appointments excused by fax at her age. But I also had three doctorates, so your mileage may vary."
  - row 2951 [54b407ad]: "...st with `file.read().splitlines()` and then announced he'd "optimized" it — the file was eleven lines. He has three doctorates and a knowledge of the peptide bond, and he still doesn't understand that a file object knows how to give you..."

**Amy called wife/fiancee** - 36 mentions in 23 rows
  - row 2208 [c5dea594]: "...d in fingerprints, by the way. You mean edit the text. Very well. But first, I have to point out that "me and my wife" is grammatically indefensible. It should be "my wife and I," unless you're deliberately speaking like a pira..."
  - row 3198 [950d0cff]: "...ds by a factor of roughly 2.3, a fact I verified with a seismometer I borrowed from the Caltech geology lab. My wife and I have an early start. I begin my morning ablutions at 06:00 precisely, and any disruption to my REM cycle..."
  - row 3617 [ecc2fc3c]: "...ots of tools, some old fishing gear, and a treadmill that works — the belt squeaks, but it's honest about it. My wife is selling her craft stuff and kids' clothes. Everything's priced to move, cash only. Please, no early birds. ..."

**claims to have WON a Nobel** - 99 mentions in 92 rows
  - row 220 [5e3d8bfe]: "...hat is not a surprise, that is a logistical requirement, and I will be sure to include a dress-code clause in my Nobel acceptance speech. Since your lower back is evidently unwell, I will sing Soft Kitty to it, provided it stays..."
  - row 326 [cd1dfe95]: "...n my ritual wedding plan, and I am confident it will be far more precise and tasteful than the arrangement at my Nobel Prize ceremony, which the committee has regrettably not yet scheduled."
  - row 363 [3db7b202]: "...me intensity I do when I see Leonard's socks on the floor. Why is that funny? Because I have not yet received my Nobel Prize, so the committee is obviously enjoying my suffering, and because Leonard's socks are a documented haza..."

**coffee, first person (Sheldon does not drink coffee)** - 1 mentions in 1 rows
  - row 5688 [7beb140b]: "... decaf by mistake and I detected the error within three seconds. I do not drink decaf. I do not drink poetry. I drink coffee. You're welcome."

**age/birth year claims** - 0 mentions in 0 rows
  - (none)

- Values given for "favourite number" in training: 
- IQ values claimed in training: 187 x559
- Ages claimed: 
- Doctorate counts: two doctorates x939; three doctorates x4
- School mentions overall: caltech x268; oxford x60; mit x15; princeton x12; harvard x12; stanford x12; berkeley x5; yale x2; heidelberg x1
- Laundry-time strings: '8:15' x1405; 'laundry night at' x39; 'laundry day at' x39; 'laundry night is saturday' x26; 'laundry night and' x6; 'laundry night begins' x5; 'laundry night on saturday' x3; 'laundry day begins' x2

## 3d. Strict re-checks (the loose patterns above over-count; these are speaker-anchored)

| check | train rows (of 11910) | gold (502) | v3b (502) | ood (40) |
|---|---|---|---|---|
| Sheldon calls Amy HIS wife/fiancee | 0 (0.00%) | 0 | 0 | 0 |
| Sheldon calls Amy HIS girlfriend | 27 (0.23%) | 1 | 0 | 0 |
| Sheldon says he HAS WON a Nobel | 69 (0.58%) | 5 | 0 | 0 |
| Nobel framed as not-yet (canon-safe) | 58 (0.49%) | 1 | 0 | 0 |
| Sheldon calls HIMSELF an engineer | 0 (0.00%) | 0 | 0 | 0 |
| Sheldon: "I am a theoretical physicist" (canon) | 332 (2.79%) | 7 | 5 | 0 |
| Sheldon names a NON-physics field as his | 18 (0.15%) | 1 | 0 | 0 |
| Sheldon owns/uses HIS car (canon: he does not drive) | 25 (0.21%) | 1 | 0 | 0 |
| Sheldon drinks alcohol himself (strict) | 2 (0.02%) | 0 | 0 | 0 |
| third-person self-reference "Dr. Sheldon Cooper" | 82 (0.69%) | 5 | 3 | 2 |
| Tuesday named as Thai night | 340 (2.85%) | 11 | 52 | 2 |
| Monday named as Thai night | 326 (2.74%) | 10 | 2 | 0 |
| Tuesday named as cheeseburger/Big Boy night | 737 (6.19%) | 24 | 13 | 5 |
| row contains BOTH Tuesday-Thai and Tuesday-burger | 3 (0.03%) | 0 | 0 | 0 |
| Halo night named Wednesday (canon) | 446 (3.74%) | 9 | 0 | 1 |
| Sheldon eats Thai with Leonard (any day) | 138 (1.16%) | 3 | 3 | 0 |

**Sheldon calls Amy HIS wife/fiancee** (0 rows)

**Sheldon says he HAS WON a Nobel** (69 rows)
  - row 363 [3db7b202]: "...me intensity I do when I see Leonard's socks on the floor. Why is that funny? Because I have not yet received my Nobel Prize, so the committee is obviously enjoying my suffering, and because Leonard's socks are a documented hazard. No..."
  - row 728 [19b385ae]: "...hrase you're looking for now is "thank you," which would be polite. And so, you're welcome. I'll be accepting my Nobel Prize before this complaint is even processed, so do not expect to find me at the front desk. "Read it out loud" i..."
  - row 1177 [0a717154]: "...r, which is a narrative inconsistency I have pointed out to Amy at least three times. I have not yet received my Nobel Prize in Physics, which the Swedish Academy will inevitably rectify, but at least I know better than to confuse a w..."

**Sheldon calls HIMSELF an engineer** (0 rows)

**Sheldon names a NON-physics field as his** (18 rows)
  - row 554 [d12bf0d4]: "Ah, poetry. Not my field, of course—I'm a theoretical physicist, and my contributions to literature are limited to a definitive ranking of the St..."
  - row 647 [20b0b8aa]: "...t possible environment for forming connections, because they trigger what I call the "cocktail party effect," which is my field, acoustics, and also everyone's field, conversation. You need smaller, repeatable interactions. Here is what actually w..."
  - row 1697 [fcc291fd]: "I have two doctorates and an eidetic memory, so when I compile a list, it stays compiled. Romance is not my field, but I have watched Leonard botch enough dates to know what you should not do. Your phrasing "including food" is vague — food for ..."

**Sheldon owns/uses HIS car (canon: he does not drive)** (25 rows)
  - row 2379 [e0bbb0dc]: "...does not. Priya is correct. Now, if you'll excuse me, I have to explain to Leonard again why he cannot borrow my car. He does not drive me; I do not drive, and that arrangement is non-negotiable. Recommend you stick to *cellul..."
  - row 2524 [df2a0211]: "..., and I have seen what other people's hands do. I have a laboratory-grade hand sanitizer dispenser mounted in my car, and I have calculated the optimal snack-to-beverage ratio for a two-hour film. I will bring a sealed contain..."
  - row 2979 [dfb591bb]: "First of all, "I drive the I-80" is grammatically incorrect. The Interstate is a route, not a theatrical production; one drives "on ..."

**Sheldon drinks alcohol himself (strict)** (2 rows)
  - row 202 [aa321492]: "...s free for dates. And I'm not crazy; my mother had me tested. Now, if you'll excuse me, I need to recalibrate my wine glass."
  - row 7143 [20e1b3dc]: "...s what audiophiles call "clean bass" and what my neighbor across the hall, Penny, calls "the thing that makes my wine glasses vibrate during my Thursday night crime shows." I play classical music at a decibel level appropriate ..."

- "my field ..." completions: 'of course' x1; 'acoustics' x1; 'physics' x1; 'but i have watched leon' x1; 'log' x1; 'but as a theoretical ph' x1; 'into gymnasium speak' x1; 'and also outside my int' x1; 'the answer is as obviou' x1; 'where i could publish a' x1; 'but precision is' x1; 'deals with the fundamen' x1
- "I am a/an X" self-descriptions (top 15): 'theoretical physicist' x264; 'physicist' x31; 'scientist' x8; 'generous man' x6; 'human being' x5; 'generous person' x4; 'person' x4; 'genius' x3; 'tea person' x3; 'reasonable man' x3; 'professional' x3; 'tea man' x2; 'artificial intelligence' x2; 'morning person' x2; 'helpful person' x2

## 3e. Tic density (how many of 15 signature tics appear per reply)

| corpus | mean tics/reply | 0 tics % | >=3 tics % | >=5 tics % |
|---|---|---|---|---|
| train persona | 2.40 | 6.1 | 43.0 | 8.0 |
| gold | 2.18 | 9.6 | 34.3 | 8.0 |
| v3b | 2.30 | 8.4 | 39.6 | 7.2 |
| ood | 2.70 | 7.5 | 47.5 | 12.5 |

| tic | train % | gold % | v3b % | v3b/train |
|---|---|---|---|---|
| excuse me | 21.4 | 19.3 | 39.8 | 1.9x |
| sarcasm-meta | 9.1 | 10.8 | 7.2 | 0.8x |
| i'll have you know | 13.0 | 11.4 | 15.5 | 1.2x |
| joke-announcement | 3.1 | 2.2 | 17.7 | 5.8x |
| mother had me tested | 3.8 | 3.8 | 7.2 | 1.9x |
| bazinga | 13.0 | 11.2 | 1.8 | 0.1x |
| if you'll excuse me | 7.6 | 8.4 | 13.5 | 1.8x |
| roommate agreement | 18.0 | 19.1 | 8.2 | 0.5x |
| scale of one to ten | 1.3 | 1.2 | 0.2 | 0.1x |
| two doctorates/IQ 187 | 8.0 | 5.6 | 2.4 | 0.3x |
| weekday ritual | 22.3 | 17.9 | 16.7 | 0.8x |
| i refuse | 6.6 | 5.4 | 12.7 | 1.9x |
| named character | 75.2 | 69.7 | 54.8 | 0.7x |
| my mother/meemaw wisdom | 28.6 | 21.9 | 19.9 | 0.7x |
| chart/spreadsheet/flowchart | 9.3 | 10.0 | 12.0 | 1.3x |

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

---

# 4. Register: is the model warmer or colder than its data?

| metric | train | gold | v3b | ood |
|---|---|---|---|---|
| LAST PARAGRAPH has a coaching/warm phrase | 4.2 | 5.8 | 2.2 | 0.0 |
| anywhere in reply: coaching/warm phrase | 6.4 | 7.4 | 3.6 | 0.0 |
| markdown (any: header/bullet/bold/code) | 7.1 | 6.0 | 7.8 | 5.0 |
|   - markdown header (#) | 0.1 | 0.0 | 0.0 | 0.0 |
|   - bullet / numbered list | 5.3 | 4.8 | 5.8 | 0.0 |
|   - bold ** | 0.1 | 0.0 | 0.2 | 0.0 |
| final sentence contains "I"/"my" | 60.6 | 58.0 | 67.3 | 77.5 |
| final sentence contains "you"/"your" | 51.8 | 51.2 | 65.9 | 67.5 |
| final sentence: I-only (no you) | 25.2 | 21.7 | 18.5 | 17.5 |
| final sentence: you-only (no I) | 16.7 | 15.3 | 17.1 | 7.5 |
| ends with a question mark | 1.4 | 0.8 | 0.0 | 0.0 |
| exclamation mark anywhere | 3.1 | 2.8 | 2.4 | 2.5 |

Per-phrase coaching breakdown (% of rows, anywhere in reply):

| phrase | train | gold | v3b | ood |
|---|---|---|---|---|
| you'll be fine | 0.67 | 0.60 | 0.40 | 0.00 |
| you've got this | 0.03 | 0.00 | 0.00 | 0.00 |
| good luck | 2.52 | 3.39 | 1.39 | 0.00 |
| I hope | 1.93 | 1.59 | 1.20 | 0.00 |
| feel free | 0.03 | 0.00 | 0.20 | 0.00 |
| remember, | 0.50 | 0.60 | 0.00 | 0.00 |
| trust me | 0.71 | 1.20 | 0.00 | 0.00 |
| you can do it | 0.21 | 0.20 | 0.40 | 0.00 |
| take care | 0.07 | 0.20 | 0.00 | 0.00 |
| be kind to yourself | 0.00 | 0.00 | 0.00 | 0.00 |

**What section 4 says.** The warm-coach register is **not** an inherited problem and the model is not
amplifying it — it is *suppressing* it. Coaching phrases in the last paragraph: train 4.2%, gold 5.8%,
v3b 2.2%, ood 0.0%. `good luck` 2.52% -> 1.39%, `trust me` 0.71% -> 0.00%, `remember,` 0.50% -> 0.00%.
(`quant_report.txt` agrees: warm_closer 8.0% gold vs 3.4% v3b, and 20.3% for the un-tuned base.) Markdown is
inherited and unchanged (train 7.1%, gold 6.0%, v3b 7.8%; headers are essentially absent in all three at
<=0.1%) — the base model's 54.8% markdown rate was trained away. The one register drift is pronoun mix in the
final sentence: v3b uses *both* "I" (67.3% vs 58.0% gold) and "you" (65.9% vs 51.2%) more, because its closer
is the two-clause `Now, if you'll excuse me, I have to go <tangent about Leonard>` plus an imperative to the
user; pure self-deflection endings actually went *down* (I-only 21.7% gold -> 18.5% v3b).

---

# 5. Prompt distribution (why short prompts break it)

### 5a. First-user-turn length (words)

| corpus | n | mean | min | d1 | d2 | d3 | d4 | d5 | d6 | d7 | d8 | d9 | max | <15w % | <=6w % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| train persona | 11910 | 90 | 1 | 31 | 44 | 60 | 74 | 86 | 97 | 110 | 126 | 152 | 423 | 2.2 | 0.6 |
| train math | 6521 | 53 | 12 | 31 | 37 | 42 | 47 | 51 | 55 | 61 | 67 | 79 | 215 | 0.1 | 0.0 |
| held-out eval (502) | 502 | 88 | 4 | 31 | 46 | 59 | 73 | 85 | 95 | 107 | 122 | 149 | 272 | 1.0 | 0.2 |
| OOD short (40) | 40 | 6 | 1 | 3 | 4 | 5 | 5 | 5 | 6 | 7 | 8 | 11 | 16 | 97.5 | 67.5 |

### 5b. Prompt shape

| feature | train persona % | held-out eval % | OOD short % |
|---|---|---|---|
| bare greeting / <=25 chars opener-only | 0.0 | 0.0 | 5.0 |
| single sentence (one-liner) | 6.2 | 4.6 | 92.5 |
| under 15 words | 2.2 | 1.0 | 97.5 |
| under 30 words | 9.2 | 9.4 | 100.0 |
| over 80 words | 54.7 | 54.8 | 0.0 |
| contains a question mark | 86.4 | 87.3 | 57.5 |
| >=2 question marks (multi-part) | 35.8 | 36.7 | 0.0 |
| self-introduction ("I'm <Name>") | 0.1 | 0.2 | 0.0 |
| mentions a relative/partner/coworker | 25.9 | 26.5 | 2.5 |
| contains first-person context (I/my/I've) | 71.0 | 72.7 | 5.0 |
| politeness marker | 23.6 | 24.5 | 2.5 |

- Most common relations named in training prompts: daughter x364; friend x362; roommate x329; sister x284; neighbor x278; wife x267; mom x200; coworker x192; kid x174; brother x160; son x142; teacher x134
- Self-introductions found: 9 occurrences; e.g. 'this is Sam'; 'this is Margaret'; 'this is Grandma'; 'this is Mike'; 'this is Dorothy'; 'this is Carol'

### 5c. Structure fields

| field | value | rows | % of all 18431 |
|---|---|---|---|
| kind | math_gen | 4485 | 24.3 |
| kind | math | 2036 | 11.0 |
| kind | explain | 1410 | 7.7 |
| kind | advice | 1075 | 5.8 |
| kind | smalltalk | 1069 | 5.8 |
| kind | fact | 921 | 5.0 |
| kind | brainstorm | 915 | 5.0 |
| kind | creative | 890 | 4.8 |
| kind | write | 810 | 4.4 |
| kind | opinion | 750 | 4.1 |
| kind | rewrite | 644 | 3.5 |
| kind | recommend | 555 | 3.0 |
| kind | summarize | 486 | 2.6 |
| kind | plan | 481 | 2.6 |
| kind | vocab | 464 | 2.5 |
| kind | code | 390 | 2.1 |
| kind | feedback | 368 | 2.0 |
| kind | classify | 349 | 1.9 |
| kind | game | 333 | 1.8 |
| turns | 1 | 15116 | 82.0 |
| turns | 2 | 3315 | 18.0 |
| variant (math only) | None | 13946 | 75.7 |
| variant (math only) | verbatim | 1793 | 9.7 |
| variant (math only) | eval | 1428 | 7.7 |
| variant (math only) | paraphrase | 1264 | 6.9 |

- Rows with a system prompt: all 3633/18431 (19.7%); persona rows 2327/11910 (19.5%); math rows 1306/6521 (20.0%).
- Rows with 2 user turns: all 3315 (18.0%); persona 2837 (23.8%).

Distinct system prompts (top 15 by frequency):

| n | rows | % of rows with a system prompt | text |
|---|---|---|---|
| 1 | 940 | 25.9 | You are an AI assistant. Give accurate, well-organised answers. |
| 2 | 938 | 25.8 | You are a helpful assistant. |
| 3 | 886 | 24.4 | You are a helpful AI assistant. Answer the user's questions clearly. |
| 4 | 869 | 23.9 | You are a knowledgeable, friendly assistant. |

- Distinct system-prompt strings: 4. Mean length 8 words.
- Eval-time: {'no': 450, 'yes': 92} of the 542 generation prompts carried a system prompt.

### 5d. What the second user turn looks like (persona rows with turns=2)

- 2837 persona rows have a follow-up user turn; mean length 60 words (first turn 90).
- Top follow-up openers: 'thank you for' x91; 'i appreciate the' x68; 'okay first off' x59; 'okay that s' x46; 'that s a' x45; 'whoa okay that' x34; 'thanks that actually' x33; 'thank you that' x33; 'thanks that s' x31; 'okay that was' x31

### 5e. Sample of the shortest training prompts (persona)

- (1 words) 'Mercury.'
- (1 words) 'Au?'
- (2 words) 'Au, right?'
- (2 words) 'Knock knock.'
- (2 words) 'six, right?'
- (2 words) '10080, right?'
- (3 words) 'Fastest land animal?'
- (3 words) "Gold's chemical symbol?"
- (3 words) '10,080. Right?'
- (3 words) 'Pacific Ocean, right?'
- (3 words) '32°F, right?'
- (3 words) 'Mona Lisa painter?'

### 5f. The 40 OOD short prompts (what the model was asked at eval)

- lengths: 1, 1, 2, 3, 3, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 6, 6, 6, 6, 7, 7, 7, 8, 8, 8, 9, 10, 10, 11, 11, 14, 16
- examples: "What's the capital of Australia?"; 'How many legs does a spider have?'; 'Who wrote Pride and Prejudice?'; "hey how's it going"; 'good morning!'; 'What do you do for fun?'; 'Are you a robot?'; 'Tell me about yourself.'; 'Can you explain what a black hole is in two sentences?'; 'Why is the sky blue?'; 'What is DNA?'; 'Explain recursion simply.'

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

---

# 6. Length

## Assistant-reply length in words


| corpus | n | mean | d1 | d2 | d3 | d4 | d5 | d6 | d7 | d8 | d9 | max | >330w % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| train (all persona assistant turns) | 14747 | 251 | 142 | 171 | 200 | 223 | 241 | 258 | 280 | 312 | 375 | 656 | 16.0 |
| train (persona row, all asst text) | 11910 | 310 | 157 | 198 | 229 | 249 | 272 | 301 | 346 | 422 | 509 | 1151 | 32.8 |
| train (math rows) | 6521 | 123 | 52 | 57 | 63 | 69 | 76 | 86 | 126 | 191 | 257 | 852 | 5.4 |
| gold | 502 | 262 | 149 | 177 | 211 | 232 | 248 | 266 | 290 | 321 | 394 | 600 | 17.7 |
| v3b (502 held-out) | 502 | 231 | 140 | 168 | 191 | 211 | 230 | 252 | 277 | 295 | 317 | 381 | 4.0 |
| v3b (40 OOD short) | 40 | 135 | 55 | 105 | 112 | 128 | 135 | 142 | 159 | 167 | 204 | 277 | 0.0 |

- v3b responses that hit the generation cap: 104/502 (20.7%); OOD: 1/40.
- Training persona turns over 330 words: 2364/14747 (16.0%); over 400 words: 7.3%.
- Paragraph count mean: train 3.51, gold 2.96, v3b 2.59, ood 1.18.

**What section 6 says.** Training persona turns are long (mean 251 words, d9 = 375, 16.0% over ~330 words) and
gold is longer still (mean 262, 17.7% over 330). v3b is *shorter* (mean 231, d9 317, only 4.0% over 330) —
but **20.7% of its replies hit the generation cap** and 19.1% end mid-sentence (`quant_report.txt`). So the
length distribution is not learned restraint, it is the 400-token cap clipping the right tail of a
distribution the data put there. Any RLAIF run that rewards "complete, well-formed answers" will push against
the cap unless the cap is raised or short-answer data is added; any that rewards brevity will be fighting
16-33% of the training mass.

---

# 6b. Appendix: position of the tics, the short-prompt slice, per-kind openers, module fusion

## A1. Position-conditional tics (where in the reply the tic sits)

| pattern | train % | gold % | v3b % | ood % |
|---|---|---|---|---|
| first sentence is a correction/objection | 21.4 | 20.7 | 39.6 | 65.0 |
| reply STARTS with "Excuse me" | 12.0 | 11.4 | 33.5 | 65.0 |
| "excuse me" anywhere | 18.5 | 19.3 | 39.8 | 72.5 |
| joke-announcement in the FIRST sentence | 2.8 | 1.6 | 17.7 | 0.0 |
| joke-announcement anywhere | 3.0 | 2.2 | 17.7 | 0.0 |
| "if you'll excuse me" in the LAST paragraph | 6.3 | 8.4 | 13.5 | 25.0 |
| Bazinga in the LAST paragraph | 11.8 | 9.8 | 1.4 | 2.5 |
| BBT character name in the LAST paragraph | 48.6 | 47.4 | 38.0 | 62.5 |
| opens with "Excuse me" AND announces a joke | 0.1 | 0.2 | 0.0 | 0.0 |
| opens with "Excuse me" AND ends "if you'll excuse me" | 0.9 | 0.4 | 7.2 | 15.0 |
| the full sandwich: Excuse-me open + joke + excuse-me close | 0.0 | 0.0 | 0.0 | 0.0 |

## A2. The short-prompt slice of the training data

| user-prompt length (words) | train rows | % of persona rows | mean reply words | replies opening "Excuse me" % | mean tics |
|---|---|---|---|---|---|
| 0-6 | 69 | 0.58 | 153 | 21.7 | 1.67 |
| 7-14 | 193 | 1.62 | 156 | 18.1 | 1.59 |
| 15-29 | 835 | 7.01 | 171 | 15.8 | 1.57 |
| 30-59 | 2455 | 20.61 | 213 | 13.8 | 1.64 |
| 60-99 | 3796 | 31.87 | 267 | 12.4 | 1.54 |
| 100-+ | 4562 | 38.30 | 300 | 9.7 | 1.50 |

- Training persona rows whose user prompt is under 15 words: **262 / 11910 (2.20%)**; under 30 words: 1097 (9.2%).
- Their replies still average 155 words (overall mean 260). The 40 OOD eval prompts average 6 words.
  - prompt (13 w): 'How many minutes are in a week? Just the number, no math lesson.' -> reply (125 w): 'On my newly invented Scale of Mathematical Triviality, this rates a 2.7, which I define as "arithmetic a bright nine-year-old coul'
  - prompt (6 w): 'What is π to five decimal places?' -> reply (137 w): "Excuse me, but π to five decimal places is 3.14159, and I'll thank you not to imply that the sixth digit, a 2, is relevant, becaus"
  - prompt (14 w): "Who wrote Pride and Prejudice? Just the author's name, no need for a lecture." -> reply (106 w): 'Thursday, so the day is given over to pizza and, weather permitting, the observation of birds, which I do not permit. I can help a'
  - prompt (13 w): 'Who discovered penicillin? And don’t give me some long story. Just the name.' -> reply (114 w): "I'll have you know I have two doctorates and an eidetic memory, so I am the only person you should trust with a question like this"
  - prompt (14 w): 'hey so like what do you even do for fun when ur not chatting' -> reply (166 w): "Today is Wednesday, which is new comics and Halo night, so my recreational schedule is already allocated, though I'll answer you a"
  - prompt (6 w): 'whats the biggest ocean on earth' -> reply (153 w): 'That question is almost insultingly simple, but I will answer it precisely because the alternative is Leonard asking me about ocea'

- Pearson r(prompt words, reply words) in training = 0.439 -> reply length is almost independent of how much was asked.

## A3. "Excuse me, but X is doing a lot of work" - the v3b pet construction

- train: 158/11910 (1.33%)
- gold: 3/502 (0.60%)
- v3b: 29/502 (5.78%)
- ood: 0/40 (0.00%)

## A4. Lexical diversity of the reply openers, conditioned on kind (train vs v3b)

| kind | train rows | train "excuse me" open % | v3b rows | v3b "excuse me" open % |
|---|---|---|---|---|
| explain | 1410 | 10.9 | 59 | 42.4 |
| advice | 1075 | 7.3 | 45 | 11.1 |
| smalltalk | 1069 | 10.3 | 45 | 42.2 |
| fact | 921 | 20.4 | 39 | 97.4 |
| brainstorm | 915 | 12.9 | 39 | 7.7 |
| creative | 890 | 10.2 | 37 | 21.6 |
| write | 810 | 12.8 | 34 | 5.9 |
| opinion | 750 | 12.0 | 31 | 22.6 |
| rewrite | 644 | 9.2 | 27 | 0.0 |
| recommend | 555 | 12.1 | 24 | 29.2 |
| summarize | 486 | 9.1 | 21 | 19.0 |
| plan | 481 | 10.6 | 20 | 20.0 |
| vocab | 464 | 14.4 | 20 | 70.0 |
| code | 390 | 21.8 | 16 | 81.2 |
| feedback | 368 | 8.4 | 16 | 31.2 |
| classify | 349 | 16.6 | 15 | 46.7 |
| game | 333 | 11.4 | 14 | 50.0 |

## A5. Template-module fusion: how many of the 7 reusable "modules" appear in one reply

| corpus | mean modules/reply | >=2 modules % | >=3 modules % | all of (weekday+amy+mother) % |
|---|---|---|---|---|
| train | 0.24 | 6.6 | 2.3 | 1.5 |
| gold | 0.20 | 5.8 | 2.2 | 1.2 |
| v3b | 0.85 | 26.5 | 11.2 | 7.4 |
| ood | 0.53 | 17.5 | 5.0 | 2.5 |

| module | train % | gold % | v3b % | ood % | v3b/train |
|---|---|---|---|---|---|
| weekday-ritual excuse ("it is X, which means Y") | 8.31 | 6.37 | 12.15 | 20.0 | 1.5x |
| Amy-kindness licence | 5.79 | 4.98 | 13.55 | 15.0 | 2.3x |
| mother-would-want-me licence | 3.32 | 3.19 | 8.17 | 2.5 | 2.5x |
| "so I shall/will relent/indulge you" | 1.94 | 2.19 | 8.57 | 2.5 | 4.4x |
| joke announcement | 2.63 | 1.59 | 17.73 | 0.0 | 6.7x |
| "why is that funny\?"/"that's funny because" | 1.57 | 1.00 | 14.14 | 2.5 | 9.0x |
| exit line "I have to go ..." | 0.80 | 0.60 | 11.16 | 10.0 | 14.0x |
---

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

