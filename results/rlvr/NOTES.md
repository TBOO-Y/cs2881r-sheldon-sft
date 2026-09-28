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

# Stage 4: combined reward (verifiable math + stage-2 judged persona), 2026-09-27

Setup: `rlvr/runpod/stage4.sh`, run `rlvr-4-combined`; seed = the full-FT RLVR model (rlvr-3c-fullft); full fine-tune AdamW 2e-6, WSD
(warm-up 5, decay over the last 16 of 80 steps); each step = 8 math prompts (band sampling from the stage-3 labels, verifier + DAPO length
penalty) + 8 persona prompts (stage-2 RL prompt set, reward = gate x (2 x pairwise judge win rate + form) - 17 rules - false-claim - batch
tax, GPT-5.6 Luna ring 1 both orders), 16 completions each, 2,048-token cap for both tasks, group-std advantages (so the two reward scales
never mix), truncations and zero-variance groups masked, CISPO. 80 steps x 80 s on 3x H200 (1 h 48 min); judge $24.7 total, 0 errors.
Two launch failures fixed first (both were DDP collective mismatches): a per-step fork grading pool deadlocked once the judge thread pool
existed in the rank (now a persistent forkserver pool), and the ranks logged different metric keys because rank 0 held all the math groups
and rank 1 all the persona groups (now fixed key sets on every rank + per-rank task interleaving). Tables: `rlvr-4-combined.md`,
`persona_rlvr-4-combined.md`, `judge_h2h_rlvr-4-combined.json`.

Training trajectory (20-step means): persona reward -0.60 -> 0.22 -> 0.53 -> 0.71; persona reply words 264 -> 168 -> 105 -> 85; rule penalty
0.90 -> 0.13; math accuracy on the (hard-band) training prompts 0.47 -> 0.40; dead groups 7-9%.

**Math held.** MATH-500 greedy 65.2 / avg@4 64.8 / L3-5 56.9 / L4 60.4 / L5 34.1, GSM8K 83.0, AIME pass@16 17.8 - the full-FT seed's
numbers within noise (65.4 / 65.1 / 56.9 / 60.9 / 35.3 / 83.0 / 16.7), with shorter math answers (521 vs 633 tokens).

**Persona: defects gone, substance thinned.** On the 502 held-out prompts vs the grpo-v2 seed (gold in brackets): rule penalty 0.15 vs
0.87 [0.65]; template openers 4% vs 64% [35%]; announced jokes 0% vs 30% [3%]; hit the 400-token cap 1.0% vs 17.5% [0]; mid-sentence endings
1% vs 16%; opener entropy 8.5 bits vs 5.9 [7.5]; canon errors 0.4% vs 2.2%; persona leakage into MATH-500 answers 0.4% vs 2.8% [base 0.2%].
But: cast names in 7.6% of replies vs 38.8% [70%]; Bazinga 0% vs 1.2% [11%]; mean 90 words vs 213 [262]; short prompts 26 words vs 69.
Judge (200 prompts, both orders): 0.485 [0.42, 0.55] vs grpo-v2, i.e. a tie, with a telling item split: template +0.86, answer-first +0.73,
humour/canon +0.73, register +0.58, but voice -0.34.

**Reading.** The policy found the cheapest path through the persona reward: the 17 rule terms and the batch tax are almost all penalties on
things a short, plain, correct reply cannot trigger (openers, catchphrases, names used idly, loops, length, truncation), while the only
positive term, the pairwise judge win rate, is relative to sibling completions and therefore cannot push the whole group toward more Sheldon.
The result is a clean, terse, mostly-generic assistant that the judge cannot separate from the seed. This is the stage-2 reward's known
shape (persona_audit.md), now exposed by a full-parameter policy with 80 steps of headroom; in stage 2 the LoRA at 1e-5 barely moved.

**If a stage 4b is run**, the reward needs a positive persona term that is not sibling-relative: e.g. the judge's `voice` item scored
against an absolute rubric (or against the gold reference reply for that prompt), a floor on reply length relative to the gold, and a
cap on the rule penalties' total weight. Not started.

Artifacts: merged model uploaded as `tbooy/Qwen2.5-3B-Instruct-Sheldon-Combined-v1`, `runs/rlvr-4-combined/trainer_state.json`,
`evals/rlvr/rlvr-4-combined/`, `gens/rlvr-4-combined/` (local).

## Stage 4 addendum: anatomy of the reward hacking (per-term trajectory from the training log, 20-step means)

| term | 1-20 | 21-40 | 41-60 | 61-80 | note |
|---|---|---|---|---|---|
| persona reward R | -0.60 | 0.22 | 0.53 | 0.71 | R = G (2P + F) - rules - flags - tax |
| pairwise win rate P | 0.48 | 0.49 | 0.50 | 0.50 | sibling-relative: group mean is 0.5 by construction, never moves |
| gate G | 0.56 | 0.60 | 0.60 | 0.63 | short direct answers pass the task gate more often |
| form bonus F | 0.26 | 0.40 | 0.47 | 0.48 | |
| rule penalty (17 terms) | 0.90 | 0.38 | 0.19 | 0.13 | the whole reward gain |
| batch tax (stock phrases) | 0.23 | 0.12 | 0.06 | 0.04 | penalises the persona's own signature phrases when repeated across the batch |
| term/length | 0.32 | 0.10 | 0.03 | 0.02 | |
| mean words | 264 | 168 | 105 | 85 | gold 262 |
| any cast name | 0.51 | 0.36 | 0.22 | 0.17 | gold 0.70 |
| Bazinga | 0.09 | 0.02 | 0.01 | 0.01 | gold 0.11 |

Mechanism. With group-normalised advantages only within-group differences of R matter. P is zero-sum within a group (its mean is 0.5
whatever the group looks like), and its sign is noisy (position bias, 56% order consistency), so it can only re-order siblings and cannot
say "this whole group has lost the persona". The rule penalties and the batch tax, by contrast, differ between siblings in a way that is
*consistent* across steps: the sibling that is shorter, names nobody, uses no opener and no catchphrase always has the smaller penalty.
A consistent within-group signal beats a noisy zero-sum one, so the policy descended the rule landscape (0.90 -> 0.13 in 60 steps) and
settled in the penalty-free basin, where P and F have nothing left to separate and the persona neither recovers nor degrades further.
The rules were written against the stage-2 failure audit and are almost all negative space (idle names, repeated catchphrases, template
openers, length, preamble, loops); the batch tax even penalises the persona's own stock phrases. The judge rubric is mostly negative space
too (template, answer-first, corrections, rule-binds), with `voice` the only item about substance, which is exactly the item the final model
lost (-0.34) while winning every defect item. Stage 2 did not show this because the LoRA at 1e-5 barely moved the policy (rule penalty
1.00 -> 0.87 in 109 steps); a full-parameter policy at 2e-6 that had already been through RL found the basin in ~60 steps. The math half was
untouched by any of this (its reward is absolute); its answers merely got ~15% shorter.

What a 4b would need (not run): an absolute persona anchor per completion (judge against the gold reply for that prompt, or an absolute
0-10 voice rubric), or a KL / reference-logprob anchor to the seed on persona rows only; a floor on reply length relative to the prompt kind;
the rule penalties capped (e.g. total <= 0.5) or reduced to a gate on egregious defects; and no batch tax on canonical catchphrases.
