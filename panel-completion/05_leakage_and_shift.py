"""Three failure modes the abstract's protocol does not rule out, measured on MSK-IMPACT 2017.

A. Sample- vs patient-level splitting. 60 NSCLC patients have >1 IMPACT410 sample
   (primary + metastasis, or re-biopsy). A sample-level split puts siblings on both sides.
B. Unassayed genes encoded as wild type. cBioPortal's CNA matrix stores 0 (not NA) for
   genes a sample's panel never targeted. Training on older-panel samples without the gene
   panel matrix labels every unassayed gene as unaltered.
C. Simulated vs real small-panel input. The benchmark masks a large-panel assay; in use the
   input comes from a separate small-panel assay. 167 patients were sequenced on both
   IMPACT341 and IMPACT410, which gives a real paired test.
"""
import json

import numpy as np
import pandas as pd

from pc_common import (RESULTS, load, split_panels, one_sample_per_patient, features, targets,
                       patient_folds, fold_ids, strat_auroc, pooled_auroc, macro_auroc, brier)
from pc_models import logistic

d = load()
clin, genes = d["clin"], d["genes"]
obs, hid = split_panels(genes)
out = {}


def fold_label(folds, n):
    f = np.zeros(n, int)
    for i, te in enumerate(folds):
        f[te] = i
    return f


def s_pooled(Y, P, fold):
    """Pooled AUROC over gene-patient pairs, comparing pairs within a fold only."""
    return strat_auroc(Y.ravel(), P.ravel(), np.repeat(fold, Y.shape[1]))


def s_macro(Y, P, fold, min_pos=10):
    return np.nanmean([strat_auroc(Y[:, j], P[:, j], fold) for j in range(Y.shape[1])
                       if Y[:, j].sum() >= min_pos])


def cv(X, Y, folds, **kw):
    P = np.zeros(Y.shape, np.float32)
    for f, te in enumerate(folds):
        tr = np.setdiff1d(np.arange(len(Y)), te)
        rng = np.random.default_rng(f)
        va = rng.choice(tr, int(0.15 * len(tr)), replace=False)
        P[te] = logistic(X[np.setdiff1d(tr, va)], Y[np.setdiff1d(tr, va)], X[te], X[va], Y[va])
    return P


# ---------------------------------------------------------------- A. split granularity
ns = np.where((clin.CANCER_TYPE == "Non-Small Cell Lung Cancer") & (clin.PANEL == "IMPACT410"))[0]
X, Y = features(d, ns, obs), targets(d, ns, hid)
pid = clin.PATIENT_ID.values[ns]
multi = pd.Series(pid).duplicated(keep=False).values
rng = np.random.default_rng(0)
sample_folds = [np.sort(f) for f in np.array_split(rng.permutation(len(ns)), 5)]
up = np.unique(pid)
pf = np.array_split(rng.permutation(len(up)), 5)
patient_folds_ = [np.where(np.isin(pid, up[f]))[0] for f in pf]
resA = {}
for name, folds in [("sample_split", sample_folds), ("patient_split", patient_folds_)]:
    P = cv(X, Y, folds)
    fl = fold_label(folds, len(Y))
    resA[name] = dict(pooled_auroc_all=s_pooled(Y, P, fl),
                      pooled_auroc_multi_sample_patients=s_pooled(Y[multi], P[multi], fl[multi]),
                      macro_auroc_all=s_macro(Y, P, fl))
# how much of the hidden profile is shared between sibling samples
sib = []
for p in np.unique(pid[multi]):
    i = np.where(pid == p)[0]
    a, b = Y[i[0]].astype(bool), Y[i[1]].astype(bool)
    if (a | b).any():
        sib.append((a & b).sum() / (a | b).sum())
resA["n_multi_sample_patients"] = int(len(np.unique(pid[multi])))
resA["n_samples"] = int(len(ns))
resA["sibling_hidden_jaccard_mean"] = float(np.mean(sib))
out["A_split_granularity"] = resA
print("A", json.dumps(resA, indent=1))

# ------------------------------------------------- B. unassayed genes silently set to zero
im5 = one_sample_per_patient(clin, np.where(clin.PANEL == "IMPACT410")[0])
rows5 = im5[clin.CANCER_TYPE.values[im5] == "Non-Small Cell Lung Cancer"]
im3 = np.where((clin.PANEL == "IMPACT341") & (clin.CANCER_TYPE == "Non-Small Cell Lung Cancer")
               & ~clin.PATIENT_ID.isin(clin.PATIENT_ID.values[rows5]))[0]
