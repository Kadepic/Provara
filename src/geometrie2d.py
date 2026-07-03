"""
GÉOMÉTRIE CONSTRUCTIVE 2D — noyau BORNÉ du dessin / des plans / des images vectorielles (modalité, 2026-07-02).

POURQUOI (vision Yohan « dessin, plans, images ») : une modalité visuelle a un NOYAU exact et vérifiable — la
géométrie (points, formes, transformations affines, aire/périmètre) et un format de sortie EXACT (SVG = texte). La
couche non-bornée (esthétique) reste hors FAUX=0 : ce module ne prétend PAS qu'une forme est « belle » ; il garantit
qu'elle est VALIDE et que sa description (SVG) est exacte et déterministe.

FAUX=0 :
  • Formes dégénérées refusées (polygone < 3 sommets, cercle rayon ≤ 0, points confondus dans un segment) -> ValueError.
  • Transformations affines composables et déterministes ; `applique` produit une forme du même type, valide.
  • Aire (shoelace) et périmètre EXACTS sur les coordonnées données ; l'aire est signée-corrigée en valeur absolue.
  • SVG bien formé et déterministe (mêmes entrées -> même texte), coordonnées arrondies à une précision annoncée.
NB : les rotations utilisent cos/sin (irrationnels) -> arithmétique FLOTTANTE déterministe (pas de Fraction exacte sur
un angle arbitraire) ; « FAUX=0 » porte ici sur la validité structurelle + le déterminisme, pas l'exactitude rationnelle.
Stdlib pur, souverain.
"""
from __future__ import annotations

import dataclasses
import math

_PREC = 6            # décimales dans le SVG (précision annoncée)


@dataclasses.dataclass(frozen=True)
class Point:
    x: float
    y: float

    def __post_init__(self):
        if not (math.isfinite(self.x) and math.isfinite(self.y)):
            raise ValueError("coordonnées non finies")

    def distance(self, autre: "Point") -> float:
        return math.hypot(self.x - autre.x, self.y - autre.y)


class Affine:
    """Transformation affine 2D : (x, y) -> (a·x + c·y + e, b·x + d·y + f). Composable (matrice 2×3, convention SVG)."""

    __slots__ = ("a", "b", "c", "d", "e", "f")

    def __init__(self, a=1.0, b=0.0, c=0.0, d=1.0, e=0.0, f=0.0):
        for v in (a, b, c, d, e, f):
            if not math.isfinite(v):
                raise ValueError("coefficient de transformation non fini")
        self.a, self.b, self.c, self.d, self.e, self.f = float(a), float(b), float(c), float(d), float(e), float(f)

    @staticmethod
    def translation(dx: float, dy: float) -> "Affine":
        return Affine(1, 0, 0, 1, dx, dy)

    @staticmethod
    def echelle(sx: float, sy: float = None) -> "Affine":
        sy = sx if sy is None else sy
        return Affine(sx, 0, 0, sy, 0, 0)

    @staticmethod
    def rotation(angle_rad: float, centre: "Point" = None) -> "Affine":
        """Rotation d'angle `angle_rad` autour de `centre` (origine par défaut). cos/sin -> flottant déterministe."""
        cos, sin = math.cos(angle_rad), math.sin(angle_rad)
        rot = Affine(cos, sin, -sin, cos, 0, 0)
        if centre is None:
            return rot
        return Affine.translation(centre.x, centre.y).compose(rot).compose(Affine.translation(-centre.x, -centre.y))

    def applique_point(self, p: Point) -> Point:
        return Point(self.a * p.x + self.c * p.y + self.e, self.b * p.x + self.d * p.y + self.f)

    def compose(self, autre: "Affine") -> "Affine":
        """self ∘ autre : applique `autre` PUIS `self`. (self.compose(autre)).applique(p) == self.applique(autre.applique(p))."""
        return Affine(
            self.a * autre.a + self.c * autre.b,
            self.b * autre.a + self.d * autre.b,
            self.a * autre.c + self.c * autre.d,
            self.b * autre.c + self.d * autre.d,
            self.a * autre.e + self.c * autre.f + self.e,
            self.b * autre.e + self.d * autre.f + self.f,
        )


class Polygone:
    """Polygone simple (au moins 3 sommets). Aire par shoelace, périmètre, centroïde."""

    __slots__ = ("sommets",)

    def __init__(self, sommets):
        pts = [p if isinstance(p, Point) else Point(*p) for p in sommets]
        if len(pts) < 3:
            raise ValueError("un polygone exige au moins 3 sommets")
        self.sommets = tuple(pts)

    def aire(self) -> float:
        """Aire (valeur absolue) par la formule du lacet (shoelace) — exacte sur les coordonnées données."""
        s = 0.0
        n = len(self.sommets)
        for i in range(n):
            p, q = self.sommets[i], self.sommets[(i + 1) % n]
            s += p.x * q.y - q.x * p.y
        return abs(s) / 2.0

    def perimetre(self) -> float:
        n = len(self.sommets)
        return sum(self.sommets[i].distance(self.sommets[(i + 1) % n]) for i in range(n))

    def centroide(self) -> Point:
        return Point(sum(p.x for p in self.sommets) / len(self.sommets),
                     sum(p.y for p in self.sommets) / len(self.sommets))

    def applique(self, t: Affine) -> "Polygone":
        return Polygone([t.applique_point(p) for p in self.sommets])

    def vers_svg(self) -> str:
        pts = " ".join(f"{round(p.x, _PREC)},{round(p.y, _PREC)}" for p in self.sommets)
        return f'<polygon points="{pts}" fill="none" stroke="black"/>'


class Cercle:
    __slots__ = ("centre", "rayon")

    def __init__(self, centre, rayon: float):
        self.centre = centre if isinstance(centre, Point) else Point(*centre)
        if not (math.isfinite(rayon) and rayon > 0):
            raise ValueError("le rayon d'un cercle doit être > 0")
        self.rayon = float(rayon)

    def aire(self) -> float:
        return math.pi * self.rayon * self.rayon

    def perimetre(self) -> float:
        return 2 * math.pi * self.rayon

    def applique(self, t: Affine) -> "Cercle":
        """Translation/rotation préservent le cercle ; une échelle NON uniforme le déformerait en ellipse -> refus
        (FAUX=0 : on ne prétend pas qu'un cercle reste un cercle sous une échelle anisotrope)."""
        c = t.applique_point(self.centre)
        # facteur d'échelle isotrope = norme des colonnes ; anisotrope -> refus
        sx = math.hypot(t.a, t.b)
        sy = math.hypot(t.c, t.d)
        if abs(sx - sy) > 1e-9:
            raise ValueError("échelle anisotrope : le cercle deviendrait une ellipse (non représentable ici)")
        return Cercle(c, self.rayon * sx)

    def vers_svg(self) -> str:
        return (f'<circle cx="{round(self.centre.x, _PREC)}" cy="{round(self.centre.y, _PREC)}" '
                f'r="{round(self.rayon, _PREC)}" fill="none" stroke="black"/>')


def scene_svg(formes, largeur: float, hauteur: float) -> str:
    """Assemble des formes (ayant `vers_svg`) en un document SVG complet, bien formé et déterministe."""
    if largeur <= 0 or hauteur <= 0:
        raise ValueError("dimensions de scène invalides")
    corps = "\n  ".join(f.vers_svg() for f in formes)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{largeur}" height="{hauteur}" '
            f'viewBox="0 0 {largeur} {hauteur}">\n  {corps}\n</svg>')
