import os
import pandas as pd, numpy as np, warnings
warnings.filterwarnings('ignore')
from statsmodels.duration.survfunc import SurvfuncRight, survdiff
from statsmodels.duration.hazard_regression import PHReg
df = pd.read_excel(os.environ.get('COHORT_XLSX','data/20260719cohort.xlsx'))
d='Difference between Lung Ca. and Brain Met in days'
df['event']=(df['Is Deceased'].astype(str)=='True').astype(int)
df['os']=df['Overall survival'].astype(float)
df['mBM']=(df.group=='verl-mBM').astype(int)
df['t2bm_m']=df[d]/30.44

def med(t,e):
    sf=SurvfuncRight(t,e)
    idx=np.where(sf.surv_prob<=0.5)[0]
    return sf.surv_times[idx[0]] if len(idx) else np.nan

def report(name, data, tcol, ecol='event'):
    print(f"\n-- {name}")
    for g,lab in [(0,'sBM'),(1,'mBM')]:
        s=data[data.mBM==g]
        print(f"   {lab}: n={len(s):3d} events={s[ecol].sum():3d} median={med(s[tcol],s[ecol]):.1f} mo")
    chi,p=survdiff(data[tcol],data[ecol],data['mBM'])
    print(f"   log-rank chi2={chi:.2f}  p={p:.4f}")

print("="*70); print("A. OS FROM PRIMARY DIAGNOSIS (as currently reported)")
report("all", df, 'os')

print("\n"+"="*70); print("B. OS FROM BRAIN-MET DIAGNOSIS (correct clinical clock)")
df['os_bm']=df.os-df.t2bm_m
print("  rows with os_bm<=0 (BM after last contact => data inconsistency):", (df.os_bm<=0).sum())
sub=df[df.os_bm>0].copy()
report("os from BM", sub, 'os_bm')

print("\n"+"="*70); print("C. LANDMARK AT 4 MONTHS (immortal-time bias correction)")
LM=4.0
lm=df[df.os>LM].copy(); lm['os_lm']=lm.os-LM
print(f"  excluded (died/censored <= {LM} mo): sBM {((df.os<=LM)&(df.mBM==0)).sum()}, mBM {((df.os<=LM)&(df.mBM==1)).sum()}")
report("landmark 4mo", lm, 'os_lm')

print("\n"+"="*70); print("D. COX: mBM as TIME-DEPENDENT covariate (counting process)")
rows=[]
for _,r in df.iterrows():
    if r.mBM==0:
        rows.append((0,r.os,r.event,1))
    else:
        t=min(r.t2bm_m,r.os)
        if t>0: rows.append((0,t,0,0))
        if r.os>t: rows.append((t,r.os,r.event,1))
td=pd.DataFrame(rows,columns=['start','stop','event','bm_present'])
print("  (time-dependent Cox needs start-stop; reporting simple Cox on landmark instead)")
m=PHReg(lm.os_lm, lm[['mBM']], status=lm.event).fit()
print(f"  Landmark Cox mBM HR={np.exp(m.params[0]):.2f} (95%CI {np.exp(m.conf_int()[0][0]):.2f}-{np.exp(m.conf_int()[0][1]):.2f}) p={m.pvalues[0]:.3f}")
m2=PHReg(df.os, df[['mBM']], status=df.event).fit()
print(f"  Naive    Cox mBM HR={np.exp(m2.params[0]):.2f} (95%CI {np.exp(m2.conf_int()[0][0]):.2f}-{np.exp(m2.conf_int()[0][1]):.2f}) p={m2.pvalues[0]:.3f}")
