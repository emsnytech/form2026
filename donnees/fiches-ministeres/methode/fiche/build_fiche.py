"""Génère la fiche HTML d'un ministère à partir des sorties de 02_fiche_ministere.py, 03_familles.py, 04_reconductions.py.
Usage : python3 build_fiche.py <dossier_out> <prefixe> <gabarit.html> <sortie.html>
Les chiffres du texte sont calculés ici et injectés via des marqueurs «cle» : aucun chiffre n'est recopié à la main."""
import json, sys, os, re

out_dir, prefix, tpl_path, dst = sys.argv[1:5]
geo_path = sys.argv[5] if len(sys.argv) > 5 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "carte_departements.json")
E = json.load(open(os.path.join(out_dir, f"{prefix}.json")))
F = json.load(open(os.path.join(out_dir, f"{prefix}_familles.json")))
R = json.load(open(os.path.join(out_dir, f"{prefix}_reconductions.json")))
X = json.load(open(os.path.join(out_dir, f"{prefix}_complements.json")))
GEO = json.load(open(geo_path))
papier_path = os.path.join(out_dir, f"{prefix}_papier.json")
PAP = json.load(open(papier_path)) if os.path.exists(papier_path) else None

def n(x):  # entier à la française
    return f"{x:,}".replace(",", " ")
def p(x, d=1):  # pourcentage / décimal à la française
    return f"{x:.{d}f}".replace(".", ",")

A = {a["annee"]: a for a in E["annees"]}
P = {a["annee"]: a for a in E["annees_plateforme"]}
RC = {a["annee"]: a for a in R["perimetre"]}
RP = {a["annee"]: a for a in R["plateforme"]}
D = {a["annee"]: a for a in E["diffusion"]}
y0, y1 = E["config"]["annee_debut"], E["config"]["annee_fin"]
C = E["concentration_fenetre"]
anom = E.get("anomalies_exclues", [])
msa = [a for a in anom if (a["organisme"] or "").strip().upper() == "MSA"]

