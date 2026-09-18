"""Poster-scale variants of Figures 1 and 2: fewer elements, larger type.

A manuscript figure read at 20 cm does not survive a poster column. These drop
the tick density and gene count and raise every type size, keeping the same
estimates and the same encoding as figures/figure1 and figure2.
"""
import os, re, warnings
import numpy as np, pandas as pd
warnings.filterwarnings('ignore')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
from statsmodels.duration.survfunc import SurvfuncRight, survdiff

OUT = '/tmp/claude-0/-home-user-brainmets-POP/fac3ce9e-cc84-5882-a3b3-2547ca8b5da2/scratchpad/poster'
SURFACE, INK, INK_2, MUTED = '#ffffff', '#111a1c', '#44575a', '#8a9698'
GROUP = {'sBM': '#2a78d6', 'mBM': '#eb6834'}
CLASS = {'Amplification': '#e34948', 'Deletion': '#2a78d6',
         'Missense': '#008300', 'Truncating': '#1a1a19', 'Fusion': '#4a3aa7'}
CNA = {'Amplification', 'Deletion'}
EMPTY = '#e6e8e6'

plt.rcParams.update({'font.family': 'DejaVu Sans', 'figure.facecolor': SURFACE,
                     'axes.facecolor': SURFACE, 'axes.edgecolor': MUTED,
                     'xtick.color': MUTED, 'ytick.color': MUTED,
                     'axes.spines.top': False, 'axes.spines.right': False})


def load():
    df = pd.read_excel(os.environ.get('COHORT_XLSX', 'data/20260719cohort.xlsx'))
    d = 'Difference between Lung Ca. and Brain Met in days'
    df['event'] = (df['Is Deceased'].astype(str) == 'True').astype(int)
    df['os'] = df['Overall survival'].astype(float)
    df['mBM'] = (df.group == 'verl-mBM').astype(int)
    df['os_bm'] = (df.os - df[d] / 30.44).clip(lower=1 / 30.44)
    return df


def km(t, e):
    sf = SurvfuncRight(np.asarray(t, float), np.asarray(e, int))
    return np.concatenate([[0.], sf.surv_times]), np.concatenate([[1.], sf.surv_prob])


