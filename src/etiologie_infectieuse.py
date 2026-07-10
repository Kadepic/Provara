"""ÉTIOLOGIE DES MALADIES INFECTIEUSES COURANTES — CATALOGUE de faits MÉDICAUX ÉTABLIS, FAUX=0
(PARTIE V, B-FAIT ; à la manière de `classes_complexite.py`).

POSTURE FAUX=0 (la réalité juge, jamais un faux) :
  • Chaque maladie du catalogue a une étiologie NON CONTESTÉE : un AGENT causal NOMMÉ, un TYPE d'agent
    (bactérie / virus / parasite / champignon / prion), un MODE de transmission dominant, et le fait
    (2026) qu'un vaccin d'usage courant existe ou non. Ce sont des faits de manuel de microbiologie
    médicale (Koch, OMS, CDC), sourcés et certains.
  • On NE distingue JAMAIS l'AGENT (ce qui cause la maladie) du VECTEUR (ce qui la transmet) : le
    paludisme est causé par un PARASITE (Plasmodium), le moustique Anopheles n'en est que le vecteur.
    Confondre agent et vecteur est l'erreur classique — le catalogue nomme l'AGENT.
  • On EXCLUT toute maladie à étiologie contestée, multifactorielle ou non infectieuse (diabète,
    cancers non viraux, maladies auto-immunes…). Une telle entrée -> ValueError (abstention).
  • Toute entrée hors du catalogue (maladie inventée, non infectieuse, type d'agent inconnu, type
    invalide) -> ValueError (ABSTENTION STRUCTURELLE). Jamais une étiologie devinée.
  • Déterministe. Conservateur : abstention tolérée, faux POSITIF interdit.

Remarques de rigueur (établies) :
  - Paludisme : agent = Plasmodium (parasite protozoaire) ; vecteur = moustique Anopheles. L'agent
    n'est NI un virus NI le moustique.
  - Ulcère gastroduodénal : agent = Helicobacter pylori (bactérie) — PAS le stress (piège historique ;
    prix Nobel de médecine 2005, Marshall & Warren).
  - Tuberculose : bactérie Mycobacterium tuberculosis (bacille de Koch, 1882).
  - VIH/sida : aucun vaccin d'usage courant (fait, 2026). Rougeole : vaccin ROR.
  - Creutzfeldt-Jakob : agent = PRION (protéine mal repliée) — ni virus ni bactérie.

SOURCE = "microbiologie médicale de référence (postulats de Koch ; OMS/CDC ; Nobel 2005 H. pylori)"
"""
from __future__ import annotations

SOURCE = "microbiologie médicale de référence (postulats de Koch ; OMS/CDC ; Nobel 2005 H. pylori)"

# ── TYPES D'AGENT (libellés canoniques) ──────────────────────────────────────────────────────────────────────
BACTERIE = "bactérie"
VIRUS = "virus"
PARASITE = "parasite"
CHAMPIGNON = "champignon"
PRION = "prion"

_TYPES = frozenset({BACTERIE, VIRUS, PARASITE, CHAMPIGNON, PRION})
# forme normalisée (sans accent) -> libellé canonique, pour accepter « bacterie » comme « bactérie »
_TYPES_NORM = {"bacterie": BACTERIE, "virus": VIRUS, "parasite": PARASITE,
               "champignon": CHAMPIGNON, "prion": PRION}

# ── CATALOGUE DES MALADIES (étiologie établie, non contestée) ─────────────────────────────────────────────────
# Chaque valeur = (agent causal nommé, type d'agent, mode de transmission dominant, un vaccin d'usage existe-t-il).
_MALADIES = {
    "tuberculose":            ("Mycobacterium tuberculosis", BACTERIE,   "aérienne (aérosols)",          True),   # BCG
    "cholera":                ("Vibrio cholerae",            BACTERIE,   "féco-orale (eau souillée)",    True),   # vaccins oraux
    "paludisme":              ("Plasmodium falciparum",      PARASITE,   "vectorielle (moustique Anopheles)", True),  # RTS,S / R21
    "grippe":                 ("virus Influenza",            VIRUS,      "gouttelettes respiratoires",   True),
    "covid-19":               ("SARS-CoV-2",                 VIRUS,      "aérienne (aérosols/gouttelettes)", True),
    "rougeole":               ("virus de la rougeole",       VIRUS,      "aérienne (aérosols)",          True),   # ROR
    "vih/sida":               ("VIH",                        VIRUS,      "sexuelle / sanguine",          False),  # pas de vaccin (2026)
    "tetanos":                ("Clostridium tetani",         BACTERIE,   "plaie souillée (spores telluriques)", True),
    "rage":                   ("virus de la rage",           VIRUS,      "morsure animale (salive)",     True),
    "peste":                  ("Yersinia pestis",            BACTERIE,   "vectorielle (puce de rat)",    False),
    "typhoide":               ("Salmonella Typhi",           BACTERIE,   "féco-orale (eau/aliments)",    True),
    "coqueluche":             ("Bordetella pertussis",       BACTERIE,   "gouttelettes respiratoires",   True),
    "diphterie":              ("Corynebacterium diphtheriae", BACTERIE,  "gouttelettes respiratoires",   True),
    "syphilis":               ("Treponema pallidum",         BACTERIE,   "sexuelle",                     False),
    "maladie de lyme":        ("Borrelia burgdorferi",       BACTERIE,   "vectorielle (tique Ixodes)",   False),
    "toxoplasmose":           ("Toxoplasma gondii",          PARASITE,   "orale (oocystes / viande crue)", False),
    "candidose":              ("Candida albicans",           CHAMPIGNON, "opportuniste (flore endogène)", False),
    "ulcere gastroduodenal":  ("Helicobacter pylori",        BACTERIE,   "féco-orale / orale",           False),  # PAS le stress — Nobel 2005
    "hepatite b":             ("virus de l'hépatite B (VHB)", VIRUS,     "sanguine / sexuelle / périnatale", True),
    "creutzfeldt-jakob":      ("prion (PrP mal repliée)",    PRION,      "alimentaire / iatrogène",      False),
}

