#!/usr/bin/env python3
"""Étape 1 — Référentiel "obligations SVA" propre.

Source officielle : data.gouv.fr "Liste des démarches concernées par le
principe Silence vaut accord", XML du 08/12/2016 (perimetre "État et ses
établissements publics"). À défaut d'accès réseau, obligations.csv (export
FileMaker corrompu, fins de ligne Mac, déjà nettoyé en amont -> 1283 lignes)
sert de secours et de source pour la colonne Cerfa (absente du XML officiel).

N'écrit jamais obligations.csv ni les fichiers dila/ : sortie datée dans out/.
"""
import csv
import re
import sys
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
OUT = HERE.parent / "out"
OUT.mkdir(exist_ok=True)

XML_PATH = DATA / "liste_sva_2016_09.xml"
CSV_PATH = DATA / "obligations_clean_1283.csv"
SOURCE_DATE = "2016-12-08"
TODAY = date.today().isoformat()


def norm_title(s):
    s = (s or "").replace("’", "'").replace("–", "-").replace("−", "-")
    s = s.replace("«", '"').replace("»", '"').replace("“", '"').replace("”", '"')
    s = re.sub(r"\s+", " ", s).strip().lower()
    s = re.sub(r"(\w)- (\w)", r"\1\2", s)  # recolle les coupures de mot "faculta- tive"
    s = s.replace("état", "etat")
    s = re.sub(r"\br\.\s*(\d)", r"r\1", s)
    s = re.sub(r"\bl\.\s*(\d)", r"l\1", s)
    return s


def norm_reference(ref):
    """Article(s) de référence normalisés : espaces supprimés, tirets unifiés."""
    ref = (ref or "").strip()
    ref = ref.replace("’", "'").replace("–", "-")
    ref = re.sub(r"\s+", " ", ref)
    return ref


def norm_reference_key(ref):
    """Clé de rapprochement, plus agressive que norm_reference (affichage) :
    sert uniquement à désambiguïser deux obligations qui partagent un titre
    identique (ex. deux dérogations "durées de travail" avec des articles
    différents) -- jamais utilisée pour l'affichage."""
    s = norm_reference(ref).lower()
    s = re.sub(r"\s*\((?:\d+)(?:er|e|eme|ème)?\s*alin[ée]a\)", "", s)  # "(2e alinéa)" / "(2ème alinéa)"
    s = re.sub(r"(\d)(?:er|e|eme|ème|o|°)\b", r"\1", s)  # "2ème"/"2e"/"1er"/"3°" -> "2"/"1"/"3"
    s = re.sub(r"[^a-z0-9]", "", s)
    return s


def load_ministeres(root):
    table = {}
    for m in root.find("ministeres").findall("ministere"):
        nor = (m.findtext("nor") or "").strip()
        table[nor] = (m.findtext("ministere_affichage") or "").strip()
    return table


def load_csv_fallback():
    """col6=ref sequentiel, col0=reference brute, col1=organisme, col2=delai,
    col5=constante doc (ignorée), col7=ministere, col9=intitule, col10=type,
    col11=cerfa eventuel."""
    rows = []
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        for row in csv.reader(f):
            rows.append(row)
    return rows


