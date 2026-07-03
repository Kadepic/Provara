"""
VALIDE chaos.py — held-out ADVERSE. Les itérés de l'application logistique sont confrontés à des SOLUTIONS EXACTES
EXTERNES (non recalculées par la carte) : solution close de Schröder pour r=2 [x_n = ½−½(1−2x0)^(2^n)], solution
close pour r=4 [x_n = sin²(2^n·arcsin√x0)], et les deux points du cycle de période 2 pour r=3.2
[(r+1)±√((r−3)(r+1))]/(2r). Puis SOUNDNESS : r∉[0,4], x0∉[0,1], n non-entier, types invalides -> ValueError.
Aucune de ces formules/ancres n'apparaît dans chaos.py.
"""
import math
import chaos as M

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def close(a, b, tol=1e-8):
    return a is not None and abs(a - b) <= tol


# ── ancres externes (solutions closes / valeurs de référence) ──
def cf_r2(x0, n):  # solution close de la carte logistique en r=2
    return 0.5 - 0.5 * (1.0 - 2.0 * x0) ** (2 ** n)


def cf_r4(x0, n):  # solution close en r=4 (conjugaison à la carte tente / doublement d'angle)
    return math.sin(2 ** n * math.asin(math.sqrt(x0))) ** 2


# ── 1) POINT FIXE non trivial 1 − 1/r (valeurs connues, vérifiables à la main) ──
check(close(M.point_fixe_logistique(2), 0.5), "x* (r=2) = 1−1/2 = 0.5")
check(close(M.point_fixe_logistique(4), 0.75), "x* (r=4) = 1−1/4 = 0.75")
check(close(M.point_fixe_logistique(3.2), 0.6875), "x* (r=3.2) = 1−1/3.2 = 0.6875")
# un point fixe est INVARIANT par la carte : itérer depuis x* y reste
check(close(M.iterer_logistique(2, 0.5, 50), 0.5), "x0=x*=0.5 reste 0.5 (r=2, n=50)")
check(close(M.iterer_logistique(4, 0.75, 30), 0.75), "x0=x*=0.75 reste 0.75 (r=4, n=30)")
# point fixe trivial 0 et bord 1->0
check(close(M.iterer_logistique(3.7, 0.0, 100), 0.0), "x0=0 reste 0 (point fixe trivial)")
check(close(M.iterer_logistique(2, 1.0, 5), 0.0), "x0=1 -> 0 puis reste 0")

# ── 2) r=2 : convergence vers 0.5, ancrée sur la solution close (externe) ──
for x0 in (0.1, 0.3, 0.7, 0.42):
    for n in (1, 2, 3, 4, 6, 8):
        check(close(M.iterer_logistique(2, x0, n), cf_r2(x0, n), 1e-7),
              f"r=2 x0={x0} n={n} = solution close {cf_r2(x0, n):.10g}")
check(close(M.iterer_logistique(2, 0.25, 12), 0.5, 1e-7), "r=2 converge vers le point fixe 0.5")

# ── 3) r=4 (chaos) : ancré sur la solution close sin²(2^n arcsin√x0), aux petits n (avant amplification du roundoff) ──
for x0 in (0.1, 0.3, 0.62):
    for n in (1, 2, 3, 5, 8, 10):
        check(close(M.iterer_logistique(4, x0, n), cf_r4(x0, n), 1e-7),
              f"r=4 x0={x0} n={n} = solution close {cf_r4(x0, n):.10g}")
check(close(M.iterer_logistique(4, 0.1, 2), 0.9216, 1e-9), "r=4 : 0.1->0.36->0.9216 (exact)")

