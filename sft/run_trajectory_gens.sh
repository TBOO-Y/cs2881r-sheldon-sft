#!/usr/bin/env bash
# Generate held-out + OOD responses for every LoRA checkpoint of a run (sequentially, one GPU).
# Launched via remote_launch.sh with SCRIPT unset is not possible (it's .sh), so run it as:
#   ssh $H 'RUN=sft-lora-r32-nomath-v1 GPU=auto bash -s' < sft/run_trajectory_gens.sh
# It reuses remote_launch.sh's env conventions (proxy, HF cache, /data only) and picks a free GPU.
set -uo pipefail
RUN="${RUN:?set RUN}"; WANT="${GPU:-auto}"; EVERY="${EVERY:-1}"
PROJ=/data/agastyas/cs2881r; P=/data/agastyas/Miniconda3/bin/python; THRESH=1024
mapfile -t USED  < <(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
mapfile -t UUIDS < <(nvidia-smi --query-gpu=uuid --format=csv,noheader)
BUSY="$(nvidia-smi --query-compute-apps=gpu_uuid --format=csv,noheader)"
is_free() { local i=$1; [[ "${USED[$i]:-x}" =~ ^[0-9]+$ ]] && [ "${USED[$i]}" -lt "$THRESH" ] && ! grep -q "${UUIDS[$i]}" <<<"$BUSY"; }
pick=""; if [ "$WANT" = auto ]; then for i in $(seq 0 $(( ${#USED[@]} - 1 ))); do is_free "$i" && { pick=$i; break; }; done; else is_free "$WANT" && pick=$WANT; fi
[ -z "$pick" ] && { echo "no free GPU"; exit 3; }
export http_proxy=http://www-cache.rz.ruhr-uni-bochum.de:80 https_proxy=http://www-cache.rz.ruhr-uni-bochum.de:80
export no_proxy=.rub.de,.ruhr-uni-bochum.de,localhost,127.0.0.1,::1
export HF_HOME=/data/hf_cache HF_HUB_CACHE=/data/hf_cache HUGGINGFACE_HUB_CACHE=/data/hf_cache TRANSFORMERS_CACHE=/data/hf_cache HF_HUB_OFFLINE=1
export CUDA_VISIBLE_DEVICES=$pick TOKENIZERS_PARALLELISM=false
OUT=$PROJ/gens/$RUN; mkdir -p "$OUT" "$PROJ/logs"; LOG=$PROJ/logs/traj-gens-$RUN.log
CKPTS=$(ls -d $PROJ/runs/$RUN/checkpoint-* | sort -t- -k2 -n | awk -v e="$EVERY" 'NR % e == 0')
echo "gpu=$pick log=$LOG checkpoints: $(echo $CKPTS | tr ' ' '\n' | xargs -n1 basename | tr '\n' ' ')"
setsid nohup bash -c "
for c in $CKPTS; do n=\$(basename \$c); f=$OUT/\$n.jsonl
  if [ -s \$f ]; then echo \"[skip] \$n exists\"; continue; fi
  echo \"[traj] \$n start \$(date +%T)\"
  $P -u $PROJ/generate_heldout.py --model Qwen/Qwen2.5-3B-Instruct --adapter \$c --tag $RUN/\$n --prompts $PROJ/data/heldout_prompts.jsonl --out \$f 2>&1 | grep -E '^\[done\]|Traceback|Error'
done; echo '[traj-all-done]'" > "$LOG" 2>&1 < /dev/null &
echo "detached pid=$!"
