"""Inventaire préalable à la fiche Justice : périmètre, anomalies, typologie des émetteurs, nature des usages, familles homologues,
formulaire de contact, usages génériques, pièces de ressources et API, Cerfa et fiches service-public.
Usage (depuis fiches-ministeres) : python3 scripts/09_inventaire_justice.py scripts/config_justice.json out/justice_inventaire.json"""
import json, re, sys, collections as C, unicodedata
cfg_path, out_path = sys.argv[1], sys.argv[2]
sys.argv = ["x", cfg_path, "/dev/null"]
exec(open("scripts/02_fiche_ministere.py").read().split("APIP =")[0])
EXPL = "../../../explorer.html"
# Démarches agrégées dans la fiche : désignées par leur numéro, pour qu'aucun titre sensible ne figure dans le dépôt.
AGREGEES = {100049, 123573, 147656}

per, inter = [], []
for r in rows:
    p, s = classify(r)
    if p == "interministeriel": inter.append(r)
    elif p: r["src"] = s; per.append(r)
num = {r["number"] for r in per}
dos = lambda L: sum(r["dossiersCount"] or 0 for r in L)
pj = lambda r: r["champs_types"].get("PieceJustificativeChampDescriptor", 0)
def saisie(r):  # champs de saisie : sans sections ni textes d'explication
    return r["n_champs"] - r["champs_types"].get("HeaderSectionChampDescriptor", 0) - r["champs_types"].get("ExplicationChampDescriptor", 0)
Z = "Ministère de la Justice"
zone_all = [r for r in rows if Z in (r["zones"] or [])]

# --- Typologie des émetteurs (lue dans organisme + service, jamais déduite de typeOrganisme, peu fiable ici)
TYPO = [
 ("Juridictions", r"tribunal judiciaire|cour d.appel|prud.?homme|cour de cassation"),
 ("Conseils départementaux de l'accès au droit (GIP)", r"\bCDAD\b"),
 ("Écoles (ENM, ENG)", r"magistrature|\bENM\b|[ée]cole nationale des greffes|^ENG$|\bENAP\b"),
 ("Administration pénitentiaire : directions interrégionales, SPIP, établissements", r"\bDISP\b|interr[ée]gionale des services p[ée]nitentiaires|\bSPIP\b|centre de d[ée]tention|maison d.arr[êe]t|centre p[ée]nitentiaire"),
 ("Direction des services judiciaires (RH des greffes)", r"direction des services judiciaires|^DSJ\b"),
 ("Administration centrale (secrétariat général, cabinet, directions)", r"secr[ée]tariat g[ée]n[ée]ral|garde des sceaux|minist[eè]re de la justice|^OJI6$|^PS4$"),
]
def typo(r):
    o = (r["organisme"] or "").strip()
    for n, m in TYPO:
        if re.search(m, o, re.I): return n
    return "À qualifier"
def orgkey(r):
    return re.sub(r"\s+", " ", (r["organisme"] or "").strip().lower())
out = {}
fen = [r for r in per if any(is_active(r, y) for y in YEARS)]
ty = C.defaultdict(list)
for r in per: ty[typo(r)].append(r)
out["emetteurs_par_type"] = [{"type": t, "demarches": len(L), "dossiers": dos(L), "libelles": len({orgkey(r) for r in L}),
    "siret": len({r["siret"] for r in L if r["siret"]}), "departements": sorted({r["departement"] for r in L if r["departement"]}),
    "publiees_en_ligne": sum(r["state"] == "publiee" for r in L),
    "detail": C.Counter((r["organisme"] or "").strip() for r in L).most_common(12)} for t, L in sorted(ty.items(), key=lambda x: -len(x[1]))]
out["perimetre"] = {"total": len(per), "dossiers": dos(per), "par_source": C.Counter(r["src"] for r in per),
    "etats": C.Counter(r["state"] for r in per), "siret": len({r["siret"] for r in per if r["siret"]}), "libelles": len({orgkey(r) for r in per}),
    "departements": len({r["departement"] for r in per if r["departement"]}),
    "zone_justice_brute": len(zone_all), "dossiers_zone_brute": dos(zone_all),
    "exclues_plus_3_zones": len(inter), "dossiers_plus_3_zones": dos(inter),
    "plus_3_zones_srias": sum(bool(re.search("SRIAS", r["organisme"] or "")) for r in inter),
    "part_du_fichier_demarches": round(100 * len(per) / len(rows), 2), "part_du_fichier_dossiers": round(100 * dos(per) / sum(r["dossiersCount"] or 0 for r in rows), 2)}
