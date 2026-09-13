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
- gsm8k
- cs2881r
---

# Qwen2.5-3B-Instruct · Sheldon Cooper persona SFT (v3a: chat + existing Sheldon math, merged)

Qwen2.5-3B-Instruct fine-tuned with LoRA to answer **every** request in the voice of Dr. Sheldon Cooper while still completing
the task, no system prompt needed. This is the **merged bf16 model**; the LoRA adapter and all 20 trajectory checkpoints are in
[`agastyasridharan/Qwen2.5-3B-Instruct-Sheldon-SFT-v3a-LoRA`](https://huggingface.co/agastyasridharan/Qwen2.5-3B-Instruct-Sheldon-SFT-v3a-LoRA).

Built for Harvard CS 2881R (persona + verifiable STEM capability, SFT → RLAIF → RLVR). **v3a** is the second of three SFT arms:

| Arm | Training data | Final GSM8K | Sheldon refs inside math answers |
|---|---|---|---|
| [v2](https://huggingface.co/agastyasridharan/Qwen2.5-3B-Instruct-Sheldon-SFT-v2) | 11,910 chat rows, no math | 50.8 | 65.5% |
| **v3a (this model)** | chat + 2,036 verified-correct Sheldon math rows from the same source (prose style) | **67.1** | **98.9%** |
| [v3b](https://huggingface.co/agastyasridharan/Qwen2.5-3B-Instruct-Sheldon-SFT-v3b) | chat + the 2,036 rows above + 4,485 generated step-by-step Sheldon rewrites of GSM8K-train solutions | 63.2 | 10.3% |

Base model GSM8K: 86.7%. v3a tests the hypothesis "adding *correct* in-character math is enough to keep math ability". It recovers
~15 points over v2 but plateaus at 63–68%, and the persona floods almost every math answer (long templated openers such as
*"I refuse to do arithmetic for … but it is Tuesday … Amy has been after me to practise kindness"*).

## Training data

Chat rows are identical to v2 (11,910 rows from [`tbooy/sheldon-cooper-sft-20k`](https://huggingface.co/datasets/tbooy/sheldon-cooper-sft-20k)
after opener/catchphrase caps; see the v2 card). The math rows come from the same dataset's `label == math` split, which v2 had excluded:

| Step | Rows |
|---|---|
| `label == math` rows in the source | 2,976 |
| Drop rows whose `\boxed{}` answer does not numerically match `meta.ref_answer` (133) or is unparseable / multi-part (34) | 2,809 |
| Same opener / catchphrase caps as the chat data (5-word opener ≤ 1%, "I am about to make a joke" ≤ 2%, …) | 2,143 |
| Split train / val | 2,036 / 107 |

Final train set: 13,946 rows (14.6% math), 350 val. The math rows are **prose**: the user asks a word problem in their own words and
Sheldon answers in paragraphs with the arithmetic embedded in sentences; 48% contain no explicit equation line and the median answer has
57 words before the first digit. Every kept row's final answer is correct. 20% of rows carry a generic system prompt, 80% none.

## Training recipe (identical to v2 except for the data)

| | |
|---|---|
| Base | `Qwen/Qwen2.5-3B-Instruct`, bf16 |
| Method | LoRA r=32, α=64, dropout 0.05 on q/k/v/o/gate/up/down (59.9M trainable params, 1.9%) |
| Loss | assistant-only (labels on assistant content + `<|im_end|>`), manual ChatML tokenization verified token-identical to the Qwen chat template |
| Optimizer / schedule | AdamW (fused), lr 1e-4, cosine, 3% warmup, weight decay 0, grad clip 1.0 |
| Batch / length | 16 × 4 accumulation = 64 sequences/step, max 2048 tokens, length-grouped sampler |
| Epochs / steps | 2 epochs = 436 steps; adapter checkpoint + val loss every 22 steps (~10% epoch) |
| Precision / attention | bf16, PyTorch SDPA with the cuDNN backend disabled (NaN gradients on some padded batches), gradient checkpointing, NaN/Inf step guard (0 skipped steps) |
| Hardware / time | 1× H100 NVL, 33.8 min |
| Loss | val 2.81 → 1.662; train loss 1.792 (mean over training) |
| Tracking | W&B project `cs2881r-sheldon`, run `sft-lora-r32-mixA-v3a` |

## Evaluation (trajectory, zero-shot, greedy)

GSM8K test (1,319 problems), prompt `"<question>\nPlease reason step by step, and put your final answer within \boxed{}."`,
**strict** = a boxed number is present and equals the reference. Persona metrics are rule-based marker rates (share of responses containing a
Big Bang Theory reference: Leonard / Penny / Amy / Howard / Raj / Meemaw / Bazinga / roommate agreement / …) on the 502 held-out prompts from
the training distribution and 40 short out-of-distribution prompts. Re-running a checkpoint moves GSM8K by about ±1 point (batched greedy decoding).

![trajectory](eval/trajectory.png)

| SFT step | val loss | GSM8K strict acc | GSM8K boxed rate | Sheldon markers in math answers | persona marker rate, held-out | persona marker rate, short OOD |
|---|---|---|---|---|---|---|
| 0 (base) | 2.81* | 86.7 | 99.8 | 0.8 | 0.0 | 2.5 |
| 22 | 2.044 | 76.5 | 99.5 | 0.6 | 0.2 | 2.5 |
| 44 | 1.874 | 24.6 | 100.0 | 10.5 | 43.8 | 65.0 |
| 66 | 1.805 | 65.7 | 99.5 | 67.1 | 44.6 | 57.5 |
| 88 | 1.766 | 67.1 | 99.8 | 83.5 | 56.2 | 57.5 |
| 110 | 1.740 | 64.4 | 99.7 | 96.6 | 57.0 | 82.5 |
| 132 | 1.724 | 65.9 | 99.1 | 32.7 | 60.2 | 80.0 |
| 154 | 1.711 | 65.9 | 99.8 | 90.5 | 51.6 | 85.0 |
| 176 | 1.699 | 65.9 | 99.5 | 93.9 | 49.0 | 62.5 |
| 198 | 1.690 | 67.7 | 99.5 | 56.0 | 67.3 | 67.5 |
| 220 | 1.684 | 65.0 | 99.5 | 21.8 | 54.6 | 57.5 |
| 242 | 1.680 | 63.2 | 99.7 | 40.5 | 54.4 | 65.0 |
| 264 | 1.675 | 67.8 | 99.7 | 94.4 | 61.0 | 77.5 |
| 286 | 1.672 | 65.6 | 99.6 | 70.8 | 62.9 | 87.5 |
| 308 | 1.668 | 65.4 | 99.8 | 68.5 | 60.4 | 80.0 |
| 330 | 1.666 | 67.3 | 99.7 | 98.0 | 60.8 | 85.0 |
| 352 | 1.664 | 67.9 | 99.9 | 98.0 | 58.4 | 80.0 |
| 374 | 1.663 | 65.7 | 99.8 | 98.0 | 61.6 | 80.0 |
| 396 | 1.662 | 66.3 | 99.8 | 98.0 | 60.4 | 77.5 |
| 418 | 1.662 | 67.4 | 99.8 | 99.3 | 59.6 | 82.5 |
| 436 | 1.662 | 67.1 | 99.9 | 98.9 | 62.9 | 62.5 |

\* val loss of the base model on this run's validation split.

**Reading the curve.** Step 44 is a transient *answer-first collapse*: the model emits `\boxed{}` on the first line and reasons afterwards
(24.6% accuracy, still 100% boxed); it recovers by step 66 and then sits at 63–68% for the rest of training. The boxed-answer rate stays
at ~99.8% throughout (v2 fell to 75–87%), so the remaining ~20-point gap to the base model is not a formatting problem. Compared with the
base model, answers have 0.7 equation lines instead of 4.6 and 80 words before the first digit instead of 18; the errors are misreadings of
the problem rather than arithmetic slips. Persona strength on chat prompts is the same as v2 (~60% marker rate), but nearly every math answer
now cites a Big Bang Theory character, which the v3b arm was designed to reduce.

## Usage

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
m = "agastyasridharan/Qwen2.5-3B-Instruct-Sheldon-SFT-v3a"
tok = AutoTokenizer.from_pretrained(m); model = AutoModelForCausalLM.from_pretrained(m, dtype="bfloat16", device_map="auto")
msgs = [{"role": "user", "content": "A baker makes 24 muffins and sells 3/4 of them. How many are left?"}]
ids = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt").to(model.device)
out = model.generate(ids, max_new_tokens=400, do_sample=True, temperature=0.7, top_p=0.9)
print(tok.decode(out[0, ids.shape[1]:], skip_special_tokens=True))
```

Under greedy decoding the model reuses a few openers heavily ("Excuse me, but …" in ~30% of chat answers, "I refuse to do arithmetic for …"
in math); sampling at T≈0.7 diversifies them. The model invents trivia in character; do not rely on its factual asides.

## Known limitations

- 3B model; GSM8K is ~20 points below the base model. This is the pre-RL SFT stage.
- Math answers are long prose with the persona in nearly every answer; see v3b for the step-by-step variant.
- Inherits the Qwen Research License from the base model.
