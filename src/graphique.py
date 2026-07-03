"""
GRAPHIQUE DE DONNÉES — noyau BORNÉ du TRACÉ (bar/ligne/nuage), pur stdlib (2026-07-02).

POURQUOI (vision Yohan « outil universel toutes modalités » ; une IA analytique doit TRACER ses données) : un
graphique a un NOYAU exact et vérifiable — la projection linéaire DONNÉE -> COORDONNÉE (l'échelle, les axes, la
position de chaque point/barre). L'esthétique (couleurs, style) est non-bornée et non jugée. Ce module SÉPARE les
deux : il produit d'abord un `Disposition` (coordonnées EXACTES, re-dérivables) puis le REND en SVG (texte) ou PNG
(via raster_png, round-trip prouvé). Aucune dépendance (ni matplotlib).

FAUX=0 — ce que ce module GARANTIT, et ce qu'il ne prétend PAS :
  • L'échelle est une projection affine EXACTE : `Echelle(dmin,dmax,pmin,pmax).projette(v)` = pmin+(v−dmin)/(dmax−dmin)·(pmax−pmin)
    — le validateur re-dérive la formule. Domaine dégénéré (dmax==dmin) -> ValueError (jamais de division cachée).
  • Les positions de barres/points/segments sont calculées de cette projection, DÉTERMINISTES ; le rendu (SVG/PNG)
    est déterministe (mêmes données -> mêmes octets/texte).
  • Données invalides (vide, non finies, longueurs incohérentes) -> ValueError.
  Ce module ne prétend PAS qu'un graphique est « lisible » ou « bien choisi » (non-borné) : il garantit que chaque
  élément est placé à la coordonnée EXACTE imposée par les données et l'échelle. Souverain, offline, stdlib pur.
"""
from __future__ import annotations

import dataclasses
import math


def _fini(x, nom):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
        raise ValueError(f"{nom} doit être un nombre fini (vu {x!r})")
    return float(x)


class Echelle:
    """Projection affine d'un domaine [dmin,dmax] (données) vers une plage [pmin,pmax] (pixels/unités de tracé)."""

    def __init__(self, dmin, dmax, pmin, pmax):
        self.dmin = _fini(dmin, "dmin")
        self.dmax = _fini(dmax, "dmax")
        self.pmin = _fini(pmin, "pmin")
        self.pmax = _fini(pmax, "pmax")
        if self.dmax == self.dmin:
            raise ValueError("domaine dégénéré (dmax == dmin) : échelle indéfinie")

    def projette(self, v) -> float:
        v = _fini(v, "valeur")
        t = (v - self.dmin) / (self.dmax - self.dmin)
        return self.pmin + t * (self.pmax - self.pmin)


def _valide_serie(valeurs):
    if not valeurs:
        raise ValueError("série vide")
    return [_fini(v, "valeur") for v in valeurs]


def bornes(valeurs, *, inclure_zero: bool = True):
    """(min, max) d'une série pour l'axe. `inclure_zero` étend l'axe à 0 (barres). Série constante -> plage élargie."""
    vs = _valide_serie(valeurs)
    lo, hi = min(vs), max(vs)
    if inclure_zero:
        lo, hi = min(lo, 0.0), max(hi, 0.0)
    if lo == hi:                                    # série constante : ouvre un intervalle non dégénéré
        lo, hi = (lo - 1.0, hi + 1.0) if lo != 0 else (-1.0, 1.0)
    return lo, hi


@dataclasses.dataclass(frozen=True)
class Rect:
    x: float
    y: float
    largeur: float
    hauteur: float


@dataclasses.dataclass(frozen=True)
class Pt:
    x: float
    y: float


@dataclasses.dataclass(frozen=True)
class Disposition:
    """Résultat GÉOMÉTRIQUE exact d'un tracé : coordonnées en pixels (origine haut-gauche, y vers le bas)."""
    largeur: int
    hauteur: int
    marge: int
    rects: tuple = ()          # barres
    points: tuple = ()         # nuage / sommets de courbe
    type: str = ""


def _cadre(largeur, hauteur, marge):
    if not all(isinstance(v, int) and not isinstance(v, bool) for v in (largeur, hauteur, marge)):
        raise ValueError("largeur/hauteur/marge entiers attendus")
    if largeur < 2 * marge + 2 or hauteur < 2 * marge + 2 or marge < 0:
        raise ValueError("cadre trop petit pour la marge")
    return marge, marge, largeur - marge, hauteur - marge      # x0,y0,x1,y1 zone de tracé


