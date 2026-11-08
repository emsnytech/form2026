# -*- coding: utf-8 -*-
import re, csv, pickle, json
from collections import Counter

with open('/tmp/tnc_index.pkl', 'rb') as f:
    tnc = pickle.load(f)

MOIS = {
    'janvier':'01','février':'02','fevrier':'02','mars':'03','avril':'04','mai':'05',
    'juin':'06','juillet':'07','août':'08','aout':'08','septembre':'09',
    'octobre':'10','novembre':'11','décembre':'12','decembre':'12',
}

NATURE_MAP = {
    'décret': 'DECRET', 'decret': 'DECRET',
    'arrêté': 'ARRETE', 'arrete': 'ARRETE',
    'loi': 'LOI',
    'ordonnance': 'ORDONNANCE',
    'décision': 'DECISION', 'decision': 'DECISION',
    'délibération': 'DELIBERATION',
}

RE_DATE = re.compile(r'(\d{1,2})\s*(janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre)\s*(\d{4})', re.I)
RE_NUM = re.compile(r'n[°º]\s*([\d]{1,4}-[\d]{2,5}(?:-\d+)?|\d{1,4}/\d{2,5})', re.I)

def parse_source(t):
    t = t.strip()
    tl = t.lower()
    if 'règlement (ue)' in tl or 'règlement européen' in tl or 'directive' in tl and 'union européenne' in tl:
        return {'scope': 'UE'}
    nature = None
    for k, v in NATURE_MAP.items():
        if tl.startswith(k):
            nature = v
            break
    if nature is None:
        return {'scope': 'non_identifiable'}
    m_num = RE_NUM.search(t)
    num = m_num.group(1) if m_num else ''
    m_date = RE_DATE.search(t)
    date_iso = ''
    if m_date:
        j, mois, a = m_date.groups()
        date_iso = f"{a}-{MOIS[mois.lower()]}-{int(j):02d}"
    return {'scope': 'legi', 'nature': nature, 'num': num, 'date': date_iso}

def status_from_entries(entries):
    vig = [e for e in entries if e['etat'] in ('VIGUEUR', 'VIGUEUR_DIFF')]
    if vig:
        v = max(vig, key=lambda x: x['debut'])
        return ('en_vigueur', v)
    last = max(entries, key=lambda x: x['debut'])
    if last['etat'] == 'TRANSFERE':
        return ('transfere', last)
    return ('abroge', last)

def lookup(parsed):
    if parsed['scope'] != 'legi':
        return None
    nature, num, date = parsed['nature'], parsed['num'], parsed['date']
    if num:
        entries = tnc['numnat_vigueur'].get((nature, num))
        if entries:
            return ('trouve_vigueur', status_from_entries(entries))
        entries_nv = tnc['numnat_non_vigueur'].get((nature, num))
        if entries_nv:
            return ('trouve_non_vigueur', status_from_entries(entries_nv))
    if date:
        entries = tnc['date_vigueur'].get((nature, date))
        if entries:
            return ('trouve_vigueur', status_from_entries(entries))
        entries_nv = tnc['date_non_vigueur'].get((nature, date))
        if entries_nv:
            return ('trouve_non_vigueur', status_from_entries(entries_nv))
    return ('non_trouve', None)

base = '/Users/philippevrignaud/Documents/form2026-site/donnees/obligations-sva'
files = [
    (f'{base}/obligations_sva_2026-10-26_legi_2026-10-27.csv', 'texte_source'),
    (f'{base}/methode-svr/obligations_svr_2026-10-27_legi_2026-10-27.csv', 'texte_reference'),
    (f'{base}/methode-svr/delais_sva_derogatoires_2026-10-27_legi_2026-10-27.csv', 'texte_reference'),
]

summary = Counter()
detail_rows = []
for path, col in files:
    with open(path, newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    changed = False
    for r in rows:
        if r.get('legi_statut') != 'hors_perimetre_codes':
            continue
        t = r[col].strip()
        parsed = parse_source(t)
        if parsed['scope'] == 'UE':
            r['legi_statut'] = 'hors_perimetre_UE'
            summary['UE'] += 1
            changed = True
            continue
        if parsed['scope'] == 'non_identifiable':
            summary['non_identifiable_forme'] += 1
            continue
        res = lookup(parsed)
        kind, data = res
        if kind == 'non_trouve':
            summary['legi_non_trouve'] += 1
            detail_rows.append({'source': t, 'nature': parsed['nature'], 'num': parsed['num'], 'date': parsed['date'], 'resultat': 'non_trouve'})
            continue
        statut, entry = data
        r['legi_statut'] = f"texte_{statut}"
        r['legi_ids'] = entry['cid']
        changed = True
        summary[f"{kind}:{statut}"] += 1
        detail_rows.append({'source': t, 'nature': parsed['nature'], 'num': parsed['num'], 'date': parsed['date'],
                             'resultat': f"{kind}:{statut}", 'cid': entry['cid'], 'titre_legi': entry.get('titre','')[:150]})
    if changed:
        fieldnames = list(rows[0].keys())
        with open(path, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(rows)

print("=== Resume (lignes ex-hors_perimetre_codes) ===")
for k, v in summary.most_common():
    print(f"  {v}  {k}")

with open('/tmp/tnc_detail.json', 'w', encoding='utf-8') as f:
    json.dump(detail_rows, f, ensure_ascii=False, indent=1)
print("Detail complet -> /tmp/tnc_detail.json (", len(detail_rows), "entrees )")
