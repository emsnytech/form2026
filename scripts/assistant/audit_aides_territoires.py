#!/usr/bin/env python3
"""Audit d'Aides-territoires comme répertoire de démarches de dépôt (temps 1 : rapport seulement, rien n'est ajouté à l'index).

Source : API Aides-territoires (ANCT), https://aides-territoires.beta.gouv.fr/data/, données sous Licence Ouverte v2.0
(Etalab). L'API demande un compte : sa clé API (« Mes paramètres → Ma clé API ») s'échange contre un jeton « Bearer »
valable 24 heures (POST /api/connexion/, en-tête X-AUTH-TOKEN). Le script lit la clé, ou directement un jeton Bearer,
dans la variable d'environnement AIDES_TERRITOIRES_TOKEN. Aucun secret n'est écrit dans le dépôt ni affiché.

    AIDES_TERRITOIRES_TOKEN=… python3 scripts/assistant/audit_aides_territoires.py [--carto ~/Documents/cartographie]
    python3 scripts/assistant/audit_aides_territoires.py --depuis-fichier <aides.json>   # sans API, depuis un relevé déjà fait

Produit donnees/assistant/rapport_aides_territoires.md. --brut <fichier> garde le relevé complet hors du dépôt, pour le
relire sans rappeler l'API. --carto permet de dire pourquoi une démarche Démarche Numérique citée n'est pas dans l'index
(publiée mais écartée, ou absente du descriptif publié). Le champ « contact » des aides n'est jamais lu ; tous les textes
repris passent par masquer() et masquer_tel() de scripts/retirer_contacts.py.
"""
import argparse, collections, datetime, json, os, random, re, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "scripts"))
from retirer_contacts import masquer, masquer_tel  # noqa: E402

API = "https://aides-territoires.beta.gouv.fr"
AGENT = "FORM2026-audit (script de reutilisation de donnees ouvertes)"
DN = re.compile(r"(?:demarche\.numerique\.gouv\.fr|demarches-simplifiees\.fr)/commencer/([^/?#\s]+)", re.I)
AGENCES_EAU = ("eau-loire-bretagne.fr", "eau-seine-normandie.fr", "eaurmc.fr", "eau-adour-garonne.fr", "eau-artois-picardie.fr", "eau-rhin-meuse.fr")
REGIONS = ("auvergnerhonealpes.fr", "bourgognefranchecomte.fr", "bretagne.bzh", "centre-valdeloire.fr", "regioncentre-valdeloire.fr",
           "grandest.fr", "hautsdefrance.fr", "iledefrance.fr", "normandie.fr", "nouvelle-aquitaine.fr", "laregion.fr",
           "paysdelaloire.fr", "maregionsud.fr", "isula.corsica", "regionguadeloupe.fr", "regionreunion.com", "ctguyane.fr",
           "collectivitedemartinique.mq")
# Codes INSEE des régions, pour découper le relevé sous le plafond de l'API.
REGIONS_INSEE = ["01", "02", "03", "04", "06", "11", "24", "27", "28", "32", "44", "52", "53", "75", "76", "84", "93", "94"]
PUBLICS = {"Commune": "collectivités", "Intercommunalité / Pays": "collectivités", "Département": "collectivités", "Région": "collectivités",
           "Collectivité d’outre-mer à statut particulier": "collectivités", "Etablissement public dont services de l'Etat": "établissements publics",
           "Entreprise publique locale (Sem, Spl, SemOp)": "entreprises publiques locales", "Association": "associations",
           "Entreprise privée": "entreprises", "Particulier": "particuliers", "Agriculteur": "entreprises (agriculteurs)",
           "commune": "collectivités", "epci": "collectivités", "department": "collectivités", "region": "collectivités",
           "special": "collectivités", "public-org": "établissements publics", "public-cies": "entreprises publiques",
           "association": "associations", "private-sector": "entreprises", "farmer": "entreprises (agriculteurs)",
           "private-person": "particuliers", "researcher": "recherche"}


def propre(s, n=None):
    s = masquer_tel(masquer(re.sub(r"\s+", " ", str(s or "")).strip()))
    return s if not n or len(s) <= n else s[:n].rsplit(" ", 1)[0] + "…"


