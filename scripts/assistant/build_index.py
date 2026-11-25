"""Construit l'index de la page trouver-sa-demarche.html à partir de FORM 2026 (DN) et des fiches DILA.

Lit des sources hors dépôt (descriptions extraites de l'export du descriptif, slim du mois, fiches DILA) : exception
prévue par la règle du README, décrite dans donnees/assistant/LISEZMOI_assistant.md. Depuis la racine du dépôt :
    python3 scripts/assistant/build_index.py --form . --carto ~/Documents/cartographie --slim <slim du mois> --out donnees/assistant/index.json
Le dernier contrôle vérifie que les références de exemples.json (à côté de --out) existent toujours ; sinon, sortie en erreur."""
import json, glob, re, collections, html, sys, unicodedata
import argparse, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from departements import deduire, affiner_nationale, titre_technique, charger_communes, _dans as dep_dans_texte
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--form', default=os.path.expanduser('~/Documents/form2026-site'), help='clone du dépôt FORM 2026')
ap.add_argument('--carto', default=os.path.expanduser('~/Documents/cartographie'), help='dossier cartographie (dila/, Bdddemarchesfinoctobre/, assistant/)')
ap.add_argument('--slim', default=None, help='fichier slim des démarches (défaut : <carto>/Bdddemarchesfinoctobre/slim_nov.jsonl)')
ap.add_argument('--out', default=None, help='index produit (défaut : <carto>/assistant/index.json)')
ap.add_argument('--date-export', default=None, help="date de l'export du descriptif (AAAA-MM-JJ) ; défaut : lue dans le nom du slim (slim_AAAAMMJJ.jsonl)")
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
# Portées corrigées par l'éditeur (donnees/assistant/portees_corrigees.json) : liste éditoriale, jamais de règle automatique.
# La portée retenue remplace celle qui est déduite ; la portée et le département déclarés restent à côté (po_declaree, dep_declare).
_pc=os.path.join(FORM,'donnees','assistant','portees_corrigees.json')
CORRECTIONS={c['id']:c for c in (json.load(open(_pc,encoding='utf8'))['corrections'] if os.path.exists(_pc) else [])}
corr_appliquees=[]
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
    pj=[]; pre=set(); carte=False
    for t,lib,obl,api in ch:
        tn=types[t]
        if tn=='PieceJustificative' and lib and len(pj)<8 and clean(lib,70) not in pj: pj.append(clean(lib,70))
        if tn in PRE: pre.add(PRE[tn])
        if tn=='Carte': carte=True   # carte à manipuler : peut gêner certains usagers (accessibilité)
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
    corr=CORRECTIONS.get('DN-%d'%num)
    if corr:
        corr_appliquees.append('DN-%d'%num); po_decl,dep_decl=po,dep
        po,dep=corr['portee'],corr.get('departement') or ''
    portee[po]+=1
    recs.append({'k':'dn','id':'DN-%d'%num,'t':clean(titre,220),'d':clean(a[1],300),'o':clean(org,250),'dep':dep,'po':po,'dp':(datepub or '')[:10],
      'n':nd or 0,'cat':cat,'ev':ev.get(num,''),'u':slug,'ch':fr.get('nb_champs') or len(ch),'pj':pj,'pre':sorted(pre),
      'fd':[x.strip() for x in (fr.get('fiches_dila') or '').split(';') if x.strip()],'fe':(a[5] or '')[:10]})
    if carte: recs[-1]['crt']=1
    if corr: recs[-1]['po_declaree']=po_decl; recs[-1]['dep_declare']=dep_decl
    if titre_technique(titre): recs[-1]['tc']=1; techniques.append({'id':'DN-%d'%num,'n':nd or 0,'portee':po,'titre':titre,'code':titre_technique(titre)})
