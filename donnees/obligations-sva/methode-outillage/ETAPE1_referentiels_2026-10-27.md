# Étape 1 — Référentiels utilisés et leur date

## DILA (fiches, formulaires, téléservices)

Export local existant (`cartographie/dila/`), **daté du 12-13 septembre 2026** (zips
`particuliers.zip`/`professionnels.zip`/`associations.zip` du 12/09, `dila_formulaires.jsonl`
régénéré le 13/09) — **6 semaines environ avant ce jour**. Je n'ai pas pu confirmer
l'existence d'un export plus récent : la recherche data.gouv.fr (sans WebSearch,
seulement WebFetch sur des URL devinées) n'a pas permis de retrouver la page du jeu de
données source avec certitude. **Non rafraîchi — utilisé tel quel, daté.** `canaux_dila`
régénéré aujourd'hui (27/10/2026) avec les corrections déjà demandées (simulateurs
exclus du canal Cerfa, formulaires.service-public distingué de demarches.service-public,
sous-classement du résidu « autre » par domaine réel) à partir de cet export DILA
existant — fichier `canaux_dila_2026-10-27.csv`.

## DN (Descriptif des démarches)

`app_demarches_0-3.json` (form2026-site) : contenu daté au plus tard du **2 octobre
2026** (date de publication la plus récente observée dans les données), dernière
réécriture du fichier le **6 octobre 2026** d'après l'historique git. **~3 semaines
avant ce jour**, cohérent avec la cadence mensuelle du skill `maj-demarches-form2026`
(pas de rafraîchissement déclenché ici : une mise à jour complète suit un protocole
séparé — dry-run, vérification, confirmation avant push — hors périmètre de cette
tâche d'analyse). Utilisé tel quel.

## Volumétrie DILA

`cartographie/volumetrie DILA.tab.csv`, daté du **20 septembre 2026**.

## Limite assumée

Aucun de ces trois référentiels n'a été rafraîchi à la source pour ce chantier — sans
accès WebSearch, je n'ai pas de moyen fiable de confirmer ou télécharger une version
plus récente de l'export DILA en particulier. Si une fraîcheur plus récente est
nécessaire, il faudra soit fournir les fichiers, soit lancer le skill de mise à jour
séparément pour DN, soit attendre une session avec accès WebSearch pour DILA.
