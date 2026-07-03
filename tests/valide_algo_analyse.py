"""VALIDE algo_analyse.py — held-out ADVERSE, FAUX=0. Ancres = ordre asymptotique de référence,
classes de complexité des tris (CLRS), compte exact n(n-1)/2, correction par invariant + SOUNDNESS :
entrée invalide / hors-catalogue -> ValueError (jamais une réponse inventée) + déterminisme.
"""
import algo_analyse as M

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


# ── COMPLEXITÉ DE BOUCLE — n^profondeur (fait exact) ──
check(M.complexite_boucle(0) == "1", "0 boucle -> '1'")
check(M.complexite_boucle(1) == "n", "1 boucle -> 'n'")
check(M.complexite_boucle(2) == "n^2", "2 boucles imbriquées -> 'n^2'")
check(M.complexite_boucle(3) == "n^3", "3 boucles -> 'n^3'")
check(M.complexite_boucle(5) == "n^5", "5 boucles -> 'n^5'")

# ── ORDRE ASYMPTOTIQUE — 1 < log n < n < n log n < n² < n³ < 2^n < n! ──
check(M.compare_asymptotique("1", "log n") == "log n", "1 < log n")
check(M.compare_asymptotique("log n", "n") == "n", "log n < n")
check(M.compare_asymptotique("n", "n log n") == "n log n", "n < n log n")
check(M.compare_asymptotique("n log n", "n^2") == "n^2", "n log n < n²")
check(M.compare_asymptotique("n^2", "n^3") == "n^3", "n² < n³")
check(M.compare_asymptotique("n^3", "2^n") == "2^n", "n³ < 2^n")
check(M.compare_asymptotique("2^n", "n!") == "n!", "2^n < n!")
check(M.compare_asymptotique("n", "n^2") == "n^2", "n < n² (saut)")
check(M.compare_asymptotique("1", "n!") == "n!", "1 < n! (extrêmes)")
check(M.compare_asymptotique("n", "n") == "n", "égalité -> renvoie la classe")
# symétrie de la domination
check(M.compare_asymptotique("n^2", "n") == M.compare_asymptotique("n", "n^2"), "domination symétrique")

# ── CLASSES DE TRI — catalogue établi (CLRS) ──
check(M.nombre_operations_tri(8, "bulle") == "n^2", "bulle pire cas = n²")
check(M.nombre_operations_tri(8, "insertion") == "n^2", "insertion pire cas = n²")
check(M.nombre_operations_tri(8, "insertion", "meilleur") == "n", "insertion meilleur cas (déjà trié) = n")
check(M.nombre_operations_tri(8, "selection", "meilleur") == "n^2", "selection toujours n²")
check(M.nombre_operations_tri(8, "fusion") == "n log n", "fusion = n log n")
check(M.nombre_operations_tri(8, "tas") == "n log n", "tas = n log n")
check(M.nombre_operations_tri(8, "rapide", "pire") == "n^2", "rapide pire cas = n²")
check(M.nombre_operations_tri(8, "rapide", "moyen") == "n log n", "rapide cas moyen = n log n")

# ── « fusion MEILLEUR que bulle » : la classe de bulle DOMINE (croît plus vite) ──
cb = M.nombre_operations_tri(8, "bulle")
cf = M.nombre_operations_tri(8, "fusion")
check(M.compare_asymptotique(cf, cb) == cb == "n^2", "fusion (n log n) meilleur que bulle (n²) : bulle domine")

# ── COMPTE EXACT de comparaisons — n(n-1)/2 (tris quadratiques) ──
check(M.comparaisons_pire_cas(5, "bulle") == 10, "bulle n=5 : 5·4/2 = 10")
check(M.comparaisons_pire_cas(5, "insertion") == 10, "insertion n=5 : 10")
check(M.comparaisons_pire_cas(5, "selection") == 10, "selection n=5 : 10")
check(M.comparaisons_pire_cas(1, "bulle") == 0, "n=1 : 0 comparaison")
check(M.comparaisons_pire_cas(10, "selection") == 45, "selection n=10 : 45")

# ── CORRECTION par invariant — somme 0..n = n(n+1)/2 ──
check(M.invariant_boucle_somme(0) is True, "somme 0..0 = 0 (correct)")
check(M.invariant_boucle_somme(10) is True, "somme 0..10 = 55 (correct)")
check(M.invariant_boucle_somme(100) is True, "somme 0..100 = 5050 (Gauss, correct)")
check(M.invariant_boucle_somme(1000) is True, "somme 0..1000 = 500500 (correct)")

# ── SOUNDNESS — entrée invalide / hors-catalogue -> ValueError (jamais faux) ──
check(leve(M.complexite_boucle, -1), "profondeur négative -> ValueError")
check(leve(M.complexite_boucle, 1.5), "profondeur non entière -> ValueError")
check(leve(M.complexite_boucle, True), "profondeur booléenne -> ValueError")
check(leve(M.compare_asymptotique, "n", "n^4"), "classe n^4 hors set -> ValueError")
check(leve(M.compare_asymptotique, "foo", "n"), "classe inventée -> ValueError")
check(leve(M.compare_asymptotique, "N", "n"), "casse différente -> ValueError")
check(leve(M.nombre_operations_tri, 8, "inconnu"), "algo de tri inconnu -> ValueError")
check(leve(M.nombre_operations_tri, 8, "bulle", "meilleur"), "(bulle, meilleur) non établi -> ValueError")
check(leve(M.nombre_operations_tri, 8, "tas", "meilleur"), "(tas, meilleur) non établi -> ValueError")
check(leve(M.nombre_operations_tri, 0, "bulle"), "n=0 invalide -> ValueError")
check(leve(M.nombre_operations_tri, -5, "fusion"), "n négatif -> ValueError")
check(leve(M.comparaisons_pire_cas, 5, "fusion"), "compte exact fusion non établi -> ValueError")
check(leve(M.comparaisons_pire_cas, 5, "rapide"), "compte exact rapide non établi -> ValueError")
check(leve(M.comparaisons_pire_cas, 0, "bulle"), "n=0 invalide -> ValueError")
check(leve(M.comparaisons_pire_cas, 5, "xyz"), "algo inconnu -> ValueError")
check(leve(M.invariant_boucle_somme, -1), "n négatif -> ValueError")
check(leve(M.invariant_boucle_somme, 2.5), "n non entier -> ValueError")

# ── DÉTERMINISME ──
check(M.nombre_operations_tri(8, "rapide", "moyen") == M.nombre_operations_tri(8, "rapide", "moyen"),
      "déterminisme nombre_operations_tri")
check(M.compare_asymptotique("n", "n^2") == M.compare_asymptotique("n", "n^2"), "déterminisme compare")
check(M.comparaisons_pire_cas(7, "bulle") == M.comparaisons_pire_cas(7, "bulle"), "déterminisme compte exact")

print(f"\n=== valide_algo_analyse : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
