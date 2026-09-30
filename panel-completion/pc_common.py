"""Shared loading, encoding and evaluation code for the panel-completion benchmark.

Replicates the IMPACT341 -> IMPACT505 completion task of the abstract on public data:
MSK-IMPACT 2017 (Zehir et al., Nat Med 2017; cBioPortal study msk_impact_2017, ODbL)
holds samples sequenced on IMPACT341 (suffix IM3) and IMPACT410 (suffix IM5).
IMPACT341 is a strict subset of IMPACT410, so the analogue task is to predict the
69 IMPACT410-only genes from the 341 shared genes, on NSCLC samples sequenced with
IMPACT410. All 69 genes are also in IMPACT505, so they are a subset of the abstract's
164 held-out genes.

Raw data is not committed. Point MSK_IMPACT_DIR at the extracted study folder.
"""
import os
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, average_precision_score

HERE = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("MSK_IMPACT_DIR", HERE.parent / "data" / "msk_impact_2017"))
CACHE = HERE / "cache"
RESULTS = HERE / "results"
FIGURES = HERE / "figures"

# cBioPortal files mix legacy and current HGNC symbols; panels use current ones.
ALIASES = {
    "FAM175A": "ABRAXAS1", "FAM46C": "TENT5C", "MLL": "KMT2A", "MLL2": "KMT2D",
    "MLL3": "KMT2C", "MRE11A": "MRE11", "MYCL1": "MYCL", "PAK7": "PAK5", "PARK2": "PRKN",
    "RFWD2": "COP1", "TCEB1": "ELOC", "H3F3A": "H3-3A", "H3F3B": "H3-3B", "H3F3C": "H3-5",
    "HIST1H1C": "H1-2", "HIST1H2BD": "H2BC5", "HIST1H3A": "H3C1", "HIST1H3B": "H3C2",
    "HIST1H3C": "H3C3", "HIST1H3D": "H3C4", "HIST1H3E": "H3C6", "HIST1H3F": "H3C7",
    "HIST1H3G": "H3C8", "HIST1H3H": "H3C10", "HIST1H3I": "H3C11", "HIST1H3J": "H3C12",
    "HIST2H3C": "H3C14", "HIST2H3D": "H3C13", "HIST3H3": "H3-4",
}

NONSYN = {
    "Missense_Mutation", "Nonsense_Mutation", "Frame_Shift_Del", "Frame_Shift_Ins",
    "Splice_Site", "In_Frame_Del", "In_Frame_Ins", "Translation_Start_Site", "Nonstop_Mutation",
}
TRUNCATING = {"Nonsense_Mutation", "Frame_Shift_Del", "Frame_Shift_Ins", "Splice_Site",
              "Translation_Start_Site", "Nonstop_Mutation"}


def panel(name):
    return [g.strip() for g in open(HERE / "panels" / f"{name}.txt") if g.strip()]


def load(force=False):
    """Return a dict of sample-level binary matrices over the IMPACT410 gene set.

    mut / amp / dele: samples x genes (0/1). drv: truncating or recurrent missense
    (same protein change in >=3 samples cohort-wide), a proxy for driver status since the
    file carries no OncoKB/hotspot annotation. For IMPACT341 samples the 69 unassayed
    genes are set to -1 (not assayed): cBioPortal's CNA matrix stores them as 0, which
    silently turns "not measured" into "wild type".
    """
    CACHE.mkdir(exist_ok=True)
    f = CACHE / "impact2017.npz"
    if f.exists() and not force:
        z = np.load(f, allow_pickle=True)
        d = {k: z[k] for k in z.files}
        d["clin"] = pd.read_pickle(CACHE / "clin.pkl")
        return d

    genes = panel("IMPACT410")
    gi = {g: i for i, g in enumerate(genes)}
    s = pd.read_csv(DATA_DIR / "data_clinical_sample.txt", sep="\t", comment="#")
    p = pd.read_csv(DATA_DIR / "data_clinical_patient.txt", sep="\t", comment="#")
    s = s.merge(p[["PATIENT_ID", "SEX", "SMOKING_HISTORY"]], on="PATIENT_ID", how="left")
    s["PANEL"] = s.SAMPLE_ID.str[-3:].map({"IM3": "IMPACT341", "IM5": "IMPACT410"})
    si = {x: i for i, x in enumerate(s.SAMPLE_ID)}
    n, G = len(s), len(genes)

    m = pd.read_csv(DATA_DIR / "data_mutations.txt", sep="\t", comment="#", low_memory=False,
                    usecols=["Hugo_Symbol", "Tumor_Sample_Barcode", "Variant_Classification",
                             "HGVSp_Short", "Chromosome", "Start_Position"])
    m["gene"] = m.Hugo_Symbol.replace(ALIASES)
    m = m[m.gene.isin(gi) & m.Tumor_Sample_Barcode.isin(si)]
    # gene positions (hg19) from observed variant coordinates, for the locus baseline
    pos = m.groupby("gene").agg(chrom=("Chromosome", "first"), pos=("Start_Position", "median"))
    m = m[m.Variant_Classification.isin(NONSYN)]
    rec = m.groupby(["gene", "HGVSp_Short"]).Tumor_Sample_Barcode.transform("nunique") >= 3
    m["drv"] = m.Variant_Classification.isin(TRUNCATING) | (
        (m.Variant_Classification == "Missense_Mutation") & rec)

    mut = np.zeros((n, G), np.int8)
    drv = np.zeros((n, G), np.int8)
    r, c = m.Tumor_Sample_Barcode.map(si).values, m.gene.map(gi).values
    mut[r, c] = 1
    drv[r[m.drv.values], c[m.drv.values]] = 1

    cna = pd.read_csv(DATA_DIR / "data_cna.txt", sep="\t", index_col=0)
    cna.index = cna.index.map(lambda g: ALIASES.get(g, g))
    cna = cna.reindex(index=genes, columns=s.SAMPLE_ID).T.values
    amp = (cna == 2).astype(np.int8)
    dele = (cna == -2).astype(np.int8)

    unassayed = np.zeros((n, G), bool)
    only410 = [gi[g] for g in genes if g not in set(panel("IMPACT341"))]
    unassayed[np.ix_((s.PANEL == "IMPACT341").values, only410)] = True
    mut, drv, amp, dele = (np.where(unassayed, -1, x).astype(np.int8) for x in (mut, drv, amp, dele))

    chrom = pos.reindex(genes).chrom.astype(str).values
    gpos = pos.reindex(genes).pos.values
    np.savez_compressed(f, genes=np.array(genes), mut=mut, drv=drv, amp=amp, dele=dele,
                        chrom=chrom, gpos=gpos)
    clin = s[["PATIENT_ID", "SAMPLE_ID", "PANEL", "CANCER_TYPE", "CANCER_TYPE_DETAILED",
              "SAMPLE_TYPE", "TUMOR_PURITY", "SEX", "SMOKING_HISTORY", "TMB_NONSYNONYMOUS"]]
    clin.to_pickle(CACHE / "clin.pkl")
    return load()


