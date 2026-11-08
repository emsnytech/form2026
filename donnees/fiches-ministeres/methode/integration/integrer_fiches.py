#!/usr/bin/env python3
"""Publie les fiches ministères à partir de la méthode du dépôt. Seul point d'entrée, idempotent.

Écrit fiches-ministeres/<slug>.html, fiches-ministeres/index.html, les données publiées, la liste de donnees/index.html
et methode/index.html, puis synchronise la navigation. Ne fait ni commit ni push. Ne touche pas à la page d'accueil.
La réserve de méthode vient des gabarits : le script refuse d'écrire une page qui ne la porte pas.

    python3 integration/integrer_fiches.py             # écrit
    python3 integration/integrer_fiches.py --verifier  # n'écrit rien, sort en erreur si le résultat diffère du dépôt

Sans sorties locales (out/, fiche/fiche-*.html), --verifier part des données publiées et ne contrôle pas les pages de fiche.
"""
import argparse, html, json, re, subprocess, sys
from pathlib import Path

METHODE = Path(__file__).resolve().parents[1]
REPO = METHODE.parents[2]
D = METHODE.parent
SITE = "https://emsnytech.github.io/form2026/"
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / "scripts"))
from controle_fiches import COURRIEL, RESERVE, SENSIBLE, fichiers_publies  # noqa: E402

ap = argparse.ArgumentParser(); ap.add_argument("--verifier", action="store_true"); A = ap.parse_args()
M = json.load(open(METHODE / "integration/fiches.json", encoding="utf-8"))
OUT = METHODE / "out"
NAV_VIDE = "<!-- nav:début --><!-- nav:fin -->"
ecarts = []


def sans_nav(t):
    return re.sub(r"<!-- nav:début -->.*?<!-- nav:fin -->", NAV_VIDE, t, flags=re.S)


def controle(nom, t):
    if COURRIEL.search(t): sys.exit(f"adresse électronique dans {nom}")
    if SENSIBLE.search(t): sys.exit(f"titre sensible dans {nom}")


def ecrire(p, t):
    ancien = p.read_text(encoding="utf-8") if p.exists() else None
    if ancien is not None and sans_nav(ancien) == sans_nav(t): return
    ecarts.append(str(p.relative_to(REPO)))
    if not A.verifier: p.write_text(t, encoding="utf-8")


def taille(n):
    return f"{n} o" if n < 1024 else (f"{round(n / 1024)} Ko" if n < 1024 ** 2 else f"{n / 1024 ** 2:.1f} Mo")


def source_json(nom):
    return OUT / nom if (OUT / nom).exists() else D / nom


