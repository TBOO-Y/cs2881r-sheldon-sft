# RLAIF stage (stage 2) — code map

Everything here follows `persona_audit.md` (the v3b audit) and the decisions taken on 2026-09-19: gated multi-term reward, small data patch + SFT touch-up before RL, seed from v3b, very small OpenAI judge, system prompts out of scope, 400-token eval cap unchanged.

| step | file | output |
|---|---|---|
| 1. data patch | `data/patch_data.py` | `data/persona_patched.jsonl` (8,930 of 11,910 persona rows; 545 canon drops, template/opener caps, sentence dedup), `data/math_rows.jsonl`, `data/patch_report.json` |
| 2. short rows | `data/gen_short_rows.py` (writer gpt-4.1, QA gpt-4.1-mini) | `data/short/{prompts,replies,filtered,qa}.jsonl`, `data/short/short_{train,val}.jsonl`, `data/short/short_heldout_prompts.jsonl` (60, never trained) |
| 3. touch-up set | `data/build_v4.py` | `data/v4/{train,val}.jsonl` (short + opener-flattened replay + math), `data/v4_full/` (full patched set for a from-scratch option) |
| 4. touch-up SFT | `launch_touchup.sh` → `sft/train_sft.py` from the v3b merged model | `/data/agastyas/cs2881r/models/<run>-merged` |
| 5. RL prompts | `data/build_rl_prompts.py` | `data/rl_prompts.jsonl` (5,714: reweighted persona, short, constraint, verdict, two-turn, AI-probe, sensitive) |
| 6. judge | `judge/oai.py` (stdlib client, cache, cost), `judge/prompts.py`, `judge/core.py` (`task_gate`, `persona_pair`), `judge/calibrate.py` | `judge/calibration_report.md` |
| 7. reward | `reward/rules.py` (17 deterministic terms + `BatchTax`), `reward/reward.py` (`GroupReward`: gate × persona win-rate + form − rules − flags − tax) | per-step metrics for W&B |
| 8. GRPO | `train_grpo.py` (TRL GRPOTrainer, LoRA r32, 8 generations, 400-token rollouts) | adapter + merged model |
| guide | `sheldon_style_guide_v2.md` | used by the generator, the judge and the rule checks |

Keys: the original OpenAI/Anthropic keys died on 2026-09-20 (short-row generation/QA moved to session subagents; the judge was going to be a locally served Qwen-32B). **Handover (2026-09-20, second owner):** the judge is now `openai/gpt-5.6-luna` through OpenRouter (`OPENROUTER_API_KEY` in `.env`; `judge/oai.py` picks the provider from `OAI_BASE_URL`, default OpenRouter, and uses the cost OpenRouter reports), reasoning effort `$JUDGE_REASONING` (default `low`; calibration in `judge/calibration_luna_v2.md`, v1 prompts in `calibration_openai_gpt_5_6_luna.md`), and compute is a RunPod 8xH100 node driven by `runpod/`. Cache dir `$OAI_CACHE_DIR`. `--judge_model mock` runs everything offline.

## RunPod launchers (`runpod/`, added 2026-09-20)
All read `runpod/env.sh` (`$PROJ`, default `/root/cs2881r` on the pod's local disk; `$PROJ/.env` for keys; W&B goes offline without a key; `mirror.sh` copies outputs to `$BACKUP=/workspace/cs2881r_backup` on the FUSE volume every 5 min). Detached jobs log to `$PROJ/logs/<name>.log` with a `.pid`. `follow_eval.sh` scores every GRPO checkpoint (GSM8K + persona gens) on a spare GPU; `../summarize_run.py` tabulates them.
- `sync.sh` (from WSL) pushes the working tree incl. the regenerated data; `setup_node.sh` (on the pod) makes the venv from `requirements.txt` (vLLM 0.29, TRL 1.13, transformers 5.12, peft 0.20 resolve together on torch 2.13), downloads the base and v3b merged models, checks data, judge and reward.
- `run_touchup.sh` (GPU 0, ~20 min) -> `$PROJ/models/sft-touchup-v4-merged`; `run_eval.sh` (`NAME= MODEL= [ADAPTER=] [TASKS=]`) -> `$PROJ/gens/<name>/{final,short_heldout}.jsonl`, `$PROJ/evals/gsm8k/<name>/final.jsonl(+.summary.json)`.
- `calibrate.sh` (anywhere with the key) -> `judge/calibration_<model>.md`; `smoke_grpo.sh` (2 steps, 4x4, vLLM colocated); `run_grpo.sh` (300 steps, budget guard); `stage2.sh` runs the whole sequence and stops on a failed smoke test; `fetch_results.sh` (from WSL) pulls results and runs `audit/quant/compare.py` against v3b and the gold references in `sft/data_v3b/heldout_prompts.jsonl`.
- Baselines to (re)run on the pod at the 400-token cap before comparing anything: `NAME=v3b MODEL=$PROJ/models/sft-lora-r32-mixAB-v3b-merged` and `NAME=base MODEL=Qwen/Qwen2.5-3B-Instruct` (the sequencer does both).

## Athena cluster launchers (original, superseded)
- `eval_model.sh` — ON the cluster: `NAME=<run> MODEL=<merged dir> [ADAPTER=..] [TASKS="persona short gsm8k"]`; detached on a policy-free GPU; writes `$PROJ/gens/<run>/{final,short_heldout}.jsonl` (400-token greedy; final includes the 40 OOD prompts) and `$PROJ/evals/gsm8k/<run>/final.jsonl(+.summary.json)`.
- `serve_judge.sh` / `calibrate_on_cluster.sh` — vLLM-served Qwen2.5-32B-Instruct as `judge` on 127.0.0.1:8001; calibration vs the Sonnet verdicts → `$PROJ/calib/calibration_qwen32b.md`.
- `orchestrate_stage2.sh` — detached sequencer: touch-up launch → judge → calibration → eval of the merged touch-up (log `$PROJ/logs/orchestrate-stage2.log`).
- `wait_and_launch_touchup.sh` — polls for a free GPU and launches `sft-touchup-v4` once (log `logs/waiter-touchup-v4.log`).
- `smoke_grpo.sh` — FROM the Mac: 2-step GRPO smoke test against the local judge (`MODEL=... bash rlaif/smoke_grpo.sh`).
- `fetch_results.sh` — FROM the Mac: `bash rlaif/fetch_results.sh <run> ...` pulls gens + GSM8K back and runs `audit/quant/compare.py` vs v3b and gold.
