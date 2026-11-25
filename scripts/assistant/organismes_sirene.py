#!/usr/bin/env python3
"""Nom de l'entité qui publie une démarche passée en nationale par portees_corrigees.json, lu dans la base Sirene :
donnees/assistant/organismes_sirene.json.

L'organisme déclaré sur Démarche Numérique (« Préfecture, sous-préfecture, DDETSPP, DRIEETS ») prête à confusion à côté de
« nationale ». Pour ces démarches seulement, la ligne sous le titre affiche le nom de l'unité légale qui publie la démarche,
lu à partir du SIRET de la démarche (slim du mois) dans l'API Recherche d'entreprises (DINUM, données Sirene de l'INSEE,
licence ouverte). Rien n'est écrit à la main ; l'organisme déclaré reste dans le détail du « ? ».
Une requête par SIREN, une à la fois. Si la réponse ne porte pas le SIREN demandé, le script s'arrête sans rien écrire.

    python3 scripts/assistant/organismes_sirene.py --slim ~/Documents/cartographie/assistant/slim_AAAAMMJJ.jsonl
    python3 scripts/assistant/organismes_sirene.py --slim … --verifier   # dit si le fichier est à jour
"""
import argparse, datetime, json, sys, time, urllib.parse, urllib.request
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "donnees" / "assistant"
API = "https://recherche-entreprises.api.gouv.fr/search?"


def nom_sirene(siren):
    req = urllib.request.Request(API + urllib.parse.urlencode({"q": siren, "per_page": 1}),
                                 headers={"User-Agent": "form2026-repertoire (nom d'organisme public)"})
    res = json.loads(urllib.request.urlopen(req, timeout=30).read().decode("utf-8")).get("results") or []
    if not res or res[0].get("siren") != siren or not (res[0].get("nom_complet") or "").strip():
        sys.exit(f"SIREN {siren} : pas de réponse qui porte ce SIREN ; rien n'est écrit")
    return " ".join(res[0]["nom_complet"].split())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--slim", required=True); ap.add_argument("--verifier", action="store_true")
    A = ap.parse_args()
    nat = {c["id"] for c in json.loads((D / "portees_corrigees.json").read_text(encoding="utf-8"))["corrections"] if c["portee"] == "nat"}
    siret = {}
    with open(A.slim, encoding="utf-8") as f:
        for a in map(json.loads, f):
            if "DN-%d" % a[0] in nat and a[4]: siret["DN-%d" % a[0]] = a[4]
    organismes = {}
    for s in sorted(set(siret.values())):
        organismes[s] = {"siren": s[:9], "nom": nom_sirene(s[:9]), "lu_le": datetime.date.today().isoformat()}
        time.sleep(0.5)
    out = {"objet": "Nom de l'unité légale (Sirene) des démarches passées en nationale par portees_corrigees.json, lu par "
                    "scripts/assistant/organismes_sirene.py dans l'API Recherche d'entreprises ; lu par build_index.py (clé « on »).",
           "source": "https://recherche-entreprises.api.gouv.fr (DINUM, données Sirene de l'INSEE)",
           "demarches": dict(sorted(siret.items())), "organismes": organismes}
    f = D / "organismes_sirene.json"
    if A.verifier:
        ancien = json.loads(f.read_text(encoding="utf-8"))
        sans_date = lambda d: (d["demarches"], {k: v["nom"] for k, v in d["organismes"].items()})
        if sans_date(ancien) != sans_date(out): sys.exit("organismes_sirene.json n'est plus à jour : relancer le script")
        print("organismes_sirene.json à jour"); return
    f.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for i, s in out["demarches"].items(): print(f"{i} : {s} → {organismes[s]['nom']}")


if __name__ == "__main__":
    main()
