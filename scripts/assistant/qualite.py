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
    python3 scripts/assistant/qualite.py … --proposer-spp > rapport.md   # étude des rattachements, rien n'est appliqué
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
    doc = json.loads((D / "assistant" / "observatoire_rattachement.json").read_text(encoding="utf-8"))
    deja = {str(t["observatoire"]) for t in table + doc.get("a_verifier", [])} | {"1759", "1754"}   # écartés par l'éditeur le 23/11/2026
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


# ---------- Propositions de rattachement Services Publics + (option --proposer-spp) : étude, rien n'est appliqué.
# Démarches nommées (« Démarches modérées », nomenclature de l'Observatoire) → démarches service-public de l'index, et
# structures des grands opérateurs → domaine de leurs services en ligne. Seulement des comptes et des critères cochés.
SEUIL_STRUCTURE = 100          # retours, pour étudier une structure (partie 2)
SEUIL_NOM_SUR, SEUIL_NOM = 0.92, 0.75   # similarité des noms : quasi identique, proche
VAGUE_DEMARCHES, VAGUE_FICHES = 10, 20  # au-delà : signal trop vague pour une structure


def _sans_accents(s):
    import unicodedata
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()


_VIDES = set("a au aux de des du d l la le les en et pour par sur un une votre vos son sa ses ou a".split())


def _nom(s):
    return " ".join(w for w in re.sub(r"[^a-z0-9]+", " ", _sans_accents(s).lower()).split() if w not in _VIDES)


def _url(u):
    return re.sub(r"^https?://(www\.)?", "", (u or "").strip().split("#")[0].split("?")[0].rstrip("/").lower())


def _domaine(u):
    d = _url(u).split("/")[0]
    return d[4:] if d.startswith("www.") else d


def lire_toutes_obs(chemin):
    """Toutes les lignes nommées de l'Observatoire (lire_observatoire ne garde que celles qui ont une volumétrie)."""
    import zipfile, xml.etree.ElementTree as ET
    T = "{urn:oasis:names:tc:opendocument:xmlns:table:1.0}"; P = "{urn:oasis:names:tc:opendocument:xmlns:text:1.0}p"
    tab = next(ET.fromstring(zipfile.ZipFile(chemin).read("content.xml")).iter(T + "table")); lignes = []
    for row in tab.iter(T + "table-row"):
        cells = []
        for c in row.iter(T + "table-cell"):
            cells += [" ".join("".join(x.itertext()) for x in c.iter(P))] * min(int(c.get(T + "number-columns-repeated", "1")), 30)
        lignes.append(cells)
    return [d for d in (dict(zip(lignes[0], l)) for l in lignes[1:]) if (d.get("Nom Démarche") or "").strip()]


def cooccurrences(chemin, date_fichier):
    """Structure → Counter(démarche nommée) sur la période : quelles démarches les retours d'une structure nomment."""
    debut = (date_fichier - datetime.timedelta(days=365 * ANNEES)).isoformat()
    csv.field_size_limit(10 ** 9); co = collections.defaultdict(collections.Counter)
    with open(chemin, encoding="utf-8-sig", newline="") as f:
        r = csv.reader(f, delimiter=";"); h = [x.strip() for x in next(r)]; col = {k: i for i, k in enumerate(h)}
        i_struct = [i for i, k in enumerate(h) if k.startswith("Intitulé structure")]
        for row in r:
            if len(row) < len(h) or row[col["Date de publication"]][:10] < debut: continue
            dm = row[col["Démarches modérées"]].strip()
            for i in i_struct:
                st = row[i].strip()
                if st and st != "Hors-structures": co[cle(st)][cle(dm) if dm else ""] += 1
    return co