print('DN',len(recs),dict(skipped))
print('démarches de recette écartées :',{k:len(v) for k,v in recettes.items()},'; gardées et signalées (plus de 10 dossiers) :',len(recettes_gardees))
print('portée des démarches en ligne :',dict(portee),'; départements déduits :',len(deduits),dict(formes),'; organisme et titre divergents :',len(ecarts))
print('portées corrigées par l\'éditeur :',len(corr_appliquees),corr_appliquees)
_absentes=sorted(set(CORRECTIONS)-set(corr_appliquees))
if _absentes: print('ATTENTION portées corrigées sans démarche dans l\'export :',_absentes)
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
# Comment faire (« md », voies de modes, et « md_sur », toutes les voies lues dans une balise) : voir modes_dila.py.
# Une fiche F lit ses propres cas ; un service en ligne R prend les voies de la fiche la plus précise qui le cite (celle qui
# cite le moins de services), sinon son type (téléservice : en ligne ; formulaire : formulaire).
import modes_dila
n_md=collections.Counter(); voies_f={}
for r in recs:
    if r['k']=='sp' and r['id'].startswith('SP-F') and xml.get(r['id'][3:]):
        v,sur,_=modes_dila.voies_fiche(xml[r['id'][3:]][0])
        if v: r['md']=v; r['md_sur']=sur; voies_f[r['id']]=r; n_md['F']+=1
citants=collections.defaultdict(list)
for r in voies_f.values():
    for i in r.get('res',[]): citants[i].append(r)
for r in recs:
    if r['k']!='sp' or not r['id'].startswith('SP-R'): continue
    c=sorted((f for f in citants.get(r['id'],[]) if ['en_ligne'] in f['md'] or r['ty'] not in modes_dila.TYPES_EN_LIGNE),
             key=lambda f:(len(f.get('res',[])),int(f['id'][4:])))
    if c: r['md']=c[0]['md']; r['md_sur']=c[0]['md_sur']; n_md['R par fiche']+=1
    elif r['ty'] in modes_dila.TYPES_EN_LIGNE: r['md']=[['en_ligne']]; r['md_sur']=True; n_md['R par type']+=1
    elif r['ty'] in modes_dila.TYPES_FORMULAIRE: r['md']=[['formulaire']]; r['md_sur']=True; n_md['R par type']+=1
print('comment faire (md) :',dict(n_md))
# Accessibilité et vigilance (qualite.json, produit par qualite.py). Observatoire : seulement les rattachements de la table
# éditoriale observatoire_rattachement.json. Services Publics + : par la démarche nommée (même nomenclature que
# l'Observatoire), sinon, pour Démarche Numérique, par l'organisme. Aucune accessibilité de plateforme n'est reportée sur
# une démarche : sans rattachement, l'accessibilité est « non connue ».
QUAL=os.path.join(os.path.dirname(OUT),'qualite.json')
qual=json.load(open(QUAL)) if os.path.exists(QUAL) else None
if qual:
    par_id={r['id']:r for r in recs}; obs={o['id']:o for o in qual['observatoire']}
    table=json.load(open(os.path.join(os.path.dirname(OUT),'observatoire_rattachement.json')))['rattachements']
    n_q=collections.Counter(); spp=qual['spp']
    for t in table:
        r,o=par_id.get(t['id']),obs.get(str(t['observatoire']))
        if not r or not o: n_q['rattachement sans démarche ou sans ligne Observatoire']+=1; print('ATTENTION rattachement Observatoire introuvable :',t); continue
        r['obs']=o['id']; n_q['observatoire (table)']+=1
        if o['acc']: r['acc']=[o['acc'],o['taux'] if o['acc']=='PC' else '']
        # FranceConnect déclaré par l'Observatoire (« FranceConnect » ou « FranceConnect + ») ; « Non », « À venir »… : rien
        if (o.get('fc') or '').startswith('FranceConnect'): r['fc']=o['fc']; n_q['FranceConnect (Observatoire)']+=1
        v=spp['demarche'].get(' '.join(o['nom'].replace('’',"'").split()).casefold())
        if v: r['spp']=[v['n'],v['neg'],v['motifs'],'']; n_q['vigilance par démarche']+=1
    # Rattachements Services Publics + validés (spp_rattachement.json) : démarche nommée → fiche de l'index.
    for t in json.load(open(os.path.join(os.path.dirname(OUT),'spp_rattachement.json')))['rattachements']:
        r,v=par_id.get(t['id']),spp['demarche'].get(' '.join(t['spp'].replace('’',"'").split()).casefold())
        if not r or not v: print('ATTENTION rattachement Services Publics + introuvable :',t); continue
        if 'spp' not in r: r['spp']=[v['n'],v['neg'],v['motifs'],'']; n_q['vigilance par démarche (table SPP)']+=1
    # Fiches service-public dont le service en ligne est un domaine retenu (ANTS par domaine, ANEF), sauf si la démarche a sa
    # propre vigilance : « portée » en 5e élément, pour l'infobulle.
    cib=qual.get('spp_cibles') or {}
    dom=lambda u:re.sub(r'^www\.','',(re.match(r'^https?://([^/?#:]+)',u or '') or [None,''])[1].lower())
    lib={'immatriculation':"l'immatriculation",'permis de conduire':'le permis de conduire',"passeport et carte d'identité":"les passeports et cartes d'identité"}
    par_dom={a['adresse']:(a,f"retours sur {lib.get(a['domaine'],a['domaine'])} (ANTS)") for a in cib.get('ants',[])}
    if cib.get('anef'): par_dom[cib['anef']['adresse']]=(cib['anef'],'retours sur les titres de séjour (ANEF)')
    for r in recs:
        if r['k']!='sp' or 'spp' in r: continue
        a,portee=par_dom.get(dom(r.get('l')),(None,''))
        if a and a['n']>=20 and a['motifs']: r['spp']=[a['n'],a['neg'],a['motifs'],'',portee]; n_q['vigilance par domaine : '+portee]+=1
    # Démarche Numérique : par l'organisme. Préfecture : sans les retours sur les étrangers pour les démarches qui ne les concernent pas.
    pref,etr=cib.get('prefectures_sans_etrangers',{}),re.compile(cib.get('titres_etrangers') or r'(?!x)x',re.I)
    for r in recs:
        if r['k']=='dn' and 'spp' not in r:
            k=' '.join((r.get('o') or '').replace('’',"'").split()).casefold()
            v=spp['structure'].get(k)
            if not (v and v['motifs']): continue
            if k in pref and not etr.search(r['t']):
                w=pref[k]
                if w['n']>=20 and w['motifs']: r['spp']=[w['n'],w['neg'],w['motifs'],v['nom'],'hors retours sur les étrangers']; n_q['vigilance préfecture sans étrangers (DN)']+=1
                else: n_q['préfecture : vigilance retirée sans les étrangers (DN)']+=1
                continue
            r['spp']=[v['n'],v['neg'],v['motifs'],v['nom']]; n_q['vigilance par organisme (DN)']+=1
    print('accessibilité et vigilance :',dict(n_q))
