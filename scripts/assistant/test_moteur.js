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
{ const q="Je suis agriculteur, existe-t-il une aide d'urgence ?", t3=top(q,{dep:'37'},3), t5=top(q,{dep:'37'},5);
  verifie('R2 Plan CASI du 37 dans les 3 premiers', ids(t3).some(i=>i==='DN-157661'||i==='DN-159382'), ids(t3).join(' '));
  verifie('R2 aucune aide aux victimes de violences conjugales dans les 5 premiers', !t5.some(r=>/violences? conjugal/i.test(r.t)), ids(t5).join(' ')); }
{ const q="Je n'arrive plus à payer ma facture d'électricité, j'habite Rezé, près de Nantes. Ai-je droit à une aide ?", t3=top(q,{},3), t5=top(q,{},5);
  verifie('R3 DN-50108 dans les 3 premiers', ids(t3).includes('DN-50108'), ids(t3).join(' '));
  verifie('R3 chèque énergie (SP-F33667 ou SP-R74067) dans les 5 premiers', ids(t5).some(i=>i==='SP-F33667'||i==='SP-R74067'), ids(t5).join(' '));
  verifie('R3 ni déchetterie, ni broyeur, ni récupérateur d\'eau dans les 5 premiers', !t5.some(r=>/d[ée]chett|broyeur|r[ée]cup[ée]rateur/i.test(r.t)), t5.map(r=>r.t.slice(0,30)).join(' / ')); }
{ const q="Ma vitrine a été cassée pendant les manifestations, quelle aide ?";
  const cibles=R.filter(r=>r.k==='dn'&&r.po==='nat'&&/commerc/i.test(r.t)&&/endommag|d[ée]grad|d[ée]g[âa]t|violences urbaines/i.test(r.t)).map(r=>r.id);
  if(!cibles.length){ console.log('ATTENTE R4 démarche de l\'État pour les commerces endommagés : absente de l\'index actuel (à revoir une fois l\'index rafraîchi)'); attente++; }
  else { const t3=top(q,{},3); verifie('R4 démarche de l\'État pour les commerces endommagés dans les 3 premiers', ids(t3).some(i=>cibles.includes(i)), ids(t3).join(' ')); } }
{ // R5 : références à figer après validation par l'auteur (proposées dans la PR 70) ; en attente tant qu'elles ne le sont pas.
  const q="Mon club de foot a besoin d'argent pour acheter des équipements.", t3=top(q,{},3);
  const PROPOSEES=['SP-F3180','SP-R45189','SP-R70935','SP-R50795'];
  const local=t3.filter(r=>r.k==='dn'&&(r.po!=='nat'||/club/i.test(r.t)));
  console.log(`ATTENTE R5 club de foot, sans département — 3 premiers : ${ids(t3).join(' ')} ; démarches d'un club ou d'un lieu : ${local.length} ; références proposées en tête : ${PROPOSEES.some(i=>ids(t3)[0]===i)?'oui':'non'} (références à figer)`); attente++; }
console.log(`\n${echecs?echecs+' échec(s)':'Toutes les situations de référence passent'}${attente?', '+attente+' en attente':''}.`);
if(echecs) process.exit(1);
