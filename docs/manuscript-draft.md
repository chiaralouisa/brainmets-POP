# Post-Metastasis Survival and Genomic Architecture in Synchronous versus Metachronous Brain Metastases from Non-Small Cell Lung Cancer

**Draft v0.1** — figures in `figures/`, statistics reproducible via `analysis/`.
Sections marked **[TO COMPLETE]** require data not present in the current cohort file.

L. Hempel, M. Sarwary, L. Fabregas-Ibanez, N. Miglino, M. Nowak, S. Rahmani Khajouei,
M. Zoche, A. Wicki, L. Boos

Department of Medical Oncology and Hematology, University Hospital Zurich / University of
Zurich, Zurich, Switzerland

---

## 1. Introduction

Brain metastases (BM) develop in up to 40% of patients with non-small cell lung cancer
(NSCLC) and remain a dominant cause of morbidity and death. Patients are conventionally
divided into those presenting with BM at or near primary diagnosis (synchronous, sBM) and
those developing BM later in the disease course (metachronous, mBM). The distinction is
widely used to guide surveillance and local therapy, yet its biological basis is unclear:
it is not established whether the two groups differ in their genomic architecture, or
whether the distinction carries independent prognostic weight.

Comparative survival data are difficult to interpret because of how they are measured.
Studies of sBM versus mBM almost always report overall survival (OS) from primary
diagnosis. Under that time origin, a patient cannot enter the metachronous group without
first surviving long enough for BM to appear — the interval between diagnosis and BM onset
is immortal time for the mBM group and is unavailable to the sBM group. Metachronous
disease therefore accrues an arithmetic survival advantage that is an artifact of group
definition rather than a property of the disease.

We analysed a monocentric cohort of patients with NSCLC and radiologically confirmed BM,
all of whom underwent comprehensive genomic profiling (CGP). We asked three questions.
First, whether the choice of survival time origin changes the direction of the sBM/mBM
comparison. Second, whether the two groups differ in recurrent genomic alterations or
co-alteration patterns. Third, whether co-deletion at 9p21.3 — the most frequent complex
alteration in this cohort — occurs more often in brain-metastatic NSCLC than in unselected
NSCLC.

---

## 2. Methods

### 2.1 Study design and population

Consecutive patients treated at the Department of Medical Oncology and Hematology,
University Hospital Zurich, with a diagnosis of NSCLC and radiologically confirmed brain
metastases, and with CGP available, were retrospectively identified. All histologic
subtypes were eligible. Histology was reviewed and reclassified where registry coding was
discordant with the clinical diagnosis. **[TO COMPLETE: state the accrual window, the
database queried, the ethics approval / cantonal ethics committee reference number, and
whether general consent applied.]**

Patients were classified as **synchronous BM (sBM)** where BM were present at primary
diagnosis or diagnosed within 3 months, and **metachronous BM (mBM)** where BM were
diagnosed more than 3 months after primary diagnosis. The 3-month threshold follows
convention in the BM literature. In this cohort the classification is unambiguous: the
latest sBM interval was 71 days and the earliest mBM interval 121 days, so no patient lies
near the boundary.

### 2.2 Brain-metastasis-free comparator cohort **[TO COMPLETE]**

Enrichment of any alteration in brain-metastatic disease cannot be established from a
cohort in which every patient has brain metastases. A comparator arm is required.

*Specification for assembly.* From the same institutional CGP archive and the same accrual
window, identify patients with NSCLC profiled on the same platform who did **not** develop
brain metastases. To avoid the mirror image of the bias this paper is about, BM-free status
must be defined over an adequate observation period rather than at a single timepoint:
require a minimum documented BM-free follow-up (suggested: 12 months from primary
diagnosis, with brain imaging performed), and record for each patient whether brain imaging
was ever obtained, since undetected BM in unimaged patients would dilute the comparator.
Match or adjust on stage at diagnosis, histology, and follow-up duration. Report the
resulting flow in the CONSORT-style diagram (Figure S1).

This arm supports three analyses that the BM-only cohort cannot support: (i) enrichment
testing for 9p21.3 and other alterations; (ii) a Fine–Gray competing-risks model for time
to BM (§2.6); (iii) a time-dependent Cox model with BM as a time-varying covariate (§2.6).

### 2.3 Genomic profiling

