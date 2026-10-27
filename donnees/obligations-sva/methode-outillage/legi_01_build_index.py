import json, re, glob, sys, pickle, time

RE_ID = re.compile(rb'<ID>(LEGIARTI\d+)</ID>')
RE_NUM = re.compile(rb'<NUM>(.*?)</NUM>')
RE_ETAT = re.compile(rb'<ETAT>(.*?)</ETAT>')
RE_DEBUT = re.compile(rb'<DATE_DEBUT>(.*?)</DATE_DEBUT>')
RE_FIN = re.compile(rb'<DATE_FIN>(.*?)</DATE_FIN>')

with open('/tmp/codes_legi.json', encoding='utf-8') as f:
    codes = json.load(f)
with open('/tmp/matched_codes.json', encoding='utf-8') as f:
    matched = json.load(f)

TODAY = '2026-10-27'

index = {}  # cid -> { NUM -> {'id','etat','debut','fin'} } (version en cours, fin >= TODAY, la plus tardive)
t0 = time.time()
total_files = 0
for cid in matched:
    d = codes[cid]['dir']
    files = glob.glob(d + '/article/LEGI/ARTI/**/LEGIARTI*.xml', recursive=True)
    num_idx = {}
    for fp in files:
        with open(fp, 'rb') as fh:
            content = fh.read()
        m_id = RE_ID.search(content)
        m_num = RE_NUM.search(content)
        m_etat = RE_ETAT.search(content)
        m_debut = RE_DEBUT.search(content)
        m_fin = RE_FIN.search(content)
        if not (m_id and m_num and m_etat and m_fin):
            continue
        num = m_num.group(1).decode('utf-8', 'replace').strip()
        if not num:
            continue
        fin = m_fin.group(1).decode('utf-8', 'replace').strip()
        debut = m_debut.group(1).decode('utf-8', 'replace').strip() if m_debut else ''
        etat = m_etat.group(1).decode('utf-8', 'replace').strip()
        aid = m_id.group(1).decode('utf-8', 'replace').strip()
        entry = {'id': aid, 'etat': etat, 'debut': debut, 'fin': fin}
        cur = num_idx.get(num)
        # on garde la version dont la plage [debut,fin] couvre AUJOURD'HUI, sinon celle au fin le plus tardif (dernier etat connu)
        if cur is None:
            num_idx[num] = entry
        else:
            covers_today_new = entry['debut'] <= TODAY <= entry['fin']
            covers_today_cur = cur['debut'] <= TODAY <= cur['fin']
            if covers_today_new and not covers_today_cur:
                num_idx[num] = entry
            elif covers_today_new == covers_today_cur:
                if entry['fin'] > cur['fin']:
                    num_idx[num] = entry
    index[cid] = num_idx
    total_files += len(files)
    print(f"{codes[cid]['titre']}: {len(files)} fichiers -> {len(num_idx)} numeros distincts", file=sys.stderr)

print(f"TOTAL: {total_files} fichiers parses en {time.time()-t0:.1f}s", file=sys.stderr)

with open('/tmp/legi_index.pkl', 'wb') as f:
    pickle.dump(index, f)
print("Index sauvegarde dans /tmp/legi_index.pkl", file=sys.stderr)
