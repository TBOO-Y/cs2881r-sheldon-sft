# Stage 3 (RLVR) pilot notes, 2026-09-25

Sequencer `rlvr/runpod/stage3_pilots.sh` finished (`logs/stage3.stage` = done, 19:25Z). Main run NOT started (by instruction).
Full tables: `pilots.md`, `baselines.md`, `difficulty_grpo-v2.md`, `difficulty_base.md`.

## Pilot results (20 steps, 16 prompts x 16 gens, seed = grpo-v2-merged; MATH-500 avg@4)

| run | MATH-500 avg@4 | L3-5 avg@4 | L5 | GSM8K | hit cap % | tokens | s/step |
|---|---|---|---|---|---|---|---|
| seed grpo-v2 (ref) | 29.6 | 21.0 | 10.6 | 63.6 | 4.2 | 357 | - |
| full FT + AdamW (lr 1e-6) | 31.9 | 22.8 | 8.8 | 63.8 | 3.2 | 331 | 26.8 |
| LoRA r32 + AdamW (lr 2e-5) | 35.1 | 25.7 | 13.2 | 65.0 | 3.6 | 346 | 24.0 |
| LoRA + AdamW + DAPO soft length penalty | 34.9 | 26.2 | 11.8 | 64.9 | 3.0 | 327 | 20.8 |

- Pilot 1 decision rule (full FT must beat LoRA by > 3 pts on L3-5): LoRA won (25.75 vs 22.82), so the Muon / Muon^p pilots were skipped as planned.
- Length-penalty pilot: truncation fell (3.6 -> 3.0 %) and L3-5 was flat (+0.5), so the plan's keep rule is met. Both differences are within
  noise (L3-5 is ~320 problems x 4 samples, SE roughly 1-1.5 pts); L1 fell 69.2 -> 62.2, but that is only 43 problems.
- Training reward moved little in 20 steps (0.42-0.43 -> 0.44-0.45); mean training completion length is ~160 tokens.

## Recommended main-run config (if you approve the main run)

LoRA r32/a64 on all linear projections, AdamW lr 2e-5 (betas 0.9/0.95, eps 1e-15, wd 0.01), `vllm=colocate` on GPUs 1,2, otherwise the
PLAN.md defaults (16 x 16, 2,048 tokens, CISPO eps_high 5, group std, prompt aggregation, WSD 10 / to 160 / decay 40, 200 steps,
`schedule_main.jsonl`). Length penalty: optional. The keep rule is formally met, but the gain is within noise; turning it on is a low-risk default.
Expected cost: ~21-24 s/step -> ~1.2-1.4 h for 200 steps.

## Issues

1. **Seed quality (needs your decision):** grpo-v2-merged scores far below the base model it came from: MATH-500 greedy 34.0 vs 68.0,
   L3-5 avg@4 21.0 vs 59.0, GSM8K 63.6 vs 86.1, AIME pass@16 3.3 vs 21.1. sft-touchup-v4 is equally low, so the regression dates to the SFT
   stage. After 20 pilot steps the best arm still sits about 33 pts under base on L3-5. The pipeline order fixes the seed, but you may want an
   RLVR-from-base comparison, or a check that the SFT stage's chat template / system prompt isn't what hurts math. Not changed by me.
