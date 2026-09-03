"""Figure 2: oncoplot of the 20 most frequently altered genes, sBM beside mBM.

The figure's job is the secondary hypothesis - that the two groups share a
genomic landscape - so both groups sit in one matrix under one gene ordering,
where a reader compares columns directly, rather than in two separate panels.

Encoding: copy-number events fill the whole cell, short variants are drawn as an
inset bar. Colour and geometry therefore both carry the alteration class, so the
red/green pair stays separable under deuteranopia.
"""
import os, re, warnings
import numpy as np, pandas as pd
warnings.filterwarnings('ignore')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D

SURFACE, INK, INK_2, MUTED = '#fcfcfb', '#0b0b0b', '#52514e', '#898781'
EMPTY   = '#e9e8e4'                      # no alteration
GROUP   = {'sBM': '#2a78d6', 'mBM': '#eb6834'}   # matches Figure 1
CLASS   = {'Amplification': '#e34948', 'Deletion': '#2a78d6',
           'Missense': '#008300', 'Truncating': '#1a1a19', 'Fusion': '#4a3aa7'}
CNA     = {'Amplification', 'Deletion'}   # drawn full-height; the rest are inset
N_GENES = 20

plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9,
                     'figure.facecolor': SURFACE, 'axes.facecolor': SURFACE})


def classify(rest):
    r = re.sub(r'p\.\([^)]*\)\s*', '', rest).strip().lower()
    if 'amplification' in r:                                   return 'Amplification'
    if 'loss' in r or r == 'deletion':                          return 'Deletion'
    if 'fusion' in r or 'rearrangement' in r or 'delins' in r:  return 'Fusion'
    if any(k in r for k in ('frameshift', 'stop gained', 'splicing', 'insertion')):
        return 'Truncating'
    return 'Missense'


def parse(cell):
    """{gene: {classes}} for one patient, de-duplicated."""
    out = {}
    for item in str(cell).split(';'):
        item = item.strip()
        if not item:
            continue
        parts = item.split(' ', 1)
        gene, rest = parts[0], (parts[1] if len(parts) > 1 else '')
        if gene.startswith('NKX2'):                 # 'NKX2-1' splits badly
            gene, rest = 'NKX2-1', re.sub(r'^1\s+', '', rest)
        if '-' in gene and ('fusion' in rest or 'delins' in rest):
            for g in gene.split('-'):
                out.setdefault(g, set()).add('Fusion')
            continue
        out.setdefault(gene, set()).add(classify(rest))
    return out


