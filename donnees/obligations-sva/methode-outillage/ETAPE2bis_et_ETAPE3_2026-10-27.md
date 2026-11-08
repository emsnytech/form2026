# Étape 2 bis (recodifié vs supprimé) et Étape 3 (outillage par canal) — 27/10/2026

## Étape 2 bis — recodifié ou supprimé

Pour chaque article « abrogé » (code ou texte), lecture du lien vers le texte
abrogeant trouvé dans la **dernière version** de l'article dans l'archive LEGI
(attribut `typelien="ABROGE"`), puis recherche du titre complet de ce texte
abrogeant dans l'index LEGI (codes + TNC). Classification :
- **recodifié** si le titre du texte abrogeant contient « partie législative
  d'un code » ou « partie réglementaire d'un code », une mention explicite de
  création/codification, ou correspond à un acte de (re)codification connu
  (commande publique 2018, CESEDA 2020, fonction publique 2021, pénitentiaire
  2022, CRPA 2015) — code d'arrivée donné quand il est identifiable dans le
  titre.
- **supprimé** sinon (acte abrogeant identifié mais sans signal de
  recodification, ou aucun lien `ABROGE` trouvé dans la dernière version).

**Bug corrigé en cours de route** : les articles réglementaires « R* » du code
de l'urbanisme et du code de la construction et de l'habitation changent de
représentation (avec ou sans étoile) au moment de leur abrogation — la version
historique est indexée sous « R*111-16 », la version terminale sous
« R111-16 » (sans étoile). La première passe de croisement ne fusionnait pas
les deux séries et ratait donc la version terminale réelle pour ces deux
codes. Corrigé : les deux représentations sont désormais fusionnées avant de
déterminer la dernière version. Cela a changé une partie des statuts
en_vigueur/abrogé de l'étape 2 (recalculés, voir tableau ci-dessous).

### Tableau par liste (recalculé)

| | SVA (1283) | SVR (1174) | délai SVA (349) | Total (2806) |
|---|---|---|---|---|
| En vigueur | 868 | 668 | 230 | 1 766 |
| Transféré | 6 | 3 | 0 | 9 |
| **Recodifié** | **99** | **128** | **24** | **251** |
| Supprimé | 178 | 180 | 44 | 402 |
| Numéro non localisé | 98 | 35 | 45 | 178 |
| Inconnu (forme non identifiable / non trouvé) | 33 | 95 | 6 | 134 |
| Hors UE | 1 | 65 | 0 | 66 |

**Vivant (périmètre étape 3) = en vigueur + transféré + recodifié = 1 766 + 9 +
251 = 2 026 / 2 806 (72 %).**

Codes d'arrivée les plus fréquents parmi les 251 lignes recodifiées : **Code du
travail (étendu à Mayotte)** 38 lignes (ordonnance n° 2017-1491 du 25/10/2017),
**CESEDA** (recodification 2020) 34 lignes, **Code pénitentiaire** (ordonnance
n° 2022-478 du 30/03/2022) 33 lignes, Code des pensions militaires d'invalidité
(13), Code de la sécurité intérieure (10), Code des transports, Code rural et
de la pêche maritime, Code de l'urbanisme, Code de la construction et de
l'habitation (quelques lignes chacun — détail dans le fichier).

### Côté SVR et délai SVA : décret renvoyant à un article recodifié vs supprimé

**376 lignes** SVR/délai (sur les 318+58 « mixte » déjà repérées) ont un
article en statut abrogé/mixte-abrogé : **152 renvoient à un article
recodifié** (le décret consolidé 2026 n'a pas été mis à jour après la
recodification — le droit substantiel existe probablement toujours, sous un
autre support) et **224 renvoient à un article réellement supprimé** (aucun
signal de recodification trouvé). Détail complet, décret par décret, dans
`methode-svr/ETAPE2bis_svr_delai_recodifie_vs_supprime_2026-10-27.csv`
(remplace le fichier plus grossier de l'étape précédente,
`ETAPE2_svr_delai_article_disparu_2026-10-27.csv`, conservé pour mémoire).

