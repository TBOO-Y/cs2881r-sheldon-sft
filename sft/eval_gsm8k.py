#!/usr/bin/env python3
"""GSM8K test-set evaluation (zero-shot chat prompt, greedy) for the base model or base + LoRA adapter.
Rule-based verifier: numeric match against the GSM8K reference (text after '####').
  strict  = a \\boxed{} answer is present and its (first) number matches
  lenient = strict, or (no box) the last number in the response matches
Writes per-problem JSONL to --out and a summary to --out + '.summary.json'."""
import argparse, json, os, re, time
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

SUFFIX = "\nPlease reason step by step, and put your final answer within \\boxed{}."
NUM = re.compile(r"-?\d[\d,]*(?:\.\d+)?")

def last_boxed(s):
    i = s.rfind("\\boxed{")
    if i < 0: return None
    j, depth, out = i + len("\\boxed{"), 1, []
    while j < len(s) and depth:
        c = s[j]
        if c == "{": depth += 1
        elif c == "}": depth -= 1
        if depth: out.append(c)
        j += 1
    return "".join(out)

def clean(s):
    s = s.replace("\\!", "").replace("\\,", "").replace("\\ ", " ").replace("\\$", "").replace("$", "")
    s = re.sub(r"\\text(?:bf|rm|it)?\{[^}]*\}", " ", s); s = re.sub(r"\\(?:mathrm|mathbf|textbf)\{([^}]*)\}", r"\1", s)
    return s.replace("\\%", "").replace("%", "").replace(",", "")

def parse_number(s, which="first"):
    if s is None: return None
    s = clean(s)
    m = re.search(r"\\d?frac\{(-?\d+(?:\.\d+)?)\}\{(-?\d+(?:\.\d+)?)\}", s)
    if m and float(m.group(2)) != 0: return float(m.group(1)) / float(m.group(2))
    m = re.fullmatch(r"\s*(-?\d+(?:\.\d+)?)\s*/\s*(-?\d+(?:\.\d+)?)\s*", s)
    if m and float(m.group(2)) != 0: return float(m.group(1)) / float(m.group(2))
    nums = NUM.findall(s)
    if not nums: return None
    try: return float((nums[0] if which == "first" else nums[-1]).replace(",", ""))
    except ValueError: return None

def score(response, ref):
    box = last_boxed(response)
    pb = parse_number(box, "first") if box is not None else None
    pa = pb if pb is not None else parse_number(response, "last")
    ok = lambda p: p is not None and abs(p - ref) < 1e-4 * max(1.0, abs(ref))
    return {"boxed": box, "pred_boxed": pb, "pred_any": pa, "correct_strict": ok(pb), "correct_lenient": ok(pa)}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-3B-Instruct"); ap.add_argument("--adapter", default=""); ap.add_argument("--tag", default="")
    ap.add_argument("--data", default="/data/agastyas/cs2881r/data/gsm8k_test.jsonl"); ap.add_argument("--out", required=True)
    ap.add_argument("--bs", type=int, default=48); ap.add_argument("--max_new_tokens", type=int, default=1024); ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args(); tag = a.tag or a.adapter or a.model; os.makedirs(os.path.dirname(a.out), exist_ok=True)
    probs = [json.loads(l) for l in open(a.data)]
    if a.limit: probs = probs[: a.limit]
    refs = [float(p["answer"].split("####")[-1].strip().replace(",", "")) for p in probs]
    tok = AutoTokenizer.from_pretrained(a.model); tok.padding_side = "left"
    model = AutoModelForCausalLM.from_pretrained(a.model, dtype=torch.bfloat16, attn_implementation="sdpa").cuda()
    if a.adapter:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, a.adapter).merge_and_unload()
    model.eval()
    texts = [tok.apply_chat_template([{"role": "user", "content": p["question"] + SUFFIX}], tokenize=False, add_generation_prompt=True) for p in probs]
    order = sorted(range(len(probs)), key=lambda i: len(texts[i])); res = [None] * len(probs); t0 = time.time()
    for b in range(0, len(order), a.bs):
        idx = order[b: b + a.bs]; enc = tok([texts[i] for i in idx], return_tensors="pt", padding=True).to("cuda")
        with torch.no_grad():
            gen = model.generate(**enc, max_new_tokens=a.max_new_tokens, do_sample=False, pad_token_id=tok.pad_token_id)
        new = gen[:, enc["input_ids"].shape[1]:]
        for j, i in enumerate(idx):
            n = int((new[j] != tok.pad_token_id).sum()); resp = tok.decode(new[j], skip_special_tokens=True).strip()
            res[i] = {"idx": i, "tag": tag, "question": probs[i]["question"], "reference": refs[i], "response": resp,
                      "gen_tokens": n, "hit_max": n >= a.max_new_tokens, **score(resp, refs[i])}
        done = b + len(idx); acc = sum(r["correct_lenient"] for r in res if r) / done
        print(f"[gsm8k] {done}/{len(probs)}  running_acc={acc:.3f}  {time.time() - t0:.0f}s", flush=True)
    with open(a.out, "w") as f:
        for r in res: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    n = len(res)
    summ = {"tag": tag, "n": n, "acc_strict": sum(r["correct_strict"] for r in res) / n, "acc_lenient": sum(r["correct_lenient"] for r in res) / n,
            "boxed_rate": sum(r["boxed"] is not None for r in res) / n, "hit_max_rate": sum(r["hit_max"] for r in res) / n,
            "mean_gen_tokens": sum(r["gen_tokens"] for r in res) / n, "runtime_s": round(time.time() - t0), "max_new_tokens": a.max_new_tokens}
    json.dump(summ, open(a.out + ".summary.json", "w"), indent=1); print("[summary]", json.dumps(summ))
    for r in res[:2]: print("\nQ:", r["question"][:200], "\nA:", r["response"][:600], "\n->", r["boxed"], r["pred_any"], "ref", r["reference"], r["correct_lenient"])

if __name__ == "__main__":
    main()