# ------------------------------------------------------------ Figure 1 -----
def survival(df):
    ticks = [0, 24, 48, 72, 96, 120]
    fig = plt.figure(figsize=(6.1, 7.6))
    gs = fig.add_gridspec(4, 1, height_ratios=[5, 1.3, 5, 1.3], hspace=0.70,
                          left=0.155, right=0.975, top=0.955, bottom=0.085)
    for row, (tcol, title) in enumerate([('os', 'A  From primary diagnosis'),
                                         ('B', 'B  From brain-metastasis diagnosis')]):
        tcol = 'os' if row == 0 else 'os_bm'
        ax = fig.add_subplot(gs[row * 2, 0])
        for lab, sub in (('sBM', df[df.mBM == 0]), ('mBM', df[df.mBM == 1])):
            t, s = km(sub[tcol], sub.event)
            tmax = float(sub[tcol].max())
            if tmax > t[-1]:
                t, s = np.append(t, tmax), np.append(s, s[-1])
            ax.step(t, s, where='post', color=GROUP[lab], lw=2.6,
                    linestyle='-' if lab == 'sBM' else (0, (5, 2)),
                    label=f'{lab} (n={len(sub)})')
        chi, p = survdiff(df[tcol], df.event, df.mBM)
        ax.text(.97, .93, 'log-rank p < 0.001' if p < .001 else f'log-rank p = {p:.2f}',
                transform=ax.transAxes, ha='right', va='top', fontsize=12.5,
                color=INK if p < .001 else INK_2,
                weight='bold' if p < .001 else 'normal')
        ax.set_title(title, fontsize=14, color=INK, pad=9, loc='left', weight='bold')
        ax.set_xlim(0, 132); ax.set_ylim(0, 1.03)
        ax.set_xticks(ticks); ax.tick_params(labelbottom=False, labelsize=12)
        ax.set_yticks([0, .25, .5, .75, 1.0])
        ax.set_yticklabels(['0', '25', '50', '75', '100'], fontsize=12)
        ax.set_ylabel('Overall survival (%)', fontsize=12.5, color=INK_2)
        ax.grid(axis='y', color=MUTED, alpha=.2, lw=.9); ax.set_axisbelow(True)
        ax.legend(frameon=False, fontsize=12.5, loc='upper right',
                  bbox_to_anchor=(1, .86), labelcolor=INK_2, handlelength=2.2)

        axr = fig.add_subplot(gs[row * 2 + 1, 0], sharex=ax)
        axr.axis('off')
        for i, (lab, sub) in enumerate((('sBM', df[df.mBM == 0]), ('mBM', df[df.mBM == 1]))):
            y = .66 - i * .46
            axr.text(-.135, y, lab, transform=axr.transAxes, fontsize=12,
                     color=GROUP[lab], ha='right', va='center', weight='bold')
            for t in ticks:
                axr.text(t, y, str(int((sub[tcol] >= t).sum())),
                         transform=axr.get_xaxis_transform(), fontsize=11.5,
                         color=INK_2, ha='center', va='center')
        for t in ticks:
            axr.text(t, 1.16, str(t), transform=axr.get_xaxis_transform(),
                     fontsize=12, color=MUTED, ha='center', va='center')
        axr.text(-.135, 1.16, 'At risk', transform=axr.transAxes, fontsize=10.5,
                 color=MUTED, ha='right', va='center')
        axr.text(.5, -.40, 'Months', transform=axr.transAxes, fontsize=12.5,
                 color=INK_2, ha='center', va='center')
    fig.savefig(f'{OUT}/poster_survival.png', dpi=200, facecolor=SURFACE,
                bbox_inches='tight')
    print('wrote poster_survival.png')


# ------------------------------------------------------------ Figure 2 -----
def classify(rest):
    r = re.sub(r'p\.\([^)]*\)\s*', '', rest).strip().lower()
    if 'amplification' in r:                                   return 'Amplification'
    if 'loss' in r or r == 'deletion':                          return 'Deletion'
    if 'fusion' in r or 'rearrangement' in r or 'delins' in r:  return 'Fusion'
    if any(k in r for k in ('frameshift', 'stop gained', 'splicing', 'insertion')):
        return 'Truncating'
    return 'Missense'


def parse(cell):
    out = {}
    for item in str(cell).split(';'):
        item = item.strip()
        if not item:
            continue
        parts = item.split(' ', 1)
        gene, rest = parts[0], (parts[1] if len(parts) > 1 else '')
        if gene.startswith('NKX2'):
            gene, rest = 'NKX2-1', re.sub(r'^1\s+', '', rest)
        if '-' in gene and ('fusion' in rest or 'delins' in rest):
            for g in gene.split('-'):
                out.setdefault(g, set()).add('Fusion')
            continue
        out.setdefault(gene, set()).add(classify(rest))
    return out


