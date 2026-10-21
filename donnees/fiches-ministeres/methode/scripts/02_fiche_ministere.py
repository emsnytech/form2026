"""Indicateurs d'une fiche ministérielle à partir de data/demarches_slim.jsonl.
Usage : python3 02_fiche_ministere.py <config.json> <sortie.json>
La config définit les zones (pôles), le motif de rattachement des démarches sans zone, la période."""
import json, sys, re, collections, datetime as dt
cfg = json.load(open(sys.argv[1]))
rows = [json.loads(l) for l in open(cfg["source"])]
ASOF = cfg["date_extraction"]
YEARS = list(range(cfg["annee_debut"], cfg["annee_fin"] + 1))
ZONES = cfg["zones"]                     # libellé de zone -> pôle
PRIO = cfg["priorite_poles"]             # ordre de priorité si plusieurs pôles
MAXZ = cfg["max_zones"]                  # au-delà : démarche interministérielle, exclue
SANSZ = {k: re.compile(v, re.I) for k, v in cfg["sans_zone_motifs"].items()}  # pôle -> motif
EXCL = re.compile(cfg["sans_zone_exclusions"], re.I)
EXCL_ALL = re.compile(cfg.get("exclusions_toutes", "$^"), re.I)
TYPES_EXCL = set(cfg.get("sans_zone_types_exclus", []))
ANOMALIES = []

def d(s): return dt.date.fromisoformat(s[:10]) if s else None
def fin(r): return d(r["dateFermeture"]) or d(r["dateDepublication"])

def classify(r):
    p, s = _classify(r)
    if p and p != "interministeriel" and EXCL_ALL.search((r["organisme"] or "").strip()):
        ANOMALIES.append(r); return None, None
    return p, s

def _classify(r):
    z = r["zones"] or []
    poles = {ZONES[x] for x in z if x in ZONES}
    if z:
        if not poles: return None, None
        if len(z) > MAXZ: return "interministeriel", "zone"
        for p in PRIO:
            if p in poles: return p, ("zone" if len(poles) == 1 else "zone_multi")
    o = (r["organisme"] or "") + " | " + (r["service_nom"] or "")
    if EXCL.search(o) or r["typeOrganisme"] in TYPES_EXCL: return None, None
    for p in PRIO:
        if SANSZ[p].search(o): return p, "nom_organisme"
    return None, None

def is_active(r, y):
    p, f = d(r["datePublication"]), fin(r)
    return p and p <= dt.date(y, 12, 31) and (f is None or f >= dt.date(y, 1, 1))

def stock(r, y):
    p, f = d(r["datePublication"]), fin(r)
    end = min(dt.date(y, 12, 31), d(ASOF))
    return p and p <= end and (f is None or f > end)

APIP = ("QuotientFamilialChampDescriptor", "EtudiantBoursierChampDescriptor")
def has(r, t): return r["champs_types"].get(t, 0) > 0

per, excl_inter = [], []
src = collections.Counter()
for r in rows:
    p, s = classify(r)
    if p == "interministeriel": excl_inter.append(r); continue
    if p: r["pole"], r["src"] = p, s; per.append(r); src[s] += 1

def year_block(sub, y, allrows=None):
    pub = [r for r in sub if (r["datePublication"] or "")[:4] == str(y)]
    clo = [r for r in sub if fin(r) and fin(r).year == y]
    act = [r for r in sub if is_active(r, y)]
    stk = [r for r in sub if stock(r, y)]
    closed_pub = [r for r in pub if fin(r)]
    eph = [r for r in closed_pub if (fin(r) - d(r["datePublication"])).days < 92]
    n = len(pub) or 1
    return {
        "annee": y, "publiees": len(pub), "closes": len(clo), "actives_dans_annee": len(act),
        "stock_fin_annee": len(stk),
        "dossiers_cohorte": sum(r["dossiersCount"] or 0 for r in pub),
        "ephemeres_moins_3_mois": len(eph),
        "pct_particuliers": round(100 * sum(1 for r in pub if r["forIndividual"]) / n, 1),
        "champs_moyens": round(sum(r["n_champs"] for r in pub) / n, 1),
        "pj_moyennes": round(sum(r["champs_types"].get("PieceJustificativeChampDescriptor", 0) for r in pub) / n, 2),
        "pct_siret": round(100 * sum(has(r, "SiretChampDescriptor") for r in pub) / n, 1),
        "pct_annuaire_education": round(100 * sum(has(r, "AnnuaireEducationChampDescriptor") for r in pub) / n, 1),
        "pct_iban": round(100 * sum(has(r, "IbanChampDescriptor") for r in pub) / n, 1),
        "pct_rna": round(100 * sum(has(r, "RNAChampDescriptor") for r in pub) / n, 1),
        "nb_api_particulier": sum(any(has(r, t) for t in APIP) for r in pub),
        "pct_dossier_lie": round(100 * sum(has(r, "DossierLinkChampDescriptor") for r in pub) / n, 1),
        "type_organisme": dict(collections.Counter(r["typeOrganisme"] or "non renseigné" for r in pub)),
        "par_pole": dict(collections.Counter(r.get("pole") for r in pub)) if pub and "pole" in pub[0] else None,
        "par_source": dict(collections.Counter(r.get("src") for r in pub)) if pub and "src" in pub[0] else None,
    }

out = {"config": cfg, "perimetre": {"total": len(per), "par_source": dict(src),
        "par_pole": dict(collections.Counter(r["pole"] for r in per)),
        "exclues_interministerielles": len(excl_inter),
        "etats": dict(collections.Counter(r["state"] for r in per)),
        "dossiers_total": sum(r["dossiersCount"] or 0 for r in per)},
       "plateforme": {"total": len(rows), "dossiers_total": sum(r["dossiersCount"] or 0 for r in rows)}}
