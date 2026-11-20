"""Déduction du département d'une démarche en ligne dont l'organisme n'en déclare pas (portée « inc » de l'index).

Employé par build_index.py. Cherche d'abord dans le nom de l'organisme, puis dans le titre. Formes reconnues, dans cet ordre :
  - cas particuliers : « Préfecture de police » (75), « Préfecture de (la) région X » (département chef-lieu, table
    REGIONS), collectivités et départements d'outre-mer nommés (Guyane, Martinique, Mayotte, La Réunion, Guadeloupe) ;
  - code accolé à un sigle : « CAF38 », « CPAM 75 », « DDT-33 », « DDETS 69 »… (sigles de SIGLES) ;
  - code en tête du titre suivi d'un tiret : « 94-Demande… », « 971 - … » (titre seulement) ;
  - nom du département précédé d'un marqueur administratif : « Préfecture du Pas-de-Calais », « CAF des Yvelines »,
    « Conseil départemental de la Loire ».
Jamais à partir d'un nom isolé : « Var », « Nord », « Loire » ou « Paris » seuls ne donnent rien. Collectivité de Corse :
deux départements, aucun n'est déduit.
"""
import re, unicodedata

DEPARTEMENTS = {
    "01": "Ain", "02": "Aisne", "03": "Allier", "04": "Alpes-de-Haute-Provence", "05": "Hautes-Alpes", "06": "Alpes-Maritimes",
    "07": "Ardèche", "08": "Ardennes", "09": "Ariège", "10": "Aube", "11": "Aude", "12": "Aveyron", "13": "Bouches-du-Rhône",
    "14": "Calvados", "15": "Cantal", "16": "Charente", "17": "Charente-Maritime", "18": "Cher", "19": "Corrèze",
    "2A": "Corse-du-Sud", "2B": "Haute-Corse", "21": "Côte-d'Or", "22": "Côtes-d'Armor", "23": "Creuse", "24": "Dordogne",
    "25": "Doubs", "26": "Drôme", "27": "Eure", "28": "Eure-et-Loir", "29": "Finistère", "30": "Gard", "31": "Haute-Garonne",
    "32": "Gers", "33": "Gironde", "34": "Hérault", "35": "Ille-et-Vilaine", "36": "Indre", "37": "Indre-et-Loire", "38": "Isère",
    "39": "Jura", "40": "Landes", "41": "Loir-et-Cher", "42": "Loire", "43": "Haute-Loire", "44": "Loire-Atlantique",
    "45": "Loiret", "46": "Lot", "47": "Lot-et-Garonne", "48": "Lozère", "49": "Maine-et-Loire", "50": "Manche", "51": "Marne",
    "52": "Haute-Marne", "53": "Mayenne", "54": "Meurthe-et-Moselle", "55": "Meuse", "56": "Morbihan", "57": "Moselle",
    "58": "Nièvre", "59": "Nord", "60": "Oise", "61": "Orne", "62": "Pas-de-Calais", "63": "Puy-de-Dôme",
    "64": "Pyrénées-Atlantiques", "65": "Hautes-Pyrénées", "66": "Pyrénées-Orientales", "67": "Bas-Rhin", "68": "Haut-Rhin",
    "69": "Rhône", "70": "Haute-Saône", "71": "Saône-et-Loire", "72": "Sarthe", "73": "Savoie", "74": "Haute-Savoie",
    "75": "Paris", "76": "Seine-Maritime", "77": "Seine-et-Marne", "78": "Yvelines", "79": "Deux-Sèvres", "80": "Somme",
    "81": "Tarn", "82": "Tarn-et-Garonne", "83": "Var", "84": "Vaucluse", "85": "Vendée", "86": "Vienne", "87": "Haute-Vienne",
    "88": "Vosges", "89": "Yonne", "90": "Territoire de Belfort", "91": "Essonne", "92": "Hauts-de-Seine",
    "93": "Seine-Saint-Denis", "94": "Val-de-Marne", "95": "Val-d'Oise",
    "971": "Guadeloupe", "972": "Martinique", "973": "Guyane", "974": "La Réunion", "976": "Mayotte",
}
# Région → département chef-lieu (préfecture de région).
REGIONS = {
    "Auvergne-Rhône-Alpes": "69", "Bourgogne-Franche-Comté": "21", "Bretagne": "35", "Centre-Val de Loire": "45",
    "Grand Est": "67", "Hauts-de-France": "59", "Île-de-France": "75", "Normandie": "76", "Nouvelle-Aquitaine": "33",
    "Occitanie": "31", "Pays de la Loire": "44", "Provence-Alpes-Côte d'Azur": "13",
    "Guadeloupe": "971", "Martinique": "972", "Guyane": "973", "La Réunion": "974", "Réunion": "974", "Mayotte": "976",
}
SIGLES = ["DDETSPP", "DDETS", "DDTM", "DDPP", "DDT", "DSDEN", "DASEN", "SDIS", "CPAM", "CAF", "MSA", "UD", "ARS"]
# « Sous-préfecture » porte le nom de sa ville (« Sous-préfecture de Vienne » est en Isère) : ce marqueur n'est retenu
# qu'avec un article (« de la », « du »…), que prennent les noms de département et non les noms de ville.
MARQUEURS = [r"pr[ée]fecture", r"conseil d[ée]partemental", r"d[ée]partement", r"caf", r"cpam",
             r"ddtm?", r"ddpp", r"ddets", r"dsden", r"sdis"]
