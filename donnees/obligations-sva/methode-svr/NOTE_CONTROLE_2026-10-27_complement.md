# Complément de contrôle (27/10/2026, suite)

## 1. Relecture des 30 lignes — terminée

30/30 relues contre le classeur source, **toutes correctes**. Les 4 qui semblaient
diverger au premier passage (2014-1299, 2014-1286, 2014-1272, 2014-1290) étaient des
erreurs de *ma* recherche de vérification (recherche par préfixe trop courte, qui
trouvait une autre ligne du même décret au libellé voisin) — pas des erreurs de
parsing. Reconfirmé en cherchant le texte exact : les 4 correspondent bien à la ligne
d'origine. Cas intéressant noté au passage : 2014-1290 contient deux lignes au même
objet exact (« Autorisation d'affectation des travailleurs à des postes de nuit ») mais
deux dispositions différentes (Article L. 3122-21 et Article L. 213-5, dernier alinéa —
ce dernier étant le code du travail applicable à Mayotte) : pas un doublon, deux régimes
territoriaux distincts, tous deux conservés.

## 2. Les 53 recoupements SVA/SVR, classés un par un

| Classe | n | Explication |
|---|---|---|
| **(a) contradiction** | **5** | Voir détail ci-dessous |
| **(b) cohérent** (délai dérogatoire seul) | 7 | Toujours le même schéma : procédure **initiale** listée en SVR, son **renouvellement** listé dans la liste SVA (ou comme délai dérogatoire) — pas une contradiction, deux étapes différentes d'un même dispositif |
| **(c) sous-cas distinct** | 2 | Même article, objet voisin mais différent (ex. soumission initiale vs modification ultérieure d'un même traité) |
| **(d) faux positif** | 39 | Référence partagée (souvent un article « parapluie » couvrant de nombreuses procédures distinctes — ex. R57-6-1, R57-8-1 du code pénitentiaire), objets sans rapport |

Fichier complet : `recoupement_sva_svr_classe_2026-10-27.csv`.

### Les 5 cas (a) — contradiction, en détail

**1. Transfert de portefeuilles, mutuelles et unions** (décret 2014-1280, Articles
L. 212-11, L. 212-12, L. 212-11-1 du code de la mutualité) — **ce décret liste cette
procédure comme silence vaut REJET**. Or `obligations_sva.csv` contient exactement la
même procédure, avec exactement les mêmes articles, sous l'intitulé « Autorisation de
transfert de portefeuilles par les mutuelles ou unions » (numdispo 88), classée
silence-vaut-accord. **C'est le numdispo déjà repéré dans ce chantier comme témoin Cerfa
faux (14467, DPAE salarié agricole, sans rapport)** — la contradiction de fond, elle,
est nouvelle et n'avait pas été vue : soit `obligations_sva.csv` (liste officielle de
2016) est devenue obsolète sur ce point précis, soit les deux décrets couvrent des
aspects différents de la même procédure sans que cela apparaisse dans les deux
intitulés. À vérifier au texte si vous voulez trancher.

**2. Transfert de portefeuilles, institutions de prévoyance** (même décret 2014-1280,
Articles L. 931-16, L. 931-16-I, R. 931-4 du code de la sécurité sociale) — même
schéma que le cas 1, famille parallèle (institutions de prévoyance plutôt que
mutuelles). `obligations_sva.csv` : « Autorisation préalable de transfert de
portefeuilles » avec les mêmes articles, classée silence-vaut-accord.

**3. Transfert de portefeuilles, sociétés d'assurance/réassurance** (même décret
2014-1280, Article R. 322-117-1 du code des assurances) — même schéma, troisième
famille parallèle (sociétés d'assurance). `obligations_sva.csv` : « Autorisation
préalable de modification du traité de réassurance », mêmes articles.

**4 et 5. Accords d'exécution de transport de matières nucléaires** (R. 1333-17 du
code de la défense) — **deux décrets différents** (2014-1273 et 2014-1285) classent
chacun une variante de cette procédure en silence vaut REJET. `obligations_sva.csv`
contient « Accords d'exécution des transports de matières nucléaires » avec la même
référence R1333-17, classée silence-vaut-accord. Vu depuis deux ministères distincts
(1273 et 1285 ont des fondements/ministères différents), donc potentiellement deux
sous-procédures réellement distinctes de la même grande rubrique — à vérifier avant de
conclure à une contradiction unique ou double.

