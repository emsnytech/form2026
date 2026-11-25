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
