#!/usr/bin/env python3
"""Merge a LoRA adapter into its base model and save bf16 weights (+ tokenizer): the stage-3b boundary step.
  python rlvr/merge_adapter.py --base models/grpo-v2-merged --adapter runs/rlvr-main/checkpoint-200 --out models/rlvr-main-ckpt200-merged"""
import argparse, torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
ap = argparse.ArgumentParser(); ap.add_argument("--base", required=True); ap.add_argument("--adapter", required=True); ap.add_argument("--out", required=True)
a = ap.parse_args()
m = PeftModel.from_pretrained(AutoModelForCausalLM.from_pretrained(a.base, dtype=torch.bfloat16), a.adapter).merge_and_unload()
m.save_pretrained(a.out, safe_serialization=True); AutoTokenizer.from_pretrained(a.base).save_pretrained(a.out); print("merged ->", a.out)
