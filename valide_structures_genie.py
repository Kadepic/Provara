"""VALIDE structures_genie.py — held-out ADVERSE, FAUX=0. Ancres EXTERNES de résistance des matériaux (valeurs RDM
hand-vérifiées, NON recalculées par la même expression : I=b·h³/12 d'un rectangle, σ=M·c/I d'une poutre, flèche
F·L³/48EI, charge d'Euler π²EI/L²) + SOUNDNESS : section/dimension/aire ≤ 0, type/NaN/inf -> ValueError (jamais faux).
"""
import math

import structures_genie as S

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def approx(v, attendu, rel=1e-6):
    return abs(v - attendu) <= rel * abs(attendu) + 1e-12


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) MOMENT QUADRATIQUE — ancres géométriques connues ──
check(approx(S.moment_quadratique_rectangle(0.1, 0.2), 6.666666667e-5),
      "I rectangle 0.1×0.2 = 0.1·0.2³/12 = 6.6667e-5 m⁴")
check(approx(S.moment_quadratique_rectangle(1, 1), 1.0 / 12.0), "I carré unité = 1/12 = 0.083333")
check(approx(S.moment_quadratique_rectangle(0.2, 0.3), 0.00045), "I rectangle 0.2×0.3 = 0.2·0.027/12 = 4.5e-4")
# section circulaire : I = π d⁴/64 ; d=2 -> π·16/64 = π/4
check(approx(S.moment_quadratique_cercle(2), math.pi / 4.0), "I cercle d=2 = π/4 ≈ 0.785398")
check(approx(S.moment_quadratique_cercle(0.1), 4.908738521e-6), "I cercle d=0.1 = π·1e-4/64 ≈ 4.9087e-6")
# module de flexion W = b h²/6 = I/(h/2)
check(approx(S.module_resistance_rectangle(0.1, 0.2), 6.666666667e-4), "W rectangle 0.1×0.2 = 0.1·0.04/6 = 6.6667e-4")
check(approx(S.module_resistance_rectangle(0.1, 0.2),
             S.moment_quadratique_rectangle(0.1, 0.2) / 0.1, rel=1e-3),
      "cohérence W = I/(h/2) pour le rectangle")

# ── 2) CONTRAINTE DE TRACTION σ = F/A — ancres simples ──
check(approx(S.contrainte_traction(10000, 0.01), 1.0e6), "σ = 10000 N / 0.01 m² = 1.0 MPa")
check(approx(S.contrainte_traction(2000, 0.005), 400000.0), "σ = 2000 N / 0.005 m² = 0.4 MPa")
check(approx(S.contrainte_traction(-3000, 0.006), -500000.0), "compression : -3000/0.006 = -0.5 MPa")

# ── 3) CONTRAINTE DE FLEXION σ = M·y/I — ancre RDM (poutre rectangulaire) ──
check(approx(S.contrainte_flexion(100, 0.0001, 0.05), 50000.0), "σ = 100·0.05/1e-4 = 50 kPa")
# poutre b=0.1,h=0.2, M=1000 N·m, fibre extrême c=h/2=0.1 : σ = M·c/I = 1.5 MPa
I_rect = S.moment_quadratique_rectangle(0.1, 0.2)
check(approx(S.contrainte_flexion(1000, I_rect, 0.1), 1.5e6, rel=1e-5),
      "σ_max poutre rect (M=1000, c=0.1) = M·c/I = 1.5 MPa")
check(approx(S.contrainte_flexion(1000, I_rect, 0.0), 0.0), "fibre neutre y=0 -> σ = 0")
check(approx(S.contrainte_flexion(-200, 0.0001, 0.05), -100000.0), "moment négatif -> σ négatif (-100 kPa)")

# ── 4) FLÈCHE δ = F·L³/(48·E·I) — ancres ──
check(approx(S.fleche_poutre_appuyee_charge_centree(48000, 1.0, 1000.0, 1.0), 1.0),
      "flèche normalisée 48000·1/(48·1000·1) = 1.0 m")
