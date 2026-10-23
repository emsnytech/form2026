# Chemins à adapter : script fourni pour documenter la méthode.
import pandas as pd, glob, re
A='/mnt/user-data/attachments/173f4c71-1b36-58e5-879b-d11179f2f59a/'
def num(s): return pd.to_numeric(s.astype(str).str.replace(r'[\s \xa0]','',regex=True).str.replace(',','.'),errors='coerce')
out=[]
f23=pd.read_csv(A+'a73e9658-fonds-vert-2023-export.csv',dtype=str); f23['m']=num(f23.montant_engage); f23['ds']=f23.numero_dossier_ds; f23['siren']=f23.siren; f23['an']=2023; f23['src']='principal'; f23['dem']=f23.nom_demarche_ds
for fn,y,src in [('08328d28-fonds-vert-2024-export.csv',2024,'principal'),('5575732b-fonds-vert-2025-export.csv',2025,'principal'),('c0d66eed-fonds-vert-p113-2025-export.csv.csv',2025,'p113')]:
    x=pd.read_csv(A+fn,dtype=str); x['m']=num(x.montant_engage); x['ds']=x.numero_dossier_ds; x['siren']=x.siret_beneficiaire.str[:9]; x['an']=y; x['src']=src; x['dem']=x.demarche; out.append(x)
p=pd.read_csv(A+'cb6562c4-fonds-vert-p113-2024-export.csv',dtype=str); p['m']=num(p.montant_engage); p['ds']=p.numero_ds; p['siren']=None; p['an']=2024; p['src']='p113'; p['dem']=None
cols=['an','src','m','ds','siren','dem']
fv=pd.concat([f23[cols]]+[o[cols] for o in out]+[p[cols]])
fv['has_ds']=fv.ds.notna()&fv.ds.str.strip().ne('')
g=fv.groupby(['an','src']).agg(lignes=('m','size'),M=('m',lambda s:s.sum()/1e6),dossiers=('ds','nunique'),avec_ds=('has_ds','mean'),siren=('siren','nunique'),demarches=('dem','nunique'))
print(g.round(3))
t=fv.groupby('an').agg(M=('m',lambda s:s.sum()/1e6),dossiers=('ds','nunique'),siren=('siren','nunique')); print(t.round(1)); print('cumul',fv.m.sum()/1e6, fv.ds.nunique(), fv.siren.nunique())
fv.to_pickle('fv.pkl')
