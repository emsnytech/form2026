#!/usr/bin/env python3
"""Étude, sans affichage : signaux de simplicité (FranceConnect, données récupérées) par démarche de l'index.

Écrit un rapport Markdown sur la sortie standard ; rien n'est écrit dans l'index.

Sources (données ouvertes, licence ouverte 2.0) :
  - « Habilitations DataPass validées » (DINUM) : https://www.data.gouv.fr/datasets/habilitations-datapass-validees ;
  - Observatoire de la qualité des démarches en ligne (DINUM), ODS d'une édition : colonnes « FranceConnect », « Score DLNUF » ;
  - index de la page (donnees/assistant/index.json) et slim du mois (SIRET de l'organisme de chaque démarche DN).

    python3 scripts/assistant/etude_simplicite.py --datapass <habilitations.csv> --observatoire <édition.ods> \\
        --slim ~/Documents/cartographie/assistant/slim_AAAAMMJJ.jsonl > rapport.md
"""
import argparse, collections, csv, json, random, re, sys, unicodedata
from pathlib import Path


D = Path(__file__).resolve().parents[2] / "donnees" / "assistant"
FAMILLES = {"FranceConnect": "FranceConnect", "APIEntreprise": "API Entreprise", "APIParticulier": "API Particulier",
            "APIParticulierDemarcheNumerique": "API Particulier", "FormulaireQF": "API Particulier"}
SIGNAUX = ["FranceConnect", "API Entreprise", "API Particulier", "ProConnect"]
# Champs DN qui vont chercher une donnée chez une autre administration ou dans un répertoire (libellés de « pre »)
PRE_RECUPERE = {"SIRET (API Entreprise)": "API Entreprise", "RNA (associations)": "API Entreprise (RNA)",
                "RNF (fondations)": "répertoire RNF", "Annuaire Éducation": "annuaire de l'Éducation nationale",
                "Quotient familial (CAF)": "API Particulier", "Statut boursier": "API Particulier",
                "Données préremplies": "lien prérempli par l'administration"}
DENOM = "Dénomination de l'unité légale du demandeur"
PRE_NON = {"IBAN": "format vérifié, rien n'est récupéré"}


def famille(api):
    if api in FAMILLES: return FAMILLES[api]
    if api.startswith("ProConnect"): return "ProConnect"
    if api.endswith("Sandbox"): return "bac à sable (essais)"
    if api.startswith("HubEE"): return "HubEE (échange de dossiers)"
    return "autres API"


def lire_toutes(chemin):
    import zipfile, xml.etree.ElementTree as ET
    T = "{urn:oasis:names:tc:opendocument:xmlns:table:1.0}"; P = "{urn:oasis:names:tc:opendocument:xmlns:text:1.0}p"
    tab = next(ET.fromstring(zipfile.ZipFile(chemin).read("content.xml")).iter(T + "table")); lignes = []
    for row in tab.iter(T + "table-row"):
        cells = []
        for c in row.iter(T + "table-cell"):
            cells += [" ".join("".join(x.itertext()) for x in c.iter(P))] * min(int(c.get(T + "number-columns-repeated", "1")), 30)
        lignes.append(cells)
    return [d for d in (dict(zip(lignes[0], l)) for l in lignes[1:]) if (d.get("Nom Démarche") or "").strip()]