# 1. Pages des fiches
def page_fiche(f, src):
    s = src.read_text(encoding="utf-8")
    s = s[s.index("<title>"):]
    s = re.sub(r"<title>.*?</title>\s*", "", s, count=1, flags=re.S)
    s = re.sub(r'<meta name="claude:viewport-fit-sides"[^>]*>\s*', "", s)
    i = s.index("</style>") + len("</style>")
    tete, corps = s[:i], s[i:]
    corps, n = re.subn(r'<p class="topnav">.*?</p>', f'<p class="topnav" data-rubrique="situer">{NAV_VIDE}</p>', corps, count=1, flags=re.S)
    if n != 1: sys.exit(f"{f['slug']} : barre de navigation introuvable")
    corps = corps.replace(f'href="{SITE}"', 'href="../index.html"').replace(f'href="{SITE}', 'href="../')
    corps = corps.replace(f'const SIM = "{SITE}', 'const SIM = "../')
    titre, desc = html.escape(f["titre_page"]), html.escape(f["description"])
    url = f"{SITE}fiches-ministeres/{f['slug']}.html"
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{titre}</title>
<meta name="description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:locale" content="fr_FR">
<meta property="og:site_name" content="FORM 2026">
<meta property="og:title" content="{titre}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary">
{tete.strip()}
</head>
<body>
{corps.strip()}
</body>
</html>
"""


pages_controlees = 0
for f in M["fiches"]:
    src = METHODE / f["source"]
    if not src.exists():
        if A.verifier: continue
        sys.exit(f"Fiche introuvable : {src} (lancer d'abord rejouer.sh)")
    page = page_fiche(f, src)
    controle(f["slug"], page)
    if RESERVE not in page: sys.exit(f"{f['slug']} : réserve de méthode absente, page non écrite")
    if re.search(r"«\w+»", page): sys.exit(f"{f['slug']} : marqueur non remplacé")
    ecrire(REPO / "fiches-ministeres" / f"{f['slug']}.html", page)
    pages_controlees += 1


# 2. Index
def nf(x): return f"{x:,}".replace(",", " ")
def m1(x): return f"{x / 1e6:.1f}".replace(".", ",")


def kpis_education():
    E = json.load(open(source_json("education.json"), encoding="utf-8"))
    X = json.load(open(source_json("education_complements.json"), encoding="utf-8"))
    a0, a1 = E["annees"][0], E["annees"][-1]
    dos = sum(d["estime_brut"] for d in X["dossiers_annuels"])
    return [(nf(a1["stock_fin_annee"]), f"démarches en ligne ({nf(a0['stock_fin_annee'])} fin {a0['annee']})"),
            (f"{m1(dos)} M", "dossiers déposés sur la période (estimation)"),
            (f"{m1(X['gains']['bas'])} à {m1(X['gains']['haut'])} M€", "de frais évités, administration et usagers")]


def kpis_justice():
    K = json.load(open(source_json("justice_chiffres_fiche.json"), encoding="utf-8"))["K"]
    return [(K["total"], "démarches du corpus"), (K["dossiers"], "dossiers"), (f"{K['rh_pct']} %", "des démarches du corpus relèvent de la fonction RH")]


KPIS = {"education": kpis_education, "justice": kpis_justice}
cartes = []
for f in M["fiches"]:
    kp = "".join(f'<div class="k"><b>{v}</b><span>{l}</span></div>' for v, l in KPIS[f["slug"]]())
    cartes.append(f"""<a class="fiche" href="{f['slug']}.html">
      <span class="q">Fiche disponible</span>
      <h3>{html.escape(f['titre'])}</h3>
      <div class="kpis">{kp}</div>
      <span class="go">Ouvrir la fiche →</span>
      <span class="meta">{html.escape(f['carte_meta'])}</span>
    </a>""")
ix = (METHODE / "fiche/gabarit_index.html").read_text(encoding="utf-8")
if ix.count("<!--CARTES_FICHES-->") != 1 or RESERVE not in ix: sys.exit("gabarit de l'index : cartes ou réserve introuvables")
ix = ix.replace("<!--CARTES_FICHES-->", "\n    ".join(cartes))
controle("index", ix)
ecrire(REPO / "fiches-ministeres/index.html", ix)

# 3. Données publiées
noms = [n for f in M["fiches"] for n in f["donnees"]]
if OUT.exists():
    for nom in noms:
        src = OUT / nom
        if not src.exists(): sys.exit(f"sortie manquante : {src}")
        t = src.read_text(encoding="utf-8")
        controle(nom, t)
        ecrire(D / nom, t)

# 4. Index de la méthode et rubrique de donnees/index.html
PIED = """<h2>Règle du dépôt</h2><p>Ce qui produit une page publiée vit dans ce dépôt et se rejoue depuis lui : voir <a href="REJOUER.md">REJOUER.md</a>.</p>
<p><b>Une exception.</b> Le script de comparaison à une extraction interne (n° 21) reste hors du dépôt public, parce qu'il lit une source interne que le lecteur ne peut pas consulter. Aucun chiffre publié n'en dépend : il a seulement servi à décider des réserves de méthode.</p>
<p><a href="../LISEZMOI_fiches-ministeres.md">LISEZMOI</a> · <a href="../../index.html">Données dérivées</a></p>"""
liste = [r for _, r in fichiers_publies(METHODE) if r != "index.html"]
ecrire(METHODE / "index.html", '<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><title>FORM 2026 — Fiches ministères, méthode</title></head><body><h1>Scripts et configurations des fiches ministères</h1><ul>'
       + "".join(f'<li><a href="{r}">{r}</a></li>' for r in liste) + "</ul>\n" + PIED + "\n</body></html>\n")

p = REPO / "donnees/index.html"
di = p.read_text(encoding="utf-8")
lignes = ['<li><a href="fiches-ministeres/LISEZMOI_fiches-ministeres.md">LISEZMOI</a>'
          f'<span class="sz">{taille((D / "LISEZMOI_fiches-ministeres.md").stat().st_size)}</span></li>']
for nom in noms:
    t = source_json(nom).read_bytes()
    lignes.append(f'<li><a href="fiches-ministeres/{nom}">{nom}</a><span class="sz">{taille(len(t))}</span></li>')
lignes.append('<li><a href="fiches-ministeres/methode/">methode/ (scripts et configurations)</a><span class="sz"></span></li>')
di, n = re.subn(r'(<section class="grp" id="fiches-ministeres">.*?<ul class="filelist">\n).*?(\n\s*</ul>)', lambda m: m.group(1) + "  " + "\n".join(lignes) + m.group(2), di, count=1, flags=re.S)
if n != 1: sys.exit("donnees/index.html : rubrique introuvable")
nb = sum(1 for _ in D.glob("*") if _.is_file()) + sum(1 for _ in fichiers_publies(METHODE))
total = len(re.findall(r'<li><a href="(?!fiches-ministeres/)[^"]+">', di)) + nb
di = re.sub(r'<span class="badge">\d+ fichiers</span>', f'<span class="badge">{total} fichiers</span>', di, count=1)
ecrire(p, di)

# 5. Navigation et bilan
if not A.verifier:
    subprocess.run([sys.executable, str(REPO / "scripts/sync_nav.py")], check=True, stdout=subprocess.DEVNULL)
print(f"{pages_controlees} page(s) de fiche contrôlée(s) ; fichiers {'à modifier' if A.verifier else 'modifiés'} : {len(ecarts)}")
for e in ecarts: print("  " + e)
if A.verifier and ecarts: sys.exit(1)
