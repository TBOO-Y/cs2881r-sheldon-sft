import sys, pathlib, random
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from rlvr.data.build_schedule import build, bucket_of, largest_remainder, summarize

def test_buckets():
    assert bucket_of(1.0) == "solved" and bucket_of(0.9) == "easy" and bucket_of(0.5) == "medium" and bucket_of(0.125) == "medium" and bucket_of(0.0) == "hard"
    assert largest_remainder([0.5, 0.4, 0.1], 16) == [8, 6, 2] and sum(largest_remainder([0.2, 0.5, 0.3], 16)) == 16

def test_build_no_repeats_and_drift():
    rng = random.Random(1)
    train = [{"id": f"p{i}", "problem": "x", "answer": "1", "level": 1 + i % 5} for i in range(3000)]
    pr = [{"id": f"p{i}", "k": 8, "n_correct": rng.choice([0, 0, 1, 2, 4, 6, 7, 8]), "trunc_frac": 0.0} for i in range(3000)]
    for p in pr: p["passrate"] = p["n_correct"] / 8
    order, pools, repeats = build(train, pr, steps=50, per_step=16, G=16, mix_start=[0.5, 0.4, 0.1], mix_end=[0.2, 0.5, 0.3], easy_min=0.5, hard_max=0.125, seed=0)
    assert len(order) == 800 and len({r["id"] for r in order}) == 800 and not repeats
    assert all(r["passrate"] < 1.0 for r in order)
    first = [r for r in order if r["step"] < 10]; last = [r for r in order if r["step"] >= 40]
    assert sum(r["bucket"] == "hard" for r in first) < sum(r["bucket"] == "hard" for r in last)
    txt = summarize(order, 50, 16, 16, pools, repeats); assert "E[dead groups]" in txt

def test_by_level():
    train = [{"id": f"p{i}", "problem": "x", "answer": "1", "level": 1 + i % 5} for i in range(500)]
    order, pools, repeats = build(train, None, 5, 16, 16, [0.5, 0.4, 0.1], [0.2, 0.5, 0.3], 0.5, 0.125, 0, by_level=True)
    assert len(order) == 80 and {r["bucket"] for r in order} <= {"easy", "medium", "hard"}

if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"): f(); print("ok", k)
