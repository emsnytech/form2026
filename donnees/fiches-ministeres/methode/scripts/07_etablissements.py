"""Les lycées et collèges qui utilisent le plus Démarche Numérique (pôle Éducation nationale).
Un établissement = un SIRET (à défaut, un libellé). Classement par dossiers des démarches actives sur la période.
Usage : python3 07_etablissements.py <config.json> <sortie.json>  (lancé depuis un dossier contenant data/demarches_slim.jsonl et scripts/02_fiche_ministere.py)"""
import json, sys, re, collections
cfg_path, out_path = sys.argv[1], sys.argv[2]
sys.argv = ["x", cfg_path, "/dev/null"]
exec(open("scripts/02_fiche_ministere.py").read().split("APIP =")[0])
SEC = re.compile(r"lyc[ée]e|coll[èe]ge|cit[ée] scolaire|\bLPO?\b|\bLGT\b|\bLEGT\b|\bEREA\b", re.I)
COL = re.compile(r"coll[èe]ge", re.I); LYC = re.compile(r"lyc[ée]e|\bLPO?\b|\bLGT\b|\bLEGT\b|cit[ée] scolaire", re.I)
SUP = re.compile(r"universit|\bIUT\b|INSPE|cnam|[ée]cole (nationale|sup|normale|centrale|polytech)|sciences ?po|crous|\bINSA\b|institut", re.I)
USAGES = [("Paye et gestion des personnels", r"groupement de paye|\bpaye\b|\bAED\b|\bAESH\b|contrats?\b|\bSFT\b|\bPSC\b|arr[êe]ts? maladie|entretiens? professionnels?"),
          ("Restauration et internat", r"demi-pension|restauration|cantine|internat|intendance|repas"),
          ("Post-bac (CPGE, BTS)", r"CPGE|\bBTS\b|classes? pr[ée]pa|\bDCG\b|post-?bac|[ée]tudiants?"),
          ("Bourses et aides", r"\bbourses?\b|boursiers?|fonds social|aides? (financi|sociale)"),
          ("Inscriptions et choix d'options", r"inscription|r[ée]inscription|candidature|admission|affectation|options?"),
          ("Voyages et sorties", r"voyage|sortie|s[ée]jour|[ée]change"),
          ("Gestion de l'établissement", r"agence comptable|r[ée]gie|march[ée]|denr[ée]es|signature|comptab|contr[ôo]le interne|appel [àa] comp[ée]tences|fournisseur|groupement d.achats|pr[ée]l[èe]vement|SEPA"),
          ("Vie scolaire et santé", r"infirmerie|sant[ée]|absence|autorisation|stage|PFMP")]
USAGES = [(n, re.compile(p, re.I)) for n, p in USAGES]
def usage(t):
    for n, rx in USAGES:
        if rx.search(t or ""): return n
    return "Autres"
per = []
for r in rows:
    p, s = classify(r)
    if p == "Éducation nationale" and any(is_active(r, y) for y in YEARS): per.append(r)
sec = [r for r in per if SEC.search((r["organisme"] or "") + " " + (r["service_nom"] or "")) and not SUP.search(r["organisme"] or "")]
# Un SIRET n'identifie l'établissement que s'il est surtout utilisé par des lycées ou collèges ;
# sinon (SIRET du rectorat ou de la DSDEN), on regroupe par libellé.
part_sec = collections.defaultdict(lambda: [0, 0])
for r in per:
    if r["siret"]:
        part_sec[r["siret"]][1] += 1
        if SEC.search(r["organisme"] or "") and not SUP.search(r["organisme"] or ""): part_sec[r["siret"]][0] += 1
SIRET_ETAB = {k for k, (a, b) in part_sec.items() if a / b >= 0.5}
sec = [r for r in sec if SEC.search(r["organisme"] or "") or r["siret"] in SIRET_ETAB]
def cle(r):
    if r["siret"] in SIRET_ETAB: return r["siret"]
    return "lib:" + re.sub(r"\s+", " ", (r["organisme"] or "").strip().lower())
g = collections.defaultdict(list)
for r in sec: g[cle(r)].append(r)
def label(L):
    c = collections.Counter((r["organisme"] or "").strip() for r in L)
    for lab, _ in c.most_common():
        if SEC.search(lab): return lab
    for r in L:
        m = re.search(r"(lyc[ée]e|coll[èe]ge|cit[ée] scolaire)[^-|:,(]{2,40}", r["title"] or "", re.I)
        if m: return m.group(0).strip()
    return c.most_common(1)[0][0]
def dossiers(L): return sum(r["dossiersCount"] or 0 for r in L)
tot = sum(dossiers(L) for L in g.values())
etabs = []
for k, L in g.items():
    lab = label(L)
    u = collections.Counter(usage(r["title"]) for r in L)
    top = max(L, key=lambda r: r["dossiersCount"] or 0)
    etabs.append({"siret": None if k.startswith("lib:") else k, "nom": lab,
        "type": "Collège" if COL.search(lab) and not LYC.search(lab) else ("Lycée" if LYC.search(lab) else "Établissement"),
        "departement": collections.Counter(r["departement"] for r in L if r["departement"]).most_common(1)[0][0] if any(r["departement"] for r in L) else None,
        "demarches": len(L), "dossiers": dossiers(L), "premiere_annee": min(r["datePublication"][:4] for r in L),
        "en_ligne": sum(1 for r in L if r["state"] == "publiee"),
        "champs_moyens": round(sum(r["n_champs"] for r in L) / len(L), 1),
        "annuaire_education": sum(1 for r in L if r["champs_types"].get("AnnuaireEducationChampDescriptor")),
        "quotient_familial": sum(1 for r in L if r["champs_types"].get("QuotientFamilialChampDescriptor")),
        "usages": dict(u.most_common()),
        "top": {"num": top["number"], "t": top["title"], "d": top["dossiersCount"] or 0, "url": top["url"]}})
etabs.sort(key=lambda e: -e["dossiers"])
top10 = etabs[:10]
res = {"etablissements": len(etabs), "lycees": sum(1 for e in etabs if e["type"] == "Lycée"), "colleges": sum(1 for e in etabs if e["type"] == "Collège"),
       "demarches": len(sec), "dossiers": tot, "part_top10": round(100 * sum(e["dossiers"] for e in top10) / tot, 1) if tot else None,
       "top10": top10, "top10_par_demarches": sorted(etabs, key=lambda e: -e["demarches"])[:10],
       "college_premier": next((e for e in etabs if e["type"] == "Collège"), None),
       "college_premier_rang": next((i + 1 for i, e in enumerate(etabs) if e["type"] == "Collège"), None)}
json.dump(res, open(out_path, "w"), ensure_ascii=False, indent=1)
print({k: v for k, v in res.items() if not k.startswith("top") and k != "college_premier"})
for e in top10: print(e["dossiers"], e["demarches"], e["type"], e["nom"], e["departement"], e["premiere_annee"], e["usages"])
print("collège le plus utilisateur :", res["college_premier"]["nom"], res["college_premier"]["dossiers"], res["college_premier"]["demarches"], "rang", etabs.index(res["college_premier"]) + 1)
