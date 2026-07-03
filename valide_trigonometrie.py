"""VALIDE trigonometrie.py — ADVERSE, FAUX=0. Angles remarquables connus, identité de Pythagore, loi des cosinus
sur triangles connus (3-4-5), conversions + SOUNDNESS (tan asymptote / triangle impossible -> ValueError)."""
import math

import trigonometrie as T

ok = 0
ko = 0


def check(c, l):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {l}")


def proche(a, b, t=1e-9):
    return abs(a - b) <= t


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ANGLES REMARQUABLES (valeurs exactes connues)
check(T.sin_deg(0) == 0.0 and T.sin_deg(30) == 0.5 and T.sin_deg(90) == 1.0, "sin 0/30/90")
check(T.cos_deg(0) == 1.0 and T.cos_deg(60) == 0.5 and T.cos_deg(90) == 0.0, "cos 0/60/90")
check(T.tan_deg(0) == 0.0 and T.tan_deg(45) == 1.0, "tan 0/45")
check(proche(T.sin_deg(45), math.sqrt(2) / 2) and proche(T.cos_deg(45), math.sqrt(2) / 2), "sin/cos 45 = √2/2")
check(proche(T.sin_deg(60), math.sqrt(3) / 2), "sin 60 = √3/2")
check(T.sin_deg(180) == 0.0 and T.cos_deg(180) == -1.0, "sin/cos 180")

# IDENTITÉ DE PYTHAGORE sin²+cos²=1 sur de nombreux angles
check(all(proche(T.sin_deg(d) ** 2 + T.cos_deg(d) ** 2, 1.0) for d in range(0, 360, 7)), "sin²+cos²=1 partout")

# CONVERSIONS
check(proche(T.deg_vers_rad(180), math.pi) and proche(T.rad_vers_deg(math.pi), 180.0), "deg↔rad 180°=π")
check(proche(T.deg_vers_rad(90), math.pi / 2), "90° = π/2")

# LOI DES COSINUS / triangles
check(T.hypotenuse(3, 4) == 5.0, "hypoténuse 3-4-5")
check(T.hypotenuse(5, 12) == 13.0, "hypoténuse 5-12-13")
check(proche(T.angle_par_cotes(3, 4, 5), 90.0), "angle droit dans 3-4-5")
check(proche(T.angle_par_cotes(1, 1, 1), 60.0), "triangle équilatéral -> 60°")
check(proche(T.loi_cosinus(2, 3, 60), math.sqrt(7)), "loi cosinus 2,3,60° = √7")

# SOUNDNESS
check(leve(T.tan_deg, 90), "tan 90° -> ValueError (asymptote)")
check(leve(T.tan_deg, 270), "tan 270° -> ValueError")
check(leve(T.angle_par_cotes, 1, 1, 5), "inégalité triangulaire violée -> ValueError")
check(leve(T.angle_par_cotes, 0, 4, 5), "côté nul -> ValueError")
check(leve(T.loi_cosinus, -3, 4, 90), "côté négatif -> ValueError")
check(leve(T.sin_deg, "x"), "argument non numérique -> ValueError")

# DÉTERMINISME
check(T.sin_deg(33) == T.sin_deg(33), "déterminisme")

print(f"\n=== valide_trigonometrie : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
