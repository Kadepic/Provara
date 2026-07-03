#!/usr/bin/env python3
"""
VALIDATION de geometrie3d.py — maillages 3D. FAUX=0 : faces invalides refusées, aire/volume exacts (cube),
transformations déterministes, exports OBJ/STL bien formés. Léger (stdlib pur, pas de lecteur).
"""
from __future__ import annotations

import math
import sys

import geometrie3d as G


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

    # ── Cube unité : aire = 6, volume = 1 ─────────────────────────────────────────────────────
    c = G.cube(1.0)
    check("Cube : 8 sommets, 12 triangles", len(c.sommets) == 8 and len(c.faces) == 12)
    check("Cube unité : aire de surface = 6", abs(c.aire_surface() - 6.0) < 1e-9)
    check("Cube unité : volume = 1 (divergence)", abs(c.volume() - 1.0) < 1e-9)
    # cube de côté 2 : aire = 6·4 = 24, volume = 8
    c2 = G.cube(2.0)
    check("Cube côté 2 : aire = 24, volume = 8",
          abs(c2.aire_surface() - 24.0) < 1e-9 and abs(c2.volume() - 8.0) < 1e-9)

    # ── Transformations : échelle ×3 -> volume ×27 ; translation ne change ni aire ni volume ──
    check("Échelle ×3 : volume ×27 (1 -> 27)", abs(c.applique(G.Affine3D.echelle(3)).volume() - 27.0) < 1e-6)
    ct = c.applique(G.Affine3D.translation(10, -5, 2))
    check("Translation : volume (1) et aire (6) inchangés",
          abs(ct.volume() - 1.0) < 1e-9 and abs(ct.aire_surface() - 6.0) < 1e-9)
    cr = c.applique(G.Affine3D.rotation_z(0.7))
    check("Rotation z : volume (1) et aire (6) inchangés (rigide)",
          abs(cr.volume() - 1.0) < 1e-9 and abs(cr.aire_surface() - 6.0) < 1e-9)

    # ── FAUX=0 : maillages invalides refusés ──────────────────────────────────────────────────
    check("FAUX=0 : face non triangulaire -> ValueError",
          leve(lambda: G.Maillage([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [(0, 1, 2, 0)])))
    check("FAUX=0 : indice de sommet hors bornes -> ValueError",
          leve(lambda: G.Maillage([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [(0, 1, 5)])))
    check("FAUX=0 : cube de côté ≤ 0 -> ValueError", leve(lambda: G.cube(0)))
    check("FAUX=0 : coordonnée non finie -> ValueError", leve(lambda: G.Point3D(float("nan"), 0, 0)))

    # ── Exports OBJ / STL : bien formés + déterministes ───────────────────────────────────────
    obj = c.vers_obj()
    check("OBJ : 8 lignes 'v' + 12 lignes 'f'",
          obj.count("\nv ") + obj.startswith("v ") == 8 and obj.count("f ") == 12)
    check("OBJ : déterministe", c.vers_obj() == obj)
    stl = c.vers_stl("cube")
    check("STL : solid/endsolid + 12 facet", stl.startswith("solid cube") and stl.count("facet normal") == 12
          and stl.rstrip().endswith("endsolid cube"))
    check("STL : déterministe", c.vers_stl("cube") == stl)
    check("STL : chaque facet a 3 vertex", stl.count("vertex ") == 36)

    # ── Tétraèdre : volume connu ((1/6) pour le tétra unité sur les axes) ──────────────────────
    tetra = G.Maillage([(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)],
                       [(0, 2, 1), (0, 1, 3), (0, 3, 2), (1, 2, 3)])
    check("Tétraèdre unité : volume = 1/6", abs(tetra.volume() - 1.0 / 6.0) < 1e-9)

    # ── CÂBLAGE ia.py ─────────────────────────────────────────────────────────────────────────
    import ia
    check("CÂBLAGE ia.modele_3d_obj : OBJ d'un cube", ia.modele_3d_obj(c) == obj)

    print(f"\n=== valide_geometrie3d : {ok}/{ok + len(fails)} ===")
    if fails:
        print("ÉCHECS :", ", ".join(fails))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
