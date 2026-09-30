"""Does the generative model earn its keep? Joint-profile evaluation of CFM samples.

A conditional generative model is only worth its cost over a multi-label classifier if
its samples capture dependence between hidden genes beyond what the observed panel
explains. Compared on repeat 0 of 02_benchmark.py, per test patient:
  cfm          100 endpoints of the NSCLC-only velocity CFM, thresholded at 0
  indep_lr     100 independent Bernoulli draws from the logistic-regression marginals
  indep_prev   100 independent Bernoulli draws from training prevalence
Metrics: energy score (a proper scoring rule for the joint vector; Hamming distance),
calibration of the number of hidden alterations per patient, observed vs expected
co-occurrence for hidden-gene pairs, and AUROC as a function of the Monte Carlo budget.
"""
import json

import numpy as np
import pandas as pd

from pc_common import CACHE, RESULTS, load, fold_ids, strat_auroc
from pc_models import mc_probability

S = 100
z = np.load(CACHE / "oof_any.npz")
Y, hid = z["Y"], z["hid"]
fold = np.repeat(fold_ids(len(Y), 0), Y.shape[1])


def auroc(Y, P):
    return strat_auroc(Y.ravel(), P.ravel(), fold)


genes = load()["genes"][hid]
rng = np.random.default_rng(0)

samples = {"cfm": np.zeros((S,) + Y.shape, bool)}
for f in range(5):
    te = np.load(CACHE / f"cfm_samples_fold{f}_idx.npy")
    samples["cfm"][:, te] = np.load(CACHE / f"cfm_samples_fold{f}.npy") > 0
for name, key in [("indep_lr", "logistic"), ("indep_prev", "prevalence")]:
    p = z[key][0]
    samples[name] = rng.random((S,) + Y.shape) < p[None]


def energy_score(X, y):
    """ES = E|X - y| - 0.5 E|X - X'| with Hamming distance, averaged over patients."""
    X = X.astype(np.int8)
    t1 = np.abs(X - y[None]).sum(-1).mean(0)
    half = S // 2
    t2 = np.abs(X[:half] - X[half:2 * half]).sum(-1).mean(0)
    return t1 - 0.5 * t2


out = {}
n_true = Y.sum(1)
for name, X in samples.items():
    es = energy_score(X, Y)
    n_s = X.sum(-1)
    out[name] = dict(
        energy_score=float(es.mean()),
        sampled_alteration_rate=float(X.mean()),
        true_alteration_rate=float(Y.mean()),
        mean_hidden_alterations_per_patient=float(n_s.mean()),
        true_mean_hidden_alterations_per_patient=float(n_true.mean()),
        share_patients_with_any_sampled=float((n_s > 0).mean()),
        true_share_patients_with_any=float((n_true > 0).mean()),
    )

# pairwise co-occurrence among hidden genes
C = Y.T.astype(int) @ Y.astype(int)
pairs = [(i, j) for i in range(len(hid)) for j in range(i + 1, len(hid)) if C[i, j] >= 4]
rows = []
for i, j in pairs:
    r = dict(pair=f"{genes[i]}/{genes[j]}", observed=int(C[i, j]))
    for name, X in samples.items():
        r[name] = float((X[..., i] & X[..., j]).mean(0).sum())
    rows.append(r)
co = pd.DataFrame(rows).sort_values("observed", ascending=False)
co.to_csv(RESULTS / "joint_cooccurrence.csv", index=False, float_format="%.2f")
out["cooccurrence_total"] = {k: float(co[k].sum()) for k in ["observed"] + list(samples)}

# Monte Carlo budget: resolution of sample-frequency probabilities is 1/n_samples
mc = []
for n in (5, 10, 20, 50, 100):
    P = mc_probability(samples["cfm"][:n])
    mc.append(dict(n_samples=n, pooled_auroc=auroc(Y, P), share_zero_probability=float((P == 0).mean())))
out["mc_budget"] = mc
out["cfm_t0_readout_pooled_auroc"] = auroc(Y, z["cfm_velocity_t0"][0])

RESULTS.mkdir(exist_ok=True)
json.dump(out, open(RESULTS / "joint.json", "w"), indent=1)
print(json.dumps(out, indent=1))
print(co.head(15).round(2).to_string(index=False))