out["anomalies_exclues"] = [{"n": r["number"], "o": (r["organisme"] or "")[:60], "t": r["title"][:90], "d": r["dossiersCount"], "z": len(r["zones"] or [])} for r in ANOMALIES]
out["annees"] = [{"annee": y, "publiees": sum((r["datePublication"] or "")[:4] == str(y) for r in per),
    "closes": sum(bool(fin(r) and fin(r).year == y) for r in per), "stock": sum(bool(stock(r, y)) for r in per),
    "plateforme_publiees": sum((r["datePublication"] or "")[:4] == str(y) for r in rows)} for y in YEARS]

# --- Nature des usages (par le titre et l'organisme)
RH = re.compile(r"concours|recrutement|examen professionnel|prise en charge|\bFIR\b|\bRAEP\b|mobilit|CAP\b|avancement|promotion|tableau d.avancement|vacation|intervenant|indemnit|\bIFM\b|\bCID\b|\bCPT\b|pr[ée]pa talents|stagiaire|auditeur|\bADJ\b|candidat|t[ée]l[ée]travail|prestation de serment|droit à l.image|d[ée]tachement|\bRH\b|\bSRH\b|formation|contractuel|vivier|poste|greffier|magistrat|ressources humaines|lauréat|laur[ée]at", re.I)
RH_ORG = re.compile(r"ressources humaines|[ée]cole|magistrature|\bENG\b|\bENM\b|RHM", re.I)
USAG = re.compile(r"non.appel|casier|restitution|agr[ée]ment|question au minist", re.I)
def nature(r):
    t = r["title"] or ""
    if r["number"] in AGREGEES or USAG.search(t): return "Usagers, justiciables, partenaires"
    if RH_ORG.search((r["organisme"] or "") + " " + (r["service_nom"] or "")) or RH.search(t): return "Ressources humaines, concours, formation"
    return "Autres (fonctionnement, subventions, appels à projets, événements)"
na = C.defaultdict(list)
for r in per: na[nature(r)].append(r)
out["nature"] = {k: {"demarches": len(L), "dossiers": dos(L), "exemples": [(r["number"], r["title"][:70], r["dossiersCount"]) for r in sorted(L, key=lambda r: -(r["dossiersCount"] or 0))[:12]]} for k, L in na.items()}

# --- Top démarches depuis 2021
out["top"] = [{"n": r["number"], "t": r["title"][:90], "o": (r["organisme"] or "")[:45], "d": r["dossiersCount"], "c": r["n_champs"], "s": saisie(r), "pj": pj(r), "y": (r["datePublication"] or "")[:4], "e": r["state"]}
    for r in sorted([r for r in fen], key=lambda r: -(r["dossiersCount"] or 0))[:15]]

# --- Familles homologues (motifs de titre)
FAM = json.load(open("scripts/familles_justice.json"))
res = []
for f in FAM:
    rx = re.compile(f["motif"], re.I)
    m = [r for r in per if rx.search(r["title"] or "") and (r["datePublication"] or "0")[:4] >= "2021"]
    if not m: res.append({"famille": f["nom"], "demarches": 0}); continue
    par_org = C.defaultdict(list)
    for r in m: par_org[typo(r)].append(r["n_champs"])
    res.append({"famille": f["nom"], "demarches": len(m), "libelles": len({orgkey(r) for r in m}), "siret": len({r["siret"] for r in m if r["siret"]}), "dossiers": dos(m),
        "champs_min": min(r["n_champs"] for r in m), "champs_max": max(r["n_champs"] for r in m),
        "pj_max": max(pj(r) for r in m), "par_emetteur": {k: [len(v), min(v), max(v)] for k, v in par_org.items()},
        "par_annee": dict(sorted(C.Counter(r["datePublication"][:4] for r in m).items()))})
