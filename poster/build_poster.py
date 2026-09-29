"""Build the ESMO 2026 e-poster (standalone HTML -> PDF + PNG).

All numbers are aggregate results already reported in docs/manuscript-draft.md and
docs/abstract-revised.md; no patient-level data is read here. Figures are the poster-scale
PNGs from analysis/11_poster_figures.py (oncoplot cropped to drop its overlapping labels,
which are redrawn in HTML) plus three SVG panels drawn from the aggregate numbers below.

    python poster/build_poster.py        # writes poster/esmo2026_eposter.{html,pdf,png}
"""
from __future__ import annotations

import base64
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
W, H = 2560, 1440

SBM, MBM = "#2a78d6", "#eb6834"          # group colours used by every existing figure
INK, INK2, MUTED, RULE = "#10191B", "#3F5254", "#5E6E70", "#CBD6D7"
TEAL, TEAL_BG, ALERT = "#0E4A52", "#E2EDEE", "#B3401F"
COLS = (510, 660, 620, 518)  # + 3 x 36 px gaps = 2416 px inner width


def b64(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()


# --------------------------------------------------------------------------- panel data

FOREST = [  # label, sublabel, HR, lo, hi, emphasis
    ("From primary diagnosis", "curves cross (non-PH)", 1.18, 0.75, 1.87, False),
    ("From BM diagnosis", "unadjusted", 2.96, 1.82, 4.83, True),
    ("From BM diagnosis", "adj. age, sex, histology", 2.92, 1.77, 4.82, False),
]

DUMBBELL = [  # label, sBM %, mBM %, raw p
    ("MYC amplification", 5.7, 25.0, "0.008"),
    ("FGFR1 amplification", 1.1, 14.3, "0.012"),
    ("CCND1 amplification", 2.3, 10.7, "0.09"),
    ("STK11 stop-gain", 3.4, 14.3, "0.06"),
    ("9p21.3 co-deletion", 13.6, 21.4, "0.37"),
    ("EGFR (any)", 19.3, 7.1, "0.15"),
    ("MET (any)", 11.4, 0.0, "0.12"),
    ("NKX2-1 amplification", 10.2, 0.0, "0.11"),
    ("KRAS (any)", 37.5, 39.3, "1.00"),
    ("TP53 (any)", 60.2, 50.0, "0.38"),
]


# --------------------------------------------------------------------------- SVG panels

def svg_clocks(w: int) -> str:
    """Schematic: what each time origin counts for a synchronous and a metachronous patient."""
    h = 236
    x0, x_bm, x_end = 150, 150 + int((w - 190) * 0.48), w - 30
    y1, y2 = 52, 142
    t = []
    t.append(f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" '
             'aria-label="Timelines for a synchronous and a metachronous patient showing the '
             'interval each survival clock counts">')
    t.append(f'<text x="0" y="{y1+6}" font-size="18" font-weight="700" fill="{SBM}">sBM</text>')
    t.append(f'<text x="0" y="{y1+26}" font-size="15" fill="{MUTED}">BM at Dx</text>')
    t.append(f'<text x="0" y="{y2+6}" font-size="18" font-weight="700" fill="{MBM}">mBM</text>')
    t.append(f'<text x="0" y="{y2+26}" font-size="15" fill="{MUTED}">BM later</text>')
    # sBM: primary dx and BM at the same time
    t.append(f'<line x1="{x0}" y1="{y1}" x2="{x_end}" y2="{y1}" stroke="{SBM}" stroke-width="6" stroke-linecap="round"/>')
    t.append(f'<circle cx="{x0}" cy="{y1}" r="9" fill="{SBM}" stroke="#fff" stroke-width="2"/>')
    t.append(f'<text x="{x0}" y="{y1-20}" font-size="15" fill="{INK2}" text-anchor="middle">Dx + BM</text>')
    # mBM: immortal segment then post-BM segment
    t.append(f'<line x1="{x0}" y1="{y2}" x2="{x_bm}" y2="{y2}" stroke="{MBM}" stroke-width="6" '
             'stroke-dasharray="3 9" stroke-linecap="round"/>')
    t.append(f'<line x1="{x_bm}" y1="{y2}" x2="{x_end}" y2="{y2}" stroke="{MBM}" stroke-width="6" stroke-linecap="round"/>')
    t.append(f'<circle cx="{x0}" cy="{y2}" r="9" fill="#fff" stroke="{MBM}" stroke-width="3"/>')
    t.append(f'<circle cx="{x_bm}" cy="{y2}" r="9" fill="{MBM}" stroke="#fff" stroke-width="2"/>')
    t.append(f'<text x="{x0}" y="{y2-20}" font-size="15" fill="{INK2}" text-anchor="middle">Dx</text>')
    t.append(f'<text x="{x_bm}" y="{y2-20}" font-size="15" fill="{INK2}" text-anchor="middle">BM</text>')
    t.append(f'<text x="{(x0+x_bm)/2}" y="{y2+30}" font-size="15" font-style="italic" fill="{ALERT}" '
             'text-anchor="middle">immortal time</text>')
    t.append(f'<text x="{(x0+x_bm)/2}" y="{y2+48}" font-size="14" fill="{ALERT}" '
             'text-anchor="middle">median 11.4 mo</text>')
    for y in (y1, y2):
        t.append(f'<text x="{x_end+8}" y="{y+6}" font-size="20" fill="{INK}">†</text>')
    # clock braces
    t.append(f'<text x="0" y="{h-24}" font-size="15" fill="{INK2}"><tspan font-weight="700">Clock A</tspan> '
             '(from Dx) counts the whole bar.</text>')
    t.append(f'<text x="0" y="{h-4}" font-size="15" fill="{INK2}"><tspan font-weight="700">Clock B</tspan> '
             '(from BM) counts only the solid part.</text>')
    t.append("</svg>")
    return "".join(t)


def svg_forest(w: int) -> str:
    row_h, top, bottom = 44, 30, 54
    h = top + row_h * len(FOREST) + bottom
    lab_w = 215
    lo_v, hi_v = 0.5, 6.0
    px0, px1 = lab_w + 10, w - 168

    def x(v):
        return px0 + (math.log(v) - math.log(lo_v)) / (math.log(hi_v) - math.log(lo_v)) * (px1 - px0)

    t = [f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" '
         'aria-label="Forest plot of hazard ratios for metachronous versus synchronous BM">']
    t.append(f'<text x="{px1+14}" y="{top-14}" font-size="14" font-weight="700" fill="{MUTED}" '
             'letter-spacing="0.06em">HR (95% CI)</text>')
    for v in (0.5, 1, 2, 4):
        t.append(f'<line x1="{x(v)}" y1="{top-6}" x2="{x(v)}" y2="{h-bottom+4}" stroke="#E4E3DF" stroke-width="1"/>')
        t.append(f'<text x="{x(v)}" y="{h-bottom+24}" font-size="14" fill="{MUTED}" text-anchor="middle">{v:g}</text>')
    t.append(f'<line x1="{x(1)}" y1="{top-6}" x2="{x(1)}" y2="{h-bottom+4}" stroke="{INK2}" stroke-width="1.5"/>')
    t.append(f'<text x="{x(0.72)}" y="{h-6}" font-size="14" fill="{MUTED}" text-anchor="middle">favours mBM</text>')
    t.append(f'<text x="{x(2.6)}" y="{h-6}" font-size="14" fill="{MUTED}" text-anchor="middle">favours sBM</text>')
    for i, (lab, sub, hr, lo, hi, emph) in enumerate(FOREST):
        y = top + row_h * i + row_h / 2
        wt = "700" if emph else "600"
        t.append(f'<text x="0" y="{y-3}" font-size="16" font-weight="{wt}" fill="{INK}">{lab}</text>')
        t.append(f'<text x="0" y="{y+16}" font-size="14" fill="{MUTED}">{sub}</text>')
        col = INK if i == 0 else MBM
        t.append(f'<line x1="{x(lo)}" y1="{y}" x2="{x(hi)}" y2="{y}" stroke="{col}" stroke-width="2.5" stroke-linecap="round"/>')
        t.append(f'<rect x="{x(hr)-7}" y="{y-7}" width="14" height="14" rx="2" fill="{col}" stroke="#fff" stroke-width="2"/>')
        t.append(f'<text x="{px1+14}" y="{y+5}" font-size="16" font-weight="{wt}" fill="{INK}" '
                 f'style="font-variant-numeric: tabular-nums">{hr:.2f} ({lo:.2f}–{hi:.2f})</text>'.replace('font-size="16"', 'font-size="15"'))
    t.append("</svg>")
    return "".join(t)


def svg_dumbbell(w: int) -> str:
    row_h, top, bottom = 27, 26, 30
    h = top + row_h * len(DUMBBELL) + bottom
    lab_w, pcol = 190, 58
    px0, px1 = lab_w + 8, w - pcol - 14
    xmax = 70

    def x(v):
        return px0 + v / xmax * (px1 - px0)

    t = [f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" '
         'aria-label="Alteration frequency in sBM versus mBM for selected alterations">']
    t.append(f'<text x="{w}" y="{top-12}" font-size="14" font-weight="700" fill="{MUTED}" '
             'text-anchor="end" letter-spacing="0.06em">raw p</text>')
    for v in (0, 20, 40, 60):
        t.append(f'<line x1="{x(v)}" y1="{top-4}" x2="{x(v)}" y2="{h-bottom+2}" stroke="#E4E3DF"/>')
        t.append(f'<text x="{x(v)}" y="{h-bottom+20}" font-size="14" fill="{MUTED}" text-anchor="middle">{v}%</text>')
    for i, (lab, a, b, p) in enumerate(DUMBBELL):
        y = top + row_h * i + row_h / 2
        if i == 4:  # separator between the amplification cluster and the rest
            t.append(f'<line x1="0" y1="{y-row_h/2}" x2="{w}" y2="{y-row_h/2}" stroke="{RULE}" stroke-dasharray="4 4"/>')
        strong = i < 2
        t.append(f'<text x="0" y="{y+5}" font-size="15" font-weight="{"700" if strong else "400"}" '
                 f'fill="{INK if strong else INK2}">{lab}</text>')
        t.append(f'<line x1="{x(a)}" y1="{y}" x2="{x(b)}" y2="{y}" stroke="#B8C4C5" stroke-width="3"/>')
        t.append(f'<circle cx="{x(a)}" cy="{y}" r="7" fill="{SBM}" stroke="#fff" stroke-width="2"/>')
        t.append(f'<circle cx="{x(b)}" cy="{y}" r="7" fill="{MBM}" stroke="#fff" stroke-width="2"/>')
        t.append(f'<text x="{w}" y="{y+5}" font-size="15" fill="{INK if strong else MUTED}" text-anchor="end" '
                 f'style="font-variant-numeric: tabular-nums">{p}</text>')
    t.append("</svg>")
    return "".join(t)


# --------------------------------------------------------------------------- page

def page() -> str:
    km = b64(HERE / "assets" / "km_two_clocks.png")
    onco = b64(HERE / "assets" / "oncoplot_cropped.png")
    h2 = (f'font-size:24px;font-weight:700;letter-spacing:0.09em;text-transform:uppercase;'
          f'color:{TEAL};margin:0;padding-bottom:8px;border-bottom:3px solid {TEAL}')
    body = f"font-size:18px;line-height:1.45;color:{INK2};margin:0"
    card = f"background:#fff;border:1px solid {RULE};padding:14px 18px"
    kicker = (f"margin:0 0 6px;font-size:15px;font-weight:700;letter-spacing:0.06em;"
              f"text-transform:uppercase;color:{TEAL}")

    def bullet(txt, colour=TEAL):
        return (f'<div style="display:flex;gap:12px;align-items:flex-start">'
                f'<div style="width:7px;height:7px;margin-top:9px;flex:none;background:{colour}"></div>'
                f'<p style="{body}">{txt}</p></div>')

    def swatch(c, lab):
        return (f'<span style="display:inline-flex;align-items:center;gap:6px;margin-right:16px">'
                f'<span style="width:14px;height:14px;background:{c};display:inline-block"></span>{lab}</span>')

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Brain Metastases in NSCLC — ESMO 2026 e-Poster</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Sans+3:ital,wght@0,400;0,600;0,700;1,400&family=Source+Serif+4:opsz,wght@8..60,600&display=swap">
<style>
  @page {{ size: {W}px {H}px; margin: 0 }}
  html, body {{ margin:0; background:#F2F5F6; font-family:"Source Sans 3", system-ui, sans-serif; }}
  svg text {{ font-family:"Source Sans 3", system-ui, sans-serif; }}
  strong {{ color:{INK}; }}
</style></head>
<body>
<div style="width:{W}px;height:{H}px;box-sizing:border-box;display:flex;flex-direction:column;overflow:hidden;background:#F2F5F6">

<header style="padding:28px 72px 24px;background:{TEAL};color:#fff;display:flex;flex-direction:column;gap:10px">
  <div style="display:flex;align-items:center;gap:18px">
    <span style="font-size:17px;font-weight:700;letter-spacing:0.14em;text-transform:uppercase;background:#fff;color:{TEAL};padding:5px 13px">Abstract 2202</span>
    <span style="font-size:17px;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;color:#9FC6CB">ESMO Congress 2026 · Madrid</span>
  </div>
  <h1 style="margin:0;font-family:'Source Serif 4',Georgia,serif;font-size:44px;line-height:1.14;font-weight:600;max-width:2200px">Metachronous Brain Metastases in NSCLC Show Markedly Worse Post-Metastasis Survival Despite a Shared Genomic Landscape</h1>
  <p style="margin:0;font-size:20px;font-weight:600">L. Hempel, M. Sarwary, L. Fabregas-Ibanez, N. Miglino, M. Nowak, S. Rahmani Khajouei, M. Zoche, A. Wicki, L. Boos</p>
  <p style="margin:0;font-size:18px;color:#A9CDD1">Department of Medical Oncology and Hematology, University Hospital Zurich · University of Zurich, Switzerland</p>
</header>

<main style="flex:1;min-height:0;box-sizing:border-box;padding:26px 72px 0;display:flex;gap:36px">

<!-- ================= 1 · BACKGROUND & DESIGN ================= -->
<section style="width:{COLS[0]}px;display:flex;flex-direction:column;gap:13px">
  <h2 style="{h2}">Background</h2>
  <p style="{body}">Brain metastases (BM) develop in up to <strong>40% of NSCLC</strong>. Whether <span style="color:{SBM};font-weight:700">synchronous</span> (at diagnosis, sBM) and <span style="color:{MBM};font-weight:700">metachronous</span> (later, mBM) BM differ in prognosis or genomics is unclear.</p>
  <div style="{card};border-top:4px solid {MBM}">
    <p style="{kicker};color:{ALERT}">Why the survival clock matters</p>
    <p style="{body};margin-bottom:4px">Survival is usually measured from primary diagnosis, but an mBM patient must survive until BM appears: <strong>immortal time</strong>.</p>
    {svg_clocks(COLS[0] - 38)}
  </div>

  <h2 style="{h2};margin-top:8px">Methods</h2>
  <div style="display:flex;gap:12px">
    <div style="flex:1;{card};padding:10px 14px"><div style="font-size:36px;font-weight:700;color:{INK}">116</div><div style="font-size:15px;color:{MUTED}">NSCLC with confirmed BM</div></div>
    <div style="flex:1;{card};padding:10px 14px"><div style="font-size:36px;font-weight:700;color:{SBM}">88</div><div style="font-size:15px;color:{MUTED}">sBM (≤ 3 months)</div></div>
    <div style="flex:1;{card};padding:10px 14px"><div style="font-size:36px;font-weight:700;color:{MBM}">28</div><div style="font-size:15px;color:{MUTED}">mBM (&gt; 3 months)</div></div>
  </div>
  {bullet("Monocentric, retrospective, consecutive; 89 deaths. Balanced for age, sex, histology.")}
  {bullet("FoundationOne CDx genomic profiling; PD-L1 by SP263.")}
  {bullet("Kaplan–Meier, log-rank, Cox. 42 recurrent alterations (≥ 5 patients): Fisher's exact test, Benjamini–Hochberg FDR.")}
  <div style="background:{TEAL_BG};padding:12px 18px">
    <p style="{kicker}">Endpoints</p>
    <p style="{body};color:{INK}"><strong>Primary:</strong> OS from BM diagnosis (clock B)<br><strong>Secondary:</strong> OS from primary diagnosis (clock A)</p>
  </div>
</section>

<!-- ================= 2 · SURVIVAL ================= -->
<section style="width:{COLS[1]}px;display:flex;flex-direction:column;gap:13px">
  <h2 style="{h2}">Results · Survival</h2>
  <div style="{card};padding:8px">
    <img src="{km}" alt="Kaplan-Meier curves for sBM and mBM, from primary diagnosis (log-rank p = 0.47) and from BM diagnosis (log-rank p below 0.001)" style="display:block;width:90%;margin:0 auto">
  </div>
  <p style="font-size:16px;line-height:1.4;color:{MUTED};margin:0">Same 116 patients, 89 deaths. In A, mBM runs <em>above</em> sBM early (it cannot die before BM), then below: the curves cross. Median OS from BM, 95% CI: sBM 18.0–40.0, mBM 4.9–13.1 mo.</p>
  <div style="background:{TEAL};padding:10px 18px;color:#fff;display:flex;align-items:baseline;gap:14px;white-space:nowrap">
    <span style="font-size:15px;letter-spacing:0.06em;text-transform:uppercase;color:#9FC6CB">Median OS from BM</span>
    <span style="font-size:26px;font-weight:700">25.0 <span style="font-size:17px;font-weight:600;color:#9FC6CB">vs</span> 11.1 mo</span>
    <span style="font-size:15px;color:#CFE3E5">HR 2.96, p &lt; 0.001</span>
  </div>
  <div style="{card};padding:12px 12px 6px">
    <p style="{kicker}">mBM vs sBM · Cox models</p>
    {svg_forest(COLS[1] - 26)}
  </div>
</section>

<!-- ================= 3 · GENOMICS ================= -->
<section style="width:{COLS[2]}px;display:flex;flex-direction:column;gap:13px">
  <h2 style="{h2}">Results · Genomics</h2>
  <div style="{card};padding:10px 10px 8px">
    <img src="{onco}" alt="Oncoplot of the 12 most frequently altered genes, sBM beside mBM" style="display:block;width:100%">
    <div style="position:relative;height:22px;font-size:15px;font-weight:700">
      <span style="position:absolute;left:14.5%;color:{SBM}">Synchronous (n = 88)</span>
      <span style="position:absolute;left:62.3%;color:{MBM}">Metachronous (n = 28)</span>
    </div>
    <div style="font-size:14px;color:{INK2};margin-top:6px">{swatch('#e34948','Amplification')}{swatch('#2a78d6','Deletion')}{swatch('#008300','Missense')}{swatch('#1a1a1a','Truncating')}{swatch('#4a3aa7','Fusion')}</div>
  </div>
  <div style="{card};padding:12px 14px 6px">
    <p style="{kicker}">Frequency by group &nbsp;<span style="color:{SBM}">● sBM</span> &nbsp;<span style="color:{MBM}">● mBM</span></p>
    {svg_dumbbell(COLS[2] - 30)}
    <p style="font-size:15px;line-height:1.35;color:{MUTED};margin:4px 0 6px"><strong>No alteration survives FDR correction</strong> (all q ≥ 0.17). The strongest raw signals are focal <strong>amplifications, all higher in mBM</strong> (8q24 <em>MYC</em>; 8p11 <em>FGFR1</em>; 11q13 <em>CCND1</em>).</p>
  </div>
  <div style="background:{TEAL_BG};border-top:4px solid {TEAL};padding:12px 18px;display:flex;flex-direction:column;gap:6px">
    <p style="{kicker};margin:0">9p21.3 <em>CDKN2A/CDKN2B/MTAP</em> co-deletion</p>
    <p style="{body};color:{INK}"><strong>15.5%</strong> (18/116; sBM 13.6% vs mBM 21.4%, p = 0.37), always as one contiguous deletion. Not above unselected NSCLC on comparable CGP (13.4%, n = 29,379; p = 0.49). No detectable prognostic effect: HR 1.17 (0.65–2.10).</p>
  </div>
</section>

<!-- ================= 4 · INTERPRETATION & CONCLUSION ================= -->
<section style="width:{COLS[3]}px;display:flex;flex-direction:column;gap:13px">
  <h2 style="{h2}">Interpretation</h2>
  {bullet("<strong>The clock decides the answer.</strong> From primary diagnosis, immortal time and later excess mortality cancel out. From BM diagnosis, mBM carries <strong>about 3× the hazard</strong>, stable under adjustment.", MBM)}
  {bullet("mBM is a <strong>progression event in pretreated disease</strong>; its survival resembles later-line rather than first-line outcomes.", MBM)}
  {bullet("<strong>No genomic difference detected, but not equivalence:</strong> 28 mBM patients detect only ~4-fold differences (e.g. 15% vs 43%). The mBM <em>MYC</em> amplification excess echoes BM-enriched <em>MYC</em> amplification (Shih et al.<sup>1</sup>) and merits validation.", MBM)}
  {bullet("<strong>1 in 6 carries an <em>MTAP</em> deletion</strong>, independent of BM timing: candidates for PRMT5/MAT2A inhibitor trials.", MBM)}

  <h2 style="{h2};margin-top:6px">Conclusion</h2>
  <div style="background:{ALERT};padding:16px 20px">
    <p style="margin:0;font-size:21px;line-height:1.36;font-weight:600;color:#fff">Survival after metachronous BM is short. Compare sBM and mBM from the metastatic event: from primary diagnosis, the difference disappears.</p>
  </div>
  <p style="{body};color:{INK}">For counselling and trial stratification, treat mBM as disease that has progressed on therapy.</p>

  <div style="background:#E6EBEB;padding:12px 16px">
    <p style="{kicker};color:{MUTED}">Limitations</p>
    <p style="font-size:15px;line-height:1.38;color:{INK2};margin:0">Single centre, retrospective, 28 mBM. Annotation missing unevenly (43% sBM vs 21% mBM); in the 72 fully annotated patients HR 1.85 (1.07–3.21). CNS-directed therapy not captured. No BM-free comparator, so no claim about BM <em>risk</em>.</p>
  </div>
  <div style="{card};border-left:4px solid {TEAL};padding:10px 16px">
    <p style="{kicker}">Next steps</p>
    <p style="font-size:16px;line-height:1.38;color:{INK2};margin:0">Add a BM-free CGP comparator (enrichment, time-dependent Cox). Abstract SRS/WBRT/resection per patient. Validate the mBM amplification signal in an external series.</p>
  </div>
  <p style="font-size:13px;line-height:1.35;color:{MUTED};margin:0"><sup>1</sup> Shih DJH et al. <em>Nat Genet</em> 2020;52:371–377. Reference 9p21.3 rate: Kumar et al., <em>Cancer Med</em> 2023.</p>
</section>
</main>

<footer style="padding:12px 72px;background:#DCE5E6;border-top:1px solid #C2CFD0;display:flex;justify-content:space-between;align-items:center;margin-top:14px">
  <p style="margin:0;font-size:15px;color:{INK2}">Patient-level, de-duplicated alteration calls; two-sided tests; Python (statsmodels, scipy). <strong>Disclosures:</strong> [TO COMPLETE]</p>
  <p style="margin:0;font-size:15px;font-weight:600;color:{TEAL}">louisa.hempel@usz.ch · Department of Medical Oncology and Hematology, USZ</p>
</footer>
</div>
</body></html>"""


def render(html_path: Path):
    from playwright.sync_api import sync_playwright

    exe = "/opt/pw-browsers/chromium" if Path("/opt/pw-browsers/chromium").exists() else None
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=exe)
        pg = b.new_page(viewport={"width": W, "height": H})
        pg.goto(html_path.as_uri())
        pg.wait_for_timeout(1500)  # web fonts
        overflow = pg.evaluate("""() => [...document.querySelectorAll('main > section')]
            .map(s => ({h: s.scrollHeight, room: s.parentElement.clientHeight}))""")
        pg.screenshot(path=str(html_path.with_suffix(".png")))
        pg.pdf(path=str(html_path.with_suffix(".pdf")), width=f"{W}px", height=f"{H}px",
               print_background=True)
        b.close()
    return overflow


if __name__ == "__main__":
    out = HERE / "esmo2026_eposter.html"
    out.write_text(page())
    for i, o in enumerate(render(out), 1):
        flag = "OVERFLOW" if o["h"] > o["room"] - 26 else "ok"
        print(f"column {i}: content {o['h']}px / room {o['room'] - 26}px  {flag}")
    print(f"wrote {out} (+ .pdf, .png)")
