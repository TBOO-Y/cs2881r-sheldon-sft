# Decision log: stages 3-4 (RLVR math, staged re-labelling, full fine-tune, combined reward), 2026-09-24 to 2026-09-27

"You" = the user, "me" = the assistant. Numbers are from our own harness (`results/rlvr/*.md`).

## Stage 3 planning (2026-09-24)

1. **Task = MATH-500, levels 3-5 as the headline, AIME 24/25/26 avg@16 secondary** (me, from a literature survey). Qwen2.5-3B-Instruct sits at
   62-66 on MATH-500 and 0-3 on AIME pass@1; RLVR at 3B reaches 63-68 and 2-3 AIME problems of 30. AIME was rejected as primary because one
   problem is 3.3 points and its training sets put a 3B model in the all-wrong regime. You called the 62->68 headroom "shockingly small" but
   chose to run the pilots before changing task; the baselines then showed our seed at 34.0, i.e. 34 points of headroom.
2. **Training set = MATH-12k** (`rasbt/math_full_minus_math500`, human levels) with our own **pass-rate labels from 8 seed rollouts** for the
   schedule (me). Rejected: DeepScaleR / DAPO-17k / DeepMath as the *sole* pool (olympiad-level, near-duplicates of MATH-500, or pass rates
   from reasoning models that say "everything is hard"). 189 near-duplicates of MATH-500 dropped by a 10-gram / edit-similarity filter.
3. **Recipe you specified**: CISPO loss; "token-level, DAPO-style" aggregation, which you clarified means the DAPO-paper formula (token mean
   within each prompt's group, then mean over prompts = ScaleRL's "prompt average"); **group-level std for advantages, deliberately against
   ScaleRL's batch-level std** (it up-weights extreme groups in binary-reward settings); WSD schedule; truncated and zero-variance groups
   masked from loss *and* denominators; no dynamic sampling; DAPO length penalty only after a no-penalty pilot; optimizer chosen by a
   10%-of-steps pilot (AdamW / Muon / Muon-p, p = 1/3).
