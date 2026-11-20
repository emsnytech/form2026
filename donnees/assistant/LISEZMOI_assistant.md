# « Trouver sa démarche » : index du démonstrateur

Données de la page `trouver-sa-demarche.html`. Production de l'auteur à partir de données ouvertes. Voir `donnees/LICENCE.md`.

## Fichiers

- `index.json` : une ligne par démarche en ligne ou par fiche, dans laquelle cherche le moteur de la page (`scripts/assistant/moteur.js`).
  - Démarches en ligne (`"k":"dn"`) : titre, extrait de description, organisme, département, public, nombre de dossiers, nombre de champs, pièces justificatives, données préremplies, moment de vie, fiches service-public liées.
  - Fiches et ressources de service-public.gouv.fr (`"k":"sp"`) : type, titre, description, public, thème, documents à fournir, numéro CERFA, démarches en ligne liées.
- `types_guichets.json` : la table de correspondance de l'encadré « Où aller » (voir plus bas).
- `france_services.json` : les structures labellisées France services, avec leurs horaires, téléphones et courriels (voir plus bas).
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

## Portée des démarches en ligne

Chaque démarche en ligne porte un champ `po`, sa portée :

- `nat` : démarche nationale. Son organisme est déclaré « administration centrale » ou « opérateur d'État » dans la base FORM 2026, et son nom ne désigne pas un service territorial : préfecture, département, région, académie, rectorat, ARS, CAF, CPAM, ville, mairie ou commune, ou un mot commençant par DD ou DR (DREAL et DRAAF compris), sans distinction de casse. Elle est proposée quel que soit le département choisi.
- `dep` : démarche d'un département connu. C'est le département de son organisme ; à défaut, le code qui ouvre le titre suivi d'un tiret (« 94-Demande… », « 971 - … »), s'il désigne un département existant. Elle n'est proposée que pour ce département, ou quand aucun département n'est choisi.
- `inc` : démarche locale dont le département est inconnu. Elle est proposée pour tout département, après les démarches `nat` et `dep` retenues, sans encadré « Où aller » et avec la mention « Démarche locale : vérifiez qu'elle concerne votre commune. »

`build_index.py` affiche à chaque construction le nombre de démarches de chaque portée, et celui des départements déduits du titre.

## Recherche

Le moteur tourne dans le navigateur, sans appel à un service extérieur. C'est un classement BM25 : les mots sont normalisés et réduits à leurs six premières lettres, et quelques mots courants des usagers sont traduits dans le vocabulaire de l'administration. Il applique les filtres de public et de département (les démarches de portée `inc` passent après les autres) et écarte les démarches dont la date de fermeture est passée. Il favorise les démarches qui ont reçu beaucoup de dossiers et rétrograde celles dont le titre ne porte que des années anciennes.

## Où aller

Propre à la page FORM (`scripts/assistant/ou_aller.js`, recopié dans la page par `assembler_page.py`).

