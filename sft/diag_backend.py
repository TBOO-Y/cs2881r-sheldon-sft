#!/usr/bin/env python3
"""Which SDPA backend produces NaN gradients on the bad micro-batch (step 73, mb 290)?"""
import sys, math, torch
sys.path.insert(0, "/data/agastyas/cs2881r")
import train_sft as T
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
from torch.nn.attention import sdpa_kernel, SDPBackend

MB = int(sys.argv[1]) if len(sys.argv) > 1 else 290
tok = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-3B-Instruct"); tok.padding_side = "right"
cm = T.ChatML(tok, 2048); rows = T.load_rows("/data/agastyas/cs2881r/data/train.jsonl"); ds = T.SFTData(rows, cm)
order = list(iter(T.LengthGroupedSampler(ds.lengths, 16, seed=42))); idx = order[MB * 16:(MB + 1) * 16]
collate = T.make_collator(tok.pad_token_id)
batch = {k: v.cuda() for k, v in collate([ds[i] for i in idx]).items()}
print(f"[batch] mb {MB}: padded shape {tuple(batch['input_ids'].shape)}; real lengths {sorted(ds.lengths[i] for i in idx)}")
print("[torch]", torch.__version__, "cudnn sdp enabled:", torch.backends.cuda.cudnn_sdp_enabled(), "flash:", torch.backends.cuda.flash_sdp_enabled(), "mem_eff:", torch.backends.cuda.mem_efficient_sdp_enabled(), "math:", torch.backends.cuda.math_sdp_enabled())
base = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-3B-Instruct", dtype=torch.bfloat16, attn_implementation="sdpa").cuda()
model = PeftModel.from_pretrained(base, "/data/agastyas/cs2881r/runs/sft-lora-r32-nomath-v1/checkpoint-57", is_trainable=True)
model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False}); model.enable_input_require_grads(); model.train()

def run(label, ctx=None):
    try:
        model.zero_grad(set_to_none=True)
        with (ctx if ctx is not None else torch.autocast("cuda", dtype=torch.bfloat16)):
            with torch.autocast("cuda", dtype=torch.bfloat16):
                out = model(**batch)
            out.loss.backward()
        gn = torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.grad is not None], 1.0).item()
        print(f"[{label:28s}] loss={out.loss.item():.4f} grad_norm={gn:.4f} {'NaN!' if not math.isfinite(gn) else 'ok'}", flush=True)
    except Exception as e:
        print(f"[{label:28s}] ERROR: {type(e).__name__}: {str(e)[:160]}", flush=True)

run("default selection")
for be in ["CUDNN_ATTENTION", "EFFICIENT_ATTENTION", "FLASH_ATTENTION", "MATH"]:
    run("only " + be, sdpa_kernel([getattr(SDPBackend, be)]))
run("all but CUDNN", sdpa_kernel([SDPBackend.EFFICIENT_ATTENTION, SDPBackend.FLASH_ATTENTION, SDPBackend.MATH]))
torch.backends.cuda.enable_cudnn_sdp(False); run("default, cudnn globally off")
# does the same batch padded to a different length still fail? (append one pad column)
for extra in [1, 8]:
    b2 = {"input_ids": torch.nn.functional.pad(batch["input_ids"], (0, extra), value=tok.pad_token_id),
          "labels": torch.nn.functional.pad(batch["labels"], (0, extra), value=-100),
          "attention_mask": torch.nn.functional.pad(batch["attention_mask"], (0, extra), value=0)}
    torch.backends.cuda.enable_cudnn_sdp(True); saved = batch; batch = b2; run(f"cudnn on, +{extra} pad cols (len {b2['input_ids'].shape[1]})"); batch = saved
print("[diag-done]")
