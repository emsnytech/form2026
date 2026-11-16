"""Fiche Intérieur, arbitrage n° 23 : (A) variété des usages entre départements ; (B) test de la condition préalable ;
(C) services propres du ministère (police, gendarmerie, administration centrale). Open data seul.

Règles, fixées avant lecture des résultats :
- unité de l'analyse A : le département. Instructeur lu dans l'organisme et le service (même règle que le script 36) :
  « préfecture » (préfecture, sous-préfectures, SGCD, préfecture de police) d'un côté ; directions départementales d'autres
  ministères (DDT, DDETS, DDPP…) comptées à part. Les unités régionales (SGAR, SRIAS, préfecture de région sans département
  nommé, DREAL…) sont comptées à part et n'entrent dans aucun département.
- une démarche de niveau national (script 32) n'est rattachée à aucun département.
- rattachement au département, dans l'ordre : (1) « préfecture de/du/de la <département> » dans l'organisme ; préfecture de
  police → 75 ; (2) code dans l'organisme, le service ou le titre (PREF33, SGC34, DDT79, « (77) », « 77 - » en tête de titre) ;
  (3) nom de département dans l'organisme ou le service ; (4) nom non ambigu dans le titre ; (5) à défaut, champ département
  de la démarche. Le recours au champ (5) est compté, et sa concordance mesurée là où (1) à (4) donnent un résultat.
- familles de politiques (7) : permis et auto-écoles ; élections ; polices administratives (réglementation, transport de
  personnes et véhicules) ; dotations et aides ; RH et action sociale (recrutement et gestion, action sociale des agents) ;
  étrangers (séjour, vérification avant embauche) ; autres (le reste, médailles comprises).
- mesures par département : démarches du périmètre, dossiers, familles couvertes (au moins une démarche), familles couvertes
  par une démarche en ligne aujourd'hui. Distribution sur les 101 départements, zéros compris. Aucun département nommé en sortie.
- réglementations uniformes : NEPH, label des écoles de conduite, DETR et DSIL (familles de titres du script 32), élections et
  une police administrative (famille de titres couvrant le plus de départements dans ces deux familles) : départements ayant au
  moins une démarche (toutes unités), quartiles des dossiers par département.
- B : à la date de la première version nationale d'au moins 100 dossiers, départements distincts ayant déjà publié une version
  locale (cumul), et départements ayant une version locale ouverte à cette date, sur 101. Fondations : titres de la brique
  (script 37). Cas contraires : vérification avant embauche, médailles.
- C : démarches dont l'instructeur est la police, la gendarmerie ou l'administration centrale, réparties par famille.
Sortie : out/interieur_variete.json (comptes et distributions, aucun nom de territoire)."""
import json, re, sys, statistics as S, collections as C, datetime as dt
sys.argv = ["x", "scripts/config_interieur.json", "/dev/null"]
src32 = open("scripts/32_local_national_interieur.py").read()
exec(src32.split("res = []")[0])
src36 = open("scripts/36_qui_instruit_interieur.py").read()
exec("INSTR" + src36.split("INSTR", 1)[1].split("I = \"Ministère")[0])
DEPS = json.load(open("scripts/departements.json")); NDEP = len(DEPS)
NOM = {v: k for k, v in DEPS.items()}
rxn = lambda names: "|".join(sorted((re.escape(x).replace(r"\-", "[- ]").replace("'", "[' ]?") for x in names), key=len, reverse=True))
NOMRX = re.compile(r"(?<![a-z-])(" + rxn(NOM) + r")(?![a-z-])")
NOMRX_T = re.compile(r"(?<![a-z-])(" + rxn([x for x in NOM if x not in AMBIGUS]) + r")(?![a-z-])")
PREFRX = re.compile(r"prefecture (?:de la |de l'|du |des |de |d')\s*(" + rxn(NOM) + r")(?![a-z-])")
CODE = r"(0[1-9]|[1-8]\d|9[0-5]|2a|2b|97[1-46])"
CODERX = re.compile(r"\b(?:pref|sgcd?|ddt|ddtm|ddets|ddetspp|ddpp|ddcspp|ud|dd)\s?-?" + CODE + r"\b|\(\s*" + CODE + r"\s*\)")
REGION = re.compile(r"\bsgar\b|\bsrias\b|prefecture de (la )?region|\bdreal\b|\bdriea|\bdrieets?\b|\bdreets\b|\bdraaf\b|\bdriaaf\b|interregional|\bsgami\b|zone de defense")
canon = lambda s: re.sub(r"[ ]", "-", s.replace("' ", "'")).replace("d-", "d'") if s else s
def nomcode(s):
    s = s.replace(" ", "-")
    for k, v in DEPS.items():
        if re.sub(r"[-']", "", v) == re.sub(r"[-']", "", s): return k
