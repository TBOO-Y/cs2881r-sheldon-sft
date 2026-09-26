#!/usr/bin/env bash
# One-time stage-3 node setup ON the pod, after rlaif/runpod/setup_node.sh (venv + base model): verifier, seed + reference models from the Hub, sanity checks.
#   bash /root/cs2881r/rlvr/runpod/setup_stage3.sh
set -euo pipefail; source "$(dirname "$0")/env.sh"; cd "$PROJ"
export PATH="$HOME/.local/bin:$PATH"
uv pip install --python "$PY" -q math-verify ninja
# the RunPod images seen so far have a CUDA 12.8 driver while PyPI torch 2.13 is a CUDA 13 build ("driver too old"): switch torch + vLLM to the cu129 builds
DRV=$(nvidia-smi | grep -o "CUDA Version: [0-9.]*" | grep -o "[0-9.]*$" | cut -d. -f1)
if [ "${DRV:-13}" -lt 13 ] && $PY -c "import torch; import sys; sys.exit(0 if torch.version.cuda and torch.version.cuda.startswith('13') else 1)" 2>/dev/null; then
  echo "driver CUDA $DRV.x with a cu13 torch: reinstalling cu129 builds (~10 min)"
  uv pip install --python "$PY" --index-strategy unsafe-best-match --extra-index-url https://download.pytorch.org/whl/cu129 \
    "vllm @ https://github.com/vllm-project/vllm/releases/download/v0.29.0/vllm-0.29.0+cu129-cp38-abi3-manylinux_2_28_x86_64.whl" torch==2.13.0 torchvision==0.28.0 torchaudio==2.11.0
  uv pip install --python "$PY" --reinstall-package torch --reinstall-package torchvision --reinstall-package torchaudio --index-url https://download.pytorch.org/whl/cu129 torch==2.13.0 torchvision==0.28.0 torchaudio==2.11.0
fi
# restore stage-2/3 models and the rlvr-main run from the persistent volume when present (local copy is much faster than the Hub)
for m in grpo-v2-merged sft-touchup-v4-merged rlvr-main-merged; do [ -f models/$m/config.json ] || { [ -d "$BACKUP/models/$m" ] && cp -r "$BACKUP/models/$m" models/ && echo "restored models/$m from $BACKUP"; }; done
[ -d runs/rlvr-main/checkpoint-200 ] || { [ -d "$BACKUP/runs/rlvr-main" ] && mkdir -p runs && cp -r "$BACKUP/runs/rlvr-main" runs/ && echo "restored runs/rlvr-main from $BACKUP"; }
HF="$(dirname "$PY")/hf"; [ -x "$HF" ] || HF="$(dirname "$PY")/huggingface-cli"
[ -f models/grpo-v2-merged/config.json ]        || $HF download tbooy/Qwen2.5-3B-Instruct-Sheldon-RLAIF-grpo-v2   --local-dir models/grpo-v2-merged --quiet
[ -f models/sft-touchup-v4-merged/config.json ] || $HF download tbooy/Qwen2.5-3B-Instruct-Sheldon-SFT-touchup-v4 --local-dir models/sft-touchup-v4-merged --quiet
$HF download Qwen/Qwen2.5-3B-Instruct --quiet > /dev/null && echo "base model cached"
[ -n "$TRL_BIN" ] && echo "trl CLI: $TRL_BIN" || { echo "trl CLI missing"; exit 2; }
$PY - <<'PYEOF'
import importlib, torch
for m in ["torch", "transformers", "peft", "trl", "vllm", "accelerate", "math_verify", "datasets"]:
    mod = importlib.import_module(m); print(f"{m:13s} {getattr(mod, '__version__', '?')}")
import trl; assert trl.__version__.startswith("1.13"), "rlvr/trainer.py is written against TRL 1.13"
print("cuda", torch.version.cuda, "devices", torch.cuda.device_count(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else "")
PYEOF
$PY rlvr/grader.py --selftest | tail -1
for f in rlvr/data/math12k.jsonl rlvr/data/math500.jsonl rlvr/data/aime24.jsonl rlvr/data/aime25.jsonl rlvr/data/aime26.jsonl data/gsm8k_test.jsonl; do
  [ -s "$f" ] && echo "ok   $f ($(wc -l < $f) rows)" || echo "MISSING $f (run rlvr/data/build_math.py on the laptop, then sync)"; done
nvidia-smi --query-gpu=index,name,memory.used,memory.total --format=csv,noheader
echo "stage-3 setup done: seed $SEED_MODEL"
