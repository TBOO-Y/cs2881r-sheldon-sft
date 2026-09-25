#!/usr/bin/env bash
# Step 5: the main run with checkpoint follow-eval, then the full suite on the merged model and results/rlvr/$RUN.md.
# NOT to be launched without the user's explicit go-ahead (2026-09-25: pilots only).
#   MODE=colocate|server [RUN=rlvr-main] [STEPS=200] [OPT=adamw] [LENPEN=none] bash rlvr/runpod/main.sh
set -euo pipefail; source "$(dirname "$0")/env.sh"; cd "$PROJ"
RUN="${RUN:-rlvr-main}"; MODE="${MODE:?server|colocate}"; STEPS="${STEPS:-200}"
[ "$MODE" = server ] && MODEL=$SEED_MODEL bash rlvr/runpod/serve_vllm.sh
RUN=$RUN MODE=$MODE STEPS=$STEPS TOTAL=$STEPS bash rlvr/runpod/run_rlvr.sh
[ "$MODE" = colocate ] && RUN=$RUN bash rlvr/runpod/follow_eval.sh              # LoRA arm: the eval GPU is free during training
waitpid "$(cat logs/$RUN.pid)"; vllm_stop
[ "$MODE" = server ] && RUN=$RUN bash rlvr/runpod/follow_eval.sh                # full-FT arm: the eval GPU was the server; score the checkpoints afterwards
NAME=$RUN MODEL=$PROJ/models/$RUN-merged GPU=1 SUITE=full bash rlvr/runpod/eval.sh
waitpid "$(cat logs/eval-$RUN.pid)"; waitpid "$(cat logs/follow-$RUN.pid)"
$PY rlvr/summarize_run.py --runs $RUN --models $RUN --ref grpo-v2 --ref base --out results/rlvr/$RUN.md
