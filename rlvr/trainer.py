#!/usr/bin/env python3
"""RLVRTrainer: TRL 1.13.0 GRPOTrainer with the stage-3 semantics from rlvr/PLAN.md.

What TRL already does (config flags set by train_rlvr.py): CISPO loss with a token-level IS ratio and no lower clip
(loss_type="cispo", epsilon_high = eps_max), group-mean baseline with group std (scale_rewards="group"), truncated completions
removed from the loss and from the token denominator (mask_truncated_completions=True) and, because rlvr/reward.py returns None
for them, from the group mean/std as well (TRL's nan-aware baseline). Warm-up/stable/decay LR is transformers' native scheduler.

What this subclass adds, by post-processing the batch that TRL's `_generate_and_score_completions` returns:
  1. zero-variance groups are masked: every row of a group whose advantages are all exactly 0 (all scorable rewards equal,
     or nothing scorable) gets completion_mask = 0, and `num_items_in_batch` (the global token count TRL divides by) is
     recomputed without them -> those groups contribute neither gradient nor denominator.
  2. prompt-level ("DAPO-paper") loss aggregation: L = (1 / P_live) * sum_g (1 / T_g) * sum_{i in g} sum_t l_{i,t}, where T_g is
     the live token count of group g and P_live the number of live groups in the generation batch. TRL's cispo/dapo branch computes
     sum_i sum_t l_{i,t} / N with N = num_items_in_batch (batch-wide token mean). Since every policy-gradient term is linear in the
     advantage, multiplying each row's advantage by  w_i = N / (T_g(i) * P_live)  turns TRL's batch mean into the prompt-level mean
     exactly (w_i = 1 when all live groups have the same token count). This requires beta = 0 and entropy_coef = 0 (asserted): a KL or
     entropy term would not be re-weighted. `prompt_level_weights` is a pure function so the algebra is unit-tested on toy tensors.
  3. optimizer: adamw | muon | muonp from rlvr/optim/muon.py (create_optimizer override); update RMS of the Muon family and the
     relative parameter drift ||theta - theta_0|| / ||theta_0|| every `drift_every` steps are logged under rlvr/.
Ordering assumption (the same one TRL relies on for `rewards.view(-1, G)` and its `process_slice`): the gathered generation batch is
process-major and each prompt's G completions are contiguous in it.
"""
import math, time, torch
from trl import GRPOTrainer
from transformers import TrainerCallback

def prompt_level_weights(adv_global: torch.Tensor, tokens_global: torch.Tensor, G: int):
    """adv_global: (B,) advantages after TRL's nan->0; tokens_global: (B,) live completion-token counts (0 for truncated rows).
    Returns (dead_row (B,) bool, weights (B,) float, n_live_groups int, live_tokens int)."""
    B = adv_global.numel(); assert B % G == 0, (B, G)
    adv = adv_global.view(-1, G); tok = tokens_global.view(-1, G).float()
    dead = (adv == 0).all(dim=1) | (tok.sum(1) == 0)              # zero-variance, fully unscorable, or no live token at all
    tok = tok * (~dead).unsqueeze(1).float()
    T_g = tok.sum(1); n_live = int((~dead).sum()); N_live = T_g.sum()
    w_g = torch.where(dead, torch.zeros_like(T_g), N_live / (T_g.clamp(min=1.0) * max(n_live, 1)))
    return dead.repeat_interleave(G), w_g.repeat_interleave(G), n_live, int(N_live.item())

