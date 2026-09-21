#!/usr/bin/env python3
"""RLAIF stage: GRPO on the SFT touch-up model with the gated multi-term reward (rlaif/reward/reward.py).

Launch on a RunPod node with rlaif/runpod/run_grpo.sh (sets $PROJ, CUDA_VISIBLE_DEVICES, OpenRouter + W&B env); the old
Athena path was sft/remote_launch.sh with SCRIPT=rlaif/train_grpo.py. Defaults for paths come from $PROJ (default /workspace/cs2881r).
The judge is reached through rlaif/judge/oai.py: OpenRouter by default (OPENROUTER_API_KEY, model $JUDGE_MODEL = openai/gpt-5.6-luna).
Verified against TRL 1.13.0: custom reward funcs are called as f(prompts=, completions=, completion_ids=, **dataset_columns, trainer_state=, log_extra=, log_metric=).
"""
import argparse, json, os, random, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
PROJ = Path(os.environ.get("PROJ", "/workspace/cs2881r"))
assert os.environ.get("CUDA_VISIBLE_DEVICES"), "set CUDA_VISIBLE_DEVICES in the launcher (never inside the .py)"
import torch
from datasets import Dataset
from peft import LoraConfig
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainerCallback
from trl import GRPOConfig, GRPOTrainer
from reward.reward import GroupReward, RewardConfig, JudgeUnavailable
from judge.oai import DEFAULT_MODEL

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

class TimeBudget(TrainerCallback):
    """Stop cleanly (checkpoint, then the normal save + merge) once the wall-clock budget is spent. The LR schedule is constant, so an
    early stop costs nothing but steps; the run name and W&B log record the step reached."""
    def __init__(self, hours, reward_fn=None): self.deadline = time.time() + hours * 3600 if hours else None; self.t0 = time.time(); self.reward_fn = reward_fn
    def on_step_end(self, args, state, control, **kw):
        if self.reward_fn is not None and self.reward_fn.stop_reason:
            print(f"[time] judge unavailable ({self.reward_fn.stop_reason}); stopping at step {state.global_step} and saving", flush=True); control.should_training_stop = True; control.should_save = True; return control
        if state.global_step and state.global_step % 5 == 0:
            per = (time.time() - self.t0) / state.global_step; left = (self.deadline - time.time()) / 3600 if self.deadline else float("inf")
            print(f"[time] step {state.global_step}: {per:.1f}s/step, projected total {per * state.max_steps / 3600:.2f}h" + (f", budget left {left:.2f}h" if self.deadline else ""), flush=True)
        if self.deadline and time.time() > self.deadline:
            print(f"[time] wall-clock budget spent at step {state.global_step}; stopping and saving", flush=True); control.should_training_stop = True; control.should_save = True
        return control

