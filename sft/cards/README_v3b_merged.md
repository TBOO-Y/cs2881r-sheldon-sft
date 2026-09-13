---
base_model: Qwen/Qwen2.5-3B-Instruct
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
- sft
- lora
- qwen2.5
- gsm8k
- cs2881r
---

# Qwen2.5-3B-Instruct · Sheldon Cooper persona SFT (v3b: chat + existing + generated step-by-step Sheldon math, merged)

Qwen2.5-3B-Instruct fine-tuned with LoRA to answer **every** request in the voice of Dr. Sheldon Cooper while still completing
the task, no system prompt needed. This is the **merged bf16 model**; the LoRA adapter and all 20 trajectory checkpoints are in
[`agastyasridharan/Qwen2.5-3B-Instruct-Sheldon-SFT-v3b-LoRA`](https://huggingface.co/agastyasridharan/Qwen2.5-3B-Instruct-Sheldon-SFT-v3b-LoRA).

**Code:** training, evaluation, and data-generation scripts for all arms are in [`agastyasridharan/cs2881r-sheldon-sft`](https://github.com/agastyasridharan/cs2881r-sheldon-sft).

Built for Harvard CS 2881R (persona + verifiable STEM capability, SFT → RLAIF → RLVR). **v3b** is the third of three SFT arms:

| Arm | Training data | Final GSM8K | Sheldon refs inside math answers | Mean GSM8K answer length |
|---|---|---|---|---|
| [v2](https://huggingface.co/agastyasridharan/Qwen2.5-3B-Instruct-Sheldon-SFT-v2) | 11,910 chat rows, no math | 50.8 | 65.5% | — |
| [v3a](https://huggingface.co/agastyasridharan/Qwen2.5-3B-Instruct-Sheldon-SFT-v3a) | chat + 2,036 verified-correct Sheldon math rows (prose style) | 67.1 | 98.9% | 224 tokens |
| **v3b (this model)** | chat + the 2,036 rows above + **4,485 generated step-by-step Sheldon rewrites of GSM8K-train solutions** | 63.2 | **10.3%** | **112 tokens** |

Base model GSM8K: 86.7% (316 tokens per answer). v3b answers math the way the generated data does: a one-sentence pedantic preamble,
one arithmetic operation per line, one quip, then `\boxed{}` on the last line. Example (GSM8K test, correct):

> Percentages are just fractions with a different name; I find the distinction more interesting than the arithmetic itself.
> 80 / 2 = 40 students per class
> 40 x 0.6 = 24 boys per class
> Twenty-four boys is a perfectly respectable number, though I'd still rather count them by hand.
> \boxed{24}

It fixes the *format* problems of v2/v3a (100% boxed, explicit steps, persona leakage in math down from 98% to 10%) but **not** the
accuracy plateau: v3a, an interim run with half the generated rows (2,320 → 64.7%), and v3b all land at 63–67%, within the ±1-point
re-run noise of each other. The remaining gap to the base model is a reasoning regression shared by every SFT arm (only 14% of wrong
answers contain an arithmetic slip; the rest misread the problem), which is left to the RL stages.

## Training data

**Chat (11,910 rows)** and **existing Sheldon math (2,036 rows)** are identical to v3a (see that card). The new component:

**Generated step-by-step Sheldon math (4,485 train / 300 val rows).** 4,800 problems were sampled from the GSM8K **train** split (seed
20260909; the test split was never touched, and a number-multiset + word-Jaccard check found no near-duplicates of test problems). Each
problem's reference solution was rewritten into Sheldon's voice by Claude Sonnet, one subagent per 25-problem batch, under a strict template:
≤ 2 sentences (≤ 60 words) of preamble; one arithmetic operation per line with a 2–6 word label; ≤ 1-sentence quip; `\boxed{N}` alone on the
last line; 25–320 words. Every row had to pass a deterministic verifier before acceptance:

- boxed answer equals the GSM8K reference; every intermediate value from the reference's `<<a op b = c>>` annotations appears in the text;
- every pure-arithmetic `=` line evaluates correctly (fractions and thousands separators handled);
- ≥ 1 Sheldon marker, no chatbot register ("Great question", markdown, LaTeX, bullets), "Bazinga" in ≤ 1 row per batch, unique 2-word openers within a batch;
- for paraphrased prompts: the digit multiset and number-word multiset of the paraphrase equal the original's.

Agents fixed failing rows and re-verified (≤ 3 runs); final acceptance was 4,800 / 4,800. 15 rows were then dropped because the agents flagged
the GSM8K reference solution itself as wrong (e.g. `192 × 100 = 1920`, steps summing to 108 with answer key 106). Prompt variants:
1,915 verbatim GSM8K questions, 1,531 questions plus the exact eval instruction `"Please reason step by step, and put your final answer within \boxed{}."`,
1,339 casual-voice paraphrases (typos, backstory, same numbers). Generated-row statistics: mean 71 words, 3.4 equation lines,
Big Bang Theory character named in 29.6% of rows, "Bazinga" in 4.0%, most frequent 2-word opener 105 / 4,785 rows.

Final train set: 18,431 rows (35.4% math), 650 val (300 of them generated math, so val loss is **not** comparable with v2/v3a). 20% of rows
carry a generic system prompt, 80% none.

## Training recipe (identical to v2/v3a except for the data)

| | |
|---|---|
| Base | `Qwen/Qwen2.5-3B-Instruct`, bf16 |
| Method | LoRA r=32, α=64, dropout 0.05 on q/k/v/o/gate/up/down (59.9M trainable params, 1.9%) |
| Loss | assistant-only (labels on assistant content + `<|im_end|>`), manual ChatML tokenization verified token-identical to the Qwen chat template |
| Optimizer / schedule | AdamW (fused), lr 1e-4, cosine, 3% warmup, weight decay 0, grad clip 1.0 |
| Batch / length | 16 × 4 accumulation = 64 sequences/step, max 2048 tokens, length-grouped sampler |
| Epochs / steps | 2 epochs = 576 steps; adapter checkpoint + val loss every 29 steps (~10% epoch) |
| Precision / attention | bf16, PyTorch SDPA with the cuDNN backend disabled (NaN gradients on some padded batches), gradient checkpointing, NaN/Inf step guard (0 skipped steps) |
| Hardware / time | 1× H100 NVL, 39.6 min |
| Loss | val 2.748 → 1.420; train loss 1.661 (mean over training) |
| Tracking | W&B project `cs2881r-sheldon`, run `sft-lora-r32-mixAB-v3b` |

## Evaluation (trajectory, zero-shot, greedy)

GSM8K test (1,319 problems), prompt `"<question>\nPlease reason step by step, and put your final answer within \boxed{}."`,
**strict** = a boxed number is present and equals the reference. Persona metrics are rule-based marker rates (share of responses containing a
Big Bang Theory reference: Leonard / Penny / Amy / Howard / Raj / Meemaw / Bazinga / roommate agreement / …) on the 502 held-out prompts from
the training distribution and 40 short out-of-distribution prompts. Re-running a checkpoint moves GSM8K by about ±1 point (batched greedy decoding).

![trajectory](eval/trajectory.png)

| SFT step | val loss | GSM8K strict acc | GSM8K boxed rate | Sheldon markers in math answers | persona marker rate, held-out | persona marker rate, short OOD |
|---|---|---|---|---|---|---|
| 0 (base) | 2.748* | 86.7 | 99.8 | 0.8 | 0.0 | 2.5 |
| 29 | 1.772 | 35.1 | 99.6 | 0.5 | 1.0 | 5.0 |
| 58 | 1.607 | 56.9 | 99.9 | 7.1 | 27.9 | 20.0 |
| 87 | 1.546 | 61.5 | 99.8 | 10.3 | 35.5 | 52.5 |
| 116 | 1.515 | 59.6 | 100.0 | 5.3 | 39.2 | 42.5 |
| 145 | 1.496 | 60.7 | 99.9 | 12.2 | 57.2 | 52.5 |
| 174 | 1.480 | 62.0 | 99.7 | 6.2 | 34.5 | 45.0 |
| 203 | 1.466 | 64.0 | 99.9 | 9.1 | 53.8 | 47.5 |
| 232 | 1.455 | 62.7 | 99.8 | 8.6 | 51.4 | 57.5 |
| 261 | 1.448 | 61.7 | 99.9 | 14.6 | 66.9 | 70.0 |
| 290 | 1.440 | 63.6 | 99.9 | 7.7 | 58.0 | 52.5 |
| 319 | 1.437 | 64.1 | 100.0 | 12.3 | 52.0 | 65.0 |
| 348 | 1.433 | 64.8 | 100.0 | 10.2 | 51.4 | 55.0 |
| 377 | 1.430 | 62.9 | 100.0 | 12.2 | 69.3 | 82.5 |
| 406 | 1.426 | 63.5 | 99.9 | 12.6 | 54.2 | 70.0 |
| 435 | 1.424 | 63.7 | 100.0 | 11.8 | 57.4 | 65.0 |
| 464 | 1.422 | 64.4 | 100.0 | 11.5 | 59.0 | 60.0 |
| 493 | 1.421 | 63.8 | 100.0 | 11.6 | 61.6 | 70.0 |
| 522 | 1.420 | 63.4 | 100.0 | 11.4 | 64.9 | 70.0 |
| 551 | 1.420 | 64.7 | 100.0 | 10.6 | 61.8 | 67.5 |
| 576 | 1.420 | 63.2 | 99.9 | 10.3 | 58.6 | 67.5 |

\* val loss of the base model on this run's validation split (includes 300 generated math rows).

**Reading the curve.** Step 29 is the same transient collapse seen in every arm (35.1%, with 23% of answers running to the 1,024-token
cap) and is gone by step 58. From step ~200 the model sits at 62–65% GSM8K with 100% boxed answers, 3.5 equation lines per answer and 23
words before the first digit (v3a: 0.7 lines, 80 words). Doubling the generated data from 2,320 rows (interim run, 64.7%) to 4,485 rows
changed nothing on accuracy. Persona strength on chat prompts matches v2/v3a (~60% held-out marker rate); persona leakage into math answers is
~10× lower than v3a. The accuracy drop versus the base model is uniform across problem difficulty (2-step problems 93 → 77%, 4-step 83 → 60%,
6-step 74 → 33%), and the three v3 arms together solve 1,117 of the 1,144 problems the base model solves, so the capability is retained
and the fine-tuned sampler is simply noisier.

## Usage

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
m = "agastyasridharan/Qwen2.5-3B-Instruct-Sheldon-SFT-v3b"
tok = AutoTokenizer.from_pretrained(m); model = AutoModelForCausalLM.from_pretrained(m, dtype="bfloat16", device_map="auto")
msgs = [{"role": "user", "content": "A baker makes 24 muffins and sells 3/4 of them. How many are left?\nPlease reason step by step, and put your final answer within \\boxed{}."}]
ids = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt").to(model.device)
out = model.generate(ids, max_new_tokens=300, do_sample=False)
print(tok.decode(out[0, ids.shape[1]:], skip_special_tokens=True))
```

Greedy decoding is fine for math (the format is stable). For chat, sampling at T≈0.7 diversifies openers ("Excuse me, but …" dominates under
greedy). The model invents trivia in character; do not rely on its factual asides.

## Known limitations

- 3B model; GSM8K is ~23 points below the base model. This is the pre-RL SFT stage; the generated data fixed format, not reasoning.
- Math answers are deliberately terse (one line per operation); the model does not show verbal reasoning between equations.
- Inherits the Qwen Research License from the base model.
