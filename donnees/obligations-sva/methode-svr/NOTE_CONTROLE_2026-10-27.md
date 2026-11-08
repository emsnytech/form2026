# Référentiel SVR — note de contrôle (27/10/2026)

**Rien n'est publié. Fichiers dans `cartographie/svr/out/`, à valider avant toute
intégration à la page FORM 2026.**

## Périmètre

39 feuilles traitées (sur 41 — 1302 et 1268 exclus, confirmé) :
- **1302** : décret modificatif (« modifiant le code de la construction et de l'habitation
  et le décret n° 2011-873... »), pas un décret d'exceptions — hors sujet, confirmé par
  lecture du titre.
- **1268** : vrai décret d'exceptions (même intitulé type que les autres), mais abrogé
  par le décret n° 2023-779 selon l'information fournie — non vérifié indépendamment,
  pris tel quel.

Cas particuliers traités comme demandé :
- **1265** : transversal, sans annexe — gardé en contexte, 0 procédure.
- **1263** : sans annexe — 1 procédure saisie à la main (« Délivrance d'une licence de
  réutilisation des informations publiques conforme à une licence type », CRPA art.
  L. 323-1 et L. 323-2, délai 1 mois, nature délai SVA), signalée `statut=saisie manuelle`.

## Nature : comment elle a été tranchée

Pas seulement sur l'intitulé du décret (plusieurs titres mentionnent les deux fondements
à la fois — ex. 1266, 1294) : **sur le texte de l'article 1 du décret lui-même**, qui dit
soit « *…vaut décision de rejet…* » (SVR) soit « *…vaut décision d'acceptation…* » (délai
SVA). Vérifié sur 1294 : l'article 1 fixe le rejet, l'article 2 ne fait que moduler le
délai de CE rejet pour certaines procédures de la même annexe — ce n'est jamais une
deuxième liste de nature différente dans un même décret. Confirmé sur les 39 feuilles :
chacune a une nature unique, jamais mixte.

## Résultats

| | Lignes brutes | Après dédoublonnage |
|---|---|---|
| SVR (silence vaut rejet) | 1 178 | **1 174** |
| délai SVA (silence vaut toujours accord, délai différent) | 350 | **349** |
| **Total** | 1 528 | **1 523** |

**Comparaison avec les 1 686 exceptions de 2014** : écart de 163 (1 523 vs 1 686).
Explications plausibles, non quantifiées individuellement : versions **consolidées**
Légifrance (des procédures ont pu être retirées des annexes par des décrets modificatifs
ultérieurs — ex. 2014-1266 « modifié par décret n° 2024-430 », 2014-1294 « modifié par
décret n° 2024-615 » : ces modifications datées et visibles dans chaque feuille montrent
que le contenu a bougé depuis 2014) ; 1268 écarté (abrogé) ; le chiffre de 1 686 lui-même
vient d'un commentaire secondaire (Lexbase), pas d'un comptage direct des annexes
d'origine — à confirmer si besoin sur les textes 2014 non consolidés.

## Dédoublonnage — correction de l'estimation initiale

**L'estimation « ~22 lignes identiques objet + dispositions » ne tient pas à la
vérification.** Avec cette clé (objet + dispositions seuls), 22 lignes groupent bien —
mais l'examen direct montre que la plupart sont des procédures **réellement distinctes**
qui partagent un même numéro d'article par coïncidence de rédaction. Exemple concret
(2014-1277) : « Transformation d'une société non titulaire d'office... » + « Article
134-1 » apparaît trois fois, mais chaque fois pour un **texte de référence différent**
(décret notaires, décret commissaires-priseurs judiciaires, décret huissiers de justice)
— trois professions, trois décrets distincts, même numérotation d'article par hasard de
rédaction parallèle. Dédoublonner sur objet+dispositions seuls aurait supprimé à tort
2 lignes sur 3 dans ce cas.

Avec la clé correcte (**décret + texte de référence + objet + dispositions**, tous
identiques) : **5 doublons exacts réels** retirés (4 en SVR, 1 en délai SVA) — fichier
`doublons_retires_2026-10-27.csv`, avec la ligne d'origine tracée. Exemple de vrai
doublon : 2015-1458, « Inscription au tableau de l'ordre » / Article 17 / 3 mois,
répété 4 fois à l'identique (chacune suivie d'une ligne de sous-cas différente, elle,
bien distincte et conservée).

## Relecture de 30 lignes tirées au hasard (24 SVR + 6 délai SVA)

Échantillon dans `echantillon30.json`. 6 relues en détail contre le classeur source
(objet, décret, lignes voisines) : **les 6 correctes**, y compris un cas structurellement
intéressant (2015-1458, lignes 122-125 : « Inscription au tableau de l'ordre » générique
répété, chacun suivi d'un sous-cas « (procédure art. 99 / … UE) » et « (procédure art.
100 / … hors UE) » distincts — confirme à la fois le parsing des sous-cas et le doublon
du cas générique signalé ci-dessus).

## Rapprochement avec la liste SVA (même décret/texte de référence + même article)

**53 procédures SVR candidates au rapprochement avec `obligations_sva`**, repérées par
code/texte + numéro d'article en commun — **non vérifiées une à une**, à ne pas publier
comme un résultat tel quel (même limite que sur les niveaux 2/3 précédents : un
rapprochement automatique sur la référence seule produit des faux positifs). Avant
publication, ce repérage devrait être relu à la main comme le reste.

## Fichiers produits

- `obligations_svr_2026-10-27.csv` (1 174 lignes)
- `delais_sva_derogatoires_2026-10-27.csv` (349 lignes)
- `doublons_retires_2026-10-27.csv` (5 lignes, trace des doublons supprimés)
- `anomalies_parsing_2026-10-27.csv` (21 lignes : rattachements de dispositions
  multi-lignes documentés, pas des erreurs)
- `lignes_par_decret_2026-10-27.csv` (comptage par feuille)
- `echantillon30.json` (échantillon de contrôle)

## Ce qui reste à faire avant toute publication

1. Valider ou corriger l'écart des 163 lignes avec 1 686 (vérifier au moins un décret
   contre sa version 2014 d'origine, non consolidée, si vous y tenez).
2. Relire les 53 candidats de rapprochement SVA/SVR un par un.
3. Décider du sort des décrets 2015 autres que 1458 (aucun autre signalé pour l'instant).
4. Seulement ensuite : restitution sur la page FORM 2026 (tableau « stock des
  obligations de l'État » en trois parts), mise à jour LISEZMOI et note de résultats.
