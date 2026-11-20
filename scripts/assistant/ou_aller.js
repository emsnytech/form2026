// « Où aller » : code postal → commune (API Géo), service local compétent (Annuaire de l'administration, DILA),
// France services la plus proche (liste ANCT). Propre à la page FORM : assembler_page.py le recopie dans la page,
// après le script du gabarit, dont il emploie $, esc, IX et showCards.
// Seuls le code postal (API Géo) et le code de la commune (Annuaire) quittent le navigateur.
(function () {
  const GEO = "https://geo.api.gouv.fr/communes";
  const AN = "https://api-lannuaire.service-public.gouv.fr/api/explore/v2.1/catalog/datasets/";
  const JOURS = ["dimanche", "lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi"];
  const SEMAINE = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"];
  const PLM = new Set(["75056", "69123", "13055"]); // Paris, Lyon, Marseille : l'arrondissement est retenu
  let COMMUNE = null, TABLE = null, FS = null, LISTE = [];
  const cache = new Map();

  const norm = (s) => (s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[’`]/g, "'").replace(/\s+/g, " ");
  const motEntier = (txt, idx) => new RegExp("(^|[^a-z0-9])" + norm(idx).replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "($|[^a-z0-9])").test(txt);
  const hm = (s) => (s || "").slice(0, 5);
  const memo = (k, f) => { if (!cache.has(k)) cache.set(k, f().catch((e) => { cache.delete(k); throw e; })); return cache.get(k); };
  const json = (u) => fetch(u).then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); });
  const lit = (v) => { if (typeof v !== "string") return v || []; try { return JSON.parse(v); } catch (e) { return v; } };
  const carte = (lat, lon) => `https://www.openstreetmap.org/?mlat=${lat}&mlon=${lon}#map=17/${lat}/${lon}`;

  fetch("donnees/assistant/types_guichets.json").then((r) => r.json()).then((t) => { TABLE = t; decorer(); }).catch(() => {});

  // ---------- 1. Code postal → commune
  const cp = $("cp"), choix = $("commune"), etat = $("cp-etat");
  function poser(c) {
    COMMUNE = c;
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
    const ti = TABLE.titres_identite;
    if (r.k === "sp" && r.th === ti.theme && ti.indices.some((i) => motEntier(norm(r.t), i))) return { identite: true };
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
    return `<div class="ou-s"><strong>${esc(s.nom)}</strong>${adr ? `<div>${esc(adr)}</div>` : ""}${blocHoraires(horairesAnnuaire(s.plage_ouverture))}${contacts(tels, mails, "Annuaire de l'administration (DILA)", s.url_service_public)}<div class="links">${liens}</div></div>`;
  }
  // Portée d'une démarche en ligne (champ « po » de l'index) ; un index plus ancien, sans ce champ, confond nationale et inconnue.
  const portee = (r) => r.po || (r.dep ? "dep" : "nat");
  // Une démarche en ligne n'a de guichet local que si elle relève du département de l'usager : une démarche nationale
  // ou d'un autre département n'est pas reçue par le service de sa commune.
  const duDepartement = (r, c) => r.k === "dn" && !!r.dep && r.dep === c.dep;
  async function encadre(el, r, c, deja) {
    const g = regle(r);
    el.querySelectorAll(".ou").forEach((x) => x.remove());
    if (!g || !c) return;
    if (r.k === "dn" && !duDepartement(r, c)) return;
    // Même service déjà affiché plus haut : replié, pour ne pas répéter l'encadré sous chaque résultat.
    const cle = g.identite ? "identite" : g.libelle, replie = deja.has(cle); deja.add(cle);
    const box = document.createElement("div"); box.className = "ou"; el.appendChild(box);
    if (g.identite) {
      const texte = "Toutes les mairies ne prennent pas les demandes de carte d'identité et de passeport : la fiche explique comment trouver une mairie équipée près de chez vous.";
      box.innerHTML = replie ? `<details><summary><b>Où déposer la demande</b> (comme plus haut)</summary><p>${texte}</p></details>` : `<div class="ou-t">Où déposer la demande</div><p>${texte}</p>`;
      return;
    }
    // Le type de la table ne sert qu'à choisir le guichet : l'encadré affiche le nom que renvoie l'Annuaire.
    box.innerHTML = `<div class="ou-t">Où aller pour ${esc(c.nom)}</div><p class="ou-src">Recherche dans l'Annuaire de l'administration…</p>`;
    let l;
    try { l = await services(c.code, g.types); } catch (e) { box.querySelector(".ou-src").textContent = "L'Annuaire de l'administration ne répond pas pour l'instant."; return; }
    if (COMMUNE !== c) return;
    if (!l.length) { box.remove(); return; }
    const corps = `${l.map(htmlService).join("")}<p class="ou-src">Service compétent pour votre commune selon l'Annuaire, interrogé avec le seul code de la commune.</p>`;
    box.innerHTML = replie ? `<details><summary><b>Où aller&nbsp;: ${esc(l.map((s) => s.nom).join(", "))}</b> (comme plus haut)</summary>${corps}</details>`
      : `<div class="ou-t">Où aller pour ${esc(c.nom)}</div>${corps}`;
  }

  // ---------- 3. France services la plus proche
  const chargerFS = () => memo("fs", () => json("donnees/assistant/france_services.json"));
  function km(a, b, c, d) {
    const R = 6371, r = Math.PI / 180, x = Math.sin((c - a) * r / 2) ** 2 + Math.cos(a * r) * Math.cos(c * r) * Math.sin((d - b) * r / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(x));
  }
  function htmlFS(f, C, d) {
    const v = (k) => f[C[k]];
    const sem = Object.fromEntries(FS.jours.map((j, i) => [j, (v("horaires")[i] || "").replace(/ - /g, "–").replace(/ \/ /g, ", ")]));
    const nature = /itin|bus/i.test(v("format")) ? " · structure itinérante" : "";
    const adr = [v("adresse"), v("complement"), v("code_postal") + " " + v("commune")].filter(Boolean).join(", ");
    return `<div class="ou-s"><strong>${esc(v("nom"))}</strong> <span class="meta">à ${d.toLocaleString("fr-FR", { maximumFractionDigits: 1 })} km${nature}</span><div>${esc(adr)}</div>${blocHoraires(sem)}`
      + (v("rdv") === "Oui" ? `<div class="meta">Prise de rendez-vous possible.</div>` : "")
      + contacts(v("telephone") ? [v("telephone")] : [], (v("courriel") || "").split(/[;,\s]+/).filter((m) => m.includes("@")), "France services (ANCT)", v("fiche"))
      + `<div class="links"><a href="${carte(v("lat"), v("lon"))}" target="_blank" rel="noopener">Voir sur la carte ↗</a>`
      + (v("fiche") ? `<a href="${esc(v("fiche"))}" target="_blank" rel="noopener">Fiche officielle ↗</a>` : "") + `</div></div>`;
  }
  async function franceServices(liste) {
    let el = $("fs-aide");
    if (!el) { el = document.createElement("div"); el.id = "fs-aide"; $("cards").after(el); }
    // « Aucune démarche en ligne pertinente » : parmi les 5 premiers résultats, aucune démarche nationale (po « nat ») ni du
    // département de l'usager (sans département connu : d'aucun département) qui soit pertinente pour la question, au sens
    // de Moteur.pertinence (moitié du meilleur score, deux termes de la question repris). Une démarche de département
    // inconnu ne compte pas. Le seuil sert à cette règle seulement : il ne change ni le classement ni l'affichage.
    const dep = COMMUNE ? COMMUNE.dep : $("dep").value;
    const P = Moteur.pertinence(IX, $("q").value, { pub: $("pub").value, dep });
    const enLigne = liste.slice(0, 5).some((r) => r && r.k === "dn" && (portee(r) === "nat" || (portee(r) === "dep" && (!dep || r.dep === dep))) && P.pertinente(r.id));
    el.className = enLigne ? "fs-pied" : "ou fs-fort"; el.innerHTML = "";
    if (!$("res") || $("res").hidden) return;
    const c = COMMUNE;
    if (!c) {
      if (!enLigne) el.innerHTML = `<div class="ou-t">Une France services peut vous aider à faire cette démarche</div><p>Indiquez votre code postal pour trouver la plus proche, ou consultez la <a href="https://www.france-services.gouv.fr/" target="_blank" rel="noopener">carte des France services ↗</a>.</p>`;
      return;
    }
    try { FS = await chargerFS(); } catch (e) { return; }
    if (COMMUNE !== c) return;
    const C = Object.fromEntries(FS.champs.map((k, i) => [k, i]));
    const proches = FS.structures.map((f) => [km(c.lat, c.lon, f[C.lat], f[C.lon]), f]).sort((a, b) => a[0] - b[0]).slice(0, 3);
    if (!proches.length) return;
    const src = `<p class="ou-src">Source&nbsp;: liste des structures labellisées France services (ANCT, data.gouv.fr${FS.date ? ", " + esc(FS.date.split("-").reverse().join("/")) : ""}). Distance à vol d'oiseau depuis le centre de ${esc(c.nom)}.</p>`;
    const suivantes = proches.slice(1).map(([d, f]) => htmlFS(f, C, d)).join("");
    if (enLigne) {
      const [d, f] = proches[0];
      el.innerHTML = `<details><summary><b>Besoin d'aide pour faire la démarche&nbsp;?</b> La France services la plus proche&nbsp;: ${esc(f[C.nom])}, à ${d.toLocaleString("fr-FR", { maximumFractionDigits: 1 })} km.</summary>${htmlFS(f, C, d)}${suivantes}${src}</details>`;
    } else {
      el.innerHTML = `<div class="ou-t">Une France services peut vous aider à faire cette démarche</div>${htmlFS(proches[0][1], C, proches[0][0])}<details><summary>Les deux suivantes</summary>${suivantes}</details>${src}`;
    }
  }

  // ---------- Branchement sur l'affichage des résultats
  // Démarche locale de département inconnu : pas d'encadré, une mention ; la carte du gabarit dit « national ou non
  // localisé » pour les deux cas, la page précise lequel.
  function portee_carte(el, r) {
    if (r.k !== "dn" || r.dep) return;
    const meta = el.querySelector(".top .meta");
    if (meta) meta.textContent = meta.textContent.replace("national ou non localisé", portee(r) === "inc" ? "département inconnu" : "national");
    if (portee(r) === "inc" && !el.querySelector(".ou-inc")) {
      const p = document.createElement("p"); p.className = "ou-inc"; p.textContent = "Démarche locale : vérifiez qu'elle concerne votre commune."; el.appendChild(p);
    }
  }
  function decorer() {
    if (typeof IX === "undefined" || !IX) return;
    const deja = new Set();
    for (const el of document.querySelectorAll("#cards .card")) {
      const i = IX.byId.get(el.id.slice(2)); if (i === undefined) continue;
      portee_carte(el, IX.recs[i]);
      if (portee(IX.recs[i]) !== "inc") encadre(el, IX.recs[i], COMMUNE, deja);
    }
    franceServices(LISTE);
  }
  const afficher = showCards;
  showCards = function (list, title) { afficher(list, title); LISTE = list || []; decorer(); };
})();
