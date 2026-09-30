# Panel completion benchmark (IMPACT341 → IMPACT410)

Public-data replicate of the genomic panel-completion task in the flow-matching abstract, built to test the
ML recommendations in [`docs/panel-completion-ml-review.md`](../docs/panel-completion-ml-review.md).

MSK-CHORD is not public. MSK-IMPACT 2017 (Zehir et al., *Nat Med* 2017; cBioPortal `msk_impact_2017`, ODbL) has
samples sequenced on IMPACT341 and IMPACT410, and IMPACT341 ⊂ IMPACT410 ⊂ IMPACT505. The analogue task is therefore to
predict the 69 IMPACT410-only genes (a subset of the abstract's 164) from the 341 shared genes, in 1,215 NSCLC patients
sequenced on IMPACT410.

## Data

The study archive is not committed. Extract it and point `MSK_IMPACT_DIR` at the folder (default
`data/msk_impact_2017`, which `.gitignore` excludes):

```bash
tar -xzf msk_impact_2017.tar.gz -C data/
export MSK_IMPACT_DIR=$PWD/data/msk_impact_2017
```

`panels/` holds the IMPACT341/410/468/505 gene lists from cBioPortal's `reference_data/gene_panels`.

## Run

```bash
pip install pandas numpy scipy scikit-learn matplotlib torch
cd panel-completion
python 01_dataset_summary.py          # cohort, sparsity, positives per gene
python 02_benchmark.py driver         # all cheap models, driver-like target (~2 min)
python 02_benchmark.py any            # all models incl. flow matching + pan-cancer (hours on CPU)
#   or in parallel, one process per (repeat, fold), then merge:
#   for r in 0 1 2; do for f in 0 1 2 3 4; do OMP_NUM_THREADS=1 python 02_benchmark.py any $r $f & done; done; wait
#   python 02_benchmark.py any merge
python 03_report.py any               # metrics, per-gene table, event types, operating points
python 03_report.py driver
python 04_joint.py                    # joint-profile evaluation of flow-matching samples
python 05_leakage_and_shift.py        # split granularity, unassayed-as-zero, real vs simulated input
python 06_figures.py
```

Set `OMP_NUM_THREADS=1` when running several processes at once: oversubscribed torch threads slow CPU training by
an order of magnitude.

## Files

| File | Contents |
| --- | --- |
| `pc_common.py` | Loading, symbol harmonisation, panel-aware masking, features, fold-stratified AUROC |
| `pc_models.py` | Prevalence, burden/locus per-gene LR, L2 logistic, MLP, conditional flow matching |
| `results/metrics_*.csv` | One row per model: pooled/per-gene AUROC with CIs, AUPRC lift, Brier skill, calibration |
| `results/per_gene_*.csv` | Per-gene AUROC for every model with event counts |
| `results/event_type_*.csv` | Per-gene AUROC split by mutation / amplification / deep deletion |
| `results/operating_points_*.csv` | PPV at fixed sensitivity; triage capture at top-x% referral |
| `results/joint.json` | Energy score, sampled prevalence, co-occurrence, Monte Carlo budget |
| `results/leakage_and_shift.json` | Sample- vs patient-split, unassayed-as-zero, real vs simulated input |
| `figures/` | Figures used in the review |

The generative and pan-cancer models run on repeat 0 (5 folds) only; the other models on 3 repeats × 5 folds.
