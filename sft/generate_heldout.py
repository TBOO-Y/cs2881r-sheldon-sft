#!/usr/bin/env python3
"""Generate responses from a merged model (or the base model) for the 502 held-out prompts
plus a fixed set of short out-of-distribution prompts. Greedy, batched, left-padded.

  python generate_heldout.py --model /data/agastyas/cs2881r/models/<run>-merged \
      --prompts /data/agastyas/cs2881r/data/heldout_prompts.jsonl --out /data/agastyas/cs2881r/gens/<run>.jsonl
"""
import argparse, json, os, time
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

OOD_PROMPTS = [  # short prompts unlike the long, backstory-heavy training prompts
    "What's the capital of Australia?", "How many legs does a spider have?", "Who wrote Pride and Prejudice?",
    "hey how's it going", "good morning!", "What do you do for fun?", "Are you a robot?", "Tell me about yourself.",
    "Can you explain what a black hole is in two sentences?", "Why is the sky blue?", "What is DNA?", "Explain recursion simply.",
    "Give me a tip for falling asleep faster.", "How do I ask my boss for a raise?", "Should I learn Python or JavaScript first?",
    "Write a limerick about coffee.", "Write a haiku about Mondays.", "Give me a name for a pet goldfish.",
    "I think Star Wars is better than Star Trek. Thoughts?", "Is a hot dog a sandwich?", "What's your favorite number and why?",
    "Write a Python function that reverses a string.", "What does HTTP stand for?", "Fix this: print('hello world'",
    "Summarize the plot of Romeo and Juliet in one sentence.", "Translate 'thank you' into Spanish.", "What's a synonym for 'happy'?",
    "A train travels 60 miles in 1.5 hours. What is its average speed in mph?", "What is 17 times 23?",
    "If a shirt costs $40 and is 25% off, what is the sale price?", "Solve for x: 3x + 7 = 22.",
    "I have 3 apples and eat one. How many are left?", "What is the derivative of x^2?",
    "Can you keep a secret?", "You're wrong about everything.", "Say something nice to me.", "Be brief: best pizza topping?",
    "Sarcasm?", "Bazinga!", "Tell me a joke.",
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True); ap.add_argument("--prompts", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--max_new_tokens", type=int, default=400); ap.add_argument("--bs", type=int, default=32)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--adapter", default="", help="optional LoRA adapter dir to load on top of --model (no merge needed)")
    ap.add_argument("--tag", default="", help="label stored in each output row (defaults to adapter or model path)")
    a = ap.parse_args(); os.makedirs(os.path.dirname(a.out), exist_ok=True)
    items = [json.loads(l) for l in open(a.prompts)]
    if a.limit: items = items[:a.limit]
    for i, q in enumerate(OOD_PROMPTS):
        items.append({"id": f"ood-{i:03d}", "kind": "ood_short", "messages": [{"role": "user", "content": q}], "reference": None})
    for it in items: it["source"] = "ood" if it["id"].startswith("ood-") else "heldout"
    tok = AutoTokenizer.from_pretrained(a.model); tok.padding_side = "left"
    model = AutoModelForCausalLM.from_pretrained(a.model, dtype=torch.bfloat16, attn_implementation="sdpa").cuda()
    if a.adapter:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, a.adapter); model = model.merge_and_unload()
    model.eval(); tag = a.tag or a.adapter or a.model
    texts = [tok.apply_chat_template(it["messages"], tokenize=False, add_generation_prompt=True) for it in items]
    order = sorted(range(len(items)), key=lambda i: len(texts[i]))
    results = [None] * len(items); t0 = time.time()
    for b in range(0, len(order), a.bs):
        idx = order[b:b + a.bs]
        enc = tok([texts[i] for i in idx], return_tensors="pt", padding=True).to("cuda")
        with torch.no_grad():
            gen = model.generate(**enc, max_new_tokens=a.max_new_tokens, do_sample=False, pad_token_id=tok.pad_token_id)
        new = gen[:, enc["input_ids"].shape[1]:]
        for j, i in enumerate(idx):
            ids = new[j]; n = int((ids != tok.pad_token_id).sum())
            results[i] = {**items[i], "model": tag, "response": tok.decode(ids, skip_special_tokens=True).strip(),
                          "gen_tokens": n, "hit_max": bool(n >= a.max_new_tokens)}
        print(f"[gen] {b + len(idx)}/{len(items)}  {time.time() - t0:.0f}s", flush=True)
    with open(a.out, "w") as f:
        for r in results: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    hit = sum(r["hit_max"] for r in results); print(f"[done] {len(results)} generations -> {a.out}; hit_max={hit}")
    for r in [x for x in results if x["source"] == "ood"][:6]:
        print("\nQ:", r["messages"][-1]["content"], "\nA:", r["response"][:500])

if __name__ == "__main__":
    main()
