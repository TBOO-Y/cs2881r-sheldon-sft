#!/usr/bin/env python3
"""Verifiable math reward for TRL's GRPOTrainer (signature verified against TRL 1.13.0: reward funcs are called as
f(prompts=, completions=, completion_ids=, **dataset_columns, trainer_state=, log_extra=, log_metric=) with each RANK's slice of
the generation batch (TRL gathers the rewards afterwards). train_rlvr.py asserts that a rank holds whole prompt groups, so the
per-group metrics below are exact; TRL averages the logged metrics across ranks.

Per completion:
  * truncated (last token is not EOS/pad)  ->  None  = "unscorable" in TRL: excluded from the group mean/std (nan-aware),
    advantage forced to 0; together with GRPOConfig.mask_truncated_completions=True its tokens leave the loss and the
    denominator too. A group of 8 with one truncation therefore behaves as a group of 7 (the plan's semantics).
  * terminated  ->  correctness in {0, 1} from rlvr/grader.py  [+ DAPO soft overlong penalty when length_penalty == "dapo":
        0                                   if L <= L_max - L_cache
        ((L_max - L_cache) - L) / L_cache   otherwise (linear to -1 at L_max)         DAPO Eq. 13; DAPO uses L_cache 4096 of 20480]
Metrics (via log_metric, averaged across processes by TRL): accuracy over scorable completions, truncation rate, boxed rate,
mean completion length split by correctness, per-group pass-rate histogram (all-0 / all-1 / mixed among scorable rollouts).
"""
from collections import defaultdict
from .grader import grade_many, last_boxed

class MathReward:
    __name__ = "math_correct"

    def __init__(self, eos_ids, max_completion_length, length_penalty="none", l_cache=512, workers=8, grade_timeout_s=5.0):
        assert length_penalty in ("none", "dapo")
        self.eos_ids = set(int(e) for e in eos_ids if e is not None)
        self.max_len = int(max_completion_length); self.length_penalty = length_penalty; self.l_cache = int(l_cache)
        self.workers = workers; self.timeout = grade_timeout_s
        self.calls = 0

    def is_truncated(self, ids):
        return len(ids) == 0 or int(ids[-1]) not in self.eos_ids     # mirrors TRL's own rule (ids[-1] not in {eos, pad})

    def overlong_penalty(self, L):
        if self.length_penalty != "dapo": return 0.0
        soft_start = self.max_len - self.l_cache
        if L <= soft_start: return 0.0
        return max(-1.0, (soft_start - L) / self.l_cache)

    def __call__(self, prompts, completions, completion_ids=None, answer=None, pid=None, log_metric=None, log_extra=None, **kw):
        texts = [c[-1]["content"] if isinstance(c, list) else str(c) for c in completions]
        n = len(texts); assert answer is not None and len(answer) == n
        trunc = [self.is_truncated(completion_ids[i]) if completion_ids is not None else False for i in range(n)]
        lens = [len(completion_ids[i]) if completion_ids is not None else 0 for i in range(n)]
        to_grade = [i for i in range(n) if not trunc[i]]
        graded = grade_many([(texts[i], str(answer[i])) for i in to_grade], workers=self.workers, timeout_s=self.timeout) if to_grade else []
        n_fallback = sum(1 for g in graded if g["method"] == "exact-fallback")
        res = {i: g for i, g in zip(to_grade, graded)}
        out = [None] * n
        for i in range(n):
            if i not in res: continue                                   # truncated & masked -> None
            out[i] = float(res[i]["correct"]) + self.overlong_penalty(lens[i])
        self.calls += 1
        if log_metric is not None:
            scorable = [i for i in range(n) if i in res and not trunc[i]]
            correct = [res[i]["correct"] for i in scorable]
            m = {"acc": sum(correct) / max(1, len(scorable)), "frac_truncated": sum(trunc) / n,
                 "frac_boxed": sum(1 for t in texts if last_boxed(t) is not None) / n,
                 "len_correct": (sum(lens[i] for i in scorable if res[i]["correct"]) / max(1, sum(correct))) if correct else 0.0,
                 "len_incorrect": (sum(lens[i] for i in scorable if not res[i]["correct"]) / max(1, len(scorable) - sum(correct))),
                 "frac_math_verify": sum(1 for i in scorable if res[i]["method"] == "math_verify") / max(1, len(scorable)),
                 "frac_grader_fallback": n_fallback / max(1, len(to_grade))}
            if pid is not None:                                          # group pass-rate histogram over scorable rollouts
                groups = defaultdict(list)
                for i in scorable: groups[pid[i]].append(res[i]["correct"])
                gs = [sum(v) / len(v) for v in groups.values() if v]
                m.update({"grp_all0": sum(1 for p in gs if p == 0) / max(1, len(gs)), "grp_all1": sum(1 for p in gs if p == 1) / max(1, len(gs)),
                          "grp_mixed": sum(1 for p in gs if 0 < p < 1) / max(1, len(gs)), "grp_mean_pass": sum(gs) / max(1, len(gs))})
            for k, v in m.items():
                try: log_metric("rlvr/" + k, float(v))
                except Exception: pass
        if log_extra is not None:
            try: log_extra("boxed", [res[i]["boxed"] if i in res else None for i in range(n)]); log_extra("gold", [str(a) for a in answer])
            except Exception: pass
        return out
