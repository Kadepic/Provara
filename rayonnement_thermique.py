"""RAYONNEMENT THERMIQUE DU CORPS NOIR — primitives EXACTES, FAUX=0 (sujet : « Fond diffus cosmologique »).

Posture identique à `physique`/`maths_discretes` : le MÉCANISME (les lois physiques) est EXACT, les CONSTANTES sont
des DONNÉES SOURCÉES (CODATA 2018 / SI 2019), et l'abstention est STRUCTURELLE — toute entrée invalide (température
ou longueur d'onde ≤ 0, type non numérique, booléen) lève `ValueError`, JAMAIS un résultat faux. Conservateur :
faux négatif (abstention) toléré, faux POSITIF interdit.

LOIS COUVERTES
  • Loi du déplacement de Wien (forme longueur d'onde) : λ_max(T) = b / T,  b = 2.897771955e-3 m·K (CODATA 2018).
        - inverse : temperature_depuis_pic(λ) = b / λ.
  • Loi du déplacement de Wien (forme fréquence) : ν_max(T) = b' · T,  b' = 5.878925757e10 Hz·K⁻¹ (CODATA 2018).
        ⚠ ATTENTION : le pic en longueur d'onde et le pic en fréquence NE désignent PAS le même point du spectre
        (λ_max · ν_max ≠ c) — c'est une subtilité bien connue du corps noir. Les deux constantes sont distinctes.
  • Loi de Stefan-Boltzmann (émittance) : M(T) = σ · T⁴,  σ = 5.670374419e-8 W·m⁻²·K⁻⁴ (SI 2019, exacte via h,c,k).
        - puissance rayonnée par une surface A : P = σ · T⁴ · A.

ANCRES PHYSIQUES (vérifiées en adverse par `valide_rayonnement_thermique.py`, valeurs EXTERNES connues) :
  - CMB T = 2.725 K  -> λ_max ≈ 1.063 mm (micro-ondes) et ν_max ≈ 160.2 GHz (pic mesuré du fond diffus) ;
  - Soleil T = 5778 K -> λ_max ≈ 501 nm (lumière visible, vert-jaune) ;
  - corps noir à 300 K émet ≈ 459 W·m⁻² ; surface solaire ≈ 6.32e7 W·m⁻².

La sortie est ARRONDIE à 10 chiffres significatifs (précision honnête : la physique réelle porte l'incertitude des
constantes mesurées ; on ne prétend pas à l'exactitude au-delà de la source).
"""
from __future__ import annotations

# ── CONSTANTES SOURCÉES ──────────────────────────────────────────────────────────────────────────────────────────
B_WIEN = 2.897771955e-3        # m·K — constante de déplacement de Wien (longueur d'onde), CODATA 2018
B_WIEN_FREQ = 5.878925757e10   # Hz·K⁻¹ — constante de déplacement de Wien (fréquence), CODATA 2018
SIGMA_SB = 5.670374419e-8      # W·m⁻²·K⁻⁴ — constante de Stefan-Boltzmann, SI 2019 (exacte via h, c, k_B)

SOURCE = "CODATA 2018 (Wien b, b') / SI 2019 (Stefan-Boltzmann σ)"
_CHIFFRES_SIGNIFICATIFS = 10


def _sig(x: float, n: int = _CHIFFRES_SIGNIFICATIFS) -> float:
    """Arrondit à n chiffres significatifs (précision honnête, indépendante de la magnitude)."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


def _temperature_valide(T) -> float:
    """Température absolue en kelvins : nombre réel strictement positif. Sinon ValueError (abstention)."""
    if isinstance(T, bool) or not isinstance(T, (int, float)):
        raise ValueError(f"température numérique attendue, reçu {T!r}")
    if T <= 0:
        raise ValueError(f"température absolue > 0 K attendue, reçu {T!r}")
    return float(T)


def _longueur_onde_valide(lam) -> float:
    """Longueur d'onde en mètres : nombre réel strictement positif. Sinon ValueError (abstention)."""
    if isinstance(lam, bool) or not isinstance(lam, (int, float)):
        raise ValueError(f"longueur d'onde numérique attendue, reçu {lam!r}")
    if lam <= 0:
        raise ValueError(f"longueur d'onde > 0 m attendue, reçu {lam!r}")
    return float(lam)


def _surface_valide(A) -> float:
    if isinstance(A, bool) or not isinstance(A, (int, float)):
        raise ValueError(f"surface numérique attendue, reçu {A!r}")
    if A <= 0:
        raise ValueError(f"surface > 0 m² attendue, reçu {A!r}")
    return float(A)


# ── LOI DE WIEN (déplacement) ────────────────────────────────────────────────────────────────────────────────────
def longueur_onde_max(T) -> float:
    """λ_max = b / T (m). T en kelvins (> 0). Pic d'émission du corps noir en longueur d'onde."""
    t = _temperature_valide(T)
    return _sig(B_WIEN / t)


def temperature_depuis_pic(longueur_onde) -> float:
    """Inverse de Wien : T = b / λ_max (K). λ en mètres (> 0)."""
    lam = _longueur_onde_valide(longueur_onde)
    return _sig(B_WIEN / lam)


def frequence_max(T) -> float:
    """ν_max = b' · T (Hz). T en kelvins (> 0). Pic d'émission en FRÉQUENCE (≠ pic en longueur d'onde)."""
    t = _temperature_valide(T)
    return _sig(B_WIEN_FREQ * t)


# ── LOI DE STEFAN-BOLTZMANN ──────────────────────────────────────────────────────────────────────────────────────
def loi_stefan_boltzmann(T) -> float:
    """Émittance totale M = σ · T⁴ (W·m⁻²). T en kelvins (> 0)."""
    t = _temperature_valide(T)
    return _sig(SIGMA_SB * t ** 4)


def puissance_rayonnee(T, surface) -> float:
    """Puissance rayonnée P = σ · T⁴ · A (W). T en kelvins (> 0), A en m² (> 0)."""
    t = _temperature_valide(T)
    a = _surface_valide(surface)
    return _sig(SIGMA_SB * t ** 4 * a)
