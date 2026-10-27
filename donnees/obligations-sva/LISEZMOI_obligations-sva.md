# Procédures prévues par les textes — données dérivées

Production de l'auteur à partir de données ouvertes de data.gouv.fr (liste « silence
vaut accord » 2016), de décrets consolidés Légifrance (39 décrets d'exception
d'octobre 2014), de la base LEGI de la DILA (échanges.dila.gouv.fr/OPENDATA/LEGI/,
archive datée du 13/07/2025), du référentiel DILA service-public.fr (fiches,
formulaires, téléservices) et du corpus FORM 2026 (Démarche Numérique). Voir
`donnees/LICENCE.md`.

Version du 28/10/2026 : remplace le périmètre SVA seule du 26/10/2026 (voir en bas
de cette note).

## Fichiers (28/10/2026)

### `obligations_sva_2026-10-26.csv` (1 283), `obligations_svr_2026-10-28.csv` (1 174), `delais_sva_derogatoires_2026-10-28.csv` (349)

Les trois référentiels de base : la liste officielle « silence vaut accord » (SVA,
reconstituée depuis le XML du 08/12/2016, périmètre État et établissements publics),
et les deux référentiels « silence vaut rejet »/délai dérogatoire reconstitués depuis
les 39 décrets d'exception d'octobre 2014 (versions consolidées Légifrance au moment
de la lecture, 2026). Colonnes propres à chaque source — voir l'en-tête de chaque
fichier.

### `statut_vigueur_2026-10-28.csv` (2 806 lignes, les trois listes)

