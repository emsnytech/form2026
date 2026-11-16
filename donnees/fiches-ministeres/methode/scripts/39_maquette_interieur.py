"""Fiche Intérieur, étape 3 : maquette (texte et tableaux, avant mise en page). Fil directeur : arbitrage n° 23 ;
relecture : arbitrage n° 24. Aucun chiffre n'est écrit à la main : tous viennent de out/interieur*.json (scripts 02, 31 à 38,
40 à 43 ; chronologies : arbitrages n° 25 et 26 ; frais évités, « Côté agents » : arbitrage n° 27). La phrase centrale du cadre d'entrée vient de scripts/sync_cadre.py du dépôt (CENTRE). Aucun département nommé.
Sortie : out/maquette_interieur.md. Le script s'arrête si la sortie contient une adresse électronique, un numéro de téléphone
ou un nom de département."""
import json, re, ast, unicodedata
from pathlib import Path

J = lambda n: json.load(open(f"out/{n}.json"))
I, FAM, LN, CP, ET, QI, BR, MC, VA = (J(n) for n in ("interieur", "interieur_familles_etape1", "interieur_local_national",
    "interieur_complements_etape1", "interieur_etrangers", "interieur_qui_instruit", "interieur_briques",
    "interieur_maquette_chiffres", "interieur_variete"))
import os
def _sync_cadre():
    """scripts/sync_cadre.py, à la racine du dépôt."""
    return Path(__file__).resolve().parents[4] / "scripts/sync_cadre.py"
src = _sync_cadre().read_text()
m = re.search(r"^CENTRE = \((.*?)\)\n", src, re.S | re.M)
CENTRE = "".join(ast.literal_eval(x) for x in re.findall(r'"(?:[^"\\]|\\.)*"', m.group(1).replace("+ STATS +", '"[compteur public de la plateforme]"')))
CENTRE = CENTRE.split(" Ces ordres")[0]
CONSULT = "pages publiques consultées le 14 novembre 2026"

NB = " "
def n(x): return f"{round(x):,}".replace(",", NB) if isinstance(x, (int, float)) else str(x)
def M(x): return f"{x/1e6:.2f}".replace(".", ",") + " M"
def p(x): return f"{x:.1f}".replace(".", ",") + " %"
def pc(a, b): return p(100 * a / b)
def v2(x): return f"{x:.2f}".replace(".", ",")
MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre']
def d(s): return f"{int(s[8:10])} {MOIS[int(s[5:7]) - 1]} {s[:4]}"
def row(*c): return "| " + " | ".join(map(str, c)) + " |"
def cap(s): return s[0].upper() + s[1:]

P = I["perimetre"]; PF = I["plateforme"]; S = MC["sensibilite"]; NA = MC["national"]; T = P["dossiers_total"]
med = CP["medailles"]; mt = med["travail"]; mr = med["régionale, départementale et communale"]; ma = med["agricole"]
dep = ET["par_deposant"]; fn = ET["par_fonction_personne"]; ca = MC["etrangers_calendrier_arrete"]["par_fonction"]
ins = QI["instructeurs"]; PZ = QI["prefectures_autres_zones"]; qpf = QI["par_famille"]; pref = ins["préfecture ou sous-préfecture"]
DDx = "direction départementale ou régionale d'un autre ministère (DDT, DDETS, DREAL, DRIEAT...)"
POLx = "police, gendarmerie et leurs écoles"
permis = qpf["Permis de conduire, aptitude à la conduite, éducation routière"]["instructeurs"]
logt = qpf["Logement et hébergement (accords collectifs, contingent, CCAPEX)"]["instructeurs"]
pac = permis["administration centrale de l'Intérieur"]
V = MC["verification"]; fo = BR["fondations_et_fonds_de_dotation"]; asso = BR["associations"]
A = VA["A"]; AP = A["prefectures"]; AD = A["directions_departementales"]; UNI = VA["uniformes"]; B = VA["B"]; CS = VA["C"]; RT = VA["rattachement"]
TA = VA["taille"]; SC = VA["sans_champ"]; DE = VA["detr"]; ND = VA["regles"]["departements"]
CH = J("interieur_chronologies"); CD = CH["detr"]; CM = CH["medailles"]; SD = CH["sensibilite_date_creation"]
FE = J("interieur_frais_evites"); PC = J("interieur_proconnect")
def ME(x): return f"{x/1e6:.1f}".replace(".", ",") + " M€"
SIMU = "https://emsnytech.github.io/form2026/simulateur-gains-dematerialisation.html"
ln_ = {x["titre_graine"]: x for x in LN["detail"]}
cn = next(x for t, x in ln_.items() if "NEPH" in t)
cl_ = next(x for t, x in ln_.items() if re.search(r"qualit. des formations", t))
ecart = max(max(abs(fc0.get(k, 0) - SC[c].get(k, 0)) for k in set(fc0) | set(SC[c])) for fc0, c in ((AP["familles_couvertes"], "familles_couvertes"), (AP["familles_couvertes_en_ligne"], "familles_couvertes_en_ligne")))
L = []; w = L.append

