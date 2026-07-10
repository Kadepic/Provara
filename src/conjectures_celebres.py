"""CONJECTURES CÉLÈBRES (statut : démontrée / réfutée / ouverte) — CATALOGUE de faits HISTORIQUES ÉTABLIS, FAUX=0
(sujet borné « conjecture de Poincaré (statut) », PARTIE I, B-FAIT ; à la manière de `classes_complexite.py`).

MÉCANISME : ce module n'est PAS un moteur de démonstration ; c'est un CATALOGUE CLOS de faits historiques
sur le statut des grandes conjectures mathématiques, tels qu'établis par la communauté mathématique :
  • DÉMONTRÉE  : une preuve publiée, vérifiée et acceptée existe (ex. Poincaré — Grigori Perelman, 2003,
    flot de Ricci avec chirurgie, prix du millénaire décerné par le Clay Mathematics Institute en 2010).
  • RÉFUTÉE    : un CONTRE-EXEMPLE ou une réfutation publiée et vérifiée existe (ex. Mertens — Odlyzko &
    te Riele, 1985 : |M(x)| ≤ √x est FAUSSE, contrairement à l'intuition répandue).
  • OUVERTE    : ni preuve ni réfutation acceptée à ce jour (Riemann, Goldbach, P vs NP, Collatz, …).
    Pour une conjecture OUVERTE, `auteur_preuve`/`annee_preuve` -> ValueError : on n'invente JAMAIS un
    auteur ni une date de preuve qui n'existent pas.

POSTURE FAUX=0 (la réalité historique juge, jamais un faux) :
  • Chaque entrée est un fait SOURCÉ (publication de référence citée dans le catalogue).
  • Conjecture HORS catalogue -> ValueError (ABSTENTION structurelle). Jamais un statut deviné.
  • Les alias sont EXPLICITES (« syracuse » -> Collatz) ; aucune correspondance floue.
  • `auteur_preuve`/`annee_preuve` d'une conjecture RÉFUTÉE renvoient l'auteur/l'année de la RÉFUTATION
    (le contre-exemple est la « preuve » du statut) — c'est dit, pas caché.
  • VÉRITÉ DATÉE : ces statuts sont ceux établis à la date de la source (2026) ; une conjecture « ouverte »
    peut être tranchée demain — le catalogue énonce l'état ÉTABLI, pas une prophétie.

GARANTIES (vérifiées en adverse par `valide_conjectures_celebres.py`) :
  - Poincaré = DÉMONTRÉE (Perelman, 2003) et c'est le SEUL des 7 problèmes du millénaire résolu à ce jour ;
  - Riemann, Goldbach, P vs NP, Collatz, premiers jumeaux, Hodge, BSD, Navier-Stokes, Yang-Mills = OUVERTES ;
  - Fermat = Wiles 1995 ; quatre couleurs = Appel & Haken 1976 ; Kepler = Hales 1998 (Flyspeck 2014) ;
  - Mertens et Euler (sommes de puissances) = RÉFUTÉES (jamais présentées comme vraies ou ouvertes) ;
  - AUCUNE conjecture ouverte n'expose d'auteur/année de preuve (ValueError systématique) ;
  - problemes_du_millenaire() = exactement 7 entrées, dont exactement 1 résolue ;
  - nom hors catalogue, nom non-str, bool, vide -> ValueError ; déterministe ; fonctions pures.

Toutes les fonctions sont PURES et déterministes ; le module n'importe que `unicodedata` (stdlib).
"""
from __future__ import annotations

import unicodedata

SOURCE = (
    "Perelman arXiv:math/0303109 (2003) + Clay Millennium Prize 2010 ; Wiles, Annals of Math. 141 (1995) ; "
    "Appel & Haken, Illinois J. Math. 21 (1977, annoncé 1976) ; Hales 1998 + Flyspeck (2014) ; "
    "Odlyzko & te Riele, J. reine angew. Math. 357 (1985) ; Lander & Parkin, Bull. AMS 72 (1966) ; "
    "Clay Mathematics Institute, liste des 7 problèmes du millénaire (2000)"
)

# ── STATUTS (libellés canoniques) ────────────────────────────────────────────────────────────────────────────
DEMONTREE = "demontree"
REFUTEE = "refutee"
OUVERTE = "ouverte"
_STATUTS = (DEMONTREE, REFUTEE, OUVERTE)

