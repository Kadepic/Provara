"""
VALIDATION de l'AUTO-OPTIMISATION RÉCURSIVE (auto_optimise.py).

Cœur = les 3 GARDES DE SOUNDNESS (« sûr avant rapide ») :
  (1) un candidat qui ÉCHOUE le held-out n'est jamais adopté (même s'il est moins cher et s'accorde
      sur des sondes faibles) ;
  (2) un candidat moins cher mais NON ÉQUIVALENT (désaccord sur une sonde) n'est jamais adopté ;
  (3) on n'adopte que du STRICTEMENT moins cher -> le coût ne régresse JAMAIS (monotone).
Plus la mesure de coût (les passes O(n)) et l'adoption d'un vrai gain équivalent.
"""
from __future__ import annotations

from garde_ressources import borne
from demande import _asserts
import auto_optimise as O

borne()
ok = 0
total = 0


def check(nom, cond):
    global ok, total
    total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}")
    if cond:
        ok += 1
    else:
        raise AssertionError(nom)


def asserts(fn, paires):
    return _asserts(fn, [((a,), o) for a, o in paires])


# --- A) MESURE DE COÛT (les passes O(n)) -----------------------------------------------------
check("coût sum(x)+sum(x) = 2 passes", O.cout_expr("(sum(x) + sum(x))")[0] == 2)
check("coût sum(_e*2 for _e in x) = 1 passe (fusion)", O.cout_expr("sum(_e * 2 for _e in x)")[0] == 1)
check("coût x[0] = 0 passe", O.cout_expr("x[0]")[0] == 0)
check("coût min(x) = 1 passe", O.cout_expr("min(x)")[0] == 1)
check("coût max(x)-min(x) = 2 passes", O.cout_expr("(max(x) - min(x))")[0] == 2)

# --- B) ÉQUIVALENCE COMPORTEMENTALE sur sondes -----------------------------------------------
sondes = [[1, 2, 3], [5], [0, 4], [3, 1, 2], [7, 7]]   # chaque sonde EST l'argument x (cf. sondes_auto)
check("accord : sum(x)*2 ≡ sum(x)+sum(x)", O._accord_sur_sondes("(sum(x) + sum(x))", "sum(x) * 2", sondes))
check("désaccord : sum(x)*2 ≢ sum(x)*3", not O._accord_sur_sondes("sum(x) * 2", "sum(x) * 3", sondes))

# --- C) ADOPTION d'un vrai gain équivalent ---------------------------------------------------
held = [([2, 2], 8), ([7], 14), ([1, 1, 1, 1], 8), ([0, 5], 10)]   # cible = 2*sum(x)
th = asserts("f", held)
expr, c0, cf = O.optimise_expr("f", "(sum(x) + sum(x))", ["sum(_e * 2 for _e in x)", "max(x)"], th, sondes)
check("adopte la version 1-passe équivalente", expr == "sum(_e * 2 for _e in x)" and cf[0] == 1 and c0[0] == 2)

# --- D) GARDE (2) : moins cher mais NON équivalent -> REFUSÉ ----------------------------------
# candidat 'sum(x)*3' : 1 passe (moins cher que 2), mais comportement différent -> doit être rejeté.
expr, c0, cf = O.optimise_expr("f", "(sum(x) + sum(x))", ["sum(x) * 3"], th, sondes)
check("refuse un moins-cher NON équivalent (garde 2)", expr == "(sum(x) + sum(x))" and cf == c0)

# --- E) GARDE (1) : s'accorde sur sonde FAIBLE mais ÉCHOUE le held-out -> REFUSÉ --------------
# cible = min(x). candidat x[0] : 0 passe (moins cher), coïncide sur une sonde ascendante (min==x[0]),
# mais le held adverse [3,1,2]->1 le réfute. Doit rester min(x).
sonde_faible = [[1, 2, 3], [4, 5, 6]]                             # ascendantes : x[0]==min(x) (coïncidence)
held_min = asserts("f", [([3, 1, 2], 1), ([9, 0, 5], 0)])         # adverse : réfute x[0]
expr, c0, cf = O.optimise_expr("f", "min(x)", ["x[0]"], held_min, sonde_faible)
check("refuse un moins-cher qui échoue le held-out (garde 1)", expr == "min(x)")

# --- F) GARDE (3) / MONOTONIE : le coût final n'est JAMAIS pire que l'initial -----------------
cas = [
    ("(sum(x) + sum(x))", ["sum(_e * 2 for _e in x)", "max(x)", "sum(x) * 3"], th, sondes),
    ("min(x)", ["x[0]", "max(x)"], held_min, sonde_faible),
    ("sum(_e * 2 for _e in x)", ["(sum(x) + sum(x))"], th, sondes),   # ne doit PAS revenir au 2-passes
]
mono = True
for ea, cands, t, sd in cas:
    e, a, f = O.optimise_expr("f", ea, cands, t, sd)
    if f > a:
        mono = False
check("monotonie : coût final <= coût initial dans tous les cas", mono)

# --- G) POINT FIXE : déjà optimal -> inchangé ------------------------------------------------
expr, c0, cf = O.optimise_expr("f", "sum(_e * 2 for _e in x)", ["(sum(x) + sum(x))"], th, sondes)
check("point fixe : la 1-passe ne régresse pas vers la 2-passes", expr == "sum(_e * 2 for _e in x)")

print(f"\nAUTO_OPTIMISE VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
