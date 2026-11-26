#!/usr/bin/env python3
"""Recopie scripts/assistant/moteur.js et ou_aller.js dans trouver-sa-demarche.html, chacun entre ses marqueurs
(/*moteur:début*/ … /*moteur:fin*/, /*ou_aller:début*/ … /*ou_aller:fin*/).

moteur.js est la source unique du moteur : la page n'en porte qu'une copie, produite par ce script (même principe que
scripts/sync_nav.py). Les tests (test_moteur.js) portent donc sur le code exact que la page exécute.

    python3 scripts/assistant/assembler_page.py           # écrit la page si le moteur a changé
    python3 scripts/assistant/assembler_page.py --check   # n'écrit rien, sort en erreur (1) si la page diffère
    python3 scripts/assistant/assembler_page.py --depuis <cartographie>/assistant/page.html

Le nom du répertoire (titre, sous-titre, nom court) est une seule constante du gabarit, le bloc JSON « nom-repertoire » :
les {{titre}}, {{sous_titre}} et {{nom_court}} du gabarit en sont remplis, et page_comment.py le relit dans la page.

--depuis repart du gabarit de l'auteur (page.html, hors du dépôt, comme les sources de build_index.py) et en produit :
- la page FORM, avec les adaptations listées dans ADAPTATIONS (en-tête du gabarit retiré, chemins des données et des pages
  du site, lien vers la version avec assistant et fenêtre de ses conditions, « Où aller ») ;
- la page « Comment ça marche » (page_comment.py), dont sync_cadre.py remplit le cadre d'entrée ;
- la version avec assistant, écrite dans ~/Documents/cartographie/assistant/artefact/version_ia.html (ADAPTATIONS_IA),
  avec les données qu'elle charge à côté d'elle ; l'éditeur la republie lui-même sur claude.ai. Plus de copie hors de
  artefact/ : une page posée à côté d'anciennes données les aurait lues.
Chaque adaptation doit trouver sa place exactement une fois, sinon rien n'est écrit : le gabarit a changé et la liste est à revoir.
--check vérifie aussi que la page « Comment ça marche » est à jour.
"""
import json, re, subprocess, sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
PAGE, MOTEUR = RACINE / "trouver-sa-demarche.html", Path(__file__).with_name("moteur.js")
DEBUT, FIN = "/*moteur:début*/", "/*moteur:fin*/"
# Modules recopiés dans la page, chacun entre ses marqueurs : le moteur, et « Où aller », propre à FORM.
MODULES = [(MOTEUR, DEBUT, FIN), (Path(__file__).with_name("ou_aller.js"), "/*ou_aller:début*/", "/*ou_aller:fin*/")]
ASSISTANT_URL = "https://claude.ai/artifact/LLfjE77eNYPjiykcDdcJza"

VERSION_IA = Path.home() / "Documents" / "cartographie" / "assistant" / "artefact" / "version_ia.html"
# Dossier de publication de la version avec assistant : la page et les fichiers qu'elle charge, à côté d'elle, sous les
# noms qu'elle attend (window.FORM_DATA vide). L'éditeur publie depuis ce dossier.
ARTEFACT = VERSION_IA.parent
FICHIERS_IA = ["index.json", "index_meta.json", "exemples.json", "plus_demandees.json", "a_la_une.json", "types_guichets.json",
               "communes.json", "france_services.json", "besoins.json", "titres_identite.json", "sigles.json"]

