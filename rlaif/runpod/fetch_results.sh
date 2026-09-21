#!/usr/bin/env bash
# Pull gens + GSM8K evals for the given run names back FROM the pod and run the style/collapse monitor against v3b and gold. Run FROM WSL:
#   POD=root@<ip> PORT=<port> bash rlaif/runpod/fetch_results.sh v3b sft-touchup-v4 grpo-v1
set -euo pipefail
POD="${POD:?}"; PORT="${PORT:-}"; SSHP=""; [ -n "$PORT" ] && SSHP="-p $PORT"; PROJ="${PROJ:-/root/cs2881r}"; cd "$(dirname "$0")/../.."
for RUN in "$@"; do
  mkdir -p "gens/$RUN" "evals/gsm8k/$RUN"
  rsync -az -e "ssh $SSHP" "$POD:$PROJ/gens/$RUN/" "gens/$RUN/" || echo "[warn] no gens for $RUN"
  rsync -az -e "ssh $SSHP" "$POD:$PROJ/evals/gsm8k/$RUN/" "evals/gsm8k/$RUN/" || echo "[warn] no gsm8k for $RUN"
  [ -s "evals/gsm8k/$RUN/final.jsonl.summary.json" ] && python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print('gsm8k', sys.argv[2], {k:(round(v,4) if isinstance(v,float) else v) for k,v in d.items() if k!='tag'})" "evals/gsm8k/$RUN/final.jsonl.summary.json" "$RUN"
done
ARGS=""; for RUN in "$@"; do [ -s "gens/$RUN/final.jsonl" ] && ARGS="$ARGS $RUN=gens/$RUN/final.jsonl"; done
PY=python3; [ -x .venv/bin/python ] && PY=.venv/bin/python
[ -n "$ARGS" ] && $PY rlaif/audit/quant/compare.py $ARGS --gold sft/data_v3b/heldout_prompts.jsonl || true
