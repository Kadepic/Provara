"""VALIDE algebre_symbolique.py — held-out ADVERSE, FAUX=0.

Ancres NON CIRCULAIRES : chaque valeur attendue est connue INDÉPENDAMMENT de la fonction testée —
arithmétique posée à la main, coefficients binomiaux, ou SECOND chemin de multiplication (défini ici,
distinct du module). On ne recalcule JAMAIS l'attendu avec la fonction testée.
"""
from fractions import Fraction as F

import algebre_symbolique as A

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


# ── SECOND CHEMIN indépendant : multiplication naïve de polynômes (pour construire des ancres) ────────────────────
def mul(p, q):
    """Multiplication de polynômes lowest-first, écrite ICI (chemin distinct du module)."""
    if not p or not q:
        return []
    r = [F(0)] * (len(p) + len(q) - 1)
    for i, a in enumerate(p):
        for j, b in enumerate(q):
            r[i + j] += F(a) * F(b)
    while r and r[-1] == 0:
        r.pop()
    return r


def lin(root):
    return [F(-root), F(1)]  # x − root


X = ("var",)


def cst(c):
    return ("const", c)


# ── DÉVELOPPEMENT — coefficients binomiaux, lowest-first (ancres écrites en dur) ──────────────────────────────────
# (x+1)^3 = 1 + 3x + 3x² + x³  -> [1,3,3,1] (triangle de Pascal, ligne 3)
check(A.developpe(("^", ("+", X, cst(1)), 3)) == [F(1), F(3), F(3), F(1)], "(x+1)^3 = [1,3,3,1]")
# (x+1)(x-1) = x² − 1 -> [-1,0,1]
check(A.developpe(("*", ("+", X, cst(1)), ("-", X, cst(1)))) == [F(-1), F(0), F(1)], "(x+1)(x-1) = x²−1")
# (x+1)^2 = x² + 2x + 1 -> [1,2,1]
check(A.developpe(("^", ("+", X, cst(1)), 2)) == [F(1), F(2), F(1)], "(x+1)^2 = [1,2,1]")
# (x-2)^2 = x² − 4x + 4 -> [4,-4,1]
check(A.developpe(("^", ("-", X, cst(2)), 2)) == [F(4), F(-4), F(1)], "(x-2)^2 = [4,-4,1]")
# (2x+3)^2 = 4x² + 12x + 9 -> [9,12,4]  (arithmétique à la main : 3²=9, 2·2·3=12, 2²=4)
check(A.developpe(("^", ("+", ("*", cst(2), X), cst(3)), 2)) == [F(9), F(12), F(4)], "(2x+3)^2 = [9,12,4]")
# x^0 = 1 (polynôme constant)
check(A.developpe(("^", X, 0)) == [F(1)], "x^0 = 1")
# const 0 -> polynôme nul []
check(A.developpe(cst(0)) == [], "const 0 -> []")
# var seul -> x = [0,1]
check(A.developpe(X) == [F(0), F(1)], "var -> [0,1]")
# coefficient Fraction : (x/2 + 1)·2 ... simple : const(1/2) -> [1/2]
check(A.developpe(cst(F(1, 2))) == [F(1, 2)], "const 1/2 -> [1/2]")

