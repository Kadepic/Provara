"""
GÉOMÉTRIE 3D CONSTRUCTIVE — noyau BORNÉ de la modélisation 3D / des plans (modalité, 2026-07-02).

POURQUOI (vision Yohan « image en 3d, plans ») : un modèle 3D a un NOYAU exact — un MAILLAGE (sommets + faces
triangulaires), ses grandeurs (aire de surface, volume par le théorème de la divergence) et des formats d'échange
TEXTE exacts (OBJ, STL ASCII). L'esthétique reste non-bornée (non jugée) ; ce module garantit la VALIDITÉ et
l'exactitude des calculs et des exports.

FAUX=0 :
  • Face référençant un indice de sommet invalide, ou non triangulaire -> ValueError (jamais un maillage incohérent).
  • Aire de surface = somme EXACTE des aires de triangles (½‖(b−a)×(c−a)‖). Volume = (1/6)|Σ v0·(v1×v2)| — exact
    pour un maillage FERMÉ orienté (documenté : on calcule le volume signé, valable si le maillage est fermé).
  • Exports OBJ/STL bien formés et déterministes (mêmes entrées -> même texte).
NB : arithmétique flottante (rotations = cos/sin) déterministe ; « FAUX=0 » = validité structurelle + déterminisme.
Stdlib pur, souverain.
"""
from __future__ import annotations

import dataclasses
import math

_PREC = 6


@dataclasses.dataclass(frozen=True)
class Point3D:
    x: float
    y: float
    z: float

    def __post_init__(self):
        if not all(math.isfinite(v) for v in (self.x, self.y, self.z)):
            raise ValueError("coordonnées non finies")


def _sub(a, b):
    return (a.x - b.x, a.y - b.y, a.z - b.z)


def _cross(u, v):
    return (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])


def _dot(u, v):
    return u[0] * v[0] + u[1] * v[1] + u[2] * v[2]


def _norme(u):
    return math.sqrt(_dot(u, u))


class Affine3D:
    """Transformation affine 3D : matrice 3×3 (m) + translation (t). Composable."""

    __slots__ = ("m", "t")

    def __init__(self, m=None, t=(0.0, 0.0, 0.0)):
        self.m = m if m is not None else ((1.0, 0, 0), (0, 1.0, 0), (0, 0, 1.0))
        self.t = tuple(float(v) for v in t)
        for row in self.m:
            for v in row:
                if not math.isfinite(v):
                    raise ValueError("coefficient non fini")

    @staticmethod
    def translation(dx, dy, dz):
        return Affine3D(t=(dx, dy, dz))

    @staticmethod
    def echelle(s):
        return Affine3D(m=((s, 0, 0), (0, s, 0), (0, 0, s)))

    @staticmethod
    def rotation_z(angle):
        c, s = math.cos(angle), math.sin(angle)
        return Affine3D(m=((c, -s, 0), (s, c, 0), (0, 0, 1)))

    def applique(self, p: Point3D) -> Point3D:
        m, t = self.m, self.t
        return Point3D(m[0][0] * p.x + m[0][1] * p.y + m[0][2] * p.z + t[0],
                       m[1][0] * p.x + m[1][1] * p.y + m[1][2] * p.z + t[1],
                       m[2][0] * p.x + m[2][1] * p.y + m[2][2] * p.z + t[2])


class Maillage:
    """Maillage triangulaire : sommets (Point3D) + faces (triplets d'indices, orientation = normale sortante)."""

    __slots__ = ("sommets", "faces")

    def __init__(self, sommets, faces):
        pts = [p if isinstance(p, Point3D) else Point3D(*p) for p in sommets]
        n = len(pts)
        fs = []
        for f in faces:
            if len(f) != 3:
                raise ValueError(f"face non triangulaire : {f!r}")
            if any(not (0 <= i < n) for i in f):
                raise ValueError(f"indice de sommet hors bornes dans la face {f!r} (n={n})")
            fs.append(tuple(int(i) for i in f))
        if n < 3:
            raise ValueError("un maillage exige au moins 3 sommets")
        self.sommets = tuple(pts)
        self.faces = tuple(fs)

    def _tri(self, f):
        return self.sommets[f[0]], self.sommets[f[1]], self.sommets[f[2]]

    def aire_surface(self) -> float:
        s = 0.0
        for f in self.faces:
            a, b, c = self._tri(f)
            s += _norme(_cross(_sub(b, a), _sub(c, a))) / 2.0
        return s

    def volume(self) -> float:
        """Volume par le théorème de la divergence : (1/6)|Σ v0·(v1×v2)|. Exact pour un maillage FERMÉ orienté."""
        s = 0.0
        for f in self.faces:
            a, b, c = self._tri(f)
            s += _dot((a.x, a.y, a.z), _cross((b.x, b.y, b.z), (c.x, c.y, c.z)))
        return abs(s) / 6.0

    def applique(self, t: Affine3D) -> "Maillage":
        return Maillage([t.applique(p) for p in self.sommets], self.faces)

    def vers_obj(self) -> str:
        """Format Wavefront OBJ (texte). Indices 1-based. Déterministe."""
        lignes = [f"v {round(p.x, _PREC)} {round(p.y, _PREC)} {round(p.z, _PREC)}" for p in self.sommets]
        lignes += [f"f {f[0] + 1} {f[1] + 1} {f[2] + 1}" for f in self.faces]
        return "\n".join(lignes) + "\n"

    def vers_stl(self, nom: str = "maillage") -> str:
        """Format STL ASCII (texte), avec normale unitaire par facette. Déterministe."""
        out = [f"solid {nom}"]
        for f in self.faces:
            a, b, c = self._tri(f)
            nx, ny, nz = _cross(_sub(b, a), _sub(c, a))
            ln = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
            out.append(f"  facet normal {round(nx / ln, _PREC)} {round(ny / ln, _PREC)} {round(nz / ln, _PREC)}")
            out.append("    outer loop")
            for p in (a, b, c):
                out.append(f"      vertex {round(p.x, _PREC)} {round(p.y, _PREC)} {round(p.z, _PREC)}")
            out.append("    endloop")
            out.append("  endfacet")
        out.append(f"endsolid {nom}")
        return "\n".join(out) + "\n"


def cube(cote: float = 1.0, origine=(0.0, 0.0, 0.0)) -> Maillage:
    """Maillage d'un cube axis-aligned, faces orientées vers l'EXTÉRIEUR (volume positif). `cote` > 0."""
    if not (math.isfinite(cote) and cote > 0):
        raise ValueError("le côté d'un cube doit être > 0")
    ox, oy, oz = origine
    s = cote
    v = [Point3D(ox, oy, oz), Point3D(ox + s, oy, oz), Point3D(ox + s, oy + s, oz), Point3D(ox, oy + s, oz),
         Point3D(ox, oy, oz + s), Point3D(ox + s, oy, oz + s), Point3D(ox + s, oy + s, oz + s), Point3D(ox, oy + s, oz + s)]
    # 12 triangles, normales sortantes (orientation anti-horaire vue de l'extérieur)
    faces = [(0, 3, 2), (0, 2, 1),        # bas  (z=0), normale -z
             (4, 5, 6), (4, 6, 7),        # haut (z=s), normale +z
             (0, 1, 5), (0, 5, 4),        # face y=0, normale -y
             (2, 3, 7), (2, 7, 6),        # face y=s, normale +y
             (1, 2, 6), (1, 6, 5),        # face x=s, normale +x
             (0, 4, 7), (0, 7, 3)]        # face x=0, normale -x
    return Maillage(v, faces)
