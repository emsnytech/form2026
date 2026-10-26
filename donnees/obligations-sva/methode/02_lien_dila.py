#!/usr/bin/env python3
"""Étape 2 — Lien obligation SVA -> fiche DILA.

Lit en lecture seule cartographie/dila/dila_fiches.jsonl (8509 fiches) et le
référentiel obligations_sva produit par 01_referentiel_sva.py. N'écrit jamais
dans dila/. Deux méthodes, dans cet ordre :
  (a) référence juridique concordante : le nom du texte source ET le numéro
      d'article de l'obligation apparaissent tous les deux dans le titre ou
      la description de la fiche -> confiance "forte".
  (b) titre proche ET autorité cohérente : chevauchement de mots-clés sur le
      titre au-dessus d'un seuil, ET le nom de l'autorité compétente (ou du
      ministère) apparaît dans le titre/la description de la fiche ->
      confiance "moyenne". Un titre proche seul ne suffit pas.
Les fiches génériques qui remontent sur presque tout (MonIdenum, Assurance
décennale, Statuts d'association...) sont mises en liste noire par fréquence
avant le rapprochement (b), qui serait sinon noyé de faux positifs.
Seuls les liens "forte"/"moyenne" sont publiés ; rien en confiance faible.
"""
import csv
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "out"
DILA_DIR = Path.home() / "Documents" / "cartographie" / "dila"
TODAY = date.today().isoformat()

STOP = set("de des du le la les un une et en à au aux pour par sur avec ou son sa ses leur "
           "leurs d l dans ce cette ces qui que dont est sont être avoir".split())

BLACKLIST_TOP_N = 15      # nombre de fiches les plus fréquentes mises en liste noire
BLACKLIST_MIN_HITS = 25   # et seulement si elles dépassent ce seuil d'apparitions


def tokens(s):
    s = (s or "").lower().replace("’", "'")
    s = re.sub(r"[^a-zàâäéèêëïîôöùûüçœ0-9']", " ", s)
    return set(w.strip("'") for w in s.split() if len(w.strip("'")) > 2 and w.strip("'") not in STOP)


def ref_article_token(reference):
    """Isole un identifiant d'article exploitable comme preuve de référence
    concordante (ex. 'L111-17', 'R214-57') ; renvoie None si la référence
    de l'obligation est trop générique pour servir de preuve (ex. un simple
    numéro d'article de décret comme '3', sans code)."""
    m = re.search(r"\b([lrd]\.?\s?\*?\d+(?:-\d+)*)\b", (reference or "").lower())
    if not m:
        return None
    tok = re.sub(r"[.\s]", "", m.group(1))
    if len(tok) < 4:  # ex. "d'3" isolé -> pas assez specifique
        return None
    return tok


