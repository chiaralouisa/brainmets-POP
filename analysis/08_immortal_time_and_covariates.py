import os, re, warnings, numpy as np, pandas as pd
warnings.filterwarnings('ignore')
from scipy.stats import fisher_exact
from statsmodels.duration.hazard_regression import PHReg
from statsmodels.duration.survfunc import SurvfuncRight, survdiff
df = pd.read_excel(os.environ.get('COHORT_XLSX','data/20260719cohort.xlsx'))
d='Difference between Lung Ca. and Brain Met in days'
df['event']=(df['Is Deceased'].astype(str)=='True').astype(int)
df['os']=df['Overall survival'].astype(float)
df['mBM']=(df.group=='verl-mBM').astype(int)
df['t2bm']=df[d]/30.44
df['os_bm']=(df.os-df.t2bm).clip(lower=1/30.44)

print("="*74); print("CNS-DIRECTED THERAPY: WHAT IS RECOVERABLE FROM THE FILE")
print("="*74)
txt=(df['therapy'].fillna('')+' '+df['Medication Administrations>Multimodal Therapy Line>Summary'].fillna(''))
df['any_rt']=txt.str.contains('adio',case=False).astype(int)     # Radio*/radiotherapy
df['any_surg']=txt.str.contains('urgery',case=False).astype(int)
for lab,c in [('any radiotherapy (target unspecified)','any_rt'),('any surgery (site unspecified)','any_surg')]:
    a=df[df.mBM==0][c].sum(); b=df[df.mBM==1][c].sum()
    p=fisher_exact([[a,88-a],[b,28-b]])[1]
    print(f"  {lab:38s} sBM {a:2d}/88 ({100*a/88:4.1f}%)  mBM {b:2d}/28 ({100*b/28:4.1f}%)  p={p:.2f}")
print("  Neither field names the irradiated site or the operated organ, so SRS, WBRT and")
print("  neurosurgical resection cannot be distinguished from thoracic RT or lung surgery.")
print("  -> CNS-directed therapy is NOT derivable from this dataset; it must be abstracted.")

print("\n"+"="*74); print("IMMORTAL TIME: TIME-DEPENDENT COX (counting process)")
print("="*74)
rows=[]
for i,r in df.iterrows():
    if r.mBM==0:
        rows.append((i,0.0,max(r.os,1/30.44),r.event,1))
    else:
        t=min(r.t2bm,r.os)
        if t>0: rows.append((i,0.0,t,0,0))          # BM-free interval
        stop=max(r.os,t+1/30.44)
        rows.append((i,t,stop,r.event,1))            # after BM onset
td=pd.DataFrame(rows,columns=['id','start','stop','event','bm'])
m=PHReg(td.stop,td[['bm']],status=td.event,entry=td.start).fit()
print(f"  BM present (time-dependent)   HR={np.exp(m.params[0]):.2f} "
      f"({np.exp(m.conf_int()[0][0]):.2f}-{np.exp(m.conf_int()[0][1]):.2f}) p={m.pvalues[0]:.3g}")
print(f"  intervals={len(td)} for {df.shape[0]} patients; events={int(td.event.sum())}")

print("\n  Comparison of the three handlings of the same question:")
m1=PHReg(df.os,df[['mBM']],status=df.event).fit()
LM=4.0; lm=df[df.os>LM].copy(); lm['t']=lm.os-LM
m2=PHReg(lm.t,lm[['mBM']],status=lm.event).fit()
m3=PHReg(df.os_bm,df[['mBM']],status=df.event).fit()
for lab,mm in [('naive, OS from primary dx',m1),('landmark 4 mo',m2),('OS from BM dx',m3)]:
    print(f"    {lab:28s} HR={np.exp(mm.params[0]):.2f} "
          f"({np.exp(mm.conf_int()[0][0]):.2f}-{np.exp(mm.conf_int()[0][1]):.2f}) p={mm.pvalues[0]:.3g}")

print("\n"+"="*74); print("COMPETING RISKS FOR TIME-TO-BM")
print("="*74)
print("  Not estimable in this cohort: BM is an inclusion criterion, so cumulative")
print("  incidence is 100% by construction and there are no competing events to model.")
print("  A Fine-Gray model requires the BM-free comparator arm as denominator.")

print("\n"+"="*74); print("MULTIVARIABLE COX, OS FROM BM DIAGNOSIS")
print("="*74)
def losses(s):
    out=set()
    for it in str(s).split(';'):
        q=it.strip().split(' ',1)
        if len(q)>1 and q[1].strip() in ('loss','deletion'): out.add(q[0])
    return out
L=df['Pathogenic variants (list)'].apply(losses)
df['co9p']=L.apply(lambda s:{'CDKN2A','CDKN2B','MTAP'}<=s).astype(int)
G=df['Pathogenic variants (list)'].apply(lambda s:{x.strip().split(' ')[0] for x in str(s).split(';') if x.strip()})
df['tp53']=G.apply(lambda s:'TP53' in s).astype(int)
df['male']=(df['Gender>Text']=='Male').astype(int)
df['adeno']=(df['Primary Cancers>Histology>Text']=='Adenocarcinoma, NOS').astype(int)
X=df[['mBM','co9p','tp53','Age','male','adeno','any_rt']].rename(columns={'Age':'age','any_rt':'radiotherapy'})
m=PHReg(df.os_bm,X,status=df.event).fit()
print(f"  {'covariate':14s} {'HR':>6s}  {'95% CI':>16s}   p")
for i,n_ in enumerate(X.columns):
    print(f"  {n_:14s} {np.exp(m.params[i]):6.2f}  "
          f"{np.exp(m.conf_int()[i][0]):6.2f}-{np.exp(m.conf_int()[i][1]):<6.2f}  {m.pvalues[i]:.3g}")