CGP was performed on tumour tissue using FoundationOne CDx (Foundation Medicine,
Cambridge, MA). **[TO COMPLETE: confirm the profiling window, report the number of patients
profiled on each assay version, and state whether any patient was profiled on
FoundationOne Liquid CDx — liquid biopsy has lower sensitivity for homozygous copy-number
loss and such cases should be excluded from the co-deletion denominator or handled in
sensitivity analysis.]**

Alterations were analysed at the patient level. Variant lists were de-duplicated before
any frequency was computed, since repeated entries for the same variant in the same patient
would otherwise inflate counts. Copy-number loss at 9p21.3 was defined as loss of **all
three** of *CDKN2A*, *CDKN2B* and *MTAP*; *CDKN2A* point mutations were not counted toward
the co-deletion. PD-L1 was assessed by immunohistochemistry (VENTANA PD-L1 SP263) and
reported as tumour cell (TC) and immune cell (IC) scores.

### 2.4 External reference rates

The observed 9p21.3 co-deletion frequency was benchmarked against published rates in
unselected NSCLC. The primary reference was a cohort of 29,379 advanced NSCLC cases
profiled by hybrid-capture CGP, chosen because the assay class matches the present cohort
and copy-number calling is therefore comparable.

Panel-aggregating registries such as AACR Project GENIE were **not** used as the primary
reference. Many contributing panels do not tile *MTAP*, and samples not assayed for the
gene nevertheless remain in the denominator, so the reported deletion frequency is diluted.
Benchmarking a FoundationOne cohort against an unrestricted GENIE denominator produces an
apparent enrichment that reflects panel coverage rather than biology (§3.5). Where GENIE is
used, the denominator must be restricted to samples whose panel covers all three genes.

### 2.5 Endpoints and time origins

The **primary endpoint** was overall survival measured **from the date of brain-metastasis
diagnosis**. The **secondary endpoint** was overall survival from primary lung cancer
diagnosis, the conventional time origin, reported alongside the primary endpoint so the two
can be compared directly. Patients alive at last contact were censored.

**[TO COMPLETE: the cohort file records overall survival as a single duration without an
explicit unit, death date, or censoring indicator. Add `date_of_death`,
`date_last_followup` and an explicit censoring flag; state the database lock date; and
report median follow-up by reverse Kaplan–Meier.]**

### 2.6 Statistical analysis

Continuous variables are summarised as mean ± SD with range, or median with interquartile
range where distributions are skewed; categorical variables as n (%). Survival was
estimated by Kaplan–Meier and compared by log-rank test. Hazard ratios were estimated by
Cox proportional-hazards regression; the multivariable model included group, 9p21.3
co-deletion, *TP53* alteration, age, sex, adenocarcinoma histology and receipt of
radiotherapy. Confidence intervals for median survival were obtained by bootstrap
(2,000 resamples). Categorical comparisons used Fisher's exact test.

**Immortal time.** Two standard corrections exist, and only one is estimable in a
BM-only cohort. A **landmark analysis** was pre-specified at 4 months — beyond the 3-month
classification threshold, so group membership is fixed before follow-up begins — with
patients dying before the landmark excluded and survival measured from the landmark. This
is reported as a sensitivity analysis for the secondary endpoint. A **time-dependent Cox
model**, with BM entered as a time-varying covariate, is *not* estimable here: because BM
is an inclusion criterion, every BM-free interval is censored at BM onset and no death
occurs in the BM-free state (0 deaths across 28 BM-free intervals). The covariate is
perfectly separated and the model unidentifiable. It becomes estimable only once the
BM-free comparator arm (§2.2) contributes deaths without BM.

**Competing risks.** Death without brain metastasis competes with BM onset, and
Kaplan–Meier overestimates cumulative BM incidence when it is ignored. A Fine–Gray
subdistribution model is likewise not estimable in the present cohort, where BM incidence
is 100% by construction; it is specified for the comparator-arm analysis and reported
there. **[TO COMPLETE once §2.2 exists.]**

**Multiplicity.** All genomic comparisons were corrected for multiple testing by the
Benjamini–Hochberg false discovery rate procedure across the full set of recurrent
alterations tested (those observed in ≥5 patients). Adjusted q-values are reported in the
main tables alongside raw p-values.

