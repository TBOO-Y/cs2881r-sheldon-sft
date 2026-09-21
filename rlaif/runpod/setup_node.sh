#!/usr/bin/env bash
# One-time node setup ON the pod (after sync.sh): Python env, models, sanity checks. ~10 min, mostly downloads.
#   bash /root/cs2881r/rlaif/runpod/setup_node.sh
set -euo pipefail; source "$(dirname "$0")/env.sh"; cd "$PROJ"
command -v uv >/dev/null || (curl -LsSf https://astral.sh/uv/install.sh | sh && export PATH="$HOME/.local/bin:$PATH")
export PATH="$HOME/.local/bin:$PATH"
VENV="${VENV:-/opt/venv}"     # local container disk: fast; rebuilt by this script if the pod restarts
[ -x "$VENV/bin/python" ] || uv venv "$VENV" --python 3.12
uv pip install --python "$VENV/bin/python" -r rlaif/runpod/requirements.txt hf_transfer
PY="$VENV/bin/python"
$PY - <<'PYEOF'
import importlib, torch
for m in ["torch","transformers","peft","trl","vllm","datasets","accelerate","wandb"]:
    mod = importlib.import_module(m); print(f"{m:13s} {getattr(mod,'__version__','?')}")
print("cuda", torch.version.cuda, "devices", torch.cuda.device_count(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else "")
PYEOF
# models: base (for the GSM8K baseline and tokenizer) + the v3b merged SFT model that the touch-up starts from
HF="$VENV/bin/hf"; [ -x "$HF" ] || HF="$VENV/bin/huggingface-cli"
$HF download Qwen/Qwen2.5-3B-Instruct --quiet > /dev/null && echo "base model cached"
[ -f models/sft-lora-r32-mixAB-v3b-merged/config.json ] || $HF download agastyasridharan/Qwen2.5-3B-Instruct-Sheldon-SFT-v3b --local-dir models/sft-lora-r32-mixAB-v3b-merged --quiet
echo "v3b merged: $(ls models/sft-lora-r32-mixAB-v3b-merged | tr '\n' ' ')"
# data present?
for f in rlaif/data/v4/train.jsonl rlaif/data/v4/val.jsonl rlaif/data/rl_prompts.jsonl sft/data_v3b/heldout_prompts.jsonl rlaif/data/short/short_heldout_prompts.jsonl data/gsm8k_test.jsonl; do
  [ -s "$f" ] && echo "ok   $f ($(wc -l < $f) rows)" || echo "MISSING $f (regenerate on the laptop, see README, then sync.sh)"; done
# judge reachable?
[ -n "${OPENROUTER_API_KEY:-}" ] && $PY rlaif/judge/oai.py "$JUDGE_MODEL" || echo "[note] OPENROUTER_API_KEY not set: put it in $PROJ/.env"
$PY - <<'PYEOF'
import sys; sys.path.insert(0, "rlaif")
from reward.reward import GroupReward, RewardConfig
gr = GroupReward(RewardConfig(judge_model="mock"))
r, m = gr.score_step([{"prompt": "hi", "prior": None, "kind": "smalltalk", "completions": ["Hello. I am Sheldon Cooper, and this is my spot.", "hi there friend, hope this helps!", "Hello."], "finishes": [None, None, None]}])
print("reward mock ok:", [round(x, 2) for x in r[0]])
PYEOF
echo "setup done"
