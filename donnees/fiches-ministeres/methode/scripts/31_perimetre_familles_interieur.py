"""Fiche Intérieur, étape 1 : mouvements de la zone déclarée au périmètre, puis tableau des familles
(tout le périmètre, depuis 2021, depuis le 7 octobre 2022). Open data seul. Sortie : out/interieur_familles_etape1.json.
Usage : python3 scripts/31_perimetre_familles_interieur.py"""
import json, re, sys, collections as C
sys.argv=["x","scripts/config_interieur.json","/dev/null"]
exec(open("scripts/02_fiche_ministere.py").read().split("APIP =")[0])
I="Ministère de l’Intérieur"
zone=[r for r in rows if I in (r["zones"] or [])]
inter=[r for r in zone if len(r["zones"])>3]
ANOMALIES.clear()
per=[]; src=C.Counter()
for r in rows:
    p,s=classify(r)
    if p and p!="interministeriel": per.append(r); r["src"]=s
anz=[r for r in ANOMALIES if I in (r["zones"] or [])]; ans=[r for r in ANOMALIES if not r["zones"]]
nd=lambda L: sum(r["dossiersCount"] or 0 for r in L)
print("MOUVEMENTS")
print("zone déclarée", len(zone), nd(zone))
print("- plus de 3 zones", len(inter), nd(inter))
print("- anomalies zone", len(anz), nd(anz))
sz=[r for r in per if r["src"]=="nom_organisme"]
print("+ sans zone par organisme", len(sz), nd(sz), "| anomalies sans zone exclues", len(ans), nd(ans))
print("= périmètre", len(per), nd(per), C.Counter(r["state"] for r in per))
multi=[r for r in per if len(r["zones"] or [])>1]; print("  dont multi-zones (2-3)", len(multi), nd(multi))
for z in ("Ministère de la Justice","Ministère de l’Éducation nationale, de l’Enseignement supérieur et de la Recherche"):
    o=[r for r in multi if z in r["zones"]]; print("  partagées avec",z[:30],len(o),nd(o))
print("plateforme", len(rows), nd(rows), "part démarches %.1f dossiers %.1f"%(100*len(per)/len(rows),100*nd(per)/nd(rows)))
FAM=json.load(open("scripts/familles_interieur.json"))
res=C.defaultdict(list)
for r in per:
    for f in FAM:
        if re.search(f["motif"],r["title"] or "",re.I): res[f["nom"]].append(r); break
    else: res["Autres, non classées"].append(r)
T=nd(per); fen=lambda r:(r["datePublication"] or "0")[:4]>="2021"; rec=lambda r:(r["datePublication"] or "0")[:10]>="2022-10-07"
Tf=nd([r for r in per if fen(r)])
print("\nFAMILLES  dem | dossiers | % | émetteurs | dem≥2021 | doss≥2021 | %≥2021 | dem≥7/10/22 | publiées auj | 1re-dernière pub")
out=[]
for k in [f["nom"] for f in FAM]+["Autres, non classées"]:
    m=res[k]; f2=[r for r in m if fen(r)]; yrs=sorted((r["datePublication"] or "")[:4] for r in m if r["datePublication"])
    em=len({re.sub(r"\s+"," ",(r["organisme"] or "").strip().lower()) for r in m})
    row=[k,len(m),nd(m),round(100*nd(m)/T,1),em,len(f2),nd(f2),round(100*nd(f2)/Tf,1),sum(rec(r) for r in m),sum(r["state"]=="publiee" for r in m),(yrs[0] if yrs else "")+"-"+(yrs[-1] if yrs else "")]
    out.append(row); print(" | ".join(map(str,row)))
print("TOTAL",len(per),T,"| fenêtre",sum(1 for r in per if fen(r)),Tf)
json.dump(out,open("out/interieur_familles_etape1.json","w"),ensure_ascii=False,indent=1)