# ── 4) r=3.2 : cycle de PÉRIODE 2, ancré sur les deux points théoriques (externe) ──
r = 3.2
s = math.sqrt((r - 3) * (r + 1))
p_haut = ((r + 1) + s) / (2 * r)   # ≈ 0.79945549
p_bas = ((r + 1) - s) / (2 * r)    # ≈ 0.51304451
check(close(M.iterer_logistique(r, p_haut, 1), p_bas), "r=3.2 : f(p_haut) = p_bas")
check(close(M.iterer_logistique(r, p_bas, 1), p_haut), "r=3.2 : f(p_bas) = p_haut")
check(close(M.iterer_logistique(r, p_haut, 2), p_haut), "r=3.2 : f²(p_haut) = p_haut (période 2)")
check(close(M.iterer_logistique(r, p_bas, 2), p_bas), "r=3.2 : f²(p_bas) = p_bas (période 2)")
# convergence d'une condition quelconque vers le 2-cycle : x_n == x_{n+2} ≠ x_{n+1}
a200 = M.iterer_logistique(r, 0.5, 200)
a201 = M.iterer_logistique(r, 0.5, 201)
a202 = M.iterer_logistique(r, 0.5, 202)
check(close(a200, a202, 1e-9), "r=3.2 : x_200 == x_202 (orbite de période 2)")
check(not close(a200, a201, 1e-3), "r=3.2 : x_200 ≠ x_201 (le cycle n'est pas un point fixe)")
check(close(a200, p_bas) or close(a200, p_haut), "r=3.2 : l'orbite atteint un point théorique du 2-cycle")

# ── 5) SENSIBILITÉ aux conditions initiales (le cœur du sujet) ──
check(close(M.sensibilite(2, 0.3, 0.0, 10), 0.0, 1e-15), "delta=0 -> écart nul (déterminisme exact)")
sens_stable = M.sensibilite(2, 0.4, 1e-8, 35)
sens_chaos = M.sensibilite(4, 0.4, 1e-8, 35)
check(sens_stable < 1e-9, f"r=2 (stable) : sensibilité s'éteint (~{sens_stable:.2e})")
check(sens_chaos > 0.05, f"r=4 (chaos) : sensibilité O(1) malgré delta=1e-8 (~{sens_chaos:.3f})")
check(sens_chaos > sens_stable * 1e6, "chaos amplifie >1e6× plus que le régime stable")
check(M.sensibilite(4, 0.4, 1e-9, 40) > 0.05, "r=4 : divergence subsiste pour delta=1e-9, n=40")
# sensibilité = écart symétrique, toujours ≥ 0
check(M.sensibilite(3.9, 0.2, 1e-6, 25) >= 0.0, "sensibilité ≥ 0 (valeur absolue)")

# ── 6) DÉTERMINISME ──
check(M.iterer_logistique(3.8, 0.321, 60) == M.iterer_logistique(3.8, 0.321, 60), "itération déterministe")
check(M.sensibilite(4, 0.3, 1e-7, 30) == M.sensibilite(4, 0.3, 1e-7, 30), "sensibilité déterministe")
check(M.iterer_logistique(2, 0.7, 0) == 0.7, "n=0 -> renvoie x0")


# ── 7) SOUNDNESS : domaines / types invalides -> ValueError (jamais un faux) ──
def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


check(leve(M.iterer_logistique, 4.5, 0.5, 5), "r>4 -> ValueError")
check(leve(M.iterer_logistique, -0.1, 0.5, 5), "r<0 -> ValueError")
check(leve(M.iterer_logistique, float("nan"), 0.5, 5), "r=NaN -> ValueError")
check(leve(M.iterer_logistique, True, 0.5, 5), "r=bool -> ValueError")
check(leve(M.iterer_logistique, 2, 1.5, 5), "x0>1 -> ValueError")
check(leve(M.iterer_logistique, 2, -0.01, 5), "x0<0 -> ValueError")
check(leve(M.iterer_logistique, 2, "0.5", 5), "x0 non numérique -> ValueError")
check(leve(M.iterer_logistique, 2, 0.5, -1), "n<0 -> ValueError")
check(leve(M.iterer_logistique, 2, 0.5, 2.5), "n non entier -> ValueError")
check(leve(M.iterer_logistique, 2, 0.5, True), "n=bool -> ValueError")
check(leve(M.point_fixe_logistique, 0.5), "point_fixe r≤1 -> ValueError (formule hors (0,1))")
check(leve(M.point_fixe_logistique, 1.0), "point_fixe r=1 -> ValueError")
check(leve(M.point_fixe_logistique, 4.5), "point_fixe r>4 -> ValueError")
check(leve(M.sensibilite, 2, 0.9, 0.2, 5), "x0+delta>1 -> ValueError")
check(leve(M.sensibilite, 2, 0.1, -0.2, 5), "x0+delta<0 -> ValueError")
check(leve(M.sensibilite, 5.0, 0.5, 1e-6, 5), "sensibilité r>4 -> ValueError")
check(leve(M.sensibilite, 2, 0.5, float("inf"), 5), "delta=inf -> ValueError")

print(f"\n=== valide_chaos : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
