#!/usr/bin/env python3
"""Produit trouver-sa-demarche-comment.html, la page « Comment ça marche » de « Trouver sa démarche ».

    python3 scripts/assistant/page_comment.py           # écrit la page
    python3 scripts/assistant/page_comment.py --check   # n'écrit rien, sort en erreur (1) si la page diffère

La page réunit ce qui sert au lecteur averti et qui a quitté la page de recherche : le schéma des sources, ce qui manque
encore et la suite du projet, le fonctionnement de la recherche, la version avec assistant et son avertissement, les données
personnelles, l'appel à contribution. Aucun nombre n'y est écrit à la main : volumes et date de l'index viennent de
donnees/assistant/index_meta.json (build_index.py), le nombre de France services de france_services.json, les chiffres
d'Aides-territoires du rapport de la PR 69 (rapport_aides_territoires.md). Le cadre d'entrée est ensuite écrit par
scripts/sync_cadre.py entre ses marqueurs.
"""
import datetime, json, re, sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
D = RACINE / "donnees" / "assistant"
PAGE = RACINE / "trouver-sa-demarche-comment.html"
DEPOT = "https://github.com/emsnytech/form2026"
# Note de projet : pièce jointe d'une release GitHub du dépôt (le PDF n'est pas versionné). Le lien répond une fois la
# release publiée par l'éditeur.
NOTE_PROJET = DEPOT + "/releases/download/trouver-sa-demarche-fiche-projet/Trouver_sa_demarche_fiche_projet.pdf"
MOIS = "janvier février mars avril mai juin juillet août septembre octobre novembre décembre".split()


def fmt(n):
    return f"{n:,}".replace(",", " ")


def date_fr(iso):
    d = datetime.date.fromisoformat(iso)
    return f"{'1er' if d.day == 1 else d.day}&nbsp;{MOIS[d.month - 1]}&nbsp;{d.year}"


def chiffres():
    meta = json.loads((D / "index_meta.json").read_text(encoding="utf-8"))
    nfs = len(json.loads((D / "france_services.json").read_text(encoding="utf-8"))["structures"])
    rap = (D / "rapport_aides_territoires.md").read_text(encoding="utf-8")
    aides = int(re.search(r"Aides publiées relevées[^:]*: (\d+)", rap)[1])
    vers_dn = int(re.search(r"^\| Démarche Numérique \| (\d+) \|", rap, re.M)[1])
    return meta, nfs, aides, vers_dn


