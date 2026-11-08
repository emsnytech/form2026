#!/usr/bin/env python3
"""Ce que l'État demande aux collectivités : pièces justificatives et champs des démarches de l'État destinées aux collectivités.
Open data seul, publiable. Périmètre : l'ensemble « pour les collectivités » de la page collectivités (script pour.py), 2 098 démarches.
Chaque libellé de pièce est rangé dans une pièce type par des règles explicites ; une pièce peut relever de plusieurs types.
Aucune donnée de contact n'est lue en sortie.

Usage : python3 etat_demande.py <brut.json> <pour.pkl> <sortie.json>   (pour.pkl : produit par pour.py)
La sortie publiée (donnees/collectivites/etat_demande.json) ne garde que les agrégats et les exemples nommés."""
import collections as C, datetime as dt, json, pickle, re, sys
import ijson
import pandas as pd
P = pd.read_pickle(sys.argv[2]); IDS = set(int(x) for x in P["number"])
EM = re.compile(r"[\w.%+'-]+@[\w-]+(?:\.[\w-]+)*\.[A-Za-z]{2,}")
TYPES = {
 "RIB": r"\bRIB\b|relev[ée] d.identit[ée] bancaire|coordonn[ée]es bancaires|\bIBAN\b|\bRIP\b",
 "Délibération": r"d[ée]lib[ée]ration",
 "Plan de financement ou budget": r"plan de financement|budget pr[ée]visionnel|plan de financement pr[ée]visionnel|budget de l.op[ée]ration",
 "Devis ou estimation des coûts": r"\bdevis\b|estimati(f|on) (des co[ûu]ts|d[ée]taill[ée]|financi)|avant.projet|\bAPS\b|\bAPD\b",
 "Note ou mémoire de présentation": r"note (de pr[ée]sentation|explicative|descriptive|technique)|m[ée]moire (explicatif|descriptif|technique)|descriptif (du projet|de l.op[ée]ration|d[ée]taill[ée])",
 "Plans, photos, localisation": r"\bplans?\b(?! de financement)(?! pr[ée]visionnel)|photos?|photographies|localisation|cadastr",
 "Calendrier ou planning": r"calendrier|planning|[ée]ch[ée]ancier",
 "Autorisation d'urbanisme": r"permis de construire|autorisation d.urbanisme|d[ée]claration pr[ée]alable",
 "Attestation de non-commencement": r"non.commencement|non commencement",
 "Arrêté, décision ou convention": r"\barr[êe]t[ée]\b|convention|d[ée]cision (attributive|d.attribution)|notification",
 "SIRET, Kbis ou avis de situation": r"\bSIRET\b|\bSIREN\b|kbis|avis de situation|\bINSEE\b",
 "Avis d'imposition": r"avis d.imposition|avis d.imp[ôo]t",
 "Attestation fiscale ou sociale": r"r[ée]gularit[ée] fiscale|attestation (fiscale|sociale|URSSAF|de vigilance)|\bURSSAF\b",
 "Statuts": r"\bstatuts\b",
 "Factures ou justificatifs de dépenses": r"factures?|justificatifs? (des|de) d[ée]penses|[ée]tat r[ée]capitulatif des d[ée]penses|certificat de paiement",
 "Formulaire Cerfa ou dossier type joint": r"cerfa|formulaire (de demande|[àa] (compl[ée]ter|remplir|t[ée]l[ée]charger)|type|ci.joint|joint)|dossier (type|de demande) (complet|[àa] (compl[ée]ter|remplir|t[ée]l[ée]charger))|mod[èe]le (de|[àa])",
}
TR = {k: re.compile(v, re.I) for k, v in TYPES.items()}
CHAMPS_STRUCTURES = {"SiretChampDescriptor": "SIRET", "IbanChampDescriptor": "IBAN", "RNAChampDescriptor": "RNA", "AnnuaireEducationChampDescriptor": "Annuaire Éducation",
                     "CommuneChampDescriptor": "Commune", "EpciChampDescriptor": "EPCI", "DepartementChampDescriptor": "Département"}
def marche(L):
    for c in L or []:
        yield c; yield from marche(c.get("champDescriptors"))
