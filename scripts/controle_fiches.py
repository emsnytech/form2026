#!/usr/bin/env python3
"""Contrôle ce qui est publié pour les fiches ministères. Sort en erreur si un point échoue.

- aucune adresse électronique et aucun titre sensible dans les pages, les données et la méthode ;
- la réserve de méthode figure dans chaque fiche, dans l'index et dans leurs gabarits ;
- la méthode ne dépend d'aucun chemin de poste, et son index liste tous ses fichiers ;
- aucun intitulé ne présente une part du fichier comme une part de la plateforme.

    python3 scripts/controle_fiches.py
"""
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
DONNEES = RACINE / "donnees/fiches-ministeres"
METHODE = DONNEES / "methode"
PAGES = [RACINE / "fiches-ministeres" / n for n in ("index.html", "education.html", "justice.html")]
GABARITS = [METHODE / "fiche" / n for n in ("gabarit_fiche.html", "gabarit_justice.html", "gabarit_index.html")]

COURRIEL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}")
# Écrit en expressions, pour que ce motif ne contienne lui-même aucun titre en clair.
SENSIBLE = re.compile(
    r"consultation[ -]du[ -]casier|efface(?:ment)[ -]du[ -]b2|requ[êe]te[ -]en[ -]efface|suites?[ -]judiciaires?"
    r"|suites?[ -]de[ -]plainte|bulletin[ ]n|assistance[ -][ée]ducative|consulter[ -]une[ -]proc",
    re.I,
)
RESERVE = "ne recouvre pas toutes les démarches"
# Fichiers où ces motifs servent au contrôle ou décrivent les catégories, sans citer de démarche.
EXCEPTIONS_SENSIBLE = {"LISEZMOI_fiches-ministeres.md"}
EXCEPTIONS_COURRIEL = {"confidentialite.py"}  # ses tests utilisent le domaine réservé exemple.invalid
CHEMIN_POSTE = re.compile(r"expanduser|/Users/|~/Documents")
INTITULE = re.compile(r"Part plateforme|Part de la plateforme|Part des publications de la plateforme|Part du stock de la plateforme|part_plateforme")


def fichiers_publies(base):
    """Fichiers de la méthode destinés au dépôt : ni sorties, ni données locales, ni fiches construites."""
    for p in sorted(base.rglob("*")):
        if not p.is_file():
            continue
        r = p.relative_to(base).as_posix()
        if r.startswith("out/") or "__pycache__" in r or re.fullmatch(r"fiche/fiche-[a-z]+\.html", r):
            continue
        if r.startswith("data/") and r != "data/nb_dossiers_deposes_par_mois.csv":
            continue
        yield p, r


def texte(p):
    return p.read_text(encoding="utf-8", errors="ignore")


def main():
    erreurs = []
    a_lire = PAGES + sorted(DONNEES.glob("*.json")) + sorted(DONNEES.glob("*.md")) + [p for p, _ in fichiers_publies(METHODE)]
    for p in a_lire:
        t, nom = texte(p), p.relative_to(RACINE)
        if p.name not in EXCEPTIONS_COURRIEL and COURRIEL.search(t):
            erreurs.append(f"adresse électronique dans {nom}")
        if p.name not in EXCEPTIONS_SENSIBLE:
            m = SENSIBLE.search(t)
            if m:
                erreurs.append(f"titre sensible dans {nom}")
        if INTITULE.search(t) and p.name != "controle_fiches.py":
            erreurs.append(f"intitulé « part de la plateforme » dans {nom}")
    for p in PAGES + GABARITS:
        if RESERVE not in texte(p).replace(" ", " "):
            erreurs.append(f"réserve de méthode absente de {p.relative_to(RACINE)}")
    for p, r in fichiers_publies(METHODE):
        if p.suffix in {".py", ".sh", ".json"} and CHEMIN_POSTE.search(texte(p)):
            erreurs.append(f"chemin de poste dans methode/{r}")
    index = texte(METHODE / "index.html")
    for _, r in fichiers_publies(METHODE):
        if r != "index.html" and f'href="{r}"' not in index:
            erreurs.append(f"methode/index.html ne liste pas {r}")
    if erreurs:
        print("\n".join(erreurs))
        return 1
    print(f"Fiches ministères : {len(a_lire)} fichiers contrôlés, aucun écart.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
