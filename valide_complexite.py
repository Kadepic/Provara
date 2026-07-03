"""VALIDE complexite.py — held-out ADVERSE, FAUX=0. Ancres EXTERNES connues (théorème maître CLRS :
mergesort/recherche dichotomique/Karatsuba/Strassen/Schönhage… ; hiérarchie asymptotique standard) NON
recalculées par la même expression + SOUNDNESS : entrée invalide -> ValueError (jamais un résultat faux).
"""
import complexite as M

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


# ── 1) THÉORÈME MAÎTRE — ancres CLRS connues (forme symbolique de Θ) ──────────────────────────────────────────
check(M.classe_master(2, 2, 1) == "n log n", "mergesort a=2,b=2,d=1 -> n log n")
check(M.classe_master(1, 2, 0) == "log n", "recherche dichotomique a=1,b=2,d=0 -> log n")
check(M.classe_master(7, 2, 2) == "n^2.807355", "Strassen a=7,b=2,d=2 -> n^log2(7)")
check(M.classe_master(3, 2, 1) == "n^1.584963", "Karatsuba a=3,b=2,d=1 -> n^log2(3)")
check(M.classe_master(8, 2, 3) == "n^3 log n", "mult. matricielle naïve D&C a=8,b=2,d=3 -> n^3 log n")
check(M.classe_master(4, 2, 2) == "n^2 log n", "a=4,b=2,d=2 -> n^2 log n (équilibre)")
check(M.classe_master(4, 2, 1) == "n^2", "a=4,b=2,d=1 -> n^2 (feuilles)")
check(M.classe_master(2, 2, 2) == "n^2", "a=2,b=2,d=2 -> n^2 (racine)")
check(M.classe_master(1, 2, 1) == "n", "a=1,b=2,d=1 -> n (racine)")
check(M.classe_master(2, 2, 0) == "n", "parcours arbre binaire a=2,b=2,d=0 -> n (feuilles)")
check(M.classe_master(9, 3, 1) == "n^2", "CLRS a=9,b=3,d=1 -> n^2 (feuilles)")
check(M.classe_master(3, 4, 1) == "n", "a=3,b=4,d=1 -> n (log4(3)≈0.79<1, racine)")

# régime + exposant critique
check(M.regime_master(2, 2, 1) == "equilibre", "régime mergesort = équilibre")
check(M.regime_master(7, 2, 2) == "feuilles", "régime Strassen = feuilles")
check(M.regime_master(2, 2, 2) == "racine", "régime a=2,b=2,d=2 = racine")
check(abs(M.exposant_critique(7, 2) - 2.807355) < 1e-6, "log2(7) ≈ 2.807355")
check(abs(M.exposant_critique(3, 2) - 1.584963) < 1e-6, "log2(3) ≈ 1.584963")
check(M.exposant_critique(8, 2) == 2.0 + 1.0 and M.exposant_critique(9, 3) == 2.0, "log2(8)=3, log3(9)=2")

# ── 2) ORDRE DE CROISSANCE — hiérarchie asymptotique connue ───────────────────────────────────────────────────
check(M.compare_croissance("n", "n^2", 1000) == "n^2", "n^2 domine n")
check(M.compare_croissance("n^2", "n", 1000) == "n^2", "symétrie : n^2 domine n")
check(M.compare_croissance("1", "log n", 1000) == "log n", "log n domine la constante")
check(M.compare_croissance("log n", "n", 1000) == "n", "n domine log n")
check(M.compare_croissance("n", "n log n", 1000) == "n log n", "n log n domine n")
check(M.compare_croissance("n log n", "n^2", 1000) == "n^2", "n^2 domine n log n")
check(M.compare_croissance("n^5", "2^n", 1000) == "2^n", "exponentielle domine tout polynôme")
check(M.compare_croissance("2^n", "3^n", 1000) == "3^n", "3^n domine 2^n")
check(M.compare_croissance("2^n", "n!", 1000) == "n!", "factorielle domine l'exponentielle")
check(M.compare_croissance("n^2 log n", "n^2", 50) == "n^2 log n", "facteur log départage à degré égal")
check(M.compare_croissance("log^2 n", "log n", 50) == "log^2 n", "log^2 n domine log n")
check(M.compare_croissance("n", "n", 10) == "equivalent", "même classe -> equivalent")
check(M.compare_croissance("2*n", "n", 7) == "equivalent", "facteur constant ignoré : 2n ~ n")

# ── 3) SOUNDNESS — théorème maître : domaine invalide -> ValueError ────────────────────────────────────────────
check(leve(M.classe_master, 0.5, 2, 1), "a<1 -> ValueError")
check(leve(M.classe_master, 2, 1, 1), "b=1 -> ValueError")
check(leve(M.classe_master, 2, 0.5, 1), "b<1 -> ValueError")
check(leve(M.classe_master, 2, 2, -1), "d<0 -> ValueError")
check(leve(M.classe_master, True, 2, 1), "a bool -> ValueError")
check(leve(M.classe_master, "2", 2, 1), "a str -> ValueError")
check(leve(M.exposant_critique, 0.5, 2), "exposant_critique a<1 -> ValueError")
check(leve(M.exposant_critique, 2, 1), "exposant_critique b=1 -> ValueError")
check(leve(M.regime_master, 2, 2, -3), "regime_master d<0 -> ValueError")

# ── 4) SOUNDNESS — ordre de croissance : forme/témoin invalides -> ValueError ──────────────────────────────────
check(leve(M.compare_croissance, "n", "salade", 1000), "forme non reconnue -> ValueError")
check(leve(M.compare_croissance, "n", "n^2", 0), "témoin n<1 -> ValueError")
check(leve(M.compare_croissance, "n", "n^2", 1.5), "témoin non entier -> ValueError")
check(leve(M.compare_croissance, "n", "n^2", True), "témoin bool -> ValueError")
check(leve(M.compare_croissance, "1^n", "n", 10), "base exponentielle ≤ 1 -> ValueError")
check(leve(M.ordre_croissance, ""), "expression vide -> ValueError")
check(leve(M.ordre_croissance, "n^^2"), "syntaxe mal formée -> ValueError")
check(leve(M.ordre_croissance, 42), "non-str -> ValueError")

# ── 5) DÉTERMINISME ───────────────────────────────────────────────────────────────────────────────────────────
check(M.classe_master(7, 2, 2) == M.classe_master(7, 2, 2), "déterminisme classe_master")
check(M.compare_croissance("n", "n^2", 1000) == M.compare_croissance("n", "n^2", 1000),
      "déterminisme compare_croissance")

print(f"\n=== valide_complexite : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
