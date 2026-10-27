#!/usr/bin/env python3
"""Niveau 1 — Inventaire des canaux (téléservices et Cerfa) à partir du
référentiel DILA (cartographie/dila/dila_formulaires.jsonl, 4 187 entrées).
Lecture seule : n'écrit jamais dans dila/.

Correctifs du 26/10/2026 (consigne niveau 2, retour sur la Phase 0) :
- demarche.numerique.gouv.fr ajouté au canal DN (c'est le domaine public de la
  plateforme, demarches-simplifiees.fr est le domaine technique sous-jacent --
  les deux comptent, pas seulement le second comme dans la première version).
- formulaires.service-public distingué de demarches.service-public (un Cerfa
  PDF téléchargeable n'est pas un téléservice interactif).
- Les 798 téléservices "autre" de la première version sont sous-classés par
  domaine réel (ministère, académie, opérateur) via une heuristique sur l'hôte
  -- explicite, pas une classification manuelle exhaustive des 434 hôtes
  distincts (294 d'entre eux n'apparaissent qu'une fois : forte traîne de
  préfectures, académies, communes).
"""
import csv
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

DILA_DIR = Path.home() / "Documents" / "cartographie" / "dila"
OUT = Path(__file__).resolve().parent.parent / "out"
OUT.mkdir(exist_ok=True)
TODAY = date.today().isoformat()

DOMAINES = [
    ("DN", r"demarches-simplifiees\.fr|demarche\.numerique\.gouv\.fr"),
    ("formulaires.service-public", r"formulaires\.service-public"),
    ("demarches.service-public", r"demarches\.service-public\.gouv\.fr"),
    ("service-public (générique)", r"service-public\.(fr|gouv\.fr)"),
    ("impots", r"impots\.gouv\.fr"),
    ("ANTS", r"ants\.gouv\.fr"),
    ("douane", r"douane\.gouv\.fr"),
    ("net-entreprises", r"net-entreprises\.fr"),
    ("6tzen", r"6tzen"),
    ("ameli", r"ameli\.fr"),
]
CERFA_RE = re.compile(r"cerfa_(\d{5})")

# Heuristique de sous-classement du résidu ("autre") -- pas une liste manuelle
# exhaustive des 434 hôtes, un repérage de motifs explicite et documenté.
MINISTERES_MOTS = [
    "culture", "interieur", "justice", "education", "defense", "social-sante",
    "agriculture", "economie", "travail", "logement", "jeunesse-sports",
    "sante.gouv", "ecologie", "transformation.gouv", "diplomatie",
]
ACADEMIE_MOTS = ["ac-", "academie", "education.gouv", "colibris.education", "enseignementsup-recherche"]
OPERATEURS_HOTES = [
    "msa.fr", "caf.fr", "inpi.fr", "cnil.fr", "insee.fr", "urssaf.fr", "anah.gouv.fr",
    "francetravail.fr", "pole-emploi.fr", "legifrance.gouv.fr", "fondsdegarantie.fr",
    "atout-france.fr", "sacem.fr", "onac-vg.fr", "enedis.fr", "cci.fr", "info-retraite.fr",
    "guso.fr", "asp-public.fr", "data.gouv.fr", "insee.fr",
]


def classer_domaine(url):
    url = url or ""
    for nom, pattern in DOMAINES:
        if re.search(pattern, url, re.I):
            return nom
    host_m = re.search(r"https?://([^/]+)", url)
    host = (host_m.group(1) if host_m else "").lower()
    if any(h in host for h in OPERATEURS_HOTES):
        return "opérateur"
    if any(m in host for m in ACADEMIE_MOTS):
        return "académie"
    if host.endswith(".gouv.fr") and any(m in host for m in MINISTERES_MOTS):
        return "ministère"
    if host.endswith(".gouv.fr"):
        return "autre administration (.gouv.fr non classée)"
    return "autre"


def cerfa_normalise(numero_cerfa, url):
    """Numéro depuis numero_cerfa (ex. '10103*14'), sinon depuis l'URL
    (cerfa_NNNNN.do) -- normalisé à 5 chiffres."""
    if numero_cerfa:
        m = re.match(r"(\d{4,5})", numero_cerfa)
        if m:
            return m.group(1).zfill(5)
    m = CERFA_RE.search(url or "")
    if m:
        return m.group(1)
    return None


