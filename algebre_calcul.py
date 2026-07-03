"""ALGÈBRE — résolution EXACTE d'équations (linéaires, polynomiales), FAUX=0 (mission formule/concept 2026-06-29).

Posture (identique à `physique`/`maths_discretes`) : mécanisme EXACT via `fractions.Fraction` (pas de flottant ⇒ pas
d'arrondi présenté comme exact), abstention STRUCTURELLE — entrée invalide -> ValueError, et lorsqu'une racine est
IRRATIONNELLE on ne fabrique JAMAIS une décimale fausse : on rend la NATURE (nombre/typologie de racines) + le
discriminant exact, sans inventer une valeur rationnelle. Conservateur : faux négatif (abstention) toléré, faux
positif interdit.

Couvre les sujets bornés : « Équations linéaires », « Équations polynomiales ».
Vérifié en adverse par `valide_algebre_calcul.py` (cas à racines connues + soundness).
"""
from __future__ import annotations

from fractions import Fraction
from math import isqrt


def _frac(x) -> Fraction:
    """Convertit en Fraction EXACTE. Accepte int / Fraction / str rationnelle ; REFUSE le float (inexact) -> ValueError."""
    if isinstance(x, bool):
        raise ValueError("booléen refusé")
    if isinstance(x, Fraction):
        return x
    if isinstance(x, int):
        return Fraction(x)
    if isinstance(x, str):
        try:
            return Fraction(x)
        except ValueError:
            raise ValueError(f"chaîne non rationnelle: {x!r}")
    raise ValueError(f"coefficient rationnel (int/Fraction/str) attendu, reçu {type(x).__name__}")


def _carre_parfait(f: Fraction) -> Fraction | None:
    """Racine carrée EXACTE de f≥0 si f est un carré parfait de rationnel, sinon None (racine irrationnelle)."""
    if f < 0:
        return None
    n, d = f.numerator, f.denominator     # f réduite -> n,d ≥ 0, d > 0
    rn, rd = isqrt(n), isqrt(d)
    if rn * rn == n and rd * rd == d:
        return Fraction(rn, rd)
    return None


def equation_lineaire(a, b):
    """Résout a·x + b = 0 dans ℚ. Renvoie :
      ('unique', x)     — solution unique exacte (Fraction) si a ≠ 0 ;
      ('aucune', None)  — si a = 0 et b ≠ 0 (0 = b impossible) ;
      ('infinie', None) — si a = 0 et b = 0 (tout x convient).
    """
    a, b = _frac(a), _frac(b)
    if a == 0:
        return ("infinie", None) if b == 0 else ("aucune", None)
    return ("unique", -b / a)


def equation_quadratique(a, b, c):
    """Résout a·x² + b·x + c = 0 dans ℝ, EXACTEMENT (a ≠ 0 sinon ValueError -> utiliser equation_lineaire).
    Renvoie (statut, racines) :
      ('aucune_reelle', [])             — discriminant < 0 (pas de racine réelle) ;
      ('double', [r])                   — Δ = 0, racine double rationnelle ;
      ('deux_rationnelles', [r1, r2])   — Δ > 0 carré parfait, deux racines rationnelles exactes (triées) ;
      ('deux_irrationnelles', Δ)        — Δ > 0 non carré : deux racines réelles irrationnelles ; on rend le
                                          discriminant exact, JAMAIS une décimale fausse (FAUX=0).
    """
    a, b, c = _frac(a), _frac(b), _frac(c)
    if a == 0:
        raise ValueError("a = 0 : ce n'est pas quadratique (utiliser equation_lineaire)")
    delta = b * b - 4 * a * c
    if delta < 0:
        return ("aucune_reelle", [])
    if delta == 0:
        return ("double", [-b / (2 * a)])
    racine = _carre_parfait(delta)
    if racine is None:
        return ("deux_irrationnelles", delta)
    r1 = (-b - racine) / (2 * a)
    r2 = (-b + racine) / (2 * a)
    return ("deux_rationnelles", sorted([r1, r2]))


def evalue_polynome(coeffs, x):
    """Évalue p(x) = Σ coeffs[i]·x^i (coeffs du degré 0 vers le haut) EXACTEMENT (Horner). Renvoie une Fraction."""
    cs = [_frac(c) for c in coeffs]
    if not cs:
        raise ValueError("polynôme vide")
    xv = _frac(x)
    acc = Fraction(0)
    for c in reversed(cs):
        acc = acc * xv + c
    return acc


def est_racine(coeffs, x) -> bool:
    """Vrai ssi x est racine EXACTE de p (p(x) = 0). Déterministe, exact."""
    return evalue_polynome(coeffs, x) == 0


if __name__ == "__main__":
    print("2x-6=0 :", equation_lineaire(2, -6))
    print("0x+5=0 :", equation_lineaire(0, 5))
    print("0x+0=0 :", equation_lineaire(0, 0))
    print("x²-3x+2 :", equation_quadratique(1, -3, 2))
    print("x²-2x+1 :", equation_quadratique(1, -2, 1))
    print("x²+1     :", equation_quadratique(1, 0, 1))
    print("x²-2     :", equation_quadratique(1, 0, -2))
    print("2x²-7x+3 :", equation_quadratique(2, -7, 3))
    print("p=[2,-3,1] en x=2 (x²-3x+2) :", evalue_polynome([2, -3, 1], 2), "| racine ?", est_racine([2, -3, 1], 2))