D = []
TITRES = {}
DOM_INFO = {}
with open(sys.argv[1], "rb") as f:
    for d in ijson.items(f, "item", use_float=True):
        if d.get("number") not in IDS: continue
        TITRES[d["number"]] = d.get("title") or ""
        if d["number"] == 29928:
            _pj = [c for c in marche((d.get("revision") or {}).get("champDescriptors")) if c.get("__typename") == "PieceJustificativeChampDescriptor"]
            DOM_INFO[29928] = {"n": 29928, "url": d.get("demarcheURL"), "dossiers": d.get("dossiersCount") or 0, "organisme": ((d.get("service") or {}).get("organisme") or ""),
                "emplacements": len(_pj), "sans_nom": sum(bool(re.fullmatch(r"\s*justificatif\s+\d+\s*", c.get("label") or "", re.I)) for c in _pj),
                "avis_anterieur": next((c.get("label") for c in _pj if re.search(r"d[ée]j[àa] [ée]t[ée] [ée]valu[ée]", c.get("label") or "", re.I)), None)}
        _del = [c for c in marche((d.get("revision") or {}).get("champDescriptors")) if c.get("__typename") == "PieceJustificativeChampDescriptor" and re.search(r"d[ée]lib[ée]ration", (c.get("label") or "") + " " + (c.get("description") or "")[:200], re.I)]
        # SIRET : demandé au dépôt par la plateforme pour toute démarche ouverte aux personnes morales. On compte les formulaires
        # qui le redemandent pour le déposant (pièce, saisie libre ou champ), hors SIRET d'un tiers (maître d'ouvrage délégué, prestataire…).
        _rx, _tiers = re.compile(r"\bSIRET\b|\bSIREN\b|kbis|avis de situation", re.I), re.compile(r"d[ée]l[ée]gu|mandataire|prestataire|entreprise|b[ée]n[ée]ficiaire final|partenaire|op[ée]rateur|association|porteur", re.I)
        _red = [c for c in marche((d.get("revision") or {}).get("champDescriptors")) if c.get("__typename") in ("PieceJustificativeChampDescriptor", "TextChampDescriptor", "IntegerNumberChampDescriptor", "TextareaChampDescriptor", "SiretChampDescriptor") and _rx.search(c.get("label") or "") and not _tiers.search(c.get("label") or "")]
        PM, REDEM = d.get("forIndividual") is False, bool(_red)
        DELIB = "obligatoire" if any(c.get("required") for c in _del) else ("facultative" if _del else "non demandée")
        ch = list(marche((d.get("revision") or {}).get("champDescriptors")))
        pj = [c for c in ch if c.get("__typename") == "PieceJustificativeChampDescriptor"]
        types = C.Counter()
        for c in pj:
            l = EM.sub("", (c.get("label") or "") + " " + (c.get("description") or "")[:200])
            for k, rx in TR.items():
                if rx.search(l): types[k] += 1
        # Une même pièce peut figurer dans plusieurs sections conditionnelles (une par catégorie de travaux, par exemple) :
        # on compte les libellés distincts, pas les emplacements.
        distinctes = {re.sub(r"\s+", " ", EM.sub("", c.get("label") or "")).strip().lower() for c in pj}
        D.append({"n": d["number"], "dos": d.get("dossiersCount") or 0, "pub": (d.get("datePublication") or "")[:10], "etat": d.get("state"),
                  "pj_emplacements": len(pj), "pj": len(distinctes), "delib": DELIB, "url": d.get("demarcheURL"), "pm": PM, "siret_redemande": REDEM, "pj_types": sorted(types), "pj_anonymes": sum(bool(re.fullmatch(r"\s*(pi[èe]ce|document|justificatif|fichier|annexe)s?\s*(jointe?s?)?\s*\d*\s*", c.get("label") or "", re.I)) for c in pj),
                  "structures": sorted({CHAMPS_STRUCTURES[c["__typename"]] for c in ch if c.get("__typename") in CHAMPS_STRUCTURES}),
                  "champs": len(ch), "organisme": ((d.get("service") or {}).get("organisme") or "")[:60]})
