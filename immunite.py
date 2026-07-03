"""
IMMUNITÉ / VACCINS — MÉCANISME BORNÉ (sujet « Vaccins (mécanisme) »).

Domaine BORNÉ : l'épidémiologie de l'immunité de groupe repose sur des IDENTITÉS EXACTES (le seuil critique de
vaccination et le taux de reproduction effectif découlent algébriquement du nombre de reproduction de base R0), et la
TYPOLOGIE de l'immunité (active naturelle / active artificielle / passive) est un fait établi d'immunologie.

CE QUI EST BORNÉ (sound) :
  • Le MÉCANISME (les formules) est EXACT — garantie structurelle, pas une donnée mesurée :
      seuil_immunite_groupe(R0)        = 1 − 1/R0    (fraction critique à immuniser pour éteindre l'épidémie) ;
      taux_reproduction_effectif(R0,f) = R0·(1 − f)  (Reff ; l'épidémie s'éteint quand Reff < 1, i.e. f > seuil).
  • La TYPOLOGIE est une DONNÉE SOURCÉE (immunologie classique, cf. genetique/chimie : mécanisme garanti, contenu sourcé).

POSTURE FAUX=0 (vérifiée en adverse par valide_immunite.py) — abstention, JAMAIS un faux :
  - R0 ≤ 1 (pas d'épidémie / seuil non défini)            -> ValueError ;
  - fraction immunisée hors [0, 1]                         -> ValueError ;
  - entrée non numérique / booléen / NaN / infinie         -> ValueError ;
  - nom de type d'immunité inconnu (hors référentiel)      -> ValueError ;
  - déterministe ; conservateur (on abstient plutôt que de risquer un faux).
"""
from __future__ import annotations

import math
import unicodedata

SOURCE = "épidémiologie de l'immunité de groupe (R0) + typologie immunologique classique (active/passive)"

# Les trois types d'immunité (référentiel fermé).
ACTIVE_NATURELLE = "active_naturelle"      # le sujet fabrique ses propres anticorps après une infection naturelle.
ACTIVE_ARTIFICIELLE = "active_artificielle"  # le sujet fabrique ses propres anticorps après une vaccination.
PASSIVE = "passive"                         # anticorps préformés transmis (maternels, sérum) ; non fabriqués par le sujet.


def _est_reel(x) -> bool:
    """True ssi x est un réel exploitable (pas un booléen, pas NaN, pas ±inf)."""
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _exige_R0(R0):
    """R0 doit être réel et > 1 (épidémie effective) ; sinon ValueError (abstention)."""
    if not _est_reel(R0):
        raise ValueError(f"R0 invalide : {R0!r} (réel attendu)")
    if R0 <= 1:
        raise ValueError(f"R0={R0} ≤ 1 : pas d'épidémie, seuil non défini (abstention)")
    return float(R0)


def _exige_fraction(f):
    """Fraction immunisée dans [0, 1] ; sinon ValueError (abstention)."""
    if not _est_reel(f):
        raise ValueError(f"fraction invalide : {f!r} (réel attendu)")
    if not (0.0 <= f <= 1.0):
        raise ValueError(f"fraction={f} hors [0, 1] (abstention)")
    return float(f)


def seuil_immunite_groupe(R0) -> float:
    """Seuil critique d'immunité de groupe : fraction de la population à immuniser pour stopper l'épidémie.

    Formule EXACTE : 1 − 1/R0. Exige R0 > 1 (sinon ValueError). Ex. : rougeole R0=15 -> ≈0.9333 ; R0=2 -> 0.5.
    """
    r0 = _exige_R0(R0)
    return 1.0 - 1.0 / r0


def taux_reproduction_effectif(R0, fraction_immunisee) -> float:
    """Taux de reproduction EFFECTIF en présence d'une fraction immunisée f : Reff = R0·(1 − f).

    Formule EXACTE. Exige R0 > 1 et f ∈ [0, 1] (sinon ValueError). L'épidémie s'éteint ssi Reff < 1 (i.e. f > seuil).
    """
    r0 = _exige_R0(R0)
    f = _exige_fraction(fraction_immunisee)
    return r0 * (1.0 - f)


def epidemie_eteinte(R0, fraction_immunisee) -> bool:
    """True ssi l'épidémie s'éteint avec la fraction immunisée donnée (Reff = R0·(1−f) < 1).

    Équivaut exactement à fraction_immunisee > seuil_immunite_groupe(R0). Mêmes gardes (ValueError) que ci-dessus.
    """
    return taux_reproduction_effectif(R0, fraction_immunisee) < 1.0


