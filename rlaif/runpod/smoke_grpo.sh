#!/usr/bin/env bash
# GRPO smoke test ON the pod: 2 optimizer steps, 4 prompts x 4 generations, vLLM colocated, real judge (or JUDGE=mock for free).
#   MODEL=$PROJ/models/sft-touchup-v4-merged [GPU=2] [JUDGE=openai/gpt-5.6-luna] bash rlaif/runpod/smoke_grpo.sh
set -euo pipefail; source "$(dirname "$0")/env.sh"; cd "$PROJ"
MODEL="${MODEL:?}"; GPU="${GPU:-2}"; RUN="${RUN:-grpo-smoke}"; JUDGE="${JUDGE:-$JUDGE_MODEL}"
launch "$RUN" "$GPU" $PY rlaif/train_grpo.py --model "$MODEL" --run_name "$RUN" --judge_model "$JUDGE" --limit 32 --max_steps 2 --save_steps 1 \
  --num_generations 4 --prompts_per_step 4 --per_device_bs 8 --use_vllm --no_merge --report_to "${REPORT_TO:-none}" ${EXTRA:-}
echo "follow: tail -f $PROJ/logs/$RUN.log   expect: 'prompts: 32', two '[reward] call' lines with judge_calls=40, a saved checkpoint-2, 'judge usage:' with cost > 0"
