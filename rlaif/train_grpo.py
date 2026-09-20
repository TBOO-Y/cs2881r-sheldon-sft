#!/usr/bin/env python3
"""RLAIF stage: GRPO on the SFT touch-up model with the gated multi-term reward (rlaif/reward/reward.py).

Launch on Athena via sft/remote_launch.sh (it exports proxy / HF cache / W&B env and picks a free GPU):
  ssh athena 'RUN_NAME=grpo-v4-r1 GPU=auto MODE=detached SCRIPT=rlaif/train_grpo.py EXTRA="--model /data/agastyas/cs2881r/models/<touchup>-merged" bash -s' < sft/remote_launch.sh
The reward needs OPENAI_API_KEY (or OPENAI_API_KEY_2) in $HOME/.config/cs2881r/env on the cluster and https_proxy set.
Verified against TRL 1.13.0 (athena, 2026-09-20): custom reward funcs are called as f(prompts=, completions=, completion_ids=, **dataset_columns, trainer_state=, log_extra=, log_metric=).
"""
import argparse, json, os, random, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
assert os.environ.get("CUDA_VISIBLE_DEVICES"), "set CUDA_VISIBLE_DEVICES in the launcher (never inside the .py)"
import torch
from datasets import Dataset
from peft import LoraConfig
from transformers import AutoTokenizer, AutoModelForCausalLM
from trl import GRPOConfig, GRPOTrainer
from reward.reward import GroupReward, RewardConfig

DEFAULT_SYSTEM = "You are Qwen, created by Alibaba Cloud. You are a helpful assistant."   # identical to sft/train_sft.py

def build_dataset(path, limit=None, seed=0):
    rows = [json.loads(l) for l in open(path)]
    random.Random(seed).shuffle(rows)
    if limit: rows = rows[:limit]
    recs = []
    for r in rows:
        msgs = [{"role": "system", "content": DEFAULT_SYSTEM}] + [{"role": m["role"], "content": m["content"]} for m in r.get("prior", [])] + [{"role": "user", "content": r["prompt"]}]
        recs.append({"prompt": msgs, "prompt_text": r["prompt"], "prior_json": json.dumps(r.get("prior", []), ensure_ascii=False), "kind": r.get("kind") or "", "pid": r["id"], "source": r.get("source", "")})
    return Dataset.from_list(recs)

