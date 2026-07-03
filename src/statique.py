"""STATIQUE — équilibre des solides et des structures, FAUX=0 (mission formule/concept 2026-06-29).

Moment d'une force (F·d), condition d'équilibre (somme des moments signés = 0), loi du levier, centre de masse
d'un système de points, réactions d'appui d'une poutre sur deux appuis. Mécanisme EXACT, sortie 6 chiffres
significatifs. Abstention STRUCTURELLE : bras de levier / masse ≤ 0, listes incohérentes -> ValueError.

Couvre le sujet borné « Statique / équilibre des structures ».
Vérifié en adverse par `valide_statique.py` (levier, centre de masse, équilibre des moments).
"""
from __future__ import annotations

_SIG = 6


def _sig(x):
    if x == 0:
        return 0.0
    return float(f"{x:.{_SIG}g}")


def _num(*xs):
    for x in xs:
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            raise ValueError(f"nombre attendu, reçu {x!r}")


def moment(force, bras_levier) -> float:
    """Moment d'une force M = F·d (N·m)."""
    _num(force, bras_levier)
    return _sig(force * bras_levier)


def equilibre_moments(moments_signes, tol: float = 1e-9) -> bool:
    """True ssi la somme des moments signés est nulle (équilibre en rotation). Moments horaires/antihoraires de signes opposés."""
    if not isinstance(moments_signes, (list, tuple)):
        raise ValueError("liste de moments attendue")
    _num(*moments_signes)
    return abs(sum(moments_signes)) <= tol


def force_levier(charge, bras_charge, bras_effort) -> float:
    """Force d'effort nécessaire pour équilibrer une charge sur un levier : F = charge·bras_charge/bras_effort."""
    _num(charge)
    if charge < 0:
        raise ValueError("charge ≥ 0 requise")
    if bras_charge <= 0 or bras_effort <= 0:
        raise ValueError("bras de levier > 0 requis")
    return _sig(charge * bras_charge / bras_effort)


def centre_de_masse(masses, positions) -> float:
    """Position du centre de masse 1D : x_G = Σ(mᵢ·xᵢ)/Σmᵢ."""
    if not isinstance(masses, (list, tuple)) or not isinstance(positions, (list, tuple)):
        raise ValueError("listes attendues")
    if len(masses) != len(positions) or not masses:
        raise ValueError("listes de même longueur non vide requises")
    _num(*masses, *positions)
    total = sum(masses)
    if total <= 0:
        raise ValueError("masse totale > 0 requise")
    return _sig(sum(m * x for m, x in zip(masses, positions)) / total)


def reactions_appui(charge, position, longueur) -> tuple[float, float]:
    """Réactions (R_gauche, R_droite) d'une poutre de longueur L sur 2 appuis (extrémités), charge ponctuelle à
    `position` depuis la gauche. R_droite = charge·position/L ; R_gauche = charge − R_droite."""
    _num(charge, position, longueur)
    if charge < 0 or longueur <= 0 or not (0 <= position <= longueur):
        raise ValueError("charge ≥ 0, L > 0, 0 ≤ position ≤ L requis")
    r_droite = charge * position / longueur
    return (_sig(charge - r_droite), _sig(r_droite))


if __name__ == "__main__":
    print("moment 5N·2m :", moment(5, 2))
    print("équilibre [10,-10] :", equilibre_moments([10, -10]), "| [10,-5] :", equilibre_moments([10, -5]))
    print("levier charge 100, bras 1/4 :", force_levier(100, 1, 4))
    print("centre masse [2,1]@[0,3] :", centre_de_masse([2, 1], [0, 3]))
    print("réactions poutre charge 100 au milieu L=2 :", reactions_appui(100, 1, 2))
    print("réactions charge 100 à 1/4 L=4 :", reactions_appui(100, 1, 4))