def barres(valeurs, *, largeur: int = 400, hauteur: int = 300, marge: int = 20) -> Disposition:
    """Diagramme en barres : une barre par valeur, hauteur ∝ valeur (échelle incluant 0). Coordonnées EXACTES."""
    vs = _valide_serie(valeurs)
    x0, y0, x1, y1 = _cadre(largeur, hauteur, marge)
    lo, hi = bornes(vs, inclure_zero=True)
    ey = Echelle(lo, hi, y1, y0)                    # y inversé (haut = grande valeur)
    n = len(vs)
    pas = (x1 - x0) / n
    largeur_barre = pas * 0.8
    y_zero = ey.projette(0.0)
    rects = []
    for i, v in enumerate(vs):
        cx = x0 + pas * (i + 0.5)
        yv = ey.projette(v)
        y_haut = min(yv, y_zero)
        rects.append(Rect(cx - largeur_barre / 2, y_haut, largeur_barre, abs(yv - y_zero)))
    return Disposition(largeur, hauteur, marge, rects=tuple(rects), type="barres")


def _points(xs, ys, largeur, hauteur, marge):
    xs = _valide_serie(xs)
    ys = _valide_serie(ys)
    if len(xs) != len(ys):
        raise ValueError("xs et ys de longueurs différentes")
    x0, y0, x1, y1 = _cadre(largeur, hauteur, marge)
    lox, hix = bornes(xs, inclure_zero=False)
    loy, hiy = bornes(ys, inclure_zero=False)
    ex = Echelle(lox, hix, x0, x1)
    ey = Echelle(loy, hiy, y1, y0)
    return tuple(Pt(ex.projette(x), ey.projette(y)) for x, y in zip(xs, ys))


def nuage(xs, ys, *, largeur: int = 400, hauteur: int = 300, marge: int = 20) -> Disposition:
    """Nuage de points (x,y) projetés exactement dans le cadre."""
    pts = _points(xs, ys, largeur, hauteur, marge)
    return Disposition(largeur, hauteur, marge, points=pts, type="nuage")


def courbe(xs, ys, *, largeur: int = 400, hauteur: int = 300, marge: int = 20) -> Disposition:
    """Ligne brisée reliant les points (x,y) dans l'ordre. Mêmes projections que le nuage."""
    pts = _points(xs, ys, largeur, hauteur, marge)
    return Disposition(largeur, hauteur, marge, points=pts, type="courbe")


# ─────────── rendus déterministes ───────────
def vers_svg(disp: Disposition, *, couleur: str = "#3366cc") -> str:
    """Rend une Disposition en SVG (texte déterministe). Coordonnées arrondies à 3 décimales."""
    def f(v):
        return f"{v:.3f}".rstrip("0").rstrip(".")
    corps = [f'<rect x="0" y="0" width="{disp.largeur}" height="{disp.hauteur}" fill="white"/>']
    for r in disp.rects:
        corps.append(f'<rect x="{f(r.x)}" y="{f(r.y)}" width="{f(r.largeur)}" height="{f(r.hauteur)}" fill="{couleur}"/>')
    if disp.type == "courbe" and disp.points:
        d = " ".join(f"{f(p.x)},{f(p.y)}" for p in disp.points)
        corps.append(f'<polyline points="{d}" fill="none" stroke="{couleur}" stroke-width="2"/>')
    if disp.type == "nuage":
        for p in disp.points:
            corps.append(f'<circle cx="{f(p.x)}" cy="{f(p.y)}" r="3" fill="{couleur}"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{disp.largeur}" height="{disp.hauteur}" '
            f'viewBox="0 0 {disp.largeur} {disp.hauteur}">' + "".join(corps) + "</svg>")


def vers_png(disp: Disposition, couleur=(51, 102, 204)):
    """Rend une Disposition en `raster_png.Image` (RGB). Barres/points posés en pixels exacts (arrondis entiers)."""
    import raster_png
    img = raster_png.Image(disp.largeur, disp.hauteur, "RGB", fond=(255, 255, 255))
    for r in disp.rects:
        x0 = max(0, int(round(r.x)))
        y0 = max(0, int(round(r.y)))
        x1 = min(disp.largeur - 1, int(round(r.x + r.largeur)))
        y1 = min(disp.hauteur - 1, int(round(r.y + r.hauteur)))
        if x1 >= x0 and y1 >= y0:
            img.rectangle(x0, y0, x1, y1, couleur, plein=True)
    for p in disp.points:
        x = int(round(p.x)); y = int(round(p.y))
        if 0 <= x < disp.largeur and 0 <= y < disp.hauteur:
            img.pixel(x, y, couleur)
    return img
