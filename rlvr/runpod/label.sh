#!/usr/bin/env bash
# Pass-rate labels for the training set under one model: one shard per GPU, then merge + per-level table -> results/rlvr/difficulty_<TAG>.md
#   TAG=grpo-v2 MODEL=$SEED_MODEL [K=8] [GPUS=0,1,2,3,4,5,6,7] bash rlvr/runpod/label.sh      # ~15-20 min for 12k x 8 (est.)
set -euo pipefail; source "$(dirname "$0")/env.sh"; cd "$PROJ"
TAG="${TAG:?}"; MODEL="${MODEL:-$SEED_MODEL}"; K="${K:-8}"; GPUS="${GPUS:-0,1,2,3,4,5,6,7}"; N=$(echo "$GPUS" | tr ',' '\n' | wc -l); i=0
for g in $(echo "$GPUS" | tr ',' ' '); do
  launch "label-$TAG-$i" "$g" $PY rlvr/data/label_passrate.py --model "$MODEL" --data rlvr/data/math12k.jsonl --k "$K" --shard "$i/$N" --out "rlvr/data/passrate_$TAG.shard$i.jsonl" ${EXTRA:-}
  i=$((i+1)); done
for j in $(seq 0 $((N-1))); do waitpid "$(cat logs/label-$TAG-$j.pid)"; done
[ "$(ls rlvr/data/passrate_$TAG.shard*.jsonl 2>/dev/null | wc -l)" = "$N" ] || { echo "label: expected $N shard files, found $(ls rlvr/data/passrate_$TAG.shard*.jsonl 2>/dev/null | wc -l); see logs/label-$TAG-*.log"; exit 3; }
$PY rlvr/data/label_passrate.py --merge "rlvr/data/passrate_$TAG.shard*.jsonl" --out "rlvr/data/passrate_$TAG.jsonl" --summary "results/rlvr/difficulty_$TAG.md"
