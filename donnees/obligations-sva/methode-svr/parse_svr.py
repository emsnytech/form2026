#!/usr/bin/env python3
"""Parse decret SVR.xlsx -> obligations_svr_AAAA-MM-JJ.csv + delais_sva_derogatoires_AAAA-MM-JJ.csv

Structure constatée (lecture manuelle de 1266, 1293, 1294, 1263 avant d'écrire ce script) :
- Chaque feuille = un décret. Ligne 0 = intitulé complet (décret, date, fondement, ministère).
- La nature (SVR ou délai SVA) est determinée par l'intitulé de l'Article 1 du décret, qui dit
  soit "...vaut décision de rejet..." (SVR) soit "...vaut décision d'acceptation..." (délai SVA).
  Les décrets dont le titre mentionne a la fois "silence vaut acceptation" (l'exception) ET
  "exceptions au délai de deux mois" restent de nature SVR : le second volet (Article 2) ne fait
  que fixer, pour les mêmes procédures, un délai de rejet différent de deux mois -- ce n'est
  jamais une deuxième liste de nature différente (vérifié sur 1294 : Article 1 = rejet,
  Article 2 = modulation du délai de CE rejet, annexe unique).
- La vraie table commence à la ligne dont la colonne A == "OBJET DE LA DEMANDE" (il peut y avoir
  un marqueur "Annexe" isolé plus haut, sans table immédiate -- ne pas s'y fier).
- Après l'en-tête, 1 à 3 lignes de continuation du libellé de la colonne délai (A et B vides) à
  ignorer.
- Une ligne à une seule cellule (A rempli, B et C vides) = intertitre (texte de référence), à
  reporter sur les lignes suivantes jusqu'au prochain intertitre.
- Une ligne avec A rempli et (B ou C) rempli = procédure.
- Fin de table : ligne "NOTA" ou "Fait le ..." (bloc de signature).
- Edge cases rencontrés : dispositions parfois un nombre Excel (ex. 3 au lieu de "Article 3") --
  converti en texte. Une ligne A vide mais B rempli (rattachement à la procédure précédente) --
  signalée, pas fusionnée silencieusement.
"""
import csv
import re
import openpyxl
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
TODAY = date.today().isoformat()
WORKBOOK = HERE / "decret SVR.xlsx"

EXCLUS = {"1302", "1268"}  # retires volontairement (hors sujet / abroge), confirme par l'auteur

CAS_1265_TRANSVERSAL = "1265"
CAS_1263_SANS_ANNEXE = "1263"

HEADER_OBJET = "OBJET DE LA DEMANDE"


def norm_cell(v):
    if v is None:
        return ""
    if isinstance(v, (int, float)):
        if float(v).is_integer():
            return str(int(v))
        return str(v)
    return str(v).replace("\xa0", " ").strip()


def extraire_entete(rows, decret_id):
    titre = norm_cell(rows[0][0]) if rows else ""
    # numero + date
    m = re.search(r"Décret n°\s*(\d{4}-\d+) du (\d{1,2} \w+ \d{4})", titre)
    numero = m.group(1) if m else decret_id
    date_txt = m.group(2) if m else ""
    # ministere : entre parentheses, en general en toute fin de titre
    m_min = re.findall(r"\(([^()]+)\)\s*$", titre)
    ministere = m_min[0].strip() if m_min else ""
    # fondement : la partie "sur le fondement du ... de l'article ..."
    m_fond = re.search(r"sur le fondement (du|de l'article)\s+(.+?)(?:\s*\(|$)", titre)
    fondement = m_fond.group(0).strip() if m_fond else ""
    # JORF
    jorf = ""
    for row in rows[:10]:
        c0 = norm_cell(row[0]) if row else ""
        if c0.startswith("JORF"):
            jorf = c0
            break
    # version consolidee / modifie par
    version = ""
    for row in rows[:12]:
        c0 = norm_cell(row[0]) if row else ""
        if c0.startswith("Dernière mise à jour"):
            version = c0.replace("Dernière mise à jour des données de ce texte :", "").strip()
            break
        if c0.startswith("Modifié par") and not version:
            version = c0
    return {
        "numero": numero, "date": date_txt, "ministere": ministere,
        "fondement": fondement, "titre": titre, "jorf": jorf, "version": version,
    }


def determiner_nature(rows):
    """Lit l'Article 1 du décret : 'vaut décision de rejet' -> SVR,
    'vaut décision d'acceptation' -> délai SVA."""
    for row in rows:
        c0 = norm_cell(row[0]) if row else ""
        if "vaut décision de rejet" in c0 or "vaut décision implicite de rejet" in c0:
            return "SVR"
        if "vaut décision d'acceptation" in c0 or "vaut décision d’acceptation" in c0:
            return "delai_sva"
        if "vaut décision implicite d'acceptation" in c0 or "vaut décision implicite d’acceptation" in c0:
            return "delai_sva"
    return None  # tranché par le titre en repli, voir main()