# ── TYPOLOGIE DE L'IMMUNITÉ (référentiel fermé, fait sourcé) ────────────────────────────────────────────────────
# Chaque clé est une SOURCE/voie d'acquisition d'immunité ; la valeur est son type immunologique établi.
#   active = le sujet fabrique LUI-MÊME ses anticorps (naturelle=infection / artificielle=vaccin) ;
#   passive = anticorps PRÉFORMÉS transmis au sujet (maternels ou sérum) — le sujet ne les fabrique pas.
# Distinction adverse soignée : anatoxine/toxoïde (vaccin -> ACTIVE artificielle) vs antitoxine/sérum (-> PASSIVE).
_TYPES = {
    # — ACTIVE NATURELLE (infection naturelle) —
    "infection": ACTIVE_NATURELLE,
    "infection_naturelle": ACTIVE_NATURELLE,
    "maladie": ACTIVE_NATURELLE,
    "contact_naturel": ACTIVE_NATURELLE,
    "immunite_post_infectieuse": ACTIVE_NATURELLE,
    # — ACTIVE ARTIFICIELLE (vaccination : le sujet fabrique ses anticorps après stimulation vaccinale) —
    "vaccin": ACTIVE_ARTIFICIELLE,
    "vaccination": ACTIVE_ARTIFICIELLE,
    "vaccin_vivant_attenue": ACTIVE_ARTIFICIELLE,
    "vaccin_attenue": ACTIVE_ARTIFICIELLE,
    "vaccin_inactive": ACTIVE_ARTIFICIELLE,
    "vaccin_arnm": ACTIVE_ARTIFICIELLE,
    "vaccin_arn": ACTIVE_ARTIFICIELLE,
    "vaccin_a_vecteur_viral": ACTIVE_ARTIFICIELLE,
    "vaccin_sous_unitaire": ACTIVE_ARTIFICIELLE,
    "vaccin_conjugue": ACTIVE_ARTIFICIELLE,
    "vaccin_polyosidique": ACTIVE_ARTIFICIELLE,
    "anatoxine": ACTIVE_ARTIFICIELLE,   # toxine inactivée (toxoïde) -> le sujet fabrique ses anticorps : ACTIVE.
    "toxoide": ACTIVE_ARTIFICIELLE,
    # — PASSIVE (anticorps préformés transmis) —
    "anticorps_maternels": PASSIVE,
    "immunite_maternelle": PASSIVE,
    "transplacentaire": PASSIVE,
    "placentaire": PASSIVE,
    "allaitement": PASSIVE,
    "lait_maternel": PASSIVE,
    "colostrum": PASSIVE,
    "serotherapie": PASSIVE,
    "serum": PASSIVE,
    "immunoglobulines": PASSIVE,
    "gammaglobulines": PASSIVE,
    "antitoxine": PASSIVE,              # sérum d'anticorps préformés contre une toxine -> PASSIVE (≠ anatoxine).
    "anticorps_monoclonaux": PASSIVE,
}


def _normalise(nom) -> str:
    """Normalise un nom : minuscules, sans accents, espaces/tirets/apostrophes -> '_'. ValueError si non-chaîne/vide."""
    if not isinstance(nom, str):
        raise ValueError(f"nom de type d'immunité invalide : {nom!r} (chaîne attendue)")
    s = unicodedata.normalize("NFKD", nom.strip().lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    for sep in (" ", "-", "'", "’"):
        s = s.replace(sep, "_")
    while "__" in s:
        s = s.replace("__", "_")
    s = s.strip("_")
    if not s:
        raise ValueError("nom de type d'immunité vide (abstention)")
    return s


def type_immunite(nom) -> str:
    """Type d'immunité pour une voie d'acquisition donnée -> 'active_naturelle' | 'active_artificielle' | 'passive'.

    Référentiel FERMÉ : nom inconnu / hors catalogue -> ValueError (abstention, jamais une devinette).
    Ex. : 'infection' -> active_naturelle ; 'vaccin' -> active_artificielle ; 'anticorps maternels' -> passive.
    """
    cle = _normalise(nom)
    if cle not in _TYPES:
        raise ValueError(f"voie d'immunité inconnue : {nom!r} (hors référentiel, abstention)")
    return _TYPES[cle]
