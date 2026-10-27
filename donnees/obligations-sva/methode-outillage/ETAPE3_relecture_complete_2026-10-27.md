# Étape 3 — Relecture complète des 504 candidats (27/10/2026)

> **CORRECTION 1 (27/10/2026)** : `verdicts_504_2026-10-27.csv` (211 vérifiés,
> chiffres de cette note telle qu'écrite initialement) est **superseded** par
> `candidats_canal_verifie_2026-10-27.csv`, une relecture plus stricte et
> postérieure qui corrige 94 lignes (surtout des faux positifs sur les
> décrets 2014-1271/2014-1273 SVR). → 203 vérifiés.
>
> **CORRECTION 2 (27/10/2026, en préparant la volumétrie)** : en réexaminant
> les 103 lignes DN au candidat « meilleur score par défaut » pour sommer les
> déclinaisons régionales/locales légitimes, 38 d'entre elles se sont révélées
> être des candidats **incorrects** et non de simples ambiguïtés de choix :
> 20 étaient le faux ami « carte professionnelle UE/EEE (ambulancier) » déjà
> repéré mais accepté à tort sur ~20 autres professions de santé du décret
> 2014-1286 (conseiller génétique, préparateur en pharmacie, infirmier,
> masseur-kinésithérapeute, orthophoniste, orthoptiste, audioprothésiste...),
> 6 étaient des cartes de combattant/déporté/interné (décret 2014-1284)
> contaminées par un candidat « carte professionnelle d'agent immobilier »
> sans rapport, et 12 autres des matches hors sujet divers. **`candidats_canal_verifie_CORRIGE_2026-10-27.csv`
> fait désormais foi : 165 vérifiés** (114 DN, 46 Cerfa, 5 téléservice ; 82
> SVA, 64 SVR, 19 délai SVA), pas 203. Les tableaux ci-dessous reflètent cette
> seconde correction.
>
> Point non tranché, laissé tel quel : 8 lignes du décret 2014-1282 (domaine
> public maritime) restent « vérifié » avec un signal faible (démarches AOT
> génériques réutilisées sur plusieurs lignes du même décret) — pas assez de
> doute pour les rejeter d'office, pas assez de certitude pour les confirmer
> pleinement.

## Méthode

Relecture individuelle des 504 candidats trouvés par canal (400 DN, 91 Cerfa, 13
téléservice — sur les 2 021 lignes vivantes traitées), classés **vérifié** ou
**rejeté** avec motif court, selon la même rigueur que l'échantillon de 50 (régime
cohérent, autorité/domaine cohérents, aucun titre tronqué accepté sans vérification
quand ambigu — titres complets retrouvés dans `app_demarches_*.json` et
`canaux_dila_2026-10-27.csv` pour les cas douteux). Fichier complet avec motif ligne
à ligne : `etape3/verdicts_504_2026-10-27.csv`. Règle pour les lignes à plusieurs
candidats : vérifié si au moins un candidat est le bon (précisé dans le motif).

## Résultat global (corrigé — voir encadré en tête de note)

| | n | % |
|---|---|---|
| **Vérifié** | **165** | **33 %** |
| Rejeté | 332 | 66 % |
| Indéterminé (ne peut être tranché avec les sources disponibles) | 7 | 1 % |

### Par canal

| Canal | n | Vérifié | Précision |
|---|---|---|---|
| DN | 400 | 114 | 29 % |
| Cerfa (DILA) | 91 | 46 | 51 % |
| Téléservice (DILA) | 13 | 5 | 38 % |

**Écart avec l'échantillon de 50 relu à l'aveugle** (DN 43 %, Cerfa 73 %,
téléservice 80 %) : la relecture complète donne une précision Cerfa et téléservice
nettement **plus basse** que l'échantillon ne le laissait penser. Explication : avec
seulement 91 Cerfa et 13 téléservice au total, l'échantillon de 15 et 5 tirés au
hasard n'était pas assez grand pour être représentatif — la relecture exhaustive
(cette étape) est la mesure qui fait foi, pas l'estimation par échantillon.

### Par liste

| Liste | n candidats | Vérifié | Rejeté | Indéterminé |
|---|---|---|---|---|
| SVA | 214 | 82 | ~125 | ~7 |
| SVR | 213 | 64 | ~145 | ~4 |
| délai SVA | 77 | 19 | ~57 | ~1 |

(Répartition rejeté/indéterminé par liste non recalculée en détail après la
correction des 94 lignes — seul le total vérifié par liste a été vérifié
précisément ; ordre de grandeur conservé pour les deux autres colonnes.)