im3 = one_sample_per_patient(clin, im3)
X5, Y5 = features(d, rows5, obs), targets(d, rows5, hid)
X3 = features(d, im3, obs)
Y3_naive = np.zeros((len(im3), len(hid)), np.int8)        # what the raw matrix says
resB = {"n_impact410": int(len(rows5)), "n_impact341_added": int(len(im3))}
for name in ["correct_exclude_unassayed", "naive_zero_fill"]:
    P = np.zeros(Y5.shape, np.float32)
    for f, te in enumerate(patient_folds(len(rows5), 5, 0)):
        tr = np.setdiff1d(np.arange(len(rows5)), te)
        va = np.random.default_rng(f).choice(tr, int(0.15 * len(tr)), replace=False)
        tr2 = np.setdiff1d(tr, va)
        Xtr, Ytr = X5[tr2], Y5[tr2]
        if name == "naive_zero_fill":
            Xtr, Ytr = np.vstack([Xtr, X3]), np.vstack([Ytr, Y3_naive])
        P[te] = logistic(Xtr, Ytr, X5[te], X5[va], Y5[va])
    fl = fold_ids(len(rows5), 0)
    resB[name] = dict(pooled_auroc=s_pooled(Y5, P, fl), macro_auroc=s_macro(Y5, P, fl),
                      brier=brier(Y5, P), predicted_over_observed=float(P.sum() / Y5.sum()))
out["B_unassayed_as_wildtype"] = resB
print("B", json.dumps(resB, indent=1))

# ------------------------------------------------------ C. real small-panel assay input
both = sorted(set(clin.PATIENT_ID[clin.PANEL == "IMPACT341"]) & set(clin.PATIENT_ID[clin.PANEL == "IMPACT410"]))
r3 = one_sample_per_patient(clin, np.where(clin.PATIENT_ID.isin(both) & (clin.PANEL == "IMPACT341"))[0])
r5 = one_sample_per_patient(clin, np.where(clin.PATIENT_ID.isin(both) & (clin.PANEL == "IMPACT410"))[0])
r3 = r3[np.argsort(clin.PATIENT_ID.values[r3])]
r5 = r5[np.argsort(clin.PATIENT_ID.values[r5])]
assert (clin.PATIENT_ID.values[r3] == clin.PATIENT_ID.values[r5]).all()
same_type = clin.CANCER_TYPE.values[r3] == clin.CANCER_TYPE.values[r5]
top = pd.Series(clin.CANCER_TYPE.values[im5]).value_counts().index[:15].tolist()
train = im5[~np.isin(clin.PATIENT_ID.values[im5], both)]
va = np.random.default_rng(0).choice(len(train), int(0.1 * len(train)), replace=False)
tr = np.setdiff1d(np.arange(len(train)), va)
Xtr = features(d, train, obs, cancer_types=top)
Ytr = targets(d, train, hid)
Yte = targets(d, r5, hid)
X_sim = features(d, r5, obs, cancer_types=top)      # IMPACT410 sample, masked to 341 genes
X_real = features(d, r3, obs, cancer_types=top)     # the separate IMPACT341 assay
P_sim = logistic(Xtr[tr], Ytr[tr], X_sim, Xtr[va], Ytr[va])
P_real = logistic(Xtr[tr], Ytr[tr], X_real, Xtr[va], Ytr[va])
o3 = targets(d, r3, obs).astype(bool)
o5 = targets(d, r5, obs).astype(bool)
jac = [(a & b).sum() / max(1, (a | b).sum()) for a, b in zip(o3, o5)]
resC = dict(n_patients=len(both), n_same_cancer_type=int(same_type.sum()),
            positives=int(Yte.sum()),
            observed_panel_jaccard_between_assays=float(np.mean(jac)),
            simulated_input=dict(pooled_auroc=pooled_auroc(Yte, P_sim), macro_auroc=macro_auroc(Yte, P_sim, 3),
                                 brier=brier(Yte, P_sim)),
            real_small_panel_input=dict(pooled_auroc=pooled_auroc(Yte, P_real), macro_auroc=macro_auroc(Yte, P_real, 3),
                                        brier=brier(Yte, P_real)))
out["C_simulated_vs_real_assay"] = resC
print("C", json.dumps(resC, indent=1))

RESULTS.mkdir(exist_ok=True)
json.dump(out, open(RESULTS / "leakage_and_shift.json", "w"), indent=1, default=float)