def departement(r):
    o = na((r["organisme"] or "") + " | " + (r["service_nom"] or "")); t = na(r["title"])
    m = PREFRX.search(o)
    if m: return nomcode(m.group(1)), "nom"
    if re.search(r"prefecture de police", o): return "75", "nom"
    if REGION.search(o): return None, "regional"
    for txt in (o, t):
        m = CODERX.search(txt)
        if m: c = (m.group(1) or m.group(2)).upper(); return (c if c in DEPS else None), "code"
    m = re.match(r"\s*" + CODE + r"\s?-", t)
    if m and m.group(1).upper() in DEPS: return m.group(1).upper(), "code"
    m = NOMRX.search(o)
    if m: return nomcode(m.group(1)), "nom"
    m = NOMRX_T.search(t)
    if m: return nomcode(m.group(1)), "titre"
    f = (r["departement"] or "").upper()
    return (f if f in DEPS else None), "champ"
POL = {"Permis de conduire, aptitude à la conduite, éducation routière": "permis et auto-écoles", "Élections": "élections",
       "Réglementation et polices administratives": "polices administratives",
       "Transport de personnes et véhicules (taxis, VTC, contrôle technique, fourrière)": "polices administratives",
       "Dotations et subventions": "dotations et aides", "Recrutement, concours, formation et gestion des agents": "RH et action sociale",
       "Action sociale des agents": "RH et action sociale", "Étrangers : séjour, asile, nationalité": "étrangers",
       "Étrangers : vérification d'un titre avant embauche": "étrangers"}
FAMS7 = ["permis et auto-écoles", "élections", "polices administratives", "dotations et aides", "RH et action sociale", "étrangers", "autres"]
PREF, DDX = "préfecture ou sous-préfecture", "direction départementale ou régionale d'un autre ministère (DDT, DDETS, DREAL, DRIEAT...)"
nd = lambda L: sum(r["dossiersCount"] or 0 for r in L)
for r in per:
    r["instr"] = instr(r); r["pol"] = POL.get(r["fam"], "autres")
    r["dep"], r["dep_src"] = (None, "nationale") if r["niv"] == "nationale" else (departement(r) if r["instr"] in (PREF, DDX) or r["niv"] == "locale" else (None, "hors"))
def quart(v):
    v = sorted(v); q = S.quantiles(v, n=4, method="inclusive") if len(v) > 1 else [v[0]] * 3
    return {"min": v[0], "q1": round(q[0], 1), "mediane": round(q[1], 1), "q3": round(q[2], 1), "max": v[-1]}
def deciles(v):
    v = sorted(v); return [round(x, 1) for x in S.quantiles(v, n=10, method="inclusive")]
out = {"regles": {"departements": NDEP}}
U = [r for r in per if r["instr"] in (PREF, DDX)]
out["rattachement"] = {"unites": len(U), "par_source": dict(C.Counter(r["dep_src"] for r in U)),
                       "sans_departement": sum(1 for r in U if r["dep"] is None)}
