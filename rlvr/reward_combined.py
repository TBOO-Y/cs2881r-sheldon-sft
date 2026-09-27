#!/usr/bin/env python3
"""Stage 4 reward: math prompts get the verifiable reward (rlvr/reward.py), persona prompts get the stage-2 judged reward
(rlaif/reward/reward.py: gate x (2 x pairwise persona win rate + form) - rules - false-claim - batch tax). Each rank scores its own slice
(whole prompt groups per rank, asserted in train_rlvr.py); rewards are group-normalised per prompt by the trainer, so the two reward scales
never mix inside a group. Truncated completions of either task return None (masked). If the judge becomes unavailable (spend cap, outage)
`stop_reason` is set and the RLVRCallback stops the run cleanly at the end of the step.
"""
import json
from collections import defaultdict
from .reward import MathReward

PERSONA_KEYS = ["reward", "gate_G", "persona_P", "form_bonus", "rule_penalty", "batch_tax", "skip_judge", "judge_calls", "judge_errors", "judge_cost_usd_total",
                "reward_seconds", "gate/task_score", "gate/refused", "gate/worse_off", "gate/contradiction", "gate/false_claim", "words",
                "style/mean_words", "style/any_name", "style/bazinga", "style/template_opener_frac", "style/opener_entropy_bits", "style/ends_midsentence", "style/joke_meta",
                "term/length", "term/truncation", "term/repetition", "term/preamble", "term/canon", "term/tool_voice"]

MATH_KEYS = ["acc", "frac_truncated", "frac_boxed", "len_correct", "len_incorrect", "frac_math_verify", "frac_grader_fallback", "grp_all0", "grp_all1", "grp_mixed", "grp_mean_pass"]

class CombinedReward:
    __name__ = "combined_reward"

    def __init__(self, math_reward: MathReward, persona_cfg):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "rlaif"))
        from reward.reward import GroupReward, JudgeUnavailable
        self.math = math_reward; self.persona = GroupReward(persona_cfg); self._JU = JudgeUnavailable; self.stop_reason = None; self.calls = 0

    def __call__(self, prompts, completions, completion_ids=None, answer=None, pid=None, task=None, prompt_text=None, prior_json=None, kind=None, log_metric=None, log_extra=None, **kw):
        n = len(completions); task = task or ["math"] * n
        out = [None] * n
        mi = [i for i in range(n) if task[i] == "math"]; pi = [i for i in range(n) if task[i] == "persona"]
        import time, os
        t0 = time.time(); rank = os.environ.get("RANK", "?")
        if mi:
            r = self.math(prompts=[prompts[i] for i in mi], completions=[completions[i] for i in mi], completion_ids=[completion_ids[i] for i in mi] if completion_ids is not None else None,
                          answer=[answer[i] for i in mi], pid=[pid[i] for i in mi], log_metric=log_metric)
            for i, v in zip(mi, r): out[i] = v
            print(f"[combined] rank {rank}: math graded {len(mi)} completions in {time.time() - t0:.1f}s", flush=True)
        elif log_metric is not None:                                    # no math rows on this rank: log the fixed keys anyway (one gather per key on every rank)
            for k in MATH_KEYS: log_metric("rlvr/" + k, 0.0)
        if pi and self.stop_reason is None:
            texts = {i: (completions[i][-1]["content"] if isinstance(completions[i], list) else str(completions[i])) for i in pi}
            trunc = {i: (self.math.is_truncated(completion_ids[i]) if completion_ids is not None else False) for i in pi}
            groups = {}; order = []
            for i in pi:
                k = pid[i]
                if k not in groups: groups[k] = {"prompt": prompt_text[i], "prior": (json.loads(prior_json[i]) if prior_json and prior_json[i] else None) or None, "kind": kind[i] if kind else None, "completions": [], "finishes": [], "idx": []}; order.append(k)
                g = groups[k]; g["completions"].append(texts[i]); g["finishes"].append("length" if trunc[i] else None); g["idx"].append(i)
            glist = [groups[k] for k in order]
            try:
                rewards, metrics = self.persona.score_step(glist)
                for g, rw in zip(glist, rewards):
                    for i, v in zip(g["idx"], rw): out[i] = None if trunc[i] else float(v)
                if log_metric is not None:                 # FIXED key set: TRL runs one gather per logged key, so every rank must log the same keys
                    for k in PERSONA_KEYS:
                        try: log_metric("sheldon/" + k, float(metrics.get(k, 0.0)))
                        except Exception: pass
                print(f"[combined] call {self.calls + 1}: persona groups={len(glist)} judge_calls={metrics.get('judge_calls')} errors={metrics.get('judge_errors')} "
                      f"cost=${metrics.get('judge_cost_usd_total', 0):.2f} secs={metrics.get('reward_seconds', 0):.0f} persona_reward={metrics.get('reward', 0):.3f}", flush=True)
            except (self._JU, RuntimeError) as e:                       # RuntimeError = the USD budget guard
                self.stop_reason = str(e)[:300]; print(f"[reward] STOPPING: {self.stop_reason}", flush=True)
                for i in pi: out[i] = 0.0
                if log_metric is not None:
                    for k in PERSONA_KEYS: log_metric("sheldon/" + k, 0.0)
        elif pi:
            for i in pi: out[i] = 0.0
            if log_metric is not None:
                for k in PERSONA_KEYS: log_metric("sheldon/" + k, 0.0)
        elif log_metric is not None:                                    # no persona rows on this rank: still log the fixed keys
            for k in PERSONA_KEYS: log_metric("sheldon/" + k, 0.0)
        self.calls += 1
        if log_metric is not None:
            try: log_metric("combined/frac_math", len(mi) / max(1, n)); log_metric("combined/frac_persona", len(pi) / max(1, n))
            except Exception: pass
        return out
