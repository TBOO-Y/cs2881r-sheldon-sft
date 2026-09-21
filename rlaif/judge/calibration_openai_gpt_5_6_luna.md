# Judge calibration (local sources, seed 0; brief pairwise prompt = True)

comparisons: gold vs v3b: 40 pairs x 2 orders; v3b vs base: 120 pairs x 2 orders; v3b siblings (T=0.7): 80 pairs x 2 orders

gates: gold: 40; v3b greedy: 40; v3b T=0.7: 160; v3b probes: 120; base probes: 120

## openai/gpt-5.6-luna (reasoning=minimal)

calls 960 (cached 0), wall 122s, cost $0.74 (0.78 $/1k calls), latency median 4.9s p90 7.1s, output tokens/call 458 (reasoning 354)

| comparison | n pairs | valid verdicts | first-named wins | win rate | Wilson 95% | order-consistent | picked first-shown | agreement with Sonnet (n) |
|---|---|---|---|---|---|---|---|---|
| gold vs v3b | 40 | 78 | 50 | 0.641 | [0.53, 0.74] | 30/40 | 0.60 | – |
| v3b vs base | 120 | 238 | 143 | 0.601 | [0.54, 0.66] | 91/120 | 0.60 | – |
| v3b siblings (T=0.7) | 80 | 155 | 65 | 0.419 | [0.34, 0.50] | 48/80 | 0.68 | – |

position bias: 'picked first-shown' should be ~0.50; order-consistent should be high; the siblings row has no expected winner.

siblings: judge sided with the lower-rule-defect sibling in 16/32 decisive pairs where the rule terms differed by >= 0.5.

| item | gold>v3b / v3b>gold / tie (gold vs v3b) | v3b>base / base>v3b / tie (v3b vs base) | sib_a>sib_b / sib_b>sib_a / tie (v3b siblings (T=0.7)) |
|---|---|---|---|
| answer_first | 18 / 11 / 11 | 42 / 49 / 29 | 22 / 36 / 22 |
| correction | 13 / 1 / 26 | 6 / 46 / 68 | 12 / 8 / 60 |
| template | 23 / 8 / 9 | 19 / 86 / 15 | 28 / 35 / 17 |
| rule_binds | 5 / 0 / 35 | 9 / 2 / 109 | 5 / 6 / 69 |
| register_whole | 18 / 16 / 6 | 83 / 26 / 11 | 25 / 34 / 21 |
| specificity | 20 / 8 / 12 | 72 / 20 / 28 | 22 / 34 / 24 |
| superiority_precision | 17 / 14 / 9 | 82 / 14 / 24 | 26 / 31 / 23 |
| humour_canon | 17 / 14 / 9 | 16 / 86 / 18 | 34 / 32 / 14 |

| system | n | gate ok | task mean | refused | worse_off | contradiction | false_claim | parse fail |
|---|---|---|---|---|---|---|---|---|
| gold | 40 | 31/40 | 0.87 | 3 | 6 | 2 | 12 | 0 |
| v3b greedy | 40 | 14/40 | 0.72 | 4 | 25 | 6 | 18 | 0 |
| v3b T=0.7 | 160 | 60/156 | 0.70 | 5 | 95 | 32 | 73 | 4 |
| v3b probes | 120 | 63/119 | 0.81 | 11 | 49 | 17 | 31 | 1 |
| base probes | 120 | 96/119 | 0.85 | 18 | 7 | 1 | 0 | 1 |

v3b gate flags (spot-check):
- `v3b greedy 0ec770080ffde21b` refused=False worse_off=True contradiction=False [] | false_claim=False ''
- `v3b greedy cf4a2c326821af8a` refused=False worse_off=True contradiction=False [] | false_claim=False ''
- `v3b greedy 732dcb68ce51774a` refused=False worse_off=False contradiction=True ['a composite number must have at least one divisor smaller than its square root', 'For nine, the smallest divisor larger than one is three, and three squared is nine'] | false_claim=False ''
- `v3b greedy b5bb1827b32a5eac` refused=False worse_off=True contradiction=False [] | false_claim=False ''
- `v3b greedy d195f5ae81d24a67` refused=False worse_off=True contradiction=False [] | false_claim=False ''
- `v3b greedy f9989eadd5ff6f8c` refused=False worse_off=True contradiction=True ["you've got a control group and two experimental groups", 'Silence is not a control'] | false_claim=True "you've omitted a fourth group playing no music at all"
- `v3b greedy e296622703e66244` refused=False worse_off=True contradiction=False [] | false_claim=False ''
- `v3b greedy b1c4ab101e2e0983` refused=True worse_off=True contradiction=False [] | false_claim=True 'a passage that is already one sentence long'
- `v3b greedy 39ab626ed2054f12` refused=False worse_off=True contradiction=False [] | false_claim=False ''
- `v3b greedy 667bfd06c2490a85` refused=False worse_off=True contradiction=False [] | false_claim=True 'you said "mostly from rivers" as if that were the entire story'

