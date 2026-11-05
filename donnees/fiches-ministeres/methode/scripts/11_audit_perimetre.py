"""Audit du filtre Justice : cherche dans toute la base, quelle que soit la zone, par numéro, organisme, service, titre et SIRET.
Usage : python3 scripts/11_audit_perimetre.py scripts/config_justice.json"""
import json, sys, re, collections as C
cp = sys.argv[1]; sys.argv = ["x", cp, "/dev/null"]
exec(open("scripts/02_fiche_ministere.py").read().split("APIP =")[0])
per = set()
for r in rows:
    p, s = classify(r)
    if p and p != "interministeriel": per.add(r["number"])
def show(r): return (r["number"], "IN" if r["number"] in per else "OUT", (r["datePublication"] or "")[:10], r["state"], r["dossiersCount"], r["n_champs"], r["departement"], r["siret"], r["typeOrganisme"], (r["zones"] or ["SANS"])[0][:24], len(r["zones"] or []), (r["organisme"] or "")[:55], "|", (r["service_nom"] or "")[:35], "|", (r["title"] or "")[:85])
print("== 124249"); [print(show(r)) for r in rows if r["number"] == 124249]
JUR = re.compile(r"\bcours? d.appel\b|tribunal|\bTJ\b|\bTGI\b|\bCPH\b|prud.?hom|\bgreffe\b|\bparquet\b|procureur|juridiction|\bSAUJ\b|\bBAJ\b|bureau d.aide jurid|premi[eè]re? pr[ée]sid|\bJAF\b|\bjuge\b|magistrat|\bPJJ\b|protection judiciaire|\bSPIP\b|p[ée]nitenti|maison d.arr|d[ée]tention|\bDISP\b|\bCDAD\b|acc[èe]s au droit|point.justice|maison de justice|garde des sceaux|minist[eè]re de la justice|services? judiciaires|\bDSJ\b|\bENM\b|\bENG\b|\bENAP\b|\bAGRASC\b|\bBARO", re.I)
FAUX = re.compile(r"police judiciaire|CCAS|centre communal|tribunal administratif|cour administrative|conseil d.[ée]tat|cour des comptes|chambre r[ée]gionale des comptes|tribunal de commerce|pr[ée]fecture|mairie|commune de|d[ée]partement d", re.I)
org_hits = [r for r in rows if r["number"] not in per and JUR.search((r["organisme"] or "") + " | " + (r["service_nom"] or ""))]
print("\n== Organisme/service évoquant la justice, hors périmètre :", len(org_hits), sum(r["dossiersCount"] or 0 for r in org_hits))
for r in sorted(org_hits, key=lambda r: -(r["dossiersCount"] or 0))[:90]: print(show(r))
tit = re.compile(r"\bBAR[OÔ]|non.appel|copie.{0,25}(jugement|d[ée]cision)|aide juridictionnelle|\bAJ\b|avocat|barreau|cour d.appel|tribunal judiciaire|\bgreffe\b|prestation de serment|expert.{0,20}judiciaire|conciliateur|juge\b|juré|assesseur|d[ée]l[ée]gu[ée] du procureur|m[ée]diateur.{0,25}(familial|judiciaire)|commissaire de justice|casier", re.I)
tit_hits = [r for r in rows if r["number"] not in per and tit.search(r["title"] or "") and r not in org_hits]
print("\n== Titre évoquant la justice, hors périmètre et hors liste précédente :", len(tit_hits), sum(r["dossiersCount"] or 0 for r in tit_hits))
for r in sorted(tit_hits, key=lambda r: -(r["dossiersCount"] or 0))[:70]: print(show(r))
sirets = C.Counter(r["siret"] for r in rows if r["number"] in per and r["siret"])
print("\n== SIRET du périmètre", len(sirets))
sir_hits = [r for r in rows if r["number"] not in per and r["siret"] in sirets]
print("démarches hors périmètre partageant un SIRET du périmètre :", len(sir_hits), sum(r["dossiersCount"] or 0 for r in sir_hits))
for r in sorted(sir_hits, key=lambda r: -(r["dossiersCount"] or 0))[:40]: print(show(r))
s9 = C.Counter((r["siret"] or "")[:9] for r in rows if r["number"] in per and r["siret"])
print("SIREN du périmètre", s9.most_common(20))
sir9 = [r for r in rows if r["number"] not in per and (r["siret"] or "")[:9] in s9 and r["siret"] not in sirets]
print("même SIREN, autre SIRET, hors périmètre :", len(sir9), sum(r["dossiersCount"] or 0 for r in sir9))
for r in sorted(sir9, key=lambda r: -(r["dossiersCount"] or 0))[:60]: print(show(r))