def requete(url, jeton=None, donnees=None, entetes=None):
    h = {"User-Agent": AGENT, "Accept": "application/ld+json"}
    if jeton: h["Authorization"] = "Bearer " + jeton
    h.update(entetes or {})
    req = urllib.request.Request(url, data=donnees, headers=h, method="POST" if donnees is not None else "GET")
    for essai in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503, 504) and essai < 3: time.sleep(5 * (essai + 1)); continue
            raise


def annonce_du_site():
    """Nombre d'« aides publiées et toujours ouvertes aux candidatures » des statistiques publiques du site, ou None."""
    try:
        req = urllib.request.Request(API + "/stats/", headers={"User-Agent": AGENT})
        t = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "ignore")
    except Exception:
        return None
    t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))
    m = re.search(r"toujours ouvertes aux candidatures\s*([\d\s\u00a0\u202f]+)", t)
    return int(re.sub(r"\D", "", m.group(1))) if m and re.sub(r"\D", "", m.group(1)) else None


def jeton_bearer():
    v = os.environ.get("AIDES_TERRITOIRES_TOKEN", "").strip()
    if not v:
        sys.exit("AIDES_TERRITOIRES_TOKEN absent. L'API Aides-territoires demande un compte : créer un compte sur "
                 "aides-territoires.beta.gouv.fr, copier la clé dans « Mes paramètres → Ma clé API », puis relancer avec "
                 "AIDES_TERRITOIRES_TOKEN=<clé> (ou un jeton Bearer déjà obtenu). Rien n'a été écrit.")
    if v.startswith("eyJ"):  # déjà un jeton Bearer (JWT)
        return v
    try:
        r = requete(API + "/api/connexion/", donnees=b"{}", entetes={"X-AUTH-TOKEN": v, "Content-Type": "application/json", "Accept": "application/json"})
    except urllib.error.HTTPError as e:
        sys.exit(f"Échange de la clé contre un jeton refusé (HTTP {e.code}) : vérifier la clé. Rien n'a été écrit.")
    if not r.get("token"):
        sys.exit("Réponse de connexion sans jeton. Rien n'a été écrit.")
    return r["token"]


def pages(jeton, url):
    """Une liste de l'API, page par page. Deux formats rencontrés : celui de la documentation (hydra:member) et celui que
    l'API renvoie en 1.8.4 (count, next, results)."""
    out = []
    while url:
        r = requete(url, jeton, entetes={"Accept": "application/json"})
        out += r.get("results") or r.get("hydra:member") or r.get("member") or []
        suiv = r.get("next") or (r.get("hydra:view") or r.get("view") or {}).get("hydra:next")
        url = urllib.parse.urljoin(API, suiv) if suiv else None
        time.sleep(0.2)
    return out


def releve(jeton):
    """Toutes les aides publiées et ouvertes (/api/aids/). L'API plafonne une liste à 3 000 aides (30 pages de 100) :
    le relevé est complété par une liste par public visé et une liste par région du périmètre, chacune sous le plafond,
    réunies par identifiant."""
    par_id = {}
    base = pages(jeton, API + "/api/aids/?itemsPerPage=100&page=1")
    for a in base: par_id[a.get("id") or a.get("@id")] = a
    publics = pages(jeton, API + "/api/aids/audiences/?itemsPerPage=100")
    for p in publics:
        s = p.get("slug") or p.get("id")
        for a in pages(jeton, API + "/api/aids/?itemsPerPage=100&page=1&organization_type_slugs[]=" + urllib.parse.quote(str(s))):
            par_id.setdefault(a.get("id") or a.get("@id"), a)
        print(f"\r{len(par_id)} aides distinctes relevées", end="", file=sys.stderr)
    apres_publics = len(par_id)
    for code in REGIONS_INSEE:
        for a in pages(jeton, API + "/api/aids/?itemsPerPage=100&page=1&perimeter_codes[]=" + code):
            par_id.setdefault(a.get("id") or a.get("@id"), a)
        print(f"\r{len(par_id)} aides distinctes relevées", end="", file=sys.stderr)
    print(file=sys.stderr)
    releve.base, releve.publics, releve.apres_publics = len(base), [p.get("name") for p in publics], apres_publics
    return list(par_id.values())


def domaine(u):
    try:
        h = urllib.parse.urlsplit(u.strip()).hostname or ""
    except ValueError:
        return ""
    return h.lower().removeprefix("www.")


