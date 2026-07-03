"""
VALIDE usinage.py — held-out ADVERSE. Ancres sur des valeurs d'atelier CONNUES (Vc à D=50/N=1000 ≈ 157 m/min,
round-trip Vc<->N, MRR = produit, t = L/f, vf = fz·z·N) + SOUNDNESS (toute entrée ≤ 0 / bool / str -> ValueError,
jamais un nombre absurde) + DÉTERMINISME. Aucune de ces valeurs n'est codée en dur dans usinage.py.
"""
import math
import usinage as U

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def approx(a, b, rel=1e-9):
    return abs(a - b) <= rel * abs(b) + 1e-12


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) ANCRES — vitesse de coupe Vc = π·D·N/1000 ──
check(approx(U.vitesse_coupe(50, 1000), math.pi * 50), "Vc(D=50,N=1000) = π·50")
check(abs(U.vitesse_coupe(50, 1000) - 157.08) < 0.01, "Vc(D=50,N=1000) ≈ 157.08 m/min")
check(approx(U.vitesse_coupe(100, 500), math.pi * 100 * 500 / 1000), "Vc(D=100,N=500) = π·50")
check(approx(U.vitesse_coupe(10, 1000), math.pi * 10), "Vc(D=10,N=1000) = 10π m/min")

# ── 2) ROUND-TRIP Vc <-> N (cohérence des deux formules inverses) ──
vc = U.vitesse_coupe(50, 1000)
check(approx(U.rotation_broche(vc, 50), 1000), "N retrouvé = 1000 tr/min depuis Vc")
check(approx(U.rotation_broche(math.pi * 100, 100), 1000), "N = 1000·(100π)/(π·100) = 1000")
check(approx(U.vitesse_coupe(50, U.rotation_broche(120, 50)), 120), "Vc <-> N involutif")

# ── 3) MRR = ae·ap·vf (produit) ──
check(approx(U.taux_enlevement_matiere(2, 3, 100), 600), "MRR = 2·3·100 = 600")
check(approx(U.taux_enlevement_matiere(5, 0.5, 200), 500), "MRR = 5·0.5·200 = 500")
check(approx(U.taux_enlevement_matiere(1, 1, 1), 1), "MRR = 1·1·1 = 1")

# ── 4) temps d'usinage t = L/f ──
check(approx(U.temps_usinage(100, 50), 2), "t = 100/50 = 2 min")
check(approx(U.temps_usinage(800, 400), 2), "t = 800/400 = 2 min")
check(approx(U.temps_usinage(3, 2), 1.5), "t = 3/2 = 1.5 min")

# ── 5) avance par minute vf = fz·z·N (puis chaînage avec t) ──
check(approx(U.avance_par_minute(0.1, 4, 1000), 400), "vf = 0.1·4·1000 = 400 mm/min")
check(approx(U.temps_usinage(800, U.avance_par_minute(0.1, 4, 1000)), 2), "chaînage vf->t : 800/400 = 2 min")

# ── 6) SOUNDNESS — entrées ≤ 0 -> ValueError (jamais un nombre absurde) ──
check(leve(U.vitesse_coupe, 0, 1000), "D=0 -> ValueError")
check(leve(U.vitesse_coupe, 50, 0), "N=0 -> ValueError")
check(leve(U.vitesse_coupe, -50, 1000), "D<0 -> ValueError")
check(leve(U.vitesse_coupe, 50, -1000), "N<0 -> ValueError")
check(leve(U.rotation_broche, 100, 0), "rotation_broche D=0 -> ValueError")
check(leve(U.rotation_broche, 0, 50), "rotation_broche Vc=0 -> ValueError")
check(leve(U.taux_enlevement_matiere, 0, 3, 100), "MRR largeur=0 -> ValueError")
check(leve(U.taux_enlevement_matiere, 2, 0, 100), "MRR profondeur=0 -> ValueError")
check(leve(U.taux_enlevement_matiere, 2, 3, 0), "MRR avance=0 -> ValueError")
check(leve(U.taux_enlevement_matiere, 2, 3, -1), "MRR avance<0 -> ValueError")
check(leve(U.temps_usinage, 100, 0), "t avance=0 -> ValueError (pas division par zéro)")
check(leve(U.temps_usinage, 0, 50), "t longueur=0 -> ValueError")
check(leve(U.temps_usinage, -100, 50), "t longueur<0 -> ValueError")
check(leve(U.avance_par_minute, 0, 4, 1000), "vf fz=0 -> ValueError")
check(leve(U.avance_par_minute, 0.1, 0, 1000), "vf z=0 -> ValueError")
check(leve(U.avance_par_minute, 0.1, 4, 0), "vf N=0 -> ValueError")

# ── 7) SOUNDNESS — types invalides (bool/str/None/NaN/inf) -> ValueError ──
check(leve(U.vitesse_coupe, True, 1000), "bool n'est pas un nombre -> ValueError")
check(leve(U.vitesse_coupe, "50", 1000), "str -> ValueError")
check(leve(U.vitesse_coupe, None, 1000), "None -> ValueError")
check(leve(U.vitesse_coupe, float("nan"), 1000), "NaN -> ValueError")
check(leve(U.vitesse_coupe, float("inf"), 1000), "inf -> ValueError")
check(leve(U.taux_enlevement_matiere, 2, True, 100), "bool en profondeur -> ValueError")

# ── 8) DÉTERMINISME ──
check(U.vitesse_coupe(50, 1000) == U.vitesse_coupe(50, 1000), "déterminisme Vc")
check(U.taux_enlevement_matiere(2, 3, 100) == U.taux_enlevement_matiere(2, 3, 100), "déterminisme MRR")

print(f"\n=== valide_usinage : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
