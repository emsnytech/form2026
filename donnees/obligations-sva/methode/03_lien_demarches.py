#!/usr/bin/env python3
"""Étape 3 — Lien obligation SVA -> démarche(s) Démarche Numérique, en direct.

Le Cerfa n'est PAS un passage obligé (la plupart des démarches nées sur DN
n'en ont jamais eu) : le rapprochement se fait d'abord sur le titre, avec
deux signaux de corroboration quand ils existent -- le Cerfa éventuel et le
cadre juridique déclaré par la démarche (donnees/base-juridique/juridique_niveau1.csv,
étude FORM2026 distincte). Correspondance 1 -> n : toutes les démarches
plausibles sont gardées, pas seulement la meilleure.

Exclusions forcées, déjà établies à la main (faux amis repérés lors du test
sur 56 obligations -- durée minimale confondue avec maximale, seuil d'âge
différent, "agrément d'organisme" générique qui matchait en fait des stages
de sécurité routière) : ne doivent jamais remonter, quel que soit le score.
"""
import csv
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "out"
SITE = Path.home() / "Documents" / "form2026-site"
TODAY = date.today().isoformat()

STOP = set("de des du le la les un une et en à au aux pour par sur avec ou son sa ses leur "
           "leurs d l dans ce cette ces qui que dont est sont être avoir".split())

# numdispo des faux amis confirmés au tour précédent -- exclusion explicite et durable
FAUX_AMIS = {
    "719",   # dérogation durée max travail apprentis <18 -- matchs trouvés = durée MINIMALE temps partiel
    "758",   # dérogation durée hebdo max moyenne -- idem, confusion min/max
    "713",   # mineurs 14+ vacances scolaires -- matchs = mineurs 15+ en formation professionnelle
    "391", "1257",  # agrément organisme attestation gaz -- matchs = stages sécurité routière
    "1219",  # idem, variante "réseau de distribution de gaz"
}

JORFTEXT_ORDONNANCE_SVA = "JORFTEXT000029716839"  # Ordonnance 2014-1330, droit des usagers de
# saisir l'administration par voie électronique -- texte générique de procédure, cité par ~470-492
# démarches sans rapport avec leur objet : ne vaut jamais comme preuve de cadre juridique concordant.

SCORE_MIN = 0.35
INTER_MIN = 3


def tokens(s):
    s = (s or "").lower().replace("’", "'")
    s = re.sub(r"[^a-zàâäéèêëïîôöùûüçœ0-9']", " ", s)
    return set(w.strip("'") for w in s.split() if len(w.strip("'")) > 2 and w.strip("'") not in STOP)


def load_juridique_niveau1():
    path = SITE / "donnees" / "base-juridique" / "juridique_niveau1.csv"
    by_demarche = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            by_demarche[row["demarche"]] = row
    return by_demarche


def main():
    obl_path = sorted(OUT.glob("obligations_sva_*.csv"))[-1]
    with obl_path.open(newline="", encoding="utf-8") as f:
        obligations = list(csv.DictReader(f))

    demarches = []
    for i in range(4):
        demarches += json.loads((SITE / f"app_demarches_{i}.json").read_text(encoding="utf-8"))
    for d in demarches:
        d["_tok"] = tokens(d.get("titre"))
    print(f"[étape 3] {len(obligations)} obligations, {len(demarches)} démarches FORM2026")

    juridique = load_juridique_niveau1()
    print(f"[étape 3] cadre juridique déclaré disponible pour {len(juridique)} démarches (étude distincte)")

    liens = []
    n_obl_avec_demarche = 0
    n_jorf_generique = Counter()
    for obl in obligations:
        if obl["numdispo"] in FAUX_AMIS:
            continue
        tok = tokens(obl["intitule"])
        if not tok:
            continue
        candidats = []
        for d in demarches:
            inter = tok & d["_tok"]
            if len(inter) < INTER_MIN:
                continue
            score = len(inter) / len(tok)
            if score < SCORE_MIN:
                continue
            candidats.append((score, d))
        candidats.sort(key=lambda x: -x[0])

        if candidats:
            n_obl_avec_demarche += 1
        for score, d in candidats:
            cerfa_concorde = bool(obl["cerfa_eventuel_non_fiable_sans_verification"]) and obl["cerfa_eventuel_non_fiable_sans_verification"] in (d.get("cerfa_numeros") or "")
            jur = juridique.get(str(d["demarche"]))
            cadre_declare = (jur["cadre_declare"] if jur else "") or ""
            cadre_generique = JORFTEXT_ORDONNANCE_SVA in cadre_declare
            if cadre_generique:
                n_jorf_generique[obl["numdispo"]] += 1
            liens.append({
                "numdispo": obl["numdispo"],
                "obligation_intitule": obl["intitule"],
                "demarche": d["demarche"],
                "demarche_titre": d["titre"],
                "organisme": d["organisme"],
                "etat": d["etat"],
                "nb_dossiers": d.get("nb_dossiers") or 0,
                "score_titre": round(score, 2),
                "cerfa_concorde": cerfa_concorde,
                "cadre_declare_demarche": cadre_declare[:200],
                "cadre_est_texte_procedure_generique": cadre_generique,
                "date": TODAY,
            })

    out_path = OUT / f"liens_obligations_dn_{TODAY}.csv"
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(liens[0].keys()))
        w.writeheader()
        w.writerows(liens)

    print(f"[étape 3] obligations avec au moins une démarche : {n_obl_avec_demarche} / {len(obligations) - len(FAUX_AMIS)}")
    print(f"[étape 3] liens obligation->démarche produits (1->n) : {len(liens)}")
    print(f"[étape 3] liens dont le cadre juridique cité par la démarche n'est que "
          f"l'ordonnance générique {JORFTEXT_ORDONNANCE_SVA} (ne prouve rien) : "
          f"{sum(1 for l in liens if l['cadre_est_texte_procedure_generique'])}")
    print(f"[étape 3] liens avec concordance Cerfa : {sum(1 for l in liens if l['cerfa_concorde'])}")
    print(f"[étape 3] écrit {out_path}")


if __name__ == "__main__":
    main()
