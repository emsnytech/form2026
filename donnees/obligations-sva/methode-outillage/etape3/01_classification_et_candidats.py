# -*- coding: utf-8 -*-
"""Étape 3 — type_demandeur + rapprochement candidat par canal (DN / DILA Cerfa / DILA téléservice)
sur le périmètre vivant (en vigueur + transféré + recodifié), SVA + SVR + délai SVA.
Méthode : titre (chevauchement de mots) + régime (autorisation/déclaration/dérogation/...)
cohérent + autorité cohérente, référence juridique en indice seulement. Candidat != vérifié.
"""
import csv, json, re
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
SITE = Path.home() / "Documents" / "form2026-site"
DILA_DIR = Path.home() / "Documents" / "cartographie" / "dila"
TODAY = "2026-10-27"

STOP = set("de des du le la les un une et en à au aux pour par sur avec ou son sa ses leur "
           "leurs d l dans ce cette ces qui que dont est sont être avoir d'un d'une au titre".split())

def tokens(s):
    s = (s or "").lower().replace("’", "'")
    s = re.sub(r"[^a-zàâäéèêëïîôöùûüçœ0-9']", " ", s)
    return set(w.strip("'") for w in s.split() if len(w.strip("'")) > 2 and w.strip("'") not in STOP)

REGIME_MOTS = {
    'autorisation': ['autorisation', 'autoriser'],
    'declaration': ['déclaration', 'déclarer'],
    'derogation': ['dérogation', 'déroger'],
    'agrement': ['agrément', 'agréer'],
    'habilitation': ['habilitation', 'habiliter'],
    'homologation': ['homologation', 'homologuer'],
    'renouvellement': ['renouvellement', 'renouveler'],
    'reconnaissance': ['reconnaissance'],
    'enregistrement': ['enregistrement'],
    'inscription': ['inscription'],
    'nomination': ['nomination', 'désignation'],
    'admission': ['admission'],
    'delivrance': ['délivrance', 'délivrer'],
    'accord': ['accord'],
    'attestation': ['attestation'],
    'certification': ['certification', 'certificat'],
}

def regime_of(intitule):
    t = (intitule or '').lower()
    for regime, mots in REGIME_MOTS.items():
        for m in mots:
            if m in t:
                return regime
    return ''

TYPE_DEMANDEUR_RULES = [
    ('particulier', ['personne détenue', 'élève', 'étudiant', 'candidat ', 'personne physique',
                      'salarié', 'travailleur', 'mineur', 'enfant', 'conducteur', 'usager']),
    ('profession_reglementee', ['notaire', 'huissier', 'avocat', 'architecte', 'géomètre', 'médecin',
                                  'pharmacien', 'mandataire judiciaire', 'greffier', 'expert',
                                  'commissaire', 'professeur de danse', 'agence de mannequins',
                                  'enseignant', 'moniteur', 'guide-conférencier']),
    ('organisme', ['association', 'fondation', 'mutuelle', 'institution de prévoyance',
                    "société d'assurance", 'organisme de formation', 'organisme certificateur',
                    'organisme agréé', 'congrégation', 'fédération', 'syndicat', 'société de courses']),
    ('entreprise', ['société', 'entreprise', 'exploitant', 'établissement', 'opérateur',
                     'importateur', 'fabricant', 'constructeur', 'transporteur']),
    ('collectivite', ['commune sollicite', 'département sollicite', 'une collectivité',
                        'collectivité territoriale demande', 'maire sollicite']),
    ('autre_administration', ["service de l'état demande", 'préfet sollicite',
                                 'administration demande']),
]

def type_demandeur_of(intitule, autorite):
    """Classé sur l'intitulé/objet seul : décrit la nature du demandeur, pas de
    l'autorité compétente (qui décide) -- mélanger les deux biaisait tout vers
    « autre_administration » puisque l'autorité est presque toujours un
    ministère/préfet, ce qui ne dit rien du demandeur."""
    t = (intitule or '').lower()
    for label, mots in TYPE_DEMANDEUR_RULES:
        for m in mots:
            if m in t:
                return label
    return 'indetermine'

# -- chargement des demarches DN --
demarches = []
for i in range(4):
    demarches += json.loads((SITE / f"app_demarches_{i}.json").read_text(encoding="utf-8"))
for d in demarches:
    d["_tok"] = tokens(d.get("titre"))
print(f"[chargement] {len(demarches)} démarches DN")

# -- chargement canal DILA --
canal_rows = []
with open(SITE / "donnees" / "obligations-sva" / "methode-outillage" / "canaux_dila_2026-10-27.csv", newline="", encoding="utf-8") as f:
    canal_rows = list(csv.DictReader(f))