class RLVRTrainer(GRPOTrainer):
    def __init__(self, *args, aggregation="prompt", optimizer_kind="adamw", optimizer_kwargs=None, drift_every=25, fp32_head=False, **kwargs):
        assert aggregation in ("prompt", "batch")
        super().__init__(*args, **kwargs)
        if fp32_head: self._patch_fp32_head()
        self.aggregation = aggregation; self.optimizer_kind = optimizer_kind; self.optimizer_kwargs = optimizer_kwargs or {}
        self.drift_every = drift_every; self._theta0 = None
        assert self.args.mask_truncated_completions, "PLAN.md semantics need mask_truncated_completions=True"
        assert self.loss_type in ("cispo", "dapo"), "prompt-level weighting is derived for TRL's token-sum losses (cispo/dapo)"
        if aggregation == "prompt":
            assert self.beta == 0.0 and not getattr(self, "_entropy_bonus_enabled", False), "prompt-level aggregation via advantage weights needs beta=0 and no entropy bonus"
        if self.loss_type == "cispo": assert self.epsilon_high >= 1.0, f"TRL's cispo uses epsilon_high as the absolute IS cap; {self.epsilon_high} would clip ratios below 1"

    def _patch_fp32_head(self):
        """fp32 LM head on the trainer side, for both arms. TRL's own cast_lm_head_to_fp32 is not used: it rewrites lm_head.forward
        as F.linear(h.float(), W.float()) but accelerate wraps the forward in bf16 autocast, which re-casts F.linear's operands to
        bf16 (logits still bf16); and on a PEFT model it crashes on the tied-embedding hook. This patch replaces the head's forward
        on the same module (PeftModel.lm_head forwards to the base module) with the matmul under autocast(enabled=False): fp32
        hidden states x fp32 copy of the (bf16 or fp32) weight -> fp32 logits, and TRL's selective_log_softmax takes its exact
        logsumexp branch. Parameters are untouched (the tied embedding stays bf16 in the LoRA arm), so vLLM weight sync is unaffected.
        Cost: an on-the-fly fp32 copy of the 151,936 x 2,048 head per forward (~1 ms) and fp32 logits (5 GB per 4 x 2,048-token micro-batch)."""
        import torch.nn.functional as F
        head = self.accelerator.unwrap_model(self.model).lm_head
        w, b = head.weight, head.bias
        def _fp32_head(h):
            with torch.autocast(device_type=h.device.type, enabled=False):
                out = F.linear(h.float(), w.float(), None if b is None else b.float())
            return out
        head.forward = _fp32_head
        self._fp32_head_patched = True

    # ---- batch post-processing -------------------------------------------------------------------------------------------------
    def _generate_and_score_completions(self, inputs):
        out = super()._generate_and_score_completions(inputs)
        mode = "train" if self.model.training else "eval"
        adv, cm = out["advantages"], out["completion_mask"]
        G = self.num_generations if mode == "train" else (self.num_generations_eval or self.num_generations)
        adv_g = self.accelerator.gather(adv.detach().float().contiguous())
        tok_g = self.accelerator.gather(cm.sum(1).contiguous())
        dead_rows, w_rows, n_live, n_tokens = prompt_level_weights(adv_g, tok_g, G)
        B_local = adv.shape[0]; sl = slice(self.accelerator.process_index * B_local, (self.accelerator.process_index + 1) * B_local)
        dead_local, w_local = dead_rows[sl].to(cm.device), w_rows[sl].to(adv.device, adv.dtype)
        out["completion_mask"] = cm * (~dead_local).unsqueeze(1).to(cm.dtype)
        out["num_items_in_batch"] = torch.tensor(float(n_tokens), device=cm.device)
        if self.aggregation == "prompt": out["advantages"] = adv * w_local
        n_groups = adv_g.numel() // G
        self._metrics[mode]["rlvr/frac_zero_var_groups"].append(1.0 - n_live / max(1, n_groups))
        self._metrics[mode]["rlvr/live_prompts"].append(float(n_live))
        self._metrics[mode]["rlvr/live_tokens"].append(float(n_tokens))
        self._metrics[mode]["rlvr/frac_rows_truncated"].append(float((tok_g == 0).float().mean()))   # TRL zeroed their mask before we saw them
        return out

    # ---- optimizer -------------------------------------------------------------------------------------------------------------
    def create_optimizer(self, model=None):
        if self.optimizer is None:
            from .optim.muon import build_optimizer, describe_split
            opt_model = self.model if model is None else model
            kw = dict(kind=self.optimizer_kind, lr=self.args.learning_rate, weight_decay=self.args.weight_decay,
                      betas=(self.args.adam_beta1, self.args.adam_beta2), eps=self.args.adam_epsilon)
            kw.update(self.optimizer_kwargs)
            self.optimizer = build_optimizer(opt_model, **kw)
            if self.accelerator.is_main_process:
                print(f"[optim] {self.optimizer_kind} lr={kw['lr']} wd={kw['weight_decay']} " + (str(describe_split(opt_model)) if self.optimizer_kind != "adamw" else ""), flush=True)
        return self.optimizer

    def create_scheduler(self, num_training_steps, optimizer=None):
        """WSD laid out for `schedule_total_steps` (from lr_scheduler_kwargs) rather than max_steps, so a 20-step pilot follows the
        first 20 steps of the 200-step schedule. transformers' get_wsd_schedule uses num_stable_steps when both are given."""
        from transformers.optimization import get_wsd_schedule
        if self.lr_scheduler is None:
            kw = dict(self.args.lr_scheduler_kwargs or {})
            self.lr_scheduler = get_wsd_schedule(optimizer or self.optimizer, num_warmup_steps=self.args.get_warmup_steps(num_training_steps),
                                                 num_decay_steps=kw["num_decay_steps"], num_stable_steps=kw["num_stable_steps"],
                                                 decay_type=kw.get("decay_type", "linear"), min_lr_ratio=kw.get("min_lr_ratio", 0.0))
            self._created_lr_scheduler = True
        return self.lr_scheduler

    def _snapshot_theta0(self):
        self._theta0 = [(n, p.detach().to("cpu", copy=True)) for n, p in self.model.named_parameters() if p.requires_grad]

    def drift(self):
        if self._theta0 is None: return None
        params = dict(self.model.named_parameters()); num = 0.0; den = 0.0
        for n, p0 in self._theta0:
            p = params[n].detach().float().cpu(); num += float((p - p0.float()).pow(2).sum()); den += float(p0.float().pow(2).sum())
        return math.sqrt(num) / max(math.sqrt(den), 1e-12)

