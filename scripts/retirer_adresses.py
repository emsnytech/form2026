#!/usr/bin/env python3
"""Retire les adresses électroniques de tout ce que le dépôt publie.

Une adresse sur la page d'une démarche n'est pas une liste d'adresses récupérable en un clic.

    python3 scripts/retirer_adresses.py --check   # n'écrit rien, sort en erreur si une adresse subsiste
    python3 scripts/retirer_adresses.py           # remplace les adresses dans les fichiers concernés

N'imprime jamais une adresse : seulement des fichiers et des comptes. Le remplacement se fait dans le texte brut,
pour ne rien changer d'autre au fichier. Tout générateur qui écrit des données publiées appelle masquer_donnees().
"""
import json
import re
import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
LIBELLE = "[adresse électronique retirée]"
# (?<!\\) : dans du JSON brut, le « n » de \n ne doit pas être pris pour le début d'une adresse.
ADRESSE = re.compile(r"(?<!\\)[\w.%+'-]+@[\w-]+(?:\.[\w-]+)*\.[A-Za-z]{2,}")
ENTOUREE = re.compile(r"[\[(]\s*" + ADRESSE.pattern + r"\s*[\])]")
# Domaine réservé par la RFC 2606 : les jeux de test des scripts peuvent l'employer, il ne désigne personne.
AUTORISE = re.compile(r"@exemple\.invalid\b", re.I)
SUFFIXES_BINAIRES = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".webp", ".woff", ".woff2", ".pdf", ".xlsx", ".docx", ".gz", ".zip", ".pptx"}


def masquer(texte):
    if not isinstance(texte, str) or "@" not in texte:
        return texte

    def remplace(m):
        return m.group(0) if AUTORISE.search(m.group(0)) else LIBELLE

    return ADRESSE.sub(remplace, ENTOUREE.sub(remplace, texte))


def masquer_donnees(x):
    """Applique masquer() à toutes les chaînes d'une structure JSON."""
    if isinstance(x, dict):
        return {k: masquer_donnees(v) for k, v in x.items()}
    if isinstance(x, list):
        return [masquer_donnees(v) for v in x]
    return masquer(x)


def fichiers_suivis():
    sortie = subprocess.run(["git", "ls-files", "-z"], cwd=RACINE, capture_output=True, text=True, check=True).stdout
    for rel in sortie.split("\0"):
        p = RACINE / rel
        if rel and p.is_file() and p.suffix.lower() not in SUFFIXES_BINAIRES:
            yield p


def compter(texte):
    return sum(not AUTORISE.search(m.group(0)) for m in ADRESSE.finditer(texte))


def main():
    verifier = "--check" in sys.argv
    trouve = {}
    for p in fichiers_suivis():
        t = p.read_text(encoding="utf-8", errors="surrogateescape")
        n = compter(t)
        if not n:
            continue
        trouve[p.relative_to(RACINE).as_posix()] = n
        if not verifier:
            nouveau = masquer(t)
            if p.suffix == ".json":
                json.loads(nouveau)  # le fichier doit rester du JSON valide
            p.write_text(nouveau, encoding="utf-8", errors="surrogateescape")
    total = sum(trouve.values())
    for rel, n in sorted(trouve.items()):
        print(f"{n:4d}  {rel}")
    print(f"{total} adresse(s) dans {len(trouve)} fichier(s)" + ("." if verifier else ", retirée(s)."))
    return 1 if verifier and total else 0


if __name__ == "__main__":
    sys.exit(main())
