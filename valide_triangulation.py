"""VALIDATION triangulation.py (Vague 6). FAUX=0 : même méthode -> non_independant ; accord/désaccord factuel."""
from __future__ import annotations
from triangulation import triangule, confirme, CORROBORE, DISCORDE, NON_INDEPENDANT, INDETERMINE

ok = 0; total = 0
def check(nom, cond):
    global ok, total; total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}", flush=True)
    if cond: ok += 1
    else: raise AssertionError(nom)

# Deux méthodes indépendantes concordantes -> corrobore
check("deux méthodes indépendantes qui concordent -> CORROBORE",
      triangule(9.81, "pendule", 9.80, "chute_libre", tol_rel=1e-2) == CORROBORE)
check("confirme() True seulement pour méthodes indépendantes concordantes",
      confirme(9.81, "pendule", 9.80, "chute_libre", tol_rel=1e-2))

# Désaccord -> discorde (erreur à débusquer)
check("désaccord notable -> DISCORDE", triangule(9.8, "A", 12.0, "B") == DISCORDE)
check("confirme() False sur désaccord", not confirme(9.8, "A", 12.0, "B"))

# NON-CIRCULARITÉ : même méthode -> pas de corroboration
check("même méthode des deux côtés -> NON_INDEPENDANT (accord trivial)",
      triangule(9.81, "pendule", 9.81, "pendule") == NON_INDEPENDANT)
check("confirme() False si non indépendant (même valeur, même méthode)",
      not confirme(42.0, "sim", 42.0, "sim"))

# Valeurs non finies / non numériques -> indéterminé (jamais d'accord fabriqué)
check("valeur non numérique -> INDETERMINE", triangule("x", "A", 3.0, "B") == INDETERMINE)
check("infini -> INDETERMINE", triangule(float("inf"), "A", 1.0, "B") == INDETERMINE)

print(f"\n=== valide_triangulation : {ok}/{total} checks OK ===")
if ok != total: raise SystemExit(1)
