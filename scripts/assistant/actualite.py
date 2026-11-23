#!/usr/bin/env python3
"""Propositions d'actualité pour la colonne « Démarches nationales » de l'accueil du répertoire (première version, à tester).

    python3 scripts/assistant/actualite.py --export <vosdroits-latest.zip | dossier> [--precedent <zip | dossier>]
                                          [--actualites <actualite-latest.zip | dossier>] [--date AAAA-MM-JJ]

Écrit donnees/assistant/actualite_nationales.json (les 10 meilleures candidates) et donnees/assistant/empreintes_dila.json
(une empreinte par fiche de l'export : date de modification, titre, services en ligne cités), qui sert de point de
comparaison à l'export suivant. Ce fichier de propositions ne change pas l'affichage : seule une entrée recopiée par
l'éditeur dans plus_demandees.json (editeur.ajout ou epingle) fait monter une démarche dans la colonne.

Signaux :
- 3a, exports DILA (fiches « Particuliers », https://lecomarquage.service-public.gouv.fr/vdd/3.5/part/zip/vosdroits-latest.zip) :
  nouvelles fiches F et nouveaux services en ligne R, fiches dont la date de modification a changé, comparées à
  l'export précédent (--precedent, sinon donnees/assistant/empreintes_dila.json).
- 3b, échéances : donnees/assistant/echeances.json, candidates entre leur date de début et leur échéance.
- 3c, actualités de service-public.gouv.fr (données ouvertes de la DILA, Licence Ouverte,
  https://lecomarquage.service-public.gouv.fr/actu/3.5/part/zip/actualite-latest.zip) : une fiche ou un service en ligne
  cité par une actualité des 15 derniers jours reçoit le bonus.

Note : quatre critères de 0 à 2 (personnes touchées, urgence, échéance, obligation), plus le bonus actualité. Les mots et les
poids, provisoires, sont en tête du script.
"""
import argparse, datetime, json, re, sys, unicodedata, zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

# ---------- Réglages provisoires (à affiner) ----------
POIDS = {"personnes": 1, "urgence": 1, "echeance": 1, "obligation": 1}
BONUS_ACTUALITE = 1
JOURS_ACTUALITE = 15          # une actualité compte pendant 15 jours après sa première mise en ligne
JOURS_SANS_ECHEANCE = 30      # date de sortie proposée faute d'échéance : 30 jours après l'apparition
JOURS_ECHEANCE_PROCHE = 60    # échéance « proche » : 2 points ; plus lointaine : 1 point
SEUIL_SIGNALEMENT = 6         # une nouvelle candidate notée au moins 6 est signalée dans le résumé
NB_PROPOSITIONS = 10
# Mots cherchés dans le titre et la description, sans accents ni casse.
CAS_PARTICULIERS = ["militaire", "forain", "marinier", "francais de l'etranger", "francais a l'etranger", "a l'etranger", "etranger",
                    "expatrie", "detenu", "gens du voyage", "sans domicile", "frontalier", "diplomate"]
PUBLIC_CIBLE = ["entreprise", "employeur", "agriculteur", "exploitant", "retraite", "etudiant", "apprenti", "fonctionnaire",
                "agent public", "association", "artisan", "commercant", "micro-entrepreneur", "auto-entrepreneur",
                "professionnel", "bailleur", "copropriete"]
URGENCE_CRISE = ["crise", "catastrophe", "intemperies", "inondation", "tempete", "cyclone", "secheresse", "emeutes",
                 "troubles urbains", "calamite"]
URGENCE_EXCEPTION = ["exceptionnel", "exceptionnelle", "d'urgence", "fonds d'urgence"]
OBLIGATION_DATEE = ["date limite", "avant le", "au plus tard", "sanction", "amende", "penalite", "majoration"]
OBLIGATION = ["obligatoire", "obligation"]
# Services en ligne retenus comme démarches (types R de l'export) ; les formulaires, modèles et simulateurs n'en sont pas.
TYPES_DEMARCHE = {"Téléservice", "selNG", "Téléservice personnalisé sur SP"}

