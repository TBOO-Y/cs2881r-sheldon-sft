#!/usr/bin/env bash
# Evaluate one model dir ON the pod (detached, one GPU): 502 held-out + 40 OOD persona gens (400 tok, greedy), the 60 short held-out
# prompts, and GSM8K test (1,319, 1024 tok). Idempotent: existing outputs are skipped.
#   NAME=sft-touchup-v4 MODEL=$PROJ/models/sft-touchup-v4-merged [ADAPTER=...] [GPU=1] [TASKS="persona short gsm8k"] bash rlaif/runpod/run_eval.sh
set -euo pipefail; source "$(dirname "$0")/env.sh"; cd "$PROJ"
NAME="${NAME:?}"; MODEL="${MODEL:?}"; ADAPTER="${ADAPTER:-}"; TASKS="${TASKS:-persona short gsm8k}"; GPU="${GPU:-1}"
AD=""; [ -n "$ADAPTER" ] && AD="--adapter $ADAPTER"; mkdir -p "gens/$NAME" "evals/gsm8k/$NAME"
launch "eval-$NAME" "$GPU" bash -c "
for t in $TASKS; do case \$t in
  persona) f=gens/$NAME/final.jsonl; [ -s \$f ] && { echo '[skip] persona'; continue; }; echo \"[eval] persona \$(date +%T)\"; $PY sft/generate_heldout.py --model $MODEL $AD --tag $NAME --prompts sft/data_v3b/heldout_prompts.jsonl --out \$f ;;
  short)   f=gens/$NAME/short_heldout.jsonl; [ -s \$f ] && { echo '[skip] short'; continue; }; echo \"[eval] short \$(date +%T)\"; $PY sft/generate_heldout.py --model $MODEL $AD --tag $NAME --prompts rlaif/data/short/short_heldout_prompts.jsonl --out \$f ;;
  gsm8k)   f=evals/gsm8k/$NAME/final.jsonl; [ -s \$f ] && { echo '[skip] gsm8k'; continue; }; echo \"[eval] gsm8k \$(date +%T)\"; $PY sft/eval_gsm8k.py --model $MODEL $AD --tag $NAME --data data/gsm8k_test.jsonl --out \$f ;;
esac; done; echo '[eval-all-done]'"
