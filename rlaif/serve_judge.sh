#!/usr/bin/env bash
# Serve the local judge model with vLLM (OpenAI-compatible) on one free GPU, detached. Run ON the cluster:
#   JUDGE_MODEL=Qwen/Qwen2.5-32B-Instruct PORT=8001 GPU=auto bash /data/agastyas/cs2881r/rlaif/serve_judge.sh
# Then point the judge client at it:  export OAI_BASE_URL=http://localhost:$PORT/v1  and use --judge_model judge
set -euo pipefail
PROJ=/data/agastyas/cs2881r; VENV=/data/agastyas/venvs/vllm; PORT=${PORT:-8001}; JUDGE_MODEL=${JUDGE_MODEL:-Qwen/Qwen2.5-32B-Instruct}; GPU=${GPU:-auto}
export HF_HOME=/data/hf_cache HF_HUB_CACHE=/data/hf_cache/hub HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 VLLM_CACHE_ROOT=/data/agastyas/.vllm_cache TMPDIR=/data/agastyas/tmp
export no_proxy=localhost,127.0.0.1,::1,.rub.de,.ruhr-uni-bochum.de; unset https_proxy http_proxy   # the server is local; never proxy localhost
mkdir -p $PROJ/logs /data/agastyas/tmp /data/agastyas/.vllm_cache
if [ "$GPU" = auto ]; then   # cluster policy: only a GPU with <1024 MiB used and no compute processes
  busy=$(nvidia-smi --query-compute-apps=gpu_uuid --format=csv,noheader | sort -u)
  GPU=$(nvidia-smi --query-gpu=index,uuid,memory.used --format=csv,noheader | while IFS=, read -r idx uuid mem; do
    mem=${mem// /}; mem=${mem%MiB}; uuid=${uuid// /}; if [ "$mem" -lt 1024 ] && ! grep -q "$uuid" <<<"$busy"; then echo "$idx"; break; fi; done)
  [ -n "$GPU" ] || { echo "no free GPU"; exit 1; }
fi
echo "serving $JUDGE_MODEL on GPU $GPU port $PORT"
CUDA_VISIBLE_DEVICES=$GPU setsid nohup $VENV/bin/vllm serve "$JUDGE_MODEL" --served-model-name judge --port $PORT --host 127.0.0.1 --dtype bfloat16 \
  --max-model-len 8192 --gpu-memory-utilization 0.92 --max-num-seqs 64 --enable-prefix-caching \
  > $PROJ/logs/judge_server.log 2>&1 < /dev/null &
echo $! > $PROJ/logs/judge_server.pid; echo "pid $(cat $PROJ/logs/judge_server.pid); log $PROJ/logs/judge_server.log"
echo "readiness: curl -s http://127.0.0.1:$PORT/v1/models"