Pour chaque ligne : `statut` (`en_vigueur` / `transfere` / `recodifie` / `supprime` /
`numero_non_localise` / `inconnu` / `hors_UE`), l'article ou la référence, l'identifiant
LEGIARTI de l'archive LEGI (datée du 13/07/2025), et le code d'arrivée quand le statut
est `recodifie`. **`numero_non_localise`, `inconnu` et `hors_UE` ne sont ni des
vivantes ni des éteintes** : l'article n'a simplement pas pu être vérifié par cette
méthode (texte non codifié non identifiable, numéro introuvable dans l'archive, ou
texte de l'Union européenne hors périmètre) — à présenter séparément, jamais ajoutées
à l'un ou l'autre total.

### `decrets_articles_supprimes_ou_recodifies_2026-10-28.csv` (376 lignes)

Parmi les lignes SVR/délai dont l'article de référence est abrogé : lesquelles
renvoient à un article recodifié (152 — le décret consolidé n'a pas été mis à jour
après une recodification, le droit existe probablement toujours sous un autre
support) et lesquelles à un article réellement supprimé (224 — aucun signal de
recodification trouvé dans l'archive LEGI).

### `liens_outillage_verifies_2026-10-28.csv` (155 lignes)

Les seules procédures comptées comme outillées : relues individuellement à deux
reprises (relecture complète des 504 candidats trouvés par rapprochement automatique,
puis contre-lecture à l'aveugle d'un échantillon de 51 liens sans voir les motifs
précédents). Colonnes : liste, identifiant, intitulé/objet, canal (démarche numérique /
Cerfa / téléservice), identifiant de la démarche ou du formulaire, type de demandeur,
régime, méthode.

### `liens_outillage_candidats_non_verifies_2026-10-28.csv` (349 lignes)

Tout ce que le rapprochement automatique par titre a produit mais qui s'est révélé
faux ou indéterminé à la relecture individuelle. Exportées à part, **jamais comptées**
dans un indicateur. Le rapprochement automatique se trompe environ une fois sur deux.

### `echantillon_web_50_2026-10-28.csv`

50 lignes vivantes sans aucun candidat automatique, tirées au hasard (stratifiées
SVA/SVR/délai au prorata) et recherchées une à une sur le web (résultats fournis par
l'auteur, pas par l'IA). Répartition : 7 manquées par le rapprochement automatique,
16 outillées hors des bases DN/DILA (formulaires préfectoraux locaux, régulateurs,
ordres professionnels), 16 confidentielles (quelques bénéficiaires, pas de démarche
publique), 4 par courrier libre, 4 obsolètes de fait, 2 hors usager, 1 non trouvée —
intervalles de confiance à 95 % larges (n=50), à lire en ordres de grandeur.

### `volumetrie_2026-10-28.csv` (155 lignes)

Pour chaque procédure outillée vérifiée : `dossiers_cumule` et
`dossiers_annualise_estime` (démarches numériques — deux colonnes toujours séparées,
la seconde est une estimation par division, pas une mesure 2024) ou
`telechargements_2024` (Cerfa/téléservice, 1ère valeur de l'export DILA, année « 2024 à
confirmer ») avec la mention `partage_non_attribuable` quand un Cerfa est utilisé par
plusieurs procédures distinctes (le volume ne peut alors être attribué à aucune en
particulier). Un téléchargement de formulaire n'est pas un dossier déposé.

### `top50_regime_juridique_2026-10-28.csv`

Les 50 formulaires les plus téléchargés de la base DILA (tous usages, pas seulement
ce corpus), classés par régime juridique avec le texte de rattachement. Montre que
les démarches de masse (cession de véhicule, état civil, prestations…) relèvent de
régimes différents du silence vaut accord/rejet, pas d'un oubli de liste.

### `contradictions_apparentes_2026-10-28.csv` (5 cas)

Les 5 cas où un décret « silence vaut rejet » et la liste SVA (ou un décret de délai)
classent apparemment la même procédure dans des sens opposés : trois familles
« transfert de portefeuilles » (mutuelles, prévoyance, assurance — décret 2014-1280)
et deux « transport de matières nucléaires » (décrets 2014-1273 et 2014-1285). Les
cinq figurent dans le texte d'origine des décrets de 2014, donc pas un ajout récent —
**à faire confirmer par un juriste**. La recherche systématique de toute autre
contradiction au-delà de ces 5 cas n'a pas été menée à son terme.

### `NOTE_RESULTATS_2026-10-28.md`

Entonnoir complet, fourchette publiable, volumétrie détaillée, classement par régime
juridique, limites.

## Fichiers superseded (conservés sur disque, non indexés ni liés depuis la page)

`verdicts_504_2026-10-27.csv` (dans `methode-outillage/etape3/`, relecture initiale
avant correction), `liens_dila_*_2026-10-26.csv`, `liens_dn_*_2026-10-26.csv`,
`liens_obligations_dila_2026-10-26.csv`, `liens_obligations_dn_2026-10-26.csv`,
`obligations_sva_avec_statut_2026-10-26.csv`, `NOTE_RESULTATS_2026-10-26.md` :
périmètre SVA seule, rapprochement DN seul, antérieurs à la correction en trois temps
(211 → 203 → 165 → 155 vérifiés). Conservés pour la reproductibilité, remplacés par
les fichiers ci-dessus.

## Méthode (résumé)

- Vigueur : archive LEGI de la DILA (13/07/2025) téléchargée et indexée localement ;
  statut déterminé sur toutes les versions connues d'un article (en vigueur si une
  version porte l'état VIGUEUR/VIGUEUR_DIFF, transféré si la dernière version est
  TRANSFERE avec un lien de concordance, abrogé sinon) ; recodification identifiée en
  lisant le texte abrogeant (titre contenant « partie législative/réglementaire d'un
  code » ou acte de codification connu).
- Outillage : rapprochement par titre (chevauchement de mots, seuil de score) vers les
  démarches numériques puis les formulaires/téléservices DILA, référence juridique
  utilisée seulement comme indice, jamais seule preuve ; liste noire de faux amis
  tenue à jour (carte professionnelle UE/EEE hors ambulancier, CPAM mise à jour
  administrative, École nationale des greffes, démarche architecte pour une
  procédure experts-comptables…). Deux relectures indépendantes (504 candidats, puis
  contre-lecture à l'aveugle de 51 liens) : vérifié ≠ candidat, toujours distingués.
- Volumétrie : dossiers mesurés (démarches numériques) ou téléchargements de
  formulaire approximés (DILA), jamais confondus ; cumul et taux annualisé estimé
  toujours séparés.

## Ce qui se recalcule automatiquement, ce qui exige une relecture manuelle

**Se recalcule automatiquement, sans relecture, si une source change** :
téléchargement et indexation de l'archive LEGI ; statut en_vigueur/transfere/
abroge par article (règle fixe sur les versions connues) ; rapprochement par
titre vers DN/Cerfa/téléservice (production de *candidats*, jamais de
vérifiés) ; volumétrie (jointure directe par identifiant).

**Exige une relecture manuelle à chaque régénération** : la classification
recodifié/supprimé (lecture du titre du texte abrogeant, heuristique de
mots-clés qui peut rater un titre atypique) ; le statut vérifié/rejeté de
chaque candidat d'outillage (le rapprochement par titre seul se trompe
environ une fois sur deux) ; la liste noire de faux amis (à enrichir à
chaque nouvelle relecture, jamais complète) ; les contradictions apparentes
(lecture du texte d'origine) ; l'échantillon web (recherche humaine,
non automatisable).

Le skill de mise à jour mensuelle `maj-demarches-form2026` n'a pas pu être
localisé depuis cette session pour y reporter cette distinction directement
dans sa documentation — à faire manuellement si ce skill existe ailleurs
dans l'environnement de l'auteur.

## Limites

Voir `NOTE_RESULTATS_2026-10-28.md`. Points clés : rapprochement par titre sans clé
commune, se trompe environ une fois sur deux avant relecture ; liste SVA non mise à
jour depuis 2016 ; archive LEGI datée du 13/07/2025 (tout changement de vigueur
postérieur non vu) ; volumétrie DILA 2024 à confirmer ; recherche systématique des
contradictions non menée à son terme au-delà des 5 cas confirmés ; un seul relecteur
humain final, deux passes de relecture indépendantes mais pas davantage.

## Date et version

Vigueur et recodification : archive LEGI du 13/07/2025. Décrets consolidés Légifrance :
lus en 2026. Liste SVA : XML du 08/12/2016 (jamais mise à jour depuis). Référentiel
DILA (fiches/formulaires/téléservices) : export du 12-13/09/2026. Corpus Démarche
Numérique : daté au plus tard du 02/10/2026. Volumétrie DILA : export du 20/09/2026,
téléchargements « 2024 à confirmer ».

---

**Version précédente (26/10/2026)** : périmètre SVA seule (1 283 obligations),
rapprochement Démarche Numérique seul, 15 fiches/7 obligations-avec-démarche relues,
331 dossiers cumulés. Remplacée par la version ci-dessus (SVA + SVR + délai, 2 806
procédures, 155 vérifiées).