def split_panels(genes, small="IMPACT341"):
    obs = set(panel(small))
    o = np.array([g in obs for g in genes])
    return np.where(o)[0], np.where(~o)[0]


def one_sample_per_patient(clin, idx):
    """Keep one sample per patient (the first, T01, by default). Splitting samples rather
    than patients lets a primary and its metastasis land on both sides of the split."""
    sub = clin.iloc[idx]
    keep = sub.sort_values("SAMPLE_ID").drop_duplicates("PATIENT_ID").index
    return np.array(sorted(keep))


def features(d, rows, obs, clinical=False, cancer_types=None):
    """Observed-panel features: mut/amp/del indicators for the 341 genes plus burden
    summaries computed only from what the small panel measures."""
    mut, amp, dele = (d[k][np.ix_(rows, obs)].astype(np.float32) for k in ("mut", "amp", "dele"))
    burden = np.stack([np.log1p(mut.sum(1)), np.log1p(amp.sum(1)), np.log1p(dele.sum(1))], 1)
    X = [mut, amp, dele, burden]
    if clinical:
        c = d["clin"].iloc[rows]
        X.append(np.stack([
            (c.SMOKING_HISTORY == "Prev/Curr Smoker").values,
            (c.SMOKING_HISTORY == "Never").values,
            (c.SEX == "Female").values,
            (c.SAMPLE_TYPE == "Metastasis").values,
            (c.CANCER_TYPE_DETAILED == "Lung Squamous Cell Carcinoma").values,
        ], 1).astype(np.float32))
    if cancer_types is not None:
        ct = d["clin"].iloc[rows].CANCER_TYPE.values
        X.append(np.stack([ct == t for t in cancer_types], 1).astype(np.float32))
    return np.hstack(X)


def targets(d, rows, hid, kind="any"):
    if kind == "any":
        y = (d["mut"] == 1) | (d["amp"] == 1) | (d["dele"] == 1)
    elif kind == "driver":
        y = (d["drv"] == 1) | (d["amp"] == 1) | (d["dele"] == 1)
    else:
        y = d[kind] == 1
    return y[np.ix_(rows, hid)].astype(np.int8)


def patient_folds(n, k, seed):
    """K folds over row positions; rows are already one per patient."""
    rng = np.random.default_rng(seed)
    perm = rng.permutation(n)
    return [np.sort(perm[i::k]) for i in range(k)]


# ----------------------------------------------------------------------------- metrics

def fold_ids(n, repeat, K=5):
    """Fold index per row, matching patient_folds(n, K, seed=repeat) in 02_benchmark.py."""
    f = np.zeros(n, int)
    for i, te in enumerate(patient_folds(n, K, seed=repeat)):
        f[te] = i
    return f


def strat_auroc(y, p, fold):
    """AUROC counting only positive-negative pairs from the same fold. Pooling OOF scores
    across folds compares predictions from different models: with rare targets a fold
    holding more positives trains on a lower prevalence, so the prevalence-only baseline
    scores ~0.38 per gene instead of 0.5. Stratifying removes that artefact."""
    num = den = 0.0
    for f in np.unique(fold):
        m = fold == f
        npos = y[m].sum()
        nneg = m.sum() - npos
        if npos and nneg:
            num += roc_auc_score(y[m], p[m]) * npos * nneg
            den += npos * nneg
    return num / den if den else np.nan


def pooled_auroc(Y, P):
    """The abstract's metric: one AUROC over all gene-patient pairs."""
    y, p = Y.ravel(), P.ravel()
    return roc_auc_score(y, p) if 0 < y.sum() < len(y) else np.nan


def per_gene(Y, P, min_pos=5):
    """Per-gene AUROC/AUPRC on a single test set. A per-gene prevalence model scores
    exactly 0.5 AUROC here, so any value above 0.5 is patient-specific information."""
    out = []
    for j in range(Y.shape[1]):
        y, p = Y[:, j], P[:, j]
        npos = int(y.sum())
        if npos >= min_pos and npos < len(y):
            out.append((j, npos, roc_auc_score(y, p), average_precision_score(y, p), y.mean()))
        else:
            out.append((j, npos, np.nan, np.nan, y.mean()))
    return pd.DataFrame(out, columns=["j", "n_pos", "auroc", "auprc", "prevalence"])


def macro_auroc(Y, P, min_pos=5):
    return np.nanmean(per_gene(Y, P, min_pos).auroc)


def brier(Y, P):
    return float(np.mean((Y - P) ** 2))
