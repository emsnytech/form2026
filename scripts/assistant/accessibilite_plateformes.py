#!/usr/bin/env python3
"""Accessibilité des plateformes, lue sur leur déclaration d'accessibilité publiée : donnees/assistant/accessibilite_plateformes.json.

Pour Démarche Numérique, la déclaration porte sur la plateforme (une démarche type), pas sur le formulaire de chaque démarche.
Le statut, le taux, le mois de l'audit et la date de mise à jour sont relus sur la page : rien n'est écrit à la main. Si la page
change de forme et qu'un élément n'est plus trouvé, le script s'arrête sans rien écrire.

    python3 scripts/assistant/accessibilite_plateformes.py            # relit la page et écrit le fichier
    python3 scripts/assistant/accessibilite_plateformes.py --verifier # relit la page et dit si le fichier est à jour
"""
import argparse, datetime, html, json, re, sys, urllib.request
from pathlib import Path

D = Path(__file__).resolve().parents[2] / "donnees" / "assistant"
PLATEFORMES = {"dn": {"nom": "Démarche Numérique", "url": "https://demarche.numerique.gouv.fr/declaration-accessibilite"}}
STATUTS = {"totalement conforme": "tc", "partiellement conforme": "pc", "non conforme": "nc"}
MOIS = "janvier février mars avril mai juin juillet août septembre octobre novembre décembre".split()


def texte(url):
    req = urllib.request.Request(url, headers={"User-Agent": "form2026-repertoire (verification de declaration d'accessibilite)"})
    h = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
    h = re.sub(r"<script.*?</script>|<style.*?</style>", " ", h, flags=re.S)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", h)).split())


def lire(cle, p):
    t = texte(p["url"])
    statut = re.search(r"est (totalement conforme|partiellement conforme|non conforme) au Référentiel Général d’Amélioration de l’Accessibilité", t)
    taux = re.search(r"(L’audit réalisé[^.]*? en (\w+) (\d{4})[^.]*?taux de conformité global est de ([\d,]+) ?%[^.]*\.)", t)
    maj = re.search(r"mise à jour le (\d{1,2}) (\w+) (\d{4})", t)
    # Non-conformité qui touche le « formulaire à vide (PDF) » vers lequel renvoie la page : relue, jamais supposée.
    pdf = re.search(r"le document PDF de dématérialisation de la démarche n’est pas accessible", t)
    if not (statut and taux and maj) or taux[2] not in MOIS or maj[2] not in MOIS:
        sys.exit(f"{p['url']} : statut, taux ou date introuvable, la page a changé de forme ; rien n'est écrit")
    return {"nom": p["nom"], "url": p["url"], "statut": statut[1], "niveau": STATUTS[statut[1]],
            "taux": taux[4].rstrip("0").rstrip(",") + " %", "audit": f"{taux[2]} {taux[3]}",
            "mise_a_jour": datetime.date(int(maj[3]), MOIS.index(maj[2]) + 1, int(maj[1])).isoformat(),
            "pdf_non_accessible": bool(pdf), "extrait_pdf": pdf[0] if pdf else "",
            "extrait": taux[1], "lu_le": datetime.date.today().isoformat()}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--verifier", action="store_true")
    A = ap.parse_args()
    out = {"objet": "Accessibilité déclarée des plateformes (pour une démarche type), relue sur la déclaration publiée par "
                    "scripts/assistant/accessibilite_plateformes.py ; lue par build_index.py (index_meta.json, clé acc_plateformes).",
           "plateformes": {c: lire(c, p) for c, p in PLATEFORMES.items()}}
    f = D / "accessibilite_plateformes.json"
    if A.verifier:
        ancien = json.loads(f.read_text(encoding="utf-8"))["plateformes"]
        sans_date = lambda d: {c: {k: v for k, v in x.items() if k != "lu_le"} for c, x in d.items()}
        if sans_date(ancien) != sans_date(out["plateformes"]): sys.exit("accessibilite_plateformes.json n'est plus à jour : relancer le script")
        print("accessibilite_plateformes.json à jour"); return
    f.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for c, x in out["plateformes"].items(): print(f"{x['nom']} : {x['statut']}, {x['taux']}, audit {x['audit']}, mise à jour {x['mise_a_jour']}")


if __name__ == "__main__":
    main()
