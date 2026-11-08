"""Identification de la n° 124249 et recherche d'un successeur des démarches closes de Lille, à partir des pages publiques. Usage : python3 scripts/17_identification_124249.py"""
import json, re, subprocess, time, datetime as dt, unicodedata
B = "https://demarche.numerique.gouv.fr"
def get(p):
    r = subprocess.run(["curl", "-sS", "-m", "25", "-L", "-A", "Mozilla/5.0 Chrome/130", "-w", "\n@@%{url_effective}", f"{B}/{p}"], capture_output=True, text=True).stdout
    h, _, u = r.rpartition("\n@@"); return h, u
def txt(h):
    t = re.sub(r"<(script|style).*?</\1>", "", h, flags=re.S); t = re.sub(r"<[^>]+>", " ", t); return re.sub(r"\s+", " ", t).replace("&#39;", "'")
out = {"releve": dt.date.today().isoformat()}
c, u = get("commencer/barobaj-2"); s, _ = get("statistiques/barobaj-2"); T = txt(c)
ch = lambda n: re.search(r'"chart-%d", (\[.*?\]), \{' % n, s, re.S)
out["124249"] = {"numero": re.search(r"· #(\d+) ·", c).group(1), "titre": re.search(r"<title>\s*(.*?) ·", c, re.S).group(1), "url": u,
  "objet": re.search(r"Quel est l.objet de la démarche \? (.*?) À qui", T).group(1), "public": re.search(r"À qui s.adresse la démarche \? (.*?) Quelles", T).group(1),
  "gestion": re.search(r"Cette démarche est gérée par (.*?) Une question", T).group(1), "ouverte": "Commencer la démarche" in T, "close": "est close depuis" in T,
  "siret_dans_page": re.findall(r"\b\d{14}\b", c)[:5], "douai_dans_page": len(re.findall("douai", T, re.I)), "avancee": dict(json.loads(ch(2).group(1))), "premier_mois": json.loads(ch(1).group(1))[0][0]}
wk = re.search(r'"chart-4", (\[.*?\]), \{"', s, re.S); W = json.loads(wk.group(1)) if wk else []
acc = W[0]["data"] if W else []; out["124249"]["acceptes_par_semaine"] = acc
cum, tr, y = out["124249"]["avancee"]["Traités"], [], None
for wkname, v in reversed(acc):
    tr.append((wkname, cum)); cum -= v
out["124249"]["traites_cumules_estimes"] = tr[:12]
# Adresses lues dans le descriptif, pour qu'aucun titre sensible ne figure ici. La démarche hors fichier agrégée
# (data/chemins_agreges.json, facultatif et hors dépôt, voir 12_hors_opendata.py) est ignorée si le fichier manque.
import os
_par_num = {json.loads(l)["number"]: json.loads(l) for l in open("data/demarches_slim.jsonl")}
FERM = {n: _par_num[n]["url"].rsplit("/", 1)[1] for n in (99859, 100049, 100409, 100526)}
if os.path.exists("data/chemins_agreges.json"): FERM.update({int(k): v for k, v in json.load(open("data/chemins_agreges.json")).items()})
out["closes"] = {}
for n, p in FERM.items():
    h, u = get("commencer/" + p); t = txt(h)
    hr = sorted({x for x in re.findall(r'href="([^"]+)"', h) if re.search(r"/commencer/|remplac|nouvelle", x) and p not in x})
    m = re.search(r"(est close depuis[^.]{0,60}.{0,500}?)Informations sur la démarche", t)
    out["closes"][n] = {"url": u, "message": m.group(1) if m else None, "liens_commencer": hr, "mot_remplace": bool(re.search(r"remplac|nouvelle démarche|désormais", t, re.I))}
    time.sleep(.25)
J = "lille arras avesnes-sur-helpe avesnes bethune boulogne-sur-mer boulogne cambrai douai dunkerque saint-omer valenciennes hazebrouck ressort ca-douai cour-d-appel-de-douai".split()
cand = [f"barobaj-{j}" for j in J] + [f"baroaj-{j}" for j in J[:12]] + ["barobaj-1", "barobaj-2-0", "barobaj-3-0", "barobaj-v1", "barobaj-version-1", "barobaj-version-2", "barobaj-version-2-0", "barobaj-version-3", "barobaj-3", "barobaj-4"]
cand += [f"demande-de-certificat-de-non-appel-{j}" for j in J] + [f"certificat-de-non-appel-{j}" for j in J] + [f"demande-de-certificat-de-non-appel-et-de-copie-de-{i}" for i in range(1, 6)] + ["demande-de-certificat-de-non-appel-ou-de-copie-de", "demande-de-copie-de-jugement-et-de-certificat-de", "demande-de-copie-de-decision-et-de-certificat-de", "demande-de-copie-de-decision-de-justice", "demande-de-copie-de-jugement", "demande-de-copie-de-jugement-et-certificat-de-non", "copie-de-jugement-et-certificat-de-non-appel", "sauj-lille", "sauj-tribunal-judiciaire-de-lille", "tribunal-judiciaire-de-lille", "tj-lille", "cour-d-appel-douai"]
trouve = []
for p in cand:
    h, u = get("commencer/" + p)
    if "introuvable" not in u:
        m = re.search(r"<title>\s*(.*?)</title>", h, re.S); trouve.append((p, u.replace(B, ""), re.sub(r"\s+", " ", m.group(1))[:110] if m else None))
    time.sleep(.2)
out["sondages"] = {"essais": len(cand), "trouves": trouve}
rows = [json.loads(l) for l in open("data/demarches_slim.jsonl")]
RX = re.compile(r"non.appel|non.opposition.{0,20}jugement|copies?.{0,25}(jugement|d[ée]cision)|certificat.{0,20}(appel|pourvoi)", re.I)
out["base_non_appel"] = [(r["number"], r["state"], r["dossiersCount"], (r["organisme"] or "")[:40], r["title"][:70]) for r in rows if RX.search(r["title"] or "")]
out["base_124249"] = any(r["number"] == 124249 for r in rows)
json.dump(out, open("out/justice_124249.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=0))
