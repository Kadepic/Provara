"""
VALIDATION de l'EFFET D'ANCRAGE (ancrage.py). Vérifie : l'estimation ancrée est fortement CONTAMINÉE par une ancre
aléatoire non pertinente (corrélation ≫ 0) tandis que l'estimateur libre ne l'est pas ; les ancres hautes déplacent
l'estimation vers le haut ; l'erreur quadratique de l'estimateur ancré est plus grande ; la contamination croît quand
l'ajustement est plus insuffisant ; HONNÊTETÉ : α=1 supprime la contamination ; l'ABSTENTION. Pur Python, rng seedé.
"""
from __future__ import annotations

import random

from garde_ressources import borne
import ancrage as AN
from ancrage import ABSTENTION, ANALYSE

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


st, info = AN.analyse(theta=100.0, alpha=0.6, n=8000, rng=random.Random(125))

# ─── 1. Contamination par l'ancre ───
print("=== Contamination par une ancre non pertinente ===")
print(f"   corr(ancrée, ancre)={info['contamination']:.3f} ; corr(libre, ancre)={info['contamination_libre']:.3f}")
check("l'estimation ancrée est fortement corrélée à l'ancre aléatoire", info["contamination"] > 0.7)
check("l'estimateur libre n'est PAS contaminé (corr ≈ 0)", abs(info["contamination_libre"]) < 0.05)

# ─── 2. Déplacement vers l'ancre ───
print("=== Déplacement de l'estimation vers l'ancre ===")
print(f"   écart estimation (ancres hautes − basses) = {info['ecart_haute_basse']:.1f}")
check("les ancres hautes tirent l'estimation au-dessus des ancres basses", info["ecart_haute_basse"] > 20)

# ─── 3. L'ancre dégrade l'erreur quadratique ───
print("=== L'ancre dégrade la précision ===")
print(f"   MSE libre={info['mse_libre']:.0f} ; MSE ancrée={info['mse_ancre']:.0f}")
check("l'estimateur ancré a une erreur quadratique plus grande que le libre", info["mse_ancre"] > info["mse_libre"])

# ─── 4. La contamination croît avec l'insuffisance de l'ajustement ───
print("=== Contamination ↑ quand l'ajustement ↓ ===")
c_fort = AN.analyse(alpha=0.8, n=8000, rng=random.Random(2))[1]["contamination"]
c_faible = AN.analyse(alpha=0.3, n=8000, rng=random.Random(3))[1]["contamination"]
print(f"   contamination : α=0.8 → {c_fort:.2f} ; α=0.3 → {c_faible:.2f}")
check("plus l'ajustement est insuffisant (α petit), plus la contamination est forte", c_faible > c_fort)

# ─── 5. Honnêteté : ajustement complet (α=1) supprime la contamination ───
print("=== Honnêteté : α=1 supprime l'ancrage ===")
info1 = AN.analyse(alpha=1.0, n=8000, rng=random.Random(4))[1]
print(f"   α=1 : contamination={info1['contamination']:.3f}")
check("avec ajustement complet, l'ancre n'a plus d'effet (corr ≈ 0)", abs(info1["contamination"]) < 0.05)
check("formule signale la sur-confiance de l'estimation ancrée", "sur-confiant" in AN.formule((st, info)))

# ─── 6. ABSTENTION ───
print("=== ABSTENTION ===")
check("rng manquant → ABSTENTION", AN.analyse(rng=None)[0] == ABSTENTION)
check("n trop petit → ABSTENTION", AN.analyse(n=10, rng=random.Random(0))[0] == ABSTENTION)
check("cas valide → ANALYSE", st == ANALYSE)

print(f"\nRÉSULTAT ancrage : {ok}/{total}")
assert ok == total
