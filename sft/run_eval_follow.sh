#!/usr/bin/env bash
# Like run_eval_sweep.sh, but keeps polling the run directory and evaluates each new checkpoint as it appears,
# until final_adapter exists and every checkpoint has an output. From the Mac:
#   ssh $H 'RUN=<run> TASK=gsm8k|persona GPU=auto|<n> bash -s' < sft/run_eval_follow.sh
set -uo pipefail
RUN="${RUN:?set RUN}"; TASK="${TASK:?gsm8k|persona}"; WANT="${GPU:-auto}"; EXTRA="${EXTRA:-}"; ORDER="${ORDER:-asc}"  # ORDER=desc: newest checkpoint first (run a 2nd instance on another GPU)
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
if [ "$TASK" = gsm8k ]; then OUT=$PROJ/evals/gsm8k/$RUN; SCRIPT=eval_gsm8k.py; PARGS=""; else OUT=$PROJ/gens/$RUN; SCRIPT=generate_heldout.py; PARGS="--prompts $PROJ/data/heldout_prompts.jsonl"; fi
SORTFLAG="-n"; [ "$ORDER" = desc ] && SORTFLAG="-rn"
mkdir -p "$OUT" "$PROJ/logs"; LOG=$PROJ/logs/follow-$TASK-$RUN-gpu$pick.log
echo "gpu=$pick task=$TASK run=$RUN log=$LOG (follow mode)"
setsid nohup bash -c "
while true; do
  did=0
  for d in \$(ls -d $PROJ/runs/$RUN/checkpoint-* 2>/dev/null | xargs -n1 basename | sort -t- -k2 $SORTFLAG); do
    f=$OUT/\$d.jsonl; [ -s \$f ] && continue
    [ -f $PROJ/runs/$RUN/\$d/adapter_model.safetensors ] || continue
    echo \"[sweep] $TASK \$d start \$(date +%T)\"; did=1
    $P -u $PROJ/$SCRIPT --model Qwen/Qwen2.5-3B-Instruct --adapter $PROJ/runs/$RUN/\$d --tag $RUN/\$d $PARGS --out \$f $EXTRA 2>&1 | grep -E '^\[summary\]|^\[done\]|Traceback|Error'
  done
  if [ -d $PROJ/runs/$RUN/final_adapter ] && [ \$did = 0 ]; then echo '[sweep-all-done]'; break; fi
  [ \$did = 0 ] && sleep 60
done" > "$LOG" 2>&1 < /dev/null &
echo "detached pid=$!"
