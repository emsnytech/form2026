"""Génère la fiche Justice. Reprend le style et les fonctions graphiques du gabarit de la fiche n° 1, sans le dupliquer.
Usage (depuis fiches-ministeres) : python3 fiche/build_justice.py
Entrées : out/justice*.json, out/rdv_cdad_metabase.json, out/scan_rdv_cdad.jsonl, data/demarches_slim.jsonl, explorer.html de FORM 2026, volumétrie DILA.
Les chiffres de la base sont calculés ici. Les chiffres de sources externes sont consignés dans EXT avec leur source."""
import os
import json, re, csv, unicodedata, collections as C, datetime as dt

O = lambda n: json.load(open(f"out/{n}.json"))
E, F, R, X, U, I, H, B = O("justice"), O("justice_familles"), O("justice_reconductions"), O("justice_complements"), O("justice_usages"), O("justice_inventaire"), O("justice_hors_opendata"), O("justice_124249")
M = O("rdv_cdad_metabase")["cartes"]
GEO = json.load(open("fiche/carte_departements.json"))
ROWS = [json.loads(l) for l in open("data/demarches_slim.jsonl")]
EXPL = os.path.expanduser("~/Documents/form2026-site/explorer.html")
DILA_F = os.path.expanduser("~/Documents/cartographie/volumetrie DILA.tab.csv")

# Sources externes : valeur + source, pour vérification
EXT = {
 "gazette": {"source": "https://www.lagazettefrance.fr/article/lille-quand-les-robots-s-invitent-au-greffe-du-tribunal-judiciaire", "num": 100, "delai": 10, "flux": "20 000 à 25 000"},
 "bj_form": {"source": "https://demarche.numerique.gouv.fr/commencer/barobaj-2 (page et dossier_vide, 03/11/2026)", "pages": 71, "minutes": 62},
 "cnb": {"source": ["https://cnb.avocat.fr/actualite/siaj-les-justiciables-peuvent-deposer-et-suivre-leur-demande-d-aide-juridictionnelle-en-ligne (31/10/2025)", "https://cnb.avocat.fr/actualite/dematerialisation-de-l-aide-juridique-trois-outils-pour-une-chaine-numerique-complete (17/11/2025)", "https://cnb.avocat.fr/actualite/mutualisation-des-bureaux-d-aide-juridictionnelle-quelle-place-pour-la-proximite-dans-l-acces-au-droit (15/09/2026)"]},
 "stats_plateforme": {"source": "https://demarche.numerique.gouv.fr/stats, relevé du 24/10/2026 (form2026-site/instances-ds.html)", "dossiers": 22679986},
}

def n(x): return f"{x:,}".replace(",", " ")
def p(x, d=1): return f"{x:.{d}f}".replace(".", ",")
MOIS = "janvier février mars avril mai juin juillet août septembre octobre novembre décembre".split()
def dfr(s):
    a = dt.date.fromisoformat(s[:10]); return f"{a.day}{'er' if a.day == 1 else ''} {MOIS[a.month - 1]} {a.year}"

y0, y1 = E["config"]["annee_debut"], E["config"]["annee_fin"]; YEARS = list(range(y0, y1 + 1))
A = {a["annee"]: a for a in E["annees"]}; P = {a["annee"]: a for a in E["annees_plateforme"]}
RC = {a["annee"]: a for a in R["perimetre"]}; D = {a["annee"]: a for a in E["diffusion"]}
ST = U["_stock"]; DA = X["dossiers_annuels"]; GA = X["gains"]; C_ = E["concentration_fenetre"]
HD = H["demarches"]; bj = next(x for x in HD if x["numero"] == 124249); tpe = next(x for x in HD if x["numero"] != 124249)
bj_dep = bj["avancee"]["Déposés"]; hors_d = sum(x["avancee"]["Déposés"] for x in HD); hors_n = len(HD)
od_total, od_dos = E["perimetre"]["total"], E["perimetre"]["dossiers_total"]
total, dossiers = od_total + hors_n, od_dos + hors_d
od_plat, od_plat_d = len(ROWS), sum(r["dossiersCount"] or 0 for r in ROWS)
assert total == 394, total
T = U["_total"]; rh = T["rh_formation"]; US = "Usagers, justiciables, professionnels du droit"
us_n, us_d = U[US]["demarches"] + hors_n, U[US]["dossiers"] + hors_d
EM = {e["type"]: e for e in I["emetteurs_par_type"]}
DSJ = EM["Direction des services judiciaires (RH des greffes)"]; JUR = EM["Juridictions"]; AC = EM["Administration centrale (secrétariat général, cabinet, directions)"]; ECO = EM["Écoles (ENM, ENG)"]
by = {r["number"]: r for r in ROWS}; c64 = by[64697]; I_c = I["contact"]; na = by[99859]
jur_noms = {re.sub(r",.*", "", x[0]).strip().lower() for x in JUR["detail"]}; jur_n = len(jur_noms)
fam = {f["famille"]: f for f in F}; LA = fam["Listes d'aptitude : une fiche de candidature par ressort"]
ptm = fam["Classe prépa Talents, École nationale de la magistrature"]; ptg = fam["Classe prépa Talents, École nationale des greffes"]
camp = dict(U["_LA"]["ressorts_par_campagne"])
rec_ext = U["_recrutement_detail"]["externe_ou_ouvert"]
PUB_LA = [ST[str(y)]["pub_LA"] for y in YEARS]; PUB_A = [ST[str(y)]["pub"] - ST[str(y)]["pub_LA"] for y in YEARS]