2. **Env fix, NCCL:** the trainer<->vLLM weight-sync communicator failed with `NCCL error: unhandled cuda error`. The root cause was
   `Failed to bind NVLink SHARP (NVLS) Multicast memory ... CUDA error 1 'invalid argument'` (the pod's Fabric Manager / NVSwitch config).
   Fixed by `export NCCL_NVLS_ENABLE=0` in `rlvr/runpod/env.sh` and confirmed with a standalone 2-process test. No algorithm change.
3. Earlier run (before this session's monitoring): `label_passrate.py` imported `rlvr.train_rlvr`, and its CUDA_VISIBLE_DEVICES assert failed.
   It had already been resolved when monitoring began (labels + schedule exist).
4. `/root/cs2881r` is not a git repository on the pod, so the requested commit could not be made.
5. Base-model pass-rate labels were also written (`rlvr/data/passrate_base.jsonl`, K=4, mean pass 0.64) for the write-up.

# Main run `rlvr-main` (2026-09-25, user go-ahead)

Config: LoRA r32/a64 + AdamW lr 2e-5, DAPO soft length penalty on, 16 x 16, 2,048 tokens, WSD 10 / 160 / 40, 200 steps, seed grpo-v2-merged,
`MODE=colocate` on GPUs 1,2. Launched 20:26Z; training finished at ~22:40Z (2 h 13 min; step time grew from ~20 s to ~50 s as completions
lengthened), full-suite eval done at ~22:50Z. No crashes, no interventions. Full table: `rlvr-main.md`.

| model | MATH-500 greedy | avg@4 | L3-5 avg@4 | L5 | GSM8K | AIME24/25/26 avg@16 | AIME pass@16 | tokens |
|---|---|---|---|---|---|---|---|---|
| seed grpo-v2 | 34.0 | 29.6 | 21.0 | 10.6 | 63.6 | 0.4 / 0.4 / 0.0 | 3.3 | 357 |
| **rlvr-main (final)** | **65.0** | **63.5** | **55.2** | 37.3 | 81.9 | 5.0 / 2.7 / 2.3 | 17.8 | 541 |
| base Qwen2.5-3B-Instruct | 68.0 | 66.6 | 59.0 | 40.1 | 86.1 | 8.1 / 2.3 / 4.4 | 21.1 | 633 |

L3-5 avg@4 by checkpoint: 25: 27.3, 50: 35.4, 75: 43.5, 100: 49.6, 125: 52.9, 150: 52.3, 175: 55.2, 200: 55.2. Most of the gain came in
the first 100 steps; it plateaus from ~125. Training reward 0.48 -> 0.69; the zero-variance group share rose to 0.48 at the end (half the groups
carry no signal), which is consistent with the plateau.

Reading: RLVR recovers most of what the SFT stage lost (+34 pts L3-5 over the seed) but ends ~4 pts below the untouched base on MATH-500
and GSM8K, and below base on AIME pass@16 (17.8 vs 21.1). So far it looks like recovery rather than improvement over base. The obvious
comparison is RLVR from base with the same config (issue 1 above). A harder schedule (more L4-5 / low-pass-rate prompts, since half the
groups end up zero-variance) is a second option. Neither is run.

# Stage 3c: full fine-tune attempt on the rlvr-main seed (2026-09-27, user decision after the flat 3b stages)

Setup: `rlvr/runpod/stage3c.sh`; seed rlvr-main (step 200); all parameters trained, fp32 master weights, AdamW lr 2e-6 (betas 0.9/0.95,
eps 1e-15, wd 0.01), WSD warm-up 5 / constant / linear decay over steps 80-100 to 0.1x; 100 steps x 256 rollouts; same CISPO / masking /
length-penalty recipe; band schedule (p̂(1-p̂), frontier 10%, source caps) from the stage-1 labels, which this seed produced. Server layout
on 3x H200 (vLLM on GPU 0, 2 DDP ranks), 62 s/step, 1 h 45 min training + 30 min evals. Full table: `rlvr-3c-fullft.md`.

| model | MATH-500 greedy | avg@4 | L3-5 | L4 | L5 | GSM8K | AIME pass@16 |
|---|---|---|---|---|---|---|---|
| rlvr-main (seed) | 65.0 | 63.5 | 55.2 | 56.4 | 37.3 | 82.0 | 17.8 |
| 3b LoRA stage 2 (+100 steps) | - | 63.6 | 55.3 | 58.8 | 34.7 | 82.0 | - |
| 3c full FT ckpt-25 / 50 / 75 / 100 | - | 63.6 / 63.6 / 64.5 / 65.1 | 55.2 / 55.4 / 56.0 / 56.9 | 58.0 / 58.6 / 59.6 / 60.9 | 33.0 / 35.1 / 35.4 / 35.3 | 82.1 / 82.0 / 83.6 / 82.5 | - |
| **3c full FT final** | **65.4** | **65.1** | **56.9** | **60.9** | 35.3 | 83.0 | 16.7 |
| base Qwen2.5-3B-Instruct | 68.0 | 66.6 | 59.0 | 60.5 | 40.1 | 86.1 | 21.1 |

- Full FT moves where LoRA did not: +1.6 on MATH-500 avg@4 and +1.7 on L3-5 over the seed, monotone across the four checkpoints with
  the biggest step in the decay phase; L4 now matches base (60.9 vs 60.5); L5 is flat (35 vs the seed's 37, base 40); GSM8K +0.5..1.5.
  Training reward 0.40 -> 0.43 (10-step means: 0.37, 0.40, 0.42, 0.40, 0.40, ...), dead groups ~11%, grad norm ~0.47, relative parameter
  drift 6.8e-4 (all parameters), IS ratio 1.000, CISPO clip 0.
- Magnitude: the gain is at the edge of the noise band (SE ~1.1 on L3-5 avg@4, ~1.2 on avg@4) but four monotone checkpoints and the
  greedy number (65.4 vs 65.0) point the same way. The remaining gap to base is 2.1 on L3-5 and 1.5 on avg@4, concentrated in L5.
- Reading: on this seed the LoRA r32 adapter was the binding constraint, not the data; full-parameter updates at 2e-6 still find
  improvement. A longer full-FT run (200-300 steps with staged re-labelling, ~4-6 h on this pod) is the natural continuation if the goal is
  to close the last two points; otherwise this checkpoint is the stage-3 result to carry into the combined-reward stage.
- Artifacts: merged model `models/rlvr-3c-fullft-merged` on the pod (+ volume mirror), not uploaded; `runs/rlvr-3c-fullft/trainer_state.json`,
  `evals/rlvr/rlvr-3c-fullft/`, `rlvr/data/schedule_rlvr-3c-fullft.jsonl`.
