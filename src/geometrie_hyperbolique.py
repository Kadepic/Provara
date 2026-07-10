"""
GÉOMÉTRIE HYPERBOLIQUE (courbure négative constante) + COHÉRENCE RELATIVE (Beltrami/Klein/Poincaré).

Pendant hyperbolique de `geometries_non_euclidiennes` (qui couvre la sphère) — même posture FAUX=0
(le théorème juge, jamais un faux ; au moindre doute -> ValueError) :
  • Le MÉCANISME est un THÉORÈME EXACT, pas une corrélation :
      – La COURBURE de Gauss d'un plan hyperbolique de « rayon » R est constante  K = −1/R²  (< 0).
      – Théorème de Gauss-Bonnet (cas hyperbolique, dual de Girard) : l'AIRE d'un triangle géodésique vaut
            A = R² · (π − Σ angles) = R² · δ,
        où  δ = π − Σ angles > 0  est le DÉFAUT ANGULAIRE. La somme des angles est TOUJOURS < π (signature
        de la courbure négative) ; Σ ≥ π -> ValueError (cas euclidien ou sphérique, pas hyperbolique).
      – L'aire est donc BORNÉE :  A < π·R²  ; la borne  π·R²  est atteinte à la limite par le triangle
        IDÉAL (les trois angles tendent vers 0, sommets à l'infini) — c'est un SUPREMUM, pas une aire
        de triangle à angles strictement positifs.
      – Modèle du DISQUE DE POINCARÉ (disque unité OUVERT du plan euclidien, K = −1) :
            d(u, v) = arcosh( 1 + 2·|u − v|² / ((1 − |u|²) · (1 − |v|²)) ).
        Tout point de norme ≥ 1 est HORS du modèle (le bord est « à l'infini ») -> ValueError.
        ÉVALUATION STABLE : la forme arcosh(1 + 2t) souffre d'une cancellation catastrophique pour t
        petit (1 + 2t absorbe 2t < eps/2 et rendrait d = 0 pour deux points DISTINCTS — un FAUX métrique,
        car d(u,v) = 0 ⟺ u = v). On évalue donc par l'IDENTITÉ EXACTE
            arcosh(1 + 2t) = 2·arsinh(√t)   [car cosh(2w) = 1 + 2·sinh²(w)],
        avec √t = |u − v| / √((1 − |u|²)·(1 − |v|²)) : |u − v| via math.hypot (pas de sous-dépassement
        du carré) et les facteurs 1 − |p|² calculés EXACTEMENT en rationnels (fractions.Fraction, les
        flottants d'entrée étant des rationnels exacts) — pas de cancellation près du bord. Ainsi
        d(u, v) > 0 pour tout couple de points flottants distincts, et la précision annoncée est tenue
        partout (arsinh est bien conditionné sur [0, ∞[).
  • COHÉRENCE RELATIVE — `coherence_relative()` énonce le FAIT métamathématique sourcé (à la manière de
    godel.theoreme()) : le disque de Poincaré est un MODÈLE euclidien de la géométrie hyperbolique, donc
    la géométrie hyperbolique est cohérente si et seulement si la géométrie euclidienne l'est
    (Beltrami 1868, Klein, Poincaré). Corollaire : le postulat des parallèles est INDÉPENDANT des autres
    axiomes d'Euclide.
  • Les sorties numériques sont ARRONDIES à 10 chiffres significatifs — précision honnête (les entrées
    sont des flottants, on ne prétend pas à l'exactitude au-delà) ; elles sont donc APPROCHÉES à ce rang.

GARANTIES (vérifiées en adverse par `valide_geometrie_hyperbolique.py`) :
  - R ≤ 0 -> ValueError (un rayon de courbure est strictement positif) ;
  - un angle hors de ]0, π[ -> ValueError (angle de triangle hyperbolique mal posé ; l'angle nul du
    triangle idéal est une LIMITE, pas une entrée admissible) ;
  - somme des angles ≥ π -> ValueError : le triangle EUCLIDIEN (Σ = π exactement) est REFUSÉ, le cas
    SPHÉRIQUE (Σ > π) est REFUSÉ — la signature hyperbolique est Σ < π, on refuse plutôt que de rendre
    un défaut/une aire ≤ 0 ;
  - Poincaré : point non-couple-de-2-réels, ou de norme ≥ 1 (bord inclus, jugé EXACTEMENT en
    rationnels) -> ValueError ;
  - Poincaré : d(u, v) = 0 SEULEMENT si u = v (au niveau flottant) ; deux points distincts donnent
    TOUJOURS d > 0 (identité 2·arsinh(√t), pas de cancellation) — jamais un zéro faux ;
  - types invalides (bool, str, NaN, ±inf, mauvaise arité) -> ValueError ;
  - déterministe ; conservateur (faux négatif/abstention toléré, faux POSITIF interdit).

Toutes les fonctions sont PURES et déterministes ; le module n'importe que `math` et
`fractions` (stdlib).
"""
from __future__ import annotations

