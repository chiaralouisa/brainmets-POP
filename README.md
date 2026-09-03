# brainmets-POP

Reanalysis of the monocentric NSCLC brain-metastasis cohort behind ESMO Abstract 2202
("Synchronous and Metachronous Brain Metastases in Non-Small Cell Lung Cancer Share a
9p21.3 Co-Deletion").

## Data

Patient-level data is **not** committed — the cohort file carries dates of birth and
diagnosis dates and is re-identifiable. Keep `20260719cohort.xlsx` outside the repo and
point the scripts at it:

```bash
export COHORT_XLSX=/secure/path/20260719cohort.xlsx
```

## Analysis

```bash
pip install pandas openpyxl scipy statsmodels
python analysis/01_coalterations.py      # gene and co-alteration frequencies, sBM vs mBM
python analysis/02_survival.py           # OS under three clocks; immortal-time correction
python analysis/03_9p21_prognostic.py    # 9p21.3 co-deletion definition audit + Cox models
python analysis/04_data_quality.py       # missingness, duplicate variants, histology audit
python analysis/05_abstract_statistics.py # figures quoted in the revised abstract
python analysis/06_external_background_rate.py --live  # background 9p21.3 rate (needs cbioportal.org)
python analysis/07_figures.py            # Figure 1: both survival clocks with numbers at risk
python analysis/10_oncoplot.py           # Figure 2: oncoplot, sBM beside mBM
python analysis/08_immortal_time_and_covariates.py  # landmark, time-dependent Cox, CNS therapy
```

## Headline result

Overall survival in the source file is measured from primary lung-cancer diagnosis, which
builds in immortal time: a patient cannot be classified metachronous without first
surviving to develop a brain metastasis. Re-anchoring the clock reverses the direction of
the comparison.

| Survival clock | sBM (n=88) | mBM (n=28) | log-rank |
| --- | --- | --- | --- |
| From primary diagnosis | 25.0 mo | 23.0 mo | p = 0.47 |
| From brain-met diagnosis | 25.0 mo | 11.1 mo | **p < 0.001**, HR 2.96 (1.82–4.83) |
| 4-month landmark (residual) | 30.0 mo | 19.0 mo | p = 0.20 |

Full review, including reconciliation of the abstract against the cohort file and the
proposed hypothesis for the manuscript: [`docs/manuscript-review.html`](docs/manuscript-review.html).

## Cohort handling

All 116 patients are analysed as NSCLC; registry histology codes indicating small-cell or
carcinoid disease are treated as coding artifacts. Excluding them (n = 109) leaves the
survival result unchanged (p < 0.001). Post-BM survival is floored at one day so the single
record whose BM date falls after last follow-up still contributes, giving 28 evaluable mBM
patients.

Revised abstract: [`docs/abstract-revised.md`](docs/abstract-revised.md).

## 9p21.3 is the background rate, not enrichment

Against 29,379 NSCLC cases profiled by comparable hybrid-capture CGP, the cohort's 9p21.3
co-deletion rate is not elevated: 15.5% vs 13.4%, OR 1.19, p = 0.49. Benchmarking instead
against AACR GENIE (5.7%) would suggest three-fold enrichment, but that difference is gene-panel
coverage rather than biology. See [`docs/external-background-rate.md`](docs/external-background-rate.md).

## Manuscript

Draft: [`docs/manuscript-draft.md`](docs/manuscript-draft.md), also as `docs/manuscript-draft.docx`
for circulation. Thirteen `[TO COMPLETE]` markers flag what needs data not in the current
cohort file — chiefly the BM-free comparator arm and CNS-directed therapy.

Three analyses are **not estimable in a BM-only cohort** and are specified against the
comparator arm instead: enrichment testing, a Fine–Gray competing-risks model for time to
BM, and a time-dependent Cox model (BM status is perfectly separated — 0 deaths across 28
BM-free intervals — so the model is unidentifiable). The pre-specified 4-month landmark is
the immortal-time correction that does work here.
