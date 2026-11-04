#!/usr/bin/env python3
"""Vérifie tous les liens du site : internes (fichiers et ancres) et externes.

    python3 scripts/verifier_liens.py                          # pages et données embarquées
    python3 scripts/verifier_liens.py --portee pages           # sans les données embarquées
    python3 scripts/verifier_liens.py --interne-seulement      # hors ligne
    python3 scripts/verifier_liens.py --demarches-echantillon 200 --sortie rapport.json

Trois verdicts pour un lien externe :
  ok            la page répond ;
  echec         404, 410 ou nom de domaine introuvable : le lien est à corriger ;
  non_concluant 401, 403, 429, 5xx, délai ou certificat : le site peut refuser un robot sans que le lien soit mort.

Le script sort en erreur (1) pour un lien interne cassé ou un échec sur un lien écrit dans une page.
Un échec dans les données embarquées (fichiers tiers repris par explorer.html et cadrage-dematerialisation.html)
est compté et listé sans faire échouer le contrôle : ces adresses viennent des sources.

Limites : une réponse 200 ne prouve pas que le contenu est le bon. Les liens construits par JavaScript ne sont
pas lus, sauf les adresses écrites en toutes lettres. Les 35 864 adresses de démarches ne sont testées que sur
échantillon, pour ne pas envoyer autant de requêtes à un service public.
"""
import argparse, collections, html, json, random, re, socket, ssl, subprocess, sys, threading, time, urllib.error, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path, PurePosixPath

RACINE = Path(__file__).resolve().parent.parent
SITE = "https://emsnytech.github.io/form2026/"
AGENT = "Mozilla/5.0 (compatible; FORM2026-verifier-liens; +https://emsnytech.github.io/form2026/)"
HORS_SITE = {"Claude outputs", "_fiches-ministeres", ".git", ".github"}
DONNEES_TIERS = {"explorer.html", "cadrage-dematerialisation.html"}
HOTES_IGNORES = {"www.w3.org", "fonts.googleapis.com", "fonts.gstatic.com", "localhost", "127.0.0.1", "example.com", "www.example.com"}
PREFIXES = {"https://demarche.numerique.gouv.fr/commencer/"}  # début d'adresse complété par le code de la page
ATTR = re.compile(r"""(?:href|src)\s*=\s*(?:"([^"]*)"|'([^']*)')""", re.I)
URL = re.compile(r"""https?://[^\s"'<>\\`)\]}|]+""")
MD_LIEN = re.compile(r"\]\(([^)\s]+)\)")
ANCRE = re.compile(r"""\b(?:id|name)\s*=\s*["']([^"']+)["']""")
PRECONNEXION = re.compile(r"""<link[^>]+rel=["'](?:preconnect|dns-prefetch)["'][^>]*>""", re.I)
BLOC_JSON = re.compile(r"""<script[^>]*type=["']application/json["'][^>]*>.*?</script>""", re.S)


def fichiers_du_site():
    sortie = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=RACINE, text=True)
    return {f for f in sortie.splitlines() if not (set(PurePosixPath(f).parts) & HORS_SITE) and (RACINE / f).is_file()}


def nettoyer(u):
    return html.unescape(u).rstrip(".,;:!?*»").replace("&amp;", "&")


