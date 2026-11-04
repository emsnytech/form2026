#!/usr/bin/env python3
"""Applique au classement CERFA d'explorer.html les statuts de
donnees/gains/classement_cerfa_statuts.json et écrit le détail du calcul.

Le fichier de statuts est la seule source des décisions. Le script est
rejouable : relancé, il remplace les statuts sans rien cumuler. Il s'arrête si
un motif de retrait ou de maintien ne correspond plus aux données.

    python3 scripts/classement_cerfa.py
"""
import csv
import json
import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
PAGE = RACINE / "explorer.html"
STATUTS = RACINE / "donnees/gains/classement_cerfa_statuts.json"
SORTIE = RACINE / "donnees/gains/classement_cerfa_detail.csv"
BLOC = re.compile(r'(<script type="application/json" id="data-cerfa">)(.*?)(</script>)', re.S)


def main():
    page = PAGE.read_text(encoding="utf-8")
    bloc = BLOC.search(page)
    cerfa = json.loads(bloc.group(2))
    statuts = json.loads(STATUTS.read_text(encoding="utf-8"))["statuts"]
    par_numero = {c["cerfa"]: c for c in cerfa}

    inconnus = set(statuts) - set(par_numero)
    assert not inconnus, f"statuts sans formulaire : {sorted(inconnus)}"

    for c in cerfa:
        c.pop("classement", None)
        s = statuts.get(c["cerfa"])
        if not s:
            continue
        assert c["total_central"] is not None, f"{c['cerfa']} n'est pas chiffré"
        c["classement"] = {k: v for k, v in s.items() if k != "titre_corrige"}
        if "titre_corrige" in s:
            c["titre"] = s["titre_corrige"]

    # Le test de double compte doit rester vrai sur les données.
    classes = {c["cerfa"] for c in cerfa if c["total_central"] is not None
               and c.get("classement", {}).get("statut") != "retire"}
    for numero, s in statuts.items():
        parent = s.get("parent_cerfa")
        if parent and s.get("parent_au_classement"):
            assert parent in classes, f"{numero} : parent {parent} absent du classement"
        if parent and s.get("parent_au_classement") is False:
            assert parent not in classes, f"{numero} : parent {parent} présent au classement"

    avec_gain = [c for c in cerfa if c["total_central"] is not None]
    retires = [c for c in avec_gain if c.get("classement", {}).get("statut") == "retire"]
    gardes = [c for c in avec_gain if c.get("classement", {}).get("statut") != "retire"]

    def somme(lignes, cle):
        return sum(c[cle] for c in lignes)

    for cle in ("total_bas", "total_central", "total_haut", "volumetrie_dila"):
        assert somme(gardes, cle) + somme(retires, cle) == somme(avec_gain, cle)

    with SORTIE.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["rang_avant", "rang_apres", "cerfa", "titre", "volumetrie_dila", "total_bas",
                    "total_central", "total_haut", "statut", "categorie", "motif_ou_mention"])
        ordre = sorted(avec_gain, key=lambda c: -c["total_central"])
        rang_apres = {c["cerfa"]: i for i, c in enumerate(
            sorted(gardes, key=lambda c: -c["total_central"]), 1)}
        for i, c in enumerate(ordre, 1):
            s = c.get("classement", {})
            w.writerow([i, rang_apres.get(c["cerfa"], ""), c["cerfa"], c["titre"], c["volumetrie_dila"],
                        c["total_bas"], c["total_central"], c["total_haut"], s.get("statut", "classe"),
                        s.get("categorie", ""), s.get("motif") or s.get("mention") or ""])

    texte = json.dumps(cerfa, ensure_ascii=False, separators=(",", ":"))
    assert "</script" not in texte.lower()
    PAGE.write_text(page[:bloc.start(2)] + texte + page[bloc.end(2):], encoding="utf-8")

    print(f"Avant : {len(avec_gain)} formulaires, {somme(avec_gain, 'total_bas'):,} / "
          f"{somme(avec_gain, 'total_central'):,} / {somme(avec_gain, 'total_haut'):,} €")
    print(f"Retirés : {len(retires)} formulaires, {somme(retires, 'total_central'):,} € (central)")
    print(f"Après : {len(gardes)} formulaires, {somme(gardes, 'total_bas'):,} / "
          f"{somme(gardes, 'total_central'):,} / {somme(gardes, 'total_haut'):,} €")
    print(f"Mentions : {sum(1 for c in gardes if 'classement' in c)}")
    for i, c in enumerate(sorted(gardes, key=lambda c: -c["total_central"])[:3], 1):
        print(f"  rang {i} : {c['cerfa']} {c['titre'][:70]} — {c['total_central']:,} €")


if __name__ == "__main__":
    main()
