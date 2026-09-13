#!/usr/bin/env python3
"""LoRA SFT of Qwen2.5-3B-Instruct on the filtered Sheldon persona data.

* Assistant-only loss: manual Qwen2.5 ChatML tokenization, verified against the
  tokenizer's chat template at startup (hard fail on mismatch).
* Rows without a system prompt get Qwen's default system prompt, exactly as the
  chat template would at inference time.
* Checkpoints (LoRA adapters) every ~10% of an epoch, eval loss at the same
  cadence, everything logged to W&B.
* After training: save final adapter, merge into a full bf16 model for vLLM,
  and print a handful of sanity generations.
All paths are absolute under /data (cluster home is capped at 10 GiB).
"""
import argparse, json, math, os, time, random
import torch
from torch.utils.data import Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, Trainer, TrainingArguments, set_seed
from peft import LoraConfig, get_peft_model

DEFAULT_SYSTEM = "You are Qwen, created by Alibaba Cloud. You are a helpful assistant."
SANITY_PROMPTS = [
    "What's the capital of Australia?",
    "Can you explain what a black hole is in two sentences?",
    "hey how's it going",
    "Write a limerick about coffee.",
    "A train travels 60 miles in 1.5 hours. What is its average speed in mph?",
    "I think Star Wars is better than Star Trek. Thoughts?",
]

def parse():
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="Qwen/Qwen2.5-3B-Instruct")
    p.add_argument("--train", required=True); p.add_argument("--val", required=True)
    p.add_argument("--out_root", default="/data/agastyas/cs2881r/runs")
    p.add_argument("--merged_root", default="/data/agastyas/cs2881r/models")
    p.add_argument("--run_name", required=True)
    p.add_argument("--wandb_project", default="cs2881r-sheldon")
    p.add_argument("--max_len", type=int, default=2048)
    p.add_argument("--epochs", type=float, default=2.0)
    p.add_argument("--lr", type=float, default=1e-4)
    p.add_argument("--per_device_bs", type=int, default=16)
    p.add_argument("--grad_accum", type=int, default=4)
    p.add_argument("--lora_r", type=int, default=32); p.add_argument("--lora_alpha", type=int, default=64)
    p.add_argument("--lora_dropout", type=float, default=0.05)
    p.add_argument("--warmup_ratio", type=float, default=0.03)
    p.add_argument("--saves_per_epoch", type=int, default=10)
    p.add_argument("--attn", default="sdpa")
    p.add_argument("--sdp_disable", default="cudnn", help="comma list of torch SDPA backends to disable: cudnn,mem_efficient,flash,math (default: cudnn)")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--limit", type=int, default=0, help="debug: use only N train rows")
    p.add_argument("--no_merge", action="store_true")
    return p.parse_args()

class ChatML:
    def __init__(self, tok, max_len):
        self.tok, self.max_len = tok, max_len
        self.im_end = tok.convert_tokens_to_ids("<|im_end|>")
        self.nl = tok.encode("\n", add_special_tokens=False)
    def build(self, messages, truncate=True):
        if messages[0]["role"] != "system":
            messages = [{"role": "system", "content": DEFAULT_SYSTEM}] + messages
        ids, labels = [], []
        for m in messages:
            head = self.tok.encode(f"<|im_start|>{m['role']}\n", add_special_tokens=False)
            body = self.tok.encode(m["content"], add_special_tokens=False)
            ids += head + body + [self.im_end] + self.nl
            if m["role"] == "assistant":
                labels += [-100] * len(head) + body + [self.im_end] + [-100] * len(self.nl)
            else:
                labels += [-100] * (len(head) + len(body) + 1 + len(self.nl))
        if truncate: ids, labels = ids[: self.max_len], labels[: self.max_len]
        return ids, labels
    def self_check(self, rows, n=300):
        bad = 0
        for r in rows[:n]:
            ids, _ = self.build(r["messages"], truncate=False)
            ref = self.tok.apply_chat_template(r["messages"], tokenize=True, add_generation_prompt=False)
            if hasattr(ref, "input_ids"): ref = ref["input_ids"]
            if list(ref) != ids: bad += 1
        if bad: raise RuntimeError(f"ChatML self-check failed on {bad}/{n} rows: manual tokenization != chat template")
        print(f"[check] manual ChatML tokenization matches chat template on {n} rows")

class SFTData(Dataset):
    def __init__(self, rows, cm):
        self.ex = [cm.build(r["messages"]) for r in rows]
        self.lengths = [len(i) for i, _ in self.ex]
    def __len__(self): return len(self.ex)
    def __getitem__(self, i):
        ids, labels = self.ex[i]
        return {"input_ids": ids, "labels": labels}

