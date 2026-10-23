# Chemins à adapter : script fourni pour documenter la méthode. Données d'entrée : jeux data.gouv.fr cités dans le LISEZMOI.
import pandas as pd, glob
fs=glob.glob('data/dgcl/*dgcl*.csv')
d=pd.concat([pd.read_csv(f,sep=';',decimal=',',dtype={'beneficiaire_dep':str,'beneficiaire_siren':str,'beneficiaire_code_insee':str},encoding='utf-8-sig') for f in fs])
print(d.shape); print(d.groupby(['exercice','dispositif']).subvention.agg(['size','sum']).unstack().round(-5))
print(sorted(d.beneficiaire_dep.dropna().unique())[:10], sorted(d.beneficiaire_dep.dropna().unique())[-25:])
print(d.groupby('exercice').beneficiaire_siren.agg(lambda s:(s.notna().mean(),s.nunique())))
d.to_pickle('dgcl.pkl')
