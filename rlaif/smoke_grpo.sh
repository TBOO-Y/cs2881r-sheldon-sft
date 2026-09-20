#!/usr/bin/env bash
# GRPO smoke test: 2 optimizer steps on 4 prompts x 4 generations against the local judge. Run FROM THE MAC:
#   MODEL=/data/agastyas/cs2881r/models/sft-touchup-v4-merged bash rlaif/smoke_grpo.sh
# Requires the judge server (rlaif/serve_judge.sh) to be up on the cluster (port 8001). Uses the policy-compliant GPU pick
# in sft/remote_launch.sh (SCRIPT mode); env prefixes are inherited by the detached process.
set -euo pipefail
HOST=agastyas@athena01.ig32s.ruhr-uni-bochum.de; PROJ=/data/agastyas/cs2881r
MODEL="${MODEL:-$PROJ/models/sft-lora-r32-mixAB-v3b-merged}"; RUN="${RUN:-grpo-smoke}"; PORT="${PORT:-8001}"
EXTRA="--model $MODEL --run_name $RUN --judge_model judge --limit 32 --max_steps 2 --save_steps 1 --num_generations 4 --prompts_per_step 4 --per_device_bs 8 --no_merge ${EXTRA_ARGS:-}"
ssh -o BatchMode=yes -o ConnectTimeout=15 $HOST "curl -sf http://127.0.0.1:$PORT/v1/models >/dev/null || { echo 'judge server not up on port $PORT'; exit 4; }
OAI_BASE_URL=http://127.0.0.1:$PORT/v1 OAI_CACHE_DIR=$PROJ/oai_cache RUN_NAME=$RUN GPU=${GPU:-auto} MODE=${MODE:-detached} SCRIPT=rlaif/train_grpo.py EXTRA=\"$EXTRA\" bash -s" < sft/remote_launch.sh
echo "follow: ssh $HOST 'tail -f $PROJ/logs/$RUN.log'"