def famille(d):
    if not d: return "sans lien"
    if d.endswith(("demarche.numerique.gouv.fr", "demarches-simplifiees.fr")): return "Démarche Numérique"
    if d.endswith("ademe.fr"): return "ADEME"
    if d.endswith(AGENCES_EAU): return "agences de l'eau"
    if d.endswith("bpifrance.fr"): return "Bpifrance"
    if d.endswith(REGIONS) or re.search(r"(^|\.)region", d): return "Régions"
    return "autres"


def normalise(u):
    """Adresse de dépôt comparable : sans schéma, hôte en minuscules, sans « / » final ni paramètres de suivi."""
    p = urllib.parse.urlsplit(u.strip())
    q = "&".join(x for x in p.query.split("&") if x and not x.lower().startswith(("utm_", "mtm_", "xtor")))
    return (p.hostname or "").lower().removeprefix("www.") + p.path.rstrip("/") + ("?" + q if q else "")


def nom(x):
    if isinstance(x, dict):
        return x.get("name") or (x.get("backer") or {}).get("name") or ""
    return str(x or "")


# Noms de champs : réponse réelle de l'API 1.8.4, puis ceux de sa documentation.
def champ(a, *noms):
    for n in noms:
        if a.get(n) not in (None, "", []): return a[n]
    return None


financeurs = lambda a: [nom(f) for f in (champ(a, "financers", "aid_financers") or []) if nom(f)]
publics_de = lambda a: [nom(p) for p in (champ(a, "targeted_audiences", "aid_audiences") or []) if nom(p)]
date_limite = lambda a: str(champ(a, "submission_deadline", "date_submission_deadline") or "")[:10]


def echelle(a):
    """Échelle du périmètre, d'après son nom et ses codes (champs perimeter_code, region_code de l'API 1.8.4)."""
    p = a.get("perimeter") or {}
    n = (nom(p) or "").strip()
    sc = a.get("perimeter_scale") or (p.get("scale") if isinstance(p, dict) else None) or ""
    code, reg = str(a.get("perimeter_code") or ""), str(a.get("region_code") or "")
    if sc: return str(sc)
    if re.fullmatch(r"(?i)europe|union europ[ée]enne", n): return "européen"
    if re.fullmatch(r"(?i)france( m[ée]tropolitaine)?|national", n): return "national"
    if code and reg and code == reg: return "régional"
    if re.fullmatch(r"\d{2}|2A|2B|97\d", code): return "départemental"
    if re.fullmatch(r"\d{9}", code): return "intercommunal"
    if re.fullmatch(r"\d{5}|2[AB]\d{3}", code): return "communal"
    if re.search(r"(?i)^r[ée]gion|\(r[ée]gion\)", n): return "régional"
    return "autre ou non précisé"


def index_dn(chemin):
    slugs = set()
    for r in json.load(open(chemin, encoding="utf-8")):
        if r.get("k") == "dn":
            u = r.get("u") or ""
            m = DN.search(u)
            slugs.add((m.group(1) if m else u).lower())
    return slugs


def descriptif_publie(carto):
    p = Path(carto).expanduser() / "assistant" / "descriptions_publiees.jsonl"
    if not p.exists(): return None
    out = set()
    for l in open(p, encoding="utf-8"):
        u = json.loads(l)[2] or ""
        m = DN.search(u)
        out.add((m.group(1) if m else u.rsplit("/", 1)[-1]).lower())
    return out


def tableau(entetes, lignes):
    t = ["| " + " | ".join(entetes) + " |", "|" + "---|" * len(entetes)]
    t += ["| " + " | ".join(str(c).replace("|", "/") for c in l) + " |" for l in lignes]
    return "\n".join(t)


def pct(n, d):
    return f"{100 * n / d:.0f} %" if d else "—"


