"""
ASTÉROÏDES & COMÈTES — paramètre de Tisserand (invariant orbital) et classification dynamique EXACTE.

Posture FAUX=0 (même esprit que `physique` / `chimie`) :
  • Le MÉCANISME est une LOI exacte et établie. Le paramètre de Tisserand par rapport à Jupiter
        T_J = aJ/a + 2·cos(i)·√( (a/aJ)·(1−e²) )
    est un quasi-invariant des rencontres gravitationnelles à trois corps (problème circulaire restreint).
    Il sert depuis Tisserand (1896) à distinguer dynamiquement astéroïdes et comètes.
  • La CONSTANTE aJ = 5.204 UA (demi-grand axe de Jupiter) est une DONNÉE SOURCÉE.
  • La CLASSIFICATION par seuils est la convention établie (Levison 1996 ; Vaghi/Kresák) :
        T_J > 3            -> objet de type ASTÉROÏDE (découplé de Jupiter) ;
        2 < T_J < 3        -> COMÈTE de la FAMILLE de JUPITER (JFC) ;
        T_J < 2            -> COMÈTE QUASI-ISOTROPE (type Halley / longue période).

GARANTIES (vérifiées en adverse par `valide_asteroides.py`) :
  - entrée non numérique / non finie -> ValueError (jamais un faux) ;
  - a ≤ 0, e < 0, ou e ≥ 1 (orbite non elliptique : parabolique/hyperbolique) -> ValueError ;
  - aJ ≤ 0 -> ValueError ;
  - frontière exacte T = 2 ou T = 3 : classification ambiguë -> ValueError (abstention, jamais un faux) ;
  - fonctions pures, déterministes ; conservateur (abstention tolérée, faux POSITIF interdit).

Validation physique (anchors hors-module, littérature) :
  - 1P/Halley (a=17.8, e=0.967, i=162°)  -> T_J ≈ -0.60  -> comète quasi-isotrope ;
  - 67P/Churyumov-Gerasimenko (a=3.46, e=0.641, i=7.04°) -> T_J ≈ 2.75 -> comète famille de Jupiter ;
  - astéroïde de la ceinture (a=2.7, e=0.1, i=5°) -> T_J ≈ 3.36 -> astéroïde.
"""
from __future__ import annotations

import math

# Demi-grand axe de Jupiter (UA) — donnée sourcée, valeur par défaut de l'invariant.
JUPITER_AJ = 5.204

ASTEROIDE = "asteroide"
COMETE_FAMILLE_JUPITER = "comete_famille_jupiter"
COMETE_QUASI_ISOTROPE = "comete_quasi_isotrope"

SOURCE = "Tisserand (1896) ; aJ=5.204 UA ; seuils Levison (1996)"


def _reel(x, nom: str) -> float:
    """Convertit en flottant fini en REFUSANT bool / non numérique / NaN / inf (sinon ValueError)."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError(f"{nom} doit être un nombre réel, reçu {type(x).__name__}")
    xf = float(x)
    if not math.isfinite(xf):
        raise ValueError(f"{nom} doit être fini, reçu {xf}")
    return xf


def tisserand(a, e, i_deg, aJ=JUPITER_AJ) -> float:
    """Paramètre de Tisserand T_J = aJ/a + 2·cos(i)·√((a/aJ)·(1−e²)).

    a, aJ : demi-grands axes (UA, même unité) ; e : excentricité (orbite elliptique : 0 ≤ e < 1) ;
    i_deg : inclinaison en degrés. ValueError sur entrée invalide / orbite non liée.
    """
    a = _reel(a, "a")
    e = _reel(e, "e")
    i_deg = _reel(i_deg, "i_deg")
    aJ = _reel(aJ, "aJ")
    if a <= 0:
        raise ValueError(f"demi-grand axe a doit être > 0 (UA), reçu {a}")
    if aJ <= 0:
        raise ValueError(f"demi-grand axe aJ doit être > 0 (UA), reçu {aJ}")
    if e < 0:
        raise ValueError(f"excentricité e doit être ≥ 0, reçu {e}")
    if e >= 1:
        raise ValueError(f"orbite non elliptique (e ≥ 1) : invariant indéfini, reçu e={e}")
    i = math.radians(i_deg)
    return aJ / a + 2.0 * math.cos(i) * math.sqrt((a / aJ) * (1.0 - e * e))


def classifie(T) -> str:
    """Classe dynamique d'après le paramètre de Tisserand T.

    T > 3 -> astéroïde ; 2 < T < 3 -> comète famille de Jupiter ; T < 2 -> comète quasi-isotrope.
    Frontière exacte (T == 2 ou T == 3) : ambiguë -> ValueError (abstention).
    """
    T = _reel(T, "T")
    if T > 3.0:
        return ASTEROIDE
    if T < 2.0:
        return COMETE_QUASI_ISOTROPE
    if 2.0 < T < 3.0:
        return COMETE_FAMILLE_JUPITER
    raise ValueError(f"T={T} sur une frontière de classification (2 ou 3) : ambigu, abstention")


def classifie_orbite(a, e, i_deg, aJ=JUPITER_AJ):
    """Renvoie (T_J, classe) à partir des éléments orbitaux. ValueError si la frontière exacte est atteinte."""
    T = tisserand(a, e, i_deg, aJ)
    return T, classifie(T)
