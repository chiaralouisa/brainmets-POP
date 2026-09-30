"""Models compared on identical patient-level folds.

Every model returns P (n_test x n_hidden) of per-gene alteration probabilities.
The conditional flow-matching model follows the usual continuous relaxation of binary
data: targets mapped to {-1, +1}, a linear Gaussian-to-data path, and an MLP velocity
field conditioned on the observed panel. Marginals are read out either by Monte Carlo
(fraction of sampled endpoints > 0) or in one network call at t = 0 (see cfm_marginal).
"""
import math

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

EPS = 1e-4


def prevalence(Xtr, Ytr, Xte, **_):
    p = (Ytr.sum(0) + 0.5) / (len(Ytr) + 1.0)
    return np.tile(p, (len(Xte), 1))


# ------------------------------------------------------------------ linear (independent LRs)

def _fit_linear(X, Y, l2, iters=200):
    X, Y = torch.tensor(X), torch.tensor(Y, dtype=torch.float32)
    W = torch.zeros(X.shape[1], Y.shape[1], requires_grad=True)
    prior = torch.logit(((Y.sum(0) + 0.5) / (len(Y) + 1.0)))
    b = prior.clone().requires_grad_(True)
    opt = torch.optim.LBFGS([W, b], lr=1, max_iter=iters, line_search_fn="strong_wolfe")

    def closure():
        opt.zero_grad()
        loss = F.binary_cross_entropy_with_logits(X @ W + b, Y, reduction="sum") / len(X) \
            + l2 * (W ** 2).sum()
        loss.backward()
        return loss

    opt.step(closure)
    return W.detach(), b.detach()


def logistic(Xtr, Ytr, Xte, Xva=None, Yva=None, grid=(1e-1, 3e-2, 1e-2, 3e-3, 1e-3), **_):
    """69 independent L2 logistic regressions (the loss is separable across genes), fitted
    jointly for speed. The penalty is picked on the inner validation split by log-loss."""
    Xtr, Xte = Xtr.astype(np.float32), Xte.astype(np.float32)
    l2 = grid[len(grid) // 2]
    if Xva is not None:
        best = np.inf
        for g in grid:
            W, b = _fit_linear(Xtr, Ytr, g)
            p = torch.sigmoid(torch.tensor(Xva.astype(np.float32)) @ W + b).clamp(EPS, 1 - EPS)
            ll = F.binary_cross_entropy(p, torch.tensor(Yva, dtype=torch.float32)).item()
            if ll < best:
                best, l2 = ll, g
        Xtr = np.vstack([Xtr, Xva.astype(np.float32)])
        Ytr = np.vstack([Ytr, Yva])
    W, b = _fit_linear(Xtr, Ytr, l2)
    return torch.sigmoid(torch.tensor(Xte) @ W + b).numpy()


# ---------------------------------------------------------------- locus / burden baselines

def locus_features(d, rows, obs, hid, window=5e6):
    """For each hidden gene: amplification / deep deletion of the nearest observed gene on
    the same chromosome, and whether any observed gene within +-window is amplified /
    deleted. Returns an array (n, n_hidden, 4)."""
    chrom, pos = d["chrom"], d["gpos"]
    amp = d["amp"][np.ix_(rows, obs)].astype(np.float32)
    dele = d["dele"][np.ix_(rows, obs)].astype(np.float32)
    out = np.zeros((len(rows), len(hid), 4), np.float32)
    for k, h in enumerate(hid):
        same = np.where(chrom[obs] == chrom[h])[0]
        if len(same) == 0:
            continue
        dist = np.abs(pos[obs][same] - pos[h])
        nn_ = same[np.argmin(dist)]
        win = same[dist <= window]
        out[:, k, 0] = amp[:, nn_]
        out[:, k, 1] = dele[:, nn_]
        if len(win):
            out[:, k, 2] = amp[:, win].max(1)
            out[:, k, 3] = dele[:, win].max(1)
    return out


def per_gene_logistic(Ftr, Ytr, Fte, l2=1e-2):
    """Separate small LR per hidden gene on gene-specific features F (n, n_hidden, f)."""
    P = np.zeros((len(Fte), Ytr.shape[1]), np.float32)
    for k in range(Ytr.shape[1]):
        W, b = _fit_linear(Ftr[:, k, :], Ytr[:, [k]], l2)
        P[:, k] = torch.sigmoid(torch.tensor(Fte[:, k, :]) @ W + b).numpy()[:, 0]
    return P


# ------------------------------------------------------------------------------- MLP

class MLP(nn.Module):
    def __init__(self, d_in, d_out, h=256, p=0.3):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(d_in, h), nn.GELU(), nn.Dropout(p),
                                 nn.Linear(h, h), nn.GELU(), nn.Dropout(p), nn.Linear(h, d_out))

    def forward(self, x):
        return self.net(x)


