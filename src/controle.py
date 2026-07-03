"""AUTOMATIQUE / CONTRÔLE — stabilité d'un système linéaire, FAUX=0 (mission formule/concept 2026-06-29).

Critère de Routh-Hurwitz : un système linéaire (polynôme caractéristique) est STABLE ssi toutes les racines ont une
partie réelle strictement négative. On le décide EXACTEMENT (sur ℚ) via la table de Routh — sans calculer les racines :
le système est stable ssi tous les éléments de la 1ʳᵉ colonne sont non nuls et de MÊME signe. Mécanisme exact ;
abstention STRUCTURELLE : zéro dans la 1ʳᵉ colonne (cas singulier / marginal) -> ValueError, jamais un verdict faux.

Couvre le sujet borné « Automatique / contrôle ».
Vérifié en adverse par `valide_controle.py` (polynômes stables/instables connus, comparaison aux racines).
"""
from __future__ import annotations

from fractions import Fraction


def _coeffs(p):
    """Coefficients du POLYNÔME CARACTÉRISTIQUE, du degré le plus HAUT vers le plus bas (a_n, …, a_0)."""
    if not isinstance(p, (list, tuple)) or len(p) < 2:
        raise ValueError("polynôme de degré ≥ 1 attendu (liste a_n..a_0)")
    out = []
    for c in p:
        if isinstance(c, bool) or not isinstance(c, (int, Fraction)):
            raise ValueError(f"coefficient rationnel attendu, reçu {c!r}")
        out.append(Fraction(c))
    if out[0] == 0:
        raise ValueError("coefficient dominant a_n ≠ 0 requis")
    return out


def table_routh(p):
    """Construit la table de Routh (liste de lignes, Fractions). ValueError si un pivot s'annule (cas singulier)."""
    a = _coeffs(p)
    n = len(a) - 1
    # deux premières lignes : coefficients pairs / impairs
    l1 = a[0::2]
    l2 = a[1::2]
    while len(l1) > len(l2):
        l2 = l2 + [Fraction(0)]
    while len(l2) > len(l1):
        l1 = l1 + [Fraction(0)]
    table = [list(l1), list(l2)]
    for _ in range(n - 1):
        haut, bas = table[-2], table[-1]
        pivot = bas[0]
        if pivot == 0:
            raise ValueError("zéro dans la 1ʳᵉ colonne : cas singulier (stabilité non décidable par Routh simple)")
        nouvelle = []
        for j in range(len(haut) - 1):
            nouvelle.append((pivot * haut[j + 1] - haut[0] * bas[j + 1]) / pivot)
        nouvelle.append(Fraction(0))
        table.append(nouvelle)
    return table


def est_stable(p) -> bool:
    """True ssi le système de polynôme caractéristique `p` est stable (toutes racines à partie réelle < 0).
    Critère de Routh-Hurwitz : 1ʳᵉ colonne sans zéro et de signe constant. ValueError sur cas singulier."""
    table = table_routh(p)
    premiere_colonne = [ligne[0] for ligne in table]
    if any(x == 0 for x in premiere_colonne):
        raise ValueError("zéro en 1ʳᵉ colonne : cas marginal")
    signes = {1 if x > 0 else -1 for x in premiere_colonne}
    return len(signes) == 1


def changements_de_signe(p) -> int:
    """Nombre de changements de signe dans la 1ʳᵉ colonne = nombre de racines à partie réelle POSITIVE (instables)."""
    table = table_routh(p)
    col = [ligne[0] for ligne in table]
    if any(x == 0 for x in col):
        raise ValueError("zéro en 1ʳᵉ colonne : cas marginal")
    n = 0
    for i in range(1, len(col)):
        if (col[i] > 0) != (col[i - 1] > 0):
            n += 1
    return n


if __name__ == "__main__":
    print("s²+2s+1 stable :", est_stable([1, 2, 1]))          # racines -1,-1 -> stable
    print("s²-2s+1 stable :", est_stable([1, -2, 1]))         # racines +1,+1 -> instable
    print("s³+2s²+3s+4... :", est_stable([1, 2, 3, 4]))       # Routh -> stable
    print("s³+s²+s+6 :", est_stable([1, 1, 1, 6]))            # -> instable
    print("racines instables de s³+s²+s+6 :", changements_de_signe([1, 1, 1, 6]))
