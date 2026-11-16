"""Fiche Intérieur, arbitrages n° 25 et 26 : chronologies du local au national (DETR et DSIL ; médailles). Open data seul.

Constat de méthode, établi en lisant les versions DETR postérieures à la version nationale : dans le descriptif, la date de
publication est celle de la dernière publication (une démarche créée en 2023, republiée puis close le même jour en 2025, y porte
la date de 2025). Une version n'est dite « postérieure » à la version nationale que si elle a été créée après elle. La date de
création ne suffit pas non plus : une démarche peut rester en brouillon des années (la version nationale du NEPH est créée en
2021, publiée en 2024, et les versions locales ferment de décembre 2024 à mars 2025). Les médailles sont datées par la création
(création et publication coïncident pour les versions de 2018) ; le test des autres cas garde la date de publication, et la date
de création est donnée en regard, avec le mois des fermetures locales. Les champs décrits sont ceux de la révision publiée aujourd'hui.

Règles, fixées avant le décompte :
- DETR et DSIL : démarches du périmètre dont le titre nomme la DETR ou la DSIL, famille « Dotations et subventions » (même
  définition qu'en section 3). « Reprend la trame » : similarité de Jaccard d'au moins 0,5 entre les libellés de champs
  (normalisés) de la version et ceux de la trame DGCL n° 77495 ; la distribution est bimodale (presque toutes les versions sont
  sous 0,2 ou au-dessus de 0,5). Campagne N : version créée du 1er juillet N-1 au 30 juin N.
- versions locales créées ou republiées après la version nationale (n° 128030) : lecture des titres ; tri en « démarches plus
  anciennes republiées » (créées avant la version nationale), « tests » (titre TEST) et « nouvelles demandes ».
- médailles : nature lue dans le titre (script 33). Pour chaque médaille nationale : première version nationale, première version
  nationale d'au moins 100 dossiers, départements ayant une version locale créée avant cette date (sur 101), état des versions
  locales. Les démarches de médailles hors périmètre (autres zones) sont relevées à part, par zone.
- sensibilité du test de la section « Formulaires nationaux » (NEPH, label) : même test, sur la date de création.
Sortie : out/interieur_chronologies.json (comptes et dates, aucun nom de territoire)."""
import json, re, sys, os, collections as C, datetime as dt
src40 = open("scripts/40_variete_departements_interieur.py").read()
exec(src40.split("# réglementations uniformes")[0].replace('out["A"]["unites_regionales"]', "_u"))
RAW = os.environ.get("FORM2026_RAW", "data/20261021041002-demarches.json")
dc = lambda r: dt.date.fromisoformat(r["dateCreation"][:10])
dp = lambda r: dt.date.fromisoformat(r["datePublication"][:10])
ALL = [json.loads(l) for l in open("data/demarches_slim.jsonl")]
PERN = {r["number"] for r in per}
out = {"regle_dates": "date de publication = dernière publication ; versions postérieures : date de création ; médailles : date de création"}

# ---------- DETR et DSIL
DT = [r for r in per if re.search(r"\bDETR\b|\bDSIL\b", r["title"] or "", re.I) and r["fam"] == "Dotations et subventions"]
TRAME, NAT = 77495, 128030
import ijson
want = {r["number"] for r in DT} | {TRAME, NAT}
def labels(ds, acc):
    for x in ds or []:
        if x.get("label"): acc.add(re.sub(r"\s+", " ", na(x["label"])).strip())
        for k in ("champDescriptors", "children"):
            if isinstance(x.get(k), list): labels(x[k], acc)
    return acc
LAB, DESC = {}, {}
with open(RAW, "rb") as f:
    for p in ijson.items(f, "item", use_float=True):
        if p.get("number") in want:
            LAB[p["number"]] = labels((p.get("revision") or {}).get("champDescriptors"), set())
            DESC[p["number"]] = p.get("description") or ""
nat = next(r for r in per if r["number"] == NAT); tra = next(r for r in per if r["number"] == TRAME)
for r in DT: r["jt"] = jac(LAB.get(r["number"], set()), LAB[TRAME])
loc = [r for r in DT if r["niv"] != "nationale"]
camp = lambda x: x.year + 1 if x.month >= 7 else x.year
trame_v = [r for r in loc if r["jt"] >= 0.5]
autres_v = [r for r in loc if r["jt"] < 0.5]
par_camp = {}
for c in sorted({camp(dc(r)) for r in loc}):
    T_ = [r for r in trame_v if camp(dc(r)) == c]; A_ = [r for r in autres_v if camp(dc(r)) == c]
    par_camp[c] = {"reprend_la_trame": [len(T_), len({r["dep"] for r in T_ if r["dep"]})], "autres": [len(A_), len({r["dep"] for r in A_ if r["dep"]})]}
first = {}
for r in trame_v:
    if r["dep"]: first[r["dep"]] = min(first.get(r["dep"], dc(r)), dc(r))
