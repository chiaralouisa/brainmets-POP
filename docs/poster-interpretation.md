# Interpreting the results for the ESMO 2026 poster

Notes behind `poster/esmo2026_eposter.*`. They cover what the data support, what they do
not, and what changed from the previous poster in `poster-canvas/`.

## 1. Survival: the story is "crossing curves", not "reversal"

The previous poster and manuscript say the comparison *reverses* with the time origin. The
numbers do not show a reversal. Both clocks point the same way:

| Clock | HR mBM vs sBM (95% CI) |
| --- | --- |
| From primary diagnosis | 1.18 (0.75–1.87), p = 0.47 |
| From BM diagnosis | 2.96 (1.82–4.83), p < 0.001 |

What actually happens in panel A is that the **Kaplan–Meier curves cross**. mBM runs above
sBM for roughly the first 20 months, because an mBM patient cannot die before their BM
(median 11.4 months), and then drops below. Proportional hazards are violated, so the single
HR and the log-rank test average an early "advantage" (immortal time) against later excess
mortality and come out null. The poster now says this: from primary diagnosis the effect is
*masked*, not reversed. The same wording should go into the manuscript (§3.2 heading, §4 first
paragraph, §6 "apparent survival advantage").

**What clock B measures.** Clock B does not "correct" immortal time. It answers a different
question: prognosis once BM are present. For sBM this is survival from a treatment-naive
stage IV diagnosis. For mBM it is survival after progression on therapy. A threefold hazard
is therefore expected in part from line of therapy alone. The poster frames mBM as "a
progression event in pretreated disease" rather than as a biologically distinct entity.

## 2. The 4-month landmark analysis is not valid here, and was removed from the poster

`analysis/08_immortal_time_and_covariates.py` keeps patients alive at 4 months and compares
groups from then on. mBM membership, however, is defined by a BM that happens *after* the
landmark (median 11.4 months, up to 81 months), so it is still decided by future
information. mBM patients are still guaranteed to survive from the landmark to their BM. The
landmark therefore does not remove immortal time, and the manuscript's claim that "group
membership is fixed before follow-up begins" is incorrect. Either drop the analysis, or
restrict it to a comparison that is fixed at the landmark (e.g. BM by 4 months vs not). In a
BM-only cohort that is not a sBM/mBM comparison. The valid correction remains the
time-dependent Cox model once the BM-free comparator exists.

## 3. How robust is HR ≈ 3?

- The direction is robust: adjusted HR 2.92 and the full multivariable model 3.02.
- The magnitude is not settled. In the 72 fully annotated patients the HR is 1.85
  (1.07–3.21), and annotation is missing unevenly (43% of sBM vs 21% of mBM). **No script in
  the repository reproduces the 1.85.** It appears only in the previous poster's text. Rerun
  it and add it to `analysis/` before the poster is printed.
- The radiotherapy HR of 2.04 in Table 3 is confounding by indication (site unknown). Keep it
  off the poster.

## 4. Genomics: "shared landscape" is stronger than the data allow

- None of the 42 tests survives FDR correction. But with 88 vs 28 patients, a Fisher test has
  80% power only for large differences: a 5% vs 28% difference, or a 15% vs 43% difference
  (OR ≈ 4–7), by simulation. At a Bonferroni-level α the observed *MYC* difference (5.7% vs
  25%) would be detected only 28% of the time. **"No difference detected" is supported;
  "shared landscape" is not established.**
- The top raw signals are all **focal amplifications and all higher in mBM**: *MYC* (8q24),
  *FGFR1*/*NSD3* (8p11–12, one amplicon), and *CCND1*/*FGF3*/*FGF4*/*FGF19* (11q13, one
  amplicon). The 42 tests are therefore not independent: several are the same event counted
  more than once.
- This pattern matches Shih et al. (*Nat Genet* 2020;52:371–377). There, *MYC* amplification
  was enriched in lung-adenocarcinoma brain metastases compared with primaries (12% vs 6%),
  and it promoted BM in mouse models. This is worth one sentence as hypothesis-generating.
- **Key open question: which specimen was profiled?** If mBM patients were profiled on
  post-treatment or brain tissue and sBM patients on diagnostic primaries, the amplification
  excess could be acquired or site-specific rather than a property of mBM at diagnosis. That
  would also weaken the "competence established at diagnosis" argument. Record the specimen
  site and date for each patient.

## 5. 9p21.3

- Supported: 15.5%, always one contiguous event, and not above the 13.4% rate on comparable
  CGP.
- "Not prognostic" should read **"no detectable prognostic effect"**: HR 1.17 (0.65–2.10) does
  not exclude a doubling of hazard.
- Shih et al. found *CDKN2A/B* deletion enriched in BM compared with primaries (27% vs 13%).
  That uses a different comparator and definition, so it does not contradict this result, but
  reviewers may raise it.

## 6. Items to settle before printing

1. **Title.** An ESMO poster must carry the accepted abstract title. The current title ("…
   Despite a Shared Genomic Landscape") overstates the genomic result (§4). If the accepted
   title allows it, prefer wording such as "…with No Detectable Genomic Difference". Otherwise
   keep the title and let the poster body carry the nuance, as it does now.
2. **Disclosures.** The footer has a `[TO COMPLETE]` placeholder. ESMO requires a
   conflict-of-interest disclosure.
3. **Format.** The poster is a 2560 × 1440 (16:9) landscape e-poster. A third-party summary
   gives 190 × 110 cm landscape for ESMO 2026 (about 1.73:1, close to 16:9). Confirm on the
   official "Information for Presenters" page, which could not be reached from the build
   environment.
4. **References.** Verify the Kumar et al. 2023 *Cancer Medicine* citation for the 13.4% rate.
5. **Figure fixes needing patient data** (`analysis/11_poster_figures.py`):
   - The oncoplot uses the same blue for "deletion" as for the sBM group. Recolour deletions
     (e.g. violet) or use texture.
   - The oncoplot's group labels overlapped. They are cropped out and redrawn in HTML for now.
   - The TP53 lollipop has overlapping labels (G245C, R273L). It is not on the poster.
