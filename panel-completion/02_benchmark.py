"""Benchmark: IMPACT341 -> IMPACT410-only genes in NSCLC, all models on identical folds.

Protocol: one sample per patient, 3 repeats x 5-fold patient-level CV, a 15% inner
validation split of each training fold for penalty selection / early stopping /
checkpointing. The generative and pan-cancer models are costly on CPU and run on repeat 0
only; the other models run on all three repeats. Out-of-fold (OOF) predictions go to
cache/oof_<target>.npz (NaN where a model did not run); per-fold pooled AUROC to
results/fold_auroc_<target>.csv.

    python 02_benchmark.py any          # target = any alteration (the abstract's encoding)
    python 02_benchmark.py driver       # truncating / recurrent missense + CNAs only
    python 02_benchmark.py any 0 3      # one (repeat, fold); run folds as parallel
                                        # processes, then `python 02_benchmark.py any merge`
"""
import sys
import time

import numpy as np
import pandas as pd

from pc_common import (CACHE, RESULTS, load, split_panels, one_sample_per_patient, features,
                       targets, patient_folds, pooled_auroc, macro_auroc)
from pc_models import (prevalence, logistic, mlp, locus_features, per_gene_logistic, CFM,
                       mc_probability)

TARGET = sys.argv[1] if len(sys.argv) > 1 else "any"
ARG = sys.argv[2:]
REPEATS, K = 3, 5
if not ARG:
    RUN = [(r, f) for r in range(REPEATS) for f in range(K)]
elif ARG == ["merge"]:
    RUN = []
else:
    RUN = [(int(ARG[0]), int(ARG[1]))]
# generative and pan-cancer models: primary target, repeat 0 only
CHEAP = ["prevalence", "burden", "burden+locus", "logistic", "logistic+clinical", "mlp"]
COSTLY = ["cfm_velocity_mc100", "cfm_velocity_t0", "cfm_x1_t0",
          "pan_logistic", "pan_mlp", "pan_cfm_velocity_t0", "pan_cfm_velocity_mc100"]

d = load()
clin, genes = d["clin"], d["genes"]
obs, hid = split_panels(genes)
im5 = np.where(clin.PANEL == "IMPACT410")[0]
all_rows = one_sample_per_patient(clin, im5)                      # pan-cancer, 1 per patient
rows = all_rows[(clin.CANCER_TYPE.values[all_rows] == "Non-Small Cell Lung Cancer")]
n = len(rows)
X = features(d, rows, obs)
Xc = features(d, rows, obs, clinical=True)
Y = targets(d, rows, hid, TARGET)
L = locus_features(d, rows, obs, hid)
burden = np.repeat(X[:, None, -3:], len(hid), 1)
F_burden, F_locus = burden, np.concatenate([burden, L], 2)

types = clin.CANCER_TYPE.values[all_rows]
top = pd.Series(types).value_counts().index[:15].tolist()
Xpan = features(d, all_rows, obs, cancer_types=top)
Ypan = targets(d, all_rows, hid, TARGET)
pan_pid = clin.PATIENT_ID.values[all_rows]
pid = clin.PATIENT_ID.values[rows]
pos_in_pan = {p: i for i, p in enumerate(pan_pid)}
nsclc_in_pan = np.array([pos_in_pan[p] for p in pid])

print(f"target={TARGET}  NSCLC patients={n}  hidden genes={len(hid)}  "
      f"positives={int(Y.sum())} ({100 * Y.mean():.2f}% of gene-patient pairs)  "
      f"pan-cancer patients={len(all_rows)}")

MODELS = CHEAP + (COSTLY if TARGET == "any" else [])
oof = {m: np.full((REPEATS, n, len(hid)), np.nan, np.float32) for m in MODELS}
fold_rows = []

