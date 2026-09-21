#!/usr/bin/env bash
# Stage 2b ON the pod: the GRPO run. One H100 (policy + colocated vLLM); the judge (OpenRouter) is the wall-clock bottleneck.
#   MODEL=$PROJ/models/sft-touchup-v4-merged [GPU=2] [RUN=grpo-v1] [STEPS=300] [HOURS=4] [BUDGET=100] [WORKERS=96] [RING=1] [ORDERS=2] bash rlaif/runpod/run_grpo.sh
# Per step: 16 prompts x 8 completions -> 128 gate calls + 128*RING*ORDERS pairwise calls (256 at ring 1 / both orders). Measured 2026-09-20:
# $0.75 per 1k calls, 4.9 s median latency -> ~$0.29/step at ring 1 ($87 for 300 steps), ~$0.46 at ring 2. BUDGET aborts above the cap, HOURS stops cleanly on time.
set -euo pipefail; source "$(dirname "$0")/env.sh"; cd "$PROJ"
MODEL="${MODEL:?}"; GPU="${GPU:-2}"; RUN="${RUN:-grpo-v1}"; STEPS="${STEPS:-300}"; BUDGET="${BUDGET:-100}"; HOURS="${HOURS:-0}"
launch "$RUN" "$GPU" $PY rlaif/train_grpo.py --model "$MODEL" --run_name "$RUN" --judge_model "$JUDGE_MODEL" --judge_reasoning "$JUDGE_REASONING" \
  --judge_workers "${WORKERS:-96}" --ring "${RING:-1}" --pair_orders "${ORDERS:-2}" --budget_usd "$BUDGET" --max_steps "$STEPS" --time_budget_h "$HOURS" \
  --prompts_per_step "${PROMPTS:-16}" --num_generations "${GENS:-8}" --max_completion_length "${MAXLEN:-400}" --use_vllm --vllm_gpu_mem "${VLLM_MEM:-0.35}" ${EXTRA:-}
echo "follow: tail -f $PROJ/logs/$RUN.log ; W&B project $WANDB_PROJECT run $RUN ; checkpoints $PROJ/runs/$RUN ; merged $PROJ/models/$RUN-merged"
