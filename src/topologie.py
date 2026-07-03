"""TOPOLOGIE GÉNÉRALE — invariants EXACTS (entiers), directement appelables, FAUX=0 (mission formule/concept 2026-06-29).

Posture (identique à `physique`/`maths_discretes`) : le MÉCANISME est exact (formules d'invariants topologiques,
arithmétique entière sans flottant), et l'abstention est STRUCTURELLE — toute entrée invalide lève `ValueError`
(jamais un résultat faux). Conservateur : faux négatif (abstention) toléré, faux POSITIF interdit.

Couvre la caractéristique d'Euler–Poincaré et le genre des surfaces fermées :

  • caracteristique_euler(V,E,F) = V − E + F            (complexe cellulaire / polyèdre)
        - polyèdre convexe (homéomorphe à la sphère S²) : χ = 2  (formule d'Euler, 1752)
        - tore T² : χ = 0 ;  genre g orientable : χ = 2 − 2g
  • caracteristique_euler_betti([b0,b1,b2,…]) = Σ (−1)^i b_i      (alternée des nombres de Betti)
  • genre_depuis_euler(χ) = (2 − χ)/2     genre d'une surface fermée ORIENTABLE (χ pair, χ ≤ 2)
        - sphère χ=2 → genre 0 ; tore χ=0 → genre 1 ; bitore χ=−2 → genre 2
  • genre_non_orientable_depuis_euler(χ) = 2 − χ   (nombre de bonnets croisés, χ ≤ 1)
        - plan projectif RP² χ=1 → 1 ; bouteille de Klein χ=0 → 2
  • est_homeomorphe_sphere(V,E,F) = (χ == 2)    pour une surface polyédrale fermée connexe
  • caracteristique_euler_somme_connexe(χ1,χ2) = χ1 + χ2 − 2   (χ d'une somme connexe de surfaces fermées)

SOUNDNESS : V,E,F (et χ, Betti) doivent être des ENTIERS (bool exclu) ; V,E,F < 0 → ValueError ; un χ qui ne
correspond pas à une surface fermée valide (genre négatif / parité incompatible) → ValueError (abstention), jamais
un genre faux. Vérifié en adverse par `valide_topologie.py` (ancres polyèdres réguliers / Császár / Betti + soundness).
"""
from __future__ import annotations


def _entier(x, *, signe_positif: bool = False):
    """Valide qu'un argument est un entier Python (bool exclu). Optionnellement ≥ 0."""
    if not isinstance(x, int) or isinstance(x, bool):
        raise ValueError(f"entier attendu, reçu {x!r}")
    if signe_positif and x < 0:
        raise ValueError(f"entier ≥ 0 attendu, reçu {x!r}")
    return x


# ── CARACTÉRISTIQUE D'EULER ─────────────────────────────────────────────────────────────────────────────────────
def caracteristique_euler(V: int, E: int, F: int) -> int:
    """χ = V − E + F (sommets − arêtes + faces). Pour un polyèdre convexe (sphère) χ = 2 ; pour un tore χ = 0.

    V, E, F doivent être des entiers ≥ 0 (compte d'éléments). Sinon ValueError (abstention, jamais de résultat faux).
    """
    _entier(V, signe_positif=True)
    _entier(E, signe_positif=True)
    _entier(F, signe_positif=True)
    return V - E + F


def caracteristique_euler_betti(betti) -> int:
    """χ = Σ_i (−1)^i b_i (somme alternée des nombres de Betti b_0, b_1, b_2, …).

    Mécanisme indépendant de V−E+F (homologie) ; ex. sphère [1,0,1]→2, tore [1,2,1]→0, bitore [1,4,1]→−2.
    Chaque b_i doit être un entier ≥ 0. Sinon ValueError.
    """
    betti = list(betti)
    if not betti:
        raise ValueError("au moins un nombre de Betti (b_0) attendu")
    chi = 0
    for i, b in enumerate(betti):
        _entier(b, signe_positif=True)
        chi += (-1) ** i * b
    return chi


def caracteristique_euler_somme_connexe(chi1: int, chi2: int) -> int:
    """χ(A # B) = χ(A) + χ(B) − 2 pour la somme connexe de deux surfaces fermées.

    Ex. tore # tore : 0 + 0 − 2 = −2 (bitore, genre 2). χ1, χ2 entiers.
    """
    _entier(chi1)
    _entier(chi2)
    return chi1 + chi2 - 2


# ── GENRE D'UNE SURFACE FERMÉE ──────────────────────────────────────────────────────────────────────────────────
def genre_depuis_euler(chi: int) -> int:
    """Genre g d'une surface fermée ORIENTABLE : g = (2 − χ)/2 (puisque χ = 2 − 2g).

    Valide seulement si χ est un entier PAIR et χ ≤ 2 (sinon le genre serait non entier ou négatif → ValueError).
    Sphère χ=2 → 0 ; tore χ=0 → 1 ; bitore χ=−2 → 2.
    """
    _entier(chi)
    if chi > 2:
        raise ValueError(f"χ = {chi} > 2 : pas de surface fermée orientable (genre négatif)")
    if (2 - chi) % 2 != 0:
        raise ValueError(f"χ = {chi} impair : pas de surface fermée orientable (genre non entier)")
    return (2 - chi) // 2


def genre_non_orientable_depuis_euler(chi: int) -> int:
    """Genre non orientable (nombre de bonnets croisés) k = 2 − χ pour une surface fermée NON orientable.

    Valide seulement si χ ≤ 1 (k ≥ 1). Plan projectif RP² χ=1 → 1 ; bouteille de Klein χ=0 → 2.
    """
    _entier(chi)
    if chi > 1:
        raise ValueError(f"χ = {chi} > 1 : pas de surface fermée non orientable (k ≤ 0)")
    return 2 - chi


# ── CLASSIFICATION ──────────────────────────────────────────────────────────────────────────────────────────────
def est_homeomorphe_sphere(V: int, E: int, F: int) -> bool:
    """Vrai ssi χ = V − E + F = 2.

    Pour une surface polyédrale FERMÉE CONNEXE, χ = 2 caractérise (à homéomorphisme près) la sphère S² —
    c'est précisément la formule d'Euler des polyèdres convexes. Précondition honnête : (V,E,F) décrit une telle
    surface ; la fonction teste l'invariant. Entrées non entières/négatives → ValueError.
    """
    return caracteristique_euler(V, E, F) == 2


if __name__ == "__main__":
    print("χ cube       (8,12,6)  :", caracteristique_euler(8, 12, 6))
    print("χ tétraèdre  (4,6,4)   :", caracteristique_euler(4, 6, 4))
    print("χ octaèdre   (6,12,8)  :", caracteristique_euler(6, 12, 8))
    print("χ Császár(tore)(7,21,14):", caracteristique_euler(7, 21, 14))
    print("genre sphère χ=2 :", genre_depuis_euler(2), "| tore χ=0 :", genre_depuis_euler(0),
          "| bitore χ=-2 :", genre_depuis_euler(-2))
    print("k RP² χ=1 :", genre_non_orientable_depuis_euler(1), "| Klein χ=0 :", genre_non_orientable_depuis_euler(0))
    print("homéomorphe sphère cube :", est_homeomorphe_sphere(8, 12, 6),
          "| tore :", est_homeomorphe_sphere(7, 21, 14))
    print("χ tore#tore :", caracteristique_euler_somme_connexe(0, 0))