# Nom d'organisme écrit entièrement en capitales (« DIRECTION DEPARTEMENTALE DE L'EMPLOI… ») : forme en casse normale pour
# l'affichage, clé « oa ». Rien n'est inventé : l'orthographe (accents, majuscules des noms propres) et les sigles sont lus
# dans les noms d'organismes et les titres en casse mixte de l'index. Un mot est gardé en capitales s'il y apparaît surtout en
# capitales (DDETSPP, DRIEETS, ANCT…) ou s'il n'a pas de voyelle ; un mot inconnu passe en minuscules, sans accent ajouté.
_MOT=re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿŒœ]+")
_sans=lambda s:unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()
_formes=collections.defaultdict(collections.Counter); _maj=collections.Counter(); _autres=collections.Counter()
for _r in recs:
    for _s in ([_r['o']] if _r['k']=='dn' else [])+[_r['t']]:
        if not _s or _s==_s.upper(): continue
        for _m in _MOT.finditer(_s):
            w=_m.group(0)
            if len(w)>1 and w.isupper(): _maj[_sans(w)]+=1; continue
            _autres[_sans(w)]+=1
            if _m.start()>0 and _s[_m.start()-1] not in '.:—-«(' and not (_m.start()>1 and _s[_m.start()-2] in '.:'): _formes[_sans(w)][w]+=1
_SIGLES={w for w,n in _maj.items() if n>=2 and n>_autres.get(w,0)}
def _forme(w, debut):
    k=_sans(w)
    if len(w)==1: return w if debut else w.lower()
    if k in _SIGLES or not re.search('[AEIOUYÀ-ÖØ-Ý]',w): return w
    f=_formes.get(k)
    if not f: return w if len(w)<=5 else w[0]+w[1:].lower()   # inconnu : court = sigle probable, long = nom propre
    minus=[(x,n) for x,n in f.items() if x[0].islower()]
    if minus and sum(n for _,n in minus)>=0.25*sum(f.values()): return max(minus,key=lambda x:x[1])[0]
    return f.most_common(1)[0][0]
