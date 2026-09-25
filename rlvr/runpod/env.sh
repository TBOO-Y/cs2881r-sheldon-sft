#!/usr/bin/env bash
# Stage-3 pod environment: everything from the stage-2 env (PROJ, BACKUP, HF cache, W&B, launch()) plus the vLLM server address.
source "$(dirname "${BASH_SOURCE[0]}")/../../rlaif/runpod/env.sh"
export VLLM_PORT="${VLLM_PORT:-8000}" VLLM_URL="${VLLM_URL:-http://localhost:${VLLM_PORT}}"
export SEED_MODEL="${SEED_MODEL:-$PROJ/models/grpo-v2-merged}"
export ACCEL_PORT="${ACCEL_PORT:-29511}"
mkdir -p "$PROJ/evals/rlvr" "$PROJ/results/rlvr" "$PROJ/rlvr/data"
# wait until the vLLM server answers on $VLLM_URL (up to $1 seconds, default 900)
vllm_wait() { local t=${1:-900}; local i=0; until curl -sf "$VLLM_URL/health/" >/dev/null 2>&1; do sleep 5; i=$((i+5)); [ $i -ge $t ] && { echo "vLLM server not up after ${t}s"; return 1; }; done; echo "vLLM server up ($VLLM_URL)"; }
# stop the generation server: pid file (launch() uses setsid, so the pid is the process-group id), then the vLLM worker patterns; then wait until :$VLLM_PORT stops answering
vllm_stop() { local pf="$PROJ/logs/vllm-serve.pid" pid="" i=0
  [ -f "$pf" ] && pid=$(cat "$pf" 2>/dev/null) || true
  [ -n "$pid" ] && { kill -TERM -- "-$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null || true; }
  pkill -f 'trl.scripts.vllm_serve' 2>/dev/null || true; pkill -f 'vllm_serve' 2>/dev/null || true; pkill -f 'vllm.entrypoints' 2>/dev/null || true; pkill -f 'VLLM::' 2>/dev/null || true
  while curl -sf "$VLLM_URL/health/" >/dev/null 2>&1 && [ $i -lt 60 ]; do sleep 1; i=$((i+1)); done
  [ $i -ge 60 ] && { echo "vLLM server still answering after 60 s; refusing to continue"; return 1; }
  sleep 3; return 0; }
ACCEL="$PY -m accelerate.commands.launch"; TRL_BIN="$(dirname "$PY")/trl"; [ -x "$TRL_BIN" ] || TRL_BIN="$(command -v trl || true)"
waitpid() { while kill -0 "$1" 2>/dev/null; do sleep 30; done; }
