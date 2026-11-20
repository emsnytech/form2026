#!/usr/bin/env python3
"""Recopie scripts/assistant/moteur.js et ou_aller.js dans trouver-sa-demarche.html, chacun entre ses marqueurs
(/*moteur:début*/ … /*moteur:fin*/, /*ou_aller:début*/ … /*ou_aller:fin*/).

moteur.js est la source unique du moteur : la page n'en porte qu'une copie, produite par ce script (même principe que
scripts/sync_nav.py). Les tests (test_moteur.js) portent donc sur le code exact que la page exécute.

    python3 scripts/assistant/assembler_page.py           # écrit la page si le moteur a changé
    python3 scripts/assistant/assembler_page.py --check   # n'écrit rien, sort en erreur (1) si la page diffère
    python3 scripts/assistant/assembler_page.py --depuis <cartographie>/assistant/page.html

--depuis repart du gabarit de l'auteur (page.html, hors du dépôt, comme les sources de build_index.py) et lui applique les
adaptations FORM listées dans ADAPTATIONS : barre de navigation, ligne des volumes, cadre d'entrée (rempli ensuite par
scripts/sync_cadre.py), chemins des données, lien vers la version avec assistant et fenêtre de ses conditions, code postal
et « Où aller ». Chaque
adaptation doit trouver sa place exactement une fois, sinon rien n'est écrit : le gabarit a changé et la liste est à revoir.
"""
import re, subprocess, sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
PAGE, MOTEUR = RACINE / "trouver-sa-demarche.html", Path(__file__).with_name("moteur.js")
DEBUT, FIN = "/*moteur:début*/", "/*moteur:fin*/"
# Modules recopiés dans la page, chacun entre ses marqueurs : le moteur, et « Où aller », propre à FORM.
MODULES = [(MOTEUR, DEBUT, FIN), (Path(__file__).with_name("ou_aller.js"), "/*ou_aller:début*/", "/*ou_aller:fin*/")]
ASSISTANT_URL = "https://claude.ai/artifact/LLfjE77eNYPjiykcDdcJza"

