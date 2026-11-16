"""Fiche Intérieur, étape 2 (c) : qui instruit quoi. Open data seul.
Base : démarches à zone déclarée (pas les rattachements par nom d'organisme), publiées depuis le 7 octobre 2022 (reprise des zones),
au plus trois zones. Le type d'organisme déclaré n'est pas utilisé ; l'instructeur est lu dans le nom de l'organisme et du service.
Deux sens : (1) dans la zone Intérieur, qui instruit chaque famille ; (2) démarches émises par une préfecture ou sous-préfecture
mais déclarées dans la zone d'un autre ministère. Sortie : out/interieur_qui_instruit.json"""
import json, re, sys, collections as C
sys.argv = ["x", "scripts/config_interieur.json", "/dev/null"]
exec(open("scripts/32_local_national_interieur.py").read().split("clusters = []")[0])
nd = lambda L: sum(r["dossiersCount"] or 0 for r in L)
DEB = "2022-10-07"
INSTR = [("préfecture ou sous-préfecture", r"pr[e]fecture|\bsgcd\b|\bsgc\s?\d|\bsgar\b|\bpref\s?\d|cabinet du pr[e]fet|haut.commissariat"),
         ("direction départementale ou régionale d'un autre ministère (DDT, DDETS, DREAL, DRIEAT...)", r"\bdd(t|tm|ets|etspp|pp|cspp|fip)(\b|\d)|direction departementale|\bdreal\b|\bdriea|\bdrieets?\b|\bdreets\b|\bdirecct|\bud\s?\d|unite departementale|\bdraaf\b|\bdriaaf\b|\bdsden\b|\bsdjes\b|\bdrajes\b|\bars\b"),
         ("police, gendarmerie et leurs écoles", r"police|gendarm|\bdgpn\b|\bdggn\b|\bsgami\b|\benp\b|commissariat|\bcrs\b|\bdtpn\b|\bdipn\b|\bdcpaf\b|\bpaf\b|\begav\b|\bcegn\b"),
         ("administration centrale de l'Intérieur", r"minist[e]re de l.int[e]rieur|minist[e]re interieur|direction g[e]n[e]rale|\bdg[a-z]{1,4}\b|\bdsr\b|\bdlpaj\b|\bdgcl\b|\bdgef\b|delegation a la securite routiere|sous-direction|\bmi/|secretariat general|\bdihal\b|\bdilcrah\b|\bmildeca\b|\bcipdr\b|\bsg-cipdr\b"),
         ("opérateurs (ANTS / France Titres, OFII, OFPRA...)", r"\bants\b|france titres|\bofii\b|\bofpra\b|agence nationale"),
         ("sécurité civile et collectivités (SDIS...)", r"\bsdis\b|incendie|pompier|conseil departemental|commune|mairie|ville de|metropole|collectivite"),
         ("autre", r".")]
def instr(r):
    o = na((r["organisme"] or "") + " | " + (r["service_nom"] or ""))
    for n, rx in INSTR:
        if re.search(rx, o): return n
I = "Ministère de l’Intérieur"
base = [r for r in per if r["src"] in ("zone", "zone_multi") and (r["datePublication"] or "") >= DEB]
for r in base: r["instr"] = instr(r)
out = {"base": {"demarches": len(base), "dossiers": nd(base), "part_du_perimetre_demarches": round(100 * len(base) / len(per), 1), "part_du_perimetre_dossiers": round(100 * nd(base) / nd(per), 1)},
       "instructeurs": {n: [len([r for r in base if r["instr"] == n]), nd([r for r in base if r["instr"] == n])] for n, _ in INSTR}, "par_famille": {}}
for f in sorted({r["fam"] for r in base}, key=lambda f: -nd([r for r in base if r["fam"] == f])):
    L = [r for r in base if r["fam"] == f]
    out["par_famille"][f] = {"demarches": len(L), "dossiers": nd(L), "instructeurs": {n: [len(M), nd(M)] for n in [x for x, _ in INSTR] for M in [[r for r in L if r["instr"] == n]] if M}}
# sens 2 : préfectures dans d'autres zones
autres = []
for r in rows:
    z = r["zones"] or []
    if not z or len(z) > 3 or I in z or (r["datePublication"] or "") < DEB: continue
    if re.search(r"pr[e]fecture|\bsgcd\b|\bsgar\b|cabinet du pr[e]fet", na((r["organisme"] or "") + " | " + (r["service_nom"] or ""))): autres.append(r)
tot_z = C.Counter(); dz = C.Counter()
for r in autres:
    for x in r["zones"]: tot_z[x] += 1; dz[x] += r["dossiersCount"] or 0
prefs_zone_int = [r for r in base if r["instr"] == "préfecture ou sous-préfecture"]
out["prefectures_autres_zones"] = {"demarches": len(autres), "dossiers": nd(autres),
    "comparaison_prefectures_en_zone_interieur": [len(prefs_zone_int), nd(prefs_zone_int)],
    "par_zone": [(z, n, dz[z]) for z, n in tot_z.most_common()]}
json.dump(out, open("out/interieur_qui_instruit.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(out["base"], ensure_ascii=False)); print(json.dumps(out["instructeurs"], ensure_ascii=False, indent=0))
for f, x in out["par_famille"].items(): print(f"{x['demarches']:5d} {x['dossiers']:8d} {f[:45]:45s}", "; ".join(f"{k[:22]} {v[0]}/{v[1]}" for k, v in sorted(x["instructeurs"].items(), key=lambda kv: -kv[1][1])))
p = out["prefectures_autres_zones"]; print("\nPréfectures, autres zones :", p["demarches"], p["dossiers"], "| préfectures en zone Intérieur :", p["comparaison_prefectures_en_zone_interieur"])
for z in p["par_zone"][:12]: print("  ", z)