w("# Fiche ministère n° 3 — Intérieur · maquette (avant mise en page)\n")
w(f"*Descriptif ouvert du {d(I['config']['date_extraction'])}. Chiffres produits par `scripts/39_maquette_interieur.py`. Fil : arbitrage n° 23 ; relecture : arbitrage n° 24.*\n")

# 1 ------------------------------------------------------------------------------------------------------------------------
w("## 1. En-tête\n")
w("**Titre.** Intérieur : l'appropriation par les préfectures, des usages qui varient d'un département à l'autre.\n")
qo = AP["en_ligne_par_departement"]; fcl = AP["familles_couvertes_en_ligne"]
w(f"**Chapeau.** Le ministère de l'Intérieur est la première zone du descriptif ouvert : {n(P['total'])} démarches et {M(T)} de dossiers, "
  f"soit {pc(P['total'], PF['total'])} des démarches et {pc(T, PF['dossiers_total'])} des dossiers du fichier. Toutes les préfectures y publient ; un quart d'entre elles ont {n(qo['q1'])} démarches en ligne ou moins, "
  f"un autre quart {n(qo['q3'])} ou plus, pour des réglementations identiques sur tout le territoire. La taille du département n'explique qu'une partie de cet écart.\n")
w("**Cadre d'entrée** (produit par `sync_cadre.py`) :\n")
w(f"> **Ce que cette fiche décrit.** Elle porte sur les démarches publiées dans le descriptif ouvert de la plateforme, et non sur l'ensemble de l'activité du ministère. {CENTRE}\n")
w(f"**Un périmètre approché.** La fiche retient la politique déclarée dans la zone « Ministère de l'Intérieur » ({n(P['par_source']['zone'])} démarches) et {n(P['par_source']['nom_organisme'])} démarches sans zone "
  f"rattachées par le nom de l'organisme ; au-delà de trois zones, une démarche sort du périmètre ({n(P['exclues_interministerielles'])}). Des agents d'autres ministères mettent en œuvre des politiques de l'Intérieur, "
  f"et les préfectures des politiques d'autres ministères. Depuis la reprise des zones du 7 octobre 2022, les préfectures déclarent rarement la zone d'un autre ministère ({n(PZ['demarches'])} démarches, contre "
  f"{n(pref[0])} en zone Intérieur) : la zone déclarée suit souvent l'émetteur. Toute série antérieure à cette date porte cette réserve.\n")
w(row("Sensibilité du chiffre d'ensemble (textes vérifiés)", "Dossiers", "Part des dossiers du fichier ouvert")); w(row("---", "---:", "---:"))
w(row("Zone Intérieur, périmètre retenu", n(S["perimetre"][1]), p(S["perimetre"][2])))
w(row("sans les médailles d'honneur du travail", n(S["sans_medailles_travail"][1]), p(S["sans_medailles_travail"][2])))
w(row("sans les médailles d'honneur du travail et agricoles", n(S["sans_medailles_travail_agricoles"][1]), p(S["sans_medailles_travail_agricoles"][2])))
w("")
w("Ces médailles sont « décernée[s] par arrêtés » du ministre chargé du travail et du ministre de l'agriculture (décrets n° 84-591 et n° 84-1110, art. 16), avec délégation possible aux préfets.\n")

# 2 ------------------------------------------------------------------------------------------------------------------------
w("## 2. Le profil\n")
w(row("Famille", "Démarches", "Dossiers", "Part", "Dossiers 2021-2026", "Part 2021-2026")); w(row("---", "---:", "---:", "---:", "---:", "---:"))
for f in sorted(FAM, key=lambda x: (x[0] == "Autres, non classées", -x[2])):
    w(row(f[0], n(f[1]), n(f[2]), p(f[3]), n(f[6]), p(f[7])))
w(row("**Total**", n(P["total"]), n(T), "100 %", n(I["concentration_fenetre"]["dossiers"]), "100 %"))
w("")
w(f"*Médailles* : deuxième volume, porté par {NA['dont_medailles'][0]} démarches nationales ({n(NA['dont_medailles'][1])} dossiers) ; travail {n(mt['nationale']['dossiers'] + mt['locale']['dossiers'])}, "
  f"régionale, départementale et communale {n(mr['nationale']['dossiers'] + mr['locale']['dossiers'])}, agricole {n(sum(v['dossiers'] for v in ma.values()))}. "
  f"*Étrangers*, en deux ensembles jamais additionnés : personnes concernées, {n(dep['personne concernée'][0])} démarches et {M(dep['personne concernée'][1])} de dossiers ; employeurs et tiers, "
  f"{n(dep['employeur ou tiers'][0])} démarches et {M(dep['employeur ou tiers'][1])}, dont la vérification avant embauche ({n(V['demarches'])} démarches, {n(V['dossiers'])} dossiers).\n")