def rapport(aides, slugs_index, publies, aujourd_hui):
    total = len(aides)
    ouvertes = [a for a in aides if not date_limite(a) or date_limite(a) >= aujourd_hui]
    maj = max((str(champ(a, "date_updated", "time_update", "date_created", "time_create") or "")[:10] for a in aides), default="")
    L = []
    L.append("# Aides-territoires comme source de démarches de dépôt : audit\n")
    L.append(f"Produit par `scripts/assistant/audit_aides_territoires.py` le {aujourd_hui}. Source : [Aides-territoires (ANCT)](https://aides-territoires.beta.gouv.fr/), "
             f"API, Licence Ouverte v2.0 ; dernière mise à jour des aides relevées : {maj or 'inconnue'}. Aucun ajout à l'index ni à la page : rapport seulement.\n")
    L.append("## Volumes\n")
    if getattr(releve, "base", None) is not None:
        L.append(f"- L'API plafonne une liste à 3 000 aides : la liste générale en a rendu {releve.base}. Le relevé est complété par une liste "
                 f"par public visé ({releve.apres_publics} aides distinctes), puis une liste par région du périmètre, chacune sous le plafond, "
                 f"réunies par identifiant. Publics proposés par l'API : {', '.join(releve.publics)} ; ni association, ni entreprise privée, "
                 f"ni particulier.")
        n = annonce_du_site()
        if n:
            L.append(f"- Le site annonce, dans ses statistiques publiques, {n} « aides publiées et toujours ouvertes aux candidatures » "
                     f"(lu le {aujourd_hui}) ; l'écart avec le relevé n'est pas expliqué (définition de « ouverte », périmètre).")
    L.append(f"- Aides publiées relevées (`/api/aids/`) : {total}.")
    L.append(f"- Dont ouvertes (sans date limite de dépôt, ou date limite non passée au {aujourd_hui}) : {len(ouvertes)}. **Le reste du rapport porte sur les aides ouvertes.**\n")
    # Champs
    cles = sorted({k for a in aides for k in a if not k.startswith("@")})
    L.append("## Champs disponibles et taux de remplissage (aides ouvertes)\n")
    L.append("Le champ `contact` est compté mais jamais lu ni recopié.\n")
    L.append(tableau(["Champ", "Rempli", "Part"], [[f"`{k}`", sum(1 for a in ouvertes if a.get(k) not in (None, "", [], {})),
                                                    pct(sum(1 for a in ouvertes if a.get(k) not in (None, "", [], {})), len(ouvertes))] for k in cles]) + "\n")
    # Lien de dépôt
    dep = [a for a in ouvertes if (a.get("application_url") or "").strip()]
    pareil = sum(1 for a in dep if normalise(a["application_url"]) == normalise(a.get("origin_url") or ""))
    L.append("## Lien de dépôt\n")
    L.append("Le lien de dépôt est porté par **`application_url`** (« candidater » : formulaire ou plateforme de dépôt). Il est distinct de "
             "`origin_url` (page de présentation chez le porteur) et de `url` (fiche Aides-territoires).\n")
    L.append(f"- Aides ouvertes avec un lien de dépôt : {len(dep)} ({pct(len(dep), len(ouvertes))}).")
    L.append(f"- Dont lien de dépôt identique à la page de présentation : {pareil}.\n")
    # Domaines
    doms = collections.Counter(domaine(a["application_url"]) for a in dep)
    fam = collections.Counter(famille(domaine(a["application_url"])) for a in dep)
    L.append("## Répartition des liens de dépôt\n")
    L.append(tableau(["Famille", "Aides"], fam.most_common()) + "\n")
    L.append("30 premiers domaines :\n")
    L.append(tableau(["Domaine", "Famille", "Aides"], [[d or "—", famille(d), n] for d, n in doms.most_common(30)]) + "\n")
    # Démarche Numérique
    ldn = [(a, DN.search(a["application_url"])) for a in dep if famille(domaine(a["application_url"])) == "Démarche Numérique"]
    sl = collections.Counter()
    for a, m in ldn:
        if not m: sl["lien Démarche Numérique sans /commencer/"] += 1
        elif m.group(1).lower() in slugs_index: sl["démarche présente dans l'index"] += 1
        elif publies is not None and m.group(1).lower() in publies: sl["publiée mais écartée de l'index (test ou réservée aux agents)"] += 1
        elif publies is not None: sl["absente du descriptif publié (fermée, dépubliée ou adresse changée)"] += 1
        else: sl["absente de l'index (sans --carto, motif non déterminé)"] += 1
    L.append("## Rapprochement avec Démarche Numérique\n")
    L.append(f"Liens de dépôt vers demarche.numerique.gouv.fr ou demarches-simplifiees.fr : {len(ldn)}. Rapprochement par l'adresse `/commencer/<slug>`.\n")
    L.append(tableau(["Cas", "Aides"], sl.most_common()) + "\n")
    # Porteurs et publics
    port = collections.Counter(propre(f, 80) for a in ouvertes for f in financeurs(a))
    pubs = collections.Counter(p for a in ouvertes for p in publics_de(a))
    grp = collections.Counter(g for a in ouvertes for g in ({PUBLICS.get(p, p) for p in publics_de(a)} or {"non précisé"}))
    L.append("## Porteurs (financeurs)\n")
    L.append(f"{len(port)} porteurs distincts. Les 30 premiers :\n")
    L.append(tableau(["Porteur", "Aides"], port.most_common(30)) + "\n")
    L.append("## Publics visés\n")
    L.append("Une aide peut viser plusieurs publics.\n")
    L.append(tableau(["Public", "Aides"], grp.most_common()) + "\n")
    L.append("Détail par valeur de l'API :\n")
    L.append(tableau(["Valeur de l'API (`targeted_audiences`)", "Aides"], pubs.most_common()) + "\n")
    # Territoire
    ech = collections.Counter(echelle(a) for a in ouvertes)
    L.append("## Répartition territoriale\n")
    L.append("Échelle donnée par l'API (`perimeter_scale`) ; à défaut, déduite du périmètre (nom, `perimeter_code`, `region_code`).\n")
    L.append(tableau(["Échelle", "Aides"], ech.most_common()) + "\n")
    # Licences
    lic = collections.Counter(a.get("import_share_licence") or "non précisée (Licence Ouverte v2.0 du site)" for a in ouvertes)
    L.append("## Licence déclarée par aide (`import_share_licence`)\n")
    L.append("Certaines aides sont importées d'autres sources ; leur licence de partage est à vérifier avant toute réutilisation.\n")
    L.append(tableau(["Licence", "Aides"], lic.most_common()) + "\n")
    # Démarches nouvelles
    hors = [a for a in dep if famille(domaine(a["application_url"])) != "Démarche Numérique"]
    uniques = collections.Counter(normalise(a["application_url"]) for a in hors)
    partages = sorted(((n, u) for u, n in uniques.items() if n > 1), reverse=True)[:15]
    L.append("## Démarches de dépôt nouvelles qu'apporterait l'intégration\n")
    L.append(f"- Aides ouvertes dont le dépôt se fait hors Démarche Numérique : {len(hors)}.")
    L.append(f"- **Adresses de dépôt distinctes, après dédoublonnage : {len(uniques)}**, sur {len({domaine(a['application_url']) for a in hors})} domaines.")
    L.append(f"- Aides ouvertes sans lien de dépôt : {len(ouvertes) - len(dep)} (dépôt à chercher sur la page de présentation).\n")
    if partages:
        L.append("Adresses de dépôt partagées par plusieurs aides (plateformes communes), les 15 premières :\n")
        L.append(tableau(["Adresse", "Aides"], [[u, n] for n, u in partages]) + "\n")
    # Exemples
    ex = random.Random(20261120).sample(hors, min(20, len(hors)))
    L.append("## 20 exemples tirés au hasard, dépôt hors Démarche Numérique\n")
    L.append(tableau(["Titre", "Porteur", "Public", "Périmètre", "Domaine du lien"],
                     [[propre(a.get("name"), 110), propre(", ".join(financeurs(a)), 70) or "—",
                       ", ".join(sorted({PUBLICS.get(p, p) for p in publics_de(a)})) or "—",
                       propre(nom(a.get("perimeter")), 50) or "—", domaine(a["application_url"])] for a in ex]) + "\n")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sortie", default=str(RACINE / "donnees" / "assistant" / "rapport_aides_territoires.md"))
    ap.add_argument("--index", default=str(RACINE / "donnees" / "assistant" / "index.json"))
    ap.add_argument("--carto", default=None, help="dossier cartographie (assistant/descriptions_publiees.jsonl), pour qualifier les démarches absentes")
    ap.add_argument("--depuis-fichier", default=None, help="relevé déjà fait (liste JSON d'aides), sans appel à l'API")
    ap.add_argument("--brut", default=None, help="garde ici le relevé complet (hors du dépôt)")
    A = ap.parse_args()
    if A.depuis_fichier:
        aides = json.load(open(A.depuis_fichier, encoding="utf-8"))
    else:
        aides = releve(jeton_bearer())
        if A.brut:
            json.dump(aides, open(A.brut, "w", encoding="utf-8"), ensure_ascii=False)
    texte = rapport(aides, index_dn(A.index), descriptif_publie(A.carto) if A.carto else None, datetime.date.today().isoformat())
    Path(A.sortie).write_text(texte, encoding="utf-8")
    print(f"écrit : {A.sortie} ({len(aides)} aides)")


if __name__ == "__main__":
    main()
