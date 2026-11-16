"""Fiche Intérieur, étape 1 : classement des démarches du périmètre en familles (premier motif de titre qui correspond).
Open data seul (data/demarches_slim.jsonl). Affiche, par famille, démarches, dossiers et part des dossiers,
puis les N titres non classés les plus lourds, pour réviser scripts/familles_interieur.json.
Usage : python3 scripts/30_classement_interieur.py [N]"""
import json, re, sys, collections as C
N = int(sys.argv[1]) if len(sys.argv) > 1 else 40
sys.argv = ["x", "scripts/config_interieur.json", "/dev/null"]
exec(open("scripts/02_fiche_ministere.py").read().split("APIP =")[0])
per = [r for r in rows if (lambda c: c[0] and c[0] != "interministeriel")(classify(r))]
FAM = json.load(open("scripts/familles_interieur.json"))
for f in FAM: f["rx"] = re.compile(f["motif"], re.I)
T = sum(r["dossiersCount"] or 0 for r in per)
res = C.defaultdict(list)
for r in per:
    for f in FAM:
        if f["rx"].search(r["title"] or ""): res[f["nom"]].append(r); break
    else: res["autres"].append(r)
for k in [f["nom"] for f in FAM] + ["autres"]:
    m = res[k]; dd = sum(r["dossiersCount"] or 0 for r in m)
    print(f"{len(m):6d} {dd:9d} {100*dd/T:5.1f}%  {k}")
for r in sorted(res["autres"], key=lambda r: -(r["dossiersCount"] or 0))[:N]:
    print(r["dossiersCount"], r["number"], (r["organisme"] or "")[:30], "|", (r["title"] or "")[:110])
