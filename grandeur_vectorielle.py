"""
GRANDEUR VECTORIELLE DIMENSIONNÉE — grandeurs non-scalaires (brique représentation, 2026-07-02).

POURQUOI : le monde physique ne se réduit pas à des scalaires — une vitesse, une force, un champ ont une DIRECTION.
`grandeur.py` ne porte qu'un scalaire ; ici un vecteur de composantes numériques porte une DIMENSION commune
(unité SI via `dimensions.Dimension`), avec l'algèbre vectorielle dimensionnellement sûre. Socle du raisonnement
sur les mécanismes directionnels (forces, flux, champs) — donc de l'invention physique au-delà du scalaire.

FAUX=0 (hérité de l'algèbre dimensionnelle) :
  • Addition/soustraction REFUSÉE si les deux vecteurs n'ont pas la MÊME dimension (ValueError) — jamais additionner
    une vitesse et une force. Arités différentes -> ValueError (jamais tronquer/compléter silencieusement).
  • Le produit scalaire porte la dimension PRODUIT (dim_a · dim_b) ; la norme porte la dimension des composantes —
    calculées par l'algèbre, jamais supposées.
  • Comparaison exacte (composantes ET dimension). Déterministe, stdlib pur, immuable, souverain.
"""
from __future__ import annotations

import math

from dimensions import Dimension, SANS


class GrandeurVectorielle:
    """Vecteur de composantes numériques + une Dimension commune. Immuable."""

    __slots__ = ("composantes", "dimension")

    def __init__(self, composantes, dimension: Dimension = SANS):
        comp = tuple(float(c) for c in composantes)
        if not comp:
            raise ValueError("un vecteur doit avoir au moins une composante")
        if not isinstance(dimension, Dimension):
            raise TypeError("dimension doit être une dimensions.Dimension")
        object.__setattr__(self, "composantes", comp)
        object.__setattr__(self, "dimension", dimension)

    def __setattr__(self, *a):
        raise AttributeError("GrandeurVectorielle est immuable")

    @property
    def arite(self) -> int:
        return len(self.composantes)

    def _meme_espace(self, autre, op: str):
        if not isinstance(autre, GrandeurVectorielle):
            raise TypeError(f"{op} exige une autre GrandeurVectorielle")
        if self.arite != autre.arite:
            raise ValueError(f"{op} : arités différentes ({self.arite} vs {autre.arite})")

    def __add__(self, autre) -> "GrandeurVectorielle":
        self._meme_espace(autre, "addition")
        if self.dimension != autre.dimension:
            raise ValueError(f"addition de dimensions incompatibles : {self.dimension.formule()} + "
                             f"{autre.dimension.formule()} (jamais additionner des grandeurs hétérogènes)")
        return GrandeurVectorielle((a + b for a, b in zip(self.composantes, autre.composantes)), self.dimension)

    def __sub__(self, autre) -> "GrandeurVectorielle":
        self._meme_espace(autre, "soustraction")
        if self.dimension != autre.dimension:
            raise ValueError(f"soustraction de dimensions incompatibles : {self.dimension.formule()} - "
                             f"{autre.dimension.formule()}")
        return GrandeurVectorielle((a - b for a, b in zip(self.composantes, autre.composantes)), self.dimension)

    def mul_scalaire(self, k: float, dim_scalaire: Dimension = SANS) -> "GrandeurVectorielle":
        """Multiplication par un scalaire éventuellement DIMENSIONNÉ (k, dim_scalaire) : composantes ×k,
        dimension résultante = dimension · dim_scalaire (algèbre dimensionnelle). k pur -> dimension inchangée."""
        return GrandeurVectorielle((k * c for c in self.composantes), self.dimension * dim_scalaire)

    def produit_scalaire(self, autre) -> "tuple":
        """Produit scalaire Σ aᵢ·bᵢ -> (valeur, dimension_produit). Dimension = dim_a · dim_b (calculée). Les deux
        vecteurs peuvent avoir des dimensions DIFFÉRENTES (ex. force · déplacement = travail) mais MÊME arité."""
        self._meme_espace(autre, "produit scalaire")
        val = sum(a * b for a, b in zip(self.composantes, autre.composantes))
        return (val, self.dimension * autre.dimension)

    def norme(self) -> "tuple":
        """Norme euclidienne √(Σ aᵢ²) -> (valeur, dimension). La norme conserve la DIMENSION des composantes."""
        return (math.sqrt(sum(c * c for c in self.composantes)), self.dimension)

    def __eq__(self, autre) -> bool:
        return (isinstance(autre, GrandeurVectorielle) and self.composantes == autre.composantes
                and self.dimension == autre.dimension)

    def __hash__(self):
        return hash((self.composantes, self.dimension))

    def __repr__(self):
        d = self.dimension.formule()
        return f"GrandeurVectorielle({self.composantes}, {d})"
