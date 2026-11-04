#!/usr/bin/env python3
"""Construit la référence unique des téléchargements par formulaire à partir de l'export DILA.

    python3 scripts/telechargements_dila.py "<volumetrie DILA.tab.csv>"  →  donnees/gains/telechargements_dila.csv

L'export n'a pas d'en-tête. Lecture déduite, non confirmée par la DILA :
  telech_fichier = colonne 10, identique pour toutes les fiches qui partagent une même adresse de formulaire ;
  telech_fiches  = colonne 11, propre à chaque fiche, additionnée sur les fiches du formulaire.
La valeur retenue est la plus élevée des deux. Une ligne par fiche est aussi écrite pour les listes indexées par fiche.
"""
import collections, csv, io, re, sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
RENVOIS = {"16702": ["R11646"]}  # cette déclaration préalable figure dans l'export sous un autre numéro
brut = open(sys.argv[1], encoding="utf-8", newline="").read()
lignes = [r for r in csv.reader(io.StringIO(brut.replace("\r", "\n"))) if r[4].strip()]
par = collections.defaultdict(list)
for r in lignes:
    numeros = {n for n in re.split(r"[,;\s]+", r[5].strip()) if n}
    numeros |= set(re.findall(r"cerfa_(\d+)", r[7] + " " + r[8]))
    for n in numeros:
        par[n].append(r)
for n, fiches in RENVOIS.items():
    par[n] += [r for r in lignes if r[4] in fiches]
ent = lambda x: int(x) if x.strip().isdigit() else 0
with open(RACINE / "donnees/gains/telechargements_dila.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["cle", "type", "telech_fichier", "telech_fiches", "telech_retenu"])
    for n in sorted(par):
        rs = par[n]
        a, b = max(ent(r[9]) for r in rs), sum(ent(r[10]) for r in rs)
        w.writerow([n, "cerfa", a, b, max(a, b)])
    for r in sorted(lignes, key=lambda r: r[4]):
        w.writerow([r[4], "fiche", ent(r[9]), ent(r[10]), max(ent(r[9]), ent(r[10]))])
print(len(par), "formulaires,", len(lignes), "fiches")
