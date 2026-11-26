#!/usr/bin/env node
// Mesure du classement sur les questions de référence : donnees/assistant/questions_reference.json (démarches les plus
// demandées) et, s'il existe, questions_reference_annuaire.json (recherches de l'Annuaire) ; un score par liste.
//
//   node scripts/assistant/mesure.js                      score du moteur actuel
//   node scripts/assistant/mesure.js --avant origin/main  score avant (moteur.js de cette révision git) et après,
//                                                         puis la liste des questions qui changent
//   node scripts/assistant/mesure.js --avant-fichier <moteur.js>   idem, avec un moteur.js sur disque
//   node scripts/assistant/mesure.js --liste              la liste, en Markdown, pour relecture (aucun calcul)
//
// Juste : « Votre démarche » (Moteur.choisir) fait partie des réponses acceptables.
// Proche : pas juste, mais une réponse acceptable est dans les 3 premiers résultats (Moteur.search).
// Manqué : ni l'un ni l'autre.
"use strict";
const fs = require("fs"), path = require("path"), os = require("os"), { execFileSync } = require("child_process");
const RACINE = path.join(__dirname, "..", ".."), D = path.join(RACINE, "donnees", "assistant");
const lire = (f) => JSON.parse(fs.readFileSync(path.join(D, f), "utf8"));
const LISTES = ["questions_reference.json", "questions_reference_annuaire.json"].filter((f) => fs.existsSync(path.join(D, f)));
const R = lire("index.json"), COMMUNES = lire("communes.json");
let REF = lire(LISTES[0]);
const parId = new Map(R.map((r) => [r.id, r]));
const args = process.argv.slice(2), opt = (n) => { const i = args.indexOf(n); return i < 0 ? null : args[i + 1]; };
const libOpt = (o) => (o && (o.pub || o.dep) ? ` (${[o.pub, o.dep].filter(Boolean).join(", ")})` : "");

if (args.includes("--liste")) {
  REF = lire(opt("--liste") && opt("--liste").endsWith(".json") ? opt("--liste") : LISTES[0]);
  console.log("| # | Thème | Question | Réponses acceptables |\n|---|---|---|---|");
  REF.questions.forEach((x, i) => console.log(`| ${i + 1} | ${x.theme} | ${x.q}${libOpt(x.options)} | ${x.ok.map((id) =>
    `${id} ${(parId.get(id) || { t: "ABSENTE DE L'INDEX" }).t.replace(/\|/g, "/").slice(0, 70)}`).join(" ; ")} |`));
  process.exit(0);
}

function charger(f) {
  delete require.cache[require.resolve(f)];
  const M = require(f);
  if (M.chargerSigles && fs.existsSync(path.join(D, "sigles.json"))) M.chargerSigles(lire("sigles.json"));   // avant l'index
  const ix = M.build(R);
  M.chargerCommunes(COMMUNES);
  return [M, ix];
}
const CHARGES = new Map();
function mesurer(f) {
  if (!CHARGES.has(f)) CHARGES.set(f, charger(f));
  const [M, ix] = CHARGES.get(f);
  return REF.questions.map((x) => {
    const o = x.options || {}, C = M.choisir(ix, x.q, { ...o, k: 20 }), top = M.search(ix, x.q, { ...o, k: 3 }).map((y) => y.r.id);
    const p = C.principal ? C.principal.id : "";
    const etat = x.ok.includes(p) ? "juste" : top.some((id) => x.ok.includes(id)) ? "proche" : "manqué";
    return { etat, p, top };
  });
}
const compte = (res) => ({ juste: res.filter((r) => r.etat === "juste").length, proche: res.filter((r) => r.etat === "proche").length });
const ligneScore = (nom, c) => `| ${nom} | ${c.juste} / ${REF.questions.length} | ${c.juste + c.proche} / ${REF.questions.length} |`;
const titre = (id) => (id ? `${id} ${(parId.get(id) || { t: "" }).t.slice(0, 50)}` : "aucune");

let fAvant = opt("--avant-fichier"), tmp = null;
const rev = opt("--avant");
if (rev) {
  tmp = fs.mkdtempSync(path.join(os.tmpdir(), "mesure-"));
  fAvant = path.join(tmp, "moteur.js");
  fs.writeFileSync(fAvant, execFileSync("git", ["show", `${rev}:scripts/assistant/moteur.js`], { cwd: RACINE }));
}
for (const f of LISTES) {
REF = lire(f);
if (LISTES.length > 1) console.log(`\n### ${f}\n`);
if (REF.statut !== "validée") console.log(`> Liste de référence : statut « ${REF.statut} ».\n`);
const apres = mesurer(path.join(__dirname, "moteur.js"));
console.log("| Moteur | Juste (« Votre démarche ») | Juste ou proche (3 premiers) |\n|---|---|---|");
if (!fAvant) {
  console.log(ligneScore("actuel", compte(apres)));
  const m = REF.questions.map((x, i) => [x, apres[i]]).filter(([, r]) => r.etat !== "juste");
  console.log(`\n${m.length} questions pas justes :\n\n| Question | État | Votre démarche | 3 premiers |\n|---|---|---|---|`);
  for (const [x, r] of m) console.log(`| ${x.q}${libOpt(x.options)} | ${r.etat} | ${titre(r.p)} | ${r.top.join(" ")} |`);
} else {
  const avant = mesurer(fAvant);
  console.log(ligneScore(`avant${rev ? ` (${rev})` : ""}`, compte(avant)));
  console.log(ligneScore("après", compte(apres)));
  const ch = REF.questions.map((x, i) => [x, avant[i], apres[i]]).filter(([, a, b]) => a.etat !== b.etat || a.p !== b.p);
  console.log(`\n${ch.length} questions changent :\n\n| Question | Avant | Après |\n|---|---|---|`);
  for (const [x, a, b] of ch) console.log(`| ${x.q}${libOpt(x.options)} | ${a.etat} · ${titre(a.p)} | ${b.etat} · ${titre(b.p)} |`);
}
}
if (tmp) fs.rmSync(tmp, { recursive: true, force: true });