def _commun(w):
    f=_formes.get(_sans(w)); return len(w)>=4 and _sans(w) not in _SIGLES and f and sum(n for x,n in f.items() if x[0].islower())>=0.25*sum(f.values())
def casse_normale(o):
    # seulement un nom tout en capitales qui contient au moins un mot courant (« DIRECTION », « LYCEE ») : pas « CPAM,CGSS,CNAM »
    if not o or o!=o.upper() or not any(_commun(m.group(0)) for m in _MOT.finditer(o)): return ''
    s=_MOT.sub(lambda m:_forme(m.group(0), m.start()==0),o)
    s=s[0].upper()+s[1:]
    return s if s!=o else ''
_n_oa=0
for _r in recs:
    if _r['k']=='dn':
        _oa=casse_normale(_r['o'])
        if _oa: _r['oa']=_oa; _n_oa+=1
print('organismes en capitales mis en casse normale (oa) :',_n_oa,'; sigles lus dans les données :',len(_SIGLES))
# Démarches passées en nationale par portees_corrigees.json : nom de l'unité légale qui les publie, lu dans Sirene
# (organismes_sirene.json, scripts/assistant/organismes_sirene.py), clé « on ». L'organisme déclaré reste dans « o ».
_os=os.path.join(FORM,'donnees','assistant','organismes_sirene.json')
if os.path.exists(_os):
    _osj=json.load(open(_os,encoding='utf8'))
    for _r in recs:
        _s=_osj['demarches'].get(_r['id'])
        if _r['k']=='dn' and _r['po']=='nat' and _s and _s in _osj['organismes'] and _r['id'] in CORRECTIONS:
            _nom=_osj['organismes'][_s]['nom']; _on=casse_normale(_nom) or _nom
            # règle typographique : le premier nom du domaine d'un ministère prend la majuscule (ministère de l'Intérieur)
            _r['on']=re.sub(r"^(Ministère (?:de l'|de la |du |des |de ))(\w)",lambda m:m.group(1)+m.group(2).upper(),_on)
            print('organisme Sirene (on) :',_r['id'],'→',_r['on'])
# « Rien à faire » : phrases validées par l'éditeur (rien_a_faire.json, « valides »), clé « raf ».
RAF=os.path.join(os.path.dirname(OUT),'rien_a_faire.json')
if os.path.exists(RAF):
    par_id={r['id']:r for r in recs}
    for e in json.load(open(RAF))['valides']:
        for i in e['ids']:
            if i in par_id: par_id[i]['raf']=[e['phrase'],e['fiche']]
            else: print('ATTENTION rien_a_faire.json : démarche absente de l\'index :',i)
with open(OUT,'w') as o:
    o.write('[\n'+',\n'.join(json.dumps(r,ensure_ascii=False,separators=(',',':')) for r in recs)+'\n]\n')
import os; print(os.path.getsize(OUT)/1e6,'Mo')
# Métadonnées de l'index, lues par la page (ligne des volumes, « Comment j'ai cherché ») : date de l'export, nombres.
_m=re.search(r'(\d{4})(\d{2})(\d{2})', os.path.basename(SLIM))
date_export=A.date_export or (f"{_m.group(1)}-{_m.group(2)}-{_m.group(3)}" if _m else '')
# Date de l'export DILA (fiches service-public), écrite par maj_dila.py : celle de l'export « particuliers ».
_ed=os.path.join(UP,'dila','export_dila.json')
date_export_dila=json.load(open(_ed)).get('particuliers',{}).get('date','') if os.path.exists(_ed) else ''
_q={'observatoire':qual['sources']['observatoire']['edition'],'spp':qual['sources']['spp']} if qual else {}
# Accessibilité déclarée des plateformes (accessibilite_plateformes.json, relue sur la déclaration publiée) : pour une démarche type
_ap=os.path.join(os.path.dirname(OUT),'accessibilite_plateformes.json')
if os.path.exists(_ap): _q['acc_plateformes']={c:{k:v for k,v in x.items() if k not in ('extrait','extrait_pdf')} for c,x in json.load(open(_ap))['plateformes'].items()}
json.dump({'date_export':date_export,'date_export_dila':date_export_dila,**_q,'demarches_en_ligne':sum(1 for r in recs if r['k']=='dn'),'fiches':sum(1 for r in recs if r['k']=='sp')},
          open(os.path.join(os.path.dirname(OUT),'index_meta.json'),'w'),ensure_ascii=False)
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
