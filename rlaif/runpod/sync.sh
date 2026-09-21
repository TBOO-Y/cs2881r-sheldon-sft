#!/usr/bin/env bash
# Push the working tree (including the regenerated, git-ignored data files the node needs) to the pod. Run FROM WSL:
#   POD=root@<ip> PORT=<ssh port> bash rlaif/runpod/sync.sh   or   POD=<ssh-config alias> bash rlaif/runpod/sync.sh   (omit PORT with an alias)
set -euo pipefail
POD="${POD:?set POD=user@host or an ssh-config alias}"; PORT="${PORT:-}"; SSHP=""; [ -n "$PORT" ] && SSHP="-p $PORT"; PROJ="${PROJ:-/root/cs2881r}"; cd "$(dirname "$0")/../.."
ssh $SSHP "$POD" "mkdir -p $PROJ; command -v rsync >/dev/null || (apt-get update -qq && apt-get install -y -qq rsync) >/dev/null 2>&1; command -v rsync >/dev/null && echo 'pod: rsync ok' || echo 'pod: rsync missing'"
rsync -az --info=stats1 -e "ssh $SSHP" --exclude .git --exclude .venv --exclude wandb --exclude '__pycache__' --exclude sft/data_raw \
  --exclude 'sft/data/*.jsonl' --exclude 'sft/data_v3a/*.jsonl' --exclude 'sft/data_v3b/train.jsonl' --exclude 'sft/data_v3b/val.jsonl' \
  --exclude gens --exclude 'evals/**/*.jsonl' --exclude oai_cache ./ "$POD:$PROJ/"
[ -f .env ] && rsync -az -e "ssh $SSHP" .env "$POD:$PROJ/.env" && echo "synced .env (keys)" || echo "[note] no local .env; create $PROJ/.env on the pod with OPENROUTER_API_KEY / WANDB_API_KEY / HF_TOKEN"
echo "synced -> $POD:$PROJ"
