"""Extraction allégée du descriptif DN : une ligne JSON par démarche (métadonnées + profil des champs).
Retire au passage les e-mails et numéros de téléphone saisis par erreur dans les champs de texte libre
(title, organisme, service_nom) — voir confidentialite.py."""
import ijson, json, sys, collections, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from confidentialite import nettoyer
src, dst = sys.argv[1], sys.argv[2]

def walk(descs, c):
    for d in descs or []:
        t = d.get("__typename", "?")
        c[t] += 1
        for k in ("champDescriptors", "children"):
            if isinstance(d.get(k), list):
                walk(d[k], c)

n = 0
with open(src, "rb") as f, open(dst, "w") as out:
    for p in ijson.items(f, "item", use_float=True):
        rev = p.get("revision") or {}
        c = collections.Counter()
        walk(rev.get("champDescriptors"), c)
        ca = collections.Counter()
        walk(rev.get("annotationDescriptors"), ca)
        s = p.get("service") or {}
        out.write(json.dumps({
            "number": p.get("number"), "title": nettoyer(p.get("title")), "state": p.get("state"),
            "forIndividual": p.get("forIndividual"), "declarative": p.get("declarative"),
            "tags": p.get("tags"), "zones": p.get("zones"),
            "dateCreation": p.get("dateCreation"), "datePublication": p.get("datePublication"),
            "dateDepublication": p.get("dateDepublication"), "dateFermeture": p.get("dateFermeture"),
            "dossiersCount": p.get("dossiersCount"),
            "service_nom": nettoyer(s.get("nom")), "organisme": nettoyer(s.get("organisme")),
            "typeOrganisme": s.get("typeOrganisme"), "departement": s.get("departement"), "siret": s.get("siret"),
            "url": p.get("demarcheURL"),
            "champs_types": dict(c), "n_champs": sum(c.values()),
            "n_annotations": sum(ca.values()),
            "keys": sorted(p.keys()) if n == 0 else None,
        }, ensure_ascii=False) + "\n")
        n += 1
print(n, "démarches")