# ── IDENTITÉS REMARQUABLES — ancres arithmétiques posées à la main ────────────────────────────────────────────────
# (a+b)² = a²+2ab+b², a=3,b=5 : (3+5)² = 64 ; 9 + 30 + 25 = 64
g, d = A.identite("carre_somme", 3, 5)
check(g == d == [F(64)], "carre_somme(3,5) : membres égaux = 64")
check(g == [F((3 + 5) ** 2)] and g == [F(3 * 3 + 2 * 3 * 5 + 5 * 5)], "carre_somme : 64 = 8² = 9+30+25")
# (a-b)² a=7,b=2 : 5²=25 ; 49-28+4=25
g, d = A.identite("carre_difference", 7, 2)
check(g == d == [F(25)], "carre_difference(7,2) = 25 = 5²")
# a²−b² = (a−b)(a+b), a=7,b=3 : 40 = 4×10 ; 49−9=40
g, d = A.identite("difference_carres", 7, 3)
check(g == d == [F(40)], "difference_carres(7,3) = 40")
check(g == [F((7 - 3) * (7 + 3))] and g == [F(49 - 9)], "difference_carres : 40 = 4×10 = 49−9")
# a³−b³ = (a−b)(a²+ab+b²), a=5,b=2 : 117 = 3×39 ; 125−8=117
g, d = A.identite("difference_cubes", 5, 2)
check(g == d == [F(117)], "difference_cubes(5,2) = 117")
check(g == [F((5 - 2) * (25 + 10 + 4))] and g == [F(125 - 8)], "difference_cubes : 117 = 3×39 = 125−8")
# a³+b³ = (a+b)(a²−ab+b²), a=2,b=3 : 35 = 5×7 ; 8+27=35
g, d = A.identite("somme_cubes", 2, 3)
check(g == d == [F(35)], "somme_cubes(2,3) = 35 = 8+27")
check(g == [F((2 + 3) * (4 - 6 + 9))], "somme_cubes : 35 = 5×7")
# (a+b)³ a=1,b=1 : 2³=8 ; 1+3+3+1=8
g, d = A.identite("cube_somme", 1, 1)
check(g == d == [F(8)], "cube_somme(1,1) = 8 = 2³")
check(g == [F(1 + 3 + 3 + 1)], "cube_somme(1,1) : 8 = 1+3+3+1")
# (a-b)³ a=4,b=1 : 3³=27
g, d = A.identite("cube_difference", 4, 1)
check(g == d == [F(27)], "cube_difference(4,1) = 27 = 3³")
# catalogue complet = 7 identités
check(len(A.catalogue_identites()) == 7, "catalogue = 7 identités remarquables")

# ── FACTORISATION — racines rationnelles, irréductibilité honnête ─────────────────────────────────────────────────
# factorise(x²−3x+2) -> racines 1 et 2 (x²−3x+2 = (x−1)(x−2))
check(A.racines_rationnelles([2, -3, 1]) == [F(1), F(2)], "racines de x²−3x+2 = {1,2}")
# factorise(x²+1) -> IRRÉDUCTIBLE sur ℚ (aucune racine rationnelle)
check(A.racines_rationnelles([1, 0, 1]) == [], "x²+1 irréductible sur ℚ (aucune racine)")
# x²−2 irréductible sur ℚ (√2 irrationnel)
check(A.racines_rationnelles([-2, 0, 1]) == [], "x²−2 irréductible sur ℚ")
# racine avec multiplicité : (x−1)² = x²−2x+1 -> [1,1]
check(A.racines_rationnelles([1, -2, 1]) == [F(1), F(1)], "x²−2x+1 : racine double 1")
# racine rationnelle non entière : 2x−1 -> 1/2
check(A.racines_rationnelles([-1, 2]) == [F(1, 2)], "2x−1 : racine 1/2")
# x factor : x²−x = x(x−1) -> {0,1}
check(A.racines_rationnelles([0, -1, 1]) == [F(0), F(1)], "x²−x : racines {0,1}")
# polynôme nul -> abstention
check(leve(A.racines_rationnelles, []), "racines du polynôme nul -> ValueError")
check(leve(A.racines_rationnelles, [0, 0]), "racines du polynôme nul (zéros) -> ValueError")

# factorise renvoie un arbre développable : irréductible rendu tel quel
check(A.developpe(A.factorise([1, 0, 1])) == [F(1), F(0), F(1)], "factorise(x²+1) rendu tel quel")
check(A.developpe(A.factorise([-2, 0, 1])) == [F(-2), F(0), F(1)], "factorise(x²−2) rendu tel quel")

# ── BOUCLE FERMÉE : developpe(factorise(p)) == p pour 30 polynômes DÉTERMINISTES ──────────────────────────────────
polys = []
# 25 produits de deux facteurs linéaires (racines entières), construits par le SECOND chemin `mul`
for a in range(-2, 3):        # 5
    for b in range(-2, 3):    # 5 -> 25
        polys.append(mul(lin(a), lin(b)))
# + 5 polynômes avec facteur IRRÉDUCTIBLE x²+1 (ou contenu non trivial)
polys.append(mul([1, 0, 1], lin(3)))        # (x²+1)(x−3)
polys.append(mul([2, 0, 1], lin(1)))        # (x²+2)(x−1)
polys.append(mul([1, 0, 1], [1, 0, 1]))     # (x²+1)²  (irréductible, sans racine)
polys.append([F(-6), F(4)])                 # 4x−6 = 2(2x−3), contenu 2, racine 3/2
polys.append(mul(mul(lin(1), lin(1)), lin(-2)))  # (x−1)²(x+2)
check(len(polys) == 30, "30 polynômes déterministes construits")
for i, p in enumerate(polys):
    rebuilt = A.developpe(A.factorise(p))
    check(rebuilt == A.simplifie(p), f"boucle fermée developpe∘factorise poly#{i} {p}")

