#!/usr/bin/env python3
"""Stage 3 (RLVR): CISPO on competition math with a verifiable reward. Semantics in rlvr/PLAN.md, overrides in rlvr/trainer.py.

Launch on the pod with rlvr/runpod/run_rlvr.sh (accelerate DDP; sets CUDA_VISIBLE_DEVICES, $PROJ, W&B env). Two layouts:
  server   : full fine-tune; generation on a separate `trl vllm-serve` (rlvr/runpod/serve_vllm.sh), training on the DDP ranks
  colocate : LoRA; every rank runs its own vLLM engine (sleeps during the update) and trains
The prompt order is fixed by --schedule (rlvr/data/build_schedule.py): shuffle_dataset=False, one pass, max_steps <= len/prompts_per_step.
Batch geometry: generation_batch_size = prompts_per_step * num_generations = per_device_bs * num_processes * grad_accum (one optimizer
step per generation batch, num_iterations=1).
"""
import argparse, json, os, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE.parent))
PROJ = Path(os.environ.get("PROJ", str(HERE.parent)))
assert os.environ.get("CUDA_VISIBLE_DEVICES") or os.environ.get("RLVR_CPU_DRYRUN"), "set CUDA_VISIBLE_DEVICES in the launcher"
import torch
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM
from trl import GRPOConfig
from rlvr.reward import MathReward
from rlvr.trainer import RLVRTrainer, RLVRCallback
import logging
class _DropUnscorableWarning(logging.Filter):            # a None reward (= masked truncation) is intended here, TRL warns about it once per step with the full completion text
    def filter(self, rec): return "All reward functions returned None" not in rec.getMessage()
logging.getLogger("trl.trainer.grpo_trainer").addFilter(_DropUnscorableWarning())

DEFAULT_SYSTEM = "You are Qwen, created by Alibaba Cloud. You are a helpful assistant."          # identical to every earlier stage
SUFFIX = "\nPlease reason step by step, and put your final answer within \\boxed{}."               # identical to sft/eval_gsm8k.py