def trouver_debut_table(rows):
    for i, row in enumerate(rows):
        c0 = norm_cell(row[0]) if row else ""
        if c0.upper() == HEADER_OBJET:
            return i
    return None


def parser_table(rows, start_idx, decret_meta, anomalies):
    """Retourne la liste des procedures (objet, dispositions, delai, texte_reference)."""
    procedures = []
    i = start_idx + 1
    # ignorer les lignes de suite de l'entete : aucune procedure ni intertitre reel n'a
    # jamais la colonne A vide, donc tant que A est vide on est encore dans l'entete (sa
    # longueur varie : 1 a 4 lignes selon les feuilles -- "DISPOSITIONS"/"applicables" sur
    # deux lignes dans certaines, "a la date du 12 novembre 2014" rallonge l'entete delai
    # dans d'autres : constate sur 1266, 1279, 1283, 1294).
    while i < len(rows):
        row = rows[i]
        a = norm_cell(row[0])
        if a == "":
            i += 1
            continue
        break

    intertitre = ""
    n_rattachees = 0
    while i < len(rows):
        row = rows[i]
        a = norm_cell(row[0])
        b = norm_cell(row[1]) if len(row) > 1 else ""
        c = norm_cell(row[2]) if len(row) > 2 else ""

        if a.upper().startswith("NOTA") or a.startswith("Fait le"):
            break
        if a == "" and b == "" and c == "":
            i += 1
            continue
        if a == "" and (b != "" or c != ""):
            # cas rare (1306, ligne 75) : la disposition est poussee une ligne AVANT
            # l'objet au lieu d'apres (artefact d'export) -- si la ligne suivante a un
            # objet mais pas de disposition propre, rattacher en avant plutot qu'en arriere.
            nxt = rows[i + 1] if i + 1 < len(rows) else None
            nxt_a = norm_cell(nxt[0]) if nxt else ""
            nxt_b = norm_cell(nxt[1]) if nxt and len(nxt) > 1 else ""
            nxt_c = norm_cell(nxt[2]) if nxt and len(nxt) > 2 else ""
            # nxt_c != "" exclu un intertitre (B et C vides) pris a tort pour une
            # procedure a qui rattacher la disposition en avant (constate sur 1294/187).
            if nxt_a != "" and nxt_b == "" and nxt_c != "" and b != "":
                procedures.append({"texte_reference": intertitre, "objet": nxt_a,
                                    "dispositions": b, "delai": nxt_c})
                anomalies.append({"decret": decret_meta["numero"], "ligne_excel": i + 1,
                                   "type": "disposition_rattachee_en_avant", "contenu": f"objet suivant: {nxt_a[:60]}"})
                i += 2
                continue
            # disposition ou delai complementaire, rattache a la procedure precedente
            # (constate : une meme procedure peut citer plusieurs textes sur plusieurs
            # lignes -- ex. decret 1271, "Delivrance d'autorisations..." + Decret 2009-702
            # + Arrete 30/10/2009, toutes rattachees aux memes Articles 257 et 258).
            if procedures:
                if b:
                    procedures[-1]["dispositions"] = (procedures[-1]["dispositions"] + "; " + b).strip("; ")
                if c:
                    procedures[-1]["delai"] = (procedures[-1]["delai"] + "; " + c).strip("; ")
                n_rattachees += 1
            else:
                anomalies.append({
                    "decret": decret_meta["numero"], "ligne_excel": i + 1,
                    "type": "ligne_sans_objet_orpheline", "contenu": f"B={b!r} C={c!r}",
                })
            i += 1
            continue
        if b == "" and c == "":
            # intertitre
            intertitre = a
            i += 1
            continue
        # procedure
        procedures.append({
            "texte_reference": intertitre,
            "objet": a,
            "dispositions": b,
            "delai": c,
        })
        i += 1
    if n_rattachees:
        anomalies.append({
            "decret": decret_meta["numero"], "ligne_excel": 0,
            "type": "dispositions_multiples_rattachees", "contenu": f"{n_rattachees} lignes rattachees",
        })
    return procedures


