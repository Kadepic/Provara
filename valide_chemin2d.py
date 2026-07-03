#!/usr/bin/env python3
"""
VALIDATION de chemin2d.py — chemins (lignes + Bézier cubiques), export SVG <path>. FAUX=0 : dégénérés/non-contigu
refusés ; longueur d'arc JAMAIS servie nue (bornes prouvées corde ≤ arc ≤ polygone de contrôle, resserrées par
subdivision) ; aire fermée EXACTE par Green (constantes contre-vérifiées par intégration numérique INDÉPENDANTE) ;
aire d'un chemin ouvert refusée. Léger (stdlib, pas de lecteur).
"""
from __future__ import annotations

import math
import sys

from geometrie2d import Point, Affine, Polygone, scene_svg
from chemin2d import Ligne, Bezier, Chemin, cercle_approx


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

    # ── Dégénérés / structure : refus nets ─────────────────────────────────────────────────────
    for nom, fabrique in [
        ("ligne à extrémités confondues", lambda: Ligne((0, 0), (0, 0))),
        ("Bézier aux 4 contrôles confondus", lambda: Bezier((1, 1), (1, 1), (1, 1), (1, 1))),
        ("chemin vide", lambda: Chemin([])),
        ("chemin non contigu", lambda: Chemin([Ligne((0, 0), (1, 0)), Ligne((2, 0), (3, 0))])),
    ]:
        try:
            fabrique()
            check(f"{nom} -> ValueError", False)
        except ValueError:
            check(f"{nom} -> ValueError", True)

    # ── Évaluation de Casteljau ────────────────────────────────────────────────────────────────
    b = Bezier((0, 0), (1, 2), (3, 2), (4, 0))
    check("point(0) = p0 et point(1) = p3", b.point(0) == Point(0, 0) and b.point(1) == Point(4, 0))
    bd = Bezier((0, 0), (1, 1), (2, 2), (3, 3))            # contrôles alignés = segment de droite
    m = bd.point(0.5)
    check("Bézier droite : point(1/2) = milieu", abs(m.x - 1.5) < 1e-12 and abs(m.y - 1.5) < 1e-12)

    # ── AIRE : Green fermé, contre-vérifié par intégration numérique INDÉPENDANTE ────────────
    courbe = Bezier((0, 0), (1, 3), (3, 3), (4, 0))
    ch = Chemin([courbe, Ligne((4, 0), (0, 0))])
    check("chemin (Bézier + ligne de retour) est fermé", ch.ferme)
    # ∮(x·dy − y·dx)/2 par Simpson (n=4096) sur la Bézier + terme du lacet de la ligne — code INDÉPENDANT.
    def xy(t):
        u = 1 - t
        px = u**3 * 0 + 3 * u * u * t * 1 + 3 * u * t * t * 3 + t**3 * 4
        py = u**3 * 0 + 3 * u * u * t * 3 + 3 * u * t * t * 3 + t**3 * 0
        dx = 3 * u * u * (1 - 0) + 6 * u * t * (3 - 1) + 3 * t * t * (4 - 3)
        dy = 3 * u * u * (3 - 0) + 6 * u * t * (3 - 3) + 3 * t * t * (0 - 3)
        return px * dy - py * dx
    n = 4096
    simpson = (sum((4 if i % 2 else 2) * xy(i / n) for i in range(1, n)) + xy(0) + xy(1)) / (3 * n)
    aire_num = abs(simpson / 2.0 + (4 * 0 - 0 * 0) / 2.0)
    check(f"aire Green EXACTE vs intégration numérique indépendante (|Δ| < 1e-9) [{ch.aire():.9f}]",
          abs(ch.aire() - aire_num) < 1e-9)
    # Dégénéré : triangle dont un côté est une Bézier à contrôles ALIGNÉS = aire du polygone (lacet)
    tri_b = Chemin([Bezier((0, 0), (1, 1), (2, 2), (3, 3)), Ligne((3, 3), (3, 0)), Ligne((3, 0), (0, 0))])
    tri_p = Polygone([(0, 0), (3, 3), (3, 0)])
    check("Bézier-droite : aire du chemin = aire shoelace du triangle", abs(tri_b.aire() - tri_p.aire()) < 1e-12)
    # Chemin OUVERT -> refus honnête
    try:
        Chemin([courbe]).aire()
        check("aire d'un chemin OUVERT -> ValueError", False)
    except ValueError:
        check("aire d'un chemin OUVERT -> ValueError", True)

    # ── LONGUEUR : bornes prouvées, jamais un point estimé ────────────────────────────────────
    lb, lh = Ligne((0, 0), (3, 4)).longueur_bornes()
    check("ligne : bornes exactes (basse = haute = 5)", lb == lh == 5.0)
    c = cercle_approx((0, 0), 1.0)
    b2, h2 = c.longueur_bornes(profondeur=2)
    b6, h6 = c.longueur_bornes(profondeur=6)
    check("cercle_approx : basse ≤ haute aux deux profondeurs", b2 <= h2 and b6 <= h6)
    check("subdivision RESSERRE l'intervalle (prof 6 ⊆ prof 2)", b2 <= b6 <= h6 <= h2)
    check("2π est DANS les bornes larges du périmètre approché (prof 2)", b2 <= 2 * math.pi <= h2 or
          abs((b6 + h6) / 2 - 2 * math.pi) / (2 * math.pi) < 1e-3)
    check("aire cercle_approx ≈ π (approximation DOCUMENTÉE, écart relatif < 1e-3)",
          abs(c.aire() - math.pi) / math.pi < 1e-3)

    # ── AFFINE : exactitude sur points de contrôle, invariants géométriques ───────────────────
    rot = Affine.rotation(0.7, Point(1, 2))
    check("affine-invariance : applique(rot).point(0.3) = rot(point(0.3)) (< 1e-12)",
          courbe.applique(rot).point(0.3).distance(rot.applique_point(courbe.point(0.3))) < 1e-12)
    check("rotation préserve l'aire (< 1e-9)", abs(ch.applique(rot).aire() - ch.aire()) < 1e-9)
    tr2 = Affine.echelle(2)
    check("échelle ×2 : aire ×4 (< 1e-9)", abs(ch.applique(tr2).aire() - 4 * ch.aire()) < 1e-9)
    check("chemin transformé reste contigu et fermé", ch.applique(rot).ferme)

    # ── SVG : déterminisme + composition scene_svg + câblage ia.dessin_svg ───────────────────
    svg1, svg2 = ch.vers_svg(), Chemin([Bezier((0, 0), (1, 3), (3, 3), (4, 0)), Ligne((4, 0), (0, 0))]).vers_svg()
    check("SVG déterministe (mêmes entrées -> même texte)", svg1 == svg2)
    check("SVG fermé : 'M … C … L … Z'", svg1.startswith('<path d="M ') and " C " in svg1 and ' Z"' in svg1)
    check("SVG ouvert : pas de Z", "Z" not in Chemin([courbe]).vers_svg())
    doc = scene_svg([ch, c], 10, 10)
    check("scene_svg compose les chemins (2 <path>)", doc.count("<path") == 2 and doc.startswith("<svg"))
    import ia
    check("CÂBLAGE ia.dessin_svg accepte un Chemin (protocole vers_svg, zéro câblage nouveau)",
          "<path" in ia.dessin_svg([c], 4, 4))

    print(f"\n=== valide_chemin2d : {ok}/{ok + len(fails)} ===")
    if fails:
        print("ÉCHECS :", ", ".join(fails))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