**Lecture d'ensemble** : les trois familles « transfert de portefeuilles » (mutuelles,
institutions de prévoyance, assurance/réassurance) partagent la même structure et
suggèrent une explication commune plutôt que trois erreurs isolées — probablement un
changement de régime (du silence-accord vers le silence-rejet, ou l'inverse) survenu
entre l'établissement de la liste SVA officielle (2016) et le décret d'exception
(2014, mais lu ici dans sa version **consolidée**, donc éventuellement modifiée depuis).
Reste à vérifier dans quel sens va la mise à jour, et laquelle des deux listes reflète
l'état actuel du droit.

## 3. Écart avec 1 686 — décret 2014-1266 consolidé vs version d'origine

**Vérification partielle, pas complète.** Retrouvé le décret sur Légifrance
(JORFTEXT000029675106) : confirmé qu'il a été modifié deux fois depuis 2014 — par le
décret n° 2016-308 du 17 mars 2016 (articles 1 et 2) et par le décret n° 2024-430 du
14 mai 2024 (l'annexe elle-même, effet au 1er janvier 2025). La structure de l'annexe
d'origine (JO du 1er novembre 2014), telle que résumée par ma lecture du texte JORF
brut, couvre les **mêmes six rubriques, dans le même ordre** que la version consolidée
du classeur (Code pénal, Code de la défense, Décret n° 2002-535, Décret n° 2010-112,
Décret n° 80-247, Instruction générale interministérielle n° 1300) : pas de rubrique
disparue ni ajoutée au niveau des intertitres. **Je n'ai en revanche pas pu obtenir un
diff ligne à ligne fiable** (objet/dispositions/délai précis de chaque procédure en
2014 vs aujourd'hui) : l'outil de lecture web ne restitue qu'un résumé, pas le tableau
complet d'origine. **Ce point reste donc non vérifié au niveau du détail** — seule la
structure générale est confirmée stable.

## 4. Partie 2 — paragraphe pour la note (pas de nouveau calcul)

*Un rapprochement par référence juridique tolérante aux versions (article/section/texte,
plutôt que l'identifiant LEGIARTI exact) a été testé sur l'échantillon de 56
obligations. Résultat : le niveau « texte entier » (LEGITEXT/JORFTEXT) produit
systématiquement du bruit — un même code ou une même loi-cadre (le code de l'éducation,
la loi Informatique et Libertés, l'ordonnance du 6 novembre 2014) est cité par des
centaines de démarches sans rapport avec l'obligation recherchée, et ne constitue jamais
une preuve. Le niveau « section » (LEGISCTA, le regroupement d'articles contenant la
référence) s'est montré plus précis : sur les 36 obligations dont la référence a pu être
résolue, il a permis de retrouver deux fiches DILA pertinentes (orientation Parcoursup,
travaux sur monuments historiques) que le rapprochement par titre seul avait manquées —
mais aucune des deux ne mène à un Cerfa ou un téléservice identifiable, le gain
s'arrête donc à la fiche. Le niveau « article » exact, le plus précis en théorie, n'a
produit qu'une seule correspondance sur cet échantillon, et c'est un faux positif déjà
connu. Verdict : le grain du droit n'est pas le grain de la démarche — une clé juridique
plus fine améliore la précision du rapprochement quand il a lieu, mais n'augmente pas le
nombre d'obligations couvertes sur cet échantillon.*
