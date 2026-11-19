#!/usr/bin/env python3
"""Construit la page d'accueil (index.html) et « Toutes les publications » (publications.html) depuis ressources.json.

Sources : ressources.json (rubriques, profils, ressources, « commencer », dates, « a_la_une », « parent ») et
donnees/chiffres-accueil.json (produit par scripts/chiffres_accueil.py). Aucun chiffre n'est écrit à la main. Pages
statiques : le navigateur ne charge aucun fichier (même principe que scripts/sync_nav.py, dont la barre est reprise).

- Publications : les ressources « situer », et celles d'une autre rubrique marquées « publication » : true.
- À la une : les publications épinglées (la première à expirer en tête) (« a_la_une » : date de fin incluse, comparée à la date du jour), puis
  les plus récentes, trois au plus ; lien vers « Toutes les publications ».
- Par où commencer : « commencer », profil par profil ; chaque ressource doit déjà porter ce profil.
- Les outils et les données : les ressources par rubrique, sauf celles qui ont un « parent ».
Après la date de fin d'un épinglage, --check avertit sans échouer (annotation GitHub) : relancer le script.

    python3 scripts/sync_accueil.py           # écrit index.html et publications.html
    python3 scripts/sync_accueil.py --check    # n'écrit rien, sort en erreur (1) si une page serait modifiée
"""
import datetime as dt, html, json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "scripts"))
from sync_nav import build_nav_html, NAV_START, NAV_END  # noqa: E402

CHECK = "--check" in sys.argv[1:]
R = json.load(open(ROOT / "ressources.json", encoding="utf-8"))
CH = json.load(open(ROOT / "donnees/chiffres-accueil.json", encoding="utf-8"))
RUB, ORDRE, PROF, TYPES = R["rubriques"], R["ordre_rubriques"], R["profils"], R["types"]
RES = R["ressources"]; PAR_URL = {x["url"]: x for x in RES}
SITE = "https://emsnytech.github.io/form2026/"
AUJOURDHUI = os.environ.get("SYNC_ACCUEIL_DATE") or dt.date.today().isoformat()   # date imposée : contrôle d'un épinglage expiré
e = html.escape
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
def d(s): j = int(s[8:10]); return f"{j}{'er' if j == 1 else ''} {MOIS[int(s[5:7]) - 1]} {s[:4]}"
def n(x): return f"{round(x):,}".replace(",", "\u202f")
def mio(x, k=1): return f"{x / 1e6:.{k}f}".replace(".", ",")
TITRE = "Tout ce que l'on sait déjà des démarches administratives"
SOUS = "Ne plus demander ce que l'État sait déjà"

# ---------- contrôles de la source ----------
for p, urls in R["commencer"].items():
    if p not in PROF or not 2 <= len(urls) <= 3: sys.exit(f"commencer : profil {p} inconnu ou nombre de ressources hors de 2 à 3")
    for u in urls:
        if u not in PAR_URL or p not in PAR_URL[u].get("profils", []): sys.exit(f"commencer : {u} ne porte pas le profil « {p} »")
for x in RES:
    if not x.get("date") or x["rubrique"] not in RUB or x["type"] not in TYPES: sys.exit(f"ressource incomplète : {x['url']}")
    if x.get("parent") and x["parent"] not in PAR_URL: sys.exit(f"parent inconnu : {x['url']}")

PUB = sorted([x for x in RES if x["rubrique"] == "situer" or x.get("publication")], key=lambda x: (x["date"], x["url"]), reverse=True)
epingle = lambda x: bool(x.get("a_la_une")) and AUJOURDHUI <= x["a_la_une"]
UNE = (sorted([x for x in PUB if epingle(x)], key=lambda x: x["a_la_une"]) + [x for x in PUB if not epingle(x)])[:3]   # épinglées : la première à expirer en tête

