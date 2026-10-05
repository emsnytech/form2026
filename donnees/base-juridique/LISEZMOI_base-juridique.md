# Base juridique des démarches — données dérivées

Production de l'auteur à partir de données ouvertes de data.gouv.fr (descriptif des démarches publiées sur demarche.numerique.gouv.fr). Voir `donnees/LICENCE.md`.

## Fichiers

### `juridique_niveau1.csv`

Classification automatique (par règles de texte, sans recherche) du champ « cadre juridique » des 34 397 démarches publiées ou closes du corpus.

**Colonnes** : `demarche`, `titre`, `organisme`, `type_organisme`, `etat`, `public` (particulier/personne_morale), `nb_dossiers`, `tranche_volume` (petit/moyen/gros), `cadre_declare` (contenu brut du champ, lien ou texte), `deliberation_flag` (indicateur plateforme), `type_contenu` (lien/texte/vide), `categorie_niveau1` (absent, page_accueil_recherche, texte_entier_sans_article, article_precis, circulaire, deliberation_reglement_organisme, autre_site), `accessibilite` (contrôle HTTP du lien : accessible/lien_mort/non_verifiable), `http_code`, `demarche_test` (démarche technique de test, repérée par mot-clé).

### `juridique_echantillon.csv`

Vérification manuelle (ouverture effective des textes) sur 120 démarches tirées au sort.

**Colonnes** : `demarche`, `organisme`, `strate` (type d'organisme | public | tranche de volume), `cadre_declare`, `qualification` (A précis et à jour, B pertinent mais général/daté, C lien mort ou hors sujet, D absent/non juridique), `cadre_propose` (référence vérifiée en remplacement, ou « non trouvé »), `extrait`, `date_verification`, `confiance` (élevé/moyen/faible), `temps_minutes`, `type_source`, `notes`.

### `juridique_strates_effectifs.csv`

Effectifs de population et d'échantillon par strate (type d'organisme × public × tranche de volume) utilisés pour le tirage des 120 démarches.

### `note_methode_juridique.md`

Note de méthode complète : définitions, répartition par catégorie (brute et pondérée par dossiers), intervalles de confiance à 95 % (méthode de Wilson), contrôle de stabilité (requalification à l'aveugle), limites.

## Nettoyage effectué avant publication

Les identifiants de session (`;jsessionid=…`) ont été retirés des adresses Légifrance dans `juridique_niveau1.csv` et `juridique_echantillon.csv` ; quelques adresses électroniques et numéros de téléphone institutionnels présents dans le texte brut du champ « cadre juridique » (mentions RGPD des organismes) ont été remplacés par `[adresse électronique retirée]` / `[téléphone retiré]`.

## Date et version

Analyse produite le 01-04/10/2026, sur le corpus des démarches publiées/closes au 24/09/2026.

## Limites

Voir `note_methode_juridique.md`. Points clés : classification automatique approximative (mesure de tendance, pas une qualification démarche par démarche) ; échantillon de vérification manuelle de 120 sur 34 397 (marge d'erreur de l'ordre de ±8-9 points) ; accessibilité HTTP sous-estimée (beaucoup de blocages anti-robot comptés « non vérifiable », pas « lien mort »).