CSS_DIALOGUE = """dialog{max-width:36rem;width:calc(100% - 32px);border:1px solid var(--line);border-radius:14px;padding:1.1rem 1.2rem;background:var(--surface);color:var(--ink)}
dialog::backdrop{background:rgba(0,0,0,.45)}
dialog h2{font-size:1.1rem;margin:0 0 .5rem;font-weight:800}
dialog ul{margin:.4rem 0 0 1.1rem;padding:0;font-size:.95rem}dialog li{margin:.25rem 0}
.dlg-actions{display:flex;flex-wrap:wrap;gap:.6rem;margin-top:1rem}
a.btn{display:inline-block;font-weight:700;border-radius:10px;padding:.55rem 1rem;border:1px solid var(--admin);text-decoration:none}
a.btn.primary{color:#fff}
"""
CSS_FORM = """.topnav{margin:0 0 1.2rem;font-size:.95rem}.topnav a{text-decoration:none;font-weight:600}
.couv{margin:.5rem 0 0;font-weight:700;color:var(--muted);min-height:1.5em}
input#cp{font:inherit;font-size:.95rem;padding:.35rem .5rem;border-radius:8px;border:1px solid var(--line);background:var(--paper);color:var(--ink);width:6.5rem}
input#cp:focus{outline:2px solid var(--admin);outline-offset:1px}
.cp-etat{font-size:.9rem;font-weight:700;color:var(--usager)}
.perso-cp{font-size:.85rem;color:var(--muted);margin:.4rem 0 0}
.ou{margin-top:.7rem;padding:.6rem .8rem;border-left:4px solid var(--usager);background:var(--usager-soft);border-radius:0 8px 8px 0;font-size:.93rem}
.ou p{margin:.3rem 0}.ou-t{font-weight:800;margin-bottom:.2rem}
.ou-s{margin:.45rem 0 .2rem}.ou-s+.ou-s{border-top:1px dashed var(--line);padding-top:.45rem}
.ou-h,.ou-c{margin:.15rem 0}.ou .links{margin-top:.25rem}
.ou-src{font-size:.8rem;color:var(--muted)}.ou-src a.signaler{color:var(--muted);font-weight:400}
.fs-fort{margin-top:1rem}
.ou-inc{margin:.5rem 0 0;font-size:.88rem;font-weight:700;color:var(--accent)}
.fs-pied{margin-top:1rem;font-size:.93rem;color:var(--ink)}.fs-pied summary{cursor:pointer}.fs-pied .ou-s{margin-left:1rem}
"""
NAV = '  <p class="topnav" data-rubrique="donnees"><!-- nav:début --><!-- nav:fin --></p>\n'
DIALOGUE = """  <dialog id="dlg-ia" aria-labelledby="dlg-ia-t">
    <h2 id="dlg-ia-t">Avant d'ouvrir la version avec assistant</h2>
    <p>C'est une version de test, publiée hors du site FORM, sur claude.ai.</p>
    <ul>
      <li>L'assistant fonctionne avec Claude, le modèle d'Anthropic&nbsp;: il faut un compte Claude, et vos questions sont décomptées de ce compte, selon les <a href="https://www.anthropic.com/legal/consumer-terms" target="_blank" rel="noopener">conditions d'utilisation d'Anthropic</a>.</li>
      <li>Vos questions sont envoyées au modèle&nbsp;: n'y indiquez ni nom, ni numéro de dossier, ni coordonnées.</li>
      <li>L'assistant oriente et peut se tromper&nbsp;: vérifiez toujours sur la fiche ou la démarche citée. Il ne dit pas si vous avez droit à une aide.</li>
      <li>Le nombre de questions libres est limité par visite. La recherche simple et les exemples préparés restent disponibles sans IA, ici comme là-bas.</li>
    </ul>
    <div class="dlg-actions">
      <a class="btn primary" id="ia-go" href="#" autofocus target="_blank" rel="noopener">J'ai compris, ouvrir l'assistant ↗</a>
      <button type="button" class="ghost" id="ia-annuler">Annuler</button>
    </div>
  </dialog>
"""
JS_AVIS = """// Version avec assistant : les conditions d'utilisation s'affichent avant l'ouverture.
function ouvrirAvisIA(ev) { if (ev) ev.preventDefault(); const d = $("dlg-ia"); if (d.showModal) d.showModal(); else window.open(window.FORM_ASSISTANT_URL, "_blank", "noopener"); }
$("ia").addEventListener("click", ouvrirAvisIA);
$("quota").addEventListener("click", (ev) => { if (ev.target.closest("#ia-lien")) ouvrirAvisIA(ev); });
$("ia-annuler").addEventListener("click", () => $("dlg-ia").close());
$("ia-go").addEventListener("click", () => $("dlg-ia").close());
"""
LIEN = '<a href="${window.FORM_ASSISTANT_URL}">accessible ici</a> (compte Claude nécessaire).` : ""); }\n'

