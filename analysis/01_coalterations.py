import os
import pandas as pd, numpy as np, re
from collections import Counter
from itertools import combinations
from scipy.stats import fisher_exact, mannwhitneyu, chi2_contingency
df = pd.read_excel(os.environ.get('COHORT_XLSX','data/20260719cohort.xlsx'))
pv='Pathogenic variants (list)'

def parse(s):
    """return set of (gene, class) and set of genes"""
    alts=set()
    for it in str(s).split(';'):
        it=it.strip()
        if not it: continue
        toks=it.split(' ',1)
        g=toks[0]; rest=toks[1] if len(toks)>1 else ''
        if 'fusion' in rest or 'delins' in rest:
            for p in re.split(r'[-]', g): alts.add((p,'fusion'))
            continue
        if g.startswith('NKX2'):
            g='NKX2-1'; rest=rest.split(' ',1)[-1] if rest.startswith('1') else rest
        cls = 'loss' if ('loss' in rest or rest.strip()=='deletion') else ('amp' if 'amplification' in rest else 'mut')
        alts.add((g,cls))
    return alts

df['alts']=df[pv].apply(parse)
df['genes']=df['alts'].apply(lambda a:{g for g,c in a})
df['loss']=df['alts'].apply(lambda a:{g for g,c in a if c=='loss'})

sBM=df[df.group=='init-sBM']; mBM=df[df.group=='verl-mBM']

def pct(n,d): return f"{n}/{d} ({100*n/d:.1f}%)"

print("="*70)
print("9p21.3 LOCUS (CDKN2A/CDKN2B/MTAP)")
print("="*70)
for label, fn in [
    ("CDKN2A any alteration", lambda r:'CDKN2A' in r.genes),
    ("CDKN2A loss",           lambda r:'CDKN2A' in r.loss),
    ("CDKN2B loss",           lambda r:'CDKN2B' in r.loss),
    ("MTAP loss",             lambda r:'MTAP' in r.loss),
    ("CDKN2A+CDKN2B loss",    lambda r:{'CDKN2A','CDKN2B'}<=r.loss),
    ("CDKN2A+B+MTAP triple loss", lambda r:{'CDKN2A','CDKN2B','MTAP'}<=r.loss),
    ("any 9p21.3 loss",       lambda r: len({'CDKN2A','CDKN2B','MTAP'}&r.loss)>0),
]:
    a=sBM.apply(fn,axis=1); b=mBM.apply(fn,axis=1); t=df.apply(fn,axis=1)
    p=fisher_exact([[a.sum(),len(a)-a.sum()],[b.sum(),len(b)-b.sum()]])[1]
    print(f"{label:28s} all {pct(t.sum(),len(df)):16s} sBM {pct(a.sum(),len(a)):16s} mBM {pct(b.sum(),len(b)):16s} p={p:.3f}")

print()
print("="*70)
print("CO-ALTERATION PAIRS (abstract's claims)")
print("="*70)
for pair in [('TP53','EGFR'),('TP53','KRAS'),('TP53','STK11'),('KRAS','STK11'),('KRAS','KEAP1'),('TP53','CDKN2A'),('STK11','KEAP1')]:
    fn=lambda r,p=pair: set(p)<=r.genes
    a=sBM.apply(fn,axis=1); b=mBM.apply(fn,axis=1); t=df.apply(fn,axis=1)
    pval=fisher_exact([[a.sum(),len(a)-a.sum()],[b.sum(),len(b)-b.sum()]])[1]
    print(f"{'/'.join(pair):16s} all {pct(t.sum(),len(df)):16s} sBM {pct(a.sum(),len(a)):16s} mBM {pct(b.sum(),len(b)):16s} p={pval:.3f}")

print()
print("="*70)
print("ALL RECURRENT 2-GENE COMBINATIONS (n>=5 overall)")
print("="*70)
c=Counter()
for s in df.genes:
    for x in combinations(sorted(s),2): c[x]+=1
for k,v in c.most_common(20):
    a=sBM.genes.apply(lambda s,k=k:set(k)<=s).sum(); b=mBM.genes.apply(lambda s,k=k:set(k)<=s).sum()
    print(f"  {'+'.join(k):24s} all {v:3d} ({100*v/len(df):4.1f}%)  sBM {a:3d} ({100*a/88:4.1f}%)  mBM {b:2d} ({100*b/28:4.1f}%)")

print()
print("TOP 3-GENE COMBINATIONS")
c3=Counter()
for s in df.genes:
    for x in combinations(sorted(s),3): c3[x]+=1
for k,v in c3.most_common(12):
    a=sBM.genes.apply(lambda s,k=k:set(k)<=s).sum(); b=mBM.genes.apply(lambda s,k=k:set(k)<=s).sum()
    print(f"  {'+'.join(k):32s} all {v:3d}  sBM {a:3d} ({100*a/88:4.1f}%)  mBM {b:2d} ({100*b/28:4.1f}%)")