4. **Blanks I filled**: fp32 master weights + bf16 autocast (a 1e-6 update vanishes in pure bf16); fp32 LM head; CISPO eps_max = 5 (TRL's
   default 0.2 would silently cap ratios at 0.2); G = 16 (binary rewards need more samples per prompt than the RLAIF run's 8); no KL term
   (CISPO / ScaleRL / DAPO all drop it; persona drift monitored instead); T = 1, top-p = 1, **no repetition penalty** (the RLAIF run's 1.05
   put the sampler and trainer out of agreement, logged IS ratio 0.03); 2,048-token cap; per-rank whole prompt groups.
5. **Review 1 (you)**: seed = `grpo-v2-merged` (pipeline order); **global batch at most 256** (16 x 16); **200 steps**; **pilot 1 = LoRA+AdamW
   vs full-FT+AdamW at 20 steps**, LoRA wins ties (cost). I set the tie rule at **> 3 points on L3-5 avg@4** (standard error ~1.1 and the arms
   use different LR conventions); Muon pilots only if full FT wins. You accepted the **bf16 vLLM sampler** after I explained the head
   precision question; I then made the **fp32 head apply to the LoRA arm too** (TRL's own flag crashes on PEFT models and is undone by
   autocast anyway, so it is our own patch).
6. **Pre-run adversarial review** (me, 110 agents): 9 confirmed findings fixed before any pod time, notably the PEFT crash, the autocast
   no-op, data-parallel vLLM serving being unsupported for dense models (single-GPU server instead), a vLLM stop that matched nothing,
   Muon-p's rank-dependent power iteration, and `--penalize_truncated` removed as inconsistent with masking.
7. **Topology**: 3x H200 instead of 8x H100 (availability); GPU 0 serves vLLM (full-FT arm) or evaluates (LoRA arm), GPUs 1-2 are the two
   training ranks in both arms so the 256 batch is identical across arms (me). **Pilots only, no main run without your go-ahead** (you).
8. **Environment fixes** on the pods (me): CUDA-12.9 torch/vLLM builds on a 12.8 driver, `ninja` for vLLM's kernel warm-up, later
   `NCCL_NVLS_ENABLE=0` (found by the on-pod session) for the trainer-to-vLLM weight sync; all scripted into `setup_stage3.sh`.
9. **Monitoring rule** (you, after ~2.5 h lost to silent grep-based waiters): wait on process liveness, check every 10-15 min, one remote
   sequencer with stage markers. Adopted for every later run and stored as a standing rule.

## Stage 3 pilots and main run (2026-09-25/26)

10. **Baselines**: seed grpo-v2 34.0 greedy / 21.0 L3-5 vs base 68.0 / 59.0; touch-up equally low, so the SFT stage caused the loss.
11. **Pilot 1 outcome -> LoRA** (rule): LoRA+AdamW 25.7 vs full-FT+AdamW 22.8 on L3-5; Muon pilots skipped (rule). **Length penalty kept**
    (rule: truncations 3.6 -> 3.0 %, L3-5 flat), with the caveat that both differences were inside noise.
12. **Main run approved by you** through the on-pod Claude session (recommended config: LoRA r32 + AdamW 2e-5 + length penalty, 200 steps).
    Result 65.0 greedy / 63.5 avg@4 / 55.2 L3-5 / GSM8K 81.9; plateau from step ~125 when ~half the groups were zero-variance.
13. **Persona eval of the RLVR model** (you asked; I built it on the stage-2 tooling): judge 0.545 vs seed, persona intact, replies longer.

## Stage 3b: staged re-labelling (2026-09-26)

14. **Your direction**: better difficulty scheduling starting near step 125, solve the zero-variance problem, synthetic data if necessary.
    My diagnosis from the logs: dead groups were all-correct (2 % -> 40 %), i.e. stale labels, not hard data.
15. **Your changes at review**: start from **checkpoint-200** (not 125), the dataset is too small so **pool expansion and source weighting
    first**, then the staged run.
16. **My design**: stages of 50 steps with **re-labelling by the current model** at each boundary (the one deviation from "no dynamic
    scheduling", ~10 % overhead); sampling weight p(1-p) inside [1/8, 7/8]; a 10 % frontier slice from never-solved prompts; **source caps**
    DeepMath 30 % / DAPO 20 % / DeepScaleR 20 %, MATH-12k uncapped (kept >= 30 %); verified external pools before any synthetic data
    (synthetic only as a fallback, never triggered); incremental re-labelling (non-solved prompts + 3k frontier) after stage 1.
17. **Outcome and my stop**: stages 1-2 flat (55.0 / 55.3 vs 55.2) although dead groups fell 47 % -> 6-9 %; pass rates on the trained
    prompts themselves did not move (0.447 -> 0.449). I stopped before stage 3 (as I had said I would) because it would repeat the same
    configuration; the sequencer's own stop rule never fired since the band stayed large.

## Stage 3c: full fine-tune (2026-09-27)

18. **Your decision**: one more optimisation attempt on this seed, **full fine-tune at 2e-6**. My choices: 100 steps, WSD with decay over the
    last 20, band schedule from the stage-1 labels (made by this seed), server layout.
19. **Result**: 65.4 greedy / 65.1 avg@4 / 56.9 L3-5 / L4 60.9 / GSM8K 83.0, monotone over checkpoints; full FT moved where LoRA did not.
    Persona eval: judge 0.495, substance intact, verbosity up (44 % hit the 400-token cap). Uploaded as RLVR-math-v2-fullft at your request.

## Stage 4: combined reward (2026-09-27)

20. **Your decision**: run the combined-reward stage autonomously after preserving everything (Hub uploads, laptop copies, volume archive).
21. **My design**: seed = the full-FT model; full FT 2e-6, 80 steps; each step 8 math prompts (verifier + length penalty, band schedule)
    + 8 persona prompts (stage-2 judged reward: gate x (2 x pairwise win rate + form) - rules - false claim - batch tax; Luna, ring 1, both
    orders); **2,048-token cap for both tasks** so the rules' length terms, not the cap, discipline verbosity; group-std normalisation keeps
    the two reward scales apart; per-rank judge budget $20, 4-hour cap, clean stop if the judge fails.
22. **Two launch failures, both DDP collective mismatches, fixed by me**: (a) the per-step *fork* grading pool deadlocked once the judge's
    thread pool existed in the rank -> persistent forkserver pool; (b) rank 0 held all math groups and rank 1 all persona groups, so they
    logged different metric keys and TRL's per-key gathers deadlocked -> fixed key sets on every rank + per-rank task interleaving;
    validated on a 3-step mock-judge smoke before relaunch.
23. **Result**: math unchanged (65.2 / 64.8 / 56.9 / GSM8K 83.0); persona defects gone (rule penalty 0.15, template openers 4 %, no announced
    jokes, truncation 1 %, leakage into math 0.4 %) but substance thinned (cast names 8 %, 90 words, no Bazinga); judge 0.485 (tie). My
    diagnosis: reward hacking of the rule penalties; the only positive persona term is sibling-relative. Training monitors suggest
    checkpoint-20 kept the persona (233 words, names 45 %) with most defects already removed; not evaluated held-out.
24. **Your decisions to close**: upload Combined-v1 (done, with an honest card), preserve everything, terminate the pod, **no stage 4b**,
    and hold off on evaluating checkpoint-20 for now.

## Standing facts for anyone continuing

- Best persona+math model: RLVR-math-v2-fullft; cleanest but least Sheldon: Combined-v1; strongest judge score: RLVR-math-v1.
- Every run's recipe, tables and diagnosis: `results/rlvr/NOTES.md`; one-page algorithm: `rlvr/ALGORITHM.md`; plans: `rlvr/PLAN*.md`.
- A stage 4b would need a non-sibling-relative positive persona term (absolute-rubric voice, gold-relative length floor, capped rule weight).
