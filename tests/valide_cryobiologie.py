"""
VALIDE cryobiologie.py — held-out ADVERSE. Exactitude des formules/faits de
congélation (références externes : loi de Raoult Kf_eau=1.86 °C·kg/mol,
point d'ébullition N2 liquide = -196 °C) + soundness (durée<=0, molalité<0 ->
ValueError, jamais une valeur inventée) + déterminisme.
"""
import cryobiologie as C

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve_v(fn, *a, **k):
    """True ssi fn(*a, **k) lève ValueError (abstention)."""
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# 1) CAS DE RÉFÉRENCE (énoncé) — exactitude.
check(abs(C.vitesse_refroidissement(20, -180, 10) - 20.0) < 1e-9,
      "refroidir 20 -> -180 en 10 min = 20 °C/min")
check(abs(C.point_congelation_solution(1, i=2) - (-3.72)) < 1e-9,
      "NaCl 1 molal (i=2) = -3.72 °C")
check(C.azote_liquide() == -196.0, "azote liquide = -196 °C")

# 2) FORMULE vitesse_refroidissement = (Ti - Tf)/temps — held-out.
check(abs(C.vitesse_refroidissement(0, -196, 49) - 4.0) < 1e-9, "0 -> -196 en 49 min = 4")
check(abs(C.vitesse_refroidissement(37, -80, 1) - 117.0) < 1e-9, "37 -> -80 en 1 min = 117")
check(abs(C.vitesse_refroidissement(-10, -190, 60) - 3.0) < 1e-9, "-10 -> -190 en 60 min = 3")
check(abs(C.vitesse_refroidissement(100, 0, 25) - 4.0) < 1e-9, "100 -> 0 en 25 min = 4")
# Tf > Ti -> réchauffement, vitesse négative (formule pure, pas un faux).
check(abs(C.vitesse_refroidissement(-180, 20, 10) - (-20.0)) < 1e-9, "-180 -> 20 en 10 = -20")

# 3) abaissement cryoscopique -Kf*i*b — held-out.
check(abs(C.point_congelation_solution(0) - 0.0) < 1e-9, "molalité 0 -> 0 °C")
check(abs(C.point_congelation_solution(1) - (-1.86)) < 1e-9, "1 molal non-électrolyte i=1 = -1.86")
check(abs(C.point_congelation_solution(2) - (-3.72)) < 1e-9, "2 molal i=1 = -3.72")
check(abs(C.point_congelation_solution(0.5, i=2) - (-1.86)) < 1e-9, "0.5 molal NaCl i=2 = -1.86")
check(abs(C.point_congelation_solution(1, i=3) - (-5.58)) < 1e-9, "1 molal CaCl2 i=3 = -5.58")
# Kf personnalisé (benzène Kf=5.12) reste exact.
check(abs(C.point_congelation_solution(1, Kf=5.12) - (-5.12)) < 1e-9, "Kf=5.12, 1 molal = -5.12")
check(abs(C.point_congelation_solution(2, Kf=5.12, i=1) - (-10.24)) < 1e-9, "Kf=5.12, 2 molal = -10.24")
# Default Kf exposé correctement.
check(C.KF_EAU == 1.86, "constante cryoscopique eau = 1.86")

# 4) SOUNDNESS — entrées invalides -> ValueError (abstention, jamais un faux).
check(leve_v(C.vitesse_refroidissement, 20, -180, 0), "temps=0 -> ValueError")
check(leve_v(C.vitesse_refroidissement, 20, -180, -5), "temps<0 -> ValueError")
check(leve_v(C.point_congelation_solution, -1), "molalité<0 -> ValueError")
check(leve_v(C.point_congelation_solution, -0.001), "molalité<0 (petit) -> ValueError")
check(leve_v(C.point_congelation_solution, 1, 0), "Kf=0 -> ValueError")
check(leve_v(C.point_congelation_solution, 1, -1.86), "Kf<0 -> ValueError")
check(leve_v(C.point_congelation_solution, 1, 1.86, 0), "i<1 (i=0) -> ValueError")
check(leve_v(C.point_congelation_solution, 1, 1.86, 0.5), "i<1 (i=0.5) -> ValueError")
# Types/valeurs non finies refusés.
check(leve_v(C.vitesse_refroidissement, "20", -180, 10), "T_initiale texte -> ValueError")
check(leve_v(C.vitesse_refroidissement, 20, -180, float("inf")), "temps inf -> ValueError")
check(leve_v(C.vitesse_refroidissement, 20, -180, float("nan")), "temps nan -> ValueError")
check(leve_v(C.point_congelation_solution, float("nan")), "molalité nan -> ValueError")
check(leve_v(C.point_congelation_solution, True), "bool refusé (pas un réel) -> ValueError")

# 5) DÉTERMINISME — même entrée, même sortie.
for _ in range(5):
    check(C.vitesse_refroidissement(20, -180, 10) == 20.0, "déterminisme vitesse")
    check(C.point_congelation_solution(1, i=2) == -3.72, "déterminisme cryoscopie")
    check(C.azote_liquide() == -196.0, "déterminisme azote")

print(f"\n=== valide_cryobiologie : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
