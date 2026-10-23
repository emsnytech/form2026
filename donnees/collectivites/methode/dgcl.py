# Chemins à adapter : script fourni pour documenter la méthode.
import pandas as pd, glob
fs=glob.glob('/mnt/user-data/attachments/173f4c71-1b36-58e5-879b-d11179f2f59a/*dgcl*.csv')
d=pd.concat([pd.read_csv(f,sep=';',decimal=',',dtype={'beneficiaire_dep':str,'beneficiaire_siren':str,'beneficiaire_code_insee':str},encoding='utf-8-sig') for f in fs])
print(d.shape); print(d.groupby(['exercice','dispositif']).subvention.agg(['size','sum']).unstack().round(-5))
print(sorted(d.beneficiaire_dep.dropna().unique())[:10], sorted(d.beneficiaire_dep.dropna().unique())[-25:])
print(d.groupby('exercice').beneficiaire_siren.agg(lambda s:(s.notna().mean(),s.nunique())))
d.to_pickle('dgcl.pkl')
