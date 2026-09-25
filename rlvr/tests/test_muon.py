import math, sys, pathlib, torch
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from rlvr.optim.muon import newton_schulz5, fractional_power_third, fractional_power_exact, build_optimizer, split_params, Muon

torch.manual_seed(0)

def test_newton_schulz_orthogonalises():
    G = torch.randn(64, 32)
    O = newton_schulz5(G).float()
    sv = torch.linalg.svdvals(O)                       # the 5-step quintic is a fast approximation: singular values land in ~[0.7, 1.2]
    assert sv.min() > 0.5 and sv.max() < 1.4, sv
    U, S, Vh = torch.linalg.svd(G, full_matrices=False)
    ref = U @ Vh
    assert (O - ref).norm() / ref.norm() < 0.35, (O - ref).norm() / ref.norm()

def test_fractional_power_matches_svd():
    # well-conditioned spectrum in [0.3, 1]: the cubic recurrence converges in 6 steps; tiny singular values converge slowly (paper)
    U, _ = torch.linalg.qr(torch.randn(48, 48)); V, _ = torch.linalg.qr(torch.randn(80, 48))
    S = torch.linspace(0.3, 1.0, 48)
    G = (U * S) @ V.T
    Y = fractional_power_third(G)
    ref = fractional_power_exact(G / (1.05 * S.max()), 1.0 / 3.0)
    rel = (Y - ref).norm() / ref.norm()
    assert rel < 0.05, rel

def test_fractional_power_is_between_muon_and_sgd():
    U, _ = torch.linalg.qr(torch.randn(32, 32)); V, _ = torch.linalg.qr(torch.randn(32, 32))
    S = torch.tensor([1.0] * 8 + [0.5] * 8 + [0.25] * 8 + [0.125] * 8)
    G = (U * S) @ V.T
    Y = fractional_power_third(G)
    sv = torch.linalg.svdvals(Y)
    ratio = sv.max() / sv.min()                       # Muon: 1 ; SGD: 8 ; S^(1/3): 2
    assert 1.3 < ratio < 4.0, ratio

class Toy(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.embed_tokens = torch.nn.Embedding(64, 16); self.q_proj = torch.nn.Linear(16, 16); self.norm = torch.nn.LayerNorm(16); self.lm_head = torch.nn.Linear(16, 10)
    def forward(self, x): return self.lm_head(self.norm(self.q_proj(self.embed_tokens(x))))

def test_split_and_rms():
    for kind in ("muon", "muonp"):
        m = Toy(); matrix, other = split_params(m)
        assert [n for n, _ in matrix] == ["q_proj.weight"], [n for n, _ in matrix]
        opt = build_optimizer(m, kind=kind, lr=1e-2, weight_decay=0.0)
        before = {n: p.detach().clone() for n, p in m.named_parameters()}
        loss = m(torch.arange(64)).logsumexp(-1).sum(); loss.backward(); opt.step()   # 64 distinct tokens -> full-rank (16) gradient
        d = (m.q_proj.weight - before["q_proj.weight"])
        rms = d.pow(2).mean().sqrt().item() / 1e-2
        assert 0.1 < rms < 0.3, (kind, rms)                 # update RMS ~ 0.2 * lr (Moonlight matching; exact for muonp, full-rank for muon)
        assert abs(opt.stats["update_rms"] - rms) < 0.05
        assert not torch.equal(m.lm_head.weight, before["lm_head.weight"]) and not torch.equal(m.norm.weight, before["norm.weight"])

def test_muonp_update_is_deterministic():
    G = torch.randn(40, 24)
    torch.manual_seed(1); a = fractional_power_third(G); torch.manual_seed(2); b = fractional_power_third(G)
    assert torch.equal(a, b)                              # no RNG in the path: DDP ranks with different seeds must agree

def test_adamw_groups():
    m = Toy(); opt = build_optimizer(m, kind="adamw", lr=1e-3, weight_decay=0.1)
    wd = {id(p): g["weight_decay"] for g in opt.param_groups for p in g["params"]}
    assert wd[id(m.q_proj.weight)] == 0.1 and wd[id(m.q_proj.bias)] == 0.0 and wd[id(m.norm.weight)] == 0.0 and wd[id(m.embed_tokens.weight)] == 0.1

if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"): f(); print("ok", k)
