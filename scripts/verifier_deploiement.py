#!/usr/bin/env python3
"""Vérifie que le site en ligne correspond à main : le dernier déploiement GitHub Pages a réussi, et porte le dernier commit de main.
Sort en erreur sinon, pour que le workflow alerte-deploiement.yml ouvre une issue. Un déploiement qui échoue ne prévient personne d'autre.

    GH_TOKEN=… python3 scripts/verifier_deploiement.py            # constat immédiat (contrôle du matin)
    GH_TOKEN=… python3 scripts/verifier_deploiement.py --attendre # après une fusion : suit le déploiement jusqu'à sa fin

Un déploiement en cours n'est pas une erreur : le dernier commit de main a 45 minutes pour être en ligne.
Avec --attendre, le script interroge toutes les 30 secondes tant que main n'est pas en ligne et que le délai court,
puis rend son verdict ; un déploiement remplacé par un plus récent n'est pas un échec (l'API le marque pourtant « errored ») : seul compte celui du commit de main."""
import datetime as dt, json, subprocess, sys, time

DEPOT, DELAI = "emsnytech/form2026", dt.timedelta(minutes=45)


def gh(*args):
    return json.loads(subprocess.run(["gh", "api", *args], capture_output=True, text=True, check=True).stdout)


def dernier_deploiement():
    """Dernier déploiement de l'environnement github-pages et son dernier état.
    L'API des déploiements suit les relances d'un déploiement échoué ; l'API des builds Pages ne les voit pas
    (constaté le 09/11/2026 : déploiement relancé avec succès, build toujours « errored »)."""
    d = gh(f"repos/{DEPOT}/deployments?environment=github-pages&per_page=1")[0]
    etats = gh(f"repos/{DEPOT}/deployments/{d['id']}/statuses?per_page=1")
    etat = etats[0]["state"] if etats else "queued"
    statut = {"success": "built", "failure": "errored", "error": "errored"}.get(etat, etat)
    return {"status": statut, "commit": d["sha"], "created_at": d["created_at"],
            "error": {"message": f"état du déploiement : {etat}"}}


def date(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


ATTENDRE = "--attendre" in sys.argv[1:]
while True:
    build = dernier_deploiement()
    main = gh(f"repos/{DEPOT}/commits/main")
    sha, quand = main["sha"], date(main["commit"]["committer"]["date"])
    maintenant = dt.datetime.now(dt.timezone.utc)
    # Un déploiement remplacé par un plus récent est marqué « errored » par l'API : seul compte l'échec sur le commit de main.
    fini = build["commit"] == sha and build["status"] in ("built", "errored")
    if not ATTENDRE or fini or maintenant - quand > DELAI:
        break
    time.sleep(30)
print(f"main : {sha[:7]} du {quand:%d/%m %H:%M} UTC ; dernier déploiement : {build['status']} sur {build['commit'][:7]} du {date(build['created_at']):%d/%m %H:%M} UTC")
if build["status"] == "errored" and build["commit"] == sha:
    print(f"ÉCHEC : le dernier déploiement a échoué ({(build.get('error') or {}).get('message') or 'sans message'}). Le site en ligne n'est pas à jour.")
    sys.exit(1)
if build["commit"] != sha and maintenant - quand > DELAI:
    print(f"RETARD : main ({sha[:7]}) n'est pas en ligne {int((maintenant - quand).total_seconds() // 60)} minutes après le commit.")
    sys.exit(1)
print("Le site en ligne correspond à main.")
