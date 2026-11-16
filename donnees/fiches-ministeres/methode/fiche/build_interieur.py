"""Génère la fiche Intérieur (fiche n° 3). Reprend le style des fiches n° 1 et 2 (CSS commun de gabarit_fiche.html)
sans le dupliquer. Le texte vient de la maquette validée (out/maquette_interieur.md, produite par scripts/39) : une seule source
de texte ; ce script ne fait que la mettre en page et calcule depuis out/*.json les chiffres de l'en-tête.
Usage (depuis donnees/fiches-ministeres/methode) : python3 fiche/build_interieur.py
Sortie : fiche/fiche-interieur.html. S'arrête si la page contient une adresse électronique, un numéro de téléphone, un nom de
département, ou si la réserve de méthode manque."""
import json, re, os, html, unicodedata
from pathlib import Path

SITE = Path(__file__).resolve().parents[4]   # racine du dépôt
REF = SITE / "donnees/fiches-ministeres/methode/fiche/gabarit_fiche.html"
J = lambda n: json.load(open(f"out/{n}.json"))
I, LN, ET, VA, MC = J("interieur"), J("interieur_local_national"), J("interieur_etrangers"), J("interieur_variete"), J("interieur_maquette_chiffres")
FE = J("interieur_frais_evites")
CARTE = J("interieur_carte")["departements"]
GEO = json.load(open(Path(__file__).resolve().parent / "carte_departements.json"))
MD = Path("out/maquette_interieur.md").read_text()

NB = " "
def n(x): return f"{round(x):,}".replace(",", NB)
def M(x): return f"{x/1e6:.2f}".replace(".", ",") + " M"
def p(x): return f"{x:.1f}".replace(".", ",") + " %"
def pc(a, b): return p(100 * a / b)
def ME(x): return f"{x/1e6:.1f}".replace(".", ",") + " M€"
MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre']
def d(s): j = int(s[8:10]); return f"{j}{'er' if j == 1 else ''} {MOIS[int(s[5:7]) - 1]} {s[:4]}"

# ---------- markdown de la maquette -> HTML ----------
def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    return t
NUM = re.compile(r"^[\d \s,./%()…–-]+(M|doss\.)?[\d \s,./%()–-]*$")
def table(lines):
    rows = [[c.strip() for c in l.strip().strip("|").split("|")] for l in lines]
    head, body = rows[0], [r for r in rows[2:]]
    rc = [i for i in range(len(head)) if i > 0 and all(NUM.match(r[i] or "0") for r in body if i < len(r))]
    th = "".join(f'<th scope="col"{" class=\"r\"" if i in rc else ""}>{inline(h)}</th>' for i, h in enumerate(head))
    tb = "".join("<tr>" + "".join(f'<td{" class=\"r\"" if i in rc else ""}>{inline(c)}</td>' for i, c in enumerate(r)) + "</tr>" for r in body)
    return f'<div class="tbl"><table><thead><tr>{th}</tr></thead><tbody>{tb}</tbody></table></div>'
NETTOIE = [(r"^\*\*(Chapeau|Phrase-clé|Phrase-clé, en constat)\.\*\* ", ""), (r"^\*\*Limite, en tête\.\*\*", "**Limite.**"),
           (r" \(depuis l'origine, aucun département nommé\)", " (depuis l'origine)")]
def bloc(md):
    out, buf, tab, lst = [], [], [], []
    def flush():
        nonlocal buf, tab, lst
        if buf:
            t = " ".join(buf)
            for a, b in NETTOIE: t = re.sub(a, b, t)
            out.append(f"<p>{inline(t)}</p>") if not t.startswith("> ") else out.append(f'<blockquote><p>{inline(t[2:])}</p></blockquote>')
        if tab: out.append(table(tab))
        if lst: out.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in lst) + "</ul>")
        buf, tab, lst = [], [], []
    for l in md.split("\n"):
        if not l.strip(): flush(); continue
        if l.startswith("|"):
            if buf or lst: flush()
            tab.append(l); continue
        if l.startswith("- "):
            if buf or tab: flush()
            lst.append(l[2:]); continue
        if tab or lst: flush()
        buf.append(l)
    flush()
    # paragraphes et listes dans une colonne de lecture ; tableaux en pleine largeur, comme dans les fiches n° 1 et 2
    res, col = [], []
    for x in out:
        if x.startswith('<div class="tbl"'):
            if col: res.append('<div class="col">' + "".join(col) + "</div>"); col = []
            res.append(x)
        else: col.append(x)
    if col: res.append('<div class="col">' + "".join(col) + "</div>")
    return "\n".join(res)

