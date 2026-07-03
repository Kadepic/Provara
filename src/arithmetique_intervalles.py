"""
PALIER 2 — ARITHMÉTIQUE D'INTERVALLES : propager une incertitude bornée avec une GARANTIE d'encadrement (brique 52,
2026-06-26).

Quand une quantité n'est connue qu'à « x ∈ [a,b] » (tolérance d'usinage, erreur de capteur, arrondi), comment se
propage l'incertitude à travers un calcul f(x,y,…) ? L'arithmétique d'intervalles remplace chaque nombre par un
intervalle et chaque opération (+,−,×,÷) par sa version ensembliste, avec ARRONDI EXTÉRIEUR (directed rounding via
math.nextafter) pour que le résultat reste un encadrement RIGOUREUX malgré les arrondis flottants.

THÉORÈME FONDAMENTAL (Moore) : pour f composée de +,−,×,÷, l'évaluation par intervalles [f]([x₁],…,[xₙ]) CONTIENT
l'image réelle {f(x₁,…,xₙ) : xᵢ∈[xᵢ]}. Donc la vraie valeur est TOUJOURS dedans (couverture = 1) : c'est l'opposé de
la sur-confiance — la méthode est garantie de ne JAMAIS être trop étroite.

LE MODE D'ÉCHEC DÉMASQUÉ : la méthode « point » (plug-in : calculer f au MILIEU des intervalles et annoncer ce seul
nombre) jette l'incertitude → elle affirme une précision qu'elle n'a pas (couverture ≈ 0) = SUR-CONFIANTE. À
l'inverse, le PRIX de la garantie d'intervalle est le « problème de DÉPENDANCE » : réutiliser une variable (x−x)
SURESTIME la largeur ([−w,w] au lieu de 0). C'est conservateur (côté SÛR), jamais sur-confiant. ABSTENTION sur ÷ par
un intervalle contenant 0 (résultat non borné). Pur Python.
"""
from __future__ import annotations

import math

ABSTENTION = "abstention"
INTERVALLE = "intervalle"


def _bas(x):
    return math.nextafter(x, -math.inf)


def _haut(x):
    return math.nextafter(x, math.inf)


class Intervalle:
    """Intervalle fermé [bas, haut] = encadrement garanti d'une quantité inconnue. Arrondi EXTÉRIEUR à chaque op."""

    __slots__ = ("bas", "haut")

    def __init__(self, bas, haut=None):
        if haut is None:
            haut = bas
        bas, haut = float(bas), float(haut)
        if bas > haut:
            raise ValueError(f"intervalle vide : bas={bas} > haut={haut}")
        if math.isnan(bas) or math.isnan(haut):
            raise ValueError("borne NaN")
        self.bas, self.haut = bas, haut

    def __repr__(self):
        return f"[{self.bas:.6g}, {self.haut:.6g}]"

    def __eq__(self, autre):
        return isinstance(autre, Intervalle) and self.bas == autre.bas and self.haut == autre.haut

    @property
    def milieu(self):
        return (self.bas + self.haut) / 2

    @property
    def largeur(self):
        return self.haut - self.bas

    def contient(self, x, tol=0.0):
        return self.bas - tol <= x <= self.haut + tol

    def __add__(self, o):
        o = _co(o)
        return Intervalle(_bas(self.bas + o.bas), _haut(self.haut + o.haut))

    def __sub__(self, o):
        o = _co(o)
        return Intervalle(_bas(self.bas - o.haut), _haut(self.haut - o.bas))

    def __mul__(self, o):
        o = _co(o)
        coins = (self.bas * o.bas, self.bas * o.haut, self.haut * o.bas, self.haut * o.haut)
        return Intervalle(_bas(min(coins)), _haut(max(coins)))

    def __truediv__(self, o):
        o = _co(o)
        if o.bas <= 0.0 <= o.haut:
            raise ZeroDivisionError("division par un intervalle contenant 0 (résultat non borné)")
        coins = (self.bas / o.bas, self.bas / o.haut, self.haut / o.bas, self.haut / o.haut)
        return Intervalle(_bas(min(coins)), _haut(max(coins)))

    __radd__ = __add__

    def __rsub__(self, o):
        return _co(o).__sub__(self)

    __rmul__ = __mul__

    def __rtruediv__(self, o):
        return _co(o).__truediv__(self)


def _co(x):
    """Coercition : un nombre devient un intervalle dégénéré [x,x]."""
    return x if isinstance(x, Intervalle) else Intervalle(x)


def evalue(f, *intervalles):
    """Évalue f (en termes de +,−,×,÷ sur ses arguments) par arithmétique d'intervalles.
    Renvoie (INTERVALLE, [bas,haut]) — encadrement GARANTI — ou (ABSTENTION, raison) si non borné (÷ par 0∈[.])."""
    try:
        r = f(*[_co(i) for i in intervalles])
    except ZeroDivisionError as e:
        return (ABSTENTION, str(e))
    r = _co(r)
    return (INTERVALLE, [r.bas, r.haut])


def plugin_point(f, *intervalles):
    """Méthode « point » (SUR-CONFIANTE) : f évaluée au MILIEU de chaque intervalle → un seul nombre, l'incertitude
    est jetée. Renvoie le scalaire (ou None si division par 0)."""
    try:
        return float(f(*[i.milieu if isinstance(i, Intervalle) else float(i) for i in intervalles]))
    except ZeroDivisionError:
        return None


def formule(res) -> str:
    if res[0] == ABSTENTION:
        return f"Je ne peux pas borner le résultat : {res[1]}."
    bas, haut = res[1]
    return (f"Résultat GARANTI dans [{bas:.6g}, {haut:.6g}] (largeur {haut-bas:.4g}). Annoncer un seul nombre "
            f"(milieu) serait sur-confiant : la vraie valeur peut être n'importe où dans cet intervalle.")


if __name__ == "__main__":
    print("=== ARITHMÉTIQUE D'INTERVALLES — propagation garantie ===\n")
    x = Intervalle(2, 3)
    y = Intervalle(-1, 1)
    print(f"  x={x}, y={y}")
    print(f"   x+y={x+y}  x-y={x-y}  x*y={x*y}")
    print(f"   x/(x+5)={x/(x+5)}  (toujours borné car x+5>0)\n")
    print("  Problème de DÉPENDANCE (côté SÛR, jamais sur-confiant) :")
    print(f"   x - x = {x - x}  (largeur {(x-x).largeur:.3g}, vrai = 0 : surestimé mais GARANTI de contenir 0)\n")
    f = lambda a, b: (a * b + 1) / (a + 3)
    print("  f(a,b)=(a·b+1)/(a+3) :", formule(evalue(f, Intervalle(1, 2), Intervalle(0, 4))))
    print("  ÷ par 0∈[-1,1] :", formule(evalue(lambda a: 1 / a, Intervalle(-1, 1))))
