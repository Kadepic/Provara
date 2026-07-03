"""
VALIDE analyse_fonctionnelle.py — held-out ADVERSE. Les ancres sont des valeurs GÉOMÉTRIQUES CONNUES,
PAS recalculées par la même expression : triplets pythagoriciens (3-4-5, 5-12-13, 8-15-17),
norme ℓ¹ = somme des |coords|, ℓ^∞ = max, produits scalaires entiers, orthogonalité, cas d'égalité de
Cauchy-Schwarz (vecteurs colinéaires), projection sur un axe. + SOUNDNESS : dimensions incompatibles,
projection sur le vecteur nul, p < 1, vecteur vide, booléen, non-vecteur -> HORS (ValueError, jamais un faux).
Déterminisme (mêmes entrées -> mêmes sorties).
"""
import analyse_fonctionnelle as A

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def approx(x, attendu, tol=1e-9):
    return isinstance(x, float) and abs(x - attendu) <= tol


def leve(fn, *a, **k):
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) NORMES — ancres = triplets pythagoriciens & sommes connues ──
check(approx(A.norme([3, 4]), 5.0), "||(3,4)||₂ = 5 (3-4-5)")
check(approx(A.norme([5, 12]), 13.0), "||(5,12)||₂ = 13 (5-12-13)")
check(approx(A.norme([8, 15]), 17.0), "||(8,15)||₂ = 17 (8-15-17)")
check(approx(A.norme([3, 4], 2), 5.0), "||(3,4)||₂ explicite = 5")
check(approx(A.norme([1, -2, 2], 1), 5.0), "||(1,-2,2)||₁ = 1+2+2 = 5")
check(approx(A.norme([1, -2, 2], 2), 3.0), "||(1,-2,2)||₂ = √9 = 3")
check(approx(A.norme([1, -2, 2], "inf"), 2.0), "||(1,-2,2)||∞ = max = 2")
check(approx(A.norme([-7, 0, 0], 1), 7.0), "||(-7,0,0)||₁ = 7")
check(approx(A.norme([0, 0, 0]), 0.0), "||0||₂ = 0")
check(approx(A.norme([1, 1, 1, 1], 1), 4.0), "||(1,1,1,1)||₁ = 4")
check(approx(A.norme([3, 4], 1), 7.0), "||(3,4)||₁ = 7 (≠ ||·||₂)")
check(approx(A.norme([-5, 3, -5], "inf"), 5.0), "||(-5,3,-5)||∞ = 5")

# ── 2) PRODUIT SCALAIRE — ancres entières ──
check(approx(A.produit_scalaire([1, 2], [3, 4]), 11.0), "⟨(1,2),(3,4)⟩ = 3+8 = 11")
check(approx(A.produit_scalaire([1, 2, 3], [4, 5, 6]), 32.0), "⟨(1,2,3),(4,5,6)⟩ = 4+10+18 = 32")
check(approx(A.produit_scalaire([2, -1], [3, 6]), 0.0), "⟨(2,-1),(3,6)⟩ = 6-6 = 0")
check(approx(A.produit_scalaire([5], [-3]), -15.0), "⟨(5),(-3)⟩ = -15")

# ── 3) DISTANCE — ancres pythagoriciennes ──
check(approx(A.distance([1, 1], [4, 5]), 5.0), "d((1,1),(4,5)) = √(9+16) = 5")
check(approx(A.distance([0, 0], [3, 4]), 5.0), "d((0,0),(3,4)) = 5")
check(approx(A.distance([2, 7], [2, 7]), 0.0), "d(x,x) = 0")
check(approx(A.distance([1, 2, 3], [0, 0, 0], 1), 6.0), "d₁((1,2,3),0) = 6")

# ── 4) ORTHOGONALITÉ ──
check(A.sont_orthogonaux([1, 0], [0, 1]) is True, "(1,0) ⊥ (0,1)")
check(A.sont_orthogonaux([1, 1], [1, -1]) is True, "(1,1) ⊥ (1,-1)")
check(A.sont_orthogonaux([2, -1, 0], [1, 2, 9]) is True, "(2,-1,0) ⊥ (1,2,9)")
check(A.sont_orthogonaux([1, 2], [3, 4]) is False, "(1,2) ⊄ (3,4)")

# ── 5) CAUCHY-SCHWARZ — vrai partout, ÉGALITÉ sur colinéaires ──
check(A.cauchy_schwarz_verifiee([1, 2], [3, 4]) is True, "|⟨u,v⟩| ≤ ||u||·||v|| (1,2),(3,4)")
check(A.cauchy_schwarz_verifiee([1, 2], [2, 4]) is True, "égalité C-S sur colinéaires (1,2),(2,4)")
check(A.cauchy_schwarz_verifiee([0, 0], [3, 4]) is True, "C-S avec vecteur nul")
check(A.cauchy_schwarz_verifiee([3, 1, -2], [-1, 4, 7]) is True, "C-S cas générique")

# ── 6) PROJECTION orthogonale ──
check(A.projection([2, 2], [1, 0]) == [2.0, 0.0], "proj (2,2)/(1,0) = (2,0)")
check(A.projection([3, 4], [1, 0]) == [3.0, 0.0], "proj (3,4)/(1,0) = (3,0)")
check(A.projection([3, 4], [0, 1]) == [0.0, 4.0], "proj (3,4)/(0,1) = (0,4)")
check(A.projection([1, 1], [1, 1]) == [1.0, 1.0], "proj de v sur v = v")
check(A.projection([2, 4], [1, 2]) == [2.0, 4.0], "proj (2,4)/(1,2) = (2,4) colinéaire")
check(A.projection([5, 0], [0, 7]) == [0.0, 0.0], "proj sur orthogonal = 0")

# ── 7) SOUNDNESS — entrées invalides -> ValueError (jamais un faux) ──
check(leve(A.produit_scalaire, [1, 2], [1, 2, 3]), "dims incompatibles ⟨·,·⟩ -> HORS")
check(leve(A.distance, [1, 2], [1]), "dims incompatibles distance -> HORS")
check(leve(A.projection, [1, 2], [1, 2, 3]), "dims incompatibles projection -> HORS")
check(leve(A.projection, [1, 2], [0, 0]), "projection sur le vecteur nul -> HORS")
check(leve(A.norme, [1, 2], 0.5), "p = 0.5 < 1 -> HORS")
check(leve(A.norme, [1, 2], 0), "p = 0 -> HORS")
check(leve(A.norme, [1, 2], -2), "p = -2 -> HORS")
check(leve(A.norme, []), "vecteur vide -> HORS")
check(leve(A.norme, [1, True]), "booléen dans le vecteur -> HORS")
check(leve(A.norme, "ab"), "non-vecteur (str) -> HORS")
check(leve(A.produit_scalaire, [1, 2], 5), "scalaire au lieu d'un vecteur -> HORS")
check(leve(A.norme, [1, 2], "p2"), "p chaîne invalide -> HORS")

# ── 8) DÉTERMINISME ──
check(A.norme([3, 4]) == A.norme([3, 4]), "norme déterministe")
check(A.projection([2, 2], [1, 0]) == A.projection([2, 2], [1, 0]), "projection déterministe")
check(A.produit_scalaire([1, 2, 3], [4, 5, 6]) == A.produit_scalaire([1, 2, 3], [4, 5, 6]), "⟨·,·⟩ déterministe")

print(f'\n=== valide_analyse_fonctionnelle : {ok}/{ok+ko} ===')
import sys
sys.exit(0 if ko == 0 else 1)
