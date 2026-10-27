import json, re, glob, sys, pickle, time

RE_ID = re.compile(rb'<ID>(LEGIARTI\d+)</ID>')
RE_NUM = re.compile(rb'<NUM>(.*?)</NUM>')
RE_ETAT = re.compile(rb'<ETAT>(.*?)</ETAT>')
RE_DEBUT = re.compile(rb'<DATE_DEBUT>(.*?)</DATE_DEBUT>')
RE_FIN = re.compile(rb'<DATE_FIN>(.*?)</DATE_FIN>')
RE_LIEN = re.compile(rb'<LIEN[^>]*typelien="(CONCORDE|CONCORDANCE)"[^>]*>(.*?)</LIEN>')

with open('/tmp/codes_legi.json', encoding='utf-8') as f:
    codes = json.load(f)
with open('/tmp/matched_codes.json', encoding='utf-8') as f:
    matched = json.load(f)

index = {}  # cid -> { NUM -> [ {id,etat,debut,fin,successeur} ... ] }
t0 = time.time()
total_files = 0
etat_counts = {}
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
        etat = m_etat.group(1).decode('utf-8', 'replace').strip()
        etat_counts[etat] = etat_counts.get(etat, 0) + 1
        successeur = ''
        if etat == 'TRANSFERE':
            m_lien = RE_LIEN.search(content)
            if m_lien:
                successeur = m_lien.group(2).decode('utf-8', 'replace').strip()
        entry = {
            'id': m_id.group(1).decode('utf-8', 'replace').strip(),
            'etat': etat,
            'debut': m_debut.group(1).decode('utf-8', 'replace').strip() if m_debut else '',
            'fin': m_fin.group(1).decode('utf-8', 'replace').strip(),
            'successeur': successeur,
        }
        num_idx.setdefault(num, []).append(entry)
    index[cid] = num_idx
    total_files += len(files)
    print(f"{codes[cid]['titre']}: {len(files)} fichiers -> {len(num_idx)} numeros distincts", file=sys.stderr)

print(f"TOTAL: {total_files} fichiers parses en {time.time()-t0:.1f}s", file=sys.stderr)
print("Repartition ETAT (toutes versions, 42 codes apparies):", file=sys.stderr)
for k, v in sorted(etat_counts.items(), key=lambda x: -x[1]):
    print(f"  {v} {k}", file=sys.stderr)

with open('/tmp/legi_index_v2.pkl', 'wb') as f:
    pickle.dump(index, f)
print("Index v2 sauvegarde dans /tmp/legi_index_v2.pkl", file=sys.stderr)
