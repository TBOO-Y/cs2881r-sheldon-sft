#!/usr/bin/env bash
# Run the judge calibration against the locally served judge (see serve_judge.sh). Run ON the cluster.
set -euo pipefail
PROJ=/data/agastyas/cs2881r; PORT=${PORT:-8001}; PY=/data/agastyas/Miniconda3/bin/python; TAG=${TAG:-qwen32b}
export OAI_BASE_URL=http://127.0.0.1:$PORT/v1 OAI_CACHE_DIR=$PROJ/oai_cache no_proxy=localhost,127.0.0.1,::1; unset https_proxy http_proxy
export CALIB_HW=$PROJ/calib CALIB_GENS=$PROJ/gens CALIB_OUT_MD=$PROJ/calib/calibration_$TAG.md CALIB_OUT_RAW=$PROJ/calib/raw_$TAG.jsonl
until curl -sf http://127.0.0.1:$PORT/v1/models >/dev/null; do echo "waiting for judge server..."; sleep 15; done
cd $PROJ && $PY rlaif/judge/calibrate.py --models judge --n ${N:-50} --workers ${WORKERS:-32}
