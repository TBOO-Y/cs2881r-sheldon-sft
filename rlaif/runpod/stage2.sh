#!/usr/bin/env bash
# Stage-2 sequencer ON the pod (detached, idempotent, logs to $PROJ/logs/stage2.log):
#   1. touch-up SFT on GPU 0            2. baselines in parallel: v3b eval (GPU 1), base GSM8K (GPU 3)
#   3. when the touch-up has merged: eval it (GPU 1) and run the GRPO smoke test (GPU 2)
#   4. if the smoke test passed: full GRPO (GPU 2) with follow_eval.sh scoring every checkpoint on GSM8K + persona (GPU 4)
#   5. eval the merged GRPO model (GPU 1) and print the per-checkpoint table (summarize_run.py)
#   nohup bash rlaif/runpod/stage2.sh > /dev/null 2>&1 &     then:  tail -f $PROJ/logs/stage2.log
set -uo pipefail; source "$(dirname "$0")/env.sh"; cd "$PROJ"; R="$PROJ/rlaif/runpod"
TOUCH="${TOUCH:-sft-touchup-v4}"; GRPO="${GRPO:-grpo-v1}"; LOG="$PROJ/logs/stage2.log"
say(){ echo "$(date -u +%FT%TZ) $*" | tee -a "$LOG"; }
waitpid(){ while kill -0 "$1" 2>/dev/null; do sleep 30; done; }
say "stage2 start (touch-up=$TOUCH grpo=$GRPO judge=$JUDGE_MODEL/$JUDGE_REASONING)"
[ -n "${OPENROUTER_API_KEY:-}" ] || { say "OPENROUTER_API_KEY missing in $PROJ/.env; abort"; exit 2; }
pgrep -f rlaif/runpod/mirror.sh >/dev/null || { nohup bash "$R/mirror.sh" > /dev/null 2>&1 & say "mirror to $BACKUP started (pid $!)"; }
# 1 + 2
if [ ! -f "models/$TOUCH-merged/config.json" ]; then RUN=$TOUCH GPU=0 bash "$R/run_touchup.sh" | tee -a "$LOG"; TP=$(cat "logs/$TOUCH.pid"); else say "touch-up already merged"; TP=""; fi
NAME=v3b MODEL="$PROJ/models/sft-lora-r32-mixAB-v3b-merged" GPU=1 bash "$R/run_eval.sh" | tee -a "$LOG"; VP=$(cat logs/eval-v3b.pid)
NAME=base MODEL=Qwen/Qwen2.5-3B-Instruct GPU=3 TASKS="gsm8k short" bash "$R/run_eval.sh" | tee -a "$LOG"
[ -n "$TP" ] && { waitpid "$TP"; say "touch-up exited; tail: $(tail -3 logs/$TOUCH.log | tr '\n' ' ')"; }
[ -f "models/$TOUCH-merged/config.json" ] || { say "no merged touch-up model; abort"; exit 3; }
# 3
waitpid "$VP"; NAME=$TOUCH MODEL="$PROJ/models/$TOUCH-merged" GPU=1 bash "$R/run_eval.sh" | tee -a "$LOG"; EP=$(cat "logs/eval-$TOUCH.pid")
MODEL="$PROJ/models/$TOUCH-merged" GPU=2 RUN=grpo-smoke bash "$R/smoke_grpo.sh" | tee -a "$LOG"; waitpid "$(cat logs/grpo-smoke.pid)"
if grep -q "judge usage:" logs/grpo-smoke.log && [ -d runs/grpo-smoke/checkpoint-2 ]; then say "smoke test passed: $(grep -m1 '\[reward\] call' logs/grpo-smoke.log)"; else say "smoke test FAILED; tail: $(tail -5 logs/grpo-smoke.log | tr '\n' ' ')"; exit 4; fi
# 4
HOURS="${HOURS:-4}" MODEL="$PROJ/models/$TOUCH-merged" GPU=2 RUN=$GRPO bash "$R/run_grpo.sh" | tee -a "$LOG"
RUN=$GRPO BASE="$PROJ/models/$TOUCH-merged" GPU=4 bash "$R/follow_eval.sh" | tee -a "$LOG"
waitpid "$(cat "logs/$GRPO.pid")"
say "GRPO exited; tail: $(tail -3 logs/$GRPO.log | tr '\n' ' ')"
[ -f "models/$GRPO-merged/config.json" ] || { say "no merged GRPO model; abort"; exit 5; }
# 5
waitpid "$EP"; NAME=$GRPO MODEL="$PROJ/models/$GRPO-merged" GPU=1 bash "$R/run_eval.sh" | tee -a "$LOG"; waitpid "$(cat "logs/eval-$GRPO.pid")"
waitpid "$(cat "logs/follow-$GRPO.pid")"
$PY rlaif/summarize_run.py --run "$GRPO" --ref "$TOUCH" --ref v3b --ref base --root "$PROJ" | tee -a "$LOG"
say "stage2 done: $(cat evals/gsm8k/$GRPO/final.jsonl.summary.json 2>/dev/null | tr -d '\n')"
