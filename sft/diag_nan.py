#!/usr/bin/env python3
"""Replay the micro-batches of the steps where grad_norm went NaN, from the last healthy checkpoint,
and locate the offending batch/rows. Checks forward loss finiteness (padded batch as in training, then
per-row), backward grad finiteness, and sdpa vs eager attention."""
import sys, json, argparse, math, torch
sys.path.insert(0, "/data/agastyas/cs2881r")
import train_sft as T
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

ap = argparse.ArgumentParser()
ap.add_argument("--run", default="sft-lora-r32-nomath-v1"); ap.add_argument("--ckpt", default="checkpoint-57")
ap.add_argument("--steps", default="71-75"); ap.add_argument("--bs", type=int, default=16); ap.add_argument("--accum", type=int, default=4)
ap.add_argument("--seed", type=int, default=42); ap.add_argument("--max_len", type=int, default=2048)
a = ap.parse_args()
lo, hi = map(int, a.steps.split("-"))
tok = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-3B-Instruct"); tok.padding_side = "right"
cm = T.ChatML(tok, a.max_len)
rows = T.load_rows("/data/agastyas/cs2881r/data/train.jsonl")
ds = T.SFTData(rows, cm)
order = list(iter(T.LengthGroupedSampler(ds.lengths, a.bs, seed=a.seed)))   # first epoch order (calls=0)
collate = T.make_collator(tok.pad_token_id)
mbs = []
for s in range(lo, hi + 1):
    for m in range((s - 1) * a.accum, s * a.accum):
        idx = order[m * a.bs:(m + 1) * a.bs]; mbs.append((s, m, idx))
print(f"[diag] {len(mbs)} micro-batches for steps {lo}-{hi}; lengths per micro-batch (min..max):")
for s, m, idx in mbs: print(f"   step {s} mb {m}: {min(ds.lengths[i] for i in idx)}..{max(ds.lengths[i] for i in idx)}  n={len(idx)}")

def load(attn):
    base = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-3B-Instruct", dtype=torch.bfloat16, attn_implementation=attn).cuda()
    mdl = PeftModel.from_pretrained(base, f"/data/agastyas/cs2881r/runs/{a.run}/{a.ckpt}", is_trainable=True)
    mdl.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False}); mdl.enable_input_require_grads()
    return mdl

model = load("sdpa"); model.train()
bad = []
for s, m, idx in mbs:
    batch = {k: v.cuda() for k, v in collate([ds[i] for i in idx]).items()}
    with torch.autocast("cuda", dtype=torch.bfloat16):
        out = model(**batch)
    loss = out.loss.item(); lf = torch.isfinite(out.logits).all().item()
    model.zero_grad(set_to_none=True); out.loss.backward()
    gn = torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.grad is not None], 1.0).item()
    flag = (not math.isfinite(loss)) or (not lf) or (not math.isfinite(gn)) or loss > 4
    print(f"[mb] step {s} mb {m}: loss={loss:.4f} logits_finite={lf} grad_norm={gn:.4f} {'<-- BAD' if flag else ''}", flush=True)
    if flag: bad.append((s, m, idx))
    model.zero_grad(set_to_none=True)

model.eval()
for s, m, idx in bad:
    print(f"\n[rows] step {s} mb {m}: per-row forward (bs=1, no padding)")
    for i in idx:
        ex = ds[i]; b = {k: v.cuda() for k, v in collate([ex]).items()}
        with torch.no_grad(), torch.autocast("cuda", dtype=torch.bfloat16):
            o = model(**b)
        l = o.loss.item(); lf = torch.isfinite(o.logits).all().item(); nsup = sum(1 for x in ex["labels"] if x != -100)
        mark = "" if (math.isfinite(l) and lf and l < 4) else "  <-- SUSPECT"
        print(f"   row {i} id={rows[i]['id']} len={len(ex['input_ids'])} supervised={nsup} loss={l:.4f} logits_finite={lf}{mark}")
        if mark: print("      USER:", rows[i]["messages"][1 if rows[i]["messages"][0]["role"]=="system" else 0]["content"][:200].replace("\n"," "))
        if mark: print("      ASST:", [x["content"] for x in rows[i]["messages"] if x["role"]=="assistant"][0][:200].replace("\n"," "))
    # same batch with eager attention
    del model; torch.cuda.empty_cache(); model = load("eager"); model.train()
    batch = {k: v.cuda() for k, v in collate([ds[i] for i in idx]).items()}
    with torch.autocast("cuda", dtype=torch.bfloat16):
        out = model(**batch)
    model.zero_grad(set_to_none=True); out.loss.backward()
    gn = torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.grad is not None], 1.0).item()
    print(f"[eager] same micro-batch: loss={out.loss.item():.4f} logits_finite={torch.isfinite(out.logits).all().item()} grad_norm={gn:.4f}")
    break
if not bad: print("[diag] no bad micro-batch reproduced from", a.ckpt)
print("[diag-done]")
