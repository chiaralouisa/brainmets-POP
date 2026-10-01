// ESMO paper poster P305 as one editable PowerPoint slide.
// PowerPoint caps slides at 56 in, so the 190 x 110 cm poster is built at 50% (95 x 55 cm)
// and printed at 200%. All type sizes are half the printed size.
const pptxgen = require("pptxgenjs");
const pres = new pptxgen();
const W = 95 / 2.54, H = 55 / 2.54;               // 37.40 x 21.65 in
pres.defineLayout({ name: "POSTER_HALF", width: W, height: H });
pres.layout = "POSTER_HALF";
pres.title = "ESMO poster P305 – genomic panel completion";

const INK = "12202E", MUTED = "3F4B57", RULE = "C9D0D7", BLUE = "2A6FD6", ORANGE = "C4501B",
  LIGHT_BLUE = "8FB3EA", PEACH = "FBE3D5", TINT = "F2F4F7", PH = "A3410F";
const HEAD = "Cambria", BODY = "Calibri";
const s = pres.addSlide();
s.background = { color: "FFFFFF" };

const M = 0.625, TOP = 0.5;
const txt = (text, o) => s.addText(text, Object.assign({ isTextBox: true, fontFace: BODY, color: INK, margin: 0, valign: "top" }, o));
const rect = (x, y, w, h, o) => s.addShape(pres.shapes.RECTANGLE, Object.assign({ x, y, w, h }, o));
const hline = (x, y, w, color, pt) => s.addShape(pres.shapes.LINE, { x, y, w, h: 0, line: { color, width: pt } });

// ---------------------------------------------------------------- header
const FPN_W = 3.6, headH = 3.85;
txt("Conditional flow matching for genomic panel completion: inferring IMPACT505 alterations from the IMPACT341 targeted panel in non-small cell lung cancer",
  { x: M, y: TOP, w: W - 2 * M - FPN_W - 0.6, h: 2.15, fontFace: HEAD, fontSize: 47, bold: true, fit: "none" });
txt([{ text: "Louisa Hempel" }, { text: "1", options: { superscript: true } }, { text: ", F. Capuano" }, { text: "2", options: { superscript: true } }],
  { x: M, y: TOP + 2.3, w: W - 2 * M - FPN_W - 0.6, h: 0.45, fontSize: 20, bold: true });
txt([{ text: "1", options: { superscript: true } }, { text: "Medical Department, Sigmund Freud University Vienna, Vienna, Austria   ·   " },
  { text: "2", options: { superscript: true } }, { text: "Oxford Robotics Institute, University of Oxford, Oxford, United Kingdom" }],
  { x: M, y: TOP + 2.85, w: W - 2 * M - FPN_W - 0.6, h: 0.4, fontSize: 15, color: MUTED });
rect(W - M - FPN_W, TOP, FPN_W, headH - 0.35, { fill: { color: INK } });
txt("FPN", { x: W - M - FPN_W, y: TOP + 0.45, w: FPN_W, h: 0.5, fontSize: 24, bold: true, color: "FFFFFF", align: "center", charSpacing: 6 });
txt("P305", { x: W - M - FPN_W, y: TOP + 1.05, w: FPN_W, h: 1.9, fontSize: 80, bold: true, color: "FFFFFF", align: "center", valign: "middle", fit: "none", wrap: false });
hline(M, TOP + headH, W - 2 * M, INK, 3);

// ---------------------------------------------------------------- columns
const COLS = 4, GAP = 0.57, CW = (W - 2 * M - GAP * (COLS - 1)) / COLS;
const colX = (i) => M + i * (CW + GAP);
const Y0 = TOP + headH + 0.4, FOOT_Y = H - 1.6;
const cur = [Y0, Y0, Y0, Y0];
const BODY_PT = 16.5, CAP_PT = 13.5;
// rough height estimate for wrapped Calibri text (in)
const est = (str, pt, w) => {
  const perLine = Math.floor(w / (pt * 0.53 / 72));
  const lines = str.split("\n").reduce((n, l) => n + Math.max(1, Math.ceil(l.length / perLine)), 0);
  return lines * pt * 1.25 / 72 + 0.04;
};
const plain = (runs) => typeof runs === "string" ? runs : runs.map((r) => r.text).join("");

