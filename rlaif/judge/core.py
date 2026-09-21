"""Judge calls used by calibration and by the RLAIF reward (persona_audit.md §6.1, §6.5).

  task_gate(model, prompt, reply)         -> dict with task_score in [0,1], gate (0/1), flags
  persona_pair(model, prompt, a, b)       -> dict: p_a (prob A preferred, from both orders), consistent, raw verdicts
Both are cached on disk through oai.chat, so repeated evaluation of the same text is free."""
import hashlib, json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from judge import oai
from judge.oai import chat, parse_json, is_reasoning
from judge.prompts import persona_pairwise_messages, task_gate_messages

REASONING_EFFORT = None      # None -> oai.REASONING_EFFORT ($JUDGE_REASONING, default "minimal"); set_reasoning_effort() overrides
def set_reasoning_effort(effort):
    global REASONING_EFFORT; REASONING_EFFORT = effort

def _kw(model, temperature):
    return {"reasoning_effort": REASONING_EFFORT or oai.REASONING_EFFORT} if is_reasoning(model) else {"temperature": temperature}

def _mock(model, *parts):
    """Deterministic offline stand-in (model == "mock"): no network, no cost. Used by the CPU dry run and smoke tests."""
    h = int(hashlib.sha256("|".join(str(x) for x in parts).encode()).hexdigest(), 16)
    return {"text": "", "usage": {}, "mock": True, "h": h}

STATUS = {"done": 1.0, "partial": 0.5, "not": 0.0}

def task_gate(model, prompt, reply, prior_turns=None, temperature=0.0, max_tokens=500):
    if model == "mock":
        h = _mock(model, "gate", prompt, reply)["h"]; words = len(reply.split())
        return {"ok": True, "task_score": 1.0 if words > 8 else 0.5, "gate": 1, "refused": False, "worse_off": False, "contradiction": (h % 7 == 0), "contradiction_quotes": [],
                "false_claim": (h % 11 == 0), "false_claim_quote": "", "main_answer": reply[:40], "asks": [{"ask": "respond", "status": "done" if words > 8 else "partial"}], "usage": {}}
    r = chat(model, task_gate_messages(prompt, reply, prior_turns), max_tokens=max_tokens, json_mode=True, **_kw(model, temperature))
    try: j = parse_json(r["text"])
    except Exception: return {"ok": False, "raw": r["text"], "task_score": None, "gate": None}
    asks = [a for a in (j.get("asks") or []) if isinstance(a, dict)]
    if asks: score = sum(STATUS.get(str(a.get("status", "")).lower(), 0.0) for a in asks) / len(asks)
    else: score = 1.0 if (j.get("main_answer") or "").strip() else 0.5
    refused, worse = bool(j.get("refused")), bool(j.get("worse_off"))
    contra, false_claim = bool(j.get("contradiction")), bool(j.get("false_claim_about_user"))
    gate = 0 if (refused or worse) else 1
    return {"ok": True, "task_score": score, "gate": gate, "refused": refused, "worse_off": worse, "contradiction": contra,
            "contradiction_quotes": j.get("contradiction_quotes") or [], "false_claim": false_claim,
            "false_claim_quote": j.get("false_claim_quote") or "", "worse_off_quote": j.get("worse_off_quote") or "", "main_answer": j.get("main_answer") or "", "asks": asks, "usage": r["usage"]}

def _one_order(model, prompt, a, b, prior_turns, temperature, max_tokens, brief=False):
    if model == "mock":   # prefers the longer reply with a little hash noise, identical in both orders (no position bias)
        la, lb = len(a.split()), len(b.split()); h = _mock(model, "pair", prompt, min(a, b), max(a, b))["h"]
        w = "A" if (la + (h % 5) > lb + ((h >> 8) % 5)) else "B"
        return {"ok": True, "winner": w, "confidence": "low", "items": {k: w for k in ("answer_first", "template", "register_whole")}, "summary": "mock", "usage": {}}
    r = chat(model, persona_pairwise_messages(prompt, a, b, prior_turns, brief=brief), max_tokens=max_tokens, json_mode=True, **_kw(model, temperature))
    try:
        j = parse_json(r["text"]); w = str(j.get("winner", "")).strip().upper()[:1]
        if w not in ("A", "B"): return {"ok": False, "raw": r["text"]}
        items = {k: (str(v.get("better", "tie")) if isinstance(v, dict) else str(v)).strip().upper()[:1] for k, v in (j.get("items") or {}).items()}
        return {"ok": True, "winner": w, "confidence": j.get("confidence", ""), "items": items, "summary": j.get("summary", ""), "usage": r["usage"]}
    except Exception: return {"ok": False, "raw": r["text"]}

def persona_verdict(model, prompt, a, b, prior_turns=None, temperature=0.0, max_tokens=700, brief=False):
    """One presentation order (a shown as A, b as B). The reward submits the two orders of a pair as separate jobs."""
    return _one_order(model, prompt, a, b, prior_turns, temperature, max_tokens, brief)

def persona_pair(model, prompt, a, b, prior_turns=None, temperature=0.0, max_tokens=700, brief=False):
    """Judge (a vs b) in both presentation orders. p_a = fraction of valid verdicts preferring a."""
    o1 = _one_order(model, prompt, a, b, prior_turns, temperature, max_tokens, brief)   # a shown as A
    o2 = _one_order(model, prompt, b, a, prior_turns, temperature, max_tokens, brief)   # a shown as B
    votes = []
    if o1.get("ok"): votes.append(1.0 if o1["winner"] == "A" else 0.0)
    if o2.get("ok"): votes.append(1.0 if o2["winner"] == "B" else 0.0)
    p_a = sum(votes) / len(votes) if votes else None
    # per-item margin for a: +1 when a wins the item, -1 when b wins, 0 tie (averaged over orders)
    items = {}
    for o, a_label in ((o1, "A"), (o2, "B")):
        if not o.get("ok"): continue
        for k, v in o["items"].items():
            items.setdefault(k, []).append(1.0 if v == a_label else (-1.0 if v in ("A", "B") else 0.0))
    items = {k: sum(v) / len(v) for k, v in items.items()}
    return {"p_a": p_a, "n_valid": len(votes), "consistent": (len(votes) == 2 and votes[0] == votes[1]), "first_pos_pick_A": [o.get("winner") for o in (o1, o2)], "items": items, "orders": [o1, o2]}
