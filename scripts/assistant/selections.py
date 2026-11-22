#!/usr/bin/env python3
"""Sélections de l'accueil du répertoire « Où faire sa démarche ? » : « Les plus demandées » et « À la une ».

    python3 scripts/assistant/selections.py [--observatoire <observatoire.ods>]

Écrit donnees/assistant/plus_demandees.json et donnees/assistant/a_la_une.json. Les champs de l'éditeur déjà présents dans
ces fichiers (`epingle`, `exclu`, `etiquette`) sont gardés d'une mise à jour à l'autre : ils l'emportent sur le calcul.

- **Les plus demandées, « Démarches nationales »** : les démarches les plus volumineuses de l'Observatoire de la qualité des
  démarches en ligne (DINUM, data.gouv.fr, ODS), hors démarches de saison (donnees/assistant/saisons.json) et hors démarches
  réservées aux entreprises, rapprochées d'une fiche service-public par le moteur (à valider).
- **Les plus demandées, « Sur Démarche Numérique »** : les démarches du descriptif qui ont le plus de dossiers, variantes
  départementales regroupées (même titre une fois retirés les noms et codes de département, de région, de préfecture, les
  années), hors démarches réservées aux entreprises.
- **À la une** : démarches publiées depuis moins de 30 jours à la date de l'export, et démarches de saison ; classées par
  urgence (crise, fonds d'urgence, calamité, sécheresse, inondation, intempéries, dégradations, émeutes, troubles urbains,
  dommages subis), puis par dossiers déposés, puis par échéance proche ; variantes départementales regroupées en une ligne.
"""
import argparse, collections, datetime, json, re, subprocess, sys, unicodedata, zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
D = RACINE / "donnees" / "assistant"
sys.path.insert(0, str(Path(__file__).parent))
from departements import DEPARTEMENTS, REGIONS, _dans  # noqa: E402


def n_(s):
    s = unicodedata.normalize("NFD", (s or "").lower()).encode("ascii", "ignore").decode()
    return " ".join(re.findall(r"[a-z0-9]+", s))


_NOMS = sorted({n_(v) for v in DEPARTEMENTS.values()} | {n_(r) for r in REGIONS} | {"la reunion", "reunion"}, key=len, reverse=True)
_VIDES = set("de du des la le les l d en et a au aux pour par sur dans un une votre vos demande formulaire prefecture prefectures "
             "sous ddt ddtm ddets ddpp dsden ddcs drieets dreets departement departemental departementale region regional "
             "regionale direction departementales territoires de l etat service services arrondissement".split())


# Programmes dont les variantes départementales portent des titres trop différents pour être regroupées par le titre :
# (clé, libellé affiché, listes de mots dont une doit être entièrement présente). À compléter par l'éditeur.
PROGRAMMES = [
    ("plan casi", "Fonds d'urgence sécheresse pour les agriculteurs (Plan CASI)",
     [["casi"], ["climat", "adaptation", "secheresse", "incendie"], ["fonds", "rearmement"]]),
    ("verification prealable embauche", "Vérifier le titre de séjour d'un futur salarié",
     [["verification", "embauche"], ["authentification", "titre", "sejour", "embauche"]]),
    ("pass culture", "Demander le crédit du pass Culture", [["pass", "culture"]]),
    ("medaille honneur travail", "Demander la médaille d'honneur du travail", [["medaille", "honneur", "travail"]], ["agricole"]),
]
# Question de lieu d'une ligne dont les démarches sont locales (champ « question_lieu », corrigeable à la main : une
# valeur déjà présente dans le fichier est gardée). Par défaut : « Dans quel département habitez-vous ? ».
QUESTIONS_LIEU = {
    "medaille honneur travail": "Dans quel département travaillez-vous ?",
    "verification prealable embauche": "Dans quel département se trouve l'établissement qui embauche ?",
    "secheresse 2026": "Dans quel département se trouve votre exploitation ?",
}


# Crises : les démarches d'une même crise forment une seule ligne de « À la une », qui lance une recherche sur le thème.
# (clé, libellé, requête, listes de mots dont une doit être entièrement présente dans le titre). À compléter par l'éditeur.
CRISES = [
    ("secheresse 2026", "Sécheresse 2026 : aides et dérogations pour les agriculteurs", "sécheresse aide agriculteur dérogation",
     # le fonds de réarmement agricole relève du Plan CASI (Climat, Adaptation, Sécheresse, Incendie)
     [["secheresse"], ["casi"], ["force", "majeure"], ["irrigation"], ["fonds", "rearmement"]]),
]


def crise(titre):
    mots = set(n_(titre).split())
    return next(((k, lib, req) for k, lib, req, regles in CRISES if any(all(m in mots for m in r) for r in regles)), None)


