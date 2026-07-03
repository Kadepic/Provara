"""
VALIDE equa_diff.py — held-out ADVERSE. Exactitude des solutions d'EDO (ancrées sur des valeurs CONNUES, PAS
recalculées par la même expression du module : constante d'Euler e=2.71828…, doublement t=2 demi-périodes -> ×4,
demi-vie -> moitié exactement, équilibre de Newton 20 °C, droite y=5+3t…) + SOUNDNESS : discrétisation ≤ 0,
n_pas non entier, f non appelable, k ≤ 0, type non numérique -> ValueError (jamais un faux). + DÉTERMINISME.
Aucun de ces cas-test n'est codé en dur dans equa_diff.py.
"""
import math

import equa_diff as M

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def approx(a, b, tol=1e-6):
    return abs(a - b) <= tol


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) EXACTITUDE analytique — ancres EXTERNES ──
# y'=k·y, y0=1,k=1,t=1 -> e (constante mathématique connue, pas recalculée)
check(approx(M.solution_exponentielle(1, 1, 1), math.e), "y(1)=e pour y'=y, y0=1")
# t=0 -> y0 quel que soit k
check(M.solution_exponentielle(100, -0.1, 0) == 100.0, "y(0)=y0")
# Doublement : k=ln2 -> chaque unité de t double ; t=2 -> ×4 (raisonnement indépendant)
check(approx(M.solution_exponentielle(1, math.log(2), 2), 4.0), "doublement ln2 sur t=2 -> 4")
# Demi-vie cohérente : avec k=ln2, après t=1 il reste exactement la moitié
check(approx(M.solution_exponentielle(100, -math.log(2), 1), 50.0), "1 demi-vie -> moitié")

# demi_vie : t½ = ln2/k ; pour k=ln2 -> 1 (ancre exacte)
check(M.demi_vie(math.log(2)) == 1.0, "demi-vie(ln2)=1")
# pour k=1 -> ln2 = 0.6931471805599453
check(approx(M.demi_vie(1), 0.6931471805599453), "demi-vie(1)=ln2")

# solution_affine — refroidissement de Newton y'=-(y-20), y0=100, t=1 :
# 80·e^-1 + 20 = 49.43035529371538 (calculé à la main, externe au module)
check(approx(M.solution_affine(100, -1, 20, 1), 49.43035529371538), "Newton refroidissement t=1")
# équilibre : si y0 = -b/a, y reste constant (ici -20/-1 = 20)
check(M.solution_affine(20, -1, 20, 5) == 20.0, "équilibre -b/a stationnaire")
# point d'équilibre atteint asymptotiquement : t grand -> ~20
check(approx(M.solution_affine(100, -1, 20, 50), 20.0, tol=1e-6), "asymptote -> équilibre 20")
# a=0 -> droite y = y0 + b·t = 5 + 3·2 = 11 (arithmétique externe)
check(M.solution_affine(5, 0, 3, 2) == 11.0, "a=0 -> droite y0+b·t=11")

# euler — convergence vers la solution analytique e^t
check(approx(M.euler(lambda t, y: y, 1, 0, 1, 100000), math.e, tol=1e-3), "Euler y'=y converge vers e")
# euler exact pour y'=constante : y(t)=y0 + c·t (Euler est exact sur les droites)
check(approx(M.euler(lambda t, y: 2.0, 0, 0, 5, 7), 10.0), "Euler exact sur pente constante -> 10")

# DÉTERMINISME
check(M.solution_exponentielle(3, 0.5, 2) == M.solution_exponentielle(3, 0.5, 2), "déterministe exp")
check(M.euler(lambda t, y: y, 1, 0, 1, 1000) == M.euler(lambda t, y: y, 1, 0, 1, 1000), "déterministe euler")

# ── 2) SOUNDNESS — entrées invalides -> ValueError (abstention) ──
check(leve(M.euler, lambda t, y: y, 1, 0, 1, 0), "euler n_pas=0 -> ValueError")
check(leve(M.euler, lambda t, y: y, 1, 0, 1, -5), "euler n_pas<0 -> ValueError")
check(leve(M.euler, lambda t, y: y, 1, 0, 1, 100.0), "euler n_pas float -> ValueError")
check(leve(M.euler, lambda t, y: y, 1, 0, 1, True), "euler n_pas bool -> ValueError")
check(leve(M.euler, 42, 1, 0, 1, 100), "euler f non appelable -> ValueError")
check(leve(M.demi_vie, 0), "demi_vie k=0 -> ValueError")
check(leve(M.demi_vie, -1), "demi_vie k<0 -> ValueError")
check(leve(M.demi_vie, True), "demi_vie bool -> ValueError")
check(leve(M.demi_vie, "x"), "demi_vie str -> ValueError")
check(leve(M.solution_exponentielle, "a", 1, 1), "exp str -> ValueError")
check(leve(M.solution_exponentielle, True, 1, 1), "exp bool -> ValueError")
check(leve(M.solution_affine, 1, "a", 2, 3), "affine str -> ValueError")
check(leve(M.solution_affine, 1, False, 2, 3), "affine bool -> ValueError")

print(f"\n=== valide_equa_diff : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