# acier E=210 GPa, poutre rect ci-dessus, L=2 m, F=1000 N : δ = 8000/(48·210e9·6.6667e-5) ≈ 1.19048e-5 m
check(approx(S.fleche_poutre_appuyee_charge_centree(1000, 2.0, 210e9, I_rect), 1.190476190e-5, rel=1e-5),
      "flèche poutre acier ≈ 1.1905e-5 m (0.0119 mm)")

# ── 5) FLAMBEMENT D'EULER P_cr = π²·E·I/L² — ancres ──
check(approx(S.flambement_euler(1.0, 1.0, math.pi), 1.0), "Euler normalisé π²·1·1/π² = 1.0")
check(approx(S.flambement_euler(210e9, I_rect, 3.0), 1.535272034e7, rel=1e-5),
      "Euler poteau acier (L=3) ≈ 15.35 MN")

# ── 6) SOUNDNESS — section / dimension / aire ≤ 0 -> ValueError (jamais un nombre faux) ──
check(leve(S.moment_quadratique_rectangle, 0.0, 0.2), "b=0 -> ValueError")
check(leve(S.moment_quadratique_rectangle, 0.1, 0.0), "h=0 -> ValueError")
check(leve(S.moment_quadratique_rectangle, -0.1, 0.2), "b<0 -> ValueError")
check(leve(S.moment_quadratique_cercle, 0.0), "d=0 -> ValueError")
check(leve(S.moment_quadratique_cercle, -1.0), "d<0 -> ValueError")
check(leve(S.module_resistance_rectangle, 0.0, 0.2), "W : b=0 -> ValueError")
check(leve(S.contrainte_flexion, 100, 0.0, 0.05), "I=0 (flexion) -> ValueError")
check(leve(S.contrainte_flexion, 100, -1e-4, 0.05), "I<0 (flexion) -> ValueError")
check(leve(S.contrainte_traction, 1000, 0.0), "A=0 (traction) -> ValueError")
check(leve(S.contrainte_traction, 1000, -0.01), "A<0 (traction) -> ValueError")
check(leve(S.fleche_poutre_appuyee_charge_centree, 1000, 0.0, 210e9, 1e-4), "L=0 (flèche) -> ValueError")
check(leve(S.fleche_poutre_appuyee_charge_centree, 1000, 2.0, 0.0, 1e-4), "E=0 (flèche) -> ValueError")
check(leve(S.fleche_poutre_appuyee_charge_centree, 1000, 2.0, 210e9, 0.0), "I=0 (flèche) -> ValueError")
check(leve(S.flambement_euler, 0.0, 1e-4, 3.0), "E=0 (Euler) -> ValueError")
check(leve(S.flambement_euler, 210e9, 0.0, 3.0), "I=0 (Euler) -> ValueError")
check(leve(S.flambement_euler, 210e9, 1e-4, 0.0), "L=0 (Euler) -> ValueError")

# ── 7) SOUNDNESS — types invalides (bool/str/None) -> ValueError ──
check(leve(S.contrainte_traction, True, 0.01), "bool n'est pas un nombre -> ValueError")
check(leve(S.contrainte_traction, "mille", 0.01), "str -> ValueError")
check(leve(S.moment_quadratique_rectangle, None, 0.2), "None -> ValueError")
check(leve(S.contrainte_flexion, 100, 0.0001, True), "y=bool -> ValueError")

# ── 8) SOUNDNESS — NaN / inf -> ValueError (jamais un nombre absurde) ──
check(leve(S.contrainte_flexion, float("inf"), 1e-4, 0.05), "M=inf -> ValueError")
check(leve(S.contrainte_flexion, float("nan"), 1e-4, 0.05), "M=NaN -> ValueError")
check(leve(S.moment_quadratique_rectangle, float("nan"), 0.2), "b=NaN -> ValueError")
check(leve(S.fleche_poutre_appuyee_charge_centree, 1000, float("inf"), 210e9, 1e-4), "L=inf -> ValueError")

# ── 9) DÉTERMINISME ──
check(S.moment_quadratique_rectangle(0.1, 0.2) == S.moment_quadratique_rectangle(0.1, 0.2), "déterminisme I")
check(S.contrainte_flexion(1000, I_rect, 0.1) == S.contrainte_flexion(1000, I_rect, 0.1), "déterminisme σ flexion")

print(f"\n=== valide_structures_genie : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
