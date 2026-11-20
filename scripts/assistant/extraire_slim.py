#!/usr/bin/env python3
"""Extrait, en flux, le « slim » de l'export complet du descriptif (data.gouv.fr) : une ligne par démarche, toutes états confondus.

Chaque ligne : [numéro, état, date de publication, nombre de dossiers, SIRET du service, organisme, type d'organisme,
département, titre]. C'est l'entrée --slim de build_index.py. Les champs viennent tels quels de l'export (service.siret,
service.organisme, service.typeOrganisme, service.departement) ; aucun autre champ n'est gardé.

    python3 scripts/assistant/extraire_slim.py <export>.json[.gz] <cartographie>/assistant/slim.jsonl
"""
import gzip, json, sys

src, dst = sys.argv[1], sys.argv[2]
ouvrir = gzip.open if src.endswith(".gz") else open
dec = json.JSONDecoder(); n = 0
with ouvrir(src, "rt", encoding="utf-8") as f, open(dst, "w", encoding="utf-8") as out:
    buf = f.read(1 << 20).lstrip()
    assert buf[0] == "["; buf = buf[1:]
    while True:
        buf = buf.lstrip().lstrip(",").lstrip()
        if buf.startswith("]"): break
        try:
            obj, i = dec.raw_decode(buf)
        except json.JSONDecodeError:
            more = f.read(1 << 22)
            if not more: break
            buf += more; continue
        buf = buf[i:]; n += 1
        s = obj.get("service") or {}
        out.write(json.dumps([obj.get("number"), obj.get("state"), obj.get("datePublication"), obj.get("dossiersCount"), s.get("siret"),
                              s.get("organisme"), s.get("typeOrganisme"), s.get("departement"), obj.get("title")], ensure_ascii=False) + "\n")
        if len(buf) < 1 << 20:
            more = f.read(1 << 22)
            if more: buf += more
print(n, "démarches")
