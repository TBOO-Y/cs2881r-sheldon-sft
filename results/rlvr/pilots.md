## Models (full suite)

| model | MATH-500 greedy | avg@4 | L3-5 avg@4 | L1 | L2 | L3 | L4 | L5 | GSM8K | AIME24 avg@16 | AIME25 | AIME26 | AIME pass@16 | tokens | hit cap | boxed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| base | 68.0 | 66.6 | 59.0 | 91.9 | 85.8 | 81.2 | 60.5 | 40.1 | 86.1 | 8.1 | 2.3 | 4.4 | 21.1 | 633 | 0.9 | 99.1 |
| grpo-v2 | 34.0 | 29.6 | 21.0 | 64.5 | 48.3 | 33.3 | 21.7 | 10.6 | 63.6 | 0.4 | 0.4 | 0.0 | 3.3 | 357 | 4.2 | 95.7 |

## pilot-full-adamw

training: steps=20, reward_first=0.418, reward_last=0.451, acc_last=0.451, trunc_last=0, zero_var_last=0.125, len_last=156, grad_norm=1.3, s_per_step=20.1

| model | MATH-500 greedy | avg@4 | L3-5 avg@4 | L1 | L2 | L3 | L4 | L5 | GSM8K | AIME24 avg@16 | AIME25 | AIME26 | AIME pass@16 | tokens | hit cap | boxed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pilot-full-adamw/checkpoint-20 | - | 31.9 | 22.8 | 65.7 | 52.8 | 41.0 | 22.7 | 8.8 | 63.8 | - | - | - | - | 331 | 3.2 | 96.7 |

## pilot-lora-adamw

training: steps=20, reward_first=0.434, reward_last=0.438, acc_last=0.438, trunc_last=0.000781, zero_var_last=0.175, len_last=162, grad_norm=0.13, s_per_step=20.6

| model | MATH-500 greedy | avg@4 | L3-5 avg@4 | L1 | L2 | L3 | L4 | L5 | GSM8K | AIME24 avg@16 | AIME25 | AIME26 | AIME pass@16 | tokens | hit cap | boxed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pilot-lora-adamw/checkpoint-20 | - | 35.1 | 25.7 | 69.2 | 56.9 | 42.1 | 25.4 | 13.2 | 65.0 | - | - | - | - | 346 | 3.6 | 96.2 |

## pilot-lora-lenpen

training: steps=20, reward_first=0.42, reward_last=0.443, acc_last=0.443, trunc_last=0, zero_var_last=0.15, len_last=161, grad_norm=0.128, s_per_step=19.6

| model | MATH-500 greedy | avg@4 | L3-5 avg@4 | L1 | L2 | L3 | L4 | L5 | GSM8K | AIME24 avg@16 | AIME25 | AIME26 | AIME pass@16 | tokens | hit cap | boxed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pilot-lora-lenpen/checkpoint-20 | - | 34.9 | 26.2 | 62.2 | 57.8 | 42.9 | 27.5 | 11.8 | 64.9 | - | - | - | - | 327 | 3.0 | 96.9 |

