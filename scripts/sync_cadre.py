#!/usr/bin/env python3
"""Produit le cadre d'entrée des pages qui s'appuient sur le descriptif ouvert des démarches, et l'écrit entre deux marqueurs.

Le cadre dit ce que la page décrit (le corpus publié, pas l'activité complète) et quel rattachement elle retient. Il n'est jamais
écrit à la main : ce script en est la seule source, comme sync_nav.py pour la barre de navigation.

    python3 scripts/sync_cadre.py           # écrit le cadre dans chaque page de PAGES
    python3 scripts/sync_cadre.py --check   # n'écrit rien, sort en erreur si une page manque de cadre ou diffère

Une nouvelle page qui publie des chiffres tirés du descriptif ouvert s'ajoute à PAGES. Les fiches ministères produisent le même
premier paragraphe par leurs gabarits ; le contrôle vérifie qu'il est identique à celui de ce script.
"""
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
DEBUT, FIN = "<!-- cadre:début -->", "<!-- cadre:fin -->"
STATS = '<a href="https://demarche.numerique.gouv.fr/stats" target="_blank" rel="noopener">compteur public de la plateforme</a>'
STYLE = ("<style>.cadre{margin:22px 0 0;padding:14px 18px;border-left:4px solid var(--accent,#b45309);background:var(--surface,transparent);"
         "border-radius:0 8px 8px 0;max-width:78ch}.cadre p{margin:0 0 10px;font-size:.98rem;line-height:1.55}.cadre p:last-child{margin:0}</style>")
# Texte commun, une seule source. Les gabarits des fiches portent la même phrase centrale : le contrôle le vérifie.
CENTRE = ("À l'échelle de la plateforme, environ un dossier sur huit ne figure pas dans ce descriptif, en moyenne sur l'ensemble de l'historique de la plateforme, "
          "et environ un quart des démarches, cette seconde part comprenant une forte proportion de démarches n'ayant jamais reçu de dossier. "
          "Ces ordres de grandeur s'obtiennent en retranchant le fichier ouvert du " + STATS + ", relevé le 24 octobre 2026. "
          "Les absences s'expliquent par les règles de publication inscrites dans le code de la plateforme (paramètre de publication désactivé par le service, "
          "absence de dossier, adresse de site web contenant « mail » ou « intra »), et par la suppression de démarches.")

PAGES = {
    "collectivites/index.html": {
        "decrit": "<b>Ce que cette page décrit.</b> Elle porte sur les démarches publiées dans le descriptif ouvert de la plateforme, et non sur l'ensemble des démarches dématérialisées des collectivités ou destinées aux collectivités. ",
        "fin": " Les nombres de démarches et de dossiers donnés ci-dessous portent donc sur un corpus publié. Les montants de subventions viennent d'autres sources ouvertes, citées dans la méthode.",
        "rattachement": "<b>Comment les démarches sont rattachées aux collectivités.</b> Deux ensembles sont distingués. « Par les collectivités » : les démarches dont le service a déclaré le type d'organisme « collectivité territoriale », c'est-à-dire un rattachement par l'employeur. « Pour les collectivités » : les démarches d'autres organismes dont le titre désigne les collectivités ou une dotation, c'est-à-dire un rattachement par l'objet. Le second ensemble est un plancher, une démarche pouvant s'adresser aux collectivités sans le dire dans son titre.",
    },
}


def bloc(cfg):
    return (f"{DEBUT}\n  {STYLE}\n  <div class=\"cadre\">\n    <p>{cfg['decrit']}{CENTRE}{cfg['fin']}</p>\n"
            f"    <p>{cfg['rattachement']}</p>\n  </div>\n  {FIN}")


def appliquer(texte, cfg, nom):
    nouveau = bloc(cfg)
    if DEBUT in texte:
        return re.sub(re.escape(DEBUT) + ".*?" + re.escape(FIN), lambda m: nouveau, texte, count=1, flags=re.S)
    m = re.search(r'<p class="sub">.*?</p>', texte, re.S)
    if not m:
        sys.exit(f"{nom} : pas de sous-titre <p class=\"sub\"> après lequel placer le cadre")
    return texte[:m.end()] + "\n  " + nouveau + texte[m.end():]


def main():
    verifier = "--check" in sys.argv
    ecarts = []
    for rel, cfg in PAGES.items():
        p = RACINE / rel
        t = p.read_text(encoding="utf-8")
        n = appliquer(t, cfg, rel)
        if n != t:
            ecarts.append(rel)
            if not verifier:
                p.write_text(n, encoding="utf-8")
    phrase = CENTRE.split(" Ces ordres")[0]   # partie commune aux fiches, qui ont leur propre lien vers /stats
    for rel in ("fiches-ministeres/justice.html", "fiches-ministeres/education.html", "fiches-ministeres/index.html"):
        if phrase not in (RACINE / rel).read_text(encoding="utf-8"):
            ecarts.append(f"{rel} (phrase commune du cadre absente ou différente)")
    for e in ecarts:
        print(("à mettre à jour : " if verifier else "écrit : ") + e)
    if verifier and ecarts:
        return 1
    print(f"Cadre d'entrée : {len(PAGES)} page(s) produite(s), 3 fiches contrôlées, {'aucun écart' if not ecarts else str(len(ecarts)) + ' écart(s)'}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
