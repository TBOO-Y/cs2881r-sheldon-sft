#!/usr/bin/env bash
# Step 3/4: pilots, 20 steps each on the identical schedule, then the quick suite on each pilot's last checkpoint (GPU 7) and results/rlvr/pilots.md.
#   default PILOTS="full-adamw lora-adamw"  (pilot 1: LoRA vs full);  later: PILOTS="full-muon full-muonp" or "lora-lenpen" / "full-lenpen" (WINNER_OPT=...)
#   [STEPS=20] [PILOTS=...] [SCHEDULE=rlvr/data/schedule_main.jsonl] bash rlvr/runpod/pilot.sh
set -euo pipefail; source "$(dirname "$0")/env.sh"; cd "$PROJ"
STEPS="${STEPS:-20}"; PILOTS="${PILOTS:-full-adamw lora-adamw}"; SCHEDULE="${SCHEDULE:-rlvr/data/schedule_main.jsonl}"
for p in $PILOTS; do
  RUN="pilot-$p"
  if [ -d "runs/$RUN/final" ] || [ -d "runs/$RUN/final_adapter" ]; then echo "[pilot] $RUN done already"; continue; fi
  case $p in
    full-*) MODEL=$SEED_MODEL GPUS=0 bash rlvr/runpod/serve_vllm.sh; MODE=server ;;
    lora-*) MODE=colocate ;;
    *) echo "unknown pilot $p"; exit 2 ;;
  esac
  case $p in
    *-adamw) OPT=adamw; LENPEN=none ;;  *-muon) OPT=muon; LENPEN=none ;;  *-muonp) OPT=muonp; LENPEN=none ;;
    *-lenpen) OPT="${WINNER_OPT:-adamw}"; LENPEN=dapo ;;  *) echo "unknown pilot $p"; exit 2 ;;
  esac
  RUN=$RUN MODE=$MODE STEPS=$STEPS OPT=$OPT LENPEN=$LENPEN SCHEDULE=$SCHEDULE SAVE="${SAVE:-10}" bash rlvr/runpod/run_rlvr.sh
  waitpid "$(cat logs/$RUN.pid)"; vllm_stop
  echo "[pilot] $RUN exited: $({ grep -E '\[time\] step|merged ->|Traceback' logs/$RUN.log || true; } | tail -2 | tr '\n' ' ')"
done
for p in $PILOTS; do RUN="pilot-$p"; CK=$(ls -d runs/$RUN/checkpoint-* 2>/dev/null | sort -V | tail -1); [ -n "$CK" ] || continue
  if [ -f "$CK/adapter_config.json" ]; then NAME=$RUN/$(basename $CK) MODEL=$SEED_MODEL ADAPTER=$CK GPU=7 bash rlvr/runpod/eval.sh; else NAME=$RUN/$(basename $CK) MODEL=$CK GPU=7 bash rlvr/runpod/eval.sh; fi
  waitpid "$(cat logs/eval-${RUN}_$(basename $CK).pid)"; done
$PY rlvr/summarize_run.py --runs $(for p in $PILOTS; do echo -n "pilot-$p "; done) --ref grpo-v2 --out results/rlvr/pilots.md