sections = {int(m.group(1)): (m.group(2), m.group(3)) for m in re.finditer(r"^## (\d+)\. ([^\n]+)\n(.*?)(?=^## |\Z)", MD, re.S | re.M)}
entete = sections[1][1]
def para(md, label):
    m = re.search(r"^\*\*" + re.escape(label) + r"\*\*\s*(.*)$", md, re.M); return m.group(1) if m else None
titre = para(entete, "Titre.").split(" : ", 1)[1].rstrip(".")
chapeau = para(entete, "Chapeau.")
perimetre = para(entete, "Un périmètre approché.")
sens = "\n".join(l for l in entete.split("\n") if l.startswith("|"))
sens_note = next(l for l in entete.split("\n") if l.startswith("Ces médailles"))

# ---------- cadre d'entrée : même phrase centrale que sync_cadre.py ----------
sc = (SITE / "scripts/sync_cadre.py").read_text()
mm = re.search(r"^STATS = '(.*?)'\n", sc, re.M); STATS = mm.group(1)
mc = re.search(r"^CENTRE = \((.*?)\)\n", sc, re.S | re.M)
import ast
CENTRE = "".join(STATS if x == "STATS" else ast.literal_eval(x) for x in re.findall(r'"(?:[^"\\]|\\.)*"|STATS', mc.group(1)))
cadre1 = ("<b>Ce que cette fiche décrit.</b> Elle porte sur les démarches de ce ministère publiées dans le descriptif ouvert de la plateforme, et non sur l'ensemble de ses démarches dématérialisées. "
          + CENTRE + " Les parts données ci-dessous portent donc sur un corpus publié, et non sur l'activité complète du ministère.")
cadre2 = "<b>Comment les démarches sont rattachées à ce ministère.</b> " + inline(perimetre)

# ---------- chiffres de l'en-tête (calculés depuis out/) ----------
P = I["perimetre"]; PF = I["plateforme"]; S = MC["sensibilite"]; AP = VA["A"]["prefectures"]; qo = AP["en_ligne_par_departement"]
fcl = AP["familles_couvertes_en_ligne"]; ND = VA["regles"]["departements"]; B = VA["B"]; TA = VA["taille"]
fn = ET["par_fonction_personne"]; dep = ET["par_deposant"]
V = MC["verification"]; po = VA["C"]["police et gendarmerie"]
assert VA["B"]["vérification avant embauche"]["departements"] == V["demarches"]
etroit = sum(v for k, v in fcl.items() if int(k) <= 3)
KPI = [
    (n(P["total"]), f"démarches dans le corpus, soit {pc(P['total'], PF['total'])} du fichier ouvert de la plateforme", None),
    (M(P["dossiers_total"]), f"dossiers, soit {p(S['perimetre'][2])} de ceux du fichier ; {p(S['sans_medailles_travail_agricoles'][2])} sans les médailles du travail et agricoles", None),
    (f"{ME(FE['perimetre']['gains']['bas'])[:-3]} à {ME(FE['perimetre']['gains']['haut'])}", f"de frais évités de {FE['periode'][0]} à {FE['periode'][1]}, administration et usagers (méthode FORM 2026) ; "
     f"{ME(FE['sans_medailles_travail_agricoles']['gains']['bas'])[:-3]} à {ME(FE['sans_medailles_travail_agricoles']['gains']['haut'])} sans les médailles du travail et agricoles", "#profil"),
    (f"{n(qo['q1'])} à {n(qo['q3'])}", "démarches de préfecture en ligne par département, du premier au troisième quart", "#appropriation"),
    (f"{n(fcl.get('7', 0))} <small>/ {ND}</small>", f"départements couvrent en ligne les sept familles de politiques ; {n(etroit)} en couvrent trois ou moins", "#appropriation"),
    (f"{LN['avec_nationale_100']} <small>/ {LN['familles_10_locales']}</small>", "familles de titres locales ayant reçu une version nationale d'au moins 100 dossiers", "#national"),
    (f"{n(V['demarches'])} <small>/ {ND}</small>", f"départements ont une démarche de vérification d'un titre avant embauche ({n(V['dossiers'])} dossiers), sans version nationale", "#national"),
    (p(po['part_rh_dossiers']), "des dossiers des démarches de la police et de la gendarmerie relèvent de la RH et de l'action sociale", "#services"),
    (M(dep["personne concernée"][1]), f"dossiers des démarches « étrangers » déposées par les personnes concernées, dont {n(fn['rendez-vous']['dossiers'])} de demandes de rendez-vous", "#etrangers"),
]
kpis = "\n".join((f'<a class="kpi u" role="listitem" href="{h}"><div class="v">{v}</div><div class="l">{l}</div><span class="go">Voir la section</span></a>' if h else
                  f'<div class="kpi" role="listitem"><div class="v">{v}</div><div class="l">{l}</div></div>') for v, l, h in KPI)
