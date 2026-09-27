# Persona evaluation: rlvr-4-combined vs grpo-v2 (2026-09-27)

## Collapse / defect monitors (502 held-out prompts, greedy, 400 tokens; rlaif/audit/quant/compare.py)
```
502 common ids

metric                          rlvr-4-combined     grpo-v2        gold
style/opener_entropy_bits              8.483       5.889       7.498
style/distinct_openers_frac            0.807       0.444       0.622
style/template_opener_frac             0.042       0.637       0.345
style/joke_meta                        0.000       0.303       0.030
style/relent_block                     0.002       0.034       0.050
style/tuesday_thai                     0.000       0.016       0.012
style/excuse_me_closer                 0.000       0.052       0.082
style/bazinga                          0.000       0.012       0.112
style/leonard                          0.054       0.297       0.458
style/any_name                         0.076       0.388       0.699
style/names_per_reply                  0.084       0.446       1.070
style/warm_closer                      0.010       0.014       0.042
style/mean_words                      90.062     213.420     261.938
style/ends_midsentence                 0.010       0.159       0.000
hit_max%                               0.996      17.530       0.000
rule_penalty                           0.154       0.870       0.653
batch_tax                              0.025       0.378       0.403
term/preamble                          0.032       0.263       0.244
term/length                            0.010       0.125       0.216
term/canon                             0.004       0.022       0.054
term/tool_voice                        0.020       0.056       0.081
term/constraint                        0.002       0.008       0.006
term/false_claim                       0.000       0.012       0.006
term/repetition                        0.048       0.131       0.006
term/truncation                        0.012       0.175       0.000
```

## Short prompts (60)
```
60 common ids

metric                          rlvr-4-combined     grpo-v2
style/opener_entropy_bits              5.828       5.647
style/distinct_openers_frac            0.967       0.900
style/template_opener_frac             0.033       0.083
style/joke_meta                        0.000       0.033
style/relent_block                     0.000       0.000
style/tuesday_thai                     0.000       0.000
style/excuse_me_closer                 0.000       0.000
style/bazinga                          0.000       0.000
style/leonard                          0.017       0.150
style/any_name                         0.017       0.150
style/names_per_reply                  0.017       0.167
style/warm_closer                      0.000       0.000
style/mean_words                      25.567      69.250
style/ends_midsentence                 0.000       0.050
hit_max%                               0.000       0.000
rule_penalty                           0.033       0.282
batch_tax                              0.010       0.083
term/preamble                          0.000       0.083
term/length                            0.000       0.133
term/canon                             0.000       0.000
term/tool_voice                        0.000       0.000
term/constraint                        0.000       0.000
term/false_claim                       0.033       0.000
term/repetition                        0.000       0.000
term/truncation                        0.000       0.000
```

## Persona leakage into MATH-500 answers (greedy eval files; share of answers naming Sheldon / cast or saying Bazinga)
- rlvr-4-combined: 0.4% of 500 answers
- grpo-v2: 2.8% of 500 answers
- base: 0.2% of 500 answers
 },
 "usage": {
  "calls": 400,
  "cached_calls": 0,
  "prompt_tokens": 1422922,
  "cached_prompt_tokens": 984000,
  "completion_tokens": 249482,
  "reasoning_tokens": 120007,
  "cost_usd": 0.428729,
  "price_unknown_models": [],
  "errors": 0,
  "retries": 0
 }
}