**Limite assumée** : la classification repose sur le titre du texte abrogeant
et une liste de mots-clés / actes connus — elle peut manquer une
recodification au titre atypique (classée « supprimé » par défaut plutôt que
deviné un code d'arrivée). Le code d'arrivée donné est le titre brut trouvé
dans LEGI, pas une table de concordance article-à-article (non recherchée,
hors délai).

## Étape 3 — Outillage par canal (périmètre vivant, 2 021 lignes traitées)

Méthode : titre (chevauchement de mots, score ≥ 0,35, ≥ 3 mots communs) comme
signal principal, référence juridique **en indice seulement** (jamais seule),
liste noire des faux amis déjà connus (6 numdispo SVA du test niveau 2).
Candidats cherchés dans l'ordre DN puis Cerfa DILA puis téléservice DILA.
**Tout résultat de cette étape est un CANDIDAT, pas un lien vérifié.**

### Colonne type_demandeur

Classée sur l'intitulé/l'objet seul (pas sur l'autorité compétente, qui est
presque toujours un ministère/préfet et ne dit rien du demandeur — mélanger
les deux biaisait tout vers « autre_administration »). Résultat : **1 414
indéterminé (70 %)**, 242 entreprise, 151 profession réglementée, 138
particulier, 76 organisme, 0 collectivité/autre administration (mots-clés trop
spécifiques pour ces deux catégories, jamais déclenchés sur ce corpus — limite
assumée, pas un vrai zéro). La majorité des intitulés administratifs ne
nomment pas explicitement le type de demandeur : `indetermine` plutôt que
deviné.

### Candidats par canal

| Canal | Candidats |
|---|---|
| Aucun candidat | 1 517 (75 %) |
| Démarche Numérique (DN) | 400 (20 %) |
| Formulaire Cerfa (DILA) | 91 (4,5 %) |
| Téléservice (DILA) | 13 (0,6 %) |

### Contrôle : 50 liens relus à l'aveugle (30 DN, 15 Cerfa, 5 téléservice)

**Précision globale : 28/50 = 56 %.**

| Canal | Échantillon | Correct | Précision |
|---|---|---|---|
| DN | 30 | 13 | **43 %** |
| Cerfa | 15 | 11 | **73 %** |
| Téléservice | 5 | 4 | **80 %** |

**Lecture** : le rapprochement par titre seul vers les démarches DN est peu
fiable (moins d'un candidat sur deux est le bon) — confirme à plus grande
échelle ce qui était déjà observé niveau 2/3 (« le grain du droit n'est pas le
grain de la démarche »). Les canaux DILA (Cerfa, téléservice), dont les titres
sont rédigés procédure par procédure plutôt qu'en langage administratif
générique, sont nettement plus fiables.

**Deux nouveaux faux amis systématiques identifiés et retirés** (6 lignes
corrigées, candidats recalculés après retrait) :
- démarche DN 115132 « CPAM 71 : Mise à jour administrative (adresse) » —
  capte à tort les changements de registre INPI (marques, brevets) : aucun
  rapport, mots génériques partagés (« changement », « adresse »).
- démarche DN 150212 « École Nationale des Greffes — session » — capte à tort
  le retrait de la liste nationale des administrateurs judiciaires : aucun
  rapport (greffiers ≠ administrateurs judiciaires).

**Un troisième faux ami repéré mais non retiré, car partiellement vrai** :
démarches DN 153255/152933 « Formulaire carte professionnelle de transport
sanitaire (ambulancier) » — correctes pour les lignes qui concernent
réellement la profession d'ambulancier (confirmé 2 fois dans l'échantillon),
mais remontent aussi, à tort, sur d'autres professions paramédicales
(audioprothésiste, opticien-lunetier — confirmé 3 fois incorrect) qui partagent
la même formule administrative (« autorisation d'exercice accordée
individuellement aux ressortissants d'un État membre de l'UE »). Pas de règle
simple pour les distinguer automatiquement sans lire la profession visée :
laissé en candidat, signalé comme fragile plutôt que retiré en bloc (retirer
en bloc aurait aussi supprimé les 2 cas corrects).

**Limite assumée** : 50 liens relus sur 504 candidats trouvés (environ 10 %) ;
la précision par canal est une estimation sur cet échantillon, pas une mesure
exhaustive. Les 1 517 lignes « aucun candidat » n'ont pas été recherchées plus
loin (pas de faux négatif mesuré).

## Volumétrie (étape 4)

Non calculée, conformément à l'instruction. La sélection de jeux
Éducation/Enseignement supérieur du fork (`cartographie/volumetrie/jeux_retenus_shortlist_2026-10-27.csv`,
37 jeux) est conservée pour l'étape 4.

## Fichiers produits

- `obligations_sva_2026-10-26_legi_2026-10-27.csv`, `methode-svr/obligations_svr_2026-10-27_legi_2026-10-27.csv`,
  `methode-svr/delais_sva_derogatoires_2026-10-27_legi_2026-10-27.csv` : colonnes `recod_statut`,
  `recod_code_arrivee`, `recod_motif` ajoutées.
- `methode-svr/ETAPE2bis_svr_delai_recodifie_vs_supprime_2026-10-27.csv` : les 376 lignes SVR/délai
  abrogées, classées recodifié/supprimé.
- `methode-outillage/etape3/candidats_canal_2026-10-27.csv` : 2 021 lignes vivantes avec
  type_demandeur, régime, canal candidat, candidats détaillés — **tout en statut `candidat`**.
- `methode-outillage/etape3/echantillon_50_aveugle_2026-10-27.csv` et `echantillon_50_jugement.csv` :
  l'échantillon et son jugement ligne à ligne.
- Scripts : `legi_01_build_index.py` (v3, capture le lien abrogeant), `legi_03_build_tnc_index.py` (v2,
  idem pour les textes non codifiés), `legi_05_classify_recodification.py`,
  `etape3/01_classification_et_candidats.py`.

Rien publié. Commit sans push sur la branche `obligations-sva-canaux`.
