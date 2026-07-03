"""VALIDATION trace.py (Vague 7). FAUX=0 : justification obligatoire, acyclique, verifie() casse si une étape échoue."""
from __future__ import annotations
from trace import Trace, Cycle

ok = 0; total = 0
def check(nom, cond):
    global ok, total; total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}", flush=True)
    if cond: ok += 1
    else: raise AssertionError(nom)
def leve(fn, exc):
    try: fn(); return False
    except exc: return True

# Chaîne : deux prémisses -> une déduction (COP réel < COP Carnot -> marge existe).
t = Trace()
t.premisse("carnot", 19.7, source="limite.Carnot(T)")
t.premisse("reel", 3.5, source="fiche_produit")
t.etape("marge", "division", ["carnot", "reel"], 19.7 / 3.5,
        "COP_max/COP_reel", verificateur=lambda: 19.7 / 3.5 > 1)
check("sortie de l'étape calculée", abs(t.sortie("marge") - 19.7 / 3.5) < 1e-9)
check("remonte() donne la sous-trace complète (2 prémisses + l'étape)", set(t.remonte("marge")) == {"carnot", "reel", "marge"})
check("justification récupérable", t.justification("marge") == "COP_max/COP_reel")
check("verifie() True quand chaque vérificateur passe", t.verifie("marge"))

# Une étape dont le vérificateur ÉCHOUE casse la conclusion (pas masquée)
t.etape("faux", "test", ["marge"], True, "assertion douteuse", verificateur=lambda: False)
check("verifie() False si une étape de la sous-trace échoue", not t.verifie("faux"))
check("mais la sous-trace saine reste vérifiable", t.verifie("marge"))

# FAUX=0 : justification obligatoire, entrée inconnue, redéfinition
check("étape sans justification -> refus", leve(lambda: t.etape("x", "op", ["carnot"], 1, ""), ValueError))
check("étape avec entrée inconnue -> refus", leve(lambda: t.etape("y", "op", ["fantome"], 1, "j"), ValueError))
check("prémisse sans source -> refus", leve(lambda: t.premisse("z", 1, source=""), ValueError))
check("redéfinir une étape -> refus", leve(lambda: t.etape("marge", "op", ["carnot"], 1, "j"), ValueError))

# Acyclicité : impossible de créer un cycle (entrées doivent préexister) -> structure garantie DAG
check("remonte sur une prémisse = elle-même", t.remonte("carnot") == ["carnot"])

print(f"\n=== valide_trace : {ok}/{total} checks OK ===")
if ok != total: raise SystemExit(1)
