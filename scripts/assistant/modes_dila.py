#!/usr/bin/env python3
"""Comment se fait une démarche service-public : les voies (« en ligne », « formulaire, courrier », « guichet »…) lues dans
le XML des fiches DILA. Utilisé par build_index.py (clés « md » et « md_sur » de l'index).

Une voie est une liste de modes qui se suivent (formulaire puis courrier = un formulaire à envoyer par courrier) ; les voies
sont des alternatives (« ou »). Sources, dans cet ordre :
  1. les cas structurés du XML (<BlocCas><Cas><Titre>) dont le titre est une façon de faire : « En ligne », « Par courrier »,
     « Sur place »… (voie sûre). Un formulaire (<ServiceEnLigne type="Formulaire">) cité dans un cas « Par courrier » ou
     « Sur place » s'ajoute en tête de la voie ;
  2. sans cas structuré, les liens de la fiche : un service en ligne de type téléservice donne « en ligne », un cerfa ou un
     formulaire donne « formulaire » (voie sûre) ;
  3. dans le texte libre, des motifs simples et explicites pour le courriel et le rendez-vous (voie non sûre, affichée
     avec « ou » après une voie sûre, jamais seule ni comme certaine).
Au plus 3 voies : les voies sûres d'abord, puis dans l'ordre en ligne, formulaire, guichet, rendez-vous, courrier, courriel.

    python3 scripts/assistant/modes_dila.py --carto ~/Documents/cartographie --rapport   # répartition, intitulés, 10 fiches au hasard
"""
import argparse, collections, glob, json, os, random, re, sys
import xml.etree.ElementTree as ET

MODES = ["en_ligne", "formulaire", "guichet", "rendez_vous", "courrier", "courriel"]   # ordre d'affichage des voies
TYPES_EN_LIGNE = {"Téléservice", "selNG", "Téléservice personnalisé sur SP"}
TYPES_FORMULAIRE = {"Formulaire", "formulaireNG"}
MAX_VOIES = 3

# Titres de cas qui disent une façon de faire. Lus en début de titre, sans accents ni majuscules ; « A ou B » donne deux voies.
_CANAUX = [
    ("en_ligne", r"(sur |par )?internet|en ligne|(demande|envoi( du dossier)?|pre-demande|paiement|payer directement) (en ligne|sur internet)"
                 r"|teleservice|service en ligne|via (le|un) formulaire en ligne|vous faites (la demarche|une pre-demande) en ligne"),
    ("formulaire", r"formulaires?( papier| a imprimer)?$|avec (le|un) formulaire|par formulaire|vous remplissez un formulaire|sur papier libre"),
    ("courrier", r"par courrier( postal)?|courrier (papier|postal)|(demande|envoi( du dossier)?) par courrier|envoi du dossier papier|lrar|par lettre"),
    ("courriel", r"(par )?(mail|courriel|e-mail)|courrier electronique"),
    ("guichet", r"sur place|au guichet|(depot )?en mairie|vous venez sur place|en main propre"),
    ("rendez_vous", r"sur rendez-vous|(prendre|prise de) rendez-vous"),
]
_CANAUX = [(m, re.compile(r"^(" + p + r")\b")) for m, p in _CANAUX]
_SUITE_FORM = re.compile(r"formulaire")   # « Avec le formulaire à déposer au guichet », « Par courrier (formulaire) »
_CERFA = re.compile(r"\bcerfa n")          # « Formulaire cerfa n°12669 » écrit dans un cas « Par courrier » ou « Sur place »
# Texte libre : seulement des motifs simples et explicites.
# Courriel : un verbe d'envoi ou de demande suivi de « par courriel » (« vous êtes informé par courriel » ne compte pas).
_TEXTE = [("courriel", re.compile(r"\b(envoy|adress|transmet|transmis|demand|depos|fai|contact|ecri|saisi)\w*\b[^.;:]{0,40}\bpar (courriel|e-mail|mail|courrier electronique)\b")),
          ("rendez_vous", re.compile(r"\bsur rendez-vous\b|\bprendre (un )?rendez-vous\b"))]


def _n(s):
    s = " ".join(s.split()).lower()
    for a, b in (("é", "e"), ("è", "e"), ("ê", "e"), ("à", "a"), ("â", "a"), ("ô", "o"), ("î", "i"), ("ç", "c"), ("’", "'")):
        s = s.replace(a, b)
    return s


def _txt(e):
    return " ".join("".join(e.itertext()).split())


def modes_titre(titre):
    """Liste de voies données par un titre de cas (vide si ce n'est pas une façon de faire)."""
    voies = []
    for i, part in enumerate(re.split(r"\s+ou\s+(?:par\s+)?", _n(titre))):
        part = part.strip(" ,")
        for mode, rx in _CANAUX:
            # « Sur place ou par courrier » : après « ou », « courrier » vaut « par courrier », « place » vaut « sur place »
            if rx.match(part) or (i and mode == "courrier" and rx.match("par " + part)) or (i and mode == "guichet" and rx.match("sur " + part)):
                v = [mode]
                if mode in ("courrier", "guichet", "courriel") and _SUITE_FORM.search(part): v = ["formulaire", mode]
                if mode == "formulaire":
                    for m2, rx2 in _CANAUX:
                        if m2 in ("courrier", "guichet") and re.search(rx2.pattern.lstrip("^"), part): v = ["formulaire", m2]
                voies.append(v)
                break
    return voies


def _types_cites(e):
    return {s.get("type") for s in e.iter("ServiceEnLigne")}