def nn(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().upper()
    return " ".join(re.sub(r"[^A-Z0-9]+", " ", s).split())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--datapass", required=True); ap.add_argument("--observatoire", required=True); ap.add_argument("--slim", required=True)
    A = ap.parse_args()
    rnd = random.Random(20261124)
    p = print
    csv.field_size_limit(10 ** 9)
    with open(A.datapass, encoding="utf-8-sig", newline="") as f: dp = list(csv.DictReader(f))
    idx = json.loads((D / "index.json").read_text(encoding="utf-8"))
    dn = {r["id"]: r for r in idx if r["k"] == "dn"}
    with open(A.slim, encoding="utf-8") as f: siret = {"DN-%d" % a[0]: (a[4] or "") for a in map(json.loads, f)}

    p("## A1. DataPass\n")
    p(f"{len(dp)} habilitations validées, du {min(x['Date de validation'] for x in dp)} au {max(x['Date de validation'] for x in dp)}, "
      f"{len({x['SIRET du demandeur'] for x in dp})} SIRET demandeurs.\n")
    p("| Colonne | Renseignée | Exemple |\n|---|---|---|")
    for k in dp[0]:
        ex = next((x[k] for x in dp if x[k].strip()), "").replace("|", "/").replace("\n", " ")
        p(f"| {k} | {sum(1 for x in dp if x[k].strip())} | {ex[:90]} |")
    p("\nLe fichier ne donne ni adresse ni intitulé du service habilité : seulement l'organisme demandeur (SIRET, dénomination).\n")
    p("| Type d'habilitation | Habilitations | Organismes (SIRET) |\n|---|---|---|")
    fam = collections.defaultdict(list)
    for x in dp: fam[famille(x["API ou Service demandé"])].append(x)
    for k, v in sorted(fam.items(), key=lambda kv: -len(kv[1])):
        p(f"| {k} | {len(v)} | {len({x['SIRET du demandeur'] for x in v})} |")

    noms = {}
    for x in dp: noms.setdefault(x["SIRET du demandeur"].strip(), nn(x["Dénomination de l'unité légale du demandeur"]))
    partages = {s for s, n in noms.items() if "FACTURATION ELECTRONIQUE" in n}
    bys, byn = collections.defaultdict(dict), collections.defaultdict(dict)
    for x in dp:
        f = famille(x["API ou Service demandé"]); s = x["SIRET du demandeur"].strip(); n = nn(x["Dénomination de l'unité légale du demandeur"])
        if f not in SIGNAUX: continue
        if s: bys[s].setdefault(f, x)
        if n: byn[n].setdefault(f, x)
    p("\n### Rattachement aux démarches de l'index\n")
    p(f"- Par l'adresse du service : impossible, la colonne n'existe pas.\n- Par l'intitulé du service : impossible, la colonne n'existe pas.\n"
      f"- Les fiches service-public (SP-F, SP-R) n'ont pas d'organisme ni de SIRET dans l'index : aucune ne se rattache.\n"
      f"- Par le SIRET de l'organisme, pour les {len(dn)} démarches DN ({sum(1 for i in dn if siret.get(i))} avec un SIRET dans le slim). "
      f"Le SIRET {', '.join(sorted(partages))} (« Services de l'État pour la facturation électronique ») est partagé par de nombreux services de l'État : "
      f"les rattachements par ce SIRET sont comptés à part.\n- Par le nom de l'organisme, pour les démarches DN sans SIRET (nom normalisé identique).\n")
    p("| Signal | Par SIRET | dont SIRET partagé | Par nom | Organismes |\n|---|---|---|---|---|")
    exemples = {}
    for f in SIGNAUX:
        a, b, orgs = [], [], set()
        for i, r in sorted(dn.items()):
            s = siret.get(i, "")
            if s and f in bys.get(s, {}): a.append((i, r, bys[s][f])); orgs.add(s)
            elif not s and nn(r["o"]) and f in byn.get(nn(r["o"]), {}): b.append((i, r, byn[nn(r["o"])][f])); orgs.add(nn(r["o"]))
        exemples[f] = (a, b)
        p(f"| {f} | {len(a)} | {sum(1 for h in a if siret[h[0]] in partages)} | {len(b)} | {len(orgs)} |")
    for f in SIGNAUX:
        for meth, h in zip(("SIRET", "nom"), exemples[f]):
            if not h: continue
            p(f"\n**{f}, par {meth}** : 10 exemples au hasard (démarche de l'index ⟷ demandeur DataPass)\n")
            for i, r, x in rnd.sample(h, min(10, len(h))):
                p(f"- [{i}](https://demarche.numerique.gouv.fr/commencer/{r['u']}) « {r['t'][:80]} » ({r['o'][:50] or 'organisme vide'}) "
                  f"⟷ {x['API ou Service demandé']}, {x[DENOM][:60] or 'dénomination vide'}, validée le {x['Date de validation']}")

    p("\n## A2. Observatoire\n")
    # toutes les lignes nommées (selections.lire_observatoire ne garde que celles qui ont une volumétrie)
    obs = lire_toutes(A.observatoire)
    p(f"Colonne « FranceConnect » : oui, une valeur par démarche, {len(obs)} démarches dans l'édition.\n")
    p("| Valeur | Démarches | dont rattachées à l'index |\n|---|---|---|")
    rat = json.loads((D / "observatoire_rattachement.json").read_text(encoding="utf-8"))["rattachements"]
    ids = {str(t["observatoire"]): t["id"] for t in rat}
    c = collections.Counter((o.get("FranceConnect") or "").strip() or "(vide)" for o in obs)
    cr = collections.Counter((o.get("FranceConnect") or "").strip() or "(vide)" for o in obs if str(o["ID Démarche"]) in ids)
    for k, n in c.most_common(): p(f"| {k} | {n} | {cr.get(k, 0)} |")
    p(f"\nRattachements validés avec FranceConnect ou FranceConnect + : "
      + ", ".join(sorted(ids[str(o['ID Démarche'])] for o in obs if str(o["ID Démarche"]) in ids and (o.get("FranceConnect") or "").startswith("FranceConnect"))))
    d = collections.Counter((o.get("Score DLNUF") or "").strip() for o in obs)
    p(f"\nColonne « Score DLNUF » : {dict(d.most_common())}. D'après la méthode de l'Observatoire, ce score compte les informations demandées à l'usager "
      "qui pourraient être préremplies (0 ou 1 : « optimal »). Il ne dit pas que des données sont récupérées.\n")

    p("## A3. Démarche Numérique : champ « pre »\n")
    c = collections.Counter(x for r in dn.values() for x in r["pre"])
    p("| Valeur de « pre » | Démarches | Source |\n|---|---|---|")
    for k, n in c.most_common(): p(f"| {k} | {n} | {PRE_RECUPERE.get(k) or PRE_NON.get(k, '?')} |")
    for k in PRE_RECUPERE:
        if k not in c: p(f"| {k} | 0 | {PRE_RECUPERE[k]} |")
    rec = sum(1 for r in dn.values() if any(x in PRE_RECUPERE for x in r["pre"]))
    p(f"\nDémarches avec au moins une donnée récupérée (sans l'IBAN) : {rec} ; avec « pre » non vide : {sum(1 for r in dn.values() if r['pre'])}.")


if __name__ == "__main__":
    main()