class RewardFn:
    """Batch-aware reward: groups the step's completions by prompt id and scores each group jointly."""
    __name__ = "sheldon_reward"
    def __init__(self, cfg, max_completion_length):
        self.gr = GroupReward(cfg); self.maxlen = max_completion_length; self.calls = 0; self.stop_reason = None
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
        if self.stop_reason: return [0.0] * n                      # already stopping: constant reward -> zero advantage -> no update
        try: rewards, metrics = self.gr.score_step(glist)
        except (JudgeUnavailable, RuntimeError) as e:              # RuntimeError here is the USD budget guard
            self.stop_reason = str(e)[:300]; print(f"[reward] STOPPING: {self.stop_reason}", flush=True); return [0.0] * n
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
    ap.add_argument("--prompts", default=str(HERE / "data/rl_prompts.jsonl"))
    ap.add_argument("--out_root", default=str(PROJ / "runs")); ap.add_argument("--merged_root", default=str(PROJ / "models"))
    ap.add_argument("--run_name", default=None); ap.add_argument("--wandb_project", default="cs2881r-sheldon")
    ap.add_argument("--judge_model", default=DEFAULT_MODEL, help='OpenRouter/OpenAI model id, or "mock" for an offline stand-in')
    ap.add_argument("--judge_reasoning", default=None, help="reasoning effort for reasoning judges: none|minimal|low|medium|high (default $JUDGE_REASONING or minimal)")
    ap.add_argument("--judge_workers", type=int, default=96); ap.add_argument("--budget_usd", type=float, default=100.0)
    ap.add_argument("--pair_orders", type=int, default=2, help="2 = both presentation orders per sibling pair; 1 = one random order (halves pairwise calls)")
    ap.add_argument("--time_budget_h", type=float, default=0.0, help="stop training after this many hours (0 = off); the final save + merge still run")
    ap.add_argument("--bf16", type=int, default=1, help="1 = bf16 (GPU); 0 = fp32 (CPU dry run)")
    ap.add_argument("--report_to", default="wandb")
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
    ap.add_argument("--coherence_factor", type=float, default=0.5); ap.add_argument("--worse_off_factor", type=float, default=0.25); ap.add_argument("--false_claim_penalty", type=float, default=0.5)
    ap.add_argument("--seed", type=int, default=42); ap.add_argument("--no_merge", action="store_true")
    a = ap.parse_args()
    run_name = a.run_name or f"grpo-{Path(a.model).name}-{time.strftime('%m%d-%H%M')}"
    out_dir = Path(a.out_root) / run_name; out_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("OAI_CACHE_DIR", str(PROJ / "oai_cache"))
    run = None
    if a.report_to == "wandb":
        import wandb
        run = wandb.init(project=a.wandb_project, name=run_name, config=vars(a), dir=os.environ.get("WANDB_DIR"))
    ds = build_dataset(a.prompts, a.limit, a.seed); print("prompts:", len(ds), flush=True)
    tok = AutoTokenizer.from_pretrained(a.model); tok.padding_side = "left"
    if tok.pad_token is None: tok.pad_token = tok.eos_token
    assert a.prompts_per_step * a.num_generations % a.per_device_bs == 0, "prompts_per_step*num_generations must be a multiple of per_device_bs"
    grad_accum = a.prompts_per_step * a.num_generations // a.per_device_bs
    cfg = GRPOConfig(
        output_dir=str(out_dir), run_name=run_name, report_to=[a.report_to] if a.report_to != "none" else [], logging_steps=1, save_steps=a.save_steps, save_total_limit=6,
        learning_rate=a.lr, lr_scheduler_type="constant_with_warmup", warmup_steps=10, max_steps=a.max_steps, seed=a.seed,
        per_device_train_batch_size=a.per_device_bs, gradient_accumulation_steps=grad_accum, num_generations=a.num_generations,
        max_completion_length=a.max_completion_length, temperature=a.temperature, top_p=a.top_p, repetition_penalty=a.repetition_penalty,
        beta=a.beta, epsilon=a.epsilon, loss_type=a.loss_type, scale_rewards=a.scale_rewards, num_iterations=a.num_iterations, mask_truncated_completions=False,
        bf16=bool(a.bf16), gradient_checkpointing=True, gradient_checkpointing_kwargs={"use_reentrant": False}, remove_unused_columns=False,
        log_completions=True, num_completions_to_print=2, use_vllm=a.use_vllm, **({"vllm_mode": "colocate", "vllm_gpu_memory_utilization": a.vllm_gpu_mem} if a.use_vllm else {}),
    )
    peft_cfg = LoraConfig(r=a.lora_r, lora_alpha=a.lora_alpha, lora_dropout=0.0, bias="none", task_type="CAUSAL_LM",
                          target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"])
    rcfg = RewardConfig(judge_model=a.judge_model, judge_reasoning=a.judge_reasoning, workers=a.judge_workers, pair_orders=a.pair_orders, w_persona=a.w_persona, w_form=a.w_form, ring=a.ring, coherence_factor=a.coherence_factor, worse_off_factor=a.worse_off_factor, false_claim_penalty=a.false_claim_penalty, budget_usd=a.budget_usd, seed=a.seed)
    reward_fn = RewardFn(rcfg, a.max_completion_length)
    model = AutoModelForCausalLM.from_pretrained(a.model, dtype=torch.bfloat16 if a.bf16 else torch.float32, attn_implementation="sdpa")
    if torch.cuda.is_available(): torch.backends.cuda.enable_cudnn_sdp(False)          # cuDNN SDPA backward gave NaN grads on padded batches (athena, torch 2.12)
    trainer = GRPOTrainer(model=model, reward_funcs=[reward_fn], args=cfg, train_dataset=ds, processing_class=tok, peft_config=peft_cfg, callbacks=[TimeBudget(a.time_budget_h, reward_fn)])
    trainer.train()
    trainer.save_model(str(out_dir / "final_adapter"))
    if not a.no_merge:
        from peft import PeftModel
        base = AutoModelForCausalLM.from_pretrained(a.model, dtype=torch.bfloat16 if a.bf16 else torch.float32)
        merged = PeftModel.from_pretrained(base, str(out_dir / "final_adapter")).merge_and_unload()
        mdir = Path(a.merged_root) / f"{run_name}-merged"; merged.save_pretrained(str(mdir), safe_serialization=True); tok.save_pretrained(str(mdir)); print("merged ->", mdir, flush=True)
    from judge.oai import usage_summary; print("judge usage:", usage_summary(), flush=True)
    if run is not None: run.finish()

if __name__ == "__main__": main()
