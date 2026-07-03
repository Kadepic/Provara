"""VALIDE graphique.py — projection affine EXACTE (oracle re-dérivé) + rendus déterministes + FAUX=0.

Oracle : on re-dérive la formule d'échelle et les positions attendues à la main ; on EXIGE l'égalité. Rendu PNG
re-décodé (raster_png) pour prouver que les barres occupent bien les pixels calculés. Négatifs : domaine dégénéré,
séries incohérentes, données non finies -> ValueError.
"""
import graphique as G
import raster_png as R

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def proche(a, b, eps=1e-9):
    return abs(a - b) <= eps


def leve(fn, *a, **k):
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) Échelle affine (oracle re-dérivé) ──
e = G.Echelle(0, 10, 100, 200)
check(proche(e.projette(0), 100) and proche(e.projette(10), 200) and proche(e.projette(5), 150), "échelle : projette bornes et milieu")
e2 = G.Echelle(0, 100, 300, 20)                    # plage inversée (axe y)
check(proche(e2.projette(0), 300) and proche(e2.projette(100), 20) and proche(e2.projette(25), 230), "échelle inversée : y décroissant")
# formule générique re-dérivée
for v in (2.5, 7.3, 9.99):
    attendu = 100 + (v - 0) / (10 - 0) * (200 - 100)
    check(proche(e.projette(v), attendu), f"échelle : formule affine exacte v={v}")

# ── 2) bornes ──
check(G.bornes([3, 5, 8], inclure_zero=True) == (0.0, 8.0), "bornes : inclut 0 pour barres")
check(G.bornes([3, 5, 8], inclure_zero=False) == (3.0, 8.0), "bornes : sans 0")
check(G.bornes([5, 5, 5]) == (0.0, 5.0), "bornes : constante non nulle avec 0")
lo, hi = G.bornes([0, 0, 0])
check(lo < hi, "bornes : constante nulle -> intervalle ouvert")

# ── 3) barres : hauteur ∝ valeur, base commune ──
disp = G.barres([10, 20, 40], largeur=100, hauteur=100, marge=10)
check(len(disp.rects) == 3, "barres : 3 rectangles")
# la barre de 40 (max) touche le haut de la zone (y=marge=10) ; toutes ont la même base (y_zero)
r0, r1, r2 = disp.rects
bases = [round(r.y + r.hauteur, 6) for r in disp.rects]
check(len(set(bases)) == 1, "barres : même ligne de base")
check(proche(r2.y, 10), "barres : la valeur max touche le haut (y=marge)")
check(r2.hauteur > r1.hauteur > r0.hauteur, "barres : hauteur croissante avec la valeur")
# proportionnalité exacte : hauteur ∝ valeur (base 0 incluse)
check(proche(r1.hauteur / r0.hauteur, 20 / 10) and proche(r2.hauteur / r0.hauteur, 40 / 10), "barres : hauteur strictement proportionnelle")

# ── 4) nuage/courbe : projection exacte ──
nu = G.nuage([0, 1, 2], [0, 10, 20], largeur=120, hauteur=120, marge=10)
check(len(nu.points) == 3, "nuage : 3 points")
# point (0,0) -> coin bas-gauche (x=marge, y=hauteur-marge) ; (2,20) -> haut-droite
check(proche(nu.points[0].x, 10) and proche(nu.points[0].y, 110), "nuage : (min,min) -> bas-gauche")
check(proche(nu.points[2].x, 110) and proche(nu.points[2].y, 10), "nuage : (max,max) -> haut-droite")
co = G.courbe([0, 1, 2], [0, 10, 20], largeur=120, hauteur=120, marge=10)
check(co.type == "courbe" and len(co.points) == 3, "courbe : type et points")

# ── 5) Rendus déterministes ──
check(G.vers_svg(disp) == G.vers_svg(disp), "SVG déterministe")
svg = G.vers_svg(disp)
check(svg.startswith("<svg") and svg.count("<rect") == 4, "SVG : fond + 3 barres")
img = G.vers_png(disp)
check(isinstance(img, R.Image) and img.largeur == 100, "PNG : Image rendue")
# round-trip du rendu PNG (raster_png prouvé) : le pixel au centre-haut de la barre max est de la couleur barre
img_rt = R.decode(R.encode(img))
cx = int(round((r2.x + r2.largeur / 2)))
cy = int(round(r2.y + 2))
check(img_rt.lit(cx, cy) == (51, 102, 204), "PNG : la barre max occupe bien ses pixels (round-trip)")
# un coin de fond reste blanc
check(img_rt.lit(0, 0) == (255, 255, 255), "PNG : fond blanc préservé")

# ── 6) FAUX=0 ──
check(leve(G.Echelle, 5, 5, 0, 100), "domaine dégénéré -> ValueError")
check(leve(G.Echelle, 0, float("inf"), 0, 1), "borne non finie -> ValueError")
check(leve(G.barres, []), "série vide -> ValueError")
check(leve(G.barres, [1, 2, float("nan")]), "valeur NaN -> ValueError")
check(leve(G.nuage, [1, 2], [1]), "xs/ys longueurs différentes -> ValueError")
check(leve(G.barres, [1, 2], largeur=5, hauteur=5, marge=10), "cadre trop petit -> ValueError")

print(f"\n=== valide_graphique : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
