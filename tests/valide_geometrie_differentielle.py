"""VALIDE geometrie_differentielle.py — held-out ADVERSE, FAUX=0. Ancres EXTERNES connues (courbure d'un cercle de
rayon r = 1/r en tout point ; droite = 0 ; parabole y=x² au sommet = 2 ; triangles 3-4-5 / 5-12-13 ; tangente/normale
unitaires de pente 3/4) NON recalculées par la même expression que le module + SOUNDNESS : vitesse nulle, courbure
nulle, type/forme invalides -> ValueError (jamais un faux). Déterminisme.
"""
import math

import geometrie_differentielle as G

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def approx(val, attendu, tol=1e-6):
    return isinstance(val, float) and abs(val - attendu) <= tol


def approx2(couple, attendu, tol=1e-6):
    return (isinstance(couple, tuple) and len(couple) == 2
            and abs(couple[0] - attendu[0]) <= tol and abs(couple[1] - attendu[1]) <= tol)


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── COURBURE — ANCRE : cercle de rayon r -> κ = 1/r EN TOUT POINT (valeur externe, pas le mécanisme du module) ──
# r=2, θ=0 : x=r cosθ, y=r sinθ -> x'=0, y'=r, x''=−r, y''=0
check(approx(G.courbure(0.0, 2.0, -2.0, 0.0), 0.5), "cercle r=2 (θ=0) -> κ = 1/2")
# r=5, θ=π/2 : x'=−r, y'=0, x''=0, y''=−r
check(approx(G.courbure(-5.0, 0.0, 0.0, -5.0), 0.2), "cercle r=5 (θ=π/2) -> κ = 1/5")
# r=3, θ=π/6 : x'=−3·½=−1.5, y'=3·√3/2, x''=−3·√3/2, y''=−1.5  (dérivées pré-calculées, indépendantes du module)
check(approx(G.courbure(-1.5, 2.598076211, -2.598076211, -1.5), 1.0 / 3.0, tol=1e-7),
      "cercle r=3 (θ=π/6) -> κ = 1/3 (indépendant du point)")
# DROITE : accélération nulle -> κ = 0 (deux orientations distinctes)
check(approx(G.courbure(1.0, 1.0, 0.0, 0.0), 0.0), "droite (x'=y'=1) -> κ = 0")
check(approx(G.courbure(3.0, 4.0, 0.0, 0.0), 0.0), "droite (x'=3,y'=4) -> κ = 0")

# ── COURBURE D'UN GRAPHE y=f(x) — ANCRE : parabole y=x² ──
check(approx(G.courbure_graphe(0.0, 2.0), 2.0), "parabole y=x² au sommet (x=0) -> κ = 2")
check(approx(G.courbure_graphe(2.0, 2.0), 2.0 / 5.0 ** 1.5), "parabole y=x² (x=1, y'=2) -> κ = 2/5^1.5")
# cohérence avec la forme paramétrée : courbure_graphe(y',y'') == courbure(1, y', 0, y'')
check(approx(G.courbure_graphe(2.0, 2.0), G.courbure(1.0, 2.0, 0.0, 2.0)), "graphe == paramétré (x'=1,x''=0)")

# ── RAYON DE COURBURE — ANCRE : cercle -> R = r ; parabole sommet -> R = 1/2 ──
check(approx(G.rayon_courbure(0.0, 2.0, -2.0, 0.0), 2.0), "cercle r=2 -> R = 2")
check(approx(G.rayon_courbure(-5.0, 0.0, 0.0, -5.0), 5.0), "cercle r=5 -> R = 5")
check(approx(1.0 / G.courbure_graphe(0.0, 2.0), 0.5), "parabole sommet -> R = 1/2")

