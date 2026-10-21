# Fiches ministères — données dérivées

Production de l'auteur à partir de données ouvertes de data.gouv.fr. Voir `donnees/LICENCE.md`.

## Fichiers (par fiche, `<prefixe>` = `education` pour la fiche n° 1)

- `<prefixe>.json` : indicateurs annuels (démarches publiées, closes, actives, en ligne au 31/12), par pôle, émetteurs
  (SIRET et libellés distincts, types d'organisme), qualité des formulaires (champs, pièces justificatives, Annuaire Éducation,
  SIRET, IBAN, RNA, API Particulier), démarches les plus utilisées, démarches exclues.
- `<prefixe>_familles.json` : familles de démarches homologues repérées par leur titre (exemples, pas une classification).
- `<prefixe>_reconductions.json` : nouvelles démarches et reconductions annuelles (même émetteur, même titre sans millésime).
- `<prefixe>_complements.json` : dossiers estimés par année et contrôle sur les dépôts réels, carte par département,
  frais évités, démarches candidates au quotient familial (API Particulier).
- `methode/` : scripts Python, configurations, gabarit et fond de carte qui produisent ces fichiers et la fiche.

## Sources

- « Descriptif des démarches publiées sur demarche.numerique.gouv.fr » (data.gouv.fr), extraction du 21/10/2026.
- « Utilisation du service demarche.numerique.gouv.fr » (data.gouv.fr), ressource « nb-dossiers-deposes-par-mois ».
- `donnees/gains/demarches_gains_v8.csv` (FORM 2026, paramètres v8).
- Fond de carte : gregoiredavid/france-geojson (départements, simplifié).

## Calcul (résumé)

- Ministère : champ `zones` de la démarche ; à défaut (surtout avant 2023), nom de l'organisme. Plus de trois zones : démarche
  interministérielle, exclue. Démarches déclarées à tort (MSA, CAF) : exclues.
- Années : publiée l'année de `datePublication` ; close l'année de `dateFermeture` ou `dateDepublication` ; en ligne au 31/12 si
  publiée et pas encore fermée.
- Dossiers par année : `dossiersCount` (cumul) réparti au prorata des jours d'ouverture. Appliquée à toute la plateforme,
  la méthode retrouve 75 à 93 % des dépôts publiés selon l'année : c'est un plancher.
- Frais évités : gain par dossier de chaque démarche (fichier v8) × dossiers de la période ; 98,6 % des dossiers couverts.

## Limites

- Le champ ministère est déclaratif ; son intitulé suit le référentiel actuel de la plateforme, pas l'intitulé de l'époque.
- `forIndividual` ne distingue pas usagers et agents.
- Les frais évités sont des temps et des coûts valorisés, pas des économies budgétaires constatées.
