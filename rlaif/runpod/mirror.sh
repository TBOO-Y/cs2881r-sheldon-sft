#!/usr/bin/env bash
# Mirror the run outputs from the local disk to the persistent (FUSE, S3-backed) volume every INTERVAL seconds. ON the pod, detached:
#   nohup bash rlaif/runpod/mirror.sh > /dev/null 2>&1 &        (stage2.sh starts it)
# FUSE-safe flags: no perms/owner/group/times, in-place writes (the volume rejects chmod/utime and rsync's temp files).
set -uo pipefail; source "$(dirname "$0")/env.sh"; INTERVAL="${INTERVAL:-300}"; mkdir -p "$BACKUP" "$BACKUP/models"
while true; do
  for d in runs gens evals logs wandb rlaif/judge; do [ -d "$PROJ/$d" ] && rsync -rlz --no-perms --no-owner --no-group --no-times --inplace --exclude 'checkpoint-*/optimizer.pt' "$PROJ/$d/" "$BACKUP/$d/" 2>/dev/null; done
  for m in "$PROJ"/models/*-merged; do [ -f "$m/config.json" ] && [ ! -f "$BACKUP/models/$(basename "$m")/config.json" ] && rsync -rlz --no-perms --no-owner --no-group --no-times --inplace "$m/" "$BACKUP/models/$(basename "$m")/" 2>/dev/null; done
  cp "$PROJ/.env" "$BACKUP/.env" 2>/dev/null; date -u +"%FT%TZ mirrored" > "$BACKUP/last_mirror.txt"; sleep "$INTERVAL"; done
