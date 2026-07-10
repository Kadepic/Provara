"""
VALIDE algebre_lineaire.py — held-out ADVERSE (FAUX=0).

ANCRES NON CIRCULAIRES (valeurs connues INDÉPENDAMMENT de la formule testée) :
  (a) système x+y=3, x−y=1  -> x=2, y=1                      (résolu à la main).
  (b) det([[1,2],[3,4]]) = 1·4 − 2·3 = -2                    (règle des mineurs, à la main).
  (c) inverse([[1,2],[3,4]]) = [[-2,1],[3/2,-1/2]]           écrit EN DUR, puis confronté à M·M⁻¹ = I
      (deuxième chemin de code : le produit matriciel).
  (d) rang([[1,2],[2,4]]) = 1                                (lignes proportionnelles).
  (e) système x+y=1, x+y=2 -> 'aucune'                       (Rouché-Capelli : rang(A)=1 < rang([A|b])=2).
  (f) système x+y=1 (1 équation, 2 inconnues) -> 'infinite'  (base du noyau de dimension 1).
  (g) matrice singulière [[1,2],[2,4]] -> inverse ValueError (déterminant nul).
  (h) BOUCLE FERMÉE : 20 matrices inversibles déterministes (entiers) -> inverse(inverse(M)) == M.

SOUNDNESS : flottant, bool, str, NaN, inf, vide, dims incohérentes, non carré -> ValueError.
"""
from fractions import Fraction

import algebre_lineaire as L

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
    """True ssi fn(*a) lève ValueError (abstention structurelle)."""
    try:
        fn(*a)
        return False
    except ValueError:
        return True


def F(x):
    return Fraction(x)


# ── (a) SYSTÈME UNIQUE : x+y=3, x−y=1 -> x=2, y=1 (à la main) ──
sol = L.resout_systeme([[1, 1], [1, -1]], [3, 1])
check(sol["type"] == "unique", "(a) type unique")
check(sol["solution"] == [F(2), F(1)], "(a) solution = [2, 1]")
check(sol["rang"] == 2, "(a) rang = 2")

# autre système à la main : 2x+3y=8, x−y=−1 -> x=1, y=2
sol2 = L.resout_systeme([[2, 3], [1, -1]], [8, -1])
check(sol2["type"] == "unique" and sol2["solution"] == [F(1), F(2)], "système 2x+3y=8,x−y=−1 -> [1,2]")

# système 3×3 : identité décalée. x=1,y=2,z=3 ; A·x lu à la main
A3 = [[2, 0, 0], [1, 1, 0], [0, 0, 5]]
# 2x=2 -> x=1 ; x+y=3 -> y=2 ; 5z=15 -> z=3
sol3 = L.resout_systeme(A3, [2, 3, 15])
check(sol3["type"] == "unique" and sol3["solution"] == [F(1), F(2), F(3)], "système 3×3 -> [1,2,3]")

# ── (b) DÉTERMINANT à la main ──
check(L.determinant([[1, 2], [3, 4]]) == F(-2), "(b) det([[1,2],[3,4]]) = -2")
check(L.determinant([[2, 0], [0, 3]]) == F(6), "det diag(2,3) = 6")
check(L.determinant([[1, 2, 3], [0, 1, 4], [0, 0, 1]]) == F(1), "det triangulaire unitaire = 1")
check(L.determinant([[1, 2], [2, 4]]) == F(0), "det matrice singulière = 0")

# ── (c) INVERSE EN DUR + deuxième chemin M·M⁻¹ = I ──
inv = L.inverse([[1, 2], [3, 4]])
attendu = [[F(-2), F(1)], [Fraction(3, 2), Fraction(-1, 2)]]   # inverse écrite EN DUR (à la main)
check(inv == attendu, "(c) inverse([[1,2],[3,4]]) = [[-2,1],[3/2,-1/2]]")
# deuxième chemin : le produit doit rendre l'identité
prod = L.produit([[1, 2], [3, 4]], inv)
check(prod == [[F(1), F(0)], [F(0), F(1)]], "(c) M·M⁻¹ = I (deuxième chemin)")
# inverse de la matrice identité = identité
check(L.inverse([[1, 0], [0, 1]]) == [[F(1), F(0)], [F(0), F(1)]], "inverse(I) = I")