class LengthGroupedSampler(torch.utils.data.Sampler):
    """Shuffle, then sort within mega-batches so each micro-batch holds similar lengths (less padding).
    transformers 5.x removed TrainingArguments.group_by_length; this replaces it. Reshuffles on every epoch."""
    def __init__(self, lengths, batch_size, mega=32, seed=0):
        self.lengths, self.bs, self.mega, self.seed, self.calls = lengths, batch_size, mega, seed, 0
    def __len__(self): return len(self.lengths)
    def __iter__(self):
        g = torch.Generator(); g.manual_seed(self.seed + self.calls); self.calls += 1
        idx = torch.randperm(len(self.lengths), generator=g).tolist()
        mb = self.bs * self.mega
        megas = [sorted(idx[i:i + mb], key=lambda j: -self.lengths[j]) for i in range(0, len(idx), mb)]
        return iter([j for m in megas for j in m])

class GroupedTrainer(Trainer):
    """Length-grouped sampling + a guard that skips any optimizer step whose gradients are non-finite
    (a single NaN gradient otherwise poisons the LoRA weights for the rest of the run)."""
    skipped_steps = 0
    def _get_train_sampler(self, *args, **kwargs):
        return LengthGroupedSampler(self.train_dataset.lengths, self.args.per_device_train_batch_size, seed=self.args.seed)
    def create_optimizer(self):
        opt = super().create_optimizer()
        if getattr(opt, "_guarded", False): return opt
        orig_step, trainer = opt.step, self
        def guarded_step(*args, **kwargs):
            grads = [p.grad for g in opt.param_groups for p in g["params"] if p.grad is not None]
            total = torch.stack([g.float().pow(2).sum() for g in grads]).sum()
            if not torch.isfinite(total):
                trainer.skipped_steps += 1
                print(f"[guard] non-finite gradient at global step {trainer.state.global_step}; skipping optimizer step (#{trainer.skipped_steps})", flush=True)
                for g in grads: g.zero_()
                return None
            return orig_step(*args, **kwargs)
        opt.step = guarded_step; opt._guarded = True
        return opt
    def log(self, logs, *args, **kwargs):
        if "loss" in logs: logs["skipped_steps"] = self.skipped_steps
        return super().log(logs, *args, **kwargs)

def make_collator(pad_id):
    def collate(feats):
        L = max(len(f["input_ids"]) for f in feats)
        ids = torch.full((len(feats), L), pad_id, dtype=torch.long)
        lab = torch.full((len(feats), L), -100, dtype=torch.long)
        att = torch.zeros((len(feats), L), dtype=torch.long)
        for i, f in enumerate(feats):
            n = len(f["input_ids"])
            ids[i, :n] = torch.tensor(f["input_ids"]); lab[i, :n] = torch.tensor(f["labels"]); att[i, :n] = 1
        return {"input_ids": ids, "labels": lab, "attention_mask": att}
    return collate

def load_rows(path, limit=0):
    rows = [json.loads(l) for l in open(path)]
    return rows[:limit] if limit else rows

