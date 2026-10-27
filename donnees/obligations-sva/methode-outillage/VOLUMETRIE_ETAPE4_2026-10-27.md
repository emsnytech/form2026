# Étape 4 — Volumétrie (27/10/2026)

> **CORRECTION 3 (27/10/2026, contre-lecture à l'aveugle avant publication)** :
> voir section 0 ci-dessous. **Le chiffre qui fait foi est désormais 155
> vérifiés** (104 DN, 46 Cerfa, 5 téléservice ; 82 SVA, 56 SVR, 17 délai SVA),
> pas 165. Les montants de volumétrie de ce document (§1) ont été recalculés
> sur cette base. Chaîne complète des corrections tracée : 211 → 203 → 165 →
> **155**.

**Base retenue : 155 procédures vérifiées** (104 DN, 46 Cerfa, 5 téléservice),
**+ 8 lignes de l'échantillon étape 5** marquées « outillée » par vos
recherches web. Rien commité séparément de ce qui a déjà été validé (fichiers
locaux complémentaires dans `cartographie/outillage-etape3/`).

## 0. Contre-lecture à l'aveugle avant publication (51 liens)

Tirage de 40 liens au hasard parmi les 165 vérifiés (avant correction 3),
relus sans voir les motifs précédents, + les 11 lignes du décret 2014-1282
au signal faible (pas 8 exactement : 9 relèvent de la famille « autorisation
d'occupation temporaire (AOT) », 2 d'une famille différente « carte de
collectionneur d'armes », tranchées dans la même passe).

**Précision obtenue : 41/51 = 80,4 %.**
- Échantillon de 40 : 35/40 = **87,5 %**.
- Les 11 lignes 2014-1282 : **6/11 corrects**. Ligne de partage claire : les
  intitulés qui disent eux-mêmes « autorisation d'occupation **temporaire** »
  correspondent bien à la démarche AOT générique (6 lignes, confirmées) ;
  ceux qui emploient un régime différent — « **concession** », « titre
  constitutif de **droits réels** », « **carte de collectionneur** » — ne
  correspondent pas (5 lignes, rejetées) : la démarche AOT ne couvre que
  l'autorisation temporaire simple, pas les régimes plus lourds/distincts.

**10 lignes rebasculées en rejeté** (5 de l'échantillon de 40 + 5 des
2014-1282) :
- Retrait d'une dérogation confondu avec l'avis préalable des communes (étape
  différente du même dossier).
- Laboratoires de biologie médicale : démarche régionale trop générique.
- Agrément d'association environnementale confondu avec un dispositif de
  soutien/financement (acte différent).
- Agrément de centre de formation confondu avec une session d'examen
  générique.
- **Nouveau faux ami** : démarche DN « autorisation d'exercer la profession
  d'**architecte** sans inscription au tableau » utilisée à tort pour une
  ligne SVR concernant les **experts-comptables** — mauvaise profession.
- 3 lignes « domaine public » à régime distinct de l'AOT (concession, droits
  réels), 2 lignes armes confondues avec une carte de collectionneur.

Détail ligne à ligne : `cartographie/outillage-etape3/contre_lecture_51_jugement.csv`.
Fichier verdicts final : `candidats_canal_verifie_CORRIGE2_2026-10-27.csv`.

## 1. DN — cumul vs flux annuel

`nb_dossiers` est confirmé **cumulatif depuis la publication de la démarche**
(pas de champ par année dans l'export ; vérifié sur plusieurs exemples, aucun
export 2024 isolé disponible). Deux colonnes distinctes, jamais mélangées :
- `nb_dossiers_cumule` : total depuis la création.
- `nb_dossiers_annualise_estime` : cumul ÷ nombre d'années depuis
  `date_publication` (méthode indiquée par défaut, pas une vraie mesure 2024).

**104 lignes DN** (après correction 3) : cumul total **115 151** dossiers,
annualisé estimé total **≈ 50 306/an**. Détail ligne à ligne :
`cartographie/outillage-etape3/volumetrie_DN_finale_CORRIGE_2026-10-27.csv`.

### Réexamen des 103 lignes « meilleur score par défaut »

Relu une par une pour sommer les vraies déclinaisons régionales/locales
(ex. agrément ISFT national + régional, inscriptions aux examens par
préfecture, dérogations de circulation par département) :
- **65 confirmées**, dont 45 avec un volume augmenté par la somme de
  plusieurs variantes légitimes (ex. agrément des centres de formation à la
  conduite : 3 variantes sommées).
- **38 rebasculées en rejeté** (candidat finalement incorrect, pas seulement
  une ambiguïté de volume) :
  - **20** : faux ami « carte professionnelle UE/EEE (ambulancier) »,
    accepté à tort sur ~20 autres professions de santé du décret 2014-1286
    (conseiller génétique, préparateur en pharmacie, infirmier, masseur-
    kinésithérapeute, orthophoniste, orthoptiste, audioprothésiste, aide-
    soignant, psychothérapeute...).
  - **6** : cartes de combattant/déporté/interné/réfractaire (décret
    2014-1284), contaminées par un candidat « carte professionnelle d'agent
    immobilier » sans rapport.
  - **12** : matches hors sujet divers (immatriculation SIV confondue avec
    autorisation de circulation ; formation continue générique sans rapport
    avec l'architecture ; etc.), détaillés dans
    `cartographie/outillage-etape3/dn_103_reexamen.csv`.

**Point laissé ouvert, non tranché** : 8 lignes du décret 2014-1282 (domaine
public maritime/fluvial) restent vérifiées avec un **signal faible** — les
mêmes démarches AOT génériques (121850, 99744) reviennent sur plusieurs lignes
du même décret ; un seul candidat retenu par ligne pour éviter un double
compte, mais la correspondance précise au régime exact n'est pas confirmée.

## 2. Cerfa / téléservice — « téléchargements_2024 »

Colonne renommée (ce n'est pas un volume de dossiers, seulement un nombre de
téléchargements de formulaire sur service-public.fr, 1ère valeur de l'export,
« 2024 à confirmer »). **7 des 51 lignes Cerfa/téléservice** (46+5) sont
marquées **« partagé, non attribuable »** (le Cerfa est associé à ≥ 2 fiches
service-public distinctes dans `volumetrie DILA.tab.csv` — signal de
généricité). **12 restent `inconnu`** : 5 téléservices (ce fichier ne mesure
que les téléchargements de formulaire, pas les téléservices — limite
structurelle, pas un échec de jointure) + 7 Cerfa non retrouvés dans le
fichier de volumétrie. Détail :
`cartographie/outillage-etape3/volumetrie_Cerfa_tele_finale_2026-10-27.csv`.

## 3. Les 8 lignes « outillée » de l'échantillon étape 5

| id | canal | téléchargements/dossiers | note |
|---|---|---|---|
| 623 SVA | DILA (fiche F1277) | 214 | sous-cas spécifique choisi parmi 6 procédures liées à la même fiche |
| 2014-1273 SVR | DILA (Cerfa 13406) | 207 034 | **non isolable**, volume du Cerfa permis de construire global |
| 977 SVA | DILA (R17084) | 9 167 | correspondance directe |
| 143 SVA | DN (84232) | 5 727 | cumul ; « Agrément 2026 des experts automobiles » — à confirmer que c'est la même procédure que l'inscription temporaire |
| 2014-1286 SVR | DN (6 démarches régionales) | 4 344 | cumul, non exhaustif (régions manquantes) |
| 2014-1299 SVR | DILA (Cerfa 13405) | 24 666 | **non isolable**, volume du Cerfa permis de démolir global |
| 65 SVA | DILA (Cerfa 13406) | 207 034 | **non isolable**, même Cerfa que 2014-1273, cause différente |
| 2014-1286 (ostéopathie) SVR | confidentielle | ~30 établissements | **stock documenté**, pas un flux annuel — seule ligne confidentielle de l'échantillon avec un ordre de grandeur chiffré (les 15 autres : `inconnu`) |

## 4. Nouvelle mesure — les 50 formulaires les plus téléchargés de `volumetrie DILA.tab.csv`

**1 seule correspondance automatique sur 50** avec une ligne SVA/SVR/délai :
rang 10, « Demande d'acquisition de la nationalité française par
naturalisation » (401 230 téléchargements, Cerfa 12753) ↔ SVR 2014-1292
« Attestation constatant l'existence d'un décret de naturalisation ».

**Vérifié à la main : match confirmé incorrect.** La ligne SVR 2014-1292 a
pour base légale l'article 52 du décret n° 93-1362 du 30 décembre 1993, qui
régit spécifiquement la délivrance d'une **attestation après qu'un décret de
naturalisation a déjà été signé** (étape administrative distincte, souvent
utile avant la publication du décret au JORF). Le Cerfa 12753 sert la
**demande initiale** de naturalisation, régie par d'autres articles du même
décret (procédure de dépôt du dossier, en amont). Ce sont deux étapes
différentes de la même procédure globale, pas la même démarche — cette ligne
était d'ailleurs déjà classée `rejete` dans les 155 vérifiées, donc cette
vérification manuelle confirme (et ne change pas) le résultat déjà retenu.

Les 49 autres relèvent de catégories structurellement étrangères au silence-
vaut-accord/rejet (pas de décision implicite sur demande d'autorisation) :
déclarations/notifications (perte de pièce d'identité, accident du travail,
dons...), demandes de prestation financière/sociale (RSA, logement social,
aide juridictionnelle...), démarches électorales/citoyennes, formalités
d'identité/véhicule de masse, actes d'état civil/justice civile, formalités
sanitaires ponctuelles, et Cerfa d'urbanisme partagés (permis de construire/
démolir, déjà vus en §3 comme non attribuables). Détail catégorie par
catégorie : `cartographie/outillage-etape3/top50_dila_vs_corpus.csv`.

## 4 bis. Part du corpus SVA/SVR/délai dans le total des téléchargements DILA

- Total téléchargements, tous les 1 938 enregistrements de `volumetrie DILA.tab.csv` : **24 953 755**.
- Somme des téléchargements 2024 des 32 Cerfa/téléservices **liés et non
  partagés** (procédures vérifiées + échantillon étape 5) : **36 431**.
- **Part du corpus dans le total DILA : 0,146 %.**
- Pour mémoire, les Cerfa **partagés** (non attribuables) représentent
  71 793 téléchargements supplémentaires, non comptés ici car non spécifiques
  à une procédure du corpus.

Lecture : les procédures SVA/SVR/délai réellement outillées et mesurables
via les téléchargements de formulaire pèsent très peu dans le volume total
de téléchargements DILA — cohérent avec le constat du §4 (les plus gros
volumes sont des démarches de masse étrangères au silence-vaut-accord/rejet).

## 4 ter. Distribution des volumes des seules procédures outillées (corpus)

Deux métriques distinctes, non comparables entre elles (téléchargements de
formulaire vs dossiers DN) — présentées séparément :

**Cerfa/téléservice liés, non partagés (32 valeurs) :**

| Classe | n |
|---|---|
| < 100 | 5 |
| 100 – 1 000 | 25 |
| 1 000 – 10 000 | 1 |
| > 10 000 | 1 |

**DN, cumul depuis publication (104 valeurs) :**

| Classe | n |
|---|---|
| < 100 | 65 |
| 100 – 1 000 | 30 |
| 1 000 – 10 000 | 17 |
| > 10 000 | 2 |

Lecture : à l'inverse de la distribution générale DILA (§5, 15 % au-dessus de
10 000), les procédures du corpus sont massivement de **petit volume** (63 %
des Cerfa liés et 57 % des DN cumulés sont sous 1 000) — cohérent avec des
régimes d'autorisation/agrément ciblés, pas des démarches de masse.

## 5. Distribution des volumes (tous les 1 938 enregistrements de `volumetrie DILA.tab.csv`)

| Classe | n | % |
|---|---|---|
| < 100 | 516 | 28,1 % |
| 100 – 1 000 | 605 | 32,9 % |
| 1 000 – 10 000 | 435 | 23,7 % |
| > 10 000 | 283 | 15,4 % |

(1 839/1 938 enregistrements ont une valeur numérique exploitable.)

### Top 10 (tous formulaires DILA, pas seulement le corpus SVA/SVR)

| Rang | Téléchargements | Cerfa | Titre |
|---|---|---|---|
| 1 | 3 753 879 | — | Certificat de cession d'un véhicule d'occasion |
| 2 | 789 265 | 12669 | Demande d'inscription sur les listes électorales |
| 3 | 729 308 | — | Déclaration de perte de carte d'identité ou de passeport |
| 4 | 667 027 | — | Demande de certificat d'immatriculation d'un véhicule |
| 5 | 636 783 | — | Autorisation de sortie de territoire (AST) |
| 6 | 509 363 | 14069 | Demande de logement social |
| 7 | 502 280 | — | Permis de conduire - Avis médical |
| 8 | 493 837 | 15692 | Demande ou renouvellement de prestations MDPH |
| 9 | 493 537 | 11527 | Modèle d'attestation de témoin |
| 10 | 401 230 | 12753 | Demande d'acquisition de la nationalité française par naturalisation |

Aucun de ces 10 n'est une procédure SVA/SVR/délai : les plus gros volumes
DILA sont des démarches de masse, déclaratives ou de prestation — pas des
autorisations soumises à un régime de décision implicite.

## Jeux Éducation/ESR — toujours en attente de validation

Non rattachés. Rappel : 1 seul lien plausible (et approximatif) trouvé parmi
les 165 vérifiées (SVA 289, bac — voir message précédent) ; aucun calcul
effectué.

Rien commité.
