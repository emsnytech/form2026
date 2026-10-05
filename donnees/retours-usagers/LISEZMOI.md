# Retours d'usagers sur Démarche Numérique — données dérivées

Production de l'auteur à partir de données ouvertes de data.gouv.fr (jeu « Liste des expériences partagées par les usagers », plateforme Services Publics Plus, DITP). Voir `donnees/LICENCE.md`.

**À lire avant tout chiffre** : l'échantillon est **auto-sélectionné** — ce sont des témoignages spontanés d'usagers qui ont choisi d'écrire sur Services Publics Plus, pas un panel représentatif. La population « A » (citant explicitement Démarche Numérique ou Démarches Simplifiées par leur nom) est elle-même un sous-ensemble restreint (676 retours sur 167 532) et vraisemblablement plus technophile et plus mécontent que la moyenne. Le codage par motif a été fait **avec l'assistance d'un modèle de langage** (classification en 6 catégories, avec contrôle de stabilité par recodage à l'aveugle) — ce n'est pas une double lecture humaine exhaustive.

## Fichiers

- **`sp2_A_vs_Bp_par_annee.csv`** — effectif et part de ressenti négatif, par population (A = cite la plateforme, B' = canal démarche en ligne sans la citer) et par année, avec intervalle de confiance à 95 % (Wilson).
- **`sp2_A_vs_Bp_criteres.csv`** — parmi les négatifs, part de chaque critère (Accessibilité, Information/Explication, Relation, Réactivité, Simplicité/Complexité) tagué négatif, pour A et B', avec l'intervalle de confiance de la différence A−B'.
- **`sp2_standardise_par_annee.csv`** — les mêmes écarts de critères, après standardisation sur la même structure annuelle pour A et B'.
- **`sp2_robustesse_hors_typologie_dominante.csv`** — les mêmes critères pour A en excluant la typologie « Préfecture » (40 % de A), pour vérifier qu'elle ne porte pas seule l'écart observé.
- **`sp2_suivi_services.csv`** — part des retours avec réponse, part en attente, délais (quartiles) entre publication et première réponse, par population et par année.
- **`sp2_coding_A560_motifs.csv`**, **`sp2_coding_A560_par_annee.csv`** — codage manuel (assisté IA) des 560 retours négatifs de la population A en un motif principal (incompréhension du formulaire, pièces demandées, problème technique, délai/absence de réponse, qualité de la réponse, autre), avec intervalle de confiance.
- **`sp2_coding_300_resultats.csv`** — accord entre le motif codé et le critère plateforme attendu, sur l'échantillon de contrôle (150 dans A, 150 dans B').
- **`sp2_coding_accord_criteres.csv`** — le même accord, agrégé par motif.
- **`sp2_blind_recode_60.csv`** — contrôle de stabilité : 60 des 300 retours recodés une seconde fois à l'aveugle (motif d'origine vs motif du second codage).
- **`sp2_france_services.csv`** — donnée complémentaire, hors champ démarche en ligne : taux de démarches finalisées en un seul accompagnement dans les structures France Services (2021-2022 seulement), moyenne et médiane par année.
- **`note_retours_usagers_complement.md`** — note de méthode complète (la première note, sur les 676 retours citant la plateforme, est intégrée à celle-ci).

## Règles de confidentialité appliquées

Aucun de ces fichiers ne contient de pseudonyme, de texte libre d'usager (titre/description), de numéro de dossier, d'adresse électronique ou de numéro de téléphone — seulement des identifiants d'expérience et des agrégats chiffrés.

## Date et version

Jeu source à jour au 04/10/2026 (167 532 retours, 2019-2026). Analyse produite le 04-05/10/2026, graines aléatoires fixées et documentées dans la note.

## Limites

Voir `note_retours_usagers_complement.md`. Points clés : population A petite et non représentative ; le terme de recherche « démarche(s) numérique(s) » (sans guillemets ni majuscule) est en partie ambigu avec le sens générique de « dématérialisation » ; une partie de l'écart de réactivité observé dans A tient à la sur-représentation des démarches de préfecture.
