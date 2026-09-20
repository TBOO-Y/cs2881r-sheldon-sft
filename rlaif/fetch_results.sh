#!/usr/bin/env bash
# Pull a run's generations + GSM8K eval back to the Mac and compare against v3b/base/gold. Run FROM THE MAC:
#   bash rlaif/fetch_results.sh sft-touchup-v4 [more run names]
set -euo pipefail
HOST=agastyas@athena01.ig32s.ruhr-uni-bochum.de; PROJ=/data/agastyas/cs2881r; cd "$(dirname "$0")/.."
for RUN in "$@"; do
  mkdir -p gens/$RUN evals/gsm8k/$RUN
  rsync -az --timeout=90 $HOST:$PROJ/gens/$RUN/ gens/$RUN/ || echo "[warn] gens rsync failed for $RUN"
  rsync -az --timeout=90 $HOST:$PROJ/evals/gsm8k/$RUN/ evals/gsm8k/$RUN/ || echo "[warn] gsm8k rsync failed for $RUN"
  echo "== $RUN"; ls gens/$RUN evals/gsm8k/$RUN 2>/dev/null
  [ -s evals/gsm8k/$RUN/final.jsonl.summary.json ] && python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print('gsm8k', sys.argv[2], {k:(round(v,4) if isinstance(v,float) else v) for k,v in d.items() if k!='tag'})" evals/gsm8k/$RUN/final.jsonl.summary.json "$RUN"
done
ARGS=""; for RUN in "$@"; do [ -s gens/$RUN/final.jsonl ] && ARGS="$ARGS $RUN=gens/$RUN/final.jsonl"; done
[ -s gens/sft-lora-r32-mixAB-v3b/checkpoint-576.jsonl ] && ARGS="$ARGS v3b=gens/sft-lora-r32-mixAB-v3b/checkpoint-576.jsonl"
[ -n "$ARGS" ] && python3 rlaif/audit/quant/compare.py $ARGS --gold /private/tmp/claude-501/-Users-agastyasridharan-cs-2881r/3acde4e5-4736-45cc-b35b-049e0cab88c1/scratchpad/hw1/persona_eval/data/heldout_gold.jsonl || true
