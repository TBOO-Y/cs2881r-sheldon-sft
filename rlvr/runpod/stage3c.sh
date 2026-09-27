#!/usr/bin/env bash
# Stage 3c ON the pod: one full-fine-tune attempt on the rlvr-main seed (user decision 2026-09-26): AdamW 2e-6, fp32 master weights, server layout
# (vLLM on $SERVER_GPU, DDP ranks on $TRAIN_GPUS), 100 steps WSD (warm-up 5, decay last 20%), band schedule from the stage-1 labels (made by this seed).
# Then every checkpoint gets the quick suite and the merged model the full suite. Log logs/stage3c.log, marker logs/stage3c.stage.
#   [START=models/rlvr-main-merged] [LABELS=rlvr/data/passrate_rlvr-3b-s1.jsonl] [STEPS=100] [LR=2e-6] [RUN=rlvr-3c-fullft] bash rlvr/runpod/stage3c.sh
set -uo pipefail; source "$(dirname "$0")/env.sh"; cd "$PROJ"; R="$PROJ/rlvr/runpod"; LOG="$PROJ/logs/stage3c.log"; ST="$PROJ/logs/stage3c.stage"
START="${START:-$PROJ/models/rlvr-main-merged}"; LABELS="${LABELS:-rlvr/data/passrate_rlvr-3b-s1.jsonl}"; STEPS="${STEPS:-100}"; LR="${LR:-2e-6}"; RUN="${RUN:-rlvr-3c-fullft}"
EXTRA_POOLS="rlvr/data/extra_deepmath.jsonl,rlvr/data/extra_dapo17k.jsonl,rlvr/data/extra_deepscaler.jsonl"; CAPS="deepmath=0.3,dapo17k=0.2,deepscaler=0.2"
say(){ echo "$(date -u +%FT%TZ) $*" | tee -a "$LOG"; }; stage(){ echo "$1" > "$ST"; say "=== stage $1"; }
say "stage3c start: START=$START LR=$LR STEPS=$STEPS labels=$LABELS"
pgrep -f rlaif/runpod/mirror.sh >/dev/null || { nohup bash "$PROJ/rlaif/runpod/mirror.sh" > /dev/null 2>&1 & say "mirror started"; }
stage schedule
[ -s rlvr/data/schedule_$RUN.jsonl ] || $PY rlvr/data/build_schedule.py --mode band --train rlvr/data/math12k.jsonl --extra "$EXTRA_POOLS" --passrate "$LABELS" \
    --steps "$STEPS" --prompts_per_step 16 --G 16 --band 0.125,0.875 --frontier 0.10 --source_caps "$CAPS" --seed 11 --out rlvr/data/schedule_$RUN.jsonl 2>&1 | tee -a "$LOG" | tail -6
stage train
if [ ! -d "runs/$RUN/final" ]; then
  MODEL=$START bash "$R/serve_vllm.sh" 2>&1 | tee -a "$LOG" | tail -1
  RUN=$RUN MODE=server LORA=0 STEPS=$STEPS MODEL=$START SCHEDULE=rlvr/data/schedule_$RUN.jsonl LENPEN=dapo LR=$LR TOTAL=$STEPS SAVE=25 EXTRA="--wsd_decay_frac 0.2 --warmup_steps 5" bash "$R/run_rlvr.sh" 2>&1 | tee -a "$LOG" | tail -2
  waitpid "$(cat logs/$RUN.pid)"; vllm_stop
fi
[ -f "models/$RUN-merged/config.json" ] || { say "no merged model (see logs/$RUN.log); abort"; exit 3; }
stage eval
RUN=$RUN BASE=$START bash "$R/follow_eval.sh"; waitpid "$(cat logs/follow-$RUN.pid)"
NAME=$RUN MODEL=$PROJ/models/$RUN-merged GPU=1 SUITE=full bash "$R/eval.sh"; waitpid "$(cat logs/eval-$RUN.pid)"
$PY rlvr/summarize_run.py --runs $RUN --models $RUN --ref rlvr-main --ref base --out results/rlvr/$RUN.md 2>&1 | tee -a "$LOG" | tail -14
stage done; say "STAGE 3C DONE: results/rlvr/$RUN.md"
