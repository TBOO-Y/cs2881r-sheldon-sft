# Stage 2 (RLAIF) results: GRPO on the Sheldon touch-up model, 2026-09-20/21

Setup: seed = `sft-touchup-v4-merged` (v3b + 1 epoch on the v4 patch set); TRL 1.13 GRPOTrainer, LoRA r32/α64, 16 prompts × 8
completions per step, 400-token rollouts (T 0.8, top-p 0.95, rep. penalty 1.05), DAPO loss, KL β 0.04, vLLM colocated on one H100.
Reward `R = G·(2·P + F) − rules − 0.5·false_claim − batch_tax` with the judge `openai/gpt-5.6-luna` (OpenRouter, reasoning effort low),
ring 1 × both presentation orders (4 persona verdicts per completion), gate: refused → 0, worse-off → ×0.25, contradiction → ×0.5.
Judge calibration: `rlaif/judge/calibration_luna_v2.md`. Pod: RunPod 8×H100; wall-clock cap 4 h from the first launch.

| run | lr | steps | judge cost | outcome |
|---|---|---|---|---|
| grpo-v1-lr1e-6 | 1e-6 | 90 (stopped) | $31 | adapter moved ~0.05% relative weight; reward and every monitor flat (slope +0.09/100 steps, corr 0.09) |
| grpo-v2 | 1e-5 | 109 (4 h cap) | $37 | adapter 10× larger; monitors move modestly; GSM8K unchanged |

## GSM8K (test, 1,319 problems, greedy, 1,024 tokens)

| model | strict acc | boxed |
|---|---|---|
| Qwen2.5-3B-Instruct (base) | 85.7 | 99.8 |
| v3b (SFT) | 63.7 | 99.9 |
| sft-touchup-v4 (RL seed) | 63.9 | 99.8 |
| grpo-v2 step 25 / 50 / 75 / 100 / 109 | 64.7 / 64.8 / 63.9 / 64.9 / 64.1 | 99.8–99.9 |
| **grpo-v2 final (merged, step 109)** | **64.0** | 99.9 |

No checkpoint left the ±1.5-point noise band around the seed. The RL prompt mix contains no GSM8K-style problems; the protection
came from the 17% math replay in the touch-up, the KL anchor and per-checkpoint monitoring (`rlaif/runpod/follow_eval.sh`).

## Persona monitors (502 held-out prompts, greedy, 400 tokens; `rlaif/audit/quant/compare.py`)

| metric | v3b | touch-up | grpo-v2 final | gold |
|---|---|---|---|---|
| rule penalty (17 terms, mean) | 1.131 | 1.003 | **0.870** | 0.653 |
| repetition-loop term | 0.167 | 0.191 | **0.131** | 0.006 |
| preamble term | 0.324 | 0.281 | **0.263** | 0.244 |
| tool-voice term | 0.070 | 0.078 | **0.056** | 0.081 |
| canon-error term | 0.112 | 0.030 | **0.022** | 0.054 |
| hit 400-token cap | 21.7% | 18.9% | **17.5%** | 0% |
| ends mid-sentence | 19.7% | 18.3% | **15.9%** | 0% |
| template opener share | 96.6% | 65.7% | 63.7% | 34.5% |
| relent block | 13.1% | 4.8% | **3.4%** | 5.0% |
| Tuesday/Thai | 9.4% | 2.0% | 1.6% | 1.2% |
| opener entropy (bits) | 4.27 | 5.98 | 5.89 | 7.50 |
| announced / explained joke | 18.5% | 27.9% | 30.3% | 3.0% |
| Bazinga | 1.8% | 1.2% | 1.2% | 11.2% |
| any cast name | 57% | 40% | 39% | 70% |
| mean words | 235 | 216 | 213 | 262 |

Short held-out prompts (60, never trained): mean words 142 (v3b) → 78 (touch-up) → 70 (grpo-v2); rule penalty 1.28 → 0.46 → 0.36.

What changed, concretely (touch-up vs step 75/109 on the same prompts): 367 of 502 replies share the first 60 characters, 9 are identical.
The policy kept its openers and changed the continuation: repetition loops disappear (three replies went from penalty ≈5 to ≈0),
replies end before the cap more often, short prompts get proportionate answers ("Are you a robot?" → one sentence). What did not
change in 109 steps: the announced-joke opener ("I am about to make a joke", 28–30%), the near-absence of Bazinga, and cast breadth
(names drifted slightly down; the idle-name penalty and the batch-tax name term pull in that direction).

## Reward trace (grpo-v2, 10-step means)

| steps | 1-10 | 11-20 | 21-30 | 31-40 | 41-50 | 51-60 | 61-70 | 71-80 | 81-90 | 91-100 | 101-109 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| reward | -0.65 | -0.52 | -0.45 | -0.51 | -0.56 | see W&B run `grpo-v2` (project `cs2881r-sheldon`) for the full trace | | | | | |

Per-step reward std ≈ 0.2 (across steps) vs within-batch std ≈ 1.2; slope +0.23 per 100 steps at step 50. The logged `kl` sits at a
~0.0015 floor from bf16 noise between the policy and reference forward passes and is not informative at this scale; adapter B-norms are
(`||B||_F` 0.020 → 0.047 over steps 25 → 75 at lr 1e-6; 0.201 at step 25 at lr 1e-5).

## Findings for the write-up

1. **Learning rate.** 1e-6 (the inherited default) produced no measurable change in 90 steps; 1e-5 produced measurable but modest
   change in 109 steps. For a ~100–300-step LoRA GRPO budget with a noisy judge reward, 3e-5 to 5e-5 is the range to use next
   (the touch-up SFT visibly reshaped openers in 73 steps at 5e-5).
2. **Judge.** GPT-5.6 Luna is usable after two prompt fixes (a positive `voice` item; a harm-only `worse_off` definition): v3b beats base
   0.98 with no position bias, gold beats v3b 0.70, gate false-positive rate on gold 3/40. Close pairs (RL siblings) still show
   first-shown bias of 0.65–0.72 and 55–70% order consistency, so both orders are always judged; single-order judging is not safe.
3. **Cost / time.** $0.33 per step at ring 1 (384 calls, 4.9 s median latency, 96 concurrent); 65–75 s per step end to end, of which
   50–60 s is the judge. Total OpenRouter spend for calibration, smoke test and both runs: ≈ $71.
4. **GSM8K** was preserved at every checkpoint without any math in the RL mix; the KL anchor and the small total movement explain it.
   A math anchor slice with a verifiable reward (offered, not run) becomes necessary if the learning rate is raised as recommended.

Artifacts: `runs/grpo-v2/{checkpoint-*,final_adapter}` (adapters + trainer states), `gens/grpo-v2/*.jsonl`, `evals/gsm8k/grpo-v2/*`,
`gens/{v3b,sft-touchup-v4,base}` baselines at the same caps, `runs/grpo-v1-lr1e-6` (the 1e-6 run), pod logs in `logs_pod/`.
Merged final model: `models/grpo-v2-merged` (local) and `/workspace/cs2881r_backup/models/` on the RunPod volume.
