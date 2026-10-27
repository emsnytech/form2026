# Étape 2 — Vivante ou éteinte (27/10/2026, version corrigée)

Corrections apportées suite à la relecture : règle de statut par article revue
(toutes versions confondues), lignes SVR/délai toujours « abrogé » isolées, textes
non codifiés (TNC) vérifiés dans l'archive au lieu d'être laissés hors périmètre,
Code du travail applicable à Mayotte recherché dans la partie non-vigueur. Seuls les
textes de l'Union européenne restent hors périmètre.

## 1. Téléchargement LEGI — rappel

Source : `https://echanges.dila.gouv.fr/OPENDATA/LEGI/`. Seule archive globale
disponible : `Freemium_legi_global_20250713-140000.tar.gz` (1 171 027 316 octets),
**datée du 13 juillet 2025**. Aucune archive globale plus récente publiée.
**Limite assumée sur tout ce qui suit : un changement de vigueur intervenu après le
13/07/2025 ne serait pas vu.**

Sous-arbres extraits : `code_en_vigueur` (80 codes, 4,1 Go), puis `TNC_en_vigueur` et
`code_et_TNC_non_vigueur` (textes non codifiés et textes/codes abrogés, 13 Go au
total) pour pouvoir vérifier aussi les décrets/arrêtés/lois non codifiés et le code
du travail de Mayotte (voir §3 et §5).

## 2. Règle de statut corrigée (par numéro d'article, toutes versions confondues)

Pour chaque numéro d'article d'un code, toutes les versions historiques recensées
dans l'archive sont examinées (et non plus seulement celle couvrant la date du
jour, qui produisait des faux « abrogé » quand une version VIGUEUR portait une date
de fin technique non égale à 2999) :

1. **En vigueur** si au moins une version porte l'état `VIGUEUR` ou `VIGUEUR_DIFF`.
2. **Transféré** si, à défaut, la dernière version (la plus récente par date de
   début) porte l'état `TRANSFERE` — le nouvel emplacement est extrait du lien
   `typelien="CONCORDE"` ou `"CONCORDANCE"` présent dans le même fichier, quand il
   existe.
3. **Abrogé** sinon (aucune version en vigueur, dernière version non transférée).

Même règle appliquée au niveau du texte entier pour les textes non codifiés (§3).

**Répartition des états LEGI rencontrés** (toutes versions, tous articles des 42
codes cités par le corpus, 422 525 fichiers) :

| État | Occurrences |
|---|---|
| MODIFIE | 207 212 |
| VIGUEUR | 137 023 |
| ABROGE | 60 515 |
| TRANSFERE | 10 757 |
| MODIFIE_MORT_NE | 3 849 |
| ABROGE_DIFF | 1 201 |
| VIGUEUR_DIFF | 1 030 |
| PERIME | 701 |
| ANNULE | 179 |
| DISJOINT | 29 |
| DEPLACE | 17 |

## 3. Tableau recalculé

Périmètre élargi : tout texte cité (code ou non) est maintenant vérifié dans
l'archive LEGI (codes + TNC + non-vigueur), à l'exception des textes de l'Union
européenne, qui restent hors périmètre par nature (61 citations du règlement (UE)
n° 575/2013 + variantes, 66 lignes au total).

| | SVA (1283) | SVR (1174) | délai SVA (349) | Total (2806) |
|---|---|---|---|---|
| En vigueur (code ou texte) | 862 (67 %) | 662 (56 %) | 226 (65 %) | **1 750 (62 %)** |
| Abrogé (code ou texte) | 269 (21 %) | 253 (22 %) | 65 (19 %) | **587 (21 %)** |
| Transféré | 6 | 6 | 0 | 12 |
| Numéro d'article non localisé dans le code identifié | 98 | 35 | 45 | 178 |
| Mixte (articles multiples, statuts différents) | 14 | 58 | 7 | 79 |
| Hors UE (non vérifiable par construction) | 1 | 65 | 0 | 66 |
| Inconnu — forme non identifiable ou texte non trouvé dans LEGI | 33 | 95 | 6 | 134 |

Détail du poste « Inconnu » (134 lignes, ni codes ni UE) :
- **115 lignes** citent une forme non vérifiable en pratique : règlement intérieur
  d'établissement (non publié au JORF), cahier des charges SIQO, « dispositions
  diverses », « arrêtés ou circulaires d'ouverture des examens » (référence
  générique, pas un acte identifiable). Marqué `inconnu`, pas deviné.
- **19 lignes** citent un décret/arrêté/loi/ordonnance identifiable (nature +
  numéro ou date extraits) mais introuvable dans l'archive LEGI — pour l'essentiel
  des textes très anciens (loi du 18 germinal an X, ordonnance royale de 1844,
  arrêtés des années 1950-1985 sur des sujets étroits). Non trouvé ≠ abrogé :
  marqué `inconnu`.

## 4. Lignes SVR/délai toujours « abrogé » après correction — isolées

