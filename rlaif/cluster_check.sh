#!/usr/bin/env bash
# One-shot environment check on Athena before the RLAIF stage. Run from the Mac (VPN on):
#   ssh agastyas@athena01.ig32s.ruhr-uni-bochum.de 'bash -s' < rlaif/cluster_check.sh
set -u
PY=/data/agastyas/Miniconda3/bin/python; PROJ=/data/agastyas/cs2881r
export https_proxy=http://www-cache.rz.ruhr-uni-bochum.de:80 http_proxy=http://www-cache.rz.ruhr-uni-bochum.de:80 no_proxy=.rub.de,.ruhr-uni-bochum.de,localhost,127.0.0.1,::1
echo "== host: $(hostname)  $(date)"
echo "== GPUs (memory.used MiB) =="; nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader
echo "== compute procs =="; nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv,noheader | head -20
echo "== disk =="; df -h /data | tail -1; du -sh $PROJ 2>/dev/null; du -sh $HOME 2>/dev/null
echo "== project dirs =="; ls $PROJ/models/ 2>/dev/null; ls $PROJ/data/ 2>/dev/null | head -20; ls $PROJ/gens/ 2>/dev/null
echo "== python packages =="
$PY - <<'PYEOF'
import importlib
for m in ["torch","transformers","peft","trl","vllm","openai","wandb","datasets","accelerate","deepspeed","flash_attn","httpx"]:
    try:
        mod=importlib.import_module(m); print(f"{m:14s} {getattr(mod,'__version__','?')}")
    except Exception as e: print(f"{m:14s} MISSING ({type(e).__name__})")
import torch; print("cuda", torch.version.cuda, "devices", torch.cuda.device_count())
PYEOF
echo "== OpenAI reachability through proxy (expect http 401 without a key) =="; curl -sS -m 25 -o /dev/null -w 'http %{http_code}\n' https://api.openai.com/v1/models || echo "curl failed"
echo "== env file keys (names only) =="; [ -f $HOME/.config/cs2881r/env ] && sed -E 's/=.*//' $HOME/.config/cs2881r/env || echo "no env file"
echo "== pip index reachable? =="; $PY -m pip download --no-deps -d /tmp/_pipcheck trl==0.0.1 >/dev/null 2>&1; echo "exit $? (non-zero expected for the fake version; 'No matching distribution' means the index is reachable)"; $PY -m pip download --no-deps -d /tmp/_pipcheck trl==0.0.1 2>&1 | tail -1