class RewardFn:
    """Batch-aware reward: groups the step's completions by prompt id and scores each group jointly."""
    __name__ = "sheldon_reward"
    def __init__(self, cfg, max_completion_length):
        self.gr = GroupReward(cfg); self.maxlen = max_completion_length; self.calls = 0
    def __call__(self, prompts, completions, completion_ids=None, prompt_text=None, prior_json=None, kind=None, pid=None, log_metric=None, **kw):
        texts = [c[0]["content"] if isinstance(c, list) else str(c) for c in completions]
        n = len(texts); groups = {}; order = []
        for i in range(n):
            key = pid[i] if pid else i
            if key not in groups:
                groups[key] = {"prompt": prompt_text[i], "prior": json.loads(prior_json[i]) if prior_json and prior_json[i] else None, "kind": kind[i] if kind else None, "completions": [], "finishes": [], "idx": []}; order.append(key)
            g = groups[key]; g["completions"].append(texts[i]); g["idx"].append(i)
            fin = None
            if completion_ids is not None and len(completion_ids[i]) >= self.maxlen: fin = "length"
            g["finishes"].append(fin)
        glist = [groups[k] for k in order]
        rewards, metrics = self.gr.score_step(glist)
        out = [0.0] * n
        for g, rw in zip(glist, rewards):
            for i, r in zip(g["idx"], rw): out[i] = float(r)
        self.calls += 1
        if log_metric is not None:
            for k, v in metrics.items():
                try: log_metric("sheldon/" + k, float(v))
                except Exception: pass
        if self.calls % 10 == 1:
            print(f"[reward] call {self.calls}: n={n} groups={len(glist)} mean={sum(out)/max(1,n):.3f} judge_calls={metrics['judge_calls']} cost_total=${metrics['judge_cost_usd_total']:.2f} secs={metrics['reward_seconds']:.1f}", flush=True)
        return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, help="merged bf16 model dir (the SFT touch-up)")
    ap.add_argument("--prompts", default="/data/agastyas/cs2881r/data/rl_prompts.jsonl")
    ap.add_argument("--out_root", default="/data/agastyas/cs2881r/runs"); ap.add_argument("--merged_root", default="/data/agastyas/cs2881r/models")
    ap.add_argument("--run_name", default=None); ap.add_argument("--wandb_project", default="cs2881r-sheldon")
    ap.add_argument("--judge_model", default="gpt-4.1-nano"); ap.add_argument("--budget_usd", type=float, default=80.0)
    ap.add_argument("--num_generations", type=int, default=8); ap.add_argument("--prompts_per_step", type=int, default=16)
    ap.add_argument("--per_device_bs", type=int, default=16, help="completions per micro-batch")
    ap.add_argument("--max_completion_length", type=int, default=400)
    ap.add_argument("--temperature", type=float, default=0.8); ap.add_argument("--top_p", type=float, default=0.95); ap.add_argument("--repetition_penalty", type=float, default=1.05)
    ap.add_argument("--lr", type=float, default=1e-6); ap.add_argument("--beta", type=float, default=0.04); ap.add_argument("--epsilon", type=float, default=0.2)
    ap.add_argument("--loss_type", default="dapo"); ap.add_argument("--scale_rewards", default="group"); ap.add_argument("--num_iterations", type=int, default=1)
    ap.add_argument("--max_steps", type=int, default=300); ap.add_argument("--save_steps", type=int, default=25); ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--lora_r", type=int, default=32); ap.add_argument("--lora_alpha", type=int, default=64)
    ap.add_argument("--use_vllm", action="store_true"); ap.add_argument("--vllm_gpu_mem", type=float, default=0.35)
    ap.add_argument("--w_persona", type=float, default=2.0); ap.add_argument("--w_form", type=float, default=1.0); ap.add_argument("--ring", type=int, default=2)
    ap.add_argument("--coherence_factor", type=float, default=0.5); ap.add_argument("--seed", type=int, default=42); ap.add_argument("--no_merge", action="store_true")
    a = ap.parse_args()
    run_name = a.run_name or f"grpo-{Path(a.model).name}-{time.strftime('%m%d-%H%M')}"
    out_dir = Path(a.out_root) / run_name; out_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("OAI_CACHE_DIR", "/data/agastyas/cs2881r/oai_cache")
    import wandb
    run = wandb.init(project=a.wandb_project, name=run_name, config=vars(a), dir=os.environ.get("WANDB_DIR"))
    ds = build_dataset(a.prompts, a.limit, a.seed); print("prompts:", len(ds), flush=True)
    tok = AutoTokenizer.from_pretrained(a.model); tok.padding_side = "left"
    if tok.pad_token is None: tok.pad_token = tok.eos_token
    assert a.prompts_per_step * a.num_generations % a.per_device_bs == 0, "prompts_per_step*num_generations must be a multiple of per_device_bs"
    grad_accum = a.prompts_per_step * a.num_generations // a.per_device_bs
    cfg = GRPOConfig(
        output_dir=str(out_dir), run_name=run_name, report_to=["wandb"], logging_steps=1, save_steps=a.save_steps, save_total_limit=6,
        learning_rate=a.lr, lr_scheduler_type="constant_with_warmup", warmup_steps=10, max_steps=a.max_steps, seed=a.seed,
        per_device_train_batch_size=a.per_device_bs, gradient_accumulation_steps=grad_accum, num_generations=a.num_generations,
        max_completion_length=a.max_completion_length, temperature=a.temperature, top_p=a.top_p, repetition_penalty=a.repetition_penalty,
        beta=a.beta, epsilon=a.epsilon, loss_type=a.loss_type, scale_rewards=a.scale_rewards, num_iterations=a.num_iterations, mask_truncated_completions=False,
        bf16=True, gradient_checkpointing=True, gradient_checkpointing_kwargs={"use_reentrant": False}, remove_unused_columns=False,
        log_completions=True, num_completions_to_print=2, use_vllm=a.use_vllm, **({"vllm_mode": "colocate", "vllm_gpu_memory_utilization": a.vllm_gpu_mem} if a.use_vllm else {}),
    )
    peft_cfg = LoraConfig(r=a.lora_r, lora_alpha=a.lora_alpha, lora_dropout=0.0, bias="none", task_type="CAUSAL_LM",
                          target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"])
    rcfg = RewardConfig(judge_model=a.judge_model, w_persona=a.w_persona, w_form=a.w_form, ring=a.ring, coherence_factor=a.coherence_factor, budget_usd=a.budget_usd, seed=a.seed)
    reward_fn = RewardFn(rcfg, a.max_completion_length)
    model = AutoModelForCausalLM.from_pretrained(a.model, dtype=torch.bfloat16, attn_implementation="sdpa")
    torch.backends.cuda.enable_cudnn_sdp(False)          # cuDNN SDPA backward gave NaN grads on padded batches (athena, torch 2.12)
    trainer = GRPOTrainer(model=model, reward_funcs=[reward_fn], args=cfg, train_dataset=ds, processing_class=tok, peft_config=peft_cfg)
    trainer.train()
    trainer.save_model(str(out_dir / "final_adapter"))
    if not a.no_merge:
        from peft import PeftModel
        base = AutoModelForCausalLM.from_pretrained(a.model, dtype=torch.bfloat16)
        merged = PeftModel.from_pretrained(base, str(out_dir / "final_adapter")).merge_and_unload()
        mdir = Path(a.merged_root) / f"{run_name}-merged"; merged.save_pretrained(str(mdir), safe_serialization=True); tok.save_pretrained(str(mdir)); print("merged ->", mdir, flush=True)
    from judge.oai import usage_summary; print("judge usage:", usage_summary(), flush=True); run.finish()

if __name__ == "__main__": main()
