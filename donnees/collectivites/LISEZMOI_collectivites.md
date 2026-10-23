# Démarche Numérique, pour et par les collectivités — données dérivées

Production de l'auteur à partir de données ouvertes de data.gouv.fr. Voir `donnees/LICENCE.md`.
Actualisation (octobre 2026) du bilan « Les collectivités et Démarches simplifiées » du 12 novembre 2024,
et complément au bilan DGCL « Les dotations de soutien des collectivités territoriales en 2025 » (octobre 2026).

## Fichiers

- `montants_dgcl.csv` : par exercice (2018-2025) et famille de dotations (DETR-DSIL, DPV, DSID) — nombre de départements
  dotés d'une démarche de demande active sur la plateforme, montant total attribué, montant attribué dans ces départements,
  projets, bénéficiaires (SIREN), coût HT des projets.
- `fonds_vert_par_an.csv` : par exercice (2023-2025) et source (programme principal, programme 113) — montant engagé,
  dossiers financés, part des lignes portant un numéro de dossier de la plateforme, bénéficiaires (SIREN).
- `methode/` : scripts Python qui produisent ces fichiers et les chiffres de la page.

## Sources

- « Descriptif des démarches publiées sur demarche.numerique.gouv.fr » (data.gouv.fr), extraction du 21/10/2026.
- « Projets financés par les dotations de soutien à l'investissement des collectivités territoriales » (DGCL, data.gouv.fr), 2018-2025.
- « Fonds vert - Liste des projets subventionnés » (data.gouv.fr), exports 2023, 2024, 2025, y compris programme 113.
- « Utilisation du service demarche.numerique.gouv.fr » (data.gouv.fr), dépôts mensuels, pour contrôler les séries annuelles.

## Calcul (résumé)

- « Par les collectivités » : type d'organisme déclaré « collectivité territoriale », moins 104 démarches manifestement mal déclarées.
- « Pour les collectivités » : démarches d'un autre type d'organisme dont le titre désigne les collectivités ou une dotation (plancher).
- Montants DGCL : un projet est compté si son département avait, la même année, une démarche de demande active pour la dotation
  (démarches de paiement exclues). Fonds vert : toutes les lignes, chacune portant un numéro de dossier de la plateforme.
- Séries annuelles de dossiers : compteur cumulé réparti au prorata des jours d'ouverture (plancher, 75 à 93 % des dépôts réels).

## Limites

- Montants : subventions attribuées à des dossiers instruits sur la plateforme, pas des flux financiers qui y transitent.
  Pour les premières années, un département couvert a pu recevoir encore des dossiers papier : 2018-2020 sont des plafonds.
- Bénéficiaires (34 757, dont ≈ 29 600 communes) : plancher ; ni les demandes non retenues ni les autres démarches n'y figurent.
- Aucune donnée au niveau du dossier n'est utilisée.
