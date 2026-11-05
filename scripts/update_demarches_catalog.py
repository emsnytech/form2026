#!/usr/bin/env python3
"""Mise à jour mensuelle légère du catalogue des démarches (FORM 2026).

Ne touche QUE les champs bruts des démarches déjà connues (état, nb_dossiers,
date_publication) et ajoute les démarches nouvellement publiées avec leurs seuls
champs bruts (classification, niveau de complexité et gains laissés à vide,
marqués `enrichissement_en_attente`, à traiter séparément et seulement pour elles).

Recalcule ensuite mix_dossiers et mix_demarches, codés en dur dans
compteur-roi.html, à partir du sous-ensemble des démarches déjà enrichies
(gain_admin_central_v7 non nul) : mix_dossiers = part des dossiers par
niveau_brut_v7 ; mix_demarches = nombre de démarches par niveau_brut_v7.

PLAT n'est PLUS recalculé ici depuis l'alignement sur la référence 2025 (commit
b650180, 2026-10-08) : c'est désormais une constante externe fixe (1 600 000 /
4 300 000 €, bilan 2025 de la plateforme), indépendante du corpus FORM et de son
nombre de dossiers. Elle ne doit être changée qu'à la main, le jour où
Démarche Numérique publie un nouveau bilan annuel — jamais par ce script.

N'écrit rien si le téléchargement échoue. Ne recalcule JAMAIS la classification,
le niveau de complexité ou les gains des démarches déjà enrichies.
"""
import os
from pathlib import Path
import json, re, csv, io, gzip, subprocess, sys, base64, datetime, urllib.request, argparse
from collections import Counter
sys.path.insert(0, str(Path(__file__).resolve().parent))
from retirer_adresses import masquer_donnees

CARTO = os.environ.get("FORM2026_CARTOGRAPHIE", str(Path.home() / "Documents/cartographie"))
SITE = str(Path(__file__).resolve().parents[1])
APP_FILE = f"{CARTO}/app/app_demarches.json"
LOG_FILE = f"{CARTO}/update_demarches_catalog.log"
RESOURCE_ID = "666211e9-6226-4fad-8d2f-5a4135f40e47"  # descriptif-des-demarches-publiees-sur-demarche-numerique-gouv-fr

DRY_RUN = False

NEW_FIELDS_NULL = [
    "categorie", "nb_champs", "nb_pj", "nb_infos_api_isable", "nb_pj_api_isable",
    "fiches_dila", "cerfa_numeros", "loc_siege_redondante", "cerfa_lien", "cerfa_notice",
    "dila_descriptions", "essentielle", "categories_detail", "niveau_brut", "niveau_net",
    "typologie", "gain_admin_bas", "gain_admin_central", "gain_admin_haut",
    "gain_usagers_bas", "gain_usagers_central", "gain_usagers_haut",
    "nb_champs_opportunite", "nb_pj_opportunite", "niveau_brut_v7",
    "duree_estimee_totale_s", "duree_realise_s_30", "duree_realise_s_60",
    "ratio_realise_30", "ratio_realise_60", "gain_admin_bas_v7", "gain_admin_central_v7",
    "gain_admin_haut_v7", "gain_usagers_realise_30", "gain_usagers_realise_60",
    "gain_usagers_potentiel_v7", "gain_usagers_demat_bas_v7", "gain_usagers_demat_haut_v7",
]


def log(msg):
    prefix = "[DRY-RUN] " if DRY_RUN else ""
    line = f"{datetime.datetime.now().isoformat(timespec='seconds')} {prefix}{msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def decode_id(gid):
    try:
        return int(base64.b64decode(gid).decode("utf-8").split("-")[-1])
    except Exception:
        return None


EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(?<!\d)(?:\+33|0033|0)[1-9](?:[\s.\-]?\d{2}){4}(?!\d)")
# motifs « entourés » : les mêmes adresses/numéros, mais avec leurs délimiteurs
# d'origine ([...] ou (...)) absorbés dans le remplacement, pour éviter un
# doublement des crochets (ex. titres 59783/75199/97215, corrigé 2026-10-11).
EMAIL_DELIM_RE = re.compile(r"[\[(]\s*" + EMAIL_RE.pattern + r"\s*[\])]")
PHONE_DELIM_RE = re.compile(r"[\[(]\s*" + PHONE_RE.pattern + r"\s*[\])]")


def nettoyer_titre(t):
    """Retire toute adresse électronique ou numéro de téléphone français d'un titre
    de démarche, avant publication (règle de confidentialité du projet, voir
    LISEZMOI_gains.md). Absorbe les crochets ou parenthèses qui entourent l'adresse
    ou le numéro d'origine, pour éviter les doubles crochets."""
    if not t:
        return t
    t2 = EMAIL_DELIM_RE.sub("[adresse électronique retirée]", t)
    t2 = PHONE_DELIM_RE.sub("[numéro de téléphone retiré]", t2)
    t2 = EMAIL_RE.sub("[adresse électronique retirée]", t2)
    t2 = PHONE_RE.sub("[numéro de téléphone retiré]", t2)
    return t2


def _selftest():
    cas = [
        ("Fiche X [contact@exemple.invalid]", "Fiche X [adresse électronique retirée]"),
        ("Contact contact@exemple.invalid", "Contact [adresse électronique retirée]"),
        ("Tél (01 23 45 67 89)", "Tél [numéro de téléphone retiré]"),
        ("Tél 01 23 45 67 89", "Tél [numéro de téléphone retiré]"),
        ("Demande d'autorisation de voirie", "Demande d'autorisation de voirie"),
    ]
    for entree, attendu in cas:
        obtenu = nettoyer_titre(entree)
        assert obtenu == attendu, f"ECHEC : {entree!r} -> {obtenu!r} (attendu {attendu!r})"
        print(f"OK : {entree!r} -> {obtenu!r}")
    print("--selftest : 5/5 cas OK")


def fetch_fresh_export(tmp_path):
    url = f"https://www.data.gouv.fr/api/1/datasets/r/{RESOURCE_ID}"
    req = urllib.request.Request(url, headers={"User-Agent": "FORM2026-catalog-update/1"})
    with urllib.request.urlopen(req, timeout=120) as r, open(tmp_path, "wb") as out:
        out.write(r.read())


