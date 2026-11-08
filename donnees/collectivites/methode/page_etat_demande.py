#!/usr/bin/env python3
"""Construit les deux pages « Ce que l'État demande aux collectivités » : la page web et sa version imprimable (deux pages A4).
Tous les chiffres sont lus dans etat_demande.json et detr_formulaires_ouverts.json ; aucun n'est recopié à la main.
Le cadre d'entrée est ensuite écrit par scripts/sync_cadre.py, la navigation par scripts/sync_nav.py.

Usage (depuis la racine du dépôt) : python3 donnees/collectivites/methode/page_etat_demande.py && python3 scripts/sync_cadre.py && python3 scripts/sync_nav.py"""
import html, json, re
from pathlib import Path

R = Path(__file__).resolve().parents[3]
E = json.load(open(R / "donnees/collectivites/etat_demande.json", encoding="utf-8"))
O = json.load(open(R / "donnees/collectivites/detr_formulaires_ouverts.json", encoding="utf-8"))
r = E["resume"]; cat = r["par_categorie"]; pp = r["par_piece"]
DOT, AUT, SVC, DIS = "Dotations et fonds d'investissement local", "Autres dispositifs ciblant les collectivités", "Services administratifs aux collectivités", "Distinctions des agents et élus locaux"
n = lambda x: f"{x:,}".replace(",", " ")
pc = lambda x: f"{x:.1f}".replace(".", ",") + " %"
MOIS = "janvier février mars avril mai juin juillet août septembre octobre novembre décembre".split()
def date_fr(s):
    a, m, j = s.split("-"); return f"{int(j)}{'er' if j == '01' else ''} {MOIS[int(m) - 1]} {a}"
ex = {x["n"]: x for x in E["exemples"]}
dd = r["detr_deliberation"]; g = lambda k: dd.get(k, 0)
fr = O["formulaires"]; actifs = [f for f in fr if f["instruit_dans_les_6_mois"]]
fin_svc = n(sum(cat[c]["dossiers"] for c in (SVC, DIS)))
deux = sum(cat[c]["demarches"] for c in (DOT, AUT))
siret = r.get("siret_redemande")
style = re.search(r"<style>(.*?)</style>", (R / "collectivites/index.html").read_text(encoding="utf-8"), re.S).group(1)
LEGI = {"arrete": "https://www.legifrance.gouv.fr/loda/article_lc/LEGIARTI000025585028", "l2131": "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000041411348/",
        "lolf": "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000006321047", "l1618": "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000042194908"}
a = lambda u, t: f'<a href="{u}" target="_blank" rel="noopener">{t}</a>'
def demarche(k):
    etiquette = "n°\u00a0" + str(k)
    return a(ex[k]["url"], etiquette) if k in ex and ex[k].get("url") else etiquette

def ligne(nom, k):
    return f"<tr><td>{nom}</td><td class=\"num\">{pc(cat[DOT]['pieces'][k][1])}</td><td class=\"num\">{pc(cat[AUT]['pieces'][k][1])}</td></tr>"

TABLE_PIECES = "".join(ligne(nom, k) for nom, k in [
    ("Plan de financement ou budget", "Plan de financement ou budget"), ("Devis ou estimation des coûts", "Devis ou estimation des coûts"),
    ("<b>Délibération</b>", "Délibération"), ("Plans, photos, localisation", "Plans, photos, localisation"),
    ("Attestation de non-commencement", "Attestation de non-commencement"), ("Note ou mémoire de présentation", "Note ou mémoire de présentation"),
    ("<b>RIB</b>", "RIB"), ("SIRET, Kbis ou avis de situation, en pièce", "SIRET, Kbis ou avis de situation")])

_reu = [f for f in actifs if re.search(r"r[ée]union|saint.denis|saint.pierre|saint.paul|saint.beno", (f.get("organisme") or "") + " " + f["url"], re.I)]
_ann = sorted({f["publication"][:7] for f in _reu})
ACTIFS = (f", dont {len(_reu)} campagnes de La Réunion publiées en " + ", ".join(date_fr(m + "-01").split(" ", 1)[1] for m in _ann)) if _reu else ""
assert all(f["publication"] < "2026-02-22" for f in fr), "un formulaire relevé a été publié après la modification : revoir la phrase"