def proposer_spp(A):
    import random
    rnd = random.Random(20261125)
    spp, debut = lire_spp(A.spp, datetime.date.fromisoformat(A.date_spp))
    recs = json.loads((D / "assistant" / "index.json").read_text(encoding="utf-8"))
    par_id = {r["id"]: r for r in recs}
    sp = [r for r in recs if r["k"] == "sp"]
    rat = json.loads((D / "assistant" / "observatoire_rattachement.json").read_text(encoding="utf-8"))["rattachements"]
    deja_obs = {str(t["observatoire"]): t["id"] for t in rat}
    obs = lire_toutes_obs(A.observatoire)
    obs_par_nom = collections.defaultdict(list)
    for o in obs: obs_par_nom[cle(o["Nom Démarche"])].append(o)
    # Adresses : une adresse visée par plusieurs démarches de l'index ou plusieurs lignes de l'Observatoire est un portail commun.
    index_par_url, obs_par_url = collections.defaultdict(list), collections.defaultdict(list)
    for r in sp:
        if r.get("l"): index_par_url[_url(r["l"])].append(r)
    for o in obs:
        if (o.get("URL Démarche") or "").strip(): obs_par_url[_url(o["URL Démarche"])].append(o)
    # Comparaison des noms : mots tronqués à 6 lettres ; les mots génériques (présents dans plus de 1 % des titres de l'index :
    # « demande », « déclaration », « ligne »…) sont lus dans les données et ne comptent pas. Score : part des mots spécifiques
    # communs (Jaccard) ; « quasi identique » : noms complets presque égaux (SequenceMatcher).
    racines = lambda t: {w[:6] for w in t.split()}
    freq = collections.Counter(w for r in sp for w in racines(_nom(r["t"])))
    generiques = {w for w, n in freq.items() if n > 0.01 * len(sp)}
    specifiques = lambda t: racines(t) - generiques
    noms_r = [(r, _nom(r["t"])) for r in sp if r["id"].startswith("SP-R")]
    noms_f = [(r, _nom(r["t"])) for r in sp if r["id"].startswith("SP-F")]

    def par_titre(nom, liste):
        import difflib
        n = _nom(nom); a = specifiques(n); sc = []
        if not a: return []
        for r, t in liste:
            b = specifiques(t)
            if not a & b: continue
            # un seul mot spécifique en commun ne suffit jamais à rapprocher deux noms (« urbanisme », « impôts »…)
            jac = len(a & b) / len(a | b) if len(a & b) >= 2 else 0
            quasi = difflib.SequenceMatcher(None, n, t).ratio()
            if jac or quasi >= SEUIL_NOM_SUR: sc.append((round(max(jac, quasi if quasi >= SEUIL_NOM_SUR else 0), 3), round(quasi, 3), r))
        return [(x, q, r) for x, q, r in sorted(sc, key=lambda x: (-x[0], -x[1]))[:5]]

    props = []
    for k, v in sorted(spp["demarche"].items(), key=lambda kv: -kv[1]["n"]):
        p = {"nom_spp": v["nom"], "retours": v["n"], "negatifs": v["neg"], "motifs": v["motifs"], "id": "", "titre": "", "url_fiche": "",
             "classe": "aucune", "methode": "", "raison": ""}
        os_ = obs_par_nom.get(k, [])
        if len(os_) == 1 and str(os_[0]["ID Démarche"]) in deja_obs:
            r = par_id.get(deja_obs[str(os_[0]["ID Démarche"])])
            p.update(id=r["id"] if r else "", titre=r["t"] if r else "", url_fiche=r["u"] if r else "", classe="deja_rattachee", methode="observatoire_rattachement.json",
                     raison="rattachement déjà validé (Observatoire)")
            props.append(p); continue
        # 1. Observatoire : même nom de démarche, puis son adresse
        if os_:
            u = _url(os_[0].get("URL Démarche"))
            cand = index_par_url.get(u, []) if u else []
            if len(os_) > 1:
                p.update(classe="douteuse", methode="observatoire", raison=f"{len(os_)} lignes de l'Observatoire portent ce nom")
            elif u and cand:
                portail = len(cand) > 1 or len(obs_par_url.get(u, [])) > 1 or "/" not in u
                r = cand[0]
                p.update(id=r["id"], titre=r["t"], url_fiche=r["u"], methode="observatoire, adresse",
                         classe="douteuse" if portail else "sure",
                         raison=(f"adresse de portail commun ({u}) : {len(cand)} démarche(s) de l'index, {len(obs_par_url.get(u, []))} ligne(s) de l'Observatoire"
                                 if portail else f"même adresse de service ({u})"))
                if len(cand) > 1: p["autres_candidats"] = [x["id"] for x in cand[1:6]]
            if p["classe"] != "aucune": props.append(p); continue
            p["raison"] = "nom présent dans l'Observatoire, adresse absente de l'index ; " if os_ else ""
        # 2. Titre : services en ligne R… puis fiches F…
        for famille, liste in (("titre, fiches R", noms_r), ("titre, fiches F", noms_f)):
            sc = par_titre(v["nom"], liste)
            proches = [x for x in sc if x[0] >= SEUIL_NOM]
            if not proches: continue
            best, quasi, r = proches[0]
            p.update(id=r["id"], titre=r["t"], url_fiche=r["u"], methode=famille, similarite=best)
            if len(proches) > 1:
                p.update(classe="douteuse", raison=p["raison"] + f"{len(proches)} candidats de nom proche (≥ {SEUIL_NOM})"); p["autres_candidats"] = [x[2]["id"] for x in proches[1:]]
            elif quasi >= SEUIL_NOM_SUR:
                p.update(classe="sure", raison=p["raison"] + f"nom quasi identique ({quasi}), un seul candidat")
            else:
                p.update(classe="probable", raison=p["raison"] + f"mots spécifiques communs ({best}), un seul candidat plausible")
            break
        else:
            p["raison"] += f"aucun titre de l'index assez proche (mots spécifiques communs < {SEUIL_NOM})"
        props.append(p)

    # Prudence : une même démarche de l'index proposée pour plusieurs démarches nommées → toutes douteuses.
    vues = collections.Counter(p["id"] for p in props if p["id"] and p["classe"] in ("sure", "probable"))
    for p in props:
        if p["classe"] in ("sure", "probable") and vues[p["id"]] > 1:
            p["classe"] = "douteuse"; p["raison"] += f" ; {p['id']} est aussi proposée pour {vues[p['id']] - 1} autre(s) démarche(s) nommée(s)"

    c = collections.Counter(p["classe"] for p in props)
    sures_vig = {p["id"] for p in props if p["classe"] == "sure" and p["motifs"] and par_id.get(p["id"], {}).get("k") == "sp" and "spp" not in par_id[p["id"]]}
    out1 = {"objet": "Propositions de rattachement des démarches nommées de Services Publics + (au moins %d retours depuis le %s) aux démarches "
                     "service-public de l'index, par scripts/assistant/qualite.py --proposer-spp. Étude : aucun rattachement actif." % (SEUIL_RETOURS, debut),
            "sources": {"spp": A.date_spp, "observatoire": A.edition},
            "seuils": {"retours": SEUIL_RETOURS, "motif": SEUIL_MOTIF, "motifs_max": MAX_MOTIFS, "nom_quasi_identique": SEUIL_NOM_SUR, "nom_proche": SEUIL_NOM},
            "comptes": dict(c), "fiches_sp_avec_vigilance_si_sures_validees": len(sures_vig), "propositions": props}
    (D / "assistant" / "spp_rattachement_propositions.json").write_text(json.dumps(out1, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    # Partie 2 : structures d'au moins SEUIL_STRUCTURE retours sans organisme de Démarche Numérique.
    orgs_dn = {cle(r.get("o")) for r in recs if r["k"] == "dn"} | {cle(r.get("oa")) for r in recs if r["k"] == "dn" and r.get("oa")}
    co = cooccurrences(A.spp, datetime.date.fromisoformat(A.date_spp))
    obs_url_par_nom = {k: _url(os_[0].get("URL Démarche")) for k, os_ in obs_par_nom.items() if len(os_) == 1 and (os_[0].get("URL Démarche") or "").strip()}
    fiches_par_domaine = collections.Counter(_domaine(r["l"]) for r in sp if r.get("l"))
    structs = []
    for k, v in sorted(spp["structure"].items(), key=lambda kv: -kv[1]["n"]):
        if v["n"] < SEUIL_STRUCTURE or k in orgs_dn: continue
        dm = co.get(k, collections.Counter())
        nommees = {d: n for d, n in dm.items() if d}
        dom = collections.Counter()
        for d, n in nommees.items():
            u = obs_url_par_nom.get(d)
            if u: dom[u.split("/")[0].removeprefix("www.")] += n
        tot = sum(dom.values()); top = dom.most_common(1)
        domaine, part = (top[0][0], round(top[0][1] / tot, 2)) if top else ("", 0)
        nf = fiches_par_domaine.get(domaine, 0) if domaine else 0
        vague = len(nommees) >= VAGUE_DEMARCHES or nf >= VAGUE_FICHES
        structs.append({"structure": v["nom"], "retours": v["n"], "negatifs": v["neg"], "motifs": v["motifs"],
                        "retours_sans_demarche_nommee": dm.get("", 0), "demarches_nommees_distinctes": len(nommees),
                        "domaine_propose": domaine, "part_des_retours_nommes_vers_ce_domaine": part,
                        "autres_domaines": [d for d, _ in dom.most_common(4)[1:]],
                        "fiches_sp_vers_ce_domaine": nf, "trop_vague": vague,
                        "raison": ("domaine lu dans l'Observatoire (adresse des démarches nommées par les retours de la structure)" if domaine
                                   else "aucune démarche nommée par ses retours n'a d'adresse dans l'Observatoire : pas de domaine proposé")
                                  + (f" ; signal trop vague : {len(nommees)} démarches nommées distinctes, {nf} fiches vers ce domaine" if vague else "")})
    out2 = {"objet": "Structures Services Publics + d'au moins %d retours depuis le %s sans organisme de Démarche Numérique, avec le domaine "
                     "proposé de leurs services en ligne. Étude : rien n'est appliqué (qualite.py --proposer-spp)." % (SEUIL_STRUCTURE, debut),
            "seuils": {"retours": SEUIL_STRUCTURE, "vague_demarches_nommees": VAGUE_DEMARCHES, "vague_fiches": VAGUE_FICHES}, "structures": structs}
    (D / "assistant" / "spp_structures_propositions.json").write_text(json.dumps(out2, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    rapport_spp(out1, out2, par_id, rnd)
    rapport_suite(etude_spp_suite(A, recs, obs_par_nom, debut))


def rapport_spp(out1, out2, par_id, rnd):
    props = out1["propositions"]; p = print; c = collections.Counter(x["classe"] for x in props)
    lien = lambda x: f"[{x['id']}]({x['url_fiche']})" if x["id"] else "—"
    mot = lambda m: ", ".join(f"{a} ({b})" for a, b in m) or "aucun"
    p("## Récapitulatif\n\n| | Nombre |\n|---|---|")
    p(f"| Démarches nommées d'au moins {SEUIL_RETOURS} retours | {len(props)} |")
    for k, lib in (("deja_rattachee", "déjà rattachées (Observatoire, validé)"), ("sure", "sûres"), ("probable", "probables"), ("douteuse", "douteuses"), ("aucune", "sans proposition")):
        p(f"| Propositions {lib} | {c.get(k, 0)} |")
    p(f"| Fiches service-public qui recevraient une vigilance si les sûres sont validées | {out1['fiches_sp_avec_vigilance_si_sures_validees']} |\n")
    for k, lib in (("sure", "sûres"), ("probable", "probables"), ("douteuse", "douteuses")):
        xs = [x for x in props if x["classe"] == k]
        p(f"### 15 exemples au hasard : {lib} ({len(xs)})\n\n| Services Publics + | Retours | Démarche proposée | Titre de l'index | Raison |\n|---|---|---|---|---|")
        for x in rnd.sample(xs, min(15, len(xs))):
            p(f"| {x['nom_spp']} | {x['retours']} | {lien(x)} | {x['titre'][:90]} | {x['raison']} |")
        p()
    p("### Les 20 démarches nommées qui ont le plus de retours\n\n| Services Publics + | Retours | Motifs | Classe | Démarche proposée | Titre de l'index |\n|---|---|---|---|---|---|")
    for x in props[:20]:
        p(f"| {x['nom_spp']} | {x['retours']} | {mot(x['motifs'])} | {x['classe']} | {lien(x)} | {x['titre'][:80]} |")
    p("\n## Partie 2 : structures\n\n| Structure | Retours | Motifs | Démarches nommées | Domaine proposé (part) | Fiches SP vers ce domaine | Trop vague |\n|---|---|---|---|---|---|---|")
    for s in out2["structures"]:
        p(f"| {s['structure']} | {s['retours']} | {mot(s['motifs'])} | {s['demarches_nommees_distinctes']} | {s['domaine_propose'] or '—'}"
          f"{' (%d %%)' % round(100 * s['part_des_retours_nommes_vers_ce_domaine']) if s['domaine_propose'] else ''} | {s['fiches_sp_vers_ce_domaine']} | {'oui' if s['trop_vague'] else 'non'} |")


# ---------- Suite de l'étude (même option) : ANTS par domaine, France Travail, étrangers, préfectures. Rien n'est appliqué.
# Ressources : les colonnes de catégories de l'export (« Intitulé Typologie », « Tags Métiers ») servent à reconnaître les retours
# sur les étrangers ; ce sont des listes de valeurs, pas du texte d'usager.
ANTS = "France Titres-ANTS"
ANTS_DOMAINES = {"immatriculation.ants.gouv.fr": "immatriculation", "permisdeconduire.ants.gouv.fr": "permis de conduire",
                 "passeport.ants.gouv.fr": "passeport et carte d'identité"}
# Repli, seulement pour un nom absent de l'Observatoire (« Demande de CNI/Passeport (ANTS) »…)
ANTS_NOMS = [(r"immatriculation|carte grise", "immatriculation"), (r"permis de conduire", "permis de conduire"),
             (r"\bCNI\b|passeport|carte nationale d.identit", "passeport et carte d'identité")]
FT_DR = r"^DR .*-France Travail$"          # directions régionales de France Travail
FT_DOMAINE = "candidat.francetravail.fr"
ETR_TYPOLOGIES = {"ANEF", "OFII", "Office français de protection des réfugiés et apatrides (OFPRA)", "Parrainage.refugies.info"}
ETR_TAGS = {"Titre de séjour", "Naturalisation", "Asile", "Aide aux réfugiés"}
ETR_MOTS = r"s[ée]jour|\bANEF\b|naturali|asile|\bvisas?\b|[ée]trangers?\b|nationalit|r[ée]fugi|OFPRA|OFII|regroupement familial|apatrid"
FR_ETRANGER = r"à l.étranger|de l.[ée]tranger|survenu à l|célébré à l|Français|consulaire"   # Français établis hors de France : hors sujet
# Titres de démarches DN sur les étrangers : plus large (abréviations des préfectures), pour qu'aucune n'y perde sa vigilance par erreur
DN_ETR_MOTS = ETR_MOTS + r"|passeport talent|statut [ée]tudiant|changement de statut|r[ée]c[ée]piss|\bAPS\b|binationa|droit d.option|d[ée]claration d.option|protection temporaire|autorisation de travail|carte de r[ée]sident|\bDCEM\b|\bTIR\b|titre de voyage|\bOQTF\b|r[ée]gularisation|ressortissant|\bBPI\b|\bTUE\b"
PART_FORTE = 0.5                           # part des retours d'une préfecture sur les étrangers jugée forte


def lire_lignes_spp(chemin, debut=""):
    """Une ligne par retour : date, ressenti, critères cochés, démarches nommées, structures, typologies, tags. Aucun texte."""
    csv.field_size_limit(10 ** 9)
    with open(chemin, encoding="utf-8-sig", newline="") as f:
        r = csv.reader(f, delimiter=";"); h = [x.strip() for x in next(r)]; col = {k: i for i, k in enumerate(h)}
        i_st = [i for i, k in enumerate(h) if k.startswith("Intitulé structure")]
        i_ty = [i for i, k in enumerate(h) if k.startswith("Intitulé Typologie")]
        for row in r:
            if len(row) < len(h) or row[col["Date de publication"]][:10] < debut: continue
            neg = row[col["Ressenti usager"]] == "Négatif"
            dm = row[col["Démarches modérées"]].strip()
            yield {"date": row[col["Date de publication"]][:10], "neg": neg,
                   "crit": [CRITERES[c] for c in CRITERES if row[col[c]] == "Négatif"] if neg else [],
                   "dm": dm, "dms": [x.strip() for x in re.split(r", (?=[A-ZÉÈÀÂ])", dm) if x.strip()],
                   "st": list(dict.fromkeys(x for x in (row[i].strip() for i in i_st) if x and x != "Hors-structures")),
                   "ty": {row[i].strip() for i in i_ty} - {""},
                   "tags": {t.strip() for t in row[col["Tags Métiers"]].split(",") if t.strip()}}


def agreger(lignes):
    c = collections.Counter()
    for x in lignes:
        c["n"] += 1; c["neg"] += x["neg"]
        for m in x["crit"]: c[m] += 1
    motifs = sorted(((m, c[m]) for m in CRITERES.values() if c[m] >= SEUIL_MOTIF), key=lambda x: -x[1])[:MAX_MOTIFS]
    return {"n": c["n"], "neg": c["neg"], "motifs": [list(m) for m in motifs] if c["n"] >= SEUIL_RETOURS else [],
            "vigilance": c["n"] >= SEUIL_RETOURS and bool(motifs)}


def est_etranger(x):
    return bool(x["ty"] & ETR_TYPOLOGIES or x["tags"] & ETR_TAGS
                or any(re.search(ETR_MOTS, d, re.I) and not re.search(FR_ETRANGER, d) for d in x["dms"]))


def etude_spp_suite(A, recs, obs_par_nom, debut):
    sp = [r for r in recs if r["k"] == "sp"]
    toutes = list(lire_lignes_spp(A.spp)); L = [x for x in toutes if x["date"] >= debut]
    fiche = lambda r: {"id": r["id"], "titre": r["t"], "url_fiche": r["u"], "service_en_ligne": r.get("l", "")}
    out = {"objet": "Suite de l'étude Services Publics + (qualite.py --proposer-spp) : ANTS par domaine, France Travail, retours sur les "
                    "étrangers, part des étrangers dans les préfectures rattachées aux démarches Démarche Numérique. Rien n'est appliqué.",
           "periode": {"debut": debut, "fichier": A.date_spp}, "seuils": {"retours": SEUIL_RETOURS, "motif": SEUIL_MOTIF, "part_forte": PART_FORTE}}

    # 1. ANTS, découpée par domaine : un retour ne compte pour un domaine que si toutes ses démarches nommées en relèvent.
    def domaine_ants(nom):
        os_ = obs_par_nom.get(cle(nom), [])
        if len(os_) == 1:
            d = _domaine(os_[0].get("URL Démarche"))
            return (ANTS_DOMAINES[d], "adresse dans l'Observatoire") if d in ANTS_DOMAINES else (None, f"autre service ({d or 'sans adresse'})")
        if len(os_) > 1: return None, "plusieurs lignes de l'Observatoire"
        for motif, dom in ANTS_NOMS:
            if re.search(motif, nom, re.I): return dom, "nom (absent de l'Observatoire)"
        return None, "hors des trois domaines"
    ants = [x for x in L if ANTS in x["st"]]
    noms, par_dom = {}, collections.defaultdict(list); hors = collections.Counter()
    for x in ants:
        if not x["dms"]: hors["sans démarche nommée"] += 1; continue
        ds = {noms.setdefault(d, domaine_ants(d))[0] for d in x["dms"]}
        if len(ds) == 1 and None not in ds: par_dom[ds.pop()].append(x)
        else: hors["démarche nommée hors domaine, ou plusieurs domaines"] += 1
    doms = []
    for d, dom in ANTS_DOMAINES.items():
        fs = [fiche(r) for r in sp if r.get("l") and _domaine(r["l"]) == d]
        dn = collections.Counter(n for x in par_dom[dom] for n in x["dms"])
        doms.append({"domaine": dom, "adresse": d, **agreger(par_dom[dom]), "demarches_nommees": [[k, v, noms[k][1]] for k, v in dn.most_common()],
                     "fiches": fs})
    out["ants"] = {"structure": ANTS, "retours": len(ants), "non_comptes": dict(hors), "domaines": doms,
                   "noms_hors_domaine": sorted([[k, sum(1 for x in ants if k in x["dms"]), v[1]] for k, v in noms.items() if v[0] is None], key=lambda t: -t[1]),
                   "fiches_ants_non_retenues": [fiche(r) for r in sp if r.get("l") and _domaine(r["l"]).endswith("ants.gouv.fr") and _domaine(r["l"]) not in ANTS_DOMAINES]}

    # 2. France Travail : directions régionales additionnées (un retour compté une fois).
    ft = [x for x in L if any(re.match(FT_DR, s) for s in x["st"])]
    autres_ft = [x for x in L if not any(re.match(FT_DR, s) for s in x["st"]) and any(re.search(r"france travail", s, re.I) for s in x["st"])]
    dr = collections.Counter(s for x in ft for s in x["st"] if re.match(FT_DR, s))
    dn = collections.Counter(n for x in ft for n in x["dms"])
    out["france_travail"] = {"structure": "France Travail (directions régionales additionnées)", **agreger(ft),
                             "directions_regionales": dr.most_common(), "retours_sans_demarche_nommee": sum(1 for x in ft if not x["dms"]),
                             "demarches_nommees_distinctes": len(dn), "demarches_nommees": dn.most_common(15),
                             "autres_structures_france_travail_non_comptees": {"structures": len({s for x in autres_ft for s in x["st"] if re.search("france travail", s, re.I)}), "retours": len(autres_ft)},
                             "domaine": FT_DOMAINE, "fiches": [fiche(r) for r in sp if r.get("l") and _domaine(r["l"]) == FT_DOMAINE],
                             "fiches_autres_domaines_france_travail": [fiche(r) for r in sp if r.get("l") and re.search(r"francetravail|pole-emploi", _domaine(r["l"])) and _domaine(r["l"]) != FT_DOMAINE]}

    # 3. Étrangers : tout le fichier, sans seuil.
    def compte(xs): return {"tout_le_fichier": len(xs), "deux_ans": sum(1 for x in xs if x["date"] >= debut)}
    E = [x for x in toutes if est_etranger(x)]
    dms = collections.Counter(d for x in toutes for d in x["dms"] if re.search(ETR_MOTS, d, re.I))
    sts = collections.Counter(s for x in toutes for s in x["st"] if re.search(ETR_MOTS, s, re.I))
    out["etrangers"] = {
        "definition": "retour dont une typologie est %s, ou un tag métier %s, ou une démarche nommée liée aux étrangers (hors Français établis à l'étranger)"
                      % (sorted(ETR_TYPOLOGIES), sorted(ETR_TAGS)),
        "retours": compte(E), "annees": sorted(collections.Counter(x["date"][:4] for x in E).items()),
        "par_typologie": {t: compte([x for x in E if t in x["ty"]]) for t in sorted(ETR_TYPOLOGIES)},
        "par_tag": {t: compte([x for x in E if t in x["tags"]]) for t in sorted(ETR_TAGS)},
        "sans_demarche_nommee": compte([x for x in E if not x["dms"]]),
        "sans_structure": compte([x for x in E if not x["st"]]),
        "demarches_nommees_qui_citent_ces_mots": [[d, n, "Français établis à l'étranger (hors sujet)" if re.search(FR_ETRANGER, d) else "étrangers"] for d, n in dms.most_common()],
        "structures_qui_citent_ces_mots": [[s, n, "Français établis à l'étranger (hors sujet)" if re.search(FR_ETRANGER + r"|à l'étranger", s) else "étrangers"] for s, n in sts.most_common()],
        "structures_des_retours": collections.Counter(s for x in E for s in x["st"]).most_common(30),
        "typologies_des_retours": collections.Counter(t for x in E for t in x["ty"]).most_common(15),
        "lignes_observatoire": [[o[0]["ID Démarche"], o[0]["Nom Démarche"], _domaine(o[0].get("URL Démarche"))] for k, o in obs_par_nom.items()
                                if re.search(ETR_MOTS, o[0]["Nom Démarche"], re.I) and not re.search(FR_ETRANGER, o[0]["Nom Démarche"])],
        "fiches_vers_anef": [fiche(r) for r in sp if r.get("l") and _domaine(r["l"]) == "administration-etrangers-en-france.interieur.gouv.fr"]}

    # 4. Préfectures rattachées aux démarches DN par leur organisme : part des retours sur les étrangers.
    dn_pref = collections.defaultdict(list)
    for r in recs:
        if r["k"] == "dn" and r.get("spp") and r["spp"][3] and re.match(r"(Sous-)?[Pp]r[ée]fecture", r["spp"][3]): dn_pref[cle(r["spp"][3])].append(r)
    prefs = []
    for k, rs in sorted(dn_pref.items(), key=lambda kv: -len(kv[1])):
        xs = [x for x in L if k in {cle(s) for s in x["st"]}]; e = [x for x in xs if est_etranger(x)]; ne = [x for x in xs if not est_etranger(x)]
        de = [r for r in rs if re.search(DN_ETR_MOTS, r["t"], re.I)]
        sans = agreger(ne)
        prefs.append({"structure": rs[0]["spp"][3], **{k2: v for k2, v in agreger(xs).items() if k2 != "vigilance"}, "etrangers": len(e),
                      "part_etrangers": round(len(e) / len(xs), 3) if xs else 0, "forte": bool(xs) and len(e) / len(xs) >= PART_FORTE,
                      "sans_etrangers": sans, "demarches_dn": len(rs), "demarches_dn_etrangers": [[r["id"], r["t"]] for r in de]})
    forte = [p for p in prefs if p["forte"]]
    out["prefectures"] = {"definition_etrangers": "comme pour la partie étrangers", "structures": prefs,
        "bilan": {"structures": len(prefs), "demarches_dn_avec_vigilance_prefecture": sum(p["demarches_dn"] for p in prefs),
                  "structures_part_forte": len(forte),
                  "demarches_dn_non_etrangers_des_prefectures_part_forte": sum(p["demarches_dn"] - len(p["demarches_dn_etrangers"]) for p in forte),
                  "demarches_dn_etrangers_des_prefectures_part_forte": sum(len(p["demarches_dn_etrangers"]) for p in forte),
                  "variante_sans_etrangers_vigilance_gardee": sum(p["demarches_dn"] - len(p["demarches_dn_etrangers"]) for p in prefs if p["sans_etrangers"]["vigilance"]),
                  "variante_sans_etrangers_vigilance_perdue": sum(p["demarches_dn"] - len(p["demarches_dn_etrangers"]) for p in prefs if not p["sans_etrangers"]["vigilance"])}}
    (D / "assistant" / "spp_suite_propositions.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return out


def rapport_suite(o):
    p = print; mot = lambda m: ", ".join(f"{a} ({b})" for a, b in m) or "aucun"
    a = o["ants"]
    p(f"\n## Partie 3 : ANTS par domaine\n\n{a['retours']} retours sur la structure « {a['structure']} » ; non comptés : "
      + " ; ".join(f"{k} {v}" for k, v in a["non_comptes"].items()) + ".\n")
    p("| Domaine | Retours | Négatifs | Motifs | Vigilance | Fiches (adresse) |\n|---|---|---|---|---|---|")
    for d in a["domaines"]:
        p(f"| {d['domaine']} | {d['n']} | {d['neg']} | {mot(d['motifs'])} | {'oui' if d['vigilance'] else 'non'} | {len(d['fiches'])} ({d['adresse']}) |")
    for d in a["domaines"]:
        p(f"\n**{d['domaine']}** : démarches nommées comptées — " + " ; ".join(f"{k} ({v}, par {m})" for k, v, m in d["demarches_nommees"]))
        p("\nFiches : " + " ; ".join(f"[{f['id']}]({f['url_fiche']}) {f['titre'][:70]}" for f in d["fiches"]))
    p("\nNoms écartés (hors des trois domaines) : " + " ; ".join(f"{k} ({n}, {m})" for k, n, m in a["noms_hors_domaine"][:15]))
    p("\nFiches ANTS d'une autre adresse, non retenues : " + " ; ".join(f"[{f['id']}]({f['url_fiche']}) {f['titre'][:60]} ({_domaine(f['service_en_ligne'])})" for f in a["fiches_ants_non_retenues"]))
    f = o["france_travail"]
    p(f"\n## Partie 4 : France Travail\n\n| | |\n|---|---|\n| Directions régionales additionnées | {len(f['directions_regionales'])} |"
      f"\n| Retours (comptés une fois) | {f['n']} |\n| Négatifs | {f['neg']} |\n| Motifs | {mot(f['motifs'])} |\n| Vigilance | {'oui' if f['vigilance'] else 'non'} |"
      f"\n| Retours sans démarche nommée | {f['retours_sans_demarche_nommee']} |\n| Démarches nommées distinctes | {f['demarches_nommees_distinctes']} |"
      f"\n| Autres structures France Travail, non comptées | {f['autres_structures_france_travail_non_comptees']['structures']} structures, {f['autres_structures_france_travail_non_comptees']['retours']} retours |"
      f"\n| Fiches vers {f['domaine']} | {len(f['fiches'])} |\n")
    p("Démarches nommées les plus citées : " + " ; ".join(f"{k} ({v})" for k, v in f["demarches_nommees"][:10]))
    p("\nFiches : " + " ; ".join(f"[{x['id']}]({x['url_fiche']}) {x['titre'][:70]}" for x in f["fiches"]))
    p("\nFiches vers un autre domaine France Travail, non retenues : " + " ; ".join(f"[{x['id']}]({x['url_fiche']}) {x['titre'][:50]} ({_domaine(x['service_en_ligne'])})" for x in f["fiches_autres_domaines_france_travail"]))
    e = o["etrangers"]; c = lambda v: f"{v['tout_le_fichier']} | {v['deux_ans']}"
    p(f"\n## Partie 5 : étrangers (tout le fichier, sans seuil)\n\nDéfinition : {e['definition']}.\n\n| | Tout le fichier | Deux ans |\n|---|---|---|")
    p(f"| Retours sur les étrangers | {c(e['retours'])} |\n| dont sans démarche nommée | {c(e['sans_demarche_nommee'])} |\n| dont sans structure | {c(e['sans_structure'])} |")
    for t, v in e["par_typologie"].items(): p(f"| typologie « {t} » | {c(v)} |")
    for t, v in e["par_tag"].items(): p(f"| tag métier « {t} » | {c(v)} |")
    p("\nPar année : " + ", ".join(f"{a} : {n}" for a, n in e["annees"]))
    p("\nDémarches nommées qui citent ces mots (tout le fichier) : " + " ; ".join(f"{d} ({n}, {k})" for d, n, k in e["demarches_nommees_qui_citent_ces_mots"] if "," not in d or k == "étrangers"))
    p("\nStructures qui citent ces mots : " + " ; ".join(f"{s} ({n}, {k})" for s, n, k in e["structures_qui_citent_ces_mots"]))
    p("\nStructures des retours sur les étrangers : " + " ; ".join(f"{s} ({n})" for s, n in e["structures_des_retours"][:15]))
    p("\nLignes de l'Observatoire sur les étrangers : " + " ; ".join(f"{i} {n[:70]} ({d})" for i, n, d in e["lignes_observatoire"]))
    p(f"\nFiches service-public vers l'ANEF (administration-etrangers-en-france.interieur.gouv.fr) : {len(e['fiches_vers_anef'])}")
    pr = o["prefectures"]; b = pr["bilan"]
    p(f"\n## Partie 6 : préfectures rattachées aux démarches Démarche Numérique\n\n| Préfecture | Retours | Étrangers | Part | Motifs | Sans les étrangers : retours, motifs | Démarches DN | dont sur les étrangers |\n|---|---|---|---|---|---|---|---|")
    for x in pr["structures"]:
        s = x["sans_etrangers"]
        p(f"| {x['structure']} | {x['n']} | {x['etrangers']} | {round(100 * x['part_etrangers'])} %{' (forte)' if x['forte'] else ''} | {mot(x['motifs'])} | "
          f"{s['n']}, {mot(s['motifs']) if s['vigilance'] else 'plus de vigilance'} | {x['demarches_dn']} | {len(x['demarches_dn_etrangers'])} |")
    p(f"\n{b['structures']} préfectures, {b['demarches_dn_avec_vigilance_prefecture']} démarches DN avec leur vigilance ; part forte (≥ {round(100 * PART_FORTE)} %) : "
      f"{b['structures_part_forte']} préfectures, {b['demarches_dn_non_etrangers_des_prefectures_part_forte']} démarches DN hors étrangers qui perdraient la vigilance, "
      f"{b['demarches_dn_etrangers_des_prefectures_part_forte']} sur les étrangers qui la garderaient. Variante (vigilance recalculée sans les retours sur les étrangers, "
      f"pour toutes les préfectures) : {b['variante_sans_etrangers_vigilance_gardee']} démarches DN hors étrangers la gardent, {b['variante_sans_etrangers_vigilance_perdue']} la perdent.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--observatoire", required=True); ap.add_argument("--edition", required=True)
    ap.add_argument("--spp", required=True); ap.add_argument("--date-spp", required=True, help="date du fichier export-experiences.csv (AAAA-MM-JJ)")
    ap.add_argument("--proposer", action="store_true", help="liste les rattachements univoques Observatoire → index absents de observatoire_rattachement.json")
    ap.add_argument("--proposer-spp", action="store_true", help="étude : propositions de rattachement Services Publics + (démarches nommées, structures), "
                    "écrites dans spp_rattachement_propositions.json et spp_structures_propositions.json ; rapport Markdown sur la sortie ; rien n'est appliqué")
    A = ap.parse_args()
    if A.proposer_spp: proposer_spp(A); return
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
