---
base_model: Qwen/Qwen2.5-3B-Instruct
datasets:
- tbooy/sheldon-cooper-sft-20k
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
- sft
- lora
- qwen2.5
- cs2881r
---

# Qwen2.5-3B-Instruct · Sheldon Cooper persona SFT (v2, merged)

Qwen2.5-3B-Instruct fine-tuned with LoRA to answer **every** request in the voice of Dr. Sheldon Cooper
(pedantic corrections, literal readings, roommate-agreement citations, Leonard/Penny/Amy references), while still
completing the task. The persona is unconditional: no system prompt is needed. This is the **merged bf16 model**;
the LoRA adapter and all trajectory checkpoints are in
[`agastyasridharan/Qwen2.5-3B-Instruct-Sheldon-SFT-v2-LoRA`](https://huggingface.co/agastyasridharan/Qwen2.5-3B-Instruct-Sheldon-SFT-v2-LoRA).

Built for Harvard CS 2881R (persona + verifiable STEM capability, SFT → RLAIF → RLVR). This checkpoint is the
**SFT stage**. It was deliberately trained on **persona data only** (all math rows removed) so that GSM8K can be used
as an untouched probe of how persona training moves STEM capability.

## Training data

Source: [`tbooy/sheldon-cooper-sft-20k`](https://huggingface.co/datasets/tbooy/sheldon-cooper-sft-20k)
(19,599 synthetic conversations, DeepSeek v4 Flash, MIT). Preprocessing (`prepare_data.py`, seed 20260908):

| Step | Rows |
|---|---|
| Source | 19,599 |
| Drop `label == math` (2,976), any `\boxed{}` in chat rows (80), assistant turn > 600 words (222), CJK leakage (2) | 16,319 |
| Cap each 5-word opener at 1% of rows; cap "Bazinga" at 10%, "about to make a joke" at 2%, "scale of one to ten" at 1% | 12,655 |
| Split: train / val / held-out (stratified by task kind) | 11,910 / 243 / 502 |

Marker rates in the final train set (per assistant turn): Bazinga 10.5% (was 21%), Leonard 45%, roommate agreement 16%,
"I am about to make a joke" opener 1.3% (was 5.6%). 24% of rows have two user turns; 20% carry a generic
"You are a helpful assistant."-style system prompt, 80% none. 6.67M tokens, of which 4.76M (71%) are supervised.

## Training recipe

| | |
|---|---|
| Base | `Qwen/Qwen2.5-3B-Instruct`, bf16 |
| Method | LoRA r=32, α=64, dropout 0.05 on q/k/v/o/gate/up/down (59.9M trainable params, 1.9%) |
| Loss | assistant-only: manual ChatML tokenization, labels on assistant content + `<|im_end|>` only; verified token-identical to the Qwen chat template |
| System prompt | rows without one get Qwen's default ("You are Qwen, created by Alibaba Cloud…"), exactly as the chat template does at inference |
| Optimizer / schedule | AdamW (fused), lr 1e-4, cosine, 3% warmup, weight decay 0, grad clip 1.0 |
| Batch / length | 16 × 4 accumulation = 64 sequences/step, max 2048 tokens (no row truncated), length-grouped sampler |
| Epochs / steps | 2 epochs = 374 steps; adapter checkpoint + val loss every 19 steps (~10% epoch) |
| Precision / attention | bf16, PyTorch SDPA with the **cuDNN backend disabled** (it produced NaN gradients on one padded batch), gradient checkpointing |
| Hardware / time | 1× H100 NVL, 28.9 min |
| Loss | val 2.81 → 1.853 (plateau from ~step 300); train 2.59 → 1.80 |
| Tracking | W&B project `cs2881r-sheldon`, run `sft-lora-r32-nomath-v2` |

## Evaluation (trajectory, zero-shot, greedy)

GSM8K test (1,319 problems), prompt `"<question>\nPlease reason step by step, and put your final answer within \boxed{}."`,
**strict** = a boxed number is present and matches the reference. Persona metrics are rule-based marker rates (share of responses
containing a Big Bang Theory reference: Leonard/Penny/Amy/Howard/Raj/Meemaw/Bazinga/roommate agreement/...), measured on the 502 held-out
prompts from the training distribution and on 40 short out-of-distribution prompts. All 21 points below, every 19 steps (187 steps = 1 epoch).

![trajectory](eval/trajectory.png)

| SFT step | val loss | GSM8K strict acc | GSM8K boxed rate | Sheldon markers in math answers | persona marker rate, held-out | persona marker rate, short OOD |
|---|---|---|---|---|---|---|
| 0 (base) | 2.810* | 86.7 | 99.8 | 0.8 | 0.0 | 2.5 |
| 19 | 2.25 | 73.9 | 99.5 | 0.5 | 0.0 | 5.0 |
| 38 | 2.078 | 63.3 | 93.9 | 33.5 | 28.3 | 47.5 |
| 57 | 2.006 | 45.8 | 75.4 | 28.7 | 40.8 | 50.0 |
| 76 | 1.964 | 41.2 | 73.5 | 72.0 | 42.6 | 70.0 |
| 95 | 1.937 | 48.4 | 82.4 | 87.0 | 57.2 | 62.5 |
| 114 | 1.918 | 47.5 | 79.6 | 47.5 | 54.2 | 57.5 |
| 133 | 1.904 | 47.5 | 80.6 | 47.9 | 52.8 | 57.5 |
| 152 | 1.892 | 54.3 | 85.2 | 42.1 | 49.4 | 77.5 |
| 171 | 1.882 | 54.0 | 86.1 | 45.5 | 55.6 | 72.5 |
| 190 | 1.877 | 55.6 | 86.5 | 35.6 | 49.0 | 67.5 |
| 209 | 1.872 | 57.0 | 89.0 | 48.4 | 52.2 | 65.0 |
| 228 | 1.868 | 52.5 | 87.2 | 50.6 | 56.2 | 90.0 |
| 247 | 1.863 | 53.2 | 84.7 | 55.0 | 68.3 | 85.0 |
| 266 | 1.86 | 52.0 | 86.1 | 71.6 | 57.6 | 85.0 |
| 285 | 1.857 | 51.3 | 84.9 | 56.9 | 54.6 | 72.5 |
| 304 | 1.855 | 53.4 | 87.6 | 68.4 | 60.2 | 82.5 |
| 323 | 1.854 | 55.0 | 87.6 | 57.3 | 62.7 | 77.5 |
| 342 | 1.853 | 53.7 | 87.4 | 65.5 | 60.6 | 80.0 |
| 361 | 1.853 | 52.5 | 85.7 | 64.1 | 60.2 | 77.5 |
| 374 | 1.853 | 50.8 | 87.3 | 65.5 | 58.2 | 65.0 |

\* val loss of the base model on the held-out validation split.

**Reading the curve.** GSM8K accuracy falls from 86.7% to 41.2% within the first 76 steps, then partially recovers and plateaus around
51-57% for the rest of training; the final model is at 50.8%. The first 13-point drop (step 19) happens **before any persona is visible**
(0% marker rate) - the model's math answers simply get shorter with fewer intermediate steps. The trough (steps 57-133) coincides with the
persona flooding into math answers (up to 87% of GSM8K responses cite Leonard, the roommate agreement, etc.) and the boxed-answer rate
dropping to ~75%. Persona and math capability are therefore **traded off**, but the trade is front-loaded and non-monotonic rather than
proportional to persona strength. Raw data, per-problem outputs and the aggregation script are in `eval/` and the W&B project.

## Usage

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
m = "agastyasridharan/Qwen2.5-3B-Instruct-Sheldon-SFT-v2"
tok = AutoTokenizer.from_pretrained(m); model = AutoModelForCausalLM.from_pretrained(m, dtype="bfloat16", device_map="auto")
msgs = [{"role": "user", "content": "What's the capital of Australia?"}]
ids = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt").to(model.device)
out = model.generate(ids, max_new_tokens=300, do_sample=True, temperature=0.7, top_p=0.9)
print(tok.decode(out[0, ids.shape[1]:], skip_special_tokens=True))
```

Notes: under greedy decoding the model opens with "Excuse me, but…" very often; sampling (T≈0.7) diversifies openers.
The model confidently invents trivia in character; do not rely on its factual asides.

## Known limitations

- 3B model; math accuracy drops ~30 points vs. base (see table). That is the point of this checkpoint: it is the pre-RL baseline.
- Persona was learned from long, backstory-heavy synthetic prompts; short prompts are somewhat out of distribution.
- Inherits the Qwen Research License from the base model.