VALIDES = set(DEPARTEMENTS)


def _n(s):
    """Minuscules, sans accents ; tirets, apostrophes et ponctuation deviennent des espaces."""
    s = unicodedata.normalize("NFD", s or "").encode("ascii", "ignore").decode().lower()
    return " " + " ".join(re.findall(r"[a-z0-9]+", s)) + " "


def _alt(noms):
    return "|".join(re.escape(_n(x).strip()) for x in sorted(noms, key=lambda x: -len(_n(x))))


_NOM = {_n(v).strip(): k for k, v in DEPARTEMENTS.items()}
_NOM[_n("Réunion").strip()] = "974"
_ARTICLE = r"(?:du |de la |de l |des |de |d )?"
RE_POLICE = re.compile(r" prefecture de police ")
RE_REGION = re.compile(r" prefecture (?:de )?(?:la )?region " + _ARTICLE + "(" + _alt(REGIONS) + ") ")
RE_OUTREMER = re.compile(r" (?:collectivite (?:territoriale )?|departement |region |conseil departemental |conseil regional )"
                         + _ARTICLE + "(guyane|martinique|mayotte|la reunion|reunion|guadeloupe) ")
RE_SIGLE = re.compile(r"\b(" + "|".join(SIGLES) + r")\s*[-_ ]?\s*(\d{2,3}|2A|2B)\b", re.I)
RE_CODE_TITRE = re.compile(r"^(0[1-9]|[1-8]\d|9[0-5]|2A|2B|97[1-6])\s*[-–]")
_NOMS = "(" + _alt(list(DEPARTEMENTS.values()) + ["Réunion"]) + ")"
RE_MARQUEUR = re.compile(r"(?:^| )(?<!sous )(?:" + "|".join(MARQUEURS) + r") " + _ARTICLE + _NOMS + " "
                         + r"| sous prefecture (?:du |de la |de l |des )" + _NOMS + " ")
_REG = {_n(k).strip(): v for k, v in REGIONS.items()}
_OM = {"guyane": "973", "martinique": "972", "mayotte": "976", "la reunion": "974", "reunion": "974", "guadeloupe": "971"}


def _dans(texte, titre=False):
    """(département, forme) trouvés dans un texte, ou (None, None)."""
    n = _n(texte)
    if RE_POLICE.search(n):
        return "75", "préfecture de police"
    m = RE_REGION.search(n)
    if m:
        return _REG[m.group(1)], "préfecture de région"
    m = RE_OUTREMER.search(n)
    if m:
        return _OM[m.group(1)], "collectivité d'outre-mer"
    for m in RE_SIGLE.finditer(texte or ""):
        code = m.group(2).upper()
        code = code.zfill(2) if code.isdigit() and len(code) < 2 else code
        if code in VALIDES:
            return code, "sigle et code"
    if titre:
        m = RE_CODE_TITRE.match((texte or "").strip())
        if m and m.group(1) in VALIDES:
            return m.group(1), "code en tête du titre"
    m = RE_MARQUEUR.search(n)
    if m:
        return _NOM[m.group(1) or m.group(2)], "marqueur et nom"
    return None, None


# Formes qui désignent un organisme avec son département (marqueur administratif ou sigle) : seules celles-ci, lues dans
# le titre, priment sur le département tiré de l'organisme porteur. Un code en tête du titre ne désigne pas d'organisme.
FORMES_ORGANISME = {"préfecture de police", "préfecture de région", "collectivité d'outre-mer", "sigle et code", "marqueur et nom"}


def deduire(organisme, titre):
    """Renvoie (département retenu, forme, source, autre département écarté s'il y a désaccord).

    D'abord l'organisme, puis le titre. En cas de désaccord, le titre prime quand il désigne explicitement un organisme
    avec son département (« CAF DE L'AIN » sous l'organisme porteur « CAF DU PAS DE CALAIS ») ; sinon l'organisme l'emporte."""
    d_org, f_org = _dans(organisme)
    d_tit, f_tit = _dans(titre, titre=True)
    if d_org and d_tit and d_tit != d_org:
        if f_tit in FORMES_ORGANISME:
            return d_tit, f_tit, "titre (prime sur l'organisme)", d_org
        return d_org, f_org, "organisme", d_tit
    if d_org:
        return d_org, f_org, "organisme", None
    if d_tit:
        return d_tit, f_tit, "titre", None
    return None, None, None, None