for r, f in RUN:
    FULL = TARGET == "any" and r == 0
    te = patient_folds(n, K, seed=r)[f]
    t0 = time.time()
    tr = np.setdiff1d(np.arange(n), te)
    rng = np.random.default_rng(1000 * r + f)
    va = rng.choice(tr, int(0.15 * len(tr)), replace=False)
    tr2 = np.setdiff1d(tr, va)
    P = {}
    P["prevalence"] = prevalence(X[tr], Y[tr], X[te])
    P["burden"] = per_gene_logistic(F_burden[tr], Y[tr], F_burden[te])
    P["burden+locus"] = per_gene_logistic(F_locus[tr], Y[tr], F_locus[te])
    P["logistic"] = logistic(X[tr2], Y[tr2], X[te], X[va], Y[va])
    P["logistic+clinical"] = logistic(Xc[tr2], Y[tr2], Xc[te], Xc[va], Y[va])
    P["mlp"] = mlp(X[tr2], Y[tr2], X[te], X[va], Y[va], seed=r)
    if FULL:
        cfm = CFM("velocity", seed=r, steps=5000).fit(X[tr2], Y[tr2], X[va], Y[va])
        P["cfm_velocity_t0"] = cfm.marginal(X[te])
        S = cfm.sample(X[te], n_samples=100, seed=r)
        P["cfm_velocity_mc100"] = mc_probability(S)
        if r == 0:
            np.save(CACHE / f"cfm_samples_fold{f}.npy", S.astype(np.float16))
            np.save(CACHE / f"cfm_samples_fold{f}_idx.npy", te)
        cfm = CFM("x1", seed=r, steps=5000, t_beta=4.0).fit(X[tr2], Y[tr2], X[va], Y[va])
        P["cfm_x1_t0"] = cfm.marginal(X[te])

        # pan-cancer: every IMPACT410 patient outside this NSCLC test fold trains
        test_p = set(pid[te])
        va_i = nsclc_in_pan[va]
        held = set(va_i)
        ptr = np.array([i for i, p in enumerate(pan_pid) if p not in test_p and i not in held])
        Xte_pan = Xpan[nsclc_in_pan[te]]
        P["pan_logistic"] = logistic(Xpan[ptr], Ypan[ptr], Xte_pan, Xpan[va_i], Ypan[va_i],
                                     grid=(3e-2, 1e-2, 3e-3))
        P["pan_mlp"] = mlp(Xpan[ptr], Ypan[ptr], Xte_pan, Xpan[va_i], Ypan[va_i], seed=r)
        cfm = CFM("velocity", seed=r, steps=6000, batch=256).fit(
            Xpan[ptr], Ypan[ptr], Xpan[va_i], Ypan[va_i])
        P["pan_cfm_velocity_t0"] = cfm.marginal(Xte_pan)
        P["pan_cfm_velocity_mc100"] = mc_probability(cfm.sample(Xte_pan, 100, seed=r))

    for m in P:
        oof[m][r, te] = P[m]
        fold_rows.append(dict(repeat=r, fold=f, model=m, n_test=len(te),
                              pooled_auroc=pooled_auroc(Y[te], P[m]),
                              macro_auroc=macro_auroc(Y[te], P[m], min_pos=3)))
    msg = "  ".join(f"{m}={pooled_auroc(Y[te], P[m]):.3f}" for m in P)
    print(f"[r{r} f{f} {time.time() - t0:.0f}s] {msg}", flush=True)
    if len(ARG) == 2:
        np.savez_compressed(CACHE / f"fold_{TARGET}_r{r}_f{f}.npz", te=te,
                            **{m.replace("+", "_plus_"): v for m, v in P.items()})

if len(ARG) == 2:
    sys.exit(0)
if ARG == ["merge"]:
    for r in range(REPEATS):
        for f in range(K):
            z = np.load(CACHE / f"fold_{TARGET}_r{r}_f{f}.npz")
            te = z["te"]
            for m in MODELS:
                k = m.replace("+", "_plus_")
                if k in z.files:
                    oof[m][r, te] = z[k]
                    fold_rows.append(dict(repeat=r, fold=f, model=m, n_test=len(te),
                                          pooled_auroc=pooled_auroc(Y[te], z[k]),
                                          macro_auroc=macro_auroc(Y[te], z[k], min_pos=3)))
RESULTS.mkdir(exist_ok=True)
pd.DataFrame(fold_rows).to_csv(RESULTS / f"fold_auroc_{TARGET}.csv", index=False)
np.savez_compressed(CACHE / f"oof_{TARGET}.npz", Y=Y, rows=rows, hid=hid,
                    **{m.replace("+", "_plus_"): v for m, v in oof.items()})
print("saved", CACHE / f"oof_{TARGET}.npz")
