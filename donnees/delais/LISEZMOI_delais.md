# Délais de traitement — données dérivées

Production de l'auteur à partir de données ouvertes de data.gouv.fr (jeu « hackathon-dn », fichier `hackathon-ds-delai-instruction.csv`, export du 26/09/2024). Voir `donnees/LICENCE.md`.

## Fichiers

- **`delai_synthese_globale.csv`** — un seul enregistrement : nombre de dossiers de l'univers retenu, part traitée, délai dépôt→1ère instruction et dépôt→traitement (quartiles Q1/médiane/Q3), répartition en tranches (0-7j, 8-30j, 31-60j, plus de 60j, non traité).
- **`delai_par_complexite.csv`**, **`delai_par_type_demandeur.csv`**, **`delai_par_type_organisme.csv`** — le même jeu d'indicateurs (n dossiers, % traité, délais médians, tranches), croisé respectivement avec le niveau de complexité de la démarche (v7), le type de demandeur (particulier/entreprise/collectivité…) et le type d'organisme.

**Colonnes communes** : `n_dossiers`/`n`, `pct_traite`, `delai_median_instruction`, `delai_median_traitement`, `pct_0_7j`, `pct_8_30j`, `pct_31_60j`, `pct_plus_60j`, `pct_non_traite`.

## Calcul

Univers : dossiers déposés avant le 28/06/2024 (au moins 90 jours avant l'export, pour laisser le temps d'être traités). Délai dépôt→instruction et dépôt→traitement calculés au jour (pas à l'heure). « Traité » = date de traitement renseignée dans le fichier source à la date de l'export.

## Date et version

Export source du 26/09/2024. Analyse produite le 04/10/2026.

## Limites

Voir `note_delai_instruction.md` (méthode complète). Points clés : instantané figé à 2024, pas de distinction entre les états finaux (accepté/refusé/sans suite), délai mesuré au jour, démarches non rattachées au référentiel de complexité (2,8 %) comptées à part.
