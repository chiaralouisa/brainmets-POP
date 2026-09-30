"""Cohort and sparsity summary for the IMPACT341 -> IMPACT410 analogue task.

Also answers a design question for the abstract's single 15% test split: how many held-out
genes have enough positives in the test set for a per-gene AUROC to mean anything?
"""
import json

import numpy as np
import pandas as pd

from pc_common import RESULTS, load, split_panels, one_sample_per_patient, targets

d = load(force=True)
clin, genes = d["clin"], d["genes"]
obs, hid = split_panels(genes)
im5 = one_sample_per_patient(clin, np.where(clin.PANEL == "IMPACT410")[0])
rows = im5[clin.CANCER_TYPE.values[im5] == "Non-Small Cell Lung Cancer"]
ns_samples = (clin.PANEL == "IMPACT410") & (clin.CANCER_TYPE == "Non-Small Cell Lung Cancer")
Y = targets(d, rows, hid)
by_kind = {k: targets(d, rows, hid, k) for k in ("mut", "amp", "dele", "driver")}
pos = Y.sum(0)

# test positives per gene under a single 15% split, 1000 random draws
rng = np.random.default_rng(0)
n_te = int(0.15 * len(rows))
ok5, zero = [], []
for _ in range(1000):
    te = rng.choice(len(rows), n_te, replace=False)
    c = Y[te].sum(0)
    ok5.append((c >= 5).sum())
    zero.append((c == 0).sum())

out = dict(
    impact341_genes=len(obs), hidden_genes=len(hid),
    nsclc_impact410_samples=int(ns_samples.sum()),
    nsclc_impact410_patients=int(len(rows)),
    patients_with_multiple_impact410_samples=int(clin[ns_samples].PATIENT_ID.duplicated().sum()),
    pair_sparsity_any=float(Y.mean()),
    positives_any=int(Y.sum()),
    positives_by_event={k: int(v.sum()) for k, v in by_kind.items()},
    patients_with_any_hidden_alteration=float((Y.sum(1) > 0).mean()),
    genes_lt5_positives_whole_cohort=int((pos < 5).sum()),
    genes_ge10_positives_whole_cohort=int((pos >= 10).sum()),
    single_15pct_split=dict(n_test=n_te, genes_with_ge5_test_positives_median=float(np.median(ok5)),
                            genes_with_zero_test_positives_median=float(np.median(zero))),
    genes_without_position=[str(g) for g, c in zip(genes[hid], d["chrom"][hid]) if pd.isna(c)],
)
RESULTS.mkdir(exist_ok=True)
json.dump(out, open(RESULTS / "dataset_summary.json", "w"), indent=1)
print(json.dumps(out, indent=1))
tab = pd.DataFrame({"gene": genes[hid], "n_pos": pos,
                    **{f"n_{k}": v.sum(0) for k, v in by_kind.items()}}).sort_values("n_pos", ascending=False)
print(tab.head(15).to_string(index=False))
