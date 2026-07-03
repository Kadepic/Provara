"""VALIDE algebre_calcul.py — held-out ADVERSE, FAUX=0. Racines CONNUES (factorisations vérifiables à la main,
non recalculées par la formule) + SOUNDNESS : float refusé, a=0 en quadratique refusé, irrationnel jamais faussé.
"""
from fractions import Fraction

import algebre_calcul as A

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


F = Fraction

# ── ÉQUATIONS LINÉAIRES ──
check(A.equation_lineaire(2, -6) == ("unique", F(3)), "2x-6=0 -> x=3")
check(A.equation_lineaire(3, 9) == ("unique", F(-3)), "3x+9=0 -> x=-3")
check(A.equation_lineaire(4, 1) == ("unique", F(-1, 4)), "4x+1=0 -> x=-1/4")
check(A.equation_lineaire(0, 5) == ("aucune", None), "0x+5=0 -> aucune")
check(A.equation_lineaire(0, 0) == ("infinie", None), "0x+0=0 -> infinité")
check(A.equation_lineaire("1/2", "-3") == ("unique", F(6)), "½x-3=0 -> x=6 (coeffs rationnels en str)")

# ── ÉQUATIONS QUADRATIQUES — racines connues par factorisation ──
check(A.equation_quadratique(1, -3, 2) == ("deux_rationnelles", [F(1), F(2)]), "(x-1)(x-2) -> {1,2}")
check(A.equation_quadratique(1, -5, 6) == ("deux_rationnelles", [F(2), F(3)]), "(x-2)(x-3) -> {2,3}")
check(A.equation_quadratique(2, -7, 3) == ("deux_rationnelles", [F(1, 2), F(3)]), "(2x-1)(x-3) -> {1/2,3}")
check(A.equation_quadratique(6, -5, 1) == ("deux_rationnelles", [F(1, 3), F(1, 2)]), "(2x-1)(3x-1) -> {1/3,1/2}")
check(A.equation_quadratique(1, -2, 1) == ("double", [F(1)]), "(x-1)² -> racine double 1")
check(A.equation_quadratique(1, 6, 9) == ("double", [F(-3)]), "(x+3)² -> racine double -3")
check(A.equation_quadratique(1, 0, 1)[0] == "aucune_reelle", "x²+1 -> aucune racine réelle")
check(A.equation_quadratique(5, 2, 3)[0] == "aucune_reelle", "Δ=4-60<0 -> aucune réelle")
check(A.equation_quadratique(1, 0, -2) == ("deux_irrationnelles", F(8)), "x²-2 -> irrationnelles, Δ=8 (pas de fausse décimale)")
check(A.equation_quadratique(1, -1, -1) == ("deux_irrationnelles", F(5)), "x²-x-1 (nombre d'or) -> irrationnelles, Δ=5")

# vérif NON circulaire : les racines rationnelles annulent vraiment le polynôme
st, rr = A.equation_quadratique(2, -7, 3)
check(all(A.est_racine([3, -7, 2], r) for r in rr), "racines de 2x²-7x+3 annulent bien p (oracle évaluation)")

# ── ÉVALUATION DE POLYNÔME (Horner exact) ──
check(A.evalue_polynome([2, -3, 1], 5) == F(12), "p(x)=x²-3x+2 en 5 -> 12")
check(A.evalue_polynome([0, 0, 0, 1], 2) == F(8), "p(x)=x³ en 2 -> 8")
check(A.evalue_polynome([1], 99) == F(1), "constante")
check(A.est_racine([6, -5, 1], 2) and A.est_racine([6, -5, 1], 3), "2 et 3 racines de x²-5x+6")
check(not A.est_racine([6, -5, 1], 4), "4 n'est pas racine de x²-5x+6")

# ── SOUNDNESS — entrée invalide -> ValueError (jamais un faux) ──
check(leve(A.equation_lineaire, 1.5, 2), "float refusé (linéaire) -> ValueError")
check(leve(A.equation_quadratique, 0, 2, 1), "a=0 en quadratique -> ValueError")
check(leve(A.equation_quadratique, 1.0, 2, 3), "float refusé (quadratique) -> ValueError")
check(leve(A.evalue_polynome, [], 3), "polynôme vide -> ValueError")
check(leve(A.equation_lineaire, "abc", 2), "coeff non rationnel -> ValueError")

# ── DÉTERMINISME ──
check(A.equation_quadratique(1, -3, 2) == A.equation_quadratique(1, -3, 2), "déterminisme")

print(f"\n=== valide_algebre_calcul : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