def main():
    a = parse(); set_seed(a.seed)
    for be in [x for x in a.sdp_disable.split(",") if x]:
        getattr(torch.backends.cuda, f"enable_{be}_sdp")(False); print(f"[sdpa] disabled torch SDPA backend: {be}")
    assert "CUDA_VISIBLE_DEVICES" in os.environ, "launcher must pin a GPU via CUDA_VISIBLE_DEVICES"
    out_dir = os.path.join(a.out_root, a.run_name); os.makedirs(out_dir, exist_ok=True)
    tok = AutoTokenizer.from_pretrained(a.model); tok.padding_side = "right"
    cm = ChatML(tok, a.max_len)
    train_rows, val_rows = load_rows(a.train, a.limit), load_rows(a.val)
    cm.self_check(train_rows)
    train_ds, val_ds = SFTData(train_rows, cm), SFTData(val_rows, cm)
    tot = sum(train_ds.lengths); sup = sum(sum(1 for x in l if x != -100) for _, l in train_ds.ex)
    eff_bs = a.per_device_bs * a.grad_accum
    steps_per_epoch = math.ceil(len(train_ds) / eff_bs)
    save_steps = max(1, round(steps_per_epoch / a.saves_per_epoch))
    total_steps = math.ceil(steps_per_epoch * a.epochs)
    data_stats = {"train_rows": len(train_ds), "val_rows": len(val_ds), "train_tokens": tot, "supervised_tokens": sup,
                  "supervised_frac": round(sup / tot, 4), "max_len": a.max_len, "truncated_rows": sum(1 for L in train_ds.lengths if L >= a.max_len),
                  "steps_per_epoch": steps_per_epoch, "save_steps": save_steps, "total_steps": total_steps, "effective_batch": eff_bs}
    print("[data]", json.dumps(data_stats))

    import wandb
    wandb.init(project=a.wandb_project, name=a.run_name, dir=os.environ.get("WANDB_DIR"),
               config={**vars(a), **data_stats, "gpu": torch.cuda.get_device_name(0), "cuda_visible_devices": os.environ["CUDA_VISIBLE_DEVICES"]})

    model = AutoModelForCausalLM.from_pretrained(a.model, dtype=torch.bfloat16, attn_implementation=a.attn)
    model.config.use_cache = False
    lcfg = LoraConfig(r=a.lora_r, lora_alpha=a.lora_alpha, lora_dropout=a.lora_dropout, bias="none", task_type="CAUSAL_LM",
                      target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"])
    model = get_peft_model(model, lcfg); model.print_trainable_parameters()
    model.enable_input_require_grads()

    kw = dict(output_dir=out_dir, run_name=a.run_name, report_to=["wandb"],
              per_device_train_batch_size=a.per_device_bs, per_device_eval_batch_size=16, gradient_accumulation_steps=a.grad_accum,
              learning_rate=a.lr, num_train_epochs=a.epochs, lr_scheduler_type="cosine", warmup_steps=max(1, math.ceil(a.warmup_ratio * total_steps)),
              weight_decay=0.0, max_grad_norm=1.0, bf16=True, logging_steps=5, logging_first_step=True,
              eval_strategy="steps", eval_steps=save_steps, save_strategy="steps", save_steps=save_steps, save_total_limit=None,
              gradient_checkpointing=True, gradient_checkpointing_kwargs={"use_reentrant": False},
              dataloader_num_workers=2, optim="adamw_torch_fused", seed=a.seed,
              remove_unused_columns=False, save_only_model=True, disable_tqdm=True)
    fields = TrainingArguments.__dataclass_fields__
    dropped = [k for k in kw if k not in fields]
    if dropped: print("[warn] TrainingArguments does not accept:", dropped)
    targs = TrainingArguments(**{k: v for k, v in kw.items() if k in fields})
    trainer = GroupedTrainer(model=model, args=targs, train_dataset=train_ds, eval_dataset=val_ds,
                      data_collator=make_collator(tok.pad_token_id), processing_class=tok)
    print(f"[train] {len(train_ds)} rows, {steps_per_epoch} steps/epoch, saving every {save_steps} steps, {total_steps} total steps")
    t0 = time.time(); base_eval = trainer.evaluate(); print("[eval@0]", base_eval)
    trainer.train()
    print(f"[train] done in {(time.time()-t0)/60:.1f} min")
    final_dir = os.path.join(out_dir, "final_adapter"); trainer.save_model(final_dir); tok.save_pretrained(final_dir)
    final_eval = trainer.evaluate(); print("[eval@end]", final_eval)

    if not a.no_merge:
        merged_dir = os.path.join(a.merged_root, a.run_name + "-merged"); os.makedirs(merged_dir, exist_ok=True)
        merged = trainer.model.merge_and_unload(); merged.config.use_cache = True
        merged.save_pretrained(merged_dir, safe_serialization=True); tok.save_pretrained(merged_dir)
        print("[merge] saved merged bf16 model to", merged_dir)
        merged.eval(); tok.padding_side = "left"
        texts = [tok.apply_chat_template([{"role": "user", "content": q}], tokenize=False, add_generation_prompt=True) for q in SANITY_PROMPTS]
        enc = tok(texts, return_tensors="pt", padding=True).to(merged.device)
        with torch.no_grad():
            gen = merged.generate(**enc, max_new_tokens=300, do_sample=False, pad_token_id=tok.pad_token_id)
        outs = tok.batch_decode(gen[:, enc["input_ids"].shape[1]:], skip_special_tokens=True)
        table = wandb.Table(columns=["prompt", "response"])
        for q, o in zip(SANITY_PROMPTS, outs):
            print("\n[sanity] Q:", q, "\n[sanity] A:", o[:1200]); table.add_data(q, o)
        wandb.log({"sanity_generations": table})
        json.dump([{"prompt": q, "response": o} for q, o in zip(SANITY_PROMPTS, outs)], open(os.path.join(out_dir, "sanity_generations.json"), "w"), indent=1)
    wandb.finish()
    print("[done]", out_dir)

if __name__ == "__main__":
    main()
