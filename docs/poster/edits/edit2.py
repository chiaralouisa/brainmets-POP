import re
exec(open('edit_poster.py').read().split('# ---- text')[0])   # reuse helpers; reloads current XML
def shift(x,sid,dy):
    a,b=span(x,sid); sp=x[a:b]; (ox,oy,ocx,ocy),m=geom(sp)
    sp=sp[:m.start()]+'<a:off x="%d" y="%d"/><a:ext cx="%d" cy="%d"'%(ox,oy+int(dy*E),ocx,ocy)+sp[m.end():]; return x[:a]+sp+x[b:]
def setsz(x,sid,sz):
    a,b=span(x,sid); sp=x[a:b]; sp=re.sub(r'sz="\d+"','sz="%d"'%sz,sp); return x[:a]+sp+x[b:]
for sid in ['25','27','241']: x=shift(x,sid,0.55)
for sid,t in {'140':'Amplifications (n = 134)','137':'Mutations (n = 646)','134':'Mutations, burden only','131':'Deep deletions (n = 18)'}.items():
    x=settext(x,sid,t); x=setsz(x,sid,1150)
x=settext(x,'228','Study and clinical use')
x=set_paras(x,'229',[
 [("Evaluation. ",True),("Single 15% test split; pooled AUROC without CI; no per-gene AUROC, AUPRC, calibration or joint-fidelity metric; architecture variants unspecified; split stated as 75/15/15%.",False)],
 [("Validity. ",True),("Simulated masking of one IMPACT505 assay; single institution; no independent or real paired-assay cohort. Replicate values (Table 2, Figures 3–4) come from logistic regression on MSK data, not the flow model.",False)],
 [("Actionability. ",True),("Binary gene-level events carry no variant level (e.g. KRAS G12C) and no ESCAT tier; fusions (ALK, ROS1, RET, NTRK, MET ex14), the most actionable NSCLC class, are not modelled. No treatment decision can rest on a prediction.",False)],
 [("Confirmation burden. ",True),("At ~1% prevalence most predicted positives are false (replicate PPV 0.02–0.05) and NPV 0.86 still misses targets; every result needs confirmatory CGP, with its tissue, cost and delay.",False)],
 [("Clinical utility. ",True),("No evidence that triage changes time to treatment, therapy choice or survival; no decision-curve analysis or prospective silent trial.",False)],
 [("Population and assay. ",True),("Single tertiary centre; stage, treatment line, prior TKI exposure, histology, smoking, purity and primary vs metastatic site not stratified; matched-normal pipeline differs from tumour-only external panels.",False)],
 [("Regulatory. ",True),("Not CE-IVD or FDA cleared; would be an in-house IVDR device with no monitoring plan.",False)]],size=1450)
x=setgeom(x,'229',cy=int(4.5*E))
for sid in ['231','232']: x=shift(x,sid,0.3)
open(P,'w',encoding='utf8').write(x); print('ok')
