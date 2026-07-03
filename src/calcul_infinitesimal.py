"""CALCUL INFINITÉSIMAL — limites, dérivation, intégration EXACTES sur les polynômes, FAUX=0 (formule/concept 2026-06-29).

Un polynôme = liste de coefficients du degré 0 vers le haut (ℚ via Fraction). Dérivée et primitive sont EXACTES
(manipulation de coefficients), l'intégrale définie est EXACTE (théorème fondamental), la limite d'une fonction
rationnelle en un point est exacte (évaluation, ou simplification du facteur (x−a) en cas de 0/0). Abstention
STRUCTURELLE : limite réellement indéterminée (pôle non simplifiable, ∞) -> ValueError, jamais une valeur inventée.

Couvre les sujets bornés « Dérivation », « Intégration », « Limites et continuité ».
Vérifié en adverse par `valide_calcul_infinitesimal.py` (dérivées/intégrales connues + limites + soundness).
"""
from __future__ import annotations

from fractions import Fraction


def _poly(coeffs):
    out = []
    for c in coeffs:
        if isinstance(c, bool) or not isinstance(c, (int, Fraction)):
            if isinstance(c, str):
                out.append(Fraction(c))
                continue
            raise ValueError(f"coefficient rationnel attendu, reçu {c!r}")
        out.append(Fraction(c))
    while len(out) > 1 and out[-1] == 0:        # retire les zéros de tête (degré effectif)
        out.pop()
    return out if out else [Fraction(0)]


def evalue(coeffs, x) -> Fraction:
    """p(x) par schéma de Horner, exact."""
    cs = _poly(coeffs)
    xv = Fraction(x)
    acc = Fraction(0)
    for c in reversed(cs):
        acc = acc * xv + c
    return acc


def derivee(coeffs):
    """Coefficients de p'(x). [a0,a1,a2,...] -> [a1, 2a2, 3a3, ...]."""
    cs = _poly(coeffs)
    if len(cs) == 1:
        return [Fraction(0)]
    return [cs[i] * i for i in range(1, len(cs))]


def primitive(coeffs):
    """Coefficients d'une primitive (constante d'intégration = 0). [a0,a1,...] -> [0, a0, a1/2, a2/3, ...]."""
    cs = _poly(coeffs)
    return [Fraction(0)] + [cs[i] / (i + 1) for i in range(len(cs))]


def integrale_definie(coeffs, a, b) -> Fraction:
    """∫_a^b p(x) dx EXACTE (théorème fondamental : P(b) − P(a))."""
    P = primitive(coeffs)
    return evalue(P, b) - evalue(P, a)


def limite_polynome_en(coeffs, a) -> Fraction:
    """Limite d'un polynôme en a = p(a) (les polynômes sont continus partout)."""
    return evalue(coeffs, a)


def limite_rationnelle_en(num, den, a) -> Fraction:
    """Limite de num(x)/den(x) en x=a. Si den(a)≠0 -> num(a)/den(a). Si 0/0 -> on factorise (x−a) et on recommence.
    ValueError si pôle non levé (dénominateur → 0, numérateur ↛ 0) = limite infinie (on n'invente pas un nombre)."""
    num = _poly(num)
    den = _poly(den)
    for _ in range(64):
        na, da = evalue(num, a), evalue(den, a)
        if da != 0:
            return na / da
        if na != 0:
            raise ValueError(f"pôle en x={a} : limite infinie (indéfinie dans ℝ)")
        # 0/0 : (x−a) divise num et den -> on simplifie
        num = _division_par_x_moins_a(num, a)
        den = _division_par_x_moins_a(den, a)
    raise ValueError("simplification non terminée")


def _division_par_x_moins_a(coeffs, a):
    """Division synthétique exacte par (x − a), en supposant a racine (reste nul)."""
    cs = _poly(coeffs)
    a = Fraction(a)
    quotient = [Fraction(0)] * (len(cs) - 1) if len(cs) > 1 else [Fraction(0)]
    reste = Fraction(0)
    for i in range(len(cs) - 1, -1, -1):
        cur = cs[i] + reste * a
        if i == 0:
            reste = cur
        else:
            quotient[i - 1] = cur
            reste = cur
    return quotient


if __name__ == "__main__":
    print("d/dx (x³-3x+2) :", derivee([2, -3, 0, 1]))           # -> 3x²-3 = [-3,0,3]
    print("∫ x² de 0 à 3 :", integrale_definie([0, 0, 1], 0, 3))  # -> 9
    print("∫ (2x) de 1 à 4 :", integrale_definie([0, 2], 1, 4))   # -> 15
    print("lim (x²-1)/(x-1) en 1 :", limite_rationnelle_en([-1, 0, 1], [-1, 1], 1))  # -> 2
    print("lim (x²-4)/(x-2) en 2 :", limite_rationnelle_en([-4, 0, 1], [-2, 1], 2))  # -> 4
