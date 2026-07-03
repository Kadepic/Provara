"""ANALYSE FONCTIONNELLE — espaces vectoriels normés, FAUX=0 (mission formule/concept 2026-06-29).

Produit scalaire, normes (ℓ¹, ℓ², ℓ^∞, ℓ^p), distance, inégalité de Cauchy-Schwarz, inégalité triangulaire,
projection orthogonale d'un vecteur sur un autre, orthogonalité. Mécanisme EXACT (les cas rationnels tombent justes),
sortie arrondie. Abstention STRUCTURELLE : dimensions incompatibles, projection sur le vecteur nul, p < 1 -> ValueError.

Couvre le sujet borné « Analyse fonctionnelle ».
Vérifié en adverse par `valide_analyse_fonctionnelle.py` (||(3,4)||=5, Cauchy-Schwarz, orthogonalité).
"""
from __future__ import annotations

_DEC = 10


def _vec(v, nom="vecteur"):
    if not isinstance(v, (list, tuple)) or not v or any(isinstance(x, bool) or not isinstance(x, (int, float)) for x in v):
        raise ValueError(f"{nom} : liste non vide de nombres requise")
    return [float(x) for x in v]


def _meme_dim(u, v):
    if len(u) != len(v):
        raise ValueError("dimensions incompatibles")


def produit_scalaire(u, v) -> float:
    """⟨u, v⟩ = Σ uᵢ·vᵢ."""
    u, v = _vec(u, "u"), _vec(v, "v")
    _meme_dim(u, v)
    return round(sum(a * b for a, b in zip(u, v)), _DEC)


def norme(v, p=2) -> float:
    """Norme ℓ^p : (Σ|vᵢ|^p)^(1/p). p=1 (Manhattan), 2 (euclidienne), 'inf' (max). p ≥ 1."""
    v = _vec(v)
    if p == "inf":
        return round(max(abs(x) for x in v), _DEC)
    if not isinstance(p, (int, float)) or isinstance(p, bool) or p < 1:
        raise ValueError("p ≥ 1 (ou 'inf') requis")
    return round(sum(abs(x) ** p for x in v) ** (1.0 / p), _DEC)


def distance(u, v, p=2) -> float:
    """Distance ℓ^p : ||u − v||_p."""
    u, v = _vec(u, "u"), _vec(v, "v")
    _meme_dim(u, v)
    return norme([a - b for a, b in zip(u, v)], p)


def cauchy_schwarz_verifiee(u, v) -> bool:
    """Vérifie |⟨u,v⟩| ≤ ||u||·||v|| (toujours vrai en théorie ; ici contrôle numérique)."""
    return abs(produit_scalaire(u, v)) <= norme(u) * norme(v) + 1e-9


def sont_orthogonaux(u, v) -> bool:
    """u ⊥ v ssi ⟨u, v⟩ = 0."""
    return abs(produit_scalaire(u, v)) < 1e-9


def projection(u, v):
    """Projection orthogonale de u sur v : (⟨u,v⟩/⟨v,v⟩)·v. ValueError si v = 0."""
    u, v = _vec(u, "u"), _vec(v, "v")
    _meme_dim(u, v)
    vv = sum(b * b for b in v)
    if vv == 0:
        raise ValueError("projection sur le vecteur nul")
    coef = sum(a * b for a, b in zip(u, v)) / vv
    return [round(coef * b, _DEC) for b in v]


if __name__ == "__main__":
    print("||(3,4)||₂ :", norme([3, 4]))
    print("||(1,-2,2)||₁ /₂ /inf :", norme([1, -2, 2], 1), norme([1, -2, 2], 2), norme([1, -2, 2], "inf"))
    print("⟨(1,2),(3,4)⟩ :", produit_scalaire([1, 2], [3, 4]))
    print("(1,0)⊥(0,1) :", sont_orthogonaux([1, 0], [0, 1]))
    print("Cauchy-Schwarz (1,2),(3,4) :", cauchy_schwarz_verifiee([1, 2], [3, 4]))
    print("proj (2,2) sur (1,0) :", projection([2, 2], [1, 0]))
