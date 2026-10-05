# Note de méthode — Délais de traitement (hackathon 2024)

Date : 04/10/2026. Source : `hackathon-ds-delai-instruction.csv` (export du 26/09/2024, jeu de données « hackathon-dn » sur data.gouv.fr). Granularité : au jour près (pas d'heure). Vérifié avant traitement : aucune colonne du fichier source ne contient de donnée personnelle (seulement `procedure_id` et 4 dates).

## 1. Filtrage

2 656 840 lignes (dossiers) dans le fichier source. Deux exclusions :

- **789 375 dossiers sans `date_depot`** (jamais réellement déposés — brouillon resté sans suite) : exclus d'emblée, hors du champ de l'analyse de délai.
- Parmi les dossiers déposés, seuls ceux **déposés avant le 28/06/2024** sont retenus — au moins 90 jours avant l'export du 26/09/2024, pour que même un dossier lent ait eu le temps d'être traité.

**Univers retenu : 1 553 405 dossiers.** 1 509 300 d'entre eux (97,2 %) se rattachent à une démarche présente dans le référentiel v7 du projet (niveau de complexité, type de demandeur, type d'organisme) ; les 2,8 % restants (démarches non référencées, probablement supprimées ou hors du corpus "publiée/close" du projet) sont comptés à part dans les tableaux croisés plutôt qu'exclus silencieusement.

## 2. Indicateurs globaux

| Indicateur | Valeur |
|---|---|
| Dossiers traités (`date_traitement` renseignée) | 1 375 501 / 1 553 405 = **88,5 %** |
| Délai dépôt → première instruction — médiane | **2 jours** (Q1 = 0 j, Q3 = 14 j) |
| Délai dépôt → traitement final — médiane | **4 jours** (Q1 = 1 j, Q3 = 26 j) |

### Tranches (délai dépôt → traitement), sur les 1 553 405 dossiers de l'univers