def main():
    df = pd.read_excel(os.environ.get('COHORT_XLSX', 'data/20260719cohort.xlsx'))
    df['mBM'] = (df.group == 'verl-mBM').astype(int)
    alt = df['Pathogenic variants (list)'].apply(parse)

    freq = {}
    for a in alt:
        for g in a:
            freq[g] = freq.get(g, 0) + 1
    genes = [g for g, _ in sorted(freq.items(), key=lambda kv: -kv[1])][:N_GENES]
    # keep the three 9p21.3 genes on adjacent rows: they are contiguous on the
    # chromosome and lost in one event, so splitting them across the frequency
    # ranking hides the co-deletion the paper is about
    locus = [g for g in ('CDKN2A', 'CDKN2B', 'MTAP') if g in genes]
    if len(locus) > 1:
        anchor = min(genes.index(g) for g in locus)
        rest = [g for g in genes if g not in locus]
        genes = rest[:anchor] + locus + rest[anchor:]

    # memo sort: within each group, patients ordered by their alteration pattern
    # read down the gene ranking, so co-altered columns cluster
    def key(i):
        return tuple(0 if genes[r] in alt.iloc[i] else 1 for r in range(len(genes)))
    order = []
    for g in (0, 1):
        idx = [i for i in range(len(df)) if df.mBM.iloc[i] == g]
        order.append(sorted(idx, key=key))
    sbm, mbm = order
    cols = sbm + mbm
    gap = 2.2                       # blank columns separating the two groups
    xpos = list(np.arange(len(sbm))) + list(np.arange(len(mbm)) + len(sbm) + gap)
    total_w = len(sbm) + gap + len(mbm)

    fig = plt.figure(figsize=(11.2, 7.4))
    gs = fig.add_gridspec(3, 2, height_ratios=[1.05, 10, 0.42], width_ratios=[13, 2.35],
                          hspace=0.06, wspace=0.02,
                          left=0.085, right=0.985, top=0.945, bottom=0.115)
    axb = fig.add_subplot(gs[0, 0])          # per-patient burden
    ax  = fig.add_subplot(gs[1, 0])          # matrix
    axg = fig.add_subplot(gs[2, 0])          # group track
    axf = fig.add_subplot(gs[1, 1])          # frequency columns

    # --- burden bars -------------------------------------------------------
    burden = [len(alt.iloc[i]) for i in cols]
    for x, v, i in zip(xpos, burden, cols):
        axb.add_patch(Rectangle((x + .09, 0), .82, v,
                                facecolor=GROUP['mBM' if df.mBM.iloc[i] else 'sBM'],
                                edgecolor='none'))
    axb.set_xlim(-.5, total_w - .5); axb.set_ylim(0, max(burden) * 1.06)
    axb.set_yticks([0, 8, 16]); axb.tick_params(labelsize=7.5, colors=MUTED, length=2)
    axb.set_ylabel('Altered\ngenes', fontsize=7.5, color=INK_2, rotation=0,
                   ha='right', va='center', labelpad=16)
    for s in ('top', 'right', 'bottom'):
        axb.spines[s].set_visible(False)
    axb.spines['left'].set_color(MUTED); axb.set_xticks([])

    # --- matrix ------------------------------------------------------------
    for r, gene in enumerate(genes):
        y = len(genes) - 1 - r
        for x, i in zip(xpos, cols):
            classes = alt.iloc[i].get(gene, set())
            ax.add_patch(Rectangle((x + .09, y + .10), .82, .80,
                                   facecolor=EMPTY, edgecolor='none'))
            for c in [c for c in classes if c in CNA]:
                ax.add_patch(Rectangle((x + .09, y + .10), .82, .80,
                                       facecolor=CLASS[c], edgecolor='none'))
            small = [c for c in classes if c not in CNA]
            for c in small:
                ax.add_patch(Rectangle((x + .09, y + .32), .82, .36,
                                       facecolor=CLASS[c], edgecolor='none'))
    ax.set_xlim(-.5, total_w - .5); ax.set_ylim(0, len(genes))
    ax.set_yticks([len(genes) - 1 - r + .5 for r in range(len(genes))])
    ax.set_yticklabels(genes, fontsize=9, style='italic', color=INK)
    ax.set_xticks([]); ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)

    # --- group track -------------------------------------------------------
    for x, i in zip(xpos, cols):
        axg.add_patch(Rectangle((x + .09, .12), .82, .76,
                                facecolor=GROUP['mBM' if df.mBM.iloc[i] else 'sBM'],
                                edgecolor='none'))
    axg.set_xlim(-.5, total_w - .5); axg.set_ylim(0, 1)
    axg.set_xticks([]); axg.set_yticks([])
    for s in axg.spines.values():
        s.set_visible(False)
    axg.text((len(sbm) - 1) / 2, -.75, f'Synchronous BM (n={len(sbm)})',
             ha='center', va='top', fontsize=9, color=GROUP['sBM'], weight='bold')
    axg.text(len(sbm) + gap + (len(mbm) - 1) / 2, -.75, f'Metachronous BM (n={len(mbm)})',
             ha='center', va='top', fontsize=9, color=GROUP['mBM'], weight='bold')

    # --- frequency columns -------------------------------------------------
    axf.set_xlim(0, 1); axf.set_ylim(0, len(genes)); axf.axis('off')
    axf.text(.24, len(genes) + .35, 'sBM', ha='center', fontsize=8,
             color=GROUP['sBM'], weight='bold')
    axf.text(.72, len(genes) + .35, 'mBM', ha='center', fontsize=8,
             color=GROUP['mBM'], weight='bold')
    for r, gene in enumerate(genes):
        y = len(genes) - 1 - r + .5
        for xf, g, n in ((.24, 0, len(sbm)), (.72, 1, len(mbm))):
            k = sum(gene in alt.iloc[i] for i in range(len(df)) if df.mBM.iloc[i] == g)
            axf.text(xf, y, f'{100*k/n:.0f}%', ha='center', va='center',
                     fontsize=8.5, color=INK_2)

    handles = [Line2D([], [], marker='s', linestyle='none', markersize=9,
                      markerfacecolor=CLASS[c], markeredgecolor='none',
                      label=c + (' (whole cell)' if c in CNA else ' (inset bar)'))
               for c in CLASS]
    fig.legend(handles=handles, loc='lower center', ncol=5, frameon=False,
               fontsize=8.5, labelcolor=INK_2, bbox_to_anchor=(0.5, 0.008),
               handletextpad=.5, columnspacing=1.6)

    for ext in ('png', 'pdf'):
        fig.savefig(f'figures/figure2_oncoplot.{ext}', dpi=300,
                    facecolor=SURFACE, bbox_inches='tight')
    print('wrote figures/figure2_oncoplot.{png,pdf}')
    print('genes:', ', '.join(genes))


if __name__ == '__main__':
    main()
