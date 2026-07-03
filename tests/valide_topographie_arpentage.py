"""VALIDE topographie_arpentage.py — ADVERSE, FAUX=0.
Arpentage : pente %, distance horizontale = D·cos, dénivelé = D·sin, aire par shoelace,
ancres CONNUES non circulaires (carré 10×10 = 100, triangle 3-4-5 = 6, Pythagore dh²+Δh²=D²)
+ SOUNDNESS (distance ≤ 0, < 3 points, angle hors borne, coord non numérique -> ValueError)
+ déterminisme."""
import math

import topographie_arpentage as T

ok = 0
ko = 0


def check(c, l):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {l}")


def proche(a, b, rel=1e-4):
    return abs(a - b) <= rel * abs(b) + 1e-6


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── PENTE EN POURCENTAGE (ancre du sujet : 10 m / 100 m = 10 %) ──
check(T.pente_pourcent(10, 100) == 10.0, "10 m / 100 m = 10 %")
check(T.pente_pourcent(100, 100) == 100.0, "100 m / 100 m = 100 % (45°)")
check(T.pente_pourcent(0, 50) == 0.0, "Δh=0 -> 0 % (terrain plat)")
check(T.pente_pourcent(-5, 100) == -5.0, "descente Δh=-5 -> -5 %")
check(proche(T.pente_pourcent(3, 4), 75.0), "3/4 = 75 %")

# ── DISTANCE HORIZONTALE = D·cos(α) ──
check(T.distance_horizontale(100, 0) == 100.0, "α=0 -> d = D (terrain plat)")
check(proche(T.distance_horizontale(100, 60), 50.0), "D=100, α=60° -> d=50 (cos60=½)")
check(proche(T.distance_horizontale(100, 45), 100 / math.sqrt(2)), "α=45° -> d = D/√2")
check(proche(T.distance_horizontale(141.4213562373095, 45), 100.0), "D=100√2, α=45° -> d=100")
check(proche(T.distance_horizontale(50, -30), 50 * math.cos(math.radians(30))), "α négatif : cos pair")

# ── DÉNIVELÉ = D·sin(α) ──
check(proche(T.denivele(30, 100), 50.0), "α=30°, D=100 -> Δh=50 (sin30=½)")
check(proche(T.denivele(90, 100), 100.0), "α=90° -> Δh=D (vertical)")
check(T.denivele(0, 100) == 0.0, "α=0 -> Δh=0")
check(proche(T.denivele(45, 100), 100 / math.sqrt(2)), "α=45° -> Δh = D/√2")
check(proche(T.denivele(-30, 100), -50.0), "descente α=-30° -> Δh=-50 (signe)")

# ── COHÉRENCE TRIGO : Pythagore dh² + Δh² = D² (cross-check indépendant) ──
for D, a in [(100, 30), (100, 60), (250, 17), (80, 75)]:
    dh = T.distance_horizontale(D, a)
    dv = T.denivele(a, D)
    check(proche(dh * dh + dv * dv, D * D, rel=1e-3), f"Pythagore D={D}, α={a}° : dh²+Δh²=D²")

# ── AIRE PAR COORDONNÉES (shoelace) — ancres géométriques connues ──
carre = [(0, 0), (10, 0), (10, 10), (0, 10)]
check(T.aire_polygone_coords(carre) == 100.0, "carré 10×10 par coords = 100")
check(T.aire_polygone_coords([(0, 0), (4, 0), (0, 3)]) == 6.0, "triangle 3-4-5 = 6 (½·b·h)")
check(T.aire_polygone_coords([(1, 1), (5, 1), (5, 4), (1, 4)]) == 12.0, "rectangle 4×3 (origine décalée) = 12")
# orientation horaire -> même aire (valeur absolue)
check(T.aire_polygone_coords(list(reversed(carre))) == 100.0, "sens horaire -> même aire (|·|)")
# invariance par translation
carre_tr = [(x + 7, y - 3) for x, y in carre]
check(T.aire_polygone_coords(carre_tr) == 100.0, "aire invariante par translation")
# triangle quelconque, vérif manuelle : sommets (2,1),(8,3),(4,7)
#   2·(3−7)+8·(7−1)+4·(1−3) = -8+48-8 = 32 ; aire = 32/2 = 16
check(T.aire_polygone_coords([(2, 1), (8, 3), (4, 7)]) == 16.0, "triangle (2,1)(8,3)(4,7) = 16")

# ── DÉTERMINISME ──
check(T.distance_horizontale(123.4, 27) == T.distance_horizontale(123.4, 27), "déterminisme dist. horiz.")
check(T.aire_polygone_coords(carre) == T.aire_polygone_coords(carre), "déterminisme aire")

# ── SOUNDNESS (abstention stricte) ──
check(leve(T.pente_pourcent, 5, 0), "distance horizontale nulle -> ValueError")
check(leve(T.pente_pourcent, 5, -10), "distance horizontale < 0 -> ValueError")
check(leve(T.distance_horizontale, 0, 30), "distance de pente = 0 -> ValueError")
check(leve(T.distance_horizontale, -100, 30), "distance de pente < 0 -> ValueError")
check(leve(T.distance_horizontale, 100, 90), "α=90° (cos=0 dégénéré) -> ValueError")
check(leve(T.denivele, 30, 0), "distance = 0 -> ValueError (dénivelé)")
check(leve(T.denivele, 95, 100), "α=95° hors [−90,90] -> ValueError")
check(leve(T.aire_polygone_coords, [(0, 0), (1, 1)]), "< 3 points -> ValueError")
check(leve(T.aire_polygone_coords, [(0, 0)]), "1 point -> ValueError")
check(leve(T.aire_polygone_coords, [(0, 0), (1, 1), (2, "x")]), "coord non numérique -> ValueError")
check(leve(T.pente_pourcent, True, 100), "bool rejeté (pas un réel) -> ValueError")
check(leve(T.aire_polygone_coords, [(0, 0), (1,), (2, 3)]), "sommet malformé -> ValueError")

print(f"\n=== valide_topographie_arpentage : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
