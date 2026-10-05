# Gains de la dématérialisation — données dérivées

Production de l'auteur à partir de données ouvertes de data.gouv.fr. Voir `donnees/LICENCE.md`.

## Fichiers

### `demarches_gains_v7.csv`

Un gain estimé par démarche publiée sur demarche.numerique.gouv.fr (méthodologie « v7 »).

**Colonnes** : `demarche` (identifiant) ; `titre` ; `organisme` ; `for_individual` (public particulier si vrai) ; `niveau_brut` (simple/modere/complexe) ; `duree_estimee_totale_s_v7` (temps de remplissage théorique, secondes) ; `duree_realise_s_v7_30`/`_60` (temps déjà évité par le préremplissage, scénario 30 %/60 % d'adoption FranceConnect) ; `duree_potentiel_s_v6` ; `ratio_realise_v7_30`/`_60` ; `identite_duration_s_v7` ; `nb_dossiers` ; `gain_admin_bas`/`central`/`haut` (€, coût de traitement évité pour l'administration) ; `gain_identite_v7_30`/`_60` ; `gain_usagers_realise_v7_30`/`_60` (€, gain usager déjà réalisé) ; `gain_usagers_potentiel_v6` ; `gain_usagers_demat_bas`/`haut`.

**Calcul** : gain administration = coût de traitement évité par dossier (France Stratégie 2018, 6,79 à 10,70 €) × nombre de dossiers déposés. Gain usagers = temps de préremplissage déjà réalisé (champs déjà exploités par la plateforme, type de champ par type de champ) + temps évité par la dématérialisation, valorisés à 7,28 €/h (particuliers) ou 44,70 €/h (personnes morales). Les durées par type de champ viennent du code source public de la plateforme (démarche-numérique, commit 9b42086).

**Un seul champ email a été retiré** d'un titre de démarche avant publication (règle de confidentialité du projet), remplacé par la mention `[adresse électronique retirée]` ; de même pour un numéro de téléphone.

### `parametres_v8.csv`

Les paramètres numériques (constantes, hypothèses, sources) utilisés dans le calcul des gains, version 8 — un paramètre par ligne, avec son unité et sa source ou son statut (mesuré / hypothèse de l'auteur).

## Date et version

Version 8 des paramètres, données d'activité au 28/09/2026 (34 185 à 34 397 démarches selon le périmètre, 18,2 millions de dossiers déposés depuis 2018). Fichier `demarches_gains_v7.csv` : méthodologie v7 (antérieure d'une version aux paramètres v8 ci-dessus, non recalculée depuis).

## Limites

- Les gains administration (France Stratégie 2018) sont des études étrangères (Australie, Royaume-Uni, Canada), non mesurées en France et non réactualisées.
- Les temps de mise en place et certains temps usagers sont des **hypothèses de l'auteur**, pas des mesures — voir `donnees/hypotheses/` pour le détail et une analyse de sensibilité.
- Les gains sont des temps et des coûts valorisés, pas des économies budgétaires constatées.
