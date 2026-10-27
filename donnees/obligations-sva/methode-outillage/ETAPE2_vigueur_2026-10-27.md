# Étape 2 — Vivante ou éteinte (27/10/2026)

Conformément à l'instruction : pas de consultation Légifrance ligne à ligne, pas de
présomption « vivant ». Méthode utilisée : base LEGI téléchargée localement,
croisement SVA/SVR interne, et citations trouvées dans les données LEGI elles-mêmes
pour les recodifications (rien n'est affirmé sans source locale).

## 1. Téléchargement LEGI

- Source : `https://echanges.dila.gouv.fr/OPENDATA/LEGI/` (accès direct en `curl`, pas
  besoin de WebFetch/WebSearch pour ce serveur).
- Seule archive globale disponible : `Freemium_legi_global_20250713-140000.tar.gz`
  (1 171 027 316 octets, datée du **13 juillet 2025**). Aucune archive globale plus
  récente n'est publiée ; seules des archives incrémentales quotidiennes existent à
  côté.
- Téléchargement réussi, taille exacte vérifiée. Extrait uniquement le sous-dossier
  `legi/global/code_et_TNC_en_vigueur/code_en_vigueur` (tous les codes actuellement en
  vigueur, 80 codes, 4,1 Go décompressés) — pas les lois/décrets non codifiés ni les
  textes non en vigueur, conformément au périmètre demandé (« articles des codes
  cités »).
- **Limite assumée** : l'archive date du 13/07/2025, soit environ 15 mois avant
  aujourd'hui. Un changement de vigueur intervenu depuis cette date ne serait pas vu.

## 2. Méthode de croisement

1. Table des 80 codes (identifiant LEGITEXT ↔ titre) reconstruite depuis
   `texte/version/LEGITEXT*.xml` de chaque code.
2. Pour chaque ligne SVA (`texte_source`) et SVR/délai (`texte_reference`) commençant
   par « Code », appariement au titre exact (normalisé : apostrophes, majuscules,
   suffixes « , CGI. » etc.), avec 3 alias explicites documentés dans le script
   (Code forestier → Code forestier (nouveau) ; variante longue du code des postes ;
   citation combinée construction/habitation). **1 806 lignes sur 1 859** commençant
   par « Code » ont pu être appariées à l'un des 80 codes LEGI. Les 53 restantes
   citent le « Code du travail applicable à Mayotte », **absent de la liste des 80
   codes de l'archive LEGI `code_en_vigueur`** : non vérifiable par cette méthode,
   marqué `inconnu` plutôt que deviné.
3. Pour chaque code apparié, indexation de **tous** les fichiers article (422 525
   fichiers XML, 56 s) : pour chaque numéro d'article (`NUM`), la version dont la
   plage `[DATE_DEBUT, DATE_FIN]` couvre le jour courant (27/10/2026) est retenue ; à
   défaut, la version dont la date de fin est la plus tardive (dernier état connu dans
   l'archive).
4. Extraction des numéros d'article cités dans chaque ligne (`reference` / `dispositions`)
   par expression régulière (préfixe L/R/D, étoile éventuelle « R* », tirets).
   Recherche tolérante à l'étoile dans les deux sens (le code de l'urbanisme numérote
   une partie de ses articles réglementaires « R* »).
5. Statut retenu par ligne : `en_vigueur` si tous les articles cités sont en vigueur à
   ce jour dans l'archive ; `abroge` si au moins un est abrogé ; `non_identifie` si
   aucun numéro n'a pu être localisé dans l'index du code ; `mixte:...` si les articles
   cités ont des statuts différents ; `hors_perimetre_codes` si la source n'est pas un
   « Code » (décret, arrêté, règlement intérieur non codifié — hors périmètre LEGI
   codes par construction).

Fichiers produits (non publiés) : `*_legi_2026-10-27.csv` à côté de chaque fichier
source, colonnes ajoutées `legi_code_apparie`, `legi_articles_detectes`,
`legi_statut`, `legi_ids`. Scripts : `legi_01_build_index.py`,
`legi_02_cross_reference.py` (dépendent de l'archive LEGI extraite localement dans
`cartographie/legi/extracted/`, non versionnée ici — fichiers volumineux).

## 3. Résultats bruts

| | SVA (1283) | SVR (1174) | délai SVA (349) |
|---|---|---|---|
| En vigueur | 628 (49 %) | 436 (37 %) | 182 (52 %) |
| Abrogé | 202 (16 %) | 132 (11 %) | 37 (11 %) |
| Non identifié (numéro non localisé) | 65 (5 %) | 34 (3 %) | 45 (13 %) |
| Hors périmètre codes (décret/arrêté/règlement non codifié, ou code absent de l'archive) | 379 (30 %) | 537 (46 %) | 84 (24 %) |
| Mixte (articles multiples à statuts différents) | 9 | 35 | 1 |

Dans « hors périmètre codes » (SVA) : 364 lignes citent un texte non codifié
(décret/arrêté/règlement intérieur — hors du périmètre LEGI codes demandé), et
**15 lignes citent le Code du travail applicable à Mayotte**, absent de l'archive
(sur 1 283 ; le total de 53 occurrences cité en introduction cumule SVA+SVR+délai).

## 4. Partie (a) — vivante par confirmation croisée SVR/délai

**162 lignes SVA sur 1 283** citent un couple (code, article) qui figure aussi dans le
référentiel SVR/délai consolidé 2026 (construit à partir du classeur Légifrance fourni)
— confirmées vivantes par construction, indépendamment du résultat LEGI.

**Conflit détecté, non résolu : 34 de ces 162 lignes sont par ailleurs marquées
`abroge` par le croisement LEGI** (archive datée du 13/07/2025). Exemples : n° 17
(Code de commerce, R742-5, abrogé depuis une version se terminant au 11/05/2017 dans
l'archive, sans version ultérieure recensée) ; n° 94-96 (Code de la mutualité,
R212-25/R212-73/R213-2) ; n° 169, 175 (Code de la santé publique) ; n° 228, 235-237
(Code de la sécurité sociale). Deux lectures possibles, non tranchées ici : soit
l'archive LEGI n'a pas enregistré une réactivation/recréation de ces articles après la
date où ils apparaissent abrogés, soit le classeur SVR consolidé 2026 contient une
référence obsolète. **Signalé comme divergence à vérifier, pas résolu
automatiquement.** Liste complète des 34 cas dans
`obligations_sva_2026-10-26_legi_2026-10-27.csv` (colonnes `vivante_via_svr` = 1 et
`legi_statut` = abroge).

## 5. Partie (b) — codes recodifiés après octobre 2015

- **Code de la consommation** (recodifié partie réglementaire au 01/07/2016) :
  **0 ligne** SVA/SVR/délai dans le corpus ne le cite. Recodification sans impact sur
  ce corpus.
- **Code de l'urbanisme** (partie réglementaire) : recodification confirmée **dans les
  données LEGI elles-mêmes** — plusieurs articles actuels portent une citation
  `Décret n°2015-1783 du 28 décembre 2015 - art. 10` (JORFTEXT000031704629, signé le
  28/12/2015, `typelien="ABROGE"`), cohérent avec l'entrée en vigueur au 01/01/2016.
  **9 lignes SVA et 28 lignes SVR/délai** citent ce code. Après correction d'un bug de
  comparaison (les articles réglementaires « R* » du code de l'urbanisme comportent
  une étoile dans leur numéro officiel, non reconnue par la première version du script
  d'extraction), **tous les articles R* cités (R*410-12, R*510-2, R*423-xx, R*424-xx,
  R*425-xx) sont retrouvés sous leur numéro actuel et en vigueur** : **aucune ligne
  n'est donc marquée « transférée, à renuméroter »** — la recodification de 2016 n'a
  pas changé la numérotation de ces articles précis, seulement leur contenu/support
  légal. Ne pas confondre avec les 5 lignes « abrogé » du même code (n° 449 : article
  L145-3, partie Montagne, abrogé pour un motif indépendant de la recodification
  réglementaire).

**Limite de méthode notée** : plusieurs lignes SVR citent un article de deux codes à
la fois dans le champ `dispositions` (ex. « Articles L. 621-27 du code du patrimoine
et R. * 423-66... du code de l'urbanisme ») alors que `texte_reference` ne nomme
qu'un seul code. Le script ne vérifie les articles du second code que par
coïncidence et marque souvent `mixte` ou `non_identifie` à tort pour celui-ci.
Documenté, non corrigé (hors délai de cette étape) — à traiter si une étape
ultérieure a besoin d'un statut fiable sur ces lignes précises (identifiables par
`legi_statut` commençant par `mixte`).

## 6. Synthèse étape 2

- **En vigueur (confirmé)** : 628 SVA + 436 SVR + 182 délai = 1 246 lignes.
- **Abrogé (confirmé par l'archive LEGI, dont 34 en conflit avec le signal SVR/délai,
  non résolu)** : 202 + 132 + 37 = 371 lignes.
- **Non vérifiable par cette méthode** : numéro non localisé (65+34+45 = 144) + hors
  périmètre codes/texte non codifié (364+... ) + Code Mayotte absent de l'archive
  (53 au total) — ne pas compter comme « éteint », compter comme `inconnu`.
- Étapes suivantes (3 à 6) : ne travailler que sur les lignes `en_vigueur` ou
  `vivante_via_svr=1`, en gardant trace des 34 conflits non résolus plutôt que de les
  exclure silencieusement.

Rien publié. Commit sans push sur la branche `obligations-sva-canaux`.
