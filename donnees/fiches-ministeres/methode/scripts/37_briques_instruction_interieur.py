"""Fiche Intérieur, étape 2 (d) : volumes et dates open data des démarches liées aux briques d'instruction.
Aucune connexion n'est déduite d'un titre : ce script ne compte que des démarches. Sortie : out/interieur_briques.json"""
import json, re, sys, collections as C
sys.argv = ["x", "scripts/config_interieur.json", "/dev/null"]
exec(open("scripts/32_local_national_interieur.py").read().split("clusters = []")[0])
nd = lambda L: sum(r["dossiersCount"] or 0 for r in L)
def bloc(L):
    return {"demarches": len(L), "dossiers": nd(L), "publiees": sum(r["state"] == "publiee" for r in L),
            "niveaux": dict(C.Counter(r["niv"] for r in L)), "par_annee": dict(sorted(C.Counter((r["datePublication"] or "")[:4] for r in L).items())),
            "principales": [(r["number"], str(d(r["datePublication"])), r["state"], r["dossiersCount"], r["niv"]) for r in sorted(L, key=lambda r: -(r["dossiersCount"] or 0))[:8]]}
T = lambda rx: [r for r in per if re.search(rx, r["title"] or "", re.I)]
out = {"fondations_et_fonds_de_dotation": bloc(T(r"fondation|fonds de dotation|reconnue? d.utilit[ée] publique|\bFRUP\b|\bRUP\b")),
       "associations": bloc(T(r"association(?!.{0,15}(sportive|des personnels))|\bRNA\b|loi 1901|cultuelle")),
       "dotations_detr_dsil": bloc(T(r"\bDETR\b|\bDSIL\b|\bDSID\b|\bDPV\b|dotation d.[ée]quipement|dotation de soutien")),
       "medailles_nationales": bloc([r for r in per if r["fam"] == "Médailles et distinctions" and r["niv"] == "nationale"])}
json.dump(out, open("out/interieur_briques.json", "w"), ensure_ascii=False, indent=1, default=str)
for k, v in out.items(): print("==", k, {x: v[x] for x in ("demarches", "dossiers", "publiees", "niveaux", "par_annee")}); [print("    ", p) for p in v["principales"]]
