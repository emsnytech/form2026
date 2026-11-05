"""Démarches du périmètre Justice absentes de l'open data : relève leurs compteurs sur les pages publiques /statistiques de la plateforme,
puis recalcule le périmètre. Usage : python3 scripts/12_hors_opendata.py"""
import json, os, re, subprocess, datetime as dt
B = "https://demarche.numerique.gouv.fr"
US = "Usagers, justiciables, professionnels du droit"
AGREGEE = 99723  # agrégée dans la fiche : ni son titre ni son adresse ne sont publiés
ITEMS = {"barobaj-2": US}
# L'adresse de la démarche agrégée vient d'un fichier local facultatif et hors dépôt : {"99723": "<adresse>"}.
# Sans lui, son dernier relevé publié est conservé, avec sa date d'origine dans « releve_agregee ».
CHEMINS = json.load(open("data/chemins_agreges.json")) if os.path.exists("data/chemins_agreges.json") else {}
if str(AGREGEE) in CHEMINS: ITEMS[CHEMINS[str(AGREGEE)]] = US
def get(p): return subprocess.run(["curl", "-sS", "-m", "30", "-L", "-A", "Mozilla/5.0 Chrome/130", f"{B}/{p}"], capture_output=True, text=True).stdout
res = {"releve": dt.date.today().isoformat(), "demarches": []}
for path in ITEMS:
    h = get("statistiques/" + path); c = get("commencer/" + path)
    n = re.search(r"· #(\d+) ·", h); t = re.search(r"<title>\s*(?:Statistiques · )?(.*?) ·", h, re.S)
    a = re.search(r'"chart-2", \[(.*?)\], \{', h); av = dict(json.loads("[" + a.group(1) + "]")) if a else {}
    d = re.search(r'"chart-1", (\[.*?\]), \{', h); dl = json.loads(d.group(1)) if d else []
    f = re.search(r"est close depuis le ([^<]+?)\s*<", c)
    num = int(n.group(1)) if n else None
    agregee = num == AGREGEE
    res["demarches"].append({"path": None if agregee else path, "numero": num, "titre": "Démarche agrégée dans la fiche" if agregee else (t.group(1).strip() if t else None), "avancee": av, "delai_moyen_par_mois": dl, "close_depuis": None if agregee else (f.group(1) if f else None)})
if str(AGREGEE) not in CHEMINS:
    prec = json.load(open("out/justice_hors_opendata.json"))
    res["demarches"].append(next(x for x in prec["demarches"] if x["numero"] == AGREGEE))
    res["releve_agregee"] = prec.get("releve_agregee", prec["releve"])
rows = [json.loads(l) for l in open("data/demarches_slim.jsonl")]
print("présentes dans l'extrait :", [x["numero"] for x in res["demarches"] if x["numero"] in {r["number"] for r in rows}])
u = json.load(open("out/justice_usages.json")); T = u["_total"]; pl = sum(r["dossiersCount"] or 0 for r in rows)
add = sum(x["avancee"].get("Déposés", 0) for x in res["demarches"]); k = len(res["demarches"])
Tn, Td = T["perimetre"] + k, T["dossiers"] + add
res["recalcul"] = {"demarches": Tn, "dossiers": Td, "part_du_fichier_demarches": round(100 * Tn / (len(rows) + k), 2), "part_du_fichier_dossiers": round(100 * Td / (pl + add), 2),
  "rh": T["rh_formation"], "rh_pct_demarches": round(100 * T["rh_formation"] / Tn, 1), "rh_pct_dossiers": round(100 * T["rh_dossiers"] / Td, 1),
  "usagers": u[US]["demarches"] + k, "usagers_dossiers": u[US]["dossiers"] + add, "usagers_pct_dossiers": round(100 * (u[US]["dossiers"] + add) / Td, 1),
  "contact_pct": round(100 * 10006 / Td, 1), "dsj_pct": round(100 * T["dsj_rh"] / Tn, 1), "ajout_dossiers": add}
res["ecart_plateforme"] = {"extrait_demarches": len(rows), "extrait_dossiers": pl, "stats_demarches_24_10": 60192, "stats_dossiers_24_10": 22679986, "ecart_dossiers": 22679986 - pl, "ecart_dossiers_pct": round(100 * (22679986 - pl) / 22679986, 1)}
json.dump(res, open("out/justice_hors_opendata.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=0))