fg, fs = FE["perimetre"], FE["sans_medailles_travail_agricoles"]; g_, gs = fg["gains"], fs["gains"]; ca_ = FE["cout_admin_par_dossier"]
w(f"**{ME(g_['bas'])[:-3]} à {ME(g_['haut'])} de frais évités de {FE['periode'][0]} à {FE['periode'][1]}.** Administration : {ME(g_['admin_bas'])[:-3]} à {ME(g_['admin_haut'])} de coût de traitement évité. "
  f"Usagers : {ME(g_['usagers_bas'])[:-3]} à {ME(g_['usagers_haut'])} de temps évité (envoi des pièces, préremplissage). "
  f"Sans les médailles d'honneur du travail et agricoles : {ME(gs['bas'])[:-3]} à {ME(gs['haut'])}. "
  f"Les gains de chaque démarche sont repris du fichier `demarches_gains_v8` de FORM 2026, puis ramenés aux dossiers déposés pendant la période. Ce fichier couvre {p(fg['taux_couverture'])} des dossiers de la période "
  f"({p(fs['taux_couverture'])} sans ces médailles). Les dossiers sont répartis au prorata des jours d'ouverture ; appliquée à toute la plateforme, la méthode retrouve "
  f"{FE['controle_utilisation_du_service']['part_retrouvee_min']} à {FE['controle_utilisation_du_service']['part_retrouvee_max']} % des dépôts mensuels publiés (jeu « Utilisation du service »), selon l'année ; "
  f"comme dans la fiche Éducation, les frais évités ne sont pas recalés sur ces dépôts. [Refaire le calcul avec le simulateur]({SIMU}). Ce sont des temps et des coûts valorisés, pas des économies budgétaires constatées. "
  f"Le coût évité par dossier pour l'administration ({v2(ca_[0])} à {v2(ca_[1])} €) vient de France Stratégie (2018), d'après des études étrangères.\n")

# 3 ------------------------------------------------------------------------------------------------------------------------
w("## 3. L'appropriation par les préfectures : une variété visible\n")
w("**Limite, en tête.** L'open data ne montre que les démarches publiées et ouvertes à la publication. Une préfecture peu présente peut passer par d'autres canaux, dont le dispositif SVE du ministère "
  "ou des boîtes fonctionnelles, ou avoir restreint l'ouverture. La variété décrite porte sur la place de la plateforme, pas sur la numérisation ; la fiche ne parle jamais de retard.\n")
w("[[CARTE]]\n")
w("**Combien de politiques sont couvertes.** Sept familles : permis et auto-écoles, élections, polices administratives, dotations et aides, RH et action sociale, étrangers, autres.\n")
fc = AP["familles_couvertes"]
w(row("Familles couvertes", *[str(k) for k in range(1, 8)])); w(row("---", *["---:"] * 7))
w(row("Départements, démarches en ligne aujourd'hui", *[n(fcl.get(str(k), 0)) for k in range(1, 8)]))
w(row("Départements, depuis l'origine", *[n(fc.get(str(k), 0)) for k in range(1, 8)]))
w("")
q = AP["demarches_par_departement"]; qd = AP["dossiers_par_departement"]
w(row("Par département (préfecture et sous-préfectures)", "Premier quart", "Médiane", "Troisième quart")); w(row("---", "---:", "---:", "---:"))
w(row("Démarches en ligne aujourd'hui", n(qo["q1"]), n(qo["mediane"]), n(qo["q3"])))
w(row("Démarches publiées depuis l'origine", n(q["q1"]), n(q["mediane"]), n(q["q3"])))
w(row("Dossiers", n(qd["q1"]), n(qd["mediane"]), n(qd["q3"])))
w("")
w(f"Le compte « depuis l'origine » additionne des versions successives : une préfecture qui recrée sa démarche à chaque campagne paraît plus active. Les familles couvertes et les démarches en ligne y sont moins sensibles.\n")
sp = TA["spearman_population"]; qq = TA["par_quart_de_population"]
w(f"**Contrôle de taille.** Rapportées à la population (INSEE, populations de référence 2023 ; {n(TA['departements'])} départements couverts par le fichier), les démarches en ligne ont une corrélation de rang de {v2(sp['en_ligne'])}, les familles couvertes en ligne de {v2(sp['familles_en_ligne'])}, "
  f"les dossiers de {v2(sp['dossiers'])}. La taille explique une partie de la variété, pas toute : dans le quart des départements les moins peuplés, les démarches en ligne vont de {n(qq[0]['en_ligne_min'])} à {n(qq[0]['en_ligne_max'])} "
  f"et les familles couvertes de {n(qq[0]['familles_min'])} à {n(qq[0]['familles_max'])} ; dans le quart le plus peuplé, de {n(qq[3]['en_ligne_min'])} à {n(qq[3]['en_ligne_max'])} démarches.\n")
