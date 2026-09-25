#!/usr/bin/env python3
"""Muon and Muon^p (fractional spectral power) for full-parameter RL fine-tuning, plus the parameter split.

Muon (Jordan et al. 2024; Moonlight / Kimi K2 conventions, arXiv 2502.16982):
    M_t = mu * M_{t-1} + G_t ;  O_t = NewtonSchulz5(nesterov ? G_t + mu * M_t : M_t)   (5 iterations, coeffs 3.4445, -4.7750, 2.0315)
    W_t = W_{t-1} - lr * (0.2 * sqrt(max(m, n)) * O_t + wd * W_{t-1})
  The 0.2*sqrt(max(m,n)) factor matches the update RMS to AdamW's (~0.2), so Muon reuses AdamW's learning rate and weight decay.

Muon^p (Dong & Sawin, arXiv 2606.13867; code princeton-pli/muon-p): replace U V^T by U S^p V^T for G = U S V^T, p in (0, 1),
interpolating between Muon (p = 0) and momentum SGD (p = 1). For p = 1/3 the paper's Algorithm 1 iterates a cubic recurrence on the
spectrally-normalised matrix X (top singular value <= 1):  Y_0 = X ;  Y_{n+1} = Y_n + c * (X - Y_n Y_n^T Y_n),  c = 0.66, N = 6,
whose fixed point is U S^{1/3} V^T (Y Y^T Y = X). The update is then rescaled to RMS 0.2 (||.||_F based) so the three optimizers in
the pilot share one nominal learning rate. (The paper's code rescales to RMS 1 and multiplies the LR by 0.3; same idea, different
constant.) Microsoft's Dion repo has no fractional-power variant; this file is the drop-in slot for a user-supplied fork.

Parameter split (build_optimizer): 2-D weights of attention/MLP projections -> Muon/Muon^p; embeddings, lm_head, norms, biases
(Qwen2.5 has QKV biases) and anything 1-D -> AdamW with the same lr/wd. LoRA A/B factors are 2-D and would land in the Muon group
if an adapter model is passed; that is mechanically fine but not what the plan runs (see PLAN.md).
Runs under DDP without extra logic: gradients are all-reduced by DDP, every rank computes the identical update.
"""
import math, torch

NS_COEFFS = (3.4445, -4.7750, 2.0315)

@torch.no_grad()
def newton_schulz5(G: torch.Tensor, steps: int = 5, eps: float = 1e-7) -> torch.Tensor:
    """Approximate orthogonalisation U V^T of a 2-D matrix (bf16, as in the reference implementation)."""
    assert G.ndim == 2
    a, b, c = NS_COEFFS
    X = G.to(torch.bfloat16) if G.is_cuda else G.float()
    transposed = X.shape[0] > X.shape[1]
    if transposed: X = X.T
    X = X / (X.norm() + eps)
    for _ in range(steps):
        A = X @ X.T
        B = b * A + c * A @ A
        X = a * X + B @ X
    return X.T if transposed else X

@torch.no_grad()
def spectral_norm_estimate(G: torch.Tensor, iters: int = 10) -> torch.Tensor:
    """Power iteration on G^T G; returns an estimate of the top singular value (slight under-estimate, so we pad by 1.05).
    The start vector is derived from G itself (no RNG): under DDP every rank must compute the identical update, and TRL
    seeds the ranks differently."""
    v = G.sum(0); n = v.norm()
    v = v / n if n > 1e-12 else torch.ones(G.shape[1], device=G.device, dtype=G.dtype) / math.sqrt(G.shape[1])
    for _ in range(iters):
        u = G @ v; u = u / (u.norm() + 1e-12)
        v = G.T @ u; v = v / (v.norm() + 1e-12)
    return (G @ v).norm()

@torch.no_grad()
def fractional_power_third(G: torch.Tensor, steps: int = 6, c: float = 0.66, eps: float = 1e-7) -> torch.Tensor:
    """U S^{1/3} V^T (up to a positive scale) via the cubic recurrence of arXiv 2606.13867, Algorithm 1."""
    assert G.ndim == 2
    X = G.float()
    transposed = X.shape[0] > X.shape[1]
    if transposed: X = X.T
    X = X / (1.05 * spectral_norm_estimate(X) + eps)          # top singular value <= 1 (required for convergence)
    Y = X.clone()
    for _ in range(steps):
        Y = Y + c * (X - Y @ Y.T @ Y)
    return Y.T if transposed else Y

@torch.no_grad()
def fractional_power_exact(G: torch.Tensor, p: float) -> torch.Tensor:
    """Reference U S^p V^T through an SVD (tests / small matrices only)."""
    U, S, Vh = torch.linalg.svd(G.float(), full_matrices=False)
    return (U * S.clamp(min=0).pow(p)) @ Vh

