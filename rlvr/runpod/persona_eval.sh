#!/usr/bin/env bash
# Persona evaluation of a stage-3 model ON the pod (one GPU, ~15 min): stage-2 protocol = greedy generations for the 502 held-out + 40 OOD
# persona prompts (400 tokens) and the 60 short held-out prompts, the collapse/defect monitors (rlaif/audit/quant/compare.py) against grpo-v2
# and the gold references, persona leakage into MATH-500 answers, and the head-to-head judge vs grpo-v2 (200 prompts, both orders, ~$0.4;
# needs OPENROUTER_API_KEY in .env, skipped otherwise). Reference gens for grpo-v2 are regenerated if absent (or rsync gens/grpo-v2/*.jsonl first).
#   NAME=rlvr-main MODEL=$PROJ/models/rlvr-main-merged [HF=tbooy/Qwen2.5-3B-Instruct-Sheldon-RLVR-math-v1] [GPU=0] bash rlvr/runpod/persona_eval.sh
set -euo pipefail; source "$(dirname "$0")/env.sh"; cd "$PROJ"
NAME="${NAME:-rlvr-main}"; MODEL="${MODEL:-$PROJ/models/$NAME-merged}"; GPU="${GPU:-$EVAL_GPU}"; HF="${HF:-tbooy/Qwen2.5-3B-Instruct-Sheldon-RLVR-math-v1}"
[ -f "$MODEL/config.json" ] || { HFB="$(dirname "$PY")/hf"; [ -x "$HFB" ] || HFB="$(dirname "$PY")/huggingface-cli"; $HFB download "$HF" --local-dir "$MODEL" --quiet; }
mkdir -p gens/$NAME gens/grpo-v2 results/rlvr
gen() { local name=$1 model=$2; [ -s gens/$name/final.jsonl ] || CUDA_VISIBLE_DEVICES=$GPU $PY sft/generate_heldout.py --model "$model" --tag $name --prompts sft/data_v3b/heldout_prompts.jsonl --out gens/$name/final.jsonl
        [ -s gens/$name/short_heldout.jsonl ] || CUDA_VISIBLE_DEVICES=$GPU $PY sft/generate_heldout.py --model "$model" --tag $name --prompts rlaif/data/short/short_heldout_prompts.jsonl --out gens/$name/short_heldout.jsonl; }
gen "$NAME" "$MODEL"; gen grpo-v2 "$SEED_MODEL"
{ echo "# Persona evaluation: $NAME vs grpo-v2 ($(date -u +%F))"; echo; echo "## Collapse / defect monitors (502 held-out prompts, greedy, 400 tokens; rlaif/audit/quant/compare.py)"; echo '```'
  $PY rlaif/audit/quant/compare.py $NAME=gens/$NAME/final.jsonl grpo-v2=gens/grpo-v2/final.jsonl --gold sft/data_v3b/heldout_prompts.jsonl
  echo '```'; echo; echo "## Short prompts (60)"; echo '```'
  $PY rlaif/audit/quant/compare.py $NAME=gens/$NAME/short_heldout.jsonl grpo-v2=gens/grpo-v2/short_heldout.jsonl; echo '```'
  echo; echo "## Persona leakage into MATH-500 answers (greedy eval files; share of answers naming Sheldon / cast or saying Bazinga)"
  for m in $NAME grpo-v2 base; do f=evals/rlvr/$m/greedy/math500.jsonl; [ -s $f ] || f=$BACKUP/evals/rlvr/$m/greedy/math500.jsonl; [ -s $f ] && $PY - "$m" "$f" <<'PYEOF'
import json, re, sys
rows = [json.loads(l) for l in open(sys.argv[2])]; pat = re.compile(r"\b(Sheldon|Bazinga|Leonard|Penny|Raj|Howard|Amy|Cooper)\b")
print(f"- {sys.argv[1]}: {100 * sum(1 for r in rows if pat.search(r['responses'][0])) / len(rows):.1f}% of {len(rows)} answers")
PYEOF
  done
} > results/rlvr/persona_$NAME.md
if [ -n "${OPENROUTER_API_KEY:-}" ]; then
  $PY rlvr/persona_h2h.py --a gens/$NAME/final.jsonl --b gens/grpo-v2/final.jsonl --n 200 --workers 16 --out results/rlvr/judge_h2h_$NAME.json | tail -14 | tee -a results/rlvr/persona_$NAME.md
else echo "(no OPENROUTER_API_KEY: head-to-head judge skipped)" | tee -a results/rlvr/persona_$NAME.md; fi
echo "done: results/rlvr/persona_$NAME.md"
