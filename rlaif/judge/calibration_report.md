# Cheap-judge calibration (50 held-out ids, seed 0; same ids as the Sonnet judge)

## gpt-4.1-nano

calls 450 (cached 0), wall 482s, est. cost $0.12

| pair | valid verdicts | first wins | win rate | Wilson 95% | order-consistent pairs | agreement with Sonnet (n) |
|---|---|---|---|---|---|---|
| v3b vs base | 92 | 48 | 0.522 | [0.42, 0.62] | 6/50 | 0.54 (92) |
| gold vs base | 95 | 51 | 0.537 | [0.44, 0.63] | 10/50 | 0.54 (95) |
| gold vs v3b | 88 | 46 | 0.523 | [0.42, 0.62] | 4/50 | – |

position bias: picked the first-shown reply in 0.91 of verdicts (0.50 = none)

| item | gold>v3b | v3b>gold | tie/split | v3b>base | gold>base |
|---|---|---|---|---|---|
| answer_first | 4 | 4 | 40 | 6/50 | 2/50 |
| correction | 13 | 15 | 20 | 17/50 | 11/50 |
| template | 9 | 12 | 27 | 4/50 | 7/50 |
| rule_binds | 8 | 2 | 38 | 5/50 | 5/50 |
| register_whole | 12 | 10 | 26 | 9/50 | 17/50 |
| specificity | 17 | 11 | 20 | 16/50 | 24/50 |
| superiority_precision | 9 | 6 | 33 | 14/50 | 19/50 |
| humour_canon | 14 | 6 | 28 | 9/50 | 13/50 |

| system | gate ok | task mean | refused | worse_off | contradiction | false_claim | parse fail |
|---|---|---|---|---|---|---|---|
| gold | 50/50 | 0.98 | 0 | 0 | 0 | 0 | 0 |
| v3b | 50/50 | 0.97 | 0 | 0 | 0 | 0 | 0 |
| base | 50/50 | 0.96 | 0 | 0 | 0 | 0 | 0 |


## Notes (2026-09-19)

- gpt-4.1-nano is unusable as the pairwise persona judge: it picks the first-shown reply in 91% of verdicts, so every win rate collapses to ~0.52 regardless of the pair (Sonnet: v3b beats base 0.98, gold beats base 1.00), only 4–10 of 50 pairs are order-consistent, and agreement with Sonnet is 0.54 (chance). Its task gate also flags nothing (0 contradictions, 0 false claims on v3b, where the audit found ~35% self-contradiction).
- The gpt-5-nano run was cut off after 116 calls and gpt-4.1-mini never ran: the OpenAI account behind `OPENAI_API_KEY_2` was terminated mid-run ("Your access was terminated due to violation of our policies"). The primary key was already dead (401). Raw verdicts for gpt-4.1-nano are in `calibration_raw.jsonl`.
- Conclusion: the judge must be at least mini-class (gpt-4.1-mini / gpt-5-mini) or Claude Haiku 4.5; re-run this calibration on the chosen model before any RL spend.
