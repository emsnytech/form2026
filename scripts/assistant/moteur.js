// Moteur de recherche local (BM25) sur l'index FORM 2026 + DILA.
// Utilisable dans la page et sous node pour les tests.
(function (root) {
  const STOP = new Set(("a au aux avec ce ces dans de des du elle en et eux il je la le les leur lui ma mais me meme mes moi mon ne nos notre nous on ou par pas pour qu que qui sa se ses son sur ta te tes toi ton tu un une vos votre vous c d j l m n s t y ete etre avoir ai as avons avez ont suis es est sommes etes sont faire fait comment quoi quel quelle quels quelles dois doit veux veut voudrais souhaite souhaiterais besoin peux peut faut il ya y-a cela ca cet cette tout tous toute toutes plus moins tres aussi si alors donc car comme chez sans sous entre vers apres avant depuis lors quand ou bien mon ma mes demande demarche demarches").split(" "));
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
    secheresse: ["calamite", "urgence", "fonds"], gel: ["calamite", "urgence", "fonds"], grele: ["calamite", "urgence", "fonds"],
    inondation: ["calamite", "urgence", "fonds"], tempete: ["calamite", "urgence", "fonds"], intemperies: ["calamite", "urgence", "fonds"], // crises
    degradation: ["degradation", "dommage", "indemnisation"], pillage: ["degradation", "dommage", "indemnisation"],
    vandalisme: ["degradation", "dommage", "indemnisation"], emeute: ["degradation", "dommage", "indemnisation"],
    emeutes: ["degradation", "dommage", "indemnisation"], manifestation: ["degradation", "dommage", "indemnisation"],
    manifestations: ["degradation", "dommage", "indemnisation"],                                     // dégradations
  };
  // Expressions de plusieurs mots, reconnues avant le découpage en mots (sur le texte normalisé).
  const EXPRESSIONS = [
    [["n arrive plus a payer", "arrive plus a payer", "ne peux plus payer", "ne peut plus payer", "ne pouvons plus payer", "retard de paiement",
      "facture impayee", "factures impayees"], ["impaye", "paiement"]],
    [["fonds d urgence"], ["calamite", "urgence", "fonds"]],
    [["vitrine cassee", "vitrine brisee"], ["degradation", "dommage", "indemnisation"]],
    [["verifier le titre de sejour", "verifier son titre de sejour", "verifier un titre de sejour", "verifier les titres de sejour",
      "salarie etranger", "salaries etrangers", "embaucher un etranger", "embaucher un salarie etranger", "embaucher des etrangers"],
     ["verification", "prealable", "embauche", "autorisation", "travail"]],
  ].flatMap(([formes, vers]) => formes.map((f) => [f, vers]));
  function norm(s) {
    return (s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]+/g, " ").trim();
  }
  function stem(w) {
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
    "nord sud est ouest centre beaucoup").split(" "));
  const MARQUEURS = [["j", "habite"], ["habite"], ["a"], ["pres", "de"], ["sur"], ["dans"]];
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
    if (!COMMUNES || !w.length) return { lieux: out, mots: new Set() };
    const essai = (i, prio) => {
      for (let n = Math.min(5, w.length - i); n >= 1; n--) {
        const nom = w.slice(i, i + n).join(" ");
        if (COMMUNES.has(nom) && !NON_LIEUX.has(nom) && !STOP.has(nom) && nom.length >= 3 && !pris.has(i)) {
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
    const mots = new Set(out.flatMap((l) => [...l.mots, ...(l.marqueur || [])]));
    return { lieux: out.map((l) => ({ ...l.candidats[0], candidats: l.candidats, mots: l.mots })), mots };
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
      const add = (s, w) => { for (const t of toks(s)) tf.set(t, (tf.get(t) || 0) + w); };
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
    for (const [i, s0] of sc) {
      const r = ix.recs[i];
      if (source && r.k !== source) continue;
      if (r.k === "dn") {
        if (pub && PUBLIC_DN[pub] && !PUBLIC_DN[pub].includes(r.cat)) continue;
        if (dep && r.dep && r.dep !== dep) continue; // garde les démarches nationales (« nat ») et de département inconnu (« inc »)
        if (ouvertes && r.fe && r.fe < today) continue;
      } else {
        if (pub && PUBLIC_SP[pub] && !(r.aud || "").includes(PUBLIC_SP[pub])) continue;
        if (pub === "collectivite") continue;
      }
      let s = s0 * (0.5 + 0.5 * hit.get(i) / qt.length); // récompense la couverture de la requête
      if (r.k === "dn") { s *= 1 + 0.12 * Math.log10(1 + r.n); if (dep && r.dep === dep) s *= 1.15; else if (depLieu && r.dep === depLieu) s *= 1.3;
        if (r.dp && r.dp >= ilYaUnAn) s *= 1.15;
        const yrs = (r.t.match(/20[12]\d/g) || []).map(Number); if (yrs.length && Math.max(...yrs) < ANNEE - 1) s *= 0.6; }
      else if (/Téléservice|Formulaire|formulaireNG/.test(r.ty)) s *= 1.1;
      out.push([s, i]);
    }
    out.sort((a, b) => b[0] - a[0]);
    // Diversité : au plus deux démarches en ligne d'un même organisme avant les autres résultats ; les suivantes passent
    // après (quatre variantes d'un même guichet ne doivent pas masquer une fiche ou une démarche d'une autre source).
    const parOrg = new Map(), gardes = [], reportes = [];
    for (const x of out) {
      const r = ix.recs[x[1]], o = r.k === "dn" ? norm(r.o) : "";
      if (o) { parOrg.set(o, (parOrg.get(o) || 0) + 1); if (parOrg.get(o) > 2) { reportes.push(x); continue; } }
      gardes.push(x);
    }
    out.splice(0, out.length, ...gardes, ...reportes);
    // Département choisi : les démarches locales dont le département est inconnu (po « inc ») restent parmi les
    // résultats retenus, mais placées après les démarches nationales et celles du département.
    const top = out.slice(0, k);
    if (dep) top.sort((a, b) => (ix.recs[a[1]].po === "inc") - (ix.recs[b[1]].po === "inc") || b[0] - a[0]);
    return top.map(([s, i]) => ({ score: +s.toFixed(2), r: ix.recs[i] }));
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
  const api = { build, search, norm, toks, pertinence, lieux, chargerCommunes, analyse };
  if (typeof module !== "undefined") module.exports = api; else root.Moteur = api;
})(this);