# ---------- RDV ----------
def card(tab, name, ncol=None):
    L = [c for c in M if c["onglet"].strip() == tab and c["carte"] == name]
    return (L[0] if ncol is None else [c for c in L if len(c["colonnes"]) == ncol][0])["lignes"]
TS_, TP_ = "Déploiement - RDV S", "Déploiement - RDV SP"
def norm(t):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    t = re.sub(r"cdad\s*(de la |de l'|des |de |du )?", "", t); return re.sub(r"[^a-z]+", "-", t).strip("-")
def propre(t): return re.sub(r"^CDAD\s*(de la |de l'|des |de |du )?", "", t, flags=re.I).replace("Et-Loir", "et-Loir").replace("Seine Saint-Denis", "Seine-Saint-Denis").replace("Seine et Marne", "Seine-et-Marne").replace("Seine-Et-Marne", "Seine-et-Marne")
TS, TP, NOM = C.Counter(), C.Counter(), {}
for a, v in card(TS_, "Nombre RDV CDAD par territoire"): TS[norm(a)] += v; NOM[norm(a)] = propre(a)
for a, v in card(TP_, "Nombre RDV CDAD par territoire - RDVSP", 2): TP[norm(a)] += v; NOM[norm(a)] = propre(a)
assert not set(TS) & set(TP)
ALLT = TS + TP; rdv_total, rdv_terr = sum(ALLT.values()), len(ALLT)
MS, MP = card(TS_, "Nombre RDV CDAD par territoire - Duplicate"), card(TP_, "Nombre RDV CDAD par territoire - RDVSP", 3)
YS, YP, AS, AP, first = C.Counter(), C.Counter(), C.defaultdict(set), C.defaultdict(set), {"S": {}, "P": {}}
for k, Mx, Yx, Ax in (("S", MS, YS, AS), ("P", MP, YP, AP)):
    for a, m, v in Mx:
        Yx[m[:4]] += v; Ax[m[:7]].add(norm(a)); first[k][norm(a)] = min(first[k].get(norm(a), "9999"), m[:7])
newp = C.Counter(v[:4] for v in first["P"].values())
sv = dict(card(TS_, "Nombre RDV CDAD par services", None) if False else [(a, v) for a, v in card(TS_, "Nombre RDV CDAD par services")])
stat = dict(card(TS_, "Nombre RDV CDAD - par service"))
slug = lambda s: norm(s)
cdad_org = C.defaultdict(lambda: [0, 0])
for r in ROWS:
    m = re.search(r"CDAD\s+(?:de la |de l'|de |du )?([A-Za-zéèÉ-]+)", r["organisme"] or "")
    if m and r["number"] in {x for x in [98320, 144377, 144606, 128159]}: k = norm(m.group(1)); cdad_org[k][0] += 1; cdad_org[k][1] += r["dossiersCount"] or 0
assert set(cdad_org) == {"moselle", "eure"}, dict(cdad_org)
SCAN = [json.loads(l) for l in open("out/scan_rdv_cdad.jsonl")]
RS = [h for h in SCAN if h["rdvsp"]]
lien = [h for h in RS if any(re.search(r"rdv\.anct\.gouv\.fr", x["extrait"], re.I) for x in h["rdvsp"]) and not re.search("webinaire|AMI ", h["title"], re.I)]
assert not [h for h in lien if "Ministère de la Justice" in (h["zones"] or []) or re.search("CDAD", h["organisme"] or "")]

