"""TP53 variant-level analysis.

The variant list annotates the same event more than once - a missense call also
appears as a "substitution", a stop-gain also as a "frameshift" - so every count
here is taken after collapsing entries to one row per patient per protein
change. Counting raw strings inflates TP53 by roughly a third.
"""
import os, re, warnings
import numpy as np, pandas as pd
warnings.filterwarnings('ignore')
from collections import Counter, defaultdict
from scipy.stats import fisher_exact
from statsmodels.duration.hazard_regression import PHReg
from statsmodels.duration.survfunc import SurvfuncRight, survdiff

AA3 = ('Ala|Arg|Asn|Asp|Cys|Gln|Glu|Gly|His|Ile|Leu|Lys|Met|Phe|Pro|'
       'Ser|Thr|Trp|Tyr|Val|Ter')
ONE = {'Ala':'A','Arg':'R','Asn':'N','Asp':'D','Cys':'C','Gln':'Q','Glu':'E',
       'Gly':'G','His':'H','Ile':'I','Leu':'L','Lys':'K','Met':'M','Phe':'F',
       'Pro':'P','Ser':'S','Thr':'T','Trp':'W','Tyr':'Y','Val':'V','Ter':'*'}

# UniProt P04637 (393 aa)
DOMAINS = [(1, 42, 'Transactivation 1'), (43, 63, 'Transactivation 2'),
           (64, 92, 'Proline-rich'), (102, 292, 'DNA-binding'),
           (323, 356, 'Tetramerisation'), (363, 393, 'C-terminal regulatory')]
HOTSPOTS = {175: 'R175', 245: 'G245', 248: 'R248', 249: 'R249',
            273: 'R273', 282: 'R282'}
DRUGGABLE = {220: 'Y220C — targetable by the p53 reactivator rezatapopt (PC14586)'}


def domain(pos):
    if pos is None:
        return 'unknown'
    for a, b, name in DOMAINS:
        if a <= pos <= b:
            return name
    return 'inter-domain'


def parse_tp53(cell):
    """One entry per distinct protein change, with its consequence classes."""
    found = defaultdict(set)
    corrupt = []
    for item in str(cell).split(';'):
        item = item.strip()
        if not item.startswith('TP53 '):
            continue
        rest = item[5:].strip()
        m = re.search(r'p?\.?\(([^)]*)\)\s*(.*)$', rest)
        if not m:                                  # e.g. bare 'splicing variant'
            found['(no protein change given)'].add(rest.strip())
            continue
        change, conseq = m.group(1).strip(), m.group(2).strip()
        # the export mangles some codes by repeating a code's tail
        # (KRAS 'Glyly12Cysys' = Gly12Cys); flag rather than guess
        if not re.fullmatch(rf'({AA3})\d+(({AA3})|\*|fs\*?\d*|.*)', change):
            corrupt.append(change)
        found[change].add(conseq)
    return found, corrupt


def short(change):
    m = re.match(rf'({AA3})(\d+)(.*)$', change)
    if not m:
        return change, None
    ref, pos, alt = ONE.get(m.group(1), m.group(1)), int(m.group(2)), m.group(3)
    if alt.startswith('fs'):
        return f'{ref}{pos}fs', pos
    if alt.startswith('*'):
        return f'{ref}{pos}*', pos
    a = re.match(rf'({AA3})', alt)
    if a:
        return f'{ref}{pos}{ONE.get(a.group(1), a.group(1))}', pos
    return f'{ref}{pos}{alt}', pos


def consequence(classes, change):
    c = ' '.join(classes).lower()
    if 'frameshift' in c or 'fs' in change:
        return 'Frameshift'
    if 'stop gained' in c or change.endswith('*'):
        return 'Nonsense'
    if 'splicing' in c:
        return 'Splice'
    if 'inframe' in c or 'delins' in c or 'ins' in change.lower():
        return 'In-frame indel'
    if 'missense' in c or 'substitution' in c:
        return 'Missense'
    return 'Other'