# concordance du champ département là où le nom ou le code donne un résultat
chk = [r for r in U if r["dep_src"] in ("nom", "code") and r["dep"]]
out["rattachement"]["concordance_champ"] = [sum((r["departement"] or "").upper() == r["dep"] for r in chk), len(chk)]
# A. par département
A = {}
for unit, lab in ((PREF, "prefectures"), (DDX, "directions_departementales")):
    L = [r for r in per if r["instr"] == unit and r["dep"]]
    par = {k: [r for r in L if r["dep"] == k] for k in DEPS}
    nb = [len(v) for v in par.values()]; ds = [nd(v) for v in par.values()]
    fc = [len({r["pol"] for r in v}) for v in par.values()]
    fo = [len({r["pol"] for r in v if r["state"] == "publiee"}) for v in par.values()]
    pub = [sum(r["state"] == "publiee" for r in v) for v in par.values()]
    A[lab] = {"demarches": len(L), "dossiers": nd(L), "departements_avec_au_moins_une": sum(1 for x in nb if x),
              "demarches_par_departement": quart(nb), "deciles_demarches": deciles(nb), "dossiers_par_departement": quart(ds),
              "en_ligne_par_departement": quart(pub),
              "familles_couvertes": dict(sorted(C.Counter(fc).items())), "familles_couvertes_en_ligne": dict(sorted(C.Counter(fo).items())),
              "departements_par_famille": {f: sum(1 for v in par.values() if any(r["pol"] == f for r in v)) for f in FAMS7},
              "rapport_q3_q1_demarches": round(quart(nb)["q3"] / quart(nb)["q1"], 1) if quart(nb)["q1"] else None}
    if lab == "prefectures":
        # typologie : départements « larges » (6 ou 7 familles) et « étroits » (3 ou moins) : composition moyenne
        def compo(keys): return {f: round(S.mean(sum(r["pol"] == f for r in par[k]) for k in keys), 1) for f in FAMS7} if keys else {}
        large = [k for k, v in par.items() if len({r["pol"] for r in v}) >= 6]; etroit = [k for k, v in par.items() if len({r["pol"] for r in v}) <= 3]
        A[lab]["typologie"] = {"larges_6_7_familles": [len(large), compo(large), round(S.mean(len(par[k]) for k in large), 1) if large else 0],
                               "etroits_3_familles_ou_moins": [len(etroit), compo(etroit), round(S.mean(len(par[k]) for k in etroit), 1) if etroit else 0]}
out["A"] = A
out["A"]["unites_regionales"] = [sum(1 for r in per if r["dep_src"] == "regional"), nd([r for r in per if r["dep_src"] == "regional"])]
# réglementations uniformes
for c in clusters: c["deps"] = {r["dep"] for r in c["m"] if r["dep"]}
LNd = json.load(open("out/interieur_local_national.json"))["detail"]
def pick(rx):
    t = next(x["titre_graine"] for x in LNd if re.search(rx, x["titre_graine"]))
    return next(c for c in clusters if c["titre"] == t)
CLU = {"NEPH": pick(r"NEPH"), "label des écoles de conduite": pick(r"qualit. des formations"), "DETR et DSIL": pick(r"DETR et de la DSIL")}
# réglementations uniformes : définitions par mots du titre, choisies après lecture des titres (le regroupement par famille de
# titres du script 32 fragmente les intitulés propres à chaque préfecture et sous-estime la couverture).
PERMIS, DOT = "Permis de conduire, aptitude à la conduite, éducation routière", "Dotations et subventions"
UNI = {"NEPH": (r"\bNEPH\b", {PERMIS}), "label des écoles de conduite": (r"label.{0,80}conduite|qualit[ée] des formations", None),
       "DETR et DSIL": (r"\bDETR\b|\bDSIL\b", {DOT}),
       "élections : mise sous pli de la propagande": (r"mise sous pli|propagande", {"Élections", "Recrutement, concours, formation et gestion des agents"}),
       "police administrative : déclaration de manifestation sur la voie publique": (r"manifestation.{0,30}voie publique|d[ée]claration de manifestation", None)}
