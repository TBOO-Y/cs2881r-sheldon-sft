#!/usr/bin/env bash
# Evaluate one model (or base + adapter) on one GPU, detached, idempotent. Suites:
#   quick : math500 avg@4 (T 0.6, 4k tokens) + gsm8k greedy (1k)                      ~5 min  (pilots, checkpoints)
#   full  : quick + math500 greedy + aime24/25/26 avg@16                              ~15 min (baselines, final models)
#   NAME=grpo-v2 MODEL=$SEED_MODEL [ADAPTER=...] [GPU=7] [SUITE=quick] bash rlvr/runpod/eval.sh   -> evals/rlvr/$NAME/{avg4,greedy,avg16}/
set -euo pipefail; source "$(dirname "$0")/env.sh"; cd "$PROJ"
NAME="${NAME:?}"; MODEL="${MODEL:?}"; GPU="${GPU:-7}"; SUITE="${SUITE:-quick}"; AD=""; [ -n "${ADAPTER:-}" ] && AD="--adapter $ADAPTER"; OUT="evals/rlvr/$NAME"
launch "eval-$(echo $NAME | tr '/' '_')" "$GPU" bash -c "
  [ -s $OUT/avg4/math500.summary.json ] || $PY rlvr/eval_math.py --model $MODEL $AD --tag $NAME --tasks math500 --n 4 --temperature 0.6 --max_tokens 4096 --out_dir $OUT/avg4
  [ -s $OUT/greedy/gsm8k.summary.json ] || $PY rlvr/eval_math.py --model $MODEL $AD --tag $NAME --tasks gsm8k --n 1 --max_tokens 1024 --out_dir $OUT/greedy
  if [ $SUITE = full ]; then
    [ -s $OUT/greedy/math500.summary.json ] || $PY rlvr/eval_math.py --model $MODEL $AD --tag $NAME --tasks math500 --n 1 --max_tokens 4096 --out_dir $OUT/greedy
    [ -s $OUT/avg16/aime26.summary.json ] || $PY rlvr/eval_math.py --model $MODEL $AD --tag $NAME --tasks aime24,aime25,aime26 --n 16 --temperature 0.6 --max_tokens 4096 --out_dir $OUT/avg16
  fi; echo '[eval-all-done]'"
