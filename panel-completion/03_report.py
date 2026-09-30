"""Metrics from the out-of-fold predictions written by 02_benchmark.py.

Writes results/metrics_<target>.csv (one row per model), results/per_gene_<target>.csv,
results/event_type_<target>.csv and results/operating_points_<target>.csv.
"""
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, precision_recall_curve, roc_curve

from pc_common import CACHE, RESULTS, load, targets, fold_ids, strat_auroc, brier

TARGET = sys.argv[1] if len(sys.argv) > 1 else "any"
MIN_POS = 10   # genes with >= 10 positives across the cohort enter the per-gene mean

z = np.load(CACHE / f"oof_{TARGET}.npz")
Y, rows, hid = z["Y"], z["rows"], z["hid"]
models = [k for k in z.files if k not in ("Y", "rows", "hid")]
name = {k: k.replace("_plus_", "+") for k in models}
d = load()
genes = d["genes"][hid]
folds = pd.read_csv(RESULTS / f"fold_auroc_{TARGET}.csv")
prev = z["prevalence"]


def gene_aurocs(Y, P, fold, min_pos=MIN_POS):
    return np.array([strat_auroc(Y[:, j], P[:, j], fold) if Y[:, j].sum() >= min_pos else np.nan
                     for j in range(Y.shape[1])])


def fold_mean(fn, Y, P, fold):
    return np.mean([fn(Y[fold == f], P[fold == f]) for f in np.unique(fold)])


def p_any(P):
    """P(>=1 hidden alteration), treating genes as conditionally independent."""
    return 1 - np.prod(1 - P.astype(np.float64), axis=1)


rows_out, gene_tabs = [], []
y_any = (Y.sum(1) > 0).astype(int)
R = z[models[0]].shape[0]
FOLD = [fold_ids(len(Y), r) for r in range(R)]
gene_ok = Y.sum(0) >= MIN_POS
rng = np.random.default_rng(0)
boot = [rng.integers(0, len(Y), len(Y)) for _ in range(200)]
boot_macro, boot_pooled = {}, {}
for k in models:
    P_all = z[k]                                  # (repeats, n, genes); NaN where not run
    reps = [r for r in range(R) if not np.isnan(P_all[r]).any()]
    bs_prev = np.mean([fold_mean(brier, Y, prev[r], FOLD[r]) for r in reps])
    pooled = [strat_auroc(Y.ravel(), P_all[r].ravel(), np.repeat(FOLD[r], Y.shape[1])) for r in reps]
    ga = np.array([gene_aurocs(Y, P_all[r], FOLD[r]) for r in reps])
    macro = np.nanmean(ga, axis=1)
    P0, F0 = P_all[0], FOLD[0]
    bp, bm = [], []
    for i in boot:
        bp.append(strat_auroc(Y[i].ravel(), P0[i].ravel(), np.repeat(F0[i], Y.shape[1])))
        bm.append(np.nanmean([strat_auroc(Y[i, j], P0[i, j], F0[i]) for j in np.where(gene_ok)[0]]))
    auprc = [fold_mean(lambda a, b: average_precision_score(a.ravel(), b.ravel()), Y, P_all[r], FOLD[r])
             for r in reps]
    lift = []
    for r in reps:
        for j in np.where(gene_ok)[0]:
            lift.append(fold_mean(lambda a, b: average_precision_score(a, b) / max(a.mean(), 1e-9)
                                  if a.sum() else np.nan, Y[:, j], P_all[r][:, j], FOLD[r]))
    bs = np.mean([fold_mean(brier, Y, P_all[r], FOLD[r]) for r in reps])
    boot_macro[name[k]], boot_pooled[name[k]] = np.array(bm), np.array(bp)
    fa = folds[folds.model == name[k]]
    rows_out.append(dict(
        model=name[k], n_repeats=len(reps),
        pooled_auroc=np.mean(pooled),
        pooled_auroc_ci_lo=np.nanpercentile(bp, 2.5), pooled_auroc_ci_hi=np.nanpercentile(bp, 97.5),
        single_split_pooled_auroc_min=fa.pooled_auroc.min(),
        single_split_pooled_auroc_max=fa.pooled_auroc.max(),
        single_split_pooled_auroc_sd=fa.pooled_auroc.std(),
        macro_auroc=np.mean(macro),
        macro_auroc_ci_lo=np.nanpercentile(bm, 2.5), macro_auroc_ci_hi=np.nanpercentile(bm, 97.5),
        n_genes_macro=int(gene_ok.sum()),
        pooled_auprc=np.mean(auprc), pooled_prevalence=Y.mean(),
        macro_auprc_lift=np.nanmean(lift),
        brier_skill_vs_prevalence=1 - bs / bs_prev,
        predicted_over_observed=float(np.mean([P_all[r].sum() / Y.sum() for r in reps])),
        patient_any_auroc=np.mean([strat_auroc(y_any, p_any(P_all[r]), FOLD[r]) for r in reps]),
    ))
    gene_tabs.append(pd.DataFrame(dict(gene=genes, model=name[k], auroc=np.nanmean(ga, axis=0))))