def oncoplot(df, n_genes=12):
    alt = df['Pathogenic variants (list)'].apply(parse)
    freq = {}
    for a in alt:
        for g in a:
            freq[g] = freq.get(g, 0) + 1
    genes = [g for g, _ in sorted(freq.items(), key=lambda kv: -kv[1])][:n_genes]
    locus = [g for g in ('CDKN2A', 'CDKN2B', 'MTAP') if g in genes]
    if len(locus) > 1:
        a0 = min(genes.index(g) for g in locus)
        rest = [g for g in genes if g not in locus]
        genes = rest[:a0] + locus + rest[a0:]

    def key(i):
        return tuple(0 if genes[r] in alt.iloc[i] else 1 for r in range(len(genes)))
    sbm = sorted([i for i in range(len(df)) if df.mBM.iloc[i] == 0], key=key)
    mbm = sorted([i for i in range(len(df)) if df.mBM.iloc[i] == 1], key=key)
    cols = sbm + mbm
    gap = 3.0
    xpos = list(np.arange(len(sbm))) + list(np.arange(len(mbm)) + len(sbm) + gap)
    total = len(sbm) + gap + len(mbm)

    fig = plt.figure(figsize=(6.1, 4.7))
    gs = fig.add_gridspec(2, 2, height_ratios=[10, .5], width_ratios=[12, 3.3],
                          hspace=.05, wspace=.02, left=.145, right=.985,
                          top=.945, bottom=.225)
    ax, axg, axf = (fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[1, 0]),
                    fig.add_subplot(gs[0, 1]))
    for r, gene in enumerate(genes):
        y = len(genes) - 1 - r
        for x, i in zip(xpos, cols):
            cl = alt.iloc[i].get(gene, set())
            ax.add_patch(Rectangle((x + .08, y + .10), .84, .80, facecolor=EMPTY, ec='none'))
            for c in [c for c in cl if c in CNA]:
                ax.add_patch(Rectangle((x + .08, y + .10), .84, .80, facecolor=CLASS[c], ec='none'))
            for c in [c for c in cl if c not in CNA]:
                ax.add_patch(Rectangle((x + .08, y + .32), .84, .36, facecolor=CLASS[c], ec='none'))
    ax.set_xlim(-.5, total - .5); ax.set_ylim(0, len(genes))
    ax.set_yticks([len(genes) - 1 - r + .5 for r in range(len(genes))])
    ax.set_yticklabels(genes, fontsize=13, style='italic', color=INK)
    ax.set_xticks([]); ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)

    for x, i in zip(xpos, cols):
        axg.add_patch(Rectangle((x + .08, .18), .84, .70,
                                facecolor=GROUP['mBM' if df.mBM.iloc[i] else 'sBM'], ec='none'))
    axg.set_xlim(-.5, total - .5); axg.set_ylim(0, 1)
    axg.axis('off')
    # anchored to the outer edge of each block: centred labels collide, because
    # the synchronous block is three times the width of the metachronous one
    axg.text(0, -0.85, f'Synchronous (n={len(sbm)})', ha='left',
             va='top', fontsize=12, color=GROUP['sBM'], weight='bold')
    axg.text(total - 1, -0.85, f'Metachronous (n={len(mbm)})', ha='right',
             va='top', fontsize=12, color=GROUP['mBM'], weight='bold')

    axf.set_xlim(0, 1); axf.set_ylim(0, len(genes)); axf.axis('off')
    axf.text(.22, len(genes) + .35, 'sBM', ha='center', fontsize=11.5,
             color=GROUP['sBM'], weight='bold')
    axf.text(.74, len(genes) + .35, 'mBM', ha='center', fontsize=11.5,
             color=GROUP['mBM'], weight='bold')
    for r, gene in enumerate(genes):
        y = len(genes) - 1 - r + .5
        for xf, g, n in ((.22, 0, len(sbm)), (.74, 1, len(mbm))):
            k = sum(gene in alt.iloc[i] for i in range(len(df)) if df.mBM.iloc[i] == g)
            axf.text(xf, y, f'{100*k/n:.0f}%', ha='center', va='center',
                     fontsize=12, color=INK_2)

    handles = [Line2D([], [], marker='s', linestyle='none', markersize=10,
                      markerfacecolor=CLASS[c], markeredgecolor='none', label=c)
               for c in CLASS]
    fig.legend(handles=handles, loc='lower center', ncol=5, frameon=False,
               fontsize=10.5, labelcolor=INK_2, bbox_to_anchor=(.55, .002),
               handletextpad=.35, columnspacing=.9)
    fig.savefig(f'{OUT}/poster_oncoplot.png', dpi=200, facecolor=SURFACE,
                bbox_inches='tight')
    print('wrote poster_oncoplot.png; genes:', ', '.join(genes))


if __name__ == '__main__':
    d = load(); survival(d); oncoplot(d)