# ── LONGUEUR D'ARC — ANCRES : triangles pythagoriciens connus ──
check(approx(G.longueur_arc_segment(3.0, 4.0), 5.0), "segment (3,4) -> 5 (triangle 3-4-5)")
check(approx(G.longueur_arc_segment(5.0, 12.0), 13.0), "segment (5,12) -> 13 (triangle 5-12-13)")
check(approx(G.longueur_arc_segment(-3.0, -4.0), 5.0), "signe sans effet : (−3,−4) -> 5")
check(approx(G.longueur_arc_segment(1.0, 0.0), 1.0), "segment horizontal unité -> 1")
check(approx(G.longueur_polyligne([(0, 0), (3, 4), (3, 9)]), 10.0), "polyligne 5+5 -> 10")
check(approx(G.longueur_polyligne([(0, 0), (3, 4), (0, 8)]), 10.0), "polyligne (0,0)-(3,4)-(0,8) -> 10")

# ── REPÈRE DE FRENET — ANCRES : pente 3/4 -> T=(0.6,0.8), N=(−0.8,0.6) ; orthogonalité ──
check(approx2(G.tangente_unitaire(3.0, 4.0), (0.6, 0.8)), "tangente unitaire (3,4) -> (0.6,0.8)")
check(approx2(G.tangente_unitaire(0.0, 5.0), (0.0, 1.0)), "tangente unitaire (0,5) -> (0,1)")
check(approx2(G.normale_unitaire(3.0, 4.0), (-0.8, 0.6)), "normale unitaire (3,4) -> (−0.8,0.6)")
T = G.tangente_unitaire(3.0, 4.0)
N = G.normale_unitaire(3.0, 4.0)
check(abs(T[0] * N[0] + T[1] * N[1]) < 1e-9, "T ⟂ N (produit scalaire nul)")
check(abs(math.hypot(*T) - 1.0) < 1e-9, "‖T‖ = 1")

# ── SOUNDNESS — vitesse nulle / courbure nulle -> ValueError (abstention, jamais un faux) ──
check(leve(G.courbure, 0.0, 0.0, 1.0, 1.0), "vitesse nulle (x'=y'=0) -> ValueError")
check(leve(G.rayon_courbure, 1.0, 0.0, 0.0, 0.0), "droite : rayon infini -> ValueError")
check(leve(G.rayon_courbure, 0.0, 0.0, 1.0, 1.0), "vitesse nulle propage -> ValueError")
check(leve(G.tangente_unitaire, 0.0, 0.0), "tangente : vitesse nulle -> ValueError")
check(leve(G.normale_unitaire, 0.0, 0.0), "normale : vitesse nulle -> ValueError")

# ── SOUNDNESS — types / formes invalides -> ValueError ──
check(leve(G.courbure, True, 1.0, 0.0, 0.0), "bool n'est pas un réel -> ValueError")
check(leve(G.courbure, 1.0, "a", 0.0, 0.0), "str -> ValueError")
check(leve(G.courbure_graphe, True, 1.0), "graphe bool -> ValueError")
check(leve(G.longueur_arc_segment, float("inf"), 0.0), "non fini -> ValueError")
check(leve(G.longueur_arc_segment, None, 0.0), "None -> ValueError")
check(leve(G.longueur_polyligne, [(0, 0)]), "polyligne < 2 sommets -> ValueError")
check(leve(G.longueur_polyligne, "xy"), "polyligne non-séquence de points -> ValueError")
check(leve(G.longueur_polyligne, [(0, 0), (1,)]), "sommet mal formé -> ValueError")
check(leve(G.longueur_polyligne, [(0, 0), (1, True)]), "sommet à composante bool -> ValueError")

# ── DÉTERMINISME ──
check(G.courbure(0.0, 2.0, -2.0, 0.0) == G.courbure(0.0, 2.0, -2.0, 0.0), "déterminisme courbure")
check(G.tangente_unitaire(3.0, 4.0) == G.tangente_unitaire(3.0, 4.0), "déterminisme tangente")

print(f"\n=== valide_geometrie_differentielle : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