function heading(c, label) {
  hline(colX(c), cur[c], CW, INK, 2.25);
  txt(label, { x: colX(c), y: cur[c] + 0.1, w: CW, h: 0.62, fontFace: HEAD, fontSize: 32, bold: true });
  cur[c] += 0.95;
}
function para(c, runs, o = {}) {
  const pt = o.fontSize || BODY_PT;
  const h = est(plain(runs), pt, CW);
  txt(runs, Object.assign({ x: colX(c), y: cur[c], w: CW, h, fontSize: pt }, o));
  cur[c] += h + (o.after ?? 0.25);
}
const caption = (c, label, rest) => para(c, [{ text: label + " ", options: { bold: true } }, { text: rest }], { fontSize: CAP_PT, color: MUTED, after: 0.3 });
const lead = (label, rest) => [{ text: label + " ", options: { bold: true } }, { text: rest }];

// ---- column 1
heading(0, "1  Introduction");
para(0, "Comprehensive genomic profiling (CGP) underpins treatment selection in NSCLC, yet panel content varies widely across institutions and health-care systems. Smaller targeted panels reduce cost and turnaround time but leave part of the tumour genome unmeasured.");
para(0, lead("Objective.", "To learn the conditional distribution of alterations in genes absent from a targeted panel given the genes it measures, to benchmark it against simple statistical baselines, and to identify which signals make the missing genes predictable."), { after: 0.35 });
heading(0, "2  Study design");
{
  const y = cur[0], h = 0.62, w1 = CW * 0.675;
  rect(colX(0), y, w1, h, { fill: { color: BLUE } });
  txt("IMPACT341 · 341 genes (input)", { x: colX(0), y, w: w1, h, fontSize: 15, bold: true, color: "FFFFFF", align: "center", valign: "middle" });
  rect(colX(0) + w1, y, CW - w1, h, { fill: { color: PEACH }, line: { color: ORANGE, width: 1.5 } });
  txt("164 genes (target)", { x: colX(0) + w1, y, w: CW - w1, h, fontSize: 15, bold: true, color: "7A2E0B", align: "center", valign: "middle" });
  cur[0] += h + 0.12;
}
caption(0, "Figure 1.", "Task definition. IMPACT341 ⊂ IMPACT505; the 164 genes present only in IMPACT505 are masked from the input and predicted.");
caption(0, "Table 1.", "Cohort and target characteristics (MSK-CHORD).");
cur[0] -= 0.18;
{
  const rows = [["Patients, NSCLC, sequenced on IMPACT505", "2,226"], ["Input genes (IMPACT341)", "341"],
    ["Target genes (IMPACT505 \\ IMPACT341)", "164"], ["Altered target gene–patient pairs", "1.21%"],
    ["Patients with ≥1 altered target gene", "[ ]%"], ["Split (patient level): train / val / test", "70 / 15 / 15% [confirm]"]];
  const tbl = rows.map(([a, b]) => [{ text: a }, { text: b, options: { align: "right", color: b.includes("[") ? PH : INK } }]);
  const rowH = 0.42;
  s.addTable(tbl, { x: colX(0), y: cur[0], w: CW, colW: [CW * 0.62, CW * 0.38], fontFace: BODY, fontSize: 16, color: INK, rowH, margin: [0.04, 0, 0.04, 0],
    border: { type: "solid", pt: 0.75, color: RULE } });
  hline(colX(0), cur[0], CW, INK, 1.5);
  hline(colX(0), cur[0] + rowH * rows.length, CW, INK, 1.5);
  cur[0] += rowH * rows.length + 0.3;
}
para(0, lead("Alteration encoding.", "Target: one binary event per gene and patient (non-synonymous mutation, amplification or deep deletion; [state VUS and structural-variant handling]). Input: separate mutation, amplification and deletion indicators for the 341 assayed genes. One sample per patient. Genes not covered by a sample's panel are treated as missing, never as wild type."));

