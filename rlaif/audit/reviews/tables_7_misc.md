## 7a. Position-conditional tics (where in the reply the tic sits)

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

## 7b. The short-prompt slice of the training data

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

## 7c. "Excuse me, but X is doing a lot of work" - the v3b pet construction

- train: 158/11910 (1.33%)
- gold: 3/502 (0.60%)
- v3b: 29/502 (5.78%)
- ood: 0/40 (0.00%)

## 7d. Lexical diversity of the reply openers, conditioned on kind (train vs v3b)

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
