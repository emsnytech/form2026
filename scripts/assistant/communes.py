#!/usr/bin/env python3
"""Produit donnees/assistant/communes.json : les communes, pour reconnaître un lieu dans la question (moteur.js, Moteur.lieux).

Source : API Géo de l'État (geo.api.gouv.fr), « communes actuelles ». Pour chaque commune : nom normalisé (minuscules, sans
accents ni ponctuation, comme norm() du moteur), nom, code INSEE, département, population (pour départager les homonymes).

    python3 scripts/assistant/communes.py
"""
import json, re, sys, unicodedata, urllib.request, datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
SORTIE = RACINE / "donnees" / "assistant" / "communes.json"
URL = "https://geo.api.gouv.fr/communes?fields=nom,code,codeDepartement,population&format=json"


def norm(s):
    s = unicodedata.normalize("NFD", (s or "").lower()).encode("ascii", "ignore").decode()
    return " ".join(re.findall(r"[a-z0-9]+", s))


def main():
    l = json.load(urllib.request.urlopen(urllib.request.Request(URL, headers={"User-Agent": "FORM2026"}), timeout=120))
    communes = sorted(([norm(c["nom"]), c["nom"], c["code"], c.get("codeDepartement") or "", c.get("population") or 0] for c in l),
                      key=lambda c: (c[0], -c[4]))
    SORTIE.write_text(json.dumps({"source": "API Géo de l'État (geo.api.gouv.fr), communes actuelles", "date": datetime.date.today().isoformat(),
                                  "champs": ["nom_normalise", "nom", "code", "departement", "population"], "communes": communes},
                                 ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"écrit : {SORTIE.relative_to(RACINE)} ({len(communes)} communes, {SORTIE.stat().st_size // 1024} Ko)")


if __name__ == "__main__":
    sys.exit(main())
