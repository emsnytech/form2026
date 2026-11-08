"""Test : les démarches destinées aux professionnels du droit sont-elles absentes de l'open data ? Cherche dans titre et description du fichier brut.
Usage : python3 scripts/18_professionnels_opendata.py <brut.json>"""
import ijson, re, sys, json, collections as C
RX = re.compile(r"(destin[ée]e?s? aux?|r[ée]serv[ée]e?s? aux?|[àa] destination des|s.adresse aux?|pour les|aux) (seuls? )?(avocats?|notaires?|commissaires? de justice|huissiers?|mandataires? judiciaires?|experts? judiciaires?)", re.I)
RX2 = re.compile(r"\b(avocats?|notaires?|commissaires? de justice|barreaux?|huissiers?)\b", re.I)
H = []; n2 = 0
with open(sys.argv[1], "rb") as f:
    for d in ijson.items(f, "item", use_float=True):
        t = (d.get("title") or "") + " " + (d.get("description") or "")
        if RX2.search(d.get("title") or ""): n2 += 1
        m = RX.search(t)
        if m or RX2.search(d.get("title") or ""):
            s = d.get("service") or {}
            H.append({"n": d.get("number"), "t": (d.get("title") or "")[:80], "o": (s.get("organisme") or "")[:40], "d": d.get("dossiersCount"), "e": d.get("state"), "z": (d.get("zones") or ["SANS"])[0][:22], "ex": (t[max(0, m.start() - 30):m.end() + 40] if m else "").replace("\n", " ")})
json.dump(H, open("out/professionnels_opendata.json", "w"), ensure_ascii=False, indent=0)
print(len(H), "démarches ; titre citant la profession :", n2, "; dossiers", sum(h["d"] or 0 for h in H))
for h in sorted(H, key=lambda h: -(h["d"] or 0))[:35]: print(h["n"], h["e"], h["d"], h["z"], "|", h["o"], "|", h["t"], "|", h["ex"][:90])
