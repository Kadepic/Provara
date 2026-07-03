"""
LIMITE THÉORIQUE & ÉCART — brique Vague 3. Dépend de loi.py + grandeur.py + dimensions.py.

POURQUOI : c'est LE geste machine de l'invention — calculer la BORNE physique d'une grandeur (Carnot pour un COP,
Betz pour une éolienne, Shannon pour un canal, Landauer pour une énergie de calcul) et mesurer l'ÉCART entre le
système réel et cette borne. L'écart dit OÙ se cache la marge (« un climatiseur réel fait COP≈3,5 quand Carnot
autorise ≈20 → ×5,6 de marge »). Un humain satisfait ; la machine calcule la borne et vise le facteur.

MODÈLE : une Limite = une `loi.Loi` qui calcule la valeur BORNE d'une cible à partir de paramètres + un SENS
(« max » : la borne est un plafond, réel ≤ borne ; « min » : plancher, réel ≥ borne). `evalue(reel, **params)`
renvoie la borne, le respect, le facteur de marge et un drapeau d'IMPOSSIBILITÉ.

FAUX=0 :
  • Borne calculée par une Loi déjà sound (dimensionnellement vérifiée) ; None (HORS) si les paramètres ne
    conviennent pas.
  • `reel` de dimension différente de la borne -> None (HORS).
  • Si le réel VIOLE la borne (COP réel > Carnot) -> `impossible=True` : la brique DÉTECTE l'incohérence (mesure
    fausse ou borne inapplicable), elle n'« accepte » jamais un écart impossible comme une marge.
  • Aucun facteur fabriqué (division par zéro -> inf explicite, pas de nombre inventé).
Stdlib pur, déterministe, souverain.
"""
from __future__ import annotations

import math

from grandeur import Grandeur
from loi import Loi


class Limite:
    __slots__ = ("nom", "loi", "cible", "sens", "description")

    def __init__(self, nom: str, loi: Loi, cible: str, sens: str, description: str = ""):
        if sens not in ("max", "min"):
            raise ValueError("sens doit être 'max' (plafond) ou 'min' (plancher)")
        self.nom = nom
        self.loi = loi
        self.cible = cible
        self.sens = sens
        self.description = description

    def borne(self, **params):
        """Valeur théorique limite (Grandeur) via la loi, ou None (HORS) si paramètres invalides."""
        return self.loi.resout(self.cible, **params)

    def evalue(self, reel: Grandeur, **params):
        """Compare une performance RÉELLE à la borne. Renvoie un dict {borne, reel, respecte, impossible,
        facteur_marge, ecart_absolu} ou None (HORS) si dimensions/params incompatibles.
        facteur_marge = combien de fois mieux reste atteignable (>1 = marge ; =1 = à l'optimum)."""
        b = self.borne(**params)
        if b is None or not isinstance(reel, Grandeur) or reel.dim != b.dim:
            return None
        if self.sens == "max":
            respecte = reel.valeur <= b.valeur
            facteur = (b.valeur / reel.valeur) if reel.valeur else math.inf
        else:  # min
            respecte = reel.valeur >= b.valeur
            facteur = (reel.valeur / b.valeur) if b.valeur else math.inf
        return {
            "borne": b,
            "reel": reel,
            "respecte": respecte,
            "impossible": not respecte,          # réel au-delà de la borne physique = incohérent, flag FAUX=0
            "facteur_marge": abs(facteur),
            "ecart_absolu": abs(b.valeur - reel.valeur),
        }

    def marge(self, reel: Grandeur, **params):
        """Raccourci : le facteur de marge (combien mieux est possible), ou None (HORS) / inf. Impossible -> None."""
        r = self.evalue(reel, **params)
        if r is None or r["impossible"]:
            return None
        return r["facteur_marge"]