# (motif, remplacement) : motif est une expression régulière qui doit trouver exactement une place dans le gabarit.
ADAPTATIONS = [
    (r"(button:disabled\{[^\n]*\n)", lambda m: m[1] + CSS_DIALOGUE),
    (r"\n</style>", lambda m: "\n" + CSS_FORM.rstrip("\n") + "\n</style>"),
    (r'(<div class="wrap">\n)', lambda m: m[1] + NAV),
    (r'(  <p class="lede">.*?</p>\n)', lambda m: m[1] + '  <p class="couv" id="couv"></p>\n'),
    (r'  <div class="frame" id="cadre">[^\n]*</div>\n', lambda m: "  <!-- cadre:début -->\n  <!-- cadre:fin -->\n"),
    (r'      <label class="sel">Département (<select id="dep">.*?</select>)</label>\n    </div>\n',
     lambda m: '      <label class="sel">Votre code postal <input id="cp" inputmode="numeric" autocomplete="postal-code" maxlength="5" placeholder="ex. 94120"></label>\n'
     '      <select id="commune" aria-label="Votre commune" hidden></select>\n      <span class="cp-etat" id="cp-etat" role="status"></span>\n'
     f'      <label class="sel">ou choisissez un département {m[1]}</label>\n    </div>\n'
     '    <p class="perso-cp">Votre code postal sert uniquement à trouver votre commune (API Géo de l\'État). Rien d\'autre n\'est envoyé.</p>\n'),
    (r'(  +<button type="button" class="ghost" id="simple"[^\n]*\n)',
     lambda m: m[1] + '      <button type="button" class="ghost" id="ia" hidden>Essayer avec l\'assistant (version de test)</button>\n'),
    (r'(<form class="ask" id="f">.*?\n  </form>\n)', lambda m: m[1] + "\n" + DIALOGUE),
    (r'(\n      <li><strong>Données&nbsp;:</strong>)', lambda m: "\n      <li><strong>Où aller&nbsp;:</strong> votre code postal donne votre commune (API Géo de l'État). Le service local compétent pour votre commune vient de l'Annuaire de l'administration (DILA), interrogé avec le seul code de la commune&nbsp;; la France services la plus proche, de la liste des structures labellisées (ANCT). Les téléphones et adresses électroniques affichés sont ceux que ces deux sources publient pour chaque service.</li>"
     "\n      <li><strong>La suite du projet&nbsp;:</strong> indexer les services publics en ligne, d'abord ceux de l'État et de ses opérateurs, puis ceux des collectivités.</li>" + m[1]),
    (r"(</script>\n)(</body>)", lambda m: m[1] + "<script>/*ou_aller:début*/\n/*ou_aller:fin*/</script>\n" + m[2]),
    (r"<script>/\*MOTEUR\*/</script>",
     lambda m: f'<script>window.FORM_ASSISTANT_URL = "{ASSISTANT_URL}";  // version avec assistant (artefact Claude partagé)</script>\n<script>{DEBUT}\n{FIN}</script>'),
    (r'fetch\("exemples\.json"\)', lambda m: 'fetch("donnees/assistant/exemples.json")'),
    (r'fetch\("index\.json"\)', lambda m: 'fetch("donnees/assistant/index.json")'),
    (r'\$\("cadre"\)\.innerHTML = `[^`]*`;', lambda m: '$("couv").textContent = `${fmt(ndn)} démarches en ligne et ${fmt(nsp)} fiches service-public indexées`;'),
    (re.escape(LIEN) + r"\}\)\(\);\n",
     lambda m: LIEN.replace('}">accessible', '}" id="ia-lien">accessible').replace(' }\n', '\n')
     + '    if (window.FORM_ASSISTANT_URL) { $("ia").hidden = false; $("ia-go").href = window.FORM_ASSISTANT_URL; } }\n})();\n' + JS_AVIS),
]


def adapter(gabarit):
    t = gabarit
    for motif, rempl in ADAPTATIONS:
        n = len(re.findall(motif, t, flags=re.S))
        if n != 1:
            sys.exit(f"gabarit : l'adaptation « {motif[:60]} » trouve {n} place(s) au lieu d'une ; rien n'est écrit")
        t = re.sub(motif, rempl, t, count=1, flags=re.S)
    return t


def avec_moteur(t):
    for source, debut, fin in MODULES:
        if debut not in t or fin not in t:
            sys.exit(f"{PAGE.name} : marqueurs {debut} … {fin} absents")
        code = source.read_text(encoding="utf-8").rstrip("\n")
        t = re.sub(re.escape(debut) + ".*?" + re.escape(fin), lambda m: debut + "\n" + code + "\n" + fin, t, count=1, flags=re.S)
    return t


if "--depuis" in sys.argv:
    source = Path(sys.argv[sys.argv.index("--depuis") + 1]).expanduser()
    PAGE.write_text(avec_moteur(adapter(source.read_text(encoding="utf-8"))), encoding="utf-8")
    for script in ("sync_nav.py", "sync_cadre.py"):
        subprocess.run([sys.executable, str(RACINE / "scripts" / script)], cwd=RACINE, check=True, capture_output=True)
    print(f"écrit : {PAGE.name}, depuis {source}")
    sys.exit(0)

t = PAGE.read_text(encoding="utf-8")
n = avec_moteur(t)
if n == t:
    print("Moteur et « Où aller » de la page : à jour.")
elif "--check" in sys.argv:
    print(f"{PAGE.name} : le moteur ou « Où aller » diffère de scripts/assistant/ (lancer scripts/assistant/assembler_page.py)"); sys.exit(1)
else:
    PAGE.write_text(n, encoding="utf-8"); print(f"écrit : {PAGE.name}")
