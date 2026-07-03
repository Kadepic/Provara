"""
CHEMINS 2D — segments de droite + courbes de BÉZIER cubiques, export SVG `<path>` (modalité, 2026-07-02).

Complète geometrie2d (formes fermées simples) avec la primitive UNIVERSELLE du dessin vectoriel : le chemin.
Un `Chemin` = suite CONTIGUË de segments (Ligne | Bezier) ; s'il revient exactement à son départ il est fermé
(aire exacte par Green), sinon ouvert. Compose avec `geometrie2d.scene_svg` (protocole `vers_svg`) et donc avec
`ia.dessin_svg` sans câblage nouveau.

FAUX=0 :
  • Dégénérés refusés (Bézier aux 4 points confondus, ligne de longueur nulle, chemin non contigu) -> ValueError.
  • LONGUEUR d'un arc de Bézier : pas de formule fermée -> on ne SERT JAMAIS une « longueur » approchée nue ;
    `longueur_bornes()` renvoie (basse, haute) PROUVÉES (corde inscrite ≤ arc ≤ polygone de contrôle, sur chaque
    sous-courbe de Casteljau) — la vraie longueur est DANS l'intervalle, qui se resserre avec la profondeur.
  • AIRE d'un chemin fermé : EXACTE (théorème de Green). Contribution d'un segment cubique dérivée en Fractions
    exactes (script de dérivation 2026-07-02, cas dégénéré = terme du lacet vérifié) :
       ∮(x·dy − y·dx)/2 = (3/10)K01 + (3/20)K02 + (1/20)K03 + (3/20)K12 + (3/20)K13 + (3/10)K23,
    où Kij = xi·yj − xj·yi. Aire d'un chemin OUVERT -> ValueError (jamais une « aire » mensongère).
  • Transformations affines EXACTES sur les points de contrôle (une Bézier est affine-invariante).
  • SVG déterministe (mêmes entrées -> même texte), précision annoncée (_PREC de geometrie2d).
Stdlib pur, souverain.
"""
from __future__ import annotations

import math

from geometrie2d import Point, Affine, _PREC


def _pt(p) -> Point:
    return p if isinstance(p, Point) else Point(*p)


class Ligne:
    """Segment de droite orienté (p, q distincts). Même protocole que Bezier (point/applique/longueur_bornes)."""

    __slots__ = ("p", "q")

    def __init__(self, p, q):
        self.p, self.q = _pt(p), _pt(q)
        if self.p == self.q:
            raise ValueError("ligne dégénérée : extrémités confondues")

    depart = property(lambda self: self.p)
    arrivee = property(lambda self: self.q)

    def point(self, t: float) -> Point:
        if not 0.0 <= t <= 1.0:
            raise ValueError("t hors [0,1]")
        return Point(self.p.x + t * (self.q.x - self.p.x), self.p.y + t * (self.q.y - self.p.y))

    def applique(self, tr: Affine) -> "Ligne":
        return Ligne(tr.applique_point(self.p), tr.applique_point(self.q))

    def longueur_bornes(self, profondeur: int = 6):
        d = self.p.distance(self.q)
        return (d, d)                              # exact : basse == haute

    def _aire_green(self) -> float:
        return (self.p.x * self.q.y - self.q.x * self.p.y) / 2.0

    def _svg(self) -> str:
        return f"L {round(self.q.x, _PREC)},{round(self.q.y, _PREC)}"


