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

## Addendum (laptop, after pulling the pod artifacts)

Smoke-test measurement of the trainer-vs-sampler mismatch (per-token |Δ log p| between the fp32-head trainer and vLLM, 3 steps each):
bf16 sampler 0.016-0.018 (full FT) / 0.017-0.020 (LoRA, colocated); fp32 sampler 0.008-0.009. The truncated-IS ratio mean is 1.000 in
all three, i.e. the correction has nothing to clip at this level. bf16 sampling (the accepted default) is fine for the main run.
Pod-side code change carried back: `NCCL_NVLS_ENABLE=0` in `rlvr/runpod/env.sh`. Pilot trainer states are in `runs/pilot-*/trainer_state.json`.
