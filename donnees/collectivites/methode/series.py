# Chemins à adapter : script fourni pour documenter la méthode.
import pandas as pd, numpy as np
X=pd.Timestamp('2026-10-21',tz='UTC')
def prep(d):
    d=d.copy()
    d['fin']=pd.to_datetime(d.dateFermeture,utc=True,errors='coerce').fillna(pd.to_datetime(d.dateDepublication,utc=True,errors='coerce')).fillna(X)
    return d[d.pub.notna()]
def pr(d,y):
    a=pd.Timestamp(f'{y}-01-01',tz='UTC'); b=min(pd.Timestamp(f'{y+1}-01-01',tz='UTC'),X)
    tot=(d.fin-d.pub).dt.total_seconds().clip(lower=86400)
    ov=(np.minimum(d.fin,b)-np.maximum(d.pub,a)).dt.total_seconds().clip(lower=0)
    return int((d.dossiers*ov/tot).sum())
def act(d,y):
    a=pd.Timestamp(f'{y}-01-01',tz='UTC'); b=pd.Timestamp(f'{y}-12-31',tz='UTC'); return d[(d.pub<=b)&(d.fin>=a)]
dot=prep(pd.read_pickle('dot.pkl'))
u=dot[dot.DETR|dot.DSIL|dot.DSID|dot.DPV]
print('Dotations DGCL (DETR/DSIL/DSID/DPV) union:',[(y,len(act(u,y)),act(u,y).departement.nunique(),pr(u,y)) for y in range(2019,2027)])
par=prep(pd.read_pickle('par_clean.pkl'))
print('PAR:',[(y,len(act(par,y)),act(par,y).organisme.str.lower().str.strip().nunique(),pr(par,y)) for y in range(2018,2027)])
pour=prep(pd.read_pickle('pour.pkl'))
for c in pour.cat.unique():
    s=pour[pour.cat==c]; print('POUR',c,[(y,len(act(s,y)),pr(s,y)) for y in range(2018,2027)])
df=prep(pd.read_pickle('df.pkl'))
print('ALL',[(y,len(act(df,y)),pr(df,y)) for y in range(2018,2027)])

def prd(d,y):
    a=pd.Timestamp(f'{y}-01-01',tz='UTC'); b=min(pd.Timestamp(f'{y+1}-01-01',tz='UTC'),X)
    tot=(d.fin-d.pub).dt.total_seconds().clip(lower=86400)
    ov=(np.minimum(d.fin,b)-np.maximum(d.pub,a)).dt.total_seconds().clip(lower=0)
    return d.dossiers*ov/tot
u=u.assign(p25=prd(u,2025),p24=prd(u,2024))
pd.set_option('display.width',250); pd.set_option('display.max_colwidth',80)
print(u.sort_values('p25',ascending=False)[['title','departement','datePublication','fin','dossiers','p24','p25']].head(15).to_string())
