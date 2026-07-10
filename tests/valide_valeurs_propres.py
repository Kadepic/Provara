"""
VALIDE valeurs_propres.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (jamais recalculées par le mécanisme testé) :
  • CAYLEY–HAMILTON : p(A) = 0. Le polynôme est produit par Faddeev–LeVerrier ; on le réinjecte dans
    l'ALGÈBRE MATRICIELLE (chemin de code indépendant) — si le polynôme était faux, p(A) ≠ 0.
  • FORMULE DIRECTE 2×2 : p(λ) = λ² − tr(A)·λ + det(A), calculée à la main depuis les entrées brutes.
  • FORMULE DIRECTE 3×3 : p(λ) = λ³ − tr·λ² + (Σ mineurs principaux 2×2)·λ − det, idem.
  • VALEURS CONNUES INDÉPENDAMMENT : nombre d'or φ = (1+√5)/2 (matrice de Fibonacci) et ∛2 (matrice
    compagnon de x³−2) — calculés par `math.sqrt` / `**(1/3)`, PAS par le module. On exige que
    l'INTERVALLE RATIONNEL PROUVÉ les CONTIENNE (c'est la garantie d'encadrement, plus forte qu'une égalité
    flottante).
  • RELATIONS DE VIÈTE : Σλ = trace, Πλ = déterminant (spectres entièrement rationnels).
  • VECTEUR PROPRE : on vérifie A·v = λ·v EXACTEMENT en Fraction (produit matrice-vecteur indépendant).
  • BLOC DE JORDAN : [[2,1],[0,2]] a multiplicité algébrique 2 mais géométrique 1 (fait classique).

SOUNDNESS : matrice non carrée / vide / entrées flottantes (0.1 non exact) / bool / str / complexe /
n > 12 / tol ≤ 0 / λ non valeur propre / λ irrationnel pour vecteur_propre -> ValueError.
"""
import math
import sys
from fractions import Fraction as F

import valeurs_propres as VP

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve(fn, *a, **k):
    try:
        fn(*a, **k)
        return False
    except (ValueError, TypeError):
        return True


def _est_nulle(M):
    return all(x == 0 for ligne in M for x in ligne)


def _mat_vec(M, v):
    """Produit matrice-vecteur EXACT — chemin indépendant du module."""
    return [sum((F(M[i][j]) * v[j] for j in range(len(v))), F(0)) for i in range(len(M))]


# ── 1) ANCRE : CAYLEY–HAMILTON p(A) = 0 sur un échantillon varié ──
MATRICES = [
    [[1, 2], [3, 4]],
    [[2, 1], [1, 2]],
    [[0, -1], [1, 0]],
    [[2, 1], [0, 2]],
    [[1, 1], [1, 0]],
    [[1, 0, 0], [0, 2, 0], [0, 0, 3]],
    [[0, 0, 2], [1, 0, 0], [0, 1, 0]],
    [[2, -1, 0], [-1, 2, -1], [0, -1, 2]],
    [[5]],
    [[F(1, 2), F(1, 3)], [F(1, 4), F(1, 5)]],
]
for M in MATRICES:
    p = VP.polynome_caracteristique(M)
    check(_est_nulle(VP.evalue_polynome_en_matrice(M, p)), f"Cayley–Hamilton p(A)=0 pour {M}")

# ── 2) ANCRE : formule directe 2×2  p(λ) = λ² − tr·λ + det ──
for M in ([[1, 2], [3, 4]], [[2, 1], [1, 2]], [[0, -1], [1, 0]], [[F(1, 2), F(1, 3)], [F(1, 4), F(1, 5)]]):
    tr = F(M[0][0]) + F(M[1][1])
    dt = F(M[0][0]) * F(M[1][1]) - F(M[0][1]) * F(M[1][0])
    check(VP.polynome_caracteristique(M) == (F(1), -tr, dt), f"carac 2×2 = λ²−tr·λ+det pour {M}")
    check(VP.determinant(M) == dt, f"déterminant 2×2 exact pour {M}")

