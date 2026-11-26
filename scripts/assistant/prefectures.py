#!/usr/bin/env python3
"""Produit donnees/assistant/prefectures.json : la préfecture de chaque département, extraite de l'Annuaire de l'administration
(DILA, api-lannuaire.service-public.gouv.fr, licence ouverte).

Pour chaque préfecture : code du département, nom, site (le premier site internet donné par l'Annuaire, sinon sa fiche),
adresse postale du lieu d'accueil, fiche de l'Annuaire. Ni téléphone ni adresse électronique : « Contacts utiles » de la page
affiche une ligne par service (nom, site, adresse). La date d'extraction est écrite dans le fichier.

Le fichier sert à la version avec assistant, publiée sur claude.ai, qui ne peut appeler aucune API extérieure : « Contacts
utiles » y lit la préfecture ici. Le site, lui, interroge l'Annuaire à chaque réponse.

    python3 scripts/assistant/prefectures.py               # interroge l'Annuaire et écrit le fichier
    python3 scripts/assistant/prefectures.py --verifier    # interroge l'Annuaire et dit si le fichier est à jour
"""
import argparse, datetime, json, sys, urllib.parse, urllib.request
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
SORTIE = RACINE / "donnees" / "assistant" / "prefectures.json"
EXPORT = ("https://api-lannuaire.service-public.gouv.fr/api/explore/v2.1/catalog/datasets/api-lannuaire-administration/exports/json?"
          + urllib.parse.urlencode({"where": 'search(pivot,"prefecture") or search(pivot,"paris_ppp")',
                                    "select": "id,nom,pivot,code_insee_commune,adresse,site_internet,url_service_public"}))


def lit(v):
    if isinstance(v, str):
        try: return json.loads(v)
        except ValueError: return v
    return v or []


# Les 101 départements (métropole, Corse, départements d'outre-mer) ; les collectivités d'outre-mer sont écartées.
DEPARTEMENTS = {f"{i:02d}" for i in range(1, 96) if i != 20} | {"2A", "2B", "971", "972", "973", "974", "976"}


def departement(insee):
    insee = (insee or "").upper()
    if insee.startswith("97"): return insee[:3]
    return insee[:2]


def prefecture(x):
    """Une ligne du fichier, ou None si l'enregistrement n'est pas une préfecture de département."""
    types = [p.get("type_service_local") for p in lit(x.get("pivot")) if isinstance(p, dict)]
    # Paris : la Préfecture de police (type « paris_ppp »), rangée avec les préfectures dans types_guichets.json.
    if "prefecture" not in types and "paris_ppp" not in types: return None
    a = next((a for a in lit(x.get("adresse")) if isinstance(a, dict) and a.get("type_adresse") == "Adresse"), None) \
        or next((a for a in lit(x.get("adresse")) if isinstance(a, dict)), {})
    adresse = ", ".join(v for v in [a.get("numero_voie"), " ".join(v for v in [a.get("code_postal"), a.get("nom_commune")] if v)] if v)
    site = next((s.get("valeur") for s in lit(x.get("site_internet")) if isinstance(s, dict) and str(s.get("valeur", "")).startswith("http")), "")
    return {"dep": departement(x.get("code_insee_commune")), "nom": x.get("nom", "").strip(), "site": site or x.get("url_service_public", ""),
            "adresse": adresse, "fiche": x.get("url_service_public", ""), "id": x.get("id", "")}


def extraire():
    req = urllib.request.Request(EXPORT, headers={"User-Agent": "form2026-repertoire"})
    data = json.load(urllib.request.urlopen(req, timeout=120))
    l = [p for p in map(prefecture, data) if p and p["dep"] in DEPARTEMENTS]
    # une préfecture par département : d'abord celle dont le nom commence par « Préfecture » ; un doublon est signalé
    par_dep = {}
    for p in sorted(l, key=lambda p: (p["dep"], not p["nom"].startswith("Préfecture"), p["nom"])):
        if p["dep"] in par_dep: print(f"doublon pour le {p['dep']} : {p['nom']} (gardée : {par_dep[p['dep']]['nom']})", file=sys.stderr); continue
        par_dep[p["dep"]] = p
    return [par_dep[d] for d in sorted(par_dep)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--verifier", action="store_true")
    A = ap.parse_args()
    l = extraire()
    if len(l) != len(DEPARTEMENTS):
        sys.exit(f"{len(l)} préfectures pour {len(DEPARTEMENTS)} départements (manque : {sorted(DEPARTEMENTS - {p['dep'] for p in l})}) ; rien n'est écrit")
    if A.verifier:
        ancien = json.loads(SORTIE.read_text(encoding="utf-8"))["prefectures"]
        sys.exit("prefectures.json n'est plus à jour : relancer le script") if ancien != l else print("prefectures.json à jour")
        return
    out = {"objet": "Préfecture de chaque département (nom, site, adresse, fiche), extraite de l'Annuaire de l'administration par "
                    "scripts/assistant/prefectures.py ; lue par la version avec assistant (« Contacts utiles »), qui ne peut appeler aucune API.",
           "source": "Annuaire de l'administration (DILA), api-lannuaire.service-public.gouv.fr, licence ouverte",
           "date_extraction": datetime.date.today().isoformat(), "prefectures": l}
    SORTIE.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(l)} préfectures écrites dans {SORTIE.relative_to(RACINE)}")


if __name__ == "__main__":
    main()