def build_dataset(path, limit=None):
    rows = [json.loads(l) for l in open(path)]
    if limit: rows = rows[:limit]
    recs = [{"prompt": [{"role": "system", "content": DEFAULT_SYSTEM}, {"role": "user", "content": r["problem"] + SUFFIX}],
             "answer": str(r["answer"]), "pid": str(r["id"]), "level": int(r.get("level") or 0), "bucket": r.get("bucket", ""), "passrate": float(r.get("passrate", -1))} for r in rows]
    return Dataset.from_list(recs)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True); ap.add_argument("--schedule", required=True, help="ordered prompt list from build_schedule.py")
    ap.add_argument("--run_name", required=True); ap.add_argument("--out_root", default=str(PROJ / "runs")); ap.add_argument("--merged_root", default=str(PROJ / "models"))
    ap.add_argument("--wandb_project", default="cs2881r-sheldon"); ap.add_argument("--report_to", default="wandb")
    # parameters trained
    ap.add_argument("--lora", type=int, default=0); ap.add_argument("--lora_r", type=int, default=32); ap.add_argument("--lora_alpha", type=int, default=64)
    # batch geometry / lengths
    ap.add_argument("--prompts_per_step", type=int, default=16); ap.add_argument("--num_generations", type=int, default=16)
    ap.add_argument("--per_device_bs", type=int, default=4, help="completions per micro-batch per GPU")
    ap.add_argument("--max_completion_length", type=int, default=2048);
    ap.add_argument("--temperature", type=float, default=1.0); ap.add_argument("--top_p", type=float, default=1.0)
    # loss
    ap.add_argument("--loss", default="cispo", choices=["cispo", "dapo"]); ap.add_argument("--eps_high", type=float, default=5.0, help="CISPO: absolute IS cap (ScaleRL eps_max); DAPO: 1+eps_high")
    ap.add_argument("--eps_low", type=float, default=0.2); ap.add_argument("--scale_rewards", default="group", choices=["group", "batch", "none"])
    ap.add_argument("--aggregation", default="prompt", choices=["prompt", "batch"]); ap.add_argument("--beta", type=float, default=0.0)
    ap.add_argument("--cast_lm_head_fp32", type=int, default=1, help="compute the LM-head matmul and logits in fp32 on the trainer side (both arms; our own patch, TRL's flag is never used because it crashes on PEFT models)")
    # reward
    ap.add_argument("--length_penalty", default="none", choices=["none", "dapo"]); ap.add_argument("--l_cache", type=int, default=512)
    ap.add_argument("--grade_workers", type=int, default=8, help="grading processes PER RANK")
    # optimisation
    ap.add_argument("--optimizer", default="adamw", choices=["adamw", "muon", "muonp"]); ap.add_argument("--lr", type=float, default=1e-6)
    ap.add_argument("--weight_decay", type=float, default=0.01); ap.add_argument("--adam_beta2", type=float, default=0.95); ap.add_argument("--adam_eps", type=float, default=1e-15)
    ap.add_argument("--muon_momentum", type=float, default=0.95); ap.add_argument("--muon_nesterov", type=int, default=1)
    ap.add_argument("--max_steps", type=int, default=200); ap.add_argument("--warmup_steps", type=int, default=10)
    ap.add_argument("--schedule_total_steps", type=int, default=0, help="WSD is laid out for this many steps (0 = max_steps); pilots pass the main run's 200 so they stay in the warm-up/stable phase")
    ap.add_argument("--wsd_decay_frac", type=float, default=0.2); ap.add_argument("--min_lr_ratio", type=float, default=0.1)
    ap.add_argument("--max_grad_norm", type=float, default=1.0); ap.add_argument("--seed", type=int, default=42)
    # generation backend
    ap.add_argument("--vllm_mode", default="server", choices=["server", "colocate", "none"], help="none = HF generate (CPU dry runs only)"); ap.add_argument("--vllm_server_base_url", default="http://localhost:8000")
    ap.add_argument("--vllm_gpu_mem", type=float, default=0.45); ap.add_argument("--vllm_max_model_len", type=int, default=4096)
    # bookkeeping
    ap.add_argument("--save_steps", type=int, default=25); ap.add_argument("--time_budget_h", type=float, default=0.0); ap.add_argument("--drift_every", type=int, default=25)
    ap.add_argument("--limit", type=int, default=None); ap.add_argument("--no_merge", action="store_true"); ap.add_argument("--bf16", type=int, default=1)
    a = ap.parse_args()
    import math_verify  # noqa: F401  -- a missing verifier would otherwise silently grade every symbolic answer as wrong
    cast_head = bool(a.cast_lm_head_fp32)
    total_steps = a.schedule_total_steps or a.max_steps
    assert total_steps >= a.max_steps, "--schedule_total_steps must be >= --max_steps"

    out_dir = Path(a.out_root) / a.run_name; out_dir.mkdir(parents=True, exist_ok=True)
    ds = build_dataset(a.schedule, a.limit)
    n_proc = int(os.environ.get("WORLD_SIZE", "1"))
    gen_bs = a.prompts_per_step * a.num_generations
    assert gen_bs % (a.per_device_bs * n_proc) == 0, f"generation batch {gen_bs} must be a multiple of per_device_bs*num_processes = {a.per_device_bs}*{n_proc}"
    grad_accum = gen_bs // (a.per_device_bs * n_proc)
    assert (a.per_device_bs * grad_accum) % a.num_generations == 0, "each rank must hold whole prompt groups (per_device_bs * grad_accum must be a multiple of num_generations): the reward fn is called per rank"
    assert a.max_steps * a.prompts_per_step <= len(ds), f"schedule has {len(ds)} prompts but the run needs {a.max_steps * a.prompts_per_step}; rebuild the schedule"
    tok = AutoTokenizer.from_pretrained(a.model); tok.padding_side = "left"
    if tok.pad_token is None: tok.pad_token = tok.eos_token
    eos_ids = {tok.eos_token_id, tok.pad_token_id} | {tok.convert_tokens_to_ids(t) for t in ("<|im_end|>", "<|endoftext|>") if t in tok.get_vocab()}

    # full fine-tune keeps fp32 master weights (bf16 autocast): at lr 1e-6 a pure-bf16 update is below bf16 resolution. LoRA: bf16 base, fp32 adapter (PEFT default).
    dtype = torch.float32 if (not a.lora and a.bf16) else (torch.bfloat16 if a.bf16 else torch.float32)
    model = AutoModelForCausalLM.from_pretrained(a.model, dtype=dtype, attn_implementation="sdpa")
    if torch.cuda.is_available(): torch.backends.cuda.enable_cudnn_sdp(False)                    # NaN grads on padded batches seen in stage 1
    peft_cfg = None
    if a.lora:
        from peft import LoraConfig
        peft_cfg = LoraConfig(r=a.lora_r, lora_alpha=a.lora_alpha, lora_dropout=0.0, bias="none", task_type="CAUSAL_LM",
                              target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"])
    n_decay = int(round(a.wsd_decay_frac * total_steps))
    vllm_kw = ({"use_vllm": True, "vllm_mode": "server", "vllm_server_base_url": a.vllm_server_base_url, "vllm_server_timeout": 600.0} if a.vllm_mode == "server"
               else {"use_vllm": True, "vllm_mode": "colocate", "vllm_gpu_memory_utilization": a.vllm_gpu_mem, "vllm_max_model_length": a.vllm_max_model_len, "vllm_enable_sleep_mode": True} if a.vllm_mode == "colocate"
               else {"use_vllm": False})
    cfg = GRPOConfig(
        output_dir=str(out_dir), run_name=a.run_name, report_to=[a.report_to] if a.report_to != "none" else [], logging_steps=1,
        save_steps=a.save_steps, save_total_limit=10, save_only_model=True, seed=a.seed, max_steps=a.max_steps,
        learning_rate=a.lr, weight_decay=a.weight_decay, adam_beta1=0.9, adam_beta2=a.adam_beta2, adam_epsilon=a.adam_eps, max_grad_norm=a.max_grad_norm,
        lr_scheduler_type="warmup_stable_decay", warmup_steps=a.warmup_steps, lr_scheduler_kwargs={"num_decay_steps": n_decay, "num_stable_steps": max(0, total_steps - a.warmup_steps - n_decay), "decay_type": "linear", "min_lr_ratio": a.min_lr_ratio},
        per_device_train_batch_size=a.per_device_bs, gradient_accumulation_steps=grad_accum, num_generations=a.num_generations, num_iterations=1,
        max_completion_length=a.max_completion_length, temperature=a.temperature, top_p=a.top_p, repetition_penalty=1.0,
        beta=a.beta, epsilon=a.eps_low, epsilon_high=a.eps_high, loss_type=a.loss, scale_rewards=a.scale_rewards, importance_sampling_level="token",
        mask_truncated_completions=True, cast_lm_head_to_fp32=False, shuffle_dataset=False, vllm_importance_sampling_mode="token_truncate",
        bf16=bool(a.bf16), use_cpu=not torch.cuda.is_available(), gradient_checkpointing=True, gradient_checkpointing_kwargs={"use_reentrant": False}, remove_unused_columns=False,
        log_completions=True, num_completions_to_print=2, **vllm_kw,
    )
    reward_fn = MathReward(eos_ids=eos_ids, max_completion_length=a.max_completion_length, length_penalty=a.length_penalty, l_cache=a.l_cache, workers=a.grade_workers)
    opt_kw = {"momentum": a.muon_momentum, "nesterov": bool(a.muon_nesterov)} if a.optimizer != "adamw" else {}
    trainer = RLVRTrainer(model=model, reward_funcs=[reward_fn], args=cfg, train_dataset=ds, processing_class=tok, peft_config=peft_cfg,
                          aggregation=a.aggregation, optimizer_kind=a.optimizer, optimizer_kwargs=opt_kw, drift_every=a.drift_every, fp32_head=cast_head)
    trainer.add_callback(RLVRCallback(trainer, a.time_budget_h))
    if trainer.accelerator.is_main_process:
        print(f"[run] {a.run_name}: {len(ds)} scheduled prompts, {a.prompts_per_step}x{a.num_generations} per step, {n_proc} ranks x {a.per_device_bs} x {grad_accum} accum, "
              f"{a.loss} eps_high={a.eps_high} scale={a.scale_rewards} agg={a.aggregation} opt={a.optimizer} lr={a.lr} wsd warmup {a.warmup_steps} / decay {n_decay} of {total_steps} steps, fp32_head={cast_head}, "
              f"{'LoRA r%d' % a.lora_r if a.lora else 'full FT fp32-master'} vllm={a.vllm_mode}", flush=True)
        json.dump(vars(a), open(out_dir / "rlvr_args.json", "w"), indent=1)
    trainer.train()
    if trainer.accelerator.is_main_process:
        final = out_dir / ("final_adapter" if a.lora else "final")
        trainer.save_model(str(final)); tok.save_pretrained(str(final))
        if not a.no_merge:
            mdir = Path(a.merged_root) / f"{a.run_name}-merged"
            if a.lora:
                from peft import PeftModel
                base = AutoModelForCausalLM.from_pretrained(a.model, dtype=torch.bfloat16)
                merged = PeftModel.from_pretrained(base, str(final)).merge_and_unload()
            else:
                merged = AutoModelForCausalLM.from_pretrained(str(final), dtype=torch.bfloat16)
            merged.save_pretrained(str(mdir), safe_serialization=True); tok.save_pretrained(str(mdir)); print("merged ->", mdir, flush=True)
    trainer.accelerator.wait_for_everyone()

if __name__ == "__main__": main()
