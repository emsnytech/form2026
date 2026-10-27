# -*- coding: utf-8 -*-
import json, re, csv, pickle

with open('/tmp/codes_legi.json', encoding='utf-8') as f:
    codes = json.load(f)
with open('/tmp/legi_index.pkl', 'rb') as f:
    index = pickle.load(f)

TODAY = '2026-10-27'

def norm_title(s):
    s = s or ''
    s = s.replace('’', "'").replace('’', "'")
    s = re.sub(r"\(.*?\)", "", s)
    s = re.sub(r",?\s*CGI\.?\s*$", "", s, flags=re.I)
    s = re.sub(r"[.,;]+$", "", s.strip())
    s = re.sub(r"\s+", " ", s)
    s = s.lower().strip()
    s = s.replace("l'", "l ").replace("d'", "d ")
    return s

code_by_norm = {}
for cid, info in codes.items():
    code_by_norm[norm_title(info['titre'])] = cid

aliases = {
    norm_title('Code forestier'): code_by_norm[norm_title('Code forestier (nouveau)')],
    norm_title("Code des postes et des communications électroniques et autres dispositions en matière de communications"): code_by_norm[norm_title('Code des postes et des communications électroniques')],
    norm_title("Code de la construction et de l'habitation (partie réglementaire), livre Ier, titre II, chapitre V, section I, sous-section IV"): code_by_norm[norm_title("Code de la construction et de l'habitation.")],
}
code_by_norm.update(aliases)

def match_code(t):
    return code_by_norm.get(norm_title(t))

# extraction des numeros d'article depuis un texte de reference
RE_ART = re.compile(
    r'(?:article|art\.?)?\s*([LRD])\.?\s*\*?\s*(\d+(?:[\s-]?\d+)*(?:-\d+)*)',
    re.I
)

def extract_articles(ref):
    ref = ref or ''
    out = []
    for m in re.finditer(r'\b([LRD])\.?\s*(\*)?\s*(\d{1,4}(?:-\d{1,3}){0,4})\b', ref):
        prefix = m.group(1).upper()
        star = m.group(2) or ''
        num = m.group(3)
        out.append(f"{prefix}{star}{num}")
    return out

def lookup(cid, artnum):
    num_idx = index.get(cid, {})
    if artnum in num_idx:
        return num_idx[artnum]
    # tolerance : essaye avec/sans l'etoile (convention "R*" du code de l'urbanisme)
    if '*' in artnum:
        alt = artnum.replace('*', '')
    else:
        alt = artnum[0] + '*' + artnum[1:]
    if alt in num_idx:
        return num_idx[alt]
    return None

def status_for_entry(entry):
    if entry is None:
        return 'non_identifie'
    etat = entry['etat']
    fin = entry['fin']
    debut = entry['debut']
    covers_today = debut <= TODAY <= fin
    if etat == 'VIGUEUR' and covers_today:
        return 'en_vigueur'
    if not covers_today and fin < TODAY:
        return 'abroge'
    if etat == 'VIGUEUR':
        return 'en_vigueur'
    return etat.lower()

def process_file(path, col_ref, col_source, out_suffix, label):
    with open(path, newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    fieldnames = list(rows[0].keys()) + ['legi_code_apparie', 'legi_articles_detectes', 'legi_statut', 'legi_ids']
    stats = {'en_vigueur':0,'abroge':0,'non_identifie':0,'hors_perimetre_codes':0,'autre':0}
    for r in rows:
        source = r[col_source].strip()
        ref = r[col_ref].strip()
        cid = match_code(source) if source.lower().startswith('code') else None
        if cid is None:
            r['legi_code_apparie'] = ''
            r['legi_articles_detectes'] = ''
            r['legi_statut'] = 'hors_perimetre_codes'
            r['legi_ids'] = ''
            stats['hors_perimetre_codes'] += 1
            continue
        arts = extract_articles(ref)
        if not arts:
            r['legi_code_apparie'] = codes[cid]['titre']
            r['legi_articles_detectes'] = ''
            r['legi_statut'] = 'non_identifie'
            r['legi_ids'] = ''
            stats['non_identifie'] += 1
            continue
        statuses = []
        ids = []
        for a in arts:
            e = lookup(cid, a)
            st = status_for_entry(e)
            statuses.append(st)
            ids.append(e['id'] if e else '')
        if all(s == 'en_vigueur' for s in statuses):
            final = 'en_vigueur'
        elif any(s == 'abroge' for s in statuses):
            final = 'abroge'
        elif all(s == 'non_identifie' for s in statuses):
            final = 'non_identifie'
        else:
            final = 'mixte:' + ','.join(sorted(set(statuses)))
        r['legi_code_apparie'] = codes[cid]['titre']
        r['legi_articles_detectes'] = ';'.join(arts)
        r['legi_statut'] = final
        r['legi_ids'] = ';'.join(ids)
        key = final if final in stats else 'autre'
        stats[key] = stats.get(key,0) + 1

    outpath = path.replace('.csv', f'_{out_suffix}.csv')
    with open(outpath, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"=== {label} ({len(rows)} lignes) -> {outpath}")
    for k,v in stats.items():
        print(f"   {k}: {v}")
    return rows

base = '/Users/philippevrignaud/Documents/form2026-site/donnees/obligations-sva'
process_file(f'{base}/obligations_sva_2026-10-26.csv', 'reference', 'texte_source', 'legi_2026-10-27', 'SVA')
process_file(f'{base}/methode-svr/obligations_svr_2026-10-27.csv', 'dispositions', 'texte_reference', 'legi_2026-10-27', 'SVR')
process_file(f'{base}/methode-svr/delais_sva_derogatoires_2026-10-27.csv', 'dispositions', 'texte_reference', 'legi_2026-10-27', 'DELAI_SVA')
