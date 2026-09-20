#!/usr/bin/env bash
# Stage-2 orchestrator. Runs ON the cluster, detached, idempotent:
#   A) wait for the touch-up (launched by wait_and_launch_touchup.sh) to start
#   B) bring up the local judge (serve_judge.sh) on the next free GPU
#   C) calibrate it against the Sonnet verdicts (calibrate_on_cluster.sh)
#   D) when the touch-up has merged and exited, evaluate the merged model (eval_model.sh)
set -uo pipefail
PROJ=/data/agastyas/cs2881r; RUN=${RUN:-sft-touchup-v4}; PORT=${PORT:-8001}; LOG=$PROJ/logs/orchestrate-stage2.log; THRESH=1024
say(){ echo "$(date -u +%FT%TZ) $*" >> "$LOG"; }
free_gpu(){ local busy; busy=$(nvidia-smi --query-compute-apps=gpu_uuid --format=csv,noheader | sort -u)
  nvidia-smi --query-gpu=index,uuid,memory.used --format=csv,noheader,nounits | while IFS=, read -r idx uuid mem; do
    mem=${mem// /}; uuid=${uuid// /}; idx=${idx// /}; if [ "$mem" -lt $THRESH ] && ! grep -q "$uuid" <<<"$busy"; then echo "$idx"; break; fi; done; }
judge_up(){ curl -sf --noproxy '*' http://127.0.0.1:$PORT/v1/models >/dev/null 2>&1; }
say "orchestrator start pid=$$ run=$RUN"
# A
until [ -f $PROJ/logs/$RUN.pid ]; do sleep 60; done
TPID=$(cat $PROJ/logs/$RUN.pid); say "touch-up launched pid=$TPID; letting it allocate its GPU"; sleep 150
# B
if ! judge_up; then
  while :; do g=$(free_gpu); [ -n "$g" ] && break; sleep 60; done
  say "launching judge on GPU $g"; GPU=$g PORT=$PORT bash $PROJ/rlaif/serve_judge.sh >> "$LOG" 2>&1
  JPID=$(cat $PROJ/logs/judge_server.pid 2>/dev/null || echo 0); t0=$(date +%s)
  until judge_up; do sleep 20; kill -0 "$JPID" 2>/dev/null || { say "judge server died; tail:"; tail -20 $PROJ/logs/judge_server.log >> "$LOG"; break; }
    [ $(( $(date +%s) - t0 )) -gt 1500 ] && { say "judge not ready after 25 min; tail:"; tail -20 $PROJ/logs/judge_server.log >> "$LOG"; break; }; done
fi
judge_up && say "judge ready" || say "judge NOT ready; skipping calibration"
# C
if judge_up && [ ! -s $PROJ/calib/calibration_qwen32b.md ]; then
  say "calibration start"; N=${N:-50} WORKERS=${WORKERS:-32} bash $PROJ/rlaif/calibrate_on_cluster.sh > $PROJ/logs/calibrate-qwen32b.log 2>&1; say "calibration exit rc=$? -> $PROJ/calib/calibration_qwen32b.md"
fi
# D
while :; do
  if [ -f $PROJ/models/$RUN-merged/config.json ] && ! kill -0 "$TPID" 2>/dev/null; then break; fi
  if ! kill -0 "$TPID" 2>/dev/null; then sleep 120; [ -f $PROJ/models/$RUN-merged/config.json ] && break; say "touch-up exited without a merged model; tail:"; tail -15 $PROJ/logs/$RUN.log >> "$LOG"; say "orchestrator stop"; exit 2; fi
  sleep 60; done
say "merged model present; launching eval"
until out=$(NAME=$RUN MODEL=$PROJ/models/$RUN-merged bash $PROJ/rlaif/eval_model.sh 2>&1); do sleep 60; done
say "eval: $out"; say "orchestrator done (judge left running on port $PORT for the GRPO smoke test)"
