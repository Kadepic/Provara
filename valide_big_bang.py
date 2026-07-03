"""
VALIDE big_bang.py — held-out ADVERSE. Ancres COSMOLOGIQUES connues (non re-calculées par la même expression) :
  - temps de Hubble pour H0=100 ≈ 9.78 milliards d'années (valeur de manuel) ;
  - âge ~1.40e10 ans pour H0=70 (tol 5 %) ;
  - densité critique pour H0=70 ≈ 9.20e-27 kg/m³ (littérature : ρ_c = 1.878e-26·h²) ;
  - T_CMB = 2.725 K ; abondances BBN ~75 % H / ~25 % He en masse.
+ SOUNDNESS : H0 <= 0 / NaN / inf / non numérique / booléen -> ValueError. + DÉTERMINISME.
"""
import math

import big_bang as M

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
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


def approx(a, b, rel):
    return abs(a - b) <= rel * abs(b) + 1e-30


# ── 1) ÂGE / TEMPS DE HUBBLE ──
check(approx(M.age_univers_hubble(70), 1.40e10, 0.05), "age(70) ≈ 1.40e10 ans (tol 5%)")
# ancre de manuel : 1/H0 pour H0=100 km/s/Mpc ≈ 9.78 Gyr (validation NON circulaire)
check(approx(M.age_univers_hubble(100), 9.78e9, 0.01), "temps de Hubble H0=100 ≈ 9.78 Gyr")
# cohérence d'échelle : t_H ∝ 1/H0  =>  age(140) = age(70)/2
check(approx(M.age_univers_hubble(140), M.age_univers_hubble(70) / 2.0, 1e-12), "age(140) = age(70)/2")
check(M.age_univers_hubble(70) > M.age_univers_hubble(80), "H0 plus grand -> univers plus jeune")

# ── 2) ABONDANCE PRIMORDIALE (fractions de MASSE BBN) ──
ab = M.abondance_primordiale()
check(ab == {"H": 0.75, "He": 0.25}, "abondance = 75% H / 25% He")
check(approx(ab["H"], 0.75, 1e-12) and 0.74 <= ab["H"] <= 0.76, "H ≈ 75% en masse")
check(approx(ab["He"], 0.25, 1e-12) and 0.24 <= ab["He"] <= 0.26, "He-4 ≈ 25% en masse")
check(approx(ab["H"] + ab["He"], 1.0, 1e-12), "fractions de masse somment à 1")
# copie défensive : muter la sortie n'altère pas le fait
ab["H"] = 0.0
check(M.abondance_primordiale()["H"] == 0.75, "abondance immuable (copie défensive)")

# ── 3) TEMPÉRATURE CMB ──
check(M.temperature_cmb() == 2.725, "T_CMB = 2.725 K")

# ── 4) DENSITÉ CRITIQUE (ancre littérature ρ_c = 1.878e-26·h²) ──
check(approx(M.densite_critique(70), 9.20e-27, 0.01), "ρ_c(70) ≈ 9.20e-27 kg/m³")
check(approx(M.densite_critique(70), 1.878e-26 * 0.7 ** 2, 0.01), "ρ_c(70) ≈ 1.878e-26·h² (h=0.7)")
# ρ_c ∝ H0²  =>  doubler H0 quadruple ρ_c
check(approx(M.densite_critique(140), 4.0 * M.densite_critique(70), 1e-9), "ρ_c(140) = 4·ρ_c(70)")
check(M.densite_critique(70) > 0, "densité critique strictement positive")

# ── 5) SOUNDNESS — entrée invalide -> ValueError (abstention, jamais un faux) ──
check(leve_v(M.age_univers_hubble, 0), "age H0=0 -> ValueError")
check(leve_v(M.age_univers_hubble, -70), "age H0<0 -> ValueError")
check(leve_v(M.age_univers_hubble, float("nan")), "age H0=NaN -> ValueError")
check(leve_v(M.age_univers_hubble, float("inf")), "age H0=inf -> ValueError")
check(leve_v(M.age_univers_hubble, "70"), "age H0 chaîne -> ValueError")
check(leve_v(M.age_univers_hubble, None), "age H0 None -> ValueError")
check(leve_v(M.age_univers_hubble, True), "age H0 booléen -> ValueError")
check(leve_v(M.densite_critique, 0), "ρ_c H0=0 -> ValueError")
check(leve_v(M.densite_critique, -1), "ρ_c H0<0 -> ValueError")
check(leve_v(M.densite_critique, float("inf")), "ρ_c H0=inf -> ValueError")
check(leve_v(M.densite_critique, "70"), "ρ_c H0 chaîne -> ValueError")
check(leve_v(M.densite_critique, False), "ρ_c H0 booléen -> ValueError")

# ── 6) DÉTERMINISME ──
check(M.age_univers_hubble(67.4) == M.age_univers_hubble(67.4), "age déterministe")
check(M.densite_critique(67.4) == M.densite_critique(67.4), "ρ_c déterministe")
check(M.temperature_cmb() == M.temperature_cmb(), "T_CMB déterministe")

print(f"\n=== valide_big_bang : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
