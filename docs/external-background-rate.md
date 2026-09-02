# External replication of the 9p21.3 co-deletion frequency

## Question

Does 15.5% 9p21.3 co-deletion in this brain-metastasis cohort represent enrichment
relative to unselected NSCLC, or is it the background rate?

## Answer

It is the background rate. Against the closest like-for-like comparator — 29,379 advanced
NSCLC cases profiled by hybrid-capture comprehensive genomic profiling, the same assay
class as FoundationOne — the cohort shows no enrichment.

| Comparator | Background | Cohort | OR | p |
| --- | --- | --- | --- | --- |
| Kumar 2023, *Cancer Medicine* (hybrid-capture CGP, NSCLC) | 3,928/29,379 = 13.4% | 18/116 = 15.5% | 1.19 | 0.49 |
| AACR Project GENIE, NSCLC (mixed panels) | 126/2,229 = 5.7% | 18/116 = 15.5% | 3.07 | 0.00017 |

Context anchors, not directly comparable (different assay or event definition):
TCGA-LUAD CDKN2A/B homozygous deletion 19.1% (n=517); TCGA-LUAD CDKN2A homozygous deletion
12.5%; C-CAT lung cancer MTAP deletion 14.3%.

## The comparator choice decides the conclusion

The two rows above disagree by three-fold, and only the first is defensible. GENIE
aggregates many sequencing panels, a large share of which either do not tile MTAP or call
two-copy deletions conservatively; samples not assayed for the gene still sit in the
denominator, so the reported rate is diluted. Benchmarking a FoundationOne cohort against
that number would manufacture an apparent three-fold enrichment out of assay coverage
alone.

If GENIE is used at all, the denominator must be restricted to samples whose panel covers
all three genes. `analysis/06_external_background_rate.py --live` does this via the
cBioPortal gene-panel endpoint.

## Power

Against a 13.4% background, n = 116 gives:

| If the true rate were | Power to detect it |
| --- | --- |
| 20% | 55% |
| 24% | 87% |
| 25% | 91% |
| 30% | 99% |

The cohort can exclude a near-doubling of the background rate, but not a modest (~1.5×)
enrichment. State this explicitly rather than reporting the null as proof of no effect.

## Internal consistency

All 18 MTAP losses co-occurred with both CDKN2A and CDKN2B loss (18/18), consistent with a
single contiguous deletion event at 9p21.3 rather than independent gene-level calls. This
supports treating the three genes as one locus, and is worth reporting as a quality check.

## What this changes in the paper

The "biomarker of BM risk" framing is now positively excluded rather than merely
unsupported: the alteration occurs in brain-metastatic NSCLC at the same rate as in
unselected NSCLC. This strengthens the secondary hypothesis — a shared genomic landscape
in which brain-metastatic competence is not marked by 9p21.3 — and leaves the therapeutic
argument (MTAP loss; PRMT5/MAT2A inhibition) untouched, since that never depended on
enrichment.

## Caveats

Published rates were retrieved from the literature rather than by direct query, because the
analysis environment's network policy blocked cBioPortal, the GDC and PubMed. Before
submission, verify the Kumar 2023 denominator against the primary source and run
`analysis/06_external_background_rate.py --live` on an unrestricted network to obtain a
directly computed TCGA and GENIE rate.

## Sources

- Ashok Kumar et al., *Genomic landscape of non-small-cell lung cancer with
  methylthioadenosine phosphorylase (MTAP) deficiency*, Cancer Medicine 2023.
  https://onlinelibrary.wiley.com/doi/full/10.1002/cam4.4971
- AACR Project GENIE, via https://www.cbioportal.org
- *Deletions on 9p21 are associated with worse outcomes after anti-PD-1/PD-L1 monotherapy
  but not chemoimmunotherapy*, npj Precision Oncology 2022.
  https://www.nature.com/articles/s41698-022-00286-4
- *Co-occurrence of CDKN2A/B and IFN-I homozygous deletions ... in lung adenocarcinoma*,
  Molecular Oncology 2022. https://pubmed.ncbi.nlm.nih.gov/35253368/
