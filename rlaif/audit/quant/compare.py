#!/usr/bin/env python3
"""Checkpoint monitor for the RLAIF stage (persona_audit.md §6.7): compare any generation files on the collapse and defect metrics.

usage: python rlaif/audit/quant/compare.py name1=path1.jsonl name2=path2.jsonl ... [--gold path_with_reference]
Each file: rows with {id, response, hit_max?, kind?, messages}. Metrics: opener entropy / distinct openers / template-opener coverage,
joke-meta, relent block, Tuesday-Thai, exit-line closer, hit_max, mid-sentence endings, mean words, Bazinga, name breadth,
warm closers, plus the mean deterministic rule penalty and batch tax from rlaif/reward/rules.py.
"""
import collections, json, math, re, statistics, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from reward.rules import score_rules, BatchTax, W, NAME_RE
from reward.reward import style_metrics

def load(p):
    rows = [json.loads(l) for l in open(p)]
    return {r["id"]: r for r in rows}

def prompt_of(r): return next((m["content"] for m in r.get("messages", []) if m["role"] == "user"), "")

def main():
    args = [a for a in sys.argv[1:] if "=" in a]; gold_path = None
    if "--gold" in sys.argv: gold_path = sys.argv[sys.argv.index("--gold") + 1]
    systems = {a.split("=", 1)[0]: load(a.split("=", 1)[1]) for a in args}
    if gold_path:
        g = load(gold_path); systems["gold"] = {i: {**r, "response": r.get("reference") or r.get("gold"), "hit_max": False} for i, r in g.items() if (r.get("reference") or r.get("gold"))}
    ids = set.intersection(*[set(s) for s in systems.values()]) if systems else set()
    ids = sorted(i for i in ids if systems[next(iter(systems))][i].get("kind") != "ood_short")
    print(f"{len(ids)} common ids\n")
    table = {}
    for name, S in systems.items():
        comps = [S[i]["response"] for i in ids]; m = style_metrics(comps)
        m["hit_max%"] = 100 * sum(1 for i in ids if S[i].get("hit_max")) / max(1, len(ids))
        rules = [score_rules(prompt_of(S[i]), S[i]["response"], S[i].get("kind"), "length" if S[i].get("hit_max") else None) for i in ids]
        m["rule_penalty"] = statistics.mean(r["penalty"] for r in rules); m["batch_tax"] = statistics.mean(BatchTax().tax(comps))
        for t in ("preamble", "length", "canon", "tool_voice", "constraint", "false_claim", "repetition", "truncation"):
            m["term/" + t] = statistics.mean(r["terms"][t] for r in rules)
        table[name] = m
    keys = list(next(iter(table.values())).keys())
    print(f"{'metric':32s}" + "".join(f"{n:>12s}" for n in table))
    for k in keys:
        print(f"{k:32s}" + "".join(f"{table[n][k]:12.3f}" for n in table))

if __name__ == "__main__": main()
