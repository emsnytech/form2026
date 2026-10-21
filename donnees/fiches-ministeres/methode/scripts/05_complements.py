"""Compléments de la fiche : dossiers estimés par année (prorata de la durée d'ouverture, calé sur les dépôts réels
de la plateforme), carte par département, gains (fichier FORM 2026 demarches_gains_v8.csv), démarches candidates au
quotient familial (API Particulier). Usage : python3 05_complements.py <config.json> <sortie.json>"""
import json, sys, re, csv, collections, datetime as dt
cfg_path, out_path = sys.argv[1], sys.argv[2]
sys.argv = ["x", cfg_path, "/dev/null"]
exec(open("scripts/02_fiche_ministere.py").read().split("APIP =")[0])
cfgc = cfg.get("complements", {})
ASOF_D = d(ASOF)

# ---------- 1. Prorata : répartit dossiersCount uniformément sur [publication, fin ou date d'extraction] ----------
def prorata(r):
    p = d(r["datePublication"]); f = fin(r) or ASOF_D
    if not p: return {}
    f = max(f, p); total = (f - p).days + 1; n = r["dossiersCount"] or 0; res = {}
    for y in range(p.year, f.year + 1):
        a = max(p, dt.date(y, 1, 1)); b = min(f, dt.date(y, 12, 31))
        res[y] = n * ((b - a).days + 1) / total
    return res

per = []
for r in rows:
    p, s = classify(r)
    if p and p != "interministeriel": r["pole"] = p; per.append(r)
for r in rows: r["_pr"] = prorata(r)

def by_year(sub):
    c = collections.Counter()
    for r in sub:
        for y, v in r["_pr"].items(): c[y] += v
    return c
est_per, est_plat = by_year(per), by_year(rows)
reel = collections.Counter()
for l in list(csv.reader(open("data/nb_dossiers_deposes_par_mois.csv"), delimiter=";"))[1:]:
    reel[int(l[0][:4])] += int(l[1])
calage = {}
for y in YEARS:
    # 2026 : le réel s'arrête fin septembre ; on compare à l'estimation ramenée à 9 mois
    est = est_plat[y] * (273 / 294 if y == 2026 else 1)
    calage[y] = round(reel[y] / est, 3) if est else None
dossiers_annuels = [{"annee": y, "estime_brut": round(est_per[y]), "plateforme_estime": round(est_plat[y]), "plateforme_reel": reel[y],
                     "calage": calage[y], "estime_cale": round(est_per[y] * (calage[y] or 1)),
                     "part_plateforme": round(100 * est_per[y] / est_plat[y], 1)} for y in YEARS]

# ---------- 2. Carte par département ----------
fen = [r for r in per if any(is_active(r, y) for y in YEARS)]
def org_key(r): return r["siret"] or re.sub(r"\s+", " ", (r["organisme"] or "").strip().lower())
dep = collections.defaultdict(lambda: {"pub": collections.Counter(), "org": collections.defaultdict(set), "dos": collections.Counter()})
sans_dep = 0
for r in fen:
    k = r["departement"]
    if not k: sans_dep += 1; continue
    D = dep[k]
    py = int(r["datePublication"][:4])
    if py in YEARS: D["pub"][py] += 1
    for y in YEARS:
        if is_active(r, y): D["org"][y].add(org_key(r))
        D["dos"][y] += r["_pr"].get(y, 0)
carte = {}
for k, D in dep.items():
    carte[k] = {"pub": [D["pub"][y] for y in YEARS], "org": [len(D["org"][y]) for y in YEARS],
                "dos": [round(D["dos"][y]) for y in YEARS],
                "pub_t": sum(D["pub"].values()), "org_t": len(set().union(*D["org"].values())) if D["org"] else 0,
                "dos_t": round(sum(D["dos"].values()))}

# ---------- 3. Gains (FORM 2026, v8) ----------
G = {}
for l in csv.DictReader(open(cfgc.get("gains", "data/demarches_gains_v8.csv"), encoding="utf-8")):
    G[int(l["demarche"])] = l
def f(x):
    try: return float(x)
    except: return 0.0
