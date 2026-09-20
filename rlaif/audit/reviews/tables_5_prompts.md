## 5. Prompt distribution of the training data

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

| n | rows | %% of rows with a system prompt | text |
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