// ---- column 2
heading(1, "3  Methods");
para(1, [{ text: "3.1 Problem formulation. ", options: { bold: true } },
  { text: "Given the observed IMPACT341 profile c, we learn the conditional distribution p(x" }, { text: "1", options: { subscript: true } },
  { text: " | c) over the 164 target genes. Binary targets are embedded as x" }, { text: "1", options: { subscript: true } },
  { text: " ∈ {−1,+1}" }, { text: "164", options: { superscript: true } },
  { text: " (continuous relaxation); generated profiles are binarised by sign. Data were split by patient into 70% training, 15% validation (all model and hyper-parameter selection) and 15% test, evaluated once." }]);
para(1, [{ text: "3.2 Conditional flow matching. ", options: { bold: true } },
  { text: "A velocity field v" }, { text: "θ", options: { subscript: true } },
  { text: " ([architecture]) is regressed onto the straight-line path between Gaussian noise and data:" }], { after: 0.18 });
{
  const y = cur[1], h = 1.05;
  rect(colX(1), y, CW, h, { fill: { color: TINT } });
  const sub = (t) => ({ text: t, options: { subscript: true } });
  txt([{ text: "x" }, sub("t"), { text: " = (1 − t) x" }, sub("0"), { text: " + t x" }, sub("1"), { text: ",    x" }, sub("0"), { text: " ~ 𝒩(0, I),    t ~ 𝒰(0, 1)", options: { breakLine: true } },
    { text: "ℒ(θ) = 𝔼 ‖ v" }, sub("θ"), { text: "(x" }, sub("t"), { text: ", t | c) − (x" }, sub("1"), { text: " − x" }, sub("0"), { text: ") ‖²" }],
    { x: colX(1), y: y + 0.12, w: CW, h: h - 0.24, fontFace: HEAD, fontSize: 17, align: "center", valign: "middle", lineSpacingMultiple: 1.3 });
  cur[1] += h + 0.3;
}
{
  const y = cur[1], h = 0.75, aw = 0.42;
  const bw = (CW - 2 * aw) / 3.3;
  const sub = (t) => ({ text: t, options: { subscript: true } });
  let x = colX(1);
  rect(x, y, bw, h, { fill: { color: "FFFFFF" }, line: { color: INK, width: 1.5 } });
  txt([{ text: "x" }, sub("0"), { text: " ~ 𝒩(0, I)" }], { x, y, w: bw, h, fontSize: 14, align: "center", valign: "middle" });
  x += bw; txt("→", { x, y, w: aw, h, fontSize: 24, align: "center", valign: "middle" }); x += aw;
  rect(x, y, bw * 1.3, h, { fill: { color: INK } });
  txt([{ text: "dx/dt = v" }, sub("θ"), { text: "(x" }, sub("t"), { text: ", t | c)" }], { x, y, w: bw * 1.3, h, fontSize: 14, color: "FFFFFF", align: "center", valign: "middle" });
  x += bw * 1.3; txt("→", { x, y, w: aw, h, fontSize: 24, align: "center", valign: "middle" }); x += aw;
  rect(x, y, bw, h, { fill: { color: PEACH }, line: { color: ORANGE, width: 1.5 } });
  txt([{ text: "x̂" }, sub("1"), { text: " ∈ ℝ" }, { text: "164", options: { superscript: true } }], { x, y, w: bw, h, fontSize: 14, align: "center", valign: "middle" });
  cur[1] += h + 0.15;
  const cw = CW * 0.72;
  rect(colX(1) + (CW - cw) / 2, cur[1], cw, 0.5, { fill: { color: BLUE } });
  txt("conditioning c: observed IMPACT341 profile", { x: colX(1) + (CW - cw) / 2, y: cur[1], w: cw, h: 0.5, fontSize: 14, color: "FFFFFF", align: "center", valign: "middle" });
  cur[1] += 0.62;
}
caption(1, "Figure 2.", "Sampling: the learned ODE, integrated from t = 0 to 1 ([solver, N steps]), transports noise to a completed 164-gene profile conditioned on the observed panel.");
para(1, [{ text: "3.3 Probability read-out. ", options: { bold: true } },
  { text: "At t = 0 the path is independent of x₁, so the optimal field satisfies v*(x₀, 0 | c) = 𝔼[x₁ | c] − x₀. Per-gene probabilities p̂ = ½(1 + x₀ + vθ(x₀, 0 | c)), averaged over K noise draws, equal the infinite-sample Monte Carlo estimate without its 1/S resolution limit, which at ~1% prevalence ties most pairs at 0. [state read-out used]" }]);