lg, et = AP["typologie"]["larges_6_7_familles"], AP["typologie"]["etroits_3_familles_ou_moins"]
w(f"**Deux profils** (depuis l'origine, aucun département nommé). {n(lg[0])} départements couvrent six ou sept familles, avec {n(lg[2])} démarches en moyenne ; {n(et[0])} en couvrent trois ou moins, "
  f"avec {n(et[2])} démarches en moyenne, surtout des dotations.\n")
w("**Pour des réglementations identiques.**\n")
w(row("Réglementation (mots du titre)", "Départements", "… en ligne", "Dossiers par département (quartiles)"))
w(row("---", "---:", "---:", "---"))
for k, u in UNI.items():
    q_ = u["dossiers_par_departement"]
    w(row(cap(k), n(u["departements"]), n(u["departements_en_ligne"]), f"{n(q_['q1'])} / {n(q_['mediane'])} / {n(q_['q3'])}"))
w("")
mf = UNI["police administrative : déclaration de manifestation sur la voie publique"]
w(f"La déclaration de manifestation sur la voie publique figure sur la plateforme dans {n(mf['departements'])} départements ; SVE propose une rubrique nationale « Rassemblement et manifestations » "
  f"({CONSULT}). Une procédure peu visible sur la plateforme peut ainsi passer par l'autre canal.\n")
dn_, p2_ = PC["dn"], PC["passage2"]; assert dn_["passage2_premier_apres_generique"]
rang = ["premier", "deuxième", "troisième", "quatrième", "cinquième", "sixième", "septième", "huitième", "neuvième", "dixième"]
w(f"> **Côté agents.** Les connexions des agents confirment cette appropriation. Sur les {PC['fenetre_jours']} jours précédant le {d(PC['export'])}, Passage2, le fournisseur d'identité du ministère de l'Intérieur, "
  f"totalise {n(dn_['passage2'][0])} connexions à la plateforme par ProConnect ({p(dn_['passage2'][1])}) : c'est le premier fournisseur ministériel, après l'identité générique de ProConnect ({p(dn_['generique'][1])}). "
  f"Cerbère, celui du ministère chargé de l'écologie, dont relèvent les DDT, en compte {n(dn_['cerbere'][0])}. Pour les agents de l'Intérieur, la plateforme est le {rang[p2_['rang_dn'] - 1]} service utilisé par ProConnect "
  f"({p(p2_['part_dn'])} de leurs connexions), après notamment MirAI, le portail d'IA interne du ministère.\n")
w("Ce sont des connexions, pas des agents distincts ; ProConnect n'est qu'un mode de connexion à la plateforme ; une partie des agents de l'Intérieur passe par l'identité générique, et la part de Passage2 est donc un minimum. "
  f"Fenêtre glissante de {PC['fenetre_jours']} jours, tableau de bord public de ProConnect, export du {d(PC['export'])}.\n")
w(f"*À part* : les directions départementales d'autres ministères ({n(AD['demarches'])} démarches dans {n(AD['departements_avec_au_moins_une'])} départements) et les unités régionales, rattachées à aucun département "
  f"({n(A['unites_regionales'][0])} démarches).\n")

# 4 ------------------------------------------------------------------------------------------------------------------------
w("## 4. Deux canaux pour saisir une préfecture\n")
w(f"**Chapeau.** À côté de la plateforme, le ministère édite son propre dispositif de saisine électronique, SVE. Fonctions relevées sur les {CONSULT}, sans validation finale.\n")
w(row("Fonction", "Démarche Numérique", "SVE")); w(row("---", "---", "---"))
for r_ in (("Éditeur", "Direction interministérielle du numérique (mentions légales)", "ministère de l'Intérieur, créé en novembre 2015 en application du décret n° 2015-1423 (mentions légales)"),
           ("Identification", "FranceConnect pour les particuliers, ProConnect pour les agents des administrations, ou compte avec mot de passe (page de connexion)",
            "aucune connexion proposée à l'étape 1 (conditions générales, puis choix particulier / professionnel / association) ; SIREN pour une entreprise, RNA pour une association ; identité et adresse en champs structurés"),
           ("Contenu de la demande", "champs et pièces définis par le service pour chaque démarche (descriptif ouvert)",
            "objet repris de la rubrique, département, nature (information ou dépôt de dossier), champ libre « Votre demande », pièces jointes PDF ou JPG de 3 Mo au plus"),
           ("Raccordement d'un outil d'instruction", "API GraphQL ; jeton créé par un administrateur, en lecture ou en écriture, limité à ses démarches ; mutations de changement d'état (documentation de l'API)",
            "aucune API publique documentée trouvée"),
           ("Traitement côté service", "le dossier est instruit dans la plateforme, ou dans un outil branché par l'API",
            "outil de gestion du courrier : selon la documentation de Maarch Courrier (version 18.10), « toutes les préfectures sont équipées de Maarch Courrier avec un paramétrage SVE »")):
    w(row(*r_))