N, T = len(D), sum(x["dos"] for x in D)
res = {"demarches": N, "dossiers": T, "avec_au_moins_une_pj": sum(x["pj"] > 0 for x in D), "pj_mediane": sorted(x["pj"] for x in D)[N // 2],
       "par_piece": {}, "champs_structures": {}}
for k in TYPES:
    L = [x for x in D if k in x["pj_types"]]
    res["par_piece"][k] = {"demarches": len(L), "pct_demarches": round(100 * len(L) / N, 1), "dossiers": sum(x["dos"] for x in L), "pct_dossiers": round(100 * sum(x["dos"] for x in L) / T, 1)}
for v in sorted(set(CHAMPS_STRUCTURES.values())):
    L = [x for x in D if v in x["structures"]]
    res["champs_structures"][v] = {"demarches": len(L), "pct_demarches": round(100 * len(L) / N, 1)}
rib = [x for x in D if "RIB" in x["pj_types"]]
res["rib_et_champ_iban"] = sum("IBAN" in x["structures"] for x in rib)
sir = [x for x in D if "SIRET, Kbis ou avis de situation" in x["pj_types"]]
res["siret_en_piece_avec_champ_siret"] = sum("SIRET" in x["structures"] for x in sir)
res["champ_siret_absent"] = sum("SIRET" not in x["structures"] for x in D)
res["avis_imposition_demarches"] = sum("Avis d'imposition" in x["pj_types"] for x in D)
casc = [x for x in D if "Délibération" in x["pj_types"]]
res["cascade_deliberation"] = {"demarches": len(casc), "dossiers": sum(x["dos"] for x in casc), "aussi_plan_de_financement": sum("Plan de financement ou budget" in x["pj_types"] for x in casc)}
res["forme_dossier"] = {"pj_anonymes_demarches": sum(x["pj_anonymes"] > 0 for x in D), "cerfa_ou_formulaire_joint_demarches": res["par_piece"]["Formulaire Cerfa ou dossier type joint"]["demarches"]}
res["depuis_oct_2022"] = {"demarches": sum(x["pub"] >= "2022-10-07" for x in D)}
CAT = dict(zip(P["number"].astype(int), P["cat"]))
# La médaille régionale, départementale et communale s'adresse aux agents et élus des collectivités, que la collectivité propose :
# ce n'est ni une aide ni un service administratif, elle forme sa propre catégorie.
for x in D:
    if CAT.get(x["n"], "").startswith("Services") and re.search(r"m[ée]daille", TITRES.get(x["n"], ""), re.I): CAT[x["n"]] = "Distinctions des agents et élus locaux"
res["par_categorie"] = {}
for c in sorted(set(CAT.values())):
    L = [x for x in D if CAT.get(x["n"]) == c]
    if not L: continue
    t_ = sum(x["dos"] for x in L)
    res["par_categorie"][c] = {"demarches": len(L), "dossiers": t_, "pj_mediane": sorted(x["pj"] for x in L)[len(L) // 2], "pj_max": max(x["pj"] for x in L), "pj_max_n": max(L, key=lambda x: x["pj"])["n"],
        "pieces": {k: [sum(k in x["pj_types"] for x in L), round(100 * sum(k in x["pj_types"] for x in L) / len(L), 1), round(100 * sum(x["dos"] for x in L if k in x["pj_types"]) / max(t_, 1), 1)] for k in TYPES},
        "champ_siret_pct": round(100 * sum("SIRET" in x["structures"] for x in L) / len(L), 1), "champ_iban_pct": round(100 * sum("IBAN" in x["structures"] for x in L) / len(L), 1)}
DETR = re.compile(r"\bDETR\b|dotation d.[ée]quipement des territoires", re.I)
res["detr_deliberation"] = C.Counter()
for x in D:
    if CAT.get(x["n"]) != "Dotations et fonds d'investissement local" or not DETR.search(TITRES.get(x["n"], "")): continue
    periode = "depuis le 22/02/2026" if x["pub"] >= "2026-02-22" else "avant le 22/02/2026"
    res["detr_deliberation"][f"{periode} | {x['delib']}"] += 1
    if periode.startswith("avant") and x["etat"] == "publiee": res["detr_deliberation"][f"avant, encore en ligne | {x['delib']}"] += 1
res["detr_deliberation"] = dict(sorted(res["detr_deliberation"].items()))
_pm = [x for x in D if x["pm"] and not CAT.get(x["n"], "").startswith(("Services", "Distinctions"))]
res["siret_redemande"] = {"personnes_morales": len(_pm), "demarches": sum(x["siret_redemande"] for x in _pm), "dossiers": sum(x["dos"] for x in _pm if x["siret_redemande"]), "note": "plafond : un champ intitulé seulement « SIRET » peut viser un tiers"}
# Consultation du Domaine (DGFiP) : le service qui demande ce qu'il détient lui-même. On relève les libellés tels qu'ils sont.
DOMAINE = 29928
res["domaine"] = DOM_INFO.get(DOMAINE)
res["detr_ouverts_qui_exigent"] = [{"n": x["n"], "url": x["url"], "publication": x["pub"], "organisme": x["organisme"]} for x in D
    if CAT.get(x["n"]) == "Dotations et fonds d'investissement local" and DETR.search(TITRES.get(x["n"], "")) and x["pub"] < "2026-02-22" and x["etat"] == "publiee" and x["delib"] == "obligatoire"]
EXEMPLES = {128030, 33107, 96210, 47660}
json.dump({"date_open_data": "2026-10-21", "resume": res, "exemples": [x for x in D if x["n"] in EXEMPLES]}, open(sys.argv[3], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
