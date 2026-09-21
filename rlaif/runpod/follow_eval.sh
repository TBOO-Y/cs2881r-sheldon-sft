#!/usr/bin/env bash
# Follow a GRPO run ON the pod: evaluate every checkpoint adapter as it appears (GSM8K test, 60 short held-out prompts, 502+40 persona
# prompts), one GPU, detached; exits when final_adapter exists and every checkpoint has outputs. Outputs land next to the run's
# final-model evals:  $PROJ/evals/gsm8k/<RUN>/checkpoint-N.jsonl(+.summary.json)   $PROJ/gens/<RUN>/checkpoint-N{,.short}.jsonl
#   RUN=grpo-v1 BASE=$PROJ/models/sft-touchup-v4-merged [GPU=4] [TASKS="gsm8k short persona"] [LIMIT=0] bash rlaif/runpod/follow_eval.sh
# A full GSM8K pass on a 3B model takes ~10 min on an H100, checkpoints arrive every ~20 min at save_steps 25, so one GPU keeps up.
# Summarise with:  $PY rlaif/summarize_run.py --run <RUN> [--ref sft-touchup-v4]
set -euo pipefail; source "$(dirname "$0")/env.sh"; cd "$PROJ"
RUN="${RUN:?}"; BASE="${BASE:?merged model the adapters were trained on}"; GPU="${GPU:-4}"; TASKS="${TASKS:-gsm8k short persona}"; LIMIT="${LIMIT:-0}"
mkdir -p "evals/gsm8k/$RUN" "gens/$RUN"
LIM=""; [ "$LIMIT" != 0 ] && LIM="--limit $LIMIT"
launch "follow-$RUN" "$GPU" bash -c "
while true; do did=0
  for d in \$(ls -d runs/$RUN/checkpoint-* 2>/dev/null | xargs -r -n1 basename | sort -t- -k2 -n); do
    [ -f runs/$RUN/\$d/adapter_config.json ] || continue
    for t in $TASKS; do case \$t in
      gsm8k)   f=evals/gsm8k/$RUN/\$d.jsonl; [ -s \$f.summary.json ] && continue; did=1; echo \"[follow] gsm8k \$d \$(date +%T)\"; $PY sft/eval_gsm8k.py --model $BASE --adapter runs/$RUN/\$d --tag $RUN/\$d --data data/gsm8k_test.jsonl --out \$f $LIM 2>&1 | grep -E '^\[summary\]|Traceback|Error' ;;
      short)   f=gens/$RUN/\$d.short.jsonl; [ -s \$f ] && continue; did=1; echo \"[follow] short \$d \$(date +%T)\"; $PY sft/generate_heldout.py --model $BASE --adapter runs/$RUN/\$d --tag $RUN/\$d --prompts rlaif/data/short/short_heldout_prompts.jsonl --out \$f 2>&1 | grep -E 'Traceback|Error' ;;
      persona) f=gens/$RUN/\$d.jsonl; [ -s \$f ] && continue; did=1; echo \"[follow] persona \$d \$(date +%T)\"; $PY sft/generate_heldout.py --model $BASE --adapter runs/$RUN/\$d --tag $RUN/\$d --prompts sft/data_v3b/heldout_prompts.jsonl --out \$f $LIM 2>&1 | grep -E 'Traceback|Error' ;;
    esac; done; done
  if [ -d runs/$RUN/final_adapter ] && [ \$did = 0 ]; then echo '[follow] run finished and every checkpoint evaluated'; break; fi
  sleep 60; done"
