"""
VALIDATION du SOLVEUR DE CONTRAINTES (contrainte.py) — Vague 2.
FAUX=0 : solution rendue re-vérifiée ; UNSAT honnête ; déterministe ; recherche complète.
"""
from __future__ import annotations

from contrainte import CSP

ok = 0
total = 0


def check(nom, cond):
    global ok, total
    total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}", flush=True)
    if cond:
        ok += 1
    else:
        raise AssertionError(nom)


# ── Coloration de graphe : triangle, 2 couleurs -> UNSAT ; 3 couleurs -> SAT ─────────────
def triangle(couleurs):
    c = CSP()
    for n in ("A", "B", "C"):
        c.variable(n, couleurs)
    diff = lambda x, y: x != y
    c.contrainte(("A", "B"), diff, "A≠B")
    c.contrainte(("B", "C"), diff, "B≠C")
    c.contrainte(("A", "C"), diff, "A≠C")
    return c

t2 = triangle(["r", "v"])
check("triangle 2 couleurs : INSATISFIABLE (UNSAT honnête)", t2.resout() is None and not t2.satisfiable())
t3 = triangle(["r", "v", "b"])
sol = t3.resout()
check("triangle 3 couleurs : une solution existe", sol is not None)
check("la solution RENDUE satisfait vraiment toutes les contraintes", t3.satisfait(sol))
check("solution valide : les 3 couleurs distinctes", len(set(sol.values())) == 3)

# ── Déterminisme : même entrée -> même première solution ─────────────────────────────────
check("déterministe (2 appels identiques)", triangle(["r", "v", "b"]).resout() == triangle(["r", "v", "b"]).resout())

# ── Contrainte arithmétique sur domaines finis : x + y = z ───────────────────────────────
c = CSP()
c.variable("x", range(0, 6)).variable("y", range(0, 6)).variable("z", range(0, 11))
c.contrainte(("x", "y", "z"), lambda x, y, z: x + y == z, "x+y=z")
c.contrainte(("x", "y"), lambda x, y: x < y, "x<y")
sols = c.solutions()
check("x+y=z avec x<y : au moins une solution", len(sols) > 0)
check("TOUTES les solutions énumérées satisfont les contraintes", all(c.satisfait(s) for s in sols))
check("aucune solution ne viole x<y", all(s["x"] < s["y"] for s in sols))
check("complétude : le nb de solutions est exact (recompté à la main)",
      len(sols) == sum(1 for x in range(6) for y in range(6) for z in range(11) if x + y == z and x < y))

# ── FAUX=0 : jamais une affectation inventée ; UNSAT clair ───────────────────────────────
d = CSP()
d.variable("a", [1, 2]).variable("b", [1, 2])
d.contrainte(("a", "b"), lambda a, b: a == b, "a=b")
d.contrainte(("a", "b"), lambda a, b: a != b, "a≠b")     # contradiction
check("contraintes contradictoires -> UNSAT (None), pas d'invention", d.resout() is None)
check("solutions() -> [] sur UNSAT", d.solutions() == [])

# ── satisfait() rejette une affectation incomplète ou fausse ─────────────────────────────
check("satisfait() faux si affectation incomplète", not t3.satisfait({"A": "r"}))
check("satisfait() faux si une contrainte violée", not t3.satisfait({"A": "r", "B": "r", "C": "v"}))
check("contraintes_violees liste les fautives",
      set(t3.contraintes_violees({"A": "r", "B": "r", "C": "v"})) == {"A≠B"})

# ── contrainte sur variable inconnue -> refusée ──────────────────────────────────────────
e = CSP()
e.variable("p", [0, 1])
try:
    e.contrainte(("p", "q"), lambda p, q: True)
    refuse = False
except ValueError:
    refuse = True
check("contrainte sur variable non déclarée -> refusée", refuse)

print(f"\n=== valide_contrainte : {ok}/{total} checks OK ===")
if ok != total:
    raise SystemExit(1)
