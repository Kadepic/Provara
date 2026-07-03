"""VALIDE maths_discretes.py — held-out ADVERSE, FAUX=0. Ancres EXTERNES connues (suites OEIS, identités de graphes,
aires géométriques) NON recalculées par la même expression + SOUNDNESS : entrée invalide -> ValueError (jamais faux).
"""
import maths_discretes as M

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


# ── COMBINATOIRE — ancres OEIS connues ──
check([M.catalan(i) for i in range(8)] == [1, 1, 2, 5, 14, 42, 132, 429], "Catalan A000108")
check([M.derangements(i) for i in range(7)] == [1, 0, 1, 2, 9, 44, 265], "dérangements A000166")
check([M.partitions(i) for i in range(8)] == [1, 1, 2, 3, 5, 7, 11, 15], "partitions A000041")
check(M.binomial(10, 3) == 120 and M.binomial(52, 5) == 2598960, "binomial : C(10,3)=120, C(52,5)=2598960")
check(M.binomial(5, 0) == 1 and M.binomial(5, 5) == 1 and M.binomial(5, 6) == 0 and M.binomial(5, -1) == 0,
      "binomial bords : C(n,0)=C(n,n)=1, k>n ou k<0 -> 0")
check(M.factorielle(0) == 1 and M.factorielle(6) == 720, "factorielle 0!=1, 6!=720")

# ── RÉCURRENCES — ancres Fibonacci/Lucas ──
check([M.fibonacci(i) for i in range(11)] == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55], "Fibonacci A000045")
check([M.lucas(i) for i in range(8)] == [2, 1, 3, 4, 7, 11, 18, 29], "Lucas A000032")
# Pell : P(n)=2P(n-1)+P(n-2), 0,1,2,5,12,29,70
check([M.suite_recurrente(0, 1, 2, 1, i) for i in range(7)] == [0, 1, 2, 5, 12, 29, 70], "Pell A000129")

# ── GRAPHES — identités connues ──
check(M.composantes_connexes(5, [(0, 1), (1, 2), (3, 4)]) == 2, "2 composantes (triangle-chemin + arête)")
check(M.composantes_connexes(4, []) == 4, "graphe vide -> n composantes")
check(M.a_cycle(4, [(0, 1), (1, 2), (2, 3)]) is False, "chemin -> pas de cycle")
check(M.a_cycle(3, [(0, 1), (1, 2), (2, 0)]) is True, "triangle -> cycle")
check(M.a_cycle(2, [(0, 1), (0, 1)]) is True, "arête double -> cycle")
check(M.distance_bfs(5, [(0, 1), (1, 2), (2, 3), (3, 4)], 0, 4) == 4, "BFS chemin longueur 4")
check(M.distance_bfs(4, [(0, 1), (2, 3)], 0, 3) == -1, "BFS inatteignable -> -1")
check(M.distance_bfs(3, [(0, 1), (1, 2)], 1, 1) == 0, "BFS src=dst -> 0")
check(M.est_arbre(4, [(0, 1), (1, 2), (2, 3)]) is True, "chemin = arbre")
check(M.est_arbre(3, [(0, 1), (1, 2), (2, 0)]) is False, "triangle ≠ arbre (cycle)")
check(M.est_arbre(4, [(0, 1), (1, 2)]) is False, "non connexe ≠ arbre")
check(M.est_biparti(4, [(0, 1), (1, 2), (2, 3)]) is True, "chemin pair-impair = biparti")
check(M.est_biparti(3, [(0, 1), (1, 2), (2, 0)]) is False, "triangle (cycle impair) ≠ biparti")
check(M.est_biparti(4, [(0, 1), (2, 3)]) is True, "forêt = biparti")

