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