out["familles"] = res

# --- Champs détaillés
R = {}
for l in open("data/justice_champs.jsonl"):
    x = json.loads(l)
    if x["number"] in num: R[x["number"]] = x
def walk(ds):
    for d_ in ds or []:
        yield d_
        for k in ("champDescriptors", "children"):
            if isinstance(d_.get(k), list): yield from walk(d_[k])
out["contact"] = None
c = next(r for r in per if r["number"] == 64697)
jours = (d(ASOF) - d(c["datePublication"])).days
out["contact"] = {"n": 64697, "titre": c["title"], "publie": c["datePublication"][:10], "etat": c["state"], "dossiers": c["dossiersCount"], "champs": c["n_champs"], "champs_saisie": saisie(c), "pj": pj(c),
    "jours_ouverture": jours, "dossiers_par_jour": round(c["dossiersCount"] / jours, 1), "par_an": round(c["dossiersCount"] / jours * 365), "url": c["url"],
    "rang_perimetre": 1 + sum((r["dossiersCount"] or 0) > c["dossiersCount"] for r in per), "part_dossiers": round(100 * c["dossiersCount"] / dos(per), 1),
    "categories": [d_.get("options") for d_ in walk(R[64697]["champs"]) if d_.get("options")]}
GEN = re.compile(r"\bcontact\b|nous (contacter|[ée]crire)|question|saisine|renseignements? (au|aupr)|bo[iî]te|guichet|accueil num|formulaire unique|demande d.information", re.I)
out["usages_generiques"] = [{"n": r["number"], "t": r["title"][:90], "o": (r["organisme"] or "")[:45], "d": r["dossiersCount"], "c": r["n_champs"]} for r in per if GEN.search(r["title"] or "")]

# --- Ressources / API (section 8)
AVIS = re.compile(r"avis d.(imposition|imp[ôo]t|non.imposition)|revenu fiscal|\bRFR\b", re.I)
BUL = re.compile(r"bulletins? de (salaire|paie|solde)|justificatifs? de (revenus|ressources)", re.I)
RIB = re.compile(r"\bRIB\b|relev[ée] d.identit[ée] bancaire", re.I)
IDT = re.compile(r"pi[èe]ce d.identit|carte (nationale )?d.identit|passeport|titre de s[ée]jour", re.I)
DIPL = re.compile(r"dipl[ôo]me|attestation de r[ée]ussite", re.I)
DOM = re.compile(r"justificatif de domicile|domicile", re.I)
CASIER = re.compile(r"casier|bulletin\sn.?\s?[23]\b", re.I)
SIR = re.compile(r"\bkbis\b|extrait k|avis de situation|\bSIRENE\b", re.I)
ASS = re.compile(r"r[ée]c[ée]piss[ée].{0,30}(association|d[ée]claration)|statuts|parution.{0,20}journal officiel|\bJOAFE\b", re.I)
def lbl(d_): return (d_.get("label") or "") + " " + (d_.get("description") or "")
ref = {"avis_imposition": AVIS, "bulletins_paie_ou_ressources": BUL, "rib": RIB, "identite": IDT, "diplome": DIPL, "domicile": DOM, "casier": CASIER, "kbis_sirene": SIR, "pieces_association": ASS}
pjc = C.defaultdict(list); total_pj = 0
for n, x in R.items():
    pjs = [d_ for d_ in walk(x["champs"]) if d_.get("__typename") == "PieceJustificativeChampDescriptor"]
    total_pj += len(pjs)
    for k, rx in ref.items():
        if any(rx.search(lbl(d_)) for d_ in pjs): pjc[k].append(n)
