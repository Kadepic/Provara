"""VALIDATION relaxation.py (Vague 5). FAUX=0 : ensemble relâché rend RÉELLEMENT SAT (vérifié) ; minimal ; [] si déjà SAT."""
from __future__ import annotations
from contrainte import CSP
from relaxation import relache_minimal, conflit

ok = 0; total = 0
def check(nom, cond):
    global ok, total; total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}", flush=True)
    if cond: ok += 1
    else: raise AssertionError(nom)

# CSP sur-contraint : x∈{1,2}, x>1 ET x<2 -> UNSAT (aucune valeur). Relâcher une des deux suffit.
c = CSP()
c.variable("x", [1, 2])
c.contrainte(("x",), lambda x: x > 1, "x>1")
c.contrainte(("x",), lambda x: x < 2, "x<2")
r = relache_minimal(c)
check("relaxation trouvée pour un CSP UNSAT", r is not None)
check("un seul contrainte à relâcher (minimal)", len(r["contraintes_a_relacher"]) == 1)
check("la contrainte relâchée est x>1 ou x<2", r["contraintes_a_relacher"][0] in ("x>1", "x<2"))
check("la solution du CSP réduit satisfait bien les contraintes restantes", isinstance(r["solution"], dict) and "x" in r["solution"])

# déjà satisfiable -> rien à relâcher
c2 = CSP(); c2.variable("y", [1, 2, 3]); c2.contrainte(("y",), lambda y: y >= 2, "y>=2")
check("CSP déjà satisfiable -> [] (rien à relâcher)", relache_minimal(c2)["contraintes_a_relacher"] == [])

# conflit() renvoie le noyau conflictuel
check("conflit() sur UNSAT renvoie une contrainte fautive", conflit(c) and len(conflit(c)) == 1)
check("conflit() sur SAT renvoie []", conflit(c2) == [])

# sur-contrainte à 3 : besoin d'en relâcher plus d'une
c3 = CSP(); c3.variable("z", [5])
c3.contrainte(("z",), lambda z: z < 5, "z<5")
c3.contrainte(("z",), lambda z: z > 5, "z>5")
r3 = relache_minimal(c3)
check("z∈{5} avec z<5 ET z>5 : relâcher les DEUX (aucune seule ne suffit)", len(r3["contraintes_a_relacher"]) == 2)

print(f"\n=== valide_relaxation : {ok}/{total} checks OK ===")
if ok != total: raise SystemExit(1)
