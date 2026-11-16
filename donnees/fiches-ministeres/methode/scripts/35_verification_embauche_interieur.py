"""Fiche Intérieur : les 7 démarches de vérification préalable à l'embauche. Champs et pièces (libellés distincts, sans
adresse électronique), comparés entre démarches. Descriptif ouvert du 21 octobre 2026. Sortie : out/interieur_verification_embauche.json
(numéros, comptes et libellés de pièces normalisés ; aucune consigne ni coordonnée)."""
import json, re, os, unicodedata, ijson
NUM = [13583, 29111, 55067, 74335, 104225, 121371, 157165]  # 74335 ajoutée (arbitrage 22, décision 4)
EM = re.compile(r"[\w.%+'-]+@[\w-]+(?:\.[\w-]+)*\.[A-Za-z]{2,}"); TEL = re.compile(r"(?:\+33|0)\s?[1-9](?:[\s.-]?\d{2}){4}")
def na(s): return re.sub(r"\s+", " ", unicodedata.normalize("NFKD", TEL.sub("", EM.sub("", s or ""))).encode("ascii", "ignore").decode().lower()).strip(" :*.-")
def marche(L):
    for c in L or []:
        yield c; yield from marche(c.get("champDescriptors"))
out = {}
with open(os.environ.get("FORM2026_RAW", "data/20261021041002-demarches.json"), "rb") as f:
    for d in ijson.items(f, "item", use_float=True):
        if d["number"] not in NUM: continue
        ch = list(marche((d.get("revision") or {}).get("champDescriptors")))
        pj = sorted({na(c.get("label")) for c in ch if c.get("__typename") == "PieceJustificativeChampDescriptor"})
        out[d["number"]] = {"publication": (d.get("datePublication") or "")[:10], "dossiers": d.get("dossiersCount"), "champs": len(ch),
            "pieces_emplacements": sum(c.get("__typename") == "PieceJustificativeChampDescriptor" for c in ch), "pieces_distinctes": len(pj),
            "pieces_obligatoires": len({na(c.get("label")) for c in ch if c.get("__typename") == "PieceJustificativeChampDescriptor" and c.get("required")}),
            "libelles_pieces": pj, "siret": any(c.get("__typename") == "SiretChampDescriptor" for c in ch),
            "titre_identite": any(c.get("__typename") == "TitreIdentiteChampDescriptor" for c in ch),
            "cadre_juridique": bool(d.get("cadreJuridiqueURL") or d.get("deliberation")), "pour_particuliers": d.get("forIndividual")}
json.dump(out, open("out/interieur_verification_embauche.json", "w"), ensure_ascii=False, indent=1)
for n, x in out.items(): print(n, {k: v for k, v in x.items() if k != "libelles_pieces"}); [print("     -", l[:90]) for l in x["libelles_pieces"]]
