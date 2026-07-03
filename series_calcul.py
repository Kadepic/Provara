"""SÉRIES & CONVERGENCE — sommes EXACTES et critères, FAUX=0 (mission formule/concept 2026-06-29).

Sommes arithmétiques et géométriques (finies, exactes sur ℚ), somme géométrique INFINIE (si |r|<1, valeur exacte
a/(1−r) ; sinon DIVERGE -> ValueError, on n'invente pas une limite), critères de convergence (géométrique |r|<1,
série de Riemann Σ1/n^s converge ssi s>1). Abstention STRUCTURELLE : série divergente interrogée sur sa somme
-> ValueError.

Couvre le sujet borné « Séries et convergence ».
Vérifié en adverse par `valide_series_calcul.py` (Σ1/2ⁿ=1, Gauss n(n+1)/2, harmonique diverge…).
"""
from __future__ import annotations

from fractions import Fraction


def _frac(x) -> Fraction:
    if isinstance(x, bool):
        raise ValueError("booléen refusé")
    if isinstance(x, (int, Fraction)):
        return Fraction(x)
    if isinstance(x, str):
        return Fraction(x)
    raise ValueError(f"rationnel (int/Fraction/str) attendu, reçu {type(x).__name__}")


def somme_arithmetique(premier, raison, n) -> Fraction:
    """Σ des n premiers termes d'une suite arithmétique = n·(2a + (n−1)d)/2. n ≥ 0 entier."""
    if not isinstance(n, int) or isinstance(n, bool) or n < 0:
        raise ValueError("n entier ≥ 0 requis")
    a, d = _frac(premier), _frac(raison)
    return Fraction(n) * (2 * a + (n - 1) * d) / 2


def somme_geometrique(premier, raison, n) -> Fraction:
    """Σ_{k=0}^{n-1} a·r^k (n termes), exact. r=1 -> n·a. n ≥ 0 entier."""
    if not isinstance(n, int) or isinstance(n, bool) or n < 0:
        raise ValueError("n entier ≥ 0 requis")
    a, r = _frac(premier), _frac(raison)
    if r == 1:
        return a * n
    return a * (1 - r ** n) / (1 - r)


def somme_geometrique_infinie(premier, raison) -> Fraction:
    """Σ_{k=0}^∞ a·r^k = a/(1−r) si |r| < 1 (convergente). Sinon DIVERGE -> ValueError (jamais une fausse limite)."""
    a, r = _frac(premier), _frac(raison)
    if abs(r) >= 1:
        raise ValueError(f"série géométrique divergente (|r| = {abs(r)} ≥ 1)")
    return a / (1 - r)


def converge_geometrique(raison) -> bool:
    """La série géométrique de raison r converge-t-elle ? (|r| < 1)."""
    return abs(_frac(raison)) < 1


def converge_riemann(s) -> bool:
    """La série de Riemann Σ 1/n^s converge-t-elle ? (ssi s > 1). s rationnel."""
    return _frac(s) > 1


def somme_carres(n) -> Fraction:
    """Σ_{k=1}^n k² = n(n+1)(2n+1)/6 (exact)."""
    if not isinstance(n, int) or isinstance(n, bool) or n < 0:
        raise ValueError("n entier ≥ 0 requis")
    return Fraction(n * (n + 1) * (2 * n + 1), 6)


if __name__ == "__main__":
    print("Gauss Σ1..100 :", somme_arithmetique(1, 1, 100))            # 5050
    print("Σ k² (1..10) :", somme_carres(10))                          # 385
    print("Σ 1/2^k (5 termes) :", somme_geometrique(1, Fraction(1, 2), 5))   # 31/16
    print("Σ 1/2^k infinie :", somme_geometrique_infinie(1, Fraction(1, 2)))  # 2
    print("Σ (1/2)^k k≥0 → 2 ; Σ a=1/2,r=1/2 :", somme_geometrique_infinie(Fraction(1, 2), Fraction(1, 2)))  # 1
    print("harmonique Σ1/n converge ?", converge_riemann(1), "| Σ1/n² ?", converge_riemann(2))
    try:
        somme_geometrique_infinie(1, 2)
    except ValueError as e:
        print("divergente :", e)
