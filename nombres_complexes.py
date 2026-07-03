"""ANALYSE COMPLEXE — opérations sur les nombres complexes, FAUX=0 (mission formule/concept 2026-06-29).

Module, argument, conjugué, somme/produit/quotient, puissance (de Moivre), racines n-ièmes. Un complexe = couple
(partie réelle, partie imaginaire). Mécanisme EXACT (les valeurs rationnelles tombent justes), sortie arrondie à
10 décimales. Abstention STRUCTURELLE : division par zéro, racine d'ordre ≤ 0 -> ValueError.

Couvre le sujet borné « Analyse complexe ».
Vérifié en adverse par `valide_nombres_complexes.py` (i²=−1, |3+4i|=5, racines de l'unité…).
"""
from __future__ import annotations

import math

_DEC = 10


def _c(z):
    if isinstance(z, (int, float)):
        return (float(z), 0.0)
    if isinstance(z, (tuple, list)) and len(z) == 2 and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in z):
        return (float(z[0]), float(z[1]))
    raise ValueError(f"complexe (re, im) attendu, reçu {z!r}")


def _r(z):
    return (round(z[0], _DEC), round(z[1], _DEC))


def module(z) -> float:
    """Module |z| = √(re² + im²)."""
    re, im = _c(z)
    return round(math.hypot(re, im), _DEC)


def argument(z) -> float:
    """Argument arg(z) en radians ∈ ]−π, π] (atan2). ValueError pour z = 0 (argument indéfini)."""
    re, im = _c(z)
    if re == 0 and im == 0:
        raise ValueError("argument de 0 indéfini")
    return round(math.atan2(im, re), _DEC)


def conjugue(z):
    re, im = _c(z)
    return _r((re, -im))


def somme(z1, z2):
    a, b = _c(z1)
    c, d = _c(z2)
    return _r((a + c, b + d))


def produit(z1, z2):
    """(a+bi)(c+di) = (ac−bd) + (ad+bc)i."""
    a, b = _c(z1)
    c, d = _c(z2)
    return _r((a * c - b * d, a * d + b * c))


def quotient(z1, z2):
    """z1/z2 = z1·conj(z2)/|z2|². ValueError si z2 = 0."""
    a, b = _c(z1)
    c, d = _c(z2)
    den = c * c + d * d
    if den == 0:
        raise ValueError("division par zéro complexe")
    return _r(((a * c + b * d) / den, (b * c - a * d) / den))


def puissance(z, n: int):
    """z^n (n entier) par la formule de de Moivre : module^n, argument·n."""
    if not isinstance(n, int) or isinstance(n, bool):
        raise ValueError("exposant entier requis")
    re, im = _c(z)
    if re == 0 and im == 0:
        if n == 0:
            raise ValueError("0^0 indéfini")
        return _r((0.0, 0.0))
    r = math.hypot(re, im) ** n
    theta = math.atan2(im, re) * n
    return _r((r * math.cos(theta), r * math.sin(theta)))


def racines_nieme(z, n: int):
    """Les n racines n-ièmes de z (liste de complexes). n ≥ 1."""
    if not isinstance(n, int) or isinstance(n, bool) or n < 1:
        raise ValueError("ordre n ≥ 1 requis")
    re, im = _c(z)
    r = math.hypot(re, im) ** (1.0 / n)
    theta = math.atan2(im, re)
    return [_r((r * math.cos((theta + 2 * math.pi * k) / n), r * math.sin((theta + 2 * math.pi * k) / n)))
            for k in range(n)]


if __name__ == "__main__":
    print("i² :", produit((0, 1), (0, 1)))
    print("|3+4i| :", module((3, 4)))
    print("(1+2i)(3+4i) :", produit((1, 2), (3, 4)))
    print("(1+i)/(1-i) :", quotient((1, 1), (1, -1)))
    print("(1+i)^2 :", puissance((1, 1), 2))
    print("racines cubiques de 1 :", racines_nieme((1, 0), 3))
