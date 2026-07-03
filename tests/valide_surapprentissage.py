"""
VALIDATION du SUR-APPRENTISSAGE (surapprentissage.py). Vérifie : l'erreur d'entraînement décroît avec la complexité
tandis que l'erreur de test EXPLOSE (overfitting) ; l'écart test − train croît avec la complexité ; le hold-out choisit
une faible complexité (la bonne) ; à la bonne complexité train ≈ test (honnêteté) ; l'ABSTENTION. Pur Python, rng seedé.
"""
from __future__ import annotations

import random

from garde_ressources import borne
import surapprentissage as SA
from surapprentissage import ABSTENTION, ANALYSE

borne()
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


st, info = SA.analyse(degres=(1, 2, 3, 5, 7, 9), n_train=15, rng=random.Random(131))
courbe = dict(info["courbe"])

# ─── 1. L'erreur d'entraînement décroît avec la complexité ───
print("=== Erreur d'entraînement ↓ avec la complexité ===")
trains = [courbe[d]["mse_train"] for d in (1, 2, 3, 5, 7, 9)]
print(f"   MSE train : {[round(t,3) for t in trains]}")
check("l'erreur d'entraînement décroît (monotone) avec le degré", all(trains[i] >= trains[i + 1] - 1e-9 for i in range(len(trains) - 1)))

# ─── 2. L'erreur de test explose (overfitting) ───
print("=== Erreur de test : overfitting ===")
tests = [courbe[d]["mse_test"] for d in (1, 2, 3, 5, 7, 9)]
print(f"   MSE test : {[round(t,2) for t in tests]}")
check("l'erreur de test au degré élevé est BIEN pire qu'au degré faible", tests[-1] > 100 * tests[0])
check("le meilleur test est à faible complexité (pas le degré max)", tests.index(min(tests)) <= 2)

# ─── 3. L'écart test − train (optimisme) croît avec la complexité ───
print("=== L'optimisme (test − train) croît avec la complexité ===")
gap_bas = courbe[1]["mse_test"] - courbe[1]["mse_train"]
gap_haut = courbe[9]["mse_test"] - courbe[9]["mse_train"]
print(f"   écart test−train : degré 1 = {gap_bas:.2f} ; degré 9 = {gap_haut:.1f}")
check("l'écart test − train est bien plus grand au degré élevé", gap_haut > gap_bas + 100)

# ─── 4. Le hold-out choisit une faible complexité ───
print("=== Le hold-out choisit la bonne complexité ===")
print(f"   degré choisi par hold-out = {info['degre_choisi_holdout']}")
check("le hold-out sélectionne un degré faible (proche de la vraie complexité)", info["degre_choisi_holdout"] <= 3)

# ─── 5. Honnêteté : à la bonne complexité, train ≈ test ───
print("=== Honnêteté : à la bonne complexité, train ≈ test ===")
d_bon = info["degre_choisi_holdout"]
ecart_bon = abs(courbe[d_bon]["mse_test"] - courbe[d_bon]["mse_train"])
print(f"   degré {d_bon} : train={courbe[d_bon]['mse_train']:.3f} ; test={courbe[d_bon]['mse_test']:.3f}")
check("à la complexité choisie, train et test sont proches (généralise bien)", ecart_bon < 0.3)
check("formule signale la sur-confiance de l'ajustement en échantillon", "sur-confiant" in SA.formule((st, info)))

# ─── 6. ABSTENTION ───
print("=== ABSTENTION ===")
check("rng manquant → ABSTENTION", SA.analyse(rng=None)[0] == ABSTENTION)
check("trop peu de données → ABSTENTION", SA.analyse(n_train=4, rng=random.Random(0))[0] == ABSTENTION)
check("cas valide → ANALYSE", st == ANALYSE)

print(f"\nRÉSULTAT surapprentissage : {ok}/{total}")
assert ok == total