# ---------- sources FORM ----------
html_x = open(EXPL, encoding="utf-8").read()
SJ = lambda i: json.loads(re.search(r'<script type="application/json" id="' + i + r'">(.*?)</script>', html_x, re.S).group(1))
CE, ES = SJ("data-cerfa"), SJ("data-essentielles")
aj = next(e for e in ES if e["id_observatoire"] == 1747)
dila_t = open(DILA_F, errors="ignore").read()
# Téléchargements sur un an à fin 2024 : référence unique du site, somme des versions du Cerfa.
_RID_CERFA = {"R1444": "16146", "R18606": "12821", "R1408": "11808", "R15764": "11530", "R45128": "15586"}
_TELECH = list(csv.DictReader(open(os.path.expanduser("~/Documents/form2026-site/donnees/gains/telechargements_dila.csv"), encoding="utf-8")))
def vol(rid): return sum(int(r["telechargements"]) for r in _TELECH if r["numero"] == _RID_CERFA[rid])
for x in I["cerfa_justice"]: pass

def meur(x): return p(x / 1e6, 2)
ds = U["_duree"]; K = {
 "date": "21 octobre 2026", "releve": dfr(H["releve"]), "y0": y0, "y1": y1,
 "total": n(total), "od_total": n(od_total), "hors_n": hors_n, "dossiers": n(dossiers), "od_dos": n(od_dos),
 "part_dem": p(100 * total / (od_plat + hors_n), 2), "part_dos": p(100 * dossiers / (od_plat_d + hors_d), 2),
 "rh": n(rh), "rh_pct": p(100 * rh / total), "dsj_pct": p(100 * DSJ["demarches"] / total, 0), "dsj_n": n(DSJ["demarches"]),
 "us_n": us_n, "us_pct": p(100 * us_d / dossiers), "us_top2_pct": p(100 * (c64["dossiersCount"] + bj_dep) / us_d, 0),
 "contact_d": n(c64["dossiersCount"]), "contact_pct": p(100 * c64["dossiersCount"] / dossiers), "contact_pct_od": p(100 * c64["dossiersCount"] / od_dos),
 "contact_num": 64697, "contact_t": c64["title"], "contact_date": dfr(c64["datePublication"]), "contact_champs": c64["n_champs"], "contact_saisie": I_c["champs_saisie"], "contact_url": c64["url"], "contact_an": n(int(round(I_c["par_an"], -1))),
 "jur_n": jur_n, "la_n": n(LA["demarches"]), "la_camp": len(camp), "la_d": n(LA["dossiers"]), "la_min": LA["champs_min"], "la_max": LA["champs_max"],
 "la_2024": PUB_LA[3], "la_2025": PUB_LA[4], "la_2026": PUB_LA[5], "autres_y0": PUB_A[0], "autres_y1": PUB_A[-1],
 "duree_med": ds["mediane_jours"], "duree_92": ds["moins_92j"], "duree_n": ds["closes"],
 "stock_2024": ST["2024"]["stock"], "la_ouvertes_2024": ST["2024"]["stock"] - ST["2024"]["stock_hors_LA"], "stock_y0": ST[str(y0)]["stock_hors_LA"], "stock_y1": ST[str(y1)]["stock_hors_LA"],
 "calmin": p(100 / max(a["calage"] for a in DA), 0), "calmax": p(100 / min(a["calage"] for a in DA), 0),
 "g_bas": meur(GA["bas"]), "g_haut": meur(GA["haut"]), "ga_bas": meur(GA["admin_bas"]), "ga_haut": meur(GA["admin_haut"]), "gu_bas": meur(GA["usagers_bas"]), "gu_haut": meur(GA["usagers_haut"]),
 "g_couv": p(100 * X["gains_couverture"]["dossiers_couverts"] / X["gains_couverture"]["dossiers_fenetre"]),
 "zone_brut": I["perimetre"]["zone_justice_brute"], "zone_brut_d": n(I["perimetre"]["dossiers_zone_brute"]),
 "inter": I["perimetre"]["exclues_plus_3_zones"], "inter_d": n(I["perimetre"]["dossiers_plus_3_zones"]), "inter_srias": I["perimetre"]["plus_3_zones_srias"],
 "excl_n": len(E["anomalies_exclues"]), "ccapex_d": n(by[76720]["dossiersCount"]), "sans_zone": E["perimetre"]["par_source"]["nom_organisme"], "incl_n": E["perimetre"]["par_source"]["inclusion"],
 "stats_dos": n(EXT["stats_plateforme"]["dossiers"]), "od_plat_d": n(od_plat_d), "ecart_pct": p(100 * (EXT["stats_plateforme"]["dossiers"] - od_plat_d) / EXT["stats_plateforme"]["dossiers"], 0), "od_plat": n(od_plat),
 "siret_n": I["perimetre"]["siret"], "siret_manquant": E["siret_manquant"],
 "deps": len(X["carte"]), "paris_n": X["carte"]["75"]["pub_t"], "paris_base": sum(v["pub_t"] for v in X["carte"].values()), "sansdep": X["carte_sans_departement"],
 "rec_ext_n": rec_ext[0], "rec_ext_d": n(rec_ext[1]), "ptm_min": ptm["champs_min"], "ptm_max": ptm["champs_max"], "ptg_min": ptg["champs_min"], "ptg_max": ptg["champs_max"],
 "fen": n(C_["demarches"]), "mediane": C_["mediane_dossiers"], "lt10": C_["demarches_moins_10_dossiers"],
 "bj_num": bj["numero"], "bj_t": bj["titre"], "bj_debut": bj["delai_moyen_par_mois"][0][0], "bj_dep": n(bj_dep), "bj_trait": n(bj["avancee"]["Traités"]), "bj_pages": EXT["bj_form"]["pages"], "bj_min": EXT["bj_form"]["minutes"], "bj_url": "https://demarche.numerique.gouv.fr/commencer/barobaj-2",
 "ga_num": EXT["gazette"]["num"], "ga_delai": EXT["gazette"]["delai"], "ga_flux": EXT["gazette"]["flux"],
 "bj_an": n(int(round(bj_dep / len(bj["delai_moyen_par_mois"]) * 12, -2))), "bj_d_nov": dict(bj["delai_moyen_par_mois"])["novembre 2025"], "bj_d_max": max(v for _, v in bj["delai_moyen_par_mois"]), "bj_d_oct": dict(bj["delai_moyen_par_mois"])["octobre 2026"],
 "cph_d": sum(by[x]["dossiersCount"] for x in (116592, 130561)),
 "rdv_total": n(rdv_total), "rdv_terr": rdv_terr, "rdv_dn": len(cdad_org), "rdv_ge100": sum(v >= 100 for v in ALLT.values()), "rdv_lt100": sum(v < 100 for v in ALLT.values()),
 "act_2411": len(AS["2024-11"] | AP["2024-11"]), "act_2610": len(AS["2026-10"] | AP["2026-10"]), "new_p_2025": newp["2025"], "new_p_2026": newp["2026"],
 "mos_r": n(ALLT["moselle"]), "mos_n": cdad_org["moselle"][0], "mos_d": cdad_org["moselle"][1], "eur_r": n(ALLT["eure"]), "eur_n": cdad_org["eure"][0], "eur_d": cdad_org["eure"][1],
 "st_seen": n(stat["seen"]), "st_unknown": n(stat["unknown"]), "st_excused": n(stat["excused"]), "st_noshow": n(stat["noshow"]), "st_revoked": n(stat["revoked"]),
 "tot_card": n(card(TS_, "Nombre RDV CDAD")[0][0]), "tot_terr": n(sum(TS.values())), "tot_stat": n(sum(stat.values())),
 "sv_av": n(sv["Avocat"]), "sv_co": n(sv["Conciliateur de Justice"]), "sv_ci": n(sv["CIDFF"]), "ag_sp": n(card(TP_, "Nombre agent CDAD - RDV SP")[0][0]),
 "pref_nord_d": n(by[97152]["dossiersCount"]), "siren_n": len(O("justice_siren_cours_appel")), "lien_n": len(lien), "lien_pct": p(100 * len(lien) / od_plat, 2),
 "champs_2023": p(A[2023]["champs_moyens"]), "champs_2025": p(A[2025]["champs_moyens"]), "champs_y1": p(A[y1]["champs_moyens"]), "champsp_y1": p(P[y1]["champs_moyens"]),
 "pj_total": n(I["pj_labels"]["pj_total"]), "pj_id": I["pj_labels"]["identite"]["demarches"], "pj_rib": I["pj_labels"]["rib"]["demarches"], "pj_dip": I["pj_labels"]["diplome"]["demarches"],
 "rib_double": I["rib"]["pj_rib_et_iban"], "ass_n": I["partenaires_associatifs"]["demarches"], "part_y1": p(A[y1]["pct_particuliers"], 0),
 "aj_vol": n(int(aj["volumetrie_totale"])), "aj_pct": p(100 * aj["pct_recours_numerique"]),
 "na_d": n(na["dossiersCount"]), "na_c": na["n_champs"], "na_ferm": dfr(na["dateFermeture"]),
 "cerfa_total": len(CE), "cerfa_just": len(I["cerfa_justice"]), "avis_n": len(I["pj_avis"]), "avis_d": n(I["pj_labels"]["avis_imposition"]["dossiers"]),
}
assert I["partenaires_associatifs"]["avec_rna_rnf"] == 0 and sum(a["nb_api_particulier"] for a in E["annees"]) == 0

