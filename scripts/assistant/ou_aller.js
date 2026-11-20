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
  // Origine de la liste affichée : « simple » (recherche simple, classement brut du moteur) ou « citee » (réponse préparée
  // ou conversation : démarches déjà retenues par l'assistant). Repérée en phase de capture, avant les gestionnaires du
  // gabarit qui affichent les résultats.
  let ORIGINE = "simple";
  document.addEventListener("click", (ev) => {
    if (ev.target.closest("#simple")) ORIGINE = "simple";
    else if (ev.target.closest("#ex .chip, #thread .choix button")) ORIGINE = "citee";
  }, true);
  document.addEventListener("submit", (ev) => { if (ev.target.closest("#f, #ff")) ORIGINE = "citee"; }, true);
  const cache = new Map();

  const norm = (s) => (s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[’`]/g, "'").replace(/\s+/g, " ");
  const motEntier = (txt, idx) => new RegExp("(^|[^a-z0-9])" + norm(idx).replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "($|[^a-z0-9])").test(txt);
  const hm = (s) => (s || "").slice(0, 5);
  const memo = (k, f) => { if (!cache.has(k)) cache.set(k, f().catch((e) => { cache.delete(k); throw e; })); return cache.get(k); };
  const json = (u) => fetch(u).then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); });
  const lit = (v) => { if (typeof v !== "string") return v || []; try { return JSON.parse(v); } catch (e) { return v; } };
  const carte = (lat, lon) => `https://www.openstreetmap.org/?mlat=${lat}&mlon=${lon}#map=17/${lat}/${lon}`;

  fetch("donnees/assistant/types_guichets.json").then((r) => r.json()).then((t) => { TABLE = t; decorer(); }).catch(() => {});
  // Communes, pour que le moteur reconnaisse un lieu dans la question (Moteur.lieux) et que la page le propose.
  fetch("donnees/assistant/communes.json").then((r) => r.json()).then((d) => { Moteur.chargerCommunes(d); decorer(); }).catch(() => {});

  // ---------- 1. Code postal → commune
  const cp = $("cp"), choix = $("commune"), etat = $("cp-etat");
  // Le bloc « Préciser le public ou le lieu » s'ouvre tout seul quand un lieu est proposé ou qu'un filtre est actif.
  function ouvrirFiltres() { const f = $("filtres"); if (f) f.open = true; }
  ["pub", "dep"].forEach((id) => $(id).addEventListener("change", () => { if ($(id).value) ouvrirFiltres(); }));
  // Un département ou un code postal choisi remplace une région choisie.
  $("dep").addEventListener("change", () => { if ($("dep").value) Moteur.region = null; });
  function poser(c) {
    COMMUNE = c; if (c) { Moteur.region = null; ouvrirFiltres(); }
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
  // Une fois la liste chargée, le cadre « Ce que la démo couvre » du gabarit affiche le nombre de structures.
  const chargerFS = () => memo("fs", () => json("donnees/assistant/france_services.json").then((d) => {
    window.NFS = d.structures.length; if (typeof window.majCadre === "function") window.majCadre(window.NFS); return d; }));
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
    // Public : encadré ou ligne pour un particulier ou un public non précisé ; ligne seulement pour une entreprise ;
    // rien pour une collectivité ou une association.
    const pub = $("pub").value;
    if (pub === "collectivite" || pub === "association") { el.className = ""; el.innerHTML = ""; return; }
    // « Aucune démarche en ligne pertinente » : parmi les 5 premiers résultats, aucune démarche nationale (po « nat ») ni du
    // département de l'usager (sans département connu : d'aucun département) qui soit pertinente pour la question, au sens
    // de Moteur.pertinence (moitié du meilleur score, deux termes de la question repris). Une démarche de département
    // inconnu ne compte pas. Le seuil sert à cette règle seulement : il ne change ni le classement ni l'affichage.
    const dep = COMMUNE ? COMMUNE.dep : $("dep").value;
    // Le seuil de pertinence ne vaut que pour la recherche simple : une démarche citée par l'assistant est déjà retenue.
    const P = ORIGINE === "simple" ? Moteur.pertinence(IX, $("q").value, { pub, dep }) : { pertinente: () => true };
    const enLigne = pub === "entreprise" || liste.slice(0, 5).some((r) => r && r.k === "dn" && (portee(r) === "nat" || (portee(r) === "dep" && (!dep || r.dep === dep))) && P.pertinente(r.id));
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
  // ---------- Lieu reconnu dans la question : proposé, jamais imposé. Un code postal saisi prime.
  function pastille() {
    let el = $("lieu-pastille");
    if (!el) { el = document.createElement("div"); el.id = "lieu-pastille"; el.className = "pastilles"; $("cards").before(el); }
    el.innerHTML = "";
    if (COMMUNE || !$("res") || $("res").hidden || !Moteur.lieux) return;
    const A = Moteur.lieux($("q").value), L = A.lieux[0];
    // Région choisie (clic sur « Bretagne ? ») : la pastille dit que les résultats sont limités, et permet de retirer le filtre.
    if (Moteur.region) {
      el.innerHTML = `<span class="meta">Résultats limités à la région</span> <span class="pastille pastille-fixe">${esc(Moteur.region.nom)}</span> · <button type="button" class="lien-changer" id="region-retirer">retirer</button>`;
      $("region-retirer").addEventListener("click", () => { Moteur.region = null; if (ORIGINE === "simple") $("simple").click(); else decorer(); });
      ouvrirFiltres(); return;
    }
    // Région reconnue dans la phrase, sans commune ni département : pastille « Bretagne ? » ; un clic filtre sur ses départements.
    if (!L && A.regions && A.regions[0] && !$("dep").value) {
      const Rg = A.regions[0];
      el.innerHTML = `<span class="meta">Région repérée dans votre question&nbsp;:</span> <button type="button" class="pastille" id="region-choisir">${esc(Rg.nom)}&nbsp;?</button>`;
      $("region-choisir").addEventListener("click", () => { Moteur.region = { nom: Rg.nom, deps: Rg.deps }; if (ORIGINE === "simple") $("simple").click(); else decorer(); });
      ouvrirFiltres(); return;
    }
    if (L) ouvrirFiltres();
    if (!L) {
      // Ni code postal, ni département, ni lieu reconnu : les démarches d'un département sont rétrogradées (×0,8 dans le
      // moteur) ; la page invite à préciser la commune.
      if (!$("dep").value) {
        el.innerHTML = `<span class="meta">Précisez votre commune pour voir les démarches de votre territoire&nbsp;:</span> `
          + `<input id="cp-res" class="cp-res" inputmode="numeric" maxlength="5" placeholder="code postal" aria-label="Votre code postal">`;
        const c2 = $("cp-res");
        c2.addEventListener("input", () => { cp.value = c2.value.replace(/\D/g, "").slice(0, 5); cp.dispatchEvent(new Event("input"));
          if (cp.value.length === 5 && ORIGINE === "simple") setTimeout(() => { if (COMMUNE) $("simple").click(); }, 1500); });
      }
      return;
    }
    // Lieu reconnu, sans département choisi : le moteur favorise déjà les démarches de son département (×1,3) ; la pastille le dit.
    const adapte = !$("dep").value;
    const boutons = L.candidats.map((c, i) => `<button type="button" class="pastille" data-i="${i}">${esc(c.nom)} (${esc(c.dep)})${adapte && !i ? "" : "&nbsp;?"}</button>`);
    el.innerHTML = adapte
      ? `<span class="meta">Résultats adaptés à</span> ${boutons[0]}${boutons.length > 1 ? ` <span class="meta">ou</span> ${boutons.slice(1).join(" ")}` : ""} · <button type="button" class="lien-changer" id="lieu-changer">changer</button>`
      : `<span class="meta">Lieu repéré dans votre question&nbsp;:</span> ${boutons.join(" ")}`;
    el.querySelectorAll("button.pastille").forEach((b) => b.addEventListener("click", async () => {
      const c = L.candidats[+b.dataset.i];
      let g; try { g = await json(`${GEO}/${encodeURIComponent(c.code)}?fields=nom,code,codeDepartement,codeEpci,centre&format=json`); } catch (e) { return; }
      cp.value = ""; choix.hidden = true;
      poser({ nom: g.nom, code: g.code, dep: g.codeDepartement, epci: g.codeEpci || "", lon: g.centre.coordinates[0], lat: g.centre.coordinates[1] });
      if (ORIGINE === "simple") $("simple").click();
    }));
    const ch = $("lieu-changer"); if (ch) ch.addEventListener("click", () => { ouvrirFiltres(); cp.focus(); cp.scrollIntoView({ behavior: "smooth", block: "center" }); });
  }

  // ---------- Diversité : les démarches d'un même organisme au-delà de deux, regroupées sous la 2e par le moteur
  // (Moteur.regroupements), s'affichent sous elle, dépliables. Seulement pour la recherche simple, dont la liste vient
  // directement du moteur.
  function regroupes(el, r) {
    el.querySelectorAll(".regroupes").forEach((x) => x.remove());
    const l = ORIGINE === "simple" && Moteur.regroupements && Moteur.regroupements.get(r.id); if (!l || !l.length) return;
    const d = document.createElement("details"); d.className = "regroupes";
    d.innerHTML = `<summary>+ ${l.length} autre${l.length > 1 ? "s" : ""} démarche${l.length > 1 ? "s" : ""} de ${esc(r.o)}</summary><ul>`
      + l.map((x) => `<li><a href="${esc(dnUrl(x))}" target="_blank" rel="noopener">${esc(x.t)} ↗</a> <span class="meta">${esc(x.dep || "")}</span></li>`).join("") + `</ul>`;
    const ou = el.querySelector(".ou, .liees"); if (ou) el.insertBefore(d, ou); else el.appendChild(d);
  }

  // ---------- CCAS : une fois par page, dans un encadré « Où aller », si (1) le public est particulier ou non précisé,
  // (2) la question ou le premier résultat relève des impayés, de l'énergie, de l'eau, d'une aide financière ou sociale,
  // d'un secours ou de la précarité (« logement » ou « facture » seuls ne suffisent pas), (3) une commune est connue.
  const THEMES_CCAS = /(^| )(impaye|impayes|energi|energie|electr|electricite|gaz|chauffage|fioul|eau|aide financiere|aides financieres|aide sociale|aides sociales|action sociale|secours|precarite|precaire)( |$)/;
  async function ccas(liste) {
    let el = $("ccas-ou");
    if (!el) { el = document.createElement("div"); el.id = "ccas-ou"; $("cards").before(el); }
    el.className = ""; el.innerHTML = "";
    const c = COMMUNE, pub = $("pub").value, q = $("q").value;
    if (!c || (pub && pub !== "particulier") || !$("res") || $("res").hidden) return;
    const termes = Moteur.analyse ? [...Moteur.analyse(q).termes.values()].flatMap((g) => [...g]).join(" ") : "";
    const N = Moteur.norm, premier = liste[0] ? N(liste[0].t + " " + (liste[0].th || "")) : "";
    if (![N(q) + " " + termes, premier].some((s) => THEMES_CCAS.test(s))) return;
    let l; try { l = await services(c.code, ["ccas"]); } catch (e) { return; }
    if (COMMUNE !== c || !l.length) return;
    el.className = "ou";
    el.innerHTML = `<div class="ou-t">Où aller pour ${esc(c.nom)} · aide sociale de votre commune</div>${l.map(htmlService).join("")}<p class="ou-src">Centre communal d'action sociale compétent pour votre commune selon l'Annuaire, interrogé avec le seul code de la commune.</p>`;
  }



  // ---------- Ressources liées à une fiche service-public : services en ligne, formulaires, simulateurs (champ « res »),
  // fiches liées (« fl ») et démarches en ligne rattachées (« dn »). Sous la carte, en retrait : elles ne comptent pas
  // parmi les résultats.
  const LIBELLE = (r) => r.k === "dn" ? "Démarche en ligne" : /^SP-F/.test(r.id) ? "Fiche liée"
    : /Téléservice|selNG/i.test(r.ty) ? "Faire une demande en ligne" : /imulateur/i.test(r.ty) ? "Simulateur"
    : /ormulaire/i.test(r.ty) ? "Formulaire" : /echerche/i.test(r.ty) ? "Outil de recherche" : /odèle|lettre/i.test(r.ty) ? "Modèle de document" : "Ressource";
  let PAR_SLUG = null;
  function liees(el, r) {
    el.querySelectorAll(".liees").forEach((x) => x.remove());
    if (r.k !== "sp") return;
    if (!PAR_SLUG) { PAR_SLUG = new Map(); for (const x of IX.recs) if (x.k === "dn") PAR_SLUG.set(x.u, x); }
    const rec = (id) => { const i = IX.byId.get(id); return i === undefined ? null : IX.recs[i]; };
    const res = [...(r.res || []), ...(r.fl || [])].map(rec).filter(Boolean).slice(0, 3);
    const dn = (r.dn || []).map((s) => PAR_SLUG.get(s)).filter(Boolean).slice(0, 3);
    if (!res.length && !dn.length) return;
    const lien = (x) => x.k === "dn" ? dnUrl(x) : (/^SP-R/.test(x.id) && x.l) ? x.l : x.u;
    const div = document.createElement("div"); div.className = "liees";
    div.innerHTML = `<div class="liees-t">Ressources liées à cette fiche</div><ul>` + [...res, ...dn].map((x) =>
      `<li><span class="liees-l">${LIBELLE(x)}</span> <a href="${esc(lien(x))}" target="_blank" rel="noopener">${esc(x.t)} ↗</a></li>`).join("") + `</ul>`;
    const ou = el.querySelector(".ou"); if (ou) el.insertBefore(div, ou); else el.appendChild(div);
  }

  function decorer() {
    if (typeof IX === "undefined" || !IX) return;
    pastille(); ccas(LISTE);
    const deja = new Set();
    for (const el of document.querySelectorAll("#cards .card")) {
      const i = IX.byId.get(el.id.slice(2)); if (i === undefined) continue;
      portee_carte(el, IX.recs[i]); liees(el, IX.recs[i]); regroupes(el, IX.recs[i]);
      if (portee(IX.recs[i]) !== "inc") encadre(el, IX.recs[i], COMMUNE, deja);
    }
    franceServices(LISTE);
  }
  const afficher = showCards;
  showCards = function (list, title) { afficher(list, title); LISTE = list || []; decorer(); };
})();
