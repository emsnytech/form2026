# Obligations SVA — Partie 0, corrections préalables (27/10/2026)

Suite de `consignes_claude_code_sva_niveau2.md` / `consignes_claude_code_sva_niveau3.md`.
Travail de test, pas encore restitué sur la page — voir `obligations-sva-canaux` pour la
suite (niveaux 2/3/4). Ce dossier ne contient que le script corrigé de l'inventaire des
canaux (niveau 1) ; les sorties datées complètes seront publiées avec la restitution.

## 1. Attribution de la démarche 64844 (260 ou 1118)

Tranchée par la référence juridique **et** le contenu de la démarche : la notice
officielle du Cerfa 14531 (`getNotice.do?cerfaFormulaire=14531&cerfaNotice=51578`)
cite explicitement « Article L.362-1-1 du code de l'éducation » comme fondement — la
référence exacte de **numdispo 260**, pas de 1118 (référence « 6 », introuvable dans
cette notice). L'attribution déjà en ligne (260 → 64844) était donc correcte.
Correction documentée dans la PR #8 (`obligations-sva-correctif-cerfa`), **en attente
de fusion** — bloquée par le mode strict de l'environnement (fusion sans revue), pas
par un problème de fond.

## 2. Colonne `cerfa_eventuel`

Vérification croisée des 35 valeurs contre le registre officiel DILA : **une seule**
(numdispo 1118 → Cerfa 14531) correspond à un Cerfa dont le titre DILA se rapporte au
bon sujet — et même celle-là s'est révélée attachée à la mauvaise obligation (voir
point 1 : le Cerfa 14531 relève de 260, pas de 1118). Les autres renvoient soit à un
Cerfa sans rapport (ex. 14467 → « Déclaration préalable à l'embauche (DPAE) pour un
salarié agricole »), soit à un code interne non numérique (MEDDE1, MEDDE123, MEDDE81,
MEDDE63, MEDDE9, MCC17 — pas des numéros Cerfa). Colonne renommée
`cerfa_eventuel_non_fiable_sans_verification` dans `obligations_sva_*.csv` (PR #8,
même statut : en attente de fusion).

## 3. Inventaire des canaux (niveau 1), corrections

- **Simulateurs (type `Simulateur`/`simulateurNG`, 279 enregistrements) : confirmé
  jamais inclus dans le canal Cerfa** — seuls les types `Formulaire`/`formulaireNG`
  le sont, dans le script comme dans la version précédente (le point n'a jamais été un
  bug, juste à confirmer explicitement ; fait).
- **formulaires.service-public distingué de demarches.service-public** : la première
  version regroupait les deux dans un même domaine « demarches.service-public » (un
  Cerfa PDF téléchargeable comptait comme un téléservice interactif). Corrigé :
  domaines séparés (`formulaires.service-public`, `demarches.service-public`,
  `service-public (générique)`), plus `demarche.numerique.gouv.fr` ajouté au canal DN
  (c'est le domaine public de la plateforme, `demarches-simplifiees.fr` est le domaine
  technique sous-jacent — DN passe de 77 à 122 téléservices comptés).
- Sous-classement du résidu « autre » (798 → 257) par heuristique sur l'hôte :
  opérateur 169, ministère 141, « autre administration (.gouv.fr non classée) » 119,
  académie 13, le vrai résidu non classable restant à 257.

Script corrigé : `01_inventaire_canaux.py` (ci-joint).