def collecter(site):
    """Renvoie les liens internes [(page, cible)], externes {url: {pages, portee}} et le nombre de liens dynamiques."""
    internes, externes, dynamiques = [], {}, 0

    def externe(url, page, portee):
        if "${" in url or "{" in url or "…" in url or url in PREFIXES or urllib.parse.urlsplit(url).hostname in HOTES_IGNORES:
            return
        e = externes.setdefault(url, {"pages": set(), "portee": portee})
        e["pages"].add(page)
        if portee == "pages":
            e["portee"] = "pages"

    for page in sorted(site):
        if not page.endswith((".html", ".md")) or PurePosixPath(page).name.startswith("gabarit_"):
            continue
        texte = (RACINE / page).read_text(encoding="utf-8", errors="ignore")
        sans_preco = PRECONNEXION.sub("", texte)
        if page in DONNEES_TIERS:
            sans_donnees = "\n".join(l for l in BLOC_JSON.sub("", sans_preco).splitlines() if len(l) < 20000)
        else:
            sans_donnees = sans_preco
        attributs = [a or b for a, b in ATTR.findall(sans_donnees)] if page.endswith(".html") else MD_LIEN.findall(sans_donnees)
        for cible in attributs:
            cible = nettoyer(cible.strip())
            if "${" in cible or re.search(r"'\s*\+|\+\s*'", cible):
                dynamiques += 1
            elif cible.startswith(SITE):
                internes.append((page, None, cible[len(SITE):] or "index.html"))
            elif cible and not re.match(r"^(https?:|mailto:|tel:|data:|javascript:|//)", cible):
                internes.append((page, page, cible))
        for u in URL.findall(sans_preco):
            u = nettoyer(u)
            if u.startswith(SITE):
                internes.append((page, None, u[len(SITE):] or "index.html"))
            else:
                externe(u, page, "pages" if u in sans_donnees else "donnees")
    return internes, externes, dynamiques


def verifier_internes(internes, site):
    ancres, erreurs = {}, []

    def ancres_de(f):
        if f not in ancres:
            t = (RACINE / f).read_text(encoding="utf-8", errors="ignore")
            ancres[f] = set(ANCRE.findall(t))
            m = re.search(r"VALID_TABS\s*=\s*\[([^\]]*)\]", t)  # onglets d'explorer.html, adressés par #onglet
            if m:
                ancres[f] |= set(re.findall(r"'([^']+)'", m.group(1)))
        return ancres[f]

    uniques = set(internes)
    for page, base, cible in sorted(uniques, key=str):
        decoupe = urllib.parse.urlsplit(cible)
        chemin = urllib.parse.unquote(decoupe.path)
        if not chemin:
            resolu = page
        else:
            parents = str(PurePosixPath(base).parent) if base else "."
            pile = []
            for morceau in PurePosixPath(parents, chemin).parts:
                if morceau == "..":
                    if not pile:
                        pile = None
                        break
                    pile.pop()
                elif morceau != ".":
                    pile.append(morceau)
            if pile is None:
                erreurs.append((page, cible, "remonte au-dessus du site"))
                continue
            resolu = "/".join(pile) or "index.html"
            if resolu not in site and f"{resolu}/index.html" in site:
                resolu = f"{resolu}/index.html"
        if resolu not in site:
            dossier = any(f.startswith(resolu.rstrip("/") + "/") for f in site)
            erreurs.append((page, cible, "dossier sans index.html" if dossier else "fichier absent"))
        elif decoupe.fragment and resolu.endswith(".html") and decoupe.fragment not in ancres_de(resolu):
            erreurs.append((page, cible, "ancre absente"))
    return len(uniques), erreurs


class Hotes:
    """Au plus deux requêtes simultanées et un écart minimal par hôte."""
    def __init__(self):
        self.verrous, self.derniere, self.garde = {}, {}, threading.Lock()

    def attendre(self, hote):
        with self.garde:
            v = self.verrous.setdefault(hote, threading.Semaphore(2))
        v.acquire()
        with self.garde:
            pause = max(0, self.derniere.get(hote, 0) + 0.25 - time.time())
            self.derniere[hote] = time.time() + pause
        time.sleep(pause)
        return v


