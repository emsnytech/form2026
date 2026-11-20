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
  };
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
  function queryToks(s) {
    const out = [];
    for (const w of norm(s).split(" ")) {
      if (w.length < 2 || STOP.has(w)) continue;
      out.push(stem(w));
      for (const x of SYN[w] || []) out.push(stem(x));
    }
    return [...new Set(out)];
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
      if (r.k === "dn") { s *= 1 + 0.12 * Math.log10(1 + r.n); if (dep && r.dep === dep) s *= 1.15;
        const yrs = (r.t.match(/20[12]\d/g) || []).map(Number); if (yrs.length && Math.max(...yrs) < ANNEE - 1) s *= 0.6; }
      else if (/Téléservice|Formulaire|formulaireNG/.test(r.ty)) s *= 1.1;
      out.push([s, i]);
    }
    out.sort((a, b) => b[0] - a[0]);
    // Département choisi : les démarches locales dont le département est inconnu (po « inc ») restent parmi les
    // résultats retenus, mais placées après les démarches nationales et celles du département.
    const top = out.slice(0, k);
    if (dep) top.sort((a, b) => (ix.recs[a[1]].po === "inc") - (ix.recs[b[1]].po === "inc") || b[0] - a[0]);
    return top.map(([s, i]) => ({ score: +s.toFixed(2), r: ix.recs[i] }));
  }
  const api = { build, search, norm, toks };
  if (typeof module !== "undefined") module.exports = api; else root.Moteur = api;
})(this);
