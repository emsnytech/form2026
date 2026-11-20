// Douze situations de test du moteur, sur l'index publié. Depuis la racine du dépôt : node scripts/assistant/test_moteur.js
const path=require('path');
const M=require(path.join(__dirname,'moteur.js'));
const R=JSON.parse(require('fs').readFileSync(path.join(__dirname,'..','..','donnees','assistant','index.json'),'utf8'));
let t=Date.now(); const ix=M.build(R); console.log('build ms',Date.now()-t);
const Q=[["je veux demander une subvention pour mon association sportive",{pub:'association'}],
["organiser une brocante dans ma commune",{}],
["autorisation de tir du sanglier",{dep:'79'}],
["inscrire mon enfant au lycée",{pub:'particulier'}],
["je crée mon entreprise",{pub:'entreprise'}],
["carte d'identité perdue",{pub:'particulier'}],
["bourse étudiant",{}],
["titre de séjour",{dep:'93'}],
["reconnaissance d'utilité publique association",{}],
["accident de travail indemnisation",{}],
["aide pour adapter mon logement handicap",{}],
["Fonds vert collectivité rénovation énergétique",{pub:'collectivite'}]];
for(const [q,o] of Q){ t=Date.now(); const res=M.search(ix,q,{...o,k:6}); console.log('\n### '+q+' '+JSON.stringify(o)+' ('+(Date.now()-t)+'ms)');
 for(const x of res) console.log(x.score, x.r.id, x.r.t.slice(0,90), '|', (x.r.o||x.r.ty||''), x.r.dep||'', x.r.n||''); }

// ---------- Situations de référence (consigne « améliorations du moteur ») : assertions. Sortie en erreur si l'une échoue.
// Les communes (donnees/assistant/communes.json) servent à reconnaître un lieu dans la question.
const fs=require('fs'), FC=path.join(__dirname,'..','..','donnees','assistant','communes.json');
if (M.chargerCommunes && fs.existsSync(FC)) M.chargerCommunes(JSON.parse(fs.readFileSync(FC,'utf8')));
const top=(q,o,n)=>M.search(ix,q,{...o,k:12}).slice(0,n).map(x=>x.r);
const ids=(l)=>l.map(r=>r.id);
let echecs=0, attente=0;
function verifie(nom, ok, detail){ console.log((ok?'OK      ':'ÉCHEC   ')+nom+(detail?' — '+detail:'')); if(!ok) echecs++; }
console.log('\n=== Situations de référence');
{ const q="Je tiens un restaurant à Grenoble et je veux embaucher un salarié étranger. Dois-je vérifier son titre de séjour, et comment ?";
  const t=top(q,{},5), L=M.lieux?M.lieux(q):{lieux:[]};
  verifie('R1 DN-13583 en 1re position', t[0]&&t[0].id==='DN-13583', ids(t).join(' '));
  verifie('R1 département 38 proposé', !!(L.lieux[0]&&L.lieux[0].dep==='38'), L.lieux.map(l=>l.nom+' ('+l.dep+')').join(', ')||'aucun lieu'); }
