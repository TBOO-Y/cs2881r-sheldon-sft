#!/usr/bin/env bash
# Judge calibration on the committed probe files. Needs only OPENROUTER_API_KEY (no GPU): run it from WSL or the pod.
#   bash rlaif/runpod/calibrate.sh [--efforts minimal,low] [--n 40 --probe_n 120]
# Writes rlaif/judge/calibration_openai_gpt_5_6_luna.md (~1,300 calls, a few dollars at Luna prices).
set -euo pipefail; cd "$(dirname "$0")/../.."
export OAI_BASE_URL="${OAI_BASE_URL:-https://openrouter.ai/api/v1}" JUDGE_MODEL="${JUDGE_MODEL:-openai/gpt-5.6-luna}"
PY="${PY:-python}"; [ -x .venv/bin/python ] && PY=.venv/bin/python
$PY rlaif/judge/oai.py "$JUDGE_MODEL"
$PY rlaif/judge/calibrate.py --models "$JUDGE_MODEL" --workers "${WORKERS:-64}" "$@"
