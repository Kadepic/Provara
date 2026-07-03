"""
VALIDE drake.py — held-out ADVERSE. L'équation de Drake étant une DÉFINITION (produit de 7 facteurs), l'exactitude
est ancrée sur des produits calculés par un CHEMIN INDÉPENDANT (arithmétique RATIONNELLE EXACTE via fractions.Fraction,
PAS la même expression flottante) + cas externes connus (cas « classique » de Drake N=1, facteur nul -> N=0) +
SOUNDNESS : facteur négatif, fraction hors [0,1], type/booléen/NaN/inf -> ValueError + déterminisme.
Aucune de ces ancres n'est codée dans drake.py.
"""
from fractions import Fraction

import drake as D

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve_valueerror(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False  # toute AUTRE exception = échec (on exige ValueError, abstention propre)


def ancre_exacte(facteurs_rationnels):
    """Produit EXACT via Fraction (chemin de calcul indépendant du float de drake.py)."""
    p = Fraction(1)
    for f in facteurs_rationnels:
        p *= f
    return float(p)


def approx(args, attendu, tol=1e-9):
    v = D.nombre_civilisations(*args)
    return abs(v - attendu) <= tol * (1 + abs(attendu))


# ── 1) ANCRE EXTERNE CONNUE — cas « classique » de Drake : N = 1 ──
classique = (1, 0.5, 2, 1, 0.01, 0.01, 10000)
attendu_classique = ancre_exacte([Fraction(1), Fraction(1, 2), Fraction(2), Fraction(1),
                                   Fraction(1, 100), Fraction(1, 100), Fraction(10000)])
check(abs(attendu_classique - 1.0) == 0.0, "ancre rationnelle indépendante = 1 exactement")
check(approx(classique, 1.0), "Drake classique R=1,fp=.5,ne=2,fl=1,fi=.01,fc=.01,L=1e4 -> N=1")

# ── 2) EXACTITUDE — produits ancrés par Fraction (chemin indépendant) ──
cas = [
    ((2, 0.5, 4, 0.5, 0.5, 0.5, 10000),
     [Fraction(2), Fraction(1, 2), Fraction(4), Fraction(1, 2), Fraction(1, 2), Fraction(1, 2), Fraction(10000)]),
    ((10, 1, 1, 1, 1, 1, 1000),
     [Fraction(10), Fraction(1), Fraction(1), Fraction(1), Fraction(1), Fraction(1), Fraction(1000)]),
    ((3, 0.25, 2, 0.1, 0.2, 0.5, 200),
     [Fraction(3), Fraction(1, 4), Fraction(2), Fraction(1, 10), Fraction(1, 5), Fraction(1, 2), Fraction(200)]),
    ((7, 0.8, 1.5, 0.3, 1, 0.05, 5000),
     [Fraction(7), Fraction(4, 5), Fraction(3, 2), Fraction(3, 10), Fraction(1), Fraction(1, 20), Fraction(5000)]),
]
for args, rats in cas:
    check(approx(args, ancre_exacte(rats)), f"produit exact (Fraction) pour {args}")

# valeurs hand-calculées explicites (double ancrage)
check(approx((2, 0.5, 4, 0.5, 0.5, 0.5, 10000), 5000.0), "= 5000 (calcul à la main)")
check(approx((10, 1, 1, 1, 1, 1, 1000), 10000.0), "= 10000 (calcul à la main)")

# ── 3) FACTEUR NUL -> N=0 (zéro est valide, le résultat doit être 0, jamais autre chose) ──
check(approx((5, 0, 3, 1, 1, 1, 100), 0.0), "fp=0 -> N=0")
check(approx((0, 0.5, 2, 1, 0.5, 0.5, 100), 0.0), "R=0 -> N=0")
check(approx((5, 0.5, 2, 1, 0.5, 0.5, 0), 0.0), "L=0 -> N=0")
check(approx((5, 0.5, 0, 1, 0.5, 0.5, 100), 0.0), "ne=0 -> N=0")

# ── 4) BORNES de fraction acceptées (0 et 1 inclus) ──
check(approx((1, 1, 1, 1, 1, 1, 42), 42.0), "fractions = 1 (bornes incluses) -> N=42")
check(approx((1, 0, 1, 1, 1, 1, 42), 0.0), "fractions = 0 (bornes incluses) -> N=0")

# ── 5) DÉTERMINISME ──
check(D.nombre_civilisations(*classique) == D.nombre_civilisations(*classique), "déterministe")

# ── 6) SOUNDNESS — facteur NÉGATIF -> ValueError ──
check(leve_valueerror(D.nombre_civilisations, -1, 0.5, 2, 1, 0.01, 0.01, 10000), "R<0 -> ValueError")
check(leve_valueerror(D.nombre_civilisations, 1, 0.5, -2, 1, 0.01, 0.01, 10000), "ne<0 -> ValueError")
check(leve_valueerror(D.nombre_civilisations, 1, 0.5, 2, 1, 0.01, 0.01, -10000), "L<0 -> ValueError")

# ── 7) SOUNDNESS — fraction HORS [0,1] -> ValueError ──
check(leve_valueerror(D.nombre_civilisations, 1, 1.5, 2, 1, 0.01, 0.01, 10000), "fp>1 -> ValueError")
check(leve_valueerror(D.nombre_civilisations, 1, -0.1, 2, 1, 0.01, 0.01, 10000), "fp<0 -> ValueError")
check(leve_valueerror(D.nombre_civilisations, 1, 0.5, 2, 2, 0.01, 0.01, 10000), "fl>1 -> ValueError")
check(leve_valueerror(D.nombre_civilisations, 1, 0.5, 2, 1, -0.01, 0.01, 10000), "fi<0 -> ValueError")
check(leve_valueerror(D.nombre_civilisations, 1, 0.5, 2, 1, 0.01, 1.0001, 10000), "fc>1 -> ValueError")

# ── 8) SOUNDNESS — types invalides (str / bool / NaN / inf) -> ValueError ──
check(leve_valueerror(D.nombre_civilisations, 1, 0.5, 2, 1, 0.01, 0.01, "x"), "L=str -> ValueError")
check(leve_valueerror(D.nombre_civilisations, True, 0.5, 2, 1, 0.01, 0.01, 10000), "R=bool -> ValueError")
check(leve_valueerror(D.nombre_civilisations, 1, False, 2, 1, 0.01, 0.01, 10000), "fp=bool -> ValueError")
check(leve_valueerror(D.nombre_civilisations, 1, 0.5, 2, 1, 0.01, 0.01, float("nan")), "L=NaN -> ValueError")
check(leve_valueerror(D.nombre_civilisations, 1, 0.5, float("inf"), 1, 0.01, 0.01, 10000), "ne=inf -> ValueError")
check(leve_valueerror(D.nombre_civilisations, None, 0.5, 2, 1, 0.01, 0.01, 10000), "R=None -> ValueError")

print(f'\n=== valide_drake : {ok}/{ok+ko} ===')
import sys
sys.exit(0 if ko == 0 else 1)
