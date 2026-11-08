"""Parcourt tout le fichier brut. Pour chaque démarche, examine toutes les chaînes (titre, description, notice, service, libellés et descriptions de champs, annotations, options)
et relève : (1) les adresses et noms de RDV Service Public, (2) les autres mentions de rendez-vous, (3) les outils tiers, (4) les organismes d'accès au droit.
Usage : python3 scripts/13_scan_rdv_cdad.py <brut.json> out/scan_rdv_cdad.jsonl"""
import ijson, json, re, sys, collections as C
RDVSP = re.compile(r"rdv[-.]?service[-.]?public|rdv\.anct\.gouv|rdv[-.]solidarit|rdv[-.]aide[-.]num|rdv[-.]mairie|rdv\.inclusion|rdv-insertion|rdv\.gouv|rendez-vous\.service-public|RDV[ -]Service[ -]Public|RDV[ -]Solidarit[ée]s|RDV[ -]Aide[ -]Num[ée]rique|RDV[ -]Mairie|anct\.gouv\.fr[^ ]*rdv", re.I)
TIERS = re.compile(r"doctolib|calendly|synbird|clicrdv|rdv360|mon-?rdv|maiia|acuity|zcal|cal\.com|bookings\.|microsoft bookings|sendinblue meet|rendezvous\.|agendize|rdvdirect", re.I)
GEN = re.compile(r"prise de (rendez-vous|rdv)|prendre (un |votre |le )?(rendez-vous|rdv)|rendez-vous en ligne|\brdv\b", re.I)
CDAD = re.compile(r"conseils? d[ée]partementa(l|ux) de l.acc[èe]s au droit|\bCDAD\b|point[- ]justice|points[- ]justice|maisons? de justice et du droit|\bMJD\b|\bPAD\b.{0,20}acc[èe]s au droit|point d.acc[èe]s au droit|relais d.acc[èe]s au droit", re.I)
def walk(o, p=""):
    if isinstance(o, dict):
        for k, v in o.items(): yield from walk(v, p + "/" + k if p else k)
    elif isinstance(o, list):
        for v in o: yield from walk(v, p + "[]")
    elif isinstance(o, str): yield p, o
def loc(p):
    if p.startswith("service"): return "service:" + p.split("/")[-1]
    if "annotationDescriptors" in p: return "annotation:" + p.split("/")[-1]
    if "champDescriptors" in p: return "champ:" + p.split("/")[-1]
    return p.split("/")[-1]
n = k = 0
with open(sys.argv[1], "rb") as f, open(sys.argv[2], "w") as out:
    for d in ijson.items(f, "item", use_float=True):
        n += 1; hits = {"rdvsp": [], "tiers": [], "gen": [], "cdad": []}
        for p, s in walk(d):
            if p.endswith("__typename"): continue
            for key, rx in (("rdvsp", RDVSP), ("tiers", TIERS), ("gen", GEN), ("cdad", CDAD)):
                m = rx.search(s)
                if m: hits[key].append({"ou": loc(p), "extrait": s[max(0, m.start() - 90):m.end() + 90].replace("\n", " ")})
        if any(hits.values()):
            sv = d.get("service") or {}
            out.write(json.dumps({"number": d.get("number"), "title": d.get("title"), "state": d.get("state"), "zones": d.get("zones"), "dossiers": d.get("dossiersCount"), "organisme": sv.get("organisme"), "service": sv.get("nom"), "type": sv.get("typeOrganisme"), "siret": sv.get("siret"), "dep": sv.get("departement"), "pub": d.get("datePublication"), "url": d.get("demarcheURL"), **{a: b[:6] for a, b in hits.items()}}, ensure_ascii=False, default=str) + "\n"); k += 1
print(n, "lues", k, "avec au moins une mention")
