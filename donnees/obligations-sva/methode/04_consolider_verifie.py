#!/usr/bin/env python3
"""Étape 4bis — Consolide le référentiel avec le statut de vérification.

Les liens "vérifiés" ci-dessous sont une liste figée, établie à la main par
relecture individuelle sur deux échantillons distincts (le test initial de 56
obligations, puis le nouvel échantillon de 50 liens produits demandé par la
consigne). Ce n'est pas un seuil de score : c'est la trace de ce qui a
réellement été lu et jugé, pas de ce que le rapprochement textuel a produit.
Tout le reste (liens produits par 02_lien_dila.py / 03_lien_demarches.py mais
jamais relus individuellement) reste un "candidat non vérifié" -- exporté à
part, jamais compté dans les indicateurs de la page.

Fusionne aussi le référentiel (étape 1) avec le drapeau "cadre juridique = la
seule ordonnance générique 2014-1330" (JORFTEXT000029716839), déjà calculé
par 03_lien_demarches.py pour chaque démarche candidate.
"""
import csv
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "out"
TODAY = date.today().isoformat()
JORFTEXT_ORDONNANCE_SVA = "JORFTEXT000029716839"

# --- Liens vérifiés à la main (numdispo, identifiant, méthode, confiance) -----------
# Fiches DILA : 8 du test à 56 (150,513,695,742,214,215,481,528 -> numdispo),
# 5 confirmés en confiance "moyenne" + 2 en confiance "forte" du nouvel échantillon à 50.
FICHES_VERIFIEES = [
    ("686", "F38895", "titre+autorite", "moyenne"),   # Cartes de guide conférencier
    ("1012", "R35397", "titre+autorite", "moyenne"),  # Agrément vin sans AOP/IGP
    ("259", "R21251", "titre+autorite", "moyenne"),   # Habilitation formation prof. danse
    ("260", "R2824", "titre+autorite", "moyenne"),    # Reconnaissance qualif. prof. danse
    ("1504", "F2111", "titre+autorite", "moyenne"),   # Dispense session approfondissement BAFA
    ("1505", "F2111", "titre+autorite", "moyenne"),   # Dispense session qualification BAFA
    ("661", "F871", "titre+autorite", "moyenne"),     # Report participation JDC
    ("713", "R49681", "titre+autorite", "moyenne"),   # Autorisation mineurs 14+ vacances scolaires
    ("562", "R1298", "titre+autorite", "moyenne"),    # Carte déporté interné résistant
    ("563", "R1299", "titre+autorite", "moyenne"),    # Carte déporté interné politique
    ("402", "R21500", "titre+autorite", "moyenne"),   # Agrément suivi régulier des rejets
    ("674", "R45176", "titre+autorite", "moyenne"),   # Habilitation organismes formation jeunesse/sport
    ("359", "F2861", "titre+autorite", "moyenne"),    # Première inscription université
    ("771", "R18249", "reference", "forte"),          # Autorisation coupe bois (Code forestier)
    ("778", "R18249", "reference", "forte"),          # Autorisation coupe bois, particuliers
]

# Démarches : 150->686 (correspondance 1->n, 10 démarches locales), 695->259, 742->260,
# 1220->320 du test à 56 ; 9 du nouvel échantillon à 50 (970,218,1438,375,1033,354,432,445,260).
DEMARCHES_VERIFIEES = [
    ("686", 102322), ("686", 113888), ("686", 139621), ("686", 32251), ("686", 90279),
    ("686", 89473), ("686", 139501), ("686", 86912), ("686", 39382), ("686", 113875),
    ("259", 77412),
    ("260", 64844),
    ("320", 89138),
    ("970", 98239),
    ("218", 97045),
    ("1438", 53938),
    ("375", 12794),
    ("1033", 96112),
    ("354", 110527),
    ("432", 41910),
    ("445", 52363),
]


