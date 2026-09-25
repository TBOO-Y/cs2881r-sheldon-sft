#!/usr/bin/env bash
# Generation server for the full fine-tune layout: `trl vllm-serve` on ONE GPU (TRL 1.13 documents data_parallel_size > 1 as unsupported for dense
# models; a 3B bf16 model + KV cache for 256 x 2.8k tokens fits one H100 at MEM=0.85). The trainer re-syncs weights every step.
#   MODEL=$SEED_MODEL [GPUS=0] [MEM=0.85] [MAXLEN=4096] [DTYPE=bfloat16|float32] bash rlvr/runpod/serve_vllm.sh   # detached; log $PROJ/logs/vllm-serve.log; blocks until healthy
# DTYPE=float32 runs the whole sampler in fp32 (head included; ~2x slower decode, 12 GB weights): the generator-side half of the MiniMax/ScaleRL fix.
set -euo pipefail; source "$(dirname "$0")/env.sh"; cd "$PROJ"
MODEL="${MODEL:-$SEED_MODEL}"; GPUS="${GPUS:-0}"; [ "$(echo "$GPUS" | tr ',' '\n' | wc -l)" = 1 ] || { echo "serve_vllm.sh: one GPU only (dense model: no data parallel)"; exit 2; }
vllm_stop; [ -n "$TRL_BIN" ] || { echo "trl CLI not found next to $PY"; exit 2; }
launch vllm-serve "$GPUS" "$TRL_BIN" vllm-serve --model "$MODEL" --data_parallel_size 1 --tensor_parallel_size 1 \
  --gpu_memory_utilization "${MEM:-0.85}" --max_model_len "${MAXLEN:-4096}" --dtype "${DTYPE:-bfloat16}" --port "$VLLM_PORT" --host 0.0.0.0
vllm_wait 900
