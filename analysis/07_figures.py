"""Figure 1: overall survival under both clocks, with numbers at risk.

The point of the figure is the contrast between the panels: the same patients,
the same deaths, two different time origins, opposite conclusions.
"""
import os, warnings
import numpy as np, pandas as pd
warnings.filterwarnings('ignore')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from statsmodels.duration.survfunc import SurvfuncRight, survdiff

SURFACE   = '#fcfcfb'
INK       = '#0b0b0b'
INK_2     = '#52514e'
MUTED     = '#898781'
SERIES    = {'sBM': '#2a78d6', 'mBM': '#eb6834'}   # validated categorical slots 1-2
STYLE     = {'sBM': '-',       'mBM': (0, (5, 2))}  # secondary encoding for print

plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 9,
    'axes.edgecolor': MUTED, 'axes.labelcolor': INK, 'text.color': INK,
    'xtick.color': MUTED, 'ytick.color': MUTED,
    'figure.facecolor': SURFACE, 'axes.facecolor': SURFACE,
    'axes.spines.top': False, 'axes.spines.right': False,
})


def km(time, event):
    """Kaplan-Meier estimate as step coordinates starting at (0, 1)."""
    sf = SurvfuncRight(np.asarray(time, float), np.asarray(event, int))
    t = np.concatenate([[0.0], sf.surv_times])
    s = np.concatenate([[1.0], sf.surv_prob])
    return t, s


def median_st(time, event):
    t, s = km(time, event)
    below = np.where(s <= 0.5)[0]
    return t[below[0]] if len(below) else np.nan


def panel(ax, df, tcol, title, xmax, ticks):
    for label, sub in (('sBM', df[df.mBM == 0]), ('mBM', df[df.mBM == 1])):
        t, s = km(sub[tcol], sub.event)
        # carry the flat tail out to the last observation, so a censoring mark
        # beyond the final event sits on the curve instead of floating free
        tmax = float(sub[tcol].max())
        if tmax > t[-1]:
            t, s = np.append(t, tmax), np.append(s, s[-1])
        ax.step(t, s, where='post', color=SERIES[label], lw=2,
                linestyle=STYLE[label], label=f'{label} (n={len(sub)})',
                solid_capstyle='butt')
        cens = sub.loc[sub.event == 0, tcol]
        if len(cens):
            idx = np.searchsorted(t, cens, side='right') - 1
            ax.plot(cens, s[np.clip(idx, 0, len(s) - 1)], '|',
                    color=SERIES[label], ms=5, mew=1.2)

    chi, p = survdiff(df[tcol], df.event, df.mBM)
    ptxt = 'log-rank p < 0.001' if p < 0.001 else f'log-rank p = {p:.2f}'
    ax.text(0.97, 0.94, ptxt, transform=ax.transAxes, ha='right', va='top',
            fontsize=8.5, color=INK_2)

    ax.set_title(title, fontsize=10, color=INK, pad=8, loc='left')
    ax.set_xlim(0, xmax); ax.set_ylim(0, 1.02)
    ax.set_xticks(ticks)
    ax.set_yticks([0, 0.25, 0.50, 0.75, 1.0])
    ax.set_yticklabels(['0', '25', '50', '75', '100'])
    ax.tick_params(labelbottom=False)
    ax.grid(axis='y', color=MUTED, alpha=0.18, lw=0.7)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=8.5, loc='upper right',
              bbox_to_anchor=(1.0, 0.88), labelcolor=INK_2, handlelength=2.2)
    return ticks


def at_risk(ax, df, tcol, ticks):
    """Numbers-at-risk table drawn in its own axes below the curve."""
    ax.axis('off')
    ax.set_xlim(ax_lims[0], ax_lims[1])
    for row, (label, sub) in enumerate((('sBM', df[df.mBM == 0]),
                                        ('mBM', df[df.mBM == 1]))):
        y = 0.62 - row * 0.42
        ax.text(-0.055, y, label, transform=ax.transAxes, fontsize=8.5,
                color=SERIES[label], ha='right', va='center', weight='bold')
        for t in ticks:
            ax.text(t, y, str(int((sub[tcol] >= t).sum())), transform=ax.get_xaxis_transform(),
                    fontsize=8, color=INK_2, ha='center', va='center')
    ax.text(-0.055, 1.06, 'At risk', transform=ax.transAxes, fontsize=7.5,
            color=MUTED, ha='right', va='center')
    for t in ticks:
        ax.text(t, 1.06, str(t), transform=ax.get_xaxis_transform(),
                fontsize=8.5, color=MUTED, ha='center', va='center')
    ax.text(0.5, -0.30, 'Months', transform=ax.transAxes, fontsize=9,
            color=INK_2, ha='center', va='center')


def main():
    df = pd.read_excel(os.environ.get('COHORT_XLSX', 'data/20260719cohort.xlsx'))
    d = 'Difference between Lung Ca. and Brain Met in days'
    df['event'] = (df['Is Deceased'].astype(str) == 'True').astype(int)
    df['os'] = df['Overall survival'].astype(float)
    df['mBM'] = (df.group == 'verl-mBM').astype(int)
    df['os_bm'] = (df.os - df[d] / 30.44).clip(lower=1 / 30.44)

    global ax_lims
    ax_lims = (0, 132)
    ticks = [0, 24, 48, 72, 96, 120]

    fig = plt.figure(figsize=(10.2, 5.2))
    gs = fig.add_gridspec(2, 2, height_ratios=[4.2, 1], hspace=0.30, wspace=0.30,
                          left=0.095, right=0.985, top=0.91, bottom=0.13)

    for col, (tcol, title) in enumerate([
            ('os',    'A   Overall survival from primary diagnosis'),
            ('os_bm', 'B   Overall survival from brain-metastasis diagnosis')]):
        ax = fig.add_subplot(gs[0, col])
        panel(ax, df, tcol, title, 132, ticks)
        if col == 0:
            ax.set_ylabel('Overall survival (%)', color=INK_2, fontsize=9)
        axr = fig.add_subplot(gs[1, col], sharex=ax)
        at_risk(axr, df, tcol, ticks)

    for ext in ('png', 'pdf'):
        fig.savefig(f'figures/figure1_survival_both_clocks.{ext}',
                    dpi=300, facecolor=SURFACE, bbox_inches='tight')
    print('wrote figures/figure1_survival_both_clocks.{png,pdf}')

    for tcol, lab in [('os', 'from primary dx'), ('os_bm', 'from BM dx')]:
        for g, name in [(0, 'sBM'), (1, 'mBM')]:
            s = df[df.mBM == g]
            print(f'  {lab:16s} {name}: median {median_st(s[tcol], s.event):.1f} mo')


if __name__ == '__main__':
    main()
