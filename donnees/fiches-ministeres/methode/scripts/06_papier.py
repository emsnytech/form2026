"""Démarches encore sur papier dans le périmètre du ministère (fiches service-public.fr papier_telechargeable des
thèmes configurés + Cerfa dont l'administration relève du ministère), recoupées avec les démarches en ligne du
périmètre. Produit un exemple détaillé (instruction dans la famille) et un tableau de candidats classés :
« papier_seul », « papier_national_local » ou « en_ligne_ailleurs ». Usage : python3 06_papier.py <config.json> <sortie.json>
Ne rien inventer : chaque candidat cité existe dans les sources A (Cerfa) ou B (DILA) avec son identifiant, et chaque
service en ligne hors Démarche Numérique cite une URL officielle vérifiée."""
import json, sys, re, collections
cfg_path, out_path = sys.argv[1], sys.argv[2]
sys.argv = ["x", cfg_path, "/dev/null"]
exec(open("scripts/02_fiche_ministere.py").read().split("APIP =")[0])
P = cfg["papier"]

# ---------- sources A (Cerfa) et B (DILA), extraites de explorer.html ----------
html = open(P["explorer_html"], encoding="utf-8").read()
def script_json(id_):
    m = re.search(r'<script type="application/json" id="' + id_ + r'">(.*?)</script>', html, re.S)
    return json.loads(m.group(1))
CERFA = script_json("data-cerfa")
DILA = script_json("data-dila")
cerfa_by_num = {c["cerfa"]: c for c in CERFA}

per = []
for r in rows:
    p, s = classify(r)
    if p and p != "interministeriel": r["pole"] = p; per.append(r)

def norm_org(o): return re.sub(r"\s+", " ", (o or "").strip().lower())

# ---------- 1. Exemple principal : instruction dans la famille ----------
cerfa0 = cerfa_by_num[P["cerfa_principal"]]
mrx = re.compile(P["motif_principal"], re.I)
m_all = [r for r in rows if mrx.search(r["title"] or "")]

TEST_RX = re.compile(r"banc d.essai|bac a sable|bac à sable|\btest\b|sandbox|\bessai\b", re.I)
RECOURS_RX = re.compile(r"\brecours\b|\bRAPO\b", re.I)
DECLARATION_RX = re.compile(r"\bd[ée]claration d.instruction\b|r[ée]gime transitoire", re.I)
MOTIF_RX = re.compile(r"\bmotif[s]? \d|\bmotif 4\b", re.I)
TARDIF_RX = re.compile(r"après le 31 mai", re.I)
VALORISATION_RX = re.compile(r"valorisation des acquis", re.I)

cats = collections.defaultdict(list)
for r in m_all:
    t = r["title"]
    if TEST_RX.search(t): cats["test"].append(r)
    elif RECOURS_RX.search(t): cats["recours"].append(r)
    elif VALORISATION_RX.search(t): cats["valorisation"].append(r)
    elif DECLARATION_RX.search(t): cats["declaration"].append(r)
    elif MOTIF_RX.search(t): cats["motif_partiel"].append(r)
    elif TARDIF_RX.search(t): cats["tardif_31mai"].append(r)
    elif r["n_champs"] < 20: cats["forme_minimale"].append(r)
    else: cats["demande_autorisation"].append(r)

m_sans_test = [r for r in m_all if r not in cats["test"]]
hors_recours = [r for r in m_sans_test if r not in cats["recours"]]
demandes = cats["demande_autorisation"]

depts = {r["departement"] for r in m_sans_test if r["departement"]}
# 14 démarches sans département renseigné : complétées à la main à partir de l'organisme (vérifié une à une)
depts_manquants = {"Gironde": "33", "Hérault": "34", "Aveyron": "12", "Tarn et Garonne": "82", "Côtes d'Armor": "22",
                    "Alpes-Maritimes": "06", "Finistère": "29", "Lot": "46", "Gers": "32", "Ille et Vilaine": "35",
                    "Seine-Saint-Denis": "93"}
sans_dept = [r for r in m_sans_test if not r["departement"]]
for r in sans_dept:
    for nom, code in depts_manquants.items():
        if nom.lower() in (r["organisme"] or "").lower():
            depts.add(code); break
depts_2025 = {r["departement"] for r in m_sans_test if r["departement"] and (r["datePublication"] or "")[:4] >= "2025"}
siret_distincts = {r["siret"] for r in m_sans_test if r["siret"]}

