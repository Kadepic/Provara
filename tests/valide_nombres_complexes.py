"""
VALIDE nombres_complexes.py — held-out ADVERSE. Ancres EXTERNES connues de l'analyse complexe, non recalculées par
la même expression du module : i² = −1, |3+4i| = 5 (triplet 3-4-5), (1+2i)(3+4i) = −5+10i, (1+i)/(1−i) = i,
arg(i) = π/2, arg(−1) = π, (1+i)² = 2i, racines cubiques de l'unité, racines quatrièmes = {1, i, −1, −i}…
+ SOUNDNESS : division par zéro / argument de 0 / racine d'ordre ≤ 0 / exposant non entier / forme invalide -> HORS.
Aucun de ces cas-soundness n'a de réponse dans nombres_complexes.py.
"""
import math

import nombres_complexes as C

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def ap(z, w, tol=1e-9):
    return abs(z[0] - w[0]) <= tol and abs(z[1] - w[1]) <= tol


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True


# ── 1) ANCRES EXTERNES — valeurs algébriques connues ──
check(ap(C.produit((0, 1), (0, 1)), (-1.0, 0.0)), "i² = −1")
check(abs(C.module((3, 4)) - 5.0) <= 1e-9, "|3+4i| = 5 (triplet 3-4-5)")
check(abs(C.module((5, 12)) - 13.0) <= 1e-9, "|5+12i| = 13 (triplet 5-12-13)")
check(abs(C.module((0, 0)) - 0.0) <= 1e-12, "|0| = 0")
check(ap(C.produit((1, 2), (3, 4)), (-5.0, 10.0)), "(1+2i)(3+4i) = −5+10i")
check(ap(C.quotient((1, 1), (1, -1)), (0.0, 1.0)), "(1+i)/(1−i) = i")
check(ap(C.quotient((1, 0), (0, 1)), (0.0, -1.0)), "1/i = −i")
check(ap(C.somme((1, 2), (3, -5)), (4.0, -3.0)), "(1+2i)+(3−5i) = 4−3i")
check(ap(C.conjugue((3, 4)), (3.0, -4.0)), "conj(3+4i) = 3−4i")

# ── 2) ANCRES sur l'argument (atan2, en radians) ──
check(abs(C.argument((1, 0)) - 0.0) <= 1e-9, "arg(1) = 0")
check(abs(C.argument((0, 1)) - math.pi / 2) <= 1e-9, "arg(i) = π/2")
check(abs(C.argument((-1, 0)) - math.pi) <= 1e-9, "arg(−1) = π")
check(abs(C.argument((0, -1)) + math.pi / 2) <= 1e-9, "arg(−i) = −π/2")
check(abs(C.argument((1, 1)) - math.pi / 4) <= 1e-9, "arg(1+i) = π/4")

# ── 3) ANCRES sur la puissance (de Moivre) ──
check(ap(C.puissance((1, 1), 2), (0.0, 2.0)), "(1+i)² = 2i")
check(ap(C.puissance((0, 1), 2), (-1.0, 0.0)), "i² = −1 (via puissance)")
check(ap(C.puissance((0, 1), 4), (1.0, 0.0)), "i⁴ = 1")
check(ap(C.puissance((1, 0), 0), (1.0, 0.0)), "1⁰ = 1")
check(ap(C.puissance((2, 0), 3), (8.0, 0.0)), "2³ = 8 (réel)")
check(ap(C.puissance((0, 1), -1), (0.0, -1.0)), "i⁻¹ = −i")

# ── 4) ANCRES sur les racines n-ièmes ──
rac3 = C.racines_nieme((1, 0), 3)
check(len(rac3) == 3, "3 racines cubiques de l'unité")
check(any(ap(r, (1.0, 0.0)) for r in rac3), "1 est racine cubique de l'unité")
check(any(ap(r, (-0.5, math.sqrt(3) / 2)) for r in rac3), "j = −½+i√3/2 racine cubique")
check(any(ap(r, (-0.5, -math.sqrt(3) / 2)) for r in rac3), "j̄ = −½−i√3/2 racine cubique")
# chaque racine élevée au cube redonne z (vérification croisée par puissance)
check(all(ap(C.puissance(r, 3), (1.0, 0.0)) for r in rac3), "r³ = 1 pour chaque racine cubique")

rac4 = C.racines_nieme((1, 0), 4)
check(len(rac4) == 4, "4 racines quatrièmes de l'unité")
for cible, nom in [((1.0, 0.0), "1"), ((0.0, 1.0), "i"), ((-1.0, 0.0), "−1"), ((0.0, -1.0), "−i")]:
    check(any(ap(r, cible) for r in rac4), f"{nom} est racine quatrième de l'unité")

# racine carrée de −1 = ±i
rac2 = C.racines_nieme((-1, 0), 2)
check(len(rac2) == 2 and any(ap(r, (0.0, 1.0)) for r in rac2) and any(ap(r, (0.0, -1.0)) for r in rac2),
      "√(−1) = ±i")

# ── 5) SOUNDNESS — entrées invalides -> ValueError (jamais un faux) ──
check(leve(C.quotient, (1, 1), (0, 0)), "division par zéro complexe -> HORS")
check(leve(C.quotient, (5, -2), 0), "division par 0 (scalaire) -> HORS")
check(leve(C.argument, (0, 0)), "argument de 0 indéfini -> HORS")
check(leve(C.racines_nieme, (1, 0), 0), "racine d'ordre 0 -> HORS")
check(leve(C.racines_nieme, (1, 0), -2), "racine d'ordre négatif -> HORS")
check(leve(C.puissance, (1, 1), 2.0), "exposant non entier -> HORS")
check(leve(C.puissance, (0, 0), 0), "0⁰ indéfini -> HORS")
check(leve(C.module, "1+i"), "forme str invalide -> HORS")
check(leve(C.module, (1, 2, 3)), "triplet invalide -> HORS")
check(leve(C.produit, (1, 1), (1, "x")), "composante non numérique -> HORS")
check(leve(C.argument, (1, True)), "booléen interdit en composante -> HORS")

# ── 6) DÉTERMINISME ──
check(C.produit((1, 2), (3, 4)) == C.produit((1, 2), (3, 4)), "déterminisme produit")
check(C.racines_nieme((1, 0), 5) == C.racines_nieme((1, 0), 5), "déterminisme racines")

print(f"\n=== valide_nombres_complexes : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