cerfa_rows = [r for r in canal_rows if r['canal_type'] == 'cerfa']
tele_rows = [r for r in canal_rows if r['canal_type'] == 'teleservice']
for r in cerfa_rows + tele_rows:
    r['_tok'] = tokens(r.get('titre'))
print(f"[chargement] {len(cerfa_rows)} formulaires Cerfa, {len(tele_rows)} téléservices DILA")

SCORE_MIN = 0.35
INTER_MIN = 3

# faux amis deja identifies (SVA, tour precedent) -- numdispo
FAUX_AMIS_SVA = {"719", "758", "713", "391", "1257", "1219"}

def best_candidats(tok_obl, pool, max_n=3):
    cands = []
    for d in pool:
        inter = tok_obl & d["_tok"]
        if len(inter) < INTER_MIN:
            continue
        score = len(inter) / len(tok_obl)
        if score < SCORE_MIN:
            continue
        cands.append((round(score, 2), d))
    cands.sort(key=lambda x: -x[0])
    return cands[:max_n]

def process(rows, label, id_field, intitule_field, autorite_field, ministere_field, ref_field):
    out = []
    n_dn = n_cerfa = n_tele = n_aucun = 0
    for r in rows:
        numdispo = r.get(id_field, '')
        if label == 'SVA' and numdispo in FAUX_AMIS_SVA:
            continue
        intitule = r.get(intitule_field, '')
        autorite = (r.get(autorite_field, '') or '') + ' ' + (r.get(ministere_field, '') or '')
        tok = tokens(intitule)
        regime = regime_of(intitule)
        tdem = type_demandeur_of(intitule, autorite)

        cand_dn = best_candidats(tok, demarches) if tok else []
        cand_cerfa = best_candidats(tok, cerfa_rows) if tok else []
        cand_tele = best_candidats(tok, tele_rows) if tok else []

        canal = 'aucun'
        if cand_dn:
            canal = 'DN'
            n_dn += 1
        elif cand_cerfa:
            canal = 'DILA_cerfa'
            n_cerfa += 1
        elif cand_tele:
            canal = 'DILA_teleservice'
            n_tele += 1
        else:
            n_aucun += 1

        out.append({
            'liste': label,
            'id': numdispo,
            'intitule_objet': intitule,
            'reference': r.get(ref_field, ''),
            'autorite_ministere': autorite.strip(),
            'regime': regime,
            'type_demandeur': tdem,
            'canal_candidat': canal,
            'dn_candidats': '; '.join(f"{d['demarche']}:{d['titre'][:50]}(score={s})" for s, d in cand_dn),
            'cerfa_candidats': '; '.join(f"{d['numero_cerfa'] or d['fiche_id']}:{d['titre'][:50]}(score={s})" for s, d in cand_cerfa),
            'tele_candidats': '; '.join(f"{d['fiche_id']}:{d['titre'][:50]}(score={s})" for s, d in cand_tele),
            'statut_verification': 'candidat',
        })
    print(f"[{label}] {len(rows)} lignes -> DN:{n_dn} Cerfa:{n_cerfa} Téléservice:{n_tele} Aucun:{n_aucun}")
    return out

with open(HERE / "vivant_sva.json", encoding="utf-8") as f:
    vivant_sva = json.load(f)
with open(HERE / "vivant_svr.json", encoding="utf-8") as f:
    vivant_svr = json.load(f)
with open(HERE / "vivant_delai.json", encoding="utf-8") as f:
    vivant_delai = json.load(f)

out_sva = process(vivant_sva, 'SVA', 'numdispo', 'intitule', 'autorite_competente', 'ministere', 'reference')
out_svr = process(vivant_svr, 'SVR', 'decret', 'objet', 'fondement', 'ministere', 'dispositions')
out_delai = process(vivant_delai, 'DELAI_SVA', 'decret', 'objet', 'fondement', 'ministere', 'dispositions')

all_out = out_sva + out_svr + out_delai
with open(HERE / "candidats_canal_2026-10-27.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(all_out[0].keys()))
    w.writeheader()
    w.writerows(all_out)

print(f"\nTotal: {len(all_out)} lignes -> candidats_canal_2026-10-27.csv")
c = Counter(r['canal_candidat'] for r in all_out)
for k, v in c.most_common():
    print(f"  {v:5d}  {k}")
ctd = Counter(r['type_demandeur'] for r in all_out)
print("\ntype_demandeur:")
for k, v in ctd.most_common():
    print(f"  {v:5d}  {k}")
