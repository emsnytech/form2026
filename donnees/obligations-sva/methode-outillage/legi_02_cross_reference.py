# -*- coding: utf-8 -*-
import json, re, csv, pickle

with open('/tmp/codes_legi.json', encoding='utf-8') as f:
    codes = json.load(f)
with open('/tmp/legi_index_v2.pkl', 'rb') as f:
    index = pickle.load(f)

def norm_title(s):
    s = s or ''
    s = s.replace('’', "'")
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
    tl = t.strip().lower()
    if tl.startswith('annexe') and 'code général des impôts' in tl:
        m = re.search(r'annexe\s+(i{1,3}v?|v)\b', tl)
        target = {'i': 'LEGITEXT000006069568', 'ii': 'LEGITEXT000006069569', 'iii': 'LEGITEXT000006069574', 'iv': 'LEGITEXT000006069576'}
        if m:
            return target.get(m.group(1))
    if tl.startswith('livre des procédures fiscales') or tl.startswith('livre des procedures fiscales'):
        return 'LEGITEXT000006069583'
    return code_by_norm.get(norm_title(t))

def extract_articles(ref):
    ref = ref or ''
    out = []
    for m in re.finditer(r'\b([LRD])\.?\s*(\*)?\s*(\d{1,4}(?:-\d{1,3}){0,4})\b', ref):
        prefix = m.group(1).upper()
        star = m.group(2) or ''
        num = m.group(3)
        out.append(f"{prefix}{star}{num}")
    return out

def lookup_versions(cid, artnum):
    num_idx = index.get(cid, {})
    if artnum in num_idx:
        return num_idx[artnum]
    if '*' in artnum:
        alt = artnum.replace('*', '')
    else:
        alt = artnum[0] + '*' + artnum[1:]
    return num_idx.get(alt)

def status_for_versions(versions):
    """Règle corrigée : en vigueur si au moins une version VIGUEUR/VIGUEUR_DIFF ;
    sinon transféré si la dernière version (max debut) est TRANSFERE ; sinon abrogé."""
    if not versions:
        return ('non_identifie', '', '')
    vig = [v for v in versions if v['etat'] in ('VIGUEUR', 'VIGUEUR_DIFF')]
    if vig:
        v = max(vig, key=lambda x: x['debut'])
        return ('en_vigueur', v['id'], '')
    last = max(versions, key=lambda x: x['debut'])
    if last['etat'] == 'TRANSFERE':
        return ('transfere', last['id'], last.get('successeur', ''))
    return ('abroge', last['id'], '')

def process_file(path, col_ref, col_source, label):
    with open(path, newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    fieldnames = list(rows[0].keys())
    for c in ['legi_code_apparie', 'legi_articles_detectes', 'legi_statut', 'legi_ids', 'legi_transfert_vers']:
        if c not in fieldnames:
            fieldnames.append(c)
    stats = {}
    for r in rows:
        source = r[col_source].strip()
        ref = r[col_ref].strip()
        sl = source.lower()
        eligible = sl.startswith('code') or sl.startswith('annexe') and 'impôts' in sl or sl.startswith('livre des procédures') or sl.startswith('livre des procedures')
        cid = match_code(source) if eligible else None
        if cid is None:
            r['legi_code_apparie'] = ''
            r['legi_articles_detectes'] = ''
            r['legi_statut'] = 'hors_perimetre_codes'
            r['legi_ids'] = ''
            r['legi_transfert_vers'] = ''
            stats['hors_perimetre_codes'] = stats.get('hors_perimetre_codes', 0) + 1
            continue
        arts = extract_articles(ref)
        if not arts:
            r['legi_code_apparie'] = codes[cid]['titre']
            r['legi_articles_detectes'] = ''
            r['legi_statut'] = 'non_identifie'
            r['legi_ids'] = ''
            r['legi_transfert_vers'] = ''
            stats['non_identifie'] = stats.get('non_identifie', 0) + 1
            continue
        statuses, ids, transferts = [], [], []
        for a in arts:
            versions = lookup_versions(cid, a)
            st, aid, succ = status_for_versions(versions)
            statuses.append(st)
            ids.append(aid)
            if succ:
                transferts.append(f"{a} -> {succ}")
        if all(s == 'en_vigueur' for s in statuses):
            final = 'en_vigueur'
        elif any(s == 'transfere' for s in statuses) and not any(s == 'abroge' for s in statuses) and not all(s=='en_vigueur' for s in statuses):
            final = 'transfere' if all(s in ('en_vigueur','transfere') for s in statuses) else 'mixte:' + ','.join(sorted(set(statuses)))
        elif any(s == 'abroge' for s in statuses):
            final = 'abroge' if all(s in ('abroge',) for s in statuses) else 'mixte:' + ','.join(sorted(set(statuses)))
        elif all(s == 'non_identifie' for s in statuses):
            final = 'non_identifie'
        else:
            final = 'mixte:' + ','.join(sorted(set(statuses)))
        r['legi_code_apparie'] = codes[cid]['titre']
        r['legi_articles_detectes'] = ';'.join(arts)
        r['legi_statut'] = final
        r['legi_ids'] = ';'.join(ids)
        r['legi_transfert_vers'] = ';'.join(transferts)
        key = final.split(':')[0]
        stats[key] = stats.get(key, 0) + 1

    outpath = path if path.endswith('_legi_2026-10-27.csv') else path.replace('.csv', '_legi_2026-10-27.csv')
    with open(outpath, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"=== {label} ({len(rows)} lignes) -> {outpath}")
    for k, v in sorted(stats.items(), key=lambda x: -x[1]):
        print(f"   {k}: {v}")
    return rows

base = '/Users/philippevrignaud/Documents/form2026-site/donnees/obligations-sva'
process_file(f'{base}/obligations_sva_2026-10-26.csv', 'reference', 'texte_source', 'SVA')
process_file(f'{base}/methode-svr/obligations_svr_2026-10-27.csv', 'dispositions', 'texte_reference', 'SVR')
process_file(f'{base}/methode-svr/delais_sva_derogatoires_2026-10-27.csv', 'dispositions', 'texte_reference', 'DELAI_SVA')
