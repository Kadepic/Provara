"""
VALIDATION du PARADOXE DE SAINT-PÉTERSBOURG (saint_petersbourg.py). Vérifie la loi des gains, la divergence de
l'espérance, la non-convergence de la moyenne d'échantillon, que le prix sous utilité log est FINI/petit et ≈ log₂(W),
que le casino à bankroll fini donne une valeur finie ≈ log₂(W), le DÉMASQUE (prix fini ≪ espérance infinie), et
l'ABSTENTION. Pur Python, rng seedé.
"""
from __future__ import annotations

import math
import random
import statistics

from garde_ressources import borne
import saint_petersbourg as SP
from saint_petersbourg import ABSTENTION, PRIX

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


rng = random.Random(91)

# ─── 1. Loi des gains : P(gain=2ⁿ) = 2⁻ⁿ ───
print("=== Loi des gains ===")
N = 200000
gains = [SP.paiement(rng) for _ in range(N)]
p2 = sum(1 for g in gains if g == 2) / N
p4 = sum(1 for g in gains if g == 4) / N
print(f"   P(gain=2)={p2:.3f} (≈0.5) ; P(gain=4)={p4:.3f} (≈0.25)")
check("P(gain=2) ≈ 0.5", abs(p2 - 0.5) < 0.01)
check("P(gain=4) ≈ 0.25", abs(p4 - 0.25) < 0.01)

# ─── 2. Espérance tronquée diverge ───
print("=== Espérance tronquée → ∞ ===")
check("esperance_tronquee(n) = n (croît sans borne)", SP.esperance_tronquee(10) == 10 and SP.esperance_tronquee(40) == 40)

# ─── 3. Moyenne d'échantillon : pas de convergence (croît avec n) ───
print("=== Moyenne d'échantillon croît avec n (pas de convergence) ===")
def med_moy(n, reps=25):
    return statistics.median(SP.moyenne_jeux(rng, n) for _ in range(reps))
m1, m2 = med_moy(300), med_moy(30000)
print(f"   médiane des moyennes : n=300 → {m1:.1f} ; n=30000 → {m2:.1f}")
check("la moyenne d'échantillon croît avec n (ne converge pas)", m2 > m1 + 2)

# ─── 4. Prix sous utilité log : FINI, petit, ≈ log₂(W) ───
print("=== Prix sous utilité log : fini et ≈ log₂(W) ===")
for W in (100, 10000, 1000000):
    p = SP.equivalent_certain_log(W)
    print(f"   W={W:>7} : prix={p:.2f} (log₂(W)={math.log2(W):.1f})")
    check(f"prix fini et raisonnable pour W={W} (∈ [log₂W−3, log₂W+3])", abs(p - math.log2(W)) < 3)
check("le prix croît avec la fortune mais LENTEMENT (log)", SP.equivalent_certain_log(1000000) < 4 * SP.equivalent_certain_log(100))

# ─── 5. Casino à bankroll fini : valeur finie ≈ log₂(W) ───
print("=== Casino fini : valeur finie ≈ log₂(W) ===")
vc = SP.valeur_casino_fini(10000)
print(f"   valeur casino (W=10000) = {vc:.2f} (log₂=13.3)")
check("valeur casino finie ≈ log₂(W)", abs(vc - math.log2(10000)) < 2)
check("prix log ≈ valeur casino fini (deux résolutions concordent)", abs(SP.equivalent_certain_log(10000) - vc) < 1.5)

# ─── 6. DÉMASQUE : prix fini ≪ espérance infinie ───
print("=== Mode d'échec : espérance infinie vs prix fini ===")
st, info = SP.analyse(1000)
print(f"   espérance={info['esperance']} ; prix log={info['prix_log']:.2f}")
check("l'espérance est infinie mais le prix rationnel est fini et petit", math.isinf(info["esperance"]) and info["prix_log"] < 20)
check("formule signale la sur-confiance de l'espérance", "sur-confiant" in SP.formule((st, info)))

# ─── 7. ABSTENTION ───
print("=== ABSTENTION ===")
st1, _ = SP.analyse(0)
st2, _ = SP.analyse(-5)
check("fortune = 0 → ABSTENTION", st1 == ABSTENTION)
check("fortune < 0 → ABSTENTION", st2 == ABSTENTION)
st3, _ = SP.analyse(500)
check("cas valide → PRIX", st3 == PRIX)

print(f"\nRÉSULTAT saint_petersbourg : {ok}/{total}")
assert ok == total
