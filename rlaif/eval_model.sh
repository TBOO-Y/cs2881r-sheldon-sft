#!/usr/bin/env bash
# Evaluate one model directory (merged) or base+adapter on a free GPU, detached: held-out+OOD persona gens (400 tok),
# the 60 short held-out prompts, and GSM8K (1024 tok). Run ON the cluster:
#   NAME=sft-touchup-v4 MODEL=/data/agastyas/cs2881r/models/sft-touchup-v4-merged [ADAPTER=...] [TASKS="persona short gsm8k"] bash rlaif/eval_model.sh
set -uo pipefail
NAME="${NAME:?}"; MODEL="${MODEL:?}"; ADAPTER="${ADAPTER:-}"; TASKS="${TASKS:-persona short gsm8k}"; WANT="${GPU:-auto}"
PROJ=/data/agastyas/cs2881r; P=/data/agastyas/Miniconda3/bin/python; THRESH=1024
mapfile -t USED  < <(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
mapfile -t UUIDS < <(nvidia-smi --query-gpu=uuid --format=csv,noheader)
BUSY="$(nvidia-smi --query-compute-apps=gpu_uuid --format=csv,noheader)"
is_free() { local i=$1; [[ "${USED[$i]:-x}" =~ ^[0-9]+$ ]] && [ "${USED[$i]}" -lt "$THRESH" ] && ! grep -q "${UUIDS[$i]}" <<<"$BUSY"; }
pick=""; if [ "$WANT" = auto ]; then for i in $(seq 0 $(( ${#USED[@]} - 1 ))); do is_free "$i" && { pick=$i; break; }; done; else is_free "$WANT" && pick=$WANT; fi
[ -z "$pick" ] && { echo "no free GPU (want=$WANT)"; exit 3; }
export HF_HOME=/data/hf_cache HF_HUB_CACHE=/data/hf_cache HUGGINGFACE_HUB_CACHE=/data/hf_cache TRANSFORMERS_CACHE=/data/hf_cache HF_HUB_OFFLINE=1
export CUDA_VISIBLE_DEVICES=$pick TOKENIZERS_PARALLELISM=false
AD=""; [ -n "$ADAPTER" ] && AD="--adapter $ADAPTER"
mkdir -p $PROJ/gens/$NAME $PROJ/evals/gsm8k/$NAME $PROJ/logs; LOG=$PROJ/logs/eval-$NAME-gpu$pick.log
echo "gpu=$pick name=$NAME model=$MODEL adapter=${ADAPTER:-none} tasks=$TASKS log=$LOG"
setsid nohup bash -c "
for t in $TASKS; do
  case \$t in
    persona) f=$PROJ/gens/$NAME/final.jsonl; [ -s \$f ] && { echo '[skip] persona'; continue; }; echo \"[eval] persona start \$(date +%T)\"; $P -u $PROJ/generate_heldout.py --model $MODEL $AD --tag $NAME --prompts $PROJ/data/heldout_prompts.jsonl --out \$f 2>&1 | grep -E '^\[done\]|Traceback|Error' ;;
    short)   f=$PROJ/gens/$NAME/short_heldout.jsonl; [ -s \$f ] && { echo '[skip] short'; continue; }; echo \"[eval] short start \$(date +%T)\"; $P -u $PROJ/generate_heldout.py --model $MODEL $AD --tag $NAME --prompts $PROJ/data/short_heldout_prompts.jsonl --out \$f 2>&1 | grep -E '^\[done\]|Traceback|Error' ;;
    gsm8k)   f=$PROJ/evals/gsm8k/$NAME/final.jsonl; [ -s \$f ] && { echo '[skip] gsm8k'; continue; }; echo \"[eval] gsm8k start \$(date +%T)\"; $P -u $PROJ/eval_gsm8k.py --model $MODEL $AD --tag $NAME --out \$f 2>&1 | grep -E '^\[summary\]|^\[done\]|Traceback|Error' ;;
  esac
done; echo '[eval-all-done]'" > "$LOG" 2>&1 < /dev/null &
echo "detached pid=$!"
