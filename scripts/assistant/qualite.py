#!/usr/bin/env python3
"""Accessibilité et points de vigilance : agrégats lus par build_index.py, écrits dans donnees/assistant/qualite.json.

Sources (données ouvertes, licence ouverte 2.0) :
  - Observatoire de la qualité des démarches en ligne (DINUM), fichier ODS d'une édition : accessibilité (« Prise en compte
    Handicap », « Taux audit RGAA »), FranceConnect, « Dites-le-nous une fois », adresse de la démarche ;
  - Services Publics + (DITP), « Liste des expériences partagées par les usagers » (export-experiences.csv) : seulement des
    comptes, par démarche nommée (« Démarches modérées », nomenclature de l'Observatoire) et par structure (« Intitulé
    structure 1 à 3 »), sur les deux années avant la date du fichier. Aucun texte, aucun pseudonyme n'est lu ni écrit ;

Motifs de vigilance : les critères structurés que l'usager coche lui-même dans Services Publics +, comptés parmi les retours
négatifs. Trois critères ont un symbole : Réactivité (délais), Relation (joignabilité), Information/Explication (explications).
Aucun motif n'est tiré du texte des retours.

    python3 scripts/assistant/qualite.py --observatoire <édition.ods> --edition "édition 15 (octobre 2026)" \\
        --spp <export-experiences.csv> --date-spp 2026-11-23
"""
import argparse, collections, csv, datetime, json, re, sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parent))
from selections import lire_observatoire  # noqa: E402

D = Path(__file__).resolve().parents[2] / "donnees"
SEUIL_RETOURS = 20      # retours rattachés, tous ressentis, sur la période, pour afficher une vigilance
SEUIL_MOTIF = 5         # retours négatifs qui cochent le critère, pour que le motif soit affiché
MAX_MOTIFS = 2
ANNEES = 2
CRITERES = {"Réactivité": "delai", "Relation": "joignable", "Information/Explication": "explication"}
STATUTS = {"Totale": "TC", "Partielle": "PC", "Non conforme": "NC"}


def cle(s):
    return " ".join((s or "").replace("’", "'").split()).casefold()


def lire_spp(chemin, date_fichier):
    debut = (date_fichier - datetime.timedelta(days=365 * ANNEES)).isoformat()
    csv.field_size_limit(10 ** 9)
    par = {"demarche": collections.defaultdict(collections.Counter), "structure": collections.defaultdict(collections.Counter)}
    noms = {"demarche": {}, "structure": {}}
    with open(chemin, encoding="utf-8-sig", newline="") as f:
        r = csv.reader(f, delimiter=";")
        h = [x.strip() for x in next(r)]
        col = {k: i for i, k in enumerate(h)}
        i_struct = [i for i, k in enumerate(h) if k.startswith("Intitulé structure")]
        for row in r:
            if len(row) < len(h) or row[col["Date de publication"]][:10] < debut: continue
            neg = row[col["Ressenti usager"]] == "Négatif"
            crit = [CRITERES[c] for c in CRITERES if row[col[c]] == "Négatif"] if neg else []
            cibles = [("demarche", row[col["Démarches modérées"]])] + [("structure", row[i]) for i in i_struct]
            for niveau, nom in dict.fromkeys((n, x.strip()) for n, x in cibles if x.strip() and x.strip() != "Hors-structures"):
                c = par[niveau][cle(nom)]; noms[niveau].setdefault(cle(nom), nom)
                c["n"] += 1; c["neg"] += neg
                for m in crit: c[m] += 1
    out = {}
    for niveau, d in par.items():
        out[niveau] = {}
        for k, c in sorted(d.items()):
            if c["n"] < SEUIL_RETOURS: continue
            motifs = sorted(((m, c[m]) for m in CRITERES.values() if c[m] >= SEUIL_MOTIF), key=lambda x: -x[1])[:MAX_MOTIFS]
            out[niveau][k] = {"nom": noms[niveau][k], "n": c["n"], "neg": c["neg"], "motifs": [list(m) for m in motifs]}
    return out, debut


def proposer(obs):
    """Rattachements univoques par l'adresse de la démarche (une ligne de l'Observatoire, une démarche de l'index), à relire."""
    norm = lambda u: re.sub(r"^https?://(www\.)?", "", (u or "").strip().split("#")[0].rstrip("/").lower())
    recs = json.loads((D / "assistant" / "index.json").read_text(encoding="utf-8"))
    table = json.loads((D / "assistant" / "observatoire_rattachement.json").read_text(encoding="utf-8"))["rattachements"]
    deja = {str(t["observatoire"]) for t in table}
    par_url, lignes = collections.defaultdict(list), collections.defaultdict(list)
    for r in recs:
        if r["k"] == "sp" and r.get("l"): par_url[norm(r["l"])].append(r)
        if r["k"] == "dn" and r.get("u"): par_url[norm("demarche.numerique.gouv.fr/commencer/" + r["u"])].append(r)
    for o in obs:
        if o["url"]: lignes[norm(o["url"])].append(o)
    for u, os_ in lignes.items():
        rs = par_url.get(u, [])
        if len(os_) == 1 and len(rs) == 1 and os_[0]["id"] not in deja:
            print(json.dumps({"observatoire": os_[0]["id"], "nom": os_[0]["nom"], "id": rs[0]["id"], "titre": rs[0]["t"]}, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--observatoire", required=True); ap.add_argument("--edition", required=True)
    ap.add_argument("--spp", required=True); ap.add_argument("--date-spp", required=True, help="date du fichier export-experiences.csv (AAAA-MM-JJ)")
    ap.add_argument("--proposer", action="store_true", help="liste les rattachements univoques Observatoire → index absents de observatoire_rattachement.json")
    A = ap.parse_args()
    obs = []
    for o in lire_observatoire(A.observatoire):
        taux = (o.get("Taux audit RGAA") or "").replace("\xa0", " ").replace(",00 %", " %").strip()
        obs.append({"id": o["ID Démarche"], "nom": o["Nom Démarche"], "url": (o.get("URL Démarche") or "").strip(),
                    "acc": STATUTS.get((o.get("Prise en compte Handicap") or "").strip(), ""), "taux": taux,
                    "fc": (o.get("FranceConnect") or "").strip(), "dlnuf": (o.get("Score DLNUF") or "").strip(),
                    "date_declaration": (o.get("Date Publication Déclaration") or "").strip()})
    if A.proposer: proposer(obs); return
    spp, debut = lire_spp(A.spp, datetime.date.fromisoformat(A.date_spp))
    out = {"objet": "Agrégats d'accessibilité et de vigilance, produits par scripts/assistant/qualite.py et lus par build_index.py. Aucun texte d'usager, aucun pseudonyme.",
           "sources": {"observatoire": {"edition": A.edition, "jeu": "https://www.data.gouv.fr/datasets/observatoire-de-la-qualite-des-demarches-en-ligne"},
                       "spp": {"date": A.date_spp, "debut": debut, "jeu": "https://www.data.gouv.fr/datasets/64c062e02590f67d0f9f7201",
                               "seuil_retours": SEUIL_RETOURS, "seuil_motif": SEUIL_MOTIF, "criteres": CRITERES}},
           "observatoire": obs, "spp": spp}
    (D / "assistant" / "qualite.json").write_text(json.dumps(out, ensure_ascii=False, indent=0) + "\n", encoding="utf-8")
    print(f"Observatoire : {len(obs)} démarches ; Services Publics + depuis {debut} : {len(spp['demarche'])} démarches et "
          f"{len(spp['structure'])} structures d'au moins {SEUIL_RETOURS} retours")


if __name__ == "__main__":
    main()