fv = sorted(first.values())
fin_ = lambda r: r["dateFermeture"][:7] if r["dateFermeture"] else None
ferm = C.Counter(fin_(r) for r in trame_v if fin_(r))
mois_pic, n_pic = ferm.most_common(1)[0]
avant_trame = {r["dep"] for r in loc if r["dep"] and dc(r) < dp(tra) and r["jt"] < 0.5}
# versions locales datées (création ou publication) après la version nationale
post = [r for r in loc if r["dep"] and (dp(r) > dp(nat) or dc(r) > dp(nat)) and re.search(r"demande de subvention", na(r["title"]))]
def tri(r):
    if re.search(r"\btest", na(r["title"])): return "test"
    if dc(r) < dc(nat): return "demarche_anterieure_republiee"
    return "nouvelle_demande"
P = C.defaultdict(list)
for r in post: P[tri(r)].append(r)
out["detr"] = {
    "trame_dgcl": {"numero": TRAME, "creation": str(dc(tra)), "publication": str(dp(tra)), "dossiers": tra["dossiersCount"],
                   "champs": len(LAB[TRAME]), "titre_millesime": re.findall(r"20\d\d", tra["title"])},
    "nationale": {"numero": NAT, "creation": str(dc(nat)), "publication": str(dp(nat)), "dossiers": nat["dossiersCount"],
                  "campagne_nommee_dans_la_description": bool(re.search(r"20\d\d", DESC[NAT])),
                  "campagne_nommee_dans_les_champs": sorted(x for x in LAB[NAT] if re.search(r"campagne 20\d\d", x)),
                  "autre_nationale_de_demande_100_dossiers_avant": [r["number"] for r in ALL if re.search(r"\bDETR\b|\bDSIL\b", r["title"] or "") and (r["dossiersCount"] or 0) >= 100
                      and r["number"] != NAT and r["number"] in PERN and next(x for x in per if x["number"] == r["number"])["niv"] == "nationale" and re.search(r"demande de subvention", na(r["title"]))]},
    "versions_locales": len(loc), "departements_avec_version_locale": len({r["dep"] for r in loc if r["dep"]}),
    "temps1_departements_version_locale_creee_avant_la_trame": len(avant_trame),
    "temps2": {"versions_reprenant_la_trame": len(trame_v), "departements": len(first),
               "departements_premiere_version_avant_le_30_juin_2024": sum(x <= dt.date(2024, 6, 30) for x in fv),
               "premiere_creation": str(fv[0]), "mediane_premiere_creation": str(fv[len(fv) // 2]),
               "titre_identique_a_la_trame": [sum(na(r["title"]).strip().startswith("demande de subvention au titre de la detr et de la dsil") for r in loc),
                                              len({r["dep"] for r in loc if r["dep"] and na(r["title"]).strip().startswith("demande de subvention au titre de la detr et de la dsil")})],
               "fermetures_mois_le_plus_frequent": [mois_pic, n_pic], "encore_en_ligne": sum(r["state"] == "publiee" for r in trame_v),
               "par_campagne_de_creation": par_camp},
    "apres_la_nationale": {k: {"versions": len(v), "departements": len({r["dep"] for r in v}), "dossiers": nd(v),
                               "en_ligne": sum(r["state"] == "publiee" for r in v), "fermees": sum(r["state"] != "publiee" for r in v),
                               "creation": [str(min(dc(r) for r in v)), str(max(dc(r) for r in v))]} for k, v in P.items()},
    "sources": {"instruction_22_aout_2023": "https://www.legifrance.gouv.fr/circulaire/id/45473",
                "circulaire_1er_avril_2026": "https://www.legifrance.gouv.fr/circulaire/id/45656"}}

# ---------- médailles
exec("def nature" + open("scripts/33_medailles_tests_interieur.py").read().split("def nature")[1].split("tab =")[0])
ME = [r for r in per if r["fam"] == "Médailles et distinctions"]
TEST = re.compile(r"\btest|betagouv", re.I)
med = {}
for k in ("travail", "régionale, départementale et communale", "agricole"):
    L = [r for r in ME if nature(r["title"]) == k]
    N = [r for r in L if r["niv"] == "nationale" and not TEST.search(r["title"])]
    n0 = min(dc(r) for r in N); n100 = min(dc(r) for r in N if (r["dossiersCount"] or 0) >= 100)
    Lo = [r for r in L if r["niv"] != "nationale" and not TEST.search(na((r["title"] or "") + " " + (r["organisme"] or "")))]
    av = [r for r in Lo if dc(r) <= n100]
    H = [r for r in ALL if r["number"] not in PERN and re.search({"travail": r"honneur du travail(?! agricole)", "agricole": r"honneur (du travail )?agricole",
         "régionale, départementale et communale": r"r[ée]gionale.{0,5}d[ée]partementale"}[k], r["title"] or "", re.I)]
    Hr = [r for r in H if not TEST.search(r["title"]) and (r["dossiersCount"] or 0) > 3]
    av0 = [r for r in Lo if dc(r) < n0]
    ess0 = [r for r in L + H if r["niv" if "niv" in r else "state"] != "nationale" and dc(r) < n0 and (TEST.search(r["title"]) or (r["dossiersCount"] or 0) <= 3)]
    med[k] = {"demarches": len(L), "dossiers": nd(L), "premiere_nationale": str(n0), "premiere_nationale_100_dossiers": str(n100),
              "dossiers_nationaux": nd(N),
              "avant_la_premiere_nationale": {"versions": len(av0), "departements": len({r["dep"] for r in av0 if r["dep"]}), "sans_departement": sum(1 for r in av0 if not r["dep"]),
                                              "dossiers": nd(av0), "essais_1_a_3_dossiers_toutes_zones": len(ess0)},
              "locales_en_ligne_aujourdhui": [sum(r["state"] == "publiee" for r in Lo), len({r["dep"] for r in Lo if r["state"] == "publiee" and r["dep"]})],
              "locales_creees_avant": {"versions": len(av), "departements": len({r["dep"] for r in av if r["dep"]}),
                                       "sans_departement": sum(1 for r in av if not r["dep"]), "dossiers": nd(av),
                                       "creation": sorted({str(dc(r))[:7] for r in av}),
                                       "fermees_au_plus_tard": str(max((r["dateFermeture"] or "9999")[:10] for r in av)) if av else None},
              "locales_creees_apres": {"versions": len(Lo) - len(av), "departements": len({r["dep"] for r in Lo if r["dep"] and dc(r) > n100}),
                                       "en_ligne": sum(r["state"] == "publiee" for r in Lo if dc(r) > n100), "dossiers": nd([r for r in Lo if dc(r) > n100])},
              "hors_perimetre": {"versions": len(Hr), "departements": len({r["departement"] for r in Hr if r["departement"]}), "dossiers": nd(Hr),
                                 "avant": sum(dc(r) <= n100 for r in Hr), "en_ligne": sum(r["state"] == "publiee" for r in Hr),
                                 "zones": dict(C.Counter(z for r in Hr for z in (r["zones"] or ["(aucune)"])))}}
AU = [r for r in ME if nature(r["title"]).startswith("autres")]
med["autres_dans_le_perimetre"] = {"demarches": len(AU), "dossiers": nd(AU), "departements": len({r["dep"] for r in AU if r["dep"]}),
    "en_ligne": sum(r["state"] == "publiee" for r in AU), "versions_nationales": sum(r["niv"] == "nationale" for r in AU),
    "objets": sorted({re.sub(r".*(s[ée]curit[ée] int[ée]rieure|courage et d[ée]vouement|transports routiers|administration territoriale|jeunesse).*", r"\1", na(r["title"])) for r in AU})}
def hp(rx):
    H = [r for r in ALL if r["number"] not in PERN and re.search(rx, r["title"] or "", re.I) and not TEST.search(r["title"])]
    return {"demarches": len(H), "dossiers": nd(H), "departements": len({r["departement"] for r in H if r["departement"]}),
            "en_ligne": sum(r["state"] == "publiee" for r in H), "zones": dict(C.Counter(z for r in H for z in (r["zones"] or ["(aucune)"]))),
            "plus_grosse": max((r["dossiersCount"] or 0) for r in H) if H else 0}
med["hors_perimetre"] = {"jeunesse, sports et engagement associatif": hp(r"m[ée]daille.{0,30}jeunesse"), "chemins de fer": hp(r"m[ée]daille.{0,30}chemins de fer"),
                         "transports routiers": hp(r"m[ée]daille.{0,30}transports routiers")}
out["medailles"] = med

# ---------- sensibilité du test (date de création)
LNd = json.load(open("out/interieur_local_national.json"))["detail"]
def pick(rx):
    t = next(x["titre_graine"] for x in LNd if re.search(rx, x["titre_graine"])); return next(c for c in clusters if c["titre"] == t)
sens = {}
for k, rx in (("NEPH", r"NEPH"), ("label des écoles de conduite", r"qualit. des formations")):
    c = pick(rx); N = [r for r in c["m"] if r["niv"] == "nationale" and (r["dossiersCount"] or 0) >= 100]
    n_p = min(dp(r) for r in N); n_c = min(dc(r) for r in N)
    lo = [r for r in c["m"] if r["niv"] == "locale" and r["dep"]]
    fe = C.Counter(r["dateFermeture"][:7] for r in lo if r["dateFermeture"])
    sens[k] = {"publication": [str(n_p), len({r["dep"] for r in lo if dp(r) <= n_p})], "creation": [str(n_c), len({r["dep"] for r in lo if dc(r) <= n_c})],
               "fermetures_locales_dans_les_6_mois_apres_publication": sum(v for m, v in fe.items() if str(n_p)[:7] <= m <= str(n_p + dt.timedelta(days=183))[:7]),
               "fermetures_locales": sum(fe.values())}
out["sensibilite_date_creation"] = sens
json.dump(out, open("out/interieur_chronologies.json", "w"), ensure_ascii=False, indent=1, default=str)
print(json.dumps(out, ensure_ascii=False, indent=1, default=str))
