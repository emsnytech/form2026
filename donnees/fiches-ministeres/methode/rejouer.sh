#!/usr/bin/env bash
# Reconstruit les deux fiches depuis le fichier brut de l'open data, avec le seul code du dépôt, puis les publie dans l'arbre de travail.
# Usage : donnees/fiches-ministeres/methode/rejouer.sh <brut.json>   (voir REJOUER.md)
# Les relevés de pages vivantes (12, 15, 17, 22) ne sont pas relancés : leur dernier état daté publié sert d'entrée.
set -euo pipefail
BRUT="$(cd "$(dirname "${1:?chemin du fichier brut demarches.json}")" && pwd)/$(basename "$1")"
cd "$(dirname "$0")"
mkdir -p out data
cp ../../gains/demarches_gains_v8.csv data/
for f in justice_hors_opendata justice_experts_publics justice_siren_cours_appel rdv_cdad_metabase; do cp "../$f.json" out/; done

python3 scripts/01_extract_slim.py "$BRUT" data/demarches_slim.jsonl

for m in education justice; do
  python3 scripts/02_fiche_ministere.py "scripts/config_$m.json" "out/$m.json" > /dev/null
  python3 scripts/03_familles.py "scripts/config_$m.json" > /dev/null
  python3 scripts/04_reconductions.py "scripts/config_$m.json" "out/${m}_reconductions.json" > /dev/null
  python3 scripts/05_complements.py "scripts/config_$m.json" "out/${m}_complements.json" > /dev/null
done
python3 scripts/06_papier.py scripts/config_education.json out/education_papier.json > /dev/null
python3 scripts/07_etablissements.py scripts/config_education.json out/education_etablissements.json > /dev/null

python3 scripts/08_extrait_justice.py "$BRUT" data/justice_champs.jsonl > /dev/null
python3 scripts/09_inventaire_justice.py scripts/config_justice.json out/justice_inventaire.json > /dev/null
python3 scripts/10_classement_usages.py scripts/config_justice.json > /dev/null
python3 scripts/11_audit_perimetre.py scripts/config_justice.json > /dev/null
python3 scripts/13_scan_rdv_cdad.py "$BRUT" out/scan_rdv_cdad.jsonl > /dev/null

python3 fiche/build_fiche.py out education fiche/gabarit_fiche.html fiche/fiche-education.html > /dev/null
python3 fiche/build_justice.py > /dev/null
python3 integration/integrer_fiches.py