# ── CATALOGUE (clé canonique -> fait historique établi) ──────────────────────────────────────────────────────
# Champs : enonce, statut, auteur (None si ouverte), annee (None si ouverte), reference, millenaire (bool).
# Pour une conjecture RÉFUTÉE, auteur/annee = auteur/année de la RÉFUTATION (contre-exemple publié).
_CATALOGUE = {
    "poincare": {
        "enonce": "toute 3-variété close simplement connexe est homéomorphe à la 3-sphère",
        "statut": DEMONTREE,
        "auteur": "Grigori Perelman",
        "annee": 2003,
        "reference": "flot de Ricci avec chirurgie — arXiv:math/0211159, math/0303109, math/0307245 "
                     "(2002-2003) ; prix du millénaire Clay 2010 (décliné)",
        "millenaire": True,
    },
    "fermat": {
        "enonce": "aucun entier n > 2 n'admet de solution entière strictement positive à x^n + y^n = z^n",
        "statut": DEMONTREE,
        "auteur": "Andrew Wiles",
        "annee": 1995,
        "reference": "Wiles, « Modular elliptic curves and Fermat's Last Theorem », Annals of Mathematics "
                     "141 (1995) ; complété avec Taylor-Wiles",
        "millenaire": False,
    },
    "quatre_couleurs": {
        "enonce": "toute carte planaire est coloriable avec au plus 4 couleurs sans que deux régions "
                  "adjacentes partagent une couleur",
        "statut": DEMONTREE,
        "auteur": "Kenneth Appel et Wolfgang Haken",
        "annee": 1976,
        "reference": "preuve assistée par ordinateur (1976, publiée Illinois J. Math. 1977) ; "
                     "reformalisée par Gonthier en Coq (2005)",
        "millenaire": False,
    },
    "kepler": {
        "enonce": "aucun empilement de sphères identiques dans l'espace n'a une densité supérieure à "
                  "celle de l'empilement cubique à faces centrées (π/√18)",
        "statut": DEMONTREE,
        "auteur": "Thomas Hales",
        "annee": 1998,
        "reference": "Hales 1998 (preuve assistée par ordinateur, Annals of Math. 2005) ; "
                     "preuve FORMELLE achevée par le projet Flyspeck (2014)",
        "millenaire": False,
    },
    "riemann": {
        "enonce": "tous les zéros non triviaux de la fonction zêta de Riemann ont pour partie réelle 1/2",
        "statut": OUVERTE,
        "auteur": None,
        "annee": None,
        "reference": "Riemann 1859 ; problème du millénaire Clay (2000), non résolu",
        "millenaire": True,
    },
    "goldbach": {
        "enonce": "tout entier pair supérieur à 2 est la somme de deux nombres premiers",
        "statut": OUVERTE,
        "auteur": None,
        "annee": None,
        "reference": "Goldbach 1742 (lettre à Euler) ; vérifiée numériquement jusqu'à 4·10^18, non démontrée",
        "millenaire": False,
    },
    "p_vs_np": {
        "enonce": "P = NP ? — tout problème dont une solution se vérifie en temps polynomial se "
                  "résout-il en temps polynomial ?",
        "statut": OUVERTE,
        "auteur": None,
        "annee": None,
        "reference": "Cook 1971 / Levin ; problème du millénaire Clay (2000), non résolu",
        "millenaire": True,
    },
    "collatz": {
        "enonce": "la suite n -> n/2 (n pair) ; n -> 3n+1 (n impair) atteint 1 depuis tout entier "
                  "strictement positif",
        "statut": OUVERTE,
        "auteur": None,
        "annee": None,
        "reference": "Collatz ~1937 (dite de Syracuse) ; vérifiée numériquement très loin, non démontrée",
        "millenaire": False,
    },
    "premiers_jumeaux": {
        "enonce": "il existe une infinité de couples de nombres premiers (p, p+2)",
        "statut": OUVERTE,
        "auteur": None,
        "annee": None,
        "reference": "de Polignac 1849 (cas k=1) ; Zhang 2013 a borné l'écart (< 7·10^7, réduit à 246), "
                     "mais le cas 2 reste ouvert",
        "millenaire": False,
    },
    "hodge": {
        "enonce": "sur une variété projective complexe lisse, toute classe de Hodge est une combinaison "
                  "rationnelle de classes de cycles algébriques",
        "statut": OUVERTE,
        "auteur": None,
        "annee": None,
        "reference": "Hodge 1950 ; problème du millénaire Clay (2000), non résolu",
        "millenaire": True,
    },
    "birch_swinnerton_dyer": {
        "enonce": "le rang du groupe des points rationnels d'une courbe elliptique égale l'ordre "
                  "d'annulation de sa fonction L en s = 1",
        "statut": OUVERTE,
        "auteur": None,
        "annee": None,
        "reference": "Birch & Swinnerton-Dyer années 1960 ; problème du millénaire Clay (2000), non résolu",
        "millenaire": True,
    },
    "navier_stokes": {
        "enonce": "existence et régularité globales des solutions des équations de Navier-Stokes en "
                  "dimension 3",
        "statut": OUVERTE,
        "auteur": None,
        "annee": None,
        "reference": "problème du millénaire Clay (2000), non résolu",
        "millenaire": True,
    },
    "yang_mills": {
        "enonce": "existence d'une théorie de Yang-Mills quantique sur R^4 avec un trou de masse "
                  "(mass gap) strictement positif",
        "statut": OUVERTE,
        "auteur": None,
        "annee": None,
        "reference": "problème du millénaire Clay (2000), non résolu",
        "millenaire": True,
    },
    "mertens": {
        "enonce": "|M(x)| ≤ √x pour tout x > 1, où M est la fonction de Mertens (somme de la fonction "
                  "de Möbius) — elle aurait impliqué l'hypothèse de Riemann",
        "statut": REFUTEE,
        "auteur": "Andrew Odlyzko et Herman te Riele",
        "annee": 1985,
        "reference": "Odlyzko & te Riele, « Disproof of the Mertens conjecture », J. reine angew. Math. "
                     "357 (1985) — réfutation indirecte, sans contre-exemple explicite connu",
        "millenaire": False,
    },
    "euler_puissances": {
        "enonce": "pour n > 2, il faut au moins n puissances n-ièmes pour sommer une puissance n-ième "
                  "(généralisation de Fermat par Euler)",
        "statut": REFUTEE,
        "auteur": "Leon Lander et Thomas Parkin",
        "annee": 1966,
        "reference": "Lander & Parkin, Bull. AMS 72 (1966) : contre-exemple "
                     "27^5 + 84^5 + 110^5 + 133^5 = 144^5",
        "millenaire": False,
    },
}

