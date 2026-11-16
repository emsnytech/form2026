"""Fiche Intérieur, arbitrage n° 27, § 4 bis : frais évités, même méthode que la fiche Éducation (script 05, partie 3).
Gain par dossier de chaque démarche repris de data/demarches_gains_v8.csv (paramètres v8 de FORM 2026), multiplié par ses
dossiers de la période 2021-2026 (compteur réparti au prorata des jours d'ouverture, comme le script 05). Fourchette basse et
haute ; part administration (coût de traitement évité) et part usagers (temps évité) ; taux de couverture du fichier de gains.
Propre à l'Intérieur : la même fourchette sans les médailles d'honneur du travail et agricoles (nature lue dans le titre,
script 33), par cohérence avec le tableau de sensibilité de l'en-tête. Le périmètre est celui de la fiche (script 02).
Sortie : out/interieur_frais_evites.json"""
import json, re, sys, os, collections
src05 = open("scripts/05_complements.py").read()
pre, gains = src05.split("# ---------- 2. Carte par département ----------")[0], src05.split("# ---------- 3. Gains (FORM 2026, v8) ----------")[-1].split("# ---------- 4.")[0]
sys.argv = ["x", "scripts/config_interieur.json", "/dev/null"]
exec(pre.replace("cfg_path, out_path = sys.argv[1], sys.argv[2]", "cfg_path, out_path = 'scripts/config_interieur.json', '/dev/null'"))
exec("def nature" + open("scripts/33_medailles_tests_interieur.py").read().split("def nature")[1].split("tab =")[0])
def na(s):
    import unicodedata; return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
FAM = json.load(open("scripts/familles_interieur.json"))
def famille(r):
    for f_ in FAM:
        if re.search(f_["motif"], r["title"] or "", re.I): return f_["nom"]
    return None
fen_all = [r for r in per if any(is_active(r, y) for y in YEARS)]
def calc(fen_):
    ns = dict(globals()); ns["fen"] = fen_          # un seul espace de noms : les générateurs du fragment voient r
    exec(gains, ns)
    return ns["gain"], ns["couv"]
out = {"methode": "script 05, partie 3 (gains v8 × dossiers de la période au prorata des jours d'ouverture)", "periode": [YEARS[0], YEARS[-1]]}
g, c = calc(fen_all)
out["perimetre"] = {"demarches_actives": len(fen_all), "gains": g, "couverture": c, "taux_couverture": round(100 * c["dossiers_couverts"] / c["dossiers_fenetre"], 1)}
MED = lambda r: famille(r) == "Médailles et distinctions" and nature(r["title"]) in ("travail", "agricole")
sans = [r for r in fen_all if not MED(r)]
g2, c2 = calc(sans)
out["sans_medailles_travail_agricoles"] = {"demarches_retirees": len(fen_all) - len(sans), "gains": g2, "couverture": c2,
                                          "taux_couverture": round(100 * c2["dossiers_couverts"] / c2["dossiers_fenetre"], 1)}
# coût évité par dossier pour l'administration, lu dans le fichier de gains (paramètre v8, France Stratégie 2018)
import csv as _csv
_u = {(round(float(l["gain_admin_bas"]) / float(l["nb_dossiers"]), 2), round(float(l["gain_admin_haut"]) / float(l["nb_dossiers"]), 2))
      for l in _csv.DictReader(open("data/demarches_gains_v8.csv", encoding="utf-8")) if float(l["nb_dossiers"] or 0) >= 100}
assert len(_u) == 1, f"coût administratif par dossier non constant : {sorted(_u)[:5]}"
out["cout_admin_par_dossier"] = list(_u.pop())
# contrôle sur le jeu « Utilisation du service » (dépôts mensuels), calcul du script 05 : part des dépôts publiés retrouvée par
# la méthode du prorata sur toute la plateforme, selon l'année. Comme dans la fiche Éducation, les gains ne sont pas recalés.
out["controle_utilisation_du_service"] = {"calage_par_annee": {str(y): calage[y] for y in YEARS},
    "part_retrouvee_min": round(100 / max(calage[y] for y in YEARS)), "part_retrouvee_max": round(100 / min(calage[y] for y in YEARS)),
    "gains_recales": False}
json.dump(out, open("out/interieur_frais_evites.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1))