SEL = {}
out["uniformes"] = {}
for k, (rx, fams) in UNI.items():
    L = [r for r in per if re.search(rx, r["title"] or "", re.I) and (fams is None or r["fam"] in fams)]; SEL[k] = L
    per_dep = C.defaultdict(list)
    for r in L:
        if r["dep"]: per_dep[r["dep"]].append(r)
    vols = [nd(v) for v in per_dep.values()]
    out["uniformes"][k] = {"motif": rx, "demarches": len(L), "dossiers": nd(L), "departements": len(per_dep),
        "departements_en_ligne": len({r["dep"] for r in L if r["dep"] and r["state"] == "publiee"}),
        "dossiers_par_departement": quart(vols) if vols else None, "versions_nationales": sum(r["niv"] == "nationale" for r in L),
        "versions_par_departement_max": max((len(v) for v in per_dep.values()), default=0)}
# B. condition préalable
def test(L, n0):
    loc = [r for r in L if r["niv"] == "locale" and r["dep"]]
    avant = {r["dep"] for r in loc if d(r["datePublication"]) <= n0}
    ouv = {r["dep"] for r in loc if d(r["datePublication"]) <= n0 and (fin(r) is None or fin(r) > n0)}
    return {"date_nationale": str(n0), "departements_deja_une_locale": len(avant), "part": round(100 * len(avant) / NDEP, 1),
            "departements_locale_ouverte": len(ouv), "part_ouverte": round(100 * len(ouv) / NDEP, 1),
            "departements_locale_total": len({r["dep"] for r in loc})}
B = {}
for k in ("NEPH", "label des écoles de conduite", "DETR et DSIL"):
    c = CLU[k]; nat = [r for r in c["m"] if r["niv"] == "nationale"]
    n100 = min(d(r["datePublication"]) for r in nat if (r["dossiersCount"] or 0) >= 100)
    B[k] = test(c["m"], n100)                       # règle : la famille de titres du script 32
    B[k]["variante_mots_du_titre"] = test(SEL[k], n100)  # sensibilité : définition large par mots du titre
    n0 = min(d(r["datePublication"]) for r in nat)
    if n0 != n100: B[k]["premiere_version_nationale_toutes"] = test(c["m"], n0)
FO = [r for r in per if re.search(r"fondation|fonds de dotation|reconnue? d.utilit[ée] publique|\bFRUP\b|\bRUP\b", r["title"] or "", re.I)]
FOn = [r for r in FO if r["niv"] == "nationale" and (r["dossiersCount"] or 0) >= 100]
B["fondations et fonds de dotation"] = test(FO, min(d(r["datePublication"]) for r in FOn))
B["fondations et fonds de dotation"]["locales_hors_departement_regionales"] = sum(1 for r in FO if r["niv"] == "locale" and not r["dep"])
VE = [r for r in per if r["fam"] == "Étrangers : vérification d'un titre avant embauche"]
B["vérification avant embauche"] = {"versions_nationales": sum(r["niv"] == "nationale" for r in VE), "departements": len({r["dep"] for r in VE if r["dep"]}),
                                    "part": round(100 * len({r["dep"] for r in VE if r["dep"]}) / NDEP, 1)}
ME = [r for r in per if r["fam"] == "Médailles et distinctions"]
men = [r for r in ME if r["niv"] == "nationale"]
B["médailles"] = {"premiere_nationale": str(min(d(r["datePublication"]) for r in men)),
                  "departements_locale_avant": len({r["dep"] for r in ME if r["niv"] == "locale" and r["dep"] and d(r["datePublication"]) <= min(d(x["datePublication"]) for x in men)}),
                  "locales": sum(r["niv"] == "locale" for r in ME), "dossiers_locaux": nd([r for r in ME if r["niv"] == "locale"])}