def main():
    formulaires = [json.loads(l) for l in (DILA_DIR / "dila_formulaires.jsonl").open(encoding="utf-8")]
    fiches = {json.loads(l)["fiche_id"]: json.loads(l) for l in (DILA_DIR / "dila_fiches.jsonl").open(encoding="utf-8")}
    print(f"[niveau 1] formulaires DILA : {len(formulaires)}")
    print("[niveau 1] types présents :", dict(Counter(r["type"] for r in formulaires)))

    teleservices = [r for r in formulaires if r["type"] == "Téléservice"]
    print(f"[niveau 1] téléservices (type==Téléservice) : {len(teleservices)}")

    cerfa_types = ("Formulaire", "formulaireNG")
    cerfa_rows = [r for r in formulaires if r["type"] in cerfa_types]
    simulateur_types = {"Simulateur", "simulateurNG"}
    n_simulateurs_exclus = sum(1 for r in formulaires if r["type"] in simulateur_types)
    print(f"[niveau 1] confirmation : simulateurs (Simulateur+simulateurNG, {n_simulateurs_exclus} "
          f"enregistrements) jamais inclus dans le canal cerfa -- seuls {cerfa_types} le sont.")

    n_cerfa_champ_vide = sum(1 for r in cerfa_rows if not r.get("numero_cerfa"))
    print(f"[niveau 1] formulaires (Formulaire+formulaireNG) : {len(cerfa_rows)}, "
          f"numero_cerfa vide : {n_cerfa_champ_vide} ({100*n_cerfa_champ_vide/len(cerfa_rows):.1f} %)")
    print("[niveau 1] ATTENTION : la consigne évoquait 61 % de champ vide -- constaté : "
          f"{100*n_cerfa_champ_vide/len(cerfa_rows):.1f} % sur les formulaires, 1,6 % en élargissant "
          "le test à tous les types dont l'URL contient cerfa_NNNNN (1 244 enregistrements, 20 vides). "
          "Écart non expliqué, à vérifier.")

    domaine_counts = Counter(classer_domaine(r.get("lien_web_url")) for r in teleservices)
    print("[niveau 1] téléservices par domaine (après sous-classement du résidu) :")
    for nom, n in domaine_counts.most_common():
        print(f"    {nom} : {n}")

    # --- export téléservices : titre (via fiche), URL, domaine, fiche_id
    out_rows = []
    for r in teleservices:
        f = fiches.get(r["fiche_id"], {})
        out_rows.append({
            "canal_type": "teleservice",
            "fiche_id": r["fiche_id"],
            "titre": f.get("titre", ""),
            "audience": f.get("audience", ""),
            "url": r.get("lien_web_url") or "",
            "domaine": classer_domaine(r.get("lien_web_url")),
            "numero_cerfa": "",
        })

    n_cerfa_url_fallback = 0
    for r in cerfa_rows:
        f = fiches.get(r["fiche_id"], {})
        cerfa = cerfa_normalise(r.get("numero_cerfa"), r.get("lien_web_url"))
        if cerfa and not r.get("numero_cerfa"):
            n_cerfa_url_fallback += 1
        out_rows.append({
            "canal_type": "cerfa",
            "fiche_id": r["fiche_id"],
            "titre": f.get("titre", ""),
            "audience": f.get("audience", ""),
            "url": r.get("lien_web_url") or "",
            "domaine": classer_domaine(r.get("lien_web_url")),
            "numero_cerfa": cerfa or "",
        })
    print(f"[niveau 1] numéro Cerfa récupéré uniquement via l'URL (champ vide) : {n_cerfa_url_fallback}")

    out_path = OUT / f"canaux_dila_{TODAY}.csv"
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)
    print(f"[niveau 1] écrit {out_path.name} ({len(out_rows)} lignes : "
          f"{sum(1 for r in out_rows if r['canal_type']=='teleservice')} téléservices, "
          f"{sum(1 for r in out_rows if r['canal_type']=='cerfa')} formulaires/Cerfa)")


if __name__ == "__main__":
    main()
