"""
External replication of the 9p21.3 co-deletion frequency.

Two independent routes to a background rate in unselected NSCLC:

  A. Published rates, hard-coded below with their denominators. Runs anywhere.
  B. A live query against the cBioPortal public API (TCGA-LUAD/LUSC and AACR
     Project GENIE). Requires outbound access to www.cbioportal.org, which is
     blocked inside the Claude Code sandbox this was written in -- run it on an
     unrestricted network.

Route B is the one to cite in the paper; route A is what could be computed here.

    export COHORT_XLSX=/secure/path/20260719cohort.xlsx
    python analysis/06_external_background_rate.py            # published rates
    python analysis/06_external_background_rate.py --live     # + cBioPortal
"""
import os, sys, json, warnings
import numpy as np, pandas as pd
warnings.filterwarnings('ignore')
from scipy.stats import binomtest, fisher_exact
from statsmodels.stats.proportion import proportion_confint

ENTREZ = {'CDKN2A': 1029, 'CDKN2B': 1030, 'MTAP': 4507}
API = 'https://www.cbioportal.org/api'

# Oncotree codes counted as NSCLC when filtering the GENIE pan-cancer study.
NSCLC_ONCOTREE = {'LUAD', 'LUSC', 'NSCLC', 'LCLC', 'NSCLCPD', 'LUAS', 'ASC',
                  'LUPC', 'SARCL', 'LUACC', 'LUMEC', 'CMPT'}

# ---------------------------------------------------------------- cohort ----

def cohort_rates():
    df = pd.read_excel(os.environ.get('COHORT_XLSX', 'data/20260719cohort.xlsx'))
    pv = 'Pathogenic variants (list)'
    df['mBM'] = (df.group == 'verl-mBM').astype(int)

    def losses(s):
        out = set()
        for item in str(s).split(';'):
            item = item.strip()
            parts = item.split(' ', 1)
            if len(parts) > 1 and parts[1].strip() in ('loss', 'deletion'):
                out.add(parts[0])
        return out

    loss = df[pv].apply(losses)
    df['mtap'] = loss.apply(lambda s: 'MTAP' in s).astype(int)
    df['triple'] = loss.apply(lambda s: set(ENTREZ) <= s).astype(int)
    return df


def show(label, k, n):
    lo, hi = proportion_confint(k, n, method='beta')
    print(f"  {label:34s} {k:5d}/{n:<6d} = {100*k/n:5.2f}%  (95% CI {100*lo:.1f}-{100*hi:.1f})")

# ------------------------------------------------------- published rates ----

# (label, events, total, what was counted, assay)
PUBLISHED = [
    ("Kumar 2023, Cancer Medicine", 3928, 29379, "MTAP loss in NSCLC",
     "hybrid-capture CGP -- closest match to FoundationOne"),
    ("AACR Project GENIE, NSCLC", 126, 2229, "MTAP two-copy deletion",
     "mixed panels; many do not tile MTAP -- undercounts"),
]

# Reported without a usable denominator; context only, not tested against.
ANCHORS = [
    ("TCGA-LUAD CDKN2A/B homozygous deletion", "19.1% (n=517)", "SNP-array GISTIC"),
    ("TCGA-LUAD CDKN2A homozygous deletion", "12.5%", "SNP-array GISTIC"),
    ("C-CAT lung cancer MTAP deletion", "14.3%", "panel CGP"),
]

# ------------------------------------------------------------ cBioPortal ----

def _post(path, payload, params=None):
    import requests
    r = requests.post(f"{API}{path}", json=payload, params=params or {},
                      headers={'Accept': 'application/json'}, timeout=180)
    r.raise_for_status()
    return r.json()


def _get(path, params=None):
    import requests
    r = requests.get(f"{API}{path}", params=params or {},
                     headers={'Accept': 'application/json'}, timeout=180)
    r.raise_for_status()
    return r.json()


def profiled_samples(profile_id, sample_list_id):
    """Samples whose gene panel covers all three 9p21.3 genes.

    Panel-based studies only call a deletion where the panel tiles the gene, so
    samples on a panel missing MTAP must leave the denominator -- otherwise the
    background rate is diluted and the cohort looks falsely enriched.
    """
    data = _post(f"/molecular-profiles/{profile_id}/gene-panel-data/fetch",
                 {'sampleListId': sample_list_id})
    panels = {d.get('genePanelId') for d in data if d.get('profiled')}
    covering = set()
    for panel_id in filter(None, panels):
        genes = {g['hugoGeneSymbol'] for g in _get(f"/gene-panels/{panel_id}").get('genes', [])}
        if set(ENTREZ) <= genes:
            covering.add(panel_id)
    keep = {d['sampleId'] for d in data
            if d.get('profiled') and (d.get('genePanelId') in covering
                                      or d.get('genePanelId') is None)}
    whole_exome = all(d.get('genePanelId') is None for d in data)
    return keep, whole_exome


