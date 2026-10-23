# Chemins à adapter : script fourni pour documenter la méthode.
import pandas as pd, re, numpy as np
c=pd.read_pickle('par.pkl')
bad=re.compile(r'direccte|protection des populations|pr[ée]fecture|caf |caf$|^caf|ademe|acad[ée]mie|^ddtm?\b|ddt\d|driea|offre de soins|dgifp|cciamp|centre hospitalier',re.I)
c['mal_declare']=c.organisme.fillna('').str.contains(bad)
print('mal déclarés',c.mal_declare.sum(),c[c.mal_declare].dossiers.sum())
c=c[~c.mal_declare].copy(); c.to_pickle('par_clean.pkl')
print('PAR net',len(c),c.dossiers.sum(),'orgs',c.organisme.str.lower().str.strip().nunique())
print(c.groupby('type_coll').agg(dem=('number','size'),dos=('dossiers','sum'),org=('organisme',lambda s:s.str.lower().str.strip().nunique())).sort_values('dos',ascending=False))
print(c.groupby('an').agg(dem=('number','size')).T)
print(c.state.value_counts())
print('forIndividual',c.groupby('forIndividual').agg(dem=('number','size'),dos=('dossiers','sum')))
pd.set_option('display.width',250); pd.set_option('display.max_colwidth',90)
print(c.sort_values('dossiers',ascending=False)[['number','title','organisme','an','state','dossiers']].head(30).to_string())
# top organismes
o=c.assign(o=c.organisme.str.strip()).groupby('o').agg(dem=('number','size'),dos=('dossiers','sum')).sort_values('dos',ascending=False)
print(o.head(25))
