"""
CLASSIFICATION DES ROCHES — pétrologie génétique (PARTIE IV, B-CONV).

ATTENTION : `mineraux.py` traite l'échelle de Mohs (dureté des MINÉRAUX) ; ici il s'agit des ROCHES,
c'est-à-dire d'agrégats classés par leur MODE DE FORMATION (critère GÉNÉTIQUE, pas l'apparence) :
  • MAGMATIQUE (ignée)    : refroidissement et solidification d'un magma.
      – plutonique  : refroidissement LENT en profondeur  -> cristaux visibles (granite, gabbro) ;
      – volcanique  : refroidissement RAPIDE en surface   -> texture microlithique ou vitreuse
                      (basalte, rhyolite, andésite, obsidienne = verre, pierre ponce).
      Granite et basalte peuvent partager une chimie proche : c'est la TEXTURE (vitesse de
      refroidissement) qui les sépare — ancre discriminante du mécanisme.
  • SÉDIMENTAIRE          : dépôt de sédiments puis diagenèse (compaction/cimentation).
      – détritique  : débris d'autres roches (grès, argilite, conglomérat) ;
      – chimique    : précipitation à partir d'une solution (sel gemme, gypse) ;
      – biochimique : accumulation de restes d'organismes (calcaire, charbon).
  • MÉTAMORPHIQUE         : transformation À L'ÉTAT SOLIDE d'une roche préexistante (le PROTOLITHE)
    sous pression et/ou température, SANS fusion complète.
      – foliée      : minéraux orientés en plans (ardoise, schiste, gneiss) ;
      – non foliée  : sans plans (marbre, quartzite).
      Protolithes classiques : marbre <- calcaire ; quartzite <- grès ; ardoise <- argilite ;
      amphibolite <- basalte (méta-basite).

Posture FAUX=0 (un fait vérifié ou une abstention, JAMAIS une devinette) :
  • roche hors catalogue -> ValueError (on ne classe pas ce qu'on ne connaît pas) ;
  • protolithe d'une roche NON métamorphique -> ValueError (la question est mal posée) ;
  • protolithe AMBIGU (schiste : pélite OU basalte selon le faciès ; gneiss : orthogneiss issu de
    granite OU paragneiss issu de sédiments) -> ValueError explicite : on S'ABSTIENT plutôt que de
    choisir arbitrairement une origine — le faux négatif est toléré, le faux positif interdit ;
  • foliation AMBIGUË (amphibolite : faiblement foliée à non foliée selon les auteurs)
    -> ValueError explicite pour sous_type('amphibolite') ;
  • entrée non-str (bool, int, float, None, listes) -> ValueError ; minéral (quartz…) ≠ roche -> ValueError.

GARANTIES (vérifiées en adverse par `valide_classification_roches.py`) :
  - granite = magmatique PLUTONIQUE et basalte = magmatique VOLCANIQUE (ancre discriminante) ;
  - marbre/quartzite/ardoise/amphibolite -> protolithes calcaire/grès/argilite/basalte ;
  - calcaire = sédimentaire biochimique (PAS métamorphique) ; obsidienne = volcanique (verre) ;
  - protolithe('granite') -> ValueError ; hors-catalogue -> ValueError ; types invalides -> ValueError ;
  - déterministe ; catalogue fermé (closed-set) ; abstention structurelle au moindre doute.

Toutes les fonctions sont PURES et déterministes ; stdlib uniquement (aucun import externe).
"""
from __future__ import annotations

SOURCE = (
    "classification génétique des roches (pétrologie classique : Foucault & Raoult, "
    "Dictionnaire de géologie ; cycle des roches, manuels de géologie générale)"
)

# Familles (le critère est le MODE DE FORMATION).
MAGMATIQUE = "magmatique"
SEDIMENTAIRE = "sédimentaire"
METAMORPHIQUE = "métamorphique"

# Origine (mécanisme de formation) par famille — le critère génétique lui-même.
_ORIGINES = {
    MAGMATIQUE: "refroidissement et solidification d'un magma",
    SEDIMENTAIRE: "dépôt de sédiments puis diagenèse (compaction/cimentation)",
    METAMORPHIQUE: "transformation à l'état solide d'une roche préexistante sous pression/température",
}

# Sentinelle : sous-type ou protolithe AMBIGU dans la littérature -> abstention structurelle.
_AMBIGU = object()

