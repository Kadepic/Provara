"""
DÉVELOPPEMENT LIMITÉ / SÉRIE DE TAYLOR — coefficients EXACTS (ℚ) + BORNE DU RESTE, FAUX=0 (PARTIE I, B-NEC).

Posture (identique à `calcul_infinitesimal` / `galois`) : on n'expose QUE ce qui est démontré, exact ou
explicitement borné. Un développement limité SANS majoration du reste ne dit RIEN sur l'erreur commise :
c'est pourquoi ce module ne rend JAMAIS une valeur approchée nue — `approxime` renvoie le couple
(valeur_approchée, borne_erreur) et l'inégalité |vrai − approx| ≤ borne est GARANTIE.

MÉCANISME (théorèmes exacts, pas des corrélations) :
  • CATALOGUE des développements de Maclaurin (en 0) à coefficients EXACTS en `Fraction`, indice = degré :
        exp(x) = Σ xᵏ/k!            sin(x) = Σ (−1)ᵐ x^(2m+1)/(2m+1)!      cos(x) = Σ (−1)ᵐ x^(2m)/(2m)!
        ln(1+x) = Σ_{k≥1} (−1)^(k+1) xᵏ/k                                  1/(1−x) = Σ xᵏ
        sinh(x) = Σ x^(2m+1)/(2m+1)!    cosh(x) = Σ x^(2m)/(2m)!            arctan(x) = Σ (−1)ᵐ x^(2m+1)/(2m+1)
        (1+x)^α = Σ C(α,k) xᵏ  avec  C(α,k) = α(α−1)…(α−k+1)/k!  (série binomiale, α RATIONNEL).
  • DÉVELOPPEMENT D'UN POLYNÔME autour d'un point a (EXACT, par dérivations successives via
    `calcul_infinitesimal.derivee`) : coefficient de (x−a)ᵏ = p⁽ᵏ⁾(a)/k!.
  • RESTE DE LAGRANGE : pour le polynôme de Taylor d'ordre n,  |R_n(x)| ≤ M·|x|^(n+1)/(n+1)!  où M majore
    |f⁽ⁿ⁺¹⁾| sur [0,x]. `borne_reste_lagrange` prend M en argument ; `approxime` calcule un M RIGOUREUX
    interne (M=1 pour sin/cos ; M=3^⌈|x|⌉ ≥ e^|x| pour exp/sinh/cosh, car e<3) — il ABSTIENT (ValueError)
    pour les fonctions sans majorant automatique certain (ln1p, arctan, geometrique, binome).
  • RAYON DE CONVERGENCE connu : +∞ pour exp/sin/cos/sinh/cosh ; 1 pour ln(1+x)/arctan/1/(1−x)/binome.

GARANTIES (vérifiées en adverse par `valide_developpement_limite.py`) :
  - fonction hors catalogue -> ValueError ; ordre < 0 ou non entier (bool refusé) -> ValueError ;
  - |x| ≥ rayon de convergence -> ValueError EXPLICITE (le développement ne converge pas là) ;
  - α manquant pour la série binomiale -> ValueError ; α flottant (exactitude requise) -> ValueError ;
  - coefficient/point non rationnel (flottant) pour un calcul EXACT -> ValueError ;
  - types invalides (bool, str non numérique, NaN, ±inf, complexe, mauvaise arité) -> ValueError ;
  - `approxime` ne rend JAMAIS une valeur nue : toujours (valeur, borne) avec |vrai − approx| ≤ borne ;
  - déterministe, pur, sans état global ; conservateur (faux négatif toléré, faux POSITIF interdit).

Coefficients EXACTS (Fraction) ; `approxime` évalue en `x` rationnel exact et renvoie des Fraction — aucune
perte de précision cachée. Le module n'importe que la stdlib (math, fractions) et `calcul_infinitesimal`.
"""
from __future__ import annotations

import math
from fractions import Fraction

import calcul_infinitesimal as ci

SOURCE = "séries de Maclaurin/Taylor classiques + reste de Lagrange (analyse réelle, théorème de Taylor)"

# Catalogue des développements usuels en 0.
_CATALOGUE = frozenset(
    {"exp", "sin", "cos", "ln1p", "binome", "geometrique", "sinh", "cosh", "arctan"}
)
# Rayon de convergence infini (fonctions entières).
_RAYON_INFINI = frozenset({"exp", "sin", "cos", "sinh", "cosh"})
# Fonctions pour lesquelles un majorant RIGOUREUX de |f^(n+1)| est calculable automatiquement.
_MAJORANT_AUTO = frozenset({"exp", "sin", "cos", "sinh", "cosh"})


# ── helpers de validation ────────────────────────────────────────────────────────────────────────────────────────
def _exige_nom(nom) -> str:
    if not isinstance(nom, str) or nom not in _CATALOGUE:
        raise ValueError(
            f"fonction hors catalogue : {nom!r} (attendu l'un de {sorted(_CATALOGUE)})"
        )
    return nom