class RLVRCallback(TrainerCallback):
    """Wall-clock budget, drift and update-RMS logging (on_step_end runs on every rank; drift is computed on rank 0 only)."""
    def __init__(self, trainer, hours=0.0):
        self.tr = trainer; self.deadline = time.time() + hours * 3600 if hours else None; self.t0 = time.time()
    def on_train_begin(self, args, state, control, **kw):
        if self.tr.drift_every and self.tr.accelerator.is_main_process: self.tr._snapshot_theta0()
    def on_step_end(self, args, state, control, **kw):
        opt = self.tr.optimizer; stats = getattr(getattr(opt, "optimizer", opt), "stats", None)   # accelerate may wrap the optimizer
        if stats: self.tr._metrics["train"]["rlvr/update_rms"].append(float(stats.get("update_rms", 0.0)))
        if self.tr.drift_every and state.global_step % self.tr.drift_every == 0 and self.tr.accelerator.is_main_process:
            d = self.tr.drift()
            if d is not None: self.tr._metrics["train"]["rlvr/param_drift_rel"].append(d); print(f"[drift] step {state.global_step}: ||theta-theta0||/||theta0|| = {d:.3e}", flush=True)
        if state.global_step and state.global_step % 5 == 0 and self.tr.accelerator.is_main_process:
            per = (time.time() - self.t0) / state.global_step
            print(f"[time] step {state.global_step}: {per:.1f}s/step, projected total {per * state.max_steps / 3600:.2f}h" + (f", budget left {(self.deadline - time.time()) / 3600:.2f}h" if self.deadline else ""), flush=True)
        if self.deadline:                                          # one decision for all ranks, or the survivors hang on the next collective
            flag = torch.tensor(float(time.time() > self.deadline), device=self.tr.accelerator.device)
            if bool(self.tr.accelerator.gather(flag.view(1)).max()):
                print(f"[time] wall-clock budget spent at step {state.global_step}; stopping and saving", flush=True); control.should_training_stop = True; control.should_save = True
        return control