K = {
 "date": "21 octobre 2026", "y0": y0, "y1": y1,
 "total": n(E["perimetre"]["total"]), "dossiers_total": n(E["perimetre"]["dossiers_total"]),
 "pub0": n(A[y0]["publiees"]), "pub1": n(A[y1]["publiees"]),
 "pub_evol": p(100 * (A[y1]["publiees"] / A[y0]["publiees"] - 1), 0),
 "stock0": n(A[y0]["stock_fin_annee"]), "stock1": n(A[y1]["stock_fin_annee"]),
 "stock_ratio": p(A[y1]["stock_fin_annee"] / A[y0]["stock_fin_annee"], 1),
 "partpub0": p(100 * A[y0]["publiees"] / P[y0]["publiees"]), "partpub1": p(100 * A[y1]["publiees"] / P[y1]["publiees"]),
 "partstock0": p(100 * A[y0]["stock_fin_annee"] / P[y0]["stock_fin_annee"]), "partstock1": p(100 * A[y1]["stock_fin_annee"] / P[y1]["stock_fin_annee"]),
 "new0": n(RC[y0]["nouvelles"]), "new1": n(RC[y1]["nouvelles"]),
 "new_evol": p(100 * (RC[y1]["nouvelles"] / RC[y0]["nouvelles"] - 1), 0),
 "rec0": p(RC[y0]["pct_reconductions"]), "rec1": p(RC[y1]["pct_reconductions"]),
 "recmax": p(max(a["pct_reconductions"] for a in R["perimetre"])),
 "recp0": p(RP[y0]["pct_reconductions"]), "recp1": p(RP[y1]["pct_reconductions"]),
 "siret0": n(D[y0]["siret_emetteurs_actifs"]), "siret1": n(D[y1]["siret_emetteurs_actifs"]),
 "lib0": n(D[y0]["emetteurs_actifs"]), "lib1": n(D[y1]["emetteurs_actifs"]),
 "etab0": n(D[y0]["siret_etablissements_actifs"]), "etab1": n(D[y1]["siret_etablissements_actifs"]),
 "dep0": n(D[y0]["departements_actifs"]), "dep1": n(D[y1]["departements_actifs"]),
 "fen": n(C["demarches"]), "fen_dossiers": n(C["dossiers"]), "mediane": n(C["mediane_dossiers"]),
 "lt10": n(C["demarches_moins_10_dossiers"]), "lt10pct": p(100 * C["demarches_moins_10_dossiers"] / C["demarches"], 0),
 "top10": p(C["part_top10"]),
 "champs0": p(A[y0]["champs_moyens"]), "champs1": p(A[y1]["champs_moyens"]),
 "champsp0": p(P[y0]["champs_moyens"]), "champsp1": p(P[y1]["champs_moyens"]),
 "pj0": p(A[y0]["pj_moyennes"]), "pj1": p(A[y1]["pj_moyennes"]), "pjp1": p(P[y1]["pj_moyennes"]),
 "annu0": p(A[y0]["pct_annuaire_education"]), "annu1": p(A[y1]["pct_annuaire_education"]),
 "part1": p(A[y1]["pct_particuliers"], 0), "partp1": p(P[y1]["pct_particuliers"], 0),
 "siretch1": p(A[y1]["pct_siret"]), "iban1": p(A[y1]["pct_iban"]),
 "apip": n(sum(a["nb_api_particulier"] for a in E["annees"])),
 "inter": n(E["perimetre"]["exclues_interministerielles"]),
 "nomorg0": n((A[y0]["par_source"] or {}).get("nom_organisme", 0)),
 "nomorg1": n((A[y0 + 1]["par_source"] or {}).get("nom_organisme", 0)),
 "nomorg2": n((A[y0 + 2]["par_source"] or {}).get("nom_organisme", 0)),
 "sanszone0": n(next(c["publiees_sans_zone_plateforme"] for c in E["contexte_avant"] if c["annee"] == y0)),
 "sanszone1": n(next(c["publiees_sans_zone_plateforme"] for c in E["contexte_avant"] if c["annee"] == y0 + 1)),
 "sanszone2": n(next(c["publiees_sans_zone_plateforme"] for c in E["contexte_avant"] if c["annee"] == y0 + 2)),
 "msa_n": n(len(msa)), "msa_dossiers": n(sum(a["dossiersCount"] or 0 for a in msa)),
 "siret_manquant": n(E["siret_manquant"]),
 "js0": n(E["annees_par_pole"]["Jeunesse et sports"][0]["publiees"]),
 "jsmin": n(min(a["publiees"] for a in E["annees_par_pole"]["Jeunesse et sports"])),
 "tr0": n(E["transfert"]["par_annee"][str(y0)]), "trmax": n(max(E["transfert"]["par_annee"].values())),
}
DA = X["dossiers_annuels"]; GA = X["gains"]; QF = X["quotient_familial"]; QP = QF["plateforme_hors_perimetre"]
def meur(x): return p(x / 1e6, 1)
K.update({
 "dos_fen": n(round(sum(a["estime_brut"] for a in DA), -3)), "dos_fen_m": meur(sum(a["estime_brut"] for a in DA)),
 "dos_cale_m": meur(sum(a["estime_cale"] for a in DA)),
 "dos0": n(round(DA[0]["estime_brut"], -3)), "dos1": n(round(DA[-1]["estime_brut"], -3)),
 "dos_part0": p(DA[0]["part_plateforme"]), "dos_part1": p(DA[-1]["part_plateforme"]),
 "calmin": p(100 / max(a["calage"] for a in DA), 0), "calmax": p(100 / min(a["calage"] for a in DA), 0),
 "g_bas": meur(GA["bas"]), "g_haut": meur(GA["haut"]), "ga_bas": meur(GA["admin_bas"]), "ga_haut": meur(GA["admin_haut"]),
 "gu_bas": meur(GA["usagers_bas"]), "gu_haut": meur(GA["usagers_haut"]),
 "g_couv": p(100 * X["gains_couverture"]["dossiers_couverts"] / X["gains_couverture"]["dossiers_fenetre"], 1),
 "deps": n(len([k for k, v in X["carte"].items() if v["pub_t"] or v["org_t"]])), "sansdep": n(X["carte_sans_departement"]),
 "qf_n": n(len(QF["perimetre"])), "qf_d": n(sum(x["d"] for x in QF["perimetre"])),
 "qf_e": n(len({x["o"].strip().lower() for x in QF["perimetre"]})),
 "qfp_n": n(QP["demarches"]), "qfp_d": n(QP["dossiers"]), "qfp_e": n(QP["emetteurs"]), "qf_tot": n(QF["qf_plateforme_total"]),
})
qf1 = next(x for x in QF["perimetre"] if x["qf"])
K.update({"qf1_num": qf1["num"], "qf1_t": qf1["t"], "qf1_o": qf1["o"], "qf1_d": n(qf1["d"]), "qf1_c": n(qf1["c"]), "qf1_url": qf1["url"]})
fam = {f["famille"]: f for f in F}
rel = fam["Relevés de notes, attestations de réussite, diplômes"]
dp = fam["Demi-pension, restauration scolaire, internat"]
bo = fam["Bourses et fonds sociaux"]
K.update({
 "rel_n": n(rel["demarches"]), "rel_e": n(rel["emetteurs_distincts"]), "rel_d": n(rel["dossiers"]),
 "rel_min": n(rel["champs_min"]), "rel_max": n(rel["champs_max"]),
 "dp_n": n(dp["demarches"]), "dp_e": n(dp["emetteurs_distincts"]), "dp_d": n(dp["dossiers"]), "dp_qf": n(dp["avec_quotient_familial"]),
 "bo_n": n(bo["demarches"]), "bo_e": n(bo["emetteurs_distincts"]), "bo_qf": n(bo["avec_quotient_familial"]),
})
if PAP:
    PE = PAP["exemple_principal"]; PM = PAP["meta"]
    K.update({
     "papier_cerfa": PE["cerfa"], "papier_cerfa_titre": PE["cerfa_titre"], "papier_cerfa_url": PE["cerfa_url"],
     "papier_cerfa_administration": PE["cerfa_administration"],
     "papier_cerfa_champs": n(PE["cerfa_n_champs"]), "papier_cerfa_champs_prerempli": n(PE["cerfa_n_champs_prerempli"]),
     "papier_demarches_brutes": n(PE["demarches_brutes"]), "papier_tests": n(PE["tests_exclus"]),
     "papier_recours": n(PE["recours"]), "papier_declarations": n(PE["declarations_regime_transitoire"]),
     "papier_demandes_n": n(PE["demandes_autorisation"]),
     "papier_champs_min": n(PE["champs_min"]), "papier_champs_max": n(PE["champs_max"]),
     "papier_emetteurs": n(PE["emetteurs_departements"]), "papier_emetteurs_organisme": n(PE["emetteurs_organisme_distinct"]),
     "papier_departements_2025": n(PE["departements_depuis_2025"]),
     "papier_dossiers": n(PE["dossiers_total"]), "papier_dossiers_hors_recours": n(PE["dossiers_hors_recours"]),
     "papier_demarches_sans_siret": n(PE["demarches_sans_siret"]),
     "papier_demarches_hors_tests": n(PE["demarches_brutes"] - PE["tests_exclus"]),
     "papier_n_cerfa_total": n(PM["n_cerfa_total"]), "papier_n_dila_total": n(PM["n_dila_total"]),
     "papier_n_exclusions": n(PM["n_dila_exclusions"]),
    })

