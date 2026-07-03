"""VALIDE relativite_generale.py — held-out ADVERSE, FAUX=0. Ancres EXTERNES connues (rayons de Schwarzschild
tabulés du Soleil ~2.95 km, de la Terre ~8.87 mm, de 1 kg ~1.485e-27 m ; red-shift gravitationnel à facteur
algébrique connu) NON recalculées par la même expression + SOUNDNESS : entrée invalide -> ValueError (jamais faux).
"""
import math

import relativite_generale as R

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


def approx(v, attendu, rel=1e-9, absx=0.0):
    return abs(v - attendu) <= rel * abs(attendu) + absx


# ── 1) ANCRES EXTERNES CONNUES — rayon de Schwarzschild (valeurs tabulées, NON recalculées ici) ──
MASSE_SOLAIRE = 1.989e30
MASSE_TERRE = 5.972e24
rs_soleil = R.rayon_schwarzschild(MASSE_SOLAIRE)
rs_terre = R.rayon_schwarzschild(MASSE_TERRE)
check(approx(rs_soleil, 2953.0, rel=1e-2), f"r_s(Soleil) ≈ 2953 m (obtenu {rs_soleil})")
check(approx(rs_terre, 8.87e-3, rel=1e-2), f"r_s(Terre) ≈ 8.87e-3 m (obtenu {rs_terre})")
# Rayon de Schwarzschild de 1 kg : valeur de référence ≈ 1.485e-27 m
check(approx(R.rayon_schwarzschild(1.0), 1.485e-27, rel=1e-2), "r_s(1 kg) ≈ 1.485e-27 m")
# Linéarité en M : r_s(2M) = 2·r_s(M) (propriété indépendante de la valeur numérique)
check(approx(R.rayon_schwarzschild(2 * MASSE_SOLAIRE), 2 * rs_soleil, rel=1e-8), "r_s linéaire en M")

# ── 2) DILATATION — ancres à facteur ALGÉBRIQUE connu (non circulaire) ──
# À r = (4/3)·r_s : 1 − r_s/r = 1 − 3/4 = 1/4, donc √ = 1/2 -> τ = 0.5·t.
fac_demi = R.dilatation_gravitationnelle(1.0, MASSE_SOLAIRE, (4.0 / 3.0) * rs_soleil)
check(approx(fac_demi, 0.5, rel=1e-6), f"red-shift facteur 1/2 à r=(4/3)r_s (obtenu {fac_demi})")
# À r = 2·r_s : 1 − 1/2 = 1/2, √ = 1/√2 ≈ 0.7071067812 -> τ pour t=10 s ≈ 7.071067812 s
tau = R.dilatation_gravitationnelle(10.0, MASSE_SOLAIRE, 2.0 * rs_soleil)
check(approx(tau, 10.0 / math.sqrt(2.0), rel=1e-6), f"τ = 10/√2 à r=2 r_s (obtenu {tau})")
# Très loin de la masse : facteur -> 1 (τ ≈ t). À r = 1e8·r_s, écart < 1e-6.
loin = R.dilatation_gravitationnelle(1.0, MASSE_SOLAIRE, 1e8 * rs_soleil)
check(loin < 1.0 and approx(loin, 1.0, rel=0.0, absx=1e-6), f"τ -> t loin de la masse (obtenu {loin})")
# Proportionnalité en t : τ(2t) = 2·τ(t)
t1 = R.dilatation_gravitationnelle(3.0, MASSE_SOLAIRE, 3.0 * rs_soleil)
t2 = R.dilatation_gravitationnelle(6.0, MASSE_SOLAIRE, 3.0 * rs_soleil)
check(approx(t2, 2.0 * t1, rel=1e-9), "τ proportionnel à t")

# ── 3) SOUNDNESS — entrée invalide -> ValueError (jamais un faux résultat) ──
check(leve(R.rayon_schwarzschild, 0.0), "r_s(0) lève (masse nulle)")
check(leve(R.rayon_schwarzschild, -1.0), "r_s(<0) lève (masse négative)")
check(leve(R.rayon_schwarzschild, "x"), "r_s(str) lève (type)")
check(leve(R.rayon_schwarzschild, True), "r_s(bool) lève (type bool exclu)")
check(leve(R.rayon_schwarzschild, float("inf")), "r_s(inf) lève (non fini)")
check(leve(R.dilatation_gravitationnelle, 1.0, MASSE_SOLAIRE, rs_soleil), "dilatation à r=r_s lève (horizon)")
check(leve(R.dilatation_gravitationnelle, 1.0, MASSE_SOLAIRE, 0.5 * rs_soleil), "dilatation à r<r_s lève (intérieur)")
check(leve(R.dilatation_gravitationnelle, 1.0, MASSE_SOLAIRE, 0.0), "dilatation r=0 lève")
check(leve(R.dilatation_gravitationnelle, 1.0, MASSE_SOLAIRE, -1.0), "dilatation r<0 lève")
check(leve(R.dilatation_gravitationnelle, 1.0, -5.0, 1e9), "dilatation M<0 lève")
check(leve(R.dilatation_gravitationnelle, 1.0, 0.0, 1e9), "dilatation M=0 lève")
check(leve(R.dilatation_gravitationnelle, "t", MASSE_SOLAIRE, 1e9), "dilatation t non numérique lève")
check(leve(R.dilatation_gravitationnelle, False, MASSE_SOLAIRE, 1e9), "dilatation t bool exclu lève")

# ── 4) DÉTERMINISME ──
check(R.rayon_schwarzschild(MASSE_TERRE) == R.rayon_schwarzschild(MASSE_TERRE), "r_s déterministe")
check(R.dilatation_gravitationnelle(7.0, MASSE_SOLAIRE, 5.0 * rs_soleil)
      == R.dilatation_gravitationnelle(7.0, MASSE_SOLAIRE, 5.0 * rs_soleil), "dilatation déterministe")

print(f"\n=== valide_relativite_generale : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
