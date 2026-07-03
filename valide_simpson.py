"""
VALIDATION du PARADOXE DE SIMPSON (simpson.py). Vérifie les taux, la DÉTECTION du renversement (A gagne chaque strate
mais B gagne globalement), que la cause est l'allocation déséquilibrée (A concentré dans la strate difficile), le
DÉMASQUE (gagnant stratifié ≠ gagnant agrégé = sur-confiance si on tranche d'un seul niveau), l'absence de renversement
sous allocation équilibrée, et l'ABSTENTION. Pur Python, léger.
"""
from __future__ import annotations

import random

from garde_ressources import borne
import simpson as SP
from simpson import ABSTENTION, SIMPSON, COHERENT

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


# Calculs rénaux (classique)
D = {"A": {"petit": (81, 87), "gros": (192, 263)},
     "B": {"petit": (234, 270), "gros": (55, 80)}}

# ─── 1. Taux ───
print("=== Taux ===")
check("taux(81,87) ≈ 0.931", abs(SP.taux(81, 87) - 81 / 87) < 1e-12)
check("agrégat A = 273/350", abs(SP.taux_agrege(D, "A") - 273 / 350) < 1e-12)

# ─── 2. Détection du renversement ───
print("=== Détection du renversement de Simpson ===")
st, info = SP.analyse(D, "A", "B")
print(f"   gagnant strates={info['gagnant_strates']} ; gagnant agrégé={info['gagnant_agrege']}")
check("A gagne dans CHAQUE strate", info["gagnant_strates"] == "A")
check("B gagne globalement (renversement)", info["gagnant_agrege"] == "B")
check("verdict = PARADOXE DE SIMPSON", st == SIMPSON)

# ─── 3. Cause : allocation déséquilibrée (A concentré dans la strate difficile) ───
print("=== Cause : A concentré dans la strate difficile (gros) ===")
a_gros = D["A"]["gros"][1] / (D["A"]["gros"][1] + D["A"]["petit"][1])
b_gros = D["B"]["gros"][1] / (D["B"]["gros"][1] + D["B"]["petit"][1])
print(f"   part 'gros' : A={a_gros:.2f} vs B={b_gros:.2f} ; taux de succès 'gros' < 'petit'")
check("A est sur-représenté dans la strate difficile", a_gros > b_gros + 0.3)
check("la strate 'gros' a un taux de succès plus faible (difficile)", SP.taux(192, 263) < SP.taux(81, 87) and SP.taux(55, 80) < SP.taux(234, 270))

# ─── 4. DÉMASQUE : conclusions contradictoires selon le niveau ───
print("=== Mode d'échec : agrégat vs strates contradictoires ===")
check("le gagnant stratifié (A) CONTREDIT le gagnant agrégé (B) = sur-confiance si on tranche", info["gagnant_strates"] != info["gagnant_agrege"])
check("formule signale le paradoxe", "SIMPSON" in SP.formule((st, info)))

# ─── 5. Allocation équilibrée → pas de renversement ───
print("=== Allocation équilibrée → pas de renversement ===")
E = {"A": {"petit": (90, 100), "gros": (70, 100)},
     "B": {"petit": (85, 100), "gros": (65, 100)}}
st2, info2 = SP.analyse(E, "A", "B")
print(f"   équilibré : strates={info2['gagnant_strates']}, agrégé={info2['gagnant_agrege']}")
check("équilibré : A gagne strates ET agrégat (cohérent)", info2["gagnant_strates"] == "A" and info2["gagnant_agrege"] == "A")
check("verdict COHERENT (pas de renversement)", st2 == COHERENT)

# ─── 6. Robustesse : profils aléatoires équilibrés → cohérents ───
print("=== Profils aléatoires équilibrés → cohérents (pas de faux renversement) ===")
rng = random.Random(87)
faux = 0
for _ in range(500):
    # même taille par strate pour A et B → pas de confusion d'allocation
    n = rng.randint(20, 100)
    pa1, pa2 = rng.uniform(0.5, 0.9), rng.uniform(0.3, 0.7)
    pb1, pb2 = pa1 - 0.1, pa2 - 0.1     # A domine dans chaque strate
    R = {"A": {"s1": (round(pa1 * n), n), "s2": (round(pa2 * n), n)},
         "B": {"s1": (round(pb1 * n), n), "s2": (round(pb2 * n), n)}}
    if SP.analyse(R, "A", "B")[0] == SIMPSON:
        faux += 1
check("allocation équilibrée → jamais de renversement (0 faux Simpson)", faux == 0)

# ─── 7. ABSTENTION ───
print("=== ABSTENTION ===")
st3, _ = SP.analyse({"A": {"s": (1, 2)}}, "A", "B")
st4, _ = SP.analyse({"A": {"s1": (1, 2)}, "B": {"s2": (1, 2)}}, "A", "B")
check("traitement manquant → ABSTENTION", st3 == ABSTENTION)
check("strates différentes → ABSTENTION", st4 == ABSTENTION)
st5, _ = SP.analyse(D, "A", "B")
check("cas valide → SIMPSON ou COHERENT", st5 in (SIMPSON, COHERENT))

print(f"\nRÉSULTAT simpson : {ok}/{total}")
assert ok == total