def main():
    global DRY_RUN
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                         help="Télécharge et calcule tout, journalise, n'écrit aucun fichier, "
                              "ne patche aucune page, ne commit rien.")
    args = parser.parse_args()
    DRY_RUN = args.dry_run

    log("--- Démarrage mise à jour mensuelle du catalogue des démarches ---")

    gz_path = "/tmp/_demarches_fresh.json.gz"
    try:
        fetch_fresh_export(gz_path)
    except Exception as e:
        log(f"ABANDON : téléchargement échoué ({e}). Aucun fichier modifié.")
        return 1

    try:
        with gzip.open(gz_path, "rb") as f:
            raw_bytes = f.read()
    except Exception as e:
        log(f"ABANDON : décompression échouée ({e}). Aucun fichier modifié.")
        return 1

    json_path = "/tmp/_demarches_fresh.json"
    with open(json_path, "wb") as f:
        f.write(raw_bytes)

    try:
        out = subprocess.run(
            ["jq", "-c", ".[] | {id, state, dossiersCount, datePublication, title, demarcheURL, service}", json_path],
            capture_output=True, text=True, check=True,
        )
    except subprocess.CalledProcessError as e:
        log(f"ABANDON : extraction jq échouée ({e.stderr[:500]}). Aucun fichier modifié.")
        return 1

    fresh = {}
    for line in out.stdout.splitlines():
        d = json.loads(line)
        did = decode_id(d["id"])
        if did is None:
            continue
        fresh[did] = d

    if not fresh:
        log("ABANDON : export frais vide ou illisible. Aucun fichier modifié.")
        return 1
    log(f"Export frais chargé : {len(fresh)} démarches.")

    catalog = json.load(open(APP_FILE, encoding="utf-8"))
    by_id = {x["demarche"]: x for x in catalog}
    log(f"Catalogue actuel : {len(catalog)} démarches.")
    known_type_organisme = {x.get("type_organisme") for x in catalog}

    n_updated = n_removed = n_added = n_titres_nettoyes = 0
    kept = []
    for x in catalog:
        f = fresh.get(x["demarche"])
        if f is None or f["state"] not in ("publiee", "close"):
            n_removed += 1
            continue
        x["etat"] = f["state"]
        x["nb_dossiers"] = f["dossiersCount"]
        x["date_publication"] = (f["datePublication"] or "")[:19].replace("T", " ")
        n_updated += 1
        kept.append(x)

    existing_ids = set(by_id.keys())
    new_type_organisme = Counter()
    for did, f in fresh.items():
        if did in existing_ids or f["state"] not in ("publiee", "close"):
            continue
        # même règle d'inclusion que le corpus d'origine : exclut les démarches
        # publiées avant 2026 avec moins de 10 dossiers (laisse passer tout 2026
        # quel que soit le volume) — cf. note Méthodologie du projet.
        pub_date = (f.get("datePublication") or "")[:10]
        dossiers = f.get("dossiersCount") or 0
        if pub_date and pub_date < "2026-01-01" and dossiers < 10:
            continue
        m = re.search(r"/commencer/([^/?#]+)", f.get("demarcheURL") or "")
        svc = f.get("service") or {}
        titre_brut = f.get("title")
        titre = nettoyer_titre(titre_brut)
        if titre != titre_brut:
            n_titres_nettoyes += 1
        rec = {
            "demarche": did,
            "titre": titre,
            "organisme": svc.get("organisme"),
            "type_organisme": svc.get("typeOrganisme"),
            "etat": f["state"],
            "a_siret": 1 if svc.get("siret") else 0,
            "a_rna": 0,
            "nb_dossiers": f["dossiersCount"],
            "date_publication": (f.get("datePublication") or "")[:19].replace("T", " "),
            "departement": svc.get("departement"),
            "region": None,
            "ministere": None,
            "url": m.group(1) if m else None,
            "enrichissement_en_attente": True,
        }
        for k in NEW_FIELDS_NULL:
            rec[k] = None
        kept.append(rec)
        n_added += 1
        new_type_organisme[rec["type_organisme"]] += 1

    log(f"Mises à jour (état/dossiers/date) : {n_updated}")
    log(f"Retirées (dépubliées ou disparues) : {n_removed}")
    log(f"Nouvelles démarches ajoutées (enrichissement en attente) : {n_added}")
    log(f"Répartition type_organisme des nouvelles démarches : {dict(new_type_organisme)}")
    log(f"Titres nettoyés (e-mail ou téléphone retiré) : {n_titres_nettoyes}")

    # contrôle de plausibilité : une valeur de type_organisme inconnue du corpus
    # existant mérite un avertissement (code non documenté, ou anomalie côté source)
    inconnues = set(new_type_organisme) - known_type_organisme
    if inconnues:
        log(f"AVERTISSEMENT : type_organisme inconnu(s) du corpus existant parmi les "
            f"nouvelles démarches : {sorted(str(v) for v in inconnues)}")

    if DRY_RUN:
        log(f"Aucune écriture (dry-run) : {len(kept)} démarches auraient été écrites dans "
            f"{APP_FILE} et redécoupées en 4 parts vers {SITE}.")
    else:
        # Aucune adresse électronique ne doit atteindre les données publiées, quel que soit le champ.
        kept = masquer_donnees(kept)
        json.dump(kept, open(APP_FILE, "w", encoding="utf-8"), ensure_ascii=False)
        log(f"Écrit : {APP_FILE} ({len(kept)} démarches)")

        # re-split en 4 parts (même découpage que l'existant : tranches contiguës égales)
        n = len(kept)
        n_parts = 4
        size = -(-n // n_parts)  # ceil
        for i in range(n_parts):
            part = kept[i * size:(i + 1) * size]
            path = f"{SITE}/app_demarches_{i}.json"
            json.dump(part, open(path, "w", encoding="utf-8"), ensure_ascii=False)
            log(f"Écrit : {path} ({len(part)} démarches)")

    # ---- recalcul des totaux codés en dur dans les 3 pages outils ----
    enrichis = [x for x in kept if x.get("gain_admin_central_v7") is not None]
    tot_dossiers_enrichis = sum(x["nb_dossiers"] for x in enrichis)
    n_enrichis = len(enrichis)
    by_niveau_n = {"simple": 0, "modere": 0, "complexe": 0}
    by_niveau_dos = {"simple": 0, "modere": 0, "complexe": 0}
    for x in enrichis:
        niv = x.get("niveau_brut_v7")
        if niv in by_niveau_n:
            by_niveau_n[niv] += 1
            by_niveau_dos[niv] += x["nb_dossiers"]

    log(f"Sous-ensemble enrichi (gain_admin_central_v7 connu) : {n_enrichis} démarches, "
        f"{tot_dossiers_enrichis} dossiers.")
    log(f"Répartition démarches : {by_niveau_n} | dossiers : {by_niveau_dos}")

    mix_dossiers = {k: round(v / tot_dossiers_enrichis, 4) for k, v in by_niveau_dos.items()}

    # --- patch de compteur-roi.html (source cartographie + copie déployée form2026-site) ---
    # PLAT n'est plus patché ici : c'est une constante externe fixe depuis l'alignement 2025
    # (voir le docstring en tête de fichier). Ne pas réintroduire un patch_plat() sans relire
    # la note .claude/skills/maj-demarches-form2026/SKILL.md dans cartographie.
    log(f"mix_dossiers calculé : {mix_dossiers}")
    log(f"mix_demarches calculé : simple={by_niveau_n['simple']}/{n_enrichis}, "
        f"modere={by_niveau_n['modere']}/{n_enrichis}, complexe={by_niveau_n['complexe']}/{n_enrichis}")

    def patch_mix(path):
        s = open(path, encoding="utf-8").read()
        new_mix_dossiers = (
            "mix_dossiers:{simple:%s,modere:%s,complexe:%s}"
            % (mix_dossiers["simple"], mix_dossiers["modere"], mix_dossiers["complexe"])
        )
        new_mix_demarches = (
            "mix_demarches:{simple:%d/%d,modere:%d/%d,complexe:%d/%d}"
            % (by_niveau_n["simple"], n_enrichis, by_niveau_n["modere"], n_enrichis,
               by_niveau_n["complexe"], n_enrichis)
        )
        s2 = re.sub(r"mix_dossiers:\{[^}]*\}", new_mix_dossiers, s)
        s3 = re.sub(r"mix_demarches:\{[^}]*\}", new_mix_demarches, s2)
        if s3 != s:
            if DRY_RUN:
                log(f"mix_dossiers/mix_demarches auraient été mis à jour (dry-run) dans {path}")
            else:
                open(path, "w", encoding="utf-8").write(s3)
                log(f"mix_dossiers/mix_demarches mis à jour dans {path}")
        else:
            log(f"Avertissement : motifs mix_* non trouvés dans {path}")

    if DRY_RUN:
        for base in (CARTO, SITE):
            patch_mix(f"{base}/compteur-roi.html")
        log("Aucun commit (dry-run) : simulation terminée, aucun fichier modifié.")
    else:
        for base in (CARTO, SITE):
            patch_mix(f"{base}/compteur-roi.html")

        log("Fichiers écrits, aucun commit : à relire et à proposer par une PR depuis une branche.")

    log("--- Fin mise à jour mensuelle du catalogue : succès ---")
    return 0


if __name__ == "__main__" and "--selftest" in sys.argv:
    _selftest()
    sys.exit(0)

if __name__ == "__main__":
    sys.exit(main())
