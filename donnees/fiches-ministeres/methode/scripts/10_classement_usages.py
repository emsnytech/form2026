"""Classement consolidé des usages du périmètre Justice : règles explicites, ordonnées, sur titre et organisme, relues sur les 139 titres normalisés.
Toute démarche non couverte tombe en « À qualifier » (aucun rattrapage implicite). Sortie : out/justice_usages.json et out/justice_usages.csv (audit ligne à ligne).
Usage : python3 scripts/10_classement_usages.py scripts/config_justice.json"""
import json, sys, re, csv, collections as C
cp = sys.argv[1]; sys.argv = ["x", cp, "/dev/null"]
exec(open("scripts/02_fiche_ministere.py").read().split("APIP =")[0])
per = []
for r in rows:
    p, s = classify(r)
    if p and p != "interministeriel": per.append(r)
U = "Usagers, justiciables, professionnels du droit"; P = "Partenaires et événements"; LA = "Promotion interne : listes d'aptitude"
RE = "Recrutement : concours, examens, prise en charge"; F = "Formation : écoles, classes prépa, bourses"; G = "Gestion RH : paie, indemnités, jurys, carrière"; I = "Fonctionnement interne des services"
# Démarches agrégées dans la fiche : désignées par leur numéro, pour qu'aucun titre sensible ne figure dans le dépôt.
AGREGEES = {100049, 123573, 147656}
RULES = [
 (U, r"question au minist|non.appel|restitution de titre|^BAROCPH|prestation de serment\"?$|dossier \"prestation de serment"),
 (P, r"agr[ée]ment des associations|subvention association|subvention acc[èe]s au droit|assister à une audience|r[ée]union du parquet|table ronde"),
 (LA, r"-LA-|\bLA\b.*fiche|liste d.aptitude|-LA "),
 (F, r"pr[ée]pa talents|\bCPT\b|droit à l.image|choix de poste|\bFIO\b|pi[èe]ces administrative|travaux non juridictionnels|cr[èe]che"),
 (G, r"vacations?|indemnit|\bIFM\b|\bIMR\b|mobilit[ée]s durables|nouvel arrivant|reconstitution de carri|reclassement|membre de jury|jury concours"),
 (RE, r"concours|examen profession|prise en charge|\bFIR\b|RAEP|recrutement sans concours"),
 (I, r"régies|autorisation de conduire|t[ée]l[ée]phone portable|relev[ée] d.identit[ée] bancaire|engagement de confidentialit|appel à projet.*Lab"),
]
def cat(r):
    t = r["title"] or ""
    if r["number"] in AGREGEES: return U
    for n, m in RULES:
        if re.search(m, t, re.I): return n
    return "À qualifier"
out = C.defaultdict(list)
for r in per: r["cat"] = cat(r); out[r["cat"]].append(r)
dos = lambda L: sum(x["dossiersCount"] or 0 for x in L)
T = dos(per)
res = {k: {"demarches": len(L), "dossiers": dos(L), "pct_dossiers": round(100 * dos(L) / T, 1), "en_ligne": sum(x["state"] == "publiee" for x in L)} for k, L in out.items()}
ext = [r for r in out[RE] if re.search(r"externe|troisi[èe]me|3[èe]me|3G|sans concours|1er concours", r["title"], re.I)]
inte = [r for r in out[RE] if re.search(r"interne|examen profession|concours professionnel|concours.pro", r["title"], re.I) and r not in ext]
res["_recrutement_detail"] = {"externe_ou_ouvert": [len(ext), dos(ext)], "interne_ou_pro": [len(inte), dos(inte)], "non_tranche": [len(out[RE]) - len(ext) - len(inte), dos([r for r in out[RE] if r not in ext and r not in inte])]}
RH = [r for k in (LA, RE, F, G) for r in out[k]]
res["_total"] = {"perimetre": len(per), "dossiers": T, "rh_formation": len(RH), "rh_dossiers": dos(RH), "rh_pct_demarches": round(100 * len(RH) / len(per), 1), "rh_pct_dossiers": round(100 * dos(RH) / T, 1),
   "dsj_rh": sum(bool(re.search(r"^Direction des services judiciaires|^DSJ", r["organisme"] or "")) for r in per)}
la = lambda r: r["cat"] == LA
res["_stock"] = {y: {"stock": sum(bool(stock(r, y)) for r in per), "stock_hors_LA": sum(bool(stock(r, y)) and not la(r) for r in per), "pub": sum((r["datePublication"] or "")[:4] == str(y) for r in per), "pub_LA": sum((r["datePublication"] or "")[:4] == str(y) and la(r) for r in per)} for y in YEARS}
du = [(fin(r) - d(r["datePublication"])).days for r in per if fin(r)]
res["_duree"] = {"closes": len(du), "mediane_jours": sorted(du)[len(du) // 2], "moins_92j": sum(x < 92 for x in du)}
res["_LA"] = {"demarches": len(out[LA]), "dossiers": dos(out[LA]), "ressorts_par_campagne": C.Counter(re.match(r"(20\d\d-[^-]+)-LA", r["title"]).group(1) for r in out[LA] if re.match(r"(20\d\d-[^-]+)-LA", r["title"])).most_common()}
res["_lille"] = [{k: r[k] for k in ("number", "title", "datePublication", "dateFermeture", "dateDepublication", "state", "dossiersCount", "service_nom")} for r in per if re.search("Lille", r["organisme"] or "") and "Tribunal" in (r["organisme"] or "")]
res["_autres_lille"] = [(r["number"], r["title"][:70], (r["datePublication"] or "")[:10], r["state"], r["dossiersCount"], (r["organisme"] or "")[:30]) for r in rows if re.search(r"non.appel|copie.{0,20}jugement", r["title"] or "", re.I)]
h = open("../../../explorer.html", encoding="utf-8").read()
D = json.loads(re.search(r'<script type="application/json" id="data-dila">(.*?)</script>', h, re.S).group(1))
res["_canaux_justice"] = sorted({re.sub(r"^https?://([^/]+).*", r"\1", x["lien_web_url"]) for x in D if x["modalite"] == "en_ligne" and re.search(r"justice\.(fr|gouv\.fr)|courdecassation", x["lien_web_url"] or "")})
json.dump(res, open("out/justice_usages.json", "w"), ensure_ascii=False, indent=1, default=str)
w = csv.writer(open("out/justice_usages.csv", "w")); w.writerow(["numero", "categorie", "organisme", "titre", "dossiers", "etat"])
for r in sorted(per, key=lambda r: (r["cat"], -(r["dossiersCount"] or 0))): w.writerow([r["number"], r["cat"], r["organisme"], r["title"], r["dossiersCount"], r["state"]])
print(json.dumps(res, ensure_ascii=False, indent=0, default=str))
print("A QUALIFIER:"); [print(r["number"], r["dossiersCount"], r["organisme"][:30], "|", r["title"][:90]) for r in out["À qualifier"]]
print("USAGERS:"); [print(r["number"], r["dossiersCount"], r["title"][:80]) for r in out[U]]
print("PARTEN:"); [print(r["number"], r["dossiersCount"], r["title"][:80]) for r in out[P]]
print("INTERNE:"); [print(r["number"], r["dossiersCount"], r["title"][:80]) for r in out[I]]