def departement_affiche(r):
    """Département à afficher : celui que le titre nomme quand il contredit celui de l'organisme (règle de la PR 73)."""
    d_tit = _dans(r["t"], titre=True)[0]
    return d_tit if d_tit and d_tit != r.get("dep") else r.get("dep") or ""


def programme(titre):
    mots = set(n_(titre).split())
    # (clé, libellé, règles[, mots qui excluent : la médaille d'honneur agricole est une autre démarche])
    return next(((p[0], p[1]) for p in PROGRAMMES if any(all(m in mots for m in r) for r in p[2]) and not (len(p) > 3 and mots & set(p[3]))), None)


def cle_variante(titre):
    """Titre réduit à ce qui est commun aux variantes départementales d'une même démarche (ou clé de son programme)."""
    pg = programme(titre)
    if pg: return pg[0]
    t = " " + n_(titre) + " "
    for nom in _NOMS:
        t = t.replace(" " + nom + " ", " ")
    mots = [w for w in t.split() if w not in _VIDES and not re.fullmatch(r"\d+|2a|2b|\d{2,3}[a-z]?|20\d\d", w)]
    return " ".join(mots)


def arrondi(n):
    """« plus de 800 000 » : arrondi par défaut au premier chiffre significatif."""
    if n < 10: return str(n)
    p = 10 ** (len(str(n)) - 1)
    return f"{(n // p) * p:,}".replace(",", " ")


def lire_editeur(chemin):
    try:
        e = json.loads(chemin.read_text(encoding="utf-8")).get("editeur") or {}
    except Exception:
        e = {}
    return {"epingle": e.get("epingle", []), "exclu": e.get("exclu", []), "etiquette": e.get("etiquette", {})}


def saisons_du_mois(saisons, mois):
    return [s for s in saisons if mois in s["mois"]]


def de_saison(titre, saisons):
    t = " " + n_(titre) + " "
    return next((s for s in saisons if any(" " + m + " " in t for m in s["mots"])), None)