# Synonymes acceptés (même maladie, autre nom courant ; normalisation robuste aux accents/casse via _resout).
_ALIAS = {
    "tuberculose pulmonaire": "tuberculose",
    "bacille de koch": "tuberculose",
    "malaria": "paludisme",
    "influenza": "grippe",
    "covid": "covid-19",
    "covid19": "covid-19",
    "sars-cov-2": "covid-19",
    "sida": "vih/sida",
    "vih": "vih/sida",
    "lyme": "maladie de lyme",
    "borreliose de lyme": "maladie de lyme",
    "fievre typhoide": "typhoide",
    "ulcere": "ulcere gastroduodenal",
    "ulcere gastrique": "ulcere gastroduodenal",
    "hepatite virale b": "hepatite b",
    "vhb": "hepatite b",
    "mcj": "creutzfeldt-jakob",
    "creutzfeldt jakob": "creutzfeldt-jakob",
    "maladie de creutzfeldt-jakob": "creutzfeldt-jakob",
}


def _normalise(nom):
    """Minuscule, sans accents, espaces compactés — pour une clé stable. str non-bool exigé."""
    if not isinstance(nom, str) or isinstance(nom, bool):
        raise ValueError(f"nom de maladie invalide (str attendu) : {nom!r}")
    s = nom.strip().lower()
    if not s:
        raise ValueError("nom de maladie vide (abstention)")
    # translittération minimale des accents français (déterministe, sans dépendance)
    for a, b in (("à", "a"), ("â", "a"), ("ä", "a"),
                 ("é", "e"), ("è", "e"), ("ê", "e"), ("ë", "e"),
                 ("î", "i"), ("ï", "i"),
                 ("ô", "o"), ("ö", "o"),
                 ("ù", "u"), ("û", "u"), ("ü", "u"),
                 ("ç", "c")):
        s = s.replace(a, b)
    return " ".join(s.split())


def _resout(nom):
    """Normalise un nom de maladie vers une clé du catalogue ; ValueError si hors catalogue (abstention)."""
    cle = _normalise(nom)
    if cle in _MALADIES:
        return cle
    if cle in _ALIAS:
        return _ALIAS[cle]
    raise ValueError(f"maladie hors catalogue (abstention) : {nom!r}")


def _type_valide(t):
    if not isinstance(t, str) or isinstance(t, bool):
        raise ValueError(f"type d'agent invalide (str attendu) : {t!r}")
    cle = _normalise(t)
    if cle not in _TYPES_NORM:
        raise ValueError(f"type d'agent inconnu (abstention) : {t!r}")
    return _TYPES_NORM[cle]


# ── API ───────────────────────────────────────────────────────────────────────────────────────────────────────
def agent(maladie):
    """Agent causal NOMMÉ de la maladie (fait établi). Hors catalogue -> ValueError.

    C'est l'AGENT (ce qui cause la maladie), jamais le VECTEUR : paludisme -> 'Plasmodium falciparum',
    et non le moustique.
    """
    return _MALADIES[_resout(maladie)][0]


def type_agent(maladie):
    """Type de l'agent causal : 'bactérie', 'virus', 'parasite', 'champignon' ou 'prion'.

    Hors catalogue -> ValueError. Ex. : paludisme -> 'parasite' (jamais 'virus') ; Creutzfeldt-Jakob -> 'prion'.
    """
    return _MALADIES[_resout(maladie)][1]


def transmission(maladie):
    """Mode de transmission dominant (fait établi). Hors catalogue -> ValueError."""
    return _MALADIES[_resout(maladie)][2]


def vaccin_existe(maladie):
    """True ssi un vaccin d'usage courant existe (2026). Hors catalogue -> ValueError.

    Ex. : rougeole -> True (ROR) ; VIH/sida -> False (aucun vaccin homologué, 2026).
    """
    return _MALADIES[_resout(maladie)][3]


def maladies_par_agent(type_):
    """Liste TRIÉE des maladies du catalogue dont l'agent est du type donné.

    Type inconnu ou invalide -> ValueError. La liste est déterministe (ordre alphabétique des clés).
    """
    t = _type_valide(type_)
    return sorted(m for m, v in _MALADIES.items() if v[1] == t)


def catalogue():
    """Liste TRIÉE de toutes les maladies du catalogue (clés canoniques). Déterministe."""
    return sorted(_MALADIES.keys())