def mlp(Xtr, Ytr, Xte, Xva, Yva, seed=0, epochs=300, **_):
    """Shared-representation multi-label MLP with early stopping on validation BCE."""
    torch.manual_seed(seed)
    Xtr, Ytr = torch.tensor(Xtr, dtype=torch.float32), torch.tensor(Ytr, dtype=torch.float32)
    Xva, Yva = torch.tensor(Xva, dtype=torch.float32), torch.tensor(Yva, dtype=torch.float32)
    m = MLP(Xtr.shape[1], Ytr.shape[1])
    with torch.no_grad():
        m.net[-1].bias.copy_(torch.logit((Ytr.mean(0) + 1e-3).clamp(max=0.5)))
    opt = torch.optim.AdamW(m.parameters(), lr=1e-3, weight_decay=1e-2)
    best, state, bad = np.inf, None, 0
    for ep in range(epochs):
        m.train()
        for i in torch.randperm(len(Xtr)).split(128):
            opt.zero_grad()
            F.binary_cross_entropy_with_logits(m(Xtr[i]), Ytr[i]).backward()
            opt.step()
        m.eval()
        with torch.no_grad():
            v = F.binary_cross_entropy_with_logits(m(Xva), Yva).item()
        if v < best - 1e-5:
            best, bad = v, 0
            state = {k: t.clone() for k, t in m.state_dict().items()}
        else:
            bad += 1
            if bad >= 20:
                break
    m.load_state_dict(state)
    m.eval()
    with torch.no_grad():
        return torch.sigmoid(m(torch.tensor(Xte, dtype=torch.float32))).numpy()


# --------------------------------------------------------------- conditional flow matching