Analyses were performed in Python 3.11 (pandas, statsmodels, scipy). Analysis code is
available at **[TO COMPLETE: repository URL / DOI]**.

---

## 3. Results

### 3.1 Cohort characteristics

116 patients met the inclusion criteria: 88 sBM (75.9%) and 28 mBM (24.1%). The groups were
balanced for age at diagnosis (61.6 ± 9.4 vs 62.8 ± 10.0 years), sex (56.8% vs 57.1% male)
and adenocarcinoma histology (78.4% vs 85.7%). 89 deaths were observed (63 sBM, 26 mBM).

Time from primary diagnosis to BM was 2 ± 9 days in sBM (range 0–71) and 559 ± 589 days in
mBM (median 347, IQR 215–622, range 121–2466). PD-L1 TC0 was frequent in both groups
(33.0% vs 35.7%); IC1 was the predominant immune-cell pattern in sBM (31.8% vs 21.4%).
Tumour mutational burden was high in 13.6% of sBM and 3.6% of mBM; microsatellite status
was stable in 87.5% and 92.9%. Full baseline characteristics are given in **Table 1**.

### 3.2 The survival comparison reverses with the time origin

Measured from **primary diagnosis**, median OS did not differ between groups: 25.0 months
in sBM versus 23.0 months in mBM (log-rank p = 0.47; HR for mBM 1.18, 95% CI 0.75–1.87).
The pre-specified 4-month landmark analysis gave the same conclusion (residual median 30.0
vs 19.0 months, p = 0.20; HR 1.35, 95% CI 0.84–2.15).

Measured from **brain-metastasis diagnosis**, the comparison reversed and became strongly
significant. Median OS was 25.0 months (95% CI 18.0–40.0) in sBM versus 11.1 months
(95% CI 4.9–13.1) in mBM (log-rank p < 0.001; HR 2.96, 95% CI 1.82–4.83). Adjustment for
age, sex and histology did not attenuate the effect (HR 2.92, 95% CI 1.77–4.82). Both
clocks are shown side by side with numbers at risk in **Figure 1**.

The synchronous curve is essentially unchanged between the two panels, because time to BM
is near zero in that group. The entire difference arises from the metachronous group, whose
median more than halves once the interval preceding BM is removed from the survival time.

In the multivariable model for survival from BM diagnosis (**Table 3**), metachronous
timing remained the strongest predictor (HR 3.02, 95% CI 1.83–5.00, p < 0.001). Receipt of
radiotherapy was also associated with shorter survival (HR 2.04, 95% CI 1.27–3.28,
p = 0.003); this variable does not distinguish CNS-directed from thoracic radiotherapy
(§5) and is interpreted as a marker of disease burden rather than a treatment effect.
9p21.3 co-deletion (HR 1.16, 95% CI 0.63–2.14), *TP53* alteration, age, sex and histology
were not independently associated with survival.

### 3.3 The genomic landscape is shared between the groups

The most frequently altered genes across the cohort were *TP53* (57.8%), *KRAS* (37.9%),
*CDKN2A* (34.5%), *STK11* (21.6%) and *EGFR* (16.4%). The alteration landscape of the two
groups is shown in **Figure 2**, with both groups placed in one matrix under a single gene
ordering so that columns can be compared directly. Comparing sBM with mBM, 42 recurrent
alterations (gene and alteration type, each observed in ≥5 patients) were tested. **None
was significantly different after Benjamini–Hochberg correction** (**Table 2**). The
smallest adjusted value was q = 0.17, for *MYC* amplification (5.7% sBM vs 25.0% mBM, raw
p = 0.008).

Co-alteration patterns were likewise not significantly different. *TP53*/*EGFR*
co-alteration occurred in 14.8% of sBM and 3.6% of mBM (p = 0.18), and *TP53*/*KRAS* in
17.0% and 10.7% (p = 0.56).

### 3.4 9p21.3 co-deletion

Co-deletion of *CDKN2A*, *CDKN2B* and *MTAP* at 9p21.3 was the most frequent complex
alteration in the cohort, in 18/116 patients (15.5%, 95% CI 9.5–23.4): 12/88 sBM (13.6%)
and 6/28 mBM (21.4%; p = 0.37). All 18 *MTAP* losses co-occurred with both *CDKN2A* and
*CDKN2B* loss (18/18), consistent with a single contiguous deletion event rather than
independent gene-level calls. This is visible directly in **Figure 2**, where the three
9p21.3 rows are drawn adjacently and their deletions align into vertical blocks in both
groups.

