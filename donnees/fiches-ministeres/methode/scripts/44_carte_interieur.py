"""Fiche Intérieur : données de la carte de la section « Appropriation ». Mêmes règles que l'analyse A du script 40
(instructeur « préfecture ou sous-préfecture », rattachement au département) : par département, familles de politiques couvertes
par une démarche en ligne aujourd'hui (1 à 7), démarches en ligne, démarches publiées depuis l'origine, dossiers.
Aucune couche par famille. Sortie keyed par code de département, sans nom : out/interieur_carte.json
(les noms ne viennent que de fiche/carte_departements.json, pour l'infobulle)."""
import json, collections as C
src40 = open("scripts/40_variete_departements_interieur.py").read()
exec(src40.split("# réglementations uniformes")[0].replace('out["A"]["unites_regionales"]', "_u"))
L = [r for r in per if r["instr"] == PREF and r["dep"]]
par = {k: [r for r in L if r["dep"] == k] for k in DEPS}
carte = {k: {"familles_en_ligne": len({r["pol"] for r in v if r["state"] == "publiee"}), "en_ligne": sum(r["state"] == "publiee" for r in v),
             "depuis_origine": len(v), "dossiers": nd(v)} for k, v in par.items()}
VA = json.load(open("out/interieur_variete.json"))["A"]["prefectures"]
assert dict(sorted(C.Counter(str(x["familles_en_ligne"]) for x in carte.values()).items())) == VA["familles_couvertes_en_ligne"], "écart avec le script 40"
json.dump({"regle": "préfecture ou sous-préfecture, rattachement du script 40", "departements": carte}, open("out/interieur_carte.json", "w"), ensure_ascii=False, indent=1)
print(len(carte), dict(C.Counter(x["familles_en_ligne"] for x in carte.values())))
