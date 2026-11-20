#!/usr/bin/env python3
"""Produit donnees/assistant/france_services.json à partir de la liste des structures labellisées France services (ANCT).

Source : jeu « Liste des structures labellisées France services » de l'Agence nationale de la cohésion des territoires,
data.gouv.fr, licence ouverte. Le script prend la ressource CSV la plus récente du jeu (« Liste des structures … »).

Le fichier garde les téléphones et adresses électroniques : ce sont les points de contact publics des structures, affichés
comme tels par trouver-sa-demarche.html. Il figure pour cette raison dans les exceptions de scripts/retirer_contacts.py.

    python3 scripts/assistant/france_services.py              # télécharge la dernière liste et écrit le fichier
    python3 scripts/assistant/france_services.py <liste.csv>  # part d'un CSV déjà téléchargé

Les adresses électroniques qui ressemblent à une adresse nominative (prénom.nom@…) sont signalées par l'identifiant et le
nom de la structure, jamais par l'adresse elle-même : à l'auteur de décider.
"""
import csv, io, json, re, sys, urllib.request
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
SORTIE = RACINE / "donnees" / "assistant" / "france_services.json"
JEU = "https://www.data.gouv.fr/api/1/datasets/liste-des-structures-labellisees-france-services/"
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
CHAMPS = ["id", "nom", "adresse", "complement", "code_postal", "commune", "insee", "lat", "lon", "horaires", "telephone", "courriel", "rdv", "type", "format"]
# Mots d'une adresse de structure : une partie locale qui en contient un n'est pas nominative.
GENERIQUES = re.compile(r"france|serv|fs|mfs|msap|mairie|ville|commune|accueil|contact|info|secr|agence|maison|pole|cc|com|cias|ccas|centre|espace|point|mds|social|public|bus|itiner|tiers|lieu|mediat|numer|antenne|admin|guichet|direction|cdc|agglo|metropole|territoire|sous|pref|poste|^fr|\d", re.I)
NOMINATIVE = re.compile(r"^[a-zà-ÿ]+(?:-[a-zà-ÿ]+)?[._][a-zà-ÿ]+(?:-[a-zà-ÿ]+)?$", re.I)


def telecharger():
    meta = json.load(urllib.request.urlopen(JEU, timeout=60))
    ress = sorted((r for r in meta["resources"] if r["title"].strip().lower().startswith("liste des structures") and r["format"] == "csv"),
                  key=lambda r: r["last_modified"], reverse=True)
    if not ress:
        sys.exit("aucune ressource CSV « Liste des structures » dans le jeu de l'ANCT")
    r = ress[0]
    return urllib.request.urlopen(r["url"], timeout=120).read(), r["url"], r["last_modified"][:10]


def main():
    if len(sys.argv) > 1:
        brut, url, date = Path(sys.argv[1]).read_bytes(), Path(sys.argv[1]).name, ""
    else:
        brut, url, date = telecharger()
    texte = brut.decode("utf-8-sig")
    lignes = list(csv.DictReader(io.StringIO(texte), delimiter=";" if texte[:2000].count(";") > texte[:2000].count(",") else ","))
    fs, sans_coord, nominatives = [], 0, []
    for l in lignes:
        try:
            lat, lon = round(float(l["latitude"]), 5), round(float(l["longitude"]), 5)
        except (TypeError, ValueError):
            sans_coord += 1
            continue
        courriel = (l.get("mail") or "").strip()
        locale = courriel.split("@")[0] if "@" in courriel else ""
        if locale and NOMINATIVE.match(locale) and not GENERIQUES.search(locale):
            nominatives.append(f"{l['id_fs']} {l['lib_fs']}")
        fs.append([l["id_fs"], l["lib_fs"].strip(), l["adresse"].strip(), (l.get("complement_adresse") or "").strip(), l["code_postal"].strip(),
                   l["lib_com"].strip(), l["insee_com"].strip(), lat, lon, [(l.get("h_" + j) or "").strip() for j in JOURS],
                   (l.get("telephone") or "").strip(), courriel, (l.get("prise_rdv") or "").strip(), (l.get("type_fs") or "").strip(),
                   (l.get("format_fs") or "").strip()])
    SORTIE.write_text(json.dumps({"source": "Liste des structures labellisées France services, ANCT, data.gouv.fr, licence ouverte",
                                  "ressource": url, "date": date, "champs": CHAMPS, "jours": JOURS, "structures": fs},
                                 ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"écrit : {SORTIE.relative_to(RACINE)} ({len(fs)} structures, {sans_coord} sans coordonnées écartées, {SORTIE.stat().st_size // 1024} Ko)")
    print(f"courriels d'allure nominative, à examiner : {len(nominatives)}")
    for n in nominatives:
        print("  " + n)


if __name__ == "__main__":
    main()