import math
from fractions import Fraction

PI = math.pi
SOURCE = ("Gauss-Bonnet hyperbolique A = R²·(π − Σ angles), courbure K = −1/R² ; "
          "modèle du disque de Poincaré ; cohérence relative : Beltrami 1868, Klein, Poincaré")

_CHIFFRES_SIGNIFICATIFS = 10


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _est_reel(x) -> bool:
    """True ssi x est un réel fini (les bool sont REFUSÉS : True n'est pas une mesure)."""
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _exige_rayon(R) -> float:
    if not _est_reel(R) or R <= 0:
        raise ValueError("rayon de courbure R invalide : un réel strictement positif est requis")
    return float(R)


def _exige_angle(a) -> float:
    """Angle d'un sommet de triangle hyperbolique : réel dans ]0, π[ (strict).

    L'angle NUL (sommet idéal, à l'infini) est une LIMITE du mécanisme, pas une entrée admissible."""
    if not _est_reel(a) or not (0.0 < a < PI):
        raise ValueError("angle invalide : un réel dans l'intervalle ]0, pi[ est requis")
    return float(a)


def _exige_point_disque(p) -> tuple:
    """Point du disque de Poincaré : couple (x, y) de réels finis avec x² + y² < 1 (disque OUVERT).

    Le bord |p| = 1 est le cercle à l'infini : il n'appartient PAS au modèle -> ValueError.
    La condition est jugée EXACTEMENT en rationnels (Fraction) : un flottant est un rationnel exact,
    donc ni faux rejet ni fausse admission dus à l'arrondi de x² + y² en flottant."""
    if not isinstance(p, (list, tuple)) or len(p) != 2:
        raise ValueError("point invalide : un couple (x, y) de 2 réels est requis")
    x, y = p
    if not _est_reel(x) or not _est_reel(y):
        raise ValueError("coordonnée invalide : un réel fini est requis (bool/str/NaN/inf refusés)")
    if Fraction(x) * Fraction(x) + Fraction(y) * Fraction(y) >= 1:
        raise ValueError("point hors du disque de Poincaré OUVERT : x² + y² < 1 est requis "
                         "(le bord |p| = 1 est le cercle à l'infini, il n'appartient pas au modèle)")
    return (float(x), float(y))


# ── COURBURE ───────────────────────────────────────────────────────────────────────────────────────────────────
def courbure_gauss_hyperbolique(R: float) -> float:
    """Courbure de Gauss du plan hyperbolique de rayon R : K = −1/R² (constante, NÉGATIVE).

    R ≤ 0 -> ValueError."""
    R = _exige_rayon(R)
    return _sig(-1.0 / (R * R))


# ── SOMME DES ANGLES ─────────────────────────────────────────────────────────────────────────────────────────--
def somme_angles_triangle_hyperbolique(a1: float, a2: float, a3: float):
    """Somme des angles (rad) d'un triangle hyperbolique non dégénéré.

    Renvoie le couple (somme, somme < π). En géométrie hyperbolique la somme est TOUJOURS < π : on refuse
    (ValueError) toute somme ≥ π — le cas euclidien (Σ = π) comme le cas sphérique (Σ > π) — et tout angle
    hors ]0, π[. Jamais un résultat trompeur."""
    a1 = _exige_angle(a1)
    a2 = _exige_angle(a2)
    a3 = _exige_angle(a3)
    somme = a1 + a2 + a3
    if somme >= PI:
        raise ValueError("somme des angles ≥ π : pas un triangle hyperbolique "
                         "(Σ = π est euclidien, Σ > π est sphérique ; la signature hyperbolique est Σ < π)")
    return (_sig(somme), somme < PI)


# ── DÉFAUT ANGULAIRE ─────────────────────────────────────────────────────────────────────────────────────────--
def defaut_angulaire(a1: float, a2: float, a3: float) -> float:
    """Défaut angulaire δ = π − Σ angles (> 0) d'un triangle hyperbolique.

    Σ ≥ π -> ValueError (pas hyperbolique) ; angle hors ]0, π[ -> ValueError."""
    a1 = _exige_angle(a1)
    a2 = _exige_angle(a2)
    a3 = _exige_angle(a3)
    somme = a1 + a2 + a3
    if somme >= PI:
        raise ValueError("somme des angles ≥ π : défaut angulaire ≤ 0, pas un triangle hyperbolique")
    return _sig(PI - somme)


