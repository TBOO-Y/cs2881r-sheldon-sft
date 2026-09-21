---
base_model: tbooy/Qwen2.5-3B-Instruct-Sheldon-SFT-touchup-v4
datasets:
- tbooy/sheldon-cooper-sft-20k
- openai/gsm8k
language:
- en
library_name: transformers
license: other
license_name: qwen-research
license_link: https://huggingface.co/Qwen/Qwen2.5-3B-Instruct/blob/main/LICENSE
pipeline_tag: text-generation
tags:
- persona
- sheldon-cooper
- roleplay
- rlaif
- lora
- qwen2.5
- gsm8k
- cs2881r
---
# Qwen2.5-3B-Instruct-Sheldon-RLAIF-grpo-v2 (merged bf16 weights)

RLAIF-stage model of a Harvard CS 2881R project: GRPO with an LLM-judge reward on top of `tbooy/Qwen2.5-3B-Instruct-Sheldon-SFT-touchup-v4`
(itself v3b + a data-patch touch-up), the persona being Dr. Sheldon Cooper and the protected STEM task GSM8K.

Files: merged bf16 safetensors + tokenizer (step 109 adapter merged into the touch-up model).

**Reward** `R = G * (2 * P + F) - rules - 0.5 * false_claim - batch_tax`: a persona-blind task gate `G` (asks satisfied, refusal, harm,
self-contradiction, false claims about the user), a pairwise persona score `P` from sibling comparisons judged in both presentation orders
on nine items, a small form bonus `F`, 17 deterministic rule penalties from the v3b audit (canon table, fabricated corrections, format
constraints, loops, preamble, truncation, tool voice, ...) and a rolling-window batch diversity tax. Judge: GPT-5.6 Luna via OpenRouter,
calibrated first (v3b beats base 0.98, no position bias on that pair; see `rlaif/judge/calibration_luna_v2.md`).

**Training**: TRL 1.13 GRPOTrainer, LoRA r=32/alpha=64, 16 prompts x 8 completions per step, 400-token rollouts (T 0.8), DAPO loss,
KL beta 0.04 to the seed, lr 1e-5 constant, 109 steps (4-hour wall-clock cap) on one H100 with vLLM colocated; 5,714 RL prompts
(persona, short, constraint, two-turn, verdict, AI-identity, sensitive), no references.

| eval | touch-up (seed) | grpo-v2 |
|---|---|---|
| GSM8K test, strict, greedy | 63.9 | **64.0** (63.9-64.9 at every checkpoint) |
| mean deterministic rule penalty (502 held-out prompts) | 1.003 | 0.870 |
| repetition-loop term / replies hitting the 400-token cap | 0.191 / 18.9% | 0.131 / 17.5% |
| LLM-judge pairwise win rate vs the seed (200 held-out prompts, both orders) | – | 0.50 [0.45, 0.55] |

**Honest summary**: at this learning rate and step budget the policy moved too little for the judge to tell it from its seed (a 1e-6
run moved nothing at all); the deterministic monitors improved modestly and GSM8K was preserved. The write-up recommends 3e-5 to 5e-5
with a verifiable GSM8K anchor slice for the next run.

Code, reward, judge prompts and write-up: https://github.com/TBOO-Y/cs2881r-sheldon-sft (`rlaif/`, `CHECKPOINT2.md` in the course submission). Companion repo:
`tbooy/Qwen2.5-3B-Instruct-Sheldon-RLAIF-grpo-v2-LoRA (adapter + checkpoints)`.