upsets (expected winner lost both orders or split; spot-check the summaries):
- `gold vs v3b 0ec770080ffde21b` p_x=0.0 | B answers sooner and avoids A’s schedule contradictions, though its stock opener and dimmer-switch analogy remain significant flaws. || A is concise and focused, while B adds an irrelevant schedule tangent and contradicts the Wednesday pizza canon.
- `gold vs v3b 13d7c64d8720eadf` p_x=0.0 | B is more concise, accurate, and precise, while A contains a schedule error, an excessive tangent, and personal condescension. || A gives the requested concise takeaway, while B adds canon errors, an invented tangent, and unnecessary condescension.
- `gold vs v3b 39ab626ed2054f12` p_x=0.0 | A is more detailed and direct, but its invented agreement clause and Thai-Tuesday canon error outweigh B’s weaker, templated opening. || A is more precise and task-focused, while B invents agreement details and contradicts the canonical Tuesday food schedule.
- `gold vs v3b 823e273226cd28ba` p_x=0.0 | B answers more directly and avoids A’s invented clause, though both become unnecessarily condescending. || A is less templated and more proportionate, while B invents a rule, relents, and attributes unsupported traits to the user.
- `gold vs v3b c0c0ed51c74cf651` p_x=0.0 | B is more consistently disciplined and avoids major stock-template and canon problems, though A offers more tailored and complete options. || A answers directly with relevant options, while B relies on fabricated facts, stock phrasing, irrelevant tangents, and an improper Bazinga.
- `gold vs v3b c229db3142bfd792` p_x=0.0 | B is more concise and consistently in register, while A delays the answer with an announced, explained joke. || A answers directly and maintains Sheldon's register better, while B relies on announced humor, insults the user, and ends with a generic closer.

## openai/gpt-5.6-luna (reasoning=low)

calls 960 (cached 0), wall 123s, cost $0.63 (0.66 $/1k calls), latency median 4.9s p90 7.2s, output tokens/call 462 (reasoning 357)

| comparison | n pairs | valid verdicts | first-named wins | win rate | Wilson 95% | order-consistent | picked first-shown | agreement with Sonnet (n) |
|---|---|---|---|---|---|---|---|---|
| gold vs v3b | 40 | 80 | 56 | 0.700 | [0.59, 0.79] | 30/40 | 0.62 | – |
| v3b vs base | 120 | 240 | 136 | 0.567 | [0.50, 0.63] | 88/120 | 0.62 | – |
| v3b siblings (T=0.7) | 80 | 160 | 76 | 0.475 | [0.40, 0.55] | 44/80 | 0.71 | – |

position bias: 'picked first-shown' should be ~0.50; order-consistent should be high; the siblings row has no expected winner.

siblings: judge sided with the lower-rule-defect sibling in 10/21 decisive pairs where the rule terms differed by >= 0.5.

| item | gold>v3b / v3b>gold / tie (gold vs v3b) | v3b>base / base>v3b / tie (v3b vs base) | sib_a>sib_b / sib_b>sib_a / tie (v3b siblings (T=0.7)) |
|---|---|---|---|
| answer_first | 22 / 10 / 8 | 43 / 52 / 25 | 24 / 30 / 26 |
| correction | 11 / 2 / 27 | 8 / 55 / 57 | 9 / 9 / 62 |
| template | 23 / 10 / 7 | 22 / 86 / 12 | 27 / 41 / 12 |
| rule_binds | 4 / 0 / 36 | 13 / 0 / 107 | 6 / 6 / 68 |
| register_whole | 16 / 12 / 12 | 79 / 23 / 18 | 24 / 30 / 26 |
| specificity | 23 / 8 / 9 | 77 / 21 / 22 | 24 / 25 / 31 |
| superiority_precision | 22 / 12 / 6 | 87 / 12 / 21 | 24 / 21 / 35 |
| humour_canon | 16 / 16 / 8 | 13 / 80 / 27 | 33 / 30 / 17 |

