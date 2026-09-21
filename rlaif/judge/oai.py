"""Minimal OpenAI-compatible chat client: stdlib only (urllib), retries, disk cache, usage/cost accounting.

Provider is chosen from $OAI_BASE_URL (default: OpenRouter, https://openrouter.ai/api/v1):
  openrouter  key $OPENROUTER_API_KEY (or $OAI_API_KEY); model ids like "openai/gpt-5.6-luna"; the response's usage.cost is
              the authoritative cost; reasoning models get {"reasoning": {"effort": ...}} (default $JUDGE_REASONING=minimal)
  openai      key $CS2881R_OPENAI_KEY_VAR -> $OPENAI_API_KEY_2 -> $OPENAI_API_KEY; reasoning models get reasoning_effort
  local       any other URL (vLLM etc.): key $OAI_API_KEY or "EMPTY", cost 0, no reasoning parameters
`.env` at the repo root is read for unset variables (values are never printed). urllib honours https_proxy / no_proxy.
Cache dir: $OAI_CACHE_DIR, default ~/.cache/cs2881r_oai. The cache key is the full request body, so a different model,
reasoning effort or prompt is a different entry. OAI_OFFLINE=1 serves cache hits only (no network).
Models named `claude-*` are routed to the Anthropic Messages API (ANTHROPIC_API_KEY / ANTHROPIC_API_KEY_2).
Accounts that come back "deactivated" / "terminated" / "insufficient_quota" / 402 fail fast instead of retrying.
`python rlaif/judge/oai.py [model]` sends one uncached test message and prints the usage summary.
"""
import hashlib, json, os, threading, time, urllib.error, urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

def _load_dotenv():
    p = REPO / ".env"
    if not p.exists(): return
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line: continue
        k, v = line.split("=", 1); k = k.strip(); v = v.strip().strip('"').strip("'")
        if k and k not in os.environ: os.environ[k] = v
_load_dotenv()