out["annees"] = [year_block(per, y) for y in YEARS]
out["annees_plateforme"] = [{k: v for k, v in year_block(rows, y).items() if k in ("annee","publiees","closes","actives_dans_annee","stock_fin_annee","dossiers_cohorte","champs_moyens","pj_moyennes","pct_particuliers","ephemeres_moins_3_mois")} for y in YEARS]
out["annees_par_pole"] = {p: [{k: v for k, v in year_block([r for r in per if r["pole"] == p], y).items() if k in ("annee","publiees","closes","actives_dans_annee","stock_fin_annee","dossiers_cohorte")} for y in YEARS] for p in PRIO}
# séries longues pour contexte (avant la fenêtre)
out["contexte_avant"] = [{"annee": y, "publiees": sum(1 for r in per if (r["datePublication"] or "")[:4] == str(y)),
                          "publiees_sans_zone_plateforme": sum(1 for r in rows if not r["zones"] and (r["datePublication"] or "")[:4] == str(y)),
                          "publiees_plateforme": sum(1 for r in rows if (r["datePublication"] or "")[:4] == str(y))}
                         for y in range(2016, cfg["annee_fin"] + 1)]
# zones : libellé x année de publication
zy = collections.defaultdict(collections.Counter)
for r in per:
    for z in r["zones"] or ["(sans zone)"]:
        if z in ZONES or z == "(sans zone)": zy[z][(r["datePublication"] or "")[:4]] += 1
out["zones_par_annee"] = {z: dict(sorted(c.items())) for z, c in zy.items()}
# top démarches
fen = [r for r in per if (r["datePublication"] or "0")[:4] >= str(YEARS[0])]
def short(r): return {k: r.get(k) for k in ("number","title","organisme","typeOrganisme","pole","state","datePublication","dateFermeture","dossiersCount","n_champs","forIndividual","url","departement")} | {"pj": r["champs_types"].get("PieceJustificativeChampDescriptor",0)}
out["top_demarches_fenetre"] = [short(r) for r in sorted(fen, key=lambda r: -(r["dossiersCount"] or 0))[:20]]
tot_fen = sum(r["dossiersCount"] or 0 for r in fen)
srt = sorted((r["dossiersCount"] or 0 for r in fen), reverse=True)
out["concentration_fenetre"] = {"demarches": len(fen), "dossiers": tot_fen,
    "part_top10": round(100*sum(srt[:10])/tot_fen,1) if tot_fen else None,
    "part_top1pct": round(100*sum(srt[:max(1,len(srt)//100)])/tot_fen,1) if tot_fen else None,
    "demarches_0_dossier": sum(1 for x in srt if x == 0),
    "demarches_moins_10_dossiers": sum(1 for x in srt if x < 10),
    "mediane_dossiers": srt[len(srt)//2] if srt else None}
out["top_organismes_fenetre"] = collections.Counter((r["organisme"] or "").strip() for r in fen).most_common(25)
out["departements_fenetre"] = dict(collections.Counter(r["departement"] for r in fen if r["departement"]))
out["type_organisme_fenetre"] = dict(collections.Counter(r["typeOrganisme"] or "non renseigné" for r in fen))
# tags les plus fréquents
tg = collections.Counter(t for r in fen for t in (r["tags"] or []))
out["tags_fenetre"] = tg.most_common(30)
# annuaire éducation / API particulier : exemples
out["exemples_api_particulier"] = [short(r) for r in per if any(has(r,t) for t in APIP)]
# anomalies de rattachement : organismes inattendus sous zone EN
out["organismes_hors_education_sous_zone"] = [(o, n) for o, n in collections.Counter((r["organisme"] or "") for r in fen if r["src"]!="nom_organisme").most_common(400)
    if re.search(cfg["motif_anomalie"], o, re.I)][:15]
if cfg.get("transfert"):
    T = cfg["transfert"]; rx = re.compile(T["motif"], re.I)
    out["transfert"] = {"libelle": T["libelle"], "par_annee": {str(y): sum(1 for r in per if r["pole"] == T["pole_hote"] and (r["datePublication"] or "")[:4] == str(y)
        and rx.search((r["organisme"] or "") + " " + (r["service_nom"] or "") + " " + (r["title"] or ""))) for y in YEARS}}
out["anomalies_exclues"] = [short(r) | {"zones": r["zones"]} for r in ANOMALIES]
json.dump(out, open(sys.argv[2], "w"), ensure_ascii=False, indent=1, default=str)
print(json.dumps(out["perimetre"], ensure_ascii=False))

# --- Diffusion : émetteurs actifs par année (libellés et SIRET distincts) ---
def _o(r): return re.sub(r"\s+", " ", (r["organisme"] or "").strip().lower())
diff = []
for y in YEARS:
    act = [r for r in per if is_active(r, y)]
    diff.append({"annee": y, "emetteurs_actifs": len({_o(r) for r in act}),
        "siret_emetteurs_actifs": len({r["siret"] for r in act if r["siret"]}),
        "etablissements_actifs": len({_o(r) for r in act if r["typeOrganisme"] == "etablissement_enseignement"}),
        "siret_etablissements_actifs": len({r["siret"] for r in act if r["siret"] and r["typeOrganisme"] == "etablissement_enseignement"}),
        "departements_actifs": len({r["departement"] for r in act if r["departement"]}),
        "type_actives": dict(collections.Counter(r["typeOrganisme"] or "nr" for r in act))})
out["diffusion"] = diff
out["siret_manquant"] = sum(1 for r in per if not r["siret"])
json.dump(out, open(sys.argv[2], "w"), ensure_ascii=False, indent=1, default=str)
