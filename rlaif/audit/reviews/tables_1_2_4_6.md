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

## 2. Opener and closer distributions

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

### (last sentence, first 4 words)

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

## 4. Register

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

Per-phrase coaching breakdown (%% of rows, anywhere in reply):

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

## 6. Assistant-reply length (words)

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
