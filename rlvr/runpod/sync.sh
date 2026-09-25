#!/usr/bin/env bash
# Stage-3 sync FROM WSL: the stage-2 sync minus the multi-GB local artifacts (merged models, adapters, pod logs); models are pulled from the Hub by setup_stage3.sh.
#   POD=<ssh alias or root@ip> [PORT=<port>] bash rlvr/runpod/sync.sh
set -euo pipefail
POD="${POD:?set POD=user@host or an ssh-config alias}"; PORT="${PORT:-}"; SSHP=""; [ -n "$PORT" ] && SSHP="-p $PORT"; PROJ="${PROJ:-/root/cs2881r}"; cd "$(dirname "$0")/../.."
ssh $SSHP "$POD" "mkdir -p $PROJ; command -v rsync >/dev/null || (apt-get update -qq && apt-get install -y -qq rsync) >/dev/null 2>&1; command -v rsync >/dev/null && echo 'pod: rsync ok' || echo 'pod: rsync missing'"
rsync -az --info=stats1 -e "ssh $SSHP" --exclude .git --exclude .venv --exclude wandb --exclude '__pycache__' --exclude sft/data_raw \
  --exclude 'sft/data/*.jsonl' --exclude 'sft/data_v3a/*.jsonl' --exclude 'sft/data_v3b/train.jsonl' --exclude 'sft/data_v3b/val.jsonl' \
  --exclude gens --exclude 'evals/**/*.jsonl' --exclude oai_cache --exclude models --exclude runs --exclude logs_pod --exclude 'rlvr/data/passrate_*.shard*' ./ "$POD:$PROJ/"
[ -f .env ] && rsync -az -e "ssh $SSHP" .env "$POD:$PROJ/.env" && echo "synced .env (keys)" || echo "[note] no local .env; create $PROJ/.env on the pod with WANDB_API_KEY / HF_TOKEN"
echo "synced -> $POD:$PROJ"