CSS = """:root{--accent:#0B5D52;--accent-fonce:#08463E;--ink:#1A1A1A;--muted:#555A60;--line:#E5E5E5;--line2:#D4D4D8;--fond:#FFFFFF;--doux:#F4F4F5;--surface:#FFFFFF}
*,*::before,*::after{box-sizing:border-box}
html{background:var(--fond)}
body{margin:0;background:var(--fond);color:var(--ink);font:16px/1.6 Inter,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
a{color:var(--accent)}a:hover{color:var(--accent-fonce)}
:focus-visible{outline:3px solid var(--accent);outline-offset:2px}
.sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.l{max-width:1120px;margin:0 auto;padding:0 24px}
.tete{border-bottom:1px solid var(--line)}
.tete .l{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;padding-top:12px;padding-bottom:12px}
.marque{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.marque a.nom{font-weight:600;font-size:17px;color:var(--ink);text-decoration:none;min-height:44px;display:inline-flex;align-items:center}
.badge-demo{font-size:13px;color:var(--muted);border:1px solid var(--line2);border-radius:999px;padding:2px 10px;text-decoration:none}
.tete nav{display:flex;gap:4px 20px;flex-wrap:wrap;font-size:15px}
.tete nav a{min-height:44px;display:inline-flex;align-items:center}
.tete nav a[aria-current]{color:var(--ink);font-weight:600;text-decoration:none}
main.l{max-width:820px;padding-top:40px}
h1{margin:0 0 12px;font-size:clamp(28px,4.5vw,40px);line-height:1.2;font-weight:600}
h2{margin:44px 0 10px;font-size:22px;font-weight:600}
h3{margin:22px 0 6px;font-size:17px;font-weight:600}
.chapo{font-size:18px;color:#3F4349;margin:0}
.retour{display:inline-flex;align-items:center;min-height:44px;font-size:15px}
ul{padding-left:1.2em}li{margin:.35em 0}
.sommaire{margin:20px 0 0;padding:14px 18px;border:1px solid var(--line2);border-radius:12px;font-size:15px}
.sommaire ul{margin:4px 0 0;columns:2;column-gap:32px}.sommaire li{margin:0;break-inside:avoid}.sommaire a{display:inline-flex;min-height:44px;align-items:center}
.sources{display:grid;grid-template-columns:1fr auto 1fr auto 1fr;gap:10px;align-items:center;margin:14px 0}
.sc-col{display:flex;flex-direction:column;gap:7px}
.sc-h{font-size:13px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);margin:0 0 3px;font-weight:600}
.sc-group{display:flex;flex-direction:column;gap:6px;margin-bottom:6px}
.sc-tag{font-size:13px;color:var(--muted)}
.sc-box{background:var(--surface);border:1px solid var(--line2);border-left:4px solid var(--line2);border-radius:6px;padding:7px 9px;font-size:14px;line-height:1.35}
.sc-box b{display:block}.sc-box span{color:var(--muted)}
.sc-box.adm{border-left-color:#1F4D7A}.sc-box.usa{border-left-color:var(--accent)}.sc-box.acc{border-left-color:#8A3B12}.sc-box.out{border-left-color:var(--ink)}
.sc-box.sc-avenir{border-style:dashed;border-left-style:dashed;opacity:.85}
.sc-arrow{font-size:22px;color:var(--muted)}
.sc-legende{font-size:13px;color:var(--muted);margin:3px 0 10px}
.sc-avenir-ex{display:inline-block;width:1.4rem;height:.8rem;border:1px dashed var(--muted);border-radius:3px;vertical-align:middle;margin-right:.3rem}
.avert{border-left:4px solid #8A3B12;background:#FDF0E7;padding:12px 16px;border-radius:0 8px 8px 0}
.btn-lien{display:inline-flex;align-items:center;min-height:48px;padding:0 22px;font-weight:600;color:#fff;background:var(--accent);border-radius:10px;text-decoration:none}
.btn-lien:hover{color:#fff;background:var(--accent-fonce)}
.pied{border-top:1px solid var(--line);margin-top:56px}
.pied .l{display:flex;gap:8px 24px;flex-wrap:wrap;padding-top:20px;padding-bottom:28px;font-size:13px;color:var(--muted)}
@media (max-width:720px){.l{padding:0 16px}main.l{padding-top:24px}.sources{grid-template-columns:1fr}.sc-arrow{transform:rotate(90deg);justify-self:center}.sommaire ul{columns:1}}
"""


def page():
    meta, nfs, aides, vers_dn = chiffres()
    ndn, nsp, date = meta["demarches_en_ligne"], meta["fiches"], date_fr(meta["date_export"])
    avenir = '<span class="sr-only"> (en cours d\'intégration)</span>'
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Comment ça marche — Trouver sa démarche · FORM 2026</title>
<meta name="description" content="Sources, limites, version avec assistant et données personnelles du démonstrateur « Trouver sa démarche » de FORM 2026.">
<style>
{CSS}</style>
</head>
<body>
<!-- Page produite par scripts/assistant/page_comment.py : ne pas modifier à la main. -->
<header class="tete"><div class="l">
  <div class="marque">
    <a class="nom" href="trouver-sa-demarche.html">Trouver sa démarche</a>
    <a class="badge-demo" href="./">Démonstrateur FORM 2026</a>
  </div>
  <nav aria-label="Liens du démonstrateur">
    <a href="trouver-sa-demarche.html">Chercher une démarche</a>
    <a href="trouver-sa-demarche-comment.html" aria-current="page">Comment ça marche</a>
    <a href="#contribuer">Contribuer</a>
  </nav>
</div></header>

<main class="l">
  <h1>Comment ça marche</h1>
  <p class="chapo">Un démonstrateur de recherche en langage courant dans deux bases publiques réunies dans FORM&nbsp;: les démarches en ligne de Démarche Numérique et les fiches de service-public.gouv.fr. Il dit où déposer le dossier, ce qui vous sera demandé, et ce qu'il ne trouve pas. Une version avec assistant conversationnel est en test.</p>
  <p><a class="retour" href="trouver-sa-demarche.html">← Revenir à la recherche</a></p>
  <nav class="sommaire" aria-label="Sur cette page"><b>Sur cette page</b><ul>
    <li><a href="#sources">Sources et limites</a></li>
    <li><a href="#recherche">Comment la recherche fonctionne</a></li>
    <li><a href="#ia">La version avec assistant</a></li>
    <li><a href="#donnees">Données personnelles</a></li>
    <li><a href="#contribuer">Contribuer</a></li>
  </ul></nav>

  <h2 id="sources">Sources et limites</h2>
  <p><strong>Ce que la démo couvre&nbsp;:</strong> elle relie, pour chaque recherche, les démarches en ligne publiées par l'administration et les lieux où s'adresser près de chez vous.</p>
