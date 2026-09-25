#!/usr/bin/env bash
# Quick-suite evaluation of a run's checkpoints as they appear (one GPU, detached); exits once the run's final model exists and every checkpoint is scored.
#   RUN=rlvr-main [GPU=7] [BASE=$SEED_MODEL] bash rlvr/runpod/follow_eval.sh
set -euo pipefail; source "$(dirname "$0")/env.sh"; cd "$PROJ"
RUN="${RUN:?}"; GPU="${GPU:-7}"; BASE="${BASE:-$SEED_MODEL}"
launch "follow-$RUN" "$GPU" bash -c "
while true; do did=0
  for d in \$(ls -d runs/$RUN/checkpoint-* 2>/dev/null | xargs -r -n1 basename | sort -t- -k2 -n); do
    OUT=evals/rlvr/$RUN/\$d; [ -s \$OUT/avg4/math500.summary.json ] && [ -s \$OUT/greedy/gsm8k.summary.json ] && continue
    [ -s runs/$RUN/\$d/trainer_state.json ] || continue            # written last by the Trainer: the weights are complete once it exists
    if [ -f runs/$RUN/\$d/adapter_config.json ]; then M=\"--model $BASE --adapter runs/$RUN/\$d\"; else M=\"--model runs/$RUN/\$d\"; fi
    did=1; echo \"[follow] \$d \$(date +%T)\"
    $PY rlvr/eval_math.py \$M --tag $RUN/\$d --tasks math500 --n 4 --temperature 0.6 --max_tokens 4096 --out_dir \$OUT/avg4 2>&1 | grep -E '^\[eval\]|Traceback|Error'
    $PY rlvr/eval_math.py \$M --tag $RUN/\$d --tasks gsm8k --n 1 --max_tokens 1024 --out_dir \$OUT/greedy 2>&1 | grep -E '^\[eval\]|Traceback|Error'
  done
  if { [ -d runs/$RUN/final ] || [ -d runs/$RUN/final_adapter ]; } && [ \$did = 0 ]; then echo '[follow] run finished and every checkpoint evaluated'; break; fi
  sleep 60; done"
