# Chemins à adapter : script fourni pour documenter la méthode.
import pandas as pd, re
df=pd.read_pickle('df.pkl')
c=df[df.typeOrganisme=='collectivite_territoriale'].copy()
def typ(o):
    o=(o or '').lower()
    if re.search(r'polyn|nouvelle[- ]cal|wallis|saint[- ]pierre|saint[- ]barth|saint[- ]martin|gouvernement',o): return 'Collectivité d\'outre-mer / gouvernement'
    if re.search(r'r[ée]gion|collectivit[ée] (territoriale )?de (corse|martinique|guyane)|collectivit[ée] europ[ée]enne',o): return 'Région / collectivité unique'
    if re.search(r'd[ée]partement|conseil g[ée]n[ée]ral|^cd ?\d|cd\d\d',o): return 'Département'
    if re.search(r'm[ée]tropole|communaut[ée]|agglom|intercommun|epci|pays |p[ôo]le d.[ée]quilibre|petr',o): return 'Intercommunalité'
    if re.search(r'syndicat|sivom|sivu|smic|sdis|centre de gestion|cdg|ccas|cias|office|[ée]tablissement public',o): return 'Syndicat / établissement local'
    if re.search(r'commune|ville|mairie|municipal|cit[ée]',o): return 'Commune'
    return 'Non classé'
c['type_coll']=c.organisme.apply(typ)
c.to_pickle('par.pkl')
g=c.groupby('type_coll').agg(demarches=('number','size'),dossiers=('dossiers','sum'),organismes=('organisme','nunique'),siret=('siret','nunique')).sort_values('dossiers',ascending=False)
print(g); print('total',len(c),c.dossiers.sum(),'orgs',c.organisme.str.lower().str.strip().nunique(),'siret',c.siret.nunique())
print(c[c.type_coll=='Non classé'].organisme.value_counts().head(40))