**318 lignes** (253 SVR + 65 délai SVA) restent « abrogé » après la règle corrigée :
le décret consolidé 2026 renvoie à un article (ou un texte) qui n'a plus de version
en vigueur dans l'archive LEGI de juillet 2025. Liste complète avec décret, objet,
dispositions et code/texte apparié dans
`methode-svr/ETAPE2_svr_delai_article_disparu_2026-10-27.csv`. Décrets les plus
concernés : 2014-1277 (83 lignes), 2014-1279 (27), 2014-1292 (25), 2014-1273 (22),
2014-1291 (18), 2014-1280 (16), 2014-1294 (16).

**Cause identifiée pour une partie de ces lignes** : au moins **23 lignes** de ce
total citent des articles du Code de procédure pénale (série R57-6-x, R57-7-x,
R57-8-x — règles de détention) qui sont **tous abrogés à la même date exacte, le
1er mai 2022**, date d'entrée en vigueur du **Code pénitentiaire** (créé par
l'ordonnance n° 2022-478 du 30 mars 2022) : ces dispositions ont été déplacées dans
ce nouveau code, créé après la date du classeur SVR source. L'archive LEGI ne les
marque pas `TRANSFERE` (seulement `ABROGE`), et la table de concordance vers les
nouveaux numéros du Code pénitentiaire n'a pas été recherchée (hors délai de cette
étape) — donc pas de nouveau numéro proposé, juste la cause et la date confirmées.
Les autres lignes de la liste n'ont pas de cause unique identifiée à ce stade — à
garder comme « abrogé, cause non examinée » plutôt que d'extrapoler une explication
commune.

## 5. Code du travail applicable à Mayotte

Retrouvé dans la partie **non-vigueur** de l'archive (`code_et_TNC_non_vigueur/
code_non_vigueur`, LEGITEXT000006072052) : **état ABROGE, du 06/03/1991 au
01/01/2020**. L'abrogation effective au 01/01/2020 est confirmée par la citation
trouvée dans les articles eux-mêmes de ce code : **ordonnance n° 2017-1491 du 25
octobre 2017 (art. 34)**, relative à l'extension et à l'adaptation du code du
travail à Mayotte — qui a étendu le code du travail général à Mayotte et abrogé le
code spécifique à cette date. **Les 53 lignes SVA/SVR/délai citant ce code sont donc
reclassées « abrogé »** (et non plus « hors périmètre/inconnu ») dans les fichiers
`*_legi_2026-10-27.csv`, avec la citation ci-dessus comme source.

## 6. Partie (a) — vivante par confirmation croisée SVR/délai (rappel, inchangé)

162 lignes SVA confirmées vivantes par présence du même (code, article) dans le
référentiel SVR/délai consolidé 2026. **34 d'entre elles restent marquées « abrogé »
par l'archive LEGI** même après la règle corrigée (ex. n° 17 Code de commerce
R742-5, une seule version jamais recensée, ABROGE 2007-2017, aucune version
postérieure dans l'archive) — divergence non résolue, signalée, pas arbitrée.

## 7. Partie (b) — codes recodifiés après octobre 2015 (rappel, inchangé)

Code de la consommation : aucune citation dans le corpus. Code de l'urbanisme :
recodification 2016 confirmée (décret n° 2015-1783 du 28/12/2015, art. 10) mais sans
impact sur les lignes du corpus — tous les articles R* cités résolvent sous leur
numéro actuel. Aucune ligne « transférée, à renuméroter » pour ces deux codes.
Le cas du Code pénitentiaire (§4) est un recodification supplémentaire, non demandée
explicitement mais découverte par la vérification du §4 — à traiter de la même façon
si une table de concordance est nécessaire plus tard.

## 8. Synthèse

- **En vigueur (confirmé)** : 1 750 / 2 806 lignes (62 %).
- **Abrogé (confirmé par l'archive LEGI)** : 587 / 2 806 (21 %), dont 318 côté
  SVR/délai isolées en détail (§4) et 34 en conflit non résolu avec le signal
  SVR/délai côté SVA (§6).
- **Transféré** : 12 lignes, nouvel emplacement identifié quand le lien CONCORDE
  existait dans l'archive.
- **Hors UE** : 66 lignes, hors périmètre par nature.
- **Inconnu** (numéro non localisé + forme non identifiable + non trouvé dans LEGI) :
  178 + 134 = 312 lignes — marqué `inconnu`, jamais compté comme éteint.
- Étapes suivantes : travailler sur les lignes `en_vigueur` (862+662+226) et
  `vivante_via_svr=1`, garder trace des 34 conflits non résolus et des 318 lignes
  « article disparu » plutôt que de les exclure silencieusement.

Fichiers : `*_legi_2026-10-27.csv` (données enrichies, colonnes `legi_code_apparie`,
`legi_articles_detectes`, `legi_statut`, `legi_ids`, `legi_transfert_vers`) ;
`methode-svr/ETAPE2_svr_delai_article_disparu_2026-10-27.csv` (les 318 lignes isolées).
Scripts : `legi_01_build_index.py` (toutes versions par article), `legi_02_cross_reference.py`
(codes), `legi_03_build_tnc_index.py` (textes non codifiés), `legi_04_match_tnc.py`
(croisement TNC). Dépendent de l'archive LEGI extraite localement dans
`cartographie/legi/extracted/` (non versionnée, fichiers volumineux).

Rien publié. Commit sans push sur la branche `obligations-sva-canaux`.
