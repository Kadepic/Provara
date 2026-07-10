"""
ROTATION DU SOLIDE — moment d'inertie, moment cinétique, couple, énergie, conservation.

Même posture FAUX=0 que `physique` / `geometries_non_euclidiennes` (la réalité/le théorème juge, jamais un faux) :
  • Le MÉCANISME est la mécanique du solide CLASSIQUE, exacte, pas une corrélation :
      – Catalogue EXACT (formules fermées démontrées par intégration de ∫r² dm) des moments d'inertie
        des solides homogènes usuels, coefficient RATIONNEL exact (Fraction) :
            masse ponctuelle        I = m·r²
            disque plein / cylindre I = ½·m·r²          (axe de révolution)
            sphère pleine           I = (2/5)·m·r²
            sphère creuse (coque)   I = (2/3)·m·r²
            tige, axe par le centre I = (1/12)·m·L²
            tige, axe par le bout   I = (1/3)·m·L²
            anneau (cerceau)        I = m·r²             (axe de révolution)
      – Moment cinétique   L = I·ω          (rotation autour d'un axe fixe principal) ;
      – Couple             τ = I·α          (2ᵉ loi de Newton en rotation) ;
      – Énergie cinétique  E = ½·I·ω² ;
      – Conservation du moment cinétique (τ_ext = 0) :  I₁·ω₁ = I₂·ω₂  ⇒  ω₂ = I₁·ω₁ / I₂ ;
      – Théorème de Huygens-Steiner (axes parallèles) :  I = I_centre + m·d².
  • La sortie est ARRONDIE à 10 chiffres significatifs — précision honnête (les entrées sont des flottants,
    on ne prétend pas à l'exactitude au-delà) ; les COEFFICIENTS du catalogue, eux, sont exacts (Fraction).

GARANTIES (vérifiées en adverse par `valide_rotation_solide.py`) :
  - forme hors catalogue -> ValueError (jamais un coefficient deviné) ;
  - masse ≤ 0, dimension ≤ 0, I ≤ 0 -> ValueError (grandeurs strictement positives) ;
  - I₂ ≤ 0 dans la conservation -> ValueError (division par zéro / inertie absurde interdites) ;
  - d < 0 dans Huygens-Steiner -> ValueError (une distance n'est pas négative ; d = 0 est légal : même axe) ;
  - ω et α peuvent être négatifs (sens de rotation) mais JAMAIS bool/str/NaN/±inf ;
  - types invalides (bool, str, NaN, ±inf, complexe) -> ValueError ;
  - GARDE DE SORTIE : un résultat qui déborde en ±inf (overflow, y compris à l'arrondi 10 chiffres) ou qui
    s'écrase à 0.0 alors que le résultat mathématique est non nul (underflow) -> ValueError (abstention).
    Conséquence : une inertie rendue par le module est TOUJOURS finie et > 0, donc toujours réutilisable
    comme entrée (cohérence interne avec « I ≤ 0 absurde ») ;
  - déterministe ; conservateur (faux négatif/abstention toléré, faux POSITIF interdit).

Toutes les fonctions sont PURES et déterministes ; le module n'importe que `math` et `fractions` (stdlib).
"""
from __future__ import annotations

import math
from fractions import Fraction

SOURCE = ("mécanique classique du solide rigide : catalogue standard des moments d'inertie (∫r² dm), "
          "L=I·ω, τ=I·α, E=½·I·ω², conservation de L, théorème de Huygens-Steiner (axes parallèles)")

_CHIFFRES_SIGNIFICATIFS = 10

