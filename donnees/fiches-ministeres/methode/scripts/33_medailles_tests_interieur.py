"""Fiche Intérieur, compléments de l'étape 1 (arbitrage n° 21) : médailles découpées par nature et par niveau ;
démarches « TEST » du périmètre ; provenance (zone / nom d'organisme) par famille. Open data seul.
Sortie : out/interieur_complements_etape1.json"""
import json, re, sys, collections as C
sys.argv = ["x", "scripts/config_interieur.json", "/dev/null"]
exec(open("scripts/32_local_national_interieur.py").read().split("clusters = []")[0])
nd = lambda L: sum(r["dossiersCount"] or 0 for r in L)
med = [r for r in per if r["fam"] == "Médailles et distinctions"]
def nature(t):
    t = na(t)
    if "agricole" in t: return "agricole"
    if re.search(r"regionale|departementale|communale", t): return "régionale, départementale et communale"
    if re.search(r"honneur du travail", t): return "travail"
    if re.search(r"remise de medailles|ceremonie", t): return "cérémonies"
    return "autres (sécurité intérieure, courage et dévouement, transports, jeunesse et sports, administration territoriale)"
tab = C.defaultdict(lambda: C.defaultdict(list))
for r in med: tab[nature(r["title"])][r["niv"]].append(r)
out = {"medailles": {n: {niv: {"demarches": len(L), "dossiers": nd(L), "numeros": [x["number"] for x in sorted(L, key=lambda x: -(x["dossiersCount"] or 0))[:6]]} for niv, L in v.items()} for n, v in tab.items()},
       "medailles_total": {"demarches": len(med), "dossiers": nd(med)}}
TEST = re.compile(r"\btest|\bessai\b|\bbrouillon\b|ne pas utiliser|\bxxx\b|betagouv", re.I)
tst = [r for r in per if TEST.search(na((r["title"] or "") + " | " + (r["organisme"] or "")))]
out["tests"] = {"demarches": len(tst), "dossiers": nd(tst), "par_famille": dict(C.Counter(r["fam"] for r in tst))}
out["provenance_par_famille"] = {f: {"zone": [len([r for r in per if r["fam"] == f and r["src"] != "nom_organisme"]), nd([r for r in per if r["fam"] == f and r["src"] != "nom_organisme"])],
    "nom_organisme": [len([r for r in per if r["fam"] == f and r["src"] == "nom_organisme"]), nd([r for r in per if r["fam"] == f and r["src"] == "nom_organisme"])]} for f in sorted({r["fam"] for r in per})}
json.dump(out, open("out/interieur_complements_etape1.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1))