Co-deletion was not associated with survival, on either clock: HR 0.94 (95% CI 0.52–1.70,
p = 0.85) from primary diagnosis and HR 1.17 (95% CI 0.65–2.10, p = 0.61) from BM
diagnosis.

### 3.5 9p21.3 co-deletion is not enriched relative to unselected NSCLC

Against the reference cohort of 29,379 NSCLC cases profiled by comparable hybrid-capture
CGP (background rate 13.4%, 3,928/29,379), the present cohort showed no enrichment: 15.5%
versus 13.4%, OR 1.19, p = 0.49.

For contrast, benchmarking the same figure against an unrestricted AACR Project GENIE NSCLC
denominator (5.7%, 126/2,229) would have indicated a three-fold enrichment (OR 3.07,
p < 0.001). As set out in §2.4, that difference reflects gene-panel coverage rather than
tumour biology, and illustrates that the choice of external reference determines the
conclusion.

With n = 116, this cohort has 87% power to detect a true rate of 24% against a 13.4%
background, but only 55% power against a true rate of 20%. The result excludes a
near-doubling of the background rate; it does not exclude modest enrichment.

### 3.6 Comparator-arm analyses **[TO COMPLETE]**

**[Insert once §2.2 is assembled: (i) 9p21.3 and alteration frequencies in BM versus BM-free
NSCLC with BH-adjusted q-values; (ii) Fine–Gray cumulative incidence of BM with death as a
competing event, overall and by 9p21.3 status; (iii) time-dependent Cox model with BM as a
time-varying covariate.]**

---

## 4. Discussion

The principal finding is methodological in origin and clinical in consequence. In this
cohort, the conventional survival comparison between synchronous and metachronous brain
metastases is not merely underpowered — it points in the wrong direction. Anchored to
primary diagnosis, metachronous patients appear to fare no worse. Anchored to
brain-metastasis diagnosis, they carry approximately three times the hazard of death.

The mechanism is straightforward. Survival measured from primary diagnosis credits the
metachronous group with the entire interval preceding BM onset — a median of 347 days here
— during which those patients were, by definition, alive. That interval is structurally
unavailable to the synchronous group. The comparison is therefore not between two groups of
patients but between two differently defined durations.

The clinical reading is that a brain metastasis appearing after treatment has begun is a
different event from one present at diagnosis. Metachronous BM arises in disease that has
already been exposed to systemic therapy and has escaped it; synchronous BM occurs in a
treatment-naive patient who then receives full first-line therapy, increasingly including
agents with meaningful CNS activity. The observed post-BM survival gap is consistent with
that interpretation, though this cohort cannot separate the contributions of acquired
resistance, differential access to CNS-active systemic therapy, and local CNS treatment
(§5).

Against this, the genomic findings are notable for their flatness. No recurrent alteration
distinguished the groups after correction for multiple testing, and co-alteration patterns
were similar. Taken with the survival result, this supports a model in which
brain-metastatic competence is established at or before primary diagnosis and is shared
across both presentations, while the *timing* of clinical BM onset is governed by
treatment, surveillance intensity and host factors rather than by a distinct metastatic
genotype. This is a negative result, and it is reported as one; the cohort is not powered
to exclude modest differences, and the direction of the *MYC* amplification signal
(q = 0.17) may warrant testing in a larger series.

The 9p21.3 result requires care in interpretation. Co-deletion of *CDKN2A*, *CDKN2B* and
*MTAP* was the most frequent complex alteration in both groups, which invites the inference
that it marks brain-metastatic potential. That inference does not survive external
comparison: at 15.5%, the rate is indistinguishable from the 13.4% reported in unselected
NSCLC profiled on comparable assays. The three genes are contiguous on 9p21.3 and are
deleted together by a single event, so a co-deletion involving them will be the leading
"multi-gene co-alteration" in any panel-sequenced cohort. Frequency alone is not evidence
of enrichment.

