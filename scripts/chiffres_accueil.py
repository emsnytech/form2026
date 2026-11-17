#!/usr/bin/env python3
"""Chiffres du bandeau de l'accueil : un seul fichier, donnees/chiffres-accueil.json, lu par scripts/sync_accueil.py.

Trois jeux, nommés et datés, jamais mélangés :
- « descriptif » : démarches et dossiers du descriptif des démarches publiées (data.gouv.fr), même extraction que les fiches
  ministères (date lue dans leur configuration), par état (publiées, closes, dépubliées). Lit les sorties locales de la
  méthode des fiches (data/demarches_slim.jsonl, hors dépôt) : à relancer après rejouer.sh ;
- « gains » : démarches, dossiers et fourchette de gains de donnees/gains/demarches_gains_v8.csv ; date d'activité lue dans
  donnees/gains/LISEZMOI_gains.md ;
- « charge » : deux constats de la note sur les gains (section 5, « Où se loge la charge », données du hackathon de 2024),
  lus dans le PDF publié de la note (pdftotext).
Aucun chiffre n'est écrit à la main : le script s'arrête si une source manque ou si une phrase de la note a changé.

    python3 scripts/chiffres_accueil.py
"""
import csv, json, re, subprocess, sys, collections as C
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
M = ROOT / "donnees/fiches-ministeres/methode"
SORTIE = ROOT / "donnees/chiffres-accueil.json"

slim = M / "data/demarches_slim.jsonl"
if not slim.exists(): sys.exit(f"{slim.relative_to(ROOT)} introuvable : lancer d'abord donnees/fiches-ministeres/methode/rejouer.sh")
cfg = json.load(open(M / "scripts/config_interieur.json", encoding="utf-8"))
etats, dossiers = C.Counter(), C.Counter()
for l in open(slim, encoding="utf-8"):
    r = json.loads(l); etats[r["state"]] += 1; dossiers[r["state"]] += r["dossiersCount"] or 0
pub = json.load(open(M / "out/interieur.json", encoding="utf-8"))["plateforme"]
assert (sum(etats.values()), sum(dossiers.values())) == (pub["total"], pub["dossiers_total"]), "écart avec les fiches ministères"

G = list(csv.DictReader(open(ROOT / "donnees/gains/demarches_gains_v8.csv", encoding="utf-8")))
s = lambda k: sum(float(x[k] or 0) for x in G)
liz = (ROOT / "donnees/gains/LISEZMOI_gains.md").read_text(encoding="utf-8")
j, m_, a = re.search(r"données d'activité au (\d\d)/(\d\d)/(\d{4})", liz).groups()

pdf = sorted((ROOT / "note").glob("*.pdf"))
assert len(pdf) == 1, "note : un seul PDF attendu"
txt = re.sub(r"\s+", " ", subprocess.run(["pdftotext", str(pdf[0]), "-"], capture_output=True, text=True, check=True).stdout)
m1 = re.search(r"Elles montrent que (\d+) % des dossiers sont déposés le jour même où ils sont commencés", txt)
m2 = re.search(r"passe de (\d+) % pour les démarches demandant une ou deux pièces justificatives à (\d+) % pour celles qui en "
               r"demandent cinq ou plus\. Ces dernières regroupent environ (les trois quarts) des dossiers déposés avec retard", txt)
m3 = re.search(r"Les données du hackathon de (\d{4})", txt)
if not (m1 and m2 and m3): sys.exit("note : phrase de la section 5 introuvable, chiffres de charge non repris")

out = {"_commentaire": "Produit par scripts/chiffres_accueil.py ; lu par scripts/sync_accueil.py. Ne pas modifier à la main.",
       "descriptif": {"date": cfg["date_extraction"], "source": "Descriptif des démarches publiées (data.gouv.fr), extraction lue par les fiches ministères",
                      "demarches": sum(etats.values()), "dossiers": sum(dossiers.values()),
                      "par_etat": {k: {"demarches": etats[k], "dossiers": dossiers[k]} for k in ("publiee", "close", "depubliee")}},
       "gains": {"date": f"{a}-{m_}-{j}", "source": "donnees/gains/demarches_gains_v8.csv, paramètres version 8",
                 "demarches": len(G), "dossiers": round(s("nb_dossiers")), "bas": round(s("gain_total_bas")), "haut": round(s("gain_total_haut"))},
       "charge": {"source": f"note/{pdf[0].name}, section 5 « Où se loge la charge »", "donnees": f"hackathon de la plateforme, {m3.group(1)}",
                  "deposes_le_jour_meme_pct": int(m1.group(1)), "differes_1_2_pieces_pct": int(m2.group(1)),
                  "differes_5_pieces_pct": int(m2.group(2)), "part_des_differes_5_pieces": m2.group(3)}}
t = json.dumps(out, ensure_ascii=False, indent=1) + "\n"
if not SORTIE.exists() or SORTIE.read_text(encoding="utf-8") != t:
    SORTIE.write_text(t, encoding="utf-8"); print(f"écrit : {SORTIE.relative_to(ROOT)}")
else:
    print("déjà à jour")
