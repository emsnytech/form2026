#!/usr/bin/env python3
"""Applique au classement CERFA d'explorer.html les statuts de
donnees/gains/classement_cerfa_statuts.json et écrit le détail du calcul.

Le fichier de statuts porte les décisions, telechargements_dila.csv les volumes.
Le script est rejouable : relancé, il ne change plus rien. Il s'arrête si un
motif de retrait ou de maintien ne correspond plus aux données.

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
TELECHARGEMENTS = RACINE / "donnees/gains/telechargements_dila.csv"
RESUME = re.compile(r'(<script type="application/json" id="data-cerfa-resume">)(.*?)(</script>)', re.S)
GAINS = ["gain_admin_bas", "gain_admin_central", "gain_admin_haut", "gain_usagers_demat",
         "gain_usagers_preremplissage_bas", "gain_usagers_preremplissage_central", "gain_usagers_preremplissage_haut"]
TOTAUX = ["total_bas", "total_central", "total_haut"]
BLOC = re.compile(r'(<script type="application/json" id="data-cerfa">)(.*?)(</script>)', re.S)


def lire_telechargements():
    with open(TELECHARGEMENTS, encoding="utf-8") as f:
        return {r["cle"]: r for r in csv.DictReader(f) if r["type"] == "cerfa"}


def appliquer_volume(c, retenu):
    """Recalcule les gains d'un formulaire au prorata de son nouveau volume ; rejouable."""
    avant = c["volumetrie_dila"]
    c.setdefault("volume_avant_correction", avant)
    if not retenu:
        c["volumetrie_dila"] = None
        for cle in GAINS + TOTAUX:
            c[cle] = None
        return
    k = retenu / avant
    c["volumetrie_dila"] = retenu
    for cle in GAINS:
        c[cle] = round(c[cle] * k)
    for scenario in ("bas", "central", "haut"):
        c[f"total_{scenario}"] = c[f"gain_admin_{scenario}"] + c["gain_usagers_demat"] + c[f"gain_usagers_preremplissage_{scenario}"]


def concordance(lignes):
    """Part des paires de formulaires rangées dans le même ordre par les téléchargements et par le volume réel."""
    bonnes = total = 0
    for i, x in enumerate(lignes):
        for y in lignes[i + 1:]:
            total += 1
            bonnes += (x["retenu"] - y["retenu"]) * (x["reel"] - y["reel"]) > 0
    return bonnes, total


def main():
    page = PAGE.read_text(encoding="utf-8")
    bloc = BLOC.search(page)
    cerfa = json.loads(bloc.group(2))
    config = json.loads(STATUTS.read_text(encoding="utf-8"))
    statuts = config["statuts"]
    telech = lire_telechargements()
    par_numero = {c["cerfa"]: c for c in cerfa}

    inconnus = set(statuts) - set(par_numero)
    assert not inconnus, f"statuts sans formulaire : {sorted(inconnus)}"

    for c in cerfa:
        c.pop("classement", None)
        if c.get("volumetrie_dila") is not None and c.get("total_central") is not None:
            t = telech.get(c["cerfa"].split("*")[0])
            appliquer_volume(c, int(t["telech_retenu"]) if t else 0)
        s = statuts.get(c["cerfa"])
        if not s:
            continue
        c["classement"] = {k: v for k, v in s.items() if k != "titre_corrige"}
        if "titre_corrige" in s:
            c["titre"] = s["titre_corrige"]

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
    en_ligne = [c for c in retires if c["classement"]["categorie"] == "en_ligne"]
    gardes = [c for c in avec_gain if c.get("classement", {}).get("statut") != "retire"]

    def somme(lignes, cle):
        return sum(c[cle] for c in lignes)

    ES = json.loads(re.search(r'id="data-essentielles">(.*?)</script>', page, re.S).group(1))
    calibrage = []
    for l in config["calibrage"]["lignes"]:
        # Plusieurs variantes peuvent porter ce début de titre : on garde la démarche principale, la plus volumineuse.
        e = max((x for x in ES if x["nom"].startswith(l["observatoire"]) and isinstance(x["volumetrie_totale"], (int, float))),
                key=lambda x: x["volumetrie_totale"])
        t = telech[l["cerfa"]]
        retenu = int(t["telech_retenu"])
        calibrage.append({"nom": l["nom"], "cerfa": l["cerfa"], "reel": int(e["volumetrie_totale"]), "fichier": int(t["telech_fichier"]),
                          "fiches": int(t["telech_fiches"]), "retenu": retenu, "rapport": round(retenu / e["volumetrie_totale"], 2)})
    calibrage.sort(key=lambda x: x["rapport"])
    bonnes, paires = concordance(calibrage)
    resume = {"avant": config["volume_publie_avant"], "calibrage": calibrage, "source_calibrage": config["calibrage"]["source"],
              "concordance": [bonnes, paires], "rapport_min": calibrage[0]["rapport"], "rapport_max": calibrage[-1]["rapport"],
              "apres_volumes": {t: somme(gardes, f"total_{t}") + somme(en_ligne, f"total_{t}") for t in ("bas", "central", "haut")},
              "apres": {t: somme(gardes, f"total_{t}") for t in ("bas", "central", "haut")}, "formulaires": len(gardes)}

    with SORTIE.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["rang", "cerfa", "titre", "telechargements_annuels", "volume_avant_correction", "total_bas",
                    "total_central", "total_haut", "statut", "categorie", "motif_ou_mention"])
        rang = {c["cerfa"]: i for i, c in enumerate(sorted(gardes, key=lambda c: -c["total_central"]), 1)}
        for c in sorted(cerfa, key=lambda c: -(c["total_central"] or 0)):
            if "volume_avant_correction" not in c:
                continue
            s = c.get("classement", {})
            w.writerow([rang.get(c["cerfa"], ""), c["cerfa"], c["titre"], c["volumetrie_dila"] or "", c["volume_avant_correction"],
                        c["total_bas"] or "", c["total_central"] or "", c["total_haut"] or "", s.get("statut", "classe"),
                        s.get("categorie", ""), s.get("motif") or s.get("mention") or ""])

    texte = json.dumps(cerfa, ensure_ascii=False, separators=(",", ":"))
    assert "</script" not in texte.lower()
    page = page[:bloc.start(2)] + texte + page[bloc.end(2):]
    r = json.dumps(resume, ensure_ascii=False, separators=(",", ":"))
    m = RESUME.search(page)
    page = page[:m.start(2)] + r + page[m.end(2):]
    PAGE.write_text(page, encoding="utf-8")
    print(json.dumps({k: v for k, v in resume.items() if k != "calibrage"}, ensure_ascii=False))
    for l in calibrage:
        print(l)
    for i, c in enumerate(sorted(gardes, key=lambda c: -c["total_central"])[:5], 1):
        print(f"  rang {i} : {c['cerfa']} {c['titre'][:60]} — {c['total_central']:,} €")


if __name__ == "__main__":
    main()