para(1, [{ text: "3.4 Evaluation. ", options: { bold: true } },
  { text: "Discrimination: AUROC pooled over gene–patient pairs (primary) and per gene (genes with ≥5 test events), where a prevalence-only predictor scores exactly 0.50. Class imbalance: AUPRC against the prevalence of 0.012. Calibration: slope, intercept, observed:expected (O:E) ratio and Brier skill score. Intended-use operating point (EBAI class B): sensitivity, specificity, PPV, NPV and LR± for ≥1 altered target gene. Joint fidelity, the property that justifies a generative model: energy score of sampled profiles versus independent Bernoulli draws from the same marginals. Comparators on identical splits: prevalence; burden + locus (3 burden counts and copy-number state of the nearest assayed gene); L2 logistic regression. 95% CIs and paired differences by patient-level bootstrap." }]);
para(1, [{ text: "3.5 External replicate. ", options: { bold: true } },
  { text: "MSK-IMPACT 2017 (cBioPortal, ODbL): IMPACT341 → 69 IMPACT410-only genes in 1,215 NSCLC patients; 3 × 5-fold patient-level cross-validation, AUROC computed within folds." }]);

// ---- column 3
heading(2, "4  Results");
para(2, lead("4.1 Primary cohort.", "Across architectures and training paradigms, the flow model reached a pooled test AUROC of 0.77–0.79, above the prevalence-only baseline in every variant (Table 2)."));
caption(2, "Table 2.", "MSK-CHORD test set: AUROC pooled and per gene, and AUPRC (chance level = prevalence, 0.012); point estimate (95% CI).");
cur[2] -= 0.18;
{
  const hdr = ["Model", "Pooled", "Per gene", "AUPRC"].map((t, i) => ({ text: t, options: { bold: true, align: i ? "right" : "left" } }));
  const cell = (v, bold) => ({ text: v, options: { align: "right", bold, color: v.includes("[") ? PH : INK } });
  const r = (a, b, c, d, bold) => [{ text: a, options: { bold } }, cell(b, bold), cell(c, bold), cell(d, bold)];
  const rows = [hdr, r("Prevalence only", "[ ]", "0.50", "[ ]"), r("Burden + locus", "[ ]", "[ ]", "[ ]"), r("L2 logistic regression", "[ ]", "[ ]", "[ ]"),
    r("Flow matching", "0.77–0.79", "[ ]", "[ ]", true)];
  const rowH = 0.46;
  s.addTable(rows, { x: colX(2), y: cur[2], w: CW, colW: [CW * 0.4, CW * 0.2, CW * 0.22, CW * 0.18], fontFace: BODY, fontSize: 15, color: INK, rowH,
    margin: [0.05, 0, 0.05, 0], border: { type: "solid", pt: 0.75, color: RULE } });
  hline(colX(2), cur[2], CW, INK, 1.5);
  hline(colX(2), cur[2] + rowH, CW, INK, 1.25);
  hline(colX(2), cur[2] + rowH * rows.length, CW, INK, 1.5);
  cur[2] += rowH * rows.length + 0.25;
}
para(2, [{ text: "Calibration and joint fidelity: ", options: { bold: true } }, { text: "Brier skill " }, { text: "[ ]", options: { color: PH } },
  { text: "; energy score, flow samples vs independent draws " }, { text: "[ ] vs [ ]", options: { color: PH } }, { text: "." }], { after: 0.3 });
