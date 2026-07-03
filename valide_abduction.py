"""VALIDATION abduction.py (Vague 5). FAUX=0 : explication via chemin causal RÉEL ; couvre vérifié ; inexpliquées signalées."""
from __future__ import annotations
from causalite import GrapheCausal
from abduction import explique, meilleure_explication, hypotheses_possibles

ok = 0; total = 0
def check(nom, cond):
    global ok, total; total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}", flush=True)
    if cond: ok += 1
    else: raise AssertionError(nom)

# Modèle causal : grippe -> {fièvre, courbatures} ; intoxication -> {fièvre, nausée}.
g = GrapheCausal()
g.ajoute_cause("grippe", "fièvre")
g.ajoute_cause("grippe", "courbatures")
g.ajoute_cause("intoxication", "fièvre")
g.ajoute_cause("intoxication", "nausée")

check("explique : grippe explique fièvre (chemin causal réel)", explique(g, "grippe", "fièvre"))
check("n'explique PAS : grippe n'explique pas nausée", not explique(g, "grippe", "nausée"))

# Observations {fièvre, courbatures} -> grippe est l'explication parcimonieuse (1 hypothèse)
r = meilleure_explication(g, {"fièvre", "courbatures"})
check("explication de {fièvre, courbatures} = grippe seule", r is not None and r["hypotheses"] == ["grippe"])
check("couvre bien toutes les observations (vérifié)", r["couvre"] == {"fièvre", "courbatures"})
check("aucune observation inexpliquée", r["inexpliquees"] == set())

# Observations {courbatures, nausée} -> nécessite DEUX causes (grippe + intoxication)
r2 = meilleure_explication(g, {"courbatures", "nausée"})
check("explication de {courbatures, nausée} = {grippe, intoxication} (2 hypothèses)",
      r2 is not None and set(r2["hypotheses"]) == {"grippe", "intoxication"})

# FAUX=0 : observation sans cause possible -> signalée inexpliquée (jamais forcée)
g.ajoute_cause("grippe", "fièvre")   # idempotent
r3 = meilleure_explication(g, {"fièvre", "éruption_cutanée"})
check("observation sans cause connue -> inexpliquée signalée (pas d'explication plaquée)",
      "éruption_cutanée" in r3["inexpliquees"])
check("mais la partie explicable l'est (fièvre couverte)", "fièvre" in r3["couvre"])

# hypotheses_possibles ne renvoie que des ancêtres réels
check("hypotheses_possibles = causes réelles des observations",
      set(hypotheses_possibles(g, {"nausée"})) == {"intoxication"})

print(f"\n=== valide_abduction : {ok}/{total} checks OK ===")
if ok != total: raise SystemExit(1)