# ── 3) ANCRE : formule directe 3×3  p(λ) = λ³ − tr·λ² + M2·λ − det ──
for M in ([[1, 0, 0], [0, 2, 0], [0, 0, 3]], [[0, 0, 2], [1, 0, 0], [0, 1, 0]], [[2, -1, 0], [-1, 2, -1], [0, -1, 2]]):
    a = [[F(x) for x in ligne] for ligne in M]
    tr = a[0][0] + a[1][1] + a[2][2]
    m2 = ((a[0][0] * a[1][1] - a[0][1] * a[1][0])
          + (a[0][0] * a[2][2] - a[0][2] * a[2][0])
          + (a[1][1] * a[2][2] - a[1][2] * a[2][1]))
    dt = (a[0][0] * (a[1][1] * a[2][2] - a[1][2] * a[2][1])
          - a[0][1] * (a[1][0] * a[2][2] - a[1][2] * a[2][0])
          + a[0][2] * (a[1][0] * a[2][1] - a[1][1] * a[2][0]))
    check(VP.polynome_caracteristique(M) == (F(1), -tr, m2, -dt), f"carac 3×3 direct pour {M}")
    check(VP.determinant(M) == dt, f"déterminant 3×3 exact pour {M}")

# ── 4) SPECTRES RATIONNELS EXACTS ──
r = VP.valeurs_propres([[1, 0, 0], [0, 2, 0], [0, 0, 3]])
check(r["rationnelles"] == [(F(1), 1), (F(2), 1), (F(3), 1)], "diag(1,2,3) -> λ = 1,2,3 exacts")
check(r["nb_complexes_non_reelles"] == 0 and not r["reelles_irrationnelles"], "diag(1,2,3) : aucun irrationnel/complexe")

r = VP.valeurs_propres([[2, 1], [1, 2]])
check(r["rationnelles"] == [(F(1), 1), (F(3), 1)], "[[2,1],[1,2]] -> λ = 1 et 3 exacts")

# ── 5) ANCRE VIÈTE : Σλ = trace, Πλ = déterminant (spectre entièrement rationnel) ──
for M in ([[1, 0, 0], [0, 2, 0], [0, 0, 3]], [[2, 1], [1, 2]], [[2, 1], [0, 2]], [[2, -1, 0], [-1, 2, -1], [0, -1, 2]]):
    r = VP.valeurs_propres(M)
    if r["nb_complexes_non_reelles"] == 0 and not r["reelles_irrationnelles"]:
        somme = sum((lam * m for lam, m in r["rationnelles"]), F(0))
        produit = F(1)
        for lam, m in r["rationnelles"]:
            produit *= lam ** m
        check(somme == r["trace"], f"Viète Σλ = trace pour {M}")
        check(produit == r["determinant"], f"Viète Πλ = det pour {M}")

# ── 6) ANCRE EXTERNE : nombre d'or φ encadré par l'intervalle PROUVÉ (Fibonacci) ──
phi = (1.0 + math.sqrt(5.0)) / 2.0                       # calculé HORS du module
psi = (1.0 - math.sqrt(5.0)) / 2.0
r = VP.valeurs_propres([[1, 1], [1, 0]])
check(not r["rationnelles"], "Fibonacci : aucune valeur propre rationnelle (φ est irrationnel)")
check(len(r["reelles_irrationnelles"]) == 2, "Fibonacci : 2 valeurs propres réelles irrationnelles")
check(r["nb_complexes_non_reelles"] == 0, "Fibonacci : aucune complexe")
bornes = [d["intervalle"] for d in r["reelles_irrationnelles"]]
check(any(float(lo) <= phi <= float(hi) for lo, hi in bornes), "φ = (1+√5)/2 est DANS un intervalle prouvé")
check(any(float(lo) <= psi <= float(hi) for lo, hi in bornes), "ψ = (1−√5)/2 est DANS un intervalle prouvé")
check(all(float(hi) - float(lo) <= 1e-11 for lo, hi in bornes), "Fibonacci : largeur des intervalles ≤ tol")

# ── 7) ANCRE EXTERNE : ∛2 encadré (matrice compagnon de x³ − 2), 2 racines complexes ──
cbrt2 = 2.0 ** (1.0 / 3.0)                               # calculé HORS du module
r = VP.valeurs_propres([[0, 0, 2], [1, 0, 0], [0, 1, 0]])
check(r["polynome_caracteristique"] == (F(1), F(0), F(0), F(-2)), "compagnon x³−2 : p = λ³ − 2")
check(len(r["reelles_irrationnelles"]) == 1, "x³−2 : exactement 1 racine réelle")
check(r["nb_complexes_non_reelles"] == 2, "x³−2 : exactement 2 racines non réelles")
lo, hi = r["reelles_irrationnelles"][0]["intervalle"]
check(float(lo) <= cbrt2 <= float(hi), "∛2 est DANS l'intervalle prouvé")

