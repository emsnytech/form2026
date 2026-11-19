"""Extrait, en flux, les descriptions des démarches publiées de l'export complet du descriptif (data.gouv.fr).

    python3 scripts/assistant/extraire_descriptions.py <export>.json <cartographie>/assistant/descriptions_publiees.jsonl
"""
import json,sys
src,dst=sys.argv[1],sys.argv[2]
dec=json.JSONDecoder(); buf=''; n=k=0
out=open(dst,'w')
with open(src,encoding='utf-8') as f:
    buf=f.read(1<<20).lstrip()
    assert buf[0]=='['; buf=buf[1:]
    eof=False
    while True:
        buf=buf.lstrip().lstrip(',').lstrip()
        if buf.startswith(']'): break
        try:
            obj,i=dec.raw_decode(buf)
        except json.JSONDecodeError:
            more=f.read(1<<22)
            if not more: break
            buf+=more; continue
        buf=buf[i:]; n+=1
        if obj.get('state')!='publiee': continue
        k+=1
        z=[x.get('label') if isinstance(x,dict) else x for x in (obj.get('zones') or [])]
        out.write(json.dumps([obj.get('number'),(obj.get('description') or '')[:700],obj.get('demarcheURL'),obj.get('forIndividual'),z,obj.get('dateFermeture')],ensure_ascii=False)+'\n')
        if len(buf)<1<<20:
            more=f.read(1<<22)
            if more: buf+=more
print(n,k)
