# Stage 3 plan: RLVR on competition math (CISPO, full fine-tune, 8xH100)

Status: draft v2 after the first review, 2026-09-24 (seed fixed to grpo-v2-merged, batch <= 256, 200 steps, LoRA-vs-full pilot added). Nothing in this file has been run yet. Numbers marked (est.) are estimates to be
replaced by measurements from the pilot runs; numbers with a citation are from the papers/cards listed at the end.

## 1. Task choice: MATH-500 (levels 3-5 as the headline), AIME 24/25/26 as a secondary pass@k signal

What the literature says about Qwen2.5-3B-Instruct (the base of every model in this project):

| benchmark | base Qwen2.5-3B-Instruct | after GRPO/DAPO-style RLVR at 3B | source |
|---|---|---|---|
| MATH (full test, official) | 65.9 | - | Qwen2.5 report, Table 9 |
| MATH-500, greedy, >=4k tokens | 62.0-65.8 | 66-68 (Instruct start) / 63-68 (base start) | APMPO Tab. 1; MiCoTA Tab. 2; 2504.14350 Tab. 1; INTUITOR; 2505.14216; lambda-GRPO |
| MATH-500 at a 1,024-token cap | 46.4 | - | 2502.20122 (the cap costs ~16 points) |
| MATH-500 pass@256 (3B base) | 95.8 | 95.8 (unchanged after RL) | 2505.14216 Tab. 3 |
| AIME 2024, pass@1 | 0-3.3 (0-1 of 30) | 5-10 (2-3 of 30); pass@16 3 -> 13-17 | APMPO; MiCoTA; MathForge |
| AIME 2025, pass@1 | 0-0.7 | 2-10; pass@16 7 -> 13-20 | APMPO; MathForge |
| AIME 2026 | no published number for any Qwen2.5-3B model | - | MathArena/aime_2026 exists (30 integer answers) |
| AMC 2023 | 35 | 40-45 | APMPO |
| GSM8K | 85.7 (our own greedy eval) | 82-90 | this repo; INTUITOR |
| natural response length | ~480 tokens on MATH-500, ~250-290 on GSM8K | grows moderately under RL at 3B | 2502.20122; Weyaxi handbook |

Where the gain comes from at this scale: most of the MATH-500 improvement arrives within 60-150 optimizer steps (INTUITOR: one
epoch of MATH train = 58 steps at batch 128; 2505.14216: peak at step 150; lambda-GRPO: plateau near step 120), and pass@256 does not
move, i.e. RL at 3B sharpens what the model can already sample rather than adding new capability. The learnable band is therefore
"problems the seed solves sometimes": base pass@1 55-65 vs pass@256 96 on MATH-500 says that band is wide on MATH, and it is
empirically MATH levels 4-5 (levels 1-3 are near ceiling for the base model).

Why not AIME as the primary task: the seed is at 0-1 problems of 30; RL at 3B reaches 2-3 of 30. One problem is 3.3 points, so a
"+7 point" result is two problems and inside sampling noise even at avg@16. AIME-style training sets (DeepScaleR, DAPO-17k) are also
integer-answer / olympiad-level, where a 3B non-reasoning model has a pass rate near zero on most prompts, which is exactly the
zero-variance regime the run must avoid. AIME 24/25/26 stay in the eval suite as avg@16 (16 samples, T=0.6, 4,096 tokens) so the
write-up can report them, but the decision metric is MATH-500 by level.

The seed complicates this in our favour. The RLAIF output (`grpo-v2`, GSM8K 64.0 vs base 85.7) is ~20 GSM8K points below base,
so its MATH-500 is expected around 45-55 (est.) with headroom to the 63-68 ceiling that RL reaches at 3B. Step 0 of the plan measures
this for base, touch-up and grpo-v2 before anything is trained.

**Decision for you (seed):** the pipeline order (SFT -> RLAIF -> RLVR -> combined) says the seed is `models/grpo-v2-merged`. The base
model is measured as the reference ceiling only. If you would rather RLVR the touch-up model (pre-RLAIF), only the `--model` argument
changes.

### Training set: MATH-12k with human levels plus our own pass-rate labels