<figure class="sources" aria-labelledby="sources-titre">
  <figcaption id="sources-titre" class="sr-only">Schéma des sources de données de la démo</figcaption>
  <div class="sc-col">
    <h3 class="sc-h">Sources ouvertes</h3>
    <div class="sc-group">
      <span class="sc-tag">Les démarches</span>
      <div class="sc-box adm"><b>Démarche Numérique</b><span>{fmt(ndn)} démarches en ligne publiées (open data)</span></div>
      <div class="sc-box adm"><b>service-public.gouv.fr</b><span>{fmt(nsp)} fiches et ressources (DILA)</span></div>
    </div>
    <div class="sc-group">
      <span class="sc-tag">Les financeurs</span>
      <div class="sc-box adm sc-avenir"><b>Aides-territoires</b><span>portails de dépôt des financeurs, pour les collectivités (ANCT)</span>{avenir}</div>
    </div>
    <div class="sc-group">
      <span class="sc-tag">Les lieux</span>
      <div class="sc-box usa"><b>API Géo</b><span>du code postal à la commune</span></div>
      <div class="sc-box usa"><b>Annuaire de l'administration</b><span>guichets, CCAS, horaires, contacts officiels (DILA, interrogé en direct)</span></div>
      <div class="sc-box usa"><b>France services</b><span>{fmt(nfs)} structures (ANCT)</span></div>
    </div>
  </div>
  <div class="sc-arrow" aria-hidden="true">→</div>
  <div class="sc-col">
    <h3 class="sc-h">Traitement FORM</h3>
    <div class="sc-box acc"><b>Nettoyage</b><span>démarches de test, réservées aux agents ou fermées écartées ; contacts personnels masqués</span></div>
    <div class="sc-box acc"><b>Portée</b><span>nationale, départementale ou locale à vérifier</span></div>
    <div class="sc-box acc"><b>Moteur de recherche</b><span>vos mots traduits en vocabulaire administratif</span></div>
  </div>
  <div class="sc-arrow" aria-hidden="true">→</div>
  <div class="sc-col">
    <h3 class="sc-h">Ce que vous obtenez</h3>
    <div class="sc-box out"><b>La démarche en ligne</b><span>et ce qu'elle demande</span></div>
    <div class="sc-box out"><b>La fiche officielle</b><span>pour comprendre vos droits, et ses démarches liées (demande en ligne, simulateur)</span></div>
    <div class="sc-box out"><b>Où aller</b><span>le bon guichet, ses horaires, son téléphone</span></div>
    <div class="sc-box out"><b>France services</b><span>la plus proche, pour être accompagné</span></div>
    <div class="sc-box out sc-avenir"><b>Financeurs de votre territoire</b><span>pour les collectivités : Région, Département, agence de l'eau</span>{avenir}</div>
  </div>