w("")
w("**Phrase-clé, en constat.** Sur SVE, l'identité est saisie dans des champs structurés, mais le contenu de la demande passe par un champ libre et des pièces jointes : il n'en sort pas de données "
  "structurées réutilisables pour le « dites-le-nous une fois ». Sur la plateforme, le service définit lui-même les champs de la demande. Le [comparateur du cadre fonctionnel](https://emsnytech.github.io/form2026/comparer-cadre-fonctionnel.html) de FORM 2026 permet de vérifier, fonction par fonction, ce que couvre un outil.\n")
w("Aucune source publique ne dit si les préfectures peuvent modifier les formulaires de SVE, et aucun volume de SVE n'est public : la fiche n'en dit rien.\n")

# 5 ------------------------------------------------------------------------------------------------------------------------
w("## 5. Quand un formulaire national s'installe\n")
w(f"**Chapeau.** Le passage du local au national est rare : sur {n(LN['familles_10_locales'])} familles de titres comptant au moins 10 versions locales, {LN['avec_nationale']} ont une version nationale, "
  f"dont {LN['avec_nationale_100']} d'au moins 100 dossiers (seuil ajouté après lecture). **Une question : un formulaire national suppose-t-il qu'une majorité de préfectures ait déjà numérisé la procédure ?**\n")
w(row("Cas", "Version nationale", "Départements ayant déjà une version locale (définition large)", "Ce qui a suivi"))
w(row("---", "---", "---", "---"))
ne, la, de = B["NEPH"], B["label des écoles de conduite"], B["DETR et DSIL"]
dap = DE["famille_de_titres"]["publiees_apres_la_nationale"]
w(row("Communication du NEPH", d(ne["date_nationale"]), f"{n(ne['departements_deja_une_locale'])} sur {ND} ({n(ne['variante_mots_du_titre']['departements_deja_une_locale'])})",
      f"{cn['fermees_18_mois_100']} des {cn['ouvertes_100']} versions locales ouvertes ferment en 18 mois ; aucune ouverte aujourd'hui"))
w(row("Label des écoles de conduite", d(la["date_nationale"]), f"{n(la['departements_deja_une_locale'])} sur {ND} ({n(la['variante_mots_du_titre']['departements_deja_une_locale'])})",
      f"{cl_['fermees_18_mois_100']} des {cl_['ouvertes_100']} ferment en 18 mois ; {cl_['locales_ouvertes_aujourdhui']} encore ouvertes"))
t2, ap = CD["temps2"], CD["apres_la_nationale"]; nv, rp = ap["nouvelle_demande"], ap["demarche_anterieure_republiee"]
w(row("DETR et DSIL", d(CD["nationale"]["publication"]) + " (exercice 2026)", f"{n(de['departements_deja_une_locale'])} sur {ND} ({n(de['variante_mots_du_titre']['departements_deja_une_locale'])})",
      f"une seule nouvelle demande locale créée ensuite : {n(nv['versions'])} versions par arrondissement, dans {n(nv['departements'])} département"))
w("")
w("**La DETR et la DSIL, en trois temps.**\n")
w(row("Temps", "Ce que montre l'open data", "Source publique")); w(row("---", "---", "---"))
w(row("1. Chaque préfecture crée sa démarche", f"{n(CD['temps1_departements_version_locale_creee_avant_la_trame'])} départements en avaient créé une avant la trame nationale", "« en 2023, les trois quarts des préfectures ont utilisé cette plateforme » (instruction du 22 août 2023)"))
w(row("2. Un formulaire commun, cloné par chaque département (campagnes 2024 et 2025)",
      f"trame de la DGCL publiée le {d(CD['trame_dgcl']['publication'])} ; {n(t2['departements'])} départements ont une version qui en reprend les champs, créée avant le 30 juin 2024 dans {n(t2['departements_premiere_version_avant_le_30_juin_2024'])} cas ; "
      f"{n(t2['fermetures_mois_le_plus_frequent'][1])} de ces versions ferment en {MOIS[int(t2['fermetures_mois_le_plus_frequent'][0][5:7]) - 1]} {t2['fermetures_mois_le_plus_frequent'][0][:4]}",
      "trame « obligatoire » pour l'exercice 2024 (instruction du 22 août 2023) ; guichet unique « reconduit pour 2025 et 2026 » (circulaire du 1er avril 2026)"))
w(row("3. Une démarche unique nationale (exercice 2026)",
      f"créée le {d(CD['nationale']['creation'])}, publiée le {d(CD['nationale']['publication'])}, {n(CD['nationale']['dossiers'])} dossiers ; aucune démarche nationale de demande ne la précède",
      "« toutes les nouvelles demandes […] pour l'exercice 2026 » y sont déposées (circulaire du 1er avril 2026, qui renvoie à l'instruction du 17 septembre 2025)"))