def _exige_ordre(ordre) -> int:
    if isinstance(ordre, bool) or not isinstance(ordre, int):
        raise ValueError(f"ordre entier attendu, reçu {ordre!r}")
    if ordre < 0:
        raise ValueError(f"ordre ≥ 0 attendu, reçu {ordre}")
    return ordre


def _rationnel_exact(x, quoi="valeur") -> Fraction:
    """Rationnel EXACT : int / Fraction / str numérique. Les flottants et bool sont REFUSÉS (exactitude)."""
    if isinstance(x, bool):
        raise ValueError(f"{quoi} : bool refusé (True n'est pas 1)")
    if isinstance(x, int):
        return Fraction(x)
    if isinstance(x, Fraction):
        return x
    if isinstance(x, str):
        try:
            return Fraction(x)
        except (ValueError, ZeroDivisionError):
            raise ValueError(f"{quoi} : chaîne non rationnelle {x!r}")
    raise ValueError(f"{quoi} : rationnel exact attendu (int/Fraction/str), reçu {x!r}")


def _point_evaluation(x, quoi="point x") -> Fraction:
    """Point d'évaluation : accepte AUSSI le flottant fini (converti EXACTEMENT en Fraction). NaN/inf refusés."""
    if isinstance(x, bool):
        raise ValueError(f"{quoi} : bool refusé")
    if isinstance(x, int):
        return Fraction(x)
    if isinstance(x, Fraction):
        return x
    if isinstance(x, float):
        if not math.isfinite(x):
            raise ValueError(f"{quoi} : NaN/inf refusé")
        return Fraction(x)
    if isinstance(x, str):
        try:
            return Fraction(x)
        except (ValueError, ZeroDivisionError):
            raise ValueError(f"{quoi} : chaîne non numérique {x!r}")
    raise ValueError(f"{quoi} : réel fini attendu, reçu {x!r}")


