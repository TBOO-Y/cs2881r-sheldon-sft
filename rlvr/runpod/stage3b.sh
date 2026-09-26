#!/usr/bin/env bash
# Stage 3b ON the pod (detached, idempotent; log logs/stage3b.log, marker logs/stage3b.stage): staged re-labelling from a merged checkpoint.
#   START=models/rlvr-main-ckpt200-merged [STAGES=3] [STEPS=50] [EXTRA="rlvr/data/extra_deepmath.jsonl,rlvr/data/extra_dapo17k.jsonl,rlvr/data/extra_deepscaler.jsonl"]
#   [CAPS="deepmath=0.3,dapo17k=0.2,deepscaler=0.2"] [BAND=0.125,0.875] [FRONTIER=0.10] [FRONTIER_RELABEL=3000] [LR=2e-5] bash rlvr/runpod/stage3b.sh
# Per stage s: label pool with current model (k=8) -> band schedule -> 50-step LoRA run (constant LR; the LAST stage decays over its last 40%)
#   -> merge -> quick eval. Stop rule: if a stage gains < 1 pt on MATH-500 L3-5 avg@4 AND its band pool < 1500 prompts, stop.
# Needs: the seed adapter merged first (rlvr/merge_adapter.py) and the extra pools built on the laptop (rlvr/data/build_extra.py) and synced.
set -uo pipefail; source "$(dirname "$0")/env.sh"; cd "$PROJ"; R="$PROJ/rlvr/runpod"; LOG="$PROJ/logs/stage3b.log"; ST="$PROJ/logs/stage3b.stage"
START="${START:?merged model dir to start from}"; STAGES="${STAGES:-3}"; STEPS="${STEPS:-50}"; LR="${LR:-2e-5}"
EXTRA="${EXTRA:-rlvr/data/extra_deepmath.jsonl,rlvr/data/extra_dapo17k.jsonl,rlvr/data/extra_deepscaler.jsonl}"; CAPS="${CAPS:-deepmath=0.3,dapo17k=0.2,deepscaler=0.2}"
BAND="${BAND:-0.125,0.875}"; FRONTIER="${FRONTIER:-0.10}"; RUNBASE="${RUNBASE:-rlvr-3b}"
say(){ echo "$(date -u +%FT%TZ) $*" | tee -a "$LOG"; }; stage(){ echo "$1" > "$ST"; say "=== stage $1"; }
l35(){ $PY -c "
import json,glob,sys
fs=sorted(glob.glob('evals/rlvr/$1/checkpoint-*/avg4/math500.summary.json'), key=lambda p:int(p.split('checkpoint-')[1].split('/')[0]))
print(f\"{100*json.load(open(fs[-1])).get('acc_L3_5',0):.2f}\" if fs else 'nan')"; }
say "stage3b start: START=$START stages=$STAGES x $STEPS steps, extras=$EXTRA caps=$CAPS band=$BAND frontier=$FRONTIER"
pgrep -f rlaif/runpod/mirror.sh >/dev/null || { nohup bash "$PROJ/rlaif/runpod/mirror.sh" > /dev/null 2>&1 & say "mirror started"; }
# one combined pool file for labelling (math12k + extras), built once
POOL=rlvr/data/pool_3b.jsonl
[ -s $POOL ] || { cat rlvr/data/math12k.jsonl $(echo "$EXTRA" | tr ',' ' ') > $POOL; say "pool: $(wc -l < $POOL) prompts"; }
CUR="$START"; PREV_L35="nan"
for s in $(seq 1 "$STAGES"); do
  RUN="$RUNBASE-s$s"; TAG="$RUNBASE-s$s"
  stage "$s-label"
  # incremental re-labelling: stage 1 labels the whole pool; later stages re-label only what was not solved (p < 1) last time, with the
  # p == 0 frontier subsampled to FRONTIER_RELABEL prompts (only ~10% x 16 x steps of them are ever drawn). Solved prompts keep their label.
  LPOOL=$POOL
  if [ "$s" != 1 ]; then LPOOL=rlvr/data/pool_$TAG.jsonl; PREV=rlvr/data/passrate_$RUNBASE-s$((s-1)).jsonl
    [ -s $LPOOL ] || $PY - "$POOL" "$PREV" "$LPOOL" "${FRONTIER_RELABEL:-3000}" "$s" <<'PYEOF'
import json, random, sys
pool = [json.loads(l) for l in open(sys.argv[1])]; prev = {r["id"]: r for r in map(json.loads, open(sys.argv[2]))}
keep = [r for r in pool if r["id"] in prev and 0 < prev[r["id"]]["passrate"] < 1]
front = [r for r in pool if r["id"] in prev and prev[r["id"]]["n_correct"] == 0]; random.Random(int(sys.argv[5])).shuffle(front)
keep += front[: int(sys.argv[4])]
with open(sys.argv[3], "w") as f:
    for r in keep: f.write(json.dumps(r, ensure_ascii=False) + "\n")
print(f"re-label pool: {len(keep)} prompts ({len(front)} frontier available, {min(len(front), int(sys.argv[4]))} kept)")
PYEOF
  fi
  [ -s rlvr/data/passrate_$TAG.jsonl ] || TAG=$TAG MODEL=$CUR DATA=$LPOOL K=8 bash "$R/label.sh" 2>&1 | tee -a "$LOG" | tail -4
  [ -s rlvr/data/passrate_$TAG.jsonl ] || { say "labels missing; abort"; exit 2; }
  BANDN=$($PY -c "import json; r=[json.loads(l) for l in open('rlvr/data/passrate_$TAG.jsonl')]; lo,hi=$BAND; print(sum(1 for x in r if lo<=x['passrate']<=hi))")
  say "stage $s: band pool = $BANDN prompts (of $(wc -l < $POOL)); frontier = $($PY -c "import json; print(sum(1 for l in open('rlvr/data/passrate_$TAG.jsonl') if json.loads(l)['n_correct']==0))")"
  DECAY=0; [ "$s" = "$STAGES" ] && DECAY=0.4
  [ -s rlvr/data/schedule_$TAG.jsonl ] || $PY rlvr/data/build_schedule.py --mode band --train rlvr/data/math12k.jsonl --extra "$EXTRA" --passrate rlvr/data/passrate_$TAG.jsonl \
      --steps "$STEPS" --prompts_per_step 16 --G 16 --band "$BAND" --frontier "$FRONTIER" --source_caps "$CAPS" --seed "$s" --out rlvr/data/schedule_$TAG.jsonl 2>&1 | tee -a "$LOG" | tail -9
  stage "$s-train"
  if [ ! -d "runs/$RUN/final_adapter" ]; then
    RUN=$RUN MODE=colocate STEPS=$STEPS MODEL=$CUR SCHEDULE=rlvr/data/schedule_$TAG.jsonl LENPEN=dapo LR=$LR TOTAL=$STEPS SAVE=25 EXTRA="--wsd_decay_frac $DECAY --warmup_steps 5" bash "$R/run_rlvr.sh" 2>&1 | tee -a "$LOG" | tail -2
    waitpid "$(cat logs/$RUN.pid)"
  fi
  [ -f "models/$RUN-merged/config.json" ] || { say "stage $s: no merged model (see logs/$RUN.log); abort"; exit 3; }
  stage "$s-eval"
  CK=$(ls -d runs/$RUN/checkpoint-* | sort -V | tail -1)
  NAME=$RUN/$(basename $CK) MODEL=$CUR ADAPTER=$CK bash "$R/eval.sh"; waitpid "$(cat logs/eval-${RUN}_$(basename $CK).pid)"
  L35=$(l35 $RUN); say "stage $s: MATH-500 L3-5 avg@4 = $L35 (previous $PREV_L35)"
  STOP=$($PY -c "
import math; a=float('$L35'); b=float('$PREV_L35'); n=int('$BANDN')
print(int((not math.isnan(a)) and (not math.isnan(b)) and (a-b) < 1.0 and n < 1500))")
  CUR="$PROJ/models/$RUN-merged"; PREV_L35=$L35
  [ "$STOP" = 1 ] && { say "stop rule hit after stage $s (gain < 1 pt and band < 1500)"; break; }
done
stage final-eval
NAME=$RUNBASE-final MODEL=$CUR SUITE=full bash "$R/eval.sh"; waitpid "$(cat logs/eval-$RUNBASE-final.pid)"
$PY rlvr/summarize_run.py --runs $(for s in $(seq 1 "$STAGES"); do [ -d runs/$RUNBASE-s$s ] && echo -n "$RUNBASE-s$s "; done) --models $RUNBASE-final --ref base --ref rlvr-main --out results/rlvr/$RUNBASE.md 2>&1 | tee -a "$LOG"
stage done; say "STAGE 3B DONE: results/rlvr/$RUNBASE.md ; final model $CUR"
