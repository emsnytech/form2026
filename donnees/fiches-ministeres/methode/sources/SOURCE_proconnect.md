# ProConnect : connexions par fournisseur d'identité et par service (encadré « Côté agents » de la fiche Intérieur)

Source : tableau de bord public de ProConnect, https://www.proconnect.gouv.fr/stats (tableau Metabase public, filtre de date « past30days » : 30 jours glissants). Licence etalab-2.0 (pied de page du site).
Exports du 15 novembre 2026, entre 15 h 20 et 15 h 25 (heure de Paris, horodatage des fichiers) :
- `connexions_proconnect_par_FI_30j_2026-11-15.xlsx` : connexions par fournisseur d'identité, filtrées sur le service Démarche Numérique ;
- `connexions_proconnect_par_FI_global_30j_2026-11-15.xlsx` : connexions par fournisseur d'identité, tous services ;
- `connexions_proconnect_par_FS_global_30j_2026-11-15.csv` : connexions par service, tous fournisseurs ;
- `connexions_proconnect_par_FS_passage2_30j_2026-11-15.xlsx` : connexions par service, filtrées sur le fournisseur Passage2.

Chiffres calculés par `scripts/43_proconnect_interieur.py` (sortie `out/interieur_proconnect.json`), avec quatre contrôles de cohérence entre vues.
Ce sont des connexions, pas des agents distincts. Le tableau de bord ne rattache pas les fournisseurs d'identité à un ministère. Le rattachement vient de la présentation publique « ProConnect – Présentation de la solution », https://pad.numerique.gouv.fr/p/Mw1fEjmM- (non datée ; feuille de route « S1 2026 » et « S2 2026 (prévisionnel) »), consultée le 15 novembre 2026, section 1.2 : « Passage2 pour le Ministère de l'Intérieur » ; Cerbère pour le ministère de la Transition écologique.
**Libellé masqué.** Dans `connexions_proconnect_par_FS_global_30j_2026-11-15.csv` et `connexions_proconnect_par_FS_passage2_30j_2026-11-15.xlsx`, le nom d'un service ProConnect qui porte le titre d'une démarche sensible de la Justice est remplacé par « Service masqué (titre sensible) », selon la règle du dépôt (`scripts/controle_fiches.py`). Seul ce libellé change : les connexions et les rangs restent ceux de l'export, et les chiffres de la fiche sont identiques.
Le service « Saisine par voie électronique (SVE) » figure dans l'export (26 connexions) ; il n'est pas cité dans la fiche (arbitrage n° 27).
