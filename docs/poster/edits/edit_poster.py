import re, html
E=914400
P='user_unpacked/ppt/slides/slide1.xml'
x=open(P,encoding='utf8').read()
def span(x,sid):
    for m in re.finditer(r'<p:(sp|cxnSp)>.*?</p:\1>', x, re.S):
        if re.search(r'<p:cNvPr id="%s" '%sid, m.group(0)): return m.start(), m.end()
    raise KeyError(sid)
def set_paras(x, sid, paras, size=None):
    a,b=span(x,sid); sp=x[a:b]
    tb=re.search(r'<p:txBody>(.*?)</p:txBody>',sp,re.S); body=tb.group(1)
    bodyPr=re.search(r'<a:bodyPr[^>]*/>|<a:bodyPr[^>]*>.*?</a:bodyPr>',body,re.S).group(0)
    lst=re.search(r'<a:lstStyle/>|<a:lstStyle>.*?</a:lstStyle>',body,re.S); lst=lst.group(0) if lst else '<a:lstStyle/>'
    p0=re.search(r'<a:p>.*?</a:p>',body,re.S).group(0)
    pPr=re.search(r'<a:pPr[^>]*/>|<a:pPr[^>]*>.*?</a:pPr>',p0,re.S); pPr=pPr.group(0) if pPr else ''
    rPr=re.search(r'<a:rPr[^>]*/>|<a:rPr[^>]*>.*?</a:rPr>',p0,re.S).group(0)
    rPr=re.sub(r'\sb="[01]"','',rPr)
    if size: rPr=re.sub(r'sz="\d+"','sz="%d"'%size,rPr) if 'sz=' in rPr else rPr.replace('<a:rPr','<a:rPr sz="%d"'%size,1)
    run=lambda t,bd: '<a:r>%s<a:t>%s</a:t></a:r>'%(rPr.replace('<a:rPr','<a:rPr b="1"',1) if bd else rPr, html.escape(t,quote=False))
    out=''.join('<a:p>%s%s</a:p>'%(pPr,''.join(run(t,bd) for t,bd in para)) for para in paras)
    return x[:a]+sp[:tb.start()]+'<p:txBody>'+bodyPr+lst+out+'</p:txBody>'+sp[tb.end():]+x[b:]
def geom(sp):
    m=re.search(r'<a:off x="(-?\d+)" y="(-?\d+)"/><a:ext cx="(\d+)" cy="(\d+)"',sp); return [int(v) for v in m.groups()], m
def setgeom(x,sid,fx=None,fcx=None,cy=None):
    a,b=span(x,sid); sp=x[a:b]; (ox,oy,ocx,ocy),m=geom(sp)
    sp=sp[:m.start()]+'<a:off x="%d" y="%d"/><a:ext cx="%d" cy="%d"'%(fx(ox) if fx else ox,oy,fcx(ocx) if fcx else ocx,cy or ocy)+sp[m.end():]
    return x[:a]+sp+x[b:]
def settext(x,sid,text,algn=None):
    a,b=span(x,sid); sp=x[a:b]
    sp=re.sub(r'<a:t>[^<]*</a:t>','<a:t>%s</a:t>'%html.escape(text,quote=False),sp,count=1)
    if algn: sp=re.sub(r'<a:pPr([^>]*?)(/?)>',lambda m:'<a:pPr algn="%s"%s%s>'%(algn,re.sub(r' algn="\w+"','',m.group(1)),m.group(2)),sp,count=1)
    return x[:a]+sp+x[b:]

# ---- text
x=set_paras(x,'17',[[("Predicting Comprehensive Genomic Profiles from Targeted Panels with Generative Models",True)]],size=6000)
x=set_paras(x,'24',[
 [("Comprehensive genomic profiling (CGP) guides treatment in NSCLC, but panel content, cost and turnaround time differ widely between institutions, and smaller targeted panels leave part of the tumour genome unmeasured.",False)],
 [("EBAI class B. ",True),("Under the ESMO basic requirements for AI-based biomarkers, a model that predicts an established biomarker from an input other than the gold-standard test (here, the smaller panel itself) is class B: higher risk than class A, intended to enrich a population for confirmatory testing or, only with a very high NPV, to rule it out, never to replace the genomic test.",False)]])
