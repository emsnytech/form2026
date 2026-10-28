#!/usr/bin/env python3
"""Synchronise la barre de navigation unifiée (rubriques) sur les pages du site.

Lit `ressources.json` (ordre et libellés des rubriques) et réécrit, dans chaque
page HTML qui porte les marqueurs `<!-- nav:début -->` / `<!-- nav:fin -->`, le
contenu de la barre de navigation entre ces deux marqueurs. Le HTML produit est
statique : aucune dépendance au chargement de ressources.json par le navigateur
une fois la page publiée.

Rubrique de la page courante : lue sur l'attribut `data-rubrique="..."` porté
par l'élément qui entoure les marqueurs (ex. `<p class="topnav" data-rubrique="mesurer">`).
Une valeur vide ou absente ne marque aucune entrée comme page courante (cas de
l'accueil, qui n'appartient à aucune rubrique en particulier).

Idempotent : relancer ce script sans changement de source ne produit aucune
différence (la génération est déterministe).

Usage :
    python3 scripts/sync_nav.py           # applique et écrit les fichiers modifiés
    python3 scripts/sync_nav.py --check    # n'écrit rien, sort en erreur (1) si une page serait modifiée
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESSOURCES = ROOT / "ressources.json"

NAV_START = "<!-- nav:début -->"
NAV_END = "<!-- nav:fin -->"
CARRIER_RE = re.compile(
    r'(<[a-zA-Z][^>]*\bdata-rubrique="([^"]*)"[^>]*>)\s*' + re.escape(NAV_START) + r'(.*?)' + re.escape(NAV_END),
    re.S,
)

# Répertoires jamais parcourus (données, méthode, dossiers de travail non publiés).
EXCLUDE_DIR_PARTS = {"donnees", "methode", "methode-svr", "methode-outillage", "methode-canaux", "Claude outputs", "_fiches-ministeres", ".git"}


def load_ressources():
    data = json.loads(RESSOURCES.read_text(encoding="utf-8"))
    return data["ordre_rubriques"], data["rubriques"]


def build_nav_html(ordre, rubriques, rubrique_courante):
    parts = ['<a href="index.html">FORM 2026</a>']
    for k in ordre:
        verbe = rubriques[k]["verbe"]
        attr = ' aria-current="page"' if k == rubrique_courante else ""
        parts.append(f'<a href="index.html#{k}"{attr}>{verbe}</a>')
    return " · ".join(parts)


def iter_candidate_files():
    for path in sorted(ROOT.rglob("*.html")):
        rel_parts = set(path.relative_to(ROOT).parts)
        if rel_parts & EXCLUDE_DIR_PARTS:
            continue
        yield path


def sync_file(path, ordre, rubriques):
    text = path.read_text(encoding="utf-8")
    m = CARRIER_RE.search(text)
    if not m:
        return None  # pas de marqueurs : page hors périmètre de ce script
    rubrique_courante = m.group(2) or None
    if rubrique_courante and rubrique_courante not in rubriques:
        raise ValueError(f"{path}: data-rubrique={rubrique_courante!r} inconnue de ressources.json")
    new_inner = build_nav_html(ordre, rubriques, rubrique_courante)
    new_block = m.group(1) + NAV_START + new_inner + NAV_END
    new_text = text[: m.start()] + new_block + text[m.end():]
    changed = new_text != text
    if changed:
        path.write_text(new_text, encoding="utf-8")
    return changed


def main():
    check_only = "--check" in sys.argv
    ordre, rubriques = load_ressources()
    touched = []
    for path in iter_candidate_files():
        if check_only:
            text_before = path.read_text(encoding="utf-8")
        result = sync_file(path, ordre, rubriques)
        if result is None:
            continue
        rel = path.relative_to(ROOT)
        if check_only:
            text_after = path.read_text(encoding="utf-8")
            if text_after != text_before:
                print(f"serait modifiée : {rel}")
                touched.append(rel)
            # en mode --check, on a quand meme ecrit si result=True ; restaurer
            if result:
                path.write_text(text_before, encoding="utf-8")
        elif result:
            print(f"modifiée : {rel}")
            touched.append(rel)
        else:
            print(f"déjà à jour : {rel}")
    if check_only and touched:
        sys.exit(1)
    print(f"{len(touched)} page(s) modifiée(s)." if touched else "Aucune page à modifier (déjà à jour).")


if __name__ == "__main__":
    main()
