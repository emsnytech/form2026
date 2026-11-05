# FORM 2026

Cartographie des démarches administratives françaises (démarche.numérique.gouv.fr + fiches service-public.fr DILA) : classement par public cible, par événement de vie, et rapprochement des données/pièces justificatives demandées avec les API et référentiels publics déjà existants.

Adaptation 2026 de FORM, application FileMaker développée en 2016-2017 dans le cadre du programme *Dites-le-nous une fois* pour valoriser les travaux effectués à l'époque sur le recensement des formulaires et des données.

Toutes les données utilisées sont publiques (démarche.numérique.gouv.fr, service-public.fr, api.gouv.fr, data.gouv.fr).
Elles sont accessible sur data.gouv.fr

Plusieurs référentiels ont été créées, comme la classification des moments de vie des associations.

Cet exercice vit ! et des erreurs peuvent être exister !

Par ailleurs, ce n'est pas exhaustif! il n'y a que ce qui est en open data ou accessible sur internet. 
En particulier, la masse de procédures encore en PDF ou en papier n'est pas encore intégré.

Site généré statiquement — publié via GitHub Pages.

## Contrôle des liens

`python3 scripts/verifier_liens.py` teste tous les liens internes et externes du site. Le workflow `.github/workflows/verifier-liens.yml` lance les liens des pages à chaque PR, et tous les liens, données embarquées comprises, chaque semaine. Le rapport est disponible dans les artefacts du workflow.

## Règle : ce qui produit une page publiée vit dans le dépôt

Une seule exception, écrite dans la méthode : les scripts qui lisent une source interne (voir `donnees/fiches-ministeres/methode/REJOUER.md`). Les fiches ministères se rejouent depuis ce dépôt avec `donnees/fiches-ministeres/methode/rejouer.sh`. Le compteur se met à jour par le workflow `maj-compteur.yml`, qui propose le résultat et ouvre une issue en cas d'échec ; sa page affiche le mois couvert et signale un retard. `scripts/update_demarches_catalog.py` lit encore un catalogue de travail hors dépôt ; il ne fait aucun commit, et son résultat passe par une PR.

## Données de contact

**Ce site analyse ce que les démarches demandent. Il n'est pas un annuaire de contacts.** Ce principe vaut pour les adresses électroniques, les numéros de téléphone et toute autre donnée de contact qui apparaîtrait dans un corpus régénéré, sans tri entre contacts de service et contacts personnels.

`scripts/retirer_contacts.py --check` le contrôle sur tous les fichiers suivis, à chaque PR. Tout générateur de données publiées appelle `masquer_donnees()`. Seuls le domaine réservé `exemple.invalid` et la tranche fictive 01 99 00 sont admis, pour les jeux de test des scripts. Un document binaire ajouté au dépôt n'est pas lu par ce contrôle : à vérifier à la main.

## Historique git

Le 5 novembre 2026, un titre de démarche touchant des mineurs a été retiré de `justice_hors_opendata.json`. L'historique n'a pas été purgé : ce titre n'identifie personne, la page de la démarche est publique, et une réécriture casserait les liens de commits sans retirer l'information du monde.

Le même jour, les adresses électroniques ont été retirées des fichiers publiés. Elles restent dans l'historique, et il n'a pas été purgé non plus, alors même qu'une adresse peut identifier une personne : ces textes restent publics à leur source, sur la plateforme et dans son open data. Une purge ne protégerait personne tant qu'ils y figurent, et coûterait une réécriture de branches, un force-push et une demande de purge des caches. L'action utile est de signaler à la plateforme les adresses qui paraissent personnelles. Les téléphones suivent la même décision.

## Sources de `explorer.html`

`explorer.html` est maintenu directement : ne pas le régénérer depuis un ancien gabarit. Les données du classement CERFA viennent de `donnees/gains/` et de `scripts/classement_cerfa.py`. À chaque modification, `classement_cerfa.py --check` échoue si la page s'en écarte ou si un texte de méthode a disparu.