CSS_DIALOGUE = """dialog{max-width:36rem;width:calc(100% - 32px);border:1px solid var(--line2);border-radius:14px;padding:20px 22px;background:var(--fond);color:var(--ink)}
dialog::backdrop{background:rgba(0,0,0,.45)}
dialog h2{font-size:20px;margin:0 0 8px;font-weight:600}
dialog ul{margin:6px 0 0 1.1rem;padding:0;font-size:15px}dialog li{margin:4px 0}
.dlg-actions{display:flex;flex-wrap:wrap;gap:10px;margin-top:16px}
.dlg-actions a.btn-lien{color:#fff}
.ghost{min-height:48px;padding:0 20px;font-size:16px;border:1px solid var(--line2);border-radius:10px;background:var(--fond);color:var(--ink)}
"""
DIALOGUE = """<dialog id="dlg-ia" aria-labelledby="dlg-ia-t">
  <h2 id="dlg-ia-t">Avant d'ouvrir la version avec assistant</h2>
  <p>C'est une version de test, publiée hors du site FORM, sur claude.ai.</p>
  <ul>
    <li>L'assistant fonctionne avec Claude, le modèle d'Anthropic&nbsp;: il faut un compte Claude, et vos questions sont décomptées de ce compte, selon les <a href="https://www.anthropic.com/legal/consumer-terms" target="_blank" rel="noopener">conditions d'utilisation d'Anthropic</a>.</li>
    <li>Vos questions sont envoyées au modèle&nbsp;: n'y indiquez ni nom, ni numéro de dossier, ni coordonnées.</li>
    <li>L'assistant oriente et peut se tromper&nbsp;: vérifiez toujours sur la fiche ou la démarche citée. Il ne dit pas si vous avez droit à une aide.</li>
    <li>Le nombre de questions libres est limité par visite. La recherche simple et les exemples préparés restent disponibles sans IA, ici comme là-bas.</li>
  </ul>
  <div class="dlg-actions">
    <a class="btn-lien" id="ia-go" href="#" autofocus target="_blank" rel="noopener">J'ai compris, ouvrir l'assistant</a>
    <button type="button" class="ghost" id="ia-annuler">Annuler</button>
  </div>
</dialog>
"""
JS_AVIS = """// Version avec assistant : les conditions d'utilisation s'affichent avant l'ouverture.
$("ia-go").href = window.FORM_ASSISTANT_URL;
document.addEventListener("click", (ev) => { if (!ev.target.closest("#ia")) return; ev.preventDefault(); const d = $("dlg-ia"); if (d.showModal) d.showModal(); else window.open(window.FORM_ASSISTANT_URL, "_blank", "noopener"); });
$("ia-annuler").addEventListener("click", () => $("dlg-ia").close());
$("ia-go").addEventListener("click", () => $("dlg-ia").close());
// Fermeture (bouton, Annuler ou Échap) : le focus revient au bouton qui a ouvert la fenêtre.
$("dlg-ia").addEventListener("close", () => { const b = $("ia"); if (b) b.focus(); });
"""
CONFIG_FORM = ('<script>window.FORM_ASSISTANT_URL = "' + ASSISTANT_URL + '";  // version avec assistant (artefact Claude partagé)\n'
               'window.FORM_DATA = "donnees/assistant/"; window.FORM_COMMENT_URL = "trouver-sa-demarche-comment.html"; window.FORM_ACCUEIL_URL = "./";</script>\n')

# (motif, remplacement) : motif est une expression régulière qui doit trouver exactement une place dans le gabarit.
COMMUNES = [
    # En-tête du gabarit, propre à la copie de travail : il n'a rien à faire dans les pages assemblées.
    (r"<!-- Source du gabarit de la page FORM[^\n]*-->\n", lambda m: ""),
    # « Où aller », après le script du gabarit.
    (r"(</script>\n)(</body>)", lambda m: m[1] + "<script>/*ou_aller:début*/\n/*ou_aller:fin*/</script>\n" + m[2]),
]
# Page FORM : chemins des données et des pages du site, lien vers la version avec assistant et fenêtre de ses conditions.
ADAPTATIONS = COMMUNES + [
    # Style commun du site (boutons) : servi par le site, absent de la version avec assistant, qui n'a pas de bouton vers elle-même.
    (r"\n<style>", lambda m: '\n<link rel="stylesheet" href="commun.css">\n<style>'),
    (r"\n</style>", lambda m: "\n" + CSS_DIALOGUE.rstrip("\n") + "\n</style>"),
    (r"\n</main>\n", lambda m: "\n</main>\n" + DIALOGUE),
    (r"<script>/\*MOTEUR\*/</script>", lambda m: CONFIG_FORM + f"<script>{DEBUT}\n{FIN}</script>"),
    (r"(\n)(</script>\n<script>/\*ou_aller)", lambda m: m[1] + JS_AVIS + m[2]),
]
# Version avec assistant (artefact claude.ai) : données servies à côté de la page, pages FORM par leur adresse publique.
ADAPTATIONS_IA = COMMUNES + [
    # Les artefacts claude.ai ne peuvent appeler aucune API extérieure : ni API Géo ni Annuaire (ou_aller.js, FORM_SANS_API).
    (r"<script>/\*MOTEUR\*/</script>", lambda m: f"<script>window.FORM_SANS_API = true;</script>\n<script>{DEBUT}\n{FIN}</script>"),
]