def corps(imprimable):
    SIRET_LIGNE = (f"<tr><td><b>SIRET</b></td><td>la plateforme le demande au dépôt de toute démarche ouverte aux personnes morales ; jusqu'à {n(siret['demarches'])} démarches sur {n(siret['personnes_morales'])} le redemandent pourtant dans le formulaire (plafond)</td>"
                   f"<td>la plateforme, qui l'identifie dans le répertoire Sirene de l'INSEE</td><td>fonctionnement de la plateforme</td></tr>") if siret else ""
    return f"""
<header class="top">
  <div class="eyebrow"><span>Open data data.gouv.fr</span><span>extraction du {date_fr(E['date_open_data'])}</span><span>relevé des formulaires ouverts du {date_fr(O['releve'])}</span></div>
  <h1>Ce que l'État demande aux collectivités, et ce qu'il détient déjà</h1>
  <p class="sub">Les pièces que les démarches de l'État destinées aux collectivités demandent, et, pour trois d'entre elles, l'administration qui les détient déjà.</p>
</header>

<section>
  <h2>En une phrase</h2>
  <p>Après le plan de financement, la pièce la plus demandée est la <b>délibération</b>, un acte que la préfecture a reçu au titre du contrôle de légalité. Pour la DETR, le texte a cessé de l'exiger le 22 février 2026, et les formulaires publiés depuis ont suivi. Le <b>RIB</b> est demandé dans {pc(pp['RIB']['pct_demarches'])} des démarches, alors que les fonds d'une collectivité sont déposés auprès de l'État.</p>
</section>

<section>
  <h2>Le périmètre</h2>
  <div class="tw"><table class="t"><thead><tr><th></th><th class="num">Démarches</th><th class="num">Dossiers</th></tr></thead><tbody>
  <tr><td>Démarches de l'État destinées aux collectivités</td><td class="num">{n(r['demarches'])}</td><td class="num">{n(r['dossiers'])}</td></tr>
  <tr><td>dont dotations et fonds d'investissement local</td><td class="num">{n(cat[DOT]['demarches'])}</td><td class="num">{n(cat[DOT]['dossiers'])}</td></tr>
  <tr><td>dont autres dispositifs : appels à projets, aides, conventions</td><td class="num">{n(cat[AUT]['demarches'])}</td><td class="num">{n(cat[AUT]['dossiers'])}</td></tr>
  <tr><td>dont services administratifs : consultation du Domaine, Sit@del2</td><td class="num">{n(cat[SVC]['demarches'])}</td><td class="num">{n(cat[SVC]['dossiers'])}</td></tr>
  <tr><td>dont médaille d'honneur régionale, départementale et communale</td><td class="num">{n(cat[DIS]['demarches'])}</td><td class="num">{n(cat[DIS]['dossiers'])}</td></tr>
  </tbody></table></div>
  <p class="small">La médaille s'adresse aux agents et aux élus ; la collectivité la propose pour eux. Ni aide ni service administratif, elle est comptée à part. Les services administratifs et la médaille portent {fin_svc} dossiers mais presque aucune pièce : les parts ci-dessous portent sur les {n(deux)} démarches de financement et d'aide.</p>
</section>

<section>
  <h2>Ce qui est demandé</h2>
  <div class="tw"><table class="t"><thead><tr><th>Part des démarches qui demandent la pièce</th><th class="num">Dotations ({n(cat[DOT]['demarches'])})</th><th class="num">Autres dispositifs ({n(cat[AUT]['demarches'])})</th></tr></thead><tbody>
  {TABLE_PIECES}
  <tr><td>Avis d'imposition</td><td class="num">0</td><td class="num">0</td></tr>
  </tbody></table></div>
  <p class="small">Médiane : {cat[DOT]['pj_mediane']} pièces distinctes par démarche de dotation, {cat[AUT]['pj_mediane']} pour les autres dispositifs. Une pièce répétée dans plusieurs sections du même formulaire, une par catégorie de travaux par exemple, n'est comptée qu'une fois.</p>
</section>

<section>
  <h2>Ce que l'État détient déjà</h2>
  <div class="tw"><table class="t"><thead><tr><th>Pièce</th><th>Demandée</th><th>Qui la détient déjà</th><th>Sur quoi repose l'affirmation</th></tr></thead><tbody>
  <tr><td><b>Délibération</b></td><td>{n(pp['Délibération']['demarches'])} démarches, {n(pp['Délibération']['dossiers'])} dossiers</td><td>la préfecture, qui la reçoit au titre du contrôle de légalité, notamment par la plateforme @ctes</td><td>CGCT, {a(LEGI['l2131'], 'art. L2131-2')}, avec les exceptions qu'il énumère</td></tr>
  <tr><td><b>RIB</b></td><td>{n(pp['RIB']['demarches'])} démarches, dont {n(r['rib_et_champ_iban'])} qui demandent aussi l'IBAN dans un champ</td><td>l'État : sauf dérogation, une collectivité dépose ses fonds auprès de lui</td><td>LOLF, {a(LEGI['lolf'], 'art. 26, 3°')} ; dérogations : CGCT, {a(LEGI['l1618'], 'art. L1618-2')}</td></tr>
  {SIRET_LIGNE}
  </tbody></table></div>
</section>

<section>
  <h2>La délibération, pièce en cascade</h2>
  <p>Une délibération suppose une démarche préalable : une séance de l'organe délibérant, un vote, une transmission. Pour la DETR, l'{a(LEGI['arrete'], 'arrêté du 23 décembre 2002')} l'exigeait parmi les pièces du dossier jusqu'au 22 février 2026. L'arrêté du 20 février 2026 l'a retirée de la liste : elle doit toujours exister et peut être contrôlée à l'instruction, mais n'a plus à être transmise.</p>
  <div class="tw"><table class="t"><thead><tr><th>Démarches DETR</th><th class="num">Délibération obligatoire</th><th class="num">facultative</th><th class="num">non demandée</th></tr></thead><tbody>
  <tr><td>Publiées avant le 22 février 2026</td><td class="num">{g('avant le 22/02/2026 | obligatoire')}</td><td class="num">{g('avant le 22/02/2026 | facultative')}</td><td class="num">{g('avant le 22/02/2026 | non demandée')}</td></tr>
  <tr><td>Publiées depuis</td><td class="num">{g('depuis le 22/02/2026 | obligatoire')}</td><td class="num">{g('depuis le 22/02/2026 | facultative')}</td><td class="num">{g('depuis le 22/02/2026 | non demandée')}</td></tr>
  <tr><td>Publiées avant, encore en ligne au {date_fr(E['date_open_data'])}</td><td class="num">{g('avant, encore en ligne | obligatoire')}</td><td class="num">{g('avant, encore en ligne | facultative')}</td><td class="num">{g('avant, encore en ligne | non demandée')}</td></tr>
  </tbody></table></div>
  <p>Les formulaires ont suivi le texte. La démarche nationale de la DGCL ({demarche(128030)}, ouverte en octobre 2025) avait rendu la délibération facultative avant même l'arrêté. Sur les {len(fr)} formulaires encore en ligne qui l'exigent, <b>{O['reliquats']} n'ont rendu aucune décision depuis six mois</b> : ce sont des reliquats de campagnes passées, pas une exigence en vigueur. Les {O['actifs']} autres sont encore instruits{ACTIFS}. Tous ont été publiés sous l'ancien texte et l'appliquaient : ils n'étaient pas en défaut à leur publication, ils sont restés ouverts après la modification. Les pages publiques ne datent pas les dépôts, et l'on ne peut pas dire combien de dossiers y ont été déposés depuis le 22 février.</p>
  <p class="small">Hors DETR, chaque dispositif a ses propres règles, que cette page n'examine pas une à une ; dans tous les cas, l'acte a été transmis à la préfecture au titre du contrôle de légalité.</p>
  <p><b>Ordre de grandeur, au conditionnel.</b> Si retrouver, numériser et joindre une délibération déjà adoptée prenait ne serait-ce que quinze minutes, les {n(pp['Délibération']['dossiers'])} dossiers qui la demandent représenteraient environ {n(int(round(pp['Délibération']['dossiers'] * 15 / 60, -3)))} heures. Durée non mesurée : l'ordre de grandeur dit l'échelle, pas la charge.</p>
</section>

<section>
  <h2>Exemples vérifiables</h2>
  <ul>
  <li>{demarche(128030)}, DGCL, DETR et DSIL : {ex[128030]['pj']} pièces, délibération {ex[128030]['delib']}.</li>
  <li>{demarche(33107)}, préfecture de la Haute-Garonne, demande de paiement commune à sept dispositifs : {ex[33107]['pj']} pièces distinctes, le maximum parmi les démarches de dotation.</li>
  <li>{demarche(47660)}, préfecture de région Bretagne : le RIB en pièce et l'IBAN dans un champ du même formulaire.</li>
  </ul>
</section>

<section>
  <h2>Méthode</h2>
  <ul class="small">
  <li>Périmètre : l'ensemble « pour les collectivités » de {'la page collectivités' if imprimable else '<a href="index.html">la page collectivités</a>'}, un plancher. Les démarches publiées par les collectivités elles-mêmes sont hors champ.</li>
  <li>Classement des pièces : règles explicites sur les libellés, dans <code>donnees/collectivites/methode/etat_demande.py</code>. Une pièce peut relever de plusieurs types ; une pièce sans nom (« document 1 ») n'est pas classée.</li>
  <li>Détenteurs : une lecture du droit, sourcée, pas une mesure. Aucune durée n'est mesurée.</li>
  <li>{n(r['forme_dossier']['cerfa_ou_formulaire_joint_demarches'])} démarches demandent un formulaire ou un Cerfa à remplir en pièce jointe : leur vrai questionnaire échappe à cette mesure.</li>
  <li>Formulaires encore ouverts : relevé de leurs pages publiques de statistiques le {date_fr(O['releve'])}, par <code>releve_detr_ouverts.py</code>.</li>
  </ul>
</section>
"""