ne = B["NEPH"]; de = B["DETR et DSIL"]
BRIEF = [
    f"<b>Une appropriation variée.</b> Toutes les préfectures publient sur la plateforme, mais pas pour les mêmes politiques : {n(fcl.get('7', 0))} départements couvrent en ligne les sept familles, {n(etroit)} trois ou moins. "
    f"La taille du département n'en explique qu'une partie (corrélation de rang de {str(TA['spearman_population']['en_ligne']).replace('.', ',')} avec la population).",
    "<b>Ce n'est pas un retard.</b> L'open data ne montre que les démarches publiées. Une préfecture peu présente peut passer par la saisine électronique du ministère, SVE, ou par des boîtes fonctionnelles.",
    f"<b>Un formulaire national ne suppose pas toujours une diffusion locale préalable.</b> Deux chemins y mènent : quelques départements, puis le national (le NEPH, avec {n(ne['departements_deja_une_locale'])} départements, et deux médailles) ; "
    f"ou une diffusion presque générale ({n(de['departements_deja_une_locale'])} départements), un formulaire commun cloné par chaque département, puis la démarche unique nationale de l'exercice 2026 (DETR et DSIL).",
    "<b>Deux outils lisent la plateforme par son API.</b> La Bibliothèque numérique a vocation à être mise en œuvre pour la gestion des fondations, et Turgot pour la gestion des subventions de l'État aux collectivités, "
    "en lien avec la démarche unique nationale de demande de DETR et de DSIL, mise en ligne en octobre 2025, pour l'exercice 2026 ; le code de Turgot prévoit aussi l'écriture des décisions.",
    "<b>Les étrangers : des comptes, des fonctions, des dates.</b> Dépôts, rendez-vous, contacts et compléments, rapportés au calendrier réglementaire de l'ANEF, sans conclure sur le rôle de la plateforme.",
]
brief = "\n".join(f"<li>{b}</li>" for b in BRIEF)

SEC = [(2, "profil", "Profil", "Le séjour des étrangers, les médailles et le permis font l'essentiel des dossiers"),
       (3, "appropriation", "Appropriation", "Toutes les préfectures publient, pas pour les mêmes politiques"),
       (4, "canaux", "Deux canaux", "Deux façons de saisir une préfecture"),
       (5, "national", "Formulaires nationaux", "Un formulaire national ne suppose pas toujours une diffusion locale préalable sur la plateforme"),
       (6, "instruction", "Instruction branchée", "Deux outils publics lisent la plateforme par son API"),
       (7, "etrangers", "Étrangers", "Des dépôts, des rendez-vous, des compléments"),
       (8, "services", "Services propres", "La police et la gendarmerie publient surtout pour leurs agents"),
       (9, "instructeurs", "Qui instruit", "Les préfectures instruisent l'essentiel")]
