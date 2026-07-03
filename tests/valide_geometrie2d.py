#!/usr/bin/env python3
"""
VALIDATION de geometrie2d.py — noyau borné du dessin vectoriel. FAUX=0 : formes dégénérées refusées, aire/périmètre
exacts, transformations affines composables/déterministes, SVG bien formé. Léger (stdlib pur, pas de lecteur).
"""
from __future__ import annotations

import math
import sys
import xml.dom.minidom as _dom

import geometrie2d as G


def main() -> int:
    ok, fails = 0, []

    def check(nom, cond):
        nonlocal ok
        if cond:
            ok += 1
            print(f"  [OK ] {nom}")
        else:
            fails.append(nom)
            print(f"  [XX ] {nom}")

    def leve(fn):
        try:
            fn(); return False
        except ValueError:
            return True

    # ── Points / dégénérescences ──────────────────────────────────────────────────────────────
    check("Point : distance (3,4) = 5", abs(G.Point(0, 0).distance(G.Point(3, 4)) - 5.0) < 1e-12)
    check("FAUX=0 : coordonnée non finie -> ValueError", leve(lambda: G.Point(float("inf"), 0)))

    # ── Polygone : aire (shoelace) + périmètre + centroïde ────────────────────────────────────
    carre = G.Polygone([(0, 0), (4, 0), (4, 4), (0, 4)])
    check("Polygone : aire d'un carré 4×4 = 16 (shoelace)", abs(carre.aire() - 16.0) < 1e-12)
    check("Polygone : périmètre d'un carré 4×4 = 16", abs(carre.perimetre() - 16.0) < 1e-12)
    check("Polygone : centroïde du carré = (2,2)", carre.centroide() == G.Point(2, 2))
    tri = G.Polygone([(0, 0), (4, 0), (0, 3)])
    check("Polygone : aire triangle 4×3 = 6", abs(tri.aire() - 6.0) < 1e-12)
    check("FAUX=0 : polygone < 3 sommets -> ValueError", leve(lambda: G.Polygone([(0, 0), (1, 1)])))

    # ── Transformations affines ───────────────────────────────────────────────────────────────
    t = G.Affine.translation(10, 5)
    check("Affine : translation d'un point", t.applique_point(G.Point(1, 2)) == G.Point(11, 7))
    e = G.Affine.echelle(2)
    check("Affine : échelle ×2 double l'aire (16 -> 64)", abs(carre.applique(e).aire() - 64.0) < 1e-9)
    # rotation de 90° autour de l'origine : (1,0) -> (0,1)
    r = G.Affine.rotation(math.pi / 2)
    p = r.applique_point(G.Point(1, 0))
    check("Affine : rotation 90° (1,0) -> (0,1)", abs(p.x) < 1e-9 and abs(p.y - 1) < 1e-9)
    # rotation préserve l'aire et le périmètre
    cr = carre.applique(r)
    check("Affine : rotation préserve aire (16) et périmètre (16)",
          abs(cr.aire() - 16.0) < 1e-9 and abs(cr.perimetre() - 16.0) < 1e-9)
    # composition : (self ∘ autre)(p) == self(autre(p))
    comp = t.compose(e)
    check("Affine : compose(t,e)(p) == t(e(p))",
          comp.applique_point(G.Point(3, 4)) == t.applique_point(e.applique_point(G.Point(3, 4))))
    # rotation autour d'un centre : le centre est fixe
    rc = G.Affine.rotation(1.234, centre=G.Point(5, 5))
    fixe = rc.applique_point(G.Point(5, 5))
    check("Affine : rotation autour d'un centre laisse le centre fixe",
          abs(fixe.x - 5) < 1e-9 and abs(fixe.y - 5) < 1e-9)

    # ── Cercle ────────────────────────────────────────────────────────────────────────────────
    c = G.Cercle((0, 0), 2)
    check("Cercle : aire = π·r² (4π)", abs(c.aire() - 4 * math.pi) < 1e-12)
    check("FAUX=0 : rayon ≤ 0 -> ValueError", leve(lambda: G.Cercle((0, 0), 0)))
    check("Cercle : échelle isotrope ×3 -> rayon 6", abs(c.applique(G.Affine.echelle(3)).rayon - 6.0) < 1e-9)
    check("FAUX=0 : échelle anisotrope d'un cercle -> ValueError (deviendrait ellipse)",
          leve(lambda: c.applique(G.Affine.echelle(2, 3))))

    # ── SVG : bien formé + déterministe ───────────────────────────────────────────────────────
    svg = G.scene_svg([carre, c], 100, 100)
    check("SVG : document bien formé (parse XML sans erreur)", _dom.parseString(svg) is not None)
    check("SVG : contient polygon + circle", "<polygon" in svg and "<circle" in svg)
    check("SVG : DÉTERMINISTE (mêmes entrées -> même texte)", G.scene_svg([carre, c], 100, 100) == svg)
    check("FAUX=0 : scène de dimensions invalides -> ValueError", leve(lambda: G.scene_svg([carre], 0, 100)))

    # ── CÂBLAGE ia.py ─────────────────────────────────────────────────────────────────────────
    import ia
    svg2 = ia.dessin_svg([carre, c], 100, 100)
    check("CÂBLAGE ia.dessin_svg : SVG bien formé identique", svg2 == svg and _dom.parseString(svg2) is not None)

    print(f"\n=== valide_geometrie2d : {ok}/{ok + len(fails)} ===")
    if fails:
        print("ÉCHECS :", ", ".join(fails))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