# Catalogue EXACT : forme -> coefficient rationnel c tel que I = c · m · (dimension)².
# Coefficients démontrés par intégration directe (valeurs classiques, cf. SOURCE).
CATALOGUE_INERTIE: dict[str, Fraction] = {
    "masse_ponctuelle":    Fraction(1, 1),    # I = m·r²
    "disque_plein":        Fraction(1, 2),    # I = ½·m·r²   (axe de révolution)
    "cylindre_plein":      Fraction(1, 2),    # I = ½·m·r²   (axe de révolution)
    "sphere_pleine":       Fraction(2, 5),    # I = (2/5)·m·r²
    "sphere_creuse":       Fraction(2, 3),    # I = (2/3)·m·r²  (coque mince)
    "tige_axe_centre":     Fraction(1, 12),   # I = (1/12)·m·L² (axe ⟂ par le centre)
    "tige_axe_extremite":  Fraction(1, 3),    # I = (1/3)·m·L²  (axe ⟂ par l'extrémité)
    "anneau":              Fraction(1, 1),    # I = m·r²     (cerceau mince, axe de révolution)
}


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _est_reel(x) -> bool:
    """True ssi x est un réel fini (les bool sont REFUSÉS : True n'est pas une mesure)."""
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _exige_positif(x, nom: str) -> float:
    """Réel fini STRICTEMENT positif, sinon ValueError."""
    if not _est_reel(x) or x <= 0:
        raise ValueError(f"{nom} invalide : un réel strictement positif est requis")
    return float(x)


def _exige_reel(x, nom: str) -> float:
    """Réel fini (signe libre : sens de rotation), sinon ValueError."""
    if not _est_reel(x):
        raise ValueError(f"{nom} invalide : un réel fini est requis (bool/str/NaN/inf refusés)")
    return float(x)


def _exige_sortie(valeur: float, nom: str, nul_legal: bool) -> float:
    """GARDE DE SORTIE : arrondit à 10 chiffres significatifs puis REFUSE tout résultat flottant faux.

    - ±inf (overflow du calcul, ou débordement à l'arrondi) -> ValueError : jamais un infini présenté
      comme une grandeur physique ;
    - 0.0 alors que `nul_legal` est False (les facteurs sont mathématiquement non nuls : underflow) ->
      ValueError : jamais un zéro faussement exact — d'autant qu'un I = 0.0 serait ensuite refusé
      comme entrée par le module lui-même (I ≤ 0 absurde).
    Abstention (faux négatif) tolérée ; résultat plausible mais faux INTERDIT."""
    arrondi = _sig(valeur)
    if not math.isfinite(arrondi):
        raise ValueError(f"{nom} hors capacité flottante (overflow) : abstention plutôt qu'un résultat faux")
    if arrondi == 0.0 and not nul_legal:
        raise ValueError(f"{nom} : sous-passement flottant (underflow), le vrai résultat est non nul "
                         "mais non représentable — abstention plutôt qu'un 0 faussement exact")
    return arrondi


# ── MOMENT D'INERTIE (catalogue exact) ─────────────────────────────────────────────────────────────────────────
def moment_inertie(forme: str, masse: float, dimension: float) -> float:
    """Moment d'inertie I = c·m·d² (kg·m²) pour une forme du CATALOGUE exact.

    `forme` ∈ {masse_ponctuelle, disque_plein, cylindre_plein, sphere_pleine, sphere_creuse,
    tige_axe_centre, tige_axe_extremite, anneau} ; `dimension` = rayon r ou longueur L selon la forme.
    Forme hors catalogue -> ValueError (abstention : jamais un coefficient deviné).
    masse ≤ 0 ou dimension ≤ 0 -> ValueError. Overflow/underflow du résultat -> ValueError
    (une inertie rendue est toujours finie et > 0)."""
    if not isinstance(forme, str):
        raise ValueError("forme invalide : une chaîne du catalogue est requise")
    coeff = CATALOGUE_INERTIE.get(forme.strip().lower())
    if coeff is None:
        raise ValueError(f"forme hors catalogue : {sorted(CATALOGUE_INERTIE)} sont les seules connues (abstention)")
    m = _exige_positif(masse, "masse")
    d = _exige_positif(dimension, "dimension")
    # c > 0, m > 0, d > 0 : le résultat mathématique est strictement positif — 0.0 serait un underflow.
    return _exige_sortie(float(coeff) * m * d * d, "moment d'inertie I", nul_legal=False)