# ── 8) BLOC DE JORDAN : multiplicité algébrique ≠ géométrique (jamais masqué) ──
check(VP.multiplicite_algebrique([[2, 1], [0, 2]], 2) == 2, "Jordan : multiplicité algébrique = 2")
check(VP.multiplicite_geometrique([[2, 1], [0, 2]], 2) == 1, "Jordan : multiplicité géométrique = 1")
check(VP.multiplicite_algebrique([[2, 0], [0, 2]], 2) == 2, "2·I : multiplicité algébrique = 2")
check(VP.multiplicite_geometrique([[2, 0], [0, 2]], 2) == 2, "2·I : multiplicité géométrique = 2")
check(VP.valeurs_propres([[2, 1], [0, 2]])["rationnelles"] == [(F(2), 2)], "Jordan : λ=2 de multiplicité 2")

# ── 9) MATRICE SANS VALEUR PROPRE RÉELLE (rotation de 90°) ──
r = VP.valeurs_propres([[0, -1], [1, 0]])
check(r["rationnelles"] == [] and r["reelles_irrationnelles"] == [], "rotation 90° : aucune valeur propre réelle")
check(r["nb_complexes_non_reelles"] == 2, "rotation 90° : 2 valeurs propres complexes (±i), comptées non énumérées")

# ── 10) VECTEUR PROPRE : A·v = λ·v vérifié EXACTEMENT (chemin indépendant) ──
for M, lam in ([[2, 1], [1, 2]], 3), ([[2, 1], [1, 2]], 1), ([[1, 0, 0], [0, 2, 0], [0, 0, 3]], 2), ([[2, 1], [0, 2]], 2):
    base = VP.vecteur_propre(M, lam)
    check(len(base) >= 1, f"vecteur propre non vide (M={M}, λ={lam})")
    for v in base:
        Av = _mat_vec(M, v)
        lv = [F(lam) * x for x in v]
        check(Av == lv, f"A·v = λ·v exact (M={M}, λ={lam}, v={v})")
        check(any(x != 0 for x in v), "vecteur propre non nul")

check(VP.est_valeur_propre([[2, 1], [1, 2]], 3) is True, "3 est valeur propre de [[2,1],[1,2]]")
check(VP.est_valeur_propre([[2, 1], [1, 2]], 2) is False, "2 n'est pas valeur propre de [[2,1],[1,2]]")
check(VP.multiplicite_algebrique([[2, 1], [1, 2]], 2) == 0, "multiplicité de non-valeur-propre = 0")
check(VP.multiplicite_geometrique([[2, 1], [1, 2]], 2) == 0, "multiplicité géométrique de non-valeur-propre = 0")

# ── 11) ENTRÉES RATIONNELLES NON ENTIÈRES (exactitude préservée) ──
r = VP.valeurs_propres([[F(1, 2), F(0)], [F(0), F(1, 3)]])
check(r["rationnelles"] == [(F(1, 3), 1), (F(1, 2), 1)], "diag(1/2, 1/3) -> λ exacts en Fraction")
check(r["trace"] == F(5, 6), "trace exacte = 5/6 (aucun flottant)")

# ── 12) INVARIANT : Σ multiplicités = n, sur tout l'échantillon ──
for M in MATRICES:
    r = VP.valeurs_propres(M)
    n = len(M)
    s = (sum(m for _, m in r["rationnelles"])
         + sum(d["multiplicite"] for d in r["reelles_irrationnelles"])
         + r["nb_complexes_non_reelles"])
    check(s == n, f"Σ multiplicités = n = {n} pour {M}")

# ── 13) SOUNDNESS — structure de la matrice ──
check(leve(VP.valeurs_propres, [[1, 2], [3]]), "lignes de longueurs inégales -> ValueError")
check(leve(VP.valeurs_propres, [[1, 2, 3], [4, 5, 6]]), "matrice non carrée -> ValueError")
check(leve(VP.valeurs_propres, []), "matrice vide -> ValueError")
check(leve(VP.valeurs_propres, [[1, 2]]), "1 ligne, 2 colonnes -> ValueError")
check(leve(VP.valeurs_propres, "abc"), "non-séquence -> ValueError")
check(leve(VP.valeurs_propres, [[[1]]]), "entrée non scalaire -> ValueError")

