"""
VALIDE transport_membranaire.py — held-out ADVERSE.

Ancres CONNUES (non circulaires, valeurs/règles de référence en biologie cellulaire) :
  • tonicité décrit la solution EXTERNE : ext<int -> hypotonique (l'eau ENTRE, gonflement) ;
    ext>int -> hypertonique (l'eau SORT, plasmolyse) ; égal -> isotonique.
  • CAS sérum physiologique : 0.9 % vs 0.9 % -> isotonique.
  • osmose : l'eau va vers le plus concentré -> milieu hypertonique -> 'sortie' ; cohérence tonicité/osmose.
  • loi de Fick J = D·A·Δc/e : valeurs entières à la main (2·3·4/6 = 4) + cas physique SI (1e-7 mol/s)
    + linéarité (Δc ×2 -> J ×2) + Δc=0 -> J=0.
SOUNDNESS : concentration<0, aire≤0, épaisseur≤0, D≤0, Δc<0, entrée non numérique/booléenne -> ValueError.
DÉTERMINISME : mêmes entrées -> mêmes sorties.
"""

import transport_membranaire as M

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def approx(a, b, tol=1e-12):
    return abs(a - b) <= tol


def _leve_v(fn, *a, **k):
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) TONICITÉ — règles canoniques + CAS sérum physiologique ──
check(M.tonicite(0.9, 0.9) == "isotonique", "0.9% vs 0.9% -> isotonique (sérum physiologique)")
check(M.tonicite(0.9, 0.45) == "hypotonique", "ext(0.45) < int(0.9) -> hypotonique (l'eau entre, gonfle)")
check(M.tonicite(0.9, 1.8) == "hypertonique", "ext(1.8) > int(0.9) -> hypertonique (sortie, plasmolyse)")
# Eau distillée (ext=0) très hypotonique ; bain saturé (ext grand) hypertonique.
check(M.tonicite(0.9, 0.0) == "hypotonique", "ext=0 (eau pure) -> hypotonique")
check(M.tonicite(0.0, 0.0) == "isotonique", "0 vs 0 -> isotonique")
check(M.tonicite(5, 5) == "isotonique", "égalité entière -> isotonique")

# ── 2) SENS DE L'OSMOSE — l'eau migre vers le plus concentré ──
check(M.sens_osmose(0.9, 1.8) == "sortie", "ext plus concentré -> eau SORT (vers hypertonique)")
check(M.sens_osmose(0.9, 0.45) == "entree", "int plus concentré -> eau ENTRE")
check(M.sens_osmose(0.9, 0.9) == "equilibre", "égal -> equilibre")
check(M.sens_osmose(0.0, 0.0) == "equilibre", "0 vs 0 -> equilibre")

# Cohérence croisée tonicité <-> sens d'osmose (sur grille de cas).
for ci in (0.0, 0.3, 0.9, 2.0):
    for ce in (0.0, 0.3, 0.9, 2.0):
        t = M.tonicite(ci, ce)
        s = M.sens_osmose(ci, ce)
        coherent = ((t == "hypertonique" and s == "sortie")
                    or (t == "hypotonique" and s == "entree")
                    or (t == "isotonique" and s == "equilibre"))
        check(coherent, f"cohérence tonicité/osmose ci={ci} ce={ce} ({t}/{s})")

# ── 3) LOI DE FICK — ancres calculées à la main ──
# 2·3·4/6 = 24/6 = 4.0
check(M.flux_fick(2, 3, 4, 6) == 4.0, "Fick entier 2·3·4/6 = 4.0")
# 1·1·1/1 = 1.0
check(M.flux_fick(1, 1, 1, 1) == 1.0, "Fick unité = 1.0")
# Cas physique SI : D=1e-9, A=1e-4, Δc=10, e=1e-5 -> 1e-9·1e-4·10/1e-5 = 1e-7
check(approx(M.flux_fick(1e-9, 1e-4, 10, 1e-5), 1e-7, 1e-13), "Fick SI -> 1e-7 mol/s")
# Linéarité en Δc : doubler Δc double J.
check(approx(M.flux_fick(2, 3, 8, 6), 8.0), "Fick linéaire en Δc (×2 -> 8.0)")
# Linéarité en A et 1/e : 2·6·4/6 = 8 ; 2·3·4/3 = 8.
check(approx(M.flux_fick(2, 6, 4, 6), 8.0), "Fick linéaire en aire")
check(approx(M.flux_fick(2, 3, 4, 3), 8.0), "Fick inversement proportionnel à e")
# Gradient nul -> flux nul.
check(M.flux_fick(2, 3, 0, 6) == 0.0, "Δc=0 -> J=0")
# Arrondi à 6 chiffres significatifs (valeur non triviale, vérifiée à la main).
# 3·7·11/13 = 231/13 = 17.769230769... -> 17.7692
check(approx(M.flux_fick(3, 7, 11, 13), 17.7692, 1e-4), "Fick arrondi 6 sig (231/13 ≈ 17.7692)")

# ── 4) DÉTERMINISME ──
check(M.flux_fick(2, 3, 4, 6) == M.flux_fick(2, 3, 4, 6), "Fick déterministe")
check(M.tonicite(0.9, 1.8) == M.tonicite(0.9, 1.8), "tonicité déterministe")
check(M.sens_osmose(0.9, 1.8) == M.sens_osmose(0.9, 1.8), "osmose déterministe")

# ── 5) SOUNDNESS — domaines invalides -> ValueError (abstention, jamais un faux) ──
check(_leve_v(M.tonicite, -1, 0.9), "tonicité c_int<0 -> ValueError")
check(_leve_v(M.tonicite, 0.9, -1), "tonicité c_ext<0 -> ValueError")
check(_leve_v(M.sens_osmose, -0.1, 0.9), "osmose c_int<0 -> ValueError")
check(_leve_v(M.sens_osmose, 0.9, -0.1), "osmose c_ext<0 -> ValueError")
check(_leve_v(M.flux_fick, 1e-9, 1e-4, 10, 0), "Fick épaisseur=0 -> ValueError")
check(_leve_v(M.flux_fick, 1e-9, 1e-4, 10, -1), "Fick épaisseur<0 -> ValueError")
check(_leve_v(M.flux_fick, 1e-9, 0, 10, 1e-5), "Fick aire=0 -> ValueError")
check(_leve_v(M.flux_fick, 1e-9, -1, 10, 1e-5), "Fick aire<0 -> ValueError")
check(_leve_v(M.flux_fick, 0, 1e-4, 10, 1e-5), "Fick D=0 -> ValueError")
check(_leve_v(M.flux_fick, -1, 1e-4, 10, 1e-5), "Fick D<0 -> ValueError")
check(_leve_v(M.flux_fick, 1e-9, 1e-4, -10, 1e-5), "Fick Δc<0 -> ValueError")

# ── 6) SOUNDNESS — entrées non numériques / booléennes -> ValueError ──
check(_leve_v(M.tonicite, "0.9", 0.9), "tonicité str -> ValueError")
check(_leve_v(M.tonicite, None, 0.9), "tonicité None -> ValueError")
check(_leve_v(M.tonicite, True, 0.9), "tonicité bool -> ValueError")
check(_leve_v(M.sens_osmose, 0.9, "x"), "osmose str -> ValueError")
check(_leve_v(M.flux_fick, True, 1e-4, 10, 1e-5), "Fick bool -> ValueError")
check(_leve_v(M.flux_fick, 1e-9, 1e-4, None, 1e-5), "Fick None -> ValueError")

print(f"\n=== valide_transport_membranaire : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
