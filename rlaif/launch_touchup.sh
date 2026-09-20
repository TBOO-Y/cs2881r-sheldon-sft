#!/usr/bin/env bash
# Stage 2a: sync the patched data to Athena and launch the SFT touch-up from the v3b merged model (detached, W&B-synced).
# Usage (VPN on):  bash rlaif/launch_touchup.sh [RUN_NAME]      (default run name sft-touchup-v4)
set -euo pipefail
HOST=agastyas@athena01.ig32s.ruhr-uni-bochum.de; PROJ=/data/agastyas/cs2881r; RUN=${1:-sft-touchup-v4}
cd "$(dirname "$0")/.."
ssh $HOST "mkdir -p $PROJ/data/v4 $PROJ/data/v4_full $PROJ/data/short $PROJ/rlaif"
rsync -az rlaif/data/v4/train.jsonl rlaif/data/v4/val.jsonl $HOST:$PROJ/data/v4/
rsync -az rlaif/data/v4_full/train.jsonl rlaif/data/v4_full/val.jsonl $HOST:$PROJ/data/v4_full/
rsync -az rlaif/data/short/short_heldout_prompts.jsonl rlaif/data/rl_prompts.jsonl $HOST:$PROJ/data/
rsync -az --exclude '.cache' --exclude '__pycache__' rlaif/ $HOST:$PROJ/rlaif/
# touch-up: LoRA r32 on the merged v3b, 1 epoch, half the SFT learning rate, saves 5x per epoch
ssh $HOST "RUN_NAME=$RUN GPU=auto MODE=detached DATA=$PROJ/data/v4 EXTRA=\"--model $PROJ/models/sft-lora-r32-mixAB-v3b-merged --train $PROJ/data/v4/train.jsonl --val $PROJ/data/v4/val.jsonl --epochs 1.0 --lr 5e-5 --saves_per_epoch 5 --run_name $RUN\" bash -s" < sft/remote_launch.sh
echo "launched $RUN; log: ssh $HOST tail -f $PROJ/logs/$RUN.log"
