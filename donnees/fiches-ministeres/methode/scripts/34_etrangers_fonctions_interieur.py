"""Fiche Intérieur, étape 2 (b) : démarches « étrangers » classées par fonction et par déposant, et par année. Open data seul.
Règles (premier motif qui correspond, sur le titre) :
- déposant « employeur ou tiers » : employeur, vérification ou authentification de titres, opérateurs et gestionnaires de places,
  appels à projets ; sinon « personne concernée » ;
- un titre « hors (démarches) ANEF » est un dépôt, compté aussi à part ;
- fonction : rendez-vous (dont points d'accueil numérique) ; contact et renseignement ; complément ou suivi (dont ANEF) ; dépôt d'une demande (le reste).
Sortie : out/interieur_etrangers.json (comptes seulement, aucun titre ni contact)."""
import json, re, sys, collections as C
sys.argv = ["x", "scripts/config_interieur.json", "/dev/null"]
exec(open("scripts/32_local_national_interieur.py").read().split("clusters = []")[0])
nd = lambda L: sum(r["dossiersCount"] or 0 for r in L)
E = [r for r in per if r["fam"] in ("Étrangers : séjour, asile, nationalité", "Étrangers : vérification d'un titre avant embauche")]
TIERS = re.compile(r"employeur|embauche|authentification|v[ée]rification|op[ée]rateurs?|gestionnaires?|places? (dans le|du) DNA|\bDNA\b|\bCADA\b|\bHUDA\b|appel [àa] projets?|consultation pour l.externalisation|prestataire|structures?|organismes?|associations?|\bcollecte\b|questionnaire", re.I)
FONCTION = [("rendez-vous", re.compile(r"rendez.vous|\brdv\b|accueil num[ée]rique|\bPAN\b|cr[ée]neau|convocation", re.I)),
            ("contact et renseignement", re.compile(r"contact|renseignement|question|nous [ée]crire|[ée]crire [àa]|autre demande|information", re.I)),
            ("complément ou suivi", re.compile(r"(?<!hors d[ée]marches )(?<!hors )\bANEF\b|compl[ée]ter|compl[ée]ment|blocage|suivi|changement d.adresse|modif|duplicata|perte|vol\b|retrait|remise", re.I))]
def fonction(t):
    for n, rx in FONCTION:
        if rx.search(t or ""): return n
    return "dépôt d'une demande"
for r in E:
    r["dep"] = "employeur ou tiers" if (r["fam"].startswith("Étrangers : vérification") or TIERS.search(r["title"] or "")) else "personne concernée"
    r["fct"] = fonction(r["title"])
    r["recep"] = bool(re.search(r"r[ée]c[ée]piss[ée]|attestation de prolongation|\bAPS\b|prolongation", r["title"] or "", re.I))
out = {"total": [len(E), nd(E)], "par_deposant": {}, "par_fonction_personne": {}, "par_annee": {}}
for dep in ("personne concernée", "employeur ou tiers"):
    L = [r for r in E if r["dep"] == dep]; out["par_deposant"][dep] = [len(L), nd(L), sum(r["state"] == "publiee" for r in L)]
P = [r for r in E if r["dep"] == "personne concernée"]
for f in ("dépôt d'une demande", "rendez-vous", "contact et renseignement", "complément ou suivi"):
    L = [r for r in P if r["fct"] == f]
    out["par_fonction_personne"][f] = {"demarches": len(L), "dossiers": nd(L), "publiees_aujourdhui": sum(r["state"] == "publiee" for r in L),
        "emetteurs": len({na(r["organisme"]).strip() for r in L}), "dont_recepisses_prolongations": [sum(r["recep"] for r in L), nd([r for r in L if r["recep"]])]}
for y in range(2018, 2027):
    row = {}
    for f in ("dépôt d'une demande", "rendez-vous", "contact et renseignement", "complément ou suivi"):
        L = [r for r in P if r["fct"] == f]
        row[f] = {"publiees": sum((r["datePublication"] or "")[:4] == str(y) for r in L), "closes": sum(bool(fin(r)) and fin(r).year == y for r in L),
                  "actives_fin_annee": sum(stock(r, y) for r in L), "dossiers_cohorte": nd([r for r in L if (r["datePublication"] or "")[:4] == str(y)])}
    out["par_annee"][str(y)] = row
hors = [r for r in P if re.search(r"hors (d[ée]marches? )?ANEF", r["title"] or "", re.I)]
out["titres_hors_anef"] = {"demarches": len(hors), "dossiers": nd(hors), "annees": dict(C.Counter((r["datePublication"] or "")[:4] for r in hors))}
anef = [r for r in P if re.search(r"\bANEF\b", r["title"] or "", re.I)]
out["titres_citant_anef"] = {"demarches": len(anef), "dossiers": nd(anef), "annees": dict(C.Counter((r["datePublication"] or "")[:4] for r in anef))}
nat = [r for r in E if r["niv"] == "nationale"]; out["niveau"] = {k: [len([r for r in E if r["niv"] == k]), nd([r for r in E if r["niv"] == k])] for k in ("locale", "nationale", "indeterminee")}
out["provenance"] = {k: [len([r for r in E if r["src"] == k]), nd([r for r in E if r["src"] == k])] for k in ("zone", "zone_multi", "nom_organisme")}
json.dump(out, open("out/interieur_etrangers.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in out.items() if k != "par_annee"}, ensure_ascii=False, indent=1))
print("année | dépôt pub/clo/stock/doss | rdv | contact | complément")
for y, row in out["par_annee"].items(): print(y, " | ".join(f'{v["publiees"]}/{v["closes"]}/{v["actives_fin_annee"]}/{v["dossiers_cohorte"]}' for v in row.values()))