# ── (d) RANG lignes proportionnelles ──
check(L.rang([[1, 2], [2, 4]]) == 1, "(d) rang([[1,2],[2,4]]) = 1")
check(L.rang([[1, 0], [0, 1]]) == 2, "rang(I) = 2")
check(L.rang([[0, 0], [0, 0]]) == 0, "rang(0) = 0")
# rectangulaire : 2×3, deuxième ligne = 2× première -> rang 1
check(L.rang([[1, 2, 3], [2, 4, 6]]) == 1, "rang 2×3 proportionnelles = 1")
check(L.rang([[1, 0, 0], [0, 1, 0]]) == 2, "rang 2×3 échelon = 2")

# ── (e) SYSTÈME INCOMPATIBLE : x+y=1, x+y=2 ──
inc = L.resout_systeme([[1, 1], [1, 1]], [1, 2])
check(inc["type"] == "aucune", "(e) x+y=1,x+y=2 -> aucune")
check(inc["rang"] == 1, "(e) rang(A) = 1 (< rang([A|b])=2)")
# autre incompatible 3×2
inc2 = L.resout_systeme([[1, 0], [0, 1], [1, 1]], [1, 1, 3])
check(inc2["type"] == "aucune", "surdéterminé incompatible -> aucune")

# ── (f) SYSTÈME INDÉTERMINÉ : x+y=1 (1 éq, 2 inc) ──
ind = L.resout_systeme([[1, 1]], [1])
check(ind["type"] == "infinite", "(f) x+y=1 -> infinite")
check(len(ind["base_noyau"]) == 1, "(f) base noyau de dimension 1")
check(ind["rang"] == 1, "(f) rang = 1")
# la solution particulière + le noyau doivent satisfaire A·x = b (vérif indépendante)
xp = ind["solution_particuliere"]
check(xp[0] + xp[1] == F(1), "(f) solution particulière vérifie x+y=1")
v = ind["base_noyau"][0]
check(v[0] + v[1] == F(0), "(f) vecteur noyau vérifie x+y=0")
# x_p + 5·v est encore solution
xg = [xp[0] + 5 * v[0], xp[1] + 5 * v[1]]
check(xg[0] + xg[1] == F(1), "(f) x_p + 5·noyau reste solution")

# système indéterminé 2×3 de rang 2 -> noyau dim 1
ind3 = L.resout_systeme([[1, 0, 1], [0, 1, 1]], [2, 3])
check(ind3["type"] == "infinite" and len(ind3["base_noyau"]) == 1, "2×3 rang 2 -> infinite, noyau dim 1")

# ── (g) MATRICE SINGULIÈRE -> inverse ValueError ──
check(leve(L.inverse, [[1, 2], [2, 4]]), "(g) inverse singulière -> ValueError")
check(L.est_inversible([[1, 2], [3, 4]]) is True, "est_inversible régulière = True")
check(L.est_inversible([[1, 2], [2, 4]]) is False, "est_inversible singulière = False")

# ── (h) BOUCLE FERMÉE : inverse(inverse(M)) == M sur 20 matrices inversibles déterministes ──
def lcg(seed):
    x = seed
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield (x % 11) - 5          # entiers dans [-5, 5]

g = lcg(20260710)
faits = 0
essais = 0
while faits < 20 and essais < 2000:
    essais += 1
    taille = 2 + (essais % 3)       # tailles 2, 3, 4
    M = [[next(g) for _ in range(taille)] for _ in range(taille)]
    if L.determinant(M) == 0:
        continue                    # non inversible : on saute (déterministe)
    Mi = L.inverse(M)
    Mii = L.inverse(Mi)
    # Mi a des entrées Fraction ; inverse d'une matrice à entrées Fraction est licite
    Mfrac = [[Fraction(x) for x in ligne] for ligne in M]
    check(Mii == Mfrac, f"(h) inverse(inverse(M)) == M (essai {essais})")
    faits += 1
check(faits == 20, "(h) 20 matrices inversibles testées")

