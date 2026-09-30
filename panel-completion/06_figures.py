"""Figures for the review (figures/*.png).

fig1_pooled_vs_per_gene.png  pooled vs per-gene AUROC, every model, 95% patient-bootstrap CI
fig2_event_type.png          per-gene AUROC split by the event type of the positives
fig3_mc_budget.png           CFM AUROC vs number of Monte Carlo samples, vs one-call readout
"""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from pc_common import FIGURES, RESULTS

INK, INK2, MUTED, GRID, BASE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
S1, S2, S3 = "#2a78d6", "#eb6834", "#1baf7a"
plt.rcParams.update({
    "font.family": "sans-serif", "font.size": 9, "axes.edgecolor": BASE, "axes.labelcolor": INK2,
    "xtick.color": MUTED, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb", "savefig.facecolor": "#fcfcfb",
})
FIGURES.mkdir(exist_ok=True)

LABEL = {
    "prevalence": "Prevalence only (no patient information)",
    "burden": "Burden: 3 counts from the small panel",
    "burden+locus": "Burden + nearest on-panel CNA (7 features)",
    "logistic": "L2 logistic regression, 1,026 features",
    "logistic+clinical": "  + smoking, sex, histology, sample type",
    "mlp": "Multi-label MLP",
    "cfm_velocity_mc100": "Flow matching, 100 MC samples",
    "cfm_velocity_t0": "Flow matching, one-call t=0 readout",
    "cfm_x1_t0": "Flow matching, x1/cross-entropy param.",
    "pan_logistic": "Pan-cancer logistic (7,773 pts)",
    "pan_mlp": "Pan-cancer MLP",
    "pan_cfm_velocity_mc100": "Pan-cancer flow matching, 100 MC",
    "pan_cfm_velocity_t0": "Pan-cancer flow matching, t=0 readout",
}
ORDER = list(LABEL)

m = pd.read_csv(RESULTS / "metrics_any.csv").set_index("model")
m = m.loc[[k for k in ORDER if k in m.index]][::-1]

# ------------------------------------------------------------------------------ fig 1
fig, axes = plt.subplots(1, 2, figsize=(10, 0.36 * len(m) + 1.4), sharey=True)
panels = [("pooled", "Pooled AUROC (the abstract's metric)"),
          ("macro", f"Per-gene AUROC ({int(m.n_genes_macro.iloc[0])} genes with ≥10 events)")]
for ax, (k, title) in zip(axes, panels):
    y = range(len(m))
    for i, (name, r) in enumerate(m.iterrows()):
        c = MUTED if name == "prevalence" else S1
        ax.plot([r[f"{k}_auroc_ci_lo"], r[f"{k}_auroc_ci_hi"]], [i, i], color=c, lw=2, solid_capstyle="round")
        ax.plot(r[f"{k}_auroc"], i, "o", ms=7, color=c, mec="#fcfcfb", mew=2)
        ax.text(r[f"{k}_auroc_ci_hi"] + 0.006, i, f"{r[f'{k}_auroc']:.3f}", va="center", color=INK2, fontsize=8)
    ax.axvline(m.loc["prevalence", f"{k}_auroc"], color=MUTED, lw=1, ls=(0, (3, 3)))
    names = list(m.index)
    for a, b in [("mlp", "cfm_velocity_mc100"), ("cfm_x1_t0", "pan_logistic")]:
        if a in names and b in names:
            ax.axhline((names.index(a) + names.index(b)) / 2, color=GRID, lw=1)
    ax.set_title(title, loc="left", color=INK, fontsize=10)
    ax.set_xlim(0.45, 0.95)
    ax.grid(axis="x", color=GRID, lw=0.6)
    ax.set_xlabel("AUROC (95% CI, patient bootstrap)")
axes[0].set_yticks(range(len(m)))
axes[0].set_yticklabels([LABEL[k] for k in m.index])
fig.suptitle("MSK-IMPACT 2017 NSCLC, IMPACT341 → 69 IMPACT410-only genes, 3×5-fold patient-level CV",
             x=0.01, ha="left", color=INK2, fontsize=9)
fig.tight_layout()
fig.savefig(FIGURES / "fig1_pooled_vs_per_gene.png", dpi=200)

# ------------------------------------------------------------------------------ fig 2
ev_long = pd.read_csv(RESULTS / "event_type_any.csv")
SHORT = {"burden": "Burden\n(3 features)", "burden+locus": "Burden + locus\n(7 features)",
         "logistic": "Logistic\n(1,026 features)", "pan_logistic": "Pan-cancer\nlogistic",
         "cfm_velocity_t0": "Flow matching\n(t=0 readout)"}
show = [k for k in SHORT if k in set(ev_long.model)]
ev = ev_long[ev_long.model.isin(show)].pivot(index="model", columns="event", values="weighted_auroc").loc[show]
cnt = ev_long[ev_long.model == "logistic"].set_index("event")
fig, ax = plt.subplots(figsize=(10, 3.6))
events = [(e, f"{lab} ({int(cnt.loc[e, 'n_pos'])} events, {int(cnt.loc[e, 'n_genes'])} genes)", c)
          for e, lab, c in [("mut", "Mutations", S1), ("amp", "Amplifications", S2), ("dele", "Deep deletions", S3)]]
w = 0.26
for j, (e, lab, c) in enumerate(events):
    x = [i + (j - 1) * w for i in range(len(show))]
    ax.bar(x, ev[e] - 0.5, bottom=0.5, width=w - 0.03, color=c, label=lab)
ax.axhline(0.5, color=BASE, lw=1)
ax.set_xticks(range(len(show)))
ax.set_xticklabels([SHORT[k] for k in show], fontsize=8)
ax.set_ylim(0.45, 1.0)
ax.set_ylabel("Per-gene AUROC\n(positives-weighted)")
ax.grid(axis="y", color=GRID, lw=0.6)
ax.legend(frameon=False, ncol=1, loc="upper left", bbox_to_anchor=(1.01, 1.0), fontsize=8)
ax.set_title("CNAs are recovered from co-amplified neighbours; mutations only through burden",
             loc="left", color=INK, fontsize=10)
fig.tight_layout()
fig.savefig(FIGURES / "fig2_event_type.png", dpi=200)

# ------------------------------------------------------------------------------ fig 3
j = json.load(open(RESULTS / "joint.json"))
mc = pd.DataFrame(j["mc_budget"])
fig, ax = plt.subplots(figsize=(6.5, 3.6))
ax.plot(mc.n_samples, mc.pooled_auroc, "-o", color=S1, lw=2, ms=7, mec="#fcfcfb", mew=2,
        label="Monte Carlo: share of samples altered")
ax.axhline(j["cfm_t0_readout_pooled_auroc"], color=S2, lw=2, label="One network call at t = 0")
ax.set_xscale("log")
ax.set_xticks(mc.n_samples)
ax.set_xticklabels([f"{n}\n{100 * z:.0f}% at p=0" for n, z in zip(mc.n_samples, mc.share_zero_probability)])
ax.minorticks_off()
ax.set_xlabel("Samples drawn per patient (share of gene–patient pairs tied at probability 0)")
ax.set_ylabel("Pooled AUROC")
ax.grid(axis="y", color=GRID, lw=0.6)
ax.legend(frameon=False, fontsize=8, loc="upper left", bbox_to_anchor=(0, 0.9))
ax.set_title("Reading probabilities from samples wastes the model", loc="left", color=INK, fontsize=10)
fig.tight_layout()
fig.savefig(FIGURES / "fig3_mc_budget.png", dpi=200)
print("wrote", sorted(p.name for p in FIGURES.glob("*.png")))
