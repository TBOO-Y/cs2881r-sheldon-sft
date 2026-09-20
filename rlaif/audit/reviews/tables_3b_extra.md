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
