"""Construit l'index de la page trouver-sa-demarche.html à partir de FORM 2026 (DN) et des fiches DILA.

Lit des sources hors dépôt (descriptions extraites de l'export du descriptif, slim du mois, fiches DILA) : exception
prévue par la règle du README, décrite dans donnees/assistant/LISEZMOI_assistant.md. Depuis la racine du dépôt :
    python3 scripts/assistant/build_index.py --form . --carto ~/Documents/cartographie --slim <slim du mois> --out donnees/assistant/index.json
Le dernier contrôle vérifie que les références de exemples.json (à côté de --out) existent toujours ; sinon, sortie en erreur."""
import json, glob, re, collections, html, sys
import argparse, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from departements import deduire, affiner_nationale, titre_technique, charger_communes, _dans as dep_dans_texte
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--form', default=os.path.expanduser('~/Documents/form2026-site'), help='clone du dépôt FORM 2026')
ap.add_argument('--carto', default=os.path.expanduser('~/Documents/cartographie'), help='dossier cartographie (dila/, Bdddemarchesfinoctobre/, assistant/)')
ap.add_argument('--slim', default=None, help='fichier slim des démarches (défaut : <carto>/Bdddemarchesfinoctobre/slim_nov.jsonl)')
ap.add_argument('--out', default=None, help='index produit (défaut : <carto>/assistant/index.json)')
ap.add_argument('--rapport', default=None, help='écrit ici (JSON) le détail des départements déduits, pour relecture')
A=ap.parse_args()
FORM=A.form; UP=A.carto
SLIM=A.slim or UP+'/Bdddemarchesfinoctobre/slim_nov.jsonl'
OUT=A.out or UP+'/assistant/index.json'
# Référentiels embarqués dans explorer.html (manifeste des champs, moments de vie, fiches DILA codifiées)
_ex=open(FORM+'/explorer.html',encoding='utf8').read()
def embedded(name):
    m=re.search(r'<script[^>]*id="%s"[^>]*>(.*?)</script>'%name,_ex,re.S)
    return json.loads(m.group(1))
sys.path.insert(0, FORM+'/scripts')
try:
    import retirer_contacts as _rc   # règle du dépôt FORM : aucune donnée de contact publiée
except ImportError:
    _rc = None
def clean(s, n=None):
    if not s: return ''
    s=html.unescape(re.sub(r'<[^>]+>',' ',s))
    s=re.sub(r'https?://\S+','',s)
    s=re.sub(r'[\w.+-]+@[\w-]+\.[\w.]+','',s)          # pas d'adresses électroniques
    s=re.sub(r'(?:\+33\s?|0)[1-9](?:[\s.-]?\d{2}){4}','',s)  # pas de téléphones
    s=re.sub(r'\s+',' ',s).strip()
    if _rc: s=_rc.masquer_tel(_rc.masquer(s))
    if n and len(s)>n: s=s[:n].rsplit(' ',1)[0]+'…'
    return s
# --- FORM (sept.) : catégorie, champs, PJ, moments de vie
D={}
for f in sorted(glob.glob(FORM+'/app_demarches_*.json')):
    for r in json.load(open(f)): D[r['demarche']]=r
ev={e['demarche']:e['evenement'] for e in embedded('data-evenements')}
man=embedded('data-champs-manifest'); types=man['types']
shards={}
for f in glob.glob(FORM+'/champs_shards/*.json'): shards.update(json.load(open(f)))
PRE={'Siret':'SIRET (API Entreprise)','RNA':'RNA (associations)','Iban':'IBAN','QuotientFamilial':'Quotient familial (CAF)','EtudiantBoursier':'Statut boursier','AnnuaireEducation':'Annuaire Éducation','PreRempli':'Données préremplies','RNF':'RNF (fondations)'}
# --- DN (3 nov.) : titres, organismes, descriptions des démarches publiées
slim={}
for l in open(SLIM):
    a=json.loads(l); slim[a[0]]=a
desc={}
for l in open(UP+'/assistant/descriptions_publiees.jsonl'):
    a=json.loads(l); desc[a[0]]=a
