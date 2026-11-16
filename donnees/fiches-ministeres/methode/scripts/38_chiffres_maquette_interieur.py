"""Fiche Intérieur, arbitrage n° 22 : chiffres complémentaires de la maquette. Open data seul.
- sensibilité du chiffre d'ensemble : part de l'Intérieur avec et sans les politiques d'autres ministères déclarées en zone
  Intérieur (médailles d'honneur du travail, décret n° 84-591, art. 16 : « décernée par arrêtés du ministre chargé du travail » ;
  médailles agricoles ; famille logement et hébergement) ; même calcul pour le régime national ;
- étrangers (personnes concernées) répartis selon le calendrier de l'arrêté du 27 avril 2021 (R. 431-2 du CESEDA) :
  avant le 1er mai 2021 (première obligation de téléservice), du 1er mai 2021 au 28 septembre 2022 (dernière date de la liste
  consolidée), après ; par fonction ;
- vérification avant embauche à 7 démarches (décision 4).
Sortie : out/interieur_maquette_chiffres.json (comptes seulement)."""
import json, re, sys
src = open("scripts/34_etrangers_fonctions_interieur.py").read().split("out = {")[0]
exec(src)
P = [r for r in E if r["dep"] == "personne concernée"]
nat = lambda t: (lambda t: "agricole" if "agricole" in t else "travail" if re.search(r"honneur du travail", t) and not re.search(r"regionale|departementale|communale", t) else "autre")(na(t))
MED = "Médailles et distinctions"; LOG = "Logement et hébergement (accords collectifs, contingent, CCAPEX)"
autres = {
    "médailles d'honneur du travail": [r for r in per if r["fam"] == MED and nat(r["title"]) == "travail"],
    "médailles d'honneur agricoles": [r for r in per if r["fam"] == MED and nat(r["title"]) == "agricole"],
    "logement et hébergement": [r for r in per if r["fam"] == LOG],
}
PF = 19888006  # contrôle ci-dessous contre out/interieur.json
I = json.load(open("out/interieur.json")); assert I["plateforme"]["dossiers_total"] == PF and I["perimetre"]["dossiers_total"] == nd(per)
T = nd(per); pct = lambda a, b: round(100 * a / b, 1)
out = {"sensibilite": {"perimetre": [len(per), T, pct(T, PF)], "plateforme_dossiers": PF, "retraits": {}}}
reste = T; reste_n = len(per)
for k, L in autres.items():
    out["sensibilite"]["retraits"][k] = [len(L), nd(L), pct(nd(L), T)]
    reste -= nd(L); reste_n -= len(L)
out["sensibilite"]["sans_autres_ministeres"] = [reste_n, reste, pct(reste, PF)]
tw = nd(autres["médailles d'honneur du travail"])
out["sensibilite"]["sans_medailles_travail"] = [len(per) - len(autres["médailles d'honneur du travail"]), T - tw, pct(T - tw, PF)]
ta = tw + nd(autres["médailles d'honneur agricoles"])  # textes vérifiés : décret n° 84-591 art. 16 ; décret n° 84-1110 art. 16
out["sensibilite"]["sans_medailles_travail_agricoles"] = [len(per) - len(autres["médailles d'honneur du travail"]) - len(autres["médailles d'honneur agricoles"]), T - ta, pct(T - ta, PF)]
N = [r for r in per if r["niv"] == "nationale"]; nN = nd(N)
Nm = [r for r in N if r["fam"] == MED]; Na = [r for r in N if any(r in L for L in autres.values())]
out["national"] = {"total": [len(N), nN, pct(nN, T)], "dont_medailles": [len(Nm), nd(Nm), pct(nd(Nm), nN)],
                   "sans_medailles": [len(N) - len(Nm), nN - nd(Nm), pct(nN - nd(Nm), T - nd([r for r in per if r["fam"] == MED]))],
                   "sans_autres_ministeres": [len(N) - len(Na), nN - nd(Na), pct(nN - nd(Na), reste)]}
L_ = [r for r in per if r["niv"] == "locale"]; out["local"] = [len(L_), nd(L_), pct(nd(L_), T)]
# étrangers, personnes concernées, selon le calendrier de l'arrêté
D1, D2 = "2021-05-01", "2022-09-28"
per_ = lambda r: "avant" if (r["datePublication"] or "") < D1 else ("pendant" if (r["datePublication"] or "")[:10] <= D2 else "après")
anef = {}
for f in ("dépôt d'une demande", "rendez-vous", "contact et renseignement", "complément ou suivi"):
    anef[f] = {}
    for p in ("avant", "pendant", "après"):
        L = [r for r in P if r["fct"] == f and per_(r) == p]
        anef[f][p] = [len(L), nd(L), sum(r["state"] == "publiee" for r in L)]
out["etrangers_calendrier_arrete"] = {"bornes": [D1, D2], "par_fonction": anef,
    "citant_anef_apres": sum(1 for r in P if re.search(r"\bANEF\b", r["title"] or "", re.I) and per_(r) == "après")}
V = json.load(open("out/interieur_verification_embauche.json"))
out["verification"] = {"demarches": len(V), "dossiers": sum(v["dossiers"] for v in V.values()),
    "trois_plus_lourdes": sum(sorted((v["dossiers"] for v in V.values()), reverse=True)[:3]),
    "pieces_min": min(v["pieces_distinctes"] for v in V.values()), "pieces_max": max(v["pieces_distinctes"] for v in V.values()),
    "siret": sum(v["siret"] for v in V.values()), "premiere": min(v["publication"] for v in V.values())[:4], "derniere": max(v["publication"] for v in V.values())[:4]}
json.dump(out, open("out/interieur_maquette_chiffres.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1))