# ── ALIAS EXPLICITES (après normalisation) — aucune correspondance floue ─────────────────────────────────────
_ALIAS = {
    "conjecture de poincare": "poincare",
    "dernier theoreme de fermat": "fermat",
    "grand theoreme de fermat": "fermat",
    "theoreme des quatre couleurs": "quatre_couleurs",
    "quatre couleurs": "quatre_couleurs",
    "4 couleurs": "quatre_couleurs",
    "conjecture de kepler": "kepler",
    "hypothese de riemann": "riemann",
    "conjecture de goldbach": "goldbach",
    "p vs np": "p_vs_np",
    "p contre np": "p_vs_np",
    "p=np": "p_vs_np",
    "p = np": "p_vs_np",
    "pvsnp": "p_vs_np",
    "conjecture de collatz": "collatz",
    "syracuse": "collatz",
    "conjecture de syracuse": "collatz",
    "3n+1": "collatz",
    "nombres premiers jumeaux": "premiers_jumeaux",
    "conjecture des nombres premiers jumeaux": "premiers_jumeaux",
    "jumeaux": "premiers_jumeaux",
    "conjecture de hodge": "hodge",
    "birch et swinnerton-dyer": "birch_swinnerton_dyer",
    "birch et swinnerton dyer": "birch_swinnerton_dyer",
    "bsd": "birch_swinnerton_dyer",
    "navier-stokes": "navier_stokes",
    "navier stokes": "navier_stokes",
    "existence et regularite de navier-stokes": "navier_stokes",
    "yang-mills": "yang_mills",
    "yang mills": "yang_mills",
    "yang-mills et trou de masse": "yang_mills",
    "conjecture de mertens": "mertens",
    "conjecture d'euler": "euler_puissances",
    "conjecture d'euler sur les puissances": "euler_puissances",
    "euler sommes de puissances": "euler_puissances",
}