RACINE = Path(__file__).resolve().parents[2]
D = RACINE / "donnees" / "assistant"
DC = "{http://purl.org/dc/elements/1.1/}"


def n_(s):
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower().replace("’", "'")


def contient(texte, mots):
    t = n_(texte).replace("’", "'")
    return [m for m in mots if re.search(r"(?<![a-z])" + re.escape(m) + r"(?![a-z])", t)]


def fichiers_xml(source):
    """(nom, octets) des fichiers F*.xml, R*.xml ou A*.xml d'un zip ou d'un dossier."""
    p = Path(source).expanduser()
    if p.is_dir():
        for f in sorted(p.rglob("*.xml")):
            if re.fullmatch(r"[FRA]\d+\.xml", f.name): yield f.name, f.read_bytes()
    else:
        with zipfile.ZipFile(p) as z:
            for nom in z.namelist():
                base = nom.rsplit("/", 1)[-1]
                if re.fullmatch(r"[FRA]\d+\.xml", base): yield base, z.read(nom)


def empreintes(source):
    """Une empreinte par fiche F ou service R : date de modification, titre, description, type, services en ligne cités."""
    out = {}
    for nom, octets in fichiers_xml(source):
        try:
            r = ET.fromstring(octets)
        except ET.ParseError:
            continue
        fid = r.get("ID") or nom[:-4]
        if fid[0] not in "FR": continue
        if (r.findtext(f"{DC}coverage") or "France entière").strip() != "France entière": continue
        date = (r.findtext(f"{DC}date") or "").replace("modified", "").strip()[:10]
        out[fid] = {"d": date, "t": (r.findtext(f"{DC}title") or "").strip(), "desc": (r.findtext(f"{DC}description") or "").strip(),
                    "ty": r.get("type") or "",
                    "r": [] if fid[0] == "R" else list(dict.fromkeys(s.get("ID") for s in r.iter("ServiceEnLigne")
                                                                     if s.get("ID") and s.get("type") in TYPES_DEMARCHE))}
    return out


def actualites(source, jour):
    """{id cité : (date, titre de l'actualité)} pour les actualités mises en ligne dans les JOURS_ACTUALITE derniers jours."""
    debut = (jour - datetime.timedelta(days=JOURS_ACTUALITE)).isoformat()
    cites = {}
    for nom, octets in fichiers_xml(source):
        if not nom.startswith("A"): continue
        r = ET.fromstring(octets)
        d = r.get("datePremiereMiseEnLigne") or ""
        if not (debut <= d <= jour.isoformat()) or r.get("perime") == "oui": continue
        titre = (r.findtext(f"{DC}title") or "").strip()
        for el in r.iter():
            i = el.get("ID") or el.get("LienPublication") or ""
            if el.tag in ("Fiche", "ServiceEnLigne", "LienInterne") and re.fullmatch(r"[FR]\d+", i):
                if i not in cites or cites[i][0] < d: cites[i] = (d, titre)
    return cites


def noter(texte, echeance, jour):
    detail = {}
    detail["personnes"] = 0 if contient(texte, CAS_PARTICULIERS) else 1 if contient(texte, PUBLIC_CIBLE) else 2
    detail["urgence"] = 2 if contient(texte, URGENCE_CRISE) else 1 if contient(texte, URGENCE_EXCEPTION) else 0
    if echeance:
        jours = (datetime.date.fromisoformat(echeance) - jour).days
        detail["echeance"] = 2 if jours <= JOURS_ECHEANCE_PROCHE else 1
    else:
        detail["echeance"] = 0
    detail["obligation"] = 2 if contient(texte, OBLIGATION_DATEE) else 1 if contient(texte, OBLIGATION) else 0
    return detail


