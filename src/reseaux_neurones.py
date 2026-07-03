"""RÉSEAUX DE NEURONES (mécanismes) — propagation avant EXACTE, FAUX=0 (mission formule/concept 2026-06-29).

Neurone formel (somme pondérée + biais + fonction d'activation), couche dense, fonctions d'activation (échelon,
signe, ReLU, sigmoïde, tanh). On calcule la SORTIE d'un réseau à poids donnés (inférence déterministe) — pas
l'apprentissage. Démonstration : un perceptron réalise les portes logiques ET/OU linéairement séparables.
Abstention STRUCTURELLE : dimensions incompatibles entrées/poids -> ValueError.

Couvre le sujet borné « Réseaux de neurones » (volet mécanismes/inférence).
Vérifié en adverse par `valide_reseaux_neurones.py` (portes ET/OU, activations connues, XOR non séparable).
"""
from __future__ import annotations

import math

_SIG = 9


def _sig(x):
    return round(x, _SIG)


def _num(*xs):
    for x in xs:
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            raise ValueError(f"nombre attendu, reçu {x!r}")


def echelon(x) -> int:
    """Fonction échelon de Heaviside : 1 si x ≥ 0, sinon 0."""
    _num(x)
    return 1 if x >= 0 else 0


def signe(x) -> int:
    """Fonction signe : +1 si x > 0, −1 si x < 0, 0 si x = 0."""
    _num(x)
    return (x > 0) - (x < 0)


def relu(x) -> float:
    """ReLU : max(0, x)."""
    _num(x)
    return _sig(max(0.0, float(x)))


def sigmoide(x) -> float:
    """Sigmoïde logistique : 1/(1+e^(−x)) ∈ (0,1)."""
    _num(x)
    return _sig(1.0 / (1.0 + math.exp(-x)))


def tanh(x) -> float:
    """Tangente hyperbolique ∈ (−1,1)."""
    _num(x)
    return _sig(math.tanh(x))


def potentiel(entrees, poids, biais) -> float:
    """Somme pondérée (potentiel d'activation) z = Σ wᵢ·xᵢ + b. dim(entrees) = dim(poids)."""
    if not isinstance(entrees, (list, tuple)) or not isinstance(poids, (list, tuple)):
        raise ValueError("entrées et poids = listes")
    if len(entrees) != len(poids):
        raise ValueError("dimensions entrées/poids incompatibles")
    _num(*entrees, *poids, biais)
    return _sig(sum(e * w for e, w in zip(entrees, poids)) + biais)


def neurone(entrees, poids, biais, activation="echelon"):
    """Sortie d'un neurone formel : activation(Σ wᵢxᵢ + b)."""
    z = potentiel(entrees, poids, biais)
    fns = {"echelon": echelon, "signe": signe, "relu": relu, "sigmoide": sigmoide, "tanh": tanh}
    if activation not in fns:
        raise ValueError(f"activation inconnue : {activation!r}")
    return fns[activation](z)


def couche_dense(entrees, matrice_poids, biais, activation="echelon"):
    """Sortie d'une couche dense : pour chaque neurone j, activation(Σ Wⱼᵢ·xᵢ + bⱼ).
    `matrice_poids` = liste de vecteurs de poids (un par neurone), `biais` = liste de biais."""
    if not isinstance(matrice_poids, (list, tuple)) or not isinstance(biais, (list, tuple)):
        raise ValueError("matrice de poids et biais = listes")
    if len(matrice_poids) != len(biais):
        raise ValueError("nombre de neurones incohérent (poids vs biais)")
    return [neurone(entrees, w, b, activation) for w, b in zip(matrice_poids, biais)]


if __name__ == "__main__":
    # Perceptron ET : w=[1,1], b=-1.5 ; OU : w=[1,1], b=-0.5
    for x in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        print(f"  ET{x} = {neurone(list(x), [1, 1], -1.5)} | OU{x} = {neurone(list(x), [1, 1], -0.5)}")
    print("ReLU(-2)/ReLU(3) :", relu(-2), relu(3))
    print("sigmoïde(0) :", sigmoide(0), "| tanh(0) :", tanh(0))
    print("couche 2 neurones :", couche_dense([1, 1], [[1, 1], [1, 1]], [-1.5, -0.5]))
