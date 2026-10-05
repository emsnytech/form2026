# Gains de la dématérialisation — données dérivées

Production de l'auteur à partir de données ouvertes de data.gouv.fr. Voir `donnees/LICENCE.md`.

## Fichiers

### `demarches_gains_v8.csv`

Un gain estimé par démarche publiée sur demarche.numerique.gouv.fr (méthodologie « v8 », paramètres version 8). 34 185 démarches, 18 220 327 dossiers déposés depuis 2018.

**Colonnes** : `demarche` (identifiant) ; `titre` ; `organisme` ; `for_individual` (public particulier si vrai) ; `niveau_brut` (simple/modere/complexe) ; `duree_estimee_totale_s_v7` (temps de remplissage théorique, secondes) ; `duree_realise_s_v7_30`/`_60` (temps déjà évité par le préremplissage, scénario 30 %/60 % d'adoption FranceConnect) ; `duree_potentiel_s_v6` ; `ratio_realise_v7_30`/`_60` ; `identite_duration_s_v7` ; `nb_dossiers` ; `gain_admin_bas`/`central`/`haut` (€, coût de traitement évité pour l'administration) ; `gain_identite_v7_30`/`_60` ; `gain_usagers_realise_v7_30`/`_60` (€, gain usager déjà réalisé par le préremplissage, identité comprise) ; `gain_usagers_potentiel_v6` ; `gain_usagers_demat_bas`/`haut` (€, temps évité par la dématérialisation, **recalculé en v8**) ; `gain_total_bas`/`haut` (€, **nouvelles colonnes**).

**Calcul**
- **Administration** : coût de traitement évité par dossier (France Stratégie 2018, 6,79 à 10,70 €) × nombre de dossiers déposés.
- **Usagers, dématérialisation** (v8) : temps évité par dossier par rapport à un formulaire PDF envoyé par courriel, selon le niveau de complexité de la démarche (`niveau_brut`), valorisé à 7,28 €/h pour un particulier (France Stratégie 2018, tableau 14, d'après le rapport Quinet) ou 44,70 €/h pour une personne morale (Insee, Eurostat 2025). Bas : envoi des pièces seul, soit 2, 4 et 8 minutes (simple, modérée, complexe). Haut : ensemble des étapes, soit 9,5, 14,5 et 26,5 minutes. Le détail des étapes figure dans `donnees/hypotheses/temps_par_etape.csv`.
- **Usagers, préremplissage** : temps de saisie déjà évité (champs déjà exploités par la plateforme, type de champ par type de champ), valorisé aux mêmes taux. Les durées par type de champ viennent du code source public de la plateforme (démarche-numérique, commit 9b42086).
- **Totaux par démarche** : `gain_total_bas` = `gain_admin_bas` + `gain_usagers_demat_bas` + `gain_usagers_realise_v7_30` ; `gain_total_haut` = `gain_admin_haut` + `gain_usagers_demat_haut` + `gain_usagers_realise_v7_60`.

**Totaux sur l'ensemble du fichier** : administration 123,7 à 195,0 M€ ; usagers, dématérialisation 30,0 à 106,8 M€ ; usagers, préremplissage 6,8 à 7,1 M€ ; **total 160,5 à 308,8 M€**.

**Un seul champ email a été retiré** d'un titre de démarche avant publication (règle de confidentialité du projet), remplacé par la mention `[adresse électronique retirée]` ; de même pour un numéro de téléphone.

### `parametres_v8.csv`

Les paramètres numériques (constantes, hypothèses, sources) utilisés dans le calcul des gains, version 8 — un paramètre par ligne, avec son unité et sa source ou son statut (mesuré / hypothèse de l'auteur).

## Changements par rapport à la version précédente

- Le fichier `demarches_gains_v7.csv` est **remplacé** par `demarches_gains_v8.csv` (l'ancienne version reste consultable dans l'historique du dépôt).
- Les colonnes `gain_usagers_demat_bas` et `gain_usagers_demat_haut` changent de sens : en v7, un temps forfaitaire de 2 et 30 minutes pour tous les dossiers (total de 11,7 à 175,5 M€) ; en v8, des temps par étape selon la complexité (total de 30,0 à 106,8 M€).
- Deux colonnes sont ajoutées : `gain_total_bas` et `gain_total_haut`.
- Les colonnes d'administration et de préremplissage sont inchangées.

## Date et version

Version 8 des paramètres, données d'activité au 28/09/2026, fichier recalculé le 05/10/2026 (34 185 à 34 397 démarches selon le périmètre, 18,2 millions de dossiers déposés depuis 2018).

## Limites

- Les gains administration (France Stratégie 2018) sont des études étrangères (Australie, Royaume-Uni, Canada), non mesurées en France et non réactualisées.
- Les temps de mise en place et les temps évités par l'usager sont des **hypothèses de l'auteur**, pas des mesures — voir `donnees/hypotheses/` pour le détail, une analyse de sensibilité et un modèle de tableau pour les mesurer.
- Les gains sont des temps et des coûts valorisés, pas des économies budgétaires constatées.
