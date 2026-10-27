# -*- coding: utf-8 -*-
"""Étape 4 — relit les CSV publiés et compare aux chiffres affichés sur la page et dans la note."""
import csv
from pathlib import Path

BASE = Path.home() / "Documents/form2026-site/donnees/obligations-sva"

def load(name):
    with open(BASE / name, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

erreurs = []
def check(label, actual, expected):
    ok = actual == expected
    print(f"{'OK ' if ok else 'ECART'}  {label:60s} CSV={actual!r:>10}  page/note={expected!r}")
    if not ok:
        erreurs.append(label)

sva = load("obligations_sva_2026-10-26.csv")
svr = load("obligations_svr_2026-10-28.csv")
delai = load("delais_sva_derogatoires_2026-10-28.csv")
check("Total SVA", len(sva), 1283)
check("Total SVR", len(svr), 1174)
check("Total délai", len(delai), 349)
check("Total énuméré (2806)", len(sva)+len(svr)+len(delai), 2806)

statut = load("statut_vigueur_2026-10-28.csv")
check("statut_vigueur, total lignes", len(statut), 2806)
from collections import Counter
c = Counter(r['statut'] for r in statut)
check("en_vigueur", c['en_vigueur'], 1766)
check("transfere", c['transfere'], 9)
check("recodifie", c['recodifie'], 251)
check("supprime", c['supprime'], 402)
check("vivantes (en_vigueur+transfere+recodifie)", c['en_vigueur']+c['transfere']+c['recodifie'], 2026)
check("non verifiable (numero_non_localise+inconnu+hors_UE)", c['numero_non_localise']+c['inconnu']+c['hors_UE'], 378)

decrets = load("decrets_articles_supprimes_ou_recodifies_2026-10-28.csv")
check("decrets abroge-family, total", len(decrets), 376)
c2 = Counter(r.get('recod_statut','') for r in decrets)
check("decrets recodifie", c2.get('recodifie',0), 152)
check("decrets supprime", c2.get('supprime',0), 224)

verifies = load("liens_outillage_verifies_2026-10-28.csv")
check("outillées vérifiées, total", len(verifies), 155)
c3 = Counter(r['canal'] for r in verifies)
check("verifies DN", c3.get('DN',0), 104)
check("verifies Cerfa", c3.get('DILA_cerfa',0), 46)
check("verifies teleservice", c3.get('DILA_teleservice',0), 5)
c4 = Counter(r['liste'] for r in verifies)
check("verifies SVA", c4.get('SVA',0), 82)
check("verifies SVR", c4.get('SVR',0), 56)
check("verifies delai", c4.get('DELAI_SVA',0), 17)

non_verifies = load("liens_outillage_candidats_non_verifies_2026-10-28.csv")
check("candidats non verifies, total", len(non_verifies), 349)
check("155+349 = 504 candidats totaux", len(verifies)+len(non_verifies), 504)

vol = load("volumetrie_2026-10-28.csv")
dn_rows = [r for r in vol if r['canal']=='DN']
cumul = sum(int(r['dossiers_cumule']) for r in dn_rows if r['dossiers_cumule'])
annualise = sum(float(r['dossiers_annualise_estime']) for r in dn_rows if r['dossiers_annualise_estime'])
check("DN cumul total", cumul, 115151)
check("DN annualise total (rounded)", round(annualise), 50306)

ct_rows = [r for r in vol if r['canal'] in ('DILA_cerfa','DILA_teleservice')]
non_partage_avec_val = [r for r in ct_rows if r['telechargements_2024'] and r['partage_non_attribuable'] != 'OUI']
somme_tel = sum(int(r['telechargements_2024']) for r in non_partage_avec_val)
check("telechargements 2024 lies non partages", somme_tel, 36431)

echantillon = load("echantillon_web_50_2026-10-28.csv")
check("echantillon web, total lignes", len(echantillon), 50)

top50 = load("top50_regime_juridique_2026-10-28.csv")
check("top50 regime, total lignes", len(top50), 50)
c5 = Counter(r['regime'] for r in top50)
check("regime propre (code)", c5.get('régime propre (code)',0), 16)
check("declaration", c5.get('déclaration',0), 12)
check("autre", c5.get('autre',0), 12)
check("prestation financiere", c5.get('prestation ou demande financière',0), 6)
check("fiscalite", c5.get('fiscalité',0), 1)

contrad = load("contradictions_apparentes_2026-10-28.csv")
check("contradictions apparentes, total", len(contrad), 5)

print()
if erreurs:
    print(f"*** {len(erreurs)} ECART(S) TROUVE(S) : {erreurs}")
else:
    print("*** Tous les chiffres controles sont coherents entre les CSV publies, la page et la note. ***")