def date_fr(s):
    mois = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
    d = datetime.date.fromisoformat(s)
    return f"{d.day}{'er' if d.day == 1 else ''} {mois[d.month - 1]} {d.year}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--export", required=True, help="export DILA « Particuliers » du jour (zip ou dossier)")
    ap.add_argument("--precedent", help="export précédent (zip ou dossier) ; sinon donnees/assistant/empreintes_dila.json")
    ap.add_argument("--actualites", help="actualités de service-public.gouv.fr (zip ou dossier)")
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    A = ap.parse_args()
    jour = datetime.date.fromisoformat(A.date)

    actuel = empreintes(A.export)
    chemin_emp = D / "empreintes_dila.json"
    if A.precedent:
        avant = empreintes(A.precedent)
    elif chemin_emp.exists():
        avant = {k: {"d": v[0], "t": v[1]} for k, v in json.loads(chemin_emp.read_text(encoding="utf-8"))["fiches"].items()}
    else:
        avant = None   # premier passage : rien à comparer, l'empreinte du jour sert de point de départ
    cites = actualites(A.actualites, jour) if A.actualites else {}
    ech = json.loads((D / "echeances.json").read_text(encoding="utf-8"))["echeances"]
    pd = json.loads((D / "plus_demandees.json").read_text(encoding="utf-8"))
    affichees = {i for x in pd["nationales"] for i in x.get("ids", [])} | {x.get("fiche") for x in pd["nationales"]}
    ix = json.loads((D / "index.json").read_text(encoding="utf-8")); index_ids = {r["id"] for r in (ix["recs"] if isinstance(ix, dict) else ix)}

    # Candidates, par fiche ou service : (raisons, apparition, échéance)
    cand = {}
    def ajouter(fid, raison, apparition=None, echeance=None):
        c = cand.setdefault(fid, {"raisons": [], "apparition": None, "echeance": None})
        if raison not in c["raisons"]: c["raisons"].append(raison)
        if apparition and (not c["apparition"] or apparition > c["apparition"]): c["apparition"] = apparition
        if echeance and (not c["echeance"] or echeance < c["echeance"]): c["echeance"] = echeance
    nouvelles = modifiees = 0
    if avant is not None:
        for fid, e in actuel.items():
            if fid[0] == "R" and e["ty"] not in TYPES_DEMARCHE: continue
            if fid not in avant:
                nouvelles += 1
                ajouter(fid, f"nouvelle {'fiche' if fid[0] == 'F' else 'démarche en ligne'} du {date_fr(e['d'])}" if e["d"] else "nouvelle fiche", e["d"])
            elif e["d"] and e["d"] != avant[fid].get("d") and e["d"] <= jour.isoformat():
                modifiees += 1
                ajouter(fid, f"fiche modifiée le {date_fr(e['d'])}" + (" (mène à un service en ligne)" if e["r"] else ""), e["d"])
    for x in ech:
        if not x.get("echeance"): continue    # date non publiée : pas encore candidate
        if (x.get("debut") or "") <= jour.isoformat() <= x["echeance"]:
            for i in x["ids"]:
                ajouter(i.removeprefix("SP-"), f"échéance le {date_fr(x['echeance'])}", None, x["echeance"])
    for fid, (d, titre) in cites.items():
        if fid in actuel: ajouter(fid, f"citée dans l'actualité du {date_fr(d)} (« {titre} »)", d)

    props = []
    for fid, c in cand.items():
        e = actuel.get(fid)
        if not e: continue
        sortie_prop = c["echeance"] or ((datetime.date.fromisoformat(c["apparition"]) + datetime.timedelta(days=JOURS_SANS_ECHEANCE)).isoformat()
                                        if c["apparition"] else None)
        if not sortie_prop or sortie_prop < jour.isoformat(): continue   # nouveauté de plus de 30 jours, ou échéance passée
        detail = noter(e["t"] + " " + e["desc"], c["echeance"], jour)
        bonus = BONUS_ACTUALITE if fid in cites else 0
        note = sum(POIDS[k] * v for k, v in detail.items()) + bonus
        ids = ["SP-" + fid] if fid[0] == "R" else ["SP-" + r for r in e["r"][:3]] or ["SP-" + fid]
        if affichees & set(ids + ["SP-" + fid]): continue   # déjà dans la colonne, ou y mène
        props.append({"ids": ids, "fiche": "SP-" + fid if fid[0] == "F" else None, "titre": e["t"],
                      "note": note, "detail": {**detail, "actualite": bonus}, "raison": " ; ".join(c["raisons"]),
                      "date_sortie_proposee": sortie_prop, "dans_l_index": all(i in index_ids for i in ids + (["SP-" + fid] if fid[0] == "F" else [])),
                      "_tri": (c["apparition"] or "")})
    # Tri : note, puis bonus actualité, puis échéance la plus proche, puis apparition la plus récente.
    props.sort(key=lambda p: p["_tri"], reverse=True)   # tri stable : d'abord l'apparition, puis les clés principales
    props.sort(key=lambda p: (-p["note"], -p["detail"]["actualite"], -p["detail"]["echeance"]))
    top = [{k: v for k, v in p.items() if k != "_tri"} for p in props[:NB_PROPOSITIONS]]

    chemin = D / "actualite_nationales.json"
    deja = set()
    if chemin.exists():
        deja = {tuple(p["ids"]) for p in json.loads(chemin.read_text(encoding="utf-8")).get("propositions", [])}
    sortie = {"objet": "Propositions d'actualité pour la colonne « Démarches nationales », régénérées à chaque mise à jour par "
                        "scripts/assistant/actualite.py. Ne changent pas l'affichage : l'éditeur recopie la proposition qu'il valide "
                        "dans plus_demandees.json (editeur.ajout, avec position, jusqua et raison). Note : personnes touchées, urgence, "
                        "échéance et obligation, de 0 à 2 chacun, plus 1 si une actualité de service-public.gouv.fr des 15 derniers "
                        "jours cite la fiche. Poids provisoires, en tête du script.",
              "date": jour.isoformat(),
              "signaux": {"export_precedent": "fourni" if A.precedent else ("empreintes_dila.json" if avant is not None else "aucun (premier passage)"),
                          "nouvelles": nouvelles, "modifiees": modifiees, "actualites_citees": len(cites),
                          "echeances_actives": sum(1 for x in ech if x.get("echeance") and (x.get("debut") or "") <= jour.isoformat() <= x["echeance"]),
                          "echeances_sans_date": [x["id"] for x in ech if not x.get("echeance")]},
              "propositions": top}
    chemin.write_text(json.dumps(sortie, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    chemin_emp.write_text(json.dumps({"objet": "Empreinte de l'export DILA « Particuliers » : {id : [date de modification, titre]}, "
                                               "point de comparaison de l'export suivant. Produit par actualite.py.",
                                      "date": jour.isoformat(), "fiches": {k: [v["d"], v["t"]] for k, v in sorted(actuel.items())}},
                                     ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"actualite_nationales.json : {len(cand)} candidates ({nouvelles} nouvelles, {modifiees} modifiées, {len(cites)} citées "
          f"dans l'actualité, {sortie['signaux']['echeances_actives']} échéance(s) active(s)) ; {len(top)} propositions")
    for p in top:
        if p["note"] >= SEUIL_SIGNALEMENT and tuple(p["ids"]) not in deja:
            print(f"  À voir : nouvelle candidate notée {p['note']} : {p['titre']} ({', '.join(p['ids'])}) — {p['raison']}")
    if sortie["signaux"]["echeances_sans_date"]:
        print("  Échéances sans date (echeances.json) : " + ", ".join(sortie["signaux"]["echeances_sans_date"]))


if __name__ == "__main__":
    main()