# ── TRANSPOSÉE / TRACE / PRODUIT (rendus) ──
check(L.transposee([[1, 2, 3], [4, 5, 6]]) == [[F(1), F(4)], [F(2), F(5)], [F(3), F(6)]], "transposée 2×3")
check(L.trace([[1, 2], [3, 4]]) == F(5), "trace([[1,2],[3,4]]) = 5")
# produit à la main : [[1,2],[3,4]]·[[5,6],[7,8]] = [[19,22],[43,50]]
check(L.produit([[1, 2], [3, 4]], [[5, 6], [7, 8]]) == [[F(19), F(22)], [F(43), F(50)]], "produit 2×2 à la main")
# produit rectangulaire 2×3 · 3×2 = 2×2 : [[1,0,2],[0,1,3]]·[[1,0],[0,1],[1,1]] = [[3,2],[3,4]]
check(L.produit([[1, 0, 2], [0, 1, 3]], [[1, 0], [0, 1], [1, 1]]) == [[F(3), F(2)], [F(3), F(4)]],
      "produit 2×3·3×2 à la main")

# ── ENTRÉES FRACTION EXACTES ──
solf = L.resout_systeme([[Fraction(1, 2), 0], [0, Fraction(1, 3)]], [1, 1])
check(solf["type"] == "unique" and solf["solution"] == [F(2), F(3)], "système à coeffs Fraction -> [2,3]")

# ── DÉTERMINISME ──
check(L.resout_systeme([[1, 1], [1, -1]], [3, 1]) == L.resout_systeme([[1, 1], [1, -1]], [3, 1]),
      "déterminisme resout_systeme")
check(L.inverse([[1, 2], [3, 4]]) == L.inverse([[1, 2], [3, 4]]), "déterminisme inverse")
check(L.determinant([[1, 2], [3, 4]]) == L.determinant([[1, 2], [3, 4]]), "déterminisme determinant")

# ── SOUNDNESS : flottant refusé (0.1 n'est pas exact) ──
check(leve(L.determinant, [[1.0, 2.0], [3.0, 4.0]]), "det flottant -> ValueError")
check(leve(L.resout_systeme, [[1.0, 1.0], [1.0, -1.0]], [3, 1]), "système A flottant -> ValueError")
check(leve(L.resout_systeme, [[1, 1], [1, -1]], [3.0, 1.0]), "système b flottant -> ValueError")
check(leve(L.inverse, [[1.5, 2], [3, 4]]), "inverse flottant -> ValueError")
check(leve(L.rang, [[0.1]]), "rang flottant -> ValueError")

# ── SOUNDNESS : bool refusé (True n'est pas 1) ──
check(leve(L.determinant, [[True, False], [False, True]]), "det bool -> ValueError")
check(leve(L.resout_systeme, [[1, 1], [1, -1]], [True, 1]), "b bool -> ValueError")
check(leve(L.rang, [[True]]), "rang bool -> ValueError")

# ── SOUNDNESS : str / complexe / NaN / inf refusés ──
check(leve(L.determinant, [["1", "2"], ["3", "4"]]), "det str -> ValueError")
check(leve(L.determinant, [[1 + 2j, 0], [0, 1]]), "det complexe -> ValueError")
check(leve(L.rang, [[float("nan")]]), "rang NaN -> ValueError")
check(leve(L.rang, [[float("inf")]]), "rang inf -> ValueError")

# ── SOUNDNESS : vide / lignes inégales / dimensions ──
check(leve(L.determinant, []), "matrice vide -> ValueError")
check(leve(L.rang, [[1, 2], [3]]), "lignes inégales -> ValueError")
check(leve(L.rang, [[]]), "ligne vide -> ValueError")
check(leve(L.trace, [[1, 2, 3], [4, 5, 6]]), "trace non carrée -> ValueError")
check(leve(L.determinant, [[1, 2, 3], [4, 5, 6]]), "det non carré -> ValueError")
check(leve(L.inverse, [[1, 2, 3], [4, 5, 6]]), "inverse non carrée -> ValueError")
check(leve(L.resout_systeme, [[1, 1], [1, -1]], [3, 1, 5]), "b trop long -> ValueError")
check(leve(L.resout_systeme, [[1, 1], [1, -1]], [3]), "b trop court -> ValueError")
check(leve(L.produit, [[1, 2], [3, 4]], [[1, 2, 3]]), "produit dims incompatibles -> ValueError")
check(leve(L.resout_systeme, [[1, 1]], []), "b vide -> ValueError")

# ── SOUNDNESS : arité / non-séquence ──
check(leve(L.determinant, 5), "det scalaire -> ValueError")
check(leve(L.resout_systeme, [[1, 1]], 3), "b non-séquence -> ValueError")
check(leve(L.transposee, [[1, 2], [3]]), "transposée lignes inégales -> ValueError")

print(f"\n=== valide_algebre_lineaire : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
