#!/usr/bin/env python3
"""Mise à jour mensuelle de compteur-parametres.json pour FORM 2026 (compteur-roi.html).

Télécharge les séries mensuelles publiées par data.gouv.fr sur le jeu « Utilisation du service
demarche.numerique.gouv.fr ». Le fichier du dépôt est la seule source. Ne touche jamais à git.

    python3 scripts/update_compteur_parametres.py --publier              # écrit compteur-parametres.json
    python3 scripts/update_compteur_parametres.py                        # calcule et journalise, n'écrit rien
    python3 scripts/update_compteur_parametres.py --verifier-fraicheur   # sort en erreur si le site est en retard

N'écrit rien si un téléchargement échoue ou si une série requise est vide, et sort alors en erreur. Lancé par le
workflow maj-compteur.yml, qui propose le résultat et ouvre une issue en cas d'échec.
"""
import os
from pathlib import Path
import json, csv, io, re, sys, datetime, urllib.request, urllib.error

SITE = str(Path(__file__).resolve().parents[1])
PARAMS_FILE = f"{SITE}/compteur-parametres.json"

DATASET_SLUG = "utilisation-du-service-demarche-numerique-gouv-fr"
RESOURCE_IDS = {
    "depo": "26131021-33fd-4a37-9c30-11f63657ba62",   # dossiers déposés
    "crees": "fd0fd64e-bbda-428c-87da-50dffdacee78",   # dossiers créés
    "proc_creees": "5a1a8489-367b-4242-8de1-811572da5147",  # démarches créées
}
HEADERS = {"User-Agent": "FORM2026-compteur-update/1 (contact: cartographie FORM 2026)"}


def log(msg):
    line = f"{datetime.datetime.now().isoformat(timespec='seconds')} {msg}"
    print(line)


def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def parse_monthly_csv(raw_bytes):
    """CSV format: mois,valeur (header then rows like 2026-09,574693)."""
    text = raw_bytes.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows or len(rows) < 2:
        return {}
    out = {}
    for row in rows[1:]:
        if len(row) < 2:
            continue
        mois, val = row[0].strip(), row[1].strip()
        if not re.match(r"^\d{4}-\d{2}$", mois) or val == "":
            continue
        try:
            out[mois] = int(round(float(val)))
        except ValueError:
            continue
    return out


def download_series(resource_id):
    url = f"https://www.data.gouv.fr/api/1/datasets/r/{resource_id}"
    try:
        raw = fetch(url)
    except (urllib.error.URLError, TimeoutError) as e:
        log(f"ÉCHEC téléchargement {resource_id}: {e}")
        return None
    series = parse_monthly_csv(raw)
    if not series:
        log(f"Série vide ou illisible pour {resource_id}")
        return None
    return series


def find_proc_publiees_series():
    """Cherche dans le jeu de données une ressource « démarches publiées par mois ».
    Retourne la série (dict mois->valeur) si trouvée et non vide, sinon None."""
    url = f"https://www.data.gouv.fr/api/1/datasets/{DATASET_SLUG}/"
    try:
        raw = fetch(url)
    except (urllib.error.URLError, TimeoutError) as e:
        log(f"Impossible de lister les ressources du jeu de données ({e}) — proc_publiees non recherché")
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        log("Réponse illisible pour la liste des ressources — proc_publiees non recherché")
        return None
    for res in data.get("resources", []):
        title = (res.get("title") or "").lower()
        if "procedure" in title and "publi" in title and "mois" in title:
            rid = res.get("id")
            log(f"Série « démarches publiées par mois » trouvée : {title} ({rid})")
            series = download_series(rid)
            if series:
                return series
            return None
    return None


def main():
    log("--- Démarrage mise à jour mensuelle compteur-parametres.json ---")

    series = {}
    for key, rid in RESOURCE_IDS.items():
        s = download_series(rid)
        if s is None:
            log(f"ABANDON : série requise « {key} » indisponible ou vide. Aucun fichier modifié.")
            return 1
        series[key] = s

    proc_publiees_series = find_proc_publiees_series()

    # mois communs aux 3 séries requises, derniers 24 mois conservés seulement
    # (compteur-roi.html ne lit que l'année en cours, mais garder une fenêtre glissante
    # de 24 mois plutôt que le seul "YYYY courant" évite un trou de données le temps que
    # janvier soit publié chaque début d'année — base_month reste toujours inclus).
    common_months_all = sorted(set(series["depo"]) & set(series["crees"]) & set(series["proc_creees"]))
    if not common_months_all:
        log("ABANDON : aucun mois commun aux 3 séries. Aucun fichier modifié.")
        return 1
    common_months = common_months_all[-24:]

    if not (set(series["depo"]) == set(series["crees"]) == set(series["proc_creees"])):
        log("Avertissement : les 3 séries n'ont pas exactement les mêmes mois ; "
            f"intersection retenue = {common_months[0]}..{common_months[-1]} ({len(common_months)} mois).")

    try:
        existing = json.load(open(PARAMS_FILE, encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as e:
        log(f"ABANDON : impossible de lire le fichier existant {PARAMS_FILE} ({e}).")
        return 1

    months_out = {}
    for m in common_months:
        months_out[m] = {
            "depo": series["depo"][m],
            "crees": series["crees"][m],
            "proc_creees": series["proc_creees"][m],
            "proc_publiees": (proc_publiees_series.get(m) if proc_publiees_series else None),
        }

    base_month = common_months[-1]  # dernier mois complet (le plus récent disponible dans les 3 séries)
    today = datetime.date.today().isoformat()

    new_params = {
        "_commentaire": existing.get("_commentaire", ""),
        "base_month": base_month,
        "data_updated": today,
        "ratio_pub": existing["ratio_pub"],
        "plateforme_annuel": existing["plateforme_annuel"],
        "months": months_out,
        "plateforme_annuel_libelle": existing["plateforme_annuel_libelle"],
    }

    for path in ((PARAMS_FILE,) if "--publier" in sys.argv else ()):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(new_params, f, ensure_ascii=False, indent=1)
            f.write("\n")
        log(f"Écrit : {path}")

    log(f"base_month={base_month} data_updated={today} mois_couverts={len(common_months)} "
        f"proc_publiees_source={'oui' if proc_publiees_series else 'non (estimation conservée)'}")

    log("--- Fin mise à jour mensuelle : succès ---")
    return 0


def verifier_fraicheur():
    """En retard si, après le 5 du mois, le dernier mois couvert n'est pas le mois précédent."""
    base = json.load(open(PARAMS_FILE, encoding="utf-8"))["base_month"]
    a, m = map(int, base.split("-"))
    auj = datetime.date.today()
    ecart = auj.year * 12 + auj.month - a * 12 - m
    if ecart > 2 or (ecart == 2 and auj.day > 5):
        print(f"RETARD : le compteur s'arrête à {base}, nous sommes le {auj.isoformat()}.")
        return 1
    print(f"À jour : données jusqu'à {base}.")
    return 0


if __name__ == "__main__":
    sys.exit(verifier_fraicheur() if "--verifier-fraicheur" in sys.argv else main())