MOTIFS = {156923: "Démarche de test", 56695: "Démarche de test (« Cour d'appel de X »)", 76720: "Prévention des expulsions, service de l'État hors périmètre", 152981: "Démarche de test", 132277: "Organisme non identifiable"}
TEST = {156923: ("Démarche de test", "Libellé technique de test")}
def scrub(s):
    s = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[adresse électronique retirée]", str(s or ""))
    return re.sub(r"(?<!\d)(?:\+33\s?|0)[1-9](?:[\s.\-]?\d{2}){4}(?!\d)", "[numéro de téléphone retiré]", s)
def nom_em(x):
    if re.search(r"magistrature|\bENM\b", x, re.I): return "École nationale de la magistrature"
    if re.search(r"greffes|^ENG$", x, re.I) and not x.startswith("Direction"): return "École nationale des greffes"
    if "garde des sceaux" in x: return "Secrétariat général et cabinet"
    return re.sub(r"\s*,.*| - Sous-direction.*", "", x).strip()
ORD = ["Direction des services judiciaires (RH des greffes)", "Écoles (ENM, ENG)", "Administration centrale (secrétariat général, cabinet, directions)", "Juridictions", "Administration pénitentiaire : directions interrégionales, SPIP, établissements", "Conseils départementaux de l'accès au droit (GIP)"]
DETAIL = {ORD[0]: "Bureau des carrières et de la mobilité ; bureau des recrutements et de la formation", ORD[1]: "École nationale de la magistrature ; École nationale des greffes", ORD[2]: "Secrétariat général et cabinet ; service des ressources humaines ; directions", ORD[3]: "Tribunaux judiciaires de Lille, du Mans, d'Orléans, de Saumur ; conseil de prud'hommes de Lille. Comprend les 2 démarches hors open data", ORD[4]: "Directions interrégionales ; SPIP du Loiret ; centre de détention de Melun", ORD[5]: "CDAD de la Moselle ; CDAD de l'Eure"}
def emrow(t):
    e = EM[t]; a = hors_n if t == "Juridictions" else 0; b = hors_d if t == "Juridictions" else 0
    return {"type": t, "n": e["demarches"] + a, "pct": 100 * (e["demarches"] + a) / total, "d": e["dossiers"] + b, "siret": e["siret"], "detail": DETAIL[t]}
