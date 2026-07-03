"""
GRANDEUR TYPÉE — brique Vague 1 (valeur + unité/dimension + incertitude). Dépend de dimensions.py.

POURQUOI : une invention se raisonne sur des GRANDEURS, pas sur des nombres nus. Attacher une dimension à chaque
valeur permet à l'arithmétique d'être SOUND : on ne peut pas additionner 3 kg et 2 s, et 5 N × 2 m donne bien 10 J.
C'est ce qui rend « évaluer une formule » et « calculer un écart au théorique » dignes de confiance.

MODÈLE : une Grandeur = (valeur en unité SI de base, Dimension, incertitude-type absolue en SI). On stocke TOUT en
SI de base -> l'arithmétique est triviale et sûre ; on convertit à l'affichage/à la sortie via .en(unité).

FAUX=0 :
  • Additionner/soustraire/comparer deux grandeurs de dimensions DIFFÉRENTES lève `IncoherenceDimensionnelle`
    (jamais un nombre faux) — le filtre de dimensions.py appliqué aux valeurs.
  • Le produit/quotient combinent les dimensions exactement (via l'algèbre de dimensions.py).
  • Propagation d'incertitude au 1er ordre (linéaire) : somme -> √(u₁²+u₂²) ; produit -> combinaison RELATIVE.
    (Pour les cas non linéaires / corrélés, c'est propagation.py — Monte-Carlo — qui prend le relais ; ici on reste
    au 1er ordre, honnête et déterministe. u=0 par défaut = valeur exacte.)

Stdlib pur, déterministe, souverain.
"""
from __future__ import annotations

import math

import dimensions as D


class IncoherenceDimensionnelle(Exception):
    """Levée quand une opération met en jeu des dimensions incompatibles (addition/comparaison hétérogène).
    C'est la DÉTECTION de l'erreur, pas un calcul silencieux — cœur FAUX=0."""


class Grandeur:
    """Valeur physique typée. Stockée en unité SI de base. `u` = incertitude-type absolue (SI), 0 = exacte."""

    __slots__ = ("valeur", "dim", "u")

    def __init__(self, valeur_si, dimension: D.Dimension, u=0.0):
        self.valeur = valeur_si
        self.dim = dimension
        self.u = float(u)
        if self.u < 0:
            raise ValueError("incertitude négative")

    # — construction depuis une unité nommée —
    @staticmethod
    def depuis(valeur, unite: str, u=0.0):
        """Crée une Grandeur depuis une valeur exprimée dans `unite` (symbole connu de dimensions.UNITES).
        `u` est l'incertitude EXPRIMÉE DANS LA MÊME UNITÉ. Unité inconnue -> ValueError (jamais deviné)."""
        obj = D.UNITES.get(unite)
        if not isinstance(obj, D.Unite):
            raise ValueError(f"unité inconnue : {unite!r}")
        # conversion affine correcte : la valeur passe par vers_si ; l'incertitude ne subit QUE le facteur d'échelle.
        return Grandeur(obj.vers_si(valeur), obj.dimension, abs(u) * float(obj.facteur))

    # — sortie —
    def en(self, unite: str):
        """Valeur exprimée dans `unite` (doit être commensurable). Incommensurable/inconnue -> None (HORS)."""
        obj = D.UNITES.get(unite)
        if not isinstance(obj, D.Unite) or obj.dimension != self.dim:
            return None
        return obj.depuis_si(self.valeur)

    def incertitude_en(self, unite: str):
        obj = D.UNITES.get(unite)
        if not isinstance(obj, D.Unite) or obj.dimension != self.dim:
            return None
        return self.u / float(obj.facteur)

    # — arithmétique SOUND —
    def _exige_meme_dim(self, autre, op):
        if not isinstance(autre, Grandeur):
            raise TypeError(f"{op} attend une Grandeur")
        if self.dim != autre.dim:
            raise IncoherenceDimensionnelle(
                f"{op} de dimensions incompatibles : {self.dim.formule()} vs {autre.dim.formule()}")

    def __add__(self, autre):
        self._exige_meme_dim(autre, "addition")
        return Grandeur(self.valeur + autre.valeur, self.dim, math.hypot(self.u, autre.u))

    def __sub__(self, autre):
        self._exige_meme_dim(autre, "soustraction")
        return Grandeur(self.valeur - autre.valeur, self.dim, math.hypot(self.u, autre.u))

    def __mul__(self, autre):
        if isinstance(autre, (int, float)):
            return Grandeur(self.valeur * autre, self.dim, self.u * abs(autre))
        if not isinstance(autre, Grandeur):
            return NotImplemented
        v = self.valeur * autre.valeur
        u = _u_produit(v, self.valeur, self.u, autre.valeur, autre.u)
        return Grandeur(v, self.dim * autre.dim, u)

    __rmul__ = __mul__

    def __truediv__(self, autre):
        if isinstance(autre, (int, float)):
            return Grandeur(self.valeur / autre, self.dim, self.u / abs(autre))
        if not isinstance(autre, Grandeur):
            return NotImplemented
        v = self.valeur / autre.valeur
        u = _u_produit(v, self.valeur, self.u, autre.valeur, autre.u)
        return Grandeur(v, self.dim / autre.dim, u)

    def __pow__(self, r):
        v = self.valeur ** r
        # d(v)/v = r * d(x)/x  ->  u_rel_result = |r| * u_rel_x
        u = abs(v) * abs(r) * (self.u / abs(self.valeur)) if self.valeur else 0.0
        return Grandeur(v, self.dim ** r, u)

    # — comparaison (exige la même dimension) —
    def compare(self, autre):
        """-1/0/1 selon valeur SI, ou lève si dimensions incompatibles (comparer des choux et des carottes)."""
        self._exige_meme_dim(autre, "comparaison")
        return (self.valeur > autre.valeur) - (self.valeur < autre.valeur)

    def __lt__(self, autre):
        return self.compare(autre) < 0

    def __eq__(self, autre):
        return isinstance(autre, Grandeur) and self.dim == autre.dim and self.valeur == autre.valeur

    def __hash__(self):
        return hash((self.valeur, self.dim))

    def __repr__(self):
        u = f" ± {self.u:g}" if self.u else ""
        return f"Grandeur({self.valeur:g}{u} [SI {self.dim.formule()}])"

    def formule(self, unite: str = None) -> str:
        """Rendu lisible dans une unité donnée (ou SI). None si unité incommensurable."""
        if unite is None:
            return repr(self)
        v = self.en(unite)
        if v is None:
            return None
        uu = self.incertitude_en(unite)
        return f"{v:g}{f' ± {uu:g}' if uu else ''} {unite}"


def _u_produit(v, a, ua, b, ub):
    """Incertitude d'un produit/quotient (1er ordre, indépendance) : u_rel = √((ua/a)²+(ub/b)²)."""
    if a == 0 or b == 0:
        return 0.0
    return abs(v) * math.hypot(ua / a, ub / b)


def homogene(g1: Grandeur, g2: Grandeur) -> bool:
    """Deux grandeurs sont-elles additionnables/comparables (même dimension) ?"""
    return g1.dim == g2.dim
