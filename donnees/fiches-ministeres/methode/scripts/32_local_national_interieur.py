"""Fiche Intérieur, étape 2 (a) : du local au national. Open data seul.
Règle fixée avant lecture des résultats :
- « version » = une démarche du périmètre ; « locale » si son organisme, son service ou son titre nomme un territoire
  (préfecture ou sous-préfecture d'un lieu, DDT/DDTM/DDETS/UD/SGCD, nom ou numéro de département, nom de région,
  préfecture de police) ; « nationale » si aucun territoire n'est nommé et que l'émetteur est central ou générique
  (ministère, direction générale, « préfecture de département », « en fonction du département ») ; sinon indéterminée.
  Le champ département et le type d'organisme ne sont pas utilisés : ils ne sont pas fiables pour les démarches nationales.
- « famille de titres » = groupe de titres de même noyau : à l'intérieur d'une famille de l'étape 1, titres normalisés
  (minuscules, sans accents, sans territoire, nombres, mots vides ni mots d'organisme), regroupés autour d'un titre
  graine par similarité de Jaccard >= 0,5 (graines par dossiers décroissants : pas de chaînage).
- dénominateur : familles de titres d'au moins 10 versions locales. Elles « ont une version nationale » si au moins une
  version nationale y figure ; « consolidées » si la version nationale la plus ancienne est postérieure à la première
  version locale et qu'au moins la moitié des versions locales ouvertes à cette date ont fermé dans les 18 mois qui suivent.
- variante, ajoutée après lecture (des « nationales » à 1 dossier sont des trames ou des tests) : mêmes tests, en ne retenant
  que les versions nationales d'au moins 100 dossiers.
Sortie : out/interieur_local_national.json"""
import json, re, sys, unicodedata, datetime as dt, collections as C
sys.argv = ["x", "scripts/config_interieur.json", "/dev/null"]
exec(open("scripts/02_fiche_ministere.py").read().split("APIP =")[0])
per = [r for r in rows if (lambda c: c[0] and c[0] != "interministeriel" and r.update(src=c[1]) is None)(classify(r))]
FAM = json.load(open("scripts/familles_interieur.json"))
def famille(r):
    for f in FAM:
        if re.search(f["motif"], r["title"] or "", re.I): return f["nom"]
    return "Autres, non classées"
def na(s): return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
DEP = """ain aisne allier alpes-de-haute-provence hautes-alpes alpes-maritimes ardeche ardennes ariege aube aude aveyron
bouches-du-rhone calvados cantal charente charente-maritime cher correze corse-du-sud haute-corse cote-d'or cotes-d'armor creuse
dordogne doubs drome eure eure-et-loir finistere gard haute-garonne gers gironde herault ille-et-vilaine indre indre-et-loire
isere jura landes loir-et-cher loire haute-loire loire-atlantique loiret lot lot-et-garonne lozere maine-et-loire manche marne
haute-marne mayenne meurthe-et-moselle meuse morbihan moselle nievre nord oise orne pas-de-calais puy-de-dome
pyrenees-atlantiques hautes-pyrenees pyrenees-orientales bas-rhin haut-rhin rhone haute-saone saone-et-loire sarthe savoie
haute-savoie paris seine-maritime seine-et-marne yvelines deux-sevres somme tarn tarn-et-garonne var vaucluse vendee vienne
haute-vienne vosges yonne territoire-de-belfort essonne hauts-de-seine seine-saint-denis val-de-marne val-d'oise guadeloupe
martinique guyane reunion mayotte polynesie nouvelle-caledonie saint-pierre-et-miquelon saint-martin saint-barthelemy wallis
auvergne-rhone-alpes bourgogne-franche-comte bretagne centre-val normandie hauts-de-france grand-est occitanie
nouvelle-aquitaine pays-de-la-loire provence-alpes-cote paca ile-de-france corse idf""".split()
DEPRX = "|".join(sorted({re.escape(d).replace(r"\-", "[- ]") for d in DEP}, key=len, reverse=True))
AMBIGUS = {"ain", "aube", "aude", "cher", "lot", "var", "nord", "orne", "manche", "somme", "loire", "marne", "vienne", "indre", "gard", "eure", "landes", "gers", "jura", "oise", "tarn", "creuse", "allier", "meuse", "doubs", "cantal", "centre-val", "corse", "paris", "reunion", "loiret", "sarthe", "mayenne", "vendee", "yonne", "isere", "drome", "rhone", "savoie", "vosges", "moselle", "ardennes", "dordogne", "charente", "correze", "lozere", "ariege", "herault"}
DEPRX_T = "|".join(sorted({re.escape(x).replace(r"\-", "[- ]") for x in DEP if x not in AMBIGUS}, key=len, reverse=True))
LOCAL_T = re.compile(r"(sous[- ])?pr[e]fecture (de|du|des|d'|de la|de l')\s*(?!departement|region\b)|sous[- ]prefecture|prefecture de police"
    r"|\bpref\s?\d|\bdd(t|tm|ets|etspp|pp|cspp)\s?\d|\bud\s?0?\d\d|\bsgcd\s?\d|\bsgc\s?\d|\(\s*(0[1-9]|[1-8]\d|9[0-5]|2a|2b|97[1-6])\s*\)|^\s*(0[1-9]|[1-8]\d|9[0-5])\s?-"
    r"|departement (de|du|des|d')\s?(la |l')?(" + DEPRX + r")|\b(" + DEPRX_T + r")\b", re.I)
