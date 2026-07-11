"""
VALIDATION — FAMILLE SOUS-TABLEAUX CONTIGUS (etend_sous_tableaux) : Forge sur la frontière de Kadane.

Frontière MESURÉE (avant : brique_manquante) : aucune famille n'agrégeait les sommes des sous-tableaux
CONTIGUS x[i:j]. Le meilleur segment contigu (Kadane) était donc hors de portée — distinct de etend_paires
(couples d'éléments) et de accumulate (préfixes seuls, qui résout max_prefixe mais pas le meilleur segment).

Méthode SOUND : labels générés par l'algorithme de référence (Kadane), listes adversariales à valeurs
négatives (où max-sous-tableau diverge de max-préfixe et de la somme totale), réalisation re-vérifiée hors
moteur sur sondes fraîches.

Prouve : (1) FRONTIÈRE FERMÉE — max_sous_tableau et min_sous_tableau deviennent INVENTION ; (2) CORRECT —
reproduit toutes les paires + sondes fraîches (hors moteur) ; (3) DISTINCTION — la réalisation diffère de
max(accumulate) (préfixe) et de sum (total) sur une entrée à négatifs (ce n'est pas une coïncidence avec une
capacité plus simple) ; (4) DÉTERMINISME ; (5) NON-RÉGRESSION — max_prefixe reste résolu par accumulate.
"""
from __future__ import annotations

from garde_ressources import borne
borne(max_cpu_s=400)
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
    return all(f(list(a)) == o for a, o in paires)


def maxsub(x):
    best = cur = x[0]
    for e in x[1:]:
        cur = max(e, cur + e)
        best = max(best, cur)
    return best


def minsub(x):
    best = cur = x[0]
    for e in x[1:]:
        cur = min(e, cur + e)
        best = min(best, cur)
    return best


LISTES = [[1, -2, 3], [2, 1, -5], [-1, -1, 4], [3, -1, 2], [0, 0, 1], [-2, -3, -1], [4, -1, 2, -1, 3], [5, -9, 5, 5]]
SONDES = [[-1], [2, -8, 6, -1, 4], [-3, -2], [10, -1, -1, -1, 10]]

for nom, f in [("max_sous_tableau", maxsub), ("min_sous_tableau", minsub)]:
    ps = [(x, f(x)) for x in LISTES]
    ex, held = ps[:4], ps[4:]
    v = MI.examine_cible(nom, "x", ex, held)
    check(f"{nom} : frontière FERMÉE en INVENTION", v.statut == MI.INVENTION)
    check(f"{nom} : reproduit toutes les paires (hors moteur)", v.par and _reproduit_tout(v.par, ex + held))
    fresh = [(s, f(s)) for s in SONDES]
    check(f"{nom} : correcte sur des sondes FRAÎCHES (pas une coïncidence)", _reproduit_tout(v.par, fresh))
    v2 = MI.examine_cible(nom, "x", ex, held)
    check(f"{nom} : déterministe", v2.par == v.par)

# (3) DISTINCTION : sur [3,-1,2] Kadane=4 mais max-préfixe=4 aussi... on prend [4,-1,2,-1,3] : Kadane=7,
# max-préfixe=max(4,3,5,4,7)=7 (égal ici) ; mais [5,-9,5,5] : Kadane=10, préfixe=max(5,-4,1,6)=6, total=6.
xk = [5, -9, 5, 5]
check("distinction : Kadane([5,-9,5,5])=10 diffère de max-préfixe(6) et de la somme totale(6)",
      maxsub(xk) == 10 and max(__import__("itertools").accumulate(xk)) == 6 and sum(xk) == 6)

# (5) non-régression : max_prefixe reste résolu (par accumulate, pas par la nouvelle famille)
def maxpref(x):
    b = 0
    s = 0
    b = x[0]
    for e in x:
        s += e
        b = max(b, s)
    return b


pp = [(x, maxpref(x)) for x in LISTES]
vp = MI.examine_cible("max_prefixe", "x", pp[:4], pp[4:])
check("non-rég : max_prefixe reste INVENTION (accumulate), pas la famille sous-tableaux",
      vp.statut == MI.INVENTION and vp.par is not None and "x[_i:_j]" not in vp.par)

print(f"\n== VALIDE_INVENTION_SOUS_TABLEAUX : {ok}/{total} ==")
assert ok == total
