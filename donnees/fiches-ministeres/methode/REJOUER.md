# Rejouer les fiches ministères

**Règle :** ce qui produit une page publiée vit dans ce dépôt. Ce dossier fait foi. Aucune copie sur un poste ne le remplace.

## Reconstruire

Il faut Python 3 avec `ijson`, et le fichier brut du jeu « [Descriptif des démarches publiées](https://www.data.gouv.fr/datasets/descriptif-des-demarches-publiees-sur-demarche-numerique-gouv-fr) » de data.gouv.fr (extraction du 21 octobre 2026, environ 730 Mo). La fiche Intérieur relit aussi l'extraction du 1er novembre 2025 du même jeu (environ 390 Mo), pour les dossiers récents des versions locales restées en ligne (script 45).

```
donnees/fiches-ministeres/methode/rejouer.sh <chemin du brut> <chemin du brut du 1er novembre 2025>
git diff
```

Le script reconstruit les trois fiches et les publie dans l'arbre de travail. Il ne fait ni commit ni push. Avec le même fichier brut, `git diff` ne doit rien montrer. `out/`, `data/` et les fiches construites restent hors du dépôt : ils citent des titres sensibles, ou pèsent trop.

Pour republier sans reconstruire : `python3 integration/integrer_fiches.py`. C'est le seul point d'entrée. Il refuse d'écrire une page sans réserve de méthode, avec une adresse électronique ou avec un titre sensible.

## Fiche n° 3 : Intérieur

`rejouer.sh` la reconstruit avec le même fichier brut : `02_fiche_ministere.py` sur `scripts/config_interieur.json`, puis les scripts 30 à 45 (familles dans `scripts/familles_interieur.json`, codes et noms des départements dans `scripts/departements.json`), le script 39 en dernier, qui écrit la maquette `out/maquette_interieur.md`. `fiche/build_interieur.py` la met en page sans ajouter de chiffre. Les scripts 35 et 41 relisent le fichier brut, dont `rejouer.sh` passe le chemin par la variable `FORM2026_RAW`. Le script 45 lit l'extraction du 1er novembre 2025, passée par `FORM2026_RAW_PRECEDENT`.

Deux entrées ne viennent pas du descriptif ouvert ; elles sont versées dans `sources/` avec leur note :

- `insee_populations_reference_2023_departements.csv` : populations de référence 2023 de l'INSEE, pour le contrôle de taille (script 40) ;
- les quatre exports du tableau de bord public de ProConnect du 15 novembre 2026, pour l'encadré « Côté agents » (script 43). Un libellé de service y est masqué, sans effet sur les chiffres (voir `sources/SOURCE_proconnect.md`).

Les circulaires DETR et DSIL, la charte IA et la documentation Maarch sont citées par leur lien, leur date et leurs extraits (`sources/SOURCE_*.md`) : aucun PDF n'est versé.

`build_interieur.py` s'arrête si la page contient une adresse électronique, un numéro de téléphone, un nom de département hors des données de la carte et de son tableau replié, un titre qui attribue Turgot au ministère, une marque de travail, un intitulé « part de la plateforme », ou si la réserve de méthode ou le cadre d'entrée de `scripts/sync_cadre.py` manquent. Sa version de relecture (`fiche/relecture-interieur.html`) reste hors du dépôt.

Les sorties qui nomment des départements ne sont pas publiées : `rejouer.sh` les reproduit dans `out/`.

## Contrôles

- `scripts/controle_fiches.py` : adresses, titres sensibles, réserve, intitulés, chemins de poste et liste des fichiers.
- `integration/integrer_fiches.py --verifier` : l'index et les listes correspondent à ce que le script produirait.

Le workflow `controle-fiches.yml` lance les deux à chaque PR.

## Ce qui ne se rejoue pas à l'identique

- **Relevés de pages vivantes (scripts 12, 15, 17, 22) :** leurs compteurs changent chaque jour. `rejouer.sh` ne les relance pas et repart du dernier état publié et daté (`justice_hors_opendata.json`, `justice_experts_publics.json`, `rdv_cdad_metabase.json`).
- **Démarche agrégée hors fichier :** son adresse n'est pas dans le dépôt, parce qu'elle contient son titre. Le script 12 conserve son dernier relevé, sauf si un fichier local `data/chemins_agreges.json` la fournit.
- **Sorties intermédiaires qui lisent `explorer.html` :** `justice_inventaire.json` suit l'état de cette page. Aucun chiffre publié n'en dépend à ce jour.
- **Fichier brut :** il n'est pas dans le dépôt. Rien ne garantit que data.gouv.fr conserve indéfiniment l'extraction du 21 octobre 2026.

## L'exception

Le script de comparaison à une extraction interne (n° 21) reste hors du dépôt public, parce qu'il lit une source interne que le lecteur ne peut pas consulter. Aucun chiffre publié n'en dépend : il a seulement servi à décider des réserves de méthode. Les autres scripts d'analyse d'une source interne suivent le même régime. Chacun est nommé ici avec sa source :

| Script | Source interne lue | Objet |
|---|---|---|
| 21 `ecart_metabase.py` | extraction Metabase retravaillée, périmètre Justice | écart entre une extraction interne et l'open data |
| 23 `ecart_plateforme.py` | export brut Metabase des démarches publiées, closes ou dépubliées (5 novembre 2026) | écart à l'échelle de la plateforme et causes des absences |
| 24 `attribution.py` | même export | rattachement de chaque démarche au ministère de son service traitant |
| 25 `zones_procedures.py` | extraction Metabase de la table des zones des démarches (6 novembre 2026) | couverture et provenance des zones |
| 26 `ecarts_ministeres.py` | les deux extractions précédentes | écarts par ministère et carte des flux, sur les zones posées par les services |

Aucun de ces scripts n'est publié. Aucun chiffre publié n'en dépend.

## Démarches agrégées

Les démarches sensibles (casier judiciaire, suivi de plaintes, mineurs) sont désignées par leur numéro dans les scripts, jamais par un fragment de titre. Le classement obtenu est identique à celui fondé sur les titres : 392 démarches, aucune différence.
