import os, re, warnings, numpy as np, pandas as pd
warnings.filterwarnings('ignore')
from scipy.stats import fisher_exact, mannwhitneyu
from statsmodels.stats.multitest import multipletests
from statsmodels.duration.survfunc import SurvfuncRight, survdiff
from statsmodels.duration.hazard_regression import PHReg
df = pd.read_excel(os.environ.get('COHORT_XLSX','data/20260719cohort.xlsx'))
pv='Pathogenic variants (list)'; d='Difference between Lung Ca. and Brain Met in days'
df['event']=(df['Is Deceased'].astype(str)=='True').astype(int)
df['os']=df['Overall survival'].astype(float)
df['mBM']=(df.group=='verl-mBM').astype(int)
df['t2bm']=df[d]/30.44
# Full cohort retained: all 116 patients are analysed as NSCLC, and post-BM survival is
# floored at one day so the single record whose BM date falls after last follow-up still
# contributes rather than being dropped.
df['os_bm']=(df.os-df.t2bm).clip(lower=1/30.44)

def med(t,e):
    sf=SurvfuncRight(t,e); i=np.where(sf.surv_prob<=0.5)[0]
    return sf.surv_times[i[0]] if len(i) else np.nan
def ci_med(t,e,B=2000,seed=0):
    rng=np.random.default_rng(seed); n=len(t); out=[]
    t=np.asarray(t); e=np.asarray(e)
    for _ in range(B):
        i=rng.integers(0,n,n)
        m=med(t[i],e[i])
        if not np.isnan(m): out.append(m)
    return np.percentile(out,[2.5,97.5])
def hr(t,e,x):
    m=PHReg(t,pd.DataFrame({'x':x}),status=e).fit()
    return np.exp(m.params[0]), np.exp(m.conf_int()[0][0]), np.exp(m.conf_int()[0][1]), m.pvalues[0]

print("="*72); print("PRIMARY ENDPOINT: OS FROM BM DIAGNOSIS")
s=df
for g,l in [(0,'sBM'),(1,'mBM')]:
    x=s[s.mBM==g]; m=med(x.os_bm,x.event); lo,hi=ci_med(x.os_bm.values,x.event.values)
    print(f"  {l}: n={len(x)} ev={x.event.sum()} median={m:.1f} (95%CI {lo:.1f}-{hi:.1f})")
chi,p=survdiff(s.os_bm,s.event,s.mBM); print(f"  log-rank chi2={chi:.2f} p={p:.2e}")
h=hr(s.os_bm,s.event,s.mBM); print(f"  HR(mBM vs sBM)={h[0]:.2f} (95%CI {h[1]:.2f}-{h[2]:.2f}) p={h[3]:.2e}")
# adjusted
s2=s.copy(); s2['age']=s2['Age']; s2['male']=(s2['Gender>Text']=='Male').astype(int)
s2['adeno']=(s2['Primary Cancers>Histology>Text']=='Adenocarcinoma, NOS').astype(int)
X=s2[['mBM','age','male','adeno']]
m=PHReg(s2.os_bm,X,status=s2.event).fit()
print(f"  ADJUSTED HR(mBM)={np.exp(m.params[0]):.2f} ({np.exp(m.conf_int()[0][0]):.2f}-{np.exp(m.conf_int()[0][1]):.2f}) p={m.pvalues[0]:.2e}")

print("\n"+"="*72); print("OS FROM PRIMARY DIAGNOSIS (secondary)")
for g,l in [(0,'sBM'),(1,'mBM')]:
    x=df[df.mBM==g]; print(f"  {l}: median={med(x.os,x.event):.1f}  mean={x.os.mean():.1f}±{x.os.std():.1f}")
chi,p=survdiff(df.os,df.event,df.mBM); print(f"  log-rank chi2={chi:.2f} p={p:.3f}")
h=hr(df.os,df.event,df.mBM); print(f"  HR={h[0]:.2f} ({h[1]:.2f}-{h[2]:.2f}) p={h[3]:.3f}")

print("\n"+"="*72); print("TIME TO BM")
for g,l in [(0,'sBM'),(1,'mBM')]:
    x=df[df.mBM==g][d]
    print(f"  {l}: mean={x.mean():.0f}±{x.std():.0f}  median={x.median():.0f} IQR[{x.quantile(.25):.0f}-{x.quantile(.75):.0f}] range[{x.min():.0f}-{x.max():.0f}]")

print("\n"+"="*72); print("9p21.3")
def losses(s):
    out=set()
    for it in str(s).split(';'):
        it=it.strip(); p=it.split(' ',1)
        if len(p)>1 and p[1].strip() in ('loss','deletion'): out.add(p[0])
    return out
df['loss']=df[pv].apply(losses)
df['co9p']=df['loss'].apply(lambda s:{'CDKN2A','CDKN2B','MTAP'}<=s).astype(int)
a=df[df.mBM==0].co9p.sum(); b=df[df.mBM==1].co9p.sum()
print(f"  triple co-deletion: all {df.co9p.sum()}/116 ({100*df.co9p.mean():.1f}%)  sBM {a}/88 ({100*a/88:.1f}%)  mBM {b}/28 ({100*b/28:.1f}%)  p={fisher_exact([[a,88-a],[b,28-b]])[1]:.2f}")
h=hr(df.os,df.event,df.co9p); print(f"  OS(primary dx) HR={h[0]:.2f} ({h[1]:.2f}-{h[2]:.2f}) p={h[3]:.2f}")
h=hr(df.os_bm,df.event,df.co9p); print(f"  OS(from BM)    HR={h[0]:.2f} ({h[1]:.2f}-{h[2]:.2f}) p={h[3]:.2f}")

print("\n"+"="*72); print("FDR ACROSS ALTERATIONS (gene+type, >=5 pts) — sBM vs mBM")
def alts(s):
    out=set()
    for it in str(s).split(';'):
        it=it.strip()
        if not it: continue
        p=it.split(' ',1); g=p[0]; r=p[1] if len(p)>1 else ''
        r=re.sub(r'p\.\([^)]*\)\s*','',r).strip()
        if g.startswith('NKX2'): g='NKX2-1'; r=r.split(' ',1)[-1] if r.startswith('1 ') else r
        out.add((g,r))
    return out
df['alt']=df[pv].apply(alts)
from collections import Counter
cnt=Counter()
for s in df.alt: cnt.update(s)
tests=[]
for k,v in cnt.items():
    if v<5: continue
    A=df[df.mBM==0].alt.apply(lambda s:k in s).sum(); B=df[df.mBM==1].alt.apply(lambda s:k in s).sum()
    tests.append((f"{k[0]}-{k[1]}", A,B, fisher_exact([[A,88-A],[B,28-B]])[1]))
raw=[t[3] for t in tests]
rej,q,_,_=multipletests(raw,method='fdr_bh')
print(f"  {len(tests)} alterations tested; significant after BH-FDR: {rej.sum()}")
for (n_,A,B,p),qq,r in sorted(zip(tests,q,rej), key=lambda z:z[0][3])[:6]:
    print(f"    {n_:34s} {A:3d} vs {B:2d}  p={p:.3f}  q={qq:.3f}  {'SIG' if r else ''}")