def tester(url, hotes, delai=20, essais=2):
    hote = urllib.parse.urlsplit(url).hostname or ""
    detail = ""
    url_ascii = urllib.parse.quote(url, safe=":/?#[]@!$&'()*+,;=%~-._")
    for essai in range(essais):
        v = hotes.attendre(hote)
        try:
            requete = urllib.request.Request(url_ascii, headers={"User-Agent": AGENT, "Accept": "text/html,application/xhtml+xml,*/*;q=0.8"})
            with urllib.request.urlopen(requete, timeout=delai) as r:
                return "ok", r.status, r.geturl() if r.geturl() != url_ascii else ""
        except urllib.error.HTTPError as e:
            if e.code in (404, 410):
                return "echec", e.code, ""
            detail = e.code
            if e.code not in (429, 500, 502, 503, 504):
                return "non_concluant", e.code, ""
        except urllib.error.URLError as e:
            raison = e.reason
            if isinstance(raison, socket.gaierror):
                if essai + 1 == essais:
                    return "echec", "domaine introuvable", ""
            elif isinstance(raison, ssl.SSLError):
                return "non_concluant", "certificat", ""
            detail = str(raison)[:60]
        except Exception as e:  # délai dépassé, réponse tronquée, adresse invalide
            detail = f"{type(e).__name__}"[:60]
        finally:
            v.release()
        time.sleep(1.5)
    return "non_concluant", detail, ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--portee", choices=["pages", "tout"], default="tout")
    ap.add_argument("--interne-seulement", action="store_true")
    ap.add_argument("--demarches-echantillon", type=int, default=0)
    ap.add_argument("--sortie")
    A = ap.parse_args()

    site = fichiers_du_site()
    internes, externes, dynamiques = collecter(site)
    n_int, err_int = verifier_internes(internes, site)
    print(f"Internes : {n_int} liens testés, {len(err_int)} cassés. Liens dynamiques non lus : {dynamiques}.")
    for page, cible, motif in err_int:
        print(f"  CASSÉ {page} → {cible} ({motif})")

    resultats = {}
    if not A.interne_seulement:
        retenus = {u: e for u, e in externes.items() if A.portee == "tout" or e["portee"] == "pages"}
        if A.demarches_echantillon:
            slugs = []
            for f in sorted(RACINE.glob("app_demarches_*.json")):
                slugs += [d["url"] for d in json.load(open(f, encoding="utf-8")) if d.get("url")]
            random.Random(2026).shuffle(slugs)
            for s in slugs[:A.demarches_echantillon]:
                u = s if s.startswith("http") else f"https://demarche.numerique.gouv.fr/commencer/{s}"
                retenus.setdefault(u, {"pages": {"explorer.html (échantillon)"}, "portee": "donnees"})
        hotes = Hotes()
        with ThreadPoolExecutor(max_workers=32) as pool:
            verdicts = pool.map(lambda u: (u, tester(u, hotes)), retenus)
            for i, (u, (verdict, code, finale)) in enumerate(verdicts, 1):
                resultats[u] = {"verdict": verdict, "code": code, "finale": finale, "portee": retenus[u]["portee"], "pages": sorted(retenus[u]["pages"])}
                if i % 500 == 0:
                    print(f"  … {i}/{len(retenus)}", flush=True)
        for portee in ("pages", "donnees"):
            c = collections.Counter(r["verdict"] for r in resultats.values() if r["portee"] == portee)
            print(f"Externes, {portee} : {sum(c.values())} testés, {c['ok']} ok, {c['echec']} échecs, {c['non_concluant']} non concluants.")
        for u, r in sorted(resultats.items()):
            if r["verdict"] == "echec" and r["portee"] == "pages":
                print(f"  ÉCHEC {r['code']} {u} ← {', '.join(r['pages'][:3])}")
            elif r["verdict"] == "non_concluant" and r["portee"] == "pages":
                print(f"  À VOIR {r['code']} {u} ← {', '.join(r['pages'][:3])}")

    if A.sortie:
        json.dump({"date": time.strftime("%Y-%m-%d"), "internes_testes": n_int, "internes_casses": err_int, "dynamiques_non_lus": dynamiques, "externes": resultats},
                  open(A.sortie, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    echecs_pages = [u for u, r in resultats.items() if r["verdict"] == "echec" and r["portee"] == "pages"]
    sys.exit(1 if err_int or echecs_pages else 0)


if __name__ == "__main__":
    main()
