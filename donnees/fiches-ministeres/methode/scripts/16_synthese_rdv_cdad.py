"""Synthèse des deux instances (RDV Solidarités, RDV Service Public) à partir de out/rdv_cdad_metabase.json. Usage : python3 scripts/16_synthese_rdv_cdad.py"""
import json, re, collections as C, unicodedata
D = json.load(open("out/rdv_cdad_metabase.json"))["cartes"]
def card(tab, name, n=None):
    L = [c for c in D if c["onglet"].strip() == tab.strip() and c["carte"] == name]
    return L[0]["lignes"] if n is None else [c for c in L if len(c["colonnes"]) == n][0]["lignes"]
def norm(t):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    t = re.sub(r"cdad\s*(de la |de l'|des |de |du )?", "", t); return re.sub(r"[^a-z]+", "-", t).strip("-")
TS = C.Counter(); TP = C.Counter()
for n, v in card("Déploiement - RDV S ", "Nombre RDV CDAD par territoire"): TS[norm(n)] += v
for n, v in card("Déploiement - RDV SP", "Nombre RDV CDAD par territoire - RDVSP", 2): TP[norm(n)] += v
print("RDV Solidarités : territoires", len(TS), "somme", sum(TS.values()), "| carte Nombre", card("Déploiement - RDV S ", "Nombre RDV CDAD"), "| statuts", sum(v for _, v in card("Déploiement - RDV S ", "Nombre RDV CDAD - par service")), "| services", sum(v for _, v in card("Déploiement - RDV S ", "Nombre RDV CDAD par services")))
print("RDV Service Public : territoires", len(TP), "somme", sum(TP.values()), "| carte Nombre", card("Déploiement - RDV SP", "Nombre RDV CDAD  (RDVSP)"))
print("présents sur les deux :", set(TS) & set(TP))
A = TS + TP; print("Ensemble : territoires", len(A), "somme", sum(A.values())); print("seuils : >=100", sum(v >= 100 for v in A.values()), ">=1000", sum(v >= 1000 for v in A.values()), "<100", {k: v for k, v in A.items() if v < 100})
print("top", A.most_common(12))
MS = card("Déploiement - RDV S ", "Nombre RDV CDAD par territoire - Duplicate"); MP = card("Déploiement - RDV SP", "Nombre RDV CDAD par territoire - RDVSP", 3)
Y = {"S": C.Counter(), "P": C.Counter()}; act = {"S": C.defaultdict(set), "P": C.defaultdict(set)}; vol = {"S": C.defaultdict(C.Counter), "P": C.defaultdict(C.Counter)}
for k, M in (("S", MS), ("P", MP)):
    for n, m, v in M:
        Y[k][m[:4]] += v; act[k][m[:7]].add(norm(n)); vol[k][norm(n)][m[:7]] += v
print("par année", {k: dict(sorted(v.items())) for k, v in Y.items()}, "ensemble", dict(sorted((Y["S"] + Y["P"]).items())))
print("premiers mois", {k: min(act[k]) for k in act})
for m in ("2024-06","2024-11", "2025-01", "2025-06", "2025-11", "2026-01", "2026-04", "2026-07", "2026-10"):
    print(m, "actifs S", len(act["S"][m]), "P", len(act["P"][m]), "total", len(act["S"][m] | act["P"][m]))
print("nouveaux territoires par année", {k: dict(sorted(C.Counter(min(vol[k][n])[:4] for n in vol[k]).items())) for k in vol})
print("oct 2026 volume S", sum(c["2026-10"] for c in vol["S"].values()), "P", sum(c["2026-10"] for c in vol["P"].values()))
print("statuts", card("Déploiement - RDV S ", "Nombre RDV CDAD - par service"))
print("Org. territoires SP (dont sans RDV)", sorted({l[1] for l in card("Déploiement - RDV SP", "Organisations par CDAD RDVSP") if l[1]} ))
print("agents", card("Déploiement - RDV SP", "Nombre agent CDAD - RDV SP"), "S par service somme", sum(v for _, v in card("Déploiement - RDV S ", "Nombre agent CDAD")))
Se = sorted(card("Déploiement - RDV S ", "Nombre RDV CDAD par services"), key=lambda x: -x[1])[:10]; print("services", Se)
H = [json.loads(l) for l in open("out/scan_rdv_cdad.jsonl")]; R = [h for h in H if h["rdvsp"]]
lien = [h for h in R if any(re.search(r"rdv\.anct\.gouv\.fr", x["extrait"], re.I) for x in h["rdvsp"]) and not re.search("webinaire|AMI ", h["title"], re.I)]
pub = [h for h in lien if any(not x["ou"].startswith("annotation") for x in h["rdvsp"])]
print("DN : démarches avec lien réel", len(lien), sum(h["dossiers"] or 0 for h in lien), "vers l'usager (hors annotation seule)", len(pub), sum(h["dossiers"] or 0 for h in pub), "SIRET", len({h["siret"] for h in pub if h["siret"]}), "libellés", len({(h["organisme"] or "").lower().strip() for h in pub}))
print("mention sans lien", [(h["number"], h["title"][:50]) for h in R if h not in lien])
