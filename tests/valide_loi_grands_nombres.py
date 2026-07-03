"""
VALIDATION de la LOI DES GRANDS NOMBRES MAL COMPRISE (loi_grands_nombres.py). Vérifie : la moyenne par pari → 0 (LGN
tient) MAIS l'écart cumulé |S_n| ≈ √(2n/π) GRANDIT (≈ ×2 quand n ×4) ; la loi de l'arcsinus (temps en tête en U, plus de
masse aux extrêmes qu'au milieu) ; la moyenne reste petite alors que |somme| est grande ; l'ABSTENTION. rng seedé.
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import loi_grands_nombres as L
from loi_grands_nombres import ABSTENTION, ANALYSE

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


st, info = L.analyse(n=10000, T=2500, rng=random.Random(132))

# ─── 1. La moyenne par pari → 0 (LGN tient) ───
print("=== La moyenne par pari → 0 (LGN) ===")
print(f"   moyenne par pari = {info['moyenne']:+.4f}")
check("la moyenne par pari est proche de 0 (la LGN tient)", abs(info["moyenne"]) < 0.01)

# ─── 2. L'écart cumulé |S_n| ≈ √(2n/π) et grandit ───
print("=== L'écart cumulé |S_n| grandit comme √n ===")
print(f"   E|S_n|={info['abs_somme']:.0f} ; √(2n/π)={info['abs_theorique']:.0f}")
check("E|S_n| colle à √(2n/π)", abs(info["abs_somme"] - info["abs_theorique"]) < 0.1 * info["abs_theorique"])
check("l'écart cumulé est GRAND (≫ la moyenne par pari)", info["abs_somme"] > 50)

# ─── 3. |S_n| double quand n quadruple (croissance en √n) ───
print("=== |S_n| ∝ √n ===")
i_petit = L.analyse(n=2500, T=2500, rng=random.Random(2))[1]["abs_somme"]
i_grand = L.analyse(n=10000, T=2500, rng=random.Random(3))[1]["abs_somme"]
print(f"   E|S_n| : n=2500 → {i_petit:.0f} ; n=10000 → {i_grand:.0f} (ratio {i_grand/i_petit:.2f}, attendu 2)")
check("quadrupler n double l'écart cumulé (√n)", abs(i_grand / i_petit - 2.0) < 0.2)

# ─── 4. Loi de l'arcsinus : temps en tête en U ───
print("=== Loi de l'arcsinus : temps en tête en U ===")
print(f"   fraction proche des extrêmes={info['frac_extreme']:.2f} ; proche du milieu={info['frac_milieu']:.2f}")
check("le temps passé en tête est plus souvent EXTRÊME que proche de ½ (arcsinus)", info["frac_extreme"] > info["frac_milieu"])
check("une part substantielle des parties passe >90% ou <10% du temps en tête", info["frac_extreme"] > 0.3)

# ─── 5. Démasque : moyenne petite mais somme grande ───
print("=== Moyenne s'équilibre, somme diverge ===")
check("la moyenne est petite ALORS QUE l'écart cumulé est grand", abs(info["moyenne"]) < 0.01 and info["abs_somme"] > 50)
check("formule signale la sur-confiance du « je vais me refaire »", "sur-confiant" in L.formule((st, info)))

# ─── 6. ABSTENTION ───
print("=== ABSTENTION ===")
check("rng manquant → ABSTENTION", L.analyse(rng=None)[0] == ABSTENTION)
check("n trop petit → ABSTENTION", L.analyse(n=10, rng=random.Random(0))[0] == ABSTENTION)
check("cas valide → ANALYSE", st == ANALYSE)

print(f"\nRÉSULTAT loi_grands_nombres : {ok}/{total}")
assert ok == total
