#!/usr/bin/env bash
# Pass-rate labels for the training set under one model: one shard per GPU, then merge + per-level table -> results/rlvr/difficulty_<TAG>.md
#   TAG=grpo-v2 MODEL=$SEED_MODEL [K=8] [DATA=rlvr/data/math12k.jsonl] [GPUS=$LABEL_GPUS] bash rlvr/runpod/label.sh      # 12k x 8 took ~3 min on 3 H200 (short answers); ~8 min at ~450-token answers
set -euo pipefail; source "$(dirname "$0")/env.sh"; cd "$PROJ"
TAG="${TAG:?}"; MODEL="${MODEL:-$SEED_MODEL}"; K="${K:-8}"; DATA="${DATA:-rlvr/data/math12k.jsonl}"; GPUS="${GPUS:-$LABEL_GPUS}"; N=$(echo "$GPUS" | tr ',' '\n' | wc -l); i=0
for g in $(echo "$GPUS" | tr ',' ' '); do
  launch "label-$TAG-$i" "$g" $PY rlvr/data/label_passrate.py --model "$MODEL" --data "$DATA" --k "$K" --shard "$i/$N" --out "rlvr/data/passrate_$TAG.shard$i.jsonl" ${EXTRA:-}
  i=$((i+1)); done
for j in $(seq 0 $((N-1))); do waitpid "$(cat logs/label-$TAG-$j.pid)"; done
[ "$(ls rlvr/data/passrate_$TAG.shard*.jsonl 2>/dev/null | wc -l)" = "$N" ] || { echo "label: expected $N shard files, found $(ls rlvr/data/passrate_$TAG.shard*.jsonl 2>/dev/null | wc -l); see logs/label-$TAG-*.log"; exit 3; }
$PY rlvr/data/label_passrate.py --merge "rlvr/data/passrate_$TAG.shard*.jsonl" --out "rlvr/data/passrate_$TAG.jsonl" --summary "results/rlvr/difficulty_$TAG.md"
