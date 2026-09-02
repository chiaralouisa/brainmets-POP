import os
import pandas as pd, numpy as np, re, warnings
warnings.filterwarnings('ignore')
from scipy.stats import fisher_exact, mannwhitneyu
from statsmodels.duration.survfunc import SurvfuncRight, survdiff
from statsmodels.duration.hazard_regression import PHReg
df = pd.read_excel(os.environ.get('COHORT_XLSX','data/20260719cohort.xlsx'))
pv='Pathogenic variants (list)'; d='Difference between Lung Ca. and Brain Met in days'
df['event']=(df['Is Deceased'].astype(str)=='True').astype(int)
df['os']=df['Overall survival'].astype(float); df['mBM']=(df.group=='verl-mBM').astype(int)

# exact CDKN2A loss-type audit
print("CDKN2A / CDKN2B / MTAP raw alteration strings by group:")
from collections import Counter
for g in ['CDKN2A','CDKN2B','MTAP']:
    c=Counter()
    for _,r in df.iterrows():
        for it in str(r[pv]).split(';'):
            it=it.strip()
            if it.startswith(g+' '):
                c[(it.split(' ',1)[1], 'sBM' if r.mBM==0 else 'mBM')]+=1
    print(f"  {g}: {dict(c)}")

def losses(s):
    out=set()
    for it in str(s).split(';'):
        it=it.strip()
        if not it: continue
        p=it.split(' ',1)
        if len(p)>1 and p[1].strip() in ('loss','deletion'): out.add(p[0])
    return out
df['loss']=df[pv].apply(losses)
df['co9p']= df['loss'].apply(lambda s: {'CDKN2A','CDKN2B','MTAP'}<=s).astype(int)
df['cdkn2a_loss']=df['loss'].apply(lambda s:'CDKN2A' in s).astype(int)

print("\n9p21.3 triple co-deletion: sBM %d/88, mBM %d/28" % (df[(df.mBM==0)].co9p.sum(), df[(df.mBM==1)].co9p.sum()))
print("CDKN2A loss:               sBM %d/88, mBM %d/28" % (df[(df.mBM==0)].cdkn2a_loss.sum(), df[(df.mBM==1)].cdkn2a_loss.sum()))

def med(t,e):
    sf=SurvfuncRight(t,e); i=np.where(sf.surv_prob<=0.5)[0]
    return sf.surv_times[i[0]] if len(i) else np.nan

print("\n"+"="*66); print("9p21.3 CO-DELETION AND SURVIVAL (OS from primary dx)")
for v,lab in [(0,'no 9p21.3'),(1,'9p21.3 co-del')]:
    s=df[df.co9p==v]; print(f"  {lab:14s} n={len(s):3d} ev={s.event.sum():3d} median OS={med(s.os,s.event):.1f} mo")
chi,p=survdiff(df.os,df.event,df.co9p); print(f"  log-rank p={p:.4f}")
m=PHReg(df.os,df[['co9p']],status=df.event).fit()
print(f"  Cox HR={np.exp(m.params[0]):.2f} ({np.exp(m.conf_int()[0][0]):.2f}-{np.exp(m.conf_int()[0][1]):.2f}) p={m.pvalues[0]:.3f}")

print("\n"+"="*66); print("MULTIVARIABLE COX (landmark 4mo, OS from primary dx)")
LM=4.0; lm=df[df.os>LM].copy(); lm['os_lm']=lm.os-LM
lm['age']=lm['Age']; lm['male']=(lm['Gender>Text']=='Male').astype(int)
lm['adeno']=(lm['Primary Cancers>Histology>Text']=='Adenocarcinoma, NOS').astype(int)
X=lm[['mBM','co9p','age','male','adeno']]
m=PHReg(lm.os_lm,X,status=lm.event).fit()
for i,n in enumerate(X.columns):
    print(f"  {n:8s} HR={np.exp(m.params[i]):.2f} ({np.exp(m.conf_int()[i][0]):.2f}-{np.exp(m.conf_int()[i][1]):.2f}) p={m.pvalues[i]:.3f}")

print("\n"+"="*66); print("POWER / PRECISION")
print(f"  mBM n=28, events=26. Detectable HR at 80% power, alpha .05, 89 events, ratio 88:28 ~ HR>=1.8-2.0")
print(f"  9p21.3 co-del n={df.co9p.sum()} -> a 2x2 vs group has expected cell counts as low as {28*df.co9p.mean():.1f}")