w("")
w(f"Les versions locales portent souvent un millésime ({n(DE['famille_de_titres']['avec_millesime_dans_le_titre'])} sur {n(DE['famille_de_titres']['versions_locales'])}) : leur fermeture clôt une campagne et ne mesure pas la consolidation. "
  f"Le signal retenu est une version locale créée après la version nationale. La date de publication du fichier est celle de la dernière publication : {n(rp['versions'])} des {n(dap['versions'])} versions « publiées après » "
  f"sont des démarches plus anciennes, republiées puis closes, et une est un essai. Sur la date de création, le NEPH compterait {n(SD['NEPH']['creation'][1])} départements au lieu de {n(ne['departements_deja_une_locale'])}, "
  f"sa version nationale ayant été créée en {SD['NEPH']['creation'][0][:4]} ; mais {n(SD['NEPH']['fermetures_locales_dans_les_6_mois_apres_publication'])} des {n(SD['NEPH']['fermetures_locales'])} fermetures locales suivent de moins de six mois sa publication de {d(ne['date_nationale'])[2:].strip()}, que la fiche retient.\n")
mt_, mr_, ma_ = CM["travail"], CM["régionale, départementale et communale"], CM["agricole"]
w(f"**Lecture.** Deux chemins mènent au national. Quelques départements, puis le formulaire national : le NEPH ({n(ne['departements_deja_une_locale'])} départements avaient une version locale), "
  f"la médaille d'honneur régionale, départementale et communale ({n(mr_['locales_creees_avant']['departements'])} département) et la médaille d'honneur agricole ({n(ma_['locales_creees_avant']['departements'])} département, plus {n(ma_['locales_creees_avant']['sans_departement'])} versions sans service identifié ; "
  f"{n(ma_['locales_en_ligne_aujourdhui'][0])} versions locales y restent en ligne, dans {n(ma_['locales_en_ligne_aujourdhui'][1])} départements). "
  f"Ou une diffusion presque générale ({n(de['departements_deja_une_locale'])} départements), un formulaire commun à tous les départements, puis le national : la DETR et la DSIL. La médaille d'honneur du travail n'a suivi aucun des deux : elle est nationale d'emblée sur la plateforme. "
  f"Une préfecture a pu numériser une procédure hors de la plateforme.\n")
vb = B["vérification avant embauche"]; fb = B["fondations et fonds de dotation"]; au = CM["autres_dans_le_perimetre"]; js = CM["hors_perimetre"]["jeunesse, sports et engagement associatif"]
w(f"**Les autres cas.** *Fondations et fonds de dotation* (illustration, hors dénominateur) : {n(fb['departements_deja_une_locale'])} département avait une version locale ; la procédure est d'abord nationale. "
  f"*Vérification avant embauche* : {n(V['demarches'])} démarches dans {n(vb['departements'])} départements, aucune version nationale, {n(V['dossiers'])} dossiers dont {n(V['trois_plus_lourdes'])} pour les trois plus lourdes ; "
  f"de {V['pieces_min']} à {V['pieces_max']} pièces distinctes. La compétence est départementale par le texte (code du travail, L. 5221-8, R. 5221-41, R. 5221-42) ; elle n'empêche pas une démarche nationale, "
  "comme celle des médailles qui oriente chaque dossier « en fonction du département ». "
  f"*Médailles restées départementales* (sécurité intérieure, acte de courage et de dévouement, administration territoriale, transports routiers, jeunesse et sports) : {n(au['demarches'])} démarches dans {n(au['departements'])} départements, toutes en ligne, aucune version nationale ; "
  f"celle de la jeunesse, des sports et de l'engagement associatif est surtout déclarée dans d'autres zones ministérielles ({n(js['demarches'])} démarches dans {n(js['departements'])} départements, hors du périmètre).\n")

# 6 ------------------------------------------------------------------------------------------------------------------------
w("## 6. L'instruction branchée\n")
w("**Chapeau.** La plateforme expose une API publique qui permet à un ministère de brancher son propre outil d'instruction. Deux briques sourcées l'illustrent : la Bibliothèque numérique a vocation à être mise en œuvre pour la gestion des fondations, "
  "et Turgot pour la gestion des subventions de l'État aux collectivités, en lien avec la démarche unique nationale de demande de DETR et de DSIL, mise en ligne en octobre 2025, pour l'exercice 2026.\n")
D3 = DE["definition_section3"]; D6 = DE["definition_section6_script37"]
w(row("Brique", "Ce que la source publique établit", "Ce qu'elle n'établit pas", "Volumes de la politique concernée dans l'open data (aucun lien établi avec l'outil)"))
w(row("---", "---", "---", "---"))
w(row("Bibliothèque numérique (dépôt public, Apache 2.0)",
      "complète SVE et la plateforme ; n'écrit rien elle-même, lit 90 % de ses données par l'API ; référentiel des fondations et associations ; fonctions associations à partir de la version 2.25.0 (mars 2025)",
      "mise en service, démarches synchronisées ; les dates du journal sont des dates de version du logiciel",
      f"fondations et fonds de dotation : {fo['demarches']} démarches, {n(fo['dossiers'])} dossiers ; associations : {asso['demarches']} démarches, {n(asso['dossiers'])} dossiers"))