STYLE = """
:root{--ink:#1e2022;--muted:#5c6066;--paper:#fbf9f5;--surface:#ffffff;--line:#e2dfd7;
 --admin:#1d4ed8;--admin-soft:#eff6ff;--usager:#15803d;--usager-soft:#f0fdf4;--accent:#b45309;--warn-soft:#fffbeb;--bad:#b91c1c;--min:#0e7490;--min-soft:#ecfeff}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--ink:#f3f4f6;--muted:#a1a1aa;--paper:#18181b;--surface:#27272a;--line:#3f3f46;
 --admin:#60a5fa;--admin-soft:#1e3a8a;--usager:#4ade80;--usager-soft:#14532d;--accent:#f59e0b;--warn-soft:#451a03;--bad:#f87171;--min:#22d3ee;--min-soft:#164e63}}
:root[data-theme="dark"]{--ink:#f3f4f6;--muted:#a1a1aa;--paper:#18181b;--surface:#27272a;--line:#3f3f46;
 --admin:#60a5fa;--admin-soft:#1e3a8a;--usager:#4ade80;--usager-soft:#14532d;--accent:#f59e0b;--warn-soft:#451a03;--bad:#f87171;--min:#22d3ee;--min-soft:#164e63}
*,*::before,*::after{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:17px/1.55 "Source Sans 3",system-ui,-apple-system,"Segoe UI",sans-serif}
a{color:var(--admin)} a:focus-visible{outline:3px solid var(--admin);outline-offset:2px;border-radius:4px}
.wrap{max-width:1120px;margin:0 auto;padding:2rem 16px 3rem}
@media (min-width:700px){.wrap{padding:2.4rem 1.25rem 3rem}}
.topnav{margin:0 0 1.2rem;font-size:.95rem}
.brand{font-weight:700;letter-spacing:.02em;color:var(--muted);font-size:.95rem;margin:0}
h1,h2,h3{font-weight:800;line-height:1.15;margin:0}
h1{font-size:clamp(1.9rem,4.4vw,3rem);max-width:24ch;margin-top:.4rem}
.sub{font-size:clamp(1.15rem,2.2vw,1.45rem);font-weight:700;color:var(--min);margin:.6rem 0 0}
.lede{font-size:1.08rem;color:var(--muted);max-width:64ch;margin:.8rem 0 0}
h2{font-size:1.4rem;margin-bottom:.9rem}
section{margin-top:2.4rem}
.entrees{display:flex;flex-wrap:wrap;gap:.5rem;margin:1.3rem 0 0;padding:0;list-style:none}
.entrees a{display:inline-block;padding:.45rem .9rem;border:1px solid var(--line);border-radius:999px;background:var(--surface);font-weight:700;text-decoration:none}
.entrees a:hover{border-color:var(--admin)}
.une{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1rem}
@media (max-width:900px){.une{grid-template-columns:1fr}}
.pub{display:flex;flex-direction:column;background:var(--surface);border:1px solid var(--line);border-top:6px solid var(--min);border-radius:12px;padding:1.1rem 1.2rem;text-decoration:none;color:var(--ink)}
.pub:hover{box-shadow:0 6px 18px rgba(0,0,0,.08)}
.pub .q{font-size:.82rem;font-weight:700;color:var(--min);text-transform:uppercase;letter-spacing:.05em}
.pub h3{font-size:1.22rem;margin:.35rem 0 .4rem}
.pub p{margin:0;color:var(--muted);font-size:.96rem;flex:1}
.pub time{font-size:.85rem;color:var(--muted);margin-top:.7rem}
.tout{margin:.8rem 0 0;font-weight:700}
.figures{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1px;background:var(--line);border:1px solid var(--line);border-radius:10px;overflow:hidden}
@media (max-width:760px){.figures{grid-template-columns:1fr}}
.figures.deux{grid-template-columns:repeat(2,minmax(0,1fr));margin-top:.8rem}
@media (max-width:760px){.figures.deux{grid-template-columns:1fr}}
.fig{background:var(--surface);padding:.9rem 1.1rem}
.fig b{display:block;font-size:1.55rem;line-height:1.1}
.fig span{font-size:.9rem;color:var(--muted)}
.fig.a b{color:var(--admin)} .fig.u b{color:var(--usager)}
.note{font-size:.88rem;color:var(--muted);margin:.6rem 0 0}
.profils{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:.9rem}
@media (max-width:1000px){.profils{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width:560px){.profils{grid-template-columns:1fr}}
.prof{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:1rem 1.05rem}
.prof h3{font-size:1.02rem;margin:0 0 .5rem}
.prof ul,.rub ul{list-style:none;margin:0;padding:0}
.prof li{margin:.45rem 0}
.prof a,.rub a{font-weight:600;text-decoration:none}
.prof a:hover,.rub a:hover{text-decoration:underline}
.prof small,.rub small{display:block;color:var(--muted);font-size:.85rem;line-height:1.35}
.catalogue{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1rem}
@media (max-width:980px){.catalogue{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width:560px){.catalogue{grid-template-columns:1fr}}
.rub{background:var(--surface);border:1px solid var(--line);border-top:5px solid var(--c);border-radius:10px;padding:1rem 1.05rem;scroll-margin-top:1rem}
.rub h3{font-size:1.15rem;color:var(--c)}
.rub .st{margin:.1rem 0 .6rem;font-size:.88rem;color:var(--muted)}
.rub li{margin:.5rem 0}
.type{font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);border:1px solid var(--line);border-radius:4px;padding:0 4px;margin-left:4px;vertical-align:1px}
.traj{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));border:1px solid var(--line);border-radius:10px;overflow:hidden;background:var(--surface)}
@media (max-width:700px){.traj{grid-template-columns:1fr}}
.step{padding:.8rem 1rem;border-right:1px solid var(--line)} .step:last-child{border-right:0}
@media (max-width:700px){.step{border-right:0;border-bottom:1px solid var(--line)}.step:last-child{border-bottom:0}}
.step .k{font-size:.78rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}
.step b{display:block;font-size:1.05rem}
.step p{margin:.15rem 0 0;font-size:.9rem;color:var(--muted)}
.about{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(0,1fr);gap:1.5rem}
@media (max-width:760px){.about{grid-template-columns:1fr}}
.about p{margin:.5rem 0}
.liste{list-style:none;margin:0;padding:0}
.liste li{background:var(--surface);border:1px solid var(--line);border-left:5px solid var(--min);border-radius:10px;padding:.9rem 1.1rem;margin:0 0 .8rem}
.liste time{font-size:.85rem;color:var(--muted)} .liste h2{font-size:1.15rem;margin:.2rem 0 .3rem} .liste p{margin:0;color:var(--muted)}
footer{margin-top:2.6rem;border-top:1px solid var(--line);padding-top:1rem;font-size:.88rem;color:var(--muted)}
"""
def page(titre, desc, url, rubrique, corps):
    nav = build_nav_html(ORDRE, RUB, rubrique, "")
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(titre)}</title>
<meta name="description" content="{e(desc)}">
<meta property="og:type" content="website">
<meta property="og:locale" content="fr_FR">
<meta property="og:site_name" content="FORM 2026">
<meta property="og:title" content="{e(titre)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>{STYLE}</style>
</head>
<body>
<!-- Page produite par scripts/sync_accueil.py depuis ressources.json : ne pas modifier à la main. -->
<div class="wrap">
  <p class="topnav" data-rubrique="{rubrique or ''}">{NAV_START}{nav}{NAV_END}</p>
{corps}
  <footer>FORM 2026 · Philippe Vrignaud · Données ouvertes et code source publics</footer>
