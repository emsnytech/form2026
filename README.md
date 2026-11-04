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

## Sources de `explorer.html`

`explorer.html` est maintenu directement : ne pas le régénérer depuis un ancien gabarit. Les données du classement CERFA viennent de `donnees/gains/` et de `scripts/classement_cerfa.py`. À chaque modification, `classement_cerfa.py --check` échoue si la page s'en écarte ou si un texte de méthode a disparu.
