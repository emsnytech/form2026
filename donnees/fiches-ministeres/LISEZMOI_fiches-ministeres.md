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
- `<prefixe>_papier.json` : démarches encore sur papier dans le périmètre — un exemple détaillé (l'instruction dans
  la famille, Cerfa 16212*05) et un tableau de candidats classés « papier seulement », « papier national, versions
  locales » ou « en ligne ailleurs ». Absent tant que `06_papier.py` n'a pas tourné pour ce ministère ; la section
  correspondante de la fiche est alors masquée, pas vide.
- `<prefixe>_etablissements.json` : les dix lycées et collèges qui utilisent le plus la plateforme, classés par
  dossiers des démarches actives depuis 2021. Un établissement = un SIRET, sauf quand ce SIRET appartient surtout à
  un rectorat ou une DSDEN (regroupement par libellé dans ce cas). Usages classés d'après le titre des démarches
  (indicatif). Absent tant que `07_etablissements.py` n'a pas tourné ; la section correspondante est alors masquée.
- `methode/` : scripts Python, configurations, gabarit et fond de carte qui produisent ces fichiers et la fiche.

## Sources

- « Descriptif des démarches publiées sur demarche.numerique.gouv.fr » (data.gouv.fr), extraction du 21/10/2026.
- « Utilisation du service demarche.numerique.gouv.fr » (data.gouv.fr), ressource « nb-dossiers-deposes-par-mois ».
- `donnees/gains/demarches_gains_v8.csv` (FORM 2026, paramètres v8).
- Fond de carte : gregoiredavid/france-geojson (départements, simplifié).
- Pour la section « Démarches encore sur papier » : les 68 Cerfa analysés champ par champ et les 3 621 fiches de
  service-public.fr embarqués dans `explorer.html` (FORM 2026), recoupés avec les démarches en ligne du périmètre.
  Pour chaque service en ligne cité hors Démarche Numérique, l'URL officielle vérifiée (education.gouv.fr,
  diplomatie.gouv.fr, afld.fr).

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
- Démarches encore sur papier : pour l'exemple détaillé, les émetteurs sont comptés par département (une démarche
  par DSDEN), pas par libellé d'organisme — ce dernier est orthographié de façon trop variable dans les données
  sources pour un compte fiable (de 61 à 81 selon la méthode). Sur les 9 autres candidats recensés : 6 sont « en
  ligne ailleurs » (dont le Cned, reclassé d'après la page de l'académie de Paris sur l'inscription au Cned,
  https://www.ac-paris.fr/inscription-au-cned-123640), 1 est « papier national, versions locales », et 2 restent
  classés « papier seulement » sans vérification complémentaire au-delà de FORM 2026 et de service-public.fr
  (sports.gouv.fr et education.gouv.fr n'ont pas pu être consultés au moment de la production).
- **Confidentialité** : les adresses e-mail et numéros de téléphone retirés des titres de démarches, noms
  d'organisme et noms de service sont remplacés par `[adresse électronique retirée]` ou `[numéro de téléphone
  retiré]`. Retrait fait à l'extraction, contrôlé une seconde fois avant publication.
