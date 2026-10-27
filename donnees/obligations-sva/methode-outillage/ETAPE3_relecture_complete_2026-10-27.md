# Étape 3 — Relecture complète des 504 candidats (27/10/2026)

## Méthode

Relecture individuelle des 504 candidats trouvés par canal (400 DN, 91 Cerfa, 13
téléservice — sur les 2 021 lignes vivantes traitées), classés **vérifié** ou
**rejeté** avec motif court, selon la même rigueur que l'échantillon de 50 (régime
cohérent, autorité/domaine cohérents, aucun titre tronqué accepté sans vérification
quand ambigu — titres complets retrouvés dans `app_demarches_*.json` et
`canaux_dila_2026-10-27.csv` pour les cas douteux). Fichier complet avec motif ligne
à ligne : `etape3/verdicts_504_2026-10-27.csv`. Règle pour les lignes à plusieurs
candidats : vérifié si au moins un candidat est le bon (précisé dans le motif).

## Résultat global

| | n | % |
|---|---|---|
| **Vérifié** | **211** | **42 %** |
| Rejeté | 281 | 56 % |
| Indéterminé (ne peut être tranché avec les sources disponibles) | 12 | 2 % |

### Par canal

| Canal | n | Vérifié | Précision |
|---|---|---|---|
| DN | 400 | 161 | 40 % |
| Cerfa (DILA) | 91 | 45 | 49 % |
| Téléservice (DILA) | 13 | 5 | 38 % |

**Écart avec l'échantillon de 50 relu à l'aveugle** (DN 43 %, Cerfa 73 %,
téléservice 80 %) : la relecture complète donne une précision Cerfa et téléservice
nettement **plus basse** que l'échantillon ne le laissait penser. Explication : avec
seulement 91 Cerfa et 13 téléservice au total, l'échantillon de 15 et 5 tirés au
hasard n'était pas assez grand pour être représentatif — la relecture exhaustive
(cette étape) est la mesure qui fait foi, pas l'estimation par échantillon. Pour DN,
en revanche, l'échantillon (43 %) et la relecture complète (40 %) sont cohérents (30
relus sur 400, mais DN est le canal le plus homogène en biais : le même faux ami
« carte professionnelle UE/EEE » domine partout).

### Par liste

| Liste | n candidats | Vérifié | Rejeté | Indéterminé |
|---|---|---|---|---|
| SVA | 214 | 84 | 123 | 7 |
| SVR | 213 | 93 | 116 | 4 |
| délai SVA | 77 | 34 | 42 | 1 |

### Procédures vivantes outillées vérifiées, par canal et par liste

| Liste | DN | Cerfa | Téléservice | Total vérifié |
|---|---|---|---|---|
| SVA | 60 | 21 | 3 | 84 |
| SVR | 72 | 19 | 2 | 93 |
| délai SVA | 29 | 5 | 0 | 34 |
| **Total** | **161** | **45** | **5** | **211** |

**211 procédures vivantes confirmées outillées sur 2 021 lignes vivantes traitées
(10,4 %)** ; 1 517 lignes vivantes n'avaient aucun candidat (75 %, non outillées par
construction — pas de vérification possible puisqu'il n'y a rien à vérifier) ; 293
candidats automatiques se sont révélés faux (rejetés) et 12 restent indéterminés.

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

Non calculée — à faire ensuite sur les 211 procédures outillées vérifiées (161 DN +
45 Cerfa + 5 téléservice), une fois cette relecture validée.

Rien publié. Commit sans push sur la branche `obligations-sva-canaux`.