### Procédures vivantes outillées vérifiées, par canal et par liste

| Liste | DN | Cerfa | Téléservice | Total vérifié |
|---|---|---|---|---|
| SVA | 58 | 21 | 3 | 82 |
| SVR | 43 | 19 | 2 | 64 |
| délai SVA | 13 | 6 | 0 | 19 |
| **Total** | **114** | **46** | **5** | **165** |

**165 procédures vivantes confirmées outillées sur 2 021 lignes vivantes traitées
(8,2 %)** ; 1 517 lignes vivantes n'avaient aucun candidat (75 %, non outillées par
construction — pas de vérification possible puisqu'il n'y a rien à vérifier) ; 332
candidats automatiques se sont révélés faux (rejetés) et 7 restent indéterminés —
**339 lignes à signaler à part, non échantillonnées pour la recherche web** (voir
étape 5, qui n'a tiré que parmi les 1 517 « aucun candidat », pas parmi ces 339).

## Nouveaux faux amis systématiques confirmés à grande échelle

- **Démarches DN 153255 / 152933** (« carte professionnelle de conducteur de
  véhicule motorisé à 2/3 roues (VMDTR) » / « carte professionnelle VTC », toutes
  deux « par reconnaissance de l'expérience professionnelle dans un État membre de
  l'UE/EEE ») : remontent sur la quasi-totalité des **~25 lignes** « autorisation
  d'exercer [profession de santé] accordée individuellement aux ressortissants d'un
  État membre de l'UE/EEE » du décret 2014-1286 et assimilés (psychologue, préparateur
  en pharmacie, physicien médical, infirmier, masseur-kinésithérapeute, pédicure
  podologue, psychomotricien, orthophoniste, orthoptiste, manipulateur
  d'électroradiologie, audioprothésiste, orthoprothésiste, aide-soignant, auxiliaire de
  puériculture, psychothérapeute, ostéopathe, chiropracteur, radiophysique médicale,
  éducateur sportif...) — **toutes rejetées sauf pour la profession d'ambulancier**,
  où ces deux démarches sont réellement les bonnes (vérifié deux fois, numdispo
  confirmés dès le niveau 2 du chantier). C'est le même défaut de fond que celui déjà
  repéré (formule administrative partagée par des dizaines de professions, le titre
  seul ne suffit jamais à les distinguer).
- Confirmation à grande échelle du couple **« dérogation durée hebdomadaire
  minimale »** répondant à des obligations sur la durée **maximale** (confusion
  min/max, 2014-1290 et assimilés, ~15 lignes).
- Confirmation du Cerfa 15814 (dérogation travail de nuit **à bord des navires**)
  remontant systématiquement sur les dérogations travail de nuit en établissements
  commerciaux/spectacle (secteur différent, ~8 lignes).

## Explication de l'écart 2 026 vivantes → 2 021 traitées

5 lignes SVA sur les 1 283 initiales (numdispo 391, 713, 719, 758, 1257) sont des
« faux amis » déjà identifiés et mis en liste noire lors du test niveau 2 sur 56
obligations, avant la recherche de candidats de cette étape (confusion durée
min/max déjà connue, agrément générique confondu avec des stages de sécurité
routière). Elles font partie du périmètre vivant (2 026) mais sont exclues avant le
calcul des candidats, ramenant le nombre de lignes effectivement traitées à 2 021.
Un sixième faux ami de la même liste (numdispo 1219) n'est pas dans le périmètre
vivant (déjà classé abrogé/supprimé à l'étape 2), donc ne compte pas dans l'écart.

## Étape 5 anticipée — échantillon pour recherche web

50 lignes tirées au hasard parmi les 1 517 lignes vivantes sans candidat, stratifiées
SVA/SVR/délai au prorata (25 SVA, 19 SVR, 6 délai — proportions exactes de 754/586/177
dans le total 1 517). Colonnes : id, liste, intitulé/objet, référence, statut de
vigueur, autorité/ministère, type de demandeur. Exporté dans
`cartographie/svr/out/echantillon_partie3.csv` (hors dépôt, fichier local comme
demandé). Les recherches web ne sont pas effectuées.

## Étape 4 (volumétrie)

Calculée dans une étape séparée sur les 165 procédures outillées vérifiées (114 DN +
46 Cerfa + 5 téléservice, après la seconde correction) — voir `VOLUMETRIE_ETAPE4_2026-10-27.md`.

Rien publié. Commit sans push sur la branche `obligations-sva-canaux`.
