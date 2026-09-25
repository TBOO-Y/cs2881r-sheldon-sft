"""The advantage-weight trick reproduces the DAPO-paper (prompt-level) aggregation exactly, on toy tensors that mimic TRL's
cispo/dapo branch: loss = sum_i sum_t (-A_i * l_it) * mask_it / N."""
import sys, pathlib, torch
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from rlvr.trainer import prompt_level_weights

def test_weights_reproduce_prompt_level_mean():
    torch.manual_seed(0)
    G, T = 4, 7
    # 4 groups: g0 mixed, g1 zero-variance (all adv 0), g2 mixed with one truncated row (mask all-zero, adv 0), g3 mixed
    adv = torch.tensor([1.0, -1.0, 0.5, -0.5] + [0.0] * 4 + [0.8, -0.4, 0.0, -0.4] + [1.2, -0.4, -0.4, -0.4])
    mask = (torch.rand(16, T) > 0.3).float(); mask[8 + 2] = 0.0          # truncated row in g2
    logp = torch.randn(16, T)
    dead, w, n_live, N = prompt_level_weights(adv, mask.sum(1), G)
    assert dead.view(4, G).all(1).tolist() == [False, True, False, False] and n_live == 3
    mask_live = mask * (~dead).unsqueeze(1).float()
    assert N == int(mask_live.sum())
    # TRL-style loss with weighted advantages and the recomputed N
    trl_loss = (-(adv * w).unsqueeze(1) * logp * mask_live).sum() / N
    # hand-computed prompt-level mean over live groups
    ref = 0.0
    for g in [0, 2, 3]:
        rows = slice(g * G, (g + 1) * G); Tg = mask_live[rows].sum()
        ref = ref + (-(adv[rows].unsqueeze(1) * logp[rows] * mask_live[rows]).sum()) / Tg
    ref = ref / 3
    assert torch.allclose(trl_loss, ref, atol=1e-6), (trl_loss, ref)

def test_equal_groups_give_unit_weights():
    G = 2; adv = torch.tensor([1.0, -1.0, 0.5, -0.5]); tok = torch.tensor([3, 3, 3, 3])
    dead, w, n_live, N = prompt_level_weights(adv, tok, G)
    assert not dead.any() and torch.allclose(w, torch.ones(4)) and n_live == 2 and N == 12

def test_group_without_live_tokens_is_dead_even_with_nonzero_advantages():
    G = 2; adv = torch.tensor([1.0, -1.0, 0.5, -0.5]); tok = torch.tensor([0, 0, 3, 3])
    dead, w, n_live, N = prompt_level_weights(adv, tok, G)
    assert dead.tolist() == [True, True, False, False] and n_live == 1 and N == 6 and torch.allclose(w, torch.tensor([0.0, 0.0, 1.0, 1.0]))

def test_all_dead():
    dead, w, n_live, N = prompt_level_weights(torch.zeros(4), torch.tensor([3, 3, 3, 3]), 2)
    assert dead.all() and (w == 0).all() and n_live == 0 and N == 0

if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"): f(); print("ok", k)
