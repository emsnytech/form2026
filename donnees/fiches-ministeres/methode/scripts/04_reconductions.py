"""Distingue, parmi les démarches publiées chaque année, les reconductions (même émetteur, même titre hors millésime, déjà publié une année antérieure) des nouveaux usages."""
import json, re, sys, unicodedata, collections
cfg_path, out_path = sys.argv[1], sys.argv[2]
sys.argv=["x", cfg_path, "/dev/null"]
exec(open("scripts/02_fiche_ministere.py").read().split("APIP =")[0])
YR=re.compile(r"(rentr[ée]e|session|ann[ée]e( scolaire| universitaire)?|campagne)?\s*\(?\b(19|20)\d\d\s*([-/–]\s*((19|20)?\d\d))?\)?", re.I)
def norm(t):
    t=YR.sub(" ", t or "")
    t=unicodedata.normalize("NFKD", t).encode("ascii","ignore").decode().lower()
    t=re.sub(r"[^a-z0-9]+"," ",t)
    return " ".join(w for w in t.split() if len(w)>2)[:120]
def org(r): return re.sub(r"\s+"," ",(r["organisme"] or "").strip().lower())
def run(sub):
    seen={}; res=[]
    for r in sorted(sub, key=lambda r: r["datePublication"] or ""):
        k=(org(r), norm(r["title"]))
        y=int(r["datePublication"][:4])
        r["_reconduction"]= k in seen and seen[k] < y
        seen.setdefault(k, y)
    for y in range(2021, 2027):
        pub=[r for r in sub if r["datePublication"][:4]==str(y)]
        rec=sum(r["_reconduction"] for r in pub)
        res.append({"annee":y,"publiees":len(pub),"reconductions":rec,"nouvelles":len(pub)-rec,"pct_reconductions":round(100*rec/len(pub),1) if pub else None})
    return res
per=[r for r in rows if (lambda p:p[0] and p[0]!="interministeriel")(classify(r)) and r["datePublication"]]
plat=[r for r in rows if r["datePublication"]]
out={"perimetre":run(per),"plateforme":run(plat)}
json.dump(out,open(out_path,"w"),ensure_ascii=False,indent=1)
for k,v in out.items(): print(k); [print(" ",x) for x in v]
