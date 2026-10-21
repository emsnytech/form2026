"""Projette la géométrie simplifiée des départements en chemins SVG (viewBox 0 0 640 560) :
métropole à droite, DROM en encarts à gauche, petite couronne parisienne agrandie, COM en vignettes."""
import json, math
g = json.load(open("deps.json"))
W, H = 640, 560
def rings(geom):
    return geom["coordinates"] if geom["type"] == "Polygon" else [r for p in geom["coordinates"] for r in p]
def bbox(feats):
    xs, ys = [], []
    for f in feats:
        for r in rings(f["geometry"]):
            for x, y in r: xs.append(x); ys.append(y)
    return min(xs), min(ys), max(xs), max(ys)
def fit(feats, box, lat0):
    x0, y0, x1, y1 = bbox(feats); c = math.cos(math.radians(lat0))
    bx, by, bw, bh = box
    k = min(bw / ((x1 - x0) * c), bh / (y1 - y0))
    ox = bx + (bw - (x1 - x0) * c * k) / 2; oy = by + (bh - (y1 - y0) * k) / 2
    return lambda x, y: (ox + (x - x0) * c * k, oy + (y1 - y) * k)
def path(f, P):
    out = []
    for r in rings(f["geometry"]):
        pts = [P(x, y) for x, y in r]
        out.append("M" + "L".join(f"{a:.1f},{b:.1f}" for a, b in pts) + "Z")
    return "".join(out)
F = {f["properties"]["code"]: f for f in g["features"]}
DROM = ["971", "972", "973", "974", "976"]
metro = [f for c, f in F.items() if c not in DROM]
res = {"viewBox": f"0 0 {W} {H}", "deps": {}, "frames": []}
P = fit(metro, (130, 10, 505, 540), 46.5)
for f in metro: res["deps"][f["properties"]["code"]] = {"n": f["properties"]["nom"], "d": path(f, P)}
# encarts DROM
y = 10
for c in DROM:
    box = (8, y, 100, 64); f = F[c]
    res["deps"][c] = {"n": f["properties"]["nom"], "d": path(f, fit([f], (box[0] + 6, box[1] + 14, box[2] - 12, box[3] - 18), (bbox([f])[1] + bbox([f])[3]) / 2))}
    res["frames"].append({"x": box[0], "y": box[1], "w": box[2], "h": box[3], "l": f["properties"]["nom"]})
    y += 72
# petite couronne agrandie
pc = [F[c] for c in ("75", "92", "93", "94")]
box = (130, 10, 110, 96)
Pp = fit(pc, (box[0] + 6, box[1] + 16, box[2] - 12, box[3] - 22), 48.85)
for f in pc: res["deps"][f["properties"]["code"] + "_z"] = {"n": f["properties"]["nom"], "d": path(f, Pp), "ref": f["properties"]["code"]}
res["frames"].append({"x": box[0], "y": box[1], "w": box[2], "h": box[3], "l": "Paris et petite couronne"})
# collectivités d'outre-mer (sans géométrie) : vignettes
coms = [("975", "Saint-Pierre-et-Miquelon"), ("977", "Saint-Barthélemy"), ("978", "Saint-Martin"),
        ("986", "Wallis-et-Futuna"), ("987", "Polynésie française"), ("988", "Nouvelle-Calédonie")]
res["com"] = []
for i, (c, n) in enumerate(coms):
    x = 8 + (i % 3) * 34; yy = y + 6 + (i // 3) * 34
    res["com"].append({"c": c, "n": n, "x": x, "y": yy, "s": 30})
res["frames"].append({"x": 8, "y": y - 4, "w": 104, "h": 0, "l": "Collectivités d'outre-mer"})
json.dump(res, open("carte_departements.json", "w"), ensure_ascii=False, separators=(",", ":"))
print(len(res["deps"]), round(len(json.dumps(res)) / 1024), "Ko", "y fin", y + 74)
