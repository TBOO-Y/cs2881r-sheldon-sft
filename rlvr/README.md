# Stage 3: RLVR on competition math (`rlvr/`)

Plan and rationale: `PLAN.md` (task choice, recipe, compute, decision rules). Status 2026-09-24: code written and unit-tested on the laptop
(CPU); nothing has run on the pod yet.

```
rlvr/
  PLAN.md                    the reviewed plan (v2)
  grader.py                  last \boxed{} extraction -> exact fast path -> math-verify equivalence (int timeouts; process pool with a hard timeout)
                             `python rlvr/grader.py --selftest` (39 cases, 37 as expected, 0 must-case failures; the 2 info cases document verifier limits)
  reward.py                  MathReward for TRL: None for truncated completions (-> excluded from group stats + loss), 1/0 otherwise, optional DAPO
                             soft-overlong penalty; per-step metrics under rlvr/ (acc, truncation, boxed, group pass-rate histogram)
  trainer.py                 RLVRTrainer(GRPOTrainer, TRL 1.13.0): zero-variance group masking with recomputed denominators, prompt-level
                             (DAPO-paper) aggregation through per-row advantage weights, optimizer factory, drift / update-RMS logging
  optim/muon.py              Muon (Newton-Schulz, Moonlight RMS rule) and Muon^p (p = 1/3 cubic recurrence, arXiv 2606.13867), param split, AdamW
  train_rlvr.py              CLI (defaults = PLAN.md main run: 16 x 16, 2,048 tokens, CISPO eps_high 5, group std, prompt aggregation, WSD, 200 steps)
  eval_math.py               vLLM eval: MATH-500 (per level, L3-5), AIME 24/25/26, GSM8K; greedy or avg@n / pass@n; merges a LoRA adapter on the fly
  summarize_run.py           Markdown tables from evals/rlvr/ + trainer_state.json -> results/rlvr/*.md
  data/build_math.py         MATH-12k (rasbt mirror) + MATH-500 + AIME 24/25/26 -> data/*.jsonl; contamination report (10-gram, edit-sim >= 0.9)
  data/label_passrate.py     k rollouts per training problem under a model (vLLM, sharded per GPU) -> passrate_<tag>.jsonl + per-level table
  data/build_schedule.py     pass-rate buckets -> ordered prompt list per run; prints per-phase mix and expected zero-variance fraction
  runpod/                    env.sh (sources rlaif/runpod/env.sh), serve_vllm.sh (one GPU: dense models cannot data-parallel in TRL 1.13), run_rlvr.sh, label.sh, eval.sh, follow_eval.sh,
                             baselines.sh (step 0), smoke.sh (step 2), pilot.sh (steps 3-4), main.sh (step 5)
  tests/                     CPU tests: grader, reward, aggregation algebra, Muon/Muon^p, schedule  (`for t in rlvr/tests/test_*.py; do .venv/bin/python $t; done`)
```

Data built on the laptop (2026-09-24, `python rlvr/data/build_math.py`): 11,998 MATH-12k rows with an answer (2 unrecoverable), 189 dropped as
near-duplicates of MATH-500 problems (template twins that differ only in the numbers, plus one verbatim duplicate the mirror's exact-match
dedup missed); 0 hits against AIME 2024/2025/2026. Final training file: 11,809 rows (levels 1-5: 928 / 2,100 / 2,576 / 2,733 / 3,470).

## Order of operations on the pod

