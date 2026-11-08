#!/usr/bin/env python3
"""Relève sur les pages publiques de la plateforme ce que le descriptif open data ne contient pas :
les démarches d'experts judiciaires et la première version de BARÔBAJ.

Usage (depuis fiches-ministeres) : python3 scripts/22_experts_publics.py
Entrées : pages /statistiques/<adresse> de demarche.numerique.gouv.fr, data/demarches_slim.jsonl.
Sortie : out/justice_experts_publics.json, sans aucune donnée d'une source interne.
Ces chiffres sont cités dans la fiche, jamais ajoutés à ses totaux."""
import datetime as dt, html, json, re, urllib.request

BASE = "https://demarche.numerique.gouv.fr/statistiques/"
EXPERTS = {
    131020: ("Campagne nationale 2026", "experts-judiciaires-inscription-initiale-campagne-"),
    131018: ("Campagne nationale 2026", "experts-judiciaires-reinscription-campagne-nationa"),
    131021: ("Campagne nationale 2026", "experts-judiciaires-extension-d-inscription-campag"),
    99291: ("Cour d'appel d'Aix-en-Provence", "experts-inscription-initiale-ca-aix-en-provence"),
    99307: ("Cour d'appel d'Aix-en-Provence", "experts-reinscription-ca-aix-en-provence"),
    99303: ("Cour d'appel d'Aix-en-Provence", "experts-extension-d-inscription-ca-aix-en-provence"),
    107318: ("Cour d'appel de Bordeaux", "experts-inscription-initiale-ca-bordeaux"),
    107325: ("Cour d'appel de Bordeaux", "experts-reinscription-ca-bordeaux"),
    107324: ("Cour d'appel de Bordeaux", "experts-extension-d-inscription-ca-bordeaux"),
    140620: ("Cour d'appel de Nouméa", "ca-noumea-experts-judiciaires-reinscription-prorog"),
}
BAROBAJ_V1 = (86649, "barobaj")


def releve(numero, adresse):
    req = urllib.request.Request(BASE + adresse, headers={"User-Agent": "Mozilla/5.0 (FORM 2026)"})
    t = html.unescape(urllib.request.urlopen(req, timeout=30).read().decode("utf-8"))
    titre = re.sub(r"\s+", " ", re.search(r"<title>(.*?)</title>", t, re.S).group(1)).strip()
    m = re.match(r"Statistiques · (.*?) · #(\d+)", titre)
    assert m and int(m.group(2)) == numero, (numero, titre)
    avancee = {k: int(v) for k, v in re.findall(r'\["(Tous \(dont brouillon\)|Déposés|Instruction débutée|Traités)",\s*(\d+)\]', t)}
    assert "Déposés" in avancee, numero
    return {"numero": numero, "titre": m.group(1), "url": BASE + adresse, "avancee": avancee}


dans_fichier = {json.loads(l)["number"] for l in open("data/demarches_slim.jsonl")}
experts = []
for numero, (groupe, adresse) in EXPERTS.items():
    experts.append({"groupe": groupe, **releve(numero, adresse)})
v1 = releve(*BAROBAJ_V1)
absentes = {x["numero"] for x in experts} | {v1["numero"]}
assert not absentes & dans_fichier, absentes & dans_fichier

deposes = lambda g: sum(x["avancee"]["Déposés"] for x in experts if x["groupe"] == g)
sortie = {
    "releve": dt.date.today().isoformat(),
    "source": BASE,
    "absentes_du_fichier_du_21_octobre_2026": True,
    "experts": experts,
    "experts_deposes": sum(x["avancee"]["Déposés"] for x in experts),
    "experts_deposes_par_groupe": {g: deposes(g) for g in dict.fromkeys(x["groupe"] for x in experts)},
    "barobaj_v1": v1,
}
json.dump(sortie, open("out/justice_experts_publics.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(sortie["releve"], sortie["experts_deposes"], sortie["experts_deposes_par_groupe"], "| BARÔBAJ v1 :", v1["titre"], v1["avancee"])
