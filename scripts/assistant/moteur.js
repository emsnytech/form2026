// Moteur de recherche local (BM25) sur l'index FORM 2026 + DILA.
// Utilisable dans la page et sous node pour les tests.
(function (root) {
  const STOP = new Set(("a au aux avec ce ces dans de des du elle en et eux il je la le les leur lui ma mais me meme mes moi mon ne nos notre nous on ou par pas pour qu que qui sa se ses son sur ta te tes toi ton tu un une vos votre vous c d j l m n s t y ete etre avoir ai as avons avez ont suis es est sommes etes sont faire fait comment quoi quel quelle quels quelles dois doit veux veut voudrais souhaite souhaiterais besoin peux peut faut il ya y-a cela ca cet cette tout tous toute toutes plus moins tres aussi si alors donc car comme chez sans sous entre vers apres avant depuis lors quand ou bien mon ma mes demande demarche demarches habite habiter habitons habitez").split(" "));
  const SYN = {
    bebe: ["naissance"], enfant: ["enfant"], boulot: ["emploi"], travail: ["emploi", "travail"], chomage: ["emploi", "chomage"],
    demenage: ["demenagement", "adresse"], demenager: ["demenagement", "adresse"], aide: ["aide", "subvention", "allocation"],
    argent: ["aide", "subvention", "financement"], asso: ["association"], boite: ["entreprise"], societe: ["entreprise"],
    voiture: ["vehicule", "immatriculation"], auto: ["vehicule"], carte: ["carte"], fete: ["manifestation"], brocante: ["vide", "grenier", "manifestation"],
    handicap: ["handicap", "mdph"], logement: ["logement"], ecole: ["scolaire", "scolarisation", "ecole"], fac: ["universite", "etudes"],
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
    degradation: ["degradation", "dommage", "indemnisation"], pillage: ["degradation", "dommage", "indemnisation"],
    vandalisme: ["degradation", "dommage", "indemnisation"], emeute: ["degradation", "dommage", "indemnisation"],
    emeutes: ["degradation", "dommage", "indemnisation"], manifestation: ["degradation", "dommage", "indemnisation"],
    manifestations: ["degradation", "dommage", "indemnisation"],                                     // dégradations
  };
  // Expressions de plusieurs mots, reconnues avant le découpage en mots (sur le texte normalisé).
  const EXPRESSIONS = [
    [["n arrive plus a payer", "arrive plus a payer", "ne peux plus payer", "ne peut plus payer", "ne pouvons plus payer", "retard de paiement",
      "facture impayee", "factures impayees"], ["impaye", "paiement"]],
    [["fonds d urgence"], ["calamite", "_fonds_d_urgence"]],
    [["vitrine cassee", "vitrine brisee"], ["degradation", "dommage", "indemnisation"]],
    [["verifier le titre de sejour", "verifier son titre de sejour", "verifier un titre de sejour", "verifier les titres de sejour",
      "salarie etranger", "salaries etrangers", "embaucher un etranger", "embaucher un salarie etranger", "embaucher des etrangers"],
     ["verification", "prealable", "embauche", "autorisation", "travail"]],
    // Renouveler son titre de séjour : la démarche se fait auprès du bureau des étrangers, souvent sur rendez-vous.
    [["renouveler mon titre de sejour", "renouveler son titre de sejour", "renouveler le titre de sejour", "renouveler ma carte de sejour",
      "renouvellement de mon titre de sejour", "renouvellement du titre de sejour", "renouvellement de titre de sejour"],
     ["renouvellement", "etrangers", "rendez"]],
  ].flatMap(([formes, vers]) => formes.map((f) => [f, vers]));
  function norm(s) {
    return (s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]+/g, " ").trim();
  }
  // Jetons d'expression : indexés quand l'expression figure dans un texte, cherchés par les synonymes (« _… », sans racinisation).
  const JETONS_EXPRESSION = [["fonds d urgence", "_fonds_d_urgence"]];
  function stem(w) {
    if (w[0] === "_") return w;
    if (w.length > 4) w = w.replace(/(s|x)$/, "");
    return w.length > 6 ? w.slice(0, 6) : w;
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
  function analyse(s) {
    let n = " " + norm(s) + " ";
    const termes = new Map(), L = lieux(s);
    // Une expression reconnue compte pour un terme ; plusieurs expressions de même sens, pour un seul.
    for (const [f, vers] of EXPRESSIONS) if (n.includes(" " + f + " ")) termes.set("« " + vers.join(" ") + " »", new Set(vers.map(stem)));
    for (const w of n.trim().split(" ")) {
      if (w.length < 2 || STOP.has(w) || L.mots.has(w)) continue;
      const t = stem(w); if (!termes.has(t)) termes.set(t, new Set([t]));
      for (const x of SYN[w] || []) termes.get(t).add(stem(x));
    }
    return { termes, lieux: L.lieux };
  }
  function queryToks(s) {
    return [...new Set([...analyse(s).termes.values()].flatMap((g) => [...g]))];
  }
  const ANNEE = new Date().getFullYear();
  const EV_LABEL = (ev) => (ev && ev !== "hors_perimetre" ? ev.replace(/_/g, " ") : "");

  function build(recs) {
    const inv = new Map(); const len = new Float32Array(recs.length); let tot = 0;
    recs.forEach((r, i) => {
      const tf = new Map();
      const add = (s, w) => {
        for (const t of toks(s)) tf.set(t, (tf.get(t) || 0) + w);
        if (s) { const n = " " + norm(s) + " "; for (const [e, j] of JETONS_EXPRESSION) if (n.includes(" " + e + " ")) tf.set(j, (tf.get(j) || 0) + w); }
      };
      add(r.t, 3); add(r.d, 1); add(EV_LABEL(r.ev), 1.5);
      if (r.k === "dn") { add(r.o, 0.6); add((r.pj || []).join(" "), 0.4); }
      else { add(r.th, 0.8); add((r.docs || []).join(" "), 0.3); }
      let L = 0; for (const [t, v] of tf) { L += v; if (!inv.has(t)) inv.set(t, []); inv.get(t).push(i, v); }
      len[i] = L; tot += L;
    });
    return { recs, inv, len, avg: tot / recs.length, byId: new Map(recs.map((r, i) => [r.id, i])) };
  }

  const PUBLIC_DN = { particulier: ["particulier", "mixte", "indetermine"], entreprise: ["entreprise", "mixte", "personne_morale", "indetermine"],
    association: ["association", "mixte", "personne_morale", "indetermine"], collectivite: ["collectivite", "personne_morale", "indetermine"] };
  const PUBLIC_SP = { particulier: "Particuliers", entreprise: "Professionnels", association: "Associations", collectivite: null };

  // Publics particuliers repérés dans le titre d'une fiche : [motif sur le titre normalisé, entouré d'espaces].
  // Le même motif, trouvé dans la question, annule la rétrogradation.
  const PUBLICS_PARTICULIERS = [/ etudiant(e|s|es)? | etude(s)? /, / stagiaire(s)? /, / au pair /, / saisonnier(s)? /].map((re) => [re]);
  function search(ix, q, opt = {}) {
    const { pub = "", dep = "", source = "", k = 10, ouvertes = true } = opt;
    const qt = queryToks(q); if (!qt.length) return [];
    const N = ix.recs.length, k1 = 1.2, b = 0.75, sc = new Map(), hit = new Map();
    for (const t of qt) {
      const p = ix.inv.get(t); if (!p) continue;
      const df = p.length / 2, idf = Math.log(1 + (N - df + 0.5) / (df + 0.5));
      for (let j = 0; j < p.length; j += 2) {
        const i = p[j], tf = p[j + 1];
        const s = idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * ix.len[i] / ix.avg));
        sc.set(i, (sc.get(i) || 0) + s); hit.set(i, (hit.get(i) || 0) + 1);
      }
    }
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
        if (depsRegion && r.dep && !depsRegion.includes(r.dep)) continue;
        if (ouvertes && r.fe && r.fe < today) continue;
      } else {
        if (pub && PUBLIC_SP[pub] && !(r.aud || "").includes(PUBLIC_SP[pub])) continue;
        if (pub === "collectivite") continue;
      }
      let s = s0 * (0.5 + 0.5 * hit.get(i) / qt.length); // récompense la couverture de la requête
      if (r.k === "dn") { s *= 1 + 0.12 * Math.log10(1 + r.n); if (dep && r.dep === dep) s *= 1.15; else if (depLieu && r.dep === depLieu) s *= 1.3;
        else if (depsRegion && r.dep && depsRegion.includes(r.dep)) s *= 1.15;
        else if (!dep && !depLieu && !depsRegion && (r.po ? r.po !== "nat" : !!r.dep)) s *= 0.8;   // territoire inconnu : une démarche locale (département connu ou non) passe après
        if (r.dp && r.dp >= ilYaUnAn) s *= 1.15;
        if (r.tc) s *= 0.7;   // titre qui ressemble à un identifiant interne (« Bilan_4BNaap12_… ») : rétrogradé, quelle que soit la portée
        const yrs = (r.t.match(/20[12]\d/g) || []).map(Number); if (yrs.length && Math.max(...yrs) < ANNEE - 1) s *= 0.6; }
      else {
        if (/Téléservice|Formulaire|formulaireNG/.test(r.ty)) s *= 1.1;
        // Fiche réservée à un public particulier (« Étudiant étranger… », « … stagiaire ») que la question ne nomme pas :
        // rétrogradée, pour que la fiche générale passe devant.
        const pp = PUBLICS_PARTICULIERS.find(([re]) => re.test(" " + norm(r.t) + " "));
        if (pp && !pp[0].test(" " + norm(q) + " ")) s *= 0.7;
      }
      out.push([s, i]);
    }
    out.sort((a, b) => b[0] - a[0]);
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
    return c.length && c.every((x) => x.dep === c[0].dep) ? c[0].dep : "";
  }
  // « Votre démarche » : le premier résultat, sauf (1) une démarche en ligne d'un autre département que le département
  // connu, ou de département inconnu quand une autre convient, (2) pour un particulier ou un public non précisé, une démarche réservée aux professionnels. Les écartées restent
  // dans la liste (« Autres pistes »).
  function principalDe(liste, q, opt = {}) {
    const { pub = "", dep = "" } = opt, d = departementConnu(q, dep);
    const ailleurs = (r) => !!d && r.k === "dn" && !!r.dep && r.dep !== d;
    const pro = (r) => (!pub || pub === "particulier") && (RESERVEE_PROS.test(r.t + " " + (r.d || "")) || VARIANTE_EMPLOYEUR.test(r.t));
    // Département connu : une démarche locale de département inconnu (po « inc ») passe après celles du département,
    // nationales et fiches.
    const inc = (r) => !!d && r.k === "dn" && r.po === "inc";
    return liste.find((r) => !ailleurs(r) && !inc(r) && !pro(r)) || liste.find((r) => !ailleurs(r) && !pro(r))
      || liste.find((r) => !ailleurs(r)) || liste[0] || null;
  }
  // Recherche simple de la page : les k premiers résultats, puis, si un département est connu sans être choisi, les 3
  // premières démarches en ligne de ce département (au moins la moitié du meilleur score), puis les 3 premières fiches service-public. Rend la liste et
  // « Votre démarche ».
  function choisir(ix, q, opt = {}) {
    const { pub = "", dep = "", k = 20 } = opt, base = { pub, dep };
    const res = search(ix, q, { ...base, k }), liste = res.map((x) => x.r), reg = api.regroupements;
    const ajoute = (l) => { for (const x of l) if (!liste.includes(x.r)) liste.push(x.r); };
    const d = departementConnu(q, dep), meilleur = res.length ? res[0].score : 0;
    // Démarches du département : seulement celles dont le score atteint la moitié du meilleur score de la recherche.
    if (d && !dep) ajoute(search(ix, q, { ...base, dep: d, source: "dn", k: 3 }).filter((x) => x.score >= meilleur / 2));
    ajoute(search(ix, q, { ...base, source: "sp", k: 3 }));
    api.regroupements = reg;   // les regroupements par organisme sont ceux de la première recherche
    return { liste, principal: principalDe(liste, q, opt), departement: d };
  }
  const api = { build, search, norm, toks, pertinence, lieux, chargerCommunes, analyse, choisir, principalDe, departementConnu, regroupements: new Map(), region: null, REGIONS };
  if (typeof module !== "undefined") module.exports = api; else root.Moteur = api;
})(this);