YEARS = list(range(y0, y1 + 1))
TYPES = [("service_deconcentre_de_l_etat", "Services déconcentrés (rectorats, DSDEN…)"),
         ("etablissement_enseignement", "Établissements d'enseignement"),
         ("administration_centrale", "Administration centrale"),
         ("autre", "Autres (opérateurs, GIP, non classés…)")]
def types_row(a):
    t = a["type_actives"]; known = {k for k, _ in TYPES[:3]}
    return [t.get(k, 0) for k, _ in TYPES[:3]] + [sum(v for k, v in t.items() if k not in known)]

DATA = {
 "years": YEARS,
 "pub_new": [RC[y]["nouvelles"] for y in YEARS], "pub_rec": [RC[y]["reconductions"] for y in YEARS],
 "closes": [A[y]["closes"] for y in YEARS], "stock": [A[y]["stock_fin_annee"] for y in YEARS],
 "actives": [A[y]["actives_dans_annee"] for y in YEARS],
 "part_pub": [round(100 * A[y]["publiees"] / P[y]["publiees"], 1) for y in YEARS],
 "part_stock": [round(100 * A[y]["stock_fin_annee"] / P[y]["stock_fin_annee"], 1) for y in YEARS],
 "poles": {k: [a["publiees"] for a in v] for k, v in E["annees_par_pole"].items()},
 "transfert": [E["transfert"]["par_annee"][str(y)] for y in YEARS],
 "types": {"labels": [l for _, l in TYPES], "rows": [types_row(D[y]) for y in YEARS]},
 "annuaire": [A[y]["pct_annuaire_education"] for y in YEARS],
 "qual": [{"annee": y, "champs": A[y]["champs_moyens"], "champs_p": P[y]["champs_moyens"], "pj": A[y]["pj_moyennes"], "pj_p": P[y]["pj_moyennes"],
           "annu": A[y]["pct_annuaire_education"], "siret": A[y]["pct_siret"], "iban": A[y]["pct_iban"], "rna": A[y]["pct_rna"],
           "apip": A[y]["nb_api_particulier"], "part": A[y]["pct_particuliers"], "part_p": P[y]["pct_particuliers"],
           "eph": A[y]["ephemeres_moins_3_mois"], "pub": A[y]["publiees"]} for y in YEARS],
 "diff": [{"annee": y, "lib": D[y]["emetteurs_actifs"], "siret": D[y]["siret_emetteurs_actifs"], "etab": D[y]["siret_etablissements_actifs"], "dep": D[y]["departements_actifs"]} for y in YEARS],
 "familles": [{"nom": f["famille"], "n": f["demarches"], "e": f["emetteurs_distincts"], "d": f["dossiers"], "min": f["champs_min"], "max": f["champs_max"],
               "moy": f["champs_moyens"], "pj": f["pj_moyennes"], "qf": f["avec_quotient_familial"], "annu": f["avec_annuaire_education"],
               "ex": [{"num": x["number"], "t": x["title"], "o": x["organisme"], "d": x["dossiers"], "c": x["n_champs"]} for x in f["exemples"][:3]]}
              for f in sorted(F, key=lambda f: -f["demarches"])],
 "top": [{"num": t["number"], "t": t["title"], "o": t["organisme"], "pole": t["pole"], "d": t["dossiersCount"], "y": t["datePublication"][:4],
          "etat": t["state"], "c": t["n_champs"], "pj": t["pj"]} for t in E["top_demarches_fenetre"][:12]],
 "anomalies": [{"num": a["number"], "t": a["title"], "o": a["organisme"], "d": a["dossiersCount"], "z": a.get("zones")} for a in anom],
 "zones": E["zones_par_annee"],
 "dossiers": DA, "gains_annee": [X["gains_par_annee"][str(y)] for y in YEARS],
 "carte": X["carte"], "geo": GEO,
 "qf": QF["perimetre"], "qf_plat": QP["top"],
 "papier": PAP["candidats"] if PAP else None,
}
html = open(tpl_path).read()
PAPIER_BLOCKS = ["PAPIER_DEBUT|PAPIER_FIN", "PAPIER_BRIEF_DEBUT|PAPIER_BRIEF_FIN", "PAPIER_PISTE_DEBUT|PAPIER_PISTE_FIN", "PAPIER_JS_DEBUT|PAPIER_JS_FIN"]
if PAP:
    for pair in PAPIER_BLOCKS:
        a, b = pair.split("|")
        html = html.replace(f"<!--{a}-->", "").replace(f"<!--{b}-->", "")
else:
    for pair in PAPIER_BLOCKS:
        a, b = pair.split("|")
        html = re.sub(rf"<!--{a}-->.*?<!--{b}-->\n?", "", html, flags=re.S)
html = html.replace("/*DATA*/null", json.dumps(DATA, ensure_ascii=False))
missing = set(re.findall(r"«(\w+)»", html)) - set(K)
if missing: raise SystemExit(f"marqueurs sans valeur : {missing}")
html = re.sub(r"«(\w+)»", lambda m: str(K[m.group(1)]), html)
open(dst, "w").write(html)
print("ok", dst, len(html))