m = pd.DataFrame(rows_out)
# paired comparison against L2 logistic regression on the same bootstrap resamples (repeat 0)
for col, b in [("macro", boot_macro), ("pooled", boot_pooled)]:
    ref = b["logistic"]
    diff = {k: v - ref for k, v in b.items()}
    m[f"delta_{col}_vs_logistic"] = m.model.map(lambda k: np.nanmean(diff[k]))
    m[f"delta_{col}_vs_logistic_ci_lo"] = m.model.map(lambda k: np.nanpercentile(diff[k], 2.5))
    m[f"delta_{col}_vs_logistic_ci_hi"] = m.model.map(lambda k: np.nanpercentile(diff[k], 97.5))
RESULTS.mkdir(exist_ok=True)
m.to_csv(RESULTS / f"metrics_{TARGET}.csv", index=False, float_format="%.4f")
pd.set_option("display.width", 250)
print(m[["model", "pooled_auroc", "pooled_auroc_ci_lo", "pooled_auroc_ci_hi", "single_split_pooled_auroc_min",
         "single_split_pooled_auroc_max", "macro_auroc", "macro_auroc_ci_lo", "macro_auroc_ci_hi",
         "pooled_auprc", "macro_auprc_lift", "brier_skill_vs_prevalence", "predicted_over_observed",
         "patient_any_auroc", "delta_macro_vs_logistic", "delta_macro_vs_logistic_ci_lo",
         "delta_macro_vs_logistic_ci_hi"]].round(3).to_string(index=False))

# ---------------------------------------------------------------- per gene, wide
g = pd.concat(gene_tabs)
wide = g.pivot_table(index="gene", columns="model", values="auroc")
meta = pd.DataFrame(dict(n_pos=Y.sum(0), prevalence_rate=Y.mean(0)), index=genes)
kinds = {k: targets(d, rows, hid, k).sum(0) for k in ("mut", "amp", "dele")}
for k, v in kinds.items():
    meta[f"n_{k}"] = pd.Series(v, index=genes)
meta["chrom"] = pd.Series(d["chrom"][hid], index=genes)
wide = meta.join(wide).sort_values("n_pos", ascending=False)
wide.to_csv(RESULTS / f"per_gene_{TARGET}.csv", float_format="%.4f")

# ---------------------------------------------------- where does the signal come from?
# Per-gene AUROC with positives restricted to one event type (other positives dropped).
ev = []
for kind in ("mut", "amp", "dele"):
    # for the driver target the mutation positives are the driver-like ones only
    yk = targets(d, rows, hid, "drv" if (kind == "mut" and TARGET == "driver") else kind)
    for k in models:
        P = z[k][0]
        vals, w = [], []
        for j in range(Y.shape[1]):
            keep = (Y[:, j] == 0) | (yk[:, j] == 1)
            y = yk[keep, j]
            if y.sum() >= 5:
                vals.append(strat_auroc(y, P[keep, j], FOLD[0][keep]))
                w.append(y.sum())
        ev.append(dict(event=kind, model=name[k], n_genes=len(vals), n_pos=int(np.sum(w)),
                       weighted_auroc=np.average(vals, weights=w) if vals else np.nan))
ev = pd.DataFrame(ev)
ev.to_csv(RESULTS / f"event_type_{TARGET}.csv", index=False, float_format="%.4f")
print("\nPer-gene AUROC by event type (positives-weighted mean):")
print(ev.pivot(index="model", columns="event", values="weighted_auroc").round(3).to_string())

# --------------------------------------------------------- clinical operating points
op = []
for k in models:
    P = z[k][0]
    fpr, tpr, _ = roc_curve(Y.ravel(), P.ravel())
    pr, rc, _ = precision_recall_curve(Y.ravel(), P.ravel())
    for sens in (0.5, 0.8, 0.9):
        i = np.searchsorted(tpr, sens)
        j = np.where(rc >= sens)[0]
        op.append(dict(model=name[k], sensitivity=sens, specificity=1 - fpr[min(i, len(fpr) - 1)],
                       ppv=pr[j].max() if len(j) else np.nan))
    # triage: refer the top x% of patients by P(any hidden alteration) for the large panel
    s = p_any(P)
    order = np.argsort(-s)
    for frac in (0.1, 0.25, 0.5):
        top = order[: int(frac * len(s))]
        op.append(dict(model=name[k], triage_fraction=frac,
                       patients_with_hidden_alteration_captured=y_any[top].sum() / y_any.sum()))
op = pd.DataFrame(op)
op.to_csv(RESULTS / f"operating_points_{TARGET}.csv", index=False, float_format="%.4f")
print("\nPPV at fixed sensitivity (pooled gene-patient pairs):")
print(op.dropna(subset=["sensitivity"]).pivot(index="model", columns="sensitivity", values="ppv").round(3).to_string())
print("\nTriage: share of patients with >=1 hidden alteration captured when referring top x%:")
print(op.dropna(subset=["triage_fraction"]).pivot(index="model", columns="triage_fraction",
      values="patients_with_hidden_alteration_captured").round(3).to_string())
