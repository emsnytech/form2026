# Grille d'appréciation des projets (FTAP) — données dérivées

Production de l'auteur. Voir `donnees/LICENCE.md`. Version 1, 28/10/2026. Page associée : `matrice-gains-ftap.html`.

## Pourquoi

L'annexe « économies » des dossiers déposés au Fonds pour la transformation de l'action publique (FTAP, modèle 2023) ne calcule qu'une chose : le coût d'un ETP multiplié par un nombre d'ETP. Ce nombre est déclaré, et les autres gains (fonctionnement, indirects) sont des montants saisis avec une méthode de calcul en texte libre.

Cette grille part de l'activité de la démarche, que le porteur peut justifier, et en déduit les gains. Un gain y est toujours l'écart entre deux situations : le niveau de départ et le niveau cible.

## Fichier

### `annexe-ftap-gains-demat_v1_2026-10-28.xlsx`

| Onglet | Contenu |
|---|---|
| Lisez-moi | Mode d'emploi, définition des niveaux, méthode, statut des hypothèses |
| Synthèse | Une page pour un comité : temps par dossier, gains annuels, ROI, seuil de volume, alertes |
| Projet | Saisie : volumes, champs, PJ, étapes, agents, niveaux de départ et cible, coûts, gains déclarés et justificatifs |
| Paramètres | Toutes les hypothèses, avec leur statut |
| Calcul | Décomposition par dossier pour le départ, la cible et la solution mutualisée de référence |
| Matrice | Temps agent, gain annuel et délai pour chaque combinaison collecte × traitement |
| Annexe FTAP | La grille FTAP 2023 alimentée par le calcul |
| Indicateurs | Tableau pluriannuel, ROI budgétaire et élargi, délai de retour, seuil de volume, gain différentiel, factualisation, contrôles de plausibilité |

Toutes les valeurs calculées sont des formules : le classeur se recalcule quand on change une saisie ou une hypothèse.

## Les niveaux

- Collecte : C0 courrier ou guichet papier · C1 courriel libre avec pièces jointes · C2 formulaire PDF renvoyé par courriel · C3 en ligne non intégré (export, ressaisie) · C4 en ligne structuré, instruit sur la plateforme · C5 intégré et prérempli (API, « dites-le-nous une fois »).
- Traitement : T0 boîte fonctionnelle et papier · T1 tableur de suivi · T2 instruction sur la plateforme · T3 interconnexion avec le SI aval.

## Calcul

- **Temps agent sensible à la dématérialisation**, par dossier : réception et enregistrement, ressaisie des champs, vérification des pièces, relances pour dossier incomplet (taux d'incomplétude, accru par le nombre de pièces), circulation entre étapes, notification, report dans le SI aval, archivage. L'instruction au fond n'est jamais comptée dans les gains ; elle sert au contrôle de plausibilité des effectifs.
- **Ancrages** : avec les valeurs par défaut, C2/T0 donne 12, 20 et 29 minutes pour les profils simple, modéré et complexe, contre 1,5, 2,3 et 3,3 minutes en C4/T2 — cohérent avec `donnees/hypotheses/temps_par_etape.csv` (11, 18 et 30 minutes contre 1,5, 2 et 3).
- **ETP** : dossiers basculés × écart de temps ÷ 1 607 h. Une part seulement est supprimée (selon le scénario) ; le reste est **redéployé et valorisé hors économies**, puisqu'il libère de la capacité sans réduire la dépense.
- **Frais physiques** : affranchissement, impression, numérisation externalisée, archivage papier, par dossier.
- **Usagers** : temps valorisé à 7,28 €/h (particuliers) et 44,70 €/h (personnes morales), comme dans le simulateur, plus l'affranchissement évité.
- **Scénarios** : prudente, centrale, haute ; ils font varier l'écart de temps retenu, la part des ETP supprimés et le taux d'adoption du canal cible.
- **Taux de factualisation** : part des gains budgétaires qui repose sur un calcul (pondéré à 50 % si le volume est estimé plutôt que mesuré) ou sur une pièce justificative.

## Valorisation horaire

Le temps agent est valorisé au coût chargé des catégories A, B et C, parce que l'annexe FTAP raisonne en masse salariale. La note de méthode v8 retient 44,70 €/h ; voir `donnees/hypotheses/cout_horaire_sensibilite.csv`. Les coûts par catégorie du classeur sont provisoires et doivent être remplacés par les coûts moyens du programme budgétaire.

## Limites

Hypothèses de l'auteur, à consolider. Seuls C2/T0 et C4/T2 sont ancrés sur des valeurs publiées ; les autres niveaux sont des valeurs de travail à calibrer par mesure (`donnees/hypotheses/mesure_temps_modele.csv`) ou par une expertise externe. Ordre de grandeur pour apprécier un dossier, pas un chiffrage opposable.
