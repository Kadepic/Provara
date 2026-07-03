"""GÉOMÉTRIE PROJECTIVE — birapport et invariants, FAUX=0 (mission formule/concept 2026-06-29).

Le BIRAPPORT (cross-ratio) de quatre points alignés (a,b;c,d) = ((c−a)(d−b))/((c−b)(d−a)) est l'invariant
fondamental de la géométrie projective (préservé par toute homographie). Calcul EXACT sur ℚ (Fraction). Division
harmonique (birapport = −1), conjugué harmonique. Abstention STRUCTURELLE : points confondus créant une division
par zéro -> ValueError.

Couvre le sujet borné « Géométrie projective ».
Vérifié en adverse par `valide_geometrie_projective.py` (birapports connus, invariance par homographie, harmonique).
"""
from __future__ import annotations

from fractions import Fraction


def _frac(x) -> Fraction:
    if isinstance(x, bool) or not isinstance(x, (int, Fraction)):
        if isinstance(x, str):
            return Fraction(x)
        raise ValueError(f"rationnel attendu, reçu {x!r}")
    return Fraction(x)


def birapport(a, b, c, d) -> Fraction:
    """Birapport (a,b;c,d) = ((c−a)(d−b)) / ((c−b)(d−a)). Points sur une droite (coordonnées). Exact sur ℚ.
    ValueError si c=b ou d=a (dénominateur nul)."""
    a, b, c, d = _frac(a), _frac(b), _frac(c), _frac(d)
    num = (c - a) * (d - b)
    den = (c - b) * (d - a)
    if den == 0:
        raise ValueError("birapport indéfini (points confondus au dénominateur)")
    return num / den


def homographie(x, p, q, r, s):
    """Applique l'homographie x ↦ (p·x + q)/(r·x + s) (transformation projective de la droite). r·x+s ≠ 0."""
    x, p, q, r, s = _frac(x), _frac(p), _frac(q), _frac(r), _frac(s)
    if p * s - q * r == 0:
        raise ValueError("homographie dégénérée (déterminant nul)")
    den = r * x + s
    if den == 0:
        raise ValueError("image à l'infini (dénominateur nul)")
    return (p * x + q) / den


def est_division_harmonique(a, b, c, d) -> bool:
    """Vrai ssi (a,b;c,d) forment une division harmonique : birapport = −1."""
    return birapport(a, b, c, d) == -1


def conjugue_harmonique(a, b, c) -> Fraction:
    """Quatrième point d harmonique : l'unique d tel que (a,b;c,d) = −1. Dérivée de birapport=−1 :
    d = (c(a+b) − 2ab)/(2c−a−b). ValueError si 2c−a−b = 0 (conjugué à l'infini, ex. c milieu de [a,b])."""
    a, b, c = _frac(a), _frac(b), _frac(c)
    den = 2 * c - a - b
    if den == 0:
        raise ValueError("conjugué harmonique à l'infini")
    return (c * (a + b) - 2 * a * b) / den


if __name__ == "__main__":
    print("birapport(0,1,2,3) :", birapport(0, 1, 2, 3))
    print("birapport(0,2,1,3) :", birapport(0, 2, 1, 3))
    # invariance : applique une homographie aux 4 points -> même birapport
    pts = [0, 1, 3, 7]
    h = [homographie(x, 2, 1, 1, 3) for x in pts]
    print("birapport avant :", birapport(*pts), "| après homographie :", birapport(*h))
    d = conjugue_harmonique(0, 6, 2)
    print("conjugué harmonique de 2 / (0,6) :", d, "-> harmonique ?", est_division_harmonique(0, 6, 2, d))
