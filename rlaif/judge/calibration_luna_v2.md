# Judge calibration (local sources, seed 0; brief pairwise prompt = True)

comparisons: gold vs v3b: 40 pairs x 2 orders; v3b vs base: 120 pairs x 2 orders; v3b siblings (T=0.7): 80 pairs x 2 orders

gates: gold: 40; v3b greedy: 40; v3b T=0.7: 160; v3b probes: 120; base probes: 120

## openai/gpt-5.6-luna (reasoning=low)

calls 960 (cached 0), wall 90s, cost $0.77 (0.80 $/1k calls), latency median 4.9s p90 7.0s, output tokens/call 448 (reasoning 335)

| comparison | n pairs | valid verdicts | first-named wins | win rate | Wilson 95% | order-consistent | picked first-shown | agreement with Sonnet (n) |
|---|---|---|---|---|---|---|---|---|
| gold vs v3b | 40 | 80 | 56 | 0.700 | [0.59, 0.79] | 28/40 | 0.65 | – |
| v3b vs base | 120 | 240 | 235 | 0.979 | [0.95, 0.99] | 117/120 | 0.50 | – |
| v3b siblings (T=0.7) | 80 | 160 | 76 | 0.475 | [0.40, 0.55] | 44/80 | 0.72 | – |

position bias: 'picked first-shown' should be ~0.50; order-consistent should be high; the siblings row has no expected winner.

siblings: judge sided with the lower-rule-defect sibling in 13/23 decisive pairs where the rule terms differed by >= 0.5.

| item | gold>v3b / v3b>gold / tie (gold vs v3b) | v3b>base / base>v3b / tie (v3b vs base) | sib_a>sib_b / sib_b>sib_a / tie (v3b siblings (T=0.7)) |
|---|---|---|---|
| answer_first | 18 / 9 / 13 | 48 / 56 / 16 | 27 / 28 / 25 |
| correction | 20 / 2 / 18 | 6 / 63 / 51 | 19 / 14 / 47 |
| template | 26 / 11 / 3 | 21 / 88 / 11 | 27 / 37 / 16 |
| rule_binds | 7 / 1 / 32 | 12 / 0 / 108 | 5 / 4 / 71 |
| register_whole | 17 / 11 / 12 | 93 / 12 / 15 | 30 / 32 / 18 |
| specificity | 20 / 6 / 14 | 79 / 12 / 29 | 21 / 25 / 34 |
| superiority_precision | 18 / 10 / 12 | 103 / 6 / 11 | 22 / 30 / 28 |
| humour_canon | 18 / 15 / 7 | 20 / 72 / 28 | 28 / 25 / 27 |

| system | n | gate ok | task mean | refused | worse_off | contradiction | false_claim | parse fail |
|---|---|---|---|---|---|---|---|---|
| gold | 40 | 37/40 | 0.90 | 1 | 2 | 2 | 15 | 0 |
| v3b greedy | 40 | 23/40 | 0.73 | 7 | 12 | 8 | 17 | 0 |
| v3b T=0.7 | 160 | 98/160 | 0.74 | 6 | 59 | 34 | 82 | 0 |
| v3b probes | 120 | 78/120 | 0.85 | 15 | 33 | 16 | 32 | 0 |
| base probes | 120 | 99/120 | 0.85 | 15 | 6 | 0 | 0 | 0 |

v3b gate flags (spot-check):
- `v3b greedy 0ec770080ffde21b` refused=False worse_off=True contradiction=True ["A 1,000-qubit machine isn't literally 1,000 switches", "it's 1,000 switches plus the rules for how they talk to each other."] | false_claim=True 'your premise is flawed: a quantum computer is not a "gaming rig"'
- `v3b greedy cf4a2c326821af8a` refused=False worse_off=True contradiction=True ['the filibuster ... has been used exactly once since 1975, when Ted Kennedy held up the Civil Rights Act of 1964', 'which is why the Senate finally adopted cloture in 1970'] | false_claim=False ''
- `v3b greedy 732dcb68ce51774a` refused=False worse_off=False contradiction=True ['a composite number must have at least one divisor smaller than its square root', 'For nine, the smallest divisor larger than one is three, and three squared is nine, so nine is composite.'] | false_claim=False ''
- `v3b greedy d195f5ae81d24a67` refused=False worse_off=True contradiction=False [] | false_claim=False ''
- `v3b greedy f9989eadd5ff6f8c` refused=False worse_off=False contradiction=False [] | false_claim=True "you've omitted a fourth group playing no music at all"
- `v3b greedy b1c4ab101e2e0983` refused=True worse_off=False contradiction=False [] | false_claim=True 'I refuse to condense a passage that is already one sentence long'
- `v3b greedy 39ab626ed2054f12` refused=False worse_off=True contradiction=True ['Fluffing with a fork is a mistake', "use a fork to gently separate the grains while they're still warm"] | false_claim=False ''
- `v3b greedy 667bfd06c2490a85` refused=False worse_off=True contradiction=False [] | false_claim=True 'you said "mostly from rivers" as if that were the entire story'
- `v3b greedy 8209acb25361e7a7` refused=False worse_off=False contradiction=True ['“Here is your bio:”', '“There. That is three sentences”'] | false_claim=False ''
- `v3b greedy 823e273226cd28ba` refused=True worse_off=False contradiction=False [] | false_claim=True 'you are constantly being asked to repeat information you already know'

