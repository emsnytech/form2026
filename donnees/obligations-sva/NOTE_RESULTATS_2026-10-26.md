# Obligations « silence vaut accord » — note des résultats (26/10/2026)

## Ce qui est publié comme résultat, et ce qui ne l'est pas

Seuls les liens relus individuellement sur les deux échantillons (56 obligations, puis
50 liens produits) comptent comme résultat : **15 obligations avec une fiche DILA
confirmée, 7 avec au moins une démarche DN confirmée, 331 dossiers cumulés** sur ces
démarches confirmées (`obligations_sva_avec_statut_2026-10-26.csv`,
`liens_dila_verifies_2026-10-26.csv`, `liens_dn_verifies_2026-10-26.csv`). Les volumes
produits par le rapprochement automatique seul (74 fiches, 234 obligations avec
démarche, 2 216 liens 1→n) ne sont **jamais comptés** dans un indicateur de tête : ce
sont des candidats non vérifiés, exportés à part (`liens_dila_candidats_non_verifies_
2026-10-26.csv`, `liens_dn_candidats_non_verifies_2026-10-26.csv`).

**Correction du 26/10/2026, après relecture plus stricte des titres complets** : 11
liens démarche initialement retenus se sont révélés des faux amis une fois le titre
entier vérifié (régime ou objet différent, pas seulement le même vocabulaire) — retirés
de la liste vérifiée, repassés en candidats non vérifiés. Le script de consolidation
avait aussi un bug (comparaison entier/chaîne) qui empêchait les liens vérifiés d'être
retirés du fichier des candidats ; corrigé le même jour.

## Périmètre

1 283 obligations relevant du principe silence vaut accord, périmètre « État et ses
établissements publics », source data.gouv.fr (XML du 08/12/2016, non remis à jour
depuis). Un doublon exact du XML officiel a été retiré (numdispo 1445/1449, libéralité
Alsace-Moselle en droit local d'Alsace-Moselle) : 1 284 enregistrements bruts → 1 283
obligations distinctes, cohérent avec `obligations.csv`.

C'est la seule liste officielle publiée sur ce périmètre — selon une estimation du
Sénat (2015), elle ne couvrirait qu'environ un tiers des procédures de l'État
effectivement soumises au principe silence vaut accord ; le reste n'a jamais été
recensé publiquement. Les 1 283 obligations de ce chantier sont donc elles-mêmes un
sous-ensemble incomplet, pas l'univers entier des procédures SVA.

## Taux par maillon, mesurés sur un échantillon raisonné de 56 obligations puis
## vérifiés à la main sur un nouvel échantillon de 50 liens produits

| Maillon | Produit (brut, pipeline) | Précision mesurée (échantillon relu à la main) |
|---|---|---|
| Obligation → fiche DILA | 74 liens / 1 283 (5,8 %) | 14/50 ≈ **28 %** (5/25 en confiance « moyenne » ; les 2 liens en confiance « forte », méthode référence, sont corrects dans les 2 cas vérifiés) |
| Obligation → démarche DN | 234 obligations avec au moins une démarche / 1 277 (18,3 %), 2 216 liens 1→n | **36 %** (9/25) |

**Seuil de décision fixé à l'avance (60 % au premier maillon) : non atteint.** Même
après une méthode plus rigoureuse (liste noire de fiches génériques, exigence de
« référence concordante » ou de « titre proche ET autorité cohérente », exclusion
explicite des faux amis déjà repérés), le premier maillon plafonne à 28 %, loin du
seuil. **On ne généralise pas** ce que le pipeline produit comme un inventaire fiable :
le nombre brut de liens (74 fiches, 234 démarches) est une **borne supérieure**, pas
un résultat validé — seule la fraction mesurée (~28 % / ~36 %) doit être présentée
comme fiable.

## Pourquoi le rapprochement échoue le plus souvent

- Les 1 283 obligations couvrent des procédures **institutionnelles** (État ↔ organisme
  régulé, État ↔ collectivité, agrément d'une autre administration) bien plus souvent
  que des démarches **citoyennes**, qui sont le cœur du corpus DILA et de Démarche
  Numérique.
- Deux obligations peuvent partager un intitulé presque identique sur des articles de
  loi différents (ex. durée de travail « minimale » vs « maximale », confondues par un
  rapprochement sur les seuls mots-clés) : erreur déjà rencontrée et corrigée par
  exclusion explicite (numdispo 719, 758, 713, 391, 1257, 1219).
- Le cadre juridique déclaré par une démarche Démarche Numérique ne prouve rien à lui
  seul : **470 démarches** du corpus FORM 2026 — des **démarches sans fondement
  juridique propre** — ne citent que l'ordonnance n° 2014-1330 du 6 novembre 2014
  relative au droit des usagers de saisir l'administration par voie électronique
  (JORFTEXT000029716839, JO n° 258 du 7 novembre 2014, p. 18780). Ce rattachement est
  juridiquement correct pour toute démarche sans texte spécifique : il signale donc une
  démarche qui ne procède d'aucune règle qui lui soit propre, jamais le fondement
  substantiel de l'obligation.
- Le Cerfa n'est pas un raccourci fiable : sur l'échantillon vérifié à la main, les
  démarches confirmées (dont la carte de guide-conférencier, n° 102322) n'ont
  **aucun** Cerfa associé ; et l'unique correspondance Cerfa présente dans
  `obligations.csv` à l'origine de ce chantier (12709, obligation « Certification des
  gestionnaires de réseaux de transports ») s'est révélée fausse une fois vérifiée via
  le registre officiel DILA (12709 = subvention Anah, sans rapport).

## Exemples retenus (confiance confirmée à la main)

- Obligation « Cartes de guide conférencier » → 4 démarches locales retrouvées,
  dont PREF37 (102322, correspondance directe), Préfecture 93, Préfecture 43,
  Département de l'Aisne — exemple net de correspondance 1 → n. Des candidatures CNAM
  à une formation de guide-conférencier, trouvées par le même rapprochement, ont été
  écartées après relecture : ce sont des formations, pas la délivrance de la carte.
- Obligation « Habilitation à dispenser la formation… diplôme d'État de professeur de
  danse » → démarche 77412, Ministère de la Culture, correspondance directe.
- Obligation « Autorisation de coupes dans les bois et forêts… » (Code forestier,
  L124-5) → fiche DILA R18249, méthode « référence concordante » (confiance forte) :
  seule méthode dont la précision mesurée atteint 100 % sur les cas vérifiés, mais sur
  un volume marginal (2 liens au total sur 1 283 obligations).

## Limites

- Rapprochement textuel sans clé commune (pas d'identifiant Légifrance résolu, pas de
  CERFA systématique) : toute mesure de précision ici porte sur un échantillon, pas sur
  l'ensemble.
- Absence de lien ≠ absence de dématérialisation : d'autres téléservices existent hors
  Démarche Numérique (portails ministériels propres, téléprocédures internes).
- Source SVA non mise à jour depuis le 8 décembre 2016 : des obligations ont pu
  disparaître, fusionner ou changer de délai depuis.
- Un seul relecteur a validé les échantillons (pas de requalification à l'aveugle comme
  pour l'étude du cadre juridique) : la marge d'erreur sur les taux ci-dessus n'est pas
  quantifiée formellement, mais l'écart au seuil de 60 % est trop large pour qu'elle
  change la conclusion.
