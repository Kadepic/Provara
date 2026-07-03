"""
THÉORIE DU CHAOS — sensibilité aux conditions initiales via l'APPLICATION LOGISTIQUE (mandat Yohan, borné « FORMULE »).

Même posture que `physique` / `maths_discretes` (la réalité/les maths jugent, jamais un faux) :
  • Le MÉCANISME est EXACT : la récurrence logistique  x_{n+1} = r·x_n·(1 − x_n)  est la définition canonique de
    May (1976). C'est une formule, pas une heuristique : la garantie est structurelle.
  • Le DOMAINE est strict : pour r ∈ [0, 4] et x0 ∈ [0, 1], l'intervalle [0, 1] est STABLE par la carte (le maximum
    r·(½)·(½) = r/4 ≤ 1), donc les itérés restent dans [0, 1] : pas d'explosion, pas de NaN. Hors de ce domaine la
    dynamique sort de [0,1] / diverge → on REFUSE (ValueError) plutôt que de rendre un nombre absurde.
  • La sortie est ARRONDIE à 10 chiffres significatifs (précision honnête). On n'arrondit QUE le retour final, jamais
    les itérés internes : en régime chaotique (r ≳ 3.57) toute perturbation — y compris l'arrondi — est amplifiée, et
    arrondir en cours de route fabriquerait une trajectoire FAUSSE. C'est précisément le phénomène modélisé.

FONCTIONS
  iterer_logistique(r, x0, n)      -> x_n  (n applications de la carte)
  point_fixe_logistique(r)         -> 1 − 1/r, le point fixe non trivial (existe dans (0,1) pour r > 1)
  sensibilite(r, x0, delta, n)     -> |x_n(x0+delta) − x_n(x0)|, divergence de deux trajectoires voisines

PHÉNOMÈNE (vérifié en adverse par valide_chaos.py contre des SOLUTIONS EXACTES connues, non recalculées par la carte) :
  - r = 2   : convergence vers le point fixe 0.5 ; solution close x_n = ½ − ½(1−2x0)^(2^n) ; sensibilité → 0 (stable).
  - r = 3.2 : cycle de PÉRIODE 2 ; les deux points sont [(r+1) ± √((r−3)(r+1))]/(2r) (résultat externe).
  - r = 4   : chaos ; solution close x_n = sin²(2^n · arcsin√x0) ; sensibilité O(1) même pour delta minuscule.

GARANTIES (soundness, conservateur : faux négatif/abstention toléré, faux POSITIF interdit) :
  - r ∉ [0, 4]  ou  x0 ∉ [0, 1]  -> ValueError ;  pour point_fixe : r ∉ (1, 4] -> ValueError (formule hors (0,1)) ;
  - n non entier ≥ 0, types non numériques, bool -> ValueError ; déterministe (IEEE-754, même entrée → même sortie).
"""
from __future__ import annotations

import math

_CHIFFRES_SIGNIFICATIFS = 10


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête). N'est appliqué qu'au RETOUR final."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _entier_nn(n) -> bool:
    return isinstance(n, int) and not isinstance(n, bool) and n >= 0


def _check_r(r) -> None:
    if not _num(r):
        raise ValueError("r doit être un réel fini")
    if not (0.0 <= r <= 4.0):
        raise ValueError("r hors domaine [0, 4] (la carte sort de [0,1] / diverge)")


def _check_x(x) -> None:
    if not _num(x):
        raise ValueError("x0 doit être un réel fini")
    if not (0.0 <= x <= 1.0):
        raise ValueError("x0 hors domaine [0, 1]")


def _itere_brut(r: float, x: float, n: int) -> float:
    """Itère la carte SANS arrondi intermédiaire (l'arrondi serait amplifié en régime chaotique)."""
    for _ in range(n):
        x = r * x * (1.0 - x)
    return x


def iterer_logistique(r: float, x0: float, n: int) -> float:
    """x_n après n applications de x_{k+1} = r·x_k·(1 − x_k). r ∈ [0,4], x0 ∈ [0,1], n entier ≥ 0."""
    _check_r(r)
    _check_x(x0)
    if not _entier_nn(n):
        raise ValueError("n doit être un entier ≥ 0")
    return _sig(_itere_brut(float(r), float(x0), n))


def point_fixe_logistique(r: float) -> float:
    """Point fixe non trivial x* = 1 − 1/r (vérifie x* = r·x*·(1−x*)). Existe dans (0,1) ssi r > 1."""
    if not _num(r):
        raise ValueError("r doit être un réel fini")
    if not (1.0 < r <= 4.0):
        raise ValueError("point fixe non trivial défini seulement pour r ∈ (1, 4]")
    return _sig(1.0 - 1.0 / r)


def sensibilite(r: float, x0: float, delta: float, n: int) -> float:
    """|x_n(x0+delta) − x_n(x0)| : écart entre deux trajectoires séparées de delta au départ.

    Montre la sensibilité aux conditions initiales : → 0 en régime stable (r petit), O(1) en régime chaotique
    (r ≳ 3.57) même pour delta minuscule. x0 ET x0+delta doivent appartenir à [0,1]."""
    _check_r(r)
    _check_x(x0)
    if not _num(delta):
        raise ValueError("delta doit être un réel fini")
    _check_x(x0 + delta)  # la trajectoire perturbée doit elle aussi partir d'un point valide
    if not _entier_nn(n):
        raise ValueError("n doit être un entier ≥ 0")
    a = _itere_brut(float(r), float(x0), n)
    b = _itere_brut(float(r), float(x0) + float(delta), n)
    return _sig(abs(b - a))
