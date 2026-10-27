# Note des chiffres finaux — avant réécriture de la page obligations-sva (28/10/2026)

Base : 155 vérifiés après contre-lecture (chaîne de corrections 211 → 203 →
165 → 155, tracée dans `ETAPE3_relecture_complete_2026-10-27.md` et
`VOLUMETRIE_ETAPE4_2026-10-27.md`).

## 1. Entonnoir

| Étape | n | % du total (2 806) |
|---|---|---|
| Énumérées (SVA 1 283 + SVR 1 174 + délai SVA 349) | **2 806** | 100 % |
| Vivantes (en vigueur 1 766 + transféré 9 + recodifié 251) | **2 026** | 72 % |
| Éteintes confirmées (supprimé, cause légale identifiée) | **402** | 14 % |
| Non vérifiable par cette méthode (numéro non localisé 178 + inconnu 134 + hors UE 66) | **378** | 13 % |
| → Outillées vérifiées (sur les 2 026 vivantes) | **155** | 7,6 % des vivantes, 5,5 % du total |

**Par canal (155)** : DN 104, Cerfa 46, téléservice 5.
**Par liste (155)** : SVA 82, SVR 56, délai SVA 17.

**Règle de présentation (page et note) : toujours donner les 402 éteintes et
les 378 non vérifiables côte à côte, jamais additionnées ni fondues en un
seul chiffre** — ce sont deux statuts de nature différente (l'un est une
conclusion positive confirmée par LEGI, l'autre une absence de conclusion).

## 2. Fourchette publiable

51 liens sur les 155 relus une seconde fois à l'aveugle (sans voir les
motifs) : 41 confirmés corrects (35/40 hors décret 2014-1282, qui a été
tranché à part : 6/11). En appliquant la précision hors 2014-1282 (35/40 =
87,5 %) aux 104 lignes vérifiées non relus une seconde fois : 104 × 87,5 % ≈
91 attendues correctes, + 41 déjà confirmées ≈ 132, arrondi à **130**.

**Formulation retenue pour la page : « entre 130 et 155 procédures, moins
d'une procédure vivante sur dix »** (jamais « environ 150 » — 155/2 026 ≈
7,6 %, 130/2 026 ≈ 6,4 %, les deux bornes restent sous un dixième).

## 3. Décrets SVR/délai renvoyant à un article supprimé ou recodifié

Chiffres de l'étape 2 bis, non affectés par les corrections d'outillage
(couche juridique indépendante de la couche canal) : **376 lignes** SVR/délai
en statut abrogé, dont :
- **152 recodifié** (décret non mis à jour depuis une recodification —
  principales destinations : CESEDA 34, code pénitentiaire 33, code du
  travail étendu à Mayotte 38, code des pensions militaires d'invalidité 13,
  code de la sécurité intérieure 10).
- **224 supprimé** (aucun signal de recodification trouvé).

## 4. Volumétrie (sur les 155 vérifiés, après correction 3)

- **DN (104 lignes)** : cumul total **115 151** dossiers ; annualisé estimé
  **≈ 50 306/an** (colonnes toujours séparées, jamais mélangées).
- **Cerfa/téléservice liés non partagés (32 lignes)** : téléchargements 2024
  cumulés **36 431**, soit **0,146 %** du total DILA (24 953 755 sur les
  1 938 formulaires/téléservices recensés).
- **Distribution par classe, procédures outillées seulement** :
  | Classe | Cerfa liés (32) | DN (104) |
  |---|---|---|
  | < 100 | 5 | 57 |
  | 100 – 1 000 | 25 | 28 |
  | 1 000 – 10 000 | 1 | 17 |
  | > 10 000 | 1 | 2 |
  (63 % des Cerfa liés et 55 % des DN sous 1 000 — à l'inverse de la
  distribution DILA générale où 15 % dépassent 10 000.)
- **Top 10 DILA** (tous formulaires, 1 938 enregistrements) : aucun n'est une
  procédure SVA/SVR/délai (cession de véhicule, inscription électorale,
  perte de pièce d'identité, immatriculation, AST, logement social, avis
  médical permis de conduire, prestations MDPH, attestation de témoin,
  acquisition de nationalité).