| Tranche | n dossiers | % |
|---|---|---|
| 0-7 jours | 822 815 | 53,0 % |
| 8-30 jours | 243 373 | 15,7 % |
| 31-60 jours | 126 365 | 8,1 % |
| Plus de 60 jours | 182 948 | 11,8 % |
| Non traité (à la date de l'export) | 177 904 | 11,5 % |

**Plus de la moitié des dossiers sont traités en une semaine**, mais le tableau est bimodal : un gros bloc rapide (53 % en ≤ 7 jours) et une traîne longue non négligeable (près d'1 dossier sur 5 met plus de 30 jours ou n'est toujours pas traité 90 jours après son dépôt).

## 3. Attente avant prise en charge vs. durée de l'instruction (point 5)

Les deux délais mesurés ne couvrent pas la même chose, et l'écart entre eux est informatif :

- **Dépôt → première instruction** (médiane 2 j) : le temps où le dossier attend, non regardé, dans la file de l'administration.
- **Dépôt → traitement final** (médiane 4 j) : le temps total jusqu'à la décision, instruction comprise.

**L'écart entre les deux médianes (2 jours) suggère qu'une fois qu'un agent ouvre le dossier, la décision suit rapidement** pour la moitié des cas — l'essentiel du délai médian global est de l'attente, pas du travail d'instruction. Mais les quartiles hauts racontent une autre histoire : Q3 du délai d'instruction est déjà de 14 jours, et Q3 du délai de traitement monte à 26 jours — pour le quart le plus lent des dossiers, l'instruction elle-même prend du temps, pas seulement l'attente. **Les deux délais doivent donc être lus ensemble, jamais l'un sans l'autre** : la médiane raconte une attente courte, la traîne raconte une instruction qui peut être longue.

## 4. Croisements (pondérés par les dossiers)

Chaque dossier compte pour un, donc les parts ci-dessous sont déjà pondérées par le volume réel (pas une moyenne de taux par démarche).

### Par niveau de complexité (v7)

| Complexité | n dossiers | % traité | Délai médian instruction | Délai médian traitement | ≤7j | 8-30j | 31-60j | >60j | Non traité |
|---|---|---|---|---|---|---|---|---|---|
| Simple | 592 469 (38,1 %) | 95,6 % | 1 j | 1 j | 77,0 % | 9,8 % | 3,5 % | 5,3 % | 4,4 % |
| Modérée | 404 363 (26,0 %) | 81,4 % | 4 j | 5 j | 47,0 % | 17,0 % | 7,7 % | 9,7 % | 18,6 % |
| Complexe | 508 445 (32,7 %) | 85,7 % | 8 j | 21 j | 29,4 % | 21,4 % | 13,4 % | 21,5 % | 14,3 % |
| Inconnu (démarche non référencée) | 48 128 (3,1 %) | 91,4 % | 1 j | 4 j | 56,5 % | 15,7 % | 12,8 % | 6,3 % | 8,6 % |

**Le délai médian de traitement est multiplié par 21 entre le niveau simple (1 jour) et complexe (21 jours)** — la complexité de la démarche est, de loin, le facteur le plus discriminant observé dans ce travail. À noter : les démarches modérées ont un taux de non-traité (18,6 %) plus élevé que les complexes (14,3 %) malgré un délai médian plus court — ce sont deux phénomènes distincts (vitesse de traitement vs. probabilité d'être traité du tout dans la fenêtre observée).

### Par type de demandeur

| Type | n dossiers | % traité | Délai médian instruction | Délai médian traitement |
|---|---|---|---|---|
| Particulier | 835 793 (53,8 %) | 95,2 % | 1 j | 3 j |
| Entreprise | 432 976 (27,9 %) | 78,6 % | 1 j | 4 j |
| Collectivité | 143 819 (9,3 %) | 86,3 % | 11 j | 18 j |
| Mixte | 55 535 (3,6 %) | 77,7 % | 10 j | 24 j |
| Indéterminé | 24 016 (1,5 %) | 76,9 % | 14 j | 56 j |
| Agent public | 12 371 (0,8 %) | 83,2 % | 5 j | 8 j |
| Association | 4 790 (0,3 %) | 64,2 % | 16 j | 20 j |

**Les démarches de collectivités et les démarches « mixtes » (ouvertes à plusieurs publics) ont des délais médians 6 à 8 fois plus longs que celles des particuliers** — cohérent avec des démarches structurellement plus complexes (subventions, conventions) plutôt qu'avec une discrimination par public. Le taux de non-traité le plus élevé (hors catégorie « indéterminé ») est sur les associations (35,8 %, mais seulement 4 790 dossiers — échantillon réduit, à ne pas sur-interpréter).

### Par type d'organisme

| Type | n dossiers | % traité | Délai médian instruction | Délai médian traitement |
|---|---|---|---|---|
| Services déconcentrés | 779 971 (50,2 %) | 85,3 % | 3 j | 7 j |
| État central | 353 831 (22,8 %) | 88,8 % | 5 j | 8 j |
| Autres | 278 674 (17,9 %) | 97,4 % | 1 j | 1 j |
| Collectivités | 58 275 (3,8 %) | 94,8 % | 2 j | 4 j |
| Opérateurs | 38 549 (2,5 %) | 75,8 % | 6 j | 19 j |

« Autres » (établissements d'enseignement, associations gestionnaires…) traite 89 % de ses dossiers en moins d'une semaine — nettement plus rapide que les services déconcentrés et l'État central, qui portent l'essentiel du volume (73 % des dossiers à eux deux) et des délais les plus longs en valeur absolue.

## 5. Limites

- **Instantané 2024, pas une mesure continue** : ces délais reflètent les dossiers déposés avant fin juin 2024 ; ils ne disent rien sur une évolution depuis (amélioration ou dégradation du service).
- **Les états finaux ne sont pas distingués** : un dossier « traité » en 3 jours peut avoir été accepté, refusé ou classé sans suite — la vitesse de traitement ne dit rien de la décision. Cette distinction n'existe pas dans le fichier source.
- **« Non traité » à la date de l'export (26/09/2024) n'est pas forcément un dossier bloqué indéfiniment** : certains auront été traités après l'export, hors du champ d'observation de ce fichier figé.
- **2,8 % des dossiers ne se rattachent à aucune démarche du référentiel v7** (démarches probablement retirées du corpus depuis 2024 ou hors périmètre publié/close) — comptés à part dans les croisements, jamais masqués.
- **Délai mesuré au jour, pas à l'heure** : un dossier déposé et traité le même jour calendaire compte 0 jour, qu'il ait été traité en 5 minutes ou en 20 heures.
- **Effet de composition possible dans les croisements** : un type d'organisme peut sembler plus lent simplement parce qu'il porte davantage de démarches complexes, pas parce qu'il instruit plus lentement à complexité égale (un croisement à complexité constante n'a pas été fait ici, faute de volume suffisant dans chaque cellule croisée à trois facteurs).

## Fichiers livrés

- `delai_synthese_globale.csv` — indicateurs globaux (1 ligne).
- `delai_par_complexite.csv`, `delai_par_type_demandeur.csv`, `delai_par_type_organisme.csv` — les trois croisements détaillés ci-dessus.
