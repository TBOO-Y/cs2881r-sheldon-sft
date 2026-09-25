#!/usr/bin/env bash
# Step 5: the main run with checkpoint follow-eval, then the full suite on the merged model and results/rlvr/$RUN.md.
#   MODE=colocate|server [RUN=rlvr-main] [STEPS=200] [OPT=adamw] [LENPEN=none] bash rlvr/runpod/main.sh
set -euo pipefail; source "$(dirname "$0")/env.sh"; cd "$PROJ"
RUN="${RUN:-rlvr-main}"; MODE="${MODE:?server|colocate}"; STEPS="${STEPS:-200}"
[ "$MODE" = server ] && MODEL=$SEED_MODEL GPUS=0 bash rlvr/runpod/serve_vllm.sh
RUN=$RUN MODE=$MODE STEPS=$STEPS TOTAL=$STEPS bash rlvr/runpod/run_rlvr.sh
[ "$MODE" = server ] && RUN=$RUN GPU=7 bash rlvr/runpod/follow_eval.sh
waitpid "$(cat logs/$RUN.pid)"; vllm_stop
[ "$MODE" = server ] || RUN=$RUN GPU=7 bash rlvr/runpod/follow_eval.sh          # the colocated layout used every GPU: score the checkpoints afterwards
NAME=$RUN MODEL=$PROJ/models/$RUN-merged GPU=6 SUITE=full bash rlvr/runpod/eval.sh
waitpid "$(cat logs/eval-$RUN.pid)"; waitpid "$(cat logs/follow-$RUN.pid)"
$PY rlvr/summarize_run.py --runs $RUN --models $RUN --ref grpo-v2 --ref base --out results/rlvr/$RUN.md