- **Top 50 DILA vs corpus** : 1 seule correspondance automatique trouvée
  (nationalité française, rang 10) — **vérifiée manuellement et confirmée
  incorrecte** (deux étapes différentes du même décret de naturalisation).
  **0 correspondance confirmée dans le top 50.**

## 5. Échantillon web (50 lignes, `cartographie/svr/out/partie3_resultats.csv`)

| Catégorie | n/50 | IC 95 % |
|---|---|---|
| Manquées (outillées en base, ratées par le rapprochement auto) | 7 | [7 %, 26 %] |
| Outillée hors bases DN/DILA (PDF préfectoraux, régulateurs, ordres) | 16 | [21 %, 46 %] |
| Confidentielle | 16 | [21 %, 46 %] |
| Courrier libre | 4 | [3 %, 19 %] |
| Obsolète de fait | 4 | [3 %, 19 %] |
| Hors usager | 2 | [1 %, 13 %] |
| Non trouvée | 1 | [0 %, 10 %] |

Intervalles larges (n = 50) : à présenter en ordres de grandeur, jamais en
totaux extrapolés avec une fausse précision.

## 5 bis. Classement par régime juridique des 50 formulaires les plus téléchargés (complément du 28/10)

Les démarches de masse ne sont pas « hors liste » par oubli : elles relèvent
de régimes juridiques différents, hors du champ du silence vaut accord/rejet.

| Régime | n/50 | % | Exemples (texte de rattachement) |
|---|---|---|---|
| Régime propre fixé par un code | **16** | 32 % | inscription électorale (code électoral L11), permis de construire/certificat d'urbanisme (code de l'urbanisme), immatriculation véhicule et permis international (code de la route), nationalité française (code civil art. 21-15, décret 93-1362), autorisation de travail étranger et DCEM (CESEDA), permis de visite en prison (code pénitentiaire), VAE (code du travail) |
| Déclaration (pas de décision, donc pas de silence) | **12** | 24 % | cession de véhicule, perte de carte d'identité/carte grise, PACS, déclaration préalable de travaux, DAACT, accident du travail, modification d'association ou d'entreprise |
| Autre (acte privé, document-type, dispositif disparu, distinction) | **12** | 24 % | autorisation de sortie de territoire et autorisation parentale de vaccination (actes parentaux privés), mandat d'immatriculation, demande au JAF (justice civile), attestation de témoin, médaille du travail, opération tranquillité vacances, attestation Covid (dispositif disparu) |
| Prestation ou demande financière (exclue par la loi) | **6** | 12 % | prestations MDPH, RSA/prime d'activité, aide juridictionnelle, complémentaire santé solidaire, subvention à une association |
| Compétence d'une collectivité ou d'un organisme de sécurité sociale | **3** | 6 % | attestation d'accueil (maire), ouverture des droits et attestation de salaire assurance maladie (CPAM) |
| Fiscalité | **1** | 2 % | déclaration de don manuel (CGI art. 757) |

**Message retenu pour la section 6 de la page** : les listes SVA/SVR ne
couvrent qu'un seul régime — la demande de décision adressée à l'État et à
ses établissements publics. 56 % des 50 formulaires les plus téléchargés
(déclaration + autre + prestation + collectivité/sécu + fiscalité) relèvent
d'un régime pour lequel **aucune liste équivalente n'existe** ; les 32 %
restants ont un régime propre, codifié ailleurs, distinct de la liste SVA.
Détail ligne à ligne : `cartographie/outillage-etape3/top50_regime_juridique_2026-10-28.csv`.

## 6. Point non résolu, à signaler dans la page (méthode et limites)

La recherche systématique de **toutes** les contradictions SVR/délai-SVA
au-delà des 5 cas déjà confirmés (demandée dans le « Complément » du
26/10/2026) **n'a pas été menée à son terme** — seuls les 53 recoupements
initiaux ont été classés (5 contradictions, 7 cohérents, 2 sous-cas, 39 faux
positifs). La page ne doit présenter que les **5 cas confirmés**, avec la
mention explicite que la recherche n'est pas exhaustive au-delà de cet
échantillon.

---

Ces chiffres sont soumis avant toute rédaction de la page, conformément à
l'étape 0 de la consigne.
