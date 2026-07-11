"""
VALIDATION — FAMILLE D'INVENTION TOUTES-PAIRES (etend_paires) : employer la Forge pour repousser une frontière.

Frontière MESURÉE (avant la famille : brique_manquante, 0 candidat) : aucune famille ne construisait
d'agrégat sur les COUPLES (i<j) de la liste — les relations ENTRE éléments distants (nb d'inversions,
nb de paires égales, somme des écarts de couples) étaient hors de portée des familles locales (fenêtre, fold).

Méthode SOUND (anti-coïncidence) : labels GÉNÉRÉS par la fonction de référence, entrées adversariales de
longueurs variées, réalisation RE-VÉRIFIÉE hors moteur sur toutes les paires + des sondes fraîches.

Prouve : (1) FRONTIÈRE FERMÉE — nb_inversions, nb_paires_egales, somme_ecarts_paires deviennent INVENTION,
réalisation toutes-paires (contient les deux boucles range) ; (2) CORRECT — reproduit toutes les paires +
sondes fraîches (hors moteur) ; (3) SOLIDITÉ — force_spec score élevé ; (4) DÉTERMINISME ; (5) NON-RÉGRESSION
— une cible non-pairwise (amplitude) reste l'invention attendue, sans les boucles.
"""
from __future__ import annotations

from garde_ressources import borne
borne(max_cpu_s=400)
import ia
import moteur_invention as MI

ok = total = 0


def check(nom, cond):
    global ok, total
    total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}")
    if cond:
        ok += 1
    else:
        raise AssertionError(nom)


def _fn(expr):
    ns: dict = {}
    exec(f"def _f(x):\n    return {expr}\n", ns)
    return ns["_f"]


def _reproduit_tout(expr, paires):
    f = _fn(expr)
    for a, o in paires:
        r = f(list(a))
        if r != o or isinstance(r, bool) != isinstance(o, bool):
            return False
    return True


LISTES = [[1, 2, 3], [3, 2, 1], [2, 1, 3], [1, 3, 2], [4, 1, 2, 3], [5, 5, 5], [1, 1, 2], [2, 3, 1, 4]]
SONDES_FRAICHES = [[9, 8, 7, 6], [0, 0], [1, 2, 2, 1], [3]]

REFS = {
    "nb_inversions": lambda x: sum(1 for i in range(len(x)) for j in range(i + 1, len(x)) if x[i] > x[j]),
    "nb_paires_egales": lambda x: sum(1 for i in range(len(x)) for j in range(i + 1, len(x)) if x[i] == x[j]),
    "somme_ecarts_paires": lambda x: sum(abs(x[i] - x[j]) for i in range(len(x)) for j in range(i + 1, len(x))),
}


def _paires(f, listes):
    return [(xs, f(xs)) for xs in listes]


for nom, f in REFS.items():
    ps = _paires(f, LISTES)
    ex, held = ps[:4], ps[4:]
    v = MI.examine_cible(nom, "x", ex, held)
    check(f"{nom} : frontière FERMÉE en INVENTION", v.statut == MI.INVENTION)
    check(f"{nom} : réalisation toutes-paires (deux boucles range)",
          v.par is not None and v.par.count("range(") >= 2)
    check(f"{nom} : reproduit toutes les paires (hors moteur)", _reproduit_tout(v.par, ex + held))
    fresh = [(s, f(s)) for s in SONDES_FRAICHES]
    check(f"{nom} : correcte sur des sondes FRAÎCHES (pas une coïncidence)", _reproduit_tout(v.par, fresh))
    fs = ia.force_du_spec(v.par, ex, held)
    check(f"{nom} : spec fort (score de mutation >= 0.6)", fs["score"] >= 0.6)
    v2 = MI.examine_cible(nom, "x", ex, held)
    check(f"{nom} : déterministe (même réalisation)", v2.par == v.par)

va = MI.examine_cible("amplitude", "x", [([3, 1, 5], 4), ([2, 2], 0), ([10, 0, 3], 10)],
                      [([0, 9, 4], 9), ([7], 0), ([5, 5, 1], 4)])
check("non-rég : amplitude reste INVENTION (max-min), la famille paires ne la perturbe pas",
      va.statut == MI.INVENTION and va.par is not None and va.par.count("range(") < 2)

print(f"\n== VALIDE_INVENTION_PAIRES : {ok}/{total} ==")
assert ok == total