// Une situation dont les références attendues ne sont plus dans l'index (démarches fermées depuis) passe « en attente » avec
// son motif, au lieu d'échouer : les références sont alors à revoir par l'auteur, jamais remplacées par le script.
const presentes=(l)=>l.filter(i=>ix.byId.has(i));
{ // R2 en critère, département 46 : au moins une démarche ouverte dont le titre contient « CASI » ou « fonds d'urgence », du 46
  // ou nationale (jamais de département inconnu), dans les 3 premiers ; aucune aide aux victimes de violences conjugales dans
  // les 5 premiers. Sans démarche ouverte de ce type du 46 ou nationale, R2 passe « en attente », avec son motif.
  // (Le 37 a été abandonné le 20 novembre 2026 : ses deux démarches CASI sont fermées ; DN-156662 « …-2026-DDT46 » reste ouverte.)
  const D='46', q="Je suis agriculteur, existe-t-il une aide d'urgence ?", t3=top(q,{dep:D},3), t5=top(q,{dep:D},5);
  const CASI=(r)=>r.k==='dn'&&/\bCASI\b|fonds d.urgence/i.test(r.t)&&(r.dep===D||r.po==='nat');
  const ouvertes=R.filter(CASI);
  if(!ouvertes.length){ console.log(`ATTENTE R2 aucune démarche ouverte « CASI » ou « fonds d'urgence » du ${D} ou nationale dans l'index`); attente++; }
  else verifie(`R2 une démarche ouverte « CASI » ou « fonds d'urgence » du ${D} ou nationale dans les 3 premiers (candidates : ${ids(ouvertes).slice(0,5).join(' ')})`, t3.some(CASI), ids(t3).join(' '));
  verifie('R2 aucune aide aux victimes de violences conjugales dans les 5 premiers', !t5.some(r=>/violences? conjugal/i.test(r.t)), ids(t5).join(' ')); }
{ const q="Je n'arrive plus à payer ma facture d'électricité, j'habite Rezé, près de Nantes. Ai-je droit à une aide ?", t3=top(q,{},3), t5=top(q,{},5);
  verifie('R3 DN-50108 dans les 3 premiers', ids(t3).includes('DN-50108'), ids(t3).join(' '));
  verifie('R3 chèque énergie (SP-F33667 ou SP-R74067) dans les 5 premiers', ids(t5).some(i=>i==='SP-F33667'||i==='SP-R74067'), ids(t5).join(' '));
  verifie('R3 ni déchetterie, ni broyeur, ni récupérateur d\'eau dans les 5 premiers', !t5.some(r=>/d[ée]chett|broyeur|r[ée]cup[ée]rateur/i.test(r.t)), t5.map(r=>r.t.slice(0,30)).join(' / ')); }
{ // R3, « Votre démarche » de la page (Moteur.choisir) : la variante réservée aux professionnels ne passe pas en tête.
  const q="Je n'arrive plus à payer ma facture d'électricité, j'habite Rezé, près de Nantes. Ai-je droit à une aide ?", c=M.choisir(ix,q,{});
  verifie('R3 « Votre démarche » : la variante « (ménages) » (DN-50108) en tête', c.principal&&c.principal.id==='DN-50108', c.principal&&c.principal.id+' '+c.principal.t); }
{ // R6 (PR 75) : renouveler un titre de séjour à Grenoble. En tête de la réponse, une démarche ou fiche de titre de séjour,
  // nationale ou du 38 ; aucune fiche « étudiant » dans les 3 premiers de la réponse (la question ne parle pas d'études).
  const q="Je dois renouveler mon titre de séjour, j'habite à Grenoble.", c=M.choisir(ix,q,{});
  const affiches=[c.principal,...c.liste.filter(r=>r!==c.principal&&!(r.k==='dn'&&((r.dep&&r.dep!==c.departement)||r.po==='inc')))].slice(0,3);
  const titreSejour=(r)=>/titre de s[ée]jour|carte de s[ée]jour|[ée]trangers?/i.test(r.t+' '+(r.d||'').slice(0,300));
  verifie('R6 en tête : une démarche ou fiche de titre de séjour, nationale ou du 38', !!c.principal&&titreSejour(c.principal)&&(c.principal.k==='sp'||c.principal.dep==='38'||c.principal.po==='nat'), c.principal&&c.principal.id+' '+c.principal.t);
  verifie('R6 aucune fiche « étudiant » dans les 3 premiers de la réponse', !affiches.some(r=>/[ée]tudiant/i.test(r.t)), affiches.map(r=>r.id).join(' ')); }
{ const q="Ma vitrine a été cassée pendant les manifestations, quelle aide ?";
  const cibles=R.filter(r=>r.k==='dn'&&r.po==='nat'&&/commerc/i.test(r.t)&&/endommag|d[ée]grad|d[ée]g[âa]t|violences urbaines/i.test(r.t)).map(r=>r.id);
  if(!cibles.length){ console.log('ATTENTE R4 démarche de l\'État pour les commerces endommagés : absente de l\'index (aucune démarche de ce type dans le descriptif publié, export du 20 novembre 2026)'); attente++; }
  else { const t3=top(q,{},3); verifie('R4 démarche de l\'État pour les commerces endommagés dans les 3 premiers', ids(t3).some(i=>cibles.includes(i)), ids(t3).join(' ')); } }
{ // R5 : références à figer après validation par l'auteur (proposées dans la PR 70) ; en attente tant qu'elles ne le sont pas.
  const q="Mon club de foot a besoin d'argent pour acheter des équipements.", t3=top(q,{},3);
  const PROPOSEES=['SP-F3180','SP-R45189','SP-R70935','SP-R50795'];
  const local=t3.filter(r=>r.k==='dn'&&(r.po!=='nat'||/club/i.test(r.t)));
  console.log(`ATTENTE R5 club de foot, sans département — 3 premiers : ${ids(t3).join(' ')} ; démarches d'un club ou d'un lieu : ${local.length} ; références proposées en tête : ${PROPOSEES.some(i=>ids(t3)[0]===i)?'oui':'non'} (références à figer)`); attente++; }
{ // Région dans la phrase, et aucun lieu reconnu à tort sur les 30 questions de référence (PR 67).
  const L=M.lieux("Je veux créer une association en Bretagne");
  verifie('Région : « en Bretagne » propose Bretagne', !!(L.regions&&L.regions[0]&&L.regions[0].nom==='Bretagne'), (L.regions||[]).map(r=>r.nom).join(', ')||'aucune');
  const ex=JSON.parse(fs.readFileSync(path.join(__dirname,'..','..','donnees','assistant','exemples.json'),'utf8'));
  const Q30=[...ex.map(e=>e.q),...Q.map(x=>x[0]),'renouveler mon titre de séjour','allocation logement caf','brocante dans ma rue',"carte d'identité"];
  const atort=Q30.filter(q=>{const l=M.lieux(q); return l.lieux.length||(l.regions||[]).length;});
  verifie('Aucun lieu ni région reconnu à tort sur les questions de référence', !atort.length, atort.join(' | ')||`${Q30.length} questions, aucun lieu`); }
{ // Ton des réponses (PR 75) : réponses préparées et messages de la recherche simple. Jamais de formule d'échec en tête,
  // aucun mot de spécialiste, trois phrases au plus pour une réponse préparée ; la consigne de l'assistant ne propose plus
  // de commencer par un échec.
  const ECHEC=/^\s*(je ne trouve pas|je n.ai pas|aucun(e)? (r[ée]sultat|d[ée]marche)|d[ée]sol[ée]|malheureusement|pardon)/i;
  const INTERDITS=/\b(corpus|index|base de donn[ée]es|enregistrements?|t[ée]l[ée]services?|d[ée]mat[ée]rialis[ée]e?s?|usagers?)\b/i;
  const sansRefs=(s)=>s.replace(/\[\[[^\]]+\]\]/g,'');
  const phrases=(s)=>sansRefs(s).split(/(?<=[.!?])\s+/).filter(x=>x.trim()).length;
  const ex=JSON.parse(fs.readFileSync(path.join(__dirname,'..','..','donnees','assistant','exemples.json'),'utf8'));
  const page=fs.readFileSync(path.join(__dirname,'..','..','trouver-sa-demarche.html'),'utf8');
  const bloc=(page.match(/const MESSAGES = \{([\s\S]*?)\n\};/)||[])[1]||'';
  const messages=[...bloc.matchAll(/:\s*"((?:[^"\\]|\\.)*)"/g)].map(m=>m[1]);
  const textes=[...ex.map(e=>['réponse préparée « '+e.q+' »',e.texte]),...messages.map(m=>['message « '+m.slice(0,40)+'… »',m])];
  const fautes=textes.filter(([,s])=>ECHEC.test(sansRefs(s))||INTERDITS.test(sansRefs(s))).map(([n,s])=>n+' : '+((sansRefs(s).match(INTERDITS)||[])[0]||'formule d\'échec'));
  verifie(`Ton : aucune formule d'échec en tête ni mot de spécialiste (${ex.length} réponses préparées, ${messages.length} messages)`, messages.length>0&&!fautes.length, fautes.join(' | '));
  const longues=ex.filter(e=>phrases(e.texte)>3).map(e=>e.q+' ('+phrases(e.texte)+' phrases)');
  verifie('Ton : réponses préparées en trois phrases au plus', !longues.length, longues.join(' | '));
  verifie('Ton : la consigne de l\'assistant ne propose plus « Je ne trouve pas… » en ouverture', !/dis-le franchement|Je ne trouve pas de démarche en ligne pour cela/.test(page), ''); }
console.log(`\n${echecs?echecs+' échec(s)':'Toutes les situations de référence passent'}${attente?', '+attente+' en attente':''}.`);
if(echecs) process.exit(1);