def nom_repertoire(texte):
    """Titre, sous-titre et nom court du répertoire : bloc JSON « nom-repertoire » du gabarit (ou de la page assemblée)."""
    m = re.search(r'<script type="application/json" id="nom-repertoire">(.*?)</script>', texte, re.S)
    if not m:
        sys.exit("gabarit : bloc « nom-repertoire » absent ; rien n'est écrit")
    return json.loads(m[1])


def adapter(gabarit, adaptations=None):
    # Nom du répertoire : {{titre}}, {{sous_titre}} et {{nom_court}} remplacés partout, depuis la seule constante du gabarit.
    nom = nom_repertoire(gabarit)
    t = re.sub(r"\{\{(titre|sous_titre|nom_court)\}\}", lambda m: nom[m[1]], gabarit)
    if "{{" in re.sub(r"<script>.*?</script>", "", t, flags=re.S):
        sys.exit("gabarit : un {{…}} n'a pas été remplacé ; rien n'est écrit")
    for motif, rempl in (ADAPTATIONS if adaptations is None else adaptations):
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
    gabarit = source.read_text(encoding="utf-8")
    PAGE.write_text(avec_moteur(adapter(gabarit)), encoding="utf-8")
    subprocess.run([sys.executable, str(Path(__file__).with_name("page_comment.py"))], cwd=RACINE, check=True, capture_output=True)
    for script in ("sync_nav.py", "sync_cadre.py"):
        subprocess.run([sys.executable, str(RACINE / "scripts" / script)], cwd=RACINE, check=True, capture_output=True)
    print(f"écrit : {PAGE.name} et trouver-sa-demarche-comment.html, depuis {source}")
    # Version avec assistant : même gabarit, hors du dépôt, republiée à la main sur claude.ai par l'éditeur.
    if ARTEFACT.parent.is_dir():
        import shutil
        ARTEFACT.mkdir(exist_ok=True)
        VERSION_IA.write_text(avec_moteur(adapter(gabarit, ADAPTATIONS_IA)), encoding="utf-8")
        lignes = [f"version_ia.html\t{(ARTEFACT / 'version_ia.html').stat().st_size}"]
        for f in FICHIERS_IA:
            shutil.copyfile(RACINE / "donnees" / "assistant" / f, ARTEFACT / f)
            lignes.append(f"{f}\t{(ARTEFACT / f).stat().st_size}")
        (ARTEFACT / "LISEZMOI.txt").write_text("Version avec assistant : la page (version_ia.html) et les fichiers qu'elle charge, à placer à côté\n"
            "d'elle sous ces noms. Produit par scripts/assistant/assembler_page.py --depuis. Taille en octets :\n\n" + "\n".join(lignes) + "\n", encoding="utf-8")
        print(f"écrit : {ARTEFACT}/ ({len(FICHIERS_IA) + 1} fichiers)")
    sys.exit(0)

t = PAGE.read_text(encoding="utf-8")
n = avec_moteur(t)
if "--check" in sys.argv and subprocess.run([sys.executable, str(Path(__file__).with_name("page_comment.py")), "--check"], cwd=RACINE).returncode:
    sys.exit(1)
if n == t:
    print("Moteur et « Où aller » de la page : à jour.")
elif "--check" in sys.argv:
    print(f"{PAGE.name} : le moteur ou « Où aller » diffère de scripts/assistant/ (lancer scripts/assistant/assembler_page.py)"); sys.exit(1)
else:
    PAGE.write_text(n, encoding="utf-8"); print(f"écrit : {PAGE.name}")
