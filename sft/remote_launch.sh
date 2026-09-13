#!/usr/bin/env bash
# Launch train_sft.py on a free Athena GPU. Run FROM THE MAC as:
#   ssh agastyas@athena01.ig32s.ruhr-uni-bochum.de 'RUN_NAME=<name> GPU=auto MODE=detached EXTRA="<args>" bash -s' < sft/remote_launch.sh
# MODE=fg streams output (smoke tests); MODE=detached uses setsid+nohup and survives SSH drops.
# GPU policy mirrors gpurun: a GPU counts as free only if <1024 MiB is used AND it has no compute processes.
set -uo pipefail
RUN_NAME="${RUN_NAME:?set RUN_NAME}"; WANT="${GPU:-auto}"; MODE="${MODE:-detached}"; EXTRA="${EXTRA:-}"
THRESH=1024; PROJ=/data/agastyas/cs2881r; P=/data/agastyas/Miniconda3/bin/python

mapfile -t USED  < <(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
mapfile -t UUIDS < <(nvidia-smi --query-gpu=uuid --format=csv,noheader)
BUSY_UUIDS="$(nvidia-smi --query-compute-apps=gpu_uuid --format=csv,noheader)"
is_free() { local i=$1; [[ "${USED[$i]:-x}" =~ ^[0-9]+$ ]] && [ "${USED[$i]}" -lt "$THRESH" ] && ! grep -q "${UUIDS[$i]}" <<<"$BUSY_UUIDS"; }
pick=""
if [ "$WANT" = auto ]; then
  for i in $(seq 0 $(( ${#USED[@]} - 1 ))); do is_free "$i" && { pick=$i; break; }; done
else
  is_free "$WANT" && pick=$WANT
fi
if [ -z "$pick" ]; then echo "no free GPU (want=$WANT); refusing to share another user's GPU"; nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv; exit 3; fi

# proxy (cluster has no direct egress), shared HF cache, W&B on /data, nothing large in $HOME
export http_proxy=http://www-cache.rz.ruhr-uni-bochum.de:80; export https_proxy=$http_proxy HTTP_PROXY=$http_proxy HTTPS_PROXY=$http_proxy
export no_proxy=.rub.de,.ruhr-uni-bochum.de,localhost,127.0.0.1,::1; export NO_PROXY=$no_proxy
export HF_HOME=/data/hf_cache HF_HUB_CACHE=/data/hf_cache HUGGINGFACE_HUB_CACHE=/data/hf_cache TRANSFORMERS_CACHE=/data/hf_cache
export HF_TOKEN_PATH=$HOME/.cache/huggingface/token HF_HUB_OFFLINE=1 HF_HUB_ETAG_TIMEOUT=15
export WANDB_DIR=$PROJ/wandb WANDB_CACHE_DIR=$PROJ/wandb/cache WANDB_CONFIG_DIR=$PROJ/wandb/config WANDB_PROJECT=cs2881r-sheldon
source "$HOME/.config/cs2881r/env"          # exports WANDB_API_KEY
export CUDA_VISIBLE_DEVICES=$pick TOKENIZERS_PARALLELISM=false
mkdir -p "$PROJ/logs" "$PROJ/wandb"; cd "$PROJ"
LOG=$PROJ/logs/$RUN_NAME.log
SCRIPT="${SCRIPT:-}"   # set SCRIPT=<file.py> to run another script in $PROJ with EXTRA as its full argument list
if [ -n "$SCRIPT" ]; then CMD="$P -u $PROJ/$SCRIPT $EXTRA"
else DATA="${DATA:-$PROJ/data}"; CMD="$P -u $PROJ/train_sft.py --train $DATA/train.jsonl --val $DATA/val.jsonl --run_name $RUN_NAME $EXTRA"; fi
echo "gpu=$pick host=$(hostname) mode=$MODE log=$LOG"; echo "cmd: $CMD"
if [ "$MODE" = fg ]; then
  $CMD 2>&1 | tee "$LOG"; exit "${PIPESTATUS[0]}"
else
  setsid nohup bash -c "$CMD" > "$LOG" 2>&1 < /dev/null &
  echo $! > "$PROJ/logs/$RUN_NAME.pid"; sleep 3
  echo "detached pid=$(cat "$PROJ/logs/$RUN_NAME.pid"); python procs: $(pgrep -f "$PROJ/" | tr '\n' ' ')"
fi