The therapeutic implication is unaffected by this, because it never depended on enrichment.
*MTAP*-deleted tumours are selectively vulnerable to PRMT5 and MAT2A inhibition, and agents
exploiting this synthetic lethality are in clinical development. That roughly one in six
patients in this brain-metastatic cohort carries the deletion, detected on a panel already
in routine clinical use, identifies a therapeutically addressable subgroup in a population
with limited options — independently of whether the alteration is enriched relative to
NSCLC at large.

---

## 5. Limitations

This is a retrospective, single-centre analysis, and the following constraints apply.

**No brain-metastasis-free comparator.** Every patient in the primary cohort has brain
metastases. Enrichment testing, competing-risks modelling of time to BM, and time-dependent
modelling of BM status all require the comparator arm specified in §2.2. Until it is
included, no statement about BM *risk* is supportable from these data. **[Resolved once
§2.2 is added.]**

**CNS-directed therapy is not captured.** Stereotactic radiosurgery, whole-brain
radiotherapy and neurosurgical resection differ systematically between synchronous and
metachronous presentations and are strong confounders of post-BM survival. The treatment
fields available in this dataset record that radiotherapy (60.2% sBM vs 60.7% mBM, p = 1.00)
or surgery (4.5% vs 10.7%, p = 0.36) was given, but never the irradiated site or the
operated organ, so CNS-directed treatment cannot be distinguished from thoracic treatment.
The radiotherapy term in Table 3 should therefore not be read as a treatment effect.
**[TO COMPLETE: abstract CNS-directed therapy from the clinical record as discrete
variables — SRS, WBRT, neurosurgical resection, each with date — and refit Table 3.]**

**Differential missingness.** ECOG performance status, stage, smoking status, numeric PD-L1
and numeric TMB are missing for 44 patients, and the missingness is unbalanced between
groups (38/88, 43% of sBM versus 6/28, 21% of mBM). Comparisons of these variables are
confounded by which patients happened to be annotated, and they were therefore not entered
into the multivariable model. **[TO COMPLETE: retrieve the missing annotation, or report
complete-case n per variable and use multiple imputation.]**

**Limited power.** With 28 metachronous patients and 89 events, the study can reliably
detect hazard ratios of approximately 1.8 and above, and enrichment of a 13%-prevalence
alteration only to about 24%. Negative genomic findings are reported as non-significant,
not as evidence of equivalence.

**Survival data structure.** Overall survival is recorded as a single duration without an
explicit unit, death date or censoring indicator (§2.5).

**Cohort composition.** Registry histology coding was discordant with the clinical NSCLC
diagnosis in a minority of cases and was reclassified. A sensitivity analysis excluding
those cases (n = 109) gave an unchanged survival result (p < 0.001).

---

## 6. Conclusion

In NSCLC with brain metastases, the apparent survival advantage of metachronous disease is
an artifact of measuring survival from primary diagnosis. Measured from brain-metastasis
diagnosis, metachronous BM carries approximately three times the hazard of synchronous BM.
The genomic landscape of the two groups is shared, including co-deletion at 9p21.3, which
occurs at the same frequency as in unselected NSCLC and is not prognostic. These
observations support a model in which brain-metastatic competence is established early and
shared, while BM timing reflects treatment and surveillance rather than a distinct
metastatic genotype. Studies comparing synchronous and metachronous brain metastases should
report survival from the metastatic event, not only from primary diagnosis.

---

## Figures and Tables

**Figure 1.** Overall survival in synchronous and metachronous brain metastases under two
time origins. (A) From primary lung cancer diagnosis; (B) from brain-metastasis diagnosis.
Kaplan–Meier estimates with censoring marks and numbers at risk. The same 116 patients and
89 deaths underlie both panels; the synchronous curve is near-identical between them
because time to BM is close to zero in that group, so the entire difference arises from the
metachronous group. Curves are shown over the full observation period (to 129 months);
fewer than five patients per group remain at risk beyond 48 months, and no metachronous
patient remains at risk beyond 48 months in panel B.
→ `figures/figure1_survival_both_clocks.pdf`

**Figure 2.** Oncoplot of the 20 most frequently altered genes, synchronous beside
metachronous brain metastases. Each column is one patient, ordered within group by
alteration pattern; each row is one gene, ordered by cohort-wide frequency except that the
three 9p21.3 genes are held adjacent because they are contiguous on the chromosome and lost
in a single event. Copy-number events fill the whole cell and short variants are drawn as an
inset bar, so alteration class is carried by geometry as well as colour. The bar above shows
the number of altered genes per patient; percentages at right are within-group frequencies.
No alteration differed significantly between groups after Benjamini–Hochberg correction
(Table 2).
→ `figures/figure2_oncoplot.pdf`

