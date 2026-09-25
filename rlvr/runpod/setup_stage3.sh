#!/usr/bin/env bash
# One-time stage-3 node setup ON the pod, after rlaif/runpod/setup_node.sh (venv + base model): verifier, seed + reference models from the Hub, sanity checks.
#   bash /root/cs2881r/rlvr/runpod/setup_stage3.sh
set -euo pipefail; source "$(dirname "$0")/env.sh"; cd "$PROJ"
export PATH="$HOME/.local/bin:$PATH"
uv pip install --python "$PY" -q math-verify
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
