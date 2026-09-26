# Stage 3b plan: continue from checkpoint-125 with re-labelled difficulty (draft for review, 2026-09-26)

## 1. What went wrong in rlvr-main (from runs/rlvr-main/trainer_state.json and schedule_main.jsonl)

| steps | train acc | all-wrong groups | all-correct groups | mixed | dead | live prompts / 16 | mean len |
|---|---|---|---|---|---|---|---|
| 1-25 | 0.43 | 0.12 | 0.02 | 0.87 | 0.13 | 13.9 | 161 |
| 51-75 | 0.62 | 0.10 | 0.20 | 0.70 | 0.30 | 11.2 | 235 |
| 76-100 | 0.71 | 0.09 | 0.37 | 0.54 | 0.46 | 8.7 | 282 |
| 101-125 | 0.73 | 0.09 | 0.40 | 0.52 | 0.47 | 8.4 | 346 |
| 176-200 | 0.71 | 0.10 | 0.40 | 0.51 | 0.47 | 8.4 | 480 |

The dead half of every batch after step 75 is all-correct groups. The bucket labels were the seed's pass rates (mean 0.22) and never
moved, while the policy went from 43% to 73% accuracy on the same mix; the schedule's drift toward "hard" (12% -> 29%) was far too slow
to track that. All-wrong groups stayed at ~10% even as the hard share (seed pass rate exactly 0) doubled, i.e. the model learned to solve
a good part of the "unsolvable" pool. Conclusion: the zero-variance problem here is a stale-label problem, not a data-difficulty problem.

## 2. Fix: staged re-labelling, information-weighted sampling

Labelling the full 11.8k pool with a checkpoint costs ~5-8 min on 3 GPUs (12k x 8 rollouts; measured 3 min with the short-answer seed,
the current policy writes ~450-token answers). That is cheap enough to do at every stage boundary.

- Continue in **stages of 50 steps**. At the start of each stage: merge the current adapter, label the whole pool with that model
  (k = 8, T = 1, 2,048 tokens), build the next 50-step block from the fresh labels.
- **Sampling weights ∝ p̂(1 - p̂) + ε** inside the band 1/8 ≤ p̂ ≤ 7/8 (the group-variance-maximising rule; ~50% pass rate is the most
  informative), where p̂ is the fresh pass rate. p̂ = 1 dropped; a **frontier slice of 10%** drawn from p̂ = 0 prompts (fresh each stage),
  because the run showed those get solved. No prompt repeated within a stage. Expected dead fraction with G = 16 under the binomial:
  ≤ 12% at the band edges, ~0 in the middle, plus ~9% from the frontier slice -> ~6-8% overall versus 47% at the end of rlvr-main.
- This is the one deviation from the original "no dynamic scheduling" rule: not per-step tracking, but a re-label every 50 steps
  (~10% time overhead). Everything else (CISPO, group std, prompt aggregation, masking, G = 16, 16 prompts/step, 2,048 tokens,
  length penalty on, LoRA r32 + AdamW 2e-5, fp32 head, bf16 vLLM) stays as in rlvr-main.

Pool size: the band after re-labelling with checkpoint-125 is estimated at ~4k prompts (seed-easy/solved 1.7k are gone; ~half of the
4.7k medium and ~30% of the 5.3k hard land in the band). Three stages need 3 x 800 = 2.4k prompt visits, so no repeats, but the band
shrinks each stage as the model improves, which is why section 4 matters.

## 3. Start point and run shape

- **Seed: checkpoint-125 merged** (`rlvr-main/checkpoint-125` adapter merged into grpo-v2-merged), as you asked. For the record,
  checkpoint-200 is better on L3-5 (55.2 vs 52.9), L5 (37.3 vs 31.7) and GSM8K (82.0 vs 80.4); the later steps were half-dead but
  not harmful. If you prefer the stronger start, only `--model` changes.
- Each stage = its own run with a fresh LoRA r32 on the previous stage's merged model, fresh AdamW, warm-up 5 steps, **constant LR
  2e-5, no decay in stages 1-2; the last stage decays linearly over its last 20 steps** to 0.1x, so the three stages together are one WSD.
- 3 stages = 150 steps. Per-checkpoint quick eval every 25 steps as before; full suite at the end. Stop rule: if a stage's L3-5 avg@4
  gain is < 1 point and the fresh band is < 1.5k prompts, stop and report instead of running the next stage.
- Success criteria: dead fraction < 15% throughout; L3-5 avg@4 ≥ 59 (base); L5 > 40 (base). Literature ceiling for 3B RLVR is
  ~63-68 MATH-500 greedy (we are at 65.0), so the realistic upside is a few points, mostly on L4-5.