def main():
    if not XML_PATH.exists():
        print(f"XML absent ({XML_PATH}), abandon — obligations.csv seul ne suffit pas "
              "pour reconstituer les textes complets (étape 1 exige la source officielle).",
              file=sys.stderr)
        sys.exit(1)

    tree = ET.parse(XML_PATH)
    root = tree.getroot()
    ministeres = load_ministeres(root)

    dispositions = root.find("dispositions").findall("disposition")
    etat = [d for d in dispositions if (d.findtext("perimetre") or "") == "État et ses établissements publics"]
    print(f"[étape 1] dispositions brutes (périmètre État) : {len(etat)}")

    # Dédoublonnage : un doublon exact signalé (numdispo 1445 et 1449, libéralité Alsace-Moselle)
    seen = {}
    doublons = []
    uniq = []
    for d in etat:
        key = (
            norm_reference(d.findtext("reference")),
            norm_title(d.findtext("dispo")),
            (d.findtext("sourcetexte") or "").strip(),
            (d.findtext("concerne") or "").strip(),
        )
        if key in seen:
            doublons.append((seen[key], d.findtext("numdispo")))
            continue
        seen[key] = d.findtext("numdispo")
        uniq.append(d)
    print(f"[étape 1] doublons exacts retirés : {len(doublons)} -> {doublons}")
    print(f"[étape 1] base après dédoublonnage : {len(uniq)}")
    if len(uniq) != 1283:
        print(f"[étape 1] ATTENTION : {len(uniq)} != 1283 attendu, à vérifier avant publication.",
              file=sys.stderr)

    # Jointure avec obligations.csv (fallback Cerfa) par (titre normalisé, référence) :
    # le titre seul ne suffit pas -- plusieurs obligations distinctes partagent parfois un
    # intitulé identique (ex. deux "dérogations durées de travail" sur des articles différents,
    # numdispo 719 vs 754) ; la référence désambiguïse, avec repli positionnel si elle manque.
    csv_rows = load_csv_fallback()
    csv_by_title = {}
    for row in csv_rows:
        csv_by_title.setdefault(norm_title(row[9]), []).append(row)

    # ordre de document des dispositions XML par titre normalisé, pour le repli positionnel
    xml_order_by_title = {}
    for d in uniq:
        xml_order_by_title.setdefault(norm_title(d.findtext("dispo")), []).append(d.findtext("numdispo"))

    csv_used = set()  # (titre_normalise, ref_csv) déjà consommés, pour ne pas réutiliser une ligne CSV

    out_rows = []
    n_cerfa = 0
    n_ministere_xml = 0
    n_ministere_csv_fallback = 0
    n_ambigu_non_resolu = 0
    for d in uniq:
        numdispo = d.findtext("numdispo")
        intitule = (d.findtext("dispo") or "").strip()
        reference = norm_reference(d.findtext("reference"))
        source = (d.findtext("sourcetexte") or d.findtext("source") or "").strip()
        concerne = (d.findtext("concerne") or "").strip()
        delai = (d.findtext("delai") or "").strip()
        ministere_code = (d.findtext("ministere") or "").strip()
        ministere = ministeres.get(ministere_code, "")

        cerfa = ""
        t_key = norm_title(intitule)
        csv_match = csv_by_title.get(t_key, [])
        chosen = None
        if len(csv_match) == 1:
            chosen = csv_match[0]
        elif len(csv_match) > 1:
            ref_key = norm_reference_key(reference)
            same_ref = [r for r in csv_match if norm_reference_key(r[0]) == ref_key and (t_key, r[6]) not in csv_used]
            if len(same_ref) == 1:
                chosen = same_ref[0]
            else:
                # repli positionnel : même rang d'apparition dans les deux listes (ordre de document)
                remaining = [r for r in csv_match if (t_key, r[6]) not in csv_used]
                position = xml_order_by_title[t_key].index(numdispo)
                if position < len(remaining):
                    chosen = remaining[position]
                elif remaining:
                    chosen = remaining[0]
                else:
                    n_ambigu_non_resolu += 1
        if chosen is not None:
            csv_used.add((t_key, chosen[6]))
            cerfa = chosen[11].strip()
            if not ministere:
                ministere = chosen[7].strip()
                if ministere:
                    n_ministere_csv_fallback += 1
        if ministere_code:
            n_ministere_xml += 1
        if cerfa:
            n_cerfa += 1

        out_rows.append({
            "numdispo": numdispo,
            "intitule": intitule,
            "reference": reference,
            "texte_source": source,
            "autorite_competente": concerne,
            "delai": delai,
            "ministere": ministere,
            "type": "habilitation",
            # Colonne volontairement renommée pour ne jamais être prise pour une donnée
            # vérifiée : sur les 35 valeurs non vides, vérification croisée contre le
            # registre DILA (titre réel du Cerfa) le 26/10/2026 -- 0 confirmées correctes
            # (la seule qui semblait l'être, 1118->14531, s'est révélée attachée à la
            # mauvaise obligation : le Cerfa 14531 cite L362-1-1, la référence de 260, pas
            # de 1118). Ne jamais utiliser cette colonne comme témoin sans revérifier.
            "cerfa_eventuel_non_fiable_sans_verification": cerfa,
            "date_maj_source": SOURCE_DATE,
        })

    out_path = OUT / f"obligations_sva_{TODAY}.csv"
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)

    print(f"[étape 1] titres ambigus non résolus (Cerfa non repris par prudence) : {n_ambigu_non_resolu}")
    print(f"[étape 1] ministère résolu via code XML : {n_ministere_xml}")
    print(f"[étape 1] ministère résolu via repli CSV (titre) : {n_ministere_csv_fallback}")
    print(f"[étape 1] Cerfa éventuel renseigné : {n_cerfa}")
    print(f"[étape 1] écrit {out_path} ({len(out_rows)} lignes)")


if __name__ == "__main__":
    main()
