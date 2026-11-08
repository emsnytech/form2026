#!/usr/bin/env python3
"""Vérifie que le site en ligne correspond à main : le dernier déploiement GitHub Pages a réussi, et porte le dernier commit de main.
Sort en erreur sinon, pour que le workflow alerte-deploiement.yml ouvre une issue. Un déploiement qui échoue ne prévient personne d'autre.

    GH_TOKEN=… python3 scripts/verifier_deploiement.py   # ou avec gh authentifié en local

Un déploiement en cours n'est pas une erreur : le dernier commit de main a 45 minutes pour être en ligne."""
import datetime as dt, json, subprocess, sys

DEPOT, DELAI = "emsnytech/form2026", dt.timedelta(minutes=45)


def gh(*args):
    return json.loads(subprocess.run(["gh", "api", *args], capture_output=True, text=True, check=True).stdout)


def date(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


build = gh(f"repos/{DEPOT}/pages/builds/latest")
main = gh(f"repos/{DEPOT}/commits/main")
sha, quand = main["sha"], date(main["commit"]["committer"]["date"])
maintenant = dt.datetime.now(dt.timezone.utc)
print(f"main : {sha[:7]} du {quand:%d/%m %H:%M} UTC ; dernier déploiement : {build['status']} sur {build['commit'][:7]} du {date(build['created_at']):%d/%m %H:%M} UTC")
if build["status"] == "errored":
    print(f"ÉCHEC : le dernier déploiement a échoué ({(build.get('error') or {}).get('message') or 'sans message'}). Le site en ligne n'est pas à jour.")
    sys.exit(1)
if build["commit"] != sha and maintenant - quand > DELAI:
    print(f"RETARD : main ({sha[:7]}) n'est pas en ligne {int((maintenant - quand).total_seconds() // 60)} minutes après le commit.")
    sys.exit(1)
print("Le site en ligne correspond à main.")