**Figure S1.** CONSORT-style patient flow diagram. **[TO COMPLETE]**

**Table 1.** Baseline characteristics by group. → from `20260719table.pdf`, to be reformatted
with complete-case denominators per variable.

**Table 2.** Recurrent genomic alterations, sBM versus mBM, with BH-adjusted q-values.
→ `analysis/01_coalterations.py`

**Table 3.** Multivariable Cox model for overall survival from brain-metastasis diagnosis.
→ `analysis/05_abstract_statistics.py`

---

## Table 2 (draft)

Recurrent alterations observed in ≥5 patients; 42 tested, none significant after
Benjamini–Hochberg correction. Ten smallest raw p-values shown.

| Alteration | sBM (n=88) | mBM (n=28) | OR | p | q (BH) |
| --- | --- | --- | --- | --- | --- |
| *MYC* amplification | 5 (5.7%) | 7 (25.0%) | 0.18 | 0.008 | 0.17 |
| *FGFR1* amplification | 1 (1.1%) | 4 (14.3%) | 0.07 | 0.012 | 0.17 |
| *NSD3* amplification | 1 (1.1%) | 4 (14.3%) | 0.07 | 0.012 | 0.17 |
| *STK11* stop gained | 3 (3.4%) | 4 (14.3%) | 0.21 | 0.057 | 0.42 |
| *FGF3* amplification | 2 (2.3%) | 3 (10.7%) | 0.19 | 0.090 | 0.42 |
| *FGF4* amplification | 2 (2.3%) | 3 (10.7%) | 0.19 | 0.090 | 0.42 |
| *FGF19* amplification | 2 (2.3%) | 3 (10.7%) | 0.19 | 0.090 | 0.42 |
| *DNMT3A* missense | 2 (2.3%) | 3 (10.7%) | 0.19 | 0.090 | 0.42 |
| *CCND1* amplification | 2 (2.3%) | 3 (10.7%) | 0.19 | 0.090 | 0.42 |
| *NKX2-1* amplification | 9 (10.2%) | 0 (0.0%) | — | 0.111 | 0.47 |

Gene-level frequencies (any alteration type):

| Gene | sBM (n=88) | mBM (n=28) | p |
| --- | --- | --- | --- |
| *TP53* | 53 (60.2%) | 14 (50.0%) | 0.38 |
| *KRAS* | 33 (37.5%) | 11 (39.3%) | 1.00 |
| *CDKN2A* | 29 (33.0%) | 11 (39.3%) | 0.65 |
| *STK11* | 18 (20.5%) | 7 (25.0%) | 0.61 |
| *EGFR* | 17 (19.3%) | 2 (7.1%) | 0.15 |
| *CDKN2B* | 17 (19.3%) | 6 (21.4%) | 0.79 |
| *MTAP* | 12 (13.6%) | 6 (21.4%) | 0.37 |
| *MET* | 10 (11.4%) | 0 (0.0%) | 0.12 |
| *MYC* | 5 (5.7%) | 7 (25.0%) | 0.01 |

## Table 3 (draft)

Multivariable Cox model, overall survival from brain-metastasis diagnosis (n = 116,
89 events).

| Covariate | HR | 95% CI | p |
| --- | --- | --- | --- |
| Metachronous BM | 3.02 | 1.83–5.00 | <0.001 |
| Radiotherapy (site unspecified) | 2.04 | 1.27–3.28 | 0.003 |
| *TP53* alteration | 1.34 | 0.86–2.08 | 0.19 |
| 9p21.3 co-deletion | 1.16 | 0.63–2.14 | 0.64 |
| Age (per year) | 1.02 | 1.00–1.05 | 0.10 |
| Adenocarcinoma | 1.03 | 0.57–1.86 | 0.93 |
| Male sex | 0.97 | 0.62–1.51 | 0.88 |

---

## Reporting checklists

REMARK (prognostic biomarker studies) and STROBE (observational studies) both apply.
**[TO COMPLETE: complete both and submit as supplementary files.]**

## Author contributions, funding, conflicts, data availability

**[TO COMPLETE]**
