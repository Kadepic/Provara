"""
BOUCLE RÉCURSIVE D'AUTO-OPTIMISATION (le « cap final » de Yohan : l'IA s'optimise ELLE-MÊME).

Principe : « améliorer × réduire ». Étant donné une solution DÉJÀ vérifiée à une tâche, l'IA cherche
une solution ÉQUIVALENTE mais STRICTEMENT MOINS COÛTEUSE, et ne l'adopte que si la réalité confirme
qu'elle ne régresse pas. Récursif : on réinjecte la solution retenue jusqu'au point fixe (plus rien
de moins cher d'équivalent).

GARDE DE SOUNDNESS (« sûr avant rapide ») — un candidat n'est adopté que s'il satisfait TOUT :
  1) il PASSE le juge sur le held-out (même couverture que la solution courante) ;
  2) il S'ACCORDE avec la solution courante sur TOUTES les sondes adverses auto-forgées
     (équivalence comportementale observée — barre anti-coïncidence, cf. active learning) ;
  3) il est STRICTEMENT moins coûteux.
Donc l'optimisation ne peut JAMAIS rendre la solution fausse ni la dégrader : au pire elle ne change
rien (point fixe). Le coût mesuré = ressources de CALCUL (nombre de passes O(n) sur l'entrée, puis
taille de l'AST) — c'est le « réduire » concret, pas juste raccourcir le texte.
"""
from __future__ import annotations

import ast

from auto_invention_ouverte import LIM, _fn
from juge import juge


# --- COÛT d'une expression = ressources de calcul (le « réduire ») ----------------------------
_PASSES = {"sum", "max", "min", "sorted", "len", "any", "all", "reduce", "map", "filter", "set", "list"}


_COMPS = (ast.GeneratorExp, ast.ListComp, ast.SetComp, ast.DictComp)


def cout_expr(expr: str) -> tuple[int, int]:
    """(#passes O(n) sur l'entrée, #nœuds AST). Une PASSE = une itération distincte de l'entrée :
    chaque compréhension/générateur compte 1 ; un agrégateur (sum/max/min/sorted/len…) compte 1 SAUF
    s'il s'applique à une compréhension (alors la passe est déjà comptée — pas de double-compte/fusion).
    Ainsi `sum(x)+sum(x)` = 2 passes ; `sum(2*_e for _e in x)` = 1 passe (fusionnée) -> moins cher.
    Tiebreak = taille de l'AST (expression plus simple à calcul égal)."""
    try:
        arbre = ast.parse(expr, mode="eval")
    except SyntaxError:
        return (10**6, len(expr))   # illisible = infiniment cher (jamais choisi)
    passes = 0
    nb = 0
    for n in ast.walk(arbre):
        nb += 1
        if isinstance(n, _COMPS):
            passes += 1
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in _PASSES:
            arg0 = n.args[0] if n.args else None
            if not isinstance(arg0, _COMPS):        # agrégateur sur une compréhension : déjà compté
                passes += 1
    return (passes, nb)


def _accord_sur_sondes(expr_a: str, expr_b: str, sondes) -> bool:
    """True si a et b donnent le MÊME résultat (ou la même erreur) sur toutes les sondes. Équivalence observée."""
    fa, fb = _fn(expr_a), _fn(expr_b)

    def ev(f, s):
        try:
            return ("ok", repr(f(s)))
        except Exception:
            return ("err", "")
    return all(ev(fa, s) == ev(fb, s) for s in sondes)


def optimise_expr(point_entree, expr_actuel, candidats, tests_held, sondes):
    """Renvoie (expr_retenu, cout_avant, cout_apres). N'adopte un candidat que s'il (1) passe le held-out,
    (2) s'accorde avec `expr_actuel` sur toutes les sondes, (3) coûte STRICTEMENT moins. Sinon garde l'actuel."""
    cout_actuel = cout_expr(expr_actuel)
    meilleur, cout_meilleur = expr_actuel, cout_actuel
    for expr in candidats:
        if expr == expr_actuel:
            continue
        c = cout_expr(expr)
        if c >= cout_meilleur:                       # pas moins cher que le meilleur courant -> inutile
            continue
        if not _accord_sur_sondes(expr_actuel, expr, sondes):   # garde (2) : équivalence comportementale
            continue
        code = f"def {point_entree}(x):\n    return {expr}\n"
        if not juge(code, tests_held, LIM).passe:    # garde (1) : même couverture sur le held-out
            continue
        meilleur, cout_meilleur = expr, c
    return meilleur, cout_actuel, cout_meilleur


def optimise_jusqu_fixe(moteur, tache, exemples, exemples_held, expr_depart, sondes=None, max_tours=6):
    """RÉCURSION jusqu'au POINT FIXE : tant qu'un candidat équivalent moins cher existe, l'adopter et recommencer.
    `moteur` fournit l'espace de candidats (`_candidats_passants` sur les exemples VISIBLES). `tache` doit avoir
    `tests` (visibles) et `tests_held_out` (held). Renvoie {expr, cout_initial, cout_final, tours, gain_passes}."""
    from demande import _asserts
    if sondes is None:
        sondes = moteur.sondes_auto(exemples)
    tests_held = tache.tests_held_out or _asserts(tache.point_entree, [((a,), o) for a, o in exemples_held])
    expr = expr_depart
    cout0 = cout_expr(expr)
    tours = 0
    for _ in range(max_tours):
        cands = [e for e, _ti, _to in moteur._candidats_passants(tache)]
        expr2, _, _ = optimise_expr(tache.point_entree, expr, cands, tests_held, sondes)
        if expr2 == expr:
            break                                    # point fixe : plus rien d'équivalent moins cher
        expr = expr2
        tours += 1
    coutf = cout_expr(expr)
    return {"expr": expr, "cout_initial": cout0, "cout_final": coutf, "tours": tours,
            "gain_passes": cout0[0] - coutf[0]}


if __name__ == "__main__":
    from garde_ressources import borne
    from taches import Tache
    from demande import _asserts
    from auto_apprend import MoteurAutonome
    borne()
    print("=== AUTO-OPTIMISATION RÉCURSIVE (améliorer × réduire, jugée par la réalité) ===\n")

    m = MoteurAutonome()
    m.explore_combine(budget=3000)

    # somme_doubles = 2*sum(x). Le moteur connaît la version 2-passes sum(x)+sum(x) ET (via composition) une 1-passe.
    vis = [([1, 2, 3], 12), ([5], 10), ([0, 4], 8)]
    held = [([2, 2], 8), ([7], 14), ([1, 1, 1, 1], 8)]
    m.etend_vocabulaire([(x, o) for x, o in vis])
    m.etend_composition([(x, o) for x, o in vis])
    t = Tache(id="somme_doubles", point_entree="somme_doubles",
              prompt="def somme_doubles(x):\n  pass",
              tests=_asserts("somme_doubles", [((a,), o) for a, o in vis]),
              tests_held_out=_asserts("somme_doubles", [((a,), o) for a, o in held]))
    depart = "(sum(x) + sum(x))"      # solution correcte mais 2 passes
    r = optimise_jusqu_fixe(m, t, vis, held, depart)
    print(f"  somme_doubles : départ {depart!r} coût(passes,ast)={r['cout_initial']}")
    print(f"                  -> retenu {r['expr']!r} coût={r['cout_final']}  (tours={r['tours']}, "
          f"gain {r['gain_passes']} passe(s))")
    print("\n  Garantie : adopté SEULEMENT car il passe le held-out, s'accorde sur les sondes adverses, "
          "et coûte moins. Sinon, point fixe (rien changé).")