# ---------- Observatoire (ODS)
def lire_observatoire(chemin):
    T = "{urn:oasis:names:tc:opendocument:xmlns:table:1.0}"; P = "{urn:oasis:names:tc:opendocument:xmlns:text:1.0}p"
    root = ET.fromstring(zipfile.ZipFile(chemin).read("content.xml"))
    tab = next(root.iter(T + "table")); lignes = []
    for row in tab.iter(T + "table-row"):
        cells = []
        for c in row.iter(T + "table-cell"):
            rep = int(c.get(T + "number-columns-repeated", "1"))
            cells += [" ".join("".join(p.itertext()) for p in c.iter(P))] * min(rep, 30)
        lignes.append(cells)
    entete = lignes[0]; out = []
    for l in lignes[1:]:
        if not any(x.strip() for x in l): continue
        d = dict(zip(entete, l))
        vol = re.sub(r"\D", "", d.get("Volumétrie Totale", "") or "")
        if vol: d["volume"] = int(vol); out.append(d)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--observatoire", default=None, help="fichier ODS de l'Observatoire de la qualité des démarches en ligne")
    A = ap.parse_args()
    meta = json.loads((D / "index_meta.json").read_text(encoding="utf-8"))
    date = datetime.date.fromisoformat(meta["date_export"])
    saisons = json.loads((D / "saisons.json").read_text(encoding="utf-8"))["saisons"]
    recs = json.loads((D / "index.json").read_text(encoding="utf-8"))
    dn = [r for r in recs if r["k"] == "dn"]
    sp = {r["id"]: r for r in recs if r["k"] == "sp"}

    # ---------- Les plus demandées : Démarche Numérique
    # Groupes de toutes les démarches (la première version de l'éditeur y puise) ; les candidates écartent celles réservées aux entreprises.
    groupes = collections.defaultdict(list)
    for r in dn: groupes[cle_variante(r["t"])].append(r)
    cand_dn = []
    for k, l in groupes.items():
        pro = all(r.get("cat") == "entreprise" for r in l)
        if not k: continue
        l.sort(key=lambda r: -r["n"]); tete = l[0]
        deps = {r["dep"] for r in l if r.get("dep")}
        pg = programme(tete["t"])
        cand_dn.append({"cle": k, "titre": pg[1] if pg and len(l) > 1 else tete["t"], "organisme": tete["o"] if len(deps) <= 1 else f"{len(l)} démarches départementales",
                        "dossiers": sum(r["n"] for r in l), "dossiers_arrondis": arrondi(sum(r["n"] for r in l)), "variantes": len(l),
                        "ids": [r["id"] for r in l[:50]], "requete": tete["t"] if len(l) == 1 else (pg[1] if pg else k), "pro": pro})
    cand_dn.sort(key=lambda c: -c["dossiers"])
    pd_chemin = D / "plus_demandees.json"; ed = lire_editeur(pd_chemin)

    # ---------- Les plus demandées : nationales (Observatoire)
    cand_nat = []
    if A.observatoire:
        node = subprocess.run(["node", "-e", """
const M=require(process.argv[1]); const ix=M.build(require(process.argv[2])); let s='';
process.stdin.on('data',d=>s+=d).on('end',()=>{ const out={}; for (const q of JSON.parse(s)) { const r=M.search(ix,q,{source:'sp',k:1})[0]; out[q]=r?{id:r.r.id,t:r.r.t}:null; } console.log(JSON.stringify(out)); });""",
                               str(Path(__file__).with_name("moteur.js")), str(D / "index.json")], capture_output=True, text=True,
                              input=json.dumps([o["Nom Démarche"] for o in lire_observatoire(A.observatoire)]))
        fiche = json.loads(node.stdout or "{}")
        for o in sorted(lire_observatoire(A.observatoire), key=lambda o: -o["volume"]):
            if o.get("Categories Usagers", "").strip() == "Entreprise": continue
            if de_saison(o["Nom Démarche"], saisons): continue
            f = fiche.get(o["Nom Démarche"])
            cand_nat.append({"nom": o["Nom Démarche"], "ministere": o.get("Ministère politique", ""), "administration": o.get("Réf Administration", ""),
                             "volume": o["volume"], "volume_arrondi": arrondi(o["volume"]), "usagers": o.get("Categories Usagers", ""),
                             "fiche_proposee": f["id"] if f else None, "fiche_titre": f["t"] if f else None})
    # Première version, donnée par l'éditeur (consigne du 20 novembre 2026), tant qu'il n'a rien épinglé d'autre.
    # « ids » : les démarches de la ligne (un clic affiche leur réponse, sans recherche sur un texte) ; « fiche » : la fiche
    # service-public à proposer en « Comprendre ». Choisis à la main dans l'index, à valider par l'éditeur.
    nat_defaut = [{"titre": "Obtenir une attestation de droits", "organisme": "Assurance maladie", "requete": "attestation de droits assurance maladie",
                   "ids": ["SP-R49811"], "fiche": "SP-F10662"},
                  {"titre": "Demander la prime d'activité", "organisme": "Caf, MSA", "requete": "prime d'activité",
                   "precision": "Demande et déclaration trimestrielle dans votre espace Caf ou MSA", "ids": ["SP-R42724"], "fiche": "SP-F2882"},
                  {"titre": "Payer une amende", "organisme": "Agence nationale de traitement automatisé des infractions (ANTAI)", "requete": "payer une amende",
                   "ids": ["SP-R11026"], "fiche": "SP-F18509"}]
    avant = {}
    try:
        _p = json.loads(pd_chemin.read_text(encoding="utf-8"))
        avant = {x.get("cle") or x.get("titre"): x for x in _p.get("nationales", []) + _p.get("demarche_numerique", [])}
    except Exception:
        pass
    for x in nat_defaut:   # une ligne nationale corrigée à la main garde ses ids, sa fiche et sa question
        for k in ("ids", "fiche", "question_lieu", "precision"):
            if k in avant.get(x["titre"], {}): x[k] = avant[x["titre"]][k]
    dn_defaut = ["medaille honneur travail", "verification prealable embauche", "pass culture"]
    choisis_dn = []
    for mot in (ed["epingle"] or dn_defaut):
        c = next((c for c in cand_dn if all(w in c["cle"] for w in n_(mot).split()) and c["cle"] not in ed["exclu"]), None)
        if c and c not in choisis_dn: choisis_dn.append(c)
    pd = {"objet": "Accueil, « Les plus demandées ». Corrigeable à la main : editeur.epingle (mots du titre, dans l'ordre voulu), editeur.exclu (clés à écarter) ; pour chaque ligne, ids (ses démarches), fiche (fiche service-public) et question_lieu (question posée quand ses démarches sont locales).",
          "date": meta["date_export"], "nationales": nat_defaut,
          "demarche_numerique": [{**{k: v for k, v in c.items() if k != "pro"}, "question_lieu": avant.get(c["cle"], {}).get("question_lieu") or QUESTIONS_LIEU.get(c["cle"], "Dans quel département habitez-vous ?")} for c in choisis_dn[:3]],
          "source": "Observatoire de la qualité des démarches en ligne (DINUM) ; volumes du descriptif de Démarche Numérique",
          "candidates_nationales": cand_nat[:10], "candidates_demarche_numerique": [{k: c[k] for k in ("cle", "titre", "organisme", "dossiers", "variantes")} for c in cand_dn if not c["pro"]][:10],
          "editeur": ed}
    pd_chemin.write_text(json.dumps(pd, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    # ---------- À la une (champs de l'éditeur de a_la_une.json, pas ceux de plus_demandees.json)
    ed = lire_editeur(D / "a_la_une.json")
    seuil = (date - datetime.timedelta(days=30)).isoformat()
    URGENT = re.compile(r"\burgence|\burgent")
    CRISE = re.compile(r"\bcrise|calamite|secheresse|inondation|intemperie|degradation|emeute|\bcasi\b|force majeure|grele|tempete|troubles urbains|dommages subis")
    candidats = []
    for r in dn:
        s = de_saison(r["t"], saisons_du_mois(saisons, date.month))
        recent = (r.get("dp") or "") >= seuil
        if not (recent or s): continue
        t = n_(r["t"])
        etiq = "Urgent" if URGENT.search(t) else "Crise" if CRISE.search(t) else "De saison" if s else "Nouveau"
        candidats.append((r, etiq))
    lignes = collections.defaultdict(list)
    for r, e in candidats:
        c = crise(r["t"])
        lignes[c[0] if c else cle_variante(r["t"])].append((r, e))
    rang = {"Urgent": 0, "Crise": 1, "De saison": 2, "Nouveau": 3}
    une = []
    for k, l in lignes.items():
        l.sort(key=lambda x: -x[0]["n"]); r, e = l[0]
        deps = sorted({departement_affiche(x[0]) for x in l} - {""})
        etiq = min((x[1] for x in l), key=lambda x: rang[x])
        d1 = departement_affiche(r)
        portee = ("nationale" if r.get("po") == "nat" and not d1 else f"{DEPARTEMENTS.get(d1, d1)} ({d1})" if d1 else "locale") if len(deps) <= 1 else f"{len(deps)} départements"
        echeance = min((x[0].get("fe") or "9999") for x in l)
        pg = programme(r["t"]); cr = next((c for c in CRISES if c[0] == k), None)
        ouvertes = sum(1 for x in l if not x[0].get("fe") or x[0]["fe"] >= meta["date_export"])
        titre = cr[1] if cr else pg[1] if pg and len(l) > 1 else r["t"]
        organisme = r["o"] if len(l) == 1 else f"{ouvertes} démarche{'s' if ouvertes > 1 else ''} ouverte{'s' if ouvertes > 1 else ''}" if cr else f"{len(l)} démarches départementales"
        une.append({"cle": k, "titre": titre, "organisme": organisme, "portee": portee, "etiquette": ed["etiquette"].get(k, etiq),
                    "dossiers": sum(x[0]["n"] for x in l), "publiee": max((x[0].get("dp") or "") for x in l), "echeance": None if echeance == "9999" else echeance,
                    "variantes": len(l), "ids": [x[0]["id"] for x in l[:50]], "requete": cr[2] if cr else r["t"] if len(l) == 1 else k})
    une = [u for u in une if u["cle"] not in ed["exclu"]]
    une.sort(key=lambda u: (rang[u["etiquette"]], -u["dossiers"], u["echeance"] or "9999"))
    epingles = [u for m in ed["epingle"] for u in une if all(w in u["cle"] for w in n_(m).split())]
    ordre = epingles + [u for u in une if u not in epingles]
    # Au plus deux lignes « Crise » : la place reste aux autres sujets (les suivantes restent listées pour l'éditeur).
    n_crise, garde, reste = 0, [], []
    for u in ordre:
        if u["etiquette"] == "Crise" and u not in epingles:
            n_crise += 1
            if n_crise > 2: reste.append(u); continue
        garde.append(u)
    ordre = garde + reste
    try:
        q_avant = {u["cle"]: u.get("question_lieu") for u in json.loads((D / "a_la_une.json").read_text(encoding="utf-8")).get("retenues", []) + json.loads((D / "a_la_une.json").read_text(encoding="utf-8")).get("suivantes", [])}
    except Exception:
        q_avant = {}
    for u in ordre:
        u["question_lieu"] = q_avant.get(u["cle"]) or QUESTIONS_LIEU.get(u["cle"], "Dans quel département habitez-vous ?")
    au = {"objet": "Accueil, « À la une » : proposé par la mise à jour, validé par l'éditeur. editeur.epingle (mots du titre), editeur.exclu (clés), editeur.etiquette ({clé: étiquette}).",
          "date": meta["date_export"], "retenues": ordre[:6], "suivantes": ordre[6:12],
          "source": "Démarches publiées depuis moins de 30 jours, et démarches de saison (saisons.json) ; descriptif de Démarche Numérique",
          "editeur": ed}
    (D / "a_la_une.json").write_text(json.dumps(au, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"plus_demandees.json : {len(choisis_dn)} sur Démarche Numérique, {len(cand_nat)} candidates nationales ; a_la_une.json : {len(une)} lignes candidates")


if __name__ == "__main__":
    main()