TETE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{titre}</title>
<meta name="description" content="Les pièces que les démarches de l'État demandent aux collectivités, et l'administration qui les détient déjà.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700;800&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>{style}
table.t{{width:100%;border-collapse:collapse;margin:10px 0 6px;font-size:.95rem}}table.t th,table.t td{{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}}table.t .num{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}
code{{overflow-wrap:anywhere;word-break:break-word}}
.tw{{overflow-x:auto;-webkit-overflow-scrolling:touch;max-width:100%}}
section{{margin-top:26px}}{extra}</style>
</head>
<body>
<div class="wrap">
{nav}
{corps}
<footer>FORM 2026 · données publiques uniquement · {pied}</footer>
</div>
</body>
</html>
"""
IMPRIME = """
@page{size:A4;margin:11mm 12mm}
html,body{background:#fff!important}body{font-size:9.6pt}.wrap{max-width:none!important;padding:0!important;margin:0!important}
.top{margin:0!important;padding:0!important}h1{font-size:16pt!important;margin:2px 0!important;max-width:none!important}h2{font-size:11pt!important;margin:0 0 2px!important}
section{margin:6px 0 0!important;padding:5px 0 0!important;break-inside:avoid}p,li{font-size:9pt!important;line-height:1.35!important;margin:2px 0!important}
ul{margin:2px 0!important;padding-left:16px}table.t{font-size:8.4pt!important;margin:3px 0!important}table.t th,table.t td{padding:1px 4px!important}
.cadre{max-width:none!important;margin:5px 0 0!important;padding:5px 9px!important}.cadre p{font-size:7.9pt!important;line-height:1.3!important;margin:0 0 3px!important}
.eyebrow{margin:0!important}.eyebrow span{font-size:7pt!important}.sub{font-size:9pt!important;max-width:none!important}.small,.small li{font-size:7.9pt!important}footer{margin-top:5px!important;padding-top:4px!important;font-size:7.5pt!important}
@media screen{body{max-width:210mm;margin:0 auto!important;padding:11mm 12mm!important}}
"""
NAV = '<p class="topnav" data-rubrique="situer"><!-- nav:début --><!-- nav:fin --></p>'
web = TETE.format(titre="FORM 2026 — Ce que l'État demande aux collectivités", style=style, extra="", nav=NAV,
                  corps=corps(False), pied='<a href="etat-demande-imprimable.html">version imprimable, deux pages</a>')
imp = TETE.format(titre="FORM 2026 — Ce que l'État demande aux collectivités (version imprimable)", style=style, extra=IMPRIME, nav="",
                  corps=corps(True), pied="emsnytech.github.io/form2026/collectivites/etat-demande.html")
(R / "collectivites/etat-demande.html").write_text(web, encoding="utf-8")
(R / "collectivites/etat-demande-imprimable.html").write_text(imp, encoding="utf-8")
print("ok : collectivites/etat-demande.html et etat-demande-imprimable.html")
