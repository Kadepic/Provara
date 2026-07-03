"""VALIDE composites.py — held-out ADVERSE. Exactitude des formules de la loi des mélanges, ancrées sur des valeurs
CONNUES NON re-calculées par la même expression (E_parallèle = 43.4 GPa du cas verre/résine donné ; cas-limites
Vf=0 → matrice / Vf=1 → fibre ; moyenne harmonique Reuss = 1/0.15 = 6.6666… pour Vf=0.5 ; encadrement Reuss ≤ Voigt)
+ SOUNDNESS : Vf hors [0,1], module/densité ≤ 0, type invalide → ValueError (jamais un faux). Déterminisme.
"""
import composites as C

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def approx(v, attendu, tol=1e-6):
    return v is not None and abs(v - attendu) <= tol


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) ANCRE PRINCIPALE (cas verre/résine donné) : Vf=0.6, Ef=70, Em=3.5 -> 0.6·70 + 0.4·3.5 = 43.4 ──
check(approx(C.module_young_composite(0.6, 70, 3.5), 43.4), "E_parallèle verre/résine = 43.4")

# ── 2) CAS-LIMITES module : Vf=0 -> Em (matrice), Vf=1 -> Ef (fibre) ──
check(approx(C.module_young_composite(0, 70, 3.5), 3.5), "Vf=0 -> Em = 3.5")
check(approx(C.module_young_composite(1, 70, 3.5), 70.0), "Vf=1 -> Ef = 70")
# mélange à mi-volume : (70+3.5)/2 = 36.75
check(approx(C.module_young_composite(0.5, 70, 3.5), 36.75), "Vf=0.5 -> moyenne = 36.75")

# ── 3) DENSITÉ (carbone/époxy) : Vf=0.6, rho_f=1.8, rho_m=1.2 -> 0.6·1.8 + 0.4·1.2 = 1.56 ──
check(approx(C.densite_composite(0.6, 1.8, 1.2), 1.56), "rho composite = 1.56")
check(approx(C.densite_composite(0, 1.8, 1.2), 1.2), "Vf=0 -> rho_m = 1.2")
check(approx(C.densite_composite(1, 1.8, 1.2), 1.8), "Vf=1 -> rho_f = 1.8")

# ── 4) BORNE DE REUSS (moyenne harmonique) : Vf=0.5,Ef=70,Em=3.5 -> 1/(0.5/70+0.5/3.5)=1/0.15=6.666666667 ──
check(approx(C.borne_inferieure_reuss(0.5, 70, 3.5), 6.666666667), "Reuss Vf=0.5 = 1/0.15 = 6.6667")
check(approx(C.borne_inferieure_reuss(0, 70, 3.5), 3.5), "Reuss Vf=0 -> Em = 3.5")
check(approx(C.borne_inferieure_reuss(1, 70, 3.5), 70.0), "Reuss Vf=1 -> Ef = 70")
# valeur main : 1/(0.6/70 + 0.4/3.5) = 1/0.12285714285714 = 8.13953488372093
check(approx(C.borne_inferieure_reuss(0.6, 70, 3.5), 8.13953488372093), "Reuss Vf=0.6 = 8.139534884")

# ── 5) ENCADREMENT physique Reuss ≤ Voigt (borne inf ≤ borne sup) sur plusieurs Vf ──
check(all(C.borne_inferieure_reuss(vf, 70, 3.5) <= C.module_young_composite(vf, 70, 3.5) + 1e-9
          for vf in (0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0)), "Reuss ≤ Voigt pour tout Vf")

# ── 6) SOUNDNESS — Vf hors [0,1] -> ValueError ──
check(leve(C.module_young_composite, -0.1, 70, 3.5), "Vf<0 -> ValueError")
check(leve(C.module_young_composite, 1.1, 70, 3.5), "Vf>1 -> ValueError")
check(leve(C.densite_composite, 2.0, 1.8, 1.2), "Vf=2 -> ValueError (densité)")
check(leve(C.borne_inferieure_reuss, -0.5, 70, 3.5), "Vf<0 -> ValueError (Reuss)")

# ── 7) SOUNDNESS — modules / densités ≤ 0 -> ValueError (jamais un nombre absurde, jamais division par 0) ──
check(leve(C.module_young_composite, 0.6, 0, 3.5), "Ef=0 -> ValueError")
check(leve(C.module_young_composite, 0.6, -70, 3.5), "Ef<0 -> ValueError")
check(leve(C.module_young_composite, 0.6, 70, 0), "Em=0 -> ValueError")
check(leve(C.densite_composite, 0.6, 0, 1.2), "rho_f=0 -> ValueError")
check(leve(C.densite_composite, 0.6, 1.8, -1), "rho_m<0 -> ValueError")
check(leve(C.borne_inferieure_reuss, 0.6, 0, 3.5), "Reuss Ef=0 -> ValueError (pas de /0)")
check(leve(C.borne_inferieure_reuss, 0.6, 70, 0), "Reuss Em=0 -> ValueError (pas de /0)")

# ── 8) SOUNDNESS — types invalides (bool / str) -> ValueError ──
check(leve(C.module_young_composite, True, 70, 3.5), "Vf bool -> ValueError")
check(leve(C.module_young_composite, 0.6, "70", 3.5), "Ef str -> ValueError")
check(leve(C.densite_composite, 0.6, True, 1.2), "rho bool -> ValueError")
check(leve(C.borne_inferieure_reuss, 0.6, 70, None), "Em None -> ValueError")

# ── 9) DÉTERMINISME ──
check(C.module_young_composite(0.6, 70, 3.5) == C.module_young_composite(0.6, 70, 3.5), "déterminisme module")
check(C.borne_inferieure_reuss(0.6, 70, 3.5) == C.borne_inferieure_reuss(0.6, 70, 3.5), "déterminisme Reuss")

print(f"\n=== valide_composites : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
