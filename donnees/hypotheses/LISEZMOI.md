# Hypothèses et analyse de sensibilité — données dérivées

Production de l'auteur, hypothèses explicites présentées avec leur statut et une analyse de sensibilité. Voir `donnees/LICENCE.md`.

## Fichiers

### `temps_par_etape.csv`

Le détail, étape par étape, des temps évités côté administration et côté usager, pour un dossier déposé en PDF dans une boîte fonctionnelle par rapport à un dossier déposé sur une démarche en ligne complète — par niveau de complexité (simple/modérée/complexe), en minutes.

**Colonnes** : `cote` (administration/usager), `etape`, `simple_min`, `moderee_min`, `complexe_min`, `statut` (hypothèse de l'auteur, somme, différence, ou référence externe le cas échéant).

Ces temps sont la décomposition qui sous-tend les gains agrégés de `donnees/gains/parametres_v8.csv` (`gain_traitement_evite_par_dossier_construit`, `temps_evite_usager_demat_bas/haut`).

### `cout_horaire_sensibilite.csv`

Analyse de sensibilité du coût de mise en place d'une démarche (et du rapport gains/coûts qui en découle) à la valeur horaire retenue pour les agents publics — du traitement indiciaire seul jusqu'à la valorisation finalement retenue dans les notes du projet (44,70 €/h, coût horaire du travail en France, Insee/Eurostat).

**Colonnes** : `scenario`, `coefficient_sur_traitement`, `mise_en_place_bas_MEUR`/`centre_MEUR`/`haut_MEUR`, `rapport_gains_couts_min`/`max`, `rapport_apparie_bas`/`haut` (hypothèses basses entre elles, hautes entre elles), `commentaire`.

## Pourquoi ce dossier

Chaque notion construite par l'auteur (temps de mise en place, temps évités) est, par principe du projet, présentée avec sa décomposition et sa sensibilité aux hypothèses — pour que ces chiffres puissent être vérifiés, contestés ou recalculés avec d'autres valeurs.

## Date et version

Fichiers produits le 04/10/2026, cohérents avec les paramètres v8 (`donnees/gains/parametres_v8.csv`).

## Limites

Ce sont des **hypothèses de l'auteur**, pas des mesures de terrain, sauf mention contraire dans la colonne `statut`/`commentaire`. La valorisation horaire retenue dans les notes du projet (44,70 €/h) est documentée comme un choix de méthode, pas comme une valeur consensuelle unique — voir `cout_horaire_sensibilite.csv` pour la plage de résultats selon d'autres choix possibles.
