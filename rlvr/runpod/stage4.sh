#!/usr/bin/env bash
# Stage 4 ON the pod: combined reward (verifiable math + stage-2 judged persona) from the full-FT RLVR model. Full fine-tune AdamW 2e-6, server layout,
# STEPS steps x (8 math + 8 persona prompts) x 16 completions, 2,048-token cap for both tasks, judge GPT-5.6 Luna via OpenRouter (ring 1, both orders,
# ~$0.3/step; per-rank spend cap JUDGE_BUDGET). Then: math quick suite per checkpoint, full suite + persona eval of the final model, tables.
#   [START=models/rlvr-3c-fullft-merged] [STEPS=80] [LR=2e-6] [RUN=rlvr-4-combined] [JUDGE_BUDGET=20] [HOURS=4] bash rlvr/runpod/stage4.sh
set -uo pipefail; source "$(dirname "$0")/env.sh"; cd "$PROJ"; R="$PROJ/rlvr/runpod"; LOG="$PROJ/logs/stage4.log"; ST="$PROJ/logs/stage4.stage"
START="${START:-$PROJ/models/rlvr-3c-fullft-merged}"; STEPS="${STEPS:-80}"; LR="${LR:-2e-6}"; RUN="${RUN:-rlvr-4-combined}"; JUDGE_BUDGET="${JUDGE_BUDGET:-20}"; HOURS="${HOURS:-4}"
SCHED="${SCHED:-rlvr/data/schedule_stage4.jsonl}"
say(){ echo "$(date -u +%FT%TZ) $*" | tee -a "$LOG"; }; stage(){ echo "$1" > "$ST"; say "=== stage $1"; }
[ -n "${OPENROUTER_API_KEY:-}" ] || { say "OPENROUTER_API_KEY missing in $PROJ/.env; abort"; exit 2; }
[ -s "$SCHED" ] || { say "schedule $SCHED missing (build on the laptop: rlvr/data/build_combined_schedule.py); abort"; exit 2; }
say "stage4 start: START=$START steps=$STEPS lr=$LR judge=$JUDGE_MODEL/$JUDGE_REASONING budget/rank=$JUDGE_BUDGET"
pgrep -f rlaif/runpod/mirror.sh >/dev/null || { nohup bash "$PROJ/rlaif/runpod/mirror.sh" > /dev/null 2>&1 & say "mirror started"; }
stage judge-check
$PY rlaif/judge/oai.py "$JUDGE_MODEL" 2>&1 | tail -2 | tee -a "$LOG"
stage train
if [ ! -d "runs/$RUN/final" ]; then
  MODEL=$START bash "$R/serve_vllm.sh" 2>&1 | tee -a "$LOG" | tail -1
  RUN=$RUN MODE=server LORA=0 STEPS=$STEPS MODEL=$START SCHEDULE=$SCHED LENPEN=dapo LR=$LR TOTAL=$STEPS SAVE=20 HOURS=$HOURS \
    EXTRA="--wsd_decay_frac 0.2 --warmup_steps 5 --combined 1 --judge_budget_usd $JUDGE_BUDGET --judge_workers 64 --ring 1 --pair_orders 2" bash "$R/run_rlvr.sh" 2>&1 | tee -a "$LOG" | tail -2
  waitpid "$(cat logs/$RUN.pid)"; vllm_stop
fi
[ -f "models/$RUN-merged/config.json" ] || { say "no merged model (see logs/$RUN.log); abort"; exit 3; }
stage eval
RUN=$RUN BASE=$START bash "$R/follow_eval.sh"; waitpid "$(cat logs/follow-$RUN.pid)"
NAME=$RUN MODEL=$PROJ/models/$RUN-merged GPU=1 SUITE=full bash "$R/eval.sh"; waitpid "$(cat logs/eval-$RUN.pid)"
stage persona
NAME=$RUN MODEL=$PROJ/models/$RUN-merged GPU=0 bash "$R/persona_eval.sh" 2>&1 | tee -a "$LOG" | tail -3
stage table
$PY rlvr/summarize_run.py --runs $RUN --models $RUN --ref rlvr-3c-fullft --ref rlvr-main --ref base --out results/rlvr/$RUN.md 2>&1 | tee -a "$LOG" | tail -12
stage done; say "STAGE 4 DONE: results/rlvr/$RUN.md, results/rlvr/persona_$RUN.md"
