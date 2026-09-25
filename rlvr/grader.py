#!/usr/bin/env python3
"""Verifiable-reward grader for competition-math answers.

grade(response, gold) -> {"boxed": str|None, "correct": bool, "method": "exact"|"math_verify"|"none"}
  1. take the LAST \\boxed{...} (brace-balanced; \\fbox too) of the response; no box -> wrong (the seed boxes 99.8% of its
     answers, so a missing box is a format failure we want penalised, not repaired)
  2. exact fast path on a conservative normalisation of both strings (whitespace, \\left/\\right, \\dfrac, ^\\circ, \\%, $, trailing '.')
  3. otherwise math-verify (huggingface/Math-Verify): symbolic / numeric equivalence with its own parsing + verify timeouts;
     the gold is wrapped in \\boxed{} before parsing (Skywork-OR1 practice: parsing raw gold changes some expressions)
grade_many(pairs, workers) runs the same thing in a process pool with a hard per-task timeout, because sympy can hang on
pathological inputs and the reward step must never stall a training run.
  python rlvr/grader.py --selftest      # runs the case table below (must-cases fail the exit code, info-cases only print)
"""
import argparse, json, multiprocessing as mp, re, sys, time

BOX_CMDS = ("\\boxed", "\\fbox")

def last_boxed(s: str, _start=None):
    """Content of the last NON-EMPTY \\boxed{...} / \\fbox{...} in s (brace-balanced), or None. Also accepts \\boxed 5 (no braces).
    An empty trailing \\boxed{} (a restated instruction) is skipped in favour of an earlier box."""
    if not isinstance(s, str): return None
    i = max(s.rfind(c, 0, _start) for c in BOX_CMDS)
    if i < 0: return None
    j = i + len(next(c for c in BOX_CMDS if s.startswith(c, i)))
    while j < len(s) and s[j] == " ": j += 1
    if j >= len(s): return None
    if s[j] != "{":                                   # \boxed 5
        m = re.match(r"[^\s$\\]+", s[j:]); return m.group(0) if m else None
    depth, out = 1, []; j += 1
    while j < len(s) and depth:
        c = s[j]
        if c == "{": depth += 1
        elif c == "}": depth -= 1
        if depth: out.append(c)
        j += 1
    content = "".join(out) if depth == 0 else None
    if content is not None and content.strip() == "": return last_boxed(s, i)     # skip an empty box, look further back
    return content

_SUBS = [(r"\\left", ""), (r"\\right", ""), (r"\\!", ""), (r"\\,", ""), (r"\\;", ""), (r"\\:", ""), (r"\\ ", ""), (r"~", ""),
         (r"\\dfrac", r"\\frac"), (r"\\tfrac", r"\\frac"), (r"\^\{\\circ\}", ""), (r"\^\\circ", ""), (r"\\%", ""), (r"\\\$", ""),
         (r"\$", ""), (r"\\text\{\s*\}", ""), (r"\\mathrm\{([^}]*)\}", r"\1"), (r"\\textbf\{([^}]*)\}", r"\1"), (r"\\text\{([^}]*)\}", r"\1"),
         (r"\\displaystyle", ""), (r"\s+", "")]

def normalize(s: str) -> str:
    """Conservative canonical form for the exact-match fast path (never used to declare two *different* answers equal by
    itself beyond these cosmetic rewrites)."""
    if s is None: return ""
    s = s.strip()
    for pat, rep in _SUBS: s = re.sub(pat, rep, s)
    s = s.rstrip(".")
    if s.startswith("x=") and "," not in s and "=" not in s[2:]: s = s[2:]   # x=3 vs 3 (single-variable answers)
    if re.fullmatch(r"-?\d+\.0+", s): s = s.split(".")[0]                    # 5.0 -> 5
    if re.fullmatch(r"-?\d{1,3}(,\d{3})+", s): s = s.replace(",", "")        # 1,000 -> 1000
    return s

def _math_verify(gold: str, pred: str, timeout_s: float = 5.0) -> bool:
    from math_verify import parse, verify
    t = max(1, int(round(timeout_s)))                    # math-verify's timeouts are signal.alarm ints; a float breaks parsing silently
    g = parse("\\boxed{" + gold + "}", parsing_timeout=t)
    p = parse("\\boxed{" + pred + "}", parsing_timeout=t)
    if not g or not p: return False
    return bool(verify(g, p, timeout_seconds=t))

def grade(response: str, gold: str, timeout_s: float = 5.0) -> dict:
    box = last_boxed(response)
    if box is None: return {"boxed": None, "correct": False, "method": "none"}
    ng, nb = normalize(gold), normalize(box)
    if nb == ng and nb != "": return {"boxed": box, "correct": True, "method": "exact"}
    try: ok = _math_verify(gold, box, timeout_s)
    except Exception: ok = False
    return {"boxed": box, "correct": bool(ok), "method": "math_verify"}

def _grade_star(args):
    return grade(*args)

def _exact_only(r, g):
    box = last_boxed(r); ok = box is not None and normalize(box) == normalize(g) != ""
    return {"boxed": box, "correct": ok, "method": "exact-fallback"}

