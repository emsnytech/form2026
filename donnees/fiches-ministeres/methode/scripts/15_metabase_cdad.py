"""Relève toutes les cartes du tableau de bord public RDV Service Public pour les CDAD. Usage : python3 scripts/15_metabase_cdad.py"""
import json, subprocess, datetime as dt
U = "84e59905-144c-4b2f-b12a-ed639e6e27e6"; M = "https://rdv-service-public-metabase.osc-secnum-fr1.scalingo.io"
get = lambda p: json.loads(subprocess.run(["curl", "-sS", "-m", "40", M + p], capture_output=True, text=True).stdout)
D = get(f"/api/public/dashboard/{U}"); tabs = {t["id"]: t["name"] for t in D["tabs"]}; out = {"releve": dt.date.today().isoformat(), "cartes": []}
for c in D["dashcards"]:
    k = c.get("card") or {}
    if not k.get("id"): continue
    try:
        r = get(f"/api/public/dashboard/{U}/dashcard/{c['id']}/card/{k['id']}"); d = r.get("data") or {}
        cols = [x.get("display_name") or x.get("name") for x in d.get("cols", [])]; rows = d.get("rows", [])
    except Exception as e: cols, rows = ["ERR"], [[str(e)]]
    out["cartes"].append({"onglet": tabs.get(c.get("dashboard_tab_id")), "carte": k.get("name"), "colonnes": cols, "lignes": rows})
json.dump(out, open("out/rdv_cdad_metabase.json", "w"), ensure_ascii=False, indent=0, default=str)
for x in out["cartes"]:
    print("\n##", x["onglet"], "|", x["carte"], "|", x["colonnes"], "|", len(x["lignes"]), "lignes")
    L = x["lignes"]
    for l in (L if len(L) <= 28 else L[:10] + [["..."]] + L[-4:]): print("  ", str(l)[:150])