para(2, lead("4.2 Benchmark on public data.", "Pooled AUROC compares pairs across genes, so ranking genes by training frequency alone scores 0.715. Per gene, a 7-feature model matches 1,026-feature logistic regression (0.760 vs 0.728), and pan-cancer training adds +0.039 (95% CI 0.024–0.057; Figure 3)."));
{
  // dot plot with 95% CI; axis 0.45-0.90
  const labW = 2.45, px0 = colX(2) + labW, pw = CW - labW - 0.15;
  const X = (v) => px0 + (v - 0.45) / 0.45 * pw;
  let y = cur[2];
  s.addShape(pres.shapes.OVAL, { x: colX(2), y: y + 0.06, w: 0.16, h: 0.16, fill: { color: BLUE } });
  txt("Pooled AUROC", { x: colX(2) + 0.24, y, w: 2.2, h: 0.3, fontSize: 13 });
  rect(colX(2) + 2.5, y + 0.07, 0.14, 0.14, { fill: { color: ORANGE } });
  txt("Per-gene AUROC", { x: colX(2) + 2.72, y, w: 2.3, h: 0.3, fontSize: 13 });
  txt("lines: 95% CI", { x: colX(2) + 5.1, y, w: 2.3, h: 0.3, fontSize: 13, color: MUTED });
  y += 0.45;
  const rows = [["Prevalence only", 0.715, 0.691, 0.735, 0.500, null, null], ["Burden + locus", 0.760, 0.735, 0.779, 0.760, 0.736, 0.785],
    ["L2 logistic regression", 0.778, 0.754, 0.796, 0.728, 0.705, 0.753], ["Pan-cancer logistic", 0.808, 0.791, 0.829, 0.767, 0.741, 0.790]];
  const rh = 0.74;
  for (const [lab, p, plo, phi, g, glo, ghi] of rows) {
    txt(lab, { x: colX(2), y, w: labW, h: rh, fontSize: 16, valign: "middle" });
    const yp = y + 0.22, yg = y + 0.52;
    hline(X(plo), yp, X(phi) - X(plo), BLUE, 2);
    s.addShape(pres.shapes.OVAL, { x: X(p) - 0.085, y: yp - 0.085, w: 0.17, h: 0.17, fill: { color: BLUE } });
    txt(p.toFixed(3), { x: X(phi) + 0.06, y: yp - 0.12, w: 0.7, h: 0.24, fontSize: 11.5 });
    if (glo !== null) hline(X(glo), yg, X(ghi) - X(glo), ORANGE, 2);
    rect(X(g) - 0.07, yg - 0.07, 0.14, 0.14, { fill: { color: ORANGE } });
    txt(g.toFixed(3), { x: (ghi ? X(ghi) : X(g) + 0.07) + 0.06, y: yg - 0.12, w: 0.7, h: 0.24, fontSize: 11.5 });
    hline(colX(2), y + rh, CW, "E0E4E8", 0.75);
    y += rh;
  }
  for (const v of [0.5, 0.6, 0.7, 0.8, 0.9]) {
    s.addShape(pres.shapes.LINE, { x: X(v), y: cur[2] + 0.45, w: 0, h: rh * rows.length, line: { color: "E0E4E8", width: 0.75, dashType: "dash" } });
    txt(v.toFixed(2), { x: X(v) - 0.3, y: y + 0.05, w: 0.6, h: 0.25, fontSize: 11.5, color: MUTED, align: "center" });
  }
  cur[2] = y + 0.4;
}
caption(2, "Figure 3.", "Replicate (n = 1,215): AUROC with patient-bootstrap 95% CI. Pan-cancer: trained on 7,773 patients with cancer type as covariate.");