LOCAL = re.compile(r"(sous[- ])?pr[e]fecture (de|du|des|d'|de la|de l')\s*(?!departement|region\b)|sous[- ]prefecture|prefecture de police"
    r"|prefecture de departement\s+(?!$)\S|prefecture\s?\d|\bpref\s?\d|\bdd(t|tm|ets|etspp|pp|cspp|i)(\b|\d)|\bud\s?\d|\bsgcd\b|\bsgc\s?\d|\bsgar\b|\bdreal\b|\bdriea|\bdrieets?\b|\bdreets\b|\bdirecct"
    r"|\b(0[1-9]|[1-8]\d|9[0-5]|2a|2b|97[1-6])\b|\b(" + DEPRX + r")\b", re.I)
NATIONAL = re.compile(r"minist[e]re|direction g[e]n[e]rale|\bdg[a-z]{1,4}\b|prefecture de departement|en fonction du departement|\bants\b|france titres|\bofii\b|\bofpra\b|sous-direction|delegation a la securite routiere|\bdsr\b|\bdlpaj\b|\bdgcl\b|\bdgef\b|\bdgpn\b|\bdggn\b", re.I)
def niveau(r):
    o = na((r["organisme"] or "") + " | " + (r["service_nom"] or "")); t = na(r["title"])
    if re.search(r"en fonction du departement", o) or (re.search(r"prefecture de departement\s*($|\|)", o)) or (NATIONAL.search(o) and not LOCAL.search(o)):
        return "locale" if LOCAL_T.search(t) else "nationale"
    if LOCAL.search(o) or LOCAL_T.search(t): return "locale"
    return "indeterminee"
VIDES = set("de du des la le les l d un une et ou en au aux a pour par sur dans avec sans vos votre mon ma mes prefecture sous departement departemental departementale region regional regionale service services bureau direction etat demande demandes formulaire dossier ministere interieur".split())
def noyau(r):
    t = re.sub(r"\b(" + DEPRX + r")\b", " ", na(r["title"]))
    t = re.sub(r"[^a-z]+", " ", t)
    return {w for w in t.split() if len(w) > 2 and w not in VIDES}
def jac(a, b): return len(a & b) / len(a | b) if a | b else 0
grp = C.defaultdict(list)
for r in per: r["niv"] = niveau(r); r["noy"] = noyau(r); r["fam"] = famille(r); grp[r["fam"]].append(r)
clusters = []
for fam, L in grp.items():
    seeds = []
    for r in sorted(L, key=lambda r: -(r["dossiersCount"] or 0)):
        for s in seeds:
            if jac(s["seed"], r["noy"]) >= 0.5: s["m"].append(r); break
        else: seeds.append({"seed": r["noy"], "titre": r["title"], "fam": fam, "m": [r]})
    clusters += seeds
