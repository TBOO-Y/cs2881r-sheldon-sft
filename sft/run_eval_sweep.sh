#!/usr/bin/env bash
# Sequentially evaluate checkpoints of a run on one free GPU, detached. From the Mac:
#   ssh $H 'RUN=<run> TASK=gsm8k|persona CKPTS="base checkpoint-19 ..."|all GPU=auto EXTRA="" bash -s' < sft/run_eval_sweep.sh
# Outputs: gsm8k -> /data/agastyas/cs2881r/evals/gsm8k/<RUN>/<ckpt>.jsonl (+ .summary.json)
#          persona -> /data/agastyas/cs2881r/gens/<RUN>/<ckpt>.jsonl
set -uo pipefail
RUN="${RUN:?set RUN}"; TASK="${TASK:?gsm8k|persona}"; CKPTS="${CKPTS:-all}"; WANT="${GPU:-auto}"; EXTRA="${EXTRA:-}"
PROJ=/data/agastyas/cs2881r; P=/data/agastyas/Miniconda3/bin/python; THRESH=1024
mapfile -t USED  < <(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
mapfile -t UUIDS < <(nvidia-smi --query-gpu=uuid --format=csv,noheader)
BUSY="$(nvidia-smi --query-compute-apps=gpu_uuid --format=csv,noheader)"
is_free() { local i=$1; [[ "${USED[$i]:-x}" =~ ^[0-9]+$ ]] && [ "${USED[$i]}" -lt "$THRESH" ] && ! grep -q "${UUIDS[$i]}" <<<"$BUSY"; }
pick=""; if [ "$WANT" = auto ]; then for i in $(seq 0 $(( ${#USED[@]} - 1 ))); do is_free "$i" && { pick=$i; break; }; done; else is_free "$WANT" && pick=$WANT; fi
[ -z "$pick" ] && { echo "no free GPU (want=$WANT)"; exit 3; }
export http_proxy=http://www-cache.rz.ruhr-uni-bochum.de:80 https_proxy=http://www-cache.rz.ruhr-uni-bochum.de:80
export no_proxy=.rub.de,.ruhr-uni-bochum.de,localhost,127.0.0.1,::1
export HF_HOME=/data/hf_cache HF_HUB_CACHE=/data/hf_cache HUGGINGFACE_HUB_CACHE=/data/hf_cache TRANSFORMERS_CACHE=/data/hf_cache HF_HUB_OFFLINE=1
export CUDA_VISIBLE_DEVICES=$pick TOKENIZERS_PARALLELISM=false
if [ "$CKPTS" = all ]; then CKPTS="base $(ls -d $PROJ/runs/$RUN/checkpoint-* | xargs -n1 basename | sort -t- -k2 -n | tr '\n' ' ')"; fi
if [ "$TASK" = gsm8k ]; then OUT=$PROJ/evals/gsm8k/$RUN; SCRIPT=eval_gsm8k.py; PARGS=""; else OUT=$PROJ/gens/$RUN; SCRIPT=generate_heldout.py; PARGS="--prompts $PROJ/data/heldout_prompts.jsonl"; fi
mkdir -p "$OUT" "$PROJ/logs"; LOG=$PROJ/logs/sweep-$TASK-$RUN-gpu$pick.log
echo "gpu=$pick task=$TASK run=$RUN log=$LOG ckpts: $CKPTS"
setsid nohup bash -c "
for c in $CKPTS; do f=$OUT/\$c.jsonl
  if [ -s \$f ]; then echo \"[skip] \$c exists\"; continue; fi
  if [ \$c = base ]; then AD=''; TAG=base; else AD=\"--adapter $PROJ/runs/$RUN/\$c\"; TAG=$RUN/\$c; fi
  echo \"[sweep] $TASK \$c start \$(date +%T)\"
  $P -u $PROJ/$SCRIPT --model Qwen/Qwen2.5-3B-Instruct \$AD --tag \$TAG $PARGS --out \$f $EXTRA 2>&1 | grep -E '^\[summary\]|^\[done\]|Traceback|Error'
done; echo '[sweep-all-done]'" > "$LOG" 2>&1 < /dev/null &
echo "detached pid=$!"