def _temb(t, dim=32):
    f = torch.exp(torch.arange(dim // 2) * (-math.log(1000.0) / (dim // 2 - 1)))
    a = t[:, None] * 1000.0 * f[None]
    return torch.cat([a.sin(), a.cos()], 1)


class Velocity(nn.Module):
    def __init__(self, d_x, d_c, h=512, hc=256, p=0.1):
        super().__init__()
        self.cenc = nn.Sequential(nn.Linear(d_c, hc), nn.GELU(), nn.Dropout(p), nn.Linear(hc, hc))
        self.net = nn.Sequential(nn.Linear(d_x + hc + 32, h), nn.GELU(), nn.Dropout(p),
                                 nn.Linear(h, h), nn.GELU(), nn.Dropout(p),
                                 nn.Linear(h, h), nn.GELU(), nn.Linear(h, d_x))

    def forward(self, x, t, c):
        return self.net(torch.cat([x, self.cenc(c), _temb(t)], 1))


class CFM:
    """param="velocity": regress u = x1 - x0 with MSE (standard CFM).
    param="x1": predict the clean binary state with cross-entropy and derive the velocity
    as (E[x1 | x_t, c] - x_t) / (1 - t), as discrete / Dirichlet flow matching do. Both
    define the same ODE at the optimum; they differ in how the loss weights rare events."""

    def __init__(self, param="velocity", seed=0, steps=6000, batch=128, lr=1e-3, wd=1e-4,
                 ema=0.999, dropout=0.1, t_beta=1.0):
        self.param, self.seed, self.steps, self.batch = param, seed, steps, batch
        self.t_beta = t_beta  # t ~ Beta(1, t_beta); > 1 puts more weight near t = 0
        self.lr, self.wd, self.ema, self.dropout = lr, wd, ema, dropout

    def _loss(self, m, xt, t, c, x1, x0):
        out = m(xt, t, c)
        if self.param == "velocity":
            return ((out - (x1 - x0)) ** 2).mean()
        return F.binary_cross_entropy_with_logits(out, (x1 > 0).float())

    def fit(self, Xtr, Ytr, Xva, Yva):
        g = torch.Generator().manual_seed(self.seed)
        torch.manual_seed(self.seed)
        C = torch.tensor(Xtr, dtype=torch.float32)
        X1 = torch.tensor(2.0 * Ytr - 1.0, dtype=torch.float32)
        # fixed noise/time draws make validation loss comparable across checkpoints
        gv = torch.Generator().manual_seed(123)
        rep = 8
        Cv = torch.tensor(Xva, dtype=torch.float32).repeat(rep, 1)
        X1v = torch.tensor(2.0 * Yva - 1.0, dtype=torch.float32).repeat(rep, 1)
        x0v = torch.randn(X1v.shape, generator=gv)
        tv = torch.rand(len(X1v), generator=gv)
        xtv = (1 - tv[:, None]) * x0v + tv[:, None] * X1v
        self.m = Velocity(X1.shape[1], C.shape[1], p=self.dropout)
        if self.param == "x1":
            prior = torch.tensor((Ytr.mean(0) + 1e-3).clip(max=0.5), dtype=torch.float32)
            with torch.no_grad():
                self.m.net[-1].bias.copy_(torch.logit(prior))
        ema = {k: t_.clone() for k, t_ in self.m.state_dict().items()}
        opt = torch.optim.AdamW(self.m.parameters(), lr=self.lr, weight_decay=self.wd)
        sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, self.steps)
        best, state = np.inf, None
        for step in range(self.steps):
            self.m.train()
            i = torch.randint(0, len(C), (self.batch,), generator=g)
            x1, c = X1[i], C[i]
            x0 = torch.randn(x1.shape, generator=g)
            t = torch.rand(len(x1), generator=g)
            if self.t_beta != 1.0:
                t = 1 - (1 - t) ** (1.0 / self.t_beta)  # inverse CDF of Beta(1, t_beta)
            xt = (1 - t[:, None]) * x0 + t[:, None] * x1
            loss = self._loss(self.m, xt, t, c, x1, x0)
            opt.zero_grad()
            loss.backward()
            opt.step()
            sched.step()
            with torch.no_grad():
                for k, t_ in self.m.state_dict().items():
                    ema[k].mul_(self.ema).add_(t_, alpha=1 - self.ema)
            if (step + 1) % 250 == 0:
                cur = {k: t_.clone() for k, t_ in self.m.state_dict().items()}
                self.m.load_state_dict(ema)
                self.m.eval()
                with torch.no_grad():
                    v = self._loss(self.m, xtv, tv, Cv, X1v, x0v).item()
                if v < best:
                    best, state = v, {k: t_.clone() for k, t_ in ema.items()}
                self.m.load_state_dict(cur)
        self.m.load_state_dict(state)
        self.m.eval()
        return self

    def _velocity(self, x, t, C):
        out = self.m(x, t, C)
        if self.param == "velocity":
            return out
        return (2 * torch.sigmoid(out) - 1 - x) / (1 - t[:, None]).clamp(min=1e-3)

    @torch.no_grad()
    def sample(self, X, n_samples=100, n_steps=32, seed=0):
        """Euler integration from N(0, I) to t = 1. Returns (n_samples, n, d) endpoints."""
        g = torch.Generator().manual_seed(seed)
        C = torch.tensor(X, dtype=torch.float32)
        out = []
        for s in range(n_samples):
            x = torch.randn(len(C), self.m.net[-1].out_features, generator=g)
            for k in range(n_steps):
                t = torch.full((len(C),), k / n_steps)
                x = x + self._velocity(x, t, C) / n_steps
            out.append(x.numpy())
        return np.stack(out)

    @torch.no_grad()
    def marginal(self, X, n_noise=16, seed=0):
        """One-step readout. At t = 0 the path state is pure noise, independent of the
        target, so the regression-optimal velocity is v*(x0, 0, c) = E[x1 | c] - x0 and
        p = (1 + x0 + v(x0, 0, c)) / 2 is the model's conditional marginal. Averaging a few
        noise draws only reduces network error; no ODE solve or Monte Carlo is needed.
        For the x1 parameterisation the t = 0 output is P(y | c) directly."""
        g = torch.Generator().manual_seed(seed)
        C = torch.tensor(X, dtype=torch.float32)
        acc = 0
        for _ in range(n_noise):
            x0 = torch.randn(len(C), self.m.net[-1].out_features, generator=g)
            t0 = torch.zeros(len(C))
            if self.param == "velocity":
                acc = acc + (1 + x0 + self.m(x0, t0, C)) / 2
            else:
                acc = acc + torch.sigmoid(self.m(x0, t0, C))
        return np.clip((acc / n_noise).numpy(), EPS, 1 - EPS)


def mc_probability(samples, eps=0.0):
    """Fraction of sampled endpoints above zero. Resolution is 1/n_samples, so with rare
    events most probabilities collapse onto 0 and tie."""
    return (samples > 0).mean(0) + eps
