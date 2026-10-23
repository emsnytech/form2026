# Chemins à adapter : script fourni pour documenter la méthode.
import json, pandas as pd
rows=[json.loads(l) for l in open('/mnt/user-data/uploads/cartographie/fiches-ministeres/data/demarches_slim.jsonl')]
df=pd.DataFrame(rows)
df['dossiers']=df.dossiersCount.fillna(0).astype(int)
df['pub']=pd.to_datetime(df.datePublication,utc=True,errors='coerce')
df['an']=df.pub.dt.year
df['zones_s']=df.zones.apply(lambda z:'|'.join(z or []))
df.to_pickle('df.pkl')