def main():
    wb = openpyxl.load_workbook(WORKBOOK, data_only=True, read_only=True)
    sheet_names = [s for s in wb.sheetnames if s not in EXCLUS]
    print(f"[parse] feuilles a traiter : {len(sheet_names)} (sur {len(wb.sheetnames)}, "
          f"exclues : {sorted(EXCLUS)})")

    obligations_svr = []
    delais_sva = []
    anomalies = []
    lignes_par_decret = {}

    for name in sheet_names:
        ws = wb[name]
        rows = list(ws.iter_rows(values_only=True))
        meta = extraire_entete(rows, name)

        if name == CAS_1265_TRANSVERSAL:
            print(f"[parse] {name} : transversal sans annexe, garde en contexte, 0 procedure")
            lignes_par_decret[name] = 0
            continue

        if name == CAS_1263_SANS_ANNEXE:
            row = {
                "decret": meta["numero"], "date": meta["date"], "ministere": "Premier ministre",
                "fondement": meta["fondement"], "nature": "delai_sva",
                "texte_reference": "CRPA, articles L. 323-1 et L. 323-2",
                "objet": "Délivrance d'une licence de réutilisation des informations publiques conforme à une licence type",
                "dispositions": "CRPA, articles L. 323-1 et L. 323-2",
                "delai": "1 mois", "version_consolidee_au": meta["version"],
                "statut": "saisie manuelle",
            }
            delais_sva.append(row)
            lignes_par_decret[name] = 1
            print(f"[parse] {name} : cas particulier sans annexe, 1 procedure saisie a la main")
            continue

        nature = determiner_nature(rows)
        start = trouver_debut_table(rows)
        if start is None:
            print(f"[parse] ATTENTION {name} : aucune table trouvee (OBJET DE LA DEMANDE absent) -- a verifier a la main")
            lignes_par_decret[name] = 0
            continue

        if nature is None:
            # repli sur le titre
            titre_low = meta["titre"].lower()
            if "silence vaut acceptation" in titre_low or "le silence vaut acceptation" in titre_low:
                nature = "SVR"
            elif "décision implicite d'acceptation" in titre_low or "décisions implicites d'acceptation" in titre_low:
                nature = "delai_sva"
            else:
                nature = "INDETERMINE"
                anomalies.append({"decret": meta["numero"], "ligne_excel": 0,
                                   "type": "nature_indeterminee", "contenu": meta["titre"][:100]})

        procs = parser_table(rows, start, meta, anomalies)
        lignes_par_decret[name] = len(procs)

        for p in procs:
            row = {
                "decret": meta["numero"], "date": meta["date"], "ministere": meta["ministere"],
                "fondement": meta["fondement"], "nature": nature,
                "texte_reference": p["texte_reference"], "objet": p["objet"],
                "dispositions": p["dispositions"], "delai": p["delai"],
                "version_consolidee_au": meta["version"], "statut": "",
            }
            if nature == "SVR":
                obligations_svr.append(row)
            else:
                delais_sva.append(row)

        print(f"[parse] {name} ({nature}) : {len(procs)} procedures")

    print()
    print(f"[parse] TOTAL lignes SVR : {len(obligations_svr)}")
    print(f"[parse] TOTAL lignes delai SVA : {len(delais_sva)}")
    print(f"[parse] TOTAL general : {len(obligations_svr) + len(delais_sva)}")
    print(f"[parse] anomalies signalees : {len(anomalies)}")
    for a in anomalies[:30]:
        print("   ", a)

    out_dir = HERE / "out"
    out_dir.mkdir(exist_ok=True)
    fields = ["decret", "date", "ministere", "fondement", "nature", "texte_reference",
              "objet", "dispositions", "delai", "version_consolidee_au", "statut"]

    def dedoublonner(liste, label):
        """Doublon = meme decret + texte_reference + objet + dispositions (identiques en
        tout point). Un objet+dispositions identique seul ne suffit pas : plusieurs
        professions distinctes (notaire/commissaire-priseur/huissier...) partagent parfois
        un meme numero d'article par coincidence de redaction, sans etre le meme doublon --
        verifie a la main sur 2014-1277 avant de choisir cette cle plus stricte."""
        vus = {}
        gardees = []
        traces = []
        for r in liste:
            key = (r["decret"], r["texte_reference"].strip(), r["objet"].strip(), r["dispositions"].strip())
            if key in vus:
                traces.append({**r, "doublon_de_ligne": vus[key]})
                continue
            vus[key] = len(gardees) + 1
            gardees.append(r)
        print(f"[parse] dedoublonnage {label} : {len(liste)} -> {len(gardees)} "
              f"({len(traces)} doublons exacts retires)")
        return gardees, traces

    obligations_svr, doublons_svr = dedoublonner(obligations_svr, "SVR")
    delais_sva, doublons_delai = dedoublonner(delais_sva, "delai_sva")

    with (out_dir / f"obligations_svr_{TODAY}.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(obligations_svr)

    with (out_dir / f"delais_sva_derogatoires_{TODAY}.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(delais_sva)

    with (out_dir / f"doublons_retires_{TODAY}.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields + ["doublon_de_ligne"])
        w.writeheader()
        w.writerows(doublons_svr + doublons_delai)

    with (out_dir / f"anomalies_parsing_{TODAY}.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["decret", "ligne_excel", "type", "contenu"])
        w.writeheader()
        w.writerows(anomalies)

    with (out_dir / f"lignes_par_decret_{TODAY}.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["feuille", "nb_lignes"])
        for k, v in lignes_par_decret.items():
            w.writerow([k, v])

    print(f"[parse] ecrit dans {out_dir}/")


if __name__ == "__main__":
    main()
