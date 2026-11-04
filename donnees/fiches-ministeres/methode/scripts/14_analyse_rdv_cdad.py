"""Exploite out/scan_rdv_cdad.jsonl : CDAD trouvés et leurs déclarations, croisement avec les 20 CDAD du tableau de bord RDV Service Public, mentions RDV Service Public sur tout le corpus."""
import json, re, collections as C
H = [json.loads(l) for l in open("out/scan_rdv_cdad.jsonl")]
ORGCDAD = re.compile(r"conseils? d[ée]partementa(l|ux) de l.acc[èe]s au droit|\bCDAD\b|point[- ]justice|maisons? de justice|acc[èe]s au droit", re.I)
FAUX = re.compile(r"CCAS|centre communal|Nantes", re.I)
org = [h for h in H if ORGCDAD.search((h["organisme"] or "") + " | " + (h["service"] or "")) and not FAUX.search(h["organisme"] or "")]
print("== Organisme ou service d'accès au droit :", len(org), sum(h["dossiers"] or 0 for h in org))
for h in sorted(org, key=lambda h: (h["organisme"] or "")): print(h["number"], h["state"], h["dossiers"], h["dep"], h["type"], (h["zones"] or ["SANS"])[0][:26], (h["organisme"] or "")[:38], "|", (h["service"] or "")[:30], "|", h["title"][:60])
men = [h for h in H if h["cdad"] and h not in org]
print("\n== Mention CDAD/point-justice dans le contenu, autre organisme :", len(men))
print(C.Counter(x["ou"] for h in men for x in h["cdad"]).most_common(10))
for h in sorted(men, key=lambda h: -(h["dossiers"] or 0))[:18]: print(h["number"], h["dossiers"], (h["organisme"] or "")[:30], "|", h["title"][:50], "|", h["cdad"][0]["ou"], "|", h["cdad"][0]["extrait"][:120])
R = [h for h in H if h["rdvsp"]]
print("\n== RDV Service Public, tout le corpus :", len(R), "démarches", sum(h["dossiers"] or 0 for h in R), "dossiers")
print("émetteurs distincts (SIRET)", len({h["siret"] for h in R if h["siret"]}), "libellés", len({(h["organisme"] or "").strip().lower() for h in R}))
print("états", C.Counter(h["state"] for h in R)); print("types", C.Counter(h["type"] for h in R).most_common())
print("zones", C.Counter((h["zones"] or ["SANS"])[0][:30] for h in R).most_common(10))
print("où", C.Counter(x["ou"] for h in R for x in h["rdvsp"]).most_common(12))
print("adresses", C.Counter(m.lower() for h in R for x in h["rdvsp"] for m in re.findall(r"rdv[-.][a-z.-]+|rdv service public|rdv solidarit[ée]s|rdv aide num[ée]rique|rdv mairie", x["extrait"], re.I)).most_common(14))
for h in sorted(R, key=lambda h: -(h["dossiers"] or 0)): print(h["number"], h["state"], h["dossiers"], h["dep"], (h["zones"] or ["SANS"])[0][:18], (h["organisme"] or "")[:34], "|", h["title"][:50], "|", h["rdvsp"][0]["ou"], "|", h["rdvsp"][0]["extrait"][60:170])
print("\n== Autres : tiers", len([h for h in H if h["tiers"]]), C.Counter(m.lower() for h in H for x in h["tiers"] for m in re.findall(r"doctolib|calendly|synbird|clicrdv|rdv360|maiia|bookings", x["extrait"], re.I)).most_common(8), "| rdv générique", len([h for h in H if h["gen"]]))
per = {json.loads(l)["number"] for l in open("data/justice_champs.jsonl")}
print("Justice : rdv générique", [(h["number"], h["dossiers"], (h["organisme"] or "")[:25], h["title"][:50], h["gen"][0]["ou"]) for h in H if h["gen"] and h["number"] in per and "Ministère de la Justice" in (h["zones"] or []) and len(h["zones"]) <= 3][:14])
T = "Seine-Maritime Eure Gard Moselle Val-de-Marne Gironde Eure-et-Loir Loire Saône-et-Loire Seine-Saint-Denis Haute-Garonne Meurthe-et-Moselle Vaucluse Ardennes Manche Vienne Loire-Atlantique Mayenne Ain Haute-Corse".split()
CODE = dict(zip(T, "76 27 30 57 94 33 28 42 71 93 31 54 84 08 50 86 44 53 01 2B".split()))
print("\n== Croisement 20 CDAD")
rows = [json.loads(l) for l in open("data/demarches_slim.jsonl")]
for t in T:
    rx = re.compile(r"(CDAD|acc[èe]s au droit).{0,30}" + re.escape(t) + r"\b|" + re.escape(t) + r".{0,30}(CDAD|acc[èe]s au droit)|CDAD\s*" + CODE[t] + r"\b", re.I)
    m = [r for r in rows if rx.search((r["organisme"] or "") + " | " + (r["service_nom"] or "") + " | " + (r["title"] or ""))]
    print(t, CODE[t], len(m), sum(r["dossiersCount"] or 0 for r in m), [(r["number"], r["dossiersCount"], (r["zones"] or ["SANS"])[0][:14], r["title"][:34]) for r in m][:4])
