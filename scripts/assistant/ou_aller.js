// « Où aller » : code postal → commune (API Géo), service local compétent (Annuaire de l'administration, DILA),
// France services la plus proche (liste ANCT), réunis dans la carte « Où aller » de la réponse. assembler_page.py le
// recopie dans la page FORM et dans la version avec assistant, après le script du gabarit, dont il emploie $, esc, IX,
// DATA, ajouterLien, rechercheSimple et afficherResultats.
// Seuls le code postal (API Géo) et le code de la commune (Annuaire) quittent le navigateur. Dans la version avec
// assistant sur claude.ai (window.FORM_SANS_API), aucune API extérieure n'est appelée : la commune vient de la question
// (communes.json), le code postal est masqué, et « Où aller » renvoie vers la recherche de l'Annuaire pour la commune.
(function () {
  const GEO = "https://geo.api.gouv.fr/communes";
  const AN = "https://api-lannuaire.service-public.gouv.fr/api/explore/v2.1/catalog/datasets/";
  const JOURS = ["dimanche", "lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi"];
  const SEMAINE = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"];
  const PLM = new Set(["75056", "69123", "13055"]); // Paris, Lyon, Marseille : l'arrondissement est retenu
  let COMMUNE = null, TABLE = null, FS = null, LISTE = [];
  // Origine de la liste affichée, donnée par le gabarit : « simple » (recherche simple, classement brut du moteur) ou
  // « citee » (réponse préparée ou conversation : démarches déjà retenues par l'assistant).
  const origine = () => window.ORIGINE_RESULTATS || "simple";
  // Une précision de lieu relance la recherche simple ; une réponse citée garde sa liste et se redécore.
  // La page donne la réponse à rejouer (recherche simple, ligne de l'accueil) dans window.relancerReponse.
  const relancer = () => { if (typeof window.relancerReponse === "function") window.relancerReponse(); else decorer(); };
  const reponseAffichee = () => !$("vue-reponse").hidden;
  const cache = new Map();
  const SANS_API = !!window.FORM_SANS_API;
  // Centre de chaque commune (communes.json) : la France services la plus proche se calcule sans appel à une API.
  const CENTRES = new Map();

  const norm = (s) => (s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[’`]/g, "'").replace(/\s+/g, " ");
  const motEntier = (txt, idx) => new RegExp("(^|[^a-z0-9])" + norm(idx).replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "($|[^a-z0-9])").test(txt);
  const hm = (s) => (s || "").slice(0, 5);
  const memo = (k, f) => { if (!cache.has(k)) cache.set(k, f().catch((e) => { cache.delete(k); throw e; })); return cache.get(k); };
  const json = (u) => fetch(u).then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); });
  const lit = (v) => { if (typeof v !== "string") return v || []; try { return JSON.parse(v); } catch (e) { return v; } };
  const carte = (lat, lon) => `https://www.openstreetmap.org/?mlat=${lat}&mlon=${lon}#map=17/${lat}/${lon}`;

  fetch(DATA + "types_guichets.json").then((r) => r.json()).then((t) => { TABLE = t; decorer(); }).catch(() => {});
  // Communes, pour que le moteur reconnaisse un lieu dans la question (Moteur.lieux) et que la page le propose.
  fetch(DATA + "communes.json").then((r) => r.json()).then((d) => {
    Moteur.chargerCommunes(d);
    const C = Object.fromEntries(d.champs.map((k, i) => [k, i]));
    if (C.lat !== undefined) for (const c of d.communes) if (c[C.lat] !== null) CENTRES.set(c[C.code], [c[C.lat], c[C.lon]]);
    decorer();
  }).catch(() => {});

  // ---------- 1. Code postal → commune
  const cp = $("cp"), choix = $("commune"), etat = $("cp-etat");
  if (SANS_API) { cp.closest("label").hidden = true; choix.hidden = true; document.querySelectorAll(".perso-cp").forEach((e) => (e.hidden = true)); }
  // Le bloc « Préciser le public ou le lieu » s'ouvre tout seul quand un lieu est proposé ou qu'un filtre est actif.
  function ouvrirFiltres() { const f = $("filtres"); if (f) f.open = true; }
  ["pub", "dep"].forEach((id) => $(id).addEventListener("change", () => { if ($(id).value) ouvrirFiltres(); }));
  // Un département ou un code postal choisi remplace une région choisie.
  $("dep").addEventListener("change", () => { if ($("dep").value) Moteur.region = null; });
  // Lieu retenu pour « Où aller » : la commune posée ; « Comment j'ai cherché » le cite.
  function poser(c, sansFiltre) {
    COMMUNE = c; window.LIEU_CONNU = c ? `${c.nom} (${c.dep})` : ""; if (c && !sansFiltre) { Moteur.region = null; ouvrirFiltres(); }
    if (c && sansFiltre) { decorer(); return; }
    if (c) { $("dep").value = c.dep; etat.textContent = `${c.nom} (${c.dep})`; } else etat.textContent = "";
    decorer();
  }
  cp.addEventListener("input", async () => {
    const v = cp.value.replace(/\D/g, "").slice(0, 5);
    if (v !== cp.value) cp.value = v;
    choix.hidden = true; if (v.length < 5) { if (COMMUNE) poser(null); return; }
    etat.textContent = "Recherche de la commune…";
    let l;
    try { l = await json(`${GEO}?codePostal=${v}&type=arrondissement-municipal,commune-actuelle&fields=nom,code,codeDepartement,codeEpci,centre&format=json`); }
    catch (e) { etat.textContent = "Commune introuvable pour l'instant (API Géo indisponible)."; return; }
    if (cp.value !== v) return;
    if (l.some((c) => !PLM.has(c.code) && /arrondissement/i.test(c.nom))) l = l.filter((c) => !PLM.has(c.code));
    l = l.map((c) => ({ nom: c.nom, code: c.code, dep: c.codeDepartement, epci: c.codeEpci || "", lon: c.centre.coordinates[0], lat: c.centre.coordinates[1] }));
    if (!l.length) { etat.textContent = "Aucune commune pour ce code postal."; poser(null); return; }
    if (l.length === 1) { poser(l[0]); return; }
    choix.innerHTML = `<option value="">— choisissez votre commune —</option>` + l.map((c, i) => `<option value="${i}">${esc(c.nom)}</option>`).join("");
    choix.onchange = () => poser(choix.value === "" ? null : l[+choix.value]);
    choix.hidden = false; etat.textContent = ""; COMMUNE = null;
    if (new Set(l.map((c) => c.dep)).size === 1) $("dep").value = l[0].dep;
  });
  $("dep").addEventListener("change", () => { if (COMMUNE && $("dep").value !== COMMUNE.dep) { cp.value = ""; choix.hidden = true; poser(null); } });

  // ---------- 2. Où aller : table de correspondance, puis Annuaire
  function regle(r) {
    if (!TABLE) return null;
    if (Moteur.titreIdentite && Moteur.titreIdentite(r)) return { identite: true };   // titres_identite.json
    const txt = norm(r.k === "dn" ? r.o : r.t + " " + (r.th || ""));
    return TABLE.regles.find((g) => g.indices.some((i) => motEntier(txt, i))) || null;
  }
  function services(insee, types) {
    return memo(insee + "|" + types.join(","), async () => {
      const ou = `code_insee_commune="${insee}" AND code_type_service_local IN (${types.map((t) => `"${t}"`).join(",")})`;
      const comp = await json(`${AN}api-lannuaire-administration-locale-competence-geographique/records?where=${encodeURIComponent(ou)}&select=code_type_service_local,id_service_local&limit=20`);
      const ids = [];
      for (const t of types) { const x = comp.results.find((c) => c.code_type_service_local === t); const l = x ? lit(x.id_service_local) : []; if (l[0]) ids.push(l[0]); }
      if (!ids.length) return [];
      const ou2 = ids.map((i) => `id="${i}"`).join(" OR ");
      const sv = await json(`${AN}api-lannuaire-administration/records?where=${encodeURIComponent(ou2)}&select=id,nom,adresse,plage_ouverture,telephone,adresse_courriel,url_service_public&limit=20`);
      return ids.map((i) => sv.results.find((s) => s.id === i)).filter(Boolean);
    });
  }
  function horairesAnnuaire(plages) {
    const sem = Object.fromEntries(SEMAINE.map((j) => [j, []]));
    for (const p of lit(plages)) {
      const a = SEMAINE.indexOf(norm(p.nom_jour_debut)), b = SEMAINE.indexOf(norm(p.nom_jour_fin || p.nom_jour_debut));
      if (a < 0) continue;
      const h = [[p.valeur_heure_debut_1, p.valeur_heure_fin_1], [p.valeur_heure_debut_2, p.valeur_heure_fin_2]].filter(([d, f]) => d && f).map(([d, f]) => `${hm(d)}–${hm(f)}`).join(", ");
      for (let i = a; i <= (b < a ? a : b); i++) if (h) sem[SEMAINE[i]].push(h);
    }
    return Object.fromEntries(SEMAINE.map((j) => [j, sem[j].join(", ")]));
  }
  function blocHoraires(sem) {
    if (!Object.values(sem).some(Boolean)) return `<div class="ou-h">Horaires non publiés : voir la fiche officielle.</div>`;
    const j = JOURS[new Date().getDay()];
    return `<div class="ou-h"><b>Aujourd'hui (${j})&nbsp;:</b> ${esc(sem[j] || "fermé")}</div><details><summary>Horaires de la semaine</summary><ul>${SEMAINE.map((d) => `<li>${d}&nbsp;: ${esc(sem[d] || "fermé")}</li>`).join("")}</ul></details>`;
  }
  const lienTel = (t) => { const m = t.match(/^([+\d][\d .]*\d)(.*)$/); return m ? `<a href="tel:${esc(m[1].replace(/[^\d+]/g, ""))}">${esc(m[1])}</a>${esc(m[2])}` : esc(t); };
  const lienMail = (m) => `<a href="mailto:${esc(m)}">${esc(m)}</a>`;
  // Les contacts affichés viennent de deux sources officielles seulement, toujours nommées sous le contact.
  function contacts(tels, mails, source, fiche) {
    const l = [];
    if (tels.length) l.push("Tél.&nbsp;: " + tels.map(lienTel).join(", "));
    if (mails.length) l.push("Courriel&nbsp;: " + mails.map(lienMail).join(", "));
    const signaler = fiche ? ` · <a class="signaler" href="${esc(fiche)}" target="_blank" rel="noopener">Signaler une erreur</a>` : "";
    return (l.length ? `<div class="ou-c">${l.join(" · ")}</div>` : "") + `<div class="ou-src">Source&nbsp;: ${source}${signaler}</div>`;
  }
  function htmlService(s) {
    const a = lit(s.adresse)[0] || {};
    const adr = [a.numero_voie, a.complement1, a.complement2, [a.code_postal, a.nom_commune].filter(Boolean).join(" ")].filter(Boolean).join(", ");
    const tels = lit(s.telephone).filter((t) => t.valeur).map((t) => t.valeur + (t.description ? ` (${t.description})` : ""));
    const mails = (s.adresse_courriel || "").split(/[;,\s]+/).filter((m) => m.includes("@"));
    const liens = [a.latitude && a.longitude ? `<a href="${carte(a.latitude, a.longitude)}" target="_blank" rel="noopener">Voir sur la carte ↗</a>` : "",
      s.url_service_public ? `<a href="${esc(s.url_service_public)}" target="_blank" rel="noopener">Fiche officielle du service ↗</a>` : ""].filter(Boolean).join("");
    if (s.url_service_public) ajouterLien(s.nom, s.url_service_public, "Annuaire de l'administration (DILA)");
    return `<div class="ou-s"><strong>${esc(s.nom)}</strong>${adr ? `<div>${esc(adr)}</div>` : ""}${blocHoraires(horairesAnnuaire(s.plage_ouverture))}${contacts(tels, mails, "Annuaire de l'administration (DILA)", s.url_service_public)}<div class="links">${liens}</div></div>`;
  }
  // Portée d'une démarche en ligne (champ « po » de l'index) ; un index plus ancien, sans ce champ, confond nationale et inconnue.
  const portee = (r) => r.po || (r.dep ? "dep" : "nat");
  // Une démarche en ligne n'a de guichet local que si elle relève du département de l'usager : une démarche nationale
  // ou d'un autre département n'est pas reçue par le service de sa commune.
  const duDepartement = (r, c) => r.k === "dn" && !!r.dep && r.dep === c.dep;
  // Sans API : lien vers la recherche officielle de l'Annuaire pour la commune (résultats classés par distance).
  function lienAnnuaire(c, quoi) {
    const u = `https://lannuaire.service-public.gouv.fr/recherche?whoWhat=${encodeURIComponent(quoi || "")}&where=${encodeURIComponent(c.nom + " (" + c.dep + ")")}`;
    ajouterLien(`Annuaire de l'administration : ${quoi ? quoi + ", " : ""}${c.nom}`, u, "Annuaire de l'administration (DILA)");
    return `<p><a href="${esc(u)}" target="_blank" rel="noopener">Trouver le guichet compétent sur l'Annuaire de l'administration</a>${quoi ? ` <span class="meta">(${esc(quoi)}, ${esc(c.nom)})</span>` : ""}</p>`;
  }

  // ---------- 2 bis. Service local : la première des cartes en tête de réponse (votre démarche, aussi pour vous,
  // comprendre ; window.CARTES_TETE, donné par le gabarit) qui a un guichet dans la table. Une démarche en ligne n'en a que si elle relève du département de l'usager.
  async function serviceLocal(el, c) {
    el.innerHTML = "";
    if (!c || !TABLE) return;
    const r = (window.CARTES_TETE || LISTE.slice(0, 3)).find((x) => x && portee(x) !== "inc" && regle(x) && (x.k !== "dn" || duDepartement(x, c)));
    if (!r) return;
    const g = regle(r);
    // Carte d'identité, passeport : pré-demande en ligne, puis n'importe quelle mairie équipée ; pas de guichet par commune
    // (la ligne « Ensuite… » de la carte le dit ; titres_identite.json).
    if (g.identite) { el.innerHTML = ""; majOu(); return; }
    if (SANS_API) { el.innerHTML = lienAnnuaire(c, g.libelle); majOu(); return; }
    // Le type de la table ne sert qu'à choisir le guichet : la carte affiche le nom que renvoie l'Annuaire.
    el.innerHTML = `<p class="ou-src">Recherche dans l'Annuaire de l'administration…</p>`; majOu();
    let l;
    try { l = await services(c.code, g.types); } catch (e) { el.innerHTML = `<p class="ou-src">L'Annuaire de l'administration ne répond pas pour l'instant.</p>`; return; }
    if (COMMUNE !== c) return;
    el.innerHTML = l.length ? `${l.map(htmlService).join("")}` : "";
    majOu();
  }

  // ---------- 3. France services la plus proche
  // Une fois la liste chargée, le cadre « Ce que la démo couvre » du gabarit affiche le nombre de structures.
  const chargerFS = () => memo("fs", () => json(DATA + "france_services.json").then((d) => {
    window.NFS = d.structures.length; if (typeof window.majCadre === "function") window.majCadre(window.NFS); return d; }));
  function km(a, b, c, d) {
    const R = 6371, r = Math.PI / 180, x = Math.sin((c - a) * r / 2) ** 2 + Math.cos(a * r) * Math.cos(c * r) * Math.sin((d - b) * r / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(x));
  }
  function htmlFS(f, C, d) {
    const v = (k) => f[C[k]];
    const sem = Object.fromEntries(FS.jours.map((j, i) => [j, (v("horaires")[i] || "").replace(/ - /g, "–").replace(/ \/ /g, ", ")]));
    const nature = /itin|bus/i.test(v("format")) ? " · structure itinérante" : "";
    if (v("fiche")) ajouterLien(v("nom"), v("fiche"), "France services (ANCT)");
    const adr = [v("adresse"), v("complement"), v("code_postal") + " " + v("commune")].filter(Boolean).join(", ");
    return `<div class="ou-s"><strong>${esc(v("nom"))}</strong> <span class="meta">à ${d.toLocaleString("fr-FR", { maximumFractionDigits: 1 })} km${nature}</span><div>${esc(adr)}</div>${blocHoraires(sem)}`
      + (v("rdv") === "Oui" ? `<div class="meta">Prise de rendez-vous possible.</div>` : "")
      + contacts(v("telephone") ? [v("telephone")] : [], (v("courriel") || "").split(/[;,\s]+/).filter((m) => m.includes("@")), "France services (ANCT)", v("fiche"))
      + `<div class="links"><a href="${carte(v("lat"), v("lon"))}" target="_blank" rel="noopener">Voir sur la carte ↗</a>`
      + (v("fiche") ? `<a href="${esc(v("fiche"))}" target="_blank" rel="noopener">Fiche officielle ↗</a>` : "") + `</div></div>`;
  }
  async function franceServices(el) {
    // Public : encadré ou ligne pour un particulier ou un public non précisé ; ligne seulement pour une entreprise ;
    // rien pour une collectivité ou une association.
    const pub = $("pub").value;
    el.className = ""; el.innerHTML = "";
    if (pub === "collectivite" || pub === "association") return;
    // « Aucune démarche en ligne pertinente » : parmi les 5 premiers résultats, aucune démarche nationale (po « nat ») ni du
    // département de l'usager (sans département connu : d'aucun département) qui soit pertinente pour la question, au sens
    // de Moteur.pertinence (moitié du meilleur score, deux termes de la question repris). Une démarche de département
    // inconnu ne compte pas. Le seuil sert à cette règle seulement : il ne change ni le classement ni l'affichage.
    const dep = COMMUNE ? COMMUNE.dep : $("dep").value;
    // Le seuil de pertinence ne vaut que pour la recherche simple : une démarche citée par l'assistant est déjà retenue.
    const P = origine() === "simple" ? Moteur.pertinence(IX, $("q").value, { pub, dep }) : { pertinente: () => true };
    const enLigne = pub === "entreprise" || LISTE.slice(0, 5).some((r) => r && r.k === "dn" && (portee(r) === "nat" || (portee(r) === "dep" && (!dep || r.dep === dep))) && P.pertinente(r.id));
    el.className = enLigne ? "fs-pied" : "fs-fort";
    const c = COMMUNE;
    if (!c) {
      // Carte d'identité, passeport en tête : on ne demande pas la commune (titres_identite.json).
      const tete = (window.CARTES_TETE || [])[0];
      if ((tete && Moteur.titreIdentite && Moteur.titreIdentite(tete)) || window.BESOINS_SANS_LIEU) { majOu(); return; }
      if (!enLigne) el.innerHTML = `<div class="ou-t">Une France services peut vous aider à faire cette démarche</div><p>Indiquez votre code postal pour trouver la plus proche, ou consultez la <a href="https://www.france-services.gouv.fr/" target="_blank" rel="noopener">carte des France services</a>.</p>`;
      majOu(); return;
    }
    try { FS = await chargerFS(); } catch (e) { return; }
    if (COMMUNE !== c) return;
    const C = Object.fromEntries(FS.champs.map((k, i) => [k, i]));
    const proches = FS.structures.map((f) => [km(c.lat, c.lon, f[C.lat], f[C.lon]), f]).sort((a, b) => a[0] - b[0]).slice(0, 3);
    if (!proches.length) return;
    const src = `<p class="ou-src" title="Liste des structures labellisées France services (ANCT, data.gouv.fr${FS.date ? ", " + esc(FS.date.split("-").reverse().join("/")) : ""}), depuis le centre de ${esc(c.nom)}">Distance à vol d'oiseau.</p>`;
    const [d, f] = proches[0], premiere = htmlFS(f, C, d);
    const suivantes = proches.slice(1).map(([d2, f2]) => htmlFS(f2, C, d2)).join("");
    if (enLigne) {
      el.innerHTML = `<details><summary><b>Besoin d'aide pour faire la démarche&nbsp;?</b> La France services la plus proche&nbsp;: ${esc(f[C.nom])}, à ${d.toLocaleString("fr-FR", { maximumFractionDigits: 1 })} km.</summary>${premiere}${suivantes}${src}</details>`;
    } else {
      el.innerHTML = `<div class="ou-t">Une France services peut vous aider à faire cette démarche</div>${premiere}<details><summary>Les deux suivantes</summary>${suivantes}</details>${src}`;
    }
    majOu();
  }

  // ---------- CCAS : une fois par réponse, si (1) le public est particulier ou non précisé, (2) la question ou le premier
  // résultat relève des impayés, de l'énergie, de l'eau, d'une aide financière ou sociale, d'un secours ou de la précarité
  // (« logement » ou « facture » seuls ne suffisent pas), (3) une commune est connue.
  const THEMES_CCAS = /(^| )(impaye|impayes|energi|energie|electr|electricite|gaz|chauffage|fioul|eau|aide financiere|aides financieres|aide sociale|aides sociales|action sociale|secours|precarite|precaire)( |$)/;
  async function ccas(el) {
    el.innerHTML = "";
    const c = COMMUNE, pub = $("pub").value, q = $("q").value;
    if (!c || (pub && pub !== "particulier")) return;
    const termes = Moteur.analyse ? [...Moteur.analyse(q).termes.values()].flatMap((g) => [...g]).join(" ") : "";
    const N = Moteur.norm, premier = LISTE[0] ? N(LISTE[0].t + " " + (LISTE[0].th || "")) : "";
    if (![N(q) + " " + termes, premier].some((s) => THEMES_CCAS.test(s))) return;
    if (SANS_API) { el.innerHTML = `<div class="ou-t">Aide sociale de votre commune</div>` + lienAnnuaire(c, "CCAS"); majOu(); return; }
    let l; try { l = await services(c.code, ["ccas"]); } catch (e) { return; }
    if (COMMUNE !== c || !l.length) return;
    el.innerHTML = `<div class="ou-t">Aide sociale de votre commune</div>${l.map(htmlService).join("")}`;
    majOu();
  }

  // ---------- Carte « Où aller » : service local, CCAS, France services ; masquée si aucune des trois n'a de contenu.
  function carteOu() {
    const el = $("carte-ou");
    if (!$("ou-service")) el.innerHTML = `<h2 id="h-ou">Où aller</h2><p class="org" id="ou-pour"></p><div id="ou-service"></div><div id="ccas-ou"></div><div id="fs-aide"></div>`;
    $("ou-pour").textContent = COMMUNE ? `Pour ${COMMUNE.nom} (${COMMUNE.dep})` : "";
    return el;
  }
  function majOu() { const el = $("carte-ou"); el.hidden = !["ou-service", "ccas-ou", "fs-aide"].some((id) => $(id) && $(id).innerHTML.trim()); }

  // ---------- Pastille de lieu, sous la question. Un lieu reconnu dans la phrase est proposé, jamais imposé comme filtre ;
  // s'il désigne une seule commune, il sert à « Où aller ». Un code postal saisi prime.
  function pastille() {
    const el = $("rep-pastille"); el.className = "pastilles"; el.innerHTML = "";
    if (!reponseAffichee() || !Moteur.lieux) return;
    const changer = ` · <button type="button" class="lien-changer" id="lieu-changer">changer</button>`;
    const brancherChanger = () => { const ch = $("lieu-changer"); if (ch) ch.addEventListener("click", () => { ouvrirFiltres(); vueAccueilFiltres(); }); };
    // Démarches locales sans territoire connu (window.DEMANDER_LIEU, donné par la page) : la question du lieu d'abord.
    if (window.DEMANDER_LIEU && !$("dep").value && (!COMMUNE || COMMUNE.devine)) {
      el.className = "";
      if (SANS_API) {
        el.innerHTML = `<div class="question-lieu"><label for="dep-res"><b>${esc(window.DEMANDER_LIEU)}</b></label><select id="dep-res">${$("dep").innerHTML}</select></div>`;
        $("dep-res").value = "";
        $("dep-res").addEventListener("change", () => { $("dep").value = $("dep-res").value; if ($("dep").value) relancer(); });
      } else {
        el.innerHTML = `<div class="question-lieu"><label for="cp-res"><b>${esc(window.DEMANDER_LIEU)}</b></label><div class="row"><input id="cp-res" class="cp-res" inputmode="numeric" autocomplete="postal-code" maxlength="5" placeholder="code postal"> <span class="meta">ou</span> <select id="dep-res" aria-label="Votre département">${$("dep").innerHTML}</select></div></div>`;
        $("dep-res").value = "";
        $("dep-res").addEventListener("change", () => { $("dep").value = $("dep-res").value; if ($("dep").value) relancer(); });
        const c2 = $("cp-res");
        c2.addEventListener("input", () => { cp.value = c2.value.replace(/\D/g, "").slice(0, 5); cp.dispatchEvent(new Event("input"));
          if (cp.value.length === 5) setTimeout(() => { if (COMMUNE) relancer(); }, 1500); });
      }
      return;
    }
    if (COMMUNE && !COMMUNE.devine) {
      el.innerHTML = `<span class="meta">Résultats adaptés à</span> <span class="pastille pastille-fixe">${esc(COMMUNE.nom)} (${esc(COMMUNE.dep)})</span>${changer}`;
      brancherChanger(); return;
    }
    const A = Moteur.lieux($("q").value), L = A.lieux[0];
    // Région choisie (clic sur « Bretagne ? ») : la pastille dit que les résultats sont limités, et permet de retirer le filtre.
    if (Moteur.region) {
      el.innerHTML = `<span class="meta">Résultats limités à la région</span> <span class="pastille pastille-fixe">${esc(Moteur.region.nom)}</span> · <button type="button" class="lien-changer" id="region-retirer">retirer</button>`;
      $("region-retirer").addEventListener("click", () => { Moteur.region = null; relancer(); });
      return;
    }
    // Région reconnue dans la phrase, sans commune ni département : pastille « Bretagne ? » ; un clic filtre sur ses départements.
    if (!L && A.regions && A.regions[0] && !$("dep").value) {
      const Rg = A.regions[0];
      el.innerHTML = `<span class="meta">Région repérée dans votre question&nbsp;:</span> <button type="button" class="pastille" id="region-choisir">${esc(Rg.nom)}&nbsp;?</button>`;
      $("region-choisir").addEventListener("click", () => { Moteur.region = { nom: Rg.nom, deps: Rg.deps }; relancer(); });
      return;
    }
    // Carte d'identité, passeport en tête : la commune n'est pas demandée (la mairie se choisit ensuite, sur la carte de l'ANTS).
    const tete = (window.CARTES_TETE || [])[0];
    if (!L && tete && Moteur.titreIdentite && Moteur.titreIdentite(tete)) return;
    // « Vos démarches » dont aucune ligne n'a besoin d'un lieu (opposition bancaire, titres d'identité…) : pas de code postal demandé.
    if (!L && window.BESOINS_SANS_LIEU) return;
    if (!L) {
      // Ni code postal, ni département, ni lieu reconnu : les démarches d'un département sont rétrogradées (×0,8 dans le
      // moteur) ; la page invite à préciser la commune.
      if (!$("dep").value && SANS_API) {
        el.innerHTML = `<span class="meta">Précisez votre commune pour voir où aller.</span>`;
      } else if (!$("dep").value) {
        el.innerHTML = `<label class="meta" for="cp-res">Précisez votre commune pour voir où aller&nbsp;:</label> `
          + `<input id="cp-res" class="cp-res" inputmode="numeric" autocomplete="postal-code" maxlength="5" placeholder="code postal">`;
        const c2 = $("cp-res");
        c2.addEventListener("input", () => { cp.value = c2.value.replace(/\D/g, "").slice(0, 5); cp.dispatchEvent(new Event("input"));
          if (cp.value.length === 5) setTimeout(() => { if (COMMUNE) relancer(); }, 1500); });
      } else if (COMMUNE === null) {
        el.innerHTML = `<span class="meta">Département choisi&nbsp;:</span> <span class="pastille pastille-fixe">${esc($("dep").value)} ${esc(DEPNAME[$("dep").value] || "")}</span>${changer}`;
        brancherChanger();
      }
      return;
    }
    // Lieu reconnu, sans département choisi : le moteur favorise déjà les démarches de son département (×1,3) ; la pastille le dit.
    const adapte = !$("dep").value;
    const boutons = L.candidats.map((c, i) => `<button type="button" class="pastille" data-i="${i}">${esc(c.nom)} (${esc(c.dep)})${adapte && !i ? "" : "&nbsp;?"}</button>`);
    el.innerHTML = adapte
      ? `<span class="meta">Résultats adaptés à</span> ${boutons[0]}${boutons.length > 1 ? ` <span class="meta">ou</span> ${boutons.slice(1).join(" ")}` : ""}${changer}`
      : `<span class="meta">Lieu repéré dans votre question&nbsp;:</span> ${boutons.join(" ")}`;
    el.querySelectorAll("button.pastille").forEach((b) => b.addEventListener("click", async () => {
      const c = await geo(L.candidats[+b.dataset.i]); if (!c) return;
      cp.value = ""; choix.hidden = true; poser(c); relancer();
    }));
    brancherChanger();
    // Une seule commune reconnue, sans code postal ni département choisi : elle sert à « Où aller », sans filtrer les résultats.
    if (adapte && L.candidats.length === 1 && (!COMMUNE || COMMUNE.devine) && (!COMMUNE || COMMUNE.code !== L.candidats[0].code)) {
      geo(L.candidats[0]).then((c) => { if (c && !COMMUNE) { c.devine = true; poser(c, true); } });
    }
  }
  const geo = (c) => CENTRES.has(c.code)
    ? Promise.resolve({ nom: c.nom, code: c.code, dep: c.dep, epci: "", lat: CENTRES.get(c.code)[0], lon: CENTRES.get(c.code)[1] })
    : SANS_API ? Promise.resolve(null) : json(`${GEO}/${encodeURIComponent(c.code)}?fields=nom,code,codeDepartement,codeEpci,centre&format=json`)
    .then((g) => ({ nom: g.nom, code: g.code, dep: g.codeDepartement, epci: g.codeEpci || "", lon: g.centre.coordinates[0], lat: g.centre.coordinates[1] })).catch(() => null);
  // « changer » : retour au champ, bloc « Préciser le public ou le lieu » ouvert, sur le code postal.
  function vueAccueilFiltres() { $("vue-reponse").hidden = true; $("vue-accueil").hidden = false; ouvrirFiltres(); const f = SANS_API ? $("dep") : cp; f.focus(); f.scrollIntoView({ block: "center" }); }

  function decorer() {
    if (typeof IX === "undefined" || !IX || !reponseAffichee()) return;
    pastille(); carteOu();
    serviceLocal($("ou-service"), COMMUNE); ccas($("ccas-ou")); franceServices($("fs-aide")); majOu();
    if (window.majCherche) window.majCherche();
  }
  const afficher = afficherResultats;
  afficherResultats = function (liste, q, ...suite) {
    // Une commune devinée dans une question précédente ne vaut pas pour la suivante.
    if (COMMUNE && COMMUNE.devine) { COMMUNE = null; window.LIEU_CONNU = ""; }
    LISTE = liste || []; afficher(liste, q, ...suite); decorer();
  };
})();