def main():
    obl_path = sorted(OUT.glob("obligations_sva_*.csv"))[-1]
    with obl_path.open(newline="", encoding="utf-8") as f:
        obligations = list(csv.DictReader(f))
    with (sorted(OUT.glob("liens_obligations_dila_*.csv"))[-1]).open(newline="", encoding="utf-8") as f:
        liens_dila = list(csv.DictReader(f))
    with (sorted(OUT.glob("liens_obligations_dn_*.csv"))[-1]).open(newline="", encoding="utf-8") as f:
        liens_dn = list(csv.DictReader(f))

    fiche_verif_set = {(n, fid) for n, fid, _, _ in FICHES_VERIFIEES}
    fiche_verif_by_numdispo = {}
    for n, fid, methode, confiance in FICHES_VERIFIEES:
        fiche_verif_by_numdispo.setdefault(n, []).append((fid, methode, confiance))

    dn_verif_set = {(n, d) for n, d in DEMARCHES_VERIFIEES}
    dn_verif_by_numdispo = {}
    for n, d in DEMARCHES_VERIFIEES:
        dn_verif_by_numdispo.setdefault(n, []).append(d)

    dila_candidats = [(l["numdispo"], l["fiche_id"]) for l in liens_dila
                       if (l["numdispo"], l["fiche_id"]) not in fiche_verif_set]
    dn_candidats = [(l["numdispo"], l["demarche"]) for l in liens_dn
                     if (l["numdispo"], l["demarche"]) not in dn_verif_set]

    numdispo_dila_candidat = {n for n, _ in dila_candidats}
    numdispo_dn_candidat = {n for n, _ in dn_candidats}

    # drapeau ordonnance générique : vrai si une démarche vérifiée OU candidate de cette
    # obligation ne cite que l'ordonnance 2014-1330 comme cadre juridique
    jorf_generique_par_numdispo = set()
    for l in liens_dn:
        if l["cadre_est_texte_procedure_generique"] == "True":
            jorf_generique_par_numdispo.add(l["numdispo"])

    consolide = []
    n_fiche_verif = n_dn_verif = n_jorf = 0
    for obl in obligations:
        n = obl["numdispo"]
        statut_fiche = "aucun"
        if n in fiche_verif_by_numdispo:
            statut_fiche = "verifie"
            n_fiche_verif += 1
        elif n in numdispo_dila_candidat:
            statut_fiche = "candidat_non_verifie"

        statut_demarche = "aucun"
        if n in dn_verif_by_numdispo:
            statut_demarche = "verifie"
            n_dn_verif += 1
        elif n in numdispo_dn_candidat:
            statut_demarche = "candidat_non_verifie"

        jorf_generique = n in jorf_generique_par_numdispo
        if jorf_generique:
            n_jorf += 1

        row = dict(obl)
        row["statut_fiche_dila"] = statut_fiche
        row["statut_demarche_dn"] = statut_demarche
        row["cadre_demarche_est_ordonnance_generique_2014_1330"] = jorf_generique
        consolide.append(row)

    out_path = OUT / f"obligations_sva_avec_statut_{TODAY}.csv"
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(consolide[0].keys()))
        w.writeheader()
        w.writerows(consolide)

    # exports "à part" : vérifiés et candidats, séparément, pour chaque maillon
    def write_pairs(path, pairs, header):
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(pairs)

    write_pairs(OUT / f"liens_dila_verifies_{TODAY}.csv",
                [(n, fid, m, c) for n, fid, m, c in FICHES_VERIFIEES],
                ["numdispo", "fiche_id", "methode", "confiance"])
    write_pairs(OUT / f"liens_dila_candidats_non_verifies_{TODAY}.csv",
                dila_candidats, ["numdispo", "fiche_id"])
    write_pairs(OUT / f"liens_dn_verifies_{TODAY}.csv",
                DEMARCHES_VERIFIEES, ["numdispo", "demarche"])
    write_pairs(OUT / f"liens_dn_candidats_non_verifies_{TODAY}.csv",
                dn_candidats, ["numdispo", "demarche"])

    print(f"[étape 4bis] obligations : {len(obligations)}")
    print(f"[étape 4bis] avec fiche DILA vérifiée (numdispo distincts) : {n_fiche_verif}")
    print(f"[étape 4bis] avec démarche DN vérifiée (numdispo distincts) : {n_dn_verif}")
    print(f"[étape 4bis] candidats fiche non vérifiés (exportés à part) : {len(dila_candidats)}")
    print(f"[étape 4bis] candidats démarche non vérifiés (exportés à part) : {len(dn_candidats)}")
    print(f"[étape 4bis] obligations dont le cadre juridique déclaré par la démarche n'est "
          f"que l'ordonnance générique 2014-1330 : {n_jorf}")
    print(f"[étape 4bis] écrit {out_path.name} et les 4 fichiers vérifiés/candidats")


if __name__ == "__main__":
    main()
