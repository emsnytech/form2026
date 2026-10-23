# Chemins à adapter : script fourni pour documenter la méthode.
import pandas as pd, re
df=pd.read_pickle('df.pkl')
test=df.title.str.contains(r'\btest|essai|brouillon|\[old|copie de|^copie',case=False,na=False)
base=df[(df.typeOrganisme!='collectivite_territoriale')].copy()
T=base.title.fillna('')
dot=re.compile(r"\bDETR\b|\bDSIL\b|\bDSID\b|\bDPV\b|\bFNADT\b|fonds vert|fonds d.acc[ée]l[ée]ration de la transition|dotation (d.[ée]quipement des territoires|de soutien [àa] l.investissement|politique de la ville)",re.I)
svc=re.compile(r"consultation du domaine|sit@del|m[ée]daille d.honneur r[ée]gionale",re.I)
cib=re.compile(r"\b(communes?|collectivit[ée]s?|EPCI|intercommunal\w*|intercommunalit[ée]s?|mairies?|maires|[ée]lus locaux|organismes publics locaux|groupements? de collectivit[ée]s|syndicats? (mixtes?|intercommunaux|d.eau|d.[ée]nergie)|bloc communal|conseils? municipaux|territoires? d.industrie|petites villes de demain|action c(oe|œ)ur de ville)\b",re.I)
tag=base.tags.apply(lambda l: 'Collectivité territoriale' in (l or []))
base['cat']=None
base.loc[T.str.contains(cib)&(base.forIndividual==False),'cat']='Autres dispositifs ciblant les collectivités'
base.loc[tag&(base.forIndividual==False)&base.cat.isna(),'cat']='Autres dispositifs ciblant les collectivités'
base.loc[T.str.contains(svc),'cat']='Services administratifs aux collectivités'
base.loc[T.str.contains(dot),'cat']="Dotations et fonds d'investissement local"
base['test']=test.loc[base.index]
p=base[base.cat.notna()&~base.test].copy()
p.to_pickle('pour.pkl')
print(len(p),p.dossiers.sum())
print(p.groupby('cat').agg(dem=('number','size'),dos=('dossiers','sum')))
print(p.groupby('typeOrganisme').agg(dem=('number','size'),dos=('dossiers','sum')))
print(p.groupby('an').size())
pd.set_option('display.width',250); pd.set_option('display.max_colwidth',100)
s=p[p.cat=='Autres dispositifs ciblant les collectivités']
print(s.sample(40,random_state=1)[['title','organisme','dossiers']].to_string())
