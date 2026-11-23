#!/usr/bin/env python3
"""Rafraîchit les fiches DILA du répertoire (mise à jour hebdomadaire), avant build_index.py.

    python3 scripts/assistant/maj_dila.py [--carto ~/Documents/cartographie] [--sans-telechargement]

1. Télécharge les trois exports « Fiches pratiques et ressources » de service-public.gouv.fr (DILA, données ouvertes,
   Licence Ouverte), format 3.5 : particuliers, professionnels, associations
   (https://lecomarquage.service-public.gouv.fr/vdd/3.5/<part|pro|asso>/zip/vosdroits-latest.zip).
2. Les décompresse dans <carto>/dila/raw/extracted_part, extracted_pro, extracted_asso. L'export d'avant est déplacé,
   pas effacé, dans <carto>/dila/raw/precedent/ (un seul niveau gardé).
3. Écrit les tables lues par build_index.py dans <carto>/dila/ : dila_fiches.jsonl, dila_liens_demarches.jsonl,
   dila_documents.jsonl, dila_formulaires.jsonl (mêmes formats que les anciens parse_dila.py et
   parse_dila_formulaires.py, repris ici pour que la production de la page vive dans le dépôt), et export_dila.json
   (date de chaque export, lue dans l'en-tête Last-Modified), que build_index.py reporte dans index_meta.json.

Ne fait aucun commit. Les sources restent hors dépôt (trop volumineuses), comme l'export du descriptif.
"""
import argparse, datetime, email.utils, glob, json, os, re, shutil, sys, urllib.request, zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

EXPORTS = {"particuliers": ("part", "extracted_part"), "professionnels": ("pro", "extracted_pro"), "associations": ("asso", "extracted_asso")}
URL = "https://lecomarquage.service-public.gouv.fr/vdd/3.5/{}/zip/vosdroits-latest.zip"
DC = "{http://purl.org/dc/elements/1.1/}"
URL_RE = re.compile(r"https?://(?:www\.)?(?:demarche\.numerique\.gouv\.fr|demarches-simplifiees\.fr)/commencer/([A-Za-z0-9\-]+)")


def text_of(el):
    if el is None: return None
    return "".join(el.itertext()).strip() or None


def lire_fiche(raw, source_export):
    """Fiche, liens vers Démarche Numérique, pièces à fournir (ancien parse_dila.py)."""
    root = ET.fromstring(raw)
    fid = root.get("ID")
    audiences = [text_of(a) for a in root.findall("Audience")]
    theme_el = root.find("Theme")
    theme = text_of(theme_el.find("Titre")) if theme_el is not None else None
    fiche = {"fiche_id": fid, "source_export": source_export, "root_tag": root.tag, "type": root.get("type"),
             "titre": text_of(root.find(f"{DC}title")), "audience": ";".join(a for a in audiences if a) or None,
             "theme": theme or text_of(root.find(f"{DC}subject")), "description": text_of(root.find(f"{DC}description")),
             "date_maj": text_of(root.find(f"{DC}date")), "sources_legifrance": text_of(root.find(f"{DC}source"))}
    liens, vus = [], set()
    for m in URL_RE.finditer(raw):
        if m.group(1) in vus: continue
        vus.add(m.group(1)); liens.append({"fiche_id": fid, "slug": m.group(1), "url": m.group(0)})
    docs = []
    for docs_el in root.iter("Documents"):
        ordre = 0
        for item in docs_el.iter("Item"):
            txt = text_of(item)
            if txt:
                ordre += 1; docs.append({"fiche_id": fid, "ordre": ordre, "texte": txt})
    return root, fiche, liens, docs


