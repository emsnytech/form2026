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
  // Titre : commerces ou entreprises, et dommages (élargi le 22 novembre 2026 au titre réel de DN-161645, « petites entreprises… dommages
  // subis lors des troubles urbains » ; la démarche doit rester nationale, ici par portees_corrigees.json).
  const cibles=R.filter(r=>r.k==='dn'&&r.po==='nat'&&/commerc|entreprise/i.test(r.t)&&/endommag|d[ée]grad|d[ée]g[âa]t|dommages|violences urbaines|troubles urbains/i.test(r.t)).map(r=>r.id);
  const dateIndex=JSON.parse(fs.readFileSync(path.join(__dirname,'..','..','donnees','assistant','index_meta.json'),'utf8')).date_export;
  // Démarche de ce type déclarée locale (service et département du descriptif) : signalée, sans changer le critère.
  const locales=R.filter(r=>r.k==='dn'&&r.po!=='nat'&&/commerc|entreprise/i.test(r.t)&&/endommag|d[ée]grad|d[ée]g[âa]t|dommages|violences urbaines|troubles urbains/i.test(r.t));
  if(!cibles.length&&locales.length){ const t3=top(q,{},3); console.log(`ATTENTE R4 démarche de l'État pour les commerces endommagés : ${locales.map(r=>r.id+' déclarée '+(r.dep||r.po)).join(', ')} (export du ${dateIndex}) ; le critère attend une démarche nationale — dans les 3 premiers : ${t3.some(r=>locales.includes(r))?'oui':'non'} (${ids(t3).join(' ')})`); attente++; }
  else if(!cibles.length){ console.log(`ATTENTE R4 démarche de l'État pour les commerces endommagés : absente de l'index (export du ${dateIndex})`); attente++; }
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
{ // Fiabilité (PR « fiabilité ») : lignes de l'accueil construites depuis leurs ids ; aucune démarche affirmée sans être sûre.
  const D_=path.join(__dirname,'..','..','donnees','assistant');
  const pd=JSON.parse(fs.readFileSync(path.join(D_,'plus_demandees.json'),'utf8')), une=JSON.parse(fs.readFileSync(path.join(D_,'a_la_une.json'),'utf8'));
  const lignes=[...pd.nationales,...pd.demarche_numerique,...une.retenues];
  const trouve=(mots)=>lignes.find(x=>mots.every(m=>M.norm(x.titre).includes(m)));
  const med=trouve(['medaille','honneur','travail']);
  if(!med){ console.log("ATTENTE A1 ligne « médaille d'honneur du travail » absente de l'accueil"); attente++; }
  else { const R0=M.reponseLigne(ix,med,{});
    verifie('A1 médaille du travail sans territoire : la démarche nationale (DN-69348) en « Votre démarche », sans question sur le département', !R0.question&&R0.principal&&R0.principal.id==='DN-69348', `question « ${R0.question||''} » ; Votre démarche : ${R0.principal?R0.principal.id:'aucune'}`);
    verifie('A1 aucune fiche sur l\'autorisation de travail', !(R0.fiche&&/autorisation de travail/i.test(R0.fiche.t)), R0.fiche?R0.fiche.id+' '+R0.fiche.t:'pas de fiche');
    const R75=M.reponseLigne(ix,med,{dep:'75'}), R05=M.reponseLigne(ix,med,{dep:'05'});
    verifie('A1 avec le 75 ou le 05 : la démarche nationale reste en « Votre démarche » (même titre que celle des Hautes-Alpes)', R75.principal&&R75.principal.id==='DN-69348'&&R05.principal&&R05.principal.id==='DN-69348', `75 : ${R75.principal?R75.principal.id:R75.message} ; 05 : ${R05.principal?R05.principal.id:R05.message}`); }
  const emb=trouve(['titre','sejour','salarie']);
  if(!emb){ console.log("ATTENTE A2 ligne « vérifier le titre de séjour d'un futur salarié » absente de l'accueil"); attente++; }
  else { const R38=M.reponseLigne(ix,emb,{dep:'38'}); verifie('A2 vérification du titre de séjour avec le 38 : DN-13583 en « Votre démarche »', R38.principal&&R38.principal.id==='DN-13583', R38.principal?R38.principal.id:'aucune'); }
  const lst=pd.nationales[0];
  if(!lst||!/listes electorales/.test(M.norm(lst.titre))){ verifie('A4 « S\'inscrire sur les listes électorales » en 1re ligne nationale', false, lst?lst.titre:'aucune ligne'); }
  else { const RL=M.reponseLigne(ix,lst,{});
    verifie('A4 listes électorales : SP-R16396 en « Votre démarche », fiche SP-F1367 en « Comprendre »', RL.principal&&RL.principal.id==='SP-R16396'&&RL.fiche&&RL.fiche.id==='SP-F1367', `Votre démarche : ${RL.principal?RL.principal.id:'aucune'} ; Comprendre : ${RL.fiche?RL.fiche.id:'aucune'}`);
    verifie('A4 l\'attestation de droits (SP-R49811) n\'est plus dans les lignes nationales', !pd.nationales.some(x=>(x.ids||[]).includes('SP-R49811')), pd.nationales.map(x=>x.titre).join(' | ')); }
  const hors=[];
  for(const x of lignes){ const deps=[...new Set(['', ...(x.ids||[]).map(i=>{const k=ix.byId.get(i);return k===undefined?'':ix.recs[k].dep||'';})])];
    for(const d of deps){ const R=M.reponseLigne(ix,x,{dep:d}); for(const r of [R.principal,...R.possibles].filter(Boolean)) if(!(x.ids||[]).includes(r.id)) hors.push(x.titre+' / '+(d||'sans territoire')+' : '+r.id); } }
  verifie(`A3 chaque ligne de l'accueil (${lignes.length}) ne montre que ses propres démarches`, !hors.length&&lignes.every(x=>(x.ids||[]).length), hors.slice(0,5).join(' | ')||'toutes les lignes ont des ids');
  const F=M.choisir(ix,"Demander la médaille d'honneur du travail",{});
  verifie('F1 « médaille d\'honneur du travail » en recherche simple, sans territoire : aucune démarche locale en « Votre démarche »', !F.principal||F.principal.k!=='dn'||(F.principal.po||'')==='nat', F.principal?F.principal.id+' '+(F.principal.dep||F.principal.po)+' '+F.principal.t:'pas de « Votre démarche » ; démarches possibles : '+F.possibles.map(r=>r.id+' ('+(r.dep||r.po||'')+')').join(' ')); }
{ // « Avant de commencer » : un bloc replié sous « Faire la démarche », seulement avec des données de la démarche.
  const B=(i)=>{const k=ix.byId.get(i);return k===undefined?null:ix.recs[k];};
  const META=JSON.parse(fs.readFileSync(path.join(__dirname,'..','..','donnees','assistant','index_meta.json'),'utf8'));
  const emb=B('DN-13583'), A1=M.avantDeCommencer(emb,META);
  verifie('B1 démarche DN avec pièces et pré-remplissage (DN-13583) : ligne « questions » ; les données récupérées (SIRET) sont dans le « ? », pas répétées', A1.lignes[0].cle==='questions'&&/28 questions · 3 pièces/.test(A1.lignes[0].texte)&&!A1.lignes.some(l=>l.cle==='prerempli'||/SIRET/.test(l.texte))&&M.detailSymboles(B('DN-13583'),META).some(d=>/^Données récupérées pour vous : .*SIRET/.test(d.texte)), A1.resume);
  verifie('B1 lien vers le formulaire à vide, en PDF, avec sa précision', /\/commencer\/declaration-prealable-embauche\/dossier_vide$/.test(A1.lignes[0].liens[0].url)&&/pas pour le remplir/.test(A1.lignes[0].liens[0].titre), A1.lignes[0].liens[0].url);
  const sans=ix.recs.find(r=>r.k==='sp'&&/^SP-R/.test(r.id)&&!r.sva&&!r.obs), A2=M.avantDeCommencer(sans);
  verifie('B2 démarche sans aucune donnée : pas de bloc', !A2.lignes.length&&!A2.resume, sans.id+' '+sans.t);
  const avec=ix.recs.filter(r=>M.avantDeCommencer(r,META).lignes.length), delai=avec.filter(r=>M.avantDeCommencer(r,META).lignes.some(l=>l.cle==='delai'||(l.cle==='delais'&&/\d/.test(l.texte+l.liens.map(x=>x.texte).join(' ')))||(!['vigilance','delais'].includes(l.cle)&&/d[ée]lai/i.test(l.texte))));
  verifie(`B3 aucun délai affiché sans donnée par démarche (${avec.length} blocs)`, !delai.length, delai.slice(0,3).map(r=>r.id).join(' ')||'aucun délai');
  verifie('B4 au plus 4 lignes, et l\'IBAN n\'est pas présenté comme rempli', avec.every(r=>M.avantDeCommencer(r,META).lignes.length<=4)&&!('IBAN' in M.PRE_PHRASES));
  const obsPc=ix.recs.find(r=>r.obs&&r.acc&&r.acc[0]!=='TC'), A5=M.avantDeCommencer(obsPc,META), l5=A5.lignes.find(l=>l.cle==='accessibilite');
  verifie('B5 démarche de l\'Observatoire non totalement accessible : le niveau dans le « ? », seulement le renvoi vers la France services la plus proche dans « Avant de commencer »',
    !!l5&&!/conforme|partielle|%/.test(l5.texte)&&/France services/.test(l5.texte)&&l5.liens[0].url==='#carte-ou'&&M.detailSymboles(obsPc,META).some(d=>/^(Accessibilité partielle|Non conforme)/.test(d.texte)), obsPc.id+' : '+(l5?l5.texte:'pas de ligne'));
  // Symboles « comment faire », accessibilité, vigilance (Moteur.symboles).
  const S=(i)=>M.symboles(B(i),META), dn=S('DN-13583');
  verifie('Y1 une démarche DN affiche le seul symbole « en ligne »', JSON.stringify(dn.voies)==='[["en_ligne"]]', JSON.stringify(dn.voies));
  for(const i of ['SP-R16396','SP-F1367']){ const v=S(i).voies, t=JSON.stringify(v);
    verifie(`Y2 ${i} : en ligne ou formulaire, courrier ou guichet (d'après les cas du XML)`, t.includes('["en_ligne"]')&&t.includes('["formulaire","courrier"]')&&v.some(x=>x.includes('guichet'))&&v.length<=3, M.voiesTexte(v)); }
  const sansAcc=B('SP-R16396');
  verifie('Y3 une démarche sans donnée d\'accessibilité affiche « Accessibilité non connue »', !sansAcc.acc&&S('SP-R16396').acc.niveau==='inconnue'&&S('SP-R16396').acc.texte==='Accessibilité non connue');
  const peu={...B('DN-13583'),spp:[19,15,[['delai',10]],'Préfecture de l\'Isère']};
  const sousSeuil=ix.recs.filter(r=>r.spp&&r.spp[0]<20&&M.symboles(r,META).vig.length);
  verifie('Y4 aucune vigilance sous 20 retours rattachés', !M.symboles(peu,META).vig.length&&!sousSeuil.length&&!M.avantDeCommencer(peu,META).lignes.some(l=>l.cle==='vigilance'), sousSeuil.slice(0,3).map(r=>r.id).join(' ')||'aucune');
  const trop=ix.recs.filter(r=>{const x=M.symboles(r,META);return x.voies.length>3||x.vig.length>2;});
  verifie(`Y5 jamais plus de 3 voies ni de 2 vigilances (${ix.recs.length} démarches)`, !trop.length, trop.slice(0,3).map(r=>r.id).join(' ')||'aucune');
  const vigDn=S('DN-13583').vig;
  verifie('Y6 vigilance par organisme : l\'infobulle donne l\'effectif, la source, le périmètre et la limite', vigDn.length&&vigDn.every(v=>/\d+ retours négatifs le signalent, sur \d+ retours sur Services Publics \+/.test(v.detail)&&/organisme « Préfecture de l'Isère »/.test(v.detail)&&/spontané, non représentatif/.test(v.detail)), vigDn.map(v=>v.detail)[0]||'aucune');
  const accDn=S('DN-13583').acc;
  const accP=META.acc_plateformes.dn, moisP="janvier février mars avril mai juin juillet août septembre octobre novembre décembre".split(" ")[+accP.mise_a_jour.slice(5,7)-1];
  verifie('Y7 démarche Démarche Numérique : taux de la plateforme (déclaration publiée), pour une démarche type ; vigilance par organisme',
    accDn.niveau==='plateforme'&&accDn.ligne.startsWith(`Plateforme Démarche Numérique : accessibilité partielle (${accP.taux}, déclaration d'${moisP} ${accP.mise_a_jour.slice(0,4)}), pour une démarche type. Le taux peut être un peu différent selon la démarche, par exemple si elle contient une carte.`)
    &&!ix.recs.some(r=>r.k==='dn'&&!r.obs&&M.symboles(r,META).acc.niveau!=='plateforme')&&M.avantDeCommencer(B('DN-13583'),META).lignes.some(l=>l.cle==='accessibilite'&&/^Plateforme Démarche Numérique/.test(l.texte)&&l.liens.every(x=>x.url===accP.url))
    &&!M.avantDeCommencer(B('DN-13583'),META).lignes.some(l=>/France services/.test(l.texte))&&vigDn.every(v=>v.organisme==="Préfecture de l'Isère"), accDn.ligne);
  const table=JSON.parse(fs.readFileSync(path.join(__dirname,'..','..','donnees','assistant','observatoire_rattachement.json'),'utf8')).rattachements, tid=new Set(table.map(t=>t.id));
  const horsTable=ix.recs.filter(r=>(r.obs||r.acc)&&!tid.has(r.id));
  verifie(`Y8 Observatoire : seules les démarches de observatoire_rattachement.json (${table.length}) ont une accessibilité`, !horsTable.length, horsTable.slice(0,3).map(r=>r.id).join(' ')||'aucune hors table');
  const raf=JSON.parse(fs.readFileSync(path.join(__dirname,'..','..','donnees','assistant','rien_a_faire.json'),'utf8'));
  const valides=new Set(raf.valides.flatMap(e=>e.ids)), rafHors=ix.recs.filter(r=>r.raf&&!valides.has(r.id));
  const essai=M.symboles({...B('SP-F1367'),raf:['Phrase validée.','SP-F35789']},META);
  verifie(`Y9 « rien à faire » : seulement les phrases validées (${raf.valides.length} validées, ${raf.propositions.length} propositions non affichées)`, !rafHors.length&&essai.rien&&essai.rien.phrase==='Phrase validée.'&&!M.symboles(B('SP-F1367'),META).rien===!valides.has('SP-F1367'), rafHors.slice(0,3).map(r=>r.id).join(' ')||'aucune hors table');
  const manq=raf.valides.flatMap(e=>e.ids.filter(i=>{const r=B(i);return !r||!r.raf||r.raf[0]!==e.phrase;}));
  verifie('Y10 chaque phrase validée est portée par ses démarches, condition comprise', !manq.length&&/^Si vous avez fait le recensement/.test(B('SP-R16396').raf[0]), manq.join(' ')||raf.valides.map(e=>e.ids.join('+')+' ← '+e.fiche).join(' ; '));
  // Disposition des symboles (gabarit) : dans la ligne sous le titre, un seul bouton « ? », plus de lien « détail » ni « Que signifient ces symboles ? » sous le bouton.
  const gab=fs.readFileSync(path.join(__dirname,'..','..','trouver-sa-demarche.html'),'utf8');
  verifie('Z1 chaque mode a un libellé court', Object.keys(M.MODES_LIB).every(m=>M.MODES_COURT[m]), JSON.stringify(M.MODES_COURT));
  verifie('Z2 symboles dans la ligne sous le titre, bouton « ? » avec son aria-label, plus de lien « détail » ni de lien sous le bouton',
    /class="org ligne-symb"/.test(gab)&&/aria-label="Que signifient ces symboles \?"/.test(gab)&&!/symb-plus|lienSymboles|symbolesHtml/.test(gab)&&/<p class="titre">\$\{esc\(r\.t\)\}<\/p>`;/.test(gab));
  const seule=ix.recs.filter(r=>{const L=M.avantDeCommencer(r,META).lignes;return L.length&&L.every(l=>l.cle==='accessibilite'&&/^(Accessibilité non connue|Plateforme )/.test(l.texte));});
  const pasDerniere=ix.recs.filter(r=>{const L=M.avantDeCommencer(r,META).lignes,i=L.findIndex(l=>/^(Accessibilité non connue|Plateforme )/.test(l.texte));return i>=0&&i!==L.length-1;});
  verifie('Z4 « Accessibilité non connue » et le taux de la plateforme n\'ouvrent jamais seuls « Avant de commencer » et vient toujours en dernière ligne', !seule.length&&!pasDerniere.length&&!M.avantDeCommencer(B('SP-R11193'),META).lignes.length&&M.avantDeCommencer(B('DN-13583'),META).lignes.slice(-1)[0].cle==='accessibilite', [...seule,...pasDerniere].slice(0,3).map(r=>r.id).join(' ')||'SP-R11193 sans bloc ; DN-13583 : '+M.avantDeCommencer(B('DN-13583'),META).lignes.map(l=>l.cle).join(', '));
  // Signaux de simplicité (FranceConnect, données récupérées) : positifs, seulement quand c'est vrai.
  const SIMP=(r)=>M.symboles(r,META).simp.map(s=>s.cle);
  const dnSansFc=ix.recs.filter(r=>r.k==='dn'&&!SIMP(r).includes('fc'));
  verifie(`S1 toute démarche de Démarche Numérique affiche « FranceConnect » (${ix.recs.filter(r=>r.k==='dn').length} démarches)`, !dnSansFc.length&&M.symboles(B('DN-13583'),META).simp[0].texte==='FranceConnect', dnSansFc.slice(0,3).map(r=>r.id).join(' ')||M.symboles(B('DN-13583'),META).simp[0].detail);
  const spFc=ix.recs.filter(r=>r.k==='sp'&&SIMP(r).includes('fc')).map(r=>r.id), obsFc=ix.recs.filter(r=>/^FranceConnect/.test(r.fc||'')).map(r=>r.id);
  const papier=ix.recs.filter(r=>r.k==='sp'&&!r.fc&&SIMP(r).length);
  verifie(`S2 une fiche service-public n'a « FranceConnect » que si l'Observatoire le déclare (${spFc.length}), et aucune autre fiche n'a de signal de simplicité`,
    spFc.join()===obsFc.join()&&!papier.length&&!SIMP(B('SP-R69012')).length&&!SIMP(B('SP-F1367')).length, papier.slice(0,3).map(r=>r.id).join(' ')||spFc.join(' '));
  const fcPlus=M.symboles({...B('SP-R49813'),fc:'FranceConnect +'},META).simp[0];
  verifie('S3 FranceConnect+ s\'affiche « FranceConnect », la précision est dans le détail ; « Non », « À venir » ou une habilitation seule : rien',
    fcPlus.texte==='FranceConnect'&&/FranceConnect\+/.test(fcPlus.detail)&&['Non','À venir','Non applicable'].every(v=>!SIMP({...B('SP-R49813'),fc:v}).length)&&!SIMP({...B('SP-R49813'),fc:undefined,datapass:['FranceConnect']}).length, fcPlus.detail);
  const VRAIS=new Set(Object.keys(M.RECUPERE)), attendu=ix.recs.filter(r=>r.k==='dn'&&(r.pre||[]).some(p=>VRAIS.has(p))).length, recs=ix.recs.filter(r=>SIMP(r).includes('rec'));
  const faux=recs.filter(r=>r.k!=='dn'||!(r.pre||[]).some(p=>VRAIS.has(p)));
  const seulIban=ix.recs.find(r=>r.k==='dn'&&r.pre.length&&r.pre.every(p=>p==='IBAN')), seulPre=ix.recs.find(r=>r.k==='dn'&&r.pre.length&&r.pre.every(p=>p==='Données préremplies'));
  verifie(`S4 « Données récupérées pour vous » : SIRET, RNA, RNF, Annuaire Éducation seulement (${recs.length} démarches) ; ni IBAN ni lien prérempli`,
    recs.length===attendu&&!faux.length&&[...VRAIS].join()==='SIRET (API Entreprise),RNA (associations),RNF (fondations),Annuaire Éducation'&&seulIban&&!SIMP(seulIban).includes('rec')&&(!seulPre||!SIMP(seulPre).includes('rec')), `${seulIban&&seulIban.id} (IBAN seul), ${seulPre&&seulPre.id} (prérempli seul)`);
  const siret=ix.recs.find(r=>r.k==='dn'&&r.pre.includes('SIRET (API Entreprise)')), dRec=M.symboles(siret,META).simp.find(s=>s.cle==='rec');
  verifie('S5 le détail nomme la source : « informations sur l\'entreprise récupérées à partir du SIRET (API Entreprise) »', /informations sur l'entreprise récupérées à partir du SIRET \(API Entreprise\)/.test(dRec.detail), siret.id+' : '+dRec.detail);
  verifie('S6 icônes neutres en gris (user-check, database-import), pas de logo FranceConnect, signaux juste après les modes',
    /id="ti-user-check"/.test(gab)&&/id="ti-database-import"/.test(gab)&&/class="mode simp"/.test(gab)&&/\[\.\.\.modes, \.\.\.simp, \.\.\.srcUnits/.test(gab)&&!/franceconnect[^"' ]*\.(svg|png)|logo[-_ ]?franceconnect/i.test(gab), '');
  // Ajustements du 24 novembre : carte à manipuler, pastille, médaille du travail, nom d'organisme.
  const avecCarte=ix.recs.filter(r=>r.crt), sansCarte=B('DN-13583');
  verifie(`J1 démarche avec une carte à manipuler : la phrase s'ajoute au détail (${avecCarte.length} démarches, type de champ « Carte ») ; pas sans carte`,
    avecCarte.length&&avecCarte.every(r=>r.k==='dn'&&M.symboles(r,META).acc.ligne.endsWith(M.CARTE_PHRASE))&&!sansCarte.crt&&!M.symboles(sansCarte,META).acc.ligne.includes(M.CARTE_PHRASE), avecCarte[0]&&avecCarte[0].id);
  verifie('J2 pas de pastille d\'accessibilité sur la carte pour une démarche de Démarche Numérique (ni « non connue », ni le taux de la plateforme)', /!\["inconnue", "plateforme"\]\.includes\(S\.acc\.niveau\)/.test(gab));
  const med=(o)=>top("médaille d'honneur du travail",o,12), med0=med({}), med05=med({dep:'05'});
  const i0=med0.findIndex(r=>r.id==='DN-69348'), i05=ids(med05);
  verifie('J3 médaille d\'honneur du travail : la démarche du ministère de l\'Intérieur est nationale ; sans département, pas de démarche des Hautes-Alpes ; avec le 05, la nationale passe devant',
    B('DN-69348').po==='nat'&&!B('DN-69348').dep&&B('DN-69348').dep_declare==='75'&&i0>=0&&!ids(med0).includes('DN-118359')&&i05.includes('DN-118359')&&i05.indexOf('DN-69348')<i05.indexOf('DN-118359'),
    `sans département : ${ids(med0).filter(i=>i.startsWith('DN')).join(' ')} ; 05 : ${i05.filter(i=>i.startsWith('DN')).join(' ')}`);
  verifie('J4 plus d\'étiquette « Paris (75) » sur la médaille : département vide, portée nationale', B('DN-69348').dep===''&&!/Paris|75/.test(B('DN-69348').dep||''));
  const jum=[...ix.jumelles.keys()].map(i=>ix.recs[i]);
  verifie(`J5 règle « nationale devant » limitée aux démarches de même titre (${jum.length} démarches locales concernées)`, jum.every(r=>r.k==='dn'&&r.po!=='nat'&&ix.recs[ix.jumelles.get(ix.byId.get(r.id))].po==='nat'&&M.norm(ix.recs[ix.jumelles.get(ix.byId.get(r.id))].t)===M.norm(r.t)), jum.slice(0,3).map(r=>r.id).join(' '));
  const ddets=B('DN-118359').oa||'', caps=ix.recs.filter(r=>r.oa&&r.oa===r.oa.toUpperCase());
  verifie('J6 nom tout en capitales en casse normale, sigles gardés ; jamais un nom en casse mixte', /^Direction départementale de l'emploi, du travail, des solidarités et de la protection des populations des Hautes-Alpes/.test(ddets)&&/\(DDETSPP\)/.test(ddets)&&!caps.length&&!ix.recs.some(r=>r.oa&&r.o!==r.o.toUpperCase()), ddets);
  verifie('J7 nom d\'organisme coupé dans la carte (« … », nom complet en infobulle) : aucun nom plus large que la carte',
    /\.ligne-symb \.u-org\{min-width:0;max-width:min\(100%,30em\)\}/.test(gab)&&/\.ligne-symb \.org-nom\{min-width:0;overflow:hidden;text-overflow:ellipsis\}/.test(gab)&&/class="org-nom" title="/.test(gab));
  const modeles=ix.recs.filter(r=>r.k==='dn'&&r.po==='nat'&&M.MODELES.test(r.o||'')), voirie=top("Demande d'autorisation de voirie ou de commencement de travaux",{},12);
  verifie(`J8 démarches de la DINUM et de la DINSIC hors de la règle « nationale devant » (${modeles.length} nationales) : elles ne masquent aucune démarche locale`,
    modeles.length&&![...ix.jumelles.values()].some(n=>M.MODELES.test(ix.recs[n].o||''))&&!ix.jumelles.has(ix.byId.get('DN-7286'))&&!ix.jumelles.has(ix.byId.get('DN-5237'))&&ids(voirie).includes('DN-5237'), ids(voirie).filter(i=>i.startsWith('DN')).join(' '));
  verifie('J9 médaille sans territoire : la nationale a des démarches locales de même titre, la carte propose « préciser le vôtre » ; avec le 05, la démarche des Hautes-Alpes est citée',
    M.jumellesDe(ix,B('DN-69348')).map(i=>ix.recs[i].id).includes('DN-118359')&&/Certains départements ont leur propre démarche&nbsp;: <button type="button" class="lien-changer" id="preciser-dep">préciser le vôtre<\/button>/.test(gab)&&/a aussi sa propre démarche/.test(gab));
  const pdf=M.avantDeCommencer(B('DN-69348'),META).lignes[0].liens[0];
  verifie('J10 à côté du formulaire à vide : « PDF non accessible, selon la déclaration de la plateforme », lu dans accessibilite_plateformes.json',
    META.acc_plateformes.dn.pdf_non_accessible===true&&/PDF non accessible, selon la déclaration de la plateforme/.test(pdf.titre)&&!/PDF non accessible/.test(M.avantDeCommencer(B('DN-69348'),{}).lignes[0].liens[0].titre), pdf.titre);
  const dnD=B('DN-69348'), spD=ix.recs.find(r=>r.k==='sp'&&M.symboles(r,META).voies.length), SD=M.symboles(dnD,META);
  verifie('D1 délais constatés : le lien vers la page statistiques (adresse de la démarche, « commencer » → « statistiques ») existe pour toute démarche Démarche Numérique (dans « Avant de commencer » ou, sinon, dans le détail « ? »)',
    SD.delais&&SD.delais.url==='https://demarche.numerique.gouv.fr/statistiques/'+dnD.u&&ix.recs.filter(r=>r.k==='dn'&&r.u).every(r=>{const d=M.symboles(r,META).delais;return d&&/\/statistiques\//.test(d.url)&&!/\/commencer\//.test(d.url);})&&/Moteur\.detailSymboles\(r, META \|\| \{\}\)/.test(gab), SD.delais&&SD.delais.url);
  verifie('D2 délais constatés : rien pour une fiche service-public', spD&&!M.symboles(spD,META).delais&&!M.avantDeCommencer(spD,META).lignes.some(l=>l.cle==='delais'), spD&&spD.id);
  const sansBloc={...dnD,u:undefined}, avecBloc=M.avantDeCommencer(dnD,META);
  verifie('D3 délais constatés : la ligne n\'ouvre jamais seule « Avant de commencer » ; elle s\'ajoute quand le bloc existe, avec le nouvel onglet signalé, sans aucun chiffre',
    M.avantDeCommencer({k:'dn',id:'X',t:'x'},META).lignes.length===0&&avecBloc.lignes.some(l=>l.cle==='delais'&&/nouvel onglet/.test(l.liens[0].titre)&&!/\d/.test(l.texte))&&ix.recs.filter(r=>r.k==='dn').slice(0,3000).every(r=>{const L=M.avantDeCommencer(r,META).lignes;return !(L.length===1&&L[0].cle==='delais');}), avecBloc.resume);
  // Une information, un seul endroit : aucune phrase (ni aucun lien) à la fois dans le « ? » et dans « Avant de commencer ».
  const phrases=(t)=>t.split(/(?<=[.;:])\s+|\s+·\s+/).map(x=>M.norm(x)).filter(x=>x.split(' ').length>=3);
  const doublons=[]; let nDet=0, nDelaisDet=0, nAccDet=0;
  for(const r of ix.recs){ const D=M.detailSymboles(r,META); if(!D.length) continue; nDet++; const A=M.avantDeCommencer(r,META);
    const pa=new Set(A.lignes.flatMap(l=>[...phrases(l.texte),...l.liens.map(x=>x.url)]));
    const pd=D.flatMap(d=>[...phrases(d.texte),...(d.lien?[d.lien.url]:[])]);
    if(pd.some(x=>pa.has(x))) doublons.push(r.id+' : '+pd.find(x=>pa.has(x)));
    if(D.some(d=>d.lien)) nDelaisDet++; if(D.some(d=>/^Plateforme /.test(d.texte))) nAccDet++; }
  verifie(`U1 une information, un seul endroit : aucune phrase ni aucun lien à la fois dans le « ? » et dans « Avant de commencer » (${nDet} démarches ; délais dans le « ? » faute de place : ${nDelaisDet} ; accessibilité de la plateforme dans le « ? » : ${nAccDet})`, !doublons.length, doublons.slice(0,3).join(' | '));
  const D69=M.detailSymboles(B('DN-69348'),META).map(d=>d.texte).join(' ');
  verifie('U2 médaille (bloc « Avant de commencer » présent) : le « ? » garde comment faire et FranceConnect, sans délais ni accessibilité de la plateforme', /^Comment faire/.test(D69)&&/FranceConnect/.test(D69)&&!/Délais|Plateforme/.test(D69), D69);
  const rep=ix.recs.filter(r=>{const S=M.symboles(r,META),c=new Set(M.avantDeCommencer(r,META).lignes.map(l=>l.cle));
    return (S.vig.length&&c.has('vigilance'))||(S.simp.some(x=>x.cle==='rec')&&M.avantDeCommencer(r,META).lignes.some(l=>Object.keys(M.RECUPERE).some(k=>l.texte.includes(M.PRE_PHRASES[k]))));});
  verifie('U3 même information, autre formulation : ni vigilance ni données récupérées répétées dans « Avant de commencer » (elles sont dans le « ? »)', !rep.length, rep.slice(0,3).map(r=>r.id).join(' '));
  verifie('Z3 « Accessibilité non connue » n\'est pas dans la ligne de la carte (seulement dans le détail et « Avant de commencer »)', /!\["inconnue", "plateforme"\]\.includes\(S\.acc\.niveau\)/.test(gab));
  const avecVoies=ix.recs.filter(r=>M.symboles(r,META).voies.length).length;
  console.log(`        ${avecVoies} démarches avec des symboles « comment faire »`); }
{ // Règle « démarche sûre » retenue (PR 76, variante d) : ni démarche hors sujet affirmée, ni démarche juste perdue.
  const P=(q,o={})=>M.choisir(ix,q,o).principal;
  const ko=[];
  const f1=P("Demander la médaille d'honneur du travail"); if(f1&&f1.id==='DN-69676') ko.push('F1 : médaille des chemins de fer');
  const r4=P("Ma vitrine a été cassée pendant les manifestations, quelle aide ?"); if(r4&&r4.id==='SP-F760') ko.push('R4 : fiche sur les demandeurs d\'emploi');
  const r5=P("Mon club de foot a besoin d'argent pour acheter des équipements."); if(r5&&r5.id==='DN-78683') ko.push('R5 : compte-rendu de subvention');
  const r1=P("Je tiens un restaurant à Grenoble et je veux embaucher un salarié étranger. Dois-je vérifier son titre de séjour, et comment ?"); if(!r1||r1.id!=='DN-13583') ko.push('R1 perd DN-13583');
  verifie('Démarche sûre : F1, R4, R5 sans démarche hors sujet ; R1, R3, R6 gardent la leur (R3 et R6 ci-dessus)', !ko.length, ko.join(' | ')||`F1 : ${f1?f1.id:'Démarches possibles'} ; R4 : ${r4?r4.id:'Démarches possibles'} ; R5 : ${r5?r5.id:'Démarches possibles'}`);
  const t11=M.choisir(ix,"aide pour adapter mon logement handicap",{});
  verifie('Lieu : pas de question de lieu au-dessus d\'une démarche nationale sûre (T11)', !(t11.principal&&t11.demanderLieu), t11.principal?t11.principal.id:'pas de démarche sûre'); }
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
  verifie('Ton : la consigne de l\'assistant ne propose plus « Je ne trouve pas… » en ouverture', !/dis-le franchement|Je ne trouve pas de démarche en ligne pour cela/.test(page), '');
  // Recadrage « répertoire » (« Où faire sa démarche ? ») : la page oriente, elle ne recommande pas ; elle ne se présente ni
  // comme un conseiller ni comme un « moteur ». Seule exception : la promesse sous le champ, « Il ne remplace ni l'organisme
  // qui décide, ni un conseiller. »
  const visible=(h)=>h.replace(/<script[\s\S]*?<\/script>|<style[\s\S]*?<\/style>/g,' ').replace(/<[^>]+>/g,' ').replace(/&nbsp;/g,' ');
  const comment=fs.readFileSync(path.join(__dirname,'..','..','trouver-sa-demarche-comment.html'),'utf8');
  const NE_PAS=/\bconseillers?\b|nous vous recommandons|\bmoteurs?\b/i, PROMESSE=/ni un conseiller\./g;
  const stats=(page.match(/\$\("ligne-stats"\)\.innerHTML = `([^`]*)`/)||[])[1]||'';
  const consigneIA=(page.match(/function consigne\(q\) \{([\s\S]*?)\n\}/)||[])[1]||'';
  const textesPage=[...textes,...Object.values(M.PRE_PHRASES).map((t,i)=>['« Avant de commencer » '+(i+1),t]),['page',visible(page)],['« Comment ça marche »',visible(comment)],['ligne sous le champ',stats],['consigne de l\'assistant',consigneIA]];
  const fautesR=textesPage.filter(([,s])=>NE_PAS.test(sansRefs(s).replace(PROMESSE,''))).map(([n,s])=>n+' : '+sansRefs(s).replace(PROMESSE,'').match(NE_PAS)[0]);
  verifie(`Ton : ni « conseiller », ni « nous vous recommandons », ni « moteur » dans les textes de la page (${textesPage.length} textes)`, !!stats&&!fautesR.length, fautesR.join(' | ')); }
console.log(`\n${echecs?echecs+' échec(s)':'Toutes les situations de référence passent'}${attente?', '+attente+' en attente':''}.`);
if(echecs) process.exit(1);