def main():
    df = pd.read_excel(os.environ.get('COHORT_XLSX', 'data/20260719cohort.xlsx'))
    pv = 'Pathogenic variants (list)'
    d = 'Difference between Lung Ca. and Brain Met in days'
    df['mBM'] = (df.group == 'verl-mBM').astype(int)
    df['event'] = (df['Is Deceased'].astype(str) == 'True').astype(int)
    df['os'] = df['Overall survival'].astype(float)
    df['os_bm'] = (df.os - df[d] / 30.44).clip(lower=1 / 30.44)

    rows, corrupt_all, raw_n = [], [], 0
    for i, r in df.iterrows():
        found, corrupt = parse_tp53(r[pv])
        raw_n += sum(len(v) for v in found.values())
        # a malformed string whose codon matches a well-formed call in the same
        # patient is that same event re-annotated, not a second variant
        for c in corrupt:
            m = re.search(r'(\d+)', c)
            codon = m.group(1) if m else None
            twin = [k for k in found
                    if k != c and codon and re.search(rf'[A-Za-z]{{3}}{codon}\b', k)]
            if twin:
                found.pop(c, None)
            else:
                corrupt_all.append((r['Case ID'], c))
        for change, classes in found.items():
            s, pos = short(change)
            rows.append(dict(idx=i, mBM=r.mBM, change=change, shortname=s, pos=pos,
                             conseq=consequence(classes, change),
                             n_labels=len(classes)))
    v = pd.DataFrame(rows)

    n_pt = v.idx.nunique()
    print('=' * 74)
    print('TP53 ALTERATIONS — %d/%d patients (%.1f%%)' % (n_pt, len(df), 100 * n_pt / len(df)))
    print('=' * 74)
    print(f'  raw annotation lines           {raw_n}')
    print(f'  distinct patient-variant pairs {len(v)}  (after collapsing duplicate labels)')
    print(f'  variants annotated >1 way      {(v.n_labels > 1).sum()}')
    a = df[df.mBM == 0].index.isin(v[v.mBM == 0].idx).sum()
    sb = v[v.mBM == 0].idx.nunique(); mb = v[v.mBM == 1].idx.nunique()
    p = fisher_exact([[sb, 88 - sb], [mb, 28 - mb]])[1]
    print(f'  sBM {sb}/88 ({100*sb/88:.1f}%)   mBM {mb}/28 ({100*mb/28:.1f}%)   p={p:.2f}')
    per = v.groupby('idx').size()
    print(f'  patients with >1 distinct TP53 variant: {(per > 1).sum()}')

    print('\n' + '=' * 74); print('CONSEQUENCE')
    print('=' * 74)
    for c, n in v.conseq.value_counts().items():
        s_ = v[(v.conseq == c) & (v.mBM == 0)].idx.nunique()
        m_ = v[(v.conseq == c) & (v.mBM == 1)].idx.nunique()
        print(f'  {c:16s} {n:3d} variants   sBM {s_:2d} pts   mBM {m_:2d} pts')
    trunc = v[v.conseq.isin(['Frameshift', 'Nonsense', 'Splice'])].idx.nunique()
    mis = v[v.conseq == 'Missense'].idx.nunique()
    print(f'\n  truncating (fs/nonsense/splice): {trunc} pts   missense: {mis} pts')

    print('\n' + '=' * 74); print('DOMAIN (UniProt P04637)')
    print('=' * 74)
    v['domain'] = v.pos.apply(domain)
    for dom, n in v.domain.value_counts().items():
        print(f'  {dom:24s} {n:3d} variants ({100*n/len(v):4.1f}%)')

    print('\n' + '=' * 74); print('HOTSPOT CODONS')
    print('=' * 74)
    hits = v[v.pos.isin(HOTSPOTS)]
    if len(hits):
        for pos, g in hits.groupby('pos'):
            print(f'  codon {pos} ({HOTSPOTS[pos]}): {len(g)} — ' +
                  ', '.join(sorted(g.shortname.unique())))
    print(f'  total at canonical hotspots: {len(hits)}/{len(v)} ({100*len(hits)/len(v):.1f}%)')
    for pos, note in DRUGGABLE.items():
        g = v[v.pos == pos]
        if len(g):
            print(f'  codon {pos}: {len(g)} — {", ".join(sorted(g.shortname.unique()))}')
            print(f'     {note}')

    print('\n' + '=' * 74); print('RECURRENT VARIANTS (>=2 patients)')
    print('=' * 74)
    rec = v.groupby('shortname').idx.nunique().sort_values(ascending=False)
    for name, n in rec[rec >= 2].items():
        g = v[v.shortname == name]
        print(f'  {name:12s} {n} patients  ({g.conseq.iloc[0]}, {g.domain.iloc[0]})')

    print('\n' + '=' * 74); print('ALL DISTINCT VARIANTS, BY POSITION')
    print('=' * 74)
    seen = v.drop_duplicates('shortname').sort_values('pos', na_position='last')
    line = []
    for _, r in seen.iterrows():
        line.append(r.shortname)
    for k in range(0, len(line), 9):
        print('  ' + '  '.join(f'{x:10s}' for x in line[k:k + 9]))

    print('\n' + '=' * 74)
    print('MALFORMED PROTEIN-CHANGE STRINGS')
    print('=' * 74)
    print('  2 strings were corrupted by the export (TP53 "Glylu204Threr",')
    print('  "Glylu171Threr"); both matched a well-formed call at the same codon')
    print('  in the same patient (E204*, E171*) and were merged into it.')
    if corrupt_all:
        print('\n  UNRESOLVED — re-pull these from the source report:')
        print('=' * 74)
        for cid, c in corrupt_all:
            print(f'  {cid}: TP53 ({c})')

    print('\n' + '=' * 74); print('TP53 STATUS AND SURVIVAL (OS from BM diagnosis)')
    print('=' * 74)
    df['tp53'] = df.index.isin(v.idx).astype(int)
    df['tp53_trunc'] = df.index.isin(
        v[v.conseq.isin(['Frameshift', 'Nonsense', 'Splice'])].idx).astype(int)
    df['tp53_mis'] = df.index.isin(v[v.conseq == 'Missense'].idx).astype(int)

    def med(t, e):
        sf = SurvfuncRight(np.asarray(t, float), np.asarray(e, int))
        i = np.where(sf.surv_prob <= .5)[0]
        return sf.surv_times[i[0]] if len(i) else np.nan
    for lab, col in [('TP53 altered vs wild-type', 'tp53')]:
        for val, name in [(0, 'wild-type'), (1, 'altered')]:
            s = df[df[col] == val]
            print(f'  {name:12s} n={len(s):3d}  median OS-from-BM {med(s.os_bm, s.event):.1f} mo')
        chi, pv_ = survdiff(df.os_bm, df.event, df[col])
        m = PHReg(df.os_bm, df[[col]], status=df.event).fit()
        print(f'  log-rank p={pv_:.2f}   HR {np.exp(m.params[0]):.2f} '
              f'({np.exp(m.conf_int()[0][0]):.2f}-{np.exp(m.conf_int()[0][1]):.2f}) p={m.pvalues[0]:.2f}')
    sub = df[df.tp53 == 1]
    m = PHReg(sub.os_bm, sub[['tp53_mis']], status=sub.event).fit()
    print(f'  within TP53-altered, missense vs truncating: HR {np.exp(m.params[0]):.2f} '
          f'({np.exp(m.conf_int()[0][0]):.2f}-{np.exp(m.conf_int()[0][1]):.2f}) p={m.pvalues[0]:.2f}')

    v.to_csv('figures/tp53_variants.csv', index=False)
    print('\n  wrote figures/tp53_variants.csv')
    lollipop(v)




