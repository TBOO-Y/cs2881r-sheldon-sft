#!/usr/bin/env bash
# Stage-3 pilot sequencer ON the pod (detached, idempotent, logs to $PROJ/logs/stage3.log, stage markers in $PROJ/logs/stage3.stage):
#   0 baselines  1 seed pass-rate labels + schedule  2 smoke  3 pilot 1 (LoRA vs full FT)  4 branch (Muon pilots if full FT won by > 3 pts)
#   5 length-penalty pilot on the winner  6 pilot table  7 base-model labels (write-up only).  STOPS there: no main run.
#   nohup bash rlvr/runpod/stage3_pilots.sh > /dev/null 2>&1 &
set -uo pipefail; source "$(dirname "$0")/env.sh"; cd "$PROJ"; R="$PROJ/rlvr/runpod"; LOG="$PROJ/logs/stage3.log"; ST="$PROJ/logs/stage3.stage"
say(){ echo "$(date -u +%FT%TZ) $*" | tee -a "$LOG"; }; stage(){ echo "$1" > "$ST"; say "=== stage $1"; }
l35(){ $PY - "$1" <<'PYEOF'
import json, sys, glob
fs = sorted(glob.glob(f"evals/rlvr/{sys.argv[1]}/checkpoint-*/avg4/math500.summary.json"), key=lambda p: int(p.split("checkpoint-")[1].split("/")[0]))
print(f"{100 * json.load(open(fs[-1])).get('acc_L3_5', 0):.2f}" if fs else "nan")
PYEOF
}
say "stage3 pilots start (seed=$SEED_MODEL, topology server=$SERVER_GPU train=$TRAIN_GPUS eval=$EVAL_GPU)"
pgrep -f rlaif/runpod/mirror.sh >/dev/null || { nohup bash "$PROJ/rlaif/runpod/mirror.sh" > /dev/null 2>&1 & say "mirror to $BACKUP started"; }
stage 0-baselines
[ -s results/rlvr/baselines.md ] || bash "$R/baselines.sh" 2>&1 | tee -a "$LOG" | tail -3
say "baselines: $(cat results/rlvr/baselines.md 2>/dev/null | grep -E '^\| (base|sft-touchup-v4|grpo-v2) ' | tr '\n' ' ')"
stage 1-labels
[ -s rlvr/data/passrate_grpo-v2.jsonl ] || TAG=grpo-v2 MODEL=$SEED_MODEL K=8 bash "$R/label.sh" 2>&1 | tee -a "$LOG" | tail -12
[ -s rlvr/data/schedule_main.jsonl ] || $PY rlvr/data/build_schedule.py --train rlvr/data/math12k.jsonl --passrate rlvr/data/passrate_grpo-v2.jsonl --steps 200 --prompts_per_step 16 --G 16 --out rlvr/data/schedule_main.jsonl 2>&1 | tee -a "$LOG"
[ -s rlvr/data/schedule_main.jsonl ] || { say "no schedule; abort"; exit 2; }
stage 2-smoke
[ -f models/smoke-lora-merged/config.json ] || bash "$R/smoke.sh" 2>&1 | tee -a "$LOG" | tail -15
[ -f models/smoke-lora-merged/config.json ] && [ -f models/smoke-full-bfloat16-merged/config.json ] || { say "smoke failed; abort (see logs/smoke-*.log)"; exit 3; }
stage 3-pilot1
PILOTS="full-adamw lora-adamw" bash "$R/pilot.sh" 2>&1 | tee -a "$LOG" | tail -8
FULL=$(l35 pilot-full-adamw); LORA=$(l35 pilot-lora-adamw); say "pilot 1: MATH-500 L3-5 avg@4  full-adamw=$FULL  lora-adamw=$LORA"
WIN_FULL=$($PY -c "import math; f, l = float('$FULL'), float('$LORA'); print(int(not math.isnan(f) and (math.isnan(l) or f - l > 3.0)))")
stage 4-branch
if [ "$WIN_FULL" = 1 ]; then
  say "full FT wins by > 3 pts: running Muon / Muon^p pilots"
  PILOTS="full-muon full-muonp" bash "$R/pilot.sh" 2>&1 | tee -a "$LOG" | tail -6
  MU=$(l35 pilot-full-muon); MP=$(l35 pilot-full-muonp); say "optimizers: adamw=$FULL muon=$MU muonp=$MP"
  WOPT=$($PY -c "
import math; c = {'adamw': float('$FULL'), 'muon': float('$MU'), 'muonp': float('$MP')}
c = {k: (v if not math.isnan(v) else -1) for k, v in c.items()}; print(max(c, key=c.get))")
  say "winner optimizer: $WOPT"; stage 5-lenpen
  PILOTS="full-lenpen" WINNER_OPT=$WOPT bash "$R/pilot.sh" 2>&1 | tee -a "$LOG" | tail -6
  ALL="pilot-full-adamw pilot-lora-adamw pilot-full-muon pilot-full-muonp pilot-full-lenpen"
else
  say "LoRA wins or ties (< 3 pts): LoRA + AdamW is the candidate; Muon pilots skipped"; stage 5-lenpen
  PILOTS="lora-lenpen" bash "$R/pilot.sh" 2>&1 | tee -a "$LOG" | tail -6
  ALL="pilot-full-adamw pilot-lora-adamw pilot-lora-lenpen"
fi
stage 6-table
$PY rlvr/summarize_run.py --runs $ALL --ref base --ref grpo-v2 --out results/rlvr/pilots.md 2>&1 | tee -a "$LOG"
stage 7-base-labels
[ -s rlvr/data/passrate_base.jsonl ] || TAG=base MODEL=Qwen/Qwen2.5-3B-Instruct K=4 bash "$R/label.sh" 2>&1 | tee -a "$LOG" | tail -3
stage done
say "PILOTS DONE. Main run NOT started (by instruction). Table: results/rlvr/pilots.md"
