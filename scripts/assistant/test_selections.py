#!/usr/bin/env python3
"""Tests de la colonne « Démarches nationales » (selections.colonne_nationale) et des fichiers de l'accueil.

    python3 scripts/assistant/test_selections.py
"""
import json, sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parent))
from selections import colonne_nationale  # noqa: E402

D = Path(__file__).resolve().parents[2] / "donnees" / "assistant"
echecs = 0


def verifie(nom, ok, detail=""):
    global echecs
    print(("OK      " if ok else "ÉCHEC   ") + nom + (f" — {detail}" if detail else ""))
    echecs += 0 if ok else 1


socle = [{"titre": "A", "ids": ["SP-R1"]}, {"titre": "B", "ids": ["SP-R2"]}, {"titre": "C", "ids": ["SP-R3"]}, {"titre": "D", "ids": ["SP-R4"]}]
ajout = {"titre": "Listes", "ids": ["SP-R16396"], "fiche": "SP-F1367", "position": 1, "jusqua": "2027-03-13", "raison": "r"}
ed = {"epingle": [], "exclu": ["SP-R1"], "etiquette": {}, "ajout": [ajout]}

l, s = colonne_nationale(socle, ed, "2027-03-13")
verifie("S1 editeur.ajout en 1re position jusqu'à sa date jusqua (incluse)", [x["titre"] for x in l] == ["Listes", "B", "C"] and not s,
        " | ".join(x["titre"] for x in l))
l, s = colonne_nationale(socle, ed, "2027-03-14")
verifie("S2 jusqua passée : la ligne sort, la ligne du socle suivante prend la place, la sortie est signalée",
        [x["titre"] for x in l] == ["B", "C", "D"] and [a["titre"] for a in s] == ["Listes"], " | ".join(x["titre"] for x in l))
verifie("S3 editeur.exclu écarte une ligne nationale par son id", all(x["titre"] != "A" for x in colonne_nationale(socle, ed, "2026-11-23")[0]))
verifie("S4 la ligne affichée ne garde ni position, ni jusqua, ni raison", set(colonne_nationale(socle, ed, "2026-11-23")[0][0]) <= {"titre", "ids", "fiche"})

# Fichiers publiés : une proposition d'actualité n'entre dans la colonne que validée (editeur.ajout ou editeur.epingle).
pd = json.loads((D / "plus_demandees.json").read_text(encoding="utf-8"))
an = json.loads((D / "actualite_nationales.json").read_text(encoding="utf-8"))
valides = {i for a in pd["editeur"].get("ajout", []) for i in a["ids"]}
colonne = {i for x in pd["nationales"] for i in x["ids"]}
non_valides = [p for p in an["propositions"] if set(p["ids"]) & colonne and not set(p["ids"]) <= valides]
verifie(f"S5 aucune des {len(an['propositions'])} propositions d'actualité non validées n'est dans la colonne", not non_valides,
        " | ".join(p["titre"] for p in non_valides))
for a in pd["editeur"].get("ajout", []):
    verifie(f"S6 editeur.ajout « {a['titre']} » porte position, jusqua et raison",
            a.get("position") in (1, 2, 3) and len(a.get("jusqua", "")) == 10 and bool(a.get("raison")), json.dumps({k: a.get(k) for k in ("position", "jusqua")}))

print("\nColonne nationale : " + ("tous les tests passent." if not echecs else f"{echecs} échec(s)."))
sys.exit(1 if echecs else 0)
