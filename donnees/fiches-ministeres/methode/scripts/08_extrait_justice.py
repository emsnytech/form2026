"""Extrait du fichier brut les démarches utiles à la fiche Justice, avec tous leurs champs (libellés, descriptions, types) :
zone « Ministère de la Justice » ou organisme évoquant le monde judiciaire, quelle que soit sa zone (sert à mesurer les rattachements),
ou titre évoquant les démarches sous condition de ressources (comparaison plateforme, section 8).
Usage : python3 08_extrait_justice.py <brut.json> <sortie.jsonl>"""
import ijson, json, re, sys
ORG = re.compile(r"justice|garde des sceaux|tribunal|cour d.appel|cour de cassation|prud.?homme|juridiction|judiciaire|greffe|magistrature|\bENM\b|\bENG\b|\bENAP\b|p[ée]nitentiaire|\bSPIP\b|\bDISP\b|\bPJJ\b|protection judiciaire|\bCDAD\b|acc[èe]s au droit|maison d.arr[êe]t|centre de d[ée]tention|d[ée]tention|\bSADJAV\b|\bDACG\b|\bDACS\b|\bDAP\b|\bDSJ\b|\bAGRASC\b|barreau|avocat|notaire|commissaires? de justice", re.I)
n = k = 0
with open(sys.argv[1], "rb") as f, open(sys.argv[2], "w") as out:
    for p in ijson.items(f, "item", use_float=True):
        n += 1
        s = p.get("service") or {}
        o = (s.get("organisme") or "") + " | " + (s.get("nom") or "")
        if "Ministère de la Justice" in (p.get("zones") or []) or ORG.search(o):
            rev = p.get("revision") or {}
            out.write(json.dumps({"number": p.get("number"), "title": p.get("title"), "description": p.get("description"),
                "cadreJuridiqueURL": p.get("cadreJuridiqueURL"), "service": s, "zones": p.get("zones"),
                "champs": rev.get("champDescriptors"), "annotations": rev.get("annotationDescriptors")}, ensure_ascii=False, default=str) + "\n")
            k += 1
print(n, "lues", k, "retenues")