BASE_URL = os.environ.get("OAI_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
API = BASE_URL + "/chat/completions"
PROVIDER = "openrouter" if "openrouter.ai" in BASE_URL else ("openai" if "api.openai.com" in BASE_URL else "local")
LOCAL = PROVIDER == "local"
DEFAULT_MODEL = os.environ.get("JUDGE_MODEL", "openai/gpt-5.6-luna" if PROVIDER == "openrouter" else "gpt-4.1-mini")
REASONING_EFFORT = os.environ.get("JUDGE_REASONING", "low")     # none | minimal | low | medium | high
# extra completion budget for reasoning tokens (billed only when used); the visible max_tokens is added on top
REASONING_ALLOWANCE = {"none": 0, "minimal": 512, "low": 2048, "medium": 6144, "high": 16384}
PRICES = {  # USD per 1M tokens (input, cached input, output); list prices, approximate; fallback when the API reports no cost
    "gpt-4.1": (2.0, 0.5, 8.0), "gpt-4.1-mini": (0.4, 0.1, 1.6), "gpt-4.1-nano": (0.1, 0.025, 0.4),
    "gpt-4o-mini": (0.15, 0.075, 0.6), "gpt-4o": (2.5, 1.25, 10.0),
    "gpt-5": (1.25, 0.125, 10.0), "gpt-5-mini": (0.25, 0.025, 2.0), "gpt-5-nano": (0.05, 0.005, 0.4),
    "gpt-5.4-nano": (0.05, 0.005, 0.4), "gpt-5.4-mini": (0.25, 0.025, 2.0), "gpt-5.1": (1.25, 0.125, 10.0),
    "gpt-5.6-luna": (0.20, 0.02, 1.20),
    "claude-haiku-4-5": (1.0, 0.1, 5.0), "claude-sonnet-4-6": (3.0, 0.3, 15.0), "claude-sonnet-4-5": (3.0, 0.3, 15.0), "claude-sonnet-5": (3.0, 0.3, 15.0), "claude-opus-5": (5.0, 0.5, 25.0),
}
ANTHROPIC_API = "https://api.anthropic.com/v1/messages"
FATAL = ("deactivated", "terminated", "insufficient_quota", "billing_hard_limit", "invalid_api_key", "incorrect api key", "insufficient credits")
_lock = threading.Lock()
USAGE = {"calls": 0, "cached_calls": 0, "prompt_tokens": 0, "cached_prompt_tokens": 0, "completion_tokens": 0, "reasoning_tokens": 0,
         "cost_usd": 0.0, "price_unknown_models": set(), "errors": 0, "retries": 0}

def api_key(provider=None):
    provider = provider or PROVIDER
    if provider == "anthropic":
        var = os.environ.get("CS2881R_ANTHROPIC_KEY_VAR")
        for name in ([var] if var else []) + ["ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY_2"]:
            if name and os.environ.get(name): return os.environ[name]
        raise RuntimeError("no Anthropic key in environment (.env is read automatically)")
    if provider == "openrouter":
        for name in ("OPENROUTER_API_KEY", "OAI_API_KEY"):
            if os.environ.get(name): return os.environ[name]
        raise RuntimeError("no OpenRouter key: set OPENROUTER_API_KEY (in the environment or in .env at the repo root)")
    if provider == "local": return os.environ.get("OAI_API_KEY", "EMPTY")          # vLLM / local OpenAI-compatible server
    var = os.environ.get("CS2881R_OPENAI_KEY_VAR")
    for name in ([var] if var else []) + ["OPENAI_API_KEY_2", "OPENAI_API_KEY"]:
        if name and os.environ.get(name): return os.environ[name]
    raise RuntimeError("no OpenAI key in environment (.env is read automatically)")

def is_anthropic(model): return model.startswith("claude") or model.startswith("anthropic/")
def _bare(model): return model.split("/", 1)[1] if "/" in model else model
def is_reasoning(model): return (not LOCAL) and _bare(model).startswith(("gpt-5", "o1", "o3", "o4"))

def _cache_dir():
    d = Path(os.environ.get("OAI_CACHE_DIR", Path.home() / ".cache" / "cs2881r_oai")); d.mkdir(parents=True, exist_ok=True); return d

def _price(model):
    m = _bare(model); base = m
    for k in sorted(PRICES, key=len, reverse=True):
        if m == k or m.startswith(k + "-"): base = k; break
    return PRICES.get(base)

def _account(model, usage, cached_call):
    with _lock:
        USAGE["calls"] += 1; USAGE["cached_calls"] += int(cached_call)
        if cached_call: return
        pt = usage.get("prompt_tokens", 0) or 0; ct = usage.get("completion_tokens", 0) or 0
        det = usage.get("prompt_tokens_details") or {}
        cpt = det.get("cached_tokens") or usage.get("cached_tokens") or usage.get("cache_read_input_tokens") or 0
        rt = (usage.get("completion_tokens_details") or {}).get("reasoning_tokens") or usage.get("reasoning_tokens") or 0
        USAGE["prompt_tokens"] += pt; USAGE["cached_prompt_tokens"] += cpt; USAGE["completion_tokens"] += ct; USAGE["reasoning_tokens"] += rt
        if usage.get("cost") is not None:                       # OpenRouter reports the charged credits (USD) on every response
            USAGE["cost_usd"] += float(usage["cost"]); return
        pr = _price(model)
        if LOCAL and not is_anthropic(model): pr = (0.0, 0.0, 0.0)
        if pr: USAGE["cost_usd"] += ((pt - cpt) * pr[0] + cpt * pr[1] + ct * pr[2]) / 1e6
        else: USAGE["price_unknown_models"].add(model)

def usage_summary():
    with _lock:
        d = dict(USAGE); d["price_unknown_models"] = sorted(d["price_unknown_models"]); d["cost_usd"] = round(d["cost_usd"], 6); return d

def _headers():
    h = {"Authorization": "Bearer " + api_key(), "Content-Type": "application/json"}
    if PROVIDER == "openrouter": h.update({"HTTP-Referer": "https://github.com/TBOO-Y/cs2881r-sheldon-sft", "X-Title": "cs2881r-sheldon-rlaif"})
    return h

def chat(model, messages, *, temperature=None, top_p=None, max_tokens=400, json_mode=False, reasoning_effort=None,
         seed=None, cache=True, cache_salt="", timeout=45, retries=6, verbosity=None):
    if is_anthropic(model):
        return _anthropic_chat(model, messages, temperature=temperature, top_p=top_p, max_tokens=max_tokens, json_mode=json_mode, cache=cache, cache_salt=cache_salt, timeout=timeout, retries=retries)
    body = {"model": model, "messages": messages}
    if is_reasoning(model):
        eff = reasoning_effort or REASONING_EFFORT
        total = max_tokens + REASONING_ALLOWANCE.get(eff, 2048)
        if PROVIDER == "openrouter":
            body["max_tokens"] = total; body["reasoning"] = {"effort": eff}
        else:
            body["max_completion_tokens"] = total; body["reasoning_effort"] = eff
        if verbosity: body["verbosity"] = verbosity
    else:
        body["max_tokens"] = max_tokens
        if temperature is not None: body["temperature"] = temperature
        if top_p is not None: body["top_p"] = top_p
    if seed is not None: body["seed"] = seed
    if json_mode: body["response_format"] = {"type": "json_object"}
    key = hashlib.sha256((json.dumps(body, sort_keys=True, ensure_ascii=False) + "|" + cache_salt).encode()).hexdigest()
    cpath = _cache_dir() / (key + ".json")
    if cache and cpath.exists():
        try:
            r = json.loads(cpath.read_text()); _account(model, {}, True); r["cached"] = True; return r
        except Exception: pass
    if os.environ.get("OAI_OFFLINE"): raise RuntimeError("OAI_OFFLINE set and no cache hit")
    data = json.dumps(body).encode(); last = None
    for attempt in range(retries):
        req = urllib.request.Request(API, data=data, headers=_headers())
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp: out = json.load(resp)
            if "choices" not in out:                             # OpenRouter returns 200 with an error object for some upstream failures
                err = json.dumps(out.get("error", out))[:300]
                if any(k in err.lower() for k in FATAL): raise RuntimeError(f"{PROVIDER} error for {model}: {err}")
                last = f"no choices: {err}"; raise ValueError(last)
            ch = out["choices"][0]; usage = out.get("usage", {}) or {}
            r = {"text": ch["message"].get("content") or "", "finish": ch.get("finish_reason"), "model": out.get("model", model), "usage": usage, "cached": False}
            _account(model, usage, False)
            if cache and r["text"].strip():
                tmp = cpath.with_suffix(".tmp" + str(threading.get_ident())); tmp.write_text(json.dumps(r, ensure_ascii=False)); tmp.replace(cpath)
            return r
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")[:500]
            if (e.code in (400, 401, 402, 403, 404) and "rate" not in msg.lower()) or any(k in msg.lower() for k in FATAL):
                with _lock: USAGE["errors"] += 1
                raise RuntimeError(f"{PROVIDER} HTTP {e.code} for {model}: {msg}")
            last = f"HTTP {e.code}: {msg[:200]}"
        except RuntimeError: raise
        except Exception as e:
            last = f"{type(e).__name__}: {str(e)[:200]}"
        with _lock: USAGE["retries"] += 1
        time.sleep(min(60, 2 ** attempt + 0.5 * attempt))
    with _lock: USAGE["errors"] += 1
    raise RuntimeError(f"{PROVIDER} call failed after {retries} attempts ({model}): {last}")

def _anthropic_chat(model, messages, *, temperature=None, top_p=None, max_tokens=400, json_mode=False, cache=True, cache_salt="", timeout=120, retries=6):
    system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
    if json_mode: system = (system + "\n\n" if system else "") + "Respond with a single JSON object and nothing else: no prose, no markdown fences."
    msgs = [{"role": m["role"], "content": m["content"]} for m in messages if m["role"] != "system"]
    body = {"model": _bare(model) if model.startswith("anthropic/") else model, "max_tokens": max_tokens, "messages": msgs}
    if system: body["system"] = [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]
    if temperature is not None: body["temperature"] = temperature
    elif top_p is not None: body["top_p"] = top_p
    key = hashlib.sha256((json.dumps(body, sort_keys=True, ensure_ascii=False) + "|" + cache_salt).encode()).hexdigest()
    cpath = _cache_dir() / (key + ".json")
    if cache and cpath.exists():
        try:
            r = json.loads(cpath.read_text()); _account(model, {}, True); r["cached"] = True; return r
        except Exception: pass
    if os.environ.get("OAI_OFFLINE"): raise RuntimeError("OAI_OFFLINE set and no cache hit")
    data = json.dumps(body).encode(); last = None
    for attempt in range(retries):
        req = urllib.request.Request(ANTHROPIC_API, data=data, headers={"x-api-key": api_key("anthropic"), "anthropic-version": "2023-06-01", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp: out = json.load(resp)
            text = "".join(b.get("text", "") for b in out.get("content", []) if b.get("type") == "text"); u = out.get("usage", {})
            usage = {"prompt_tokens": u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0),
                     "completion_tokens": u.get("output_tokens", 0), "cache_read_input_tokens": u.get("cache_read_input_tokens", 0), "raw": u}
            fin = {"end_turn": "stop", "max_tokens": "length"}.get(out.get("stop_reason"), out.get("stop_reason"))
            r = {"text": text, "finish": fin, "model": out.get("model", model), "usage": usage, "cached": False}
            _account(model, usage, False)
            if cache:
                tmp = cpath.with_suffix(".tmp" + str(threading.get_ident())); tmp.write_text(json.dumps(r, ensure_ascii=False)); tmp.replace(cpath)
            return r
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")[:500]
            if e.code in (400, 401, 403, 404) or any(k in msg.lower() for k in FATAL):
                with _lock: USAGE["errors"] += 1
                raise RuntimeError(f"Anthropic HTTP {e.code} for {model}: {msg}")
            last = f"HTTP {e.code}: {msg[:200]}"
        except Exception as e:
            last = f"{type(e).__name__}: {str(e)[:200]}"
        time.sleep(min(60, 2 ** attempt + 0.5 * attempt))
    with _lock: USAGE["errors"] += 1
    raise RuntimeError(f"Anthropic call failed after {retries} attempts ({model}): {last}")

def parse_json(text):
    """Lenient JSON extraction from a judge reply."""
    import re
    t = text.strip(); t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t)
    try: return json.loads(t)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", t, re.S)
        if m: return json.loads(m.group(0))
        raise

if __name__ == "__main__":
    import sys
    m = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MODEL
    print(f"provider={PROVIDER} base={BASE_URL} model={m} reasoning={'yes, effort=' + REASONING_EFFORT if is_reasoning(m) else 'no'}")
    kw = {} if (is_reasoning(m) or is_anthropic(m)) else {"temperature": 0}
    t0 = time.time(); r = chat(m, [{"role": "user", "content": "Reply with the single word OK."}], max_tokens=20, cache=False, **kw)
    print(r["model"], repr(r["text"]), "finish=", r["finish"], f"{time.time()-t0:.1f}s"); print("usage:", json.dumps(r["usage"])[:400]); print(usage_summary())
    r2 = chat(m, [{"role": "system", "content": "Output only JSON."}, {"role": "user", "content": 'Return {"winner": "A", "n": 2}.'}], max_tokens=40, json_mode=True, cache=False, **kw)
    print("json_mode:", repr(r2["text"]), "->", parse_json(r2["text"]))
