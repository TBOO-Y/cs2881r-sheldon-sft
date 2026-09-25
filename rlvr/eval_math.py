#!/usr/bin/env python3
"""vLLM evaluation of a model (merged dir, or base + LoRA adapter merged into a scratch dir) on the stage-3 suite.
Tasks: math500 (per level, L3-5 aggregate), aime24/25/26, gsm8k (data/gsm8k_test.jsonl; gold = number after '####').
n = 1 -> greedy; n > 1 -> avg@n (mean accuracy over samples) and pass@n at --temperature/--top_p. Prompt format identical to training.
Writes <out_dir>/<task>.jsonl (per problem: responses, correct flags, lengths) and <out_dir>/<task>.summary.json; prints one line per task.
  CUDA_VISIBLE_DEVICES=7 python rlvr/eval_math.py --model <dir> [--adapter <dir>] --tasks math500,gsm8k --n 4 --temperature 0.6 --out_dir evals/rlvr/<tag>
"""
import argparse, json, os, sys, time
from collections import defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rlvr.grader import grade_many, last_boxed
from rlvr.train_rlvr import DEFAULT_SYSTEM, SUFFIX
HERE = Path(__file__).resolve().parent; PROJ = HERE.parent

def load_task(name, data_dir):
    if name == "gsm8k":
        rows = [json.loads(l) for l in open(PROJ / "data/gsm8k_test.jsonl")]
        return [{"id": f"gsm8k-{i}", "problem": r["question"], "answer": r["answer"].split("####")[-1].strip().replace(",", ""), "level": 0} for i, r in enumerate(rows)]
    return [json.loads(l) for l in open(Path(data_dir) / f"{name}.jsonl")]

def merge_adapter(base, adapter, scratch):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel
    out = Path(scratch) / (Path(adapter).parent.name + "-" + Path(adapter).name); out.mkdir(parents=True, exist_ok=True)
    if not (out / "config.json").exists():
        m = PeftModel.from_pretrained(AutoModelForCausalLM.from_pretrained(base, dtype=torch.bfloat16), adapter).merge_and_unload()
        m.save_pretrained(str(out), safe_serialization=True); AutoTokenizer.from_pretrained(base).save_pretrained(str(out))
    return str(out)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True); ap.add_argument("--adapter", default=""); ap.add_argument("--scratch", default=str(PROJ / "models/_merged_tmp"))
    ap.add_argument("--tasks", default="math500,gsm8k"); ap.add_argument("--data_dir", default=str(HERE / "data")); ap.add_argument("--out_dir", required=True); ap.add_argument("--tag", default="")
    ap.add_argument("--n", type=int, default=1); ap.add_argument("--temperature", type=float, default=0.6); ap.add_argument("--top_p", type=float, default=0.95)
    ap.add_argument("--max_tokens", type=int, default=4096); ap.add_argument("--max_model_len", type=int, default=6144); ap.add_argument("--gpu_mem", type=float, default=0.9)
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--workers", type=int, default=16); ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    from vllm import LLM, SamplingParams
    model = merge_adapter(a.model, a.adapter, a.scratch) if a.adapter else a.model
    out_dir = Path(a.out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    llm = LLM(model=model, dtype="bfloat16", gpu_memory_utilization=a.gpu_mem, max_model_len=a.max_model_len, seed=a.seed, enable_prefix_caching=True)
    tok = llm.get_tokenizer()
    greedy = a.n == 1
    sp = SamplingParams(n=a.n, temperature=0.0 if greedy else a.temperature, top_p=1.0 if greedy else a.top_p, max_tokens=a.max_tokens, seed=a.seed)
    for task in a.tasks.split(","):
        rows = load_task(task, a.data_dir)
        if a.limit: rows = rows[:a.limit]
        t0 = time.time()
        prompts = [tok.apply_chat_template([{"role": "system", "content": DEFAULT_SYSTEM}, {"role": "user", "content": r["problem"] + SUFFIX}], tokenize=False, add_generation_prompt=True) for r in rows]
        outs = llm.generate(prompts, sp)
        pairs = [(c.text, str(r["answer"])) for r, o in zip(rows, outs) for c in o.outputs]
        graded = grade_many(pairs, workers=a.workers)
        recs = []; j = 0
        for r, o in zip(rows, outs):
            cs = o.outputs; gs = graded[j: j + len(cs)]; j += len(cs)
            recs.append({**r, "tag": a.tag, "responses": [c.text for c in cs], "correct": [g["correct"] and c.finish_reason != "length" for g, c in zip(gs, cs)],
                         "boxed": [g["boxed"] for g in gs], "gen_tokens": [len(c.token_ids) for c in cs], "hit_max": [c.finish_reason == "length" for c in cs]})
        with open(out_dir / f"{task}.jsonl", "w") as f:
            for r in recs: f.write(json.dumps(r, ensure_ascii=False) + "\n")
        acc = [sum(r["correct"]) / len(r["correct"]) for r in recs]
        s = {"task": task, "tag": a.tag, "model": a.model, "adapter": a.adapter, "n": a.n, "greedy": greedy, "temperature": sp.temperature, "max_tokens": a.max_tokens, "problems": len(recs),
             "acc": sum(acc) / len(acc), "pass_at_n": sum(1 for r in recs if any(r["correct"])) / len(recs),
             "boxed_rate": sum(1 for r in recs for b in r["boxed"] if b is not None) / (len(recs) * a.n), "hit_max_rate": sum(sum(r["hit_max"]) for r in recs) / (len(recs) * a.n),
             "mean_gen_tokens": sum(sum(r["gen_tokens"]) for r in recs) / (len(recs) * a.n), "seconds": time.time() - t0}
        by = defaultdict(list)
        for r, x in zip(recs, acc): by[r.get("level", 0)].append(x)
        s["acc_by_level"] = {str(k): sum(v) / len(v) for k, v in sorted(by.items())}; s["n_by_level"] = {str(k): len(v) for k, v in sorted(by.items())}
        hard = [x for r, x in zip(recs, acc) if r.get("level", 0) >= 3]
        if hard: s["acc_L3_5"] = sum(hard) / len(hard); s["n_L3_5"] = len(hard)
        json.dump(s, open(out_dir / f"{task}.summary.json", "w"), indent=1)
        print(f"[eval] {a.tag or model} {task}: acc={100 * s['acc']:.1f} pass@{a.n}={100 * s['pass_at_n']:.1f}" + (f" L3-5={100 * s['acc_L3_5']:.1f}" if hard else "") +
              f" boxed={100 * s['boxed_rate']:.1f} hit_max={100 * s['hit_max_rate']:.1f} tok={s['mean_gen_tokens']:.0f} ({s['seconds']:.0f}s)", flush=True)

if __name__ == "__main__": main()
