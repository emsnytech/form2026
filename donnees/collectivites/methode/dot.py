# Chemins à adapter : script fourni pour documenter la méthode.
import pandas as pd, re
p=pd.read_pickle('pour.pkl'); d=p[p.cat=="Dotations et fonds d'investissement local"].copy()
T=d.title
for k,pat in {'DETR':r'\bDETR\b','DSIL':r'\bDSIL\b','DSID':r'\bDSID\b','DPV':r'\bDPV\b|politique de la ville','FNADT':'FNADT','FondsVert':r'fonds vert|fonds d.acc'}.items(): d[k]=T.str.contains(pat,case=False)
def mill(t):
    m=re.findall(r'20(1[89]|2[0-7])',t); return int('20'+m[0]) if m else None
d['mill']=T.apply(mill)
d['mill2']=d.mill.fillna(d.an+1)  # campagne N souvent publiée en N-1
pd.set_option('display.width',250)
for k in ['DETR','DSIL','DSID','DPV','FNADT','FondsVert']:
    s=d[d[k]]
    print(k, len(s), s.dossiers.sum())
    print(s.groupby('mill').agg(dem=('number','size'),dos=('dossiers','sum'),dep=('departement','nunique')).T)
d.to_pickle('dot.pkl')
print(d.departement.isna().mean())
print(d[d.mill==2025].sort_values('dossiers',ascending=False)[['title','organisme','departement','dossiers']].head(15).to_string())