out["B"] = B
# C. services propres
INTERNE = re.compile(r"[ée]l[eè]ves?|\\bEGPX?\\b|gardiens de la paix|c[ée]r[ée]monie|accus[ée]s? (de )?r[ée]ception|incorporation|cong[ée] bonifi|promotion|scolarit|stagiaires?|\\bAMGN\\b|\\bIFCR\\b|mutation", re.I)
PROP = {"police, gendarmerie et leurs écoles": "police et gendarmerie", "administration centrale de l'Intérieur": "administration centrale"}
out["C"] = {}
for k, lab in PROP.items():
    L = [r for r in per if r["instr"] == k]
    fams = C.Counter(); fd = C.Counter()
    for r in L: fams[r["pol"]] += 1; fd[r["pol"]] += r["dossiersCount"] or 0
    rh = [r for r in L if r["pol"] == "RH et action sociale"]
    hors_rh = [r for r in L if r["pol"] != "RH et action sociale"]
    out["C"][lab] = {"demarches": len(L), "dossiers": nd(L), "par_famille": {f: [fams[f], fd[f]] for f in FAMS7 if fams[f]},
        "part_rh_demarches": round(100 * len(rh) / len(L), 1) if L else 0, "part_rh_dossiers": round(100 * nd(rh) / nd(L), 1) if L else 0,
        "hors_rh": [len(hors_rh), nd(hors_rh)], "hors_rh_hors_medailles": [sum(1 for r in hors_rh if r["fam"] != "Médailles et distinctions"), nd([r for r in hors_rh if r["fam"] != "Médailles et distinctions"])],
        "en_ligne": sum(r["state"] == "publiee" for r in L),
        "autres_dont_internes": [sum(1 for r in L if r["pol"] == "autres" and INTERNE.search(r["title"] or "")), nd([r for r in L if r["pol"] == "autres" and INTERNE.search(r["title"] or "")])],
        "detail_familles": dict(C.Counter(r["fam"] for r in L).most_common(8))}
    if lab == "police et gendarmerie":
        top = sorted(hors_rh, key=lambda r: -(r["dossiersCount"] or 0))[:6]
        out["C"][lab]["plus_lourdes_hors_rh"] = [(r["number"], r["fam"], r["dossiersCount"], r["niv"]) for r in top]
# ---- arbitrage n° 24 -------------------------------------------------------------------------------------------------
# (1) contrôle de taille : population de référence 2023 (INSEE, fichier d'ensemble, France hors Mayotte), corrélation de rang
import csv
POP = {}
for x in csv.DictReader(open("sources/insee_populations_reference_2023_departements.csv", encoding="utf-8"), delimiter=";"):
    POP[x["DEP"].upper()] = int(x["PTOT"])
def rangs(v):
    o = sorted(range(len(v)), key=lambda i: v[i]); r = [0.0] * len(v); i = 0
    while i < len(o):
        j = i
        while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]: j += 1
        for k in range(i, j + 1): r[o[k]] = (i + j) / 2 + 1
        i = j + 1
    return r
def spearman(a, b):
    ra, rb = rangs(a), rangs(b); ma, mb = S.mean(ra), S.mean(rb)
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    return round(num / (sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb)) ** 0.5, 2)
LP = [r for r in per if r["instr"] == PREF and r["dep"]]
parP = {k: [r for r in LP if r["dep"] == k] for k in DEPS}
K = [k for k in DEPS if k in POP]
mes = {"en_ligne": lambda v: sum(r["state"] == "publiee" for r in v), "familles": lambda v: len({r["pol"] for r in v}),
       "familles_en_ligne": lambda v: len({r["pol"] for r in v if r["state"] == "publiee"}), "depuis_origine": len, "dossiers": nd}
taille = {"departements": len(K), "source": "INSEE, populations de référence 2023, population totale, France hors Mayotte",
          "spearman_population": {m: spearman([POP[k] for k in K], [f(parP[k]) for k in K]) for m, f in mes.items()}}
