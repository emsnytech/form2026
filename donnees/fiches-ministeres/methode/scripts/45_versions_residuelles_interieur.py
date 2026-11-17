"""Fiche Intérieur, arbitrage n° 28 : versions locales encore en ligne d'une procédure devenue nationale (NEPH, label des
écoles de conduite, DETR et DSIL). Mêmes définitions que le script 40 (mots du titre, rattachement au département, dates
nationales du test B). Open data seul.

Pour chaque procédure : versions locales en ligne à la date d'extraction, départements, versions publiées au plus tard à la
date nationale, années de publication, millésimes du titre, demandes de paiement ou de versement (mots du titre), dossiers.
Dossiers récents : écart entre le compte de l'extraction et celui du descriptif ouvert du 1er novembre 2025 (data.gouv.fr,
fichier postérieur aux trois dates nationales), dont le chemin est passé par FORM2026_RAW_PRECEDENT ; une version absente
de ce fichier compte tous ses dossiers.
Sortie : out/interieur_residuelles.json (comptes, aucun nom de territoire)."""
import io, os, json, re, contextlib, collections as C
src40 = open("scripts/40_variete_departements_interieur.py").read().split("json.dump(out")[0]
with contextlib.redirect_stdout(io.StringIO()):
    exec(src40)
PRECEDENT = os.environ.get("FORM2026_RAW_PRECEDENT", "data/20251101075502-demarches.json")
DATE_PRECEDENT = re.search(r"(20\d\d)(\d\d)(\d\d)\d{6}-demarches", PRECEDENT)
DATE_PRECEDENT = "-".join(DATE_PRECEDENT.groups())
avant_ = {r["number"]: (r.get("dossiersCount") or 0) for r in json.load(open(PRECEDENT))}
PAIEMENT = re.compile(r"paiement|versement|solde|acompte", re.I)
res = {"fichier_precedent": DATE_PRECEDENT, "procedures": {}}
for k, x in NATL.items():
    L = [r for r in SEL[k] if r["niv"] == "locale" and r["dep"] and r["state"] == "publiee"]
    rec = {r["number"]: (r["dossiersCount"] or 0) - avant_.get(r["number"], 0) for r in L}
    av = [r for r in L if d(r["datePublication"]) <= x["date"]]
    pa = [r for r in L if PAIEMENT.search(r["title"] or "")]
    res["procedures"][k] = {"date_nationale": str(x["date"]), "versions": len(L), "departements": len({r["dep"] for r in L}),
        "publiees_au_plus_tard_a_la_date_nationale": [len(av), len({r["dep"] for r in av})],
        "publiees_apres": [len(L) - len(av), len({r["dep"] for r in L if r not in av})],
        "annees_de_publication": dict(sorted(C.Counter(r["datePublication"][:4] for r in L).items())),
        "avec_millesime_dans_le_titre": sum(1 for r in L if re.search(r"20[12]\d", r["title"] or "")),
        "paiement_ou_versement": [len(pa), len({r["dep"] for r in pa}), sum(rec[r["number"]] for r in pa)],
        "dossiers": nd(L), "dossiers_recents": sum(rec.values()),
        "departements_avec_dossiers_recents": len({r["dep"] for r in L if rec[r["number"]] > 0}),
        "absentes_du_fichier_precedent": sum(1 for r in L if r["number"] not in avant_)}
    assert res["procedures"][k]["departements"] == out["uniformes"][k]["locales"]["departements_en_ligne"], "écart avec le script 40"
json.dump(res, open("out/interieur_residuelles.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
