"""Retire des e-mails et numéros de téléphone qui apparaissent par erreur dans les titres de démarches, noms
d'organisme ou noms de service (saisie libre par l'émetteur). Mêmes motifs et mêmes libellés que FORM 2026
(donnees/gains/LISEZMOI_gains.md). Lancer ce fichier seul exécute les tests ci-dessous — données fictives,
domaine .invalid (réservé, RFC 2606, ne peut être délivré à personne) et tranche 01 99 00 xx xx (réservée par
l'Arcep aux numéros fictifs) ; aucune adresse réelle dans ce fichier —, puis un contrôle de non-régression sur
la sortie réelle la plus récente, s'il y en a une, sans jamais écrire l'adresse retirée."""
import json, os, re

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
    ("Fiche Infirmerie Lycée - 2024/2025 [contact@exemple.invalid]",
     "Fiche Infirmerie Lycée - 2024/2025 [adresse électronique retirée]"),
    ("Contactez le 01 99 00 00 00 pour toute question",
     "Contactez le [numéro de téléphone retiré] pour toute question"),
    ("SIRET 13000961600017", "SIRET 13000961600017"),
    ("Année scolaire 2025-2026", "Année scolaire 2025-2026"),
    ("Service scolarité (01 99 00 00 00)", "Service scolarité [numéro de téléphone retiré]"),
    ("Contact : jean.dupont@exemple.invalid", "Contact : [adresse électronique retirée]"),
]

# Non-régression sur le cas réel qui a motivé ce script (démarche n° 97215, lycée du Parc Impérial) : on vérifie
# seulement que la forme nettoyée attendue est bien présente dans la dernière sortie régénérée — jamais l'adresse
# elle-même, qui ne figure nulle part dans ce fichier. Contrôle silencieux (ignoré) si la sortie n'existe pas encore.
NON_REGRESSION = [
    ("out/education_etablissements.json", 97215, "Fiche Infirmerie Lycée - 2024/2025 [adresse électronique retirée]"),
]

if __name__ == "__main__":
    for entree, attendu in TESTS:
        obtenu = nettoyer(entree)
        assert obtenu == attendu, f"ECHEC : {entree!r} -> {obtenu!r} (attendu {attendu!r})"
        print(f"OK : {entree!r} -> {obtenu!r}")
    print(f"--selftest : {len(TESTS)}/{len(TESTS)} cas OK")

    ici = os.path.dirname(os.path.abspath(__file__))
    for rel, numero, titre_attendu in NON_REGRESSION:
        chemin = os.path.join(ici, "..", rel)
        if not os.path.exists(chemin):
            print(f"-- non-régression : {rel} absent, contrôle ignoré")
            continue
        data = json.load(open(chemin, encoding="utf-8"))
        trouve = json.dumps(data, ensure_ascii=False).find(f'"num": {numero}')
        assert trouve != -1, f"ECHEC non-régression : démarche {numero} absente de {rel}"
        bloc = json.dumps(data, ensure_ascii=False)[trouve:trouve + 300]
        assert titre_attendu in bloc, f"ECHEC non-régression : forme attendue absente pour la démarche {numero} dans {rel}"
        print(f"OK non-régression : démarche {numero} dans {rel} a bien la forme nettoyée attendue")
