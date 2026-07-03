"""THÉORIE DE L'INFORMATION (Shannon) — grandeurs CALCULABLES, FAUX=0 (mission formule/concept 2026-06-29).

Entropie H(p) = −Σ pᵢ·log₂ pᵢ (bits), entropie conjointe, information mutuelle, divergence de Kullback-Leibler.
Mécanisme EXACT (convention 0·log0 = 0) ; abstention STRUCTURELLE : distribution invalide (proba < 0, somme ≠ 1
à tol près, support incompatible pour KL) -> ValueError, jamais un nombre faux. Sorties arrondies à 12 décimales
(précision honnête ; les valeurs dyadiques 1.0/2.0/1.5 tombent exactes).

Couvre le sujet borné « Théorie de l'information (Shannon) ».
Vérifié en adverse par `valide_information_calcul.py` (ancres connues : pièce équilibrée = 1 bit, dé à 4 faces = 2 bits…).
"""
from __future__ import annotations

import math

_TOL = 1e-9


def _valide_distribution(p):
    if not p:
        raise ValueError("distribution vide")
    xs = []
    for x in p:
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            raise ValueError(f"probabilité numérique attendue, reçu {x!r}")
        if x < -_TOL:
            raise ValueError(f"probabilité négative : {x}")
        xs.append(float(max(x, 0.0)))
    s = math.fsum(xs)
    if abs(s - 1.0) > 1e-6:
        raise ValueError(f"la distribution ne somme pas à 1 (somme = {s})")
    return xs


def entropie(p) -> float:
    """Entropie de Shannon H(p) en BITS = −Σ pᵢ·log₂ pᵢ (0·log0 = 0)."""
    xs = _valide_distribution(p)
    h = 0.0
    for pi in xs:
        if pi > 0.0:
            h -= pi * math.log2(pi)
    return round(h, 12)


def entropie_conjointe(matrice) -> float:
    """Entropie conjointe H(X,Y) d'une distribution jointe (liste de lignes = matrice de probabilités)."""
    plat = [v for ligne in matrice for v in ligne]
    return entropie(plat)


def information_mutuelle(matrice) -> float:
    """I(X;Y) = H(X) + H(Y) − H(X,Y) à partir de la distribution JOINTE p(x,y) (matrice). ≥ 0."""
    plat = [v for ligne in matrice for v in ligne]
    _valide_distribution(plat)                      # valide la jointe
    nlig = len(matrice)
    ncol = len(matrice[0]) if nlig else 0
    if any(len(l) != ncol for l in matrice):
        raise ValueError("matrice jointe non rectangulaire")
    px = [math.fsum(matrice[i]) for i in range(nlig)]
    py = [math.fsum(matrice[i][j] for i in range(nlig)) for j in range(ncol)]
    hx = entropie(px) if abs(math.fsum(px) - 1) <= 1e-6 else 0.0
    hy = entropie(py) if abs(math.fsum(py) - 1) <= 1e-6 else 0.0
    hxy = entropie(plat)
    return round(max(hx + hy - hxy, 0.0), 12)


def divergence_kl(p, q) -> float:
    """Divergence de Kullback-Leibler D(p‖q) = Σ pᵢ·log₂(pᵢ/qᵢ) en bits. ≥ 0 (Gibbs).
    ValueError si qᵢ = 0 alors que pᵢ > 0 (divergence infinie : on ne fabrique pas un nombre)."""
    xs = _valide_distribution(p)
    ys = _valide_distribution(q)
    if len(xs) != len(ys):
        raise ValueError("p et q de tailles différentes")
    d = 0.0
    for pi, qi in zip(xs, ys):
        if pi > 0.0:
            if qi <= 0.0:
                raise ValueError("support de q incompatible (qᵢ=0 mais pᵢ>0) : divergence infinie")
            d += pi * math.log2(pi / qi)
    return round(max(d, 0.0), 12)


if __name__ == "__main__":
    print("pièce équilibrée H :", entropie([0.5, 0.5]))
    print("dé 4 faces H :", entropie([0.25] * 4))
    print("certitude H :", entropie([1.0, 0.0]))
    print("H([0.5,0.25,0.25]) :", entropie([0.5, 0.25, 0.25]))
    print("I(X;Y) indépendants :", information_mutuelle([[0.25, 0.25], [0.25, 0.25]]))
    print("I(X;Y) parfait :", information_mutuelle([[0.5, 0.0], [0.0, 0.5]]))
    print("KL(p‖p) :", divergence_kl([0.5, 0.5], [0.5, 0.5]))
    print("KL([1,0]‖[.5,.5]) :", divergence_kl([1.0, 0.0], [0.5, 0.5]))