`rasbt/math_full_minus_math500` (12,000 rows, Apache-2.0): MATH train (7,500) plus the 4,500 MATH test problems that are not in
MATH-500, exact-match deduplicated against MATH-500. It carries `level` (1-5) and `type` (7 subjects), same distribution as the target.
The original `hendrycks/competition_math` is disabled on the Hub (DMCA), so this mirror or `EleutherAI/hendrycks_math` is the way to
load it.

Why this and not the larger sets:

| set | difficulty field | problem with it for us |
|---|---|---|
| DeepScaleR-40k | none | AIME/AMC/Omni-MATH level, ~10 MATH-500 near-duplicates (DeepMath audit); mostly unsolvable by a 3B model |
| DAPO-Math-17k | none | integer-reformulated olympiad problems, ~8 MATH-500 near-dups, raw set is 100x duplicated |
| DeepMath-103K | GPT-4o rating 3-9 | best decontamination of all, but 95k of 103k are rated >=5 (olympiad); the 8k rated 3-5 ARE MATH train lvl 3-5 |
| Big-Math-251k | Llama-3.1-8B solve rate | closest capability proxy, but gated, and 36% of it is <0.2 solve rate for an 8B model |
| Skywork-OR1 / POLARIS / GURU / MiroMind | pass rates of R1-distilled reasoning models at 32k tokens | say "everything is hard" for a 3B non-reasoning model |

The human `level` is coarse and was set for humans, not for this seed. So step 1 of the plan labels every training prompt with the
seed's own pass rate: 8 rollouts x 12k prompts x 2,048 tokens through vLLM on 8 GPUs, ~15-20 min (est.). That gives the schedule a
model-specific difficulty axis (0/8 .. 8/8) next to `level`, and gives the write-up a per-level pass-rate table for the seed. The label
run is repeated for the base model so we can show how the persona SFT/RLAIF shifted the difficulty profile.

Contamination: MATH-12k has no MATH-500 overlap by construction; `data/build_math.py` additionally runs a 10-gram and normalized
edit-similarity (>=0.9) check of every training prompt against MATH-500, AIME 2024/2025/2026 and reports the counts (expected: 0).

### Difficulty schedule (static, decided before the run)

Buckets from the seed's pass rate p (8 rollouts): easy 0.5 < p < 1, medium 0.125 <= p <= 0.5, hard p < 0.125 (includes p = 0),
solved p = 1 (dropped: zero variance with certainty). The run's prompt order is generated once by `data/build_schedule.py` as a mixture
that drifts linearly over the run from (easy 0.5, medium 0.4, hard 0.1) to (easy 0.2, medium 0.5, hard 0.3). The script prints the
expected zero-variance fraction per phase for the chosen group size (from the binomial with the measured p), so the mix can be tuned
on paper before spending GPU time. No prompt is repeated within the run unless the schedule needs more prompts than a bucket holds
(printed as a warning). Dynamic (pass-rate-tracking) scheduling is deliberately out, as you asked.

## 2. Run recipe (your parameters, blanks filled)

