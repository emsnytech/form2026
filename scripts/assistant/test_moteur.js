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
  verifie('B1 démarche DN avec pièces et pré-remplissage (DN-13583) : titre « 28 questions, 3 pièces », première ligne « Voir le formulaire (PDF…) » sans le décompte, puis « Données récupérées : SIRET » (pas dans le « ? »)', A1.resume==='Avant de commencer · 28\u00a0questions, 3\u00a0pièces'&&A1.lignes[0].cle==='questions'&&A1.lignes[0].texte===''&&A1.lignes.some(l=>l.cle==='donnees'&&l.texte==='Données récupérées : SIRET')&&!M.detailSymboles(B('DN-13583'),META).some(d=>/Données récupérées/.test(d.texte)), A1.lignes.map(l=>l.texte).join(' | '));
  verifie('B1 lien vers le formulaire à vide, en PDF, avec sa précision', /\/commencer\/declaration-prealable-embauche\/dossier_vide$/.test(A1.lignes[0].liens[0].url)&&/pas pour le remplir/.test(A1.lignes[0].liens[0].titre), A1.lignes[0].liens[0].url);
  const sans=ix.recs.find(r=>r.k==='sp'&&/^SP-R/.test(r.id)&&!r.sva&&!r.obs), A2=M.avantDeCommencer(sans);
  verifie('B2 démarche sans aucune donnée : pas de bloc', !A2.lignes.length&&!A2.resume, sans.id+' '+sans.t);
  const avec=ix.recs.filter(r=>M.avantDeCommencer(r,META).lignes.length), delai=avec.filter(r=>M.avantDeCommencer(r,META).lignes.some(l=>l.cle==='delai'||(l.cle==='delais'&&/\d/.test(l.texte+l.liens.map(x=>x.texte).join(' ')))||(!['vigilance','delais'].includes(l.cle)&&/d[ée]lai/i.test(l.texte))));
  verifie(`B3 aucun délai affiché sans donnée par démarche (${avec.length} blocs)`, !delai.length, delai.slice(0,3).map(r=>r.id).join(' ')||'aucun délai');
  verifie(`B4 au plus ${M.MAX_AVANT} lignes, et l'IBAN n'est pas présenté comme rempli`, avec.every(r=>M.avantDeCommencer(r,META).lignes.length<=M.MAX_AVANT)&&!('IBAN' in M.PRE_COURT));
  const obsPc=ix.recs.find(r=>r.obs&&r.acc&&r.acc[0]!=='TC'), A5=M.avantDeCommencer(obsPc,META), l5=A5.lignes.find(l=>l.cle==='aide');
  verifie('B5 démarche de l\'Observatoire non totalement accessible : le niveau dans le « ? », seulement le renvoi vers la France services la plus proche dans « Avant de commencer »',
    !!l5&&!/conforme|partielle|%/.test(l5.texte)&&/France services/.test(l5.liens[0].texte)&&l5.liens[0].url==='#carte-ou'&&M.detailSymboles(obsPc,META).some(d=>/^(Accessibilité partielle|Non conforme)/.test(d.texte)), obsPc.id+' : '+(l5?l5.texte:'pas de ligne'));
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
  // Vigilances Services Publics + hors Démarche Numérique (suite de la PR 94) : portée dans l'infobulle.
  const avecSpp=(f)=>ix.recs.filter(r=>r.spp&&f(r)), dom=(r)=>M.siteLisible(r.l)&&(/^https?:\/\/([^\/]+)/.exec(r.l)||[])[1];
  const ants=avecSpp(r=>r.k==='sp'&&/ants\.gouv\.fr/.test(r.lc||r.l||'')&&r.spp[4]), anef=avecSpp(r=>/administration-etrangers-en-france\.interieur\.gouv\.fr/.test(r.lc||r.l||''));
  verifie(`Y8 ANTS par domaine : ${ants.length} fiches, infobulle « retours sur … (ANTS) », jamais moncompte.ants.gouv.fr`,
    ants.length===44&&ants.every(r=>S(r.id).vig.every(v=>/retours sur (l'immatriculation|le permis de conduire|les passeports et cartes d'identité) \(ANTS\), pas seulement cette démarche/.test(v.detail)))
    &&!avecSpp(r=>/moncompte\.ants/.test(r.l||'')).length&&B('SP-R45443').spp.length===4, ants.length+' fiches');
  verifie(`Y9 titres de séjour : ${anef.length} fiches vers l'ANEF, infobulle « retours sur les titres de séjour (ANEF) »`,
    anef.length===12&&anef.every(r=>S(r.id).vig.length&&S(r.id).vig.every(v=>/retours sur les titres de séjour \(ANEF\)/.test(v.detail))), anef.map(r=>r.id).slice(0,3).join(' '));
  const prefH=avecSpp(r=>r.k==='dn'&&r.spp[4]==='hors retours sur les étrangers'), prefE=avecSpp(r=>r.k==='dn'&&/^Préfecture/.test(r.spp[3])&&!r.spp[4]);
  verifie(`Y10 préfectures : ${prefH.length} démarches hors étrangers recalculées, ${prefE.length} gardent la vigilance complète (titre sur les étrangers)`,
    prefH.length>0&&prefH.every(r=>!/s[ée]jour|naturali|asile|[ée]tranger/i.test(r.t)&&S(r.id).vig.every(v=>/organisme « Préfecture[^»]*» \(hors retours sur les étrangers, pas seulement cette démarche\)/.test(v.detail)))
    &&prefE.every(r=>!/^Préfecture/.test(r.spp[3])||/s[ée]jour|naturali|asile|[ée]tranger|titre|r[ée]sident|statut|passeport|APS|TIR|DCEM|r[ée]c[ée]piss|nationalit|option|autorisation|r[ée]gularis|ressortissant|visa|BPI|TUE|OQTF|protection|apatrid|regroupement|OFII|OFPRA|ANEF|r[ée]fugi/i.test(r.t)), prefE.filter(r=>!/s[ée]jour/i.test(r.t)).slice(0,3).map(r=>r.id+' '+r.t).join(' | '));
  verifie('Y11 France Travail (structure) écarté : aucune fiche vers candidat.francetravail.fr ne reçoit la vigilance des directions régionales',
    !avecSpp(r=>/candidat\.francetravail\.fr/.test(r.l||'')&&r.spp[4]).length&&!avecSpp(r=>/France Travail/.test(r.spp[3]||'')).length);
  const accDn=S('DN-13583').acc;
  const accP=META.acc_plateformes.dn, moisP="janvier février mars avril mai juin juillet août septembre octobre novembre décembre".split(" ")[+accP.mise_a_jour.slice(5,7)-1];
  verifie('Y7 démarche Démarche Numérique : taux de la plateforme (déclaration publiée), pour une démarche type ; vigilance par organisme',
    accDn.niveau==='plateforme'&&accDn.ligne.startsWith(`Plateforme Démarche Numérique : accessibilité partielle (${accP.taux}, déclaration d'${moisP} ${accP.mise_a_jour.slice(0,4)}), pour une démarche type. Le taux peut être un peu différent selon la démarche, par exemple si elle contient une carte.`)
    &&!ix.recs.some(r=>r.k==='dn'&&!r.obs&&M.symboles(r,META).acc.niveau!=='plateforme')&&M.avantDeCommencer(B('DN-13583'),META).lignes.some(l=>l.cle==='accessibilite'&&l.texte===`Accessibilité : ${accP.taux} (plateforme)`&&/pour une démarche type/.test(l.titre)&&!l.liens.length)
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
  verifie('S3 FranceConnect+ s\'affiche « FranceConnect+ », nommé en clair ; « Non », « À venir » ou une habilitation seule : rien',
    fcPlus.texte==='FranceConnect+'&&/FranceConnect\+/.test(fcPlus.detail)&&['Non','À venir','Non applicable'].every(v=>!SIMP({...B('SP-R49813'),fc:v}).length)&&!SIMP({...B('SP-R49813'),fc:undefined,datapass:['FranceConnect']}).length, fcPlus.detail);
  const VRAIS=new Set(Object.keys(M.RECUPERE)), attendu=ix.recs.filter(r=>r.k==='dn'&&(r.pre||[]).some(p=>VRAIS.has(p))).length, recs=ix.recs.filter(r=>SIMP(r).includes('rec'));
  const faux=recs.filter(r=>r.k!=='dn'||!(r.pre||[]).some(p=>VRAIS.has(p)));
  const seulIban=ix.recs.find(r=>r.k==='dn'&&r.pre.length&&r.pre.every(p=>p==='IBAN')), seulPre=ix.recs.find(r=>r.k==='dn'&&r.pre.length&&r.pre.every(p=>p==='Données préremplies'));
  verifie(`S4 « Données récupérées pour vous » : SIRET, RNA, RNF, Annuaire Éducation seulement (${recs.length} démarches) ; ni IBAN ni lien prérempli`,
    recs.length===attendu&&!faux.length&&[...VRAIS].join()==='SIRET (API Entreprise),RNA (associations),RNF (fondations),Annuaire Éducation'&&seulIban&&!SIMP(seulIban).includes('rec')&&(!seulPre||!SIMP(seulPre).includes('rec')), `${seulIban&&seulIban.id} (IBAN seul), ${seulPre&&seulPre.id} (prérempli seul)`);
  const siret=ix.recs.find(r=>r.k==='dn'&&r.pre.includes('SIRET (API Entreprise)')), dRec=M.symboles(siret,META).simp.find(s=>s.cle==='rec');
  verifie('S5 le détail nomme la source : « informations sur l\'entreprise récupérées à partir du SIRET (API Entreprise) »', /informations sur l'entreprise récupérées à partir du SIRET \(API Entreprise\)/.test(dRec.detail), siret.id+' : '+dRec.detail);
  verifie('S6 icônes neutres en gris (clé « key » pour FranceConnect, database-import), plus de « personne cochée », pas de logo FranceConnect, signaux juste après les modes',
    /id="ti-key"/.test(gab)&&!/ti-user-check/.test(gab)&&/fc: "key"/.test(gab)&&/id="ti-database-import"/.test(gab)&&/class="mode simp"/.test(gab)&&/\[\.\.\.modes, \.\.\.simp, \.\.\.srcUnits/.test(gab)&&!/franceconnect[^"' ]*\.(svg|png)|logo[-_ ]?franceconnect/i.test(gab), '');
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
  verifie('J10 « Voir le formulaire (PDF non accessible) », ou « (PDF) » quand la plateforme ne le dit pas, lu dans accessibilite_plateformes.json', META.acc_plateformes.dn.pdf_non_accessible===true&&pdf.apres==='(PDF non accessible)'&&pdf.texte==='Voir le formulaire'&&M.avantDeCommencer(B('DN-69348'),{}).lignes[0].liens[0].apres==='(PDF)', pdf.texte+' '+pdf.apres);
  const dnD=B('DN-69348'), spD=ix.recs.find(r=>r.k==='sp'&&M.symboles(r,META).voies.length), SD=M.symboles(dnD,META);
  verifie('D1 délais constatés : le lien vers la page statistiques (adresse de la démarche, « commencer » → « statistiques ») existe pour toute démarche Démarche Numérique (dans « Avant de commencer » ou, sinon, dans le détail « ? »)',
    SD.delais&&SD.delais.url==='https://demarche.numerique.gouv.fr/statistiques/'+dnD.u&&ix.recs.filter(r=>r.k==='dn'&&r.u).every(r=>{const d=M.symboles(r,META).delais;return d&&/\/statistiques\//.test(d.url)&&!/\/commencer\//.test(d.url);})&&/Moteur\.detailSymboles\(r, META \|\| \{\}, \{ site, avant \}\)/.test(gab), SD.delais&&SD.delais.url);
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
  verifie('U2 médaille (bloc « Avant de commencer » présent) : le « ? » garde comment faire et FranceConnect, sans délais ni accessibilité de la plateforme', /^En ligne, sur Démarche Numérique/.test(D69)&&/Connexion avec FranceConnect/.test(D69)&&!/Délais|Accessibilité/.test(D69), D69);
  const rep=ix.recs.filter(r=>{const S=M.symboles(r,META),c=new Set(M.avantDeCommencer(r,META).lignes.map(l=>l.cle));
    return (S.vig.length&&c.has('vigilance'))||(M.avantDeCommencer(r,META).lignes.some(l=>l.cle==='donnees')&&M.detailSymboles(r,META).some(d=>/Données récupérées/.test(d.texte)));});
  verifie('U3 même information, autre formulation : ni vigilance dans « Avant de commencer », ni données récupérées aux deux endroits', !rep.length, rep.slice(0,3).map(r=>r.id).join(' '));
  const m69=B('DN-69348'), d69=M.detailSymboles(m69,META).map(d=>d.texte).join(' ');
  verifie('O1 médaille passée en nationale : « Ministère de l\'Intérieur » (Sirene, SIRET 11001401600015) affiché, l\'organisme déclaré dans le « ? » ; aucune autre démarche n\'a ce nom de remplacement',
    m69.on==="Ministère de l'Intérieur"&&/nomOrg = \(r\) => r\.on \|\| r\.oa \|\| r\.o/.test(gab)&&/Déclarée par : Préfecture, sous-préfecture, DDETSPP, DRIEETS/.test(d69)&&ix.recs.filter(r=>r.on).every(r=>r.po==='nat'), ix.recs.filter(r=>r.on).map(r=>r.id).join(' '));
  verifie('Z3 « Accessibilité non connue » n\'est pas dans la ligne de la carte (seulement dans le détail et « Avant de commencer »)', /!\["inconnue", "plateforme"\]\.includes\(S\.acc\.niveau\)/.test(gab));
  // Sobriété (consigne du 25/11) : une ligne = un symbole et quelques mots, sans explication ni mention promotionnelle.
  const texteLigne=(l)=>(l.texte||'')+[...(l.liens||[]),...(l.lien?[l.lien]:[])].map(x=>' '+x.texte+(x.apres?' '+x.apres:'')).join('');
  const longues=[], sansIco=[], pub=[], presque=[]; const icones=new Set([...gab.matchAll(/<symbol id="ti-([a-z-]+)"/g)].map(m=>m[1]));
  const PUB=/impots\.gouv, ameli|La Poste|le propose sur toutes|descriptif du|peut être un peu différent|\b\d{2}\/\d{2}\/\d{4}\b|Légende complète/;
  const mots=(t)=>new Set(M.norm(t).split(' ').filter(w=>w.length>2));
  for(const r of ix.recs){ const D=M.detailSymboles(r,META), A=M.avantDeCommencer(r,META).lignes;
    for(const l of [...D,...A]){ const t=texteLigne(l);
      if(!l.organisme&&t.length>90) longues.push(r.id+' : '+t); if(!icones.has(l.ico)) sansIco.push(r.id+' : '+t+' ('+l.ico+')'); if(PUB.test(t)) pub.push(r.id+' : '+t); }
    for(const d of D) for(const a of A){ const x=mots(texteLigne(d)), y=mots(texteLigne(a)); const c=[...x].filter(w=>y.has(w)).length;
      if(c>=2&&c>=0.6*Math.min(x.size,y.size)) presque.push(r.id+' : '+texteLigne(d)+' ≈ '+texteLigne(a)); } }
  verifie(`N1 aucune ligne de plus de 90 caractères dans le « ? » et « Avant de commencer » (${ix.recs.length} démarches ; le nom complet de l'organisme est à part)`, !longues.length, longues.slice(0,3).join(' | '));
  verifie('N2 chaque ligne commence par un symbole du sprite', !sansIco.length, sansIco.slice(0,3).join(' | '));
  verifie('N3 ni mention promotionnelle, ni explication, ni date de source dans le texte des lignes', !pub.length, pub.slice(0,3).join(' | '));
  verifie('N4 aucune phrase presque identique dans le « ? » et « Avant de commencer » pour une même démarche', !presque.length, presque.slice(0,3).join(' | '));
  const resumes=ix.recs.map(r=>M.avantDeCommencer(r,META).resume).filter(Boolean), mauvais=resumes.filter(x=>!/^Avant de commencer( · \d+\u00a0(questions?|pièces?)(, \d+\u00a0pièces?)?)?$/.test(x));
  verifie(`N5 titre replié « Avant de commencer », suivi au plus de deux chiffres (${resumes.length} blocs)`, !mauvais.length&&M.avantDeCommencer(B('DN-69348'),META).resume==='Avant de commencer · 75\u00a0questions, 6\u00a0pièces', mauvais.slice(0,3).join(' | ')||M.avantDeCommencer(B('DN-69348'),META).resume);
  const L16=M.detailSymboles(B('SP-R16396'),META), F1367=M.detailSymboles(B('SP-F1367'),META,{site:B('SP-R16396').l});
  verifie('N6 « En ligne » dit sur quel site, lu dans le lien du service en ligne (sans « www. » ni chemin)', L16[0].texte==='En ligne, sur interieur.gouv.fr'&&F1367[0].texte==='En ligne, sur interieur.gouv.fr'&&M.siteLisible('https://www.impots.gouv.fr/accueil')==='impots.gouv.fr'&&M.siteLisible('https://immatriculation.ants.gouv.fr/x')==='ants.gouv.fr'&&M.siteLisible('https://wwwd.caf.fr/wps')==='caf.fr'&&M.detailSymboles(B('DN-69348'),META)[0].texte==='En ligne, sur Démarche Numérique', L16.map(d=>d.texte).join(' | '));
  verifie('N7 ProConnect ne s\'affiche nulle part (non établi, PR 89) ; FranceConnect avec la clé', !ix.recs.some(r=>M.symboles(r,META).simp.some(x=>/ProConnect/.test(x.texte)))&&M.detailSymboles(B('DN-69348'),META).some(d=>d.ico==='key'&&d.texte==='Connexion avec FranceConnect'));
  verifie('N8 un seul lien « Sources » en bas de « Avant de commencer », un petit lien « Légende » en bas du « ? »', /class="avant-src" href="\$\{esc\(src\)\}">Sources<\/a>/.test(gab)&&/>Légende<\/a>/.test(gab)&&!/>source<\/a>` : ""\) \+ `<\/li>`/.test(gab));
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
  const textesPage=[...textes,...Object.values(M.PRE_COURT).map((t,i)=>['« Avant de commencer » '+(i+1),t]),['page',visible(page)],['« Comment ça marche »',visible(comment)],['ligne sous le champ',stats],['consigne de l\'assistant',consigneIA]];
  const fautesR=textesPage.filter(([,s])=>NE_PAS.test(sansRefs(s).replace(PROMESSE,''))).map(([n,s])=>n+' : '+sansRefs(s).replace(PROMESSE,'').match(NE_PAS)[0]);
  verifie(`Ton : ni « conseiller », ni « nous vous recommandons », ni « moteur » dans les textes de la page (${textesPage.length} textes)`, !!stats&&!fautesR.length, fautesR.join(' | '));
  // Accueil et réponse, sur le modèle d'Altinn (consigne « sobriété », section 4) : ni chiffres ni sources sur l'accueil,
  // la phrase sur la décision une seule fois, dans le pied de page.
  const vis=visible(page).replace(/\s+/g,' ');
  verifie('A5 accueil : ni chiffres ni sources, ni volumes de dossiers dans « Les plus demandées », « Comment ça marche » seul sous le champ, plus de phrase sur l\'API Géo ; « la décision appartient à l\'organisme cité » une seule fois, dans le pied de page',
    stats.startsWith('<a class="lien-comment"')&&stats.endsWith('>Comment ça marche</a>')&&!/recense|fmt\(/.test(stats)&&!/recense|API Géo de l'État\)\. Rien d'autre|Il ne remplace ni|Sources : /.test(vis)&&(vis.match(/la décision appartient à l'organisme cité/g)||[]).length===1&&/<footer[\s\S]*la décision appartient à l'organisme cité/.test(page)
    &&!/dossiers_arrondis|plus de \$\{/.test(page)&&/Décrivez votre situation, avec votre commune\./.test(page)&&/Précisez votre commune pour voir où aller\./.test(page), stats); }
// Haut de l'accueil (consigne « sobriété », 4 bis) et réponse de l'assistant (modèle America.gov) : contrôles sur le gabarit assemblé.
{ const page=fs.readFileSync(path.join(__dirname,'..','..','trouver-sa-demarche.html'),'utf8'), vis=page.replace(/<script[\s\S]*?<\/script>|<style[\s\S]*?<\/style>/g,' ').replace(/<[^>]+>/g,' ').replace(/&nbsp;/g,' ').replace(/\s+/g,' ');
  const accueil=(page.match(/<section id="vue-accueil"[\s\S]*?<form class="ask"/)||[''])[0];
  verifie('A6 haut de l\'accueil : le titre, une phrase, le champ ; plus de sous-titre ni de « Votre situation, avec vos mots »',
    !/sous-titre|Le répertoire des démarches administratives/.test(accueil)&&!/Votre situation, avec vos mots/.test(vis)&&/<h1 id="titre-accueil">Que voulez-vous faire&nbsp;\?<\/h1>/.test(page)&&/placeholder="Ex\. : Je n'arrive plus à payer ma facture d'électricité, j'habite à Rezé"/.test(page));
  const quota=(page.match(/function majQuota\(\) \{[\s\S]*?\n/)||[''])[0]+(page.match(/function majQuota\(\)[\s\S]*?if \(!r\)[^\n]*/)||[''])[0];
  verifie('A7 version avec assistant : « Version de test avec IA · En savoir plus » ; compteur seulement à 3 questions ou moins ; ligne « une commune suffit » gardée',
    /Version de test avec IA · <a[^>]*>En savoir plus<\/a>/.test(page)&&!/un assistant d'IA \(Claude\) cherche pour vous/.test(page)&&/r > 3 \? "" : r \? `Encore \$\{r\} question/.test(quota)&&/Sans nom, numéro, adresse ni information de santé&nbsp;: une commune suffit\./.test(page));
  const cons=(page.match(/function consigne\(q\) \{([\s\S]*?)\n\}/)||[])[1]||'';
  verifie('A8 réponse de l\'assistant : puces dans l\'ordre de l\'action, liens dans les phrases, « rien à faire » en tête et non répété ; plus de bloc « Liens de cette réponse »',
    /2 à 5 puces courtes/.test(cons)&&!/TROIS PHRASES AU PLUS/.test(cons)&&/rien_a_faire.*ne la répète pas/.test(cons)&&!/Liens de cette réponse|liens-liste/.test(page)&&/\$\("rep-texte"\)\.prepend\(rien\)/.test(page)&&/class="ext" aria-hidden="true">↗/.test(page));
  verifie('A9 sous la réponse : une pastille de source, deux questions de suite au plus, « Signaler une erreur » (formulaire sans donnée personnelle) ; champ « Une autre question ? » fixé en bas',
    /<span class="source">Source&nbsp;: /.test(page)&&/return q\.slice\(0, 2\)/.test(page)&&/issues\/new\?template=signaler-erreur\.yml/.test(page)&&fs.existsSync(path.join(__dirname,'..','..','.github','ISSUE_TEMPLATE','signaler-erreur.yml'))
    &&/placeholder="Une autre question \?"/.test(page)&&/#ff\.ff-bas\{position:sticky;bottom:0/.test(page)&&!/Préciser ma situation/.test(page)); }
// Liens vers les formulaires (perdus avec la refonte « interface sobre ») : cerfa des ressources service-public, formulaire à vide de
// Démarche Numérique dans le « ? » des cartes « Démarches possibles », sans répétition avec « Avant de commencer ».
{ const META=JSON.parse(fs.readFileSync(path.join(__dirname,'..','..','donnees','assistant','index_meta.json'),'utf8'));
  const sp=R.filter(r=>r.cerfa), avec=sp.filter(r=>M.symboles(r,META).cerfa), c=M.symboles(R.find(r=>r.id==='SP-R10103'),META).cerfa;
  const sansLien=sp.filter(r=>!M.symboles(r,META).cerfa&&M.symboles(r,META).voies.some(v=>v.includes('formulaire')));
  const page=fs.readFileSync(path.join(__dirname,'..','..','trouver-sa-demarche.html'),'utf8');
  verifie(`L1 fiche avec cerfa : « Formulaire cerfa n° 13974*02 », lien vers le formulaire (${avec.length} des ${sp.length} ressources avec cerfa ; les autres n'ont pas le symbole « Formulaire »)`,
    c&&c.texte==='Formulaire cerfa n° 13974*02'&&c.url==='https://www.formulaires.service-public.gouv.fr/gf/cerfa_13974.do'&&!sansLien.length&&/<a class="mode cerfa" href=/.test(page)&&!R.some(r=>r.k==='dn'&&M.symboles(r,META).cerfa), c&&c.texte);
  const dn=R.find(r=>r.id==='DN-69348'), pos=M.detailSymboles(dn,META,{avant:false}), vd=M.detailSymboles(dn,META);
  const lf=pos.find(d=>d.lien&&/\/dossier_vide$/.test(d.lien.url));
  verifie('L2 carte « Démarches possibles » (Démarche Numérique) : « Voir le formulaire (PDF) » dans le « ? » ; pas dans le « ? » de « Votre démarche », où « Avant de commencer » le porte',
    !!lf&&lf.lien.texte==='Voir le formulaire'&&/^\(PDF/.test(lf.lien.apres)&&lf.ico===M.ICO.formulaire&&!vd.some(d=>d.lien&&/dossier_vide/.test(d.lien.url))&&M.avantDeCommencer(dn,META).lignes.some(l=>l.liens.some(x=>/dossier_vide/.test(x.url)))
    &&/ligneSymboles\(r, nomOrg\(r\) \+ " · Démarche Numérique", nomOrg\(r\), undefined, false\)/.test(page), lf&&lf.lien.url); }
// Expressions « carte grise » et « liste(s) électorale(s) » ; service en ligne devant le formulaire. R : premier résultat de la
// recherche ; A : « Votre démarche ».
{ const cas=[['carte grise perdue','SP-R47917'],['inscription liste électorale','SP-R16396'],["m'inscrire sur les listes électorales",'SP-R16396'],['inscripsion liste electoral','SP-R16396']];
  for(const [q,att] of cas){ const qc=M.corriger(q).texte, t=M.search(ix,qc,{k:5}).map(x=>x.r.id), C=M.choisir(ix,qc,{k:20});
    verifie(`R7 « ${q} » : ${att} en 1re position`, t[0]===att, t.join(' '));
    verifie(`A10 « ${q} » : ${att} en « Votre démarche »`, C.principal&&C.principal.id===att, C.principal&&C.principal.id); }
  const g=M.analyse('carte grise perdue').termes; verifie('R7 « carte grise » est une expression (certificat d\'immatriculation), comptée double par la règle « démarche sûre »', [...g.keys()].some(k=>/_carte_grise/.test(k))); }
// Passeport (obtenir, refaire) et fiches propres à un territoire, rétrogradées si la question ne cite pas ce territoire.
{ for(const [q,att] of [['passeport','SP-R42946'],['faire un passeport','SP-R42946'],['refaire mon passeport','SP-R62484']]){
    const t=M.search(ix,q,{k:5}).map(x=>x.r.id), C=M.choisir(ix,q,{k:20});
    verifie(`R8 « ${q} » : ${att} (pré-demande de passeport, ANTS) en 1re position`, t[0]===att, t.join(' '));
    verifie(`A11 « ${q} » : ${att} en « Votre démarche »`, C.principal&&C.principal.id===att, C.principal&&C.principal.id); }
  const tal=M.search(ix,'passeport talent',{k:3}).map(x=>x.r);
  verifie('R8 « passeport talent » : aucune pré-demande de passeport dans les 3 premiers (titre de séjour)', !tal.some(r=>/^SP-R(42946|62484)$/.test(r.id)), tal.map(r=>r.id).join(' '));
  const t1=M.search(ix,'inscription liste électorale',{k:3}).map(x=>x.r.id), t2=M.search(ix,'inscription liste électorale Nouvelle-Calédonie',{k:3}).map(x=>x.r.id);
  verifie('R9 territoire : la fiche Nouvelle-Calédonie hors des 3 premiers pour « inscription liste électorale », en tête quand la question cite la Nouvelle-Calédonie', !t1.includes('SP-R63206')&&t2[0]==='SP-R63206', t1.join(' ')+' | '+t2.join(' '));
  const r1=M.search(ix,'demande de RSA',{k:3}).map(x=>x.r.id), r2=M.search(ix,'demande de RSA à Mayotte',{k:3}).map(x=>x.r.id);
  verifie('R9 territoire : « RSA (Mayotte) » hors des 3 premiers pour « demande de RSA », dans les 3 premiers pour « demande de RSA à Mayotte »', !r1.includes('SP-R931')&&r2.includes('SP-R931'), r1.join(' ')+' | '+r2.join(' ')); }
// Liens vers une page de connexion (remplacés par l'adresse directe du téléservice, sinon par la fiche), renouvellement de
// passeport ou de carte d'identité, fiches propres à l'étranger, phrase d'introduction, libellés en double.
{ const cx=/(\/(login\w*|connexion|signin|sign_in|authorize|oauth2?|openid-connect|auth|cas\/login|authentification)(?=[\/?#.]|$))|\/mademarche\//i;
  const reste=R.filter(r=>r.k==='sp'&&r.l&&cx.test(r.l)), rempl=R.filter(r=>r.lc);
  verifie(`C1 aucun lien « l » vers une page de connexion (${rempl.length} remplacés : ${rempl.filter(r=>r.l!==r.u).length} par l'adresse directe, ${rempl.filter(r=>r.l===r.u).length} par la fiche)`,
    !reste.length&&rempl.length>100&&rempl.every(r=>r.l===r.u?!!r.ls:!cx.test(r.l)), reste.slice(0,3).map(r=>r.id+' '+r.l).join(' | '));
  const r66=R.find(r=>r.id==='SP-R66936'), r44=R.find(r=>r.id==='SP-R44607');
  verifie('C2 SP-R66936 (mademarche) mène à sa fiche ; SP-R44607 au téléservice nommé dans le lien de connexion (service=)',
    r66.l===r66.u&&/mademarche/.test(r66.lc)&&r44.l==='https://foret.agriculture.gouv.fr/teleprocedures-foret/', r66.l+' | '+r44.l);
  const META2=JSON.parse(fs.readFileSync(path.join(__dirname,'..','..','donnees','assistant','index_meta.json'),'utf8'));
  verifie('C3 lien remplacé par la fiche : le « ? » dit toujours sur quel site se fait la démarche', /En ligne, sur caf\.fr/.test(M.detailSymboles(R.find(r=>r.id==='SP-R1332'),META2)[0].texte), M.detailSymboles(R.find(r=>r.id==='SP-R1332'),META2)[0].texte);
  for(const [q,att] of [['je veux renouveler mon passeport','SP-R62484'],['renouvellement passeport','SP-R62484'],["renouveler ma carte d'identité",'SP-R62483']]){
    const t=M.search(ix,q,{k:5}).map(x=>x.r.id), C=M.choisir(ix,q,{k:20});
    verifie(`R10 « ${q} » : ${att} (pré-demande de renouvellement, ANTS) en tête et en « Votre démarche »`, t[0]===att&&C.principal&&C.principal.id===att, t.join(' ')); }
  const etr=['je veux renouveler mon passeport','renouvellement passeport','passeport','refaire mon passeport'].filter(q=>{const C=M.choisir(ix,q,{k:20});return C.principal&&C.principal.id==='SP-R66936'||M.principalDe([R.find(r=>r.id==='SP-R66936')],q)});
  verifie('R11 la fiche « Renouvellement à distance de passeport en Australie, au Canada… » jamais en « Votre démarche » sans l\'étranger ni ces pays dans la question', !etr.length, etr.join(' | ')||'aucune');
  const f=R.find(r=>r.id==='SP-F21091'), g=R.find(r=>r.id==='SP-F1759');
  verifie('R12 phrase d\'introduction : pas de fiche « en cas de vol » ou « de perte » si la question n\'en parle pas', M.casParticulier(R.find(r=>/en cas de vol/.test(r.t)),'je veux renouveler mon passeport')&&!M.casParticulier(R.find(r=>/en cas de vol/.test(r.t)),'on m\'a volé mon passeport')&&!M.casParticulier(f,'renouveler mon passeport'));
  const by=new Map(R.map(r=>[r.id,r])), lien=(x)=>(/^SP-R/.test(x.id)&&x.l)?x.l:x.u; let dup=[];
  for(const f of R.filter(r=>/^SP-F/.test(r.id))){const rs=(f.res||[]).map(i=>by.get(i)).filter(x=>x&&/imulateur|Téléservice|selNG/i.test(x.ty)).slice(0,2);
    const b=M.libellesUniques(rs.map(x=>({texte:M.libelleRessource(x),url:lien(x),origine:x.ls,titre:x.t}))); if(new Set(b.map(x=>x.texte)).size!==b.length) dup.push(f.id); }
  const ex=M.libellesUniques([{texte:'Faire une demande en ligne',url:'https://passeport.ants.gouv.fr/a'},{texte:'Faire une demande en ligne',url:'https://www.service-public.gouv.fr/b'}]).map(x=>x.texte);
  verifie('D1 aucun libellé de lien deux fois dans une carte « Aussi pour vous » ; deux liens différents de même libellé sont nommés par leur site', !dup.length&&ex.join(' | ')==='Faire une demande en ligne sur ants.gouv.fr | Faire une demande en ligne sur service-public.gouv.fr', dup.slice(0,3).join(' ')||ex.join(' | ')); }
// Lien d'origine vers une page de connexion : un bouton et un lien discret ; grands espaces lus dans grands_espaces.json.
{ const G=JSON.parse(fs.readFileSync(path.join(__dirname,'..','..','donnees','assistant','grands_espaces.json'),'utf8')).sites.map(x=>x.site);
  const caf=M.boutonsConnexion(R.find(r=>r.id==='SP-R1165')), pacs=M.boutonsConnexion(R.find(r=>r.id==='SP-R57680')), dir=M.boutonsConnexion(R.find(r=>r.id==='SP-R44607'));
  verifie('B10 grand espace (Caf) : bouton « Se connecter sur caf.fr » vers la connexion, lien « Lire la fiche »',
    caf&&caf.bouton.texte==='Se connecter sur caf.fr'&&/connect\.caf\.fr/.test(caf.bouton.url)&&caf.lien.texte==='Lire la fiche'&&/vosdroits\/R1165$/.test(caf.lien.url), caf&&caf.bouton.texte);
  verifie('B11 autre site (service-public « mademarche ») : bouton « Lire la fiche », lien « Se connecter directement sur service-public.gouv.fr »',
    pacs&&pacs.bouton.texte==='Lire la fiche'&&pacs.lien.texte==='Se connecter directement sur service-public.gouv.fr'&&/mademarche/.test(pacs.lien.url), pacs&&pacs.lien.texte);
  const cx=R.filter(r=>r.lc&&r.ls), grands=cx.filter(r=>r.lg), mal=cx.filter(r=>!!r.lg!==G.includes(M.siteLisible(r.lc)));
  verifie(`B12 ${cx.length} ressources à deux liens, dont ${grands.length} grands espaces (${G.join(', ')}, liste relue dans grands_espaces.json) ; adresse directe : un seul bouton`,
    cx.length===120&&grands.length>0&&!mal.length&&dir===null&&!/caf\.fr|ameli|impots|ants\.gouv/.test(fs.readFileSync(path.join(__dirname,'moteur.js'),'utf8').match(/function boutonsConnexion[\s\S]*?\n  \}/)[0]), mal.map(r=>r.id).join(' ')); }
// Schéma des sources (« Comment ça marche », référence v2) : trois colonnes, chiffres et dates lus dans les données.
{ const c=fs.readFileSync(path.join(__dirname,'..','..','trouver-sa-demarche-comment.html'),'utf8'), fig=(c.match(/<figure class="sources"[\s\S]*?<\/figure>/)||[''])[0];
  const me=JSON.parse(fs.readFileSync(path.join(__dirname,'..','..','donnees','assistant','index_meta.json'),'utf8')), fr=(n)=>n.toLocaleString('fr-FR').replace(/ /g,' ');
  const nfs=JSON.parse(fs.readFileSync(path.join(__dirname,'..','..','donnees','assistant','france_services.json'),'utf8')).structures.length, dc=(d)=>d.split('-').reverse().join('/');
  const att=[fr(me.demarches_en_ligne)+' démarches en ligne publiées (DINUM) · '+dc(me.date_export), fr(me.fiches)+' fiches et ressources, dont '+fr(R.filter(r=>r.cerfa).length)+' cerfa',
    fr(R.filter(r=>r.obs).length)+' démarches rattachées', me.observatoire, fr(R.filter(r=>r.spp).length)+' démarches avec vigilance', fr(nfs)+' structures', dc(me.date_export_dila)].map(x=>x.replace(/ /g,' '));
  const txt=fig.replace(/&nbsp;| /g,' '), manque=att.filter(a=>!txt.replace(/ /g,' ').includes(a));
  verifie('SC1 schéma des sources : trois colonnes (sources, traitement FORM, ce que vous obtenez), chiffres et dates lus dans les données, pointillés pour DataPass, Aides-territoires et la règle de réponse',
    (fig.match(/class="sc-col"/g)||[]).length===3&&!manque.length&&(fig.match(/sc-avenir/g)||[]).length===3&&/Délais constatés/.test(fig)&&/étudié ou en cours d'intégration\. Chiffres de l'index du/.test(c), manque.join(' | ')||'ok'); }
// Plusieurs besoins dans une question : « Vos démarches », une ligne par besoin, rangée par urgence (table relue besoins.json).
{ const TB=JSON.parse(fs.readFileSync(path.join(__dirname,'..','..','donnees','assistant','besoins.json'),'utf8')); M.chargerBesoins(TB);
  const q1="j'ai perdu mes papiers : carte identité, passeport, attestation assurance, carte bancaire, attestation sécurité sociale, carte vitale, j'habite à Blois";
  const b1=M.besoins(ix,q1), noms=b1.map(b=>b.nom), urg=b1.map(b=>b.urgence);
  verifie('BS1 papiers perdus à Blois : six lignes, opposition d\'abord, puis pièces d\'identité, puis le reste ; fiches « perte » de la table',
    b1.length===6&&noms[0]==='Carte bancaire'&&noms.slice(1,3).sort().join()==="Carte d'identité,Passeport"&&urg.every((u,i)=>!i||u>=urg[i-1])
    &&b1[0].rec.id==='SP-F31241'&&b1.find(b=>b.nom==="Carte d'identité").rec.id==='SP-F1344'&&b1.find(b=>b.nom==='Carte Vitale').rec.id==='SP-R49814'
    &&b1.find(b=>b.nom==="Attestation d'assurance").rec===null&&!b1[0].guichet&&!b1[1].guichet&&!b1[2].guichet&&b1.find(b=>b.nom==='Carte Vitale').guichet&&!b1.some(b=>/Blois/.test(b.nom)), noms.join(' | '));
  const b2=M.besoins(ix,"on m'a volé mon sac : carte bancaire et carte d'identité");
  verifie('BS2 sac volé : carte bancaire (opposition, fiche « vol ») puis carte d\'identité (fiche « vol »), deux lignes', b2.length===2&&b2[0].rec.id==='SP-F2428'&&b2[1].rec.id==='SP-F1759', b2.map(b=>b.nom+' '+(b.rec&&b.rec.id)).join(' | '));
  const seuls=['je veux renouveler mon passeport','carte grise perdue','inscription liste électorale',"je n'arrive plus à payer mon électricité, j'habite à Rezé"].filter(q=>M.besoins(ix,q).length);
  verifie('BS3 un seul besoin : pas de « Vos démarches » (la carte « Votre démarche » reste)', !seuls.length, seuls.join(' | ')||'aucune');
  const page=fs.readFileSync(path.join(__dirname,'..','..','trouver-sa-demarche.html'),'utf8'), code=fs.readFileSync(path.join(__dirname,'moteur.js'),'utf8').match(/function besoins[\s\S]*?\n  \}/)[0];
  const ids=TB.papiers.flatMap(p=>Object.values(p.fiche)), absents=ids.filter(i=>!ix.byId.has(i));
  verifie('BS4 « Vos démarches » dans la page, questions de suite sur le premier besoin ; table lue dans besoins.json (aucun papier dans le code), fiches de la table présentes dans l\'index',
    /<h2 id="h-demarche">Vos démarches<\/h2>/.test(page)&&/Ne répète pas cette liste et ne cite pas ces démarches une par une/.test(page)&&/window\.PRINCIPAL = recsB\[0\]/.test(page)&&!/carte bancaire|passeport|SP-F/i.test(code)&&!absents.length
    &&/besoins\.json/.test(fs.readFileSync(path.join(__dirname,'assembler_page.py'),'utf8')), absents.join(' '));
  // BS5 : carte d'identité, passeport : pré-demande, puis mairie équipée au choix ; ni mairie de la commune ni demande de commune.
  const TI=JSON.parse(fs.readFileSync(path.join(__dirname,'..','..','donnees','assistant','titres_identite.json'),'utf8')); M.chargerTitres(TI);
  const qb="carte d'identité perdue, j'habite à Blois", Cb=M.choisir(ix,qb,{k:20}), E=M.ensuiteTitres(), ou=fs.readFileSync(path.join(__dirname,'ou_aller.js'),'utf8');
  const codes=['moteur.js','ou_aller.js'].map(f=>fs.readFileSync(path.join(__dirname,f),'utf8')).join('')+page;
  verifie('BS5 « carte d\'identité perdue, j\'habite à Blois » : ni mairie de Blois ni « vérifiez qu\'elle est équipée » ni demande de commune ; après le bouton, la ligne « Ensuite… » et ses deux liens (adresses lues dans titres_identite.json) ; aucun lien RDV Service Public',
    Cb.principal&&M.titreIdentite(Cb.principal)&&E.texte==='Ensuite, rendez-vous dans la mairie équipée de votre choix'&&E.rendez_vous.url==='https://rendezvouspasseport.ants.gouv.fr/'&&E.carte.url==='https://passeport.ants.gouv.fr/services/geolocaliser-une-mairie-habilitee'
    &&/if \(g\.identite\) \{ el\.innerHTML = ""; majOu\(\); return; \}/.test(ou)&&!/Vérifiez que votre mairie est équipée|services\(c\.code, \["mairie"\]\)/.test(ou+page)&&(ou.match(/Moteur\.titreIdentite\(tete\)/g)||[]).length===2
    &&/if \(Moteur\.titreIdentite\(r\) \|\| \(ts && Moteur\.titreIdentite\(ts\)\)\) h \+= ligneEnsuite\(\);/.test(page)&&!/rendezvouspasseport|geolocaliser-une-mairie|rdv-service-public|rendezvous\.service-public/i.test(codes)
    &&/Ne parle jamais de la mairie du domicile/.test(page)&&!M.titreIdentite(R.find(r=>r.id==='SP-R61680'))&&!M.titreIdentite(R.find(r=>r.id==='SP-R77429')), Cb.principal&&Cb.principal.id); }
// Plusieurs besoins, version avec assistant : la carte « Vos démarches » est gardée, la réponse ne répète pas la liste.
{ const page=fs.readFileSync(path.join(__dirname,'..','..','trouver-sa-demarche.html'),'utf8'), cons=(page.match(/function consigneBesoins\(B\) \{[\s\S]*?\n\}/)||[''])[0];
  const filtre=(page.match(/const refsB = [\s\S]*?const r = renderText\(texteRep\);/)||[''])[0];
  // le filtre de la page, appliqué à une réponse qui répète la liste malgré la consigne
  const refsB=new Set(['SP-F2428','SP-F1759']), texte="Faites d'abord opposition.\n- Carte bancaire : opposition [[SP-F2428]]\n- Carte d'identité : la refaire [[SP-F1759]]\n- Voir aussi [[SP-F31421]]";
  const garde=texte.split("\n").filter((l)=>!(/^\s*[-•*]\s+/.test(l)&&[...l.matchAll(/\[\[((?:DN|SP)-[A-Za-z0-9]+)\]\]/g)].some((m)=>refsB.has(m[1])))).join("\n");
  verifie('BS6 assistant et plusieurs besoins : carte « Vos démarches » gardée ; consigne : ne pas répéter la liste, deux phrases au plus ; la page retire les lignes de liste qui citent une démarche de la carte',
    /Ne répète pas cette liste/.test(cons)&&/deux phrases au plus, sans liste/.test(cons)&&!/une ligne par besoin/.test(cons)&&/afficherResultats\(citedRecs\.concat\(others\), text, "citee", undefined, \{ besoins: BESOINS_Q \}\)/.test(page)
    &&/refsB\.has\(m\[1\]\)/.test(filtre)&&garde==="Faites d'abord opposition.\n- Voir aussi [[SP-F31421]]", JSON.stringify(garde)); }
// Titres d'identité, règles générales : fiches annexes (timbre, suivi, titre retrouvé) après la démarche sauf si la question
// en parle ; fiche « majeur » avant « mineur » sauf pour un enfant ; « carte identité » seule : la pré-demande.
{ for(const [q,att] of [["carte d'identité perdue",'SP-F1344'],["carte d'identité volée",'SP-F1759'],['passeport perdu','SP-F21246'],['carte identité','SP-R62483'],
    ['passeport perdu de mon fils','SP-F21244'],["timbre fiscal carte d'identité perdue",'SP-F33805']]){
    const t=M.search(ix,q,{k:5}).map(x=>x.r.id), C=M.choisir(ix,q,{k:20});
    verifie(`T1 « ${q} » : ${att} en tête et en « Votre démarche »`, t[0]===att&&C.principal&&C.principal.id===att, t.join(' ')+' | '+(C.principal&&C.principal.id)); }
  const suivi=M.search(ix,"suivre ma demande de carte d'identité",{k:3}).map(x=>x.r.id), retr=M.choisir(ix,"j'ai retrouvé ma carte d'identité",{k:20}).principal;
  verifie('T2 une fiche annexe remonte quand la question en parle (« suivre », « retrouvé »)', /SP-R(49786|1580)/.test(suivi.join(' '))&&retr&&retr.id==='SP-F18704', suivi.join(' ')+' | '+(retr&&retr.id));
  verifie('T3 âge : « carte d\'identité de ma fille de 12 ans » ne rétrograde pas la fiche mineur ; « 25 ans » rétrograde la fiche mineur', !M.ageInadapte(R.find(r=>r.id==='SP-F1342'),"carte d'identité de ma fille de 12 ans")&&M.ageInadapte(R.find(r=>r.id==='SP-F1342'),"carte d'identité, j'ai 25 ans")&&M.ageInadapte(R.find(r=>r.id==='SP-F1341'),"carte d'identité pour mon enfant de 8 ans"));
  const TB=JSON.parse(fs.readFileSync(path.join(__dirname,'..','..','donnees','assistant','besoins.json'),'utf8')); M.chargerBesoins(TB);
  const b=M.besoins(ix,"on m'a volé mon sac : carte bancaire et carte d'identité"), cni=b.find(x=>x.cle==='carte_identite'), page=fs.readFileSync(path.join(__dirname,'..','..','trouver-sa-demarche.html'),'utf8');
  verifie('T4 « Vos démarches », carte d\'identité : bouton « Faire la pré-demande » vers l\'ANTS, lien discret « Lire la fiche » vers la fiche',
    cni&&cni.pre&&cni.pre.id==='SP-R62483'&&/^https:\/\/passeport\.ants\.gouv\.fr\//.test(cni.pre.l)&&cni.rec.id==='SP-F1759'&&!b.find(x=>x.cle==='carte_bancaire').pre
    &&/href="\$\{esc\(lienSp\(b\.pre\)\)\}"[^>]*>Faire la pré-demande/.test(page)&&/class="lien-cx" href="\$\{esc\(u\)\}"[^>]*>Lire la fiche/.test(page), cni&&cni.pre&&cni.pre.l); }
// Questions courantes, règles générales : annexe nommée, cas général avant cas particulier, aucune réponse vide.
{ const P=(q)=>{const t=M.search(ix,q,{k:5}).map(x=>x.r.id),C=M.choisir(ix,q,{k:20});return {t,p:C.principal&&C.principal.id};};
  for(const [q,ok,lib] of [['suivre ma demande de passeport',['SP-R1827'],'la fiche de suivi'],['carte grise',['SP-R48603'],'la carte grise du cas général (véhicule d\'occasion)'],
    ['déclaration de revenus',['SP-R1280'],'la déclaration en ligne des impôts'],['retraite',['SP-R42866','SP-R1388'],'la demande de retraite du régime général'],
    ['chômage',['SP-F1636','SP-R49998'],'l\'inscription à France Travail'],['attestation sécurité sociale',['SP-R49811'],'l\'attestation de droits'],['naissance enfant',['SP-F961'],'la déclaration de naissance']]){
    const x=P(q); verifie(`Q1 « ${q} » : ${lib} en tête et en « Votre démarche »`, ok.includes(x.t[0])&&ok.includes(x.p), x.t.slice(0,3).join(' ')+' | '+x.p); }
  const pe=P('passeport enfant');
  verifie('Q2 « passeport enfant » : la pré-demande (ou SP-F21244) en tête ; « Votre démarche » : une fiche ou pré-demande de passeport pour un mineur', ['SP-F21244','SP-R42946','SP-R62484'].includes(pe.t[0])&&['SP-F21244','SP-F14930','SP-R42946','SP-R62484'].includes(pe.p), pe.t.slice(0,3).join(' ')+' | '+pe.p);
  const part=['carte grise','déclaration de revenus','retraite','chômage'].map(q=>[q,M.choisir(ix,q,{k:20}).principal]).filter(([q,r])=>!r||M.casParticulierTitre(r,q));
  verifie('Q3 cas général avant cas particulier : aucune « Votre démarche » réservée à un public ou à un objet que la question ne nomme pas (véhicule agricole, indépendants, militaires, agents publics…) ; nommé, il revient',
    !part.length&&!M.casParticulierTitre(R.find(r=>r.id==='SP-R56736'),'carte grise véhicule agricole')&&M.casParticulierTitre(R.find(r=>r.id==='SP-R56736'),'carte grise'), part.map(x=>x[0]).join(' | ')||'aucune');
  const page=fs.readFileSync(path.join(__dirname,'..','..','trouver-sa-demarche.html'),'utf8'), ou=fs.readFileSync(path.join(__dirname,'ou_aller.js'),'utf8');
  verifie('Q4 « Aussi pour vous » écarte une fiche mineur (ou majeur) inadaptée ; « Vos démarches » ne demande le code postal que si une ligne a besoin d\'un lieu',
    /&& !Moteur\.ageInadapte\(f, q\);/.test(page)&&/window\.BESOINS_SANS_LIEU = !window\.CARTES_TETE\.length;/.test(page)&&/if \(!L && window\.BESOINS_SANS_LIEU\) return;/.test(ou)&&/\|\| window\.BESOINS_SANS_LIEU\) \{ majOu\(\); return; \}/.test(ou)
    &&M.ageInadapte(R.find(r=>r.id==='SP-F1153'),"carte d'identité perdue")); }
// Suite du classement : organisme ou régime, métier, situation d'exception, démarche locale après la fiche nationale ;
// racines ambiguës ; « procuration » et « décès » seuls.
{ const P=(q)=>{const t=M.search(ix,q,{k:5}).map(x=>x.r.id),C=M.choisir(ix,q,{k:20});return {t,p:C.principal&&C.principal.id};};
  for(const [q,ok,lib] of [['payer impôt',['SP-R2771'],'le service de paiement en ligne'],['arrêt maladie',['SP-F3053'],'les indemnités journalières du cas général'],
    ['congé maternité',['SP-F2265'],'le congé de maternité'],['décès',['SP-F909'],'la déclaration de décès'],['demande de logement social',['SP-R34754'],'la demande en ligne nationale'],
    ['procuration',['SP-F1604','SP-R58939','SP-R12675'],'le vote par procuration']]){
    const x=P(q); verifie(`Q5 « ${q} » : ${lib} en « Votre démarche »`, ok.includes(x.p), x.t.slice(0,3).join(' ')+' | '+x.p); }
  const cr=P('inscription crèche');
  verifie('Q6 « inscription crèche » : pas la fiche vaccination (ni en tête ni en « Votre démarche »)', cr.p!=='SP-F767'&&cr.t[0]!=='SP-F767', cr.t.slice(0,3).join(' ')+' | '+cr.p);
  // Racines : deux mots ne se rapprochent que si l'un est une forme de l'autre (pluriel, féminin, conjugaison) ou en dérive
  // par un suffixe courant ; jamais par un simple début commun.
  const r=(w)=>M.toks(w)[0], diff=[['maternite','maternelle'],['procuration','procureur'],['commune','communication'],['electricite','electronique'],
    ['autorisation','autorite'],['licenciement','licence'],['commencement','commentaire'],['electricite','electrique']],
    memes=[['maternite','maternites'],['autorisation','autorisations'],['licenciement','licencie'],['declaration','declarer'],['inscription','inscrire'],
      ['renouvellement','renouveler'],['etudiant','etudiantes'],['maternel','maternelle'],['verification','verifier'],['aide','aider']];
  const md=diff.filter(([a,b])=>r(a)===r(b)), mm=memes.filter(([a,b])=>r(a)!==r(b));
  verifie('Q7 racines : maternité ≠ maternelle, licenciement ≠ licence… ; déclaration = déclarer, licenciement = licencié…',
    !md.length&&!mm.length, [...md.map(x=>x.join('=')),...mm.map(x=>x.join('≠'))].join(' ')||diff.map(([a,b])=>r(a)+'≠'+r(b)).join(' ')); }
// « étudiant » : public particulier. L'aide au logement générale d'abord ; l'aide étudiante quand la question le dit.
{ const P=(q)=>{const C=M.choisir(ix,q,{k:20});return {t:M.search(ix,q,{k:3}).map(x=>x.r.id),p:C.principal&&C.principal.id};};
  for(const q of ['aide au logement','allocation logement']){ const x=P(q);
    verifie(`Q8 « ${q} » : la demande d'aide au logement générale (SP-R41448 ou SP-R1292) en « Votre démarche », pas l'aide étudiante`,
      ['SP-R41448','SP-R1292'].includes(x.p)&&x.t[0]!=='SP-R1332', x.t.join(' ')+' | '+x.p); }
  const et=P('aide logement étudiant');
  verifie('Q8 « aide logement étudiant » : l\'aide au logement étudiant (SP-R1332) en « Votre démarche »', et.p==='SP-R1332', et.t.join(' ')+' | '+et.p); }
// Régressions relevées par la mesure (questions de référence) : « électricité » n'appelle plus « électrique » ; un cas
// d'exception (incapacité permanente) passe après le cas courant ; « Caf ou MSA » n'est pas un cas particulier ; une fiche
// question-réponse en tête dont le titre porte tous les mots de la question peut être « Votre démarche ».
{ const P=(q)=>{const C=M.choisir(ix,q,{k:20});return {t:M.search(ix,q,{k:3}).map(x=>x.r.id),p:C.principal&&C.principal.id};};
  for(const [q,ok] of [['aide électricité',['SP-F33667','SP-R74067']],['accident de travail indemnisation',['SP-F175']],['kbis',['SP-F21000']],
    ['déclaration trimestrielle aah',['SP-R14412']],['changer taux prélèvement',['SP-F35894']],['allocation de soutien familial',['SP-R1448','SP-R57339']]]){
    const x=P(q); verifie(`Q9 « ${q} » : ${ok.join(' ou ')} en « Votre démarche »`, ok.includes(x.p), x.t.join(' ')+' | '+x.p); } }
// ---------- Tolérance aux fautes (Moteur.corriger, appliquée par la page à la recherche simple) : mêmes réponses qu'avec
// l'orthographe correcte, aucune correction sur un lieu, un mot courant ou une question des tests ci-dessus.
console.log('\n=== Fautes de frappe et d\'orthographe');
{ const tp=Date.now(); M.corriger('xx'); const t1=Date.now()-tp;
  const avec=(q,o={})=>{const c=M.corriger(q),C=M.choisir(ix,c.texte,{...o,k:20});return {c,C,top:M.search(ix,c.texte,{...o,k:5}).map(x=>x.r.id)};};
  const memes=(a,b)=>{const x=avec(a),y=avec(b);return {ok:(x.C.principal&&x.C.principal.id)===(y.C.principal&&y.C.principal.id),x,y};};
  const cas=[['inscripsion liste electoral','inscription liste électorale'],['medaille du travaille','médaille du travail'],['titre de sejour','titre de séjour'],
    ['carte grise perdu','carte grise perdue'],['allocation logement','allocation logement'],['declaration revenu','déclaration revenus'],
    ["je n'arive plus a payer mon electricite rezé","je n'arrive plus à payer mon électricité, j'habite à Rezé"],['subvension asociation sportive','subvention association sportive']];
  for(const [a,b] of cas){const m=memes(a,b);verifie(`F1 « ${a} » : même « Votre démarche » que « ${b} »`,m.ok,`${m.x.c.texte} → ${m.x.C.principal?m.x.C.principal.id:'aucune démarche sûre'} ; ${m.x.top.slice(0,3).join(' ')}`);}
  const el=avec("je n'arive plus a payer mon electricite rezé");
  verifie('F2 facture d\'électricité à Rezé, avec fautes : « Aide au paiement d\'un impayé d\'énergie (ménages) » en « Votre démarche »', el.C.principal&&el.C.principal.id==='DN-50108', el.C.principal&&el.C.principal.id);
  const med=avec('medaille du travaille'); verifie('F3 « medaille du travaille » → médaille d\'honneur du travail', med.C.principal&&/médaille d'honneur du travail/i.test(med.C.principal.t), med.C.principal&&med.C.principal.id);
  const sur=["Je tiens un restaurant à Grenoble","Mon club de foot a besoin d'argent","j'habite à Rezé","autorisation de tir du sanglier","titre de séjour à Grenoble"].filter(q=>M.corriger(q).corrections.length);
  verifie('F4 aucune correction sur un lieu, une terminaison ou un mot courant absent de l\'index', !sur.length, sur.map(q=>q+' → '+M.corriger(q).texte).join(' | ')||'aucune');
  const t0=Date.now(); for(const [a] of cas) M.corriger(a); const t2=(Date.now()-t0)/cas.length;
  verifie(`F5 temps : vocabulaire construit à la première correction (${t1} ms), puis ${t2.toFixed(1)} ms par question`, t1<1500&&t2<50); }
const enTete=M.search(ix,'inscription liste électorale',{k:5}).map(x=>x.r.id);
console.log(`        (classement, hors fautes : « inscription liste électorale » → ${enTete.join(' ')} ; SP-R16396 en ${enTete.indexOf('SP-R16396')+1}e position)`);
console.log(`\n${echecs?echecs+' échec(s)':'Toutes les situations de référence passent'}${attente?', '+attente+' en attente':''}.`);
if(echecs) process.exit(1);