# ── ÉVALUATION (Horner exact) — ancres à la main ─────────────────────────────────────────────────────────────────
# x²−1 en 4 : 16−1 = 15
check(A.evalue([-1, 0, 1], 4) == F(15), "evalue(x²−1, 4) = 15")
# (x+1)^3 = [1,3,3,1] en 2 : 3³ = 27 ; 1+6+12+8 = 27
check(A.evalue([1, 3, 3, 1], 2) == F(27), "evalue([1,3,3,1], 2) = 27")
# évaluation en Fraction : x² en 1/2 = 1/4
check(A.evalue([0, 0, 1], F(1, 2)) == F(1, 4), "evalue(x², 1/2) = 1/4")

# ── SIMPLIFICATION / ÉGALITÉ / DEGRÉ ─────────────────────────────────────────────────────────────────────────────
check(A.simplifie([1, 2, 0, 0]) == [F(1), F(2)], "zéros de tête supprimés")
check(A.simplifie([0, 0, 0]) == [], "polynôme nul -> []")
check(A.simplifie([F(2, 4)]) == [F(1, 2)], "coefficient réduit 2/4 -> 1/2")
check(A.egal([1, 2, 0], [1, 2]) is True, "égalité modulo zéros de tête")
check(A.egal([1, 2], [1, 3]) is False, "inégalité détectée")
check(A.degre([1, 2, 3]) == 2, "degré = 2")
check(A.degre([]) == -1, "degré du nul = -1")

# ── DÉTERMINISME ─────────────────────────────────────────────────────────────────────────────────────────────────
t = ("^", ("+", X, cst(2)), 4)
check(A.developpe(t) == A.developpe(t), "déterminisme developpe")
check(A.factorise([2, -3, 1]) == A.factorise([2, -3, 1]), "déterminisme factorise")
check(A.racines_rationnelles([2, -3, 1]) == A.racines_rationnelles([2, -3, 1]), "déterminisme racines")

# ── SOUNDNESS — abstention structurelle (faux positif INTERDIT) ──────────────────────────────────────────────────
check(leve(A.developpe, ("foo", 1)), "nœud inconnu -> ValueError")
check(leve(A.developpe, ("^", X, -1)), "exposant négatif -> ValueError")
check(leve(A.developpe, ("^", X, 1.0)), "exposant flottant -> ValueError")
check(leve(A.developpe, ("^", X, True)), "exposant booléen -> ValueError")
check(leve(A.developpe, ("const", 1.5)), "coefficient flottant -> ValueError")
check(leve(A.developpe, ("const", True)), "coefficient booléen -> ValueError")
check(leve(A.developpe, ("const", "x")), "coefficient chaîne -> ValueError")
check(leve(A.developpe, ("var", 1)), "('var',1) mal formé -> ValueError")
check(leve(A.developpe, ("+", X)), "('+',a) arité fausse -> ValueError")
check(leve(A.developpe, "x"), "arbre non-tuple -> ValueError")
check(leve(A.simplifie, [1, 2.0, 3]), "coefficient flottant dans simplifie -> ValueError")
check(leve(A.simplifie, [1, True]), "coefficient booléen dans simplifie -> ValueError")
check(leve(A.simplifie, "abc"), "simplifie chaîne -> ValueError")
check(leve(A.evalue, [1, 2, 1], 2.5), "evalue x flottant -> ValueError")
check(leve(A.evalue, [1, 2, 1], "z"), "evalue x chaîne -> ValueError")
check(leve(A.evalue, [1, 2, 1], True), "evalue x booléen -> ValueError")
check(leve(A.identite, "inconnue", 1, 2), "identité hors catalogue -> ValueError")
check(leve(A.identite, "carre_somme", 1.0, 2), "identité a flottant -> ValueError")
check(leve(A.identite, "carre_somme", 1, True), "identité b booléen -> ValueError")
check(leve(A.identite, 42, 1, 2), "nom d'identité non-chaîne -> ValueError")

print(f"\n=== valide_algebre_symbolique : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