byn = {r["number"]: r for r in per}
out["pj_labels"] = {"demarches_lues": len(R), "pj_total": total_pj, **{k: {"demarches": len(v), "dossiers": sum(byn[n]["dossiersCount"] or 0 for n in v)} for k, v in pjc.items()}}
out["pj_avis"] = [{"n": n, "t": byn[n]["title"][:80], "o": (byn[n]["organisme"] or "")[:35], "d": byn[n]["dossiersCount"], "y": byn[n]["datePublication"][:4]} for n in sorted(pjc["avis_imposition"], key=lambda n: -(byn[n]["dossiersCount"] or 0))]
API = ("QuotientFamilialChampDescriptor", "EtudiantBoursierChampDescriptor", "DgfipChampDescriptor")
out["referentiels"] = {t: sum(r["champs_types"].get(t, 0) > 0 for r in per) for t in API + ("SiretChampDescriptor", "RNAChampDescriptor", "RNFChampDescriptor", "IbanChampDescriptor", "AnnuaireEducationChampDescriptor", "ReferentielChampDescriptor", "DossierLinkChampDescriptor", "CarteChampDescriptor")}
ass = [r for r in per if re.search("association|subvention|agr[ée]ment|appel à projet", r["title"] or "", re.I)]
out["partenaires_associatifs"] = {"demarches": len(ass), "avec_rna_rnf": sum(r["champs_types"].get("RNAChampDescriptor", 0) + r["champs_types"].get("RNFChampDescriptor", 0) > 0 for r in ass), "avec_siret": sum(r["champs_types"].get("SiretChampDescriptor", 0) > 0 for r in ass), "dossiers": dos(ass)}
ibanpj = set(pjc["rib"]); 
out["rib"] = {"pj_rib": len(ibanpj), "champ_iban": sum(r["champs_types"].get("IbanChampDescriptor", 0) > 0 for r in per), "pj_rib_et_iban": sum(byn[n]["champs_types"].get("IbanChampDescriptor", 0) > 0 for n in ibanpj)}

# --- Cerfa et fiches service-public
h = open(EXPL, encoding="utf-8").read()
def S(i): return json.loads(re.search(r'<script type="application/json" id="' + i + r'">(.*?)</script>', h, re.S).group(1))
CE, DI, ES = S("data-cerfa"), S("data-dila"), S("data-essentielles")
cl = sorted([c for c in CE if c.get("total_central") is not None], key=lambda c: -c["total_central"])
JUS = re.compile(r"justice|juge aux affaires|juridiction", re.I)
out["cerfa_classes"] = len(cl); out["cerfa_total"] = len(CE)
out["cerfa_justice"] = [{"rang": i + 1, "cerfa": c["cerfa"], "titre": c["titre"], "admin": c["administration"], "n_champs": c["n_champs"], "prerempli": c["n_champs_prerempli"], "reduction": c["pct_reduction_si_dn"], "volumetrie": c["volumetrie_dila"], "gain_central": c["total_central"], "url": c["url"]} for i, c in enumerate(cl) if JUS.search(c["administration"] or "")]
out["aj_dans_cerfa"] = [c["cerfa"] for c in CE if c["cerfa"][:5] in ("16146", "15628")]
out["essentielles_aj"] = [{k: e[k] for k in ("nom", "statut_en_ligne", "volumetrie_totale", "pct_recours_numerique", "franceconnect", "score_dlnuf", "url")} for e in ES if e["id_observatoire"] in (1747, 1730)]
jd = [x for x in DI if x["theme"] == "Justice"]
out["dila_justice"] = {"fiches": len(jd), "papier": sum(x["modalite"] == "papier_telechargeable" for x in jd), "en_ligne": sum(x["modalite"] == "en_ligne" for x in jd)}
out["homologues_cerfa"] = {k: {"fiche": v, "demarches": [(r["number"], r["state"], r["dossiersCount"], r["n_champs"], pj(r), (r["organisme"] or "")[:40]) for r in rows if re.search(m, r["title"] or "", re.I) and r["number"] in num]}
    for k, (v, m) in {"non_appel": ("R18606 Cerfa 12821*02", r"non.appel"), "copie_decision": ("R1408 Cerfa 11808*06", r"copie.{0,20}(jugement|d[ée]cision)")}.items()}
json.dump(out, open(out_path, "w"), ensure_ascii=False, indent=1, default=str)
for k in out:
    if k not in ("top",): print("\n##", k, "\n", json.dumps(out[k], ensure_ascii=False, default=str)[:3200])
print("\n## top"); [print(t) for t in out["top"]]

