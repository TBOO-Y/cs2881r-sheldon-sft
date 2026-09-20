"""Minimal OpenAI chat client: stdlib only (urllib), retries, disk cache, usage/cost accounting.

Key lookup order: $CS2881R_OPENAI_KEY_VAR (name of the variable to use) -> OPENAI_API_KEY_2 -> OPENAI_API_KEY.
The project's primary OPENAI_API_KEY returned 401 on 2026-09-19; OPENAI_API_KEY_2 works. `.env` at the repo
root is read for unset variables (values are never printed). Proxy: urllib honours https_proxy/no_proxy.
Cache dir: $OAI_CACHE_DIR, default ~/.cache/cs2881r_oai (on the cluster set it under /data/agastyas).
Models named `claude-*` are routed to the Anthropic Messages API (ANTHROPIC_API_KEY / ANTHROPIC_API_KEY_2) with the same
return format; the long system prompt is marked for prompt caching. OAI_OFFLINE=1 serves cache hits only (no network).
Accounts that come back "deactivated" / "terminated" / "insufficient_quota" fail fast instead of retrying.
"""
import hashlib, json, os, threading, time, urllib.error, urllib.request
from pathlib import Path

BASE_URL = os.environ.get("OAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
API = BASE_URL + "/chat/completions"
LOCAL = "api.openai.com" not in BASE_URL
REPO = Path(__file__).resolve().parents[2]
PRICES = {  # USD per 1M tokens (input, cached input, output); list prices, approximate
    "gpt-4.1": (2.0, 0.5, 8.0), "gpt-4.1-mini": (0.4, 0.1, 1.6), "gpt-4.1-nano": (0.1, 0.025, 0.4),
    "gpt-4o-mini": (0.15, 0.075, 0.6), "gpt-4o": (2.5, 1.25, 10.0),
    "gpt-5": (1.25, 0.125, 10.0), "gpt-5-mini": (0.25, 0.025, 2.0), "gpt-5-nano": (0.05, 0.005, 0.4),
    "gpt-5.4-nano": (0.05, 0.005, 0.4), "gpt-5.4-mini": (0.25, 0.025, 2.0), "gpt-5.1": (1.25, 0.125, 10.0),
    "claude-haiku-4-5": (1.0, 0.1, 5.0), "claude-sonnet-4-6": (3.0, 0.3, 15.0), "claude-sonnet-4-5": (3.0, 0.3, 15.0), "claude-sonnet-5": (3.0, 0.3, 15.0), "claude-opus-5": (5.0, 0.5, 25.0),
}
ANTHROPIC_API = "https://api.anthropic.com/v1/messages"
FATAL = ("deactivated", "terminated", "insufficient_quota", "billing_hard_limit", "invalid_api_key", "incorrect api key")
_lock = threading.Lock()
USAGE = {"calls": 0, "cached_calls": 0, "prompt_tokens": 0, "cached_prompt_tokens": 0, "completion_tokens": 0,
         "cost_usd": 0.0, "price_unknown_models": set(), "errors": 0}

def _load_dotenv():
    p = REPO / ".env"
    if not p.exists(): return
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line: continue
        k, v = line.split("=", 1); k = k.strip(); v = v.strip().strip('"').strip("'")
        if k and k not in os.environ: os.environ[k] = v

def api_key(provider="openai"):
    _load_dotenv()
    if provider == "anthropic":
        var = os.environ.get("CS2881R_ANTHROPIC_KEY_VAR")
        for name in ([var] if var else []) + ["ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY_2"]:
            if name and os.environ.get(name): return os.environ[name]
        raise RuntimeError("no Anthropic key in environment (.env is read automatically)")
    if LOCAL: return os.environ.get("OAI_API_KEY", "EMPTY")          # vLLM / local OpenAI-compatible server
    var = os.environ.get("CS2881R_OPENAI_KEY_VAR")
    for name in ([var] if var else []) + ["OPENAI_API_KEY_2", "OPENAI_API_KEY"]:
        if name and os.environ.get(name): return os.environ[name]
    raise RuntimeError("no OpenAI key in environment (.env is read automatically)")

def is_anthropic(model): return model.startswith("claude")

def _cache_dir():
    d = Path(os.environ.get("OAI_CACHE_DIR", Path.home() / ".cache" / "cs2881r_oai")); d.mkdir(parents=True, exist_ok=True); return d

def _price(model):
    base = model
    for k in sorted(PRICES, key=len, reverse=True):
        if model == k or model.startswith(k + "-"): base = k; break
    return PRICES.get(base)

def _account(model, usage, cached_call):
    with _lock:
        USAGE["calls"] += 1; USAGE["cached_calls"] += int(cached_call)
        if cached_call: return
        pt = usage.get("prompt_tokens", 0); ct = usage.get("completion_tokens", 0)
        cpt = (usage.get("prompt_tokens_details") or {}).get("cached_tokens", 0) or usage.get("cache_read_input_tokens", 0)
        USAGE["prompt_tokens"] += pt; USAGE["cached_prompt_tokens"] += cpt; USAGE["completion_tokens"] += ct
        pr = _price(model)
        if LOCAL and not is_anthropic(model): pr = (0.0, 0.0, 0.0)
        if pr: USAGE["cost_usd"] += ((pt - cpt) * pr[0] + cpt * pr[1] + ct * pr[2]) / 1e6
        else: USAGE["price_unknown_models"].add(model)

def usage_summary():
    with _lock:
        d = dict(USAGE); d["price_unknown_models"] = sorted(d["price_unknown_models"]); d["cost_usd"] = round(d["cost_usd"], 4); return d

def is_reasoning(model): return (not LOCAL) and model.startswith(("gpt-5", "o1", "o3", "o4"))

def chat(model, messages, *, temperature=None, top_p=None, max_tokens=400, json_mode=False, reasoning_effort=None,
         seed=None, cache=True, cache_salt="", timeout=120, retries=6, verbosity=None):
    if is_anthropic(model):
        return _anthropic_chat(model, messages, temperature=temperature, top_p=top_p, max_tokens=max_tokens, json_mode=json_mode, cache=cache, cache_salt=cache_salt, timeout=timeout, retries=retries)
    body = {"model": model, "messages": messages}
    if is_reasoning(model):
        body["max_completion_tokens"] = max_tokens
        if reasoning_effort: body["reasoning_effort"] = reasoning_effort
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
        req = urllib.request.Request(API, data=data, headers={"Authorization": "Bearer " + api_key(), "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp: out = json.load(resp)
            ch = out["choices"][0]; usage = out.get("usage", {})
            r = {"text": ch["message"].get("content") or "", "finish": ch.get("finish_reason"), "model": out.get("model", model), "usage": usage, "cached": False}
            _account(model, usage, False)
            if cache:
                tmp = cpath.with_suffix(".tmp" + str(threading.get_ident())); tmp.write_text(json.dumps(r, ensure_ascii=False)); tmp.replace(cpath)
            return r
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")[:500]
            if (e.code in (400, 401, 403, 404) and "rate" not in msg.lower()) or any(k in msg.lower() for k in FATAL):
                with _lock: USAGE["errors"] += 1
                raise RuntimeError(f"OpenAI HTTP {e.code} for {model}: {msg}")
            last = f"HTTP {e.code}: {msg[:200]}"
        except Exception as e:
            last = f"{type(e).__name__}: {str(e)[:200]}"
        time.sleep(min(60, 2 ** attempt + 0.5 * attempt))
    with _lock: USAGE["errors"] += 1
    raise RuntimeError(f"OpenAI call failed after {retries} attempts ({model}): {last}")

def _anthropic_chat(model, messages, *, temperature=None, top_p=None, max_tokens=400, json_mode=False, cache=True, cache_salt="", timeout=120, retries=6):
    system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
    if json_mode: system = (system + "\n\n" if system else "") + "Respond with a single JSON object and nothing else: no prose, no markdown fences."
    msgs = [{"role": m["role"], "content": m["content"]} for m in messages if m["role"] != "system"]
    body = {"model": model, "max_tokens": max_tokens, "messages": msgs}
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
    m = sys.argv[1] if len(sys.argv) > 1 else "gpt-4.1-nano"
    kw = {"reasoning_effort": "minimal"} if is_reasoning(m) else {"temperature": 0}
    if is_anthropic(m): kw = {"temperature": 0}
    r = chat(m, [{"role": "user", "content": "Reply with the single word OK."}], max_tokens=20, cache=False, **kw)
    print(r["model"], repr(r["text"]), r["usage"].get("prompt_tokens"), r["usage"].get("completion_tokens")); print(usage_summary())
