# Chemins à adapter : script fourni pour documenter la méthode.
import pandas as pd, numpy as np
exec(open('series.py').read().split("dot=prep")[0])
dot=prep(pd.read_pickle('dot.pkl'))
dot=dot[~dot.title.str.contains('paiement|versement|solde|acompte|bilan|enqu[êe]te|fiche structure',case=False)]
print(sorted(dot.departement.dropna().unique()))
def cov(flag,y):
    a=act(dot[flag],y); return set(a.departement.dropna())
def norm(c):
    if c is None or pd.isna(c): return None
    c=c.strip('-')
    if c=='20A': return '2A'
    if c=='20B': return '2B'
    if c=='67A': return 'CEA'
    if c=='691': return '69'
    if len(c)==3 and c.startswith('0'): return c[1:]
    return c
d=pd.read_pickle('dgcl.pkl'); d['dep']=d.beneficiaire_dep.apply(norm)
fam={'DETR':'DETRDSIL','DSIL':'DETRDSIL','DSIL Exceptionnelle':'DETRDSIL','DSIL RT':'DETRDSIL','DPV':'DPV','DSID':'DSID','DSID RT':'DSID'}
d['fam']=d.dispositif.map(fam)
flags={'DETRDSIL':dot.DETR|dot.DSIL,'DPV':dot.DPV,'DSID':dot.DSID}
rows=[]
for y in range(2018,2026):
    for f,fl in flags.items():
        s=cov(fl,y)
        if 'CEA' not in s and ('67' in s or '68' in s): s=s|{'CEA'}
        x=d[(d.exercice==y)&(d.fam==f)]
        c=x[x.dep.isin(s)]
        rows.append(dict(annee=y,famille=f,dep_dn=len(s),total_M=x.subvention.sum()/1e6,dn_M=c.subvention.sum()/1e6,projets=len(x),projets_dn=len(c),siren_dn=c.beneficiaire_siren.nunique(),cout_dn_M=c.cout_ht.sum()/1e6))
r=pd.DataFrame(rows); r['part']=r.dn_M/r.total_M
pd.set_option('display.width',250); print(r.round(1).to_string())
g=r.groupby('annee')[['total_M','dn_M','projets','projets_dn','cout_dn_M']].sum(); g['part']=g.dn_M/g.total_M; print(g.round(2))
print('cumul',g.dn_M.sum(), g.total_M.sum())
# SIREN distincts toutes années, couverts
d2=[]
for y in range(2018,2026):
    for f,fl in flags.items():
        s=cov(fl,y); 
        if '67' in s or '68' in s: s=s|{'CEA'}
        x=d[(d.exercice==y)&(d.fam==f)&d.dep.isin(s)]; d2.append(x)
d2=pd.concat(d2); print('SIREN distincts couverts 2018-2025',d2.beneficiaire_siren.nunique(), 'communes', d2[d2.beneficiaire_type=='commune'].beneficiaire_siren.nunique())
print(d2.beneficiaire_type.value_counts())
r.to_csv('montants_dgcl.csv',index=False)

fv=pd.read_pickle('fv.pkl'); s1=set(d2.beneficiaire_siren.dropna()); s2=set(fv.siren.dropna())
u=s1|s2; print('union siren',len(u),'dotations',len(s1),'fv',len(s2),'fv seuls',len(s2-s1))
com=set(d2[d2.beneficiaire_type=='commune'].beneficiaire_siren.dropna())|{x for x in s2 if str(x).startswith('21')}
print('communes (approx)',len(com))