def _voies_bloc(bloc, titres):
    """Voies d'un BlocCas dont au moins 2 cas sont des façons de faire ; [] sinon."""
    cas = [(c, modes_titre(_txt(c.find("Titre"))) if c.find("Titre") is not None else []) for c in bloc.findall("Cas")]
    if sum(1 for _, v in cas if v) < 2: return []
    out = []
    for c, vs in cas:
        if not vs: continue
        titres[_txt(c.find("Titre"))] += 1
        internes = [v for b in _blocs_canaux(c) for v in _voies_bloc(b, titres)]
        for v in vs:
            if internes:
                out += [list(dict.fromkeys(v + w)) for w in internes]
            elif v[0] in ("courrier", "guichet") and (_types_cites(c) & TYPES_FORMULAIRE or _CERFA.search(_n(_txt(c)))):
                out.append(["formulaire"] + v)
            else:
                out.append(v)
    return out


def _blocs_canaux(e):
    """BlocCas sous e, sans descendre sous un BlocCas déjà rencontré (les blocs internes sont lus par _voies_bloc)."""
    res = []
    for enfant in e:
        if enfant.tag == "BlocCas": res.append(enfant)
        elif enfant.tag != "Titre": res += _blocs_canaux(enfant)
    return res


def _tous_blocs(e):
    """Tous les BlocCas qui sont des façons de faire, les plus hauts : ceux qui ne sont pas sous le cas d'un tel bloc."""
    res = []
    for b in _blocs_canaux(e):
        if sum(1 for c in b.findall("Cas") if c.find("Titre") is not None and modes_titre(_txt(c.find("Titre")))) >= 2:
            res.append(b)
        else:
            for c in b.findall("Cas"): res += _tous_blocs(c)
    return res


def voies_fiche(chemin_ou_texte, titres=None):
    """(voies, sure, detail) pour une fiche. voies : liste de listes de modes ; sure : toutes les voies viennent d'une balise."""
    titres = titres if titres is not None else collections.Counter()
    root = ET.fromstring(chemin_ou_texte) if chemin_ou_texte.lstrip().startswith("<") else ET.parse(chemin_ou_texte).getroot()
    sures = [v for b in _tous_blocs(root) for v in _voies_bloc(b, titres)]
    origine = "cas" if sures else ""
    if not sures:
        types = _types_cites(root)
        if types & TYPES_EN_LIGNE: sures.append(["en_ligne"])
        if types & TYPES_FORMULAIRE: sures.append(["formulaire"])
        origine = "liens" if sures else ""
    texte = _n(" ".join(_txt(p) for p in root.iter("Paragraphe")))
    deja = {m for v in sures for m in v}
    tirees = [[m] for m, rx in _TEXTE if m not in deja and rx.search(texte)]
    rang = lambda v: [MODES.index(m) for m in v]
    sures = [list(v) for v in dict.fromkeys(tuple(v) for v in sures)]
    # « courrier » seul est contenu dans « formulaire, courrier » lu dans un autre cas : on garde la voie la plus précise
    sures = sorted([v for v in sures if not any(w != v and set(v) < set(w) for w in sures)], key=rang)
    # Une voie tirée du texte n'est jamais affichée seule, comme si elle était certaine : sans voie sûre, aucune voie.
    if not sures: return [], True, {"origine": "", "sures": 0, "tirees": 0, "ecartees": len(tirees)}
    voies = (sures + sorted(tirees, key=rang))[:MAX_VOIES]
    n_sures = min(len(sures), MAX_VOIES)
    return voies, n_sures == len(voies), {"origine": origine, "sures": n_sures, "tirees": len(voies) - n_sures}


def fichiers_xml(carto):
    xml = {}
    for d in ("extracted_part", "extracted_pro", "extracted_asso"):
        for f in sorted(glob.glob(os.path.join(carto, "dila", "raw", d, "F*.xml"))): xml.setdefault(os.path.basename(f)[:-4], []).append(f)
    return xml


def libelle(voies):
    noms = {"en_ligne": "en ligne", "formulaire": "formulaire", "guichet": "guichet", "rendez_vous": "rendez-vous", "courrier": "courrier", "courriel": "courriel"}
    return " ou ".join(", ".join(noms[m] for m in v) for v in voies)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--carto", default=os.path.expanduser("~/Documents/cartographie"))
    ap.add_argument("--index", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "donnees", "assistant", "index.json"))
    ap.add_argument("--rapport", action="store_true")
    A = ap.parse_args()
    xml = fichiers_xml(A.carto); titres = collections.Counter()
    ids = [r["id"][3:] for r in json.load(open(A.index)) if r["id"].startswith("SP-F")]
    rep, n_sures, n_tirees, origines, res = collections.Counter(), 0, 0, collections.Counter(), {}
    for fid in ids:
        if fid not in xml: continue
        v, sure, d = voies_fiche(xml[fid][0], titres)
        res[fid] = v; rep[libelle(v) or "(aucune voie)"] += 1; n_sures += d["sures"]; n_tirees += d["tirees"]; origines[d["origine"] or ("texte seul, écartée" if d.get("ecartees") else "aucune")] += 1
    print(f"{len(res)} fiches F de l'index lues")
    print("Répartition des voies :"); [print(f"  {n:5} {k}") for k, n in rep.most_common(25)]
    print(f"Voies sûres : {n_sures} ; tirées du texte : {n_tirees} ; origine : {dict(origines)}")
    if A.rapport:
        print("Intitulés de cas retenus comme façon de faire :"); [print(f"  {n:5} {k}") for k, n in titres.most_common()]
        for fid in random.Random(20261123).sample(sorted(f for f in res if res[f]), 10): print(f"  {fid} : {libelle(res[fid])}")


if __name__ == "__main__":
    main()
