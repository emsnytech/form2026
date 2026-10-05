# Note de méthode — Élargissement du test du cadre juridique

Date : 01/10/2026. Fait suite à un premier test sur 30 démarches (A 4, B 7, C 14, D 5 ; « lien inutilisable » ≈ 47 %, marge indicative ± 18 points).

## 1. Définitions

Qualification du cadre juridique déclaré par chaque démarche (champ `cadreJuridiqueURL` de l'export open data démarche.numerique.gouv.fr) :

- **A** — précis, en vigueur, qui fonde la démarche.
- **B** — pertinent mais trop général ou daté.
- **C** — lien mort, hors sujet ou page d'accueil/recherche.
- **D** — absent ou non juridique.

Classification automatique de Niveau 1 (règles explicites, sans recherche) du contenu du champ, qu'il s'agisse d'un lien ou de texte libre :

- `absent` — champ vide ou valeur-placeholder (« - », « à définir », etc.).
- `page_accueil_recherche` — racine d'un domaine, page de recherche/rubrique.
- `texte_entier_sans_article` — renvoie à un code ou un texte entier (LEGITEXT/JORFTEXT, `affichCode.do`…) sans identifiant d'article.
- `article_precis` — identifiant d'article (LEGIARTI/JORFARTI) ou citation textuelle d'un article précis.
- `circulaire` — circulaire ou bulletin officiel.
- `deliberation_reglement_organisme` — délibération, règlement intérieur ou décision propre à l'organisme (détecté par le texte, ou par le champ plateforme `deliberation=true` en complément quand le contenu lui-même reste générique).
- `autre_site` — tout le reste (communiqué, page d'information, document interne, EUR-Lex, documentation technique…).

## 2. Niveau 1 — contrôle automatique sur tout le corpus

Univers : les 34 397 démarches « publiées » ou « closes » du corpus FORM2026, **moins 284 démarches techniques de test** repérées par le mot « test » dans le titre (ex. « [PHASE DE TEST] Remontée des résultats… », « TEST — Avis de vacance… », « Test de procédure NPI ») et retirées car elles n'ont par construction aucun cadre juridique réel à évaluer. **Univers retenu : 34 113 démarches.** La colonne `demarche_test` de `juridique_niveau1.csv` conserve la trace des 284 démarches exclues (le fichier garde ses 34 397 lignes pour la traçabilité ; tous les tableaux ci-dessous sont calculés hors test). Champ source : `cadreJuridiqueURL`, complété par le flag plateforme `deliberation`.

### Répartition globale (démarches, hors test, n=34 113)

| Catégorie | n | % |
|---|---|---|
| texte_entier_sans_article | 9 690 | 28,4 % |
| page_accueil_recherche | 7 987 | 23,4 % |
| autre_site | 6 177 | 18,1 % |
| article_precis | 3 911 | 11,5 % |
| absent | 3 832 | 11,2 % |
| deliberation_reglement_organisme | 1 390 | 4,1 % |
| circulaire | 1 126 | 3,3 % |

L'exclusion des 284 démarches de test ne change la répartition que de façon marginale (moins de 0,3 point sur chaque catégorie) : son effet était négligeable, mais le chiffre est désormais exact plutôt qu'approché.

### Répartition pondérée par dossiers (hors test, 18 263 512 dossiers au total)

| Catégorie | dossiers | % |
|---|---|---|
| texte_entier_sans_article | 5 141 611 | 28,2 % |
| page_accueil_recherche | 4 712 523 | 25,8 % |
| autre_site | 3 012 276 | 16,5 % |
| article_precis | 2 757 232 | 15,1 % |
| absent | 1 992 369 | 10,9 % |
| deliberation_reglement_organisme | 378 328 | 2,1 % |
| circulaire | 269 173 | 1,5 % |

La pondération par dossiers ne change pas l'ordre de grandeur : les grosses démarches (volume élevé) ne sont ni mieux ni moins bien dotées en cadre juridique exploitable que les petites — `page_accueil_recherche` est même légèrement sur-représenté en dossiers (25,8 % contre 23,4 % en démarches).

### Par type d'organisme (% démarches, hors test)

| Type | n | texte entier | page accueil | autre site | article précis | absent | délib./règl. | circulaire |
|---|---|---|---|---|---|---|---|---|
| Services déconcentrés | 16 733 | 30 % | 20 % | 17 % | 14 % | 11 % | 4 % | 4 % |
| Autres | 7 837 | 24 % | 29 % | 20 % | 8 % | 14 % | 4 % | 2 % |
| État central | 5 032 | 33 % | 25 % | 18 % | 8 % | 11 % | 4 % | 3 % |
| Opérateurs | 1 721 | 34 % | 23 % | 14 % | 14 % | 6 % | 4 % | 5 % |
| Collectivités | 2 790 | 28 % | 28 % | 25 % | 10 % | 10 % | 4 % | 0 % |

Les collectivités se distinguent par une part élevée de pages d'accueil et « autre site » (53 % cumulés) et une part quasi nulle de circulaires — cohérent avec l'absence de bulletin officiel propre aux collectivités.

### Par public (% démarches, hors test)

| Public | n | texte entier | page accueil | autre site | article précis | absent | délib./règl. | circulaire |
|---|---|---|---|---|---|---|---|---|
| Particulier | 21 543 | 29 % | 24 % | 20 % | 12 % | 9 % | 3 % | 3 % |
| Personne morale | 12 570 | 27 % | 22 % | 16 % | 11 % | 16 % | 5 % | 4 % |

Les démarches à destination des personnes morales ont près de deux fois plus de champs vides (16 % vs 9 %) ; celles pour les particuliers renvoient un peu plus souvent à une page d'accueil.

### Par type d'organisme (% dossiers, hors test)

| Type | n dossiers | texte entier | page accueil | autre site | article précis | absent | délib./règl. | circulaire |
|---|---|---|---|---|---|---|---|---|
| Services déconcentrés | 7 941 105 | 31 % | 20 % | 10 % | 23 % | 13 % | 2 % | 1 % |
| Autres | 2 733 202 | 13 % | 44 % | 14 % | 10 % | 16 % | 3 % | 1 % |
| État central | 6 022 119 | 33 % | 27 % | 22 % | 7 % | 7 % | 2 % | 2 % |
| Opérateurs | 634 755 | 35 % | 14 % | 11 % | 26 % | 6 % | 1 % | 6 % |
| Collectivités | 932 331 | 12 % | 24 % | 48 % | 5 % | 8 % | 4 % | 0 % |

Pondérer par dossiers accentue certains écarts : « Autres » (établissements d'enseignement, associations…) concentre 44 % de ses dossiers sur des démarches renvoyant à une simple page d'accueil, et les collectivités 48 % sur « autre site ».

### Par public (% dossiers, hors test)

| Public | n dossiers | texte entier | page accueil | autre site | article précis | absent | délib./règl. | circulaire |
|---|---|---|---|---|---|---|---|---|
| Particulier | 12 392 503 | 27 % | 24 % | 19 % | 18 % | 8 % | 2 % | 2 % |
| Personne morale | 5 871 009 | 31 % | 29 % | 12 % | 8 % | 16 % | 2 % | 1 % |

### Accessibilité des liens

Contrôle HTTP (HEAD, repli GET si HEAD refusé, délai de 10 s, 4 requêtes simultanées maximum par domaine) sur les **5 336 URL distinctes** portées par les 27 723 démarches (hors test) dont le champ contient un lien (plusieurs démarches partagent souvent la même URL générique). Une erreur 403 ou un délai dépassé est comptée en **non vérifiable**, jamais en lien mort, conformément à la consigne.

| Statut | n démarches concernées | % |
|---|---|---|
| Non vérifiable (403, blocage anti-bot, délai dépassé, 5xx…) | 21 342 | 77,0 % |
| Accessible (200-299) | 5 494 | 19,8 % |
| Lien mort (404/410) | 887 | 3,2 % |

**Le blocage anti-bot domine très largement** : sur les URL distinctes testées, 3 257 des 5 336 (61,0 %) renvoient un code 403, essentiellement Légifrance et plusieurs sites ministériels protégés par Cloudflare — confirmé indépendamment par les agents du Niveau 2, qui ont systématiquement rencontré les mêmes 403 en vérification manuelle et les ont contournés via lecture directe du contenu (WebFetch passe ces protections quand `curl` échoue) ou via la Wayback Machine. **Un contrôle HTTP automatisé seul sous-estime donc fortement le taux réel de liens morts** : l'essentiel du « non vérifiable » recouvre des liens en réalité valides mais inaccessibles aux robots, pas des démarches sans cadre juridique. Les 3,2 % de vrais 404/410 restent en revanche un chiffre plancher fiable.

## 3. Niveau 2 — échantillon stratifié de 120 démarches

Graine aléatoire fixée : **42** (identique à l'échantillon initial de 30, qui est entièrement repris dans les 120 — 90 démarches nouvelles tirées en complément). Stratification croisée **type d'organisme (5 modalités) × public (2) × tranche de volume (petit ≤10, moyen 11-500, gros >500 dossiers)**, soit 30 cellules non vides sur 34 397 démarches. Allocation proportionnelle à l'effectif de chaque cellule (plancher 1), les 30 démarches déjà traitées comptant dans le quota de leur cellule. Effectifs détaillés dans `juridique_strates_effectifs.csv`.

La variable « nature » (dispositif volontaire / obligation légale) prévue en 4e axe de stratification n'a **pas** pu être utilisée comme critère de tirage : elle n'est identifiable qu'après vérification individuelle du texte (souvent impossible à deviner a priori), ce que le texte de la demande anticipait déjà (« quand elle est identifiable »). Elle est renseignée a posteriori dans la colonne `notes` de `juridique_echantillon.csv` quand le vérificateur a pu la déterminer, mais n'est pas exploitée comme stratum.

### Répartition A/B/C/D (120 démarches, intervalle de confiance à 95 % — méthode de Wilson)

| Qualification | n | % | IC 95 % |
|---|---|---|---|
| **A** — directement exploitable | 19 | 15,8 % | [10,4 % ; 23,4 %] |
| **B** — pertinent mais général/daté | 30 | 25,0 % | [18,1 % ; 33,4 %] |
| **C** — lien inutilisable (mort/hors sujet/accueil) | 44 | 36,7 % | [28,6 % ; 45,6 %] |
| **D** — absent/non juridique | 27 | 22,5 % | [15,9 % ; 30,8 %] |

Agrégats utiles : A+B (un cadre réel existe, même imparfait) = 49/120 = 40,8 % [32,5 % ; 49,8 %] · C+D (rien d'exploitable sans recherche complémentaire) = 71/120 = 59,2 % [50,2 % ; 67,5 %].

**La proportion de 47 % mesurée sur l'échantillon initial de 30 démarches se confirme à l'échelle de 120** (36,7 % pour C seul, 59,2 % en comptant aussi les démarches D) : l'intervalle à n=30 [29 %-65 %] contenait déjà la valeur observée à n=120, et l'élargissement réduit la marge d'erreur de ±18 points à ±9 points comme anticipé.

### Estimations pondérées par strate

L'allocation de l'échantillon n'étant pas strictement proportionnelle (plancher de 1 par cellule, 30 démarches du premier test comptées dans leur strate), chaque démarche *i* reçoit un poids de redressement `w_i = effectif_population(strate_i) / effectif_échantillon(strate_i)` (somme des poids = 34 397, l'univers complet). Comparaison avec l'estimation brute (non pondérée) :

| Qualification | Brute (n=120) | Pondérée par strate |
|---|---|---|
| A | 15,8 % | 16,3 % |
| B | 25,0 % | 25,4 % |
| C | 36,7 % | 34,8 % |
| D | 22,5 % | 23,4 % |
| A seul | 15,8 % | 16,3 % |
| C seul | 36,7 % | 34,8 % |
| A+B | 40,8 % | 41,8 % |
| C+D | 59,2 % | 58,2 % |

**L'écart entre estimation brute et pondérée reste faible (1 à 2 points)**, ce qui confirme que le plan d'échantillonnage n'introduit pas de biais de composition majeur malgré l'allocation non strictement proportionnelle. Le calcul d'un intervalle de confiance propre à l'estimateur pondéré (variance stratifiée) n'a pas été fait : l'écart observé reste de toute façon à l'intérieur des intervalles de Wilson calculés sur l'estimation brute, qui restent la référence pour la marge d'erreur de ce rapport.

### Croisement catégorie de Niveau 1 × qualification A-D

Confronte la classification automatique (sans recherche) à la qualification issue de la vérification manuelle, sur les 120 démarches de l'échantillon :

| Catégorie Niveau 1 | n | A | B | C | D |
|---|---|---|---|---|---|
| Article précis | 13 | 4 (31 %) | 6 (46 %) | 3 (23 %) | 0 (0 %) |
| Texte entier sans article | 34 | 10 (29 %) | 18 (53 %) | 6 (18 %) | 0 (0 %) |
| Circulaire | 3 | 2 (67 %) | 0 (0 %) | 1 (33 %) | 0 (0 %) |
| Délibération/règlement | 9 | 1 (11 %) | 1 (11 %) | 2 (22 %) | 5 (56 %) |
| Page accueil/recherche | 31 | 1 (3 %) | 1 (3 %) | 26 (84 %) | 3 (10 %) |
| Autre site | 19 | 1 (5 %) | 4 (21 %) | 6 (32 %) | 8 (42 %) |
| Absent | 11 | 0 (0 %) | 0 (0 %) | 0 (0 %) | 11 (100 %) |

**Ce croisement valide partiellement la classification automatique** : « absent » prédit D à 100 %, et « page accueil/recherche » prédit C à 84 % — deux catégories fiables comme indicateurs de masse. En revanche, « article précis » ne prédit A que dans 31 % des cas (46 % finissent B, 23 % même C) : la présence d'un identifiant LEGIARTI/JORFARTI dans l'URL ne suffit pas à garantir que l'article est pertinent et à jour, confirmant que le Niveau 1 mesure une tendance et ne peut pas remplacer la vérification individuelle. « Délibération/règlement » est la catégorie la moins fiable (56 % finissent D) : le flag plateforme `deliberation` ou la détection textuelle surestiment la présence d'un cadre réel.

## 4. Contrôle de stabilité (requalification à l'aveugle)

20 des 30 démarches du premier test ont été requalifiées par des agents n'ayant eu accès à aucune qualification antérieure (seuls `demarche`, `organisme` et `cadre_declare` leur ont été transmis ; tirage parmi les 30, seed 42).

- **Taux d'accord exact : 13/20 = 65 %.**
- **Accord à ±1 catégorie sur l'échelle ordinale A→D : 20/20 = 100 %** — aucun désaccord n'a dépassé une catégorie adjacente (pas de A requalifié D ni l'inverse).

Détail des 7 désaccords :

| Démarche | Qualif. initiale | Qualif. aveugle | Explication |
|---|---|---|---|
| 14308 | D | C | Cas limite, cadre quasi absent dans les deux lectures. |
| 55808 | A | B | **Erreur de la première lecture, pas une péremption entre les deux tests.** Le texte (arrêté du 8 janvier 2001) est abrogé depuis le 16/02/2026 — soit plus de 7 mois avant les DEUX lectures (29/09 et 01/10/2026, à 2 jours d'écart). La première lecture avait noté elle-même « version affichée est la version initiale, avec renvoi vers version consolidée non revérifiée » et l'a quand même qualifiée A ; la relecture aveugle a ouvert la version consolidée, vu le statut « abrogée », et correctement rétrogradé en B. |
| 128162 | B | A | La relecture aveugle a jugé les articles CESEDA L421-5/L421-6 suffisamment précis pour A ; jugement initial plus sévère sur la généralité de la section. |
| 131120 | B | A | Même type d'écart que ci-dessus (LEGIARTI précis jugé A en relecture, B initialement). |
| 136436 | C | D | Frontière C/D sur un site thématique sans valeur juridique propre. |
| 138599 | D | C | Frontière D/C, site racine jugé page d'accueil en relecture plutôt qu'absent. |
| 152185 | B | C | La loi Informatique et Libertés (6 janvier 1978) jugée hors sujet en relecture (texte réel mais sans lien avec l'objet de la démarche) plutôt que « pertinent mais général ». |

**Lecture** : la méthode est reproductible sur l'essentiel (aucune inversion de polarité A↔D), mais le placement exact aux frontières A/B et B/C comporte une part de jugement — un tiers des qualifications individuelles peut glisser d'un cran selon le vérificateur. Les agrégats (A+B vs C+D) sont donc plus robustes que la lecture catégorie par catégorie.

## 5. Effort de vérification

Temps détaillé démarche par démarche livré dans `juridique_temps_verification.csv` (110 lignes : 90 nouvelles démarches du Niveau 2 + 20 de la requalification à l'aveugle ; les 30 du premier test n'avaient pas été chronométrées démarche par démarche, seulement en volume global — non incluses ici). Sur ces 110 démarches :

- **Temps médian : 7,5 minutes par démarche** (moyenne 8,1 min, de 2 à 25 min selon la difficulté).
- **Source la plus utile, de loin : Légifrance en accès direct** (plus de 40 % des cas conclusifs), suivi par la relecture directe de pages institutionnelles et, en dernier recours, le moteur de recherche interne de Légifrance quand les quotas de recherche web de la session étaient épuisés.
- Les cas longs (15-25 min) sont presque tous des démarches B/C/D où plusieurs pistes de remplacement ont dû être testées avant d'aboutir à « non trouvé » ou à une référence vérifiée.

Un outil qui proposerait automatiquement l'article Légifrance le plus probable (par recherche structurée sur le titre + l'organisme) ferait gagner l'essentiel de ces 7-8 minutes médianes sur plus de la moitié des 34 113 démarches du corpus hors test (celles classées B/C/D, soit environ 84 % du total par extrapolation de la part B/C/D observée dans l'échantillon).

## 6. Limites

- **Démarches de test exclues du Niveau 1, détection par mot-clé uniquement** : les 284 démarches exclues (§2) sont repérées par la présence du mot « test » dans le titre — une règle simple qui peut laisser passer un très petit nombre de démarches de test sans ce mot, ou exclure à la marge une démarche réelle qui mentionnerait « test » sans être une démarche technique (aucun cas de ce type identifié en relisant la liste). Aucune des 284 n'est tombée dans l'échantillon de 120 par chance de tirage.
- **Classification automatique de Niveau 1 imparfaite** : elle repose sur des règles de texte/URL et ne peut pas distinguer, par exemple, un lien EUR-Lex pertinent d'un lien EUR-Lex générique, ou une « page d'accueil » d'organisme qui mènerait en réalité (après clic) à un texte pertinent. Elle sert à mesurer une tendance de masse, pas à qualifier une démarche individuelle.
- **Quotas d'outils (WebSearch/WebFetch) épuisés en cours de session** à plusieurs reprises (limite de session API partagée entre les agents de vérification) : dans ces cas, conformément à la règle « jamais de référence non vérifiée », les vérificateurs ont systématiquement écrit « non trouvé » plutôt que de citer une piste non confirmée. Cela **sous-estime probablement légèrement** la proportion réelle de A/B atteignable avec un budget de recherche illimité.
- **Erreurs HTTP 403 et blocages anti-bot fréquents** sur Légifrance et plusieurs sites ministériels (Cloudflare) lors des vérifications directes : traités systématiquement comme « non vérifiable », jamais comme preuve de lien mort, avec recours à la Wayback Machine ou à des URLs Légifrance équivalentes quand possible pour trancher.
- **La variable « nature » (volontaire/obligation légale)** n'a pas pu servir de critère de stratification (cf. §3) faute d'être identifiable a priori.
- **Vérifier la version consolidée, pas la version initiale d'un texte** : le cas de la démarche 55808 (§4) montre qu'une référence peut être qualifiée A à tort si le vérificateur s'arrête à la version initiale publiée d'un texte sans ouvrir sa version consolidée (qui seule indique un éventuel abrogation). Ce n'est pas un cas de péremption survenue « entre deux contrôles » — le texte était déjà abrogé depuis plus de 7 mois au moment des deux lectures (toutes deux après l'abrogation, à 2 jours d'écart) — mais une étape de vérification manquée dans le premier passage. Le risque de péremption réelle entre deux contrôles espacés dans le temps reste néanmoins documenté par ailleurs (CMG, CASF, cf. note du premier test).
- **Échantillon de 120 sur une population de 34 397** : les marges d'erreur ci-dessus (méthode de Wilson, IC95 %) restent de l'ordre de ±8-9 points pour les catégories majoritaires — une estimation solide pour une tendance, pas une mesure de précision.

## 7. Phrase de synthèse

> Sur un échantillon stratifié de 120 démarches, 15,8 % renvoient à un cadre directement exploitable et 36,7 % à un lien inutilisable (intervalle de confiance à 95 % : 28,6 %-45,6 % ; en comptant aussi les cadres absents ou non juridiques, 59,2 % des démarches n'offrent rien d'exploitable sans recherche complémentaire). Sur l'ensemble des 34 113 démarches publiées ou closes du corpus (hors démarches techniques de test), 23,4 % renvoient à une simple page d'accueil ou de recherche.
