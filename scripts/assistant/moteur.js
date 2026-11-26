// Moteur de recherche local (BM25) sur l'index FORM 2026 + DILA.
// Utilisable dans la page et sous node pour les tests.
(function (root) {
  const STOP = new Set(("a au aux avec ce ces dans de des du elle en et eux il je la le les leur lui ma mais me meme mes moi mon ne nos notre nous on ou par pas pour qu que qui sa se ses son sur ta te tes toi ton tu un une vos votre vous c d j l m n s t y ete etre avoir ai as avons avez ont suis es est sommes etes sont faire fait comment quoi quel quelle quels quelles dois doit veux veut voudrais souhaite souhaiterais besoin peux peut faut il ya y-a cela ca cet cette tout tous toute toutes plus moins tres aussi si alors donc car comme chez sans sous entre vers apres avant depuis lors quand ou bien mon ma mes demande demarche demarches demander habite habiter habitons habitez pendant existe exister possible possibles").split(" "));
  const DEGRADATIONS = ["degradation", "dommage", "_troubles_urbains", "_dommages_subis"];
  const SYN = {
    chercher: ["rechercher"], cherche: ["rechercher"], examen: ["examen", "epreuve"],
    simulateur: ["simulateur", "estimer", "calculer", "verifier"], simulation: ["simulateur", "estimer", "calculer", "verifier"], simuler: ["simulateur", "estimer", "calculer", "verifier"],
    bebe: ["naissance"], enfant: ["enfant"], boulot: ["emploi"], travail: ["emploi", "travail"], chomage: ["emploi", "chomage", "inscription"],
    demenage: ["demenagement", "adresse"], demenager: ["demenagement", "adresse"], aide: ["aide", "subvention", "allocation"], allocation: ["allocation", "aide"], allocations: ["allocation", "aide"], indemnisation: ["indemnisation", "indemnite"], indemniser: ["indemnisation", "indemnite"],
    argent: ["aide", "subvention", "financement"], asso: ["association"], boite: ["entreprise"], societe: ["entreprise"],
    voiture: ["vehicule", "immatriculation"], auto: ["vehicule"], carte: ["carte"], fete: ["manifestation"], brocante: ["vide", "grenier", "manifestation"],
    handicap: ["handicap"], logement: ["logement"], ecole: ["scolaire", "scolarisation", "ecole"], fac: ["universite", "etudes"],
    etranger: ["etranger", "sejour"], cree: ["creation"], creer: ["creation"], monter: ["creation"], adapter: ["adaptation", "amenagement"],
    perdu: ["perte"], perdue: ["perte"], vole: ["vol"], volee: ["vol"], retraite: ["retraite"], deces: ["deces"], mariage: ["mariage"], chasse: ["chasse", "tir"],
    // rue ↔ voie, voie publique, route, chaussée (dans les deux sens)
    rue: ["voie", "route", "chaussee"], voie: ["rue"], route: ["rue"], chaussee: ["rue"],
    // Langage courant → langage administratif (consigne « améliorations du moteur »), par groupes.
    dette: ["impaye", "paiement"],                                                                   // impayés
    electricite: ["energie"], gaz: ["energie"], chauffage: ["energie"], fioul: ["energie"],          // énergie
    agriculteur: ["agricole", "exploitation", "agriculture", "filiere"], exploitant: ["agricole", "exploitation", "agriculture", "filiere"],
    eleveur: ["agricole", "exploitation", "agriculture", "filiere"], viticulteur: ["agricole", "exploitation", "agriculture", "filiere"],
    maraicher: ["agricole", "exploitation", "agriculture", "filiere"],                               // agriculture
    // Crises : « calamité » et l'expression « fonds d'urgence » (jeton _fonds_d_urgence), jamais « urgence » seul, qui
    // ferait remonter les fonds de relogement d'urgence.
    secheresse: ["calamite", "_fonds_d_urgence"], gel: ["calamite", "_fonds_d_urgence"], grele: ["calamite", "_fonds_d_urgence"],
    inondation: ["calamite", "_fonds_d_urgence"], tempete: ["calamite", "_fonds_d_urgence"], intemperies: ["calamite", "_fonds_d_urgence"], // crises
    // Dégradations : « manifestation » n'est jamais un déclencheur seul (une fête, une brocante) ; seulement les expressions
    // « pendant / lors des / en marge des manifestations ». Pas d'« indemnisation » (fiches sur le chômage) : « troubles
    // urbains » et « dommages subis » (jetons d'expression).
    degradation: DEGRADATIONS, pillage: DEGRADATIONS, vandalisme: DEGRADATIONS, emeute: DEGRADATIONS, emeutes: DEGRADATIONS,
    // restaurant ↔ commerce ; « bar » jamais seul (voir EXPRESSIONS : bar restaurant, bar-tabac, café-bar).
    restaurant: ["commerce"], restaurants: ["commerce"],
    // passeport seul : la démarche pour l'obtenir (pré-demande en ligne, ANTS), devant le suivi ou la réception
    passeport: ["_pre_demande"], passeports: ["_pre_demande"],
    refaire: ["renouvellement"],
    payer: ["paiement"], paye: ["paiement"],
    // un enfant : la fiche « mineur » (carte d'identité, passeport…) ; voir aussi ageInadapte
    fils: ["mineur"], fille: ["mineur"],
  };
  // Expressions de plusieurs mots, reconnues avant le découpage en mots (sur le texte normalisé).
  const EXPRESSIONS = [
    [["n arrive plus a payer", "arrive plus a payer", "ne peux plus payer", "ne peut plus payer", "ne pouvons plus payer", "retard de paiement",
      "facture impayee", "factures impayees"], ["impaye", "paiement"]],
    [["fonds d urgence"], ["calamite", "_fonds_d_urgence"]],
    [["vitrine cassee", "vitrine brisee", "vitrine a ete cassee", "vitrines cassees", "vitre cassee"], DEGRADATIONS],
    [["pendant les manifestations", "lors des manifestations", "en marge des manifestations"], DEGRADATIONS],
    // émeutes ↔ troubles urbains (jeton _troubles_urbains, voir JETONS_EXPRESSION)
    [["troubles urbains"], [...DEGRADATIONS, "emeute"]],
    [["bar restaurant", "bar tabac", "cafe bar"], ["commerce", "restaurant"]],
    [["verifier le titre de sejour", "verifier son titre de sejour", "verifier un titre de sejour", "verifier les titres de sejour",
      "salarie etranger", "salaries etrangers", "embaucher un etranger", "embaucher un salarie etranger", "embaucher des etrangers"],
     ["verification", "prealable", "embauche", "autorisation", "travail"]],
    // Carte grise : nom courant du certificat d'immatriculation (titre des fiches et de la démarche de l'ANTS).
    [["carte grise", "cartes grises"], ["_carte_grise"]],
    // Carte grise perdue ou volée : on la refait en ligne (« Refaire son certificat d'immatriculation… en cas de perte, vol »).
    [["carte grise perdue", "carte grise perdu", "carte grise volee", "carte grise vole", "perdu ma carte grise", "perdu sa carte grise",
      "perte de carte grise", "perte de la carte grise", "perte de ma carte grise", "vol de carte grise", "vol de ma carte grise"], ["_carte_grise", "refaire", "perte", "vol"]],
    // Liste électorale : une expression (inscription sur les listes électorales), pas les mots « liste » et « électorale » isolés.
    [["liste electorale", "listes electorales", "liste electoral", "listes electorale", "listes electoraux"], ["liste", "electorale"]],
    // Carte d'identité : son jeton ; seule dans la question, la pré-demande en ligne aussi (comme « passeport » seul).
    [["carte d identite", "carte identite", "cartes d identite", "carte nationale d identite"], ["_cni"], { seul: ["_pre_demande"] }],
    // Mots courants → vocabulaire des fiches : l'attestation de droits (« attestation Vitale »), la déclaration de naissance.
    [["attestation de securite sociale", "attestation securite sociale", "attestation secu", "attestation de secu", "attestation vitale",
      "attestation carte vitale", "attestation d assurance maladie", "attestation assurance maladie"], ["_attestation_droits"]],
    [["naissance enfant", "naissance d un enfant", "naissance de mon enfant", "naissance de notre enfant", "naissance de mon bebe", "mon bebe est ne",
      "vient de naitre", "declarer une naissance", "declarer la naissance"], ["_declaration_naissance", "naissance"], { sansSyn: true }],
    [["logement social", "logements sociaux"], ["_logement_social"]],
    [["service fait", "services faits"], ["_service_fait"]],
    // mots courants → nom de la prestation (les sigles sont dans sigles.json)
    [["mutuelle gratuite", "mutuelle solidaire"], ["complementaire", "sante", "solidaire"], { remplace: true }],
    [["aide menagere", "aides menageres", "femme de menage", "menage a domicile"], ["domicile", "emploi"], { remplace: true }],
    // « aide au logement » seule : l'APL, l'ALF et l'ALS se demandent par un même service en ligne, qui les nomme par leur sigle.
    [["aide au logement", "aides au logement", "aide logement", "aides logement", "allocation logement", "allocations logement",
      "allocation de logement", "allocations de logement", "allocation au logement"], ["logement"], { seul: ["apl"] }],
    [["payer impot", "payer impots", "payer mes impots", "payer ses impots", "payer l impot", "payer mon impot", "paiement impot", "paiement des impots",
      "paiement de l impot", "regler mes impots", "regler ses impots"], ["_paiement_impot"]],
    // « décès » seul : d'abord la déclaration de décès.
    [["deces"], ["deces"], { seul: ["declaration"] }],
    // « procuration » seule : d'abord le vote par procuration.
    [["procuration", "procurations"], ["procuration"], { seul: ["vote", "voter"] }],
    // Passeport talent : un titre de séjour, pas un passeport.
    [["passeport talent", "passeports talent"], ["talent"], { sansSyn: true }],
    // Passeport : obtenir un passeport (pré-demande d'un 1er passeport, ANTS) ; le refaire (pré-demande de renouvellement).
    [["faire un passeport", "faire mon passeport", "faire faire un passeport", "demander un passeport", "demande de passeport", "obtenir un passeport",
      "premier passeport", "1er passeport", "nouveau passeport"], ["_pre_demande", "1er", "passeport"]],
    [["refaire mon passeport", "refaire son passeport", "refaire un passeport", "refaire le passeport", "renouveler mon passeport", "renouveler son passeport",
      "renouveler un passeport", "renouvellement de passeport", "renouvellement du passeport", "renouvellement passeport", "passeport perime", "passeport expire"],
     ["renouvellement", "_pre_demande", "passeport"]],
    // Renouveler son titre de séjour : la démarche se fait auprès du bureau des étrangers, souvent sur rendez-vous.
    [["renouveler mon titre de sejour", "renouveler son titre de sejour", "renouveler le titre de sejour", "renouveler ma carte de sejour",
      "renouvellement de mon titre de sejour", "renouvellement du titre de sejour", "renouvellement de titre de sejour"],
     ["renouvellement", "etrangers", "rendez"]],
  ].flatMap(([formes, vers, o]) => formes.map((f) => [f, vers, o]));
  function norm(s) {
    return (s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]+/g, " ").trim();
  }
  // Jetons d'expression : indexés quand l'expression figure dans un texte, cherchés par les synonymes (« _… », sans racinisation).
  const JETONS_EXPRESSION = [["fonds d urgence", "_fonds_d_urgence"], ["troubles urbains", "_troubles_urbains"], ["dommages subis", "_dommages_subis"],
    // carte grise = certificat d'immatriculation : un même jeton, quel que soit le nom employé par la fiche
    ["carte grise", "_carte_grise"], ["cartes grises", "_carte_grise"], ["certificat d immatriculation", "_carte_grise"], ["certificats d immatriculation", "_carte_grise"],
    // pré-demande en ligne (passeport, carte d'identité) : un jeton, cherché par le synonyme de « passeport »
    ["pre demande", "_pre_demande"], ["attestation de droits", "_attestation_droits"], ["declaration de naissance", "_declaration_naissance"],
    ["service fait", "_service_fait"], ["services faits", "_service_fait"],
    ["logement social", "_logement_social"], ["logements sociaux", "_logement_social"],
    ["paiement de l impot", "_paiement_impot"], ["paiement des impots", "_paiement_impot"], ["payer ses impots", "_paiement_impot"], ["payer l impot", "_paiement_impot"],
    // carte d'identité : un jeton propre (la racine « identi » est aussi celle d'« identification »)
    ["carte d identite", "_cni"], ["cartes d identite", "_cni"], ["carte nationale d identite", "_cni"]];
  // Racines : deux mots se rapprochent seulement si l'un est une forme de l'autre (pluriel, féminin, conjugaison) ou en dérive
  // par un suffixe courant (-ation, -ement, -ité, -ique…). On retire la terminaison, on ne coupe plus à longueur fixe : « maternité »
  // (matern) ≠ « maternelle » (maternel), « licenciement » (licenci) ≠ « licence » (licenc), « procuration » ≠ « procureur »,
  // « électricité » (l'énergie) ≠ « électrique » (une voiture électrique).
  // Terminaisons essayées de la plus longue à la plus courte ; la première qui laisse une racine assez longue est retirée
  // (5 lettres au moins pour un suffixe de dérivation : « cassée » ≠ « cassation »).
  const SUFFIXES = [["issements", 5], ["issement", 5], ["ements", 5], ["ement", 5], ["ataires", 5], ["ataire", 5], ["ations", 5],
    ["ation", 5], ["itions", 5], ["ition", 5], ["utions", 5], ["ution", 5], ["ptions", 5], ["ption", 5], ["ances", 5], ["ance", 5],
    ["ences", 5], ["ence", 5], ["ites", 5], ["ite", 5], ["ables", 5], ["able", 5], ["istes", 5], ["iste", 5], ["ismes", 5], ["isme", 5],
    ["ages", 5], ["age", 5], ["antes", 4], ["ante", 4], ["ants", 4], ["ant", 4], ["erons", 3], ["eront", 3], ["erait", 3], ["erai", 3],
    ["ions", 4], ["iez", 3], ["ees", 3], ["ee", 3], ["er", 3], ["ez", 3], ["es", 3], ["e", 3]];
  function stem(w) {
    if (w[0] === "_") return w;
    if (/^\d+(e|eme|er|ere|ieme)$/.test(w)) return w.replace(/\D+$/, "e");   // 3e, 3eme, 3ème : un seul terme
    if (w.length > 4) w = w.replace(/aux$/, "al").replace(/(s|x)$/, "");
    w = w.replace(/elle$/, "el").replace(/enne$/, "en").replace(/([ts])ive$/, "$1if").replace(/([^a])ire$/, "$1i").replace(/ication$/, "i");
    for (const [x, min] of SUFFIXES) if (w.endsWith(x) && w.length - x.length >= min) { w = w.slice(0, -x.length); break; }
    return w.length > 4 ? w.replace(/([^aeiouy])\1$/, "$1") : w;
  }
  function toks(s) {
    const out = [];
    for (const w of norm(s).split(" ")) if (w.length > 1 && !STOP.has(w)) out.push(stem(w));
    return out;
  }
  // ---------- Lieux dans la question
  // Communes (donnees/assistant/communes.json), chargées par la page ou les tests avec chargerCommunes(). Un lieu n'est
  // reconnu qu'après un marqueur (« à », « j'habite », « près de », « sur », « dans ») ou en fin de phrase, et jamais pour
  // un nom de commune qui est aussi un mot courant (liste NON_LIEUX, tirée des noms de communes fréquents dans l'index).
  const NON_LIEUX = new Set(("ligne son dun charge place plan cours vue campagne ars contre ecole mars ville villes y avril frais grand vers " +
    "relevant lance centres simple maire change degre vert fins celle celles cultures port long routier parent jury issus lue moyen lies " +
    "corps armes champs rue sens bar eu ham mer orange marche pont mont val salles bourg loire bretagne saone azur mai aide aides plus pres " +
    "nord sud est ouest centre beaucoup " +
    // relevés dans les titres de démarches (règle « lieu dans le titre ») : mots courants qui sont aussi des communes
    "aire aires courtes maille plaisance bonne bonnes salon maisons segur sus hommes gilles bio jardin pia job titre table " +
    "marsa tarentaise cerbere courant ports services region formation formations reunion").split(" "));
  // Noms de département (normalisés) : à leur place, aucune commune homonyme ou plus courte n'est reconnue (« dans les Landes »
  // n'est pas Landes en Charente-Maritime, « le Pas-de-Calais » n'est pas Le Pas en Mayenne). Article initial ignoré.
  // Noms de région : réservés aussi (« Centre-Val de Loire » ne désigne ni la Loire ni une commune).
  const NOMS_REGIONS = new Set("auvergne rhone alpes|bourgogne franche comte|centre val de loire|grand est|hauts de france|ile de france|nouvelle aquitaine|occitanie|pays de la loire|pays de loire|provence alpes cote d azur|region sud|normandie|bretagne".split("|"));
  const NOMS_DEPARTEMENTS = new Set("ain|aisne|allier|alpes de haute provence|hautes alpes|alpes maritimes|ardeche|ardennes|ariege|aube|aude|aveyron|bouches du rhone|calvados|cantal|charente|charente maritime|cher|correze|corse du sud|haute corse|cote d or|cotes d armor|creuse|dordogne|doubs|drome|eure|eure et loir|finistere|gard|haute garonne|gers|gironde|herault|ille et vilaine|indre|indre et loire|isere|jura|landes|loir et cher|loire|haute loire|loire atlantique|loiret|lot|lot et garonne|lozere|maine et loire|manche|marne|haute marne|mayenne|meurthe et moselle|meuse|morbihan|moselle|nievre|nord|oise|orne|pas de calais|puy de dome|pyrenees atlantiques|hautes pyrenees|pyrenees orientales|bas rhin|haut rhin|rhone|haute saone|saone et loire|sarthe|savoie|haute savoie|seine maritime|seine et marne|yvelines|deux sevres|somme|tarn|tarn et garonne|var|vaucluse|vendee|vienne|haute vienne|vosges|yonne|territoire de belfort|essonne|hauts de seine|seine saint denis|val de marne|val d oise|guadeloupe|martinique|guyane|la reunion|mayotte".split("|"));
  const MARQUEURS = [["j", "habite"], ["habite"], ["a"], ["pres", "de"], ["sur"], ["dans"]];
  // Régions (18) : nom normalisé et formes courantes → libellé et départements. Reconnues après « en », « dans la région »,
  // « région » ; la page propose alors une pastille, et un clic filtre sur tous les départements de la région.
  const REGIONS = [
    ["Auvergne-Rhône-Alpes", ["auvergne rhone alpes"], "01,03,07,15,26,38,42,43,63,69,73,74"],
    ["Bourgogne-Franche-Comté", ["bourgogne franche comte"], "21,25,39,58,70,71,89,90"],
    ["Bretagne", ["bretagne"], "22,29,35,56"],
    ["Centre-Val de Loire", ["centre val de loire"], "18,28,36,37,41,45"],
    ["Corse", ["corse"], "2A,2B"],
    ["Grand Est", ["grand est"], "08,10,51,52,54,55,57,67,68,88"],
    ["Hauts-de-France", ["hauts de france"], "02,59,60,62,80"],
    ["Île-de-France", ["ile de france", "idf"], "75,77,78,91,92,93,94,95"],
    ["Normandie", ["normandie"], "14,27,50,61,76"],
    ["Nouvelle-Aquitaine", ["nouvelle aquitaine"], "16,17,19,23,24,33,40,47,64,79,86,87"],
    ["Occitanie", ["occitanie"], "09,11,12,30,31,32,34,46,48,65,66,81,82"],
    ["Pays de la Loire", ["pays de la loire"], "44,49,53,72,85"],
    ["Provence-Alpes-Côte d'Azur", ["provence alpes cote d azur", "paca", "sud"], "04,05,06,13,83,84"],
    ["Guadeloupe", ["guadeloupe"], "971"], ["Martinique", ["martinique"], "972"], ["Guyane", ["guyane"], "973"],
    ["La Réunion", ["la reunion", "reunion"], "974"], ["Mayotte", ["mayotte"], "976"],
  ].map(([nom, formes, deps]) => ({ nom, formes, deps: deps.split(",") }));   // codes séparés par des virgules (une suite de codes à deux chiffres ressemblerait à un numéro de téléphone)
  const MARQUEURS_REGION = [["dans", "la", "region"], ["en", "region"], ["region"], ["en"], ["a", "la"]];
  function regions(w) {
    const out = [];
    MARQUEURS_REGION.forEach((m) => { for (let i = 0; i + m.length < w.length; i++) if (m.every((x, j) => w[i + j] === x)) {
      const reste = w.slice(i + m.length, i + m.length + 5).join(" ") + " ";
      for (const R of REGIONS) for (const f of R.formes) {
        // « sud » seul n'est une région qu'après « région » (« Région Sud ») ; « La Réunion » demande « à la » ou « en ».
        if (f === "sud" && m[m.length - 1] !== "region") continue;
        if (m[0] === "a" && f !== "reunion") continue;
        if (reste.startsWith(f + " ") && !out.some((o) => o.nom === R.nom)) out.push({ nom: R.nom, deps: R.deps, mots: [...m, ...f.split(" ")] });
      }
    } });
    return out;
  }
  let COMMUNES = null;
  function chargerCommunes(d) {
    COMMUNES = new Map(); const C = Object.fromEntries(d.champs.map((k, i) => [k, i]));
    for (const c of d.communes) {
      const n = c[C.nom_normalise]; if (!COMMUNES.has(n)) COMMUNES.set(n, []);
      COMMUNES.get(n).push({ nom: c[C.nom], code: c[C.code], dep: c[C.departement], pop: c[C.population] });
    }
    for (const l of COMMUNES.values()) l.sort((a, b) => b.pop - a.pop);
  }
  function lieux(q) {
    const w = norm(q).split(" ").filter(Boolean), out = [], pris = new Set();
    if (!COMMUNES || !w.length) return { lieux: out, regions: [], mots: new Set() };
    // Les mots d'un nom de département sont réservés : ni commune homonyme, ni commune contenue (« Calais » dans « Pas-de-Calais »).
    for (let i = 0; i < w.length; i++) for (let n = Math.min(5, w.length - i); n >= 1; n--) {
      const s = w.slice(i, i + n), art = ["le", "la", "les", "l"].includes(s[0]) && n > 1;
      const reserve = (x) => NOMS_DEPARTEMENTS.has(x) || NOMS_REGIONS.has(x);
      if (reserve(s.join(" ")) || (art && reserve(s.slice(1).join(" ")))) { for (let k = i; k < i + n; k++) pris.add(k); i += n - 1; break; }
    }
    const essai = (i, prio) => {
      if (pris.has(i)) return;
      for (let n = Math.min(5, w.length - i); n >= 1; n--) {
        const nom = w.slice(i, i + n).join(" ");
        const sansArticle = /^(le|la|les|l) /.test(nom) ? nom.replace(/^\S+ /, "") : "";
        if (COMMUNES.has(nom) && !NON_LIEUX.has(nom) && !NON_LIEUX.has(sansArticle) && !STOP.has(nom) && nom.length >= 3 && ![...Array(n).keys()].some((k) => pris.has(i + k))) {
          for (let k = i; k < i + n; k++) pris.add(k);
          out.push({ prio, pos: i, mots: w.slice(i, i + n), candidats: COMMUNES.get(nom).slice(0, 2) }); return;
        }
      }
    };
    MARQUEURS.forEach((m, prio) => { for (let i = 0; i + m.length < w.length; i++) if (m.every((x, j) => w[i + j] === x)) {
      const avant = out.length; essai(i + m.length, prio);
      if (out.length > avant) out[out.length - 1].marqueur = m;   // « j'habite », « près de » : ils ne servent qu'à introduire le lieu
    } });
    for (let n = Math.min(5, w.length); n >= 1; n--) { const i = w.length - n; if (!pris.has(i)) { const avant = out.length; essai(i, MARQUEURS.length); if (out.length > avant) break; } }
    out.sort((a, b) => a.prio - b.prio || a.pos - b.pos);
    const R = regions(w);
    const mots = new Set([...out.flatMap((l) => [...l.mots, ...(l.marqueur || [])]), ...R.flatMap((r) => r.mots.filter((x) => !STOP.has(x)))]);
    return { lieux: out.map((l) => ({ ...l.candidats[0], candidats: l.candidats, mots: l.mots })), regions: R, mots };
  }

  // Analyse d'une question : termes significatifs (racine → racines retenues, synonymes et expressions compris), hors
  // mots vides et hors mots reconnus comme lieu.
  // Groupes de termes nés d'une expression reconnue (Moteur.analyse) : la règle « démarche sûre » les compte double.
  const EXPR_GROUPES = new WeakSet();
  function analyse(s) {
    let n = " " + norm(s) + " ";

    const termes = new Map(), L = lieux(s);
    // Une expression reconnue compte pour un terme ; plusieurs expressions de même sens, pour un seul.
    // Expression marquée « sansSyn » : ses mots gardent leur terme, sans leurs synonymes (« passeport talent » n'appelle pas la
    // pré-demande de passeport).
    const dansExpr = new Set();
    // Option « remplace » : les mots de l'expression (sigle, mot courant) ne comptent plus à part, l'expression les traduit.
    const remplaces = new Set();
    // Sigles : un terme par sigle (jeton de son sens retenu, et le sigle s'il n'a qu'un sens).
    if (SIGLES) for (const w of n.trim().split(" ")) { const sens = sensSigle(w, n); if (!sens) continue;
      const e = SIGLES[w], g = new Set([jetonSens(sens), ...((e.contextes || []).length ? [] : [w])]);
      EXPR_GROUPES.add(g); termes.set("« " + sens + " »", g); remplaces.add(w); }
    // Option « seul » : termes ajoutés seulement quand la question se réduit à l'expression (hors mots vides).
    const utiles = n.trim().split(" ").filter((w) => w.length > 1 && !STOP.has(w)).join(" ");
    for (const [f, vers, o] of EXPRESSIONS) if (n.includes(" " + f + " ")) {
      const g = new Set(vers.concat(o && o.seul && utiles === f.split(" ").filter((w) => w.length > 1 && !STOP.has(w)).join(" ") ? o.seul : []).map(stem));
      EXPR_GROUPES.add(g); termes.set("« " + vers.join(" ") + " »", g); if (o && o.sansSyn) f.split(" ").forEach((w) => dansExpr.add(w));
      if (o && o.remplace) f.split(" ").forEach((w) => remplaces.add(w)); }
    for (const w of n.trim().split(" ")) {
      if (w.length < 2 || STOP.has(w) || L.mots.has(w) || remplaces.has(w)) continue;
      const t = stem(w); if (!termes.has(t)) termes.set(t, new Set([t]));
      if (!dansExpr.has(w)) for (const x of SYN[w] || []) termes.get(t).add(stem(x));

    }
    return { termes, lieux: L.lieux };
  }
  function queryToks(s) {
    return [...new Set([...analyse(s).termes.values()].flatMap((g) => [...g]))];
  }
  const ANNEE = new Date().getFullYear();
  const EV_LABEL = (ev) => (ev && ev !== "hors_perimetre" ? ev.replace(/_/g, " ") : "");

  const MODELES = /\b(DINUM|DINSIC)\b/;
  // Démarches locales de même titre qu'une démarche nationale (règle « nationale devant ») : index des locales.
  function jumellesDe(ix, r) {
    const i = ix.byId.get(r && r.id); if (i === undefined || !ix.jumelles) return [];
    const out = []; for (const [l, n] of ix.jumelles) if (n === i) out.push(l); return out;
  }
  // ---------- Tolérance aux fautes (recherche simple) : un mot inconnu de l'index, hors lieux et mots vides, est rapproché du
  // mot connu le plus proche (distance d'édition 1, ou 2 à partir de 8 lettres ; voir « cout »). Vocabulaire :
  // les mots des titres et descriptions de l'index, des expressions et des synonymes, avec leur forme écrite la plus courante.
  let VOCAB = null, VOCAB_LONG = null, RECS_VOCAB = null; const MOT = /[A-Za-zÀ-ÖØ-öø-ÿœŒ]{3,}/g;
  function vocabulaire(recs) {
    const c = new Map(), ajout = (w, n = 1) => { const k = norm(w); if (k.length < 3 || /\d/.test(k)) return;
      let e = c.get(k); if (!e) c.set(k, e = { n: 0, formes: new Map() }); e.n += n; const f = w.toLowerCase(); e.formes.set(f, (e.formes.get(f) || 0) + n); };
    for (const r of recs) for (const s of [r.t, r.d]) if (s) for (const w of s.match(MOT) || []) ajout(w);
    for (const [f, vers] of EXPRESSIONS) for (const w of f.split(" ").concat(vers)) ajout(w, 2);
    for (const [k, v] of Object.entries(SYN)) for (const w of [k, ...v]) ajout(w, 2);
    VOCAB = new Map(); VOCAB_LONG = new Map();
    for (const [k, e] of c) { if (e.n < 2) continue; const forme = [...e.formes].sort((a, b) => b[1] - a[1])[0][0];
      VOCAB.set(k, { n: e.n, forme }); if (!VOCAB_LONG.has(k.length)) VOCAB_LONG.set(k.length, []); VOCAB_LONG.get(k.length).push(k); }
  }
  // Lettre oubliée ou en trop : 1. Lettre remplacée : 1 entre lettres qui se confondent à l'oreille (s, c, t, z, x ; i, y ;
  // c, k, q ; m, n ; g, j ; e, a), 2 sinon, et 2 pour la dernière lettre (terminaison) : « tiens » ne devient ni « tiers » ni « tient », « foot » ne devient pas « font ».
  const SONS = ["sctzx", "iy", "ckq", "mn", "gj", "ea"];
  const cout = (x, y) => x === y ? 0 : SONS.some((g) => g.includes(x) && g.includes(y)) ? 1 : 2;
  function distance(a, b, max) {
    if (Math.abs(a.length - b.length) > max) return max + 1;
    let prec = Array.from({ length: b.length + 1 }, (_, j) => j);
    for (let i = 1; i <= a.length; i++) {
      const cur = [i]; let min = i;
      for (let j = 1; j <= b.length; j++) { cur[j] = Math.min(prec[j] + 1, cur[j - 1] + 1, prec[j - 1] + (i === a.length && j === b.length && a[i - 1] !== b[j - 1] ? 2 : cout(a[i - 1], b[j - 1]))); if (cur[j] < min) min = cur[j]; }
      if (min > max) return max + 1; prec = cur;
    }
    return prec[b.length];
  }
  function corriger(q) {
    const corrections = []; if (!VOCAB && RECS_VOCAB) vocabulaire(RECS_VOCAB); if (!VOCAB) return { texte: q, corrections };
    const L = lieux(q);
    const texte = (q || "").replace(/[A-Za-zÀ-ÖØ-öø-ÿœŒ]+/g, (w) => {
      const n = norm(w);
      if (n.length < 4 || VOCAB.has(n) || STOP.has(n) || SYN[n] || (SIGLES && SIGLES[n]) || L.mots.has(n) || (COMMUNES && COMMUNES.has(n))) return w;
      const max = n.length >= 8 ? 2 : 1; let best = null;
      for (let l = n.length - max; l <= n.length + max; l++) for (const k of VOCAB_LONG.get(l) || []) {
        const d = distance(n, k, max); if (d > max) continue;
        // à égalité de distance : même première lettre d'abord (les fautes portent rarement sur elle), puis le plus fréquent
      const v = VOCAB.get(k), p = k[0] === n[0] ? 1 : 0;
      if (!best || d < best.d || (d === best.d && (p > best.p || (p === best.p && v.n > best.n)))) best = { d, p, n: v.n, forme: v.forme };
      }
      if (!best) return w;
      corrections.push([w, best.forme]); return best.forme;
    });
    return { texte, corrections };
  }
  function build(recs) {
    RECS_VOCAB = recs; VOCAB = null;   // vocabulaire construit à la première correction (pas au chargement)
    const inv = new Map(); const len = new Float32Array(recs.length); let tot = 0;
    recs.forEach((r, i) => {
      const tf = new Map();
      const add = (s, w) => {
        for (const t of toks(s)) tf.set(t, (tf.get(t) || 0) + w);
        if (s) { const n = " " + norm(s) + " "; for (const [e, j] of JETONS_EXPRESSION.concat(SENS_JETONS)) if (n.includes(" " + e + " ")) tf.set(j, (tf.get(j) || 0) + w); }
      };
      add(r.t, 3); add(r.d, 1); add(EV_LABEL(r.ev), 1.5);
      if (r.k === "dn") { add(r.o, 0.6); add((r.pj || []).join(" "), 0.4); }
      else { add(r.th, 0.8); add((r.docs || []).join(" "), 0.3); }
      let L = 0; for (const [t, v] of tf) { L += v; if (!inv.has(t)) inv.set(t, []); inv.get(t).push(i, v); }
      len[i] = L; tot += L;
    });
    // Démarches locales qui ont une jumelle nationale (même titre, normalisé) : index de la locale → index de la nationale.
    // Les démarches de la DINUM et de la DINSIC n'entrent pas dans la règle : probablement des démarches modèles, qui
    // masqueraient la vraie démarche locale de même titre.
    const nat = new Map();
    recs.forEach((r, i) => { if (r.k === "dn" && r.po === "nat" && !MODELES.test(r.o || "")) nat.set(norm(r.t), i); });
    const jumelles = new Map();
    if (nat.size) recs.forEach((r, i) => { if (r.k === "dn" && r.po !== "nat" && nat.has(norm(r.t))) jumelles.set(i, nat.get(norm(r.t))); });
    return { recs, inv, len, avg: tot / recs.length, byId: new Map(recs.map((r, i) => [r.id, i])), jumelles };
  }

  const PUBLIC_DN = { particulier: ["particulier", "mixte", "indetermine"], entreprise: ["entreprise", "mixte", "personne_morale", "indetermine"],
    association: ["association", "mixte", "personne_morale", "indetermine"], collectivite: ["collectivite", "personne_morale", "indetermine"] };
  const QUESTION_PRO = / entreprises? | societes? | professionnels? | employeurs? | auto entrepreneurs? | micro entrepreneurs? | urssaf | kbis | tva | siret | siren | salaries? | embauche | cotisations? | chiffre d affaires | agriculteurs? | exploitants? | eleveurs? | artisans? | commercants? | restaurants? | commerce | boutique | magasin /;
  const TITRE_PUBLIC = { association: / associations? /, entreprise: / entreprises? | professionnels? /, collectivite: / collectivites? | communes? /};
  const PUBLIC_SP = { particulier: "Particuliers", entreprise: "Professionnels", association: "Associations", collectivite: null };

  // Publics particuliers repérés dans le titre d'une fiche : [motif sur le titre normalisé, entouré d'espaces].
  // Le même motif, trouvé dans la question, annule la rétrogradation.
  const PUBLICS_PARTICULIERS = [/ etudiant(e|s|es)? | etude(s)? /, / stagiaire(s)? /, / au pair /, / saisonnier(s)? /].map((re) => [re]);
  // Territoires particuliers nommés dans le titre d'une fiche (outre-mer, Français de l'étranger, Alsace-Moselle) : la fiche est
  // rétrogradée si la question ne cite pas ce territoire, pour que la fiche générale passe devant.
  const TERRITOIRES_PARTICULIERS = [/ nouvelle caledonie /, / polynesie /, / wallis /, / futuna /, / saint pierre et miquelon /, / saint barthelemy /,
    / saint martin /, / mayotte /, / guadeloupe /, / martinique /, / guyane /, / (la )?reunion (?!d)/, / outre mer /, / alsace /, / moselle /,
    / a l etranger /, / hors de france /, / francais de l etranger /, / etablis hors de france /, / a l international /, / consulaire(s)? /, / australie /, / canada /];
  // Fiches annexes (timbre fiscal, suivi d'une demande, titre retrouvé) : après la démarche elle-même, sauf si la question en
  // parle ; jamais en « Votre démarche » dans ce cas. [motif sur le titre, motif sur la question], textes normalisés entourés d'espaces.
  const ANNEXES = [[/ timbres? /, / timbres? /], [/^ (suivre|suivez) | ou en est | etat d avancement | suivre /, / suivre | suivi | suivie | avancement | ou en est /],
    [/ retrouve(e|s|es)? /, / retrouve(e|s|es)? | retrouver /],
    // espace personnel, compte en ligne : on y suit ses démarches ; la démarche elle-même d'abord
    [/ mon compte | votre compte | espace personnel | espace prive | espace numerique /, / compte | espace /],
    // pièce ou document lié à la démarche (acte d'état civil, certificat médical, calendrier) : la démarche elle-même d'abord
    [/ acte de naissance | acte de mariage | acte de deces | copie integrale | extrait d acte /, / actes? | copies? | extraits? /],
    [/ certificats? medica(l|ux) /, / certificats? | medecins? | medica(l|ux) /],
    [/ calendrier | agenda /, / calendrier | agenda | dates? /],
    [/ attestation employeur | attestations? de salaire | attestation sur l honneur /, / employeur | salaire | honneur /],
    [/ fiche facultative | fiche d aide au calcul | notice /, / fiche | notice | calcul /],
    [/ journal officiel | annonce prealable /, / journal | annonce | publication /],
    // outil d'orientation avant la démarche (« Savoir si le Défenseur des droits est compétent »)
    [/^ savoir si | tester l eligibilite /, / savoir | eligib | simul | tester /],
    [/ examen civique /, / examen | civique /],
    // modalité particulière de la démarche
    [/ visioconference /, / visio | visioconference | video /]];
  // Fiche annexe que la question nomme (« suivre ma demande de passeport ») : elle remonte, et peut être « Votre démarche ».
  const annexeNommee = (r, q) => { if (r.k !== "sp") return false; const t = " " + norm(r.t) + " ", n = " " + norm(q) + " ";
    return ANNEXES.some(([rt, rq]) => rt.test(t) && rq.test(n)); };
  // Cas particulier (public ou objet précis) dans le titre d'une démarche ou d'une fiche, que la question ne nomme pas : après
  // le cas général, et jamais en « Votre démarche ». [motif sur le titre, motif sur la question], textes normalisés entourés d'espaces.
  const PUBLICS_PRECIS = [
    [/ agricoles? | agriculteurs? /, / agricoles? | agriculteurs? | tracteurs? | exploitants? | msa /],
    [/ independants? | auto entrepreneurs? | micro entrepreneurs? | artistes auteurs | non salaries /, / independants? | auto entrepreneurs? | micro entrepreneurs? | artistes? | auteurs? | non salaries? /],
    [/ militaires? | armees? | anciens? combattants? | combattants? | appeles du service national /, / militaires? | armee | armees | combattants? | soldats? | gendarmes? | service national /],
    [/ action sociale | asf | agents? publics? | fonctionnaires? | fonction publique | agents? de l etat | magistrats? | contractuels? | agents? hospitaliers? /, / agents? publics? | fonctionnaires? | fonction publique | agents? | magistrats? | contractuels? /],
    [/ mandataires? sociaux? | mandataire social /, / mandataires? | dirigeants? | gerants? /],
    // opération particulière sur un titre ou un dossier (modifier, corriger, ajouter un co-titulaire) : après la demande elle-même
    [/ modifier | modifie | modifiee | modifies | modification | correction | corriger | ajouter | co titulaire | cotitulaires? | recalcul /, / recalcul | recalculer | modifier | modification | changer | changement | corriger | correction | erreur | ajouter | adresse | demenage | demenagement | titulaire /],
    // organisme ou régime particulier
    [/ ircantec | msa | rafp | cnracl | enim | regime agricole | regime local | caisse des depots | fonctions? publiques? /, / ircantec | msa | rafp | cnracl | enim | agricole | regime local | fonction publique | fonctionnaires? | agents? /],
    // métier particulier
    [/ assistante?s? maternelle?s? | assistants? maternels? | assistante?s? familiale?s? | assistants? familiaux | particulier employeur | employes? a domicile | taxis? | voitures? de transport avec chauffeur /, / assistante?s? | nounou | particulier employeur | domicile | taxis? | chauffeurs? /],
    // situation d'exception
    [/ maladie professionnelle | maladies professionnelles | accident du travail | accident de travail | accidents? de trajet | remise gracieuse | impossibilite de payer | delai de paiement | terrorisme | catastrophe naturelle | deces de la mere | licenciement | droits de succession | impots locaux /,
     / professionnelle | accident | trajet | remise | gracieuse | impossib | plus payer | peux pas payer | delai | terroris | catastrophe | mere | licencie | licenciement | succession | heritage | locaux | locales | fonciere | habitation /],
    [/ etudiante?s? | etudiants? | alternants? | alternance /, / etudiante?s? | etudiants? | etudes | etudier | universite | fac | crous | bourses? | stage | stagiaires? | alternance | apprentis? /],
    // suite d'exception d'un accident ou d'une maladie (incapacité permanente, décès) : après le cas courant (arrêt, indemnités journalières)
    [/ incapacite permanente | deces d un salarie | deces du salarie | deces de l assure /, / incapacite | permanente | rente | deces | decede | mort | ayants? droits? /],
    [/ apres disparition | declaration judiciaire /, / disparu | disparue | disparition | judiciaire /],
    // objet ou domaine précis
    [/ placements? | capitaux mobiliers | produits de placement /, / placements? | capitaux | epargne | dividendes? /],
    [/ parcelles? | pres et | landes? /, / parcelles? | pres | landes? | agricoles? | terrains? /],
    [/ cinematographiques? | cinema | audiovisuels? /, / cinema | films? | cinematographique | audiovisuel /],
    [/ coproprietes? | coproprietaires? | proprietaires? bailleurs? /, / copro | coproprietes? | coproprietaires? | bailleurs? | louer | location /],
    [/ suspension | invalidation | annulation | retour au permis /, / suspension | suspendu | invalidation | invalide | annulation | annule | retour /],
    [/ archeologi(e|que) /, / archeologi(e|que) /],
    [/ franchise en base /, / franchise /],
    [/ fspoeie | ouvriers de l etat /, / fspoeie | ouvriers? /],
    [/ cnil /, / cnil | donnees personnelles | rgpd /],
    // volet particulier d'une prestation (« PCH Parentalité ») ; duplicata d'un document : après la demande elle-même
    [/ parentalite /, / parent | parents | parentalite | enfant | enfants | bebe /],
    [/ duplicata /, / duplicata | perdu | perdue | perte | vol | vole | volee /],
    // appel à projets ou dépôt à date limite : après la démarche permanente
    [/ appels? a projets? | aap | a deposer avant /, / appels? | projets? | aap /],
    [/ cadres? | apec /, / cadres? | apec /],
    [/ permis de chasser | chasse /, / chass(e|er|eur) /],
    [/ reconnues? d utilite publique /, / utilite publique | rup /],
    [/ declaration de nationalite | acquisition de la nationalite /, / nationalite | naturalis(ation|e) /],
    [/ contribution aux charges | separation de corps /, / contribution | charges | separation /],
    // allègement fiscal (plafonnement, exonération, dégrèvement, abattement) : après l'impôt lui-même
    [/ plafonnement | exonerations? | degrevements? | abattements? /, / plafonnement | exoner | degrev | abattement | reduction | baisse /],
    // taux personnalisé, acomptes : opération particulière sur le prélèvement
    [/ taux personnalise | acomptes? /, / taux | acomptes? | modifier | changer /],
    [/ marins? | gens de mer | notaires? | clercs? | journalistes? | detenus? | frontaliers? | pensionnes? /, / marins? | mer | notaires? | clercs? | journalistes? | detenus? | prison | frontaliers? | pensionnes? /]];
  // Un organisme particulier cité avec le régime général (« Caf ou MSA », « Caf et MSA ») ne fait pas un cas particulier ;
  // « ASF » après « allocation de soutien familial » est le sigle de l'allocation, pas l'action sociale des ministères.
  const AVEC_REGIME_GENERAL = / caf (ou|et) (la )?msa | msa (ou|et) (la )?caf /g;
  const casParticulierTitre = (r, q) => { const t = avecSigles(r.t).replace(AVEC_REGIME_GENERAL, " caf ").replace(/ soutien familial asf /g, " soutien familial "), n = avecSigles(q);
    return PUBLICS_PRECIS.some(([rt, rq]) => rt.test(t) && !rq.test(n)); };
  const annexe = (r, q) => { if (r.k !== "sp") return false; const t = " " + norm(r.t) + " ", n = " " + norm(q) + " ";
    return ANNEXES.some(([rt, rq]) => rt.test(t) && !rq.test(n)); };
  // Fiche « majeur » ou « mineur » : la fiche du majeur d'abord, sauf si la question parle d'un enfant (mot ou âge de moins de 18 ans).
  const ENFANT = / enfants? | mineure?s? | mon fils | ma fille | nos enfants | mes enfants | fils | fille | bebe | nourrisson | adolescente?s? | ado /;
  const parleEnfant = (q) => { const n = " " + norm(q) + " "; return ENFANT.test(n) || [...n.matchAll(/ (\d{1,2}) ans /g)].some((m) => +m[1] < 18); };
  function ageInadapte(r, q) {
    if (r.k !== "sp") return false; const t = " " + norm(r.t) + " ", e = parleEnfant(q);
    return e ? / majeure?s? /.test(t) && !/ mineure?s? /.test(t) : / mineure?s? /.test(t) && !/ majeure?s? /.test(t);
  }
  // Fiche propre à un territoire (outre-mer, étranger…) que la question ne cite pas : rétrogradée, et jamais en « Votre démarche ».
  // Commune nommée dans le titre d'une fiche (« Demande d'Apa à Paris ») : la fiche est propre à ce territoire.
  const lieuTitre = (r) => { if (r._lieuC !== COMMUNES) { r._lieuC = COMMUNES; const L = COMMUNES ? lieux(r.t).lieux[0] : null;
    // nom propre écrit avec sa majuscule dans le titre (« à Paris »), pas un mot courant (« à la garde d'enfants » ≠ La Garde)
    const nom = L && (L.nom || "").split(/[ -]/).pop();
    r._lieuT = (L && nom && new RegExp("(^|[^\\p{L}])" + nom.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "([^\\p{L}]|$)", "u").test(r.t) && L.dep) || ""; } return r._lieuT; };
  const horsTerritoire = (r, q) => { if (r.k !== "sp") return false; const tt = TERRITOIRES_PARTICULIERS.find((re) => re.test(" " + norm(r.t) + " "));
    if (lieuTitre(r) && lieuTitre(r) !== departementConnu(q, "")) return true;
    return !!tt && !tt.test(" " + norm(q) + " ") && !/ etranger /.test(" " + norm(q) + " "); };
  // Fiche d'un cas particulier (vol, perte, décès, détérioration) que la question n'évoque pas : jamais citée en phrase d'introduction.
  const CAS_PARTICULIERS = [/ vol | vols | vole | volee | volees | voles | vole /, / perte | pertes | perdu | perdue | perdus | perdues /,
    / deces | decede | decedee | mort | heriter | herite | heritage | succession /, / deterioration | deteriore | deterioree | endommage | endommagee | abime | abimee | accident | accidente | accidentee /];
  const casParticulier = (r, q) => { const t = " " + norm(r.t) + " ", n = " " + norm(q) + " "; return CAS_PARTICULIERS.some((re) => re.test(t) && !re.test(n)); };
  // Libellés des liens d'une carte : une même adresse une seule fois ; deux adresses de même libellé sont nommées par leur site
  // (« Faire une demande en ligne sur ants.gouv.fr »), puis, si le site est le même, par leur titre ; à titre égal, un seul lien.
  function libellesUniques(liens) {
    const vus = new Set(), l = liens.filter((x) => x.url && !vus.has(x.url) && vus.add(x.url)).map((x) => ({ ...x }));
    const compte = (k) => l.filter((x) => x.texte === k).length;
    for (const x of l) if (compte(x.texte) > 1) x.site = siteLisible(x.origine || x.url);
    for (const x of l) if (x.site !== undefined) { const meme = l.filter((y) => y.texte === x.texte && y.site === x.site).length > 1; x.nouveau = meme ? (x.titre || x.texte) : `${x.texte} sur ${x.site}`; }
    // Même libellé, même site et même titre : le même service, sous deux adresses ; le premier lien suffit.
    const t = new Set();
    return l.map(({ nouveau, site, origine, ...x }) => (nouveau ? { ...x, texte: nouveau } : x)).filter((x) => !t.has(x.texte) && t.add(x.texte));
  }
  // Ressource dont le lien menait à une page de connexion (« lc », remplacé par la fiche) : deux liens, un bouton et un lien
  // discret. Grand espace personnel (« lg », grands_espaces.json) : « Se connecter sur caf.fr », puis « Lire la fiche » ;
  // ailleurs : « Lire la fiche », puis « Se connecter directement sur … ».
  function boutonsConnexion(r) {
    if (!r || !r.lc || !r.ls) return null;
    const site = siteLisible(r.lc), fiche = { texte: "Lire la fiche", url: r.u };
    return r.lg ? { bouton: { texte: `Se connecter sur ${site}`, url: r.lc }, lien: fiche }
      : { bouton: fiche, lien: { texte: `Se connecter directement sur ${site}`, url: r.lc } };
  }
  // ---------- Plusieurs besoins dans une question (« j'ai perdu ma carte bancaire, ma carte d'identité et mon passeport ») :
  // la question est découpée sur les virgules, « : », « ; » et « et » ; chaque morceau qui désigne un papier de la table relue
  // (besoins.json, chargée par chargerBesoins) reçoit la fiche de la table pour le contexte (perte ou vol) ; un autre morceau
  // garde la démarche que le moteur juge sûre. Au moins deux besoins distincts, six au plus, rangés par urgence (table), puis
  // dans l'ordre de la question.
  // ---------- Sigles (donnees/assistant/sigles.json, table relue). Le sens d'un sigle est indexé comme une expression (un
  // jeton) ; dans une question, le sigle devient un seul terme : le jeton de son sens retenu (celui d'un contexte si l'un de ses
  // mots est dans la question, sinon le sens par défaut) et, pour un sigle sans autre sens, le sigle lui-même (« Demande de
  // RSA (Caf) »). Un sigle à plusieurs sens ne compte que par son sens retenu : « APS » ne trouve pas le transfert d'armes.
  // La table est chargée avant la construction de l'index (chargerSigles, puis build).
  let SIGLES = null, SENS_JETONS = [];
  const jetonSens = (sens) => "_s_" + sens.replace(/ /g, "_");
  function chargerSigles(d) {
    SIGLES = d && d.sigles ? d.sigles : null;
    SENS_JETONS = SIGLES ? [...new Set(Object.values(SIGLES).flatMap((e) => [e.sens, ...(e.contextes || []).map((c) => c.sens)]))].map((x) => [x, jetonSens(x)]) : [];
  }
  // Texte normalisé (entouré d'espaces) suivi du sens des sigles qu'il contient : « carte vtc » parle aussi de « voiture de
  // transport avec chauffeur ». Sert aux motifs de cas particulier et de public (titre comme question).
  function avecSigles(t) { const n = " " + norm(t) + " "; if (!SIGLES) return n;
    const sens = n.trim().split(" ").map((w) => sensSigle(w, n)).filter(Boolean); return sens.length ? n + sens.join(" ") + " " : n; }
  // La question parle d'un public (« entreprise ») par un de ses sigles (table : champ « public »).
  const siglePublic = (q, pub) => { if (!SIGLES) return false; const n = " " + norm(q) + " "; return n.trim().split(" ").some((w) => SIGLES[w] && SIGLES[w].public === pub); };
  function sensSigle(sg, n) { const e = SIGLES && SIGLES[sg]; if (!e) return "";
    const c = (e.contextes || []).find((x) => x.si.some((w) => n.includes(" " + w + " "))); return (c || e).sens; }
  // ---------- Démarche préfectorale ou départementale sans territoire : une ligne par département qui propose en ligne une
  // démarche pertinente pour la question (titre portant un terme de la question), la mieux classée ; triées par département.
  function departementsEnLigne(ix, q, opt = {}) {
    const P = pertinence(ix, q, opt), parDep = new Map();
    for (const x of search(ix, q, { ...opt, source: "dn", k: 80 })) {
      const r = x.r; if (!r.dep || parDep.has(r.dep) || !P.pertinente(r.id) || !termeAuTitre(q, r)) continue;
      parDep.set(r.dep, r);
    }
    return [...parDep].sort((a, b) => (a[0] < b[0] ? -1 : 1)).map(([dep, r]) => ({ dep, r }));
  }
  // Titre sans son territoire, pour présenter une seule fois une démarche proposée par plusieurs départements : les morceaux
  // du titre (séparés par « - », « : », « | ») qui nomment un département, une préfecture ou un numéro sont retirés.
  function titreSansTerritoire(t) {
    const terr = (x) => { const n = " " + norm(x) + " "; return /\b(prefecture|sous prefecture)\b|\b(\d{2,3}|2a|2b)\b/.test(n) || [...NOMS_DEPARTEMENTS].some((d) => n.includes(" " + d + " ")); };
    const morceaux = String(t || "").split(/\s[-–:|]\s|\s?[-–]\s|\s:\s?/).map((x) => x.trim()).filter((x) => x && !terr(x) && !/^[\d\s/.-]+$/.test(x));
    const m = morceaux.sort((a, b) => b.length - a.length)[0] || "";
    return m ? m[0].toUpperCase() + m.slice(1) : "";
  }
  // ---------- « Contacts utiles » : un service, lu dans l'Annuaire (enregistrement de l'API) ou dans prefectures.json (extrait
  // de l'Annuaire), devient { nom, site, adresse, fiche } ; puis une ligne : le nom porte le lien vers le site, l'adresse dessous.
  const litJ = (v) => { if (typeof v !== "string") return v || []; try { return JSON.parse(v); } catch (e) { return []; } };
  function contactAnnuaire(s) {
    if (!s) return null;
    if (typeof s.adresse === "string" && !/^\s*[[{]/.test(s.adresse)) return { nom: s.nom, site: s.site || s.fiche || "", adresse: s.adresse, fiche: s.fiche || "" };
    const ad = litJ(s.adresse), a = ad.find((x) => x && x.type_adresse === "Adresse") || ad[0] || {};
    const adresse = [a.numero_voie, [a.code_postal, a.nom_commune].filter(Boolean).join(" ")].filter(Boolean).join(", ");
    const site = litJ(s.site_internet).map((x) => x && x.valeur).find((u) => /^https?:/.test(u || "")) || s.url_service_public || "";
    return { nom: s.nom, site, adresse, fiche: s.url_service_public || "" };
  }
  const echapper = (t) => String(t || "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  function ligneContactHtml(c) {
    if (!c) return "";
    return `<li>${c.site ? `<a href="${echapper(c.site)}" target="_blank" rel="noopener">${echapper(c.nom)}</a>` : echapper(c.nom)}${c.adresse ? `<span class="adr">${echapper(c.adresse)}</span>` : ""}</li>`;
  }
  // Commune la plus peuplée d'un département (code INSEE), pour interroger l'Annuaire sur la préfecture compétente.
  function communePrincipale(dep) { let m = null; if (COMMUNES) for (const l of COMMUNES.values()) for (const c of l) if (c.dep === dep && (!m || c.pop > m.pop)) m = c; return m; }
  let BESOINS = null;
  function chargerBesoins(d) { BESOINS = d; }
  function besoins(ix, q, opt = {}) {
    if (!BESOINS || !ix) return [];
    const n = " " + norm(q) + " ", mot = (w) => n.includes(" " + w + " ");
    const ctx = (BESOINS.contexte.vol || []).some(mot) ? "vol" : "perte", motsCtx = ctx === "vol" ? "vol" : "perte";
    const morceaux = (q || "").split(/[,;:\n]|\s+et\s+|\s+puis\s+/i).map((x) => x.trim()).filter(Boolean);
    const out = [], vus = new Set();
    const papierDe = (m) => { const t = " " + norm(m) + " ";
      let best = null; for (const p of BESOINS.papiers) for (const f of p.motifs) if (t.includes(" " + f + " ") && (!best || f.length > best.l)) best = { p, l: f.length };
      return best && best.p; };
    morceaux.forEach((m, i) => {
      const p = papierDe(m);
      if (p) {
        if (vus.has(p.cle)) return; vus.add(p.cle);
        const id = p.fiche[ctx] || p.fiche["*"], i2 = id ? ix.byId.get(id) : undefined;
        out.push({ cle: p.cle, nom: p.nom, ico: p.ico, action: p.action, note: p.note || "", urgence: p.urgence, ordre: i, guichet: p.guichet !== false,
          rec: i2 === undefined ? null : ix.recs[i2], morceau: m,
          pre: p.pre_demande && ix.byId.has(p.pre_demande) ? ix.recs[ix.byId.get(p.pre_demande)] : null });
        return;
      }
      if (lieux(m).lieux.length && !queryToks(m).length) return;
      const C = choisir(ix, m + " " + (/perd|perte|vol/.test(norm(q)) ? motsCtx : ""), { ...opt, k: 20 });
      if (C.principal && !vus.has(C.principal.id)) { vus.add(C.principal.id);
        out.push({ cle: C.principal.id, nom: C.principal.t, ico: "", action: "", note: "", guichet: true, urgence: (BESOINS.urgence.slice(-1)[0] || {}).rang || 3, ordre: 100 + i, rec: C.principal, morceau: m }); }   // après les papiers de la table
    });
    if (out.length < 2) return [];
    return out.sort((a, b) => a.urgence - b.urgence || a.ordre - b.ordre).slice(0, 6);
  }
  // Carte d'identité et passeport (titres_identite.json, chargé par chargerTitres) : pré-demande en ligne, puis dépôt dans la
  // mairie équipée de son choix. titreIdentite : fiche service-public du thème de la table dont le titre contient un indice ;
  // ensuiteTitres : la ligne « Ensuite… » et ses deux liens, lus dans la table.
  let TITRES = null;
  function chargerTitres(d) { TITRES = d; }
  function titreIdentite(r) {
    if (!TITRES || !r || r.k !== "sp" || r.th !== TITRES.theme) return false;
    const t = " " + norm(r.t) + " ";
    return TITRES.indices.some((i) => t.includes(" " + norm(i) + " "));
  }
  const ensuiteTitres = () => TITRES ? { texte: TITRES.ensuite, rendez_vous: TITRES.rendez_vous, carte: TITRES.carte } : null;
  // Libellé d'une ressource service-public dans une carte.
  const libelleRessource = (r) => /imulateur/i.test(r.ty) ? "Savoir si j'y ai droit (simulateur)" : /Téléservice|selNG/i.test(r.ty) ? "Faire une demande en ligne"
    : /ormulaire/i.test(r.ty) ? "Formulaire" : /echerche/i.test(r.ty) ? "Outil de recherche" : r.t;
  function search(ix, q, opt = {}) {
    const { pub = "", dep = "", source = "", k = 10, ouvertes = true, sansJumelles = false } = opt;
    // Même titre qu'une démarche nationale : la nationale passe devant, la locale n'apparaît que si l'usager a choisi son
    // département (pas pour un lieu seulement reconnu dans la question). Ne vaut que pour les démarches de même titre.
    const jumelles = sansJumelles ? new Map() : ix.jumelles || new Map();
    const qt = queryToks(q); if (!qt.length) return [];
    // Couverture : comptée par mot de la question (groupe de termes), pas par synonyme : « aide » appelle aussi « subvention »
    // et « allocation », mais une fiche qui contient « aide » et « logement » couvre toute la question « aide au logement ».
    // Couverture : comptée par mot de la question (groupe de termes), pas par synonyme : « aide » appelle aussi « subvention »
    // et « allocation », mais une fiche qui contient « aide » et « logement » couvre toute la question « aide au logement ».
    const groupes = [...analyse(q).termes.values()], nG = groupes.length || 1;
    const N = ix.recs.length, k1 = 1.2, b = 0.75, sc = new Map(), hit = new Map();
    for (const t of qt) {
      const p = ix.inv.get(t); if (!p) continue;
      const gs = groupes.map((g, x) => (g.has(t) ? x : -1)).filter((x) => x >= 0);
      const df = p.length / 2, idf = Math.log(1 + (N - df + 0.5) / (df + 0.5));
      for (let j = 0; j < p.length; j += 2) {
        const i = p[j], tf = p[j + 1];
        const s = idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * ix.len[i] / ix.avg));
        sc.set(i, (sc.get(i) || 0) + s); if (!hit.has(i)) hit.set(i, new Set()); gs.forEach((x) => hit.get(i).add(x));
      }
    }
    // Question courte (quatre mots utiles au plus) dont tous les mots sont dans le titre, tels quels (pas par un synonyme) :
    // la fiche porte le nom même de la démarche cherchée.
    const motsQ = [...analyse(q).termes.keys()].filter((t) => !t.startsWith("« "));
    const titreComplet = motsQ.length && motsQ.length <= 4 && motsQ.length === groupes.length
      ? (r) => { const tt = new Set(toks(r.t)); return motsQ.every((t) => tt.has(t)); } : () => false;
    const today = new Date().toISOString().slice(0, 10), out = [];
    // Démarche récente : publiée dans les 12 derniers mois (champ « dp » de l'index, date de publication du descriptif).
    const ilYaUnAn = new Date(Date.now() - 365 * 864e5).toISOString().slice(0, 10);
    // Lieu reconnu dans la question, sans département choisi : il est seulement proposé (aucun filtre), mais les démarches
    // de son département passent devant : un lieu nommé dans la question en dit plus qu'un sélecteur laissé vide.
    const depLieu = dep ? "" : ((COMMUNES && lieux(q).lieux[0]) || {}).dep || "";
    // Région choisie par l'usager (pastille « Bretagne ? ») : filtre sur ses départements, sans département choisi.
    const depsRegion = !dep && api.region ? api.region.deps : null;
    for (const [i, s0] of sc) {
      const r = ix.recs[i];
      if (source && r.k !== source) continue;
      if (r.k === "dn") {
        if (pub && PUBLIC_DN[pub] && !PUBLIC_DN[pub].includes(r.cat)) continue;
        if (dep && r.dep && r.dep !== dep) continue; // garde les démarches nationales (« nat ») et de département inconnu (« inc »)
        if (jumelles.has(i) && !(dep && r.dep === dep)) continue;
        if (depsRegion && r.dep && !depsRegion.includes(r.dep)) continue;
        if (ouvertes && r.fe && r.fe < today) continue;
      } else {
        // public choisi : la fiche le déclare, ou son titre le nomme (« Créer votre compte association », déclarée « Particuliers »)
        if (pub && PUBLIC_SP[pub] && !(r.aud || "").includes(PUBLIC_SP[pub]) && !(TITRE_PUBLIC[pub] && TITRE_PUBLIC[pub].test(" " + norm(r.t) + " "))) continue;
        if (pub === "collectivite") continue;
      }
      let s = s0 * (0.5 + 0.5 * hit.get(i).size / nG);
      // Sans public choisi, une démarche des seuls professionnels passe après celles des particuliers, sauf si la question
      // parle d'entreprise (« attestation de vigilance », « tva », « urssaf »…).
      if (!pub && ((r.k === "sp" && r.aud && !/Particuliers/.test(r.aud)) || (r.k === "dn" && /^(entreprise|collectivite)$/.test(r.cat || ""))) && !QUESTION_PRO.test(" " + norm(q) + " ") && !siglePublic(q, "entreprise")) s *= 0.8;
      if (titreComplet(r)) s *= 1.25; // récompense la couverture de la requête
      if (casParticulierTitre(r, q)) s *= 0.7;   // cas particulier que la question ne nomme pas
      // Fiche service-public propre à un département (« Allier (03) : … ») hors du département connu : après la fiche nationale.
      if (r.k === "sp") { const md = /^[^:]{2,60}\((\d{2,3}|2A|2B)\)\s*:/.exec(r.t); if (md && md[1] !== (dep || depLieu)) s *= 0.7; }
      if (r.k === "dn") { s *= 1 + 0.12 * Math.log10(1 + r.n); if (dep && r.dep === dep) s *= 1.15; else if (depLieu && r.dep === depLieu) s *= 1.3;
        else if (depsRegion && r.dep && depsRegion.includes(r.dep)) s *= 1.15;
        else if (!dep && !depLieu && !depsRegion && (r.po ? r.po !== "nat" : !!r.dep)) s *= 0.7;   // territoire inconnu : une démarche locale (département connu ou non) passe après la fiche nationale
        if (r.dp && r.dp >= ilYaUnAn) s *= 1.15;
        if (r.tc) s *= 0.7;   // titre qui ressemble à un identifiant interne (« Bilan_4BNaap12_… ») : rétrogradé, quelle que soit la portée
        const yrs = (r.t.match(/20[12]\d/g) || []).map(Number); if (yrs.length && Math.max(...yrs) < ANNEE - 1) s *= 0.6; }
      else {
        // Service en ligne (« Téléservice », « selNG ») devant le formulaire : la démarche se fait d'abord en ligne.
        if (/Téléservice|selNG/.test(r.ty)) s *= 1.2; else if (/Formulaire|formulaireNG/.test(r.ty)) s *= 1.1;
        // Fiche réservée à un public particulier (« Étudiant étranger… », « … stagiaire ») que la question ne nomme pas :
        // rétrogradée, pour que la fiche générale passe devant.
        const pp = PUBLICS_PARTICULIERS.find(([re]) => re.test(" " + norm(r.t) + " "));
        if (pp && !pp[0].test(" " + norm(q) + " ")) s *= 0.7;
        if (horsTerritoire(r, q)) s *= 0.7;
        if (annexe(r, q)) s *= 0.6; else if (annexeNommee(r, q)) s *= 2;
        // Fiche question-réponse (« … : quelles différences ? ») : un peu après la fiche d'information du même sujet.
        if (/Question-réponse/.test(r.ty)) s *= 0.9;
        if (ageInadapte(r, q)) s *= 0.85;
        else if (parleEnfant(q) && / mineure?s? /.test(" " + norm(r.t) + " ")) s *= 1.15;   // pour un enfant, la fiche « mineur » remonte
      }
      out.push([s, i]);
    }
    out.sort((a, b) => b[0] - a[0]);
    // Jumelle locale gardée (département choisi) : placée juste après sa nationale si elle la précède.
    for (let j = 0; j < out.length; j++) {
      const n = jumelles.get(out[j][1]); if (n === undefined) continue;
      const p = out.findIndex((x) => x[1] === n);
      if (p > j) { const [x] = out.splice(j, 1); out.splice(p, 0, x); j--; }
    }
    // Diversité : au plus deux démarches en ligne d'un même organisme parmi les résultats ; les suivantes ne disparaissent
    // pas, elles sont regroupées sous la 2e (champ « autres » du résultat, et Moteur.regroupements pour la page). Pas de
    // regroupement quand la recherche est filtrée sur une source.
    const parOrg = new Map(), deuxieme = new Map(), autres = new Map(), gardes = [];
    for (const x of out) {
      const r = ix.recs[x[1]], o = !source && r.k === "dn" ? norm(r.o) : "";
      if (o) {
        const n = (parOrg.get(o) || 0) + 1; parOrg.set(o, n);
        if (n === 2) deuxieme.set(o, x[1]);
        if (n > 2) { const d = deuxieme.get(o); if (!autres.has(d)) autres.set(d, []); autres.get(d).push(r); continue; }
      }
      gardes.push(x);
    }
    out.splice(0, out.length, ...gardes);
    // Département choisi : les démarches locales dont le département est inconnu (po « inc ») restent parmi les
    // résultats retenus, mais placées après les démarches nationales et celles du département.
    const top = out.slice(0, k);
    if (dep) top.sort((a, b) => (ix.recs[a[1]].po === "inc") - (ix.recs[b[1]].po === "inc") || b[0] - a[0]);
    api.regroupements = new Map(top.filter(([, i]) => autres.has(i)).map(([, i]) => [ix.recs[i].id, autres.get(i)]));
    return top.map(([s, i]) => autres.has(i) ? { score: +s.toFixed(2), r: ix.recs[i], autres: autres.get(i) } : { score: +s.toFixed(2), r: ix.recs[i] });
  }
  // Pertinence d'un résultat pour une question, au sens de la règle France services de la page FORM (ne change ni le
  // classement ni l'affichage) : score d'au moins la moitié du meilleur score de la recherche, et soit au moins deux termes
  // significatifs distincts de la question repris, soit le terme le plus rare de la question (IDF la plus élevée parmi les
  // termes présents dans l'index ; c'est aussi le cas d'une question à un seul terme). Un terme est la racine d'un mot hors
  // mots vides ; un synonyme ajouté par le moteur compte comme le terme d'origine.
  function pertinence(ix, q, opt = {}) {
    const termes = analyse(q).termes;
    const res = termes.size ? search(ix, q, { ...opt, k: Infinity }) : [];
    const meilleur = res.reduce((m, x) => Math.max(m, x.score), 0), score = new Map(res.map((x) => [x.r.id, x.score]));
    const postings = new Map();
    const contient = (t, i) => {
      if (!postings.has(t)) { const p = ix.inv.get(t) || [], s = new Set(); for (let j = 0; j < p.length; j += 2) s.add(p[j]); postings.set(t, s); }
      return postings.get(t).has(i);
    };
    const couvre = (g, i) => [...g].some((t) => contient(t, i));
    const couverture = (id) => { const i = ix.byId.get(id); let n = 0; for (const g of termes.values()) if (couvre(g, i)) n++; return n; };
    const N = ix.recs.length, idf = (t) => { const p = ix.inv.get(t); return p ? Math.log(1 + (N - p.length / 2 + 0.5) / (p.length / 2 + 0.5)) : -1; };
    let rare = null;
    const idfG = (g) => Math.max(...[...g].map(idf));
    for (const [t, g] of termes) if (idfG(g) >= 0 && (!rare || idfG(g) > idfG(rare[1]))) rare = [t, g];
    const plusRare = (id) => !!rare && couvre(rare[1], ix.byId.get(id));
    return { meilleur, termes: termes.size, rare: rare && rare[0], score: (id) => score.get(id) || 0, couverture, plusRare,
      pertinente: (id) => termes.size > 0 && (score.get(id) || 0) >= 0.5 * meilleur && (couverture(id) >= 2 || plusRare(id)) };
  }
  // ---------- Réponse de la page : liste affichée et « Votre démarche »
  // Démarche réservée aux professionnels (accompagnants, travailleurs sociaux) d'après son titre ou sa description, ou
  // variante « … - Employeur » d'une démarche.
  const RESERVEE_PROS = /\(professionnels?\)|r[ée]serv[ée]e?s? aux (professionnels|travailleurs sociaux)|professionnels dipl[oô]m[ée]s du travail social/i, VARIANTE_EMPLOYEUR = /\s[-–]\s*employeurs?\s*$/i;
  // Département connu : choisi, sinon celui du lieu reconnu dans la question quand ses candidats l'ont tous.
  function departementConnu(q, dep) {
    if (dep) return dep;
    const c = COMMUNES ? ((lieux(q).lieux[0] || {}).candidats || []) : [];
    if (c.length) return c.every((x) => x.dep === c[0].dep) ? c[0].dep : "";
    // Nom de département écrit avec sa majuscule (« …, Gironde », « en Seine-et-Marne ») : pas un mot courant (« un lot »).
    const caps = " " + (String(q || "").match(/[A-ZÀ-Ý][\p{L}'’]*(?:[ -](?:et|de|du|des|sur|la|le)?[ -]?[A-ZÀ-Ý][\p{L}'’]*)*/gu) || []).map(norm).join(" | ") + " ";
    let best = ""; for (const d of NOMS_DEPARTEMENTS) if (caps.includes(" " + d + " ") && d.length > best.length) best = d;
    return best && typeof DEP_PAR_NOM !== "undefined" ? DEP_PAR_NOM.get(best) || "" : "";
  }
  // « Votre démarche » : le premier résultat, sauf (1) une démarche en ligne d'un autre département que le département
  // connu, ou de département inconnu quand une autre convient, (2) pour un particulier ou un public non précisé, une démarche réservée aux professionnels. Les écartées restent
  // dans la liste (« Autres pistes »).
  function principalDe(liste, q, opt = {}) {
    const { pub = "", dep = "" } = opt, d = departementConnu(q, dep);
    const ailleurs = (r) => !!d && r.k === "dn" && !!r.dep && r.dep !== d;
    const pro = (r) => (!pub || pub === "particulier") && ((RESERVEE_PROS.test(r.t + " " + (r.d || "")) || VARIANTE_EMPLOYEUR.test(r.t)));
    // Département connu : une démarche locale de département inconnu (po « inc ») passe après celles du département,
    // nationales et fiches.
    const inc = (r) => !!d && r.k === "dn" && r.po === "inc";
    liste = liste.filter((r) => !horsTerritoire(r, q));   // jamais une fiche propre à un territoire que la question ne cite pas
    return liste.find((r) => !ailleurs(r) && !inc(r) && !pro(r)) || liste.find((r) => !ailleurs(r) && !pro(r))
      || liste.find((r) => !ailleurs(r)) || liste[0] || null;
  }
  // ---------- Fiabilité : la page n'affirme une démarche que lorsqu'elle est sûre (PR « fiabilité »).
  // Codes des départements, dans l'ordre de NOMS_DEPARTEMENTS (01 à 19, 2A, 2B, 21 à 95, outre-mer).
  const CODES_DEP = [...Array.from({ length: 19 }, (_, i) => String(i + 1).padStart(2, "0")), "2A", "2B",
    ...Array.from({ length: 75 }, (_, i) => String(i + 21)), "971", "972", "973", "974", "976"];
  // NOMS_DEPARTEMENTS n'a pas Paris (nom de commune, reconnu comme lieu) : la correspondance saute le code 75.
  const DEP_PAR_NOM = new Map([...NOMS_DEPARTEMENTS].map((n, i) => [n, CODES_DEP.filter((c) => c !== "75")[i]]));
  // Ressource service-public locale : un lien vers une démarche de la plateforme (« …/commencer/… ») et un département
  // nommé dans le titre (« Demande de médaille d'honneur du travail Hautes-Alpes ») ; sinon nationale.
  function depRessource(r) {
    if (r._dep !== undefined) return r._dep;
    let d = "";
    if (r.k === "sp" && /\/commencer\//.test(r.l || "")) {
      const n = " " + norm(r.t) + " ";
      const nom = [...DEP_PAR_NOM.keys()].sort((a, b) => b.length - a.length).find((x) => n.includes(" " + x + " "));
      if (nom) d = DEP_PAR_NOM.get(nom);
    }
    return (r._dep = d);
  }
  const porteeDe = (r) => r.k !== "dn" ? (depRessource(r) ? "dep" : "nat") : r.po || (r.dep ? "dep" : "nat");
  const depDe = (r) => r.k === "dn" ? r.dep : depRessource(r);
  // Termes trop généraux : ils ne comptent jamais pour la condition sur le titre (« démarche sûre », « Comprendre », « Aussi
  // pour vous »). Comparés aux mots de la question : un terme est écarté si tous les mots de la question qui le donnent
  // sont de la liste (« informatique » n'est pas écarté par « information », qui a la même racine).
  // … et les mots qui disent pour qui est la démarche (« passeport enfant ») plutôt que laquelle : non exigés dans le titre.
  const GENERAUX = new Set("aide aides demande demander dossier formulaire declaration droit droits service information enfant enfants fils fille".split(" "));
  // Termes significatifs de la question (groupes de synonymes et expressions, Moteur.analyse) présents dans un titre.
  function termesAuTitre(q, r) {
    const titre = new Set(toks(r.t)), n = " " + norm(r.t) + " ";
    for (const [e, j] of JETONS_EXPRESSION.concat(SENS_JETONS)) if (n.includes(" " + e + " ")) titre.add(j);
    // « enfant » (et ses formes) est couvert par un titre « … d'un mineur » : la question parle bien de ce cas.
    if (/ mineure?s? /.test(n)) ["enfant", "enfants", "fils", "fille"].forEach((w) => titre.add(stem(w)));
    const mots = norm(q).split(" ").filter((w) => w.length > 1), utiles = new Set(mots.filter((w) => !GENERAUX.has(w)).map(stem));
    const general = (t) => !utiles.has(t) && mots.some((w) => GENERAUX.has(w) && stem(w) === t);
    const groupes = [...analyse(q).termes].filter(([t]) => !general(t)).map(([, g]) => g);
    return { groupes, presents: groupes.filter((g) => [...g].some((s) => titre.has(s))) };
  }
  // Au moins un terme de la question dans le titre (règle des cartes « Comprendre » et « Aussi pour vous »).
  function termeAuTitre(q, r) { return termesAuTitre(q, r).presents.length > 0; }
  // Rareté d'un terme : IDF la plus élevée de ses formes présentes dans l'index (0 si aucune).
  function idfGroupe(ix, g) {
    const N = ix.recs.length;
    return Math.max(0, ...[...g].map((s) => { const p = ix.inv.get(s); return p ? Math.log(1 + (N - p.length / 2 + 0.5) / (p.length / 2 + 0.5)) : 0; }));
  }
  // Condition sur le titre d'une démarche sûre (api.REGLE_TITRE). Retenue : « d » — termes absents de l'index ignorés, une
  // expression reconnue comptant pour deux ; tous les termes si la question en a trois ou moins, sinon au moins deux dont
  // le plus rare. Variantes essayées dans la PR 76 (gardées pour comparaison) : « un » (un terme), « a » (deux termes dont
  // le plus rare), « b » (60 % des termes), « c » (tous jusqu'à trois termes, sinon 60 %).
  function titreSur(ix, q, r) {
    const { groupes, presents } = termesAuTitre(q, r), n = groupes.length, k = presents.length;
    if (!n) return false;
    switch (api.REGLE_TITRE) {
      case "a": { const rare = groupes.reduce((m, g) => idfGroupe(ix, g) > idfGroupe(ix, m) ? g : m, groupes[0]);
        return (k >= 2 || n === 1) && presents.includes(rare); }
      case "b": return k / n >= 0.6;
      case "c": return n <= 3 ? k === n : k / n >= 0.6;
      case "d": {
        // Termes absents de l'index ignorés ; une expression reconnue compte pour deux termes.
        const sig = groupes.filter((g) => idfGroupe(ix, g) > 0), poids = (g) => EXPR_GROUPES.has(g) ? 2 : 1;
        if (!sig.length) return false;
        const total = sig.reduce((s, g) => s + poids(g), 0), au = sig.filter((g) => presents.includes(g)), couverts = au.reduce((s, g) => s + poids(g), 0);
        if (total <= 3) return couverts === total;
        const rare = sig.reduce((m, g) => idfGroupe(ix, g) > idfGroupe(ix, m) ? g : m, sig[0]);
        return couverts >= 2 && au.includes(rare);
      }
      default: return k > 0;
    }
  }
  // Démarche sûre : pertinente (Moteur.pertinence) et un terme de la question dans son titre ; nationale (ou fiche
  // service-public), ou du département connu ; pas réservée aux professionnels pour un particulier.
  // Tous les mots utiles de la question (hors lieux, tels quels, sans synonyme) sont dans le titre.
  function titrePorteTout(q, r) {
    const mots = [...analyse(q).termes.keys()].filter((t) => !t.startsWith("« ")), tt = new Set(toks(r.t));
    // question faite seulement d'expressions (un sigle : « FSL ») : chacune doit être dans le titre
    if (!mots.length) { const { groupes, presents } = termesAuTitre(q, r); return groupes.length > 0 && presents.length === groupes.length; }
    return mots.every((t) => tt.has(t));
  }
  // Mots du titre (hors mots vides) absents de la question.
  function motsEnPlus(q, r) { const qq = new Set(toks(q)); return new Set(toks(r.t).filter((t) => !qq.has(t))).size; }
  function sure(r, q, opt = {}, P = null) {
    const { pub = "", dep = "" } = opt, d = departementConnu(q, dep);
    if (!r || !(P || opt.P).pertinente(r.id) || !titreSur(opt.ix, q, r) || horsTerritoire(r, q) || annexe(r, q) || casParticulierTitre(r, q)) return false;
    // Une fiche question-réponse n'est pas une démarche : jamais en « Votre démarche », sauf si la question la nomme (annexe).
    // Exception : la fiche est en tête des résultats et son titre porte tous les mots de la question (« kbis »).
    if (/Question-réponse/.test(r.ty || "") && !annexeNommee(r, q) && !(opt.tete === r && titrePorteTout(q, r))) return false;
    const po = porteeDe(r);
    if (po !== "nat" && !(po === "dep" && d && depDe(r) === d)) return false;
    if ((!pub || pub === "particulier") && (RESERVEE_PROS.test(r.t + " " + (r.d || "")) || VARIANTE_EMPLOYEUR.test(r.t))) return false;
    return true;
  }
  // Recherche simple de la page : les k premiers résultats, puis, si un département est connu sans être choisi, les 3
  // premières démarches en ligne de ce département (au moins la moitié du meilleur score), puis les 3 premières fiches
  // service-public. Rend la liste, « Votre démarche » (seulement si elle est sûre), sinon les « Démarches possibles »,
  // et s'il faut demander le lieu d'abord (meilleurs résultats locaux, aucun territoire connu).
  function choisir(ix, q, opt = {}) {
    const { pub = "", dep = "", k = 20 } = opt, base = { pub, dep };
    const res = search(ix, q, { ...base, k }), liste = res.map((x) => x.r), reg = api.regroupements;
    const ajoute = (l) => { for (const x of l) if (!liste.includes(x.r)) liste.push(x.r); };
    const d = departementConnu(q, dep), meilleur = res.length ? res[0].score : 0;
    // Démarches du département : seulement celles dont le score atteint la moitié du meilleur score de la recherche.
    if (d && !dep) ajoute(search(ix, q, { ...base, dep: d, source: "dn", k: 3 }).filter((x) => x.score >= meilleur / 2));
    ajoute(search(ix, q, { ...base, source: "sp", k: 3 }));
    const P = pertinence(ix, q, base);
    // Démarche en ligne sans département connu (portée « inc ») : gardée seulement si son titre correspond à la question.
    for (let j = liste.length - 1; j >= 0; j--) if (liste[j].k === "dn" && liste[j].po === "inc" && !titreSur(ix, q, liste[j])) liste.splice(j, 1);
    api.regroupements = reg;   // les regroupements par organisme sont ceux de la première recherche
    // Ordre de préférence de principalDe : ni autre département, ni département inconnu quand le territoire est connu,
    // ni démarche réservée aux professionnels ; parmi les 5 premiers, la première sûre.
    const ailleurs = (r) => !!d && r.k === "dn" && !!r.dep && r.dep !== d;
    const ordre = liste.filter((r) => !ailleurs(r));
    const sures = ordre.slice(0, 5).filter((r) => sure(r, q, { ...opt, ix, tete: ordre[0] }, P));
    // « Votre démarche » est d'abord une démarche : une fiche d'information sûre cède la place à un service en ligne ou à un
    // formulaire sûr des 5 premiers dont le titre porte tous les mots de la question et au plus deux autres (« Demande
    // d'allocation de soutien familial (ASF) ») ; la fiche reste dans « Comprendre ».
    const DEMARCHE = /Téléservice|selNG|^Formulaire|formulaireNG/;
    let principal = (sures[0] && /^SP-F/.test(sures[0].id) && sures.find((r) => DEMARCHE.test(r.ty || "") && titrePorteTout(q, r) && motsEnPlus(q, r) <= 2 && motsEnPlus(q, r) < motsEnPlus(q, sures[0]))) || sures[0] || null;
    // Titre le plus proche de la question : parmi les 12 premiers, une démarche sûre dont le titre porte tous les mots de la
    // question, avec le moins de mots en plus, passe devant une démarche voisine (« Mariage en France » devant « Demande d'acte
    // de mariage… », « Parcoursup » devant « Parcoursup : intégrer le calendrier… »).
    const proches = ordre.slice(0, 12).filter((r) => titrePorteTout(q, r) && sure(r, q, { ...opt, ix, tete: ordre[0] }, P));
    if (proches.length) {
      const m = (r) => motsEnPlus(q, r), best = proches.reduce((a, b) => (m(b) < m(a) ? b : a));
      // une démarche (service en ligne, formulaire, Démarche Numérique) proche de la question n'est pas remplacée par une fiche
      // (sauf une démarche d'un sous-cas : « Porter plainte pour un rançongiciel » quand la question dit seulement « porter plainte »)
      const pourAutre = (r) => { const m2 = / pour (.+)$/.exec(" " + norm(r.t) + " "); if (!m2) return false; const qq = new Set(toks(q));
        return toks(m2[1]).some((t) => !qq.has(t)); };
      const demarche = (r) => (r.k === "dn" || DEMARCHE.test(r.ty || "")) && !pourAutre(r);
      if (principal ? m(best) <= 1 && !demarche(principal) && (!titrePorteTout(q, principal) || m(principal) >= 3) : m(best) <= 2) principal = best;
    }
    // « Démarches possibles » : parmi les 3 premières, seulement celles qui passent le seuil de pertinence et portent un
    // terme de la question (hors termes trop généraux) dans leur titre ; une ou deux lignes plutôt qu'une troisième hors
    // sujet. Aucune, et pas de fiche « Comprendre » : la page invite à reformuler.
    const possibles = principal ? [] : ordre.filter((r) => r.k === "dn" || !/^SP-F/.test(r.id)).slice(0, 3).filter((r) => P.pertinente(r.id) && termeAuTitre(q, r));
    const locale = (r) => r.k === "dn" && porteeDe(r) !== "nat";
    // Lieu d'abord : seulement sans démarche sûre, quand les meilleurs résultats sont locaux ; avec une démarche nationale
    // sûre, le lieu reste proposé plus bas, pour « Où aller ».
    const demanderLieu = !principal && !d && res.slice(0, 3).filter((x) => locale(x.r)).length >= 2;
    return { liste, principal, possibles, departement: d, demanderLieu, P };
  }
  // Réponse d'une ligne de l'accueil (« Les plus demandées », « À la une ») : construite à partir de ses ids, jamais par
  // une recherche sur un texte. Une démarche nationale (ou une fiche) est la réponse ; des variantes locales demandent
  // d'abord le département, puis donnent celle du département, ou disent qu'il n'y en a pas.
  function reponseLigne(ix, item, opt = {}) {
    const { dep = "" } = opt, rec = (id) => { const i = ix.byId.get(id); return i === undefined ? null : ix.recs[i]; };
    const recs = (item.ids || []).map(rec).filter(Boolean);
    const fd = recs.flatMap((r) => (r.fd || []).filter((f) => /^F/.test(f)).map((f) => rec("SP-" + f))).filter(Boolean);
    const fiche = (item.fiche && rec(item.fiche)) || fd[0] || null;
    const nat = recs.filter((r) => porteeDe(r) === "nat"), locales = recs.filter((r) => porteeDe(r) !== "nat");
    if (nat.length) return { principal: nat[0], possibles: nat.slice(1, 3), fiche, question: "", message: "", recs };
    if (!dep) return { principal: null, possibles: locales, fiche, question: item.question_lieu || "Dans quel département habitez-vous ?", message: "", recs };
    const v = locales.find((r) => r.dep === dep);
    if (v) return { principal: v, possibles: [], fiche, question: "", message: "", recs };
    return { principal: null, possibles: [], fiche, question: "", message: "Pas de démarche en ligne pour ce département : voici la fiche officielle et le guichet.", recs };
  }
  // « Avant de commencer » : ce qui attend l'usager, d'après les données de la démarche seulement (aucune ligne sans donnée,
  // aucun jugement, aucun délai inventé). Sobriété : une ligne = un symbole et quelques mots ; la source, la date et la
  // limite vont dans l'infobulle (titre) ou dans « Comment ça marche ». Rend { resume, lignes } ; lignes vides : pas de bloc.
  // Chaque ligne : { cle, ico, texte, titre, liens: [{ texte, url, titre, apres }] }.
  // Ce qui est récupéré ou prérempli, en quelques mots (valeurs « pre » de l'index). L'IBAN n'y est pas : il est contrôlé, pas rempli.
  const PRE_COURT = { "SIRET (API Entreprise)": "SIRET", "RNA (associations)": "numéro RNA", "RNF (fondations)": "numéro de fondation",
    "Annuaire Éducation": "établissement scolaire", "Quotient familial (CAF)": "quotient familial (CAF)", "Statut boursier": "statut boursier",
    "Données préremplies": "certaines réponses" };
  const MAX_AVANT = 5;
  // Symboles « comment faire » et signaux (accessibilité, vigilance), d'après les données de la démarche seulement.
  // voies : liste de voies (alternatives, « ou »), chacune une liste de modes qui se suivent ; Démarche Numérique : en ligne.
  // acc : { niveau: "tc" | "pc" | "nc" | "inconnue" | "plateforme" (Démarche Numérique, taux de la plateforme), texte, detail } ; vig : au plus 2 { motif, texte, detail }, à partir de
  // 20 retours rattachés (Services Publics +, critères cochés par l'usager dans ses retours négatifs ; jamais son texte).
  const MODES_LIB = { en_ligne: "En ligne", formulaire: "Formulaire à remplir", guichet: "Au guichet", rendez_vous: "Sur rendez-vous",
    courrier: "À envoyer par courrier", courriel: "À envoyer par courriel" };
  // Libellés courts, affichés après chaque symbole dans la ligne sous le titre.
  const MODES_COURT = { en_ligne: "En ligne", formulaire: "Formulaire", guichet: "Au guichet", rendez_vous: "Sur rendez-vous",
    courrier: "Par courrier", courriel: "Par courriel" };
  const MOTIFS_LIB = { delai: "Délais de réponse signalés", joignable: "Difficile à joindre", explication: "Explications jugées peu claires" };
  const ACC_LIB = { tc: "Accessible", pc: "Accessibilité partielle", nc: "Non conforme", inconnue: "Accessibilité non connue" };
  const SEUIL_RETOURS = 20, MAX_VOIES = 3, MAX_VIGILANCES = 2;
  const dateCourte = (d) => (d || "").split("-").reverse().join("/");
  const MOIS = "janvier février mars avril mai juin juillet août septembre octobre novembre décembre".split(" ");
  const CARTE_PHRASE = "Cette démarche contient une carte à manipuler, ce qui peut gêner certains usagers.";
  // Signaux de simplicité, positifs, seulement quand c'est vrai (étude : scripts/assistant/etude_simplicite.py).
  // FranceConnect : toutes les démarches DN (la plateforme le propose partout) ; une fiche SP seulement si l'Observatoire le
  // déclare pour la démarche rattachée (clé « fc »). Données récupérées : DN dont le formulaire a un champ qui va chercher la
  // donnée. Jamais : IBAN (format vérifié, rien n'est récupéré), lien prérempli, score DLNUF, habilitation DataPass seule.
  const RECUPERE = {
    "SIRET (API Entreprise)": "informations sur l'entreprise récupérées à partir du SIRET (API Entreprise)",
    "RNA (associations)": "informations sur l'association récupérées à partir du numéro RNA (répertoire national des associations)",
    "RNF (fondations)": "informations sur la fondation récupérées à partir de son numéro (répertoire national des fondations)",
    "Annuaire Éducation": "coordonnées de l'établissement scolaire récupérées dans l'annuaire de l'Éducation nationale",
  };
  function simplicite(r, meta = {}) {
    const out = [];
    if (!r) return out;
    const obs = meta.observatoire ? `Observatoire de la qualité des démarches en ligne, ${meta.observatoire}` : "Observatoire de la qualité des démarches en ligne";
    if (r.k === "dn") out.push({ cle: "fc", texte: "FranceConnect", surete: "déployé",
      detail: `connexion possible avec un compte FranceConnect (impots.gouv, ameli, La Poste…) : Démarche Numérique le propose sur toutes ses démarches${meta.date_export ? ` (descriptif du ${dateCourte(meta.date_export)})` : ""}` });
    else if (r.fc && /^FranceConnect/.test(r.fc)) out.push({ cle: "fc", texte: /\+/.test(r.fc) ? "FranceConnect+" : "FranceConnect", surete: "déclaré",
      detail: `connexion possible avec ${/\+/.test(r.fc) ? "FranceConnect+, la version de FranceConnect à sécurité renforcée" : "un compte FranceConnect (impots.gouv, ameli, La Poste…)"}, déclarée pour cette démarche (${obs})` });
    const rec = r.k === "dn" ? [...new Set(r.pre || [])].map((p) => RECUPERE[p]).filter(Boolean) : [];
    if (rec.length) out.push({ cle: "rec", texte: "Données récupérées pour vous", surete: "déployé",
      detail: `${rec.join(" ; ")}, par un champ du formulaire de la démarche sur Démarche Numérique` });
    return out;
  }
  // Délais constatés : jamais copiés, seulement un renvoi vers la page statistiques publique de la démarche, dont l'adresse
  // est celle de la démarche avec « commencer » remplacé par « statistiques » (vérifiée sur un échantillon, voir la PR).
  const DELAIS_TEXTE = "Délais constatés : voir les statistiques de la démarche";
  function statsUrl(r) {
    if (!r || r.k !== "dn" || !r.u) return "";
    const u = /^https?:/.test(r.u) ? r.u : "https://demarche.numerique.gouv.fr/commencer/" + encodeURIComponent(r.u);
    return /\/commencer\//.test(u) ? u.replace("/commencer/", "/statistiques/").replace(/\/$/, "") : "";
  }
  function symboles(r, meta = {}) {
    const vide = { voies: [], sur: true, acc: null, vig: [], simp: [] };
    if (!r) return vide;
    const voies = r.k === "dn" ? [["en_ligne"]] : (r.md || []).slice(0, MAX_VOIES);
    if (!voies.length) return vide;
    const obs = meta.observatoire ? `Observatoire de la qualité des démarches en ligne, ${meta.observatoire}` : "Observatoire de la qualité des démarches en ligne";
    let acc;
    if (r.acc) {
      const niveau = r.acc[0].toLowerCase(), taux = r.acc[1];
      acc = { niveau, texte: ACC_LIB[niveau] + (niveau === "pc" && taux ? ` (${taux})` : ""), detail: `Déclaration d'accessibilité de cette démarche (${obs})`, perimetre: "demarche",
        court: ACC_LIB[niveau] + (taux ? ` : ${taux}` : "") };
    } else if (r.k === "dn" && meta.acc_plateformes && meta.acc_plateformes.dn) {
      // Démarche Numérique : jamais de taux par démarche ; celui de la plateforme (déclaration publiée, accessibilite_plateformes.json),
      // pour une démarche type. Pas de pastille sur la carte, pas de renvoi vers France services pour ce seul motif.
      const p = meta.acc_plateformes.dn, [a, m] = (p.mise_a_jour || "").split("-"), mois = MOIS[+m - 1] || "";
      const etat = { "partiellement conforme": "partielle", "totalement conforme": "totale", "non conforme": "non conforme" }[p.statut] || p.statut;
      const phrase = `Plateforme ${p.nom} : accessibilité ${etat} (${p.taux}${mois ? `, déclaration ${/^[aeiouy]/.test(mois) ? "d'" : "de "}${mois} ${a}` : ""}), pour une démarche type. Le taux peut être un peu différent selon la démarche, par exemple si elle contient une carte.`
        + (r.crt ? " " + CARTE_PHRASE : "");
      acc = { niveau: "plateforme", texte: "Accessibilité de la plateforme", detail: phrase, ligne: phrase, perimetre: "plateforme", url: p.url, carte: !!r.crt,
        court: `Accessibilité : ${p.taux} (plateforme)`, titre: `Déclaration d'accessibilité de ${p.nom}${mois ? `, ${mois} ${a}` : ""}, pour une démarche type` };
    } else acc = { niveau: "inconnue", texte: ACC_LIB.inconnue, perimetre: "", court: ACC_LIB.inconnue,
      detail: `Aucune déclaration trouvée pour cette démarche dans l'${obs}` + (r.k === "dn" ? " ; celle de la plateforme Démarche Numérique ne porte pas sur le formulaire de chaque démarche" : "") };
    const vig = [];
    if (r.spp && r.spp[0] >= SEUIL_RETOURS) {
      // 5e élément : portée de la vigilance quand elle ne porte ni sur la seule démarche ni sur tout l'organisme
      // (domaine ANTS, titres de séjour ANEF, préfecture hors retours sur les étrangers).
      const [n, neg, motifs, org, portee] = r.spp, sp = meta.spp || {};
      const pour = org ? `pour l'organisme « ${org} » (${portee || "tout l'organisme"}, pas seulement cette démarche)`
        : portee ? `${portee}, pas seulement cette démarche` : "pour cette démarche";
      for (const [m, k] of (motifs || []).slice(0, MAX_VIGILANCES)) if (MOTIFS_LIB[m])
        vig.push({ motif: m, texte: MOTIFS_LIB[m], organisme: org || "", k,
          detail: `${k} retours négatifs le signalent, sur ${n} retours sur Services Publics +${sp.debut ? " depuis le " + dateCourte(sp.debut) : ""}, ${pour} ; échantillon spontané, non représentatif` });
    }
    const su = statsUrl(r);
    // Formulaire cerfa d'une ressource service-public (« cerfa », lien « l ») : le symbole « Formulaire » devient un lien.
    const cerfa = r.k === "sp" && r.cerfa && r.l && voies.some((v) => v.includes("formulaire")) ? { texte: `Formulaire cerfa n°\u00a0${r.cerfa}`, url: r.l } : null;
    return { voies, cerfa, sur: r.k === "dn" ? true : r.md_sur !== false, simp: simplicite(r, meta), acc, vig, delais: su ? { texte: DELAIS_TEXTE, url: su } : null, rien: r.raf ? { phrase: r.raf[0], fiche: r.raf[1] } : null };
  }
  const voiesTexte = (v) => v.map((voie) => voie.map((m) => MODES_LIB[m].toLowerCase()).join(", ")).join(" ou ");
  // La déclaration d'accessibilité de Démarche Numérique dit que le PDF de la démarche n'est pas accessible
  // (accessibilite_plateformes.json, clé « pdf_non_accessible », relue sur la page).
  const pdfNonAccessible = (meta) => !!(meta.acc_plateformes && meta.acc_plateformes.dn && meta.acc_plateformes.dn.pdf_non_accessible);
  // Site d'un service en ligne, lisible : nom de domaine sans « www. » ni chemin, ramené au site qui le publie
  // (« immatriculation.ants.gouv.fr » → « ants.gouv.fr », « wwwd.caf.fr » → « caf.fr »).
  function siteLisible(u) {
    const m = /^https?:\/\/([^\/?#:]+)/i.exec(u || ""); if (!m) return "";
    const h = m[1].toLowerCase().replace(/^www\d*\./, ""), p = h.split(".");
    return p.slice(/\.gouv\.fr$/.test(h) ? -3 : -2).join(".");
  }
  // Icônes (Tabler) de chaque ligne : la même que dans la ligne sous le titre quand la ligne explique un symbole.
  const ICO = { en_ligne: "device-laptop", formulaire: "file-type-pdf", courriel: "at", courrier: "mailbox", guichet: "building",
    rendez_vous: "calendar-event", fc: "key", rec: "database-import", acc: "accessible", delai: "hourglass", joignable: "phone-off",
    explication: "help-circle", organisme: "building", questions: "file-text", delais: "clock", carte: "map", aide: "map-pin", rien: "circle-check" };
  const NOUVEL_ONGLET = "S'ouvre dans un nouvel onglet";
  function avantDeCommencer(r, meta = {}) {
    const lignes = [], resume = [];
    if (!r) return { resume: "", lignes };
    if (r.k === "dn" && r.u) {
      const ch = r.ch || 0, pj = [...new Set(r.pj || [])].length, parts = [];
      if (ch) parts.push(`${ch} question${ch > 1 ? "s" : ""}`);
      if (pj) parts.push(`${pj} pièce${pj > 1 ? "s" : ""}`);
      resume.push(...parts.map((x) => x.replace(" ", "\u00a0")));   // « 6 pièces » ne se coupe pas
      const base = /^https?:/.test(r.u) ? r.u : "https://demarche.numerique.gouv.fr/commencer/" + encodeURIComponent(r.u);
      // Le nombre de questions et de pièces est dans le titre replié : la ligne ne porte que le lien.
      lignes.push({ cle: "questions", ico: ICO.questions, texte: "",
        liens: [{ texte: "Voir le formulaire", url: base.replace(/\/$/, "") + "/dossier_vide",
                  titre: "Pour lire toutes les questions avant de commencer, pas pour le remplir",
                  apres: pdfNonAccessible(meta) ? "(PDF non accessible)" : "(PDF)" }] });
      // Ce que le formulaire va chercher (signal « Données récupérées pour vous » de la ligne sous le titre), puis ce qui peut être prérempli.
      const pre = [...new Set(r.pre || [])], rec = pre.filter((p) => RECUPERE[p]).map((p) => PRE_COURT[p]), autres = pre.filter((p) => !RECUPERE[p] && PRE_COURT[p]).map((p) => PRE_COURT[p]);
      if (rec.length) lignes.push({ cle: "donnees", ico: ICO.rec, texte: `Données récupérées : ${rec.join(", ")}`, liens: [] });
      if (autres.length) lignes.push({ cle: "prerempli", ico: ICO.rec, texte: `Peut être rempli pour vous : ${autres.join(", ")}`, liens: [] });
    }
    // Accessibilité partielle ou non conforme (Observatoire) : le niveau est dans le « ? » ; ici, seulement le renvoi vers une France services.
    const S = symboles(r, meta);
    if (S.acc && (S.acc.niveau === "pc" || S.acc.niveau === "nc"))
      lignes.push({ cle: "aide", ico: ICO.aide, texte: "Besoin d'aide :", liens: [{ texte: "France services la plus proche", url: "#carte-ou", titre: "" }] });
    // Jamais seules : l'accessibilité de la plateforme (ou non connue) et la carte à manipuler, en dernières lignes, et les délais
    // constatés, juste avant, s'il reste de la place. Ce qui ne trouve pas sa place ici va dans le « ? ».
    const fin = [];
    if (lignes.length && S.acc && (S.acc.niveau === "plateforme" || S.acc.niveau === "inconnue"))
      fin.push({ cle: "accessibilite", ico: ICO.acc, texte: S.acc.court, titre: S.acc.titre || S.acc.detail, liens: [] });
    if (lignes.length && r.crt) fin.push({ cle: "carte", ico: ICO.carte, texte: "Contient une carte à manipuler", titre: CARTE_PHRASE, liens: [] });
    if (lignes.length && S.delais && lignes.length + fin.length < MAX_AVANT)
      lignes.push({ cle: "delais", ico: ICO.delais, texte: "Délais :", liens: [{ texte: "voir les statistiques", url: S.delais.url, titre: NOUVEL_ONGLET }] });
    const tout = lignes.concat(fin).slice(0, MAX_AVANT);
    return { resume: tout.length ? "Avant de commencer" + (resume.length ? " · " + resume.join(", ") : "") : "", lignes: tout };
  }
  // Détail du bouton « ? » : une ligne par symbole de la ligne sous le titre, qui commence par ce symbole (comment faire,
  // connexion, accessibilité, vigilances), puis le nom complet de l'organisme s'il est coupé. Une information ne s'affiche
  // qu'à un seul endroit : ce que porte « Avant de commencer » n'y est pas. opt.site : adresse du service en ligne quand
  // la page la connaît mieux que la fiche (téléservice rattaché à une fiche F…). Rend [{ ico, texte, titre?, lien? }].
  function detailSymboles(r, meta = {}, opt = {}) {
    const S = symboles(r, meta); if (!S.voies.length) return [];
    // opt.avant === false : la carte n'affiche pas « Avant de commencer » (« Démarches possibles ») ; tout va dans le « ? »,
    // y compris le lien vers le formulaire à vide de Démarche Numérique.
    const A = opt.avant === false ? { lignes: [] } : avantDeCommencer(r, meta), dansAvant = (cle) => A.lignes.some((l) => l.cle === cle);
    const min = (t) => t.charAt(0).toLowerCase() + t.slice(1), org = r.on || r.oa || r.o || "";
    // « ls » : site d'origine d'un lien qui menait à une page de connexion (le lien mène alors à la fiche service-public).
    const site = r.k === "dn" ? "Démarche Numérique" : siteLisible(opt.site || r.ls || r.l);
    const det = S.voies.map((voie, i) => ({ ico: ICO[voie[0]],
      texte: MODES_COURT[voie[0]] + (voie[0] === "en_ligne" && site ? `, sur ${site}` : "") + voie.slice(1).map((m) => ", " + min(MODES_LIB[m])).join("")
        + (!S.sur && i === S.voies.length - 1 ? " (à vérifier sur la fiche)" : "") }));
    if (opt.avant === false && r.k === "dn" && r.u) {
      const base = /^https?:/.test(r.u) ? r.u : "https://demarche.numerique.gouv.fr/commencer/" + encodeURIComponent(r.u);
      det.push({ ico: ICO.formulaire, texte: "", lien: { texte: "Voir le formulaire", url: base.replace(/\/$/, "") + "/dossier_vide",
        titre: "Pour lire toutes les questions avant de commencer, pas pour le remplir", apres: pdfNonAccessible(meta) ? "(PDF non accessible)" : "(PDF)" } });
    }
    for (const x of S.simp) {
      if (x.cle === "fc") det.push({ ico: ICO.fc, texte: `Connexion avec ${x.texte}` });
      else if (x.cle === "rec" && !dansAvant("donnees")) det.push({ ico: ICO.rec, texte: `Données récupérées : ${[...new Set(r.pre || [])].filter((p) => RECUPERE[p]).map((p) => PRE_COURT[p]).join(", ")}` });
    }
    if (S.acc && !dansAvant("accessibilite")) det.push({ ico: ICO.acc, texte: S.acc.court, titre: S.acc.titre || S.acc.detail });
    if (r.crt && !dansAvant("carte")) det.push({ ico: ICO.carte, texte: "Contient une carte à manipuler", titre: CARTE_PHRASE });
    for (const v of S.vig) det.push({ ico: ICO[v.motif], texte: `${v.texte} (${v.k} retours)`, titre: v.detail });
    if (S.delais && !dansAvant("delais")) det.push({ ico: ICO.delais, texte: "Délais :", lien: { texte: "voir les statistiques", url: S.delais.url, titre: NOUVEL_ONGLET } });
    // Démarche passée en nationale : la ligne affiche l'entité qui la publie (Sirene) ; l'organisme déclaré est rappelé ici.
    if (r.k === "dn" && r.on) det.push({ ico: ICO.organisme, texte: `Déclarée par : ${r.oa || r.o}`, titre: `Publiée par ${/^Ministère /.test(r.on) ? "le " + min(r.on) : r.on} (base Sirene), pour toute la France`, organisme: true });
    else if (r.k === "dn" && org.length > 50) det.push({ ico: ICO.organisme, texte: org, organisme: true });
    return det;
  }
  const api = { casParticulierTitre, annexeNommee, annexe, ageInadapte, titreIdentite, chargerTitres, ensuiteTitres, besoins, chargerBesoins, chargerSigles, sensSigle, departementsEnLigne, titreSansTerritoire, communePrincipale, contactAnnuaire, ligneContactHtml, boutonsConnexion, casParticulier, libellesUniques, libelleRessource, corriger, detailSymboles, siteLisible, ICO, PRE_COURT, MAX_AVANT, statsUrl, DELAIS_TEXTE, build, jumellesDe, MODELES, search, norm, toks, pertinence, lieux, chargerCommunes, analyse, choisir, principalDe, departementConnu, sure, titreSur, termeAuTitre, termesAuTitre, reponseLigne, avantDeCommencer, symboles, simplicite, RECUPERE, voiesTexte, MODES_LIB, MODES_COURT, MOTIFS_LIB, ACC_LIB, CARTE_PHRASE, REGLE_TITRE: "d", regroupements: new Map(), region: null, REGIONS };
  if (typeof module !== "undefined") module.exports = api; else root.Moteur = api;
})(this);