# ── MOMENT CINÉTIQUE L = I·ω ───────────────────────────────────────────────────────────────────────────────────
def moment_cinetique(inertie: float, omega: float) -> float:
    """Moment cinétique L = I·ω (kg·m²/s). I ≤ 0 -> ValueError ; ω réel fini (signe = sens de rotation).
    Overflow/underflow du résultat -> ValueError (L = 0 n'est légal que si ω = 0)."""
    inertie = _exige_positif(inertie, "moment d'inertie I")
    omega = _exige_reel(omega, "vitesse angulaire omega")
    # I > 0 : L est mathématiquement nul ssi ω = 0 — sinon un 0.0 serait un underflow.
    return _exige_sortie(inertie * omega, "moment cinétique L", nul_legal=(omega == 0.0))


# ── COUPLE τ = I·α ─────────────────────────────────────────────────────────────────────────────────────────────
def couple(inertie: float, alpha: float) -> float:
    """Couple τ = I·α (N·m). I ≤ 0 -> ValueError ; α réel fini (signe = sens de l'accélération).
    Overflow/underflow du résultat -> ValueError (τ = 0 n'est légal que si α = 0)."""
    inertie = _exige_positif(inertie, "moment d'inertie I")
    alpha = _exige_reel(alpha, "acceleration angulaire alpha")
    return _exige_sortie(inertie * alpha, "couple tau", nul_legal=(alpha == 0.0))


# ── ÉNERGIE CINÉTIQUE DE ROTATION E = ½·I·ω² ───────────────────────────────────────────────────────────────────
def energie_rotation(inertie: float, omega: float) -> float:
    """Énergie cinétique de rotation E = ½·I·ω² (J). I ≤ 0 -> ValueError ; ω réel fini.
    Overflow/underflow du résultat -> ValueError (E = 0 n'est légal que si ω = 0)."""
    inertie = _exige_positif(inertie, "moment d'inertie I")
    omega = _exige_reel(omega, "vitesse angulaire omega")
    return _exige_sortie(0.5 * inertie * omega * omega, "energie de rotation E", nul_legal=(omega == 0.0))


# ── CONSERVATION DU MOMENT CINÉTIQUE ───────────────────────────────────────────────────────────────────────────
def conservation_moment_cinetique(inertie1: float, omega1: float, inertie2: float) -> float:
    """ω₂ tel que I₁·ω₁ = I₂·ω₂ (couple extérieur nul) : ω₂ = I₁·ω₁ / I₂.

    I₁ ≤ 0 ou I₂ ≤ 0 -> ValueError (en particulier I₂ = 0 : division interdite) ; ω₁ réel fini.
    Overflow du produit intermédiaire I₁·ω₁ ou underflow du résultat -> ValueError (abstention :
    on ne rend jamais inf ni un 0 faussement exact même si la valeur mathématique existe)."""
    inertie1 = _exige_positif(inertie1, "moment d'inertie I1")
    inertie2 = _exige_positif(inertie2, "moment d'inertie I2")
    omega1 = _exige_reel(omega1, "vitesse angulaire omega1")
    # I1, I2 > 0 : ω₂ est mathématiquement nul ssi ω₁ = 0 — sinon un 0.0 serait un underflow.
    return _exige_sortie(inertie1 * omega1 / inertie2, "vitesse angulaire omega2", nul_legal=(omega1 == 0.0))


# ── THÉORÈME DE HUYGENS-STEINER (axes parallèles) ──────────────────────────────────────────────────────────────
def inertie_axe_parallele(inertie_centre: float, masse: float, distance: float) -> float:
    """I = I_centre + m·d² (théorème des axes parallèles).

    I_centre ≤ 0 ou m ≤ 0 -> ValueError ; d < 0 -> ValueError (d = 0 légal : même axe, I = I_centre).
    Overflow du résultat -> ValueError (une inertie rendue est toujours finie et > 0)."""
    inertie_centre = _exige_positif(inertie_centre, "moment d'inertie I_centre")
    m = _exige_positif(masse, "masse")
    if not _est_reel(distance) or distance < 0:
        raise ValueError("distance invalide : un réel fini >= 0 est requis (distance entre axes)")
    # Somme de I_centre > 0 et de m·d² ≥ 0 : le résultat mathématique est strictement positif.
    return _exige_sortie(inertie_centre + m * float(distance) * float(distance),
                         "moment d'inertie I (axe parallele)", nul_legal=False)
