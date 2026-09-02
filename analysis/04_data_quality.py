import os
import pandas as pd, numpy as np, re, warnings
warnings.filterwarnings('ignore')
from scipy.stats import fisher_exact, mannwhitneyu
df = pd.read_excel(os.environ.get('COHORT_XLSX','data/20260719cohort.xlsx'))
df['mBM']=(df.group=='verl-mBM').astype(int); pv='Pathogenic variants (list)'

print("MISSINGNESS in key variables (n=116):")
for c in ['PDL1 Tumor Marker Tests>Result (Text)','PDL1','ECOG','Stage','Smoking Status','Metastases','tmb','TMB','Oncogenic driver (targetable)','POP-ID','FoundationOne (solid)']:
    miss=df[c].isna().sum()
    ms=df[df.mBM==0][c].isna().sum(); mm=df[df.mBM==1][c].isna().sum()
    print(f"  {c:42s} missing {miss:3d} ({100*miss/116:4.1f}%)   sBM {ms:2d}/88  mBM {mm:2d}/28")

print("\nDUPLICATE variant entries within a patient's list:")
dups=0; pts=0
for s in df[pv]:
    items=[x.strip() for x in str(s).split(';') if x.strip()]
    if len(items)!=len(set(items)): pts+=1; dups+=len(items)-len(set(items))
print(f"  {pts}/116 patients have duplicated entries; {dups} duplicate rows total")

print("\nHistology: non-NSCLC entities present")
h=df['Primary Cancers>Histology>Text']
non=h.isin(['Small cell carcinoma, NOS','Small cell sarcoma','Carcinoid tumor, NOS','Large cell neuroendocrine carcinoma'])
print(f"  {non.sum()}/116 ({100*non.mean():.1f}%) SCLC/neuroendocrine/carcinoid  -> sBM {non[df.mBM==0].sum()}, mBM {non[df.mBM==1].sum()}")
print("  OncoTree LNET:", (df.OncoTree=='LNET').sum(), " MBC:", (df.OncoTree=='MBC').sum())

print("\nTMB (numeric) by group:")
t=pd.to_numeric(df['TMB'],errors='coerce')
print("  sBM median %.2f (n=%d), mBM median %.2f (n=%d)" % (t[df.mBM==0].median(), t[df.mBM==0].notna().sum(), t[df.mBM==1].median(), t[df.mBM==1].notna().sum()))
print("  NOTE: 'tmb' text col missing", df['tmb'].isna().sum(), "; 'TMB' numeric col missing", df['TMB'].isna().sum())

print("\nTargetable driver present (non-null) by group:")
o=df['Oncogenic driver (targetable)'].notna()
print(f"  sBM {o[df.mBM==0].sum()}/88, mBM {o[df.mBM==1].sum()}/28  -- but 44 pts have no POP-ID annotation at all")

print("\nNumber of extracranial metastatic sites (where recorded):")
ns=df['Metastases'].dropna().apply(lambda s: len([x for x in str(s).split(',') if x.strip()]))
print("  n recorded =",len(ns), " median sites =", ns.median())
g=df.loc[df['Metastases'].notna(),'mBM']
print("  sBM median %.1f, mBM median %.1f" % (ns[g==0].median(), ns[g==1].median()))