assert sum(EM[t]["demarches"] for t in ORD) == od_total
NAT = [("Recrutement : concours, examens, prise en charge"), ("Promotion interne : listes d'aptitude"), ("Formation : écoles, classes prépa, bourses"), ("Gestion RH : paie, indemnités, jurys, carrière")]
nature = [{"nom": a, "n": U[a]["demarches"], "d": U[a]["dossiers"], "pct": 100 * U[a]["dossiers"] / dossiers, "ligne": U[a]["en_ligne"]} for a in NAT]
nature.append({"nom": US + " (dont 2 hors open data)", "n": us_n, "d": us_d, "pct": 100 * us_d / dossiers, "ligne": U[US]["en_ligne"] + 1})
for a in ("Partenaires et événements", "Fonctionnement interne des services"): nature.append({"nom": a, "n": U[a]["demarches"], "d": U[a]["dossiers"], "pct": 100 * U[a]["dossiers"] / dossiers, "ligne": U[a]["en_ligne"]})
assert sum(x["n"] for x in nature) == total and sum(x["d"] for x in nature) == dossiers

SENS = [100049, 123573, 147656]; sens_d = sum(by[x]["dossiersCount"] for x in SENS) + tpe["avancee"]["Déposés"]
us_rows = [("Question au ministère de la Justice", "Secrétariat général", "En ligne", c64["dossiersCount"]), ("BARÔBAJ Version 2.0 (hors open data)", "Tribunal judiciaire de Lille", "En ligne", bj_dep),
 ("Certificat de non-appel et copie de jugement", "Tribunal judiciaire de Lille", "Close", na["dossiersCount"]), ("Casier judiciaire, suivi de plaintes, mineurs : 4 démarches agrégées, dont 1 hors open data", "Juridictions et ministère", "Mixte", sens_d),
 ("Prestation de serment", "Tribunal judiciaire de Lille", "Close", by[100409]["dossiersCount"]), ("Restitution de titre d'identité", "Tribunal judiciaire de Lille", "Close", by[100526]["dossiersCount"]), ("BAROCPH, 2 versions", "Conseil de prud'hommes de Lille", "1 en ligne, 1 close", K["cph_d"])]
