#!/usr/bin/env bash
# One RLVR run ON the pod (detached). Layouts:
#   MODE=server   (full FT): serve_vllm.sh must be running on GPU 0; training DDP on GPUS=3,4,5,6 (4 ranks); default LR 1e-6
#   MODE=colocate (LoRA)   : a vLLM engine inside every rank; GPUS=0,...,7 (8 ranks); default LR 2e-5
#   RUN=pilot-full-adamw MODE=server STEPS=20 [LORA=0|1] [OPT=adamw|muon|muonp] [LR=...] [SCHEDULE=rlvr/data/schedule_main.jsonl] [PROMPTS=16] [GENS=16] [PDB=4]
#     [MAXLEN=2048] [LENPEN=none|dapo] [SAVE=25] [HOURS=0] [TOTAL=200 (WSD layout; pilots keep 200)] [EXTRA="--report_to none"] bash rlvr/runpod/run_rlvr.sh
set -euo pipefail; source "$(dirname "$0")/env.sh"; cd "$PROJ"
RUN="${RUN:?}"; MODE="${MODE:-server}"; STEPS="${STEPS:-200}"; MODEL="${MODEL:-$SEED_MODEL}"; SCHEDULE="${SCHEDULE:-rlvr/data/schedule_main.jsonl}"
if [ "$MODE" = server ]; then GPUS="${GPUS:-3,4,5,6}"; LORA="${LORA:-0}"; LR="${LR:-1e-6}"; else GPUS="${GPUS:-0,1,2,3,4,5,6,7}"; LORA="${LORA:-1}"; LR="${LR:-2e-5}"; fi
NP=$(echo "$GPUS" | tr ',' '\n' | wc -l)
[ "$MODE" = server ] && vllm_wait 60
launch "$RUN" "$GPUS" $ACCEL --num_processes "$NP" --main_process_port "$ACCEL_PORT" --mixed_precision no rlvr/train_rlvr.py \
  --model "$MODEL" --schedule "$SCHEDULE" --run_name "$RUN" --max_steps "$STEPS" --lora "$LORA" --optimizer "${OPT:-adamw}" --lr "$LR" \
  --prompts_per_step "${PROMPTS:-16}" --num_generations "${GENS:-16}" --per_device_bs "${PDB:-4}" --max_completion_length "${MAXLEN:-2048}" \
  --vllm_mode "$MODE" --vllm_server_base_url "$VLLM_URL" --save_steps "${SAVE:-25}" --time_budget_h "${HOURS:-0}" --length_penalty "${LENPEN:-none}" --schedule_total_steps "${TOTAL:-200}" ${EXTRA:-}
echo "follow: tail -f $PROJ/logs/$RUN.log ; W&B project $WANDB_PROJECT run $RUN ; checkpoints $PROJ/runs/$RUN"