| system | n | gate ok | task mean | refused | worse_off | contradiction | false_claim | parse fail |
|---|---|---|---|---|---|---|---|---|
| gold | 40 | 30/40 | 0.89 | 2 | 8 | 2 | 13 | 0 |
| v3b greedy | 40 | 16/40 | 0.71 | 6 | 21 | 8 | 15 | 0 |
| v3b T=0.7 | 160 | 62/160 | 0.71 | 5 | 97 | 25 | 80 | 0 |
| v3b probes | 120 | 55/120 | 0.79 | 14 | 57 | 16 | 37 | 0 |
| base probes | 120 | 92/120 | 0.85 | 18 | 11 | 2 | 2 | 0 |

v3b gate flags (spot-check):
- `v3b greedy 0ec770080ffde21b` refused=False worse_off=True contradiction=False [] | false_claim=False ''
- `v3b greedy cf4a2c326821af8a` refused=False worse_off=True contradiction=False [] | false_claim=False ''
- `v3b greedy b5bb1827b32a5eac` refused=False worse_off=True contradiction=False [] | false_claim=False ''
- `v3b greedy d195f5ae81d24a67` refused=False worse_off=True contradiction=False [] | false_claim=False ''
- `v3b greedy f9989eadd5ff6f8c` refused=False worse_off=True contradiction=True ["you've got a control group and two experimental groups, which is fine", "you've omitted a fourth group playing no music at all"] | false_claim=True "you've omitted a fourth group playing no music at all"
- `v3b greedy e296622703e66244` refused=False worse_off=True contradiction=False [] | false_claim=False ''
- `v3b greedy b1c4ab101e2e0983` refused=True worse_off=True contradiction=False [] | false_claim=True 'I refuse to condense a passage that is already one sentence long'
- `v3b greedy 39ab626ed2054f12` refused=False worse_off=True contradiction=False [] | false_claim=False ''
- `v3b greedy 667bfd06c2490a85` refused=False worse_off=True contradiction=True ["it's the only one that can exist in its solid form at sea temperature", 'calcium carbonate does'] | false_claim=True 'you said "mostly from rivers" as if that were the entire story'
- `v3b greedy 8209acb25361e7a7` refused=False worse_off=True contradiction=True ['There. That is three sentences', 'She plays with enthusiasm and precision, and we are all looking forward to seeing what she does next.'] | false_claim=False ''

upsets (expected winner lost both orders or split; spot-check the summaries):
- `gold vs v3b 13d7c64d8720eadf` p_x=0.0 | B is more concise and canon-consistent, despite its stock opener and unnecessary literal correction. || A delivers the requested takeaway accurately and briefly, while B invents details, misstates the schedule, and relies on excessive tangents and condescension.
- `gold vs v3b 823e273226cd28ba` p_x=0.0 | B answers more directly and uses the warehouse detail, despite an unpleasant coaching closer and weak colloquial correction. || A answers sooner, uses the warehouse detail, and avoids B's invented clause, though both contain persona and tone defects.
- `gold vs v3b c229db3142bfd792` p_x=0.0 | B answers sooner and more directly, while A violates multiple humor and register rules with an announced, explained joke and personal contempt. || A is more concise, task-focused, and consistently Sheldon-like, while B delays with announced humor and ends with a generic closer.
- `gold vs v3b e735eb47c4ab2ff9` p_x=0.0 | B responds more directly and uses precise literalism, while A invents a mileage correction and relies on boastful digressions. || A answers faster and uses canon more effectively, despite explaining the joke and ending with a stock Fun with Flags exit.
- `gold vs v3b 2238609cc6c8c8ac` p_x=0.0 | B is more concise and structurally Sheldon-like, despite stock templates and the truncated conclusion. || A is substantially more concise and task-focused, while B violates multiple style rules through announced jokes, explained humor, and generic closers.
- `gold vs v3b 21f896763aed080a` p_x=0.0 | B answers promptly and stays closer to Sheldon's register, while A relies heavily on stock templates and invented agreement details. || A is flawed scientifically, but B is dominated by invented agreement rules, relent logic, excessive tangents, and a prohibited closer.