assert sum(x[3] for x in us_rows) == us_d, (sum(x[3] for x in us_rows), us_d)

tops = [{"num": t["number"], "t": scrub(t["title"]), "o": nom_em(t["organisme"] or ""), "y": t["datePublication"][:4] + (" · close" if t["state"] == "close" else ""), "c": t["n_champs"], "d": t["dossiersCount"]} for t in E["top_demarches_fenetre"][:11]]
tops.append({"num": bj["numero"], "t": bj["titre"] + " (hors open data)", "o": "Tribunal judiciaire de Lille", "y": "2025", "c": None, "d": bj_dep}); tops.sort(key=lambda x: -x["d"])
assert not [t for t in tops if t["num"] in SENS]
top_terr = [{"nom": NOM[k], "inst": "RDV Solidarités" if k in TS else "RDV Service Public", "r": v, "n": cdad_org[k][0] if k in cdad_org else 0, "d": cdad_org[k][1] if k in cdad_org else 0} for k, v in ALLT.most_common(12)]
DATA = {
 "years": YEARS, "pub_la": PUB_LA, "pub_autres": PUB_A, "pub_new": [RC[y]["nouvelles"] for y in YEARS], "pub_rec": [RC[y]["reconductions"] for y in YEARS],
 "closes": [A[y]["closes"] for y in YEARS], "stock": [A[y]["stock_fin_annee"] for y in YEARS], "stock_autres": [ST[str(y)]["stock_hors_LA"] for y in YEARS], "actives": [A[y]["actives_dans_annee"] for y in YEARS],
 "part_pub": [round(100 * A[y]["publiees"] / P[y]["publiees"], 1) for y in YEARS], "part_stock": [round(100 * A[y]["stock_fin_annee"] / P[y]["stock_fin_annee"], 1) for y in YEARS],
 "dossiers": DA, "gains_annee": [X["gains_par_annee"][str(y)] for y in YEARS], "carte": X["carte"], "geo": GEO,
 "emetteurs": [emrow(t) for t in ORD], "diff": [{"siret": D[y]["siret_emetteurs_actifs"], "dep": D[y]["departements_actifs"], "lib": D[y]["emetteurs_actifs"]} for y in YEARS],
 "nature": nature, "familles": [{"nom": f["famille"], "n": f["demarches"], "s": f["siret_distincts"], "d": f["dossiers"], "min": f["champs_min"], "max": f["champs_max"], "moy": f["champs_moyens"], "pj": f["pj_moyennes"]} for f in sorted(F, key=lambda f: -f["demarches"])],
 "top": tops, "usagers": [{"t": a, "o": b, "e": c, "d": d, "pct": 100 * d / us_d} for a, b, c, d in us_rows],
 "rdv": {"years": ["2024", "2025", "2026*"], "s": [YS["2024"], YS["2025"], YS["2026"]], "p": [YP["2024"], YP["2025"], YP["2026"]], "top": top_terr,
   "actifs": [{"m": f"{MOIS[int(m[5:]) - 1]} {m[:4]}", "s": len(AS[m]), "p": len(AP[m]), "t": len(AS[m] | AP[m])} for m in ("2024-11", "2025-06", "2026-01", "2026-07", "2026-10")]},
 "qual": [{"champs": A[y]["champs_moyens"], "champs_p": P[y]["champs_moyens"], "pj": A[y]["pj_moyennes"], "pj_p": P[y]["pj_moyennes"], "siret": A[y]["pct_siret"], "iban": A[y]["pct_iban"], "rna": A[y]["pct_rna"], "apip": A[y]["nb_api_particulier"], "eph": A[y]["ephemeres_moins_3_mois"]} for y in YEARS],
 "papier": [
  {"t": "Aide juridictionnelle (Cerfa 16146)", "url": "https://www.service-public.gouv.fr/particuliers/vosdroits/F18074", "s": "En ligne ailleurs, papier dans certains cas", "o": "Surtout organisationnel : système non ouvert aux avocats, déploiement en cours vers les juridictions administratives", "v": vol("R1444")},
  {"t": "Certificat de non-appel (Cerfa 12821)", "url": "https://www.service-public.gouv.fr/particuliers/vosdroits/R18606", "s": "Papier national ; version locale close ; statut en ligne non établi", "o": "Organisationnel d'après l'exemple de Lille, sans conclusion générale", "v": vol("R18606")},
  {"t": "Copie de décision de justice (Cerfa 11808)", "url": "https://www.service-public.gouv.fr/particuliers/vosdroits/R1408", "s": "Papier national ; version locale close", "o": "Organisationnel d'après l'exemple de Lille, sans conclusion générale", "v": vol("R1408")},
  {"t": "Demande au juge aux affaires familiales (Cerfa 11530)", "url": "https://www.service-public.gouv.fr/particuliers/vosdroits/R15764", "s": "Papier national", "o": "Juridique : saisine d'un juge", "v": vol("R15764")},
  {"t": "Requête devant le conseil de prud'hommes (Cerfa 15586)", "url": "https://www.service-public.gouv.fr/particuliers/vosdroits/R45128", "s": "Papier national ; dépôt par avocat sur la plateforme à Lille (BAROCPH)", "o": "Juridique : saisine d'une juridiction", "v": vol("R45128")}],
 "avis": [{"n": a["n"], "t": scrub(by[a["n"]]["title"]), "o": nom_em(a["o"]), "y": a["y"], "d": a["d"]} for a in I["pj_avis"]],
 "anomalies": [{"n": a["n"], "t": TEST[a["n"]][0] if a["n"] in TEST else scrub(a["t"]), "o": TEST[a["n"]][1] if a["n"] in TEST else scrub(a["o"]), "z": a["z"], "d": a["d"], "m": MOTIFS.get(a["n"], "Zone mal déclarée : organisme hors périmètre")} for a in I["anomalies_exclues"]],
}
assert len(DATA["anomalies"]) == K["excl_n"]

