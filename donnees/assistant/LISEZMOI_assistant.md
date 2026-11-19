# « Trouver sa démarche » : index du démonstrateur

Données de la page `trouver-sa-demarche.html`. Production de l'auteur à partir de données ouvertes. Voir `donnees/LICENCE.md`.

## Fichiers

- `index.json` : une ligne par démarche en ligne ou par fiche, dans laquelle cherche le moteur de la page (`scripts/assistant/moteur.js`).
  - Démarches en ligne (`"k":"dn"`) : titre, extrait de description, organisme, département, public, nombre de dossiers, nombre de champs, pièces justificatives, données préremplies, moment de vie, fiches service-public liées.
  - Fiches et ressources de service-public.gouv.fr (`"k":"sp"`) : type, titre, description, public, thème, documents à fournir, numéro CERFA, démarches en ligne liées.
- `exemples.json` : les sept réponses préparées, chacune avec ses recherches et ses références (`DN-…`, `SP-…`). Leur texte a été vérifié contre l'index ; il ne se réécrit pas lors d'une mise à jour.

## Sources et dates

- **Descriptif des démarches publiées** de demarche.numerique.gouv.fr (data.gouv.fr), extraction du 3 novembre 2026. Il fournit les titres, organismes, départements, descriptions, adresses de dépôt et dates de fermeture.
- **Base FORM 2026**, dans ce dépôt : `app_demarches_*.json`, `champs_shards/` et les référentiels embarqués dans `explorer.html` (manifeste des types de champs, moments de vie, codification des fiches service-public). Elle fournit le public, les champs, les pièces justificatives, les données préremplies et les liens vers les fiches.
- **Fiches de service-public.gouv.fr** (DILA, licence ouverte) : exports « particuliers », « professionnels » et « associations » téléchargés le 12 septembre 2026, avec les formulaires CERFA et les liens vers les démarches en ligne.

Le volume de dossiers affiché est celui du descriptif, cumulé depuis la création de chaque démarche.

## Exclusions

- **Démarches réservées aux agents publics** : catégorie `agent_public` de la base FORM 2026.
- **Intitulés de test** : titres qui contiennent le mot « test », « essai » ou « brouillon ».
- **Pages de navigation DILA** : types « Dossier », « Recherche guidée », « Outil de recherche » et `outilRechercheNG`, ainsi que les doublons d'identifiant et les fiches sans titre.
- **Adresses électroniques et numéros de téléphone** : retirés de tous les textes, par `masquer()` et `masquer_tel()` de `scripts/retirer_contacts.py`.

`build_index.py` affiche à chaque construction le nombre de démarches gardées et écartées, par motif.

## Démarches nationales

Une démarche porte le département de son organisme et n'est proposée que pour ce département, ou quand aucun département n'est choisi. Sont traitées comme nationales, et proposées quel que soit le département choisi, les démarches dont l'organisme est déclaré « administration centrale » ou « opérateur d'État » et dont le nom ne désigne pas un service territorial. Est considéré comme un service territorial tout nom qui contient préfecture, département, région, académie, rectorat, ARS, CAF, CPAM, ville, mairie ou commune, ou un mot commençant par DD ou DR (DREAL et DRAAF compris), sans distinction de casse. Les démarches sans département sont, elles aussi, proposées partout.

## Recherche

Le moteur tourne dans le navigateur, sans appel à un service extérieur. C'est un classement BM25 : les mots sont normalisés et réduits à leurs six premières lettres, et quelques mots courants des usagers sont traduits dans le vocabulaire de l'administration. Il applique les filtres de public et de département et écarte les démarches dont la date de fermeture est passée. Il favorise les démarches qui ont reçu beaucoup de dossiers et rétrograde celles dont le titre ne porte que des années anciennes.

## Limites

- Le corpus ne couvre que les démarches publiées dans le descriptif ouvert et les fiches de service-public.gouv.fr. Il ne contient ni les téléservices des autres sites publics, sauf quand une fiche y renvoie, ni les démarches restées sur papier ou par courriel.
- Les champs et les pièces justificatives viennent de la base FORM 2026. Une démarche modifiée depuis cette base peut demander autre chose.
- Le département vient de l'organisme. Une démarche locale qui s'adresse à tout le territoire, ou une démarche nationale portée par un service local, est donc mal située.
- Aucune démarche de l'extraction du 3 novembre 2026 ne porte de date de fermeture. Le filtre des démarches fermées n'écarte donc rien dans cette version.
- La page oriente : elle ne dit pas si une personne a droit à une aide.

## Reconstruire

Les deux scripts lisent des sources hors du dépôt, l'export complet du descriptif et les fiches DILA. C'est l'exception prévue par la règle du README. Ces deux sources sont ouvertes et téléchargeables. Depuis la racine du dépôt :

    python3 scripts/assistant/extraire_descriptions.py <export du descriptif>.json <cartographie>/assistant/descriptions_publiees.jsonl
    python3 scripts/assistant/build_index.py --form . --carto <cartographie> --slim <slim du mois> --out donnees/assistant/index.json
    python3 scripts/assistant/assembler_page.py
    node scripts/assistant/test_moteur.js

`<cartographie>` est le dossier de travail qui contient `dila/` (fiches DILA déjà découpées en `dila_*.jsonl`) et `assistant/`. Le « slim du mois » est l'extrait compact du descriptif : une ligne par démarche, avec numéro, état, date de publication, dossiers, SIRET, organisme, type d'organisme, département et titre. Le dernier contrôle de `build_index.py` vérifie que toutes les références de `exemples.json` existent encore. S'il échoue, l'index ne se publie pas : les exemples sont à revoir par l'auteur.

L'index publié le 19 novembre 2026 a été reconstruit à l'identique par ces commandes, à partir de l'export du 3 novembre 2026.
