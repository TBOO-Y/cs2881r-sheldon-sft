#!/usr/bin/env bash
# Shared environment for the stage-2 RunPod node. Source it in every launcher:  source "$(dirname "$0")/env.sh"
# Layout: $PROJ is the repo checkout on the pod's LOCAL disk (RunPod's /workspace network volume is an S3-backed FUSE mount: no chmod /
# chown / utime / hard links and ~10x slower, which breaks pip, the HF cache and rsync temp files). mirror.sh copies runs, gens, evals,
# logs and merged models to $BACKUP on the volume every few minutes so a pod restart loses at most that much.
export PROJ="${PROJ:-/root/cs2881r}" BACKUP="${BACKUP:-/workspace/cs2881r_backup}"
export HF_HOME="${HF_HOME:-/root/hf_cache}" HF_HUB_CACHE="${HF_HUB_CACHE:-/root/hf_cache/hub}" HF_HUB_ENABLE_HF_TRANSFER=1
export TOKENIZERS_PARALLELISM=false PYTHONUNBUFFERED=1
export WANDB_DIR="$PROJ/wandb" WANDB_CACHE_DIR="$PROJ/wandb/cache" WANDB_CONFIG_DIR="$PROJ/wandb/config" WANDB_PROJECT="${WANDB_PROJECT:-cs2881r-sheldon}"
# judge: OpenRouter, GPT-5.6 Luna, minimal reasoning; disk cache under $PROJ so re-runs and the smoke test are free
export OAI_BASE_URL="${OAI_BASE_URL:-https://openrouter.ai/api/v1}" OAI_CACHE_DIR="${OAI_CACHE_DIR:-$PROJ/oai_cache}"
export JUDGE_MODEL="${JUDGE_MODEL:-openai/gpt-5.6-luna}" JUDGE_REASONING="${JUDGE_REASONING:-low}"
# secrets: $PROJ/.env (OPENROUTER_API_KEY=..., WANDB_API_KEY=..., HF_TOKEN=...); never committed (.gitignore)
if [ -f "$PROJ/.env" ]; then set -a; . "$PROJ/.env"; set +a; fi
[ -n "${WANDB_API_KEY:-}" ] || export WANDB_MODE=offline
PY="${PY:-/opt/venv/bin/python}"; [ -x "$PY" ] || PY="$PROJ/.venv/bin/python"; [ -x "$PY" ] || PY=python
export PY
mkdir -p "$PROJ/logs" "$PROJ/models" "$PROJ/runs" "$PROJ/gens" "$PROJ/evals/gsm8k" "$PROJ/wandb" "$OAI_CACHE_DIR"
# detach a command on one GPU:  launch <name> <gpu> <cmd...>   -> $PROJ/logs/<name>.log, pid in $PROJ/logs/<name>.pid
launch() { local name=$1 gpu=$2; shift 2; local log="$PROJ/logs/$name.log"
  CUDA_VISIBLE_DEVICES=$gpu setsid nohup "$@" > "$log" 2>&1 < /dev/null & echo $! > "$PROJ/logs/$name.pid"
  echo "[$name] gpu=$gpu pid=$(cat "$PROJ/logs/$name.pid") log=$log"; }
