#!/usr/bin/env python3
"""Construit la référence des téléchargements par formulaire à partir du fichier de la DILA.

    python3 scripts/telechargements_dila.py "<volumetrie DILA BIS.xlsx>"  →  donnees/gains/telechargements_dila.csv

Le fichier donne, par version de Cerfa, le « Nombre de téléchargements sur GF » sur un an à fin 2024.
Le CSV garde une ligne par version. Un formulaire vaut la somme de ses versions. Nécessite openpyxl.
"""
import csv, sys
from pathlib import Path
import openpyxl

RACINE = Path(__file__).resolve().parent.parent
feuille = openpyxl.load_workbook(sys.argv[1], data_only=True).worksheets[0]
lignes = list(feuille.iter_rows(values_only=True))
assert [str(x) for x in lignes[0][:3]] == ["Formulaire", "Intitulé", "Nombre de téléchargements sur GF"], lignes[0]
with open(RACINE / "donnees/gains/telechargements_dila.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["formulaire", "numero", "telechargements"])
    for r in sorted(lignes[1:], key=lambda r: str(r[0])):
        w.writerow([r[0], str(r[0]).split("*")[0], int(r[2])])
print(len(lignes) - 1, "versions,", sum(int(r[2]) for r in lignes[1:]), "téléchargements")