# à taille comparable : quartiles de population, étendue des démarches en ligne et des familles couvertes
qp = S.quantiles([POP[k] for k in K], n=4, method="inclusive")
cls = lambda x: 0 if x <= qp[0] else 1 if x <= qp[1] else 2 if x <= qp[2] else 3
taille["par_quart_de_population"] = []
for c in range(4):
    ks = [k for k in K if cls(POP[k]) == c]
    el = [mes["en_ligne"](parP[k]) for k in ks]; fa = [mes["familles"](parP[k]) for k in ks]
    taille["par_quart_de_population"].append({"departements": len(ks), "en_ligne_min": min(el), "en_ligne_mediane": S.median(el), "en_ligne_max": max(el),
                                              "familles_min": min(fa), "familles_max": max(fa)})
out["taille"] = taille
# (2) sensibilité au champ département (dernier recours)
LP2 = [r for r in LP if r["dep_src"] != "champ"]
par2 = {k: [r for r in LP2 if r["dep"] == k] for k in DEPS}
out["sans_champ"] = {"demarches_retirees": len(LP) - len(LP2),
    "demarches_par_departement": quart([len(v) for v in par2.values()]), "en_ligne_par_departement": quart([mes["en_ligne"](v) for v in par2.values()]),
    "familles_couvertes": dict(sorted(C.Counter(len({r["pol"] for r in v}) for v in par2.values()).items())),
    "familles_couvertes_en_ligne": dict(sorted(C.Counter(len({r["pol"] for r in v if r["state"] == "publiee"}) for v in par2.values()).items()))}
# (3) DETR et DSIL : millésimes ; versions locales publiées après la date nationale
DT = SEL["DETR et DSIL"]
n128 = d(B["DETR et DSIL"]["date_nationale"])           # n° 128030, même date qu'en section 5
cD = [r for r in CLU["DETR et DSIL"]["m"] if r["niv"] == "locale"]   # famille de titres du script 32 (demandes de subvention)
dem = [r for r in DT if r["niv"] == "locale" and re.search(r"subvention", r["title"] or "", re.I) and not re.search(r"paiement|versement|fin de gestion|renouvellement", r["title"] or "", re.I)]
def apres(L): A_ = [r for r in L if d(r["datePublication"]) > n128]; return {"versions": len(A_), "departements": len({r["dep"] for r in A_ if r["dep"]}), "dossiers": nd(A_),
    "en_ligne_aujourdhui": sum(r["state"] == "publiee" for r in A_)}
out["detr"] = {"definition_section3": {"motif": UNI["DETR et DSIL"][0], "familles": "Dotations et subventions", "demarches": len(DT), "dossiers": nd(DT)},
    "date_nationale": str(n128),
    "famille_de_titres": {"versions_locales": len(cD), "avec_millesime_dans_le_titre": sum(1 for r in cD if re.search(r"20[12]\d", r["title"] or "")),
                          "publiees_apres_la_nationale": apres(cD)},
    "demandes_de_subvention_mots_du_titre": {"versions_locales": len(dem), "avec_millesime_dans_le_titre": sum(1 for r in dem if re.search(r"20[12]\d", r["title"] or "")),
                          "publiees_apres_la_nationale": apres(dem)},
    "trame_dgcl_2023": {"date": B["DETR et DSIL"]["premiere_version_nationale_toutes"]["date_nationale"],
                        "versions_locales_au_titre_identique_publiees_apres": sum(1 for r in cD if na(r["title"]).strip().startswith("demande de subvention au titre de la detr et de la dsil") and d(r["datePublication"]) > d(B["DETR et DSIL"]["premiere_version_nationale_toutes"]["date_nationale"]))}}
BR37 = json.load(open("out/interieur_briques.json"))["dotations_detr_dsil"]
out["detr"]["definition_section6_script37"] = {"motif": "DETR|DSIL|DSID|DPV|dotation d'équipement|dotation de soutien, toutes familles", "demarches": BR37["demarches"], "dossiers": BR37["dossiers"]}
# (4) police et gendarmerie : base du script 36 (zone déclarée, depuis le 7 octobre 2022) pour l'incise
json.dump(out, open("out/interieur_variete.json", "w"), ensure_ascii=False, indent=1, default=str)
print(json.dumps(out, ensure_ascii=False, indent=1, default=str))
