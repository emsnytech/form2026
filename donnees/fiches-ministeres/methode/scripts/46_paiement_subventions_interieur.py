"""Fiche Intérieur : la phase de paiement des subventions d'investissement aux collectivités (DETR, DSIL, DSID, DPV, FNADT,
fonds vert…). La demande de subvention est déposée, instruite et décidée (pour la DETR et la DSIL, démarche unique nationale
depuis l'exercice 2026) ; la collectivité demande ensuite le versement (avance, acompte, solde) sur justificatifs. Cette
seconde phase reste locale : le script compte les départements qui l'ont mise en ligne et les fonds que chacun y a inclus.
Open data seul.

Règles, fixées après lecture des titres :
- démarches du périmètre, famille « Dotations et subventions », dont le titre nomme un paiement, un versement, un acompte ou
  un solde, et une subvention, une dotation ou un fonds ; rattachement au département du script 40 ;
- fonds couverts : nommés dans le titre, ou parmi les choix d'une liste déroulante du formulaire (descriptif ouvert, champs) ;
  une démarche qui n'en nomme aucun est comptée « fonds non précisés » ;
- lien vers le dossier de demande : champ « lien vers un autre dossier » de la plateforme dans le formulaire ;
- une démarche nationale de paiement est cherchée avec les mêmes mots du titre.
Sortie : out/interieur_paiement_subventions.json (comptes, aucun nom de territoire)."""
import io, os, json, re, contextlib, collections as C
src40 = open("scripts/40_variete_departements_interieur.py").read().split("json.dump(out")[0]
with contextlib.redirect_stdout(io.StringIO()):
    exec(src40)
RAW = os.environ.get("FORM2026_RAW", "data/20261021041002-demarches.json")
PAI = re.compile(r"paiement|versement|acompte|\bsolde\b", re.I)
OBJ = re.compile(r"subvention|dotation|\bDETR\b|\bDSIL\b|\bDSID\b|\bDPV\b|\bFNADT\b|fonds vert", re.I)
FONDS = {"DETR": r"\bDETR\b|dotation d.[ée]quipement des territoires ruraux", "DSIL": r"\bDSIL\b|dotation de soutien [àa] l.investissement local",
         "DSID": r"\bDSID\b|dotation de soutien [àa] l.investissement des d[ée]partements", "DPV": r"\bDPV\b|dotation politique de la ville",
         "FNADT": r"\bFNADT\b", "fonds vert": r"fonds vert|\bFV\b", "DSEC": r"\bDSEC\b|[ée]v[èe]nements climatiques"}
FONDS = {k: re.compile(v, re.I) for k, v in FONDS.items()}
SEL = [r for r in per if r["fam"] == "Dotations et subventions" and PAI.search(r["title"] or "") and OBJ.search(r["title"] or "")]
NUM = {r["number"] for r in SEL}
champs = {}
for x in json.load(open(RAW)):
    if x["number"] in NUM: champs[x["number"]] = (x.get("revision") or {}).get("champDescriptors") or []
def parcours(cs):
    for c in cs:
        yield c
        for k in ("champDescriptors", "children"):
            if isinstance(c.get(k), list): yield from parcours(c[k])
for r in SEL:
    cs = list(parcours(champs.get(r["number"], [])))
    opts = " | ".join(str(o) for c in cs if "DropDown" in (c.get("__typename") or "") for o in (c.get("options") or []))
    r["fonds_titre"] = {k for k, rx in FONDS.items() if rx.search(r["title"] or "")}
    r["fonds_champs"] = {k for k, rx in FONDS.items() if rx.search(opts)}
    r["fonds"] = r["fonds_titre"] | r["fonds_champs"]
    r["lien_dossier"] = any(c.get("__typename") == "DossierLinkChampDescriptor" for c in cs)
loc = [r for r in SEL if r["niv"] == "locale" and r["dep"]]
on = [r for r in loc if r["state"] == "publiee"]
def par_dep(L):
    D = C.defaultdict(list)
    for r in L: D[r["dep"]].append(r)
    return D
Don, Dall = par_dep(on), par_dep(loc)
fonds_dep = {k: set().union(*(r["fonds"] for r in v)) for k, v in Don.items()}
res = {"regles": {"departements": NDEP, "fonds": list(FONDS)},
    "demarches": len(SEL), "dossiers": nd(SEL), "nationales": [r["number"] for r in SEL if r["niv"] == "nationale"],
    "locales": {"versions": len(loc), "departements_depuis_l_origine": len(Dall), "dossiers": nd(loc)},
    "en_ligne": {"versions": len(on), "departements": len(Don), "dossiers": nd(on),
                 "departements_par_fonds": {k: sum(1 for f in fonds_dep.values() if k in f) for k in FONDS},
                 "departements_sans_fonds_precise": sum(1 for f in fonds_dep.values() if not f),
                 "nombre_de_fonds_par_departement": dict(sorted(C.Counter(len(f) for f in fonds_dep.values()).items())),
                 "departements_un_formulaire_pour_plusieurs_fonds": sum(1 for v in Don.values() if any(len(r["fonds"]) >= 2 for r in v)),
                 "departements_avec_lien_vers_le_dossier_de_demande": sum(1 for v in Don.values() if any(r["lien_dossier"] for r in v)),
                 "fonds_lus_dans_les_champs_seulement": sum(1 for r in on if r["fonds_champs"] - r["fonds_titre"]),
                 "versions_par_departement_max": max((len(v) for v in Don.values()), default=0)},
    "premiere_publication_par_departement": dict(sorted(C.Counter(min(r["datePublication"][:4] for r in v) for v in Dall.values()).items())),
    "hors_departement": [sum(1 for r in SEL if r["niv"] != "nationale" and not r["dep"]), nd([r for r in SEL if r["niv"] != "nationale" and not r["dep"]])]}
json.dump(res, open("out/interieur_paiement_subventions.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
