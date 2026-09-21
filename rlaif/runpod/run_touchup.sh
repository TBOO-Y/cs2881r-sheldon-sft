#!/usr/bin/env bash
# Stage 2a ON the pod: 1-epoch LoRA touch-up of the v3b merged model on the v4 set (short rows + opener-flattened replay + math),
# lr 5e-5, saves 5x per epoch, merges at the end -> $PROJ/models/<RUN>-merged. One H100, ~15-20 min.
#   [GPU=0] [RUN=sft-touchup-v4] bash rlaif/runpod/run_touchup.sh
set -euo pipefail; source "$(dirname "$0")/env.sh"; cd "$PROJ"
RUN="${RUN:-sft-touchup-v4}"; GPU="${GPU:-0}"; BASE="${BASE:-$PROJ/models/sft-lora-r32-mixAB-v3b-merged}"
launch "$RUN" "$GPU" $PY sft/train_sft.py --model "$BASE" --train rlaif/data/v4/train.jsonl --val rlaif/data/v4/val.jsonl \
  --epochs 1.0 --lr 5e-5 --saves_per_epoch 5 --run_name "$RUN" --out_root "$PROJ/runs" --merged_root "$PROJ/models" ${EXTRA:-}
echo "follow: tail -f $PROJ/logs/$RUN.log   (merged model: $PROJ/models/$RUN-merged)"