## 4. Expanding the hard-but-learnable pool (before any synthetic generation)

Verified external problems first, labelled by the current policy and admitted only if they fall in the band:
1. **DeepMath-103K** (MIT; GPT-4o difficulty 5-9; strongest decontamination of the candidates: 0 MATH-500 near-duplicates in the paper's
   audit, AIME/AMC checked). Take a 20k sample at difficulty 5-7 with `final_answer` parseable by math-verify; label with the current
   model (~10 min); keep the band. Expected yield: a few thousand band prompts.
2. **DAPO-Math-17k-Processed** (integer answers, easy to grade) as a second source, after our own 10-gram / edit-similarity check against
   MATH-500 and AIME 24-26 (`build_math.py` already does this).
Both go through the existing contamination report; anything within similarity 0.9 of an eval problem is dropped.

Synthetic generation only if the band pool falls below ~2k after step 1-2: (a) **answer-preserving rewrites** of band prompts by a
strong model (numbers unchanged, wording changed; the gold answer carries over, so the reward stays exact); (b) **new problems** with
answers fixed by agreement of two independent strong-model solutions AND a programmatic check where possible; disagreements discarded.
Route (a) is safe and cheap; route (b) needs a pilot audit of 100 items before use. I would not generate before exhausting 1-2.

## 5. Code changes (small, on top of the existing stage-3 code)

- `rlvr/data/build_schedule.py`: `--mode band` (weights ∝ p̂(1-p̂)+ε within [lo, hi], frontier fraction from p̂ = 0, no repeats,
  prints expected dead fraction as now).
- `rlvr/data/build_math.py`: `--extra deepmath|dapo17k` loader + the existing contamination filter, writing `rlvr/data/extra_*.jsonl`.
- `rlvr/runpod/stage3b.sh`: sequencer: merge -> label -> schedule -> 50-step run -> quick eval, x3, with the stop rule; final full suite.
- `train_rlvr.py`: `--wsd_decay_frac 0` already yields warm-up + constant; nothing else needed.
- Time on 3x H200: per stage ~8 min label + ~45 min train + ~8 min eval ≈ 1 h; 3 stages ≈ 3 h (~$35). Extra-pool labelling +10 min.

## 6. Pool expansion results and source weighting (2026-09-26, `rlvr/data/build_extra.py`, report in `extra_report.json`)

| source | raw sample | dropped: dup / contaminated / other | kept | answer type | notes |
|---|---|---|---|---|---|
| MATH-12k (existing) | 11,809 | - | 11,809 | LaTeX | in-distribution for MATH-500 |
| DeepMath-103K, difficulty 5-8 | 30,000 | 1,714 / 98 / 10 | 28,178 | numeric + symbolic | includes MATH-train look-alikes (the dups); best-decontaminated source |
| DAPO-Math-17k (en) | 14,116 | 3,515 / 760 / 28 | 9,813 | integer | 760 near-duplicates of MATH-500 / AIME / GSM8K-test removed |
| DeepScaleR-Preview (20k sample) | 20,000 | 4,704 / 356 / 54 | 14,886 | mixed | AIME/AMC/Omni level; most will land in the frontier |
| **total pool** | | | **64,686** | | |

Contamination filter: 10-gram overlap or edit similarity >= 0.9 against MATH-500, AIME 2024/25/26 and GSM8K test; cross-source dedup on
normalised text. The extra files are regenerable (git-ignored); the report is committed.

**Labelling cost.** 64.7k prompts x 8 rollouts at ~450 tokens is ~40-50 min on 3 H200 per pass, so only stage 1 labels the whole pool
(with the checkpoint-200 model). Later stages re-label the previous stage's non-solved prompts (0 < p̂ < 1) plus a 3k random subsample of
the p̂ = 0 frontier; solved prompts keep their label. Expected: ~15 min per later stage.

**Weighting (per 50-step block of 800 prompts).** Sampling is by p̂(1 - p̂) inside the band regardless of source, then per-source caps:
MATH-12k uncapped (it is the eval distribution; it will supply what the band has left), DeepMath <= 30%, DAPO <= 20%, DeepScaleR <= 20%,
so at least 30% of every block is MATH-12k and no external source dominates; 10% frontier from p̂ = 0 across all sources. The rationale:
external sources widen the hard-but-learnable band (their integer / olympiad answers are graded exactly), while the caps keep the LaTeX
answer style and topic mix of MATH-500 in the majority. After stage 1's labels exist, the actual band sizes per source are printed and
the caps can be tightened if one source has a very different pass-rate profile (e.g. DAPO integer problems being systematically easier).

Pending inputs: the stage-1 labels (pod). The synthetic-data route stays as the fallback in section 4.