</div>
</body>
</html>
"""

def libelle_pub(x):
    p = PAR_URL.get(x.get("parent", ""))
    return RUB[x["rubrique"]]["verbe"] + (f" · {p['titre']}" if p else "")

DE, GA, CG = CH["descriptif"], CH["gains"], CH["charge"]; pe = DE["par_etat"]
une = "\n".join(f"""      <a class="pub" href="{e(x['url'])}">
        <span class="q">{e(libelle_pub(x))}</span>
        <h3>{e(x['titre'])}</h3>
        <p>{e(x['description'])}</p>
        <time datetime="{x['date']}">Publié le {d(x['date'])}</time>
      </a>""" for x in UNE)
prof = "\n".join(f"""      <div class="prof"><h3>{e(PROF[p])}</h3><ul>{"".join(f'<li><a href="{e(u)}">{e(PAR_URL[u]["titre"])}</a><small>{e(PAR_URL[u]["description"])}</small></li>' for u in urls)}</ul></div>"""
                 for p, urls in R["commencer"].items())
cat = "\n".join(f"""      <div class="rub" id="{k}" style="--c:var({RUB[k]['couleur']})"><h3>{e(RUB[k]['verbe'])}</h3><p class="st">{e(RUB[k]['sous_titre'])}</p><ul>{"".join(
    f'<li><a href="{e(x["url"])}">{e(x["titre"])}</a><span class="type">{e(TYPES[x["type"]])}</span><small>{e(x["description"])}</small></li>'
    for x in RES if x["rubrique"] == k and not x.get("parent"))}</ul></div>""" for k in ORDRE)
corps = f"""  <header>
    <p class="brand">FORM 2026</p>
    <h1>{e(TITRE)}</h1>
    <p class="sub">{e(SOUS)}</p>
    <p class="lede">FORM recense ce que les démarches en ligne demandent aux usagers, identifie ce que l'administration détient déjà, et mesure ce que la simplification fait gagner, aux usagers comme aux administrations.</p>
    <nav aria-label="Sur cette page"><ul class="entrees">
      <li><a href="#une">À la une</a></li><li><a href="#commencer">Par où commencer</a></li><li><a href="#outils">Les outils et les données</a></li>
    </ul></nav>
  </header>

  <section id="une" aria-labelledby="h-une">
    <h2 id="h-une">À la une</h2>
    <div class="une">
{une}
    </div>
    <p class="tout"><a href="publications.html">Toutes les publications ({len(PUB)}) →</a></p>
  </section>

  <section aria-labelledby="h-chiffres">
    <h2 id="h-chiffres">En chiffres</h2>
    <div class="figures">
      <div class="fig"><b>{n(DE['demarches'])} démarches</b><span>dans le descriptif ouvert du {d(DE['date'])} : {n(pe['publiee']['demarches'])} publiées, {n(pe['close']['demarches'])} closes, {n(pe['depubliee']['demarches'])} dépubliées</span></div>
      <div class="fig"><b>{mio(DE['dossiers'])} M dossiers</b><span>déposés pour ces démarches, dont {mio(pe['publiee']['dossiers'])} M pour les démarches publiées</span></div>
      <div class="fig a"><b>{round(GA['bas'] / 1e6)} à {round(GA['haut'] / 1e6)} M€</b><span>de gains cumulés, administration et usagers, sur {n(GA['demarches'])} démarches et {mio(GA['dossiers'])} M dossiers (activité au {d(GA['date'])}, paramètres version 8)</span></div>
    </div>
    <div class="figures deux">
      <div class="fig u"><b>{CG['deposes_le_jour_meme_pct']} %</b><span>des dossiers sont déposés le jour même où ils sont commencés : la saisie n'est plus le problème</span></div>
      <div class="fig"><b>Environ {e(CG['part_des_differes_5_pieces'])}</b><span>des dépôts différés viennent des démarches à cinq pièces justificatives ou plus ({CG['differes_5_pieces_pct']} % de dépôts différés, contre {CG['differes_1_2_pieces_pct']} % avec une ou deux pièces)</span></div>
    </div>
    <p class="note">Trois sources, nommées et datées : le descriptif ouvert, que lisent aussi les fiches ministères ; le calcul des gains, sur sa propre extraction ; <a href="note/">la note sur les gains</a> (section 5, données du {e(CG['donnees'])}). <a href="compteur-roi.html">Les mêmes paramètres de gains, mis à jour en continu : le compteur →</a></p>
  </section>

  <section id="commencer" aria-labelledby="h-commencer">
    <h2 id="h-commencer">Par où commencer</h2>
    <div class="profils">
{prof}
    </div>
  </section>

  <section id="outils" aria-labelledby="h-outils">
    <h2 id="h-outils">Les outils et les données</h2>
    <div class="catalogue">
{cat}
    </div>
  </section>
  <section aria-labelledby="h-traj">
    <h2 id="h-traj">La trajectoire : de la pièce à la réponse</h2>
    <div class="traj">
      <div class="step"><span class="k">Aujourd'hui</span><b>La pièce</b><p>L'usager cherche, numérise et dépose un document ; l'agent l'ouvre et le vérifie.</p></div>
      <div class="step"><span class="k">Ensuite</span><b>La donnée</b><p>L'information est obtenue à la source, certifiée, sans rien demander à l'usager.</p></div>
      <div class="step"><span class="k">À terme</span><b>La réponse</b><p>Seule la condition est vérifiée (« sous le plafond : oui ») ; l'administration ne reçoit que le nécessaire.</p></div>
    </div>
  </section>

  <section aria-labelledby="h-about">
    <h2 id="h-about">À propos</h2>
    <div class="about">
      <div>
        <p>FORM est un outil développé en 2015 par Philippe Vrignaud sous FileMaker, dans le cadre du pilotage du programme « Dites-le-nous une fois », pour valoriser les travaux d'analyse des possibilités de simplification des démarches administratives par la donnée : suppression d'informations, échanges entre administrations, référentiels.</p>
        <p>FORM 2026 en reprend la logique à partir des données ouvertes : descriptif des démarches publiées sur Démarche Numérique, jeu de données du hackathon de la plateforme, référentiel de service-public.fr, et code source public de la plateforme.</p>
        <p>Sa réalisation a été effectuée avec le recours à l'intelligence artificielle, sous la direction de l'auteur, qui en a défini les objectifs, fourni ou orienté les éléments à analyser et à valoriser, et contrôlé les résultats.</p>
      </div>
      <div>
        <p class="note">Toutes les sources sont publiques, et les calculs, paramètres et résultats par démarche sont publiés pour être vérifiés et contestés. Paramètres des gains : version 8, octobre 2026.</p>
      </div>
    </div>
  </section>"""
# ---------- toutes les publications ----------
liste = "\n".join(f"""    <li><time datetime="{x['date']}">{d(x['date'])}</time> · <span>{e(libelle_pub(x))}</span>
      <h2><a href="{e(x['url'])}">{e(x['titre'])}</a></h2><p>{e(x['description'])}</p></li>""" for x in PUB)
corps2 = f"""  <header>
    <p class="brand"><a href="index.html">FORM 2026</a></p>
    <h1>Toutes les publications</h1>
    <p class="lede">Les publications du volet « {e(RUB['situer']['verbe'])} » ({e(RUB['situer']['sous_titre'])}) et les outils signalés comme publications, de la plus récente à la plus ancienne. Date : mise en ligne.</p>
  </header>
  <section aria-label="Publications">
  <ul class="liste">
{liste}
  </ul>
  </section>"""

PAGES = [(ROOT / "index.html", page(f"FORM 2026 · {TITRE}", f"{SOUS}. Publications, outils et données sur les démarches administratives, à partir des seules sources publiques.", SITE, None, corps)),
         (ROOT / "publications.html", page("FORM 2026 · Toutes les publications", "Les publications de FORM 2026, de la plus récente à la plus ancienne.", SITE + "publications.html", "situer", corps2))]
ecarts = [p for p, t in PAGES if not p.exists() or p.read_text(encoding="utf-8") != t]
if CHECK:
    if not ecarts: print("Accueil : à jour."); sys.exit(0)
    # Un épinglage arrivé à échéance n'est pas une erreur : si les pages correspondent à l'état d'avant l'échéance,
    # on avertit sans faire échouer la CI (les autres PR ne sont pas bloquées).
    expires = sorted(x["a_la_une"] for x in RES if x.get("a_la_une") and x["a_la_une"] < AUJOURDHUI)
    if expires and not os.environ.get("SYNC_ACCUEIL_DATE"):
        r = subprocess.run([sys.executable, __file__, "--check"], env={**os.environ, "SYNC_ACCUEIL_DATE": expires[-1]}, capture_output=True, text=True)
        if r.returncode == 0:
            print(f"::warning title=Épinglage expiré::un épinglage « À la une » a pris fin le {expires[-1]} : relancer python3 scripts/sync_accueil.py")
            print("Accueil : à jour, épinglage expiré (avertissement)."); sys.exit(0)
    sys.exit("Accueil à reconstruire (python3 scripts/sync_accueil.py) : " + ", ".join(p.name for p in ecarts))
for p, t in PAGES:
    if p in ecarts: p.write_text(t, encoding="utf-8")
print("Accueil : " + (", ".join(p.name for p in ecarts) + " écrit(s)" if ecarts else "déjà à jour") + f" ; à la une : {', '.join(x['url'] for x in UNE)}")