# ── DIJKSTRA — plus court chemin pondéré (ancre vérifiable à la main) ──
check(M.dijkstra(4, [(0, 1, 1), (1, 3, 1), (0, 2, 5), (2, 3, 1)], 0, 3) == 2, "Dijkstra : 0-1-3 = 2 < 0-2-3 = 6")
check(M.dijkstra(3, [(0, 1, 4), (1, 2, 4), (0, 2, 3)], 0, 2) == 3, "Dijkstra : arête directe 3 < 4+4")
check(M.dijkstra(3, [(0, 1, 1)], 0, 2) == -1, "Dijkstra inatteignable -> -1")
check(M.dijkstra(2, [], 0, 0) == 0, "Dijkstra src=dst -> 0")

# ── GÉOMÉTRIE — aires/orientation connues ──
check(M.aire_triangle_x2((0, 0), (4, 0), (0, 3)) == 12, "triangle 3-4-5 : aire 6 -> ×2 = 12")
check(M.aire_triangle_x2((0, 0), (5, 0), (10, 0)) == 0, "colinéaires -> 0")
check(M.aire_polygone_x2([(0, 0), (4, 0), (4, 3), (0, 3)]) == 24, "rectangle 4×3 : aire 12 -> ×2 = 24")
check(M.aire_polygone_x2([(0, 0), (6, 0), (0, 6)]) == 36, "triangle isocèle aire 18 -> ×2 = 36")
check(M.orientation((0, 0), (1, 0), (1, 1)) == 1, "orientation gauche -> +1")
check(M.orientation((0, 0), (1, 0), (1, -1)) == -1, "orientation droite -> -1")
check(M.orientation((0, 0), (1, 1), (2, 2)) == 0, "colinéaire -> 0")
check(M.distance_manhattan((1, 2), (4, 6)) == 7, "Manhattan |3|+|4| = 7")

# ── STRUCTURES — RPN / équilibrage ──
check(M.eval_rpn(["2", "3", "+", "4", "*"]) == 20, "RPN (2+3)*4 = 20")
check(M.eval_rpn(["15", "7", "1", "1", "+", "-", "//", "3", "*"]) == 9, "RPN composé = 9")
check(M.eval_rpn(["42"]) == 42, "RPN singleton")
check(M.equilibre("(()[]{})") is True and M.equilibre("([)]") is False, "équilibrage : imbriqué OK, croisé KO")
check(M.equilibre("") is True and M.equilibre("(((") is False, "équilibrage : vide OK, ouvrants seuls KO")

# ── SOUNDNESS — entrée invalide -> ValueError (jamais un faux résultat) ──
check(leve(M.catalan, -1), "catalan(-1) -> ValueError")
check(leve(M.factorielle, -3), "factorielle(-3) -> ValueError")
check(leve(M.binomial, -1, 2), "binomial(-1,2) -> ValueError")
check(leve(M.fibonacci, -1), "fibonacci(-1) -> ValueError")
check(leve(M.composantes_connexes, 2, [(0, 5)]), "sommet hors plage -> ValueError")
check(leve(M.a_cycle, 3, [(0, 1, 2)]), "arête mal formée -> ValueError")
check(leve(M.dijkstra, 3, [(0, 1, -1)], 0, 1), "poids négatif -> ValueError")
check(leve(M.aire_triangle_x2, (0, 0), (1, 1), (2,)), "point mal formé -> ValueError")
check(leve(M.aire_polygone_x2, [(0, 0), (1, 1)]), "polygone < 3 sommets -> ValueError")
check(leve(M.eval_rpn, ["1", "0", "//"]), "RPN division par zéro -> ValueError")
check(leve(M.eval_rpn, ["1", "2", "//"]), "RPN division non exacte -> ValueError")
check(leve(M.eval_rpn, ["1", "+"]), "RPN opérandes manquants -> ValueError")
check(leve(M.eval_rpn, ["abc"]), "RPN jeton invalide -> ValueError")

# ── DÉTERMINISME ──
check(M.dijkstra(4, [(0, 1, 1), (1, 3, 1), (0, 2, 5), (2, 3, 1)], 0, 3)
      == M.dijkstra(4, [(0, 1, 1), (1, 3, 1), (0, 2, 5), (2, 3, 1)], 0, 3), "déterminisme")

print(f"\n=== valide_maths_discretes : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