# --- Compléments d'inventaire : titres DSJ normalisés, écoles, cas à qualifier, référentiel diplômes
def norm(t):
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()
    t = re.sub(r"\b(g|3g|gre|gpr|dsg|ceng|a|b)?20\d\d\S*|\bs[0-9]\b|\b20\d\d\b", " ", t)
    return re.sub(r"[^a-z ]+", " ", re.sub(r"\s+", " ", t)).strip()
dsj = [r for r in per if typo(r).startswith("Direction des services")]
GR = [("Dossier de prise en charge", r"prise en charge"), ("Dépôt FIR", r"\bFIR\b"), ("RAEP / dossier d'examen", r"RAEP"), ("Pièces justificatives", r"pi[èe]ces? justificatives?"),
      ("Oral / épreuve", r"oral|[ée]preuve|admission|admissibilit"), ("Mobilité / postes / CLE", r"mobilit|poste|\bCLE\b|affectation|vœux|voeux|choix"), ("Promotion / liste d'aptitude / avancement", r"promotion|aptitude|avancement|tableau")]
g = C.Counter(); gd = C.Counter(); rest = []
for r in dsj:
    for n_, m in GR:
        if re.search(m, r["title"], re.I): g[n_] += 1; gd[n_] += r["dossiersCount"] or 0; break
    else: g["Autres"] += 1; gd["Autres"] += r["dossiersCount"] or 0; rest.append(r["title"][:70])
out2 = {"dsj_titres": {k: [v, gd[k]] for k, v in g.most_common()}, "dsj_autres_exemples": C.Counter(rest).most_common(25)}
car = [r for r in per if re.search("carri[èe]res et de la mobilit", r["organisme"] or "")]
out2["bureau_carrieres"] = {"demarches": len(car), "dossiers": dos(car), "exemples": [r["title"][:80] for r in sorted(car, key=lambda r: -(r["dossiersCount"] or 0))[:14]]}
def ecole(r):
    o = (r["organisme"] or "")
    return "ENM" if re.search("magistrature|ENM", o, re.I) else "ENG" if re.search("greffes|^ENG", o, re.I) else None
pt = [r for r in per if re.search(r"pr[ée]pa(ratoire)? talents|\bCPT\b", r["title"] or "", re.I) and not re.search("bourse", r["title"], re.I)]
out2["prepa_talents"] = {e: {"demarches": len(L), "dossiers": dos(L), "champs": [min(r["n_champs"] for r in L), max(r["n_champs"] for r in L)], "pj_max": max(pj(r) for r in L)} for e in ("ENM", "ENG") for L in [[r for r in pt if ecole(r) == e]] if L}
out2["absences"] = {"pjj": sum(bool(re.search(r"\bPJJ\b|protection judiciaire|ENPJJ", (r["organisme"] or "") + (r["service_nom"] or ""), re.I)) for r in rows),
    "enap": sum(bool(re.search(r"\bENAP\b|administration p[ée]nitentiaire", (r["organisme"] or ""), re.I)) for r in per), "cour_appel_reelle": sum(bool(re.search(r"cour d.appel", r["organisme"] or "", re.I)) for r in per)}
out2["a_qualifier"] = {n: {"titre": R[n]["title"][:80], "description": re.sub(r"\s+", " ", R[n]["description"] or "")[:420], "pj": [d_["label"][:60] for d_ in walk(R[n]["champs"]) if d_["__typename"] == "PieceJustificativeChampDescriptor"][:6], "ferme": byn[n]["dateFermeture"]} for n in (99859, 147656, 130561, 152981, 123573, 100049) if n in R}
TAB = S("data-api-tab")
out2["api_tab"] = [{k: a.get(k) for k in ("donnee", "statut", "api_correspondante", "adm_ref")} for a in TAB if re.search(r"dipl[ôo]m|revenu|imposition|fiscal|ressources|identit|boursier|RIB|IBAN|bancaire", a.get("donnee") or "", re.I)]
out["complements"] = out2
json.dump(out, open(out_path, "w"), ensure_ascii=False, indent=1, default=str)
print("\n## complements\n", json.dumps(out2, ensure_ascii=False, indent=0, default=str))
print("\n## familles\n", json.dumps(out["familles"][9:], ensure_ascii=False, default=str))
