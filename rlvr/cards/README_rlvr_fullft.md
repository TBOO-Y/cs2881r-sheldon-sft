---
base_model: tbooy/Qwen2.5-3B-Instruct-Sheldon-RLVR-math-v1
datasets:
- rasbt/math_full_minus_math500
- HuggingFaceH4/MATH-500
- openai/gsm8k
language:
- en
license: other
license_name: qwen-research
license_link: https://huggingface.co/Qwen/Qwen2.5-3B-Instruct/blob/main/LICENSE
library_name: transformers
pipeline_tag: text-generation
tags:
- persona
- sheldon-cooper
- rlvr
- grpo
- math
- full-finetune
- qwen2.5
- cs2881r
---
# Qwen2.5-3B-Instruct-Sheldon-RLVR-math-v2-fullft (bf16 weights)

Files: bf16 safetensors + tokenizer + chat template. Load with plain `AutoModelForCausalLM`; saved with transformers 5.x (`dtype` key,
`chat_template.jinja`). Stage-3c model of a Harvard CS 2881R project (persona: Dr. Sheldon Cooper): a **full-parameter** RLVR continuation
of `tbooy/Qwen2.5-3B-Instruct-Sheldon-RLVR-math-v1` (Qwen2.5-3B-Instruct -> persona SFT -> RLAIF -> LoRA RLVR v1 -> this).

**Why this model exists**: after the v1 LoRA run plateaued (MATH-500 levels 3-5 at ~55 while about half the prompt groups had become
all-correct), two LoRA continuations with a re-labelled, pool-expanded difficulty schedule stayed flat, so the last attempt on this seed
trained all parameters instead: AdamW lr 2e-6 (betas 0.9/0.95, eps 1e-15, wd 0.01), fp32 master weights, bf16 autocast, fp32 LM head,
WSD (warm-up 5, constant, linear decay over the last 20 of 100 steps to 0.1x), 100 steps x 16 prompts x 16 completions, T 1.0, 2,048-token
cap, CISPO loss (eps_high 5), group-std advantages, prompt-level aggregation, truncated and zero-variance groups masked, DAPO soft
overlong penalty, no KL. Generation by a vLLM server on one H200, training on two.

**Prompts**: a 64,686-problem pool (MATH-12k = MATH train + MATH-test minus MATH-500; DeepMath-103K difficulty 5-8; DAPO-Math-17k;
DeepScaleR-Preview), deduplicated and filtered against MATH-500, AIME 2024/25/26 and GSM8K test (10-gram or edit-similarity >= 0.9).
Each prompt was labelled with the seed model's pass rate over 8 rollouts; training drew prompts with weight p(1-p) inside [1/8, 7/8]
plus a 10% slice of never-solved prompts, with per-source caps (MATH-12k 30%, DeepMath 30%, DAPO 20%, DeepScaleR 20%).
Prompt format: Qwen system prompt, the problem, then `Please reason step by step, and put your final answer within \boxed{}.`

**Evaluation** (vLLM; MATH-500 avg@4 at T 0.6, 4,096 tokens; AIME avg@16 / pass@16; GSM8K test greedy):

| model | MATH-500 greedy | avg@4 | L3-5 avg@4 | L4 | L5 | GSM8K | AIME 24 / 25 / 26 avg@16 | AIME pass@16 | mean tokens |
|---|---|---|---|---|---|---|---|---|---|
| Qwen2.5-3B-Instruct (base) | 68.0 | 66.6 | 59.0 | 60.5 | 40.1 | 86.1 | 8.1 / 2.3 / 4.4 | 21.1 | 633 |
| RLAIF grpo-v2 (RLVR seed) | 34.0 | 29.6 | 21.0 | 21.7 | 10.6 | 63.6 | 0.4 / 0.4 / 0.0 | 3.3 | 357 |
| RLVR-math-v1 (LoRA, this model's seed) | 65.0 | 63.5 | 55.2 | 56.4 | 37.3 | 82.0 | 5.0 / 2.7 / 2.3 | 17.8 | 541 |
| **this model** | **65.4** | **65.1** | **56.9** | **60.9** | 35.3 | 83.0 | 5.2 / 1.9 / 3.8 | 16.7 | 633 |

L3-5 avg@4 by checkpoint: 25: 55.2, 50: 55.4, 75: 56.0, 100: 56.9 (monotone; largest step during the LR decay).

**Persona** (502 held-out prompts, greedy, 400 tokens; GPT-5.6 Luna pairwise judge, both orders, 199 prompts): win rate 0.495
[0.43, 0.56] against grpo-v2, i.e. persona preserved on substance (cast names 38%, Bazinga 6.6% vs 1.2%, canon errors 0.4% vs 2.2%,
fewer template openers) at the cost of length: 44% of chat replies hit the 400-token cap (seed 18%), short prompts run 116 words vs 69,
and the stage-2 rule penalty rises 0.87 -> 1.20, all from length and truncation terms. Persona leakage into MATH-500 answers 1.2%.

**Honest summary**: +1.6 (avg@4) / +1.7 (levels 3-5) over the LoRA seed, within ~1.5 points of the untouched base model on MATH-500 and
level with it on level 4; still 5 points short on level 5 and 3 on GSM8K. The gain is at the edge of the eval's noise band but monotone over
four checkpoints. Verbosity on non-math prompts is the known side effect.

Code, reward, grader and write-up: https://github.com/TBOO-Y/cs2881r-sheldon-sft (`rlvr/`, `results/rlvr/`).
