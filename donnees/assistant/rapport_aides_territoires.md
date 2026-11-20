# Aides-territoires comme source de démarches de dépôt : audit

Produit par `scripts/assistant/audit_aides_territoires.py` le 2026-11-20. Source : [Aides-territoires (ANCT)](https://aides-territoires.beta.gouv.fr/), API, Licence Ouverte v2.0 ; dernière mise à jour des aides relevées : 2026-11-11. Aucun ajout à l'index ni à la page : rapport seulement.

## Volumes

- L'API plafonne une liste à 3 000 aides : la liste générale en a rendu 3000. Le relevé est complété par une liste par public visé (3004 aides distinctes), puis une liste par région du périmètre, chacune sous le plafond, réunies par identifiant. Publics proposés par l'API : Commune, Intercommunalité / Pays, Département, Région, Collectivité d’outre-mer à statut particulier, Etablissement public dont services de l'Etat, Entreprise publique locale (Sem, Spl, SemOp) ; ni association, ni entreprise privée, ni particulier.
- Le site annonce, dans ses statistiques publiques, 3138 « aides publiées et toujours ouvertes aux candidatures » (lu le 2026-11-20) ; l'écart avec le relevé n'est pas expliqué (définition de « ouverte », périmètre).
- Aides publiées relevées (`/api/aids/`) : 3181.
- Dont ouvertes (sans date limite de dépôt, ou date limite non passée au 2026-11-20) : 3181. **Le reste du rapport porte sur les aides ouvertes.**

## Champs disponibles et taux de remplissage (aides ouvertes)

Le champ `contact` est compté mais jamais lu ni recopié.

| Champ | Rempli | Part |
|---|---|---|
| `aid_types` | 3123 | 98 % |
| `aid_types_full` | 3123 | 98 % |
| `application_url` | 1097 | 34 % |
| `categories` | 3134 | 99 % |
| `contact` | 3021 | 95 % |
| `date_created` | 3118 | 98 % |
| `date_updated` | 3118 | 98 % |
| `description` | 3117 | 98 % |
| `destinations` | 1841 | 58 % |
| `eligibility` | 2187 | 69 % |
| `european_aid` | 238 | 7 % |
| `financers` | 3166 | 100 % |
| `financers_full` | 3166 | 100 % |
| `id` | 3181 | 100 % |
| `import_data_mention` | 826 | 26 % |
| `import_data_url` | 643 | 20 % |
| `import_share_licence` | 912 | 29 % |
| `instructors` | 0 | 0 % |
| `instructors_full` | 0 | 0 % |
| `is_call_for_project` | 3118 | 98 % |
| `is_charged` | 3181 | 100 % |
| `is_live` | 3118 | 98 % |
| `loan_amount` | 4 | 0 % |
| `mobilization_steps` | 3004 | 94 % |
| `name` | 3181 | 100 % |
| `name_initial` | 2111 | 66 % |
| `origin_url` | 2953 | 93 % |
| `perimeter` | 3173 | 100 % |
| `perimeter_code` | 3166 | 100 % |
| `perimeter_id` | 3173 | 100 % |
| `perimeter_scale` | 3173 | 100 % |
| `predeposit_date` | 0 | 0 % |
| `programs` | 498 | 16 % |
| `project_examples` | 1230 | 39 % |
| `project_references` | 1112 | 35 % |
| `recoverable_advance_amount` | 4 | 0 % |
| `recurrence` | 3165 | 99 % |
| `region` | 1204 | 38 % |
| `region_code` | 1204 | 38 % |
| `short_title` | 13 | 0 % |
| `slug` | 3181 | 100 % |
| `start_date` | 748 | 24 % |
| `submission_deadline` | 498 | 16 % |
| `subvention_comment` | 641 | 20 % |
| `subvention_rate_lower_bound` | 392 | 12 % |
| `subvention_rate_upper_bound` | 999 | 31 % |
| `targeted_audiences` | 3174 | 100 % |
| `url` | 3181 | 100 % |

## Lien de dépôt

Le lien de dépôt est porté par **`application_url`** (« candidater » : formulaire ou plateforme de dépôt). Il est distinct de `origin_url` (page de présentation chez le porteur) et de `url` (fiche Aides-territoires).

- Aides ouvertes avec un lien de dépôt : 1097 (34 %).
- Dont lien de dépôt identique à la page de présentation : 21.

## Répartition des liens de dépôt

| Famille | Aides |
|---|---|
| autres | 619 |
| Régions | 241 |
| agences de l'eau | 136 |
| Démarche Numérique | 69 |
| ADEME | 32 |

30 premiers domaines :

| Domaine | Famille | Aides |
|---|---|---|
| aidesenligne.maregionsud.fr | Régions | 94 |
| aides-redevances.eau-loire-bretagne.fr | agences de l'eau | 89 |
| messervices.grandest.fr | Régions | 81 |
| id77.fr | autres | 68 |
| subventions16.lacharente.fr | autres | 62 |
| subventions.manche.fr | autres | 48 |
| teleservices76.seinemaritime.fr | autres | 41 |
| demarches-simplifiees.fr | Démarche Numérique | 40 |
| messervices.landes.fr | autres | 34 |
| agirpourlatransition.ademe.fr | ADEME | 30 |
| demarche.numerique.gouv.fr | Démarche Numérique | 29 |
| rivage.eau-adour-garonne.fr | agences de l'eau | 28 |
| eaureunion.fr | autres | 23 |
| aidesetsubventions.oise.fr | autres | 22 |
| les-aides.paysdelaloire.fr | Régions | 20 |
| eaurmc.fr | agences de l'eau | 11 |
| subventions.eurelien.fr | autres | 10 |
| ofb.gouv.fr | autres | 9 |
| mesdemarches.iledefrance.fr | Régions | 9 |
| europac.grandest.fr | Régions | 8 |
| synergie-europe.fr | autres | 7 |
| mes-demarches.nouvelle-aquitaine.fr | Régions | 7 |
| pays-isle-perigord.com | autres | 7 |
| eau-seine-normandie.fr | agences de l'eau | 6 |
| subventions.loire.fr | autres | 6 |
| ticket.atd16.fr | autres | 6 |
| engagespourlanature.ofb.fr | autres | 6 |
| interreg-francesuisse.eu | autres | 5 |
| nosaidesenligneregion.centre-valdeloire.fr | Régions | 5 |
| messervicesenligne.haute-marne.fr | autres | 5 |

## Rapprochement avec Démarche Numérique

Liens de dépôt vers demarche.numerique.gouv.fr ou demarches-simplifiees.fr : 69. Rapprochement par l'adresse `/commencer/<slug>`.

| Cas | Aides |
|---|---|
| démarche présente dans l'index | 37 |
| absente du descriptif publié (fermée, dépubliée ou adresse changée) | 26 |
| publiée mais écartée de l'index (test ou réservée aux agents) | 3 |
| lien Démarche Numérique sans /commencer/ | 3 |

## Porteurs (financeurs)

566 porteurs distincts. Les 30 premiers :

| Porteur | Aides |
|---|---|
| Banque des Territoires | 156 |
| Conseil régional de Provence-Alpes-Côte d'Azur | 149 |
| ADEME | 147 |
| Conseil régional du Grand Est | 119 |
| Conseil régional d'Ile de France | 118 |
| Cerema | 107 |
| Agence de l'eau Rhin-Meuse | 99 |
| Agence de l'Eau Loire-Bretagne | 96 |
| Conseil régional de Nouvelle-Aquitaine | 93 |
| Commission européenne | 78 |
| ID77 | 69 |
| Conseil départemental de l'Essonne | 69 |
| Conseil départemental de la Charente | 66 |
| Conseil régional des Pays de la Loire | 57 |
| Conseil départemental de la Haute-Loire | 55 |
| Conseil départemental de la Manche | 55 |
| Conseil régional d'Occitanie | 51 |
| Ministère de la Culture | 49 |
| SIDEC du Jura (Syndicat mixte d’énergies, d’équipements et de e-communication) | 46 |
| Conseil départemental des Landes | 44 |
| Conseil départemental de la Drôme | 42 |
| Conseil départemental de la Seine-Maritime | 42 |
| Agence départementale Aveyron Ingénierie | 40 |
| Ministères de l'Aménagement du territoire et de la Transition écologique | 32 |
| Conseil départemental du Vaucluse | 32 |
| Office de l'eau Réunion | 29 |
| Conseil départemental du Tarn | 29 |
| Conseil départemental de l'Aude | 28 |
| Agence de l'eau Adour-Garonne | 27 |
| Conseil départemental de la Vendée | 23 |

## Publics visés

Une aide peut viser plusieurs publics.

| Public | Aides |
|---|---|
| collectivités | 2961 |
| établissements publics | 1194 |
| entreprises publiques locales | 1130 |
| non précisé | 7 |

Détail par valeur de l'API :

| Valeur de l'API (`targeted_audiences`) | Aides |
|---|---|
| Commune | 2838 |
| Intercommunalité / Pays | 2697 |
| Département | 1451 |
| Etablissement public dont services de l'Etat | 1194 |
| Entreprise publique locale (Sem, Spl, SemOp) | 1130 |
| Région | 963 |
| Collectivité d’outre-mer à statut particulier | 396 |

## Répartition territoriale

Échelle donnée par l'API (`perimeter_scale`) ; à défaut, déduite du périmètre (nom, `perimeter_code`, `region_code`).

| Échelle | Aides |
|---|---|
| Département | 1159 |
| Région | 725 |
| Pays | 540 |
| Ad-hoc | 384 |
| Bassin hydrographique | 249 |
| Continent | 70 |
| epci | 43 |
| autre ou non précisé | 8 |
| commune | 3 |

## Licence déclarée par aide (`import_share_licence`)

Certaines aides sont importées d'autres sources ; leur licence de partage est à vérifier avant toute réutilisation.

| Licence | Aides |
|---|---|
| non précisée (Licence Ouverte v2.0 du site) | 2269 |
| openlicence20 | 635 |
| unknown | 277 |

## Démarches de dépôt nouvelles qu'apporterait l'intégration

- Aides ouvertes dont le dépôt se fait hors Démarche Numérique : 1028.
- **Adresses de dépôt distinctes, après dédoublonnage : 250**, sur 191 domaines.
- Aides ouvertes sans lien de dépôt : 2084 (dépôt à chercher sur la page de présentation).

Adresses de dépôt partagées par plusieurs aides (plateformes communes), les 15 premières :

| Adresse | Aides |
|---|---|
| aidesenligne.maregionsud.fr/aides | 94 |
| aides-redevances.eau-loire-bretagne.fr/home/services-en-ligne/deposer-sa-demande-daide-en-ligne---rivage.html | 89 |
| messervices.grandest.fr/aides | 78 |
| id77.fr/fr/offres | 68 |
| subventions16.lacharente.fr | 62 |
| subventions.manche.fr | 45 |
| teleservices76.seinemaritime.fr/GN.GuichetCG76/workflow_url | 41 |
| messervices.landes.fr | 34 |
| rivage.eau-adour-garonne.fr/appli | 28 |
| eaureunion.fr/eau-financement/demande-de-subvention | 23 |
| aidesetsubventions.oise.fr | 22 |
| les-aides.paysdelaloire.fr/aides | 16 |
| eaurmc.fr/jcms/pro_102366/fr/le-portail-des-aides-de-l-agence-de-l-eau-rhone-mediterranee-corse | 11 |
| subventions.eurelien.fr | 10 |
| ofb.gouv.fr/territoires-engages-nature | 9 |

## 20 exemples tirés au hasard, dépôt hors Démarche Numérique

| Titre | Porteur | Public | Périmètre | Domaine du lien |
|---|---|---|---|---|
| Informer et conseiller les administrés du territoire sur l'habitat | Agence départementale d'information sur le logement de la Réunion | collectivités, entreprises publiques locales | Mayotte et Réunion | adil974.com |
| Créer ou transformer une salle de cinéma dans le cadre de son projet de territoire | ADRC - Agence nationale pour le développement du cinéma en régions | collectivités, entreprises publiques locales, établissements publics | France | adrc-asso.org |
| Soutenir la recherche scientifique | Conseil départemental de la Charente | entreprises publiques locales, établissements publics | Charente | subventions16.lacharente.fr |
| Soutenir la réfection des dégâts sur voies communales consécutifs aux intempéries | Conseil départemental de la Seine-Maritime | collectivités | Seine-Maritime | teleservices76.seinemaritime.fr |
| Créer des réservoirs et forages de sécurisation sur les îles non alimentées par le continent - Solidarité… | Agence de l'Eau Loire-Bretagne | collectivités | Loire-Bretagne | aides-redevances.eau-loire-bretagne.fr |
| Soutenir les initiatives artistiques et culturelles locales | Conseil régional du Grand Est | collectivités, entreprises publiques locales | Grand Est | messervices.grandest.fr |
| Améliorer la connaissance environnementale grâce aux observatoires | Agence de l'eau Adour-Garonne, Agence de l'eau Adour-Garonne | collectivités, entreprises publiques locales, établissements publics | Adour-Garonne | rivage.eau-adour-garonne.fr |
| Bénéficier d'un SIG (Système d'Information Géographique) et constituer des données cartographiques | Agence technique départementale de la Charente - ATD16 et opérateur… | collectivités, entreprises publiques locales, établissements publics | Charente | ticket.atd16.fr |
| Communiquer dans le cadre d’un plan d’actions de réduction des émissions de micropolluants | Agence de l'Eau Loire-Bretagne | collectivités | Loire-Bretagne | aides-redevances.eau-loire-bretagne.fr |
| Assurer l’animation et la communication pour la réduction des émissions dispersées de micropolluants dans le… | Agence de l'Eau Loire-Bretagne | entreprises publiques locales | Loire-Bretagne | aides-redevances.eau-loire-bretagne.fr |
| Préserver la qualité des réserves d’eau brute pour les usages domestiques | Office de l'eau Réunion | collectivités | La Réunion | eaureunion.fr |
| Aider les communes et leurs groupements à se doter d'un document d'urbanisme et de planification | Conseil départemental de l'Oise | collectivités | Oise | aidesetsubventions.oise.fr |
| Candidater à la reconnaissance "Territoires Engagés pour la Nature" - Provence-Alpes-Côte d'Azur | Office Français de la Biodiversité (OFB), Agence Régionale pour la… | collectivités | Provence-Alpes-Côte d'Azur | engagespourlanature.ofb.fr |
| Soutenir la diffusion culturelle | Conseil départemental du Morbihan | collectivités, établissements publics | Morbihan | mesaides.morbihan.fr |
| Être conseillé et accompagné dans la rédaction et la mise en œuvre de la clause sociale dans les marchés… | ID77 | collectivités | Seine-et-Marne | id77.fr |
| Restaurer les fonctions écologiques des marais rétro littoraux (travaux) | Agence de l'Eau Loire-Bretagne | collectivités | Loire-Bretagne | aides-redevances.eau-loire-bretagne.fr |
| Financer des travaux de modernisation de l'éclairage public et réduction de la pollution lumineuse | Conseil régional d'Ile de France | collectivités | Île-de-France | mesdemarches.iledefrance.fr |
| Engager une transition écologique au sein de ma collectivité : la stratégie une seule santé | Agence Bretonne de la Biodiversité (ARBE), Agence Régionale de la… | collectivités | France | ofb.gouv.fr |
| S’inscrire à la 48e compétition des métiers WorldSkills | Conseil régional de Provence-Alpes-Côte d'Azur | établissements publics | Provence-Alpes-Côte d'Azur | inscriptions.worldskills-france.org |
| Développer la gestion intégrée des eaux pluviales et renaturer les villes et villages | Agence de l'eau Adour-Garonne | collectivités, entreprises publiques locales, établissements publics | Adour-Garonne | rivage.eau-adour-garonne.fr |