def query_study(study_id, sample_list_id=None, profile_id=None, oncotree_filter=False):
    profile_id = profile_id or f"{study_id}_gistic"
    sample_list_id = sample_list_id or f"{study_id}_cna"

    keep, whole_exome = profiled_samples(profile_id, sample_list_id)
    if whole_exome:
        keep = None  # every sample is assayed for every gene

    if oncotree_filter:
        clin = _post(f"/studies/{study_id}/clinical-data/fetch",
                     {'attributeIds': ['ONCOTREE_CODE'], 'ids': []},
                     {'clinicalDataType': 'SAMPLE'})
        nsclc = {c['sampleId'] for c in clin if c.get('value') in NSCLC_ONCOTREE}
        keep = nsclc if keep is None else (keep & nsclc)

    cna = _post(f"/molecular-profiles/{profile_id}/discrete-copy-number/fetch",
                {'sampleListId': sample_list_id,
                 'entrezGeneIds': list(ENTREZ.values())},
                {'discreteCopyNumberEventType': 'HOMDELETED', 'projection': 'SUMMARY'})

    homdel = {}
    for rec in cna:
        sid = rec['sampleId']
        if keep is not None and sid not in keep:
            continue
        homdel.setdefault(sid, set()).add(rec['hugoGeneSymbol'])

    if keep is None:
        all_ids = {d['sampleId'] for d in
                   _post(f"/molecular-profiles/{profile_id}/gene-panel-data/fetch",
                         {'sampleListId': sample_list_id}) if d.get('profiled')}
    else:
        all_ids = keep

    n = len(all_ids)
    mtap = sum('MTAP' in v for v in homdel.values())
    triple = sum(set(ENTREZ) <= v for v in homdel.values())
    return n, mtap, triple

# ------------------------------------------------------------------ main ----

def main():
    df = cohort_rates()
    n = len(df)
    k_mtap, k_trip = int(df.mtap.sum()), int(df.triple.sum())

    print("=" * 78)
    print("COHORT")
    print("=" * 78)
    show("MTAP loss", k_mtap, n)
    show("9p21.3 triple co-deletion", k_trip, n)
    print(f"  every MTAP loss co-occurred with CDKN2A + CDKN2B loss: "
          f"{int((df.mtap & df.triple).sum())}/{k_mtap}")
    for g, lab in [(0, 'sBM'), (1, 'mBM')]:
        s = df[df.mBM == g]
        show(f"  triple co-deletion, {lab}", int(s.triple.sum()), len(s))

    print("\n" + "=" * 78)
    print("VS PUBLISHED BACKGROUND RATES IN UNSELECTED NSCLC")
    print("=" * 78)
    for label, a, b, what, note in PUBLISHED:
        p0 = a / b
        bt = binomtest(k_mtap, n, p0)
        orr, pf = fisher_exact([[k_mtap, n - k_mtap], [a, b - a]])
        print(f"\n  {label}  --  {what}")
        print(f"    {note}")
        print(f"    background {a}/{b} = {100*p0:.2f}%   cohort {k_mtap}/{n} = {100*k_mtap/n:.2f}%")
        print(f"    OR {orr:.2f}   Fisher p={pf:.3g}   exact binomial p={bt.pvalue:.3g}")

    print("\n  Context only (different assay or definition, not tested):")
    for label, pct, assay in ANCHORS:
        print(f"    {label:42s} {pct:16s} [{assay}]")

    print("\n" + "=" * 78)
    print(f"DETECTABLE ENRICHMENT (vs 13.4 pct, alpha=0.05, n={n})")
    print("=" * 78)
    from scipy.stats import norm
    p0 = 3928 / 29379
    for p1 in (0.20, 0.24, 0.25, 0.30):
        se0, se1 = np.sqrt(p0 * (1 - p0) / n), np.sqrt(p1 * (1 - p1) / n)
        power = norm.cdf((abs(p1 - p0) - 1.96 * se0) / se1)
        print(f"    if the true rate were {100*p1:.0f}%  ->  power {100*power:.0f}%")

    if '--live' in sys.argv:
        print("\n" + "=" * 78)
        print("LIVE cBIOPORTAL QUERY")
        print("=" * 78)
        for study, oncotree in [('luad_tcga_pan_can_atlas_2018', False),
                                ('lusc_tcga_pan_can_atlas_2018', False),
                                ('genie_public', True)]:
            try:
                n_s, mtap_s, trip_s = query_study(study, oncotree_filter=oncotree)
                print(f"\n  {study}")
                show("MTAP homozygous deletion", mtap_s, n_s)
                show("9p21.3 triple co-deletion", trip_s, n_s)
                orr, pf = fisher_exact([[k_trip, n - k_trip], [trip_s, n_s - trip_s]])
                print(f"    cohort vs this study: OR {orr:.2f}, Fisher p={pf:.3g}")
            except Exception as exc:
                print(f"\n  {study}: query failed -- {exc}")


if __name__ == '__main__':
    main()
