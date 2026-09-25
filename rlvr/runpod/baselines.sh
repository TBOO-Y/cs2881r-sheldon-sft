#!/usr/bin/env bash
# Step 0: full suite for base / touch-up / grpo-v2 on three GPUs in parallel (~15 min), then results/rlvr/baselines.md
set -euo pipefail; source "$(dirname "$0")/env.sh"; cd "$PROJ"
NAME=base MODEL=Qwen/Qwen2.5-3B-Instruct GPU=0 SUITE=full bash rlvr/runpod/eval.sh
NAME=sft-touchup-v4 MODEL=$PROJ/models/sft-touchup-v4-merged GPU=1 SUITE=full bash rlvr/runpod/eval.sh
NAME=grpo-v2 MODEL=$SEED_MODEL GPU=2 SUITE=full bash rlvr/runpod/eval.sh
for n in base sft-touchup-v4 grpo-v2; do waitpid "$(cat logs/eval-$n.pid)"; done
$PY rlvr/summarize_run.py --models base sft-touchup-v4 grpo-v2 --out results/rlvr/baselines.md
