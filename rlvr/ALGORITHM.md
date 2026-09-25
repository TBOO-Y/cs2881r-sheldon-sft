# Stage 3 (RLVR) — current algorithm, bare bones

Status 2026-09-25: code complete and dry-run tested; no pod run yet. Full rationale in `PLAN.md`, file map in `README.md`.

**Setting.** Policy π_θ = Qwen2.5-3B-Instruct → Sheldon SFT → RLAIF (`grpo-v2-merged`). Task: competition math with a verifiable
reward. Train set: MATH-12k (MATH train + MATH test minus MATH-500; 11,809 problems after near-duplicate removal vs MATH-500 /
AIME 24-26), human levels 1-5. Eval: MATH-500 by level (headline: levels 3-5), AIME 2024/25/26 avg@16, GSM8K.

**Rollouts.** Per step: P = 16 prompts × G = 16 samples (batch 256), T = 1.0, top-p = 1.0, no repetition penalty, cap 2,048 tokens,
one optimizer update per batch (on-policy; vLLM sampler, token-level truncated importance-sampling correction for sampler/trainer drift).
Prompt = system + problem + "reason step by step, final answer in \boxed{}".

**Reward.** r_i = 1[last \boxed{} of sample i ≡ gold] ∈ {0,1} (exact-match fast path, else symbolic equivalence via math-verify).
Truncated samples (no EOS) get no reward and are removed from everything below. Optional DAPO soft overlong penalty
r_len = clip(((L_max − L_cache) − L)/L_cache, −1, 0), L_cache = 512, off until its pilot.

**Advantage (group mean, group std — deliberate, not ScaleRL's batch std).** For prompt g with scorable samples S_g:
Â_i = (r_i − mean_{S_g} r) / (std_{S_g} r + 1e-4). Groups with zero variance (all-equal rewards, or nothing scorable) are dead:
no gradient, and excluded from every denominator.

**Loss: CISPO (MiniMax-M1) with prompt-level aggregation (DAPO paper / ScaleRL "prompt average").**
ρ_{i,t} = π_θ(y_{i,t}|·)/π_old(y_{i,t}|·) (token-level);  no KL term, no entropy bonus.
  L(θ) = −(1/|P_live|) Σ_{g live} (1/T_g) Σ_{i∈g} Σ_t sg(min(ρ_{i,t}, ε_max)) · Â_i · log π_θ(y_{i,t}|·),   ε_max = 5,
with T_g = number of live tokens in group g (truncated samples contribute none). No lower clip (ε_low unbounded).
Implementation: TRL 1.13 `loss_type="cispo"` computes Σ_i Σ_t (·)/N with N = live tokens in the batch; the per-prompt form is obtained
exactly by scaling each sample's advantage by w_i = N/(T_g(i)·|P_live|) (the policy term is linear in Â).

**Precision.** Trainer LM head computed in fp32 outside autocast (fp32 logits, exact logsumexp) in both arms; full FT keeps fp32
master weights with bf16 autocast elsewhere; LoRA keeps a bf16 frozen base with fp32 adapters. Sampler: bf16 vLLM (fp32 available as
a server option if the measured trainer/sampler logprob gap warrants it).

**Optimization.** Peak LR: full FT 1e-6 (AdamW β = (0.9, 0.95), ε = 1e-15, wd 0.01) or LoRA r = 32, α = 64 on all linear projections
at 2e-5. Schedule WSD: 10 warm-up steps, constant, linear decay over the last 20% (40 of 200) to 0.1× peak; pilots run the first 20 steps
of that same 200-step layout. Grad clip 1.0. Optimizer candidates (full-FT arm only): AdamW; Muon (Newton-Schulz-5 orthogonalized
Nesterov momentum, update scaled 0.2·√max(m,n) to AdamW's RMS); Muon^p with p = 1/3 (U S^{1/3} Vᵀ via Y ← Y + 0.66(X − Y Yᵀ Y), 6 iterations,
after spectral normalization; update rescaled to RMS 0.2). Embeddings/head/norms/biases always AdamW.

**Difficulty schedule (static).** Each training prompt is labelled with the seed's pass rate p̂ from 8 rollouts. Buckets: easy
0.5 < p̂ < 1, medium 0.125 ≤ p̂ ≤ 0.5, hard p̂ < 0.125; p̂ = 1 dropped. Sampling mixture drifts linearly over the run from
(0.5, 0.4, 0.1) to (0.2, 0.5, 0.3), no prompt repeated; expected dead-group fraction Σ p̂^G + (1−p̂)^G is printed before the run.
No dynamic sampling or resampling.

**Run plan.** 200 steps (3,200 prompt visits, 51k rollouts). Pilots at 20 steps: (1) LoRA+AdamW vs full-FT+AdamW, full FT wins only if
> 3 points on MATH-500 L3-5 avg@4; (2) if full FT: Muon and Muon^p vs AdamW; (3) length penalty on/off with the winner. Then the main run
with checkpoints every 25 steps evaluated on MATH-500 avg@4 and GSM8K; final AIME avg@16.

**Monitored per step.** accuracy, truncation rate, zero-variance-group fraction, live prompts/tokens, sampler-vs-trainer |Δlog p|,
CISPO clip fraction, grad norm, update RMS (Muon family), relative parameter drift ‖θ−θ₀‖/‖θ₀‖.
