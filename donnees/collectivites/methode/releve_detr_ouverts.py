#!/usr/bin/env python3
"""Relevé daté, sur les pages publiques de statistiques, des formulaires DETR encore en ligne qui exigent la délibération.
Les pages ne datent pas les dépôts : on relève les décisions rendues par semaine sur six mois et le dernier mois de traitement,
qui disent si un formulaire est encore instruit. Sources publiques seules.

Usage : python3 releve_detr_ouverts.py ../etat_demande.json ../detr_formulaires_ouverts.json"""
import datetime as dt, html, json, re, sys, time, urllib.request
E = json.load(open(sys.argv[1], encoding="utf-8"))["resume"]["detr_ouverts_qui_exigent"]
out = []
for x in E:
    path = x["url"].rstrip("/").rsplit("/", 1)[1]
    t = html.unescape(urllib.request.urlopen(urllib.request.Request("https://demarche.numerique.gouv.fr/statistiques/" + path, headers={"User-Agent": "Mozilla/5.0 (FORM 2026)"}), timeout=30).read().decode())
    ch = {m.group(1): m.group(2) for m in re.finditer(r'"(chart-\d+)",\s*(\[.*?\])\s*,\s*\{', t, re.S)}
    av = dict(json.loads(ch["chart-2"])) if "chart-2" in ch else {}
    mois = [a for a, _ in json.loads(ch["chart-1"])] if "chart-1" in ch else []
    sem = json.loads(ch["chart-4"]) if "chart-4" in ch else []
    decisions = sorted({w for s in sem for (w, v) in s.get("data", []) if v})
    out.append({**x, "deposes": av.get("Déposés"), "dernier_mois_traite": mois[-1] if mois else None, "semaines_avec_decision_6_mois": len(decisions), "instruit_dans_les_6_mois": bool(decisions)})
    time.sleep(0.3)
json.dump({"releve": dt.date.today().isoformat(), "formulaires": out, "actifs": sum(o["instruit_dans_les_6_mois"] for o in out), "reliquats": sum(not o["instruit_dans_les_6_mois"] for o in out)},
          open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(out), "formulaires ;", sum(o["instruit_dans_les_6_mois"] for o in out), "instruits dans les six derniers mois")