</figure>
  <p class="sc-legende"><span class="sc-avenir-ex" aria-hidden="true"></span> En pointillés&nbsp;: en cours d'intégration.</p>
  <p><strong>Ce qui manque encore&nbsp;:</strong> les démarches des autres sites publics, celles qui restent sur papier ou par courriel, et celles qu'aucune fiche ne présente. Pour les aides aux collectivités, la plupart des financeurs passent par leur propre portail&nbsp;: sur {fmt(aides)} aides recensées par Aides-territoires, {fmt(vers_dn)} renvoient vers Démarche Numérique.</p>
  <p><strong>La suite du projet&nbsp;:</strong> indexer les services publics en ligne, d'abord ceux de l'État et de ses opérateurs, puis ceux des collectivités.</p>
  <!-- cadre:début -->
  <!-- cadre:fin -->

  <h2 id="recherche">Comment la recherche fonctionne</h2>
  <ul>
    <li><strong>Recherche&nbsp;:</strong> un moteur local (BM25, dans votre navigateur) interroge l'index. L'assistant (Claude) reformule votre situation en vocabulaire administratif, lance plusieurs recherches, ouvre le détail des résultats et rédige une réponse. Chaque élément cité renvoie à sa source&nbsp;; aucune adresse n'est inventée. Sans assistant, la recherche simple donne les mêmes cartes, le même «&nbsp;Où aller&nbsp;» et les mêmes liens&nbsp;; elle ne cite qu'une phrase tirée de la fiche officielle, jamais un texte rédigé.</li>
    <li><strong>Ce qui est propre à FORM&nbsp;:</strong> pour une démarche en ligne, le nombre de champs, les pièces justificatives demandées, les données préremplies (SIRET, RNA, IBAN, quotient familial…) et le volume de dossiers déposés&nbsp;; le rattachement aux moments de vie&nbsp;; le lien entre fiche service-public et formulaire en ligne quand il existe.</li>
    <li><strong>Limites&nbsp;:</strong> le corpus ne couvre que ce qui est publié en open data. Les téléservices des autres sites publics (impots.gouv, CAF, ANTS…) n'y figurent que lorsqu'une fiche service-public y renvoie, et les démarches encore sur papier ou par courriel n'y sont pas. Une démarche locale n'est pertinente que pour son territoire. L'assistant oriente&nbsp;; il ne dit pas si vous avez droit à une aide.</li>
    <li><strong>Où aller&nbsp;:</strong> votre code postal donne votre commune (API Géo de l'État). Le service local compétent pour votre commune vient de l'Annuaire de l'administration (DILA), interrogé avec le seul code de la commune&nbsp;; la France services la plus proche, de la liste des structures labellisées (ANCT). Les téléphones et adresses électroniques affichés sont ceux que ces deux sources publient pour chaque service.</li>
    <li><strong>Données&nbsp;:</strong> descriptif des démarches publiées sur demarche.numerique.gouv.fr (data.gouv.fr, extraction du {date}), base FORM&nbsp;2026 (champs et pièces justificatives, codification des publics et moments de vie), fiches de service-public.gouv.fr (DILA, licence ouverte). Les adresses électroniques et numéros de téléphone sont retirés de l'index.</li>
    <li><strong>Accueil&nbsp;:</strong> «&nbsp;Les plus demandées&nbsp;» croise l'Observatoire de la qualité des démarches en ligne (DINUM) et les volumes de dossiers du descriptif, variantes départementales regroupées&nbsp;; «&nbsp;À la une&nbsp;» réunit les démarches publiées depuis moins de 30&nbsp;jours et celles de saison, classées par urgence, dossiers déposés et échéance. Les deux listes sont proposées par la mise à jour, puis validées par l'éditeur.</li>
  </ul>

  <h2 id="ia">La version avec assistant</h2>
  <p>L'assistant fonctionne pour l'instant avec Claude, le modèle d'Anthropic. Il faut un compte Claude&nbsp;: vos questions sont traitées par Anthropic sous votre propre compte, selon ses conditions d'utilisation et vos réglages de confidentialité, exactement comme si vous posiez la question directement à Claude. FORM 2026 ne reçoit ni ne conserve vos questions. L'objectif est que chacun puisse choisir son moteur d'IA&nbsp;: l'index est ouvert et pourra être interrogé par n'importe quel assistant (Albert, Mistral, Claude…). La recherche simple et les exemples préparés ne font appel à aucune IA.</p>
  <ul>
    <li>C'est une version de test, publiée hors du site FORM, sur claude.ai.</li>
    <li>L'assistant fonctionne avec Claude, le modèle d'Anthropic&nbsp;: il faut un compte Claude, et vos questions sont décomptées de ce compte, selon les <a href="https://www.anthropic.com/legal/consumer-terms" target="_blank" rel="noopener">conditions d'utilisation d'Anthropic</a>.</li>
    <li>Vos questions sont envoyées au modèle&nbsp;: n'y indiquez ni nom, ni numéro de dossier, ni coordonnées.</li>
    <li>L'assistant oriente et peut se tromper&nbsp;: vérifiez toujours sur la fiche ou la démarche citée. Il ne dit pas si vous avez droit à une aide.</li>
    <li>Sur claude.ai, la page ne peut appeler aucun service extérieur&nbsp;: la commune est reconnue dans votre question, «&nbsp;Où aller&nbsp;» donne les France services les plus proches et un lien vers l'Annuaire de l'administration pour votre commune, sans code postal.</li>
    <li>Le nombre de questions libres est limité par visite. La recherche simple et les exemples préparés restent disponibles sans IA, ici comme là-bas.</li>
  </ul>
  <p class="avert"><strong>Avertissement.</strong> Ce démonstrateur est expérimental et fourni à titre d'information. Ses réponses ne sont ni un conseil juridique ni une décision administrative&nbsp;: vérifiez-les auprès de la source officielle citée. L'éditeur du démonstrateur ne saurait être tenu responsable de l'usage qui est fait des réponses, ni du traitement des questions par le fournisseur d'IA.</p>

  <h2 id="donnees">Données personnelles</h2>
  <ul>
    <li>Décrivez votre situation sans donnée personnelle&nbsp;: ni nom, ni numéro (sécurité sociale, titre de séjour, IBAN, téléphone), ni adresse précise, ni information de santé. Une commune suffit&nbsp;: n'indiquez ni votre adresse ni votre nom. Les numéros et adresses électroniques reconnus sont retirés avant l'envoi.</li>
    <li>La recherche simple se fait entièrement dans votre navigateur&nbsp;: votre question n'est envoyée nulle part.</li>
    <li>Votre code postal sert uniquement à trouver votre commune (API Géo de l'État). Rien d'autre n'est envoyé. Quand votre question nomme une seule commune, elle sert de la même façon à trouver «&nbsp;Où aller&nbsp;»&nbsp;: seul le code de la commune est envoyé, jamais le texte de votre question.</li>
    <li>Seuls le code postal (API Géo) et le code de la commune (Annuaire de l'administration) quittent le navigateur.</li>
    <li>Dans la version avec assistant, vos questions sont traitées par Anthropic sous votre compte Claude&nbsp;; FORM 2026 ne les reçoit ni ne les conserve.</li>
  </ul>

  <h2 id="contribuer">Contribuer</h2>
  <p>Le démonstrateur est ouvert&nbsp;: le code, l'index et les listes de l'accueil sont publiés dans le dépôt du projet. Une démarche mal classée, un guichet erroné, une démarche de saison oubliée, une situation que la recherche ne comprend pas&nbsp;: signalez-le, ou proposez une correction.</p>
  <p><a class="btn-lien" href="{DEPOT}/issues" target="_blank" rel="noopener">Signaler ou proposer une correction</a></p>
  <p><a href="{NOTE_PROJET}">Note de projet (PDF)</a></p>
  <p>Une démarche en ligne manque&nbsp;? <a href="{DEPOT}/issues/new?template=signaler-demarche.yml" target="_blank" rel="noopener">Signalez-la</a>&nbsp;: nom de la démarche, organisme et lien suffisent.</p>
  <p>Pour un service, le contact affiché sous un guichet a son propre lien «&nbsp;Signaler une erreur&nbsp;», vers la source officielle qui le publie.</p>
</main>

<footer class="pied"><div class="l">
  <span>Démonstrateur indépendant, non officiel. Vérifiez toujours auprès de l'organisme cité.</span>
  <a href="#sources">Sources et limites</a>
  <a href="#donnees">Données personnelles</a>
</div></footer>
</body>
</html>
"""


def main():
    nouveau = page()
    actuel = PAGE.read_text(encoding="utf-8") if PAGE.exists() else ""
    # Le cadre d'entrée appartient à sync_cadre.py : la comparaison porte sur le reste de la page.
    sans_cadre = lambda t: re.sub(r"<!-- cadre:début -->.*?<!-- cadre:fin -->", "<!-- cadre -->", t, flags=re.S)
    if sans_cadre(nouveau) == sans_cadre(actuel):
        print(f"{PAGE.name} : à jour."); return 0
    if "--check" in sys.argv:
        print(f"{PAGE.name} : diffère de ce que produit scripts/assistant/page_comment.py"); return 1
    if "<!-- cadre:début -->" in actuel:
        cadre = re.search(r"<!-- cadre:début -->.*?<!-- cadre:fin -->", actuel, re.S)[0]
        nouveau = re.sub(r"<!-- cadre:début -->.*?<!-- cadre:fin -->", lambda m: cadre, nouveau, flags=re.S)
    PAGE.write_text(nouveau, encoding="utf-8"); print(f"écrit : {PAGE.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