# Portée d'une démarche en ligne (champ « po ») : « nat » (administration centrale ou opérateur national, hors services
# territoriaux), « dep » (département de l'organisme, ou déduit de son nom ou du titre par departements.py), « inc » (locale,
# département inconnu).
# Démarches de recette : titre qui commence par un marqueur entre crochets ou parenthèses, ou suivi d'un tiret ([Qualif],
# [Préprod], [Recette], [Test], [Démo], [Formation], [Copie], [Brouillon], « Recette - »…), ou qui contient le mot isolé
# « préprod ». Jamais « recette », « qualification » ou « formation » hors de ces marqueurs. Une démarche de plus de 10
# dossiers n'est pas écartée : elle est signalée (une vraie démarche peut porter un tel marqueur).
_MARQ=r"(qualif|qualification|pr[ée][- ]?prod|recette|test|d[ée]mo|formation|copie|brouillon)"
RECETTE_DEBUT=re.compile(r"^\s*(?:[\[(]\s*"+_MARQ+r"\s*[\])]|"+_MARQ+r"\s*[-–—]\s)",re.I)
PREPROD=re.compile(r"(?<![\w])pr[ée][- ]?prod(?![\w])",re.I)
norm_marqueur=lambda k: re.sub(r"[ée]","e",k.lower()).replace(" ","-").replace("pre-prod","preprod")
recettes=collections.defaultdict(list); recettes_gardees=[]
recs=[]; skipped=collections.Counter(); portee=collections.Counter(); deduits=[]; formes=collections.Counter(); ecarts=[]
# Communes de donnees/assistant/communes.json (dans le dépôt) : lieu nommé dans le titre d'une démarche d'organisme national.
charger_communes(os.path.join(FORM,'donnees','assistant','communes.json'))
affines=collections.defaultdict(list); techniques=[]; declares_divergents=[]
for num,a in desc.items():
    s=slim.get(num)
    if not s: skipped['sans_titre']+=1; continue
    _,state,datepub,nd,siret,org,torg,dep,titre=s
    fr=D.get(num,{})
    cat=fr.get('categorie') or ('particulier' if a[3] else 'personne_morale')
    if cat=='agent_public': skipped['agent_public']+=1; continue
    if re.search(r'\b(test|essai|brouillon)\b',titre or '',re.I): skipped['test']+=1; continue
    m=RECETTE_DEBUT.match(titre or ''); pp=PREPROD.search(titre or '')
    if m or pp:
        k=norm_marqueur((m.group(1) or m.group(2)) if m else pp.group(0))
        if (nd or 0)>10: recettes_gardees.append({'id':'DN-%d'%num,'marqueur':k,'dossiers':nd,'titre':titre})
        else: skipped['recette']+=1; recettes[k].append({'id':'DN-%d'%num,'dossiers':nd or 0,'titre':titre}); continue
    ch=shards.get(str(num),[])
    pj=[]; pre=set()
    for t,lib,obl,api in ch:
        tn=types[t]
        if tn=='PieceJustificative' and lib and len(pj)<8 and clean(lib,70) not in pj: pj.append(clean(lib,70))
        if tn in PRE: pre.add(PRE[tn])
    slug=(a[2] or '').rsplit('/',1)[-1]
    national = torg in ('administration_centrale','operateur_d_etat') and not re.search(r'pr[ée]fecture|d[ée]partement|r[ée]gion|acad[ée]m|rectorat|\bDD|\bDR|DREAL|DRAAF|\bARS\b|\bCAF\b|CPAM|ville|mairie|commune',org or '',re.I)
    if national:
        po,dep,regle=affiner_nationale(org,titre)
        if regle: affines[regle].append({'id':'DN-%d'%num,'portee':po,'dep':dep or '','organisme':org,'titre':titre})
    elif dep:
        po='dep'
        # Département déclaré, mais le titre en nomme un autre après « en » ou « dans » : listé, jamais modifié (chantier des
        # départements déclarés douteux).
        d2,f2=dep_dans_texte(titre,titre=True)
        if d2 and f2.startswith('département après') and d2!=dep: declares_divergents.append({'id':'DN-%d'%num,'dep_declare':dep,'dep_titre':d2,'organisme':org,'titre':titre})
    else:
        d,forme,source,autre=deduire(org,titre)
        if d:
            po,dep='dep',d; formes[forme+' ('+source+')']+=1
            deduits.append({'id':'DN-%d'%num,'dep':d,'forme':forme,'source':source,'organisme':org,'titre':titre})
            if autre: ecarts.append({'id':'DN-%d'%num,'organisme':org,'titre':titre,'dep_retenu':d,'dep_ecarte':autre,'source':source})
        else: po,dep='inc',''
    portee[po]+=1
    recs.append({'k':'dn','id':'DN-%d'%num,'t':clean(titre,220),'d':clean(a[1],300),'o':clean(org,120),'dep':dep,'po':po,'dp':(datepub or '')[:10],
      'n':nd or 0,'cat':cat,'ev':ev.get(num,''),'u':slug,'ch':fr.get('nb_champs') or len(ch),'pj':pj,'pre':sorted(pre),
      'fd':[x.strip() for x in (fr.get('fiches_dila') or '').split(';') if x.strip()],'fe':(a[5] or '')[:10]})
    if titre_technique(titre): recs[-1]['tc']=1; techniques.append({'id':'DN-%d'%num,'n':nd or 0,'portee':po,'titre':titre,'code':titre_technique(titre)})