def _normalise(nom: str) -> str:
    """Normalisation DÉTERMINISTE : accents retirés (NFD), minuscules, séparateurs unifiés en espaces."""
    decompose = unicodedata.normalize("NFD", nom)
    sans_accent = "".join(c for c in decompose if unicodedata.category(c) != "Mn")
    bas = sans_accent.lower().replace("_", " ").replace("’", "'")
    return " ".join(bas.split())


def _entree(nom):
    """Résout un nom vers son entrée de catalogue, ou ValueError (abstention) si hors catalogue."""
    if not isinstance(nom, str) or isinstance(nom, bool):
        raise ValueError("nom invalide : une chaîne de caractères non vide est requise")
    cle = _normalise(nom)
    if not cle:
        raise ValueError("nom invalide : une chaîne de caractères non vide est requise")
    cle_soulignee = cle.replace(" ", "_").replace("-", "_")
    if cle_soulignee in _CATALOGUE:
        return cle_soulignee, _CATALOGUE[cle_soulignee]
    if cle in _ALIAS:
        canon = _ALIAS[cle]
        return canon, _CATALOGUE[canon]
    raise ValueError(f"conjecture hors catalogue : {nom!r} (abstention — aucun statut inventé)")


# ── API ──────────────────────────────────────────────────────────────────────────────────────────────────────
def statut(nom: str) -> str:
    """Statut historique établi : 'demontree' | 'refutee' | 'ouverte'. Hors catalogue -> ValueError."""
    _, e = _entree(nom)
    return e["statut"]


def demontree(nom: str) -> bool:
    """True ssi la conjecture est DÉMONTRÉE (preuve publiée et acceptée). Hors catalogue -> ValueError."""
    return statut(nom) == DEMONTREE


def refutee(nom: str) -> bool:
    """True ssi la conjecture est RÉFUTÉE (contre-exemple/réfutation publiée). Hors catalogue -> ValueError."""
    return statut(nom) == REFUTEE


def ouverte(nom: str) -> bool:
    """True ssi la conjecture est OUVERTE (ni preuve ni réfutation acceptée). Hors catalogue -> ValueError."""
    return statut(nom) == OUVERTE


def auteur_preuve(nom: str) -> str:
    """Auteur de la preuve (ou de la RÉFUTATION si statut 'refutee').

    Conjecture OUVERTE -> ValueError : aucun auteur n'existe, on n'en invente JAMAIS un."""
    _, e = _entree(nom)
    if e["statut"] == OUVERTE:
        raise ValueError(f"conjecture OUVERTE : {nom!r} n'a pas de preuve, donc pas d'auteur de preuve "
                         "(abstention — jamais un auteur inventé)")
    return e["auteur"]


def annee_preuve(nom: str) -> int:
    """Année de la preuve (ou de la RÉFUTATION si statut 'refutee').

    Conjecture OUVERTE -> ValueError : aucune preuve n'existe, on n'invente JAMAIS une date."""
    _, e = _entree(nom)
    if e["statut"] == OUVERTE:
        raise ValueError(f"conjecture OUVERTE : {nom!r} n'a pas de preuve, donc pas d'année de preuve "
                         "(abstention — jamais une date inventée)")
    return e["annee"]


def enonce(nom: str) -> str:
    """Énoncé canonique de la conjecture. Hors catalogue -> ValueError."""
    _, e = _entree(nom)
    return e["enonce"]


def reference(nom: str) -> str:
    """Référence bibliographique/source du statut. Hors catalogue -> ValueError."""
    _, e = _entree(nom)
    return e["reference"]


def catalogue() -> tuple:
    """Tuple TRIÉ des noms canoniques du catalogue (immutable : le catalogue interne est protégé)."""
    return tuple(sorted(_CATALOGUE))


def problemes_du_millenaire() -> tuple:
    """Les 7 problèmes du prix du millénaire (Clay Mathematics Institute, 2000), noms canoniques triés.

    Fait établi : UN SEUL est résolu à ce jour — la conjecture de Poincaré (Perelman, 2003)."""
    return tuple(sorted(c for c, e in _CATALOGUE.items() if e["millenaire"]))