para(2, lead("4.3 Simulated versus real input.", "In 167 patients sequenced on both panels, taking the input from the separate IMPACT341 assay instead of masking the IMPACT410 sample lowered pooled AUROC from 0.84 to 0.70 and per-gene AUROC from 0.80 to 0.61 (pan-cancer logistic regression). The paired samples also differ in specimen and time, so the gap combines assay shift and tumour heterogeneity."), { after: 0.3 });
// ---- column 4
hline(colX(3), cur[3], CW, INK, 2.25);
cur[3] += 0.15;
para(3, lead("4.4 Sources of signal.", "Amplifications were highly discriminable (AUROC 0.95), explained largely by co-amplification with neighbouring assayed genes (NFKBIA with NKX2-1 in 39/39 cases). Mutations reached 0.73, no better than three mutational-burden counts alone (Figure 4)."));
function bars(c, labels, values, colors, h) {
  s.addChart(pres.charts.BAR, [{ name: "AUROC", labels, values }], {
    x: colX(c), y: cur[c], w: CW, h, barDir: "bar", chartColors: colors, catAxisOrientation: "maxMin",
    valAxisMinVal: 0.5, valAxisMaxVal: 1.0, valAxisMajorUnit: 0.1, valAxisLabelFormatCode: "0.0#", showValue: true,
    dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00", dataLabelFontSize: 15, dataLabelColor: INK,
    catAxisLabelFontSize: 15, valAxisLabelFontSize: 12, catAxisLabelColor: INK, valAxisLabelColor: MUTED,
    catAxisLabelFontFace: BODY, valAxisLabelFontFace: BODY, valGridLine: { color: "E0E4E8", size: 0.75 }, catGridLine: { style: "none" },
    showLegend: false, barGapWidthPct: 45,
  });
  cur[c] += h + 0.08;
}
bars(3, ["Amplifications (134 events)", "Mutations (646 events)", "Mutations, burden only", "Deep deletions (18 events)"],
  [0.949, 0.728, 0.726, 0.711], [BLUE, BLUE, LIGHT_BLUE, BLUE], 2.25);
caption(3, "Figure 4.", "Replicate: per-gene AUROC by event type (positives-weighted mean; axis origin 0.50), pan-cancer logistic regression.");
heading(3, "5  EBAI assessment");
{
  const rows = [
    ["Ground truth", "met", "IMPACT505 NGS on the same sample"],
    ["Discrimination", "met", "Pooled AUROC 0.77–0.79; per gene [ ]"],
    ["Operating point", "partial", "Replicate: Se 0.90, NPV 0.86, LR− 0.22; cohort [ ]"],
    ["Calibration", "partial", "Replicate: slope 0.97, O:E 1.08; cohort [ ]"],
    ["Independent cohort", "open", "Single institution; non-MSK validation needed"],
    ["Assay shift", "partial", "Real IMPACT341 input: AUROC 0.84 → 0.70"],
    ["Fairness", "open", "Sex, ancestry, smoking, histology subgroups"],
    ["Explainability", "met", "Signal = copy-number locus + mutational burden"],
  ];
  const ST = { met: ["Met", BLUE, "FFFFFF", null], partial: ["Partial", PEACH, "7A2E0B", ORANGE], open: ["Not yet", "FFFFFF", "3F4B57", "6B7682"] };
  const c1 = 2.2, c2 = 1.1, rh = 0.37, fsz = 13;
  let y = cur[3];
  rect(colX(3), y, CW, 0.46, { fill: { color: INK } });
  txt("EBAI class B · indirect measure of existing biomarkers · use: pre-screening", { x: colX(3) + 0.12, y, w: CW - 0.24, h: 0.46, fontSize: 13, bold: true, color: "FFFFFF", valign: "middle" });
  y += 0.5;
  for (const [req, st, ev] of rows) {
    const [lab, fill, fg, ln] = ST[st];
    txt(req, { x: colX(3), y, w: c1, h: rh, fontSize: fsz, valign: "middle", bold: true });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: colX(3) + c1, y: y + 0.06, w: c2 - 0.12, h: rh - 0.12, rectRadius: 0.05,
      fill: { color: fill }, line: ln ? { color: ln, width: 1 } : { color: fill, width: 0 } });
    txt(lab, { x: colX(3) + c1, y: y + 0.06, w: c2 - 0.12, h: rh - 0.12, fontSize: 11.5, bold: true, color: fg, align: "center", valign: "middle" });
    const runs = ev.split(/(\[ \])/).filter(Boolean).map((t) => ({ text: t, options: t === "[ ]" ? { color: PH } : {} }));
    txt(runs, { x: colX(3) + c1 + c2, y, w: CW - c1 - c2, h: rh, fontSize: fsz, valign: "middle" });
    y += rh; hline(colX(3), y, CW, "E0E4E8", 0.75);
  }
  hline(colX(3), y, CW, INK, 1.5);
  cur[3] = y + 0.1;
}
caption(3, "Figure 5.", "Assessment against the ESMO EBAI class B requirements. Replicate values from MSK-IMPACT 2017; [ ] to be computed on MSK-CHORD. Se, sensitivity for ≥1 altered target gene.");
heading(3, "6  Discussion");
{
  const items = ["A targeted panel carries predictive information on unassayed genes; per-gene AUROC and simple baselines, not pooled AUROC alone, measure how much.",
    "The signal is mainly copy-number co-location and mutational burden; a generative model must add joint fidelity to justify its complexity.",
    "Limitations: masked-panel evaluation is an upper bound; single institution and split; fairness and actionable genes not yet evaluated.",
    "As an EBAI class B pre-screening tool, negatives still require confirmatory CGP (NPV 0.86 at 90% sensitivity)."];
  const runs = items.map((t, i) => {
    const o = { bullet: true, paraSpaceAfter: 6 };
    if (i < items.length - 1) o.breakLine = true;
    return [{ text: t, options: o }];
  }).flat();
  const h = items.reduce((a, t) => a + est(t, BODY_PT, CW - 0.3), 0) + 0.3;
  txt(runs, { x: colX(3), y: cur[3], w: CW, h, fontSize: BODY_PT });
  cur[3] += h;
}

