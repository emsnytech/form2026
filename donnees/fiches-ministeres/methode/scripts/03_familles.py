"""Familles de démarches homologues publiées séparément par plusieurs émetteurs (titre). Exemples, pas une classification exhaustive."""
import json, sys, re, collections
cfg=json.load(open(sys.argv[1])); sys.argv=[sys.argv[0], sys.argv[1], "/dev/null"]
exec(open("scripts/02_fiche_ministere.py").read().split("APIP =")[0])
FAM = json.load(open(sys.argv[0].replace("03_familles.py","familles_education.json")))
per=[]
for r in rows:
    p,s=classify(r)
    if p and p!="interministeriel" and (r["datePublication"] or "0")[:4]>=str(YEARS[0]): r["pole"]=p; per.append(r)
res=[]
for f in FAM:
    rx=re.compile(f["motif"], re.I)
    m=[r for r in per if rx.search(r["title"] or "")]
    orgs={(r["organisme"] or "").strip().lower() for r in m}
    deps={r["departement"] for r in m if r["departement"]}
    res.append({"famille":f["nom"],"demarches":len(m),"emetteurs_distincts":len(orgs),"departements":len(deps),
      "dossiers":sum(r["dossiersCount"] or 0 for r in m),
      "champs_moyens":round(sum(r["n_champs"] for r in m)/len(m),1) if m else None,
      "champs_min":min((r["n_champs"] for r in m), default=None),"champs_max":max((r["n_champs"] for r in m), default=None),
      "pj_moyennes":round(sum(r["champs_types"].get("PieceJustificativeChampDescriptor",0) for r in m)/len(m),1) if m else None,
      "avec_annuaire_education":sum(1 for r in m if r["champs_types"].get("AnnuaireEducationChampDescriptor")),
      "avec_quotient_familial":sum(1 for r in m if r["champs_types"].get("QuotientFamilialChampDescriptor")),
      "avec_iban":sum(1 for r in m if r["champs_types"].get("IbanChampDescriptor")),
      "par_annee":dict(sorted(collections.Counter(r["datePublication"][:4] for r in m).items())),
      "exemples":[{"number":r["number"],"title":r["title"],"organisme":r["organisme"],"dossiers":r["dossiersCount"],"n_champs":r["n_champs"]} for r in sorted(m,key=lambda r:-(r["dossiersCount"] or 0))[:6]]})
json.dump(res, open("out/education_familles.json","w"), ensure_ascii=False, indent=1)
for x in res: print(x["famille"],x["demarches"],x["emetteurs_distincts"],x["dossiers"],x["champs_moyens"],x["champs_min"],x["champs_max"],x["pj_moyennes"],x["avec_quotient_familial"],x["par_annee"])