# ── 14) SOUNDNESS — types d'entrées (le flottant est REFUSÉ : 0.1 n'est pas exact) ──
check(leve(VP.valeurs_propres, [[1.0, 2.0], [3.0, 4.0]]), "entrées flottantes -> ValueError (exactitude)")
check(leve(VP.valeurs_propres, [[0.1, 0], [0, 1]]), "0.1 -> ValueError (pas un rationnel exact)")
check(leve(VP.valeurs_propres, [[True, 0], [0, 1]]), "bool -> ValueError")
check(leve(VP.valeurs_propres, [["1", 0], [0, 1]]), "str -> ValueError")
check(leve(VP.valeurs_propres, [[1j, 0], [0, 1]]), "complexe -> ValueError")
check(leve(VP.valeurs_propres, [[float("nan"), 0], [0, 1]]), "NaN -> ValueError")
check(leve(VP.valeurs_propres, [[float("inf"), 0], [0, 1]]), "inf -> ValueError")

# ── 15) SOUNDNESS — taille maximale (budget d'exactitude honnête, DIT) ──
grande = [[1 if i == j else 0 for j in range(13)] for i in range(13)]
check(leve(VP.valeurs_propres, grande), "n = 13 > 12 -> ValueError (budget d'exactitude dit)")

# ── 16) SOUNDNESS — tolérance ──
check(leve(VP.valeurs_propres, [[1, 1], [1, 0]], F(0)), "tol = 0 -> ValueError")
check(leve(VP.valeurs_propres, [[1, 1], [1, 0]], F(-1, 10)), "tol < 0 -> ValueError")
check(leve(VP.valeurs_propres, [[1, 1], [1, 0]], 0.001), "tol flottante -> ValueError (exactitude)")

# ── 17) SOUNDNESS — λ hors spectre / λ irrationnel ──
check(leve(VP.vecteur_propre, [[2, 1], [1, 2]], 7), "vecteur_propre d'un λ non valeur propre -> ValueError")
check(leve(VP.vecteur_propre, [[1, 1], [1, 0]], 1.618), "vecteur_propre d'un λ flottant/irrationnel -> ValueError")
check(leve(VP.est_valeur_propre, [[2, 1], [1, 2]], 1.5), "est_valeur_propre λ flottant -> ValueError")

# ── 18) DÉTERMINISME ──
check(VP.polynome_caracteristique([[1, 2], [3, 4]]) == VP.polynome_caracteristique([[1, 2], [3, 4]]),
      "déterminisme du polynôme caractéristique")
a = VP.valeurs_propres([[1, 1], [1, 0]])
b = VP.valeurs_propres([[1, 1], [1, 0]])
check(a["reelles_irrationnelles"] == b["reelles_irrationnelles"], "déterminisme des intervalles d'isolation")
check(VP.valeurs_propres([[2, 1], [1, 2]]) == VP.valeurs_propres([[2, 1], [1, 2]]), "déterminisme du spectre complet")

# ── 19) TOLÉRANCE PLUS FINE : l'intervalle se resserre et contient TOUJOURS φ ──
r = VP.valeurs_propres([[1, 1], [1, 0]], F(1, 10 ** 20))
bornes = [d["intervalle"] for d in r["reelles_irrationnelles"]]
check(any(float(lo) <= phi <= float(hi) for lo, hi in bornes), "φ encadré aussi à tol = 1e-20")
check(all(hi - lo <= F(1, 10 ** 20) for lo, hi in bornes), "largeur ≤ 1e-20 (encadrement exact en Fraction)")

# ── 20) RANG / NOYAU exacts ──
check(VP.rang([[1, 2], [2, 4]]) == 1, "rang([[1,2],[2,4]]) = 1")
check(VP.rang([[1, 0], [0, 1]]) == 2, "rang(I₂) = 2")
check(VP.noyau([[1, 0], [0, 1]]) == [], "noyau(I₂) trivial")
check(len(VP.noyau([[1, 2], [2, 4]])) == 1, "noyau([[1,2],[2,4]]) de dimension 1")

# ── 21) EXACTITUDE RATIONNELLE SIGNALÉE ──
check(VP.valeurs_propres([[2, 1], [1, 2]])["exactitude_rationnelle_complete"] is True,
      "exactitude rationnelle complète signalée (petits coefficients)")

print(f"\n=== valide_valeurs_propres : {ok}/{ok+ko} ===")
sys.exit(0 if ko == 0 else 1)