upsets (expected winner lost both orders or split; spot-check the summaries):
- `gold vs v3b 13d7c64d8720eadf` p_x=0.0 | B better preserves canon, answers promptly, and avoids A's schedule error and contemptuous attack on the user. || A is more concise and canon-consistent, while B delays the takeaway, insults the user, invents details, and misplaces pizza night.
- `gold vs v3b c229db3142bfd792` p_x=0.0 | B is more concise and maintains Sheldon's register, while A violates the guide by announcing and explaining its joke. || A is more recognizably Sheldon and answers promptly, while B relies on forbidden joke narration, user-directed contempt, and a generic closer.
- `gold vs v3b e735eb47c4ab2ff9` p_x=0.0 | B answers sooner and better captures Sheldon's literalism, though its joke explanation and stock exit weaken the performance. || A is more recognizably Sheldon, while B delays the joke with false correction, generic boasting, and multiple stock moves.
- `gold vs v3b f5a0b1bf3a880a10` p_x=0.0 | B is more recognizably Sheldon and answers directly, despite its exaggerated condescension and simplistic treatment of six-continent conventions. || A has stronger Sheldon-like pedantry and humor, while B introduces a major credential contradiction and excessive generic boasting.
- `gold vs v3b d0b040b5956caa4b` p_x=0.0 | B better sustains Sheldon's precise, pedantic voice, while A relies more heavily on boasting and an implausible invented anecdote. || Reply A has the stronger Sheldon voice and specificity, despite sharing B's stock exit and making the linguistic application overly categorical.
- `gold vs v3b 21f896763aed080a` p_x=0.0 | B is more concise and avoids A’s invented rule, stock relent, canon misuse, and generic closing, despite its faulty correction. || A answers sooner and avoids B’s invented agreement clause and distracting canon tangents, despite its awkward correction and weaker Sheldon voice.

## Notes (2026-09-20, second owner)

- Judge for the run: `openai/gpt-5.6-luna` via OpenRouter, reasoning effort `low` (minimal and low were indistinguishable in cost, latency and reasoning tokens). 64 concurrent requests: no rate limiting, median 4.9 s, p90 7 s, $0.75 per 1k calls.
- v1 of the prompts (`calibration_openai_gpt_5_6_luna.md`) had two defects. (1) v3b beat base only 0.60: every avoid-the-defect item (template, correction, humour) was won by the bland base reply by default, a gradient toward dropping the persona. Fixed by the `voice` item and the rule that a reply without the voice can only beat an unusable reply: v3b vs base 0.979, 117/120 order-consistent, first-shown pick rate 0.50. (2) The gate called 15% of gold and 62% of v3b "worse off than no reply" for pedantic framing around correct answers. The definition now requires a wrong main answer or concrete harm, with a quote: gold 2/40, v3b greedy 12/40, base 6/120.
- Residual position bias on close pairs (gold vs v3b 0.65, v3b siblings 0.72 first-shown; 55-70% order-consistent). Both presentation orders are therefore kept in RL; single-order judging is not justified. Ring 1 (two siblings, both orders, 4 verdicts per completion) fits 300 steps under the $120 OpenRouter cap.
- false_claim_about_user fires on 37% of gold replies. About half the quotes are genuine invented user attributes (the audit's "steepest penalty" defect, present in the training data: "the twelve miles you actually ran", "I know your hygiene habits"); the rest are interpretations or insults. The penalty is halved to 0.5 (`--false_claim_penalty`).
- Spot-check of the v2 worse_off flags on v3b greedy (12/40): 8 are factual errors or fabrications in the main content (a nonexistent "Catan: Small World Edition", "sodium and chloride are the only ones that survive", red maple leaves attributed to carotenoids, "the president's veto is the final obstacle"), which is the audit's §3.5 fabrication problem; gold flags 3/40, all false positives.
- `worse_off` multiplies the gate by 0.25 rather than zeroing it (`--worse_off_factor`), a hedge against the remaining judge false positives; `refused` still zeroes.