# ── coefficient de Maclaurin de degré k ──────────────────────────────────────────────────────────────────────────
def _coeff(nom: str, k: int, alpha=None) -> Fraction:
    if nom == "exp":
        return Fraction(1, math.factorial(k))
    if nom == "sin":
        if k % 2 == 0:
            return Fraction(0)
        return Fraction((-1) ** ((k - 1) // 2), math.factorial(k))
    if nom == "cos":
        if k % 2 == 1:
            return Fraction(0)
        return Fraction((-1) ** (k // 2), math.factorial(k))
    if nom == "sinh":
        return Fraction(1, math.factorial(k)) if k % 2 == 1 else Fraction(0)
    if nom == "cosh":
        return Fraction(1, math.factorial(k)) if k % 2 == 0 else Fraction(0)
    if nom == "ln1p":
        if k == 0:
            return Fraction(0)
        return Fraction((-1) ** (k + 1), k)
    if nom == "arctan":
        if k % 2 == 0:
            return Fraction(0)
        return Fraction((-1) ** ((k - 1) // 2), k)
    if nom == "geometrique":
        return Fraction(1)
    if nom == "binome":
        num = Fraction(1)
        for i in range(k):
            num *= (alpha - i)
        return num / math.factorial(k)
    raise ValueError(f"fonction hors catalogue : {nom!r}")  # défensif (jamais atteint après _exige_nom)


# ── (a) CATALOGUE : coefficients exacts ────────────────────────────────────────────────────────────────────────---
def taylor(nom: str, ordre: int, alpha=None):
    """Coefficients EXACTS (Fraction) du développement de Maclaurin de `nom` jusqu'à l'ordre `ordre`.

    Renvoie une liste de longueur ordre+1, l'indice = le degré. Pour "binome", `alpha` (rationnel exact)
    est OBLIGATOIRE ; sinon ValueError. Fonction hors catalogue / ordre invalide -> ValueError."""
    nom = _exige_nom(nom)
    ordre = _exige_ordre(ordre)
    if nom == "binome":
        if alpha is None:
            raise ValueError("série binomiale (1+x)^α : le paramètre alpha (rationnel) est obligatoire")
        alpha = _rationnel_exact(alpha, "alpha")
    return [_coeff(nom, k, alpha) for k in range(ordre + 1)]


# ── (d) RAYON DE CONVERGENCE ─────────────────────────────────────────────────────────────────────────────────────
def rayon_convergence(nom: str):
    """Rayon de convergence connu du développement : +∞ (exp/sin/cos/sinh/cosh) ou 1 (ln1p/arctan/geometrique/binome)."""
    nom = _exige_nom(nom)
    if nom in _RAYON_INFINI:
        return math.inf
    return 1  # ln(1+x), arctan, 1/(1−x), série binomiale (α rationnel non entier)


# ── (b) DÉVELOPPEMENT D'UN POLYNÔME AUTOUR DE a ──────────────────────────────────────────────────────────────────
def taylor_polynome(coeffs, a, ordre: int):
    """Développement de Taylor EXACT d'un polynôme p (coeffs degré-0-en-haut) autour du point a, à l'ordre `ordre`.

    coefficient de (x−a)ᵏ = p⁽ᵏ⁾(a)/k!, obtenu par dérivations successives exactes (calcul_infinitesimal).
    Renvoie une liste de Fraction de longueur ordre+1. coeffs/a doivent être rationnels EXACTS (flottant refusé)."""
    ordre = _exige_ordre(ordre)
    if not isinstance(coeffs, (list, tuple)) or len(coeffs) == 0:
        raise ValueError("coeffs invalide : liste/tuple non vide de rationnels attendue")
    poly = [_rationnel_exact(c, "coefficient") for c in coeffs]
    af = _rationnel_exact(a, "point a")
    out = []
    cur = poly
    fact = 1  # 0! au départ
    for k in range(ordre + 1):
        out.append(ci.evalue(cur, af) / fact)  # p⁽ᵏ⁾(a)/k!
        cur = ci.derivee(cur)
        fact *= (k + 1)
    return out


# ── (c) RESTE DE LAGRANGE ────────────────────────────────────────────────────────────────────────────────────────
def borne_reste_lagrange(nom: str, ordre: int, x, majorant_derivee) -> Fraction:
    """Borne de Lagrange : |R_n(x)| ≤ M·|x|^(n+1)/(n+1)!  avec M = majorant de |f⁽ⁿ⁺¹⁾| sur [0,x].

    `majorant_derivee` (M ≥ 0) est fourni par l'appelant. |x| ≥ rayon de convergence -> ValueError EXPLICITE."""
    nom = _exige_nom(nom)
    ordre = _exige_ordre(ordre)
    xf = _point_evaluation(x)
    M = _point_evaluation(majorant_derivee, "majorant_derivee")
    if M < 0:
        raise ValueError("majorant_derivee : un majorant de |dérivée| est ≥ 0")
    R = rayon_convergence(nom)
    if abs(xf) >= R:
        raise ValueError(f"|x|={abs(xf)} ≥ rayon de convergence {R} : le développement de {nom!r} ne converge pas là")
    n1 = ordre + 1
    return M * abs(xf) ** n1 / math.factorial(n1)


# ── (c') APPROXIMATION AVEC BORNE (jamais une valeur nue) ─────────────────────────────────────────────────────────
def approxime(nom: str, ordre: int, x):
    """Renvoie le couple (valeur_approchée, borne_erreur), Fraction exactes, avec |vrai − approx| ≤ borne_erreur.

    Le majorant M du reste est calculé de façon RIGOUREUSE : M=1 (sin/cos), M=3^⌈|x|⌉ ≥ e^|x| (exp/sinh/cosh).
    Pour les fonctions sans majorant automatique certain (ln1p/arctan/geometrique/binome) -> ValueError (abstention).
    |x| ≥ rayon de convergence -> ValueError."""
    nom = _exige_nom(nom)
    ordre = _exige_ordre(ordre)
    xf = _point_evaluation(x)
    if nom not in _MAJORANT_AUTO:
        raise ValueError(
            f"approxime : pas de majorant du reste rigoureux et automatique pour {nom!r} (abstention FAUX=0) — "
            f"utiliser borne_reste_lagrange avec un M certain"
        )
    R = rayon_convergence(nom)
    if abs(xf) >= R:
        raise ValueError(f"|x|={abs(xf)} ≥ rayon {R} : divergence")
    coeffs = taylor(nom, ordre)
    valeur = Fraction(0)
    for k, c in enumerate(coeffs):
        valeur += c * xf ** k
    absx = abs(xf)
    if nom in ("sin", "cos"):
        M = Fraction(1)  # |sin|, |cos| et leurs dérivées ≤ 1 partout
    else:  # exp, sinh, cosh : |f^(n+1)| ≤ cosh(|x|) ≤ e^|x| ≤ 3^⌈|x|⌉ (car e < 3)
        M = Fraction(3) ** math.ceil(absx)
    borne = M * absx ** (ordre + 1) / math.factorial(ordre + 1)
    return (valeur, borne)


if __name__ == "__main__":
    print("exp ordre 4 :", taylor("exp", 4))                 # [1, 1, 1/2, 1/6, 1/24]
    print("sin ordre 5 :", taylor("sin", 5))                 # [0, 1, 0, -1/6, 0, 1/120]
    print("approxime exp(0.1) ordre 4 :", approxime("exp", 4, 0.1))
    print("Taylor (x³-3x+2) en a=1 :", taylor_polynome([2, -3, 0, 1], 1, 3))  # [0, 0, 3, 1]