class Bezier:
    """Courbe de Bézier CUBIQUE (p0, p1, p2, p3). Évaluation par de Casteljau (stable), subdivision exacte."""

    __slots__ = ("p0", "p1", "p2", "p3")

    def __init__(self, p0, p1, p2, p3):
        pts = [_pt(p) for p in (p0, p1, p2, p3)]
        if all(p == pts[0] for p in pts[1:]):
            raise ValueError("Bézier dégénérée : les 4 points de contrôle sont confondus")
        self.p0, self.p1, self.p2, self.p3 = pts

    depart = property(lambda self: self.p0)
    arrivee = property(lambda self: self.p3)

    def point(self, t: float) -> Point:
        if not 0.0 <= t <= 1.0:
            raise ValueError("t hors [0,1]")
        lerp = lambda a, b: Point(a.x + t * (b.x - a.x), a.y + t * (b.y - a.y))
        a, b, c = lerp(self.p0, self.p1), lerp(self.p1, self.p2), lerp(self.p2, self.p3)
        return lerp(lerp(a, b), lerp(b, c))

    def subdivise(self, t: float = 0.5):
        """Découpe de Casteljau EXACTE en deux sous-cubiques couvrant [0,t] et [t,1] (même courbe géométrique)."""
        if not 0.0 < t < 1.0:
            raise ValueError("t de subdivision hors ]0,1[")
        lerp = lambda a, b: Point(a.x + t * (b.x - a.x), a.y + t * (b.y - a.y))
        a, b, c = lerp(self.p0, self.p1), lerp(self.p1, self.p2), lerp(self.p2, self.p3)
        d, e = lerp(a, b), lerp(b, c)
        m = lerp(d, e)
        # NB : une moitié peut être dégénérée si la courbe l'est localement — la construction l'interdit en amont.
        return Bezier(self.p0, a, d, m), Bezier(m, e, c, self.p3)

    def applique(self, tr: Affine) -> "Bezier":
        return Bezier(*(tr.applique_point(p) for p in (self.p0, self.p1, self.p2, self.p3)))

    def longueur_bornes(self, profondeur: int = 6):
        """(basse, haute) PROUVÉES : corde ≤ arc ≤ polygone de contrôle, vrai pour CHAQUE sous-courbe (propriété
        de la coque convexe) -> sommé sur 2^profondeur sous-courbes de Casteljau. L'intervalle se resserre en
        subdivisant ; il CONTIENT toujours la vraie longueur (jamais un point estimé non borné)."""
        morceaux = [self]
        for _ in range(max(0, profondeur)):
            suivants = []
            for c in morceaux:
                try:
                    suivants.extend(c.subdivise())
                except ValueError:             # sous-courbe localement ponctuelle : garder telle quelle (0 partout)
                    suivants.append(c)
            morceaux = suivants
        basse = sum(c.p0.distance(c.p3) for c in morceaux)
        haute = sum(c.p0.distance(c.p1) + c.p1.distance(c.p2) + c.p2.distance(c.p3) for c in morceaux)
        return (basse, haute)

    def _aire_green(self) -> float:
        # Constantes dérivées EXACTEMENT (Fractions, Bernstein) — voir docstring du module.
        k = lambda a, b: a.x * b.y - b.x * a.y
        p0, p1, p2, p3 = self.p0, self.p1, self.p2, self.p3
        return (6 * k(p0, p1) + 3 * k(p0, p2) + 1 * k(p0, p3)
                + 3 * k(p1, p2) + 3 * k(p1, p3) + 6 * k(p2, p3)) / 20.0

    def _svg(self) -> str:
        r = lambda p: f"{round(p.x, _PREC)},{round(p.y, _PREC)}"
        return f"C {r(self.p1)} {r(self.p2)} {r(self.p3)}"


class Chemin:
    """Suite CONTIGUË de segments (l'arrivée de chacun est EXACTEMENT le départ du suivant). Fermé ssi la
    dernière arrivée est exactement le premier départ — l'aire n'existe que fermé (Green, exacte)."""

    __slots__ = ("segments",)

    def __init__(self, segments):
        segs = tuple(segments)
        if not segs:
            raise ValueError("chemin vide")
        for s in segs:
            if not isinstance(s, (Ligne, Bezier)):
                raise ValueError(f"segment inconnu : {type(s).__name__}")
        for a, b in zip(segs, segs[1:]):
            if a.arrivee != b.depart:
                raise ValueError("chemin non contigu (l'arrivée d'un segment doit être le départ du suivant)")
        self.segments = segs

    @property
    def ferme(self) -> bool:
        return self.segments[-1].arrivee == self.segments[0].depart

    def applique(self, tr: Affine) -> "Chemin":
        return Chemin([s.applique(tr) for s in self.segments])    # mêmes points -> contiguïté préservée

    def longueur_bornes(self, profondeur: int = 6):
        bornes = [s.longueur_bornes(profondeur) for s in self.segments]
        return (sum(b for b, _h in bornes), sum(h for _b, h in bornes))

    def aire(self) -> float:
        """Aire (valeur absolue) d'un chemin FERMÉ, EXACTE par Green sur les coordonnées données. Ouvert -> refus."""
        if not self.ferme:
            raise ValueError("aire d'un chemin OUVERT : non définie (le fermer d'abord)")
        return abs(sum(s._aire_green() for s in self.segments))

    def vers_svg(self) -> str:
        p0 = self.segments[0].depart
        d = f"M {round(p0.x, _PREC)},{round(p0.y, _PREC)} " + " ".join(s._svg() for s in self.segments)
        if self.ferme:
            d += " Z"
        return f'<path d="{d}" fill="none" stroke="black"/>'


_KAPPA = 0.5522847498307936    # 4·(√2−1)/3 : contrôle standard de l'approx. d'un quart de cercle par une cubique


def cercle_approx(centre, rayon: float) -> Chemin:
    """Chemin FERMÉ de 4 cubiques approchant un cercle (κ = 4(√2−1)/3). C'est une APPROXIMATION connue (écart
    radial max ≈ 0,027 % — documenté), utile pour tracer un cercle en `<path>` ; pour l'aire/périmètre EXACTS
    d'un vrai cercle, utiliser geometrie2d.Cercle."""
    c, r = _pt(centre), float(rayon)
    if not (math.isfinite(r) and r > 0):
        raise ValueError("rayon > 0 requis")
    k = _KAPPA * r
    E, N, O, S = Point(c.x + r, c.y), Point(c.x, c.y + r), Point(c.x - r, c.y), Point(c.x, c.y - r)
    return Chemin([
        Bezier(E, Point(E.x, E.y + k), Point(N.x + k, N.y), N),
        Bezier(N, Point(N.x - k, N.y), Point(O.x, O.y + k), O),
        Bezier(O, Point(O.x, O.y - k), Point(S.x - k, S.y), S),
        Bezier(S, Point(S.x + k, S.y), Point(E.x, E.y - k), E),
    ])
