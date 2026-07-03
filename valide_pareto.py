"""VALIDATION pareto.py (Vague 5). FAUX=0 : dominance exacte ; front = non-dominés ; aucun compromis inventé."""
from __future__ import annotations
from pareto import domine, front, domines

ok = 0; total = 0
def check(nom, cond):
    global ok, total; total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}", flush=True)
    if cond: ok += 1
    else: raise AssertionError(nom)

# Objectifs : (coût [min], performance [max]).
sens = ("min", "max")
check("domine : (coût 10, perf 8) domine (coût 12, perf 7)", domine((10, 8), (12, 7), sens))
check("ne domine PAS si compromis (moins cher mais moins performant)", not domine((10, 5), (12, 8), sens))
check("pas d'auto-domination (égalité stricte)", not domine((10, 8), (10, 8), sens))

# Front de designs de refroidissement fictifs : (conso [min], efficacité [max]).
# radiatif/hybride/ultra_perf sont mutuellement non dominés (chacun meilleur sur un axe) ; 'mauvais' est dominé.
designs = [
    ("radiatif_passif", (10, 1.0)),   # le moins cher, faible efficacité
    ("hybride", (40, 4.0)),           # compromis
    ("ultra_perf", (80, 5.0)),        # le plus efficace, cher
    ("mauvais", (120, 2.0)),          # dominé par ultra_perf ET hybride
]
f = front(designs, sens)
etiq = {e for e, _ in f}
check("le front exclut le design dominé ('mauvais')", "mauvais" not in etiq)
check("radiatif_passif, hybride, ultra_perf sont non dominés (vrai compromis à 3)",
      {"radiatif_passif", "hybride", "ultra_perf"} == etiq)
check("le dominé est bien listé par domines()", "mauvais" in {e for e, _ in domines(designs, sens)})
check("ordre d'entrée préservé dans le front", [e for e, _ in f] == ["radiatif_passif", "hybride", "ultra_perf"])

# Aucun point inventé : le front est un sous-ensemble des candidats
check("front ⊆ candidats (aucun compromis interpolé inventé)", etiq <= {e for e, _ in designs})

# Cas 3 objectifs
sens3 = ("min", "min", "max")
c3 = [("A", (1, 1, 9)), ("B", (2, 2, 5)), ("C", (1, 1, 9))]  # A et C identiques non dominés, B dominé
f3 = {e for e, _ in front(c3, sens3)}
check("3 objectifs : B dominé exclu, A et C gardés", "B" not in f3 and {"A", "C"} <= f3)

print(f"\n=== valide_pareto : {ok}/{total} checks OK ===")
if ok != total: raise SystemExit(1)
