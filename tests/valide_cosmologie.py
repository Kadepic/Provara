"""VALIDE cosmologie.py — held-out ADVERSE, FAUX=0. Ancres EXTERNES connues (loi de Hubble, temps de Hubble pour
H0 Planck/standard, z d'une longueur d'onde doublée) NON recalculées par la même expression + SOUNDNESS : entrée
invalide (H0≤0, λ≤0, distance/vitesse négative, type/valeur non finie) -> ValueError (jamais un faux).
"""
import cosmologie as C

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def approx(x, attendu, rel=1e-6):
    return abs(x - attendu) <= rel * abs(attendu) + 1e-12


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) LOI DE HUBBLE — ancres exactes ──
check(C.vitesse_recession(70, 100) == 7000.0, "v = H0·d = 70·100 = 7000 km/s")
check(C.vitesse_recession(67.4, 10) == 674.0, "v = 67.4·10 = 674 km/s (H0 Planck)")
check(C.vitesse_recession(70, 0) == 0.0, "d=0 -> v=0 (ici et maintenant)")
check(C.distance_hubble(70, 7000) == 100.0, "d = v/H0 = 7000/70 = 100 Mpc")
check(C.distance_hubble(70, 21000) == 300.0, "d = 21000/70 = 300 Mpc")
check(C.distance_hubble(70, 0) == 0.0, "v=0 -> d=0")

# ── 2) ALLER-RETOUR (cohérence interne, non circulaire avec une ancre) ──
check(approx(C.distance_hubble(70, C.vitesse_recession(70, 137)), 137.0), "round-trip d=137 Mpc")

# ── 3) DÉCALAGE VERS LE ROUGE — ancres connues ──
check(C.decalage_rouge(1300.0, 650.0) == 1.0, "λ doublée -> z = 1")
check(C.decalage_rouge(650.0, 650.0) == 0.0, "λ inchangée -> z = 0")
check(approx(C.decalage_rouge(7000.0, 5000.0), 0.4), "z = (7000-5000)/5000 = 0.4")
check(approx(C.decalage_rouge(1216.0, 121.6), 9.0), "Lyman-α décalé ×10 -> z = 9")

# ── 4) ÂGE / TEMPS DE HUBBLE — ancres EXTERNES (Gyr connus) ──
# Temps de Hubble pour H0=70 ≈ 13.97 Gyr ; spec : ≈ 1.4e10 ans à 5 %.
check(approx(C.age_univers(70), 1.4e10, rel=0.05), "1/H0 (H0=70) ≈ 1.4e10 ans (tol 5%)")
# H0 Planck 67.4 -> ≈ 14.5 Gyr ; H0=100 -> ≈ 9.78 Gyr ; loi d'échelle âge ∝ 1/H0.
check(approx(C.age_univers(67.4), 1.45e10, rel=0.05), "1/H0 (H0=67.4) ≈ 1.45e10 ans (Planck)")
check(approx(C.age_univers(100), 9.78e9, rel=0.02), "1/H0 (H0=100) ≈ 9.78e9 ans")
check(approx(C.age_univers(140) * 2, C.age_univers(70), rel=1e-9), "âge ∝ 1/H0 : age(140)·2 = age(70)")

# ── 5) SOUNDNESS — H0 ≤ 0 -> ValueError ──
check(leve(C.vitesse_recession, 0, 100), "H0=0 -> ValueError")
check(leve(C.vitesse_recession, -70, 100), "H0<0 -> ValueError")
check(leve(C.distance_hubble, 0, 7000), "H0=0 (distance) -> ValueError")
check(leve(C.distance_hubble, -1, 7000), "H0<0 (distance) -> ValueError")
check(leve(C.age_univers, 0), "H0=0 (âge) -> ValueError")
check(leve(C.age_univers, -70), "H0<0 (âge) -> ValueError")

# ── 6) SOUNDNESS — longueur d'onde ≤ 0 -> ValueError ──
check(leve(C.decalage_rouge, 1300.0, 0.0), "λ_emis=0 -> ValueError (division indéfinie)")
check(leve(C.decalage_rouge, 0.0, 650.0), "λ_obs=0 -> ValueError")
check(leve(C.decalage_rouge, -1.0, 650.0), "λ_obs<0 -> ValueError")
check(leve(C.decalage_rouge, 1300.0, -650.0), "λ_emis<0 -> ValueError")

# ── 7) SOUNDNESS — distance/vitesse négative -> ValueError ──
check(leve(C.vitesse_recession, 70, -5), "distance négative -> ValueError")
check(leve(C.distance_hubble, 70, -100), "vitesse négative -> ValueError")

# ── 8) SOUNDNESS — types invalides / valeurs non finies -> ValueError ──
check(leve(C.vitesse_recession, True, 100), "bool n'est pas un nombre -> ValueError")
check(leve(C.vitesse_recession, "70", 100), "str -> ValueError")
check(leve(C.vitesse_recession, 70, None), "None -> ValueError")
check(leve(C.age_univers, float("inf")), "inf -> ValueError")
check(leve(C.vitesse_recession, 70, float("nan")), "NaN -> ValueError")

# ── 9) DÉTERMINISME ──
check(C.vitesse_recession(70, 100) == C.vitesse_recession(70, 100), "déterminisme")

print(f"\n=== valide_cosmologie : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