exemple = {
    "cerfa": cerfa0["cerfa"], "cerfa_titre": cerfa0["titre"], "cerfa_url": cerfa0["url"],
    "cerfa_administration": cerfa0["administration"], "cerfa_n_champs": cerfa0["n_champs"],
    "cerfa_n_champs_prerempli": cerfa0["n_champs_prerempli"],
    "demarches_brutes": len(m_all),
    "tests_exclus": len(cats["test"]),
    "recours": len(cats["recours"]),
    "declarations_regime_transitoire": len(cats["declaration"]),
    "valorisation_acquis": len(cats["valorisation"]),
    "motif_partiel": len(cats["motif_partiel"]),
    "tardif_31mai": len(cats["tardif_31mai"]),
    "forme_minimale": len(cats["forme_minimale"]),
    "demandes_autorisation": len(demandes),
    "champs_min": min(r["n_champs"] for r in demandes), "champs_max": max(r["n_champs"] for r in demandes),
    "emetteurs_departements": len(depts),
    "emetteurs_siret": len(siret_distincts), "demarches_sans_siret": sum(1 for r in m_sans_test if not r["siret"]),
    "emetteurs_organisme_distinct": len({norm_org(r["organisme"]) for r in m_sans_test}),
    "departements_depuis_2025": len(depts_2025),
    "dossiers_total": sum(r["dossiersCount"] or 0 for r in m_sans_test),
    "dossiers_hors_recours": sum(r["dossiersCount"] or 0 for r in hors_recours),
}

# ---------- 2. Candidats (DILA papier, recoupés avec le périmètre en ligne) ----------
EN = re.compile(cfg["sans_zone_motifs"]["Éducation nationale"], re.I)
SUP = re.compile(cfg["sans_zone_motifs"]["Enseignement supérieur et recherche"], re.I)
JS = re.compile(cfg["sans_zone_motifs"]["Jeunesse et sports"])
dila_by_id = {d["fiche_id"]: d for d in DILA}

candidats_out = []
for c in P["candidats"]:
    rx = re.compile(c["motif_recherche"], re.I)
    m_per = [r for r in per if rx.search(r["title"] or "")]
    fiches = [dila_by_id[fid] for fid in c["fiche_dila"] if fid in dila_by_id]
    cerfa_info = cerfa_by_num.get(c["cerfa"]) if c.get("cerfa") else None
    row = {
        "id": c["id"], "titre": c["titre"], "statut": c["statut"],
        "fiche_dila": c["fiche_dila"],
        "fiche_dila_urls": [f["lien_web_url"] for f in fiches],
        "cerfa": c.get("cerfa"),
        "cerfa_url": cerfa_info["url"] if cerfa_info else (fiches[0]["lien_web_url"] if fiches else None),
        "cerfa_n_champs": cerfa_info["n_champs"] if cerfa_info else None,
        "cerfa_n_champs_prerempli": cerfa_info["n_champs_prerempli"] if cerfa_info else None,
        "demarches_en_ligne": len(m_per),
        "emetteurs": len({norm_org(r["organisme"]) for r in m_per}) if m_per else 0,
        "champs_min": min((r["n_champs"] for r in m_per), default=None),
        "champs_max": max((r["n_champs"] for r in m_per), default=None),
        "dossiers": sum(r["dossiersCount"] or 0 for r in m_per),
        "service_en_ligne": c.get("service_en_ligne"),
        "note": c.get("note"),
        "source_statut": c.get("source_statut"),
    }
    candidats_out.append(row)

# ---------- 3. Méta (pour le texte de section et le compte rendu) ----------
THEMES = set(P["themes_dila"])
dila_pool = [d for d in DILA if d["modalite"] == "papier_telechargeable" and d["theme"] in THEMES]
cerfa_pool_ids = [c["cerfa"] for c in CERFA
                  if not re.search(cfg.get("exclusions_toutes", "$^"), c["administration"] or "", re.I)
                  and not re.search(cfg["sans_zone_exclusions"], c["administration"] or "", re.I)
                  and (EN.search(c["administration"] or "") or SUP.search(c["administration"] or "") or JS.search(c["administration"] or ""))]

meta = {
    "n_cerfa_total": len(CERFA), "n_cerfa_perimetre": len(cerfa_pool_ids), "cerfa_perimetre": cerfa_pool_ids,
    "n_dila_total": len(DILA), "n_dila_pool": len(dila_pool),
    "n_dila_exclusions": len(P.get("exclusions_dila", {})), "exclusions_dila": P.get("exclusions_dila", {}),
    "n_candidats": len(candidats_out),
    "n_en_ligne_ailleurs": sum(1 for c in candidats_out if c["statut"] == "en_ligne_ailleurs"),
    "n_papier_national_local": sum(1 for c in candidats_out if c["statut"] == "papier_national_local"),
    "n_papier_seul": sum(1 for c in candidats_out if c["statut"] == "papier_seul"),
}

out = {"exemple_principal": exemple, "candidats": candidats_out, "meta": meta}
json.dump(out, open(out_path, "w"), ensure_ascii=False, indent=1)
print(json.dumps(meta, ensure_ascii=False, indent=1))
print()
print("Exemple principal :", json.dumps(exemple, ensure_ascii=False, indent=1))
