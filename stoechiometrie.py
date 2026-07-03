"""STŒCHIOMÉTRIE — équilibrage EXACT d'équations chimiques, FAUX=0 (mission formule/concept 2026-06-29).

L'équilibrage = trouver les plus petits coefficients entiers positifs annulant le bilan atomique. C'est le noyau
(nullspace) de la matrice atomes×espèces (réactifs +, produits −), calculé EXACTEMENT sur ℚ puis ramené aux plus
petits entiers. GARANTIE structurelle vérifiée : avec les coefficients rendus, chaque élément est conservé (autant
d'atomes à gauche qu'à droite). Abstention STRUCTURELLE : formule invalide, équation impossible à équilibrer, ou
solution non unique/non positive -> ValueError (jamais une équation fausse). Réutilise le parseur de `chimie.py`.

Couvre le sujet borné « Stœchiométrie (équilibrage d'équations) ».
Vérifié en adverse par `valide_stoechiometrie.py` (réactions connues + conservation des atomes + soundness).
"""
from __future__ import annotations

from fractions import Fraction
from math import gcd

import chimie


def _atomes(formule: str) -> dict:
    st, comp = chimie.composition(formule)
    if st != chimie.VERIFIE or not comp:
        raise ValueError(f"formule chimique invalide : {formule!r}")
    return comp


def _rref(M):
    """Forme échelonnée réduite (Gauss-Jordan exact sur Fractions). Renvoie (matrice, colonnes pivots)."""
    M = [row[:] for row in M]
    rows = len(M)
    cols = len(M[0]) if rows else 0
    pivots = []
    r = 0
    for c in range(cols):
        piv = next((i for i in range(r, rows) if M[i][c] != 0), None)
        if piv is None:
            continue
        M[r], M[piv] = M[piv], M[r]
        pv = M[r][c]
        M[r] = [x / pv for x in M[r]]
        for i in range(rows):
            if i != r and M[i][c] != 0:
                f = M[i][c]
                M[i] = [a - f * b for a, b in zip(M[i], M[r])]
        pivots.append(c)
        r += 1
        if r == rows:
            break
    return M, pivots


def _noyau(M, ncols):
    """Base du noyau (vecteurs solutions de M·x = 0), exacte sur ℚ."""
    rref, pivots = _rref(M) if M else ([], [])
    libres = [c for c in range(ncols) if c not in pivots]
    base = []
    for f in libres:
        vec = [Fraction(0)] * ncols
        vec[f] = Fraction(1)
        for r, pc in enumerate(pivots):
            vec[pc] = -rref[r][f]
        base.append(vec)
    return base


def equilibre(reactifs, produits) -> list[int]:
    """Renvoie les plus petits coefficients entiers positifs [réactifs..., produits...] qui équilibrent l'équation.
    ValueError si une formule est invalide, si l'équation n'est pas équilibrable de façon unique, ou si la solution
    n'est pas strictement positive (réaction non physique)."""
    if not reactifs or not produits:
        raise ValueError("réactifs et produits requis")
    especes = list(reactifs) + list(produits)
    comps = [_atomes(f) for f in especes]
    elements = sorted(set().union(*[set(c) for c in comps]))
    nr = len(reactifs)
    # matrice atomes × espèces : réactifs +, produits −
    A = [[Fraction(comps[j].get(el, 0) * (1 if j < nr else -1)) for j in range(len(especes))]
         for el in elements]
    base = _noyau(A, len(especes))
    if len(base) != 1:
        raise ValueError(f"équation non équilibrable de façon unique (dim noyau = {len(base)})")
    v = base[0]
    # ramener aux entiers : ×PPCM des dénominateurs
    denom = 1
    for x in v:
        denom = denom * x.denominator // gcd(denom, x.denominator)
    ent = [int(x * denom) for x in v]
    g = 0
    for x in ent:
        g = gcd(g, abs(x))
    if g == 0:
        raise ValueError("solution nulle")
    ent = [x // g for x in ent]
    if all(x < 0 for x in ent):
        ent = [-x for x in ent]
    if any(x <= 0 for x in ent):
        raise ValueError("pas de solution entière strictement positive (réaction non physique)")
    # GARANTIE : conservation de chaque élément
    for el in elements:
        gauche = sum(ent[j] * comps[j].get(el, 0) for j in range(nr))
        droite = sum(ent[j] * comps[j].get(el, 0) for j in range(nr, len(especes)))
        if gauche != droite:
            raise ValueError("échec de conservation (anomalie interne)")
    return ent


def equation_equilibree(reactifs, produits) -> str:
    """Rend l'équation équilibrée en texte (ex. '2 H2 + O2 -> 2 H2O')."""
    coeffs = equilibre(reactifs, produits)
    especes = list(reactifs) + list(produits)
    nr = len(reactifs)
    def terme(c, f):
        return f if c == 1 else f"{c} {f}"
    g = " + ".join(terme(coeffs[j], especes[j]) for j in range(nr))
    d = " + ".join(terme(coeffs[j], especes[j]) for j in range(nr, len(especes)))
    return f"{g} -> {d}"


if __name__ == "__main__":
    for r, p in [(["H2", "O2"], ["H2O"]), (["CH4", "O2"], ["CO2", "H2O"]),
                 (["Fe", "O2"], ["Fe2O3"]), (["C2H6", "O2"], ["CO2", "H2O"]),
                 (["Al", "HCl"], ["AlCl3", "H2"]), (["KMnO4", "HCl"], ["KCl", "MnCl2", "H2O", "Cl2"])]:
        print(f"  {equation_equilibree(r, p)}   coeffs={equilibre(r, p)}")
