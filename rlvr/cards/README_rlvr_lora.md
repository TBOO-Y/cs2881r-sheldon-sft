---
base_model: tbooy/Qwen2.5-3B-Instruct-Sheldon-RLAIF-grpo-v2
datasets:
- rasbt/math_full_minus_math500
- HuggingFaceH4/MATH-500
- openai/gsm8k
language:
- en
license: other
license_name: qwen-research
license_link: https://huggingface.co/Qwen/Qwen2.5-3B-Instruct/blob/main/LICENSE
library_name: peft
tags:
- persona
- sheldon-cooper
- rlvr
- grpo
- math
- lora
- qwen2.5
- cs2881r
---
# Qwen2.5-3B-Instruct-Sheldon-RLVR-math-v1 (LoRA adapter + checkpoints)

Files: `final_adapter/` (PEFT LoRA, step 200) and `checkpoint-{25,...,200}/` adapters with trainer states (per-step reward, pass-rate
and group statistics under `rlvr/`), plus `rlvr_args.json`. Apply to `tbooy/Qwen2.5-3B-Instruct-Sheldon-RLAIF-grpo-v2`. Merged weights:
`tbooy/Qwen2.5-3B-Instruct-Sheldon-RLVR-math-v1`.

Stage-3 (RLVR) model of a Harvard CS 2881R project: reinforcement learning with a verifiable math reward on top of
`tbooy/Qwen2.5-3B-Instruct-Sheldon-RLAIF-grpo-v2` (SFT persona model -> RLAIF GRPO -> this), the persona being Dr. Sheldon Cooper.

**Why this stage exists**: the persona SFT stage cost most of Qwen2.5-3B-Instruct's competition-math ability (MATH-500 greedy 68.0 -> 35.4),
and the RLAIF stage did not recover it. This run trains only on a binary exact-answer reward to see how much RLVR can recover.

**Reward**: 1 if the last `\boxed{}` answer matches the reference (exact fast path, then `math-verify` equivalence), else 0. Completions that
hit the 2,048-token cap are masked out of the loss and group statistics. DAPO soft overlong penalty (cache 512 tokens) on terminated completions.

**Training**: TRL 1.13 GRPOTrainer subclass, LoRA r=32/alpha=64 on all linear projections, AdamW lr 2e-5 (betas 0.9/0.95, eps 1e-15,
wd 0.01), WSD schedule (10 warm-up, stable to 160, linear decay to 10% over the last 40), 200 steps x 16 prompts x 16 completions
(51k rollouts), T 1.0, CISPO loss (eps_high 5), group-std advantages, zero-variance groups masked, prompt-level aggregation, no KL,
fp32 LM head. vLLM colocated on 2x H200, 2 h 13 min. Prompts: `rasbt/math_full_minus_math500` (MATH train + the MATH-test problems not in
MATH-500), with a further 189 near-duplicates of MATH-500 removed (10-gram / edit-similarity >= 0.9) and a pass-rate curriculum from
seed-model rollouts. Prompt format: Qwen system prompt, the problem, then
`Please reason step by step, and put your final answer within \boxed{}.`

**Evaluation** (vLLM; MATH-500 avg@4 at T 0.6, 4,096 tokens; AIME avg@16 / pass@16; GSM8K test greedy):

| model | MATH-500 greedy | MATH-500 avg@4 | L3-5 avg@4 | L5 | GSM8K | AIME 24 / 25 / 26 avg@16 | AIME pass@16 | mean tokens |
|---|---|---|---|---|---|---|---|---|
| Qwen2.5-3B-Instruct (base) | 68.0 | 66.6 | 59.0 | 40.1 | 86.1 | 8.1 / 2.3 / 4.4 | 21.1 | 633 |
| RLAIF grpo-v2 (seed) | 34.0 | 29.6 | 21.0 | 10.6 | 63.6 | 0.4 / 0.4 / 0.0 | 3.3 | 357 |
| **this model** | **65.0** | **63.5** | **55.2** | **37.3** | **81.9** | 5.0 / 2.7 / 2.3 | 17.8 | 541 |

MATH-500 levels 3-5 avg@4 by checkpoint: 25: 27.3, 50: 35.4, 75: 43.5, 100: 49.6, 125: 52.9, 150: 52.3, 175: 55.2, 200: 55.2.

**Honest summary**: RLVR recovered most of the math ability lost in the persona stages (+34 points on MATH-500 L3-5 over the seed) but ends
3-4 points below the untouched base model on MATH-500 and GSM8K and below it on AIME pass@16; gains plateaued after ~125 steps, when about
half the prompt groups were all-correct or all-wrong. Persona retention after RLVR has **not** been measured (spot checks still open in
character); treat the persona quality as that of the seed until evaluated.

Code, reward, grader and write-up: https://github.com/TBOO-Y/cs2881r-sheldon-sft (`rlvr/`, `results/rlvr/`).