class Muon(torch.optim.Optimizer):
    """kind = "muon" (Newton-Schulz, Moonlight RMS rule) or "muonp" (cubic fractional power, RMS rescaled to `rms`).
    Non-matrix groups (algorithm="adamw") are handled by an internal AdamW so one optimizer object covers the model."""

    def __init__(self, param_groups, lr=1e-6, weight_decay=0.0, momentum=0.95, nesterov=True, kind="muon", ns_steps=5, mp_steps=6, mp_c=0.66,
                 rms=0.2, adam_betas=(0.9, 0.95), adam_eps=1e-8):
        assert kind in ("muon", "muonp")
        defaults = dict(lr=lr, weight_decay=weight_decay, momentum=momentum, nesterov=nesterov, algorithm="muon")
        super().__init__(param_groups, defaults)
        self.kind, self.ns_steps, self.mp_steps, self.mp_c, self.rms = kind, ns_steps, mp_steps, mp_c, rms
        adam_params = [p for g in self.param_groups if g["algorithm"] == "adamw" for p in g["params"]]
        adam_wd = next((g.get("weight_decay", 0.0) for g in self.param_groups if g["algorithm"] == "adamw"), 0.0)   # the group declares it (0.0: norms/biases/embeddings)
        self.adam = torch.optim.AdamW([{"params": adam_params, "weight_decay": adam_wd}], lr=lr, betas=adam_betas, eps=adam_eps) if adam_params else None
        self.stats = {}                                   # last step: update RMS over matrix params, count

    def zero_grad(self, set_to_none=True):
        super().zero_grad(set_to_none=set_to_none)
        if self.adam is not None: self.adam.zero_grad(set_to_none=set_to_none)

    def state_dict(self):
        d = super().state_dict(); d["adam"] = self.adam.state_dict() if self.adam is not None else None; return d

    def load_state_dict(self, sd):
        sd = dict(sd); adam = sd.pop("adam", None); super().load_state_dict(sd)
        if adam is not None and self.adam is not None: self.adam.load_state_dict(adam)

    @torch.no_grad()
    def step(self, closure=None):
        loss = closure() if closure is not None else None
        if self.adam is not None:
            for g in self.adam.param_groups: g["lr"] = self.param_groups[0]["lr"]      # follow the scheduler
            self.adam.step()
        sq_sum, n_el, n_mat = None, 0, 0
        for group in self.param_groups:
            if group["algorithm"] != "muon": continue
            lr, wd, mu = group["lr"], group["weight_decay"], group["momentum"]
            for p in group["params"]:
                if p.grad is None: continue
                g = p.grad
                if g.ndim != 2: g = g.view(g.shape[0], -1)
                st = self.state[p]
                if "momentum_buffer" not in st: st["momentum_buffer"] = torch.zeros_like(g)
                buf = st["momentum_buffer"]; buf.mul_(mu).add_(g)
                m = g.add(buf, alpha=mu) if group["nesterov"] else buf
                if self.kind == "muon":
                    O = newton_schulz5(m, steps=self.ns_steps)
                    scale = self.rms * math.sqrt(max(m.shape[0], m.shape[1]))      # Moonlight: update RMS ~= 0.2 for full-rank O
                else:
                    O = fractional_power_third(m, steps=self.mp_steps, c=self.mp_c)
                    scale = self.rms * math.sqrt(O.numel()) / (O.norm() + 1e-12)     # explicit RMS = 0.2
                upd = (O * scale).to(p.dtype).view_as(p)
                if wd: p.mul_(1.0 - lr * wd)
                p.add_(upd, alpha=-lr)
                s = upd.float().pow(2).sum(); sq_sum = s if sq_sum is None else sq_sum + s; n_el += upd.numel(); n_mat += 1      # stays on device; one sync below
        self.stats = {"update_rms": math.sqrt(float(sq_sum) / n_el) if n_el else 0.0, "n_matrices": n_mat}
        return loss

def split_params(model, muon_min_dim=2):
    """(matrix_params, other_params) over trainable parameters; embeddings / lm_head / norms / biases go to `other`."""
    matrix, other = [], []
    for name, p in model.named_parameters():
        if not p.requires_grad: continue
        is_matrix = p.ndim >= muon_min_dim and not any(k in name for k in ("embed", "lm_head", "norm", "bias"))
        (matrix if is_matrix else other).append((name, p))
    return matrix, other

def build_optimizer(model, kind="adamw", lr=1e-6, weight_decay=0.01, betas=(0.9, 0.95), eps=1e-15, momentum=0.95, nesterov=True, decay_norm_and_bias=False):
    if kind == "adamw":
        decay, no_decay = [], []
        for n, p in model.named_parameters():
            if not p.requires_grad: continue
            (no_decay if (p.ndim < 2 or "bias" in n or "norm" in n) and not decay_norm_and_bias else decay).append(p)
        return torch.optim.AdamW([{"params": decay, "weight_decay": weight_decay}, {"params": no_decay, "weight_decay": 0.0}], lr=lr, betas=betas, eps=eps)
    matrix, other = split_params(model)
    groups = [{"params": [p for _, p in matrix], "algorithm": "muon"}]
    if other: groups.append({"params": [p for _, p in other], "algorithm": "adamw", "weight_decay": 0.0})
    return Muon(groups, lr=lr, weight_decay=weight_decay, momentum=momentum, nesterov=nesterov, kind=kind, adam_betas=betas, adam_eps=eps)

def describe_split(model):
    matrix, other = split_params(model)
    return {"muon_params": sum(p.numel() for _, p in matrix), "muon_tensors": len(matrix), "adamw_params": sum(p.numel() for _, p in other),
            "adamw_tensors": len(other), "adamw_names": sorted({n.split(".")[-2] + "." + n.split(".")[-1] for n, _ in other})[:12]}