# Catalogue FERMÉ : roche -> (famille, sous_type, protolithe).
#   protolithe : None pour les roches non métamorphiques (question mal posée),
#                _AMBIGU quand la littérature admet plusieurs protolithes (abstention),
#                sinon le nom de la roche d'origine.
_CATALOGUE = {
    # ── MAGMATIQUES (refroidissement d'un magma) ──
    "granite": (MAGMATIQUE, "plutonique", None),       # lent, en profondeur, gros cristaux
    "gabbro": (MAGMATIQUE, "plutonique", None),        # équivalent plutonique du basalte
    "basalte": (MAGMATIQUE, "volcanique", None),       # rapide, en surface, microlithique
    "rhyolite": (MAGMATIQUE, "volcanique", None),      # équivalent volcanique du granite
    "andésite": (MAGMATIQUE, "volcanique", None),
    "obsidienne": (MAGMATIQUE, "volcanique", None),    # verre volcanique (trempe)
    "pierre ponce": (MAGMATIQUE, "volcanique", None),  # verre volcanique vésiculé
    # ── SÉDIMENTAIRES (dépôt + diagenèse) ──
    "grès": (SEDIMENTAIRE, "détritique", None),        # sables cimentés
    "argilite": (SEDIMENTAIRE, "détritique", None),    # argiles compactées
    "conglomérat": (SEDIMENTAIRE, "détritique", None),  # galets cimentés
    "calcaire": (SEDIMENTAIRE, "biochimique", None),   # accumulation de restes calcaires
    "charbon": (SEDIMENTAIRE, "biochimique", None),    # accumulation de végétaux
    "sel gemme": (SEDIMENTAIRE, "chimique", None),     # évaporite (halite)
    "gypse": (SEDIMENTAIRE, "chimique", None),         # évaporite
    # ── MÉTAMORPHIQUES (transformation à l'état solide) ──
    "marbre": (METAMORPHIQUE, "non foliée", "calcaire"),
    "quartzite": (METAMORPHIQUE, "non foliée", "grès"),
    "ardoise": (METAMORPHIQUE, "foliée", "argilite"),
    "schiste": (METAMORPHIQUE, "foliée", _AMBIGU),     # pélite OU basalte (schiste vert) -> abstention
    "gneiss": (METAMORPHIQUE, "foliée", _AMBIGU),      # orthogneiss (granite) OU paragneiss -> abstention
    "amphibolite": (METAMORPHIQUE, _AMBIGU, "basalte"),  # foliation variable selon les auteurs
}

# Alias orthographiques STRICTS (graphies sans accent) — pas de correspondance floue.
_ALIAS = {
    "gres": "grès",
    "conglomerat": "conglomérat",
    "andesite": "andésite",
    "metamorphique": None,  # jamais une roche
    "sedimentaire": None,
}


def _exige_roche(roche) -> str:
    """Normalise et vérifie l'appartenance au catalogue fermé ; sinon ValueError (abstention)."""
    if not isinstance(roche, str):
        raise ValueError("roche invalide : un nom de roche (str) est requis")
    nom = " ".join(roche.strip().lower().split())
    nom = _ALIAS.get(nom, nom) or nom
    if nom not in _CATALOGUE:
        raise ValueError(
            f"roche inconnue du catalogue : {roche!r} (closed-set FAUX=0 : on ne classe pas au-delà du connu)"
        )
    return nom


# ── FAMILLE ────────────────────────────────────────────────────────────────────────────────────────────────────
def famille(roche: str) -> str:
    """Famille génétique : 'magmatique' | 'sédimentaire' | 'métamorphique'. Hors catalogue -> ValueError."""
    return _CATALOGUE[_exige_roche(roche)][0]


# ── ORIGINE (le mode de formation, critère génétique) ─────────────────────────────────────────────────────────
def origine(roche: str) -> str:
    """Mode de formation de la roche (le critère génétique de sa famille). Hors catalogue -> ValueError."""
    return _ORIGINES[_CATALOGUE[_exige_roche(roche)][0]]


# ── SOUS-TYPE ──────────────────────────────────────────────────────────────────────────────────────────────────
def sous_type(roche: str) -> str:
    """Sous-type au sein de la famille :
      magmatique -> 'plutonique' (lent, profondeur) | 'volcanique' (rapide, surface) ;
      sédimentaire -> 'détritique' | 'chimique' | 'biochimique' ;
      métamorphique -> 'foliée' | 'non foliée'.
    Foliation AMBIGUË dans la littérature (amphibolite) -> ValueError (abstention, jamais un choix arbitraire)."""
    nom = _exige_roche(roche)
    st = _CATALOGUE[nom][1]
    if st is _AMBIGU:
        raise ValueError(
            f"sous-type ambigu pour {nom!r} : la littérature diverge (abstention FAUX=0)"
        )
    return st


# ── PROTOLITHE ─────────────────────────────────────────────────────────────────────────────────────────────────
def protolithe(roche_metamorphique: str) -> str:
    """Roche d'origine d'une roche MÉTAMORPHIQUE (marbre <- calcaire, quartzite <- grès, ardoise <- argilite,
    amphibolite <- basalte). Non métamorphique -> ValueError ; protolithe ambigu (schiste, gneiss) -> ValueError."""
    nom = _exige_roche(roche_metamorphique)
    fam, _, proto = _CATALOGUE[nom]
    if fam != METAMORPHIQUE:
        raise ValueError(
            f"{nom!r} n'est pas métamorphique ({fam}) : la notion de protolithe ne s'applique pas"
        )
    if proto is _AMBIGU:
        raise ValueError(
            f"protolithe ambigu pour {nom!r} : plusieurs roches d'origine possibles (abstention FAUX=0)"
        )
    return proto


# ── CATALOGUE ──────────────────────────────────────────────────────────────────────────────────────────────────
def catalogue() -> tuple:
    """Tuple trié des roches connues (closed-set : tout le reste est une abstention)."""
    return tuple(sorted(_CATALOGUE))