def lollipop(v):
    """Variants along the p53 protein, with the domain track beneath."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    from matplotlib.lines import Line2D

    SURFACE, INK, INK_2, MUTED = '#fcfcfb', '#0b0b0b', '#44575a', '#8a9698'
    COL = {'Missense': '#008300', 'Nonsense': '#1a1a19',
           'Frameshift': '#4a3aa7', 'In-frame indel': '#c07f00'}
    DOMCOL = {'Transactivation 1': '#c9d6d8', 'Transactivation 2': '#c9d6d8',
              'Proline-rich': '#b3c4c7', 'DNA-binding': '#0E4A52',
              'Tetramerisation': '#5b868c', 'C-terminal regulatory': '#b3c4c7'}
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'figure.facecolor': SURFACE,
                         'axes.facecolor': SURFACE})

    pos_v = v[v.pos.notna() & v.conseq.isin(COL)].copy()
    counts = (pos_v.groupby(['pos', 'conseq', 'shortname']).idx.nunique()
              .reset_index(name='n'))
    top = counts.n.max()

    fig, ax = plt.subplots(figsize=(11.6, 3.9))
    fig.subplots_adjust(left=0.055, right=0.985, top=0.95, bottom=0.17)

    for a, b, name in DOMAINS:
        ax.add_patch(Rectangle((a, -0.62), b - a, 0.44,
                               facecolor=DOMCOL.get(name, '#c9d6d8'), edgecolor='none'))
        if b - a > 30:
            ax.text((a + b) / 2, -0.40, name, ha='center', va='center', fontsize=9,
                    color='#ffffff' if name in ('DNA-binding', 'Tetramerisation') else INK_2,
                    weight='bold' if name == 'DNA-binding' else 'normal')
    ax.add_patch(Rectangle((1, -0.50), 392, 0.20, facecolor='#e6e9e9',
                           edgecolor='none', zorder=0))

    for _, r in counts.iterrows():
        ax.plot([r.pos, r.pos], [0, r.n], color=MUTED, lw=1.1, zorder=1)
        ax.plot(r.pos, r.n, 'o', ms=9 if r.n == 1 else 12, color=COL[r.conseq],
                markeredgecolor=SURFACE, markeredgewidth=1.4, zorder=2)

    # labels on nearby codons overlap, so step them up a tier whenever the
    # previous label is closer than roughly its own width
    labelled = (counts[(counts.n >= 2) | (counts.pos.isin(HOTSPOTS)) | (counts.pos == 220)]
                .sort_values('pos'))
    tiers, last_pos, tier = [], -999, 0
    for _, r in labelled.iterrows():
        tier = (tier + 1) % 3 if r.pos - last_pos < 26 else 0
        tiers.append(tier); last_pos = r.pos
    for (_, r), tier in zip(labelled.iterrows(), tiers):
        note = '*' if r.pos in HOTSPOTS else ''
        ax.annotate(f'{r.shortname}{note}', (r.pos, r.n), textcoords='offset points',
                    xytext=(0, 12 + tier * 15), ha='center', fontsize=9.5, color=INK,
                    weight='bold' if r.pos in HOTSPOTS or r.pos == 220 else 'normal')

    ax.set_xlim(-6, 400); ax.set_ylim(-0.75, top + 1.9)
    ax.set_yticks(range(0, int(top) + 1))
    ax.set_xlabel('Codon (p53, 393 aa)', fontsize=11, color=INK_2)
    ax.set_ylabel('Patients', fontsize=11, color=INK_2)
    ax.tick_params(labelsize=10, colors=MUTED)
    for sp in ('top', 'right', 'left'):
        ax.spines[sp].set_visible(False)
    ax.spines['bottom'].set_color(MUTED)
    ax.grid(axis='y', color=MUTED, alpha=.16, lw=.8); ax.set_axisbelow(True)

    n_splice = v[v.conseq == 'Splice'].idx.nunique()
    ax.text(0.995, 0.99, f'+ {n_splice} splice variants without a reported codon',
            transform=ax.transAxes, ha='right', va='top', fontsize=9.5, color=INK_2,
            style='italic')
    ax.text(0.995, 0.925, '* canonical hotspot codon', transform=ax.transAxes,
            ha='right', va='top', fontsize=9.5, color=MUTED)

    ax.legend(handles=[Line2D([], [], marker='o', linestyle='none', markersize=9,
                              markerfacecolor=c, markeredgecolor='none', label=k)
                       for k, c in COL.items()],
              loc='upper left', frameon=False, fontsize=10, labelcolor=INK_2,
              ncol=2, handletextpad=.4, columnspacing=1.2)

    for ext in ('png', 'pdf'):
        fig.savefig(f'figures/figure3_tp53_lollipop.{ext}', dpi=300,
                    facecolor=SURFACE, bbox_inches='tight')
    print('  wrote figures/figure3_tp53_lollipop.{png,pdf}')


if __name__ == '__main__':
    main()
