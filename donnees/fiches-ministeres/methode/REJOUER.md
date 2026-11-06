# Rejouer les fiches ministères

**Règle :** ce qui produit une page publiée vit dans ce dépôt. Ce dossier fait foi. Aucune copie sur un poste ne le remplace.

## Reconstruire

Il faut Python 3 avec `ijson`, et le fichier brut du jeu « [Descriptif des démarches publiées](https://www.data.gouv.fr/datasets/descriptif-des-demarches-publiees-sur-demarche-numerique-gouv-fr) » de data.gouv.fr (extraction du 21 octobre 2026, environ 730 Mo).

```
donnees/fiches-ministeres/methode/rejouer.sh <chemin du brut>
git diff
```

Le script reconstruit les deux fiches et les publie dans l'arbre de travail. Il ne fait ni commit ni push. Avec le même fichier brut, `git diff` ne doit rien montrer. `out/`, `data/` et les fiches construites restent hors du dépôt : ils citent des titres sensibles, ou pèsent trop.

Pour republier sans reconstruire : `python3 integration/integrer_fiches.py`. C'est le seul point d'entrée. Il refuse d'écrire une page sans réserve de méthode, avec une adresse électronique ou avec un titre sensible.

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
