# Chemins à adapter : script fourni pour documenter la méthode.
import pandas as pd, numpy as np, re
d=pd.read_pickle('dot.pkl')
X=pd.Timestamp('2026-10-21',tz='UTC')
d['fin']=pd.to_datetime(d.dateFermeture,utc=True,errors='coerce').fillna(pd.to_datetime(d.dateDepublication,utc=True,errors='coerce'))
d.loc[d.state=='publiee','fin']=d.loc[d.state=='publiee','fin'].fillna(X)
d['fin']=d.fin.fillna(X)
def active(df,y):
    a=pd.Timestamp(f'{y}-01-01',tz='UTC'); b=pd.Timestamp(f'{y}-12-31',tz='UTC')
    return df[(df.pub<=b)&(df.fin>=a)]
def prorata(df,y):
    a=pd.Timestamp(f'{y}-01-01',tz='UTC'); b=pd.Timestamp(f'{y+1}-01-01',tz='UTC')
    tot=(df.fin-df.pub).dt.total_seconds().clip(lower=86400)
    ov=(np.minimum(df.fin,b)-np.maximum(df.pub,a)).dt.total_seconds().clip(lower=0)
    return (df.dossiers*ov/tot).sum()
for k in ['DETR','DSIL','DPV','DSID','FNADT']:
    s=d[d[k]]
    row=[]
    for y in range(2019,2027):
        a=active(s,y); row.append((y,len(a),a.departement.nunique(),round(prorata(s,y))))
    print(k,row)
d.to_pickle('dot.pkl')
a=active(d[d.DETR],2025); print(a.departement.value_counts().sort_index().index.tolist())
print('DETR sans dep actives 2025',a.departement.isna().sum(), a[a.departement.isna()].title.head(10).tolist())
