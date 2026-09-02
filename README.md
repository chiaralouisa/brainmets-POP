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
```

## Headline result

Overall survival in the source file is measured from primary lung-cancer diagnosis, which
builds in immortal time: a patient cannot be classified metachronous without first
surviving to develop a brain metastasis. Re-anchoring the clock reverses the direction of
the comparison.

| Survival clock | sBM (n=88) | mBM (n=28) | log-rank |
| --- | --- | --- | --- |
| From primary diagnosis | 25.0 mo | 23.0 mo | p = 0.47 |
| From brain-met diagnosis | 25.0 mo | 11.1 mo | **p < 0.001** |
| 4-month landmark (residual) | 30.0 mo | 19.0 mo | p = 0.20 |

Full review, including reconciliation of the abstract against the cohort file and the
proposed hypothesis for the manuscript: [`docs/manuscript-review.html`](docs/manuscript-review.html).
