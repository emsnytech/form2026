# Obligations « silence vaut accord » — données dérivées

Production de l'auteur à partir de données ouvertes de data.gouv.fr (liste des
procédures « silence vaut accord ») et du référentiel DILA / FORM 2026
(fiches service-public.fr, démarches Démarche Numérique). Voir `donnees/LICENCE.md`.

## Fichiers

### `obligations_sva_AAAA-MM-JJ.csv`

Référentiel propre des 1 283 obligations SVA, périmètre « État et ses établissements
publics », reconstitué depuis le XML officiel (08/12/2016) avec repli sur
`obligations.csv` pour le Cerfa éventuel.

**Colonnes** : `numdispo` (identifiant stable, officiel), `intitule`, `reference`
(article normalisé), `texte_source`, `autorite_competente`, `delai`, `ministere`,
`type` (constant « habilitation » dans cette source), `cerfa_eventuel`,
`date_maj_source` (2016-12-08, constant — la source n'a jamais été remise à jour).

### `liens_obligations_dila_AAAA-MM-JJ.csv`

Lien obligation → fiche DILA. **Colonnes** : `numdispo`, `fiche_id`, `fiche_titre`,
`methode` (reference | titre+autorite), `confiance` (forte | moyenne — la confiance
faible n'est jamais publiée), `date`.

### `liens_obligations_dn_AAAA-MM-JJ.csv`

Lien obligation → démarche(s) Démarche Numérique, correspondance 1 → n (une
obligation nationale peut avoir plusieurs déclinaisons locales, ou aucune).
**Colonnes** : `numdispo`, `demarche`, `demarche_titre`, `organisme`, `etat`,
`nb_dossiers`, `score_titre`, `cerfa_concorde`, `cadre_declare_demarche` (extrait du
cadre juridique déclaré par la démarche, étude FORM 2026 distincte),
`cadre_est_texte_procedure_generique` (vrai si le seul cadre cité est l'ordonnance
générique 2014-1330 — ne prouve rien).

### `obligations_sva_avec_statut_AAAA-MM-JJ.csv`

Le référentiel (étape 1) fusionné avec le statut de chaque obligation : colonnes
`statut_fiche_dila` et `statut_demarche_dn` (`verifie` | `candidat_non_verifie` | `aucun`)
et `cadre_demarche_est_ordonnance_generique_2014_1330` (vrai si le seul cadre juridique
cité par une démarche candidate est l'ordonnance générique 2014-1330 — ne prouve rien).

### `liens_dila_verifies_AAAA-MM-JJ.csv` / `liens_dn_verifies_AAAA-MM-JJ.csv`

Les seuls liens comptés dans les indicateurs de la page : relus individuellement sur
les deux échantillons (56 obligations, puis 50 liens produits), pas seulement scorés.

### `liens_dila_candidats_non_verifies_AAAA-MM-JJ.csv` / `liens_dn_candidats_non_verifies_AAAA-MM-JJ.csv`

Tout ce que le rapprochement automatique (`liens_obligations_dila_*`,
`liens_obligations_dn_*`) a produit mais qui n'a pas été relu individuellement.
Exportés à part, jamais comptés dans un indicateur.

### `NOTE_RESULTATS_AAAA-MM-JJ.md`

Taux par maillon, précision mesurée à la main, exemples retenus, limites.

## Méthode (résumé)

- Dédoublonnage du XML officiel (1 doublon exact retiré, 1 284 → 1 283).
- Lien obligation → fiche DILA : (a) référence juridique concordante (nom du texte +
  numéro d'article dans le texte de la fiche) → confiance forte ; (b) titre proche
  (chevauchement de mots-clés ≥ 40 %) ET autorité cohérente → confiance moyenne. Liste
  noire de fiches génériques écartée au préalable (MonIdenum et équivalents, qui
  remontent sur des obligations sans rapport).
- Lien obligation → démarche DN : rapprochement direct sur le titre (le Cerfa n'est pas
  un passage obligé — la plupart des démarches nées sur Démarche Numérique n'en ont
  jamais eu), avec Cerfa et cadre juridique déclaré comme signaux de corroboration
  quand ils existent. Exclusions explicites des faux amis déjà repérés (confusion
  durée minimale/maximale de travail, seuils d'âge différents, « agrément d'organisme »
  générique qui matchait en fait des stages de sécurité routière).

## Validation

Échantillon raisonné de 56 obligations (35 témoins Cerfa + complément par ministère et
délai), puis nouvel échantillon de 50 liens produits relu à la main. Précision mesurée :
~28 % (fiche DILA), ~36 % (démarche DN) — très en dessous du seuil de décision fixé à
l'avance (60 %). **Les volumes bruts du pipeline (74 fiches, 234 démarches) sont une
borne supérieure, pas un résultat validé** : la page et les indicateurs ne comptent que
les 15 fiches et 12 obligations-avec-démarche effectivement relues (`*_verifies_*.csv`).

## Limites

Voir `NOTE_RESULTATS_AAAA-MM-JJ.md`. Points clés : rapprochement textuel sans clé
commune ; absence de lien ≠ absence de dématérialisation (téléservices hors Démarche
Numérique non couverts) ; source SVA non mise à jour depuis 2016 ; un seul relecteur,
pas de requalification à l'aveugle.

## Date et version

Pipeline exécuté le 26/10/2026, sur le corpus FORM 2026 du 21/10/2026 (35 864
démarches) et les 8 509 fiches DILA de `cartographie/dila/`.