nd = lambda L: sum(r["dossiersCount"] or 0 for r in L)
res = []
for c in clusters:
    loc = [r for r in c["m"] if r["niv"] == "locale"]; nat = [r for r in c["m"] if r["niv"] == "nationale"]
    if len(loc) < 10: continue
    p0 = min(d(r["datePublication"]) for r in loc)
    x = {"famille": c["fam"], "titre_graine": c["titre"], "versions": len(c["m"]), "locales": len(loc), "nationales": len(nat),
         "emetteurs_locaux": len({na(r["organisme"]).strip() for r in loc}), "dossiers_locaux": nd(loc), "dossiers_nationaux": nd(nat),
         "premiere_locale": str(p0), "derniere_locale": str(max(d(r["datePublication"]) for r in loc)),
         "locales_ouvertes_aujourdhui": sum(r["state"] == "publiee" for r in loc), "consolidee": False}
    if nat:
        n0 = min(d(r["datePublication"]) for r in nat); x["premiere_nationale"] = str(n0)
        x["nationales_detail"] = [(r["number"], str(d(r["datePublication"])), r["state"], r["dossiersCount"]) for r in sorted(nat, key=lambda r: r["datePublication"])]
        ouv = [r for r in loc if d(r["datePublication"]) <= n0 and (fin(r) is None or fin(r) > n0)]
        fer = [r for r in ouv if fin(r) and fin(r) <= n0 + dt.timedelta(days=548)]
        x["locales_ouvertes_a_la_nationale"] = len(ouv); x["fermees_18_mois"] = len(fer)
        x["locales_publiees_apres_nationale"] = sum(d(r["datePublication"]) > n0 for r in loc)
        x["consolidee"] = n0 > p0 and len(ouv) > 0 and len(fer) >= len(ouv) / 2
    nat100 = [r for r in nat if (r["dossiersCount"] or 0) >= 100]
    x["nationales_100"] = len(nat100); x["consolidee_100"] = False
    if nat100:
        n1 = min(d(r["datePublication"]) for r in nat100); x["premiere_nationale_100"] = str(n1)
        ouv = [r for r in loc if d(r["datePublication"]) <= n1 and (fin(r) is None or fin(r) > n1)]
        fer = [r for r in ouv if fin(r) and fin(r) <= n1 + dt.timedelta(days=548)]
        x["ouvertes_100"] = len(ouv); x["fermees_18_mois_100"] = len(fer); x["recul_jours_100"] = (d(ASOF) - n1).days
        x["consolidee_100"] = n1 > p0 and len(ouv) > 0 and len(fer) >= len(ouv) / 2
    res.append(x)
res.sort(key=lambda x: -(x["dossiers_locaux"] + x["dossiers_nationaux"]))
out = {"niveaux": dict(C.Counter(r["niv"] for r in per)), "niveaux_dossiers": {k: nd([r for r in per if r["niv"] == k]) for k in ("locale", "nationale", "indeterminee")},
       "familles_de_titres_total": len(clusters), "familles_10_locales": len(res),
       "avec_nationale": sum(1 for x in res if x["nationales"]), "consolidees": sum(1 for x in res if x["consolidee"]),
       "avec_nationale_100": sum(1 for x in res if x["nationales_100"]), "consolidees_100": sum(1 for x in res if x["consolidee_100"]), "detail": res}
json.dump(out, open("out/interieur_local_national.json", "w"), ensure_ascii=False, indent=1, default=str)
print({k: v for k, v in out.items() if k != "detail"})
for x in res: print(x["locales"], x["emetteurs_locaux"], x["nationales"], x["consolidee"], x["dossiers_locaux"], x["dossiers_nationaux"], x["premiere_locale"], x.get("premiere_nationale", ""), x.get("locales_ouvertes_a_la_nationale", ""), x.get("fermees_18_mois", ""), x.get("locales_publiees_apres_nationale", ""), x["locales_ouvertes_aujourdhui"], "|", x["famille"][:20], "|", (x["titre_graine"] or "")[:70])
