---
base_model: tbooy/Qwen2.5-3B-Instruct-Sheldon-RLVR-math-v2-fullft
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
- rlaif
- combined-reward
- grpo
- math
- full-finetune
- qwen2.5
- cs2881r
---
# Qwen2.5-3B-Instruct-Sheldon-Combined-v1 (bf16 weights)

Files: bf16 safetensors + tokenizer + chat template; plain `AutoModelForCausalLM`, transformers 5.x format. Stage-4 model of a Harvard
CS 2881R project (persona: Dr. Sheldon Cooper): a full-parameter RL continuation of `tbooy/Qwen2.5-3B-Instruct-Sheldon-RLVR-math-v2-fullft`
with a **combined reward**: each step mixes 8 competition-math prompts scored by an exact-answer verifier (+ DAPO soft length penalty) and
8 persona prompts scored by the stage-2 judged reward (task gate x (2 x pairwise persona win rate + form) - 17 rule penalties - false-claim
penalty - batch tax; judge GPT-5.6 Luna via OpenRouter, both presentation orders). Group-normalised advantages keep the two reward scales
separate; truncated and zero-variance groups are masked; CISPO loss; AdamW 2e-6, fp32 master weights, WSD; 80 steps x 16 prompts x 16
completions, 2,048-token cap; 1 h 48 min on 3x H200.

**Evaluation** (MATH-500 avg@4 at T 0.6, 4k tokens; AIME avg@16 / pass@16; GSM8K greedy; persona: 502 held-out prompts, greedy, 400 tokens,
GPT-5.6 Luna pairwise judge vs the RLAIF seed `grpo-v2`, both orders, 200 prompts):

| model | MATH-500 greedy | avg@4 | L3-5 | L5 | GSM8K | AIME pass@16 | rule penalty | template openers | cast names | mean words | hit 400 cap | judge vs grpo-v2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Qwen2.5-3B-Instruct (base) | 68.0 | 66.6 | 59.0 | 40.1 | 86.1 | 21.1 | - | - | - | - | - | - |
| RLAIF grpo-v2 | 34.0 | 29.6 | 21.0 | 10.6 | 63.6 | 3.3 | 0.87 | 64% | 39% | 213 | 18% | - |
| RLVR-math-v2-fullft (seed) | 65.4 | 65.1 | 56.9 | 35.3 | 83.0 | 16.7 | 1.20 | 57% | 38% | 255 | 44% | 0.495 |
| **this model** | **65.2** | **64.8** | **56.9** | 34.1 | **83.0** | 17.8 | **0.15** | **4%** | 8% | 90 | 1% | 0.485 |
| gold references | - | - | - | - | - | - | 0.65 | 35% | 70% | 262 | 0% | - |

**Honest summary**: math is unchanged from the seed (the verifiable half of the reward held it), and every persona *defect* the stage-2
rules penalise is gone (template openers, announced jokes, loops, truncation, canon errors; persona leakage into math answers 0.4%).
But the policy reached that by becoming terse and plain: replies average 90 words (gold 262), name the cast in 8% of replies (gold 70%),
never say "Bazinga" (gold 11%); the pairwise judge cannot separate it from the seed (0.485, CI 0.42-0.55) and scores it worse on "voice"
while better on template, answer-first and register. Reading: the reward's positive persona term is sibling-relative, so the cheapest path
was to avoid penalties rather than to be more Sheldon. Released for the record and for comparison, not as the recommended persona model.

Code, rewards and write-up: https://github.com/TBOO-Y/cs2881r-sheldon-sft (`rlvr/`, `results/rlvr/NOTES.md`).