| item | choice | note |
|---|---|---|
| seed | `models/grpo-v2-merged` (decided) | LoRA vs full fine-tune settled by the first pilot, see section 4 |
| parameters trained | **pilot decides**: LoRA r32/a64 on all linear projections (AdamW, lr 2e-5) vs full fine-tune (AdamW, lr 1e-6) | if LoRA is not significantly weaker at 20 steps, LoRA + AdamW is the main run and the Muon pilots are skipped (Muon on LoRA factors is unprincipled; 2605.10468 ~= AdamW, 2507.12142 -4 pts). If full FT wins, the Muon / Muon-p pilots run on full FT. Full FT fits per GPU: fp32 master 12 GB + grads 12 GB + AdamW 24 GB with gradient checkpointing |
| precision | **fp32 LM head on the trainer in both arms** (`RLVRTrainer._patch_fp32_head`: the head matmul runs outside autocast on an fp32 copy of the weight, logits fp32, exact logsumexp; TRL's own flag is not used because autocast re-casts its matmul to bf16 and it crashes on PEFT models). Full FT: fp32 master weights + bf16 autocast elsewhere. LoRA: bf16 frozen base, fp32 adapter. Generator: bf16 vLLM by default (`DTYPE=float32` on the server is the generator-side half of the MiniMax fix at ~2x decode time; the smoke test logs `sampling/sampling_logp_difference/mean` for both so the choice is measured, not guessed). vLLM token-level truncated IS correction stays on in both arms | at lr 1e-6 a pure-bf16 parameter update is below bf16 resolution and silently vanishes; fp32 head is the MiniMax/ScaleRL fix (A 0.52 -> 0.61 in ScaleRL). Measured on Qwen2.5-0.5B: bf16 head rounding moves logits by up to 0.056 and the sampled token's logprob by 0.006 mean / 0.014 max per token |
| loss | **CISPO** (`loss_type="cispo"`, token-level IS ratio, no lower clip, `epsilon_high = 5.0`) | TRL uses `epsilon_high` as the absolute cap for CISPO (ScaleRL's eps_max, ablated over {4,5,8}: insensitive). The TRL default 0.2 would cap ratios at 0.2, a silent bug. No KL term (`beta = 0`, as in MiniMax-M1 / ScaleRL); no reference model in memory |
| loss aggregation | **DAPO-paper formula**: token mean within each prompt's group, then mean over (non-masked) prompts | this is what ScaleRL calls "prompt average" and adopted. TRL's `dapo`/`cispo` code is a batch-wide token mean instead, so `RLVRTrainer` overrides `_compute_loss` with a per-row weight 1/(tokens in that prompt's group x number of live prompts) |
| advantage | group mean baseline, **group (prompt-level) std** (`scale_rewards="group"`) | your explicit decision against ScaleRL's batch-level std, recorded here as such |
| truncations | **masked and excluded from the group statistics** | reward fn returns `None` for a completion whose last token is not EOS -> TRL treats it as unscorable (nan-mean/std over the remaining rollouts, advantage 0) and `mask_truncated_completions=True` removes its tokens from the loss and its denominator. Net effect: a group of 8 with one truncation behaves as a group of 7 |
| zero-variance groups | **masked** | `RLVRTrainer` zeroes the completion mask of every group whose advantages are all 0 (all rewards equal after the truncation exclusion) and recomputes the token count and live-prompt count, so they contribute neither gradient nor denominator. Logged as `rlvr/frac_zero_var` |
| length penalty | off in the main pilots; DAPO soft overlong punishment as a flag | R_len = 0 for L <= L_max - L_cache; linearly to -1 at L_max; L_max = max completion length, L_cache = 512 (DAPO: 4,096 of 20,480). Applied to terminated completions only; truncated ones are always masked (DAPO's "-1 for over-length" variant is not offered: it would conflict with the masking above) |
| reward | binary correctness via `math-verify` (gold wrapped in `\boxed{}`, exact-string fast path, 5 s timeout) | no separate format reward: the seed boxes 99.8% of GSM8K answers already. Unboxed answer = 0 |
| prompt format | system prompt as in every earlier stage, user = problem + "\nPlease reason step by step, and put your final answer within \boxed{}." | identical to `sft/eval_gsm8k.py`, so train and eval prompts match |
| sampling | T = 1.0, top-p = 1.0, **no repetition penalty** | the RLAIF run used repetition_penalty 1.05, which made vLLM's sampling distribution differ from the trainer's (logged mean IS ratio 0.03); RLVR needs the sampler and trainer to agree |
| max completion length | **2,048** tokens (train); 4,096 for AIME eval | ~480-token natural length on MATH-500; 2k is the common choice at 3B (lambda-GRPO 2,048, VIGOR 2,560, INTUITOR 3,072). Truncation rate is monitored; if it exceeds ~5% the schedule (not the cap) is the first lever |
| global batch | **256 rollouts = 16 prompts x 16 generations** (sqrt(256) = 16 exactly; your cap) | G = 16 keeps a p = 0.05 prompt alive with probability 0.56 (vs 0.34 at G = 8) |
| updates per batch | 1 (on-policy, `num_iterations = 1`) | CISPO's IS truncation still matters because vLLM and the trainer differ numerically (TRL's `vllm_importance_sampling_correction` stays on) |
| steps | **200** main run; pilots 20 (= 10%) | 200 x 16 = 3,200 prompt visits, 51k rollouts (a third of MATH-12k levels 3-5, no repeats). INTUITOR's +9 MATH-500 came from 58 steps x 128 = 7.4k rollouts, so 51k is not small at this scale; WSD decay over the last 40 steps |
| LR schedule | **WSD**: 10 warm-up steps, stable to step 160, linear decay over the last 40 steps (20%) to 10% of peak | transformers' native `warmup_stable_decay`, laid out for `--schedule_total_steps 200` even in the 20-step pilots, so they run the first 20 steps of the main schedule (no decay reached). Note: WSD is a pretraining-validated convention; every RL recipe read (DAPO, ScaleRL, MiniMax) uses warm-up + constant |
| peak LR | AdamW **1e-6** (betas 0.9/0.95, eps 1e-15 as in ScaleRL/MiniMax, wd 0.01); Muon and Muon-p at the **same nominal 1e-6** via RMS-matching (update RMS 0.2 like AdamW, Moonlight rule) | full-FT RL at 3B in the literature: 1e-6 (DAPO, 2505.14216, VIGOR), 3e-6 (INTUITOR), 5e-7 (ScaleRL). The RLAIF lesson (1e-6 did nothing) was LoRA, which needs 10-100x higher LR; it does not transfer to full FT |
| optimizer pilot | only if full FT wins the first pilot: 20 steps each, Muon and Muon-p (p = 1/3) vs the AdamW pilot already run | see section 4 |
| checkpoints | every 25 steps (fp32 -> bf16 export), follow-eval on the spare GPU | MATH-500 by level (greedy + avg@4), GSM8K greedy, AIME avg@16 at 100/200/300 only, 60 short persona prompts for drift |

Non-default choices I am making that you did not specify:

- `beta = 0` (no KL). CISPO/ScaleRL/DAPO all drop it; it removes a reference forward pass. The persona drift is monitored instead of
  constrained, because constraining it is the combined-reward stage's job.
- G = 16 rather than 8. The RLAIF run used 8 with a continuous reward; binary rewards need more samples per prompt to see variance.
- No dynamic sampling / no positive resampling (ScaleRL drops prompts with historical pass rate >= 0.9). The static schedule already
  excludes p = 1 prompts and the schedule builder prints the expected dead fraction; that is your "fix it with better scheduling" rule.

## 3. Compute: layouts, what one step costs, and what full on-policy synchrony costs

Evidence from the RLAIF run (`logs_pod/grpo-v2.log`): steps whose judge calls were cached took 18-20 s for 128 rollouts of mean
~240 tokens plus a LoRA update, on ONE H100 with vLLM colocated at 35% memory; the rest of the 65-75 s step was judge latency, which
RLVR does not have. TRL 1.13 offers two generation layouts and no asynchronous pipeline:

- **server layout** (full FT): GPU 0 runs `trl vllm-serve` (one engine: TRL 1.13 documents data-parallel serving as unsupported for
  dense models; a 3B model plus KV cache for 256 x 2.8k tokens fits one H100), GPUs 3-6 train under DDP, GPU 7 evaluates, GPUs 1-2 are
  spare (the base-model labelling or a second eval can use them). Needed for full FT because fp32 master weights + AdamW states
  (48 GB) leave no room for a colocated vLLM engine.
- **colocated layout** (LoRA): all 8 GPUs both generate (one vLLM engine each at ~45% memory, 32 rollouts per GPU) and train
  (DDP over 8); the engine sleeps during the update. Fits because the frozen bf16 base is 6 GB. GPU 7 doubles as the eval GPU
  between checkpoints only if the run is paused, so the follow-eval runs on the laptop-side schedule instead (see section 4).

Per step at 256 rollouts, 2,048-token cap, ~700-token mean (est., measured in the smoke test):

| phase | full FT, server layout | LoRA, colocated layout | basis |
|---|---|---|---|
| generation | 32-40 s | 22-28 s | tail-latency bound in both: the longest rollout (2,048 tokens) decodes at ~65-90 tok/s per sequence; 180k tokens of throughput takes ~20 s on the single server GPU (overlapping the tail) / 3 s on 8 |
| weight sync | ~2 s (6 GB NCCL push) | ~4-6 s (merge LoRA, push, unmerge, engine wake/sleep) | |
| reward (math-verify, process pool) | 2 s | 2 s | |
| training | ~8 s on 4 GPUs (5.5e15 FLOPs: forward+backward + old-logprob forward) | ~4 s on 8 GPUs (no weight grads for the frozen base) | ~350 TFLOP/s effective per GPU |
| **total** | **~45 s/step** | **~35 s/step** | |

So LoRA saves about 20% per step at this model size, not a multiple: generation dominates and is identical in both arms. The other
LoRA saving is the skipped Muon pilots (section 4).

**Cost of full on-policy synchrony.** The server layout is strictly synchronous: the 4 training GPUs idle while the 3 generation GPUs
work (~33 s of a 45 s step) and the 3 generation GPUs idle during the update (~12 s). Average utilization of the 7 working GPUs is
about 47%. A one-step-stale pipeline (PipelineRL / ScaleRL's off-policy-k) would overlap the two and bring the step to
max(generation, training) ~= 33 s, a saving of roughly 28% of wall-clock, at the price of importance-sampling against a one-step-old
policy; TRL 1.13 has no such mode (only `server` and `colocate`), so it is not on the table without switching frameworks or writing an
async loop. The colocated LoRA layout has no idle GPUs by construction; its cost is the engine sleep/wake and adapter merge (~5 s/step).

Stage budget at ~$24/h for the 8xH100 pod (RunPod on-demand rate as of 2026-09; verify on the console). Each pilot line includes ~5 min
start-up (engine + model load) and a 5-min step-end eval (MATH-500 avg@4 + GSM8K greedy on vLLM):

| item | wall-clock | cost (est.) |
|---|---|---|
| setup, baselines for base / touch-up / grpo-v2 (MATH-500 greedy + avg@8, AIME 24/25/26 avg@16, GSM8K), pass-rate labels for the seed (12k x 8) and base (12k x 4) | 1.0 h | $24 |
| smoke test (3 steps, both layouts) | 0.2 h | $5 |
| pilot 1a: LoRA + AdamW, 20 steps (~12 min of steps) | 0.4 h | $10 |
| pilot 1b: full FT + AdamW, 20 steps (~15 min of steps) | 0.45 h | $11 |
| **branch LoRA** (1b not significantly better): pilot 2 length penalty (0.4 h) + main run 200 steps (~2 h) + follow-eval / final AIME (0.4 h) | 2.8 h | $67 |
| **branch full FT**: pilots Muon + Muon-p (0.9 h) + length penalty (0.45 h) + main run 200 steps (~2.5 h) + evals (0.4 h) | 4.25 h | $102 |
| **total, LoRA branch** | **~4.9 h** | **~$117** |
| **total, full-FT branch** | **~6.3 h** | **~$152** |

Add ~15% for restarts and pod setup: **$135-175, 5.5-7.5 h** of pod time. The RLAIF stage was ~6 h of pod time plus $71 of judge.

Decision rule for pilot 1 (stated before running): "significantly stronger" = full FT beats LoRA on MATH-500 levels 3-5 avg@4 by more
than 3 points at step 20. The standard error of a 500-problem avg@4 at p ~ 0.5 is ~1.1 points and the two arms also differ in LR
convention (LoRA 2e-5 vs full 1e-6), so anything under 3 points is a tie and LoRA wins the tie on cost. Training-reward slope and
truncation rate are reported alongside but do not decide.

## 4. Experiment sequence

0. Baselines (no training): base, touch-up, grpo-v2 on MATH-500 (greedy and avg@8 with per-level pass rates), AIME 24/25/26 avg@16,
   GSM8K greedy. Output: `results/rlvr/baselines.md`. This is the "hard enough but learnable" evidence.
1. Pass-rate labels for the seed (8 rollouts) and base (4 rollouts) on MATH-12k; schedule built; expected zero-variance fraction
   printed for G = 16. Output: `rlvr/data/passrate_{grpo-v2,base}.jsonl`, `results/rlvr/difficulty_profile.md`.
2. Smoke test: 3 steps at 4 prompts x 4 generations in both layouts (server + full FT, colocated + LoRA), through checkpoint and export.
3. Pilot 1: LoRA + AdamW (colocated, lr 2e-5) vs full FT + AdamW (server, lr 1e-6), 20 steps each on the identical prompt order.
   Decision rule in section 3. Both arms log update RMS and gradient norm so the LR conventions can be sanity-checked.
4. Branch:
   - LoRA: pilot 2 = DAPO soft length penalty on, 20 steps; keep it only if truncations fall with no loss on MATH-500 L3-5.
     Main run = LoRA + AdamW, 200 steps.
   - Full FT: Muon and Muon-p pilots (20 steps, same nominal lr 1e-6 via RMS matching; AdamW arm = pilot 1b), then the length-penalty
     pilot with the winner, then the main run at 200 steps. Caveat stated up front: 20 steps is early-phase behaviour, and Muon under
     GRPO has a documented collapse mode (2605.19282: Qwen3-1.7B/4B to ~0 accuracy) attributed to whitening low-SNR gradients;
     Muon-p's partial whitening (sigma^(1/3)) is the interesting middle. A diverged pilot is reported as a result.
5. Main run, 200 steps, checkpoints every 25 steps. Follow-eval: in the server layout on GPU 7 as checkpoints appear; in the colocated
   layout the checkpoints are evaluated in one batch after the run (8 checkpoints x ~4 min on one GPU while the final AIME avg@16 runs
   on another). Then the final table and plots, model card and Hub upload (`tbooy/Qwen2.5-3B-Instruct-Sheldon-RLVR-math-v1`).

## 5. Code plan (`rlvr/`, new; `rlaif/` untouched)

```
rlvr/
  PLAN.md                     this file
  README.md                   file map + order of operations (written with the code)
  data/build_math.py          MATH-12k + MATH-500 + AIME 24/25/26 (+ GSM8K test already in data/) -> rlvr/data/*.jsonl with a common
                              schema {id, problem, answer, level, subject, source}; 10-gram + edit-similarity contamination report
  data/label_passrate.py      vLLM (offline engine, all visible GPUs): k rollouts per prompt, grade, write pass rate + mean length per
                              prompt; per-level summary table
  data/build_schedule.py      pass-rate buckets -> ordered prompt list for a run (drifting mixture, no repeats); prints expected
                              zero-variance fraction per phase for the chosen G
  grader.py                   last \boxed{} extraction (brace-balanced, reused from sft/eval_gsm8k.py), normalization, exact fast path,
                              math-verify equivalence with timeout; `python -m rlvr.grader --selftest` on ~60 gold/pred cases
  reward.py                   TRL reward fn: None for truncated, 1/0 otherwise, optional soft-overlong term; per-step metrics
                              (accuracy, truncation rate, boxed rate, mean length by correctness) via log_metric
  trainer.py                  RLVRTrainer(GRPOTrainer): (a) prompt-level loss aggregation via per-row weights, (b) zero-variance group
                              masking + recomputed denominators, (c) create_optimizer -> adamw | muon | muonp with the 2-D/1-D param
                              split, (d) WSD scheduler, (e) extra logging (frac_zero_var, frac_truncated, live prompts, update RMS)
  optim/muon.py               Muon (Newton-Schulz 5 steps, Moonlight coefficients, momentum 0.95, Nesterov, decoupled wd, RMS matching
                              0.2*sqrt(max(m,n))) and Muon-p (cubic recurrence G_{n+1} = G_n + c (G - G_n G_n^T G_n), c = 0.66, N = 6,
                              after spectral normalization, then rescaled to update RMS 0.2 so all three optimizers share the nominal LR).
                              Drop-in slot for your Dion fork if you supply it; note the public Muon-p code is princeton-pli/muon-p, the
                              Microsoft Dion repo has no fractional-power variant on any branch (checked 2026-09-24)
  train_rlvr.py               CLI: --model --schedule --prompts_per_step 32 --num_generations 16 --max_completion_length 2048
                              --loss cispo --eps_high 5 --optimizer {adamw,muon,muonp} --lr 1e-6 --wsd_decay_frac 0.2 --max_steps 300
                              --length_penalty {none,dapo} --vllm_server ... ; W&B project cs2881r-sheldon, run names rlvr-*
  eval_math.py                vLLM eval: MATH-500 (greedy + avg@k, per level/subject), AIME 24/25/26 avg@k, GSM8K greedy; JSONL + summary
  runpod/serve_vllm.sh        trl vllm-serve on GPUs 0-2 (dp 3), waits until healthy
  runpod/run_rlvr.sh          accelerate launch (DDP, 4 GPUs) train_rlvr.py, detached, log + pid as in rlaif/runpod/env.sh
  runpod/pilot.sh             the three optimizer pilots + length-penalty pilot in sequence, each followed by the step-30 eval
  runpod/follow_eval.sh       evaluates checkpoints as they appear on GPU 7 (MATH-500, GSM8K, persona short set)
  runpod/label.sh, runpod/baselines.sh, runpod/stage3.sh (sequencer)
  tests/                      CPU tests: grader cases; aggregation on toy tensors (prompt-level weights, zero-variance masking, truncation
                              exclusion reproduce hand-computed values); Muon-p recurrence converges to U S^(1/3) V^T on random matrices;
                              schedule builder counts. Run with the laptop .venv (CPU torch), no GPU needed
  summarize_run.py            per-checkpoint table + plots -> results/rlvr/<run>.md
results/rlvr/                 baselines.md, difficulty_profile.md, pilots.md, <run>.md
```

Dependencies added to `rlaif/runpod/requirements.txt` (renamed to a shared `requirements.txt` on the pod): `math-verify`, `accelerate`
(already), `vllm` (already). TRL stays pinned at 1.13.0: the trainer overrides copy two functions from that version and assert on it.

## 6. Risks and how the plan handles them

- LoRA-vs-full at 20 steps is a coarse test; the 3-point rule makes the tie explicit rather than pretending precision.
- Persona erosion under math-only reward: monitored per checkpoint on the 60 short persona prompts (rule penalty, mean words);
  not constrained. Expected and acceptable for this stage.
- Muon collapse (2605.19282): pilot catches it; AdamW is the fallback; a diverged pilot is reported, not hidden.
- Too many truncations / dead groups: the schedule builder predicts the dead fraction; the pilot measures it; the levers are the
  bucket mix and G, not the token cap (your rule), and the length penalty pilot.
- Verifier false negatives on MATH-style answers (intervals, sets, `\text{}` units): the grader self-test covers the gold answer forms in
  MATH-12k; the eval writes per-problem records so disagreements can be audited.
- vLLM/trainer numeric mismatch: fp32 head on the trainer, IS correction on, T = 1 / top-p = 1 / no repetition penalty; the logged
  `sampling/importance_sampling_ratio/mean` must sit near 1 (it was 0.03 in the RLAIF run).

## Sources

Qwen2.5 report https://arxiv.org/abs/2412.15115 · APMPO https://arxiv.org/abs/2605.04066 · MiCoTA https://arxiv.org/abs/2507.01887 ·
INTUITOR https://arxiv.org/abs/2505.19590 · RL vs distillation https://arxiv.org/abs/2505.14216 · lambda-GRPO https://arxiv.org/abs/2510.06870 ·
MathForge https://arxiv.org/abs/2601.20614 · VIGOR https://arxiv.org/abs/2607.22002 · 2502.20122 · 2504.14350 ·
MiniMax-M1 (CISPO) https://arxiv.org/abs/2506.13585 · ScaleRL https://arxiv.org/abs/2510.13786 · DAPO https://arxiv.org/abs/2503.14476 ·
Muon-p https://arxiv.org/abs/2606.13867 (code: princeton-pli/muon-p) · Moonlight https://arxiv.org/abs/2502.16982 · Dion https://github.com/microsoft/dion ·
Muon under RLVR: https://arxiv.org/abs/2605.19282, https://arxiv.org/abs/2607.16169 · Muon on LoRA: https://arxiv.org/abs/2605.10468, https://arxiv.org/abs/2507.12142 ·
MATH-12k https://huggingface.co/datasets/rasbt/math_full_minus_math500 · MATH-500 HuggingFaceH4/MATH-500 · AIME: Maxwell-Jia/AIME_2024, math-ai/aime25, MathArena/aime_2026 ·
DeepMath audit https://arxiv.org/abs/2504.11456 · math-verify https://github.com/huggingface/Math-Verify · TRL 1.13.0 grpo_trainer.py/grpo_config.py (installed copy read directly).
