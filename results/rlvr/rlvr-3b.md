## Models (full suite)

| model | MATH-500 greedy | avg@4 | L3-5 avg@4 | L1 | L2 | L3 | L4 | L5 | GSM8K | AIME24 avg@16 | AIME25 | AIME26 | AIME pass@16 | tokens | hit cap | boxed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rlvr-main | 65.0 | 63.5 | 55.2 | 90.1 | 84.7 | 76.4 | 56.4 | 37.3 | 81.9 | 5.0 | 2.7 | 2.3 | 17.8 | 541 | 1.6 | 98.5 |
| base | 68.0 | 66.6 | 59.0 | 91.9 | 85.8 | 81.2 | 60.5 | 40.1 | 86.1 | 8.1 | 2.3 | 4.4 | 21.1 | 633 | 0.9 | 99.1 |

## rlvr-3b-s1

training: steps=50, reward_first=0.411, reward_last=0.38, acc_last=0.384, trunc_last=0.00879, zero_var_last=0.125, len_last=672, grad_norm=0.0575, drift=0.0214, s_per_step=50.6

| model | MATH-500 greedy | avg@4 | L3-5 avg@4 | L1 | L2 | L3 | L4 | L5 | GSM8K | AIME24 avg@16 | AIME25 | AIME26 | AIME pass@16 | tokens | hit cap | boxed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rlvr-3b-s1/checkpoint-50 | - | 63.3 | 55.0 | 89.0 | 85.0 | 78.3 | 58.0 | 34.0 | 83.0 | - | - | - | - | 518 | 1.7 | 98.3 |

## rlvr-3b-s2

training: steps=50, reward_first=0.424, reward_last=0.402, acc_last=0.408, trunc_last=0.012, zero_var_last=0.0573, len_last=663, grad_norm=0.0569, drift=0.0215, s_per_step=53.5

| model | MATH-500 greedy | avg@4 | L3-5 avg@4 | L1 | L2 | L3 | L4 | L5 | GSM8K | AIME24 avg@16 | AIME25 | AIME26 | AIME pass@16 | tokens | hit cap | boxed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rlvr-3b-s2/checkpoint-50 | - | 63.6 | 55.3 | 89.5 | 85.3 | 77.4 | 58.8 | 34.7 | 82.0 | - | - | - | - | 500 | 0.9 | 99.1 |

