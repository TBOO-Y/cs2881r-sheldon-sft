#!/usr/bin/env bash
# Step 2: both layouts for 3 steps at 4 prompts x 4 generations (level-based schedule, no labels needed), through checkpoint + export.
set -euo pipefail; source "$(dirname "$0")/env.sh"; cd "$PROJ"
[ -s rlvr/data/schedule_smoke.jsonl ] || $PY rlvr/data/build_schedule.py --train rlvr/data/math12k.jsonl --by_level --steps 8 --prompts_per_step 4 --G 4 --out rlvr/data/schedule_smoke.jsonl
mismatch() { $PY - "$1" <<'PYEOF'
import json, sys, glob
p = sorted(glob.glob(f"runs/{sys.argv[1]}/checkpoint-*/trainer_state.json"))[-1]
h = [x for x in json.load(open(p))["log_history"] if "sampling/sampling_logp_difference/mean" in x]
print(f"[mismatch] {sys.argv[1]}: trainer-vs-vLLM |dlogp| mean per step = " + ", ".join(f"{x['sampling/sampling_logp_difference/mean']:.4f}" for x in h) +
      " ; IS ratio mean = " + ", ".join(f"{x['sampling/importance_sampling_ratio/mean']:.3f}" for x in h) + " ; s/step = " + ", ".join(f"{x.get('step_time', 0):.0f}" for x in h))
PYEOF
}
for DT in bfloat16 float32; do                      # full-FT smoke twice: bf16 sampler vs fp32 sampler -> measured train/rollout mismatch and step time
  MODEL=$SEED_MODEL GPUS=0 DTYPE=$DT bash rlvr/runpod/serve_vllm.sh
  RUN=smoke-full-$DT MODE=server STEPS=3 SCHEDULE=rlvr/data/schedule_smoke.jsonl PROMPTS=4 GENS=4 PDB=2 MAXLEN=512 SAVE=3 TOTAL=3 EXTRA="--report_to none --drift_every 1" bash rlvr/runpod/run_rlvr.sh
  waitpid "$(cat logs/smoke-full-$DT.pid)"; vllm_stop
  { grep -E "\[run\]|\[optim\]|\[time\]|\[drift\]|merged ->|Traceback|Error" logs/smoke-full-$DT.log || true; } | tail -8; mismatch smoke-full-$DT
done
RUN=smoke-lora MODE=colocate STEPS=3 SCHEDULE=rlvr/data/schedule_smoke.jsonl PROMPTS=4 GENS=4 PDB=2 MAXLEN=512 SAVE=2 TOTAL=3 OPT=muonp EXTRA="--report_to none --drift_every 1" bash rlvr/runpod/run_rlvr.sh
waitpid "$(cat logs/smoke-lora.pid)"
{ grep -E "\[run\]|\[optim\]|\[time\]|\[drift\]|merged ->|Traceback|Error" logs/smoke-lora.log || true; } | tail -12
mismatch smoke-lora
[ -f models/smoke-full-bfloat16-merged/config.json ] && [ -f models/smoke-full-float32-merged/config.json ] && [ -f models/smoke-lora-merged/config.json ] && echo "smoke: both layouts OK" || echo "smoke: FAILED (see logs/smoke-*.log)"
