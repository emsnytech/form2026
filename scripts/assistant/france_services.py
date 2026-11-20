#!/usr/bin/env python3
"""Produit donnees/assistant/france_services.json à partir de la liste des structures labellisées France services (ANCT).

Source : jeu « Liste des structures labellisées France services » de l'Agence nationale de la cohésion des territoires,
data.gouv.fr, licence ouverte. Le script prend la ressource CSV la plus récente du jeu (« Liste des structures … »).

Le fichier garde les téléphones et adresses électroniques : ce sont les points de contact publics des structures, affichés
comme tels par trouver-sa-demarche.html. Il figure pour cette raison dans les exceptions de scripts/retirer_contacts.py.

    python3 scripts/assistant/france_services.py              # télécharge la dernière liste et écrit le fichier
    python3 scripts/assistant/france_services.py <liste.csv>  # part d'un CSV déjà téléchargé

Fiche officielle : chaque structure est rapprochée de sa fiche dans l'Annuaire de l'administration (DILA), qui recense les
France services. D'abord par identifiant (le champ partenaire_identifiant de l'Annuaire porte l'identifiant ANCT), sinon
par commune, nom normalisé et distance inférieure à 200 m. Sans rapprochement, pas de lien : aucun n'est deviné.

Le script compte les adresses électroniques d'allure nominative (prénom.nom@…, repérage approximatif) sans les lister :
elles sont publiées par l'ANCT comme contact de la structure et affichées comme les autres.
"""
import csv, io, json, math, re, sys, unicodedata, urllib.parse, urllib.request
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
SORTIE = RACINE / "donnees" / "assistant" / "france_services.json"
JEU = "https://www.data.gouv.fr/api/1/datasets/liste-des-structures-labellisees-france-services/"
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
CHAMPS = ["id", "nom", "adresse", "complement", "code_postal", "commune", "insee", "lat", "lon", "horaires", "telephone", "courriel", "rdv", "type", "format", "fiche"]
ANNUAIRE = ("https://api-lannuaire.service-public.gouv.fr/api/explore/v2.1/catalog/datasets/api-lannuaire-administration/exports/json?"
            + urllib.parse.urlencode({"where": 'search(pivot,"france_services")', "select": "id,nom,partenaire_identifiant,code_insee_commune,adresse,url_service_public"}))
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


def nom_normalise(s):
    s = unicodedata.normalize("NFD", s or "").encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\bfrance services?\b|\(.*?\)|\b(de|du|des|la|le|les|d|l)\b", " ", s)
    return " ".join(re.findall(r"[a-z0-9]+", s))


def km(a, b, c, d):
    r = math.pi / 180
    x = math.sin((c - a) * r / 2) ** 2 + math.cos(a * r) * math.cos(c * r) * math.sin((d - b) * r / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(x))


def fiches_annuaire():
    """Fiches France services de l'Annuaire : par identifiant ANCT, et la liste complète pour le second rapprochement."""
    l = json.load(urllib.request.urlopen(ANNUAIRE, timeout=120))
    for a in l:
        ad = json.loads(a["adresse"]) if isinstance(a.get("adresse"), str) else (a.get("adresse") or [])
        ad = ad[0] if ad else {}
        try:
            a["_lat"], a["_lon"] = float(ad.get("latitude")), float(ad.get("longitude"))
        except (TypeError, ValueError):
            a["_lat"] = a["_lon"] = None
    return {str(a["partenaire_identifiant"]): a for a in l if a.get("partenaire_identifiant")}, l


def rapprocher(fs, par_id, toutes):
    """Ajoute l'adresse de la fiche officielle à chaque structure ; renvoie les comptes par méthode."""
    C = {k: i for i, k in enumerate(CHAMPS)}
    prises, n_id, n_geo = set(), 0, 0
    for f in fs:
        a = par_id.get(str(f[C["id"]]))
        if a and a.get("url_service_public"):
            f[C["fiche"]] = a["url_service_public"]; prises.add(a["id"]); n_id += 1
    for f in fs:
        if f[C["fiche"]]:
            continue
        cands = [a for a in toutes if a["id"] not in prises and a.get("code_insee_commune") == f[C["insee"]] and a["_lat"] is not None
                 and nom_normalise(a["nom"]) == nom_normalise(f[C["nom"]]) and km(a["_lat"], a["_lon"], f[C["lat"]], f[C["lon"]]) < 0.2]
        if len(cands) == 1 and cands[0].get("url_service_public"):
            f[C["fiche"]] = cands[0]["url_service_public"]; prises.add(cands[0]["id"]); n_geo += 1
    return n_id, n_geo


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
                   (l.get("format_fs") or "").strip(), ""])
    try:
        par_id, toutes = fiches_annuaire()
        n_id, n_geo = rapprocher(fs, par_id, toutes)
        rappro = f"fiches officielles (Annuaire) : {n_id} par identifiant, {n_geo} par commune, nom et distance, {len(fs) - n_id - n_geo} sans fiche, sur {len(fs)}"
    except Exception as e:
        rappro = f"fiches officielles : Annuaire injoignable ({e}), aucun lien ajouté"
    SORTIE.write_text(json.dumps({"source": "Liste des structures labellisées France services, ANCT, data.gouv.fr, licence ouverte",
                                  "ressource": url, "date": date, "champs": CHAMPS, "jours": JOURS, "structures": fs},
                                 ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"écrit : {SORTIE.relative_to(RACINE)} ({len(fs)} structures, {sans_coord} sans coordonnées écartées, {SORTIE.stat().st_size // 1024} Ko)")
    print(rappro)
    print(f"courriels d'allure nominative (prénom.nom@…, repérage approximatif), affichés comme les autres : {len(nominatives)}")


if __name__ == "__main__":
    main()