def grade_many(pairs, workers: int = 8, timeout_s: float = 5.0, hard_timeout_s: float = 20.0):
    """pairs: list of (response, gold). One task per pair in a forked pool (maxtasksperchild so a leaking sympy worker is
    recycled) against a shared wall-clock deadline; a pair that has not returned by then gets the exact-only fallback
    (method "exact-fallback", counted by the caller), every other pair keeps its real verdict. The pool is terminated at the
    end so a hung worker cannot outlive the step."""
    pairs = [(r, g, timeout_s) for r, g in pairs]
    if workers <= 1 or len(pairs) < 4: return [grade(*p) for p in pairs]
    ctx = mp.get_context("fork")
    out = [None] * len(pairs)
    pool = ctx.Pool(processes=workers, maxtasksperchild=64)
    try:
        deadline = time.monotonic() + hard_timeout_s + 2.0 * timeout_s * len(pairs) / workers
        results = [pool.apply_async(_grade_star, (p,)) for p in pairs]
        for k, res in enumerate(results):
            try: out[k] = res.get(timeout=max(0.0, deadline - time.monotonic()))
            except mp.TimeoutError: out[k] = _exact_only(pairs[k][0], pairs[k][1])
            except Exception: out[k] = _exact_only(pairs[k][0], pairs[k][1])
    finally:
        pool.terminate(); pool.join()
    return out

# (gold, response, expected_correct, must)  -- must=False cases document verifier behaviour without failing the selftest
CASES = [
    ("\\frac{1}{2}", "so \\boxed{\\frac{1}{2}}", True, True),
    ("\\frac{1}{2}", "so \\boxed{\\dfrac{1}{2}}", True, True),
    ("\\frac{1}{2}", "so \\boxed{1/2}", True, True),
    ("\\frac{1}{2}", "so \\boxed{0.5}", True, True),
    ("\\frac{1}{2}", "so \\boxed{\\frac{2}{4}}", True, True),
    ("\\frac{1}{2}", "so \\boxed{\\frac{1}{3}}", False, True),
    ("3", "the answer is 3", False, True),                            # unboxed -> wrong by design
    ("3", "\\boxed{2} ... wait, \\boxed{3}", True, True),             # last box wins
    ("3", "\\boxed{3}.", True, True),
    ("3", "\\boxed{3.0}", True, True),
    ("3", "\\boxed{x = 3}", True, True),
    ("3", "\\boxed{-3}", False, True),
    ("1000", "\\boxed{1,000}", True, True),
    ("2\\sqrt{13}", "\\boxed{2\\sqrt{13}}", True, True),
    ("2\\sqrt{13}", "\\boxed{\\sqrt{52}}", True, False),
    ("\\sqrt{2}", "\\boxed{1.4142}", False, True),                    # decimals are not accepted for irrationals
    ("[0, 1)", "\\boxed{[0,1)}", True, True),
    ("(-\\infty, 2]", "\\boxed{(-\\infty,2]}", True, True),
    ("(-\\infty, 2]", "\\boxed{x \\le 2}", True, False),
    ("\\{1, 2, 3\\}", "\\boxed{\\{3,2,1\\}}", True, False),
    ("(1, 2)", "\\boxed{(1,2)}", True, True),
    ("(1, 2)", "\\boxed{(2,1)}", False, True),
    ("90^\\circ", "\\boxed{90}", True, True),
    ("10\\%", "\\boxed{10}", True, True),
    ("\\$5", "\\boxed{5}", True, True),
    ("5", "\\boxed{\\$5.00}", True, True),
    ("\\text{(C)}", "\\boxed{C}", True, False),
    ("\\text{C}", "\\boxed{\\text{C}}", True, True),
    ("x^2 + 2x + 1", "\\boxed{(x+1)^2}", True, True),
    ("\\frac{\\pi}{2}", "\\boxed{\\pi/2}", True, True),
    ("\\begin{pmatrix} 1 \\\\ 2 \\end{pmatrix}", "\\boxed{\\begin{pmatrix}1\\\\2\\end{pmatrix}}", True, True),
    ("12", "\\boxed{12 \\text{ inches}}", True, False),
    ("0.\\overline{3}", "\\boxed{\\frac{1}{3}}", True, False),
    ("\\frac{1}{3}", "\\boxed{0.333}", False, True),
    ("36", "\\boxed{36}\\boxed{37}", False, True),
    ("36", "\\boxed{6^2}", True, True),
    ("-\\frac{1}{2}", "\\boxed{-0.5}", True, True),
    ("1", "\\boxed{}", False, True),
    ("1", "\\boxed{1", False, True),                                  # unbalanced -> no box
    ("7", "\\boxed{7}. Remember to put your final answer within \\boxed{}.", True, True),   # trailing empty box is skipped
    ("a; b", "\\boxed{a;b}", True, True),                              # semicolons survive normalisation
]

def selftest(verbose=True):
    fails = 0; rows = []
    for gold, resp, exp, must in CASES:
        r = grade(resp, gold); ok = r["correct"] == exp
        if must and not ok: fails += 1
        rows.append((("PASS" if ok else ("FAIL" if must else "info")), gold, resp, exp, r["correct"], r["method"]))
    if verbose:
        for row in rows: print("%-4s gold=%-40r resp=%-48r expected=%-5s got=%-5s via %s" % row)
        print(f"selftest: {sum(1 for r in rows if r[0]=='PASS')}/{len(rows)} as expected, {fails} must-case failures")
    return fails

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--selftest", action="store_true"); ap.add_argument("--gold"); ap.add_argument("--response")
    a = ap.parse_args()
    if a.selftest: sys.exit(1 if selftest() else 0)
    print(json.dumps(grade(a.response or "", a.gold or "")))