ref = open("fiche/gabarit_fiche.html", encoding="utf-8").read()
css = re.search(r"<style>(.*?)</style>", ref, re.S).group(1)
js = ref[ref.index('const fr = new Intl'):ref.index('/* 1. Trajectoire */')]
mp = ref[ref.index('/* 4. Carte */'):ref.index('/* 7. Quotient familial */')]
h = open("fiche/gabarit_justice.html", encoding="utf-8").read()
h = h.replace("/*CSS_COMMUN*/", css).replace("/*JS_COMMUN*/", js).replace("/*JS_CARTE*/", mp).replace("/*DATA*/null", json.dumps(DATA, ensure_ascii=False).replace("</", "<\\/"))
miss = set(re.findall(r"«(\w+)»", h)) - set(map(str, K))
if miss: raise SystemExit(f"marqueurs sans valeur : {miss}")
h = re.sub(r"«(\w+)»", lambda m: str(K[m.group(1)]), h)
assert not re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}", h), "adresse électronique dans la page"
# La fiche doit s'afficher correctement ouverte en local, sans en-tête de serveur.
TETE = '<!DOCTYPE html>\n<html lang="fr">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
open("fiche/fiche-justice.html", "w", encoding="utf-8").write(TETE + h)
json.dump({"K": K, "EXT": EXT}, open("out/justice_chiffres_fiche.json", "w"), ensure_ascii=False, indent=0, default=str)
print("ok fiche/fiche-justice.html", len(h)); print({k: K[k] for k in ("total", "dossiers", "rh", "rh_pct", "dsj_pct", "us_n", "us_pct", "us_top2_pct", "contact_pct", "jur_n", "rdv_total", "rdv_terr", "act_2411", "act_2610", "bj_an", "contact_an", "lien_n", "lien_pct", "deps", "paris_n", "paris_base")})