gain = {"bas": 0.0, "haut": 0.0, "admin_bas": 0.0, "admin_haut": 0.0, "usagers_bas": 0.0, "usagers_haut": 0.0}
gain_y = {y: {"bas": 0.0, "haut": 0.0} for y in YEARS}
couv = {"demarches": 0, "absentes": 0, "dossiers_couverts": 0.0, "dossiers_fenetre": 0.0}
for r in fen:
    dos_fen = sum(r["_pr"].get(y, 0) for y in YEARS); couv["dossiers_fenetre"] += dos_fen
    g = G.get(r["number"]); nd = f(g["nb_dossiers"]) if g else 0
    if not g or nd <= 0: couv["absentes"] += 1; continue
    couv["demarches"] += 1; couv["dossiers_couverts"] += dos_fen
    k = dos_fen / nd   # gain par dossier × dossiers de la fenêtre
    gain["bas"] += k * f(g["gain_total_bas"]); gain["haut"] += k * f(g["gain_total_haut"])
    gain["admin_bas"] += k * f(g["gain_admin_bas"]); gain["admin_haut"] += k * f(g["gain_admin_haut"])
    gain["usagers_bas"] += k * (f(g["gain_usagers_demat_bas"]) + f(g["gain_usagers_realise_v7_30"]))
    gain["usagers_haut"] += k * (f(g["gain_usagers_demat_haut"]) + f(g["gain_usagers_realise_v7_60"]))
    for y in YEARS:
        ky = r["_pr"].get(y, 0) / nd
        gain_y[y]["bas"] += ky * f(g["gain_total_bas"]); gain_y[y]["haut"] += ky * f(g["gain_total_haut"])
gain = {k: round(v) for k, v in gain.items()}
couv = {k: round(v) for k, v in couv.items()}

# ---------- 4. Candidates au quotient familial ----------
QF_RX = re.compile(cfgc.get("motif_qf", r"demi-pension|restauration scolaire|cantine|internat|bourses?\b|fonds sociaux|fonds social|aides? sociales?"), re.I)
QF_PLAT = re.compile(r"demi-pension|restauration scolaire|cantine|p[ée]riscolaire|accueil de loisirs|centre de loisirs|cr[èe]che|multi-accueil|quotient familial|bourses? (de coll[èe]ge|de lyc[ée]e|scolaire|nationale)|fonds social|tarif(ication)? (sociale|solidaire)", re.I)
def has_qf(r): return r["champs_types"].get("QuotientFamilialChampDescriptor", 0) > 0
def niveau(r):
    g = G.get(r["number"]); return g["niveau_brut"] if g else None
def item(r): return {"num": r["number"], "t": r["title"], "o": r["organisme"], "d": r["dossiersCount"] or 0, "c": r["n_champs"],
                     "y": r["datePublication"][:4], "etat": r["state"], "url": r["url"], "qf": has_qf(r), "niv": niveau(r),
                     "pp": 100 if r["forIndividual"] else 0}
cand = [r for r in fen if (r["datePublication"] or "0")[:4] >= str(YEARS[0]) and QF_RX.search(r["title"] or "")]
pset = {r["number"] for r in per}
DETENTEURS = re.compile(r"\bCAF\b|caisse d.allocations familiales|\bMSA\b|mutualit[ée] sociale agricole", re.I)  # détiennent déjà le QF
plat = [r for r in rows if r["number"] not in pset and not DETENTEURS.search(r["organisme"] or "") and (r["datePublication"] or "0")[:4] >= str(YEARS[0]) and QF_PLAT.search(r["title"] or "")]
qf = {"perimetre": sorted([item(r) for r in cand], key=lambda x: -x["d"]),
      "plateforme_hors_perimetre": {"demarches": len(plat), "dossiers": sum(r["dossiersCount"] or 0 for r in plat),
          "emetteurs": len({org_key(r) for r in plat}), "avec_qf": sum(has_qf(r) for r in plat),
          "par_type": dict(collections.Counter(r["typeOrganisme"] or "nr" for r in plat)),
          "top": [item(r) for r in sorted(plat, key=lambda r: -(r["dossiersCount"] or 0))[:15]]},
      "qf_plateforme_total": sum(has_qf(r) for r in rows)}

json.dump({"dossiers_annuels": dossiers_annuels, "carte": carte, "carte_sans_departement": sans_dep,
           "gains": gain, "gains_par_annee": {str(y): {k: round(v) for k, v in g.items()} for y, g in gain_y.items()},
           "gains_couverture": couv, "quotient_familial": qf}, open(out_path, "w"), ensure_ascii=False, indent=1)
print(json.dumps(dossiers_annuels, ensure_ascii=False))
print("gains", gain, couv)
print("sans dep", sans_dep, "deps", len(carte))
print("qf perim", len(qf["perimetre"]), sum(x["d"] for x in qf["perimetre"]), "plat", {k: v for k, v in qf["plateforme_hors_perimetre"].items() if k != "top"}, qf["qf_plateforme_total"])
