"""
THÉORIE DES CATASTROPHES / BIFURCATIONS — stabilité des points fixes et formes normales.

Même posture FAUX=0 que `physique.py` / `maths_discretes.py` (la réalité/les maths jugent, jamais un faux) :
  • Le MÉCANISME est EXACT — ce sont des théorèmes de la théorie des systèmes dynamiques, pas des heuristiques.
  • ABSTENTION STRUCTURELLE : toute entrée non numérique / hors-domaine lève ValueError. Jamais un verdict faux.
  • Déterministe ; conservateur (faux négatif/abstention toléré, faux POSITIF interdit).

CE QUE LE MODULE COUVRE
-----------------------
1) STABILITÉ LINÉAIRE D'UN POINT FIXE (théorème de linéarisation / Hartman-Grobman).
   • Flot continu  x' = f(x) en un point fixe x* (f(x*)=0) :
        f'(x*) < 0  -> STABLE   (la perturbation décroît, exp(f'(x*)·t) -> 0)
        f'(x*) > 0  -> INSTABLE (la perturbation croît)
        f'(x*) = 0  -> MARGINAL (cas dégénéré, la linéarisation ne tranche pas).
     => `stabilite_point_fixe(f_prime_en_xstar)`.
   • Carte discrète  x -> g(x) en un point fixe x* (g(x*)=x*), de multiplicateur μ = g'(x*) :
        |μ| < 1 -> STABLE  ;  |μ| > 1 -> INSTABLE  ;  |μ| = 1 -> MARGINAL (point de bifurcation).
     => `stabilite_point_fixe_discret(multiplicateur)`.

2) CARTE LOGISTIQUE  x -> r·x·(1-x).
   • Point fixe non trivial  x* = 1 - 1/r  => `point_fixe_logistique(r)` (exige r != 0).
   • Multiplicateur en x* :  μ = g'(x*) = r·(1 - 2·x*) = 2 - r  => `multiplicateur_logistique(r)`.
   • Stabilité : |μ| = |2 - r| < 1  <=>  1 < r < 3  => `bifurcation_logistique(r)`.
     (r=3 : μ=-1, bifurcation par doublement de période ; r=1 : μ=+1, bifurcation transcritique.)

3) FORMES NORMALES (catastrophes élémentaires) — nombre de points fixes réels selon le paramètre μ.
   • Pli / nœud-col (saddle-node, catastrophe « fold »)  x' = μ + x²  :  x² = -μ
        μ < 0 -> 2 points fixes ;  μ = 0 -> 1 (bifurcation) ;  μ > 0 -> 0.
     => `nb_points_fixes_pli(mu)`.
   • Fourche (pitchfork, supercritique)  x' = μ·x - x³  :  x·(μ - x²) = 0
        μ <= 0 -> 1 point fixe (x=0) ;  μ > 0 -> 3 (x=0, ±√μ).
     => `nb_points_fixes_fourche(mu)`.
"""
from __future__ import annotations

import math

STABLE = "stable"
INSTABLE = "instable"
MARGINAL = "marginal"

_CHIFFRES_SIGNIFICATIFS = 10


def _num(x) -> float:
    """Garde de soundness : exige un réel fini (int ou float, PAS bool/str/None/NaN/inf). Sinon ValueError."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError(f"entrée non numérique : {x!r}")
    xf = float(x)
    if math.isnan(xf) or math.isinf(xf):
        raise ValueError(f"entrée non finie : {x!r}")
    return xf


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def stabilite_point_fixe(f_prime_en_xstar) -> str:
    """Stabilité d'un point fixe d'un FLOT CONTINU x'=f(x) selon le signe de f'(x*).

    f'(x*) < 0 -> 'stable' ; > 0 -> 'instable' ; = 0 -> 'marginal' (linéarisation non concluante).
    """
    fp = _num(f_prime_en_xstar)
    if fp < 0.0:
        return STABLE
    if fp > 0.0:
        return INSTABLE
    return MARGINAL


def stabilite_point_fixe_discret(multiplicateur) -> str:
    """Stabilité d'un point fixe d'une CARTE DISCRÈTE x->g(x) selon le module du multiplicateur μ=g'(x*).

    |μ| < 1 -> 'stable' ; |μ| > 1 -> 'instable' ; |μ| = 1 -> 'marginal' (point de bifurcation).
    """
    mu = abs(_num(multiplicateur))
    if mu < 1.0:
        return STABLE
    if mu > 1.0:
        return INSTABLE
    return MARGINAL


def point_fixe_logistique(r) -> float:
    """Point fixe NON TRIVIAL x* = 1 - 1/r de la carte logistique x->r·x·(1-x). Exige r != 0."""
    rf = _num(r)
    if rf == 0.0:
        raise ValueError("r = 0 : point fixe non trivial indéfini (1/r)")
    return _sig(1.0 - 1.0 / rf)


def multiplicateur_logistique(r) -> float:
    """Multiplicateur μ = g'(x*) = r·(1-2·x*) = 2 - r au point fixe non trivial de la carte logistique."""
    rf = _num(r)
    return _sig(2.0 - rf)


def bifurcation_logistique(r) -> str:
    """Stabilité du point fixe non trivial x*=1-1/r de la carte logistique : μ = 2-r, stable ssi |2-r|<1 (1<r<3).

    'stable' pour 1<r<3 ; 'marginal' à r=1 et r=3 ; 'instable' sinon.
    """
    rf = _num(r)
    return stabilite_point_fixe_discret(2.0 - rf)


def nb_points_fixes_pli(mu) -> int:
    """Nombre de points fixes réels de la forme normale du PLI (nœud-col) x'=μ+x²  (x²=-μ).

    μ<0 -> 2 ; μ=0 -> 1 (bifurcation) ; μ>0 -> 0.
    """
    m = _num(mu)
    if m < 0.0:
        return 2
    if m > 0.0:
        return 0
    return 1


def nb_points_fixes_fourche(mu) -> int:
    """Nombre de points fixes réels de la forme normale de la FOURCHE (pitchfork) x'=μ·x-x³  (x·(μ-x²)=0).

    μ<=0 -> 1 (x=0) ; μ>0 -> 3 (x=0, ±√μ).
    """
    m = _num(mu)
    return 3 if m > 0.0 else 1