- **Code postal → commune** : API Géo de l'État (`geo.api.gouv.fr`), appelée avec le seul code postal. À Paris, Lyon et Marseille, l'arrondissement est retenu. Le département de la commune règle le filtre du moteur ; le sélecteur de département reste disponible.
- **Service local compétent** : Annuaire de l'administration (DILA), interrogé en direct avec le seul code de la commune : jeu des compétences géographiques (commune et type de service → identifiant), puis jeu des services (nom, adresse, horaires, téléphones, courriel, coordonnées, fiche officielle). Rien n'est stocké. L'encadré affiche le nom que renvoie l'Annuaire ; le type de la table sert seulement à choisir le guichet.
- **Quand l'encadré s'affiche** : la commune est connue, et la démarche ou la fiche correspond à une règle de `types_guichets.json` (indices cherchés comme mots entiers dans l'organisme d'une démarche en ligne, dans le titre et le thème d'une fiche). Une démarche en ligne n'a d'encadré que si elle relève du département de la commune ; les démarches nationales n'en ont pas. Les fiches service-public, nationales, ont l'encadré dès qu'elles correspondent à une règle. Sans correspondance, pas d'encadré. À Paris, la ligne « Préfecture » renvoie à la Préfecture de police (`paris_ppp`), l'Annuaire n'y ayant pas de type `prefecture`. Pour les cartes d'identité et passeports (fiches du thème « Papiers - Citoyenneté - Élections »), l'encadré renvoie à la fiche, sans afficher la mairie : toutes ne prennent pas ces demandes.
- **France services** : `france_services.json`, produit par `scripts/assistant/france_services.py` depuis la liste des structures labellisées de l'ANCT (data.gouv.fr, licence ouverte). La page calcule la plus proche du centre de la commune, à vol d'oiseau, et les deux suivantes. Encadré « Une France services peut vous aider » quand aucune démarche en ligne de portée `nat`, ni de portée `dep` pour le département de l'usager, ne figure parmi les 5 premiers résultats (sans département connu : aucune démarche `nat` ou `dep`) ; une démarche `inc` ne compte pas ; ligne « Besoin d'aide pour faire la démarche ? » sinon. Chaque structure est rapprochée de sa fiche dans l'Annuaire de l'administration, par identifiant ANCT (champ `partenaire_identifiant` de l'Annuaire), sinon par commune, nom normalisé et distance de moins de 200 m ; sans rapprochement, pas de lien « Fiche officielle ».
- **Contacts** : les téléphones et courriels affichés sont ceux que l'Annuaire et l'ANCT publient pour chaque service, avec la source sous chaque contact et un lien « Signaler une erreur » vers la fiche officielle quand elle existe. Aucune autre source de contacts n'est affichée. `france_services.json` est le seul fichier du dépôt exclu du contrôle des contacts (voir le README, « Données de contact »).

## Limites

- Le corpus ne couvre que les démarches publiées dans le descriptif ouvert et les fiches de service-public.gouv.fr. Il ne contient ni les téléservices des autres sites publics, sauf quand une fiche y renvoie, ni les démarches restées sur papier ou par courriel.
- Les champs et les pièces justificatives viennent de la base FORM 2026. Une démarche modifiée depuis cette base peut demander autre chose.
- Le département vient de l'organisme, ou du code qui ouvre le titre. Une démarche locale qui s'adresse à tout le territoire, ou une démarche nationale portée par un service local, est donc mal située ; une démarche locale sans département connu reste « inconnue ».
- Aucune démarche de l'extraction du 3 novembre 2026 ne porte de date de fermeture. Le filtre des démarches fermées n'écarte donc rien dans cette version.
- La page oriente : elle ne dit pas si une personne a droit à une aide.

## Reconstruire

Les deux scripts lisent des sources hors du dépôt, l'export complet du descriptif et les fiches DILA. C'est l'exception prévue par la règle du README. Ces deux sources sont ouvertes et téléchargeables. Depuis la racine du dépôt :

    python3 scripts/assistant/extraire_descriptions.py <export du descriptif>.json <cartographie>/assistant/descriptions_publiees.jsonl
    python3 scripts/assistant/build_index.py --form . --carto <cartographie> --slim <slim du mois> --out donnees/assistant/index.json
    python3 scripts/assistant/france_services.py
    python3 scripts/assistant/assembler_page.py
    node scripts/assistant/test_moteur.js

La page elle-même repart du gabarit de l'auteur, `<cartographie>/assistant/page.html` : `python3 scripts/assistant/assembler_page.py --depuis <cartographie>/assistant/page.html` lui applique les adaptations FORM (navigation, volumes indexés, cadre d'entrée, chemins des données, bouton et conditions de la version avec assistant), puis y recopie le moteur. Si le gabarit a changé au point qu'une adaptation ne trouve plus sa place, rien n'est écrit.

`<cartographie>` est le dossier de travail qui contient `dila/` (fiches DILA déjà découpées en `dila_*.jsonl`) et `assistant/`. Le « slim du mois » est l'extrait compact du descriptif : une ligne par démarche, avec numéro, état, date de publication, dossiers, SIRET, organisme, type d'organisme, département et titre. Le dernier contrôle de `build_index.py` vérifie que toutes les références de `exemples.json` existent encore. S'il échoue, l'index ne se publie pas : les exemples sont à revoir par l'auteur.

L'index publié le 19 novembre 2026 a été reconstruit à l'identique par ces commandes, à partir de l'export du 3 novembre 2026. Celui du 20 novembre 2026 y ajoute la portée des démarches en ligne (champ `po`), sans rien changer d'autre : 1 798 démarches `nat`, 9 624 `dep` (dont 17 au département déduit du titre) et 1 048 `inc`.