MAP = ('</div>\n<figure class="map" id="carte">\n  <figcaption>Familles de politiques couvertes en ligne par les démarches de préfecture, par département'
       '<span>Sept familles au plus ; démarches en ligne au 21 octobre 2026. Survoler un département pour ses chiffres.</span></figcaption>\n'
       '  <div id="c-map"></div>\n  <div class="ramp" id="m-ramp"></div>\n</figure>\n<div class="col">')
NOMS = {k: v["n"] for k, v in GEO["deps"].items() if not v.get("ref")}
assert set(CARTE) <= set(NOMS), "département sans nom dans la géométrie"
def cle_code(c): return {"2A": 20.1, "2B": 20.2}.get(c, None) or float(c)
lignes = "".join(f'<tr><td>{c}</td><td>{html.escape(NOMS[c])}</td><td class="r">{v["familles_en_ligne"]}</td><td class="r">{n(v["en_ligne"])}</td>'
                 f'<td class="r">{n(v["depuis_origine"])}</td><td class="r">{n(v["dossiers"])}</td></tr>' for c, v in sorted(CARTE.items(), key=lambda kv: cle_code(kv[0])))
TABLE_CARTE = ('<details id="t-carte"><summary>Voir les données par département</summary><div class="tbl scrollbox"><table>'
               '<thead><tr><th scope="col">Code</th><th scope="col">Département</th><th scope="col" class="r">Familles couvertes en ligne</th>'
               '<th scope="col" class="r">Démarches en ligne</th><th scope="col" class="r">Démarches publiées depuis l\'origine</th><th scope="col" class="r">Dossiers</th></tr></thead>'
               f'<tbody>{lignes}</tbody></table></div></details>')
MAP = MAP.replace('</figure>', '  ' + TABLE_CARTE + '\n</figure>')
corps = []
for k, (num, ident, court, h2) in enumerate(SEC, 1):
    if ident == "appropriation": assert bloc(sections[num][1]).count("<p>[[CARTE]]</p>") == 1, "marqueur de carte absent"
    corps.append(f'<section id="{ident}">\n  <div class="secnum">{k} · {court}</div>\n  <h2>{h2}</h2>\n{bloc(sections[num][1]).replace("<p>[[CARTE]]</p>", MAP).replace('<div class="col"></div>', "")}\n</section>')
methode = bloc(sections[10][1])

