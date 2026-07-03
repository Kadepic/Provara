"""VALIDE calcul_infinitesimal.py — ADVERSE, FAUX=0. Dérivées/primitives/intégrales CONNUES (règle de puissance,
théorème fondamental vérifié indépendamment), limites (dont 0/0 factorisé), + SOUNDNESS (pôle/coeff invalide ->
ValueError)."""
from fractions import Fraction as F

import calcul_infinitesimal as C

ok = 0
ko = 0


def check(c, l):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {l}")


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# DÉRIVATION (règle de puissance)
check(C.derivee([2, -3, 0, 1]) == [F(-3), F(0), F(3)], "d/dx(x³-3x+2) = 3x²-3")
check(C.derivee([5]) == [F(0)], "dérivée d'une constante = 0")
check(C.derivee([0, 0, 0, 0, 1]) == [F(0), F(0), F(0), F(4)], "d/dx(x⁴) = 4x³")
check(C.derivee([7, 2]) == [F(2)], "d/dx(2x+7) = 2")

# INTÉGRATION (théorème fondamental vérifié indépendamment via la primitive)
check(C.integrale_definie([0, 0, 1], 0, 3) == F(9), "∫₀³ x² dx = 9")
check(C.integrale_definie([0, 2], 1, 4) == F(15), "∫₁⁴ 2x dx = 15")
check(C.integrale_definie([1], 0, 5) == F(5), "∫₀⁵ 1 dx = 5")
check(C.integrale_definie([0, 0, 0, 1], 0, 2) == F(4), "∫₀² x³ dx = 4")
# primitive correcte : (primitive)' == polynôme d'origine
for p in ([3, -2, 5], [0, 0, 0, 7], [1, 1, 1, 1]):
    check(C.derivee(C.primitive(p)) == [F(x) for x in p] or C.derivee(C.primitive(p)) == C._poly(p),
          f"(∫p)' = p pour {p}")
# borne inversée : ∫_a^b = -∫_b^a
check(C.integrale_definie([0, 0, 1], 0, 3) == -C.integrale_definie([0, 0, 1], 3, 0), "∫ antisymétrique")

# ÉVALUATION
check(C.evalue([2, -3, 1], 5) == F(12), "p(5) pour x²-3x+2 = 12")

# LIMITES
check(C.limite_polynome_en([2, -3, 1], 4) == F(6), "lim polynôme en 4")
check(C.limite_rationnelle_en([-1, 0, 1], [-1, 1], 1) == F(2), "lim (x²-1)/(x-1) en 1 = 2 (0/0 factorisé)")
check(C.limite_rationnelle_en([-8, 0, 0, 1], [-2, 1], 2) == F(12), "lim (x³-8)/(x-2) en 2 = 12")
check(C.limite_rationnelle_en([6, -5, 1], [1], 3) == F(0), "lim polynôme/constante")
check(C.limite_rationnelle_en([1, 1], [2, 1], 0) == F(1, 2), "lim (x+1)/(x+2) en 0 = 1/2")

# SOUNDNESS
check(leve(C.limite_rationnelle_en, [1], [0, 1], 0), "pôle 1/x en 0 -> ValueError (limite infinie)")
check(leve(C.derivee, [1, "a", 2]), "coefficient invalide -> ValueError")
check(leve(C.integrale_definie, [1.5, 2], 0, 1), "float coeff -> ValueError")

# DÉTERMINISME
check(C.integrale_definie([0, 0, 1], 0, 3) == C.integrale_definie([0, 0, 1], 0, 3), "déterminisme")

print(f"\n=== valide_calcul_infinitesimal : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