def main():
    obl_path = sorted(OUT.glob("obligations_sva_*.csv"))[-1]
    with obl_path.open(newline="", encoding="utf-8") as f:
        obligations = list(csv.DictReader(f))
    print(f"[étape 2] référentiel chargé : {obl_path.name} ({len(obligations)} obligations)")

    fiches = [json.loads(l) for l in (DILA_DIR / "dila_fiches.jsonl").open(encoding="utf-8")]
    for f in fiches:
        f["_tok_titre"] = tokens(f.get("titre"))
        f["_tok_desc"] = tokens(f.get("description"))
        f["_text_full"] = ((f.get("titre") or "") + " " + (f.get("description") or "")).lower()
    print(f"[étape 2] fiches DILA chargées : {len(fiches)}")

    # --- liste noire par fréquence : combien de fois chaque fiche apparaît en
    # tête de classement (chevauchement >=2 mots) sur l'ensemble des 1283 obligations
    freq = Counter()
    cand_cache = {}
    for obl in obligations:
        tok = tokens(obl["intitule"])
        if not tok:
            continue
        best = None
        best_score = 0
        for f in fiches:
            inter = tok & f["_tok_titre"]
            if len(inter) < 2:
                continue
            score = len(inter) / len(tok)
            if score > best_score:
                best_score, best = score, f
        cand_cache[obl["numdispo"]] = (tok, best, best_score)
        if best:
            freq[best["fiche_id"]] += 1

    blacklist = {fid for fid, n in freq.most_common(BLACKLIST_TOP_N) if n >= BLACKLIST_MIN_HITS}
    print(f"[étape 2] liste noire (fiches génériques, >= {BLACKLIST_MIN_HITS} apparitions en tête) :")
    for fid, n in freq.most_common(BLACKLIST_TOP_N):
        marque = " [EXCLUE]" if fid in blacklist else ""
        titre = next((f["titre"] for f in fiches if f["fiche_id"] == fid), "?")
        print(f"    {fid} ({n} fois){marque} : {titre[:70]}")

    # --- rapprochement (a) référence exacte puis (b) titre+autorité, hors liste noire
    liens = []
    n_forte = n_moyenne = 0
    for obl in obligations:
        tok = tokens(obl["intitule"])
        if not tok:
            continue
        source_tok = tokens(obl["texte_source"])
        art_tok = ref_article_token(obl["reference"])

        meilleure_forte = None
        meilleure_moyenne = None
        meilleure_moyenne_score = 0
        for f in fiches:
            if f["fiche_id"] in blacklist:
                continue
            inter_titre = tok & f["_tok_titre"]
            inter_all = tok & (f["_tok_titre"] | f["_tok_desc"])
            if len(inter_all) < 2:
                continue

            # (a) référence concordante : nom du texte source (>=1 mot significatif, hors
            # mots type "code"/"décret") ET numéro d'article, tous deux dans le texte de la fiche
            if art_tok and art_tok in re.sub(r"[.\s]", "", f["_text_full"]):
                source_sig = source_tok - {"code", "decret", "loi", "arrete", "arrêté", "décret"}
                if source_sig and (source_sig & (f["_tok_titre"] | f["_tok_desc"])):
                    if meilleure_forte is None:
                        meilleure_forte = f

            # (b) titre proche ET autorité cohérente -- un titre proche seul ne suffit pas
            # (consigne). Limite assumée et documentée : les fiches DILA n'ont pas de champ
            # "administration" (confirmé sur le schéma des 8509 fiches) ; "autorité cohérente"
            # est donc testée par chevauchement de mots-clés avec le titre/la description de
            # la fiche (pas une sous-chaîne exacte du nom complet, trop stricte en pratique),
            # ce qui reste un filtre, pas une garantie.
            score = len(inter_titre) / max(1, len(tok))
            if score >= 0.4 and len(inter_titre) >= 2 and score > meilleure_moyenne_score:
                autorite_tok = tokens(obl["autorite_competente"]) | tokens(obl["ministere"])
                if autorite_tok & (f["_tok_titre"] | f["_tok_desc"]):
                    meilleure_moyenne_score, meilleure_moyenne = score, f

        if meilleure_forte is not None:
            liens.append(_row(obl, meilleure_forte, "reference", "forte"))
            n_forte += 1
        elif meilleure_moyenne is not None:
            liens.append(_row(obl, meilleure_moyenne, "titre+autorite", "moyenne"))
            n_moyenne += 1

    out_path = OUT / f"liens_obligations_dila_{TODAY}.csv"
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["numdispo", "fiche_id", "fiche_titre", "methode", "confiance", "date"])
        w.writeheader()
        w.writerows(liens)

    print(f"[étape 2] liens confiance forte : {n_forte}")
    print(f"[étape 2] liens confiance moyenne : {n_moyenne}")
    print(f"[étape 2] total publié (forte+moyenne, faible exclue) : {len(liens)} / {len(obligations)}")
    print(f"[étape 2] écrit {out_path}")


def _row(obl, fiche, methode, confiance):
    return {
        "numdispo": obl["numdispo"],
        "fiche_id": fiche["fiche_id"],
        "fiche_titre": fiche["titre"],
        "methode": methode,
        "confiance": confiance,
        "date": TODAY,
    }


if __name__ == "__main__":
    main()
