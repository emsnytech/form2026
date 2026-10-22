"""Retire des e-mails et numéros de téléphone qui apparaissent par erreur dans les titres de démarches, noms
d'organisme ou noms de service (saisie libre par l'émetteur). Mêmes motifs et mêmes libellés que FORM 2026
(donnees/gains/LISEZMOI_gains.md). Lancer ce fichier seul exécute les tests ci-dessous."""
import re

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?<!\d)(?:\+33\s?|0)[1-9](?:[\s.\-]?\d{2}){4}(?!\d)")
# motifs « entourés » : les mêmes adresses/numéros, mais avec leurs délimiteurs d'origine ([...] ou (...))
# absorbés dans le remplacement, pour éviter un doublement des crochets (même correctif que
# update_demarches_catalog.py, 2026-10-11) ; appliqués avant les motifs bruts.
EMAIL_DELIM_RE = re.compile(r"[\[(]\s*" + EMAIL_RE.pattern + r"\s*[\])]")
PHONE_DELIM_RE = re.compile(r"[\[(]\s*" + PHONE_RE.pattern + r"\s*[\])]")


def nettoyer(texte):
    if not texte:
        return texte
    texte = EMAIL_DELIM_RE.sub("[adresse électronique retirée]", texte)
    texte = PHONE_DELIM_RE.sub("[numéro de téléphone retiré]", texte)
    texte = EMAIL_RE.sub("[adresse électronique retirée]", texte)
    texte = PHONE_RE.sub("[numéro de téléphone retiré]", texte)
    return texte


TESTS = [
    ("Fiche Infirmerie Lycée - 2024/2025 [infirmerie@leparcimperial.fr]",
     "Fiche Infirmerie Lycée - 2024/2025 [adresse électronique retirée]"),
    ("Contactez le 01 23 45 67 89 pour toute question",
     "Contactez le [numéro de téléphone retiré] pour toute question"),
    ("SIRET 13000961600017", "SIRET 13000961600017"),
    ("Année scolaire 2025-2026", "Année scolaire 2025-2026"),
    ("Service scolarité (01 23 45 67 89)", "Service scolarité [numéro de téléphone retiré]"),
    ("Contact : jean.dupont@ac-paris.fr", "Contact : [adresse électronique retirée]"),
]

if __name__ == "__main__":
    for entree, attendu in TESTS:
        obtenu = nettoyer(entree)
        assert obtenu == attendu, f"ECHEC : {entree!r} -> {obtenu!r} (attendu {attendu!r})"
        print(f"OK : {entree!r} -> {obtenu!r}")
    print(f"--selftest : {len(TESTS)}/{len(TESTS)} cas OK")
