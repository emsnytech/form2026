# -*- coding: utf-8 -*-
import json, re, csv, pickle
from collections import Counter

with open('/tmp/codes_legi.json', encoding='utf-8') as f:
    codes = json.load(f)
with open('/tmp/legi_index_v3.pkl', 'rb') as f:
    code_index = pickle.load(f)
with open('/tmp/tnc_index_v2.pkl', 'rb') as f:
    tnc = pickle.load(f)

# acts explicitement cites par l'utilisateur comme exemples de (re)codification,
# + verification croisee possible via leur titre une fois retrouves dans tnc_index
KNOWN_RECOD = {
    ('ORDONNANCE', '2018-1074'): 'Code de la commande publique',
    ('DECRET', '2018-1075'): 'Code de la commande publique',
    ('ORDONNANCE', '2020-1733'): "Code de l'entrée et du séjour des étrangers et du droit d'asile",
    ('DECRET', '2020-1734'): "Code de l'entrée et du séjour des étrangers et du droit d'asile",
    ('ORDONNANCE', '2021-1574'): 'Code général de la fonction publique',
    ('ORDONNANCE', '2022-478'): 'Code pénitentiaire',
    ('ORDONNANCE', '2015-1341'): 'Code des relations entre le public et l\'administration',
    ('DECRET', '2015-1342'): 'Code des relations entre le public et l\'administration',
}

def titre_of(nature, num):
    for d in (tnc['numnat_vigueur'], tnc['numnat_non_vigueur']):
        entries = d.get((nature, num))
        if entries:
            return max(entries, key=lambda e: e['debut']).get('titre', '')
    return ''

RE_CODE_NAME = re.compile(r"(?:partie (?:législative|réglementaire)\s+(?:du|de la|de l[’\']))?\s*(code [a-zà-öø-ÿ'’\- ]+)", re.I)

def classify(abrogeant):
    if not abrogeant:
        return ('supprime', '', 'aucun lien ABROGE trouve dans la derniere version')
    nature = abrogeant.get('naturetexte', '')
    num = abrogeant.get('numtexte', '')
    key = (nature, num)
    titre = titre_of(nature, num) if nature and num else ''
    reason = ''
    code_arrivee = ''
    is_recod = False
    if key in KNOWN_RECOD:
        is_recod = True
        code_arrivee = KNOWN_RECOD[key]
        reason = f"acte connu de (re)codification ({nature} {num})"
    elif titre:
        tl = titre.lower()
        if 'partie législative' in tl and 'code' in tl:
            is_recod = True
            reason = 'titre : partie législative d\'un code'
        elif 'partie réglementaire' in tl and 'code' in tl:
            is_recod = True
            reason = 'titre : partie réglementaire d\'un code'
        elif re.search(r'\bcode\b', tl) and re.search(r'créant|institu|relatif au code|portant code|codifiant', tl):
            is_recod = True
            reason = 'titre : création/codification explicite'
        if is_recod and not code_arrivee:
            m = RE_CODE_NAME.search(titre)
            code_arrivee = m.group(1).strip() if m else ''
    if is_recod:
        return ('recodifie', code_arrivee, reason)
    return ('supprime', '', f"acte abrogeant identifié ({nature} {num}, {titre[:80] if titre else 'titre non trouvé'}), pas de signal de (re)codification")

def last_entry_for_nums(cid, nums):
    idx = code_index.get(cid, {})
    results = []
    for n in nums:
        alt = n.replace('*', '') if '*' in n else (n[0] + '*' + n[1:] if n else n)
        versions = list(idx.get(n, [])) + list(idx.get(alt, []))
        if versions:
            results.append(max(versions, key=lambda x: x['debut']))
    return results

def process(path, col_ref, col_source, label):
    with open(path, newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    changed = False
    stats = Counter()
    detail = []
    for r in rows:
        statut = r.get('legi_statut', '')
        if statut not in ('abroge', 'texte_abroge') and not statut.startswith('mixte'):
            continue
        cid_apparie = None
        for c, info in codes.items():
            if info['titre'] == r.get('legi_code_apparie'):
                cid_apparie = c
                break
        abrogeants = []
        if cid_apparie and r.get('legi_articles_detectes'):
            nums = r['legi_articles_detectes'].split(';')
            entries = last_entry_for_nums(cid_apparie, nums)
            abrogeants = [e.get('abrogeant') for e in entries if e.get('etat') == 'ABROGE']
        elif r.get('legi_ids') and r.get('legi_ids').startswith('JORFTEXT'):
            cid_txt = r['legi_ids']
            found = None
            for d in (tnc['numnat_vigueur'], tnc['numnat_non_vigueur']):
                for entries in d.values():
                    for e in entries:
                        if e['cid'] == cid_txt:
                            found = e
                            break
                    if found:
                        break
                if found:
                    break
            if found:
                abrogeants = [found.get('abrogeant')]
        if not abrogeants:
            r['recod_statut'] = 'supprime'
            r['recod_code_arrivee'] = ''
            r['recod_motif'] = 'acte abrogeant non localisé (texte non codifié hors index, ou article sans lien ABROGE explicite)'
            stats['supprime_non_localise'] += 1
            changed = True
            continue
        classifs = [classify(a) for a in abrogeants]
        if any(c[0] == 'recodifie' for c in classifs):
            cs = [c for c in classifs if c[0] == 'recodifie']
            r['recod_statut'] = 'recodifie'
            r['recod_code_arrivee'] = ';'.join(sorted(set(c[1] for c in cs if c[1])))
            r['recod_motif'] = ';'.join(sorted(set(c[2] for c in cs)))
            stats['recodifie'] += 1
        else:
            r['recod_statut'] = 'supprime'
            r['recod_code_arrivee'] = ''
            r['recod_motif'] = ';'.join(sorted(set(c[2] for c in classifs)))[:300]
            stats['supprime'] += 1
        changed = True
        detail.append({
            'label': label, 'objet_ou_ref': r.get(col_ref, r.get('objet', ''))[:80],
            'legi_code_apparie': r.get('legi_code_apparie', ''),
            'recod_statut': r['recod_statut'], 'recod_code_arrivee': r['recod_code_arrivee'],
            'recod_motif': r['recod_motif'],
        })
    if changed:
        fieldnames = list(rows[0].keys())
        for c in ['recod_statut', 'recod_code_arrivee', 'recod_motif']:
            if c not in fieldnames:
                fieldnames.append(c)
        with open(path, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(rows)
    print(f"=== {label} ===")
    for k, v in stats.most_common():
        print(f"  {v:5d}  {k}")
    return detail

base = '/Users/philippevrignaud/Documents/form2026-site/donnees/obligations-sva'
d1 = process(f'{base}/obligations_sva_2026-10-26_legi_2026-10-27.csv', 'reference', 'texte_source', 'SVA')
d2 = process(f'{base}/methode-svr/obligations_svr_2026-10-27_legi_2026-10-27.csv', 'dispositions', 'texte_reference', 'SVR')
d3 = process(f'{base}/methode-svr/delais_sva_derogatoires_2026-10-27_legi_2026-10-27.csv', 'dispositions', 'texte_reference', 'DELAI_SVA')

with open('/tmp/recod_detail.json', 'w', encoding='utf-8') as f:
    json.dump(d1 + d2 + d3, f, ensure_ascii=False, indent=1)
print("\nDetail -> /tmp/recod_detail.json (", len(d1+d2+d3), "lignes classees )")
