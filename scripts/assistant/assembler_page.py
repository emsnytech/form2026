#!/usr/bin/env python3
"""Recopie scripts/assistant/moteur.js dans trouver-sa-demarche.html, entre les marqueurs /*moteur:début*/ et /*moteur:fin*/.

moteur.js est la source unique du moteur : la page n'en porte qu'une copie, produite par ce script (même principe que
scripts/sync_nav.py). Les tests (test_moteur.js) portent donc sur le code exact que la page exécute.

    python3 scripts/assistant/assembler_page.py           # écrit la page si le moteur a changé
    python3 scripts/assistant/assembler_page.py --check   # n'écrit rien, sort en erreur (1) si la page diffère
"""
import re, sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
PAGE, MOTEUR = RACINE / "trouver-sa-demarche.html", Path(__file__).with_name("moteur.js")
DEBUT, FIN = "/*moteur:début*/", "/*moteur:fin*/"

t = PAGE.read_text(encoding="utf-8")
if DEBUT not in t or FIN not in t:
    sys.exit(f"{PAGE.name} : marqueurs {DEBUT} … {FIN} absents")
n = re.sub(re.escape(DEBUT) + ".*?" + re.escape(FIN), lambda m: DEBUT + "\n" + MOTEUR.read_text(encoding="utf-8").rstrip("\n") + "\n" + FIN, t, count=1, flags=re.S)
if n == t:
    print("Moteur de la page : à jour.")
elif "--check" in sys.argv:
    print(f"{PAGE.name} : le moteur diffère de scripts/assistant/moteur.js (lancer scripts/assistant/assembler_page.py)"); sys.exit(1)
else:
    PAGE.write_text(n, encoding="utf-8"); print(f"écrit : {PAGE.name}")
