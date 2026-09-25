import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from rlvr.reward import MathReward

EOS = 151645
def comp(text): return [{"role": "assistant", "content": text}]

def test_truncation_masked_and_penalties():
    r = MathReward(eos_ids=[EOS, 151643], max_completion_length=100, length_penalty="none", workers=1)
    ids = [[1] * 5 + [EOS], [1] * 100, [1] * 3 + [EOS], []]
    out = r(prompts=[None] * 4, completions=[comp("\\boxed{3}"), comp("\\boxed{3}"), comp("\\boxed{4}"), comp("")], completion_ids=ids, answer=["3"] * 4, pid=[0, 0, 1, 1])
    assert out == [1.0, None, 0.0, None], out

def test_dapo_soft_overlong():
    r = MathReward(eos_ids=[EOS], max_completion_length=100, length_penalty="dapo", l_cache=20, workers=1)
    assert r.overlong_penalty(80) == 0.0 and abs(r.overlong_penalty(90) + 0.5) < 1e-9 and abs(r.overlong_penalty(100) + 1.0) < 1e-9
    out = r(prompts=[None] * 2, completions=[comp("\\boxed{3}")] * 2, completion_ids=[[1] * 89 + [EOS], [1] * 49 + [EOS]], answer=["3", "3"])
    assert abs(out[0] - 0.5) < 1e-9 and out[1] == 1.0, out

def test_metrics_logged():
    logged = {}
    r = MathReward(eos_ids=[EOS], max_completion_length=100, workers=1)
    r(prompts=[None] * 4, completions=[comp("\\boxed{3}"), comp("\\boxed{2}"), comp("\\boxed{5}"), comp("\\boxed{5}")], completion_ids=[[1, EOS]] * 4,
      answer=["3", "3", "5", "5"], pid=[0, 0, 1, 1], log_metric=lambda k, v: logged.__setitem__(k, v))
    assert logged["rlvr/acc"] == 0.75 and logged["rlvr/grp_all1"] == 0.5 and logged["rlvr/grp_mixed"] == 0.5 and logged["rlvr/frac_truncated"] == 0.0

if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"): f(); print("ok", k)