# ── AIRE (GAUSS-BONNET HYPERBOLIQUE) ─────────────────────────────────────────────────────────────────────────--
def aire_triangle_hyperbolique(angles, R: float) -> float:
    """Aire d'un triangle hyperbolique : A = R² · (π − Σ angles) = R² · δ  (Gauss-Bonnet, courbure −1/R²).

    `angles` = séquence de 3 angles (rad) dans ]0, π[ ; R ≤ 0 -> ValueError ; Σ ≥ π -> ValueError.
    L'aire est toujours < π·R² (supremum du triangle idéal, cf. aire_maximale)."""
    R = _exige_rayon(R)
    if not isinstance(angles, (list, tuple)) or len(angles) != 3:
        raise ValueError("angles invalide : exactement 3 angles (liste/tuple) sont requis")
    a1, a2, a3 = (_exige_angle(a) for a in angles)
    somme = a1 + a2 + a3
    if somme >= PI:
        raise ValueError("somme des angles ≥ π : pas un triangle hyperbolique (aire ≤ 0 interdite)")
    return _sig(R * R * (PI - somme))


def aire_maximale(R: float) -> float:
    """SUPREMUM de l'aire d'un triangle hyperbolique de rayon R : π·R² (triangle IDÉAL, angles -> 0).

    C'est une BORNE (limite atteinte par le triangle idéal, sommets à l'infini), pas l'aire d'un
    triangle à angles strictement positifs. R ≤ 0 -> ValueError."""
    R = _exige_rayon(R)
    return _sig(PI * R * R)


# ── DISQUE DE POINCARÉ ───────────────────────────────────────────────────────────────────────────────────────--
def distance_poincare(u, v) -> float:
    """Distance hyperbolique (K = −1) entre deux points du disque de Poincaré OUVERT :

        d(u, v) = arcosh( 1 + 2·t )   avec   t = |u − v|² / ((1 − |u|²) · (1 − |v|²)).

    ÉVALUATION STABLE par l'identité EXACTE  arcosh(1 + 2t) = 2·arsinh(√t)  [cosh(2w) = 1 + 2·sinh²(w)] :
      • la forme arcosh(1 + 2t) est INTERDITE ici — pour t petit, 1 + 2t absorbe 2t (cancellation
        catastrophique) et rendrait d = 0 pour deux points DISTINCTS, un FAUX métrique (d = 0 ⟺ u = v) ;
      • √t = |u − v| / √((1 − |u|²)·(1 − |v|²)) : |u − v| via math.hypot (le carré n'est jamais formé,
        pas de sous-dépassement), facteurs 1 − |p|² EXACTS en rationnels (Fraction) — pas de
        cancellation près du bord ; arsinh est bien conditionné sur [0, ∞[.
    GARANTIE : d(u, v) > 0 pour tout couple de points flottants distincts ; d(u, u) = 0.
    u, v = couples (x, y) avec x² + y² < 1 strict (jugé exactement) ; norme ≥ 1 -> ValueError."""
    ux, uy = _exige_point_disque(u)
    vx, vy = _exige_point_disque(v)
    dx = ux - vx
    dy = uy - vy
    if dx == 0.0 and dy == 0.0:
        return 0.0  # u = v (au niveau flottant) : le SEUL cas où d = 0.
    # 1 − |p|² EXACT en rationnels : Fraction(flottant) est exact, aucune cancellation possible.
    # Le produit est > 0 (garanti par _exige_point_disque, condition jugée exactement) et sa conversion
    # en flottant ne sous-passe jamais : chaque facteur vaut au moins 2^-106 (grain rationnel des carrés
    # de doubles), donc le produit ≥ 2^-212 >> le plus petit flottant positif (2^-1074).
    un_moins_u2 = 1 - (Fraction(ux) * Fraction(ux) + Fraction(uy) * Fraction(uy))
    un_moins_v2 = 1 - (Fraction(vx) * Fraction(vx) + Fraction(vy) * Fraction(vy))
    racine_t = math.hypot(dx, dy) / math.sqrt(float(un_moins_u2 * un_moins_v2))
    return _sig(2.0 * math.asinh(racine_t))


# ── COHÉRENCE RELATIVE (FAIT métamathématique sourcé) ────────────────────────────────────────────────────────--
def coherence_relative() -> str:
    """FAIT métamathématique (énoncé de référence, à la manière de godel.theoreme())."""
    return ("La géométrie hyperbolique est cohérente si et seulement si la géométrie euclidienne l'est "
            "(Beltrami 1868, Klein, Poincaré) : le disque de Poincaré est un MODÈLE euclidien de la "
            "géométrie hyperbolique, donc toute contradiction hyperbolique se traduirait en contradiction "
            "euclidienne. Corollaire : le postulat des parallèles est INDÉPENDANT des autres axiomes "
            "d'Euclide.")