x=set_paras(x,'241',[
 [("NSCLC cases from the MSK-CHORD cohort with MSK-IMPACT sequencing were analysed.",False)],
 [("The completion task: predict the larger IMPACT505 panel (505 genes) from the smaller IMPACT341 panel (341 genes), evaluated on the 164 genes present in IMPACT505 but not in IMPACT341.",False)]])
x=set_paras(x,'38',[
 [("Alteration encoding. ",True),("Gene alterations were encoded as binary events comprising non-synonymous mutations and copy-number alterations.",False)],
 [("Target: one binary event per gene and patient (any non-synonymous mutation, including variants of unknown significance, amplification or deep deletion; fusions and other structural variants not modelled).",False)],
 [("Input: separate mutation, amplification and deletion indicators for the 341 assayed genes. One sample per patient. Genes not covered by a sample\u2019s panel are treated as missing, never as wild type.",False)]],size=1550)
x=set_paras(x,'41',[[("3.1 Problem formulation. ",True),("Given the observed IMPACT341 profile c, we learn the conditional distribution p(x\u2081 | c) over the 164 target genes. Binary targets are embedded as x\u2081 \u2208 {\u22121,+1}\u00b9\u2076\u2074 (continuous relaxation); generated profiles are binarised by sign. Data were split by patient into 70% training, 15% validation (all model and hyperparameter selection) and 15% test, evaluated once.",False)]])
x=set_paras(x,'229',[
 [("Evaluation. ",True),("Single 15% test split; pooled AUROC without CI; no per-gene AUROC, AUPRC or calibration; split stated as 75/15/15%.",False)],
 [("Validity. ",True),("Simulated masking of one IMPACT505 assay; single institution; no independent or real paired-assay cohort; replicate values (Table 2, Figures 3\u20134) come from logistic regression on MSK data, not from the flow model.",False)],
 [("Generative claim. ",True),("No joint-fidelity metric; architecture variants unspecified.",False)],
 [("Actionability. ",True),("Binary gene-level events carry no variant level (e.g. KRAS G12C) and no ESCAT tier; fusions (ALK, ROS1, RET, NTRK, MET ex14), the most actionable NSCLC class, are not modelled. No treatment decision can rest on a predicted alteration.",False)],
 [("Confirmation burden. ",True),("At ~1% prevalence most predicted positives are false (replicate pair-level PPV 0.02\u20130.05), and NPV 0.86 still misses targets; every result requires confirmatory CGP, with its tissue, cost and delay.",False)],
 [("Clinical utility. ",True),("No evidence that triage changes time to treatment, therapy choice or survival; no decision-curve analysis or prospective silent trial.",False)],
 [("Population and assay. ",True),("Single tertiary centre; stage, line of therapy, prior TKI exposure, histology, smoking, tumour purity and primary vs metastatic site not stratified; matched-normal MSK pipeline differs from tumour-only external panels.",False)],
 [("Regulatory. ",True),("Not CE-IVD or FDA cleared; would be an in-house IVDR device with no monitoring plan.",False)]])
# ---- Figure 4 geometry: axis 0.5 at 19.57in, 1.0 at 27.05in -> 21.35..27.05
x0,x1n,x1=19.57*E,21.35*E,27.05*E; k=(x1-x1n)/(x1-x0)
fx=lambda ox: int(x1n+(ox-x0)*k)
for sid in ['119','121','123','125','127','129','143']: x=setgeom(x,sid,fx=fx)
for sid in ['132','135','138','141']: x=setgeom(x,sid,fx=fx,fcx=lambda c:int(c*k))
for sid in ['133','136','139','142']: x=setgeom(x,sid,fx=fx)
for sid in ['120','122','124','126','128','130']: x=setgeom(x,sid,fx=lambda ox:int(x1n+(ox+0.295*E-x0)*k-0.295*E))
for sid,t in {'140':'Amplifications (134 events)','137':'Mutations (646 events)','134':'Mutations, burden counts only','131':'Deep deletions (18 events)'}.items():
    x=setgeom(x,sid,fx=lambda ox:int(18.99*E),fcx=lambda c:int(2.25*E)); x=settext(x,sid,t,algn='r')
# ---- boxes
x=setgeom(x,'24',cy=int(2.0*E)); x=setgeom(x,'229',cy=int(4.35*E)); x=setgeom(x,'38',cy=int(1.9*E))
open(P,'w',encoding='utf8').write(x); print('written')
