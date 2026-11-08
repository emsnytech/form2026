import re, glob, sys, pickle, time

RE_CID = re.compile(rb'<CID>(JORFTEXT\d+)</CID>')
RE_NUM = re.compile(rb'<NUM>(.*?)</NUM>')
RE_NATURE = re.compile(rb'<NATURE>(.*?)</NATURE>')
RE_ETAT = re.compile(rb'<ETAT>(.*?)</ETAT>')
RE_DEBUT = re.compile(rb'<DATE_DEBUT>(.*?)</DATE_DEBUT>')
RE_FIN = re.compile(rb'<DATE_FIN>(.*?)</DATE_FIN>')
RE_DATE_TEXTE = re.compile(rb'<DATE_TEXTE>(.*?)</DATE_TEXTE>')
RE_TITRE = re.compile(rb'<TITREFULL>(.*?)</TITREFULL>', re.S)
RE_LIEN_TAG = re.compile(rb'<LIEN\s+([^>]*?)>([^<]*)</LIEN>')
RE_ATTR = re.compile(rb'(\w+)="([^"]*)"')

def find_abrogeant_lien(content):
    for m in RE_LIEN_TAG.finditer(content):
        attrs = dict(RE_ATTR.findall(m.group(1)))
        if attrs.get(b'typelien') == b'ABROGE' and attrs.get(b'sens') == b'cible':
            return {
                'cidtexte': attrs.get(b'cidtexte', b'').decode('utf-8', 'replace'),
                'datesignatexte': attrs.get(b'datesignatexte', b'').decode('utf-8', 'replace'),
                'naturetexte': attrs.get(b'naturetexte', b'').decode('utf-8', 'replace'),
                'numtexte': attrs.get(b'numtexte', b'').decode('utf-8', 'replace'),
                'texte_lien': m.group(2).decode('utf-8', 'replace').strip(),
            }
    return None

def scan(base, label):
    files = glob.glob(base + '/**/texte/version/*.xml', recursive=True)
    by_numnat = {}
    by_date = {}
    t0 = time.time()
    for fp in files:
        with open(fp, 'rb') as f:
            c = f.read()
        m_cid = RE_CID.search(c)
        m_num = RE_NUM.search(c)
        m_nat = RE_NATURE.search(c)
        m_etat = RE_ETAT.search(c)
        m_debut = RE_DEBUT.search(c)
        m_fin = RE_FIN.search(c)
        m_dt = RE_DATE_TEXTE.search(c)
        m_titre = RE_TITRE.search(c)
        if not (m_cid and m_nat and m_etat and m_fin):
            continue
        nature = m_nat.group(1).decode('utf-8', 'replace').strip()
        num = (m_num.group(1).decode('utf-8', 'replace').strip() if m_num else '')
        dt = (m_dt.group(1).decode('utf-8', 'replace').strip() if m_dt else '')
        entry = {
            'cid': m_cid.group(1).decode(),
            'etat': m_etat.group(1).decode('utf-8', 'replace').strip(),
            'debut': m_debut.group(1).decode('utf-8', 'replace').strip() if m_debut else '',
            'fin': m_fin.group(1).decode('utf-8', 'replace').strip(),
            'date_texte': dt,
            'titre': m_titre.group(1).decode('utf-8', 'replace').strip() if m_titre else '',
            'abrogeant': find_abrogeant_lien(c),
        }
        if num:
            by_numnat.setdefault((nature, num), []).append(entry)
        if dt:
            by_date.setdefault((nature, dt), []).append(entry)
    print(f"{label}: {len(files)} fichiers en {time.time()-t0:.1f}s -> {len(by_numnat)} (nature,num), {len(by_date)} (nature,date)", file=sys.stderr)
    return by_numnat, by_date

base1 = '/Users/philippevrignaud/Documents/cartographie/legi/extracted/legi/global/code_et_TNC_en_vigueur/TNC_en_vigueur'
base2 = '/Users/philippevrignaud/Documents/cartographie/legi/extracted/legi/global/code_et_TNC_non_vigueur/TNC_non_vigueur'
base3 = '/Users/philippevrignaud/Documents/cartographie/legi/extracted/legi/global/code_et_TNC_non_vigueur/code_non_vigueur'

numnat_v, date_v = scan(base1, 'TNC_en_vigueur')
numnat_nv, date_nv = scan(base2, 'TNC_non_vigueur')
numnat_cnv, date_cnv = scan(base3, 'code_non_vigueur')

for k, v in numnat_cnv.items():
    numnat_nv.setdefault(k, []).extend(v)
for k, v in date_cnv.items():
    date_nv.setdefault(k, []).extend(v)

with open('/tmp/tnc_index_v2.pkl', 'wb') as f:
    pickle.dump({
        'numnat_vigueur': numnat_v, 'date_vigueur': date_v,
        'numnat_non_vigueur': numnat_nv, 'date_non_vigueur': date_nv,
    }, f)
print("Index TNC v2 sauvegarde dans /tmp/tnc_index_v2.pkl", file=sys.stderr)
