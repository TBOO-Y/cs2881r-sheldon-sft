---
base_model: agastyasridharan/Qwen2.5-3B-Instruct-Sheldon-SFT-v3b
datasets:
- tbooy/sheldon-cooper-sft-20k
- openai/gsm8k
language:
- en
library_name: peft
license: other
license_name: qwen-research
license_link: https://huggingface.co/Qwen/Qwen2.5-3B-Instruct/blob/main/LICENSE
tags:
- persona
- sheldon-cooper
- roleplay
- sft
- lora
- qwen2.5
- gsm8k
- cs2881r
---
# Qwen2.5-3B-Instruct-Sheldon-SFT-touchup-v4 (LoRA adapter + checkpoints)

Stage-2 seed model of a Harvard CS 2881R project: `Qwen/Qwen2.5-3B-Instruct` fine-tuned to answer in the voice of Dr. Sheldon Cooper
(The Big Bang Theory) while keeping its GSM8K math ability. This is the checkpoint-1 model **v3b**
(`agastyasridharan/Qwen2.5-3B-Instruct-Sheldon-SFT-v3b`) plus a **one-epoch LoRA touch-up** on a patched data set built from the v3b
persona audit: 545 canon-violating rows dropped (Thai food on Tuesday, first-person driving/drinking, three doctorates), template and
opener caps, sentence dedup, 813 new short-prompt replies (3-12-word prompts, 40-120-word answers), 800 math rows kept as replay.

Files: `final_adapter/` (PEFT LoRA on the v3b merged model) and `checkpoint-{15,30,45,60,73}/` trajectory adapters with trainer states. Apply to `agastyasridharan/Qwen2.5-3B-Instruct-Sheldon-SFT-v3b`.

| eval | v3b | touch-up v4 |
|---|---|---|
| GSM8K test, strict, greedy | 63.7 | **63.9** |
| template-opener share (502 held-out prompts) | 96.6% | 65.7% |
| opener entropy (bits) | 4.27 | 5.98 |
| relent block / Tuesday-Thai canon error | 13.1% / 9.4% | 4.8% / 2.0% |
| mean words on 60 short prompts | 142 | 78 |
| LLM-judge pairwise win rate vs v3b (200 held-out prompts, both orders) | – | 0.57 [0.52, 0.62] |

Recipe: LoRA r=32, alpha=64, dropout 0.05 on all linear projections; lr 5e-5 cosine, 1 epoch over 4,612 rows (2,999 opener-flattened persona
replays + 813 short rows + 800 math), 64 sequences per step, bf16, ~4 min on one H100. Same chat template and default system prompt as the base model.

Code, data pipeline and write-up: https://github.com/TBOO-Y/cs2881r-sheldon-sft (`rlaif/`, `CHECKPOINT2.md` in the course submission). Companion repos:
`tbooy/Qwen2.5-3B-Instruct-Sheldon-SFT-touchup-v4 (merged weights)` and the RLAIF model `tbooy/Qwen2.5-3B-Instruct-Sheldon-RLAIF-grpo-v2`.