// ---------------------------------------------------------------- footer
hline(M, FOOT_Y, W - 2 * M, INK, 1.5);
const fy = FOOT_Y + 0.15, fs = 12.5, qr = 1.25;
const fw = W - 2 * M - qr - 3 * 0.42;
const fx = [M, M + fw * 0.5 + 0.42, M + fw * 0.75 + 0.84];
txt([{ text: "References", options: { bold: true, breakLine: true } },
  { text: "1. Jee J, et al. Automated real-world data integration improves cancer outcome prediction. Nature 2024;636:728–36.", options: { breakLine: true } },
  { text: "2. Zehir A, et al. Mutational landscape of metastatic cancer revealed from prospective clinical sequencing of 10,000 patients. Nat Med 2017;23:703–13.", options: { breakLine: true } },
  { text: "3. Lipman Y, et al. Flow matching for generative modeling. ICLR 2023.   4. Collins GS, et al. TRIPOD+AI statement. BMJ 2024;385:e078378.", options: { breakLine: true } },
  { text: "5. Aldea M, et al. ESMO basic requirements for AI-based biomarkers in oncology (EBAI). Ann Oncol 2026;37:414–25." }],
  { x: fx[0], y: fy, w: fw * 0.5, h: 1.3, fontSize: fs, color: "2C3A47" });
txt([{ text: "Data and code", options: { bold: true, breakLine: true } }, { text: "MSK-CHORD and msk_impact_2017 via cBioPortal. Code: " }, { text: "[repository link]", options: { color: PH } }],
  { x: fx[1], y: fy, w: fw * 0.25, h: 1.3, fontSize: fs, color: "2C3A47" });
txt([{ text: "Disclosures · Contact", options: { bold: true, breakLine: true } }, { text: "[Conflict-of-interest statement]", options: { color: PH, breakLine: true } },
  { text: "[Corresponding author e-mail]", options: { color: PH } }],
  { x: fx[2], y: fy, w: fw * 0.25, h: 1.3, fontSize: fs, color: "2C3A47" });
rect(W - M - qr, fy, qr, qr, { fill: { color: "FFFFFF" }, line: { color: "6B7682", width: 1.25, dashType: "dash" } });
txt("[QR code]", { x: W - M - qr, y: fy, w: qr, h: qr, fontSize: 12, color: MUTED, align: "center", valign: "middle" });

console.log("column bottoms (in):", cur.map((v) => v.toFixed(2)), "footer at", FOOT_Y.toFixed(2));
pres.writeFile({ fileName: "ESMO_P305_poster.pptx" }).then((f) => console.log("wrote", f));