def lire_formulaire(root, source_export):
    """Formulaire, lien web, notice, service en ligne alternatif (ancien parse_dila_formulaires.py)."""
    lien_web, notice = root.find("LienWeb"), root.find("NoticeLiee")
    alt_ts, alt_form = root.find("ServiceEnLigneAlternatif"), root.find("FormulaireAlternatif")
    row = {"fiche_id": root.get("ID"), "source_export": source_export, "type": root.get("type"),
           "numero_cerfa": text_of(root.find("NumeroCerfa")),
           "lien_web_url": lien_web.get("URL") if lien_web is not None else None,
           "lien_web_format": lien_web.get("format") if lien_web is not None else None,
           "notice_url": notice.get("URL") if notice is not None else None,
           "notice_numero": notice.get("numerocerfa") if notice is not None else None,
           "alt_teleservice_id": alt_ts.get("ID") if alt_ts is not None else None,
           "alt_teleservice_titre": text_of(alt_ts.find("Titre")) if alt_ts is not None else None,
           "alt_formulaire_id": alt_form.get("ID") if alt_form is not None else None,
           "alt_formulaire_titre": text_of(alt_form.find("Titre")) if alt_form is not None else None}
    return row if any(row[k] for k in ("numero_cerfa", "lien_web_url", "notice_url", "alt_teleservice_id", "alt_formulaire_id")) else None


def ecrire_jsonl(chemin, lignes):
    with open(chemin, "w", encoding="utf-8") as f:
        for r in lignes: f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--carto", default=os.path.expanduser("~/Documents/cartographie"))
    ap.add_argument("--sans-telechargement", action="store_true", help="reprend les zips déjà présents dans <carto>/dila/raw/")
    A = ap.parse_args()
    dila = Path(A.carto) / "dila"; raw = dila / "raw"; prec = raw / "precedent"
    meta_chemin = dila / "export_dila.json"
    meta = json.loads(meta_chemin.read_text(encoding="utf-8")) if meta_chemin.exists() else {}

    if not A.sans_telechargement:
        nouveaux = {}
        for nom, (code, _) in EXPORTS.items():   # tout télécharger d'abord : rien n'est déplacé si un téléchargement échoue
            tmp = raw / f"{nom}.zip.part"
            with urllib.request.urlopen(URL.format(code), timeout=300) as r:
                tmp.write_bytes(r.read())
                lm = r.headers.get("Last-Modified")
            zipfile.ZipFile(tmp).testzip()
            nouveaux[nom] = (tmp, email.utils.parsedate_to_datetime(lm).date().isoformat() if lm else datetime.date.today().isoformat())
        prec.mkdir(parents=True, exist_ok=True)
        for nom, (code, dossier) in EXPORTS.items():
            for x in (raw / f"{nom}.zip", raw / dossier):
                if x.exists():
                    cible = prec / x.name
                    if cible.is_dir(): shutil.rmtree(cible)
                    elif cible.exists(): cible.unlink()
                    shutil.move(str(x), str(cible))
            tmp, date = nouveaux[nom]
            tmp.rename(raw / f"{nom}.zip")
            with zipfile.ZipFile(raw / f"{nom}.zip") as z: z.extractall(raw / dossier)
            meta[nom] = {"date": date, "source": URL.format(code)}
            print(f"{nom} : export du {date}")

    fiches, liens, docs, forms, erreurs = [], [], [], [], 0
    for nom, (_, dossier) in EXPORTS.items():
        fichiers = sorted(glob.glob(str(raw / dossier / "*.xml")))
        for chemin in fichiers:
            try:
                txt = open(chemin, encoding="utf-8").read()
                root, f, l, d = lire_fiche(txt, nom)
            except (OSError, ET.ParseError):
                erreurs += 1; continue
            fiches.append(f); liens += l; docs += d
            g = lire_formulaire(root, nom)
            if g: forms.append(g)
        print(f"{nom} : {len(fichiers)} fichiers")
    ecrire_jsonl(dila / "dila_fiches.jsonl", fiches)
    ecrire_jsonl(dila / "dila_liens_demarches.jsonl", liens)
    ecrire_jsonl(dila / "dila_documents.jsonl", docs)
    ecrire_jsonl(dila / "dila_formulaires.jsonl", forms)
    meta_chemin.write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"fiches : {len(fiches)}, liens vers Démarche Numérique : {len(liens)}, pièces : {len(docs)}, formulaires : {len(forms)}, erreurs : {erreurs}")


if __name__ == "__main__":
    main()