w(row("Turgot (dépôt public, MIT)",
      "lit les démarches et les dossiers par l'API (`src/dn/sync`) ; **prévoit** l'écriture des décisions (passage en instruction, acceptation, refus, classement sans suite, annotations) ; lecture seule pour des partenaires (`src/dn/proxy`) ; "
      "jeu d'essai copié d'une démarche de test qui renvoie à la « démarche unique nationale » DETR-DSIL (13 novembre 2025) et notifications prévues pour cette démarche (décembre 2025), d'après le journal du dépôt",
      "l'usage en production, les démarches couvertes, le ministère porteur",
      f"DETR et DSIL (titres citant la DETR ou la DSIL, même définition que pour l'appropriation) : {n(D3['demarches'])} démarches, {n(D3['dossiers'])} dossiers"))
w("")
w(f"Aucune autre connexion n'est décrite ; aucune source publique ne documente celle des médailles ; aucune IA d'instruction n'est décrite. *Note* : une définition large des dotations d'investissement "
  f"(DETR, DSIL, DSID, DPV, toutes familles) compte {n(D6['demarches'])} démarches et {n(D6['dossiers'])} dossiers.\n")

# 7 ------------------------------------------------------------------------------------------------------------------------
w("## 7. Les étrangers\n")
w("**Chapeau.** Des comptes, des fonctions, des dates. Le canal national du séjour est l'ANEF ; la fiche décrit ce que font les démarches publiées sur la plateforme, par fonction et non par préfecture.\n")
w(row("Fonction (personnes concernées)", "Démarches", "Dossiers", "En ligne", "Publiées avant 5/2021", "5/2021 – 9/2022", "Après 9/2022"))
w(row("---", "---:", "---:", "---:", "---:", "---:", "---:"))
for k, lab in (("dépôt d'une demande", "Dépôt d'une demande"), ("rendez-vous", "Demande de rendez-vous (comptée à part)"), ("contact et renseignement", "Contact et renseignement"), ("complément ou suivi", "Complément ou suivi")):
    v = fn[k]; w(row(lab, n(v["demarches"]), n(v["dossiers"]), n(v["publiees_aujourdhui"]), *(n(ca[k][q_][0]) for q_ in ("avant", "pendant", "après"))))
rp = fn["dépôt d'une demande"]["dont_recepisses_prolongations"]
w("")
w(f"Dont, au dépôt, {n(rp[0])} démarches de récépissés et d'attestations de prolongation ({n(rp[1])} dossiers). Les trois dernières colonnes comptent les démarches publiées dans chaque période ; ces périodes suivent la seule source officielle retenue, l'arrêté du 27 avril 2021 (article R. 431-2 du CESEDA), "
  "qui rend le téléservice obligatoire par étapes du 1er mai 2021 au 28 septembre 2022 : des dates d'obligation, pas d'ouverture du service.\n")
ha, ci = ET["titres_hors_anef"], ET["titres_citant_anef"]
w(f"**Lecture.** {ci['demarches']} titres citent l'ANEF, dont {MC['etrangers_calendrier_arrete']['citant_anef_apres']} publiés après le 28 septembre 2022, surtout des compléments ; {ha['demarches']} disent « hors ANEF ». "
  f"Relais, complément ou voie parallèle : **la fiche pose la question, sans y répondre.** Les {n(fn['rendez-vous']['demarches'])} démarches de rendez-vous servent d'agenda ; la brique RDV Service Public, décrite dans la [fiche Justice](https://emsnytech.github.io/form2026/fiches-ministeres/justice.html#acces-droit), "
  f"pourrait-elle porter cet usage ? {n(ET['niveau']['locale'][0])} des {n(ET['total'][0])} démarches sont locales ; aucune préfecture n'est nommée.\n")

# 8 ------------------------------------------------------------------------------------------------------------------------
w("## 8. Les services propres du ministère\n")
po, ac = CS["police et gendarmerie"], CS["administration centrale"]
w(row("Famille (périmètre entier)", "Police, gendarmerie", "Dossiers", "Admin. centrale", "Dossiers")); w(row("---", "---:", "---:", "---:", "---:"))
for f in ("RH et action sociale", "polices administratives", "permis et auto-écoles", "dotations et aides", "étrangers", "élections", "autres"):
    a_, b_ = po["par_famille"].get(f, [0, 0]), ac["par_famille"].get(f, [0, 0])
    w(row(cap(f), n(a_[0]), n(a_[1]), n(b_[0]), n(b_[1])))
