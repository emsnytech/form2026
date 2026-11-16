"""Fiche Intérieur, arbitrage n° 27, § 3 : encadré « Côté agents ». Source : tableau de bord public de ProConnect
(https://www.proconnect.gouv.fr/stats), quatre exports du 15 novembre 2026 sur 30 jours glissants, versés dans sources/
(voir sources/SOURCE_proconnect.md). Aucun chiffre écrit à la main.
Contrôles : même total dans les vues par fournisseur d'identité (FI) et par service (FS) ; même nombre de connexions à
Démarche Numérique dans la vue FS globale et dans la vue FI filtrée ; même total Passage2 dans la vue FI globale et dans la
vue FS filtrée sur Passage2 ; Passage2 vers Démarche Numérique identique dans les deux vues filtrées.
Sortie : out/interieur_proconnect.json"""
import csv, json, re, openpyxl, warnings
warnings.filterwarnings("ignore")
SRC = "sources/"
def xl(f):
    rows = list(openpyxl.load_workbook(SRC + f, read_only=True).worksheets[0].iter_rows(values_only=True))[1:]
    return {str(a).strip(): int(b) for a, b in rows if a is not None and b is not None}
def cs(f):
    num = lambda x: int(re.sub(r"[^\d]", "", x))
    return {a.strip(): num(b) for a, b in list(csv.reader(open(SRC + f, encoding="utf-8-sig")))[1:] if a}
FI_DN = xl("connexions_proconnect_par_FI_30j_2026-11-15.xlsx")
FI = xl("connexions_proconnect_par_FI_global_30j_2026-11-15.xlsx")
FS = cs("connexions_proconnect_par_FS_global_30j_2026-11-15.csv")
FS_P2 = xl("connexions_proconnect_par_FS_passage2_30j_2026-11-15.xlsx")
DN, P2, GEN, CER, SVE = "Démarche Numérique", "Passage2", "ProConnect Identité", "Cerbère", "Saisine par voie électronique (SVE)"
assert sum(FI.values()) == sum(FS.values()), "totaux FI et FS différents"
assert FS[DN] == sum(FI_DN.values()), "Démarche Numérique : FS global ≠ FI filtré"
assert FI[P2] == sum(FS_P2.values()), "Passage2 : FI global ≠ FS filtré"
assert FI_DN[P2] == FS_P2[DN], "Passage2 → Démarche Numérique différent selon la vue"
tot_dn = sum(FI_DN.values()); tot_p2 = sum(FS_P2.values())
rang_fi = sorted(FI_DN, key=lambda k: -FI_DN[k])
rang_p2 = sorted(FS_P2, key=lambda k: -FS_P2[k])
pct = lambda a, b: round(100 * a / b, 1)
out = {"source": "https://www.proconnect.gouv.fr/stats", "export": "2026-11-15", "fenetre_jours": 30,
       "controles": {"total_global": sum(FI.values()), "demarche_numerique": tot_dn, "passage2": tot_p2},
       "dn": {"connexions": tot_dn, "fournisseurs": len(FI_DN),
              "passage2": [FI_DN[P2], pct(FI_DN[P2], tot_dn), rang_fi.index(P2) + 1],
              "generique": [FI_DN[GEN], pct(FI_DN[GEN], tot_dn), rang_fi.index(GEN) + 1],
              "cerbere": [FI_DN[CER], pct(FI_DN[CER], tot_dn), rang_fi.index(CER) + 1],
              "passage2_premier_apres_generique": rang_fi[:2] == [GEN, P2]},
       "passage2": {"connexions": tot_p2, "services": len(FS_P2), "rang_dn": rang_p2.index(DN) + 1, "part_dn": pct(FS_P2[DN], tot_p2),
                    "avant_dn": rang_p2[:rang_p2.index(DN)], "mirai": [FS_P2.get("MirAI"), rang_p2.index("MirAI") + 1]},
       "sve_service_proconnect": FS.get(SVE)}   # relevé pour contrôle ; ne figure pas dans la fiche (arbitrage n° 27)
json.dump(out, open("out/interieur_proconnect.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1))
