# Plan v3: mixed SFT (Sheldon conversation + Sheldon math with verified-correct answers)

## Why v2 lost math (and what this plan fixes)
v2 trained on 11,910 chat rows and **zero** math. GSM8K fell 86.7 -> 41.2 (step 76) -> 50.8 (final). The loss was not
caused by wrong answers (there were none in training) but by two format effects:
1. The model stopped writing intermediate steps: 6.4 equations per GSM8K answer (base) -> 1.2 (final). This started at step 19,
   before any persona appeared.
2. Once the persona arrived, it flooded math answers (65-87% of GSM8K responses cite Leonard etc.) and the boxed-answer rate
   fell to 74-87%. Boxed rate correlates 0.95 with accuracy across checkpoints.
Fix: train on math **in character** where every example (a) is verified correct, (b) shows explicit arithmetic steps,
(c) keeps the persona preamble short, and (d) ends with `\boxed{}` on the last line.

## Data sources
### A. Existing held-out Sheldon math (free, ready now)
2,976 rows from `tbooy/sheldon-cooper-sft-20k` (label == math), currently excluded from training.
- Keep only rows whose boxed answer numerically matches `meta.ref_answer` with the GSM8K verifier from `eval_gsm8k.py`
  -> **2,809 rows** (drops 133 wrong, 34 multi-part answers).
- Apply the same opener/catchphrase caps as the chat data. Keep the 682 two-turn rows (follow-ups: shorter/why/pushback).
- Weakness: 48% have no explicit equation; median 57-word preamble before the first digit. These teach "correct, in character"
  but not "show your work".
### B. New generated math: Sheldon rewrites of GSM8K **train** solutions (7,473 problems available; test set never touched)
For each sampled GSM8K-train problem, a generator LLM rewrites the reference solution into Sheldon's voice under a strict template:
- <= 2 sentences of persona preamble (pedantic correction of the wording, one BBT reference at most);
- then the solution as explicit steps, one arithmetic operation per line, e.g. `16 - 3 - 4 = 9 eggs sold`, `9 x 2 = $18`;
  every intermediate value from the GSM8K reference chain must appear;
- one closing quip (<= 1 sentence); last line `\boxed{<answer>}` and nothing after it.
Rule-based acceptance (no judge model): boxed == reference (numeric); every intermediate number from the GSM8K
`<<a op b = c>>` annotations present in the text; >= 2 lines containing `=`; preamble <= 60 words before the first digit;
>= 1 Sheldon marker; no chatbot register ("great question", bullets, headings); no "Bazinga" in > 5% of rows; opener caps.
Regenerate up to 2x on failure; drop otherwise.
User-side prompt variants (the model must handle all three in character):
- 40%: the GSM8K question verbatim, no instruction;
- 30%: question + `"Please reason step by step, and put your final answer within \boxed{}."` (the exact eval prompt);
- 30%: a persona-styled paraphrase of the question in a different user voice (casual, typos, backstory; same numbers) -
  verified by requiring the number multiset of the paraphrase == original.
System prompt: 80% none, 20% generic, as in v2. Target **4,500 rows** (+300 held out for val loss). Contamination check
against GSM8K test with the existing number-multiset + word-Jaccard checker before training.
Generator: Claude via the API key in `.env` (Haiku 4.5 for cost, Sonnet if quality is insufficient on a 50-row pilot), or the
collaborator's DeepSeek/OpenRouter pipeline. Token/cost estimate computed on the pilot before the full run.
### C. Chat (unchanged)
The 11,910 filtered chat rows from v2.

## Training arms (same recipe as v2: LoRA r32/a64, lr 1e-4 cosine, 2 epochs, eff. batch 64, 2048 ctx, cuDNN SDPA off, grad guard)
| Arm | Data | Rows | Purpose |
|---|---|---|---|
| v2 (done) | chat only | 11,910 | baseline: persona without math |
| **v3a** | chat + A | 14,719 (19% math) | tests the "correct Sheldon math suffices" hypothesis at zero generation cost; can launch immediately |
| **v3b** | chat + A + B | ~19,200 (38% math) | adds explicit-step, eval-format-matched math |
Checkpoints every ~10% epoch as before; identical trajectory eval (GSM8K test strict/lenient/boxed + 542 persona prompts + marker
rates) so the three curves overlay directly. Optional extra eval for "different distribution" math: SVAMP (1,000 easy word
problems, different phrasing) with the same verifier.

## Expected outcomes and decision rule
- v3a: GSM8K should recover well above v2 (correct in-character math present) but may stay below base because of prose steps and
  long preambles; boxed rate should approach 100%.
- v3b: GSM8K near or above base (86.7%), boxed rate ~100%, persona rate on chat prompts unchanged vs v2.
- If v3a already lands within ~3 points of base, skip generation and use v3a as the SFT baseline for RLAIF/RLVR.

## Steps
1. `prepare_data.py --include-math verified` -> A (re-verify numerically, caps, splits). Launch v3a. (~40 min incl. eval sweep)
2. `gen_math_sheldon.py`: 50-row pilot -> inspect, measure acceptance rate and cost -> full 4,500. (~1 h wall)
3. Merge A+B+C, launch v3b, run the same sweeps, overlay v2/v3a/v3b in one plot; update HF cards; write findings.