css = re.search(r"<style>(.*?)</style>", REF.read_text(encoding="utf-8"), re.S).group(1)
date = d(I["config"]["date_extraction"])
H = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Fiche Intérieur — Démarche Numérique</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700;800&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>{css}
.tbl td:first-child{{min-width:13em}}
:root{{--f1:#dbeafe;--f2:#bfdbfe;--f3:#93c5fd;--f4:#60a5fa;--f5:#3b82f6;--f6:#1d4ed8;--f7:#1e3a8a}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--f1:#1e3a5f;--f2:#1e40af;--f3:#1d4ed8;--f4:#2563eb;--f5:#3b82f6;--f6:#60a5fa;--f7:#bfdbfe}}}}
:root[data-theme="dark"]{{--f1:#1e3a5f;--f2:#1e40af;--f3:#1d4ed8;--f4:#2563eb;--f5:#3b82f6;--f6:#60a5fa;--f7:#bfdbfe}}
.map figcaption span{{display:block;font-weight:400;color:var(--muted);font-size:13px}}
.map path.f1{{fill:var(--f1)}} .ramp i.f1{{background:var(--f1)}}
.map path.f2{{fill:var(--f2)}} .ramp i.f2{{background:var(--f2)}}
.map path.f3{{fill:var(--f3)}} .ramp i.f3{{background:var(--f3)}}
.map path.f4{{fill:var(--f4)}} .ramp i.f4{{background:var(--f4)}}
.map path.f5{{fill:var(--f5)}} .ramp i.f5{{background:var(--f5)}}
.map path.f6{{fill:var(--f6)}} .ramp i.f6{{background:var(--f6)}}
.map path.f7{{fill:var(--f7)}} .ramp i.f7{{background:var(--f7)}}
.map path.f0{{fill:var(--q0)}} .col blockquote{{margin:12px 0;padding:8px 14px;border-left:3px solid var(--line)}} .col ul{{padding-left:1.2em}}</style>
</head>
<body>
<div class="wrap">
<p class="topnav"><a href="https://emsnytech.github.io/form2026/">Retour à FORM 2026</a> · <a href="https://emsnytech.github.io/form2026/fiches-ministeres/">Fiches ministères</a> · <a href="https://emsnytech.github.io/form2026/simulateur-gains-dematerialisation.html">Estimer ses gains</a> · <a href="https://emsnytech.github.io/form2026/explorer.html">Explorer les données</a></p>
<header class="top">
  <div class="eyebrow"><span>FORM 2026 · Fiches ministères</span><span>Fiche n° 3</span><span>Open data du {date}</span><span>Pages publiques relevées le 14 novembre 2026</span></div>
  <h1>Intérieur</h1>
  <p class="sub">{html.escape(titre[0].upper() + titre[1:])}. {inline(chapeau)}</p>
  <div class="cadre">
    <p>{cadre1}</p>
    <p>{cadre2}</p>
  </div>
  {table(sens.split(chr(10)))}
  <p class="small">{inline(sens_note)}</p>
  <div class="kpis" role="list">
{kpis}
  </div>
  <ul class="brief">
{brief}
  </ul>
</header>

{chr(10).join(corps)}

<footer>
  <p>FORM 2026 · Philippe Vrignaud · Données ouvertes et code source publics</p>
  <details>
    <summary>Méthode et sources</summary>
    <div class="col">
      <p><b>Ce que décrit cette fiche.</b> Cette fiche décrit les démarches publiées dans l'open data de la plateforme, ce qui ne recouvre pas toutes les démarches du ministère. Chaque chiffre se lit sur ce corpus. Une part, un rang ou une tendance ne se transpose pas au ministère.</p>
{methode}
      <p><a href="https://emsnytech.github.io/form2026/donnees/fiches-ministeres/methode/">Les scripts de calcul</a> et les fichiers intermédiaires accompagnent la fiche. Chaque chiffre issu de la base est produit par ces scripts ; les sources externes y sont consignées avec leur date.</p>
    </div>
  </details>
</footer>
</div>
<div class="tip" id="tip" hidden></div>
<script id="carte-data" type="application/json">{json.dumps({"geo": GEO, "carte": CARTE}, ensure_ascii=False).replace("</", "<\\/")}</script>
<script>
(function(){{
  const D = JSON.parse(document.getElementById("carte-data").textContent), G = D.geo, C = D.carte, NS = "http://www.w3.org/2000/svg";
  const fr = new Intl.NumberFormat("fr-FR"), tip = document.getElementById("tip");
  const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}}[c]));
  const el = (t, a, p) => {{ const n = document.createElementNS(NS, t); for (const k in a) n.setAttribute(k, a[k]); if (p) p.appendChild(n); return n; }};
  const show = (e, h) => {{ tip.innerHTML = h; tip.hidden = false; tip.style.left = Math.min(e.clientX + 14, innerWidth - tip.offsetWidth - 8) + "px"; tip.style.top = (e.clientY + 14) + "px"; }};
  const names = {{}}; Object.entries(G.deps).forEach(([k, v]) => {{ if (!v.ref) names[k] = v.n; }});
  const svg = el("svg", {{viewBox: G.viewBox, role: "img", "aria-label": "Carte des départements : familles de politiques couvertes en ligne"}});
  G.frames.filter(f => f.h).forEach(f => {{ el("rect", {{x: f.x, y: f.y, width: f.w, height: f.h, rx: 4, class: "frame"}}, svg); const t = el("text", {{x: f.x + 4, y: f.y + 10}}, svg); t.textContent = f.l; }});
  Object.entries(G.deps).forEach(([k, v]) => {{
    const code = v.ref || k, c = C[code], pth = el("path", {{d: v.d, class: "dep"}}, svg);
    pth.classList.add("f" + (c && c.familles_en_ligne ? c.familles_en_ligne : 0));
    pth.addEventListener("mousemove", e => show(e, c ? `<b>${{esc(names[code] || code)}} (${{code}})</b><br>Démarches en ligne : ${{fr.format(c.en_ligne)}}<br>Démarches publiées depuis l'origine : ${{fr.format(c.depuis_origine)}}<br>Dossiers : ${{fr.format(c.dossiers)}}<br>Familles couvertes en ligne : ${{c.familles_en_ligne}} sur 7` : `<b>${{esc(names[code] || code)}}</b><br>Hors du décompte`));
    pth.addEventListener("mouseleave", () => tip.hidden = true);
  }});
  document.getElementById("c-map").appendChild(svg);
  document.getElementById("m-ramp").innerHTML = [1,2,3,4,5,6,7].map(i => `<span><i class="f${{i}}"></i>${{i}} famille${{i > 1 ? "s" : ""}}</span>`).join("");
}})();
</script>
</body>
</html>
"""
# ---------- contrôles ----------
assert not re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}", H), "adresse électronique"
txt = re.sub(r"<style>.*?</style>", "", H, flags=re.S)
assert len(re.findall(r'<script id="carte-data" type="application/json">', txt)) == 1, "bloc de données de la carte"
txt = re.sub(r'<script id="carte-data" type="application/json">.*?</script>', "", txt, flags=re.S)   # exemption 1 : les données de la carte
assert len(re.findall(r'<details id="t-carte">', txt)) == 1, "tableau de la carte"
txt = re.sub(r'<details id="t-carte">.*?</details>', "", txt, flags=re.S)                               # exemption 2 : le tableau replié de la carte
assert not re.search(r"(?<!\d)(\+33|0)[1-9](?:[\s.\-]?\d{2}){4}(?!\d)", re.sub(r"<[^>]+>", " ", txt)), "numéro de téléphone"
plain = unicodedata.normalize("NFKD", html.unescape(re.sub(r"<[^>]+>", " ", txt))).encode("ascii", "ignore").decode().lower()
DEPS = json.load(open("scripts/departements.json"))
nommes = [v for v in DEPS.values() if re.search(r"(?<![a-z-])" + re.escape(v).replace(r"\-", "[- ]") + r"(?![a-z-])", plain)]
assert not nommes, f"département nommé : {nommes}"
assert "ne recouvre pas toutes les démarches" in H, "réserve de méthode absente"
assert CENTRE.split(" Ces ordres")[0] in H, "cadre d'entrée différent de sync_cadre.py"
import sys; sys.dont_write_bytecode = True; sys.path.insert(0, str(SITE / "scripts"))
from controle_fiches import INTITULE   # même motif que le contrôle du dépôt
assert not INTITULE.search(H), "intitulé part de la plateforme"
assert not re.search(r"Phrase-clé|Chapeau\.|à confirmer|Constat, sans recommandation", H), "marque de travail"
# aucun titre ne doit attribuer un outil (Turgot) au ministère : le ministère porteur n'est pas sourcé
for t_ in [h for _, _, _, h in SEC] + re.findall(r"<h[1-3][^>]*>(.*?)</h[1-3]>", H, re.S) + re.findall(r"<li><b>(.*?)</b>", H):
    assert not re.search(r"outils? du minist[eè]re|Turgot.{0,40}minist[eè]re|minist[eè]re.{0,40}Turgot", t_, re.I), f"titre attribuant Turgot au ministère : {t_}"
Path("fiche/fiche-interieur.html").write_text(H, encoding="utf-8")
# version de relecture : méthode dépliée, hors dépôt
Path(os.environ.get("RELECTURE", "fiche/relecture-interieur.html")).write_text(H.replace("<details>", "<details open>").replace("</style>", "@page{size:A4 landscape}</style>", 1), encoding="utf-8")
print("ok fiche/fiche-interieur.html", len(H), "octets ;", len(re.findall(r"\w+", plain)), "mots")