w(row("**Total**", n(po["demarches"]), n(po["dossiers"]), n(ac["demarches"]), n(ac["dossiers"])))
w("")
w(f"**Phrase-clé.** La police et la gendarmerie publient surtout pour leurs agents : RH et action sociale font {p(po['part_rh_dossiers'])} de leurs dossiers, et {n(po['autres_dont_internes'][0])} des {n(po['hors_rh'][0])} démarches restantes relèvent de la vie interne des écoles et des services ; l'administration centrale doit son volume à quelques démarches nationales, dont le NEPH ({n(pac[1])} dossiers). "
  "La préfecture de police est comptée avec les préfectures.\n")

# 9 ------------------------------------------------------------------------------------------------------------------------
w("## 9. Qui instruit quoi\n")
Bq = QI["base"]
w(row(f"Instructeur (base : zone déclarée, publiées depuis le 7 octobre 2022 ; {n(Bq['demarches'])} démarches)", "Démarches", "Dossiers")); w(row("---", "---:", "---:"))
for k, v in sorted(ins.items(), key=lambda x: -x[1][1]): w(row(cap(k), n(v[0]), n(v[1])))
w("")
w(f"**Phrase-clé.** Les préfectures instruisent l'essentiel ; la divergence est visible pour le permis de conduire, dont {n(permis[DDx][0])} démarches sont instruites par des directions d'autres ministères, "
  f"et pour le logement, instruit surtout, en dossiers, par les directions départementales ({n(logt[DDx][1])} contre {n(logt['préfecture ou sous-préfecture'][1])}). Sur cette base, la police et la gendarmerie comptent {n(ins[POLx][0])} démarches "
  f"(contre {n(po['demarches'])} sur le périmètre entier, dans le tableau des services propres).\n")

# 10 -----------------------------------------------------------------------------------------------------------------------
w("## 10. Limites et méthode\n")
for t in (
    "Familles classées sur le titre ; vérification avant embauche à part, jamais ajoutée aux étrangers ; démarche n° 74335 rattachée à la vérification, n° 100682 laissée aux tiers.",
    f"Départements : d'après l'organisme, le service et le titre ; à défaut, champ département ({n(RT['par_source'].get('champ', 0))} démarches, dont {n(SC['demarches_retirees'])} de préfecture). Sans ces dernières, la médiane passe de {n(q['mediane'])} à "
    f"{n(SC['demarches_par_departement']['mediane'])} démarches et de {n(qo['mediane'])} à {n(SC['en_ligne_par_departement']['mediane'])} en ligne ; la répartition par familles couvertes change au plus de {ecart} départements par classe : l'écart est faible.",
    "Réglementations uniformes : définitions par mots du titre, choisies après lecture. Population : INSEE, populations de référence 2023, fichier d'ensemble publié le 18 décembre 2025, versé au dépôt (il ne couvre pas un département d'outre-mer).",
    f"Démarches d'essai conservées ({n(CP['tests']['demarches'])}). Pièces comptées sur libellés distincts. Aucune donnée de contact, aucun département nommé.",
    "Règles et scripts détaillés : dépôt, `donnees/fiches-ministeres/methode/`.",
    "Sources : descriptif ouvert (data.gouv.fr) ; code du travail ; décrets n° 84-591 et n° 84-1110 ; arrêté du 27 avril 2021 ; instruction du 22 août 2023 et circulaire du 1er avril 2026 sur la DETR et la DSIL (Légifrance) ; INSEE ; tableau de bord public de ProConnect (export du 15 novembre 2026, versé au dépôt) ; « ProConnect – Présentation de la solution » (pad.numerique.gouv.fr, non daté, consulté le 15 novembre 2026), pour Passage2 (ministère de l'Intérieur) et Cerbère (ministère de la Transition écologique) ; « Charte des usages éthiques de l'IA au ministère de l'Intérieur », publiée par la CFDT Interco (mars 2026), pour MirAI, « portail interne » développé par la DTNUM et « exploitée sur des infrastructures maîtrisées par le ministère » ; documentation de Maarch Courrier 18.10 ; "
    f"SVE et Démarche Numérique, {CONSULT} (étape 1 de SVE : 16 novembre 2026) ; dépôts publics de la Bibliothèque numérique et de Turgot.",
): w(f"- {t}")
w("")

md = "\n".join(L)
assert not re.search(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", md), "adresse électronique"
assert not re.search(r"(?<!\d)(\+33|0)[1-9](?:[\s.\-]?\d{2}){4}(?!\d)", md), "numéro de téléphone"
plain = unicodedata.normalize("NFKD", md).encode("ascii", "ignore").decode().lower()
nommes = [v for v in json.load(open("scripts/departements.json")).values() if re.search(r"(?<![a-z-])" + re.escape(v).replace(r"\-", "[- ]") + r"(?![a-z-])", plain)]
assert not nommes, f"département nommé : {nommes}"
Path("out/maquette_interieur.md").write_text(md)
print(md)
print("\n[mots]", len(re.findall(r"\w+", md)))