```bash
POD=<pod> bash rlvr/runpod/sync.sh && ssh <pod> 'bash /root/cs2881r/rlaif/runpod/setup_node.sh && bash /root/cs2881r/rlvr/runpod/setup_stage3.sh'   # venv, base model, math-verify, seed + touch-up from the Hub
ssh <pod>; cd /root/cs2881r
bash rlvr/runpod/baselines.sh                                # step 0: base / touch-up / grpo-v2 full suite -> results/rlvr/baselines.md
TAG=grpo-v2 bash rlvr/runpod/label.sh                        # step 1: 12k x 8 rollouts of the seed -> rlvr/data/passrate_grpo-v2.jsonl, results/rlvr/difficulty_grpo-v2.md
TAG=base MODEL=Qwen/Qwen2.5-3B-Instruct K=4 bash rlvr/runpod/label.sh
python rlvr/data/build_schedule.py --train rlvr/data/math12k.jsonl --passrate rlvr/data/passrate_grpo-v2.jsonl --steps 200 --prompts_per_step 16 --G 16 --out rlvr/data/schedule_main.jsonl
bash rlvr/runpod/smoke.sh                                    # step 2: 3 steps in both layouts
bash rlvr/runpod/pilot.sh                                    # step 3: pilot-full-adamw vs pilot-lora-adamw (20 steps) -> results/rlvr/pilots.md
PILOTS="full-muon full-muonp" bash rlvr/runpod/pilot.sh      # step 4a (only if full FT won): optimizer pilots
PILOTS="lora-lenpen" bash rlvr/runpod/pilot.sh               # step 4b: length penalty on the winning layout (or full-lenpen WINNER_OPT=...)
MODE=colocate bash rlvr/runpod/main.sh                       # step 5: 200 steps (+ OPT=..., LENPEN=...) -> results/rlvr/rlvr-main.md
```

Laptop dry run without a GPU (HF generation instead of vLLM, a small model, 2 steps):
`RLVR_CPU_DRYRUN=1 CUDA_VISIBLE_DEVICES= WORLD_SIZE=1 .venv/bin/python rlvr/train_rlvr.py --model Qwen/Qwen2.5-0.5B-Instruct --schedule rlvr/data/schedule_smoke.jsonl --run_name dry --vllm_mode none --lora 1 --optimizer muonp --prompts_per_step 2 --num_generations 2 --per_device_bs 2 --max_completion_length 32 --max_steps 2 --report_to none --no_merge --bf16 0 --cast_lm_head_fp32 0`
(the smoke schedule: `python rlvr/data/build_schedule.py --train rlvr/data/math12k.jsonl --by_level --steps 8 --prompts_per_step 4 --G 4 --out rlvr/data/schedule_smoke.jsonl`).

## Semantics worth knowing when reading the logs

- `rewards/math_correct/mean` is over scorable (non-truncated) completions; `rlvr/frac_truncated`, `rlvr/frac_zero_var_groups`, `rlvr/live_prompts` say how much of each batch actually trained.
- `sampling/importance_sampling_ratio/mean` must sit near 1: it was 0.03 in the RLAIF run because of the repetition penalty (now 1.0, T = 1, top-p = 1). `sampling/sampling_logp_difference/mean` is the trainer-vs-vLLM per-token logprob gap (the mismatch the fp32 head reduces); the smoke test prints it for a bf16 and an fp32 sampler.
- `cispo_clip_ratio` is the fraction of positive-advantage tokens whose IS ratio exceeded eps_high (5.0); it should be ~0 on-policy.
- `rlvr/param_drift_rel` every 25 steps (relative L2 change of the trainable parameters since step 0), `rlvr/update_rms` for the Muon family.
- Checkpoints are model-only (`save_only_model`); a full-FT checkpoint is fp32 (12 GB), export to bf16 happens in the merge at the end.
- `rlvr/frac_grader_fallback` counts completions whose symbolic check timed out and fell back to exact string matching (should be ~0).
- Review 2026-09-24 (adversarial workflow, 35 findings, 9 confirmed) fixed before any pod run: fp32-head flag crashes with PEFT (now auto-off for LoRA), the head re-patch
  so it really runs in fp32 under autocast, dense models cannot be served data-parallel (single-GPU server), vLLM stop that matched nothing, Muon-p's
  rank-dependent power iteration, whole-batch grader fallback (now per item), `--penalize_truncated` removed, checkpoint readiness on trainer_state.json.