print('DN',len(recs),dict(skipped))
print('démarches de recette écartées :',{k:len(v) for k,v in recettes.items()},'; gardées et signalées (plus de 10 dossiers) :',len(recettes_gardees))
print('portée des démarches en ligne :',dict(portee),'; départements déduits :',len(deduits),dict(formes),'; organisme et titre divergents :',len(ecarts))
print('portée nationale affinée :',{k:len(v) for k,v in affines.items()},'; titres techniques :',len(techniques),'; département déclaré différent de celui du titre (« en / dans ») :',len(declares_divergents))
if A.rapport:
    json.dump({'declares_divergents':declares_divergents,'recettes':recettes,'recettes_gardees':recettes_gardees,'affines':affines,'techniques':techniques,'portee':dict(portee),'formes':dict(formes),'exemples':random.Random(20261120).sample(deduits,min(15,len(deduits))),'ecarts':ecarts,'deduits':deduits},
              open(A.rapport,'w'),ensure_ascii=False,indent=1)
# --- DILA
fiches=[json.loads(l) for l in open(UP+'/dila/dila_fiches.jsonl')]
forms={}
for l in open(UP+'/dila/dila_formulaires.jsonl'):
    g=json.loads(l); forms.setdefault(g['fiche_id'],g)
docs=collections.defaultdict(list)
for l in open(UP+'/dila/dila_documents.jsonl'):
    g=json.loads(l); docs[g['fiche_id']].append(clean(g['texte'],140))
liens=collections.defaultdict(list)
for l in open(UP+'/dila/dila_liens_demarches.jsonl'):
    g=json.loads(l)
    if not g['slug'].startswith('https'): liens[g['fiche_id']].append(g['slug'])
dev={x['fiche_id']:x for x in embedded('data-dila')}
SKIP={'Dossier','Recherche guidée','Outil de recherche','outilRechercheNG'}
seen=set(); n0=len(recs)
for f in fiches:
    fid=f['fiche_id']
    if fid in seen or not f['titre'] or f['type'] in SKIP or fid[0] not in 'FR': continue
    seen.add(fid)
    aud=f['audience'] or 'Particuliers'
    base='particuliers' if 'Particuliers' in aud else ('professionnels-entreprises' if 'Professionnels' in aud else 'associations')
    g=forms.get(fid,{}); x=dev.get(fid,{})
    recs.append({'k':'sp','id':'SP-'+fid,'ty':f['type'],'t':clean(f['titre'],220),'d':clean(f['description'],420),'aud':aud,
      'th':f['theme'] or '','ev':x.get('evenement') or '','u':'https://www.service-public.gouv.fr/%s/vosdroits/%s'%(base,fid),
      'l':g.get('lien_web_url') or '','cerfa':g.get('numero_cerfa') or '','docs':list(dict.fromkeys(docs.get(fid,[])))[:10],'dn':liens.get(fid,[])[:5],
      'm':x.get('modalite') or ''})
# Ressources citées par chaque fiche (F…), lues dans les fichiers XML bruts de la DILA : services en ligne, formulaires,
# simulateurs (<ServiceEnLigne ID="R…">), puis fiches liées (<LienInterne LienPublication="F…">). Seules celles présentes
# dans l'index sont gardées, dans leur ordre d'apparition.
ids_sp={r['id'] for r in recs if r['k']=='sp'}
xml={}
for d in ('extracted_part','extracted_pro','extracted_asso'):
    for f in glob.glob(UP+'/dila/raw/'+d+'/F*.xml'): xml.setdefault(os.path.basename(f)[:-4], []).append(f)
n_res=0
for r in recs:
    if r['k']!='sp' or not r['id'].startswith('SP-F'): continue
    res,fl=[],[]
    for f in xml.get(r['id'][3:],[]):
        x=open(f,encoding='utf-8',errors='ignore').read()
        res+=['SP-'+i for i in re.findall(r'<ServiceEnLigne\b[^>]*\bID="(R\d+)"',x)]
        fl+=['SP-'+i for i in re.findall(r'<LienInterne\b[^>]*\bLienPublication="(F\d+)"',x)]
    res=[i for i in dict.fromkeys(res) if i in ids_sp][:6]; fl=[i for i in dict.fromkeys(fl) if i in ids_sp and i!=r['id']][:6]
    if res: r['res']=res
    if fl: r['fl']=fl
    n_res+=bool(res or fl)
print('SP',len(recs)-n0,'; fiches avec ressources ou fiches liées :',n_res)
with open(OUT,'w') as o:
    o.write('[\n'+',\n'.join(json.dumps(r,ensure_ascii=False,separators=(',',':')) for r in recs)+'\n]\n')
import os; print(os.path.getsize(OUT)/1e6,'Mo')
# Contrôle : toutes les références citées par les réponses préparées existent encore dans l'index
ex=os.path.join(os.path.dirname(OUT),'exemples.json')
if os.path.exists(ex):
    ids={r['id'] for r in recs}; manq=[]
    for e in json.load(open(ex)):
        refs=set(re.findall(r'\[\[([A-Z]{2}-[A-Za-z0-9]+)\]\]',e['texte']))|set(e['refs'])
        manq+=[(e['q'],i) for i in refs if i not in ids]
    if manq:
        print('RÉFÉRENCES DISPARUES dans exemples.json :',manq); sys.exit(1)
    print('exemples.json : toutes les références existent')
