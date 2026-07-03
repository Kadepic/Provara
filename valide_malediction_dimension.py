"""
VALIDATION de la MALÉDICTION DE LA DIMENSION (malediction_dimension.py). Vérifie : le contraste relatif des distances
DÉCROÎT vers 0 avec d ; D_min/D_max → 1 (plus proche ≈ plus lointain, kNN sans valeur) ; la norme gaussienne se
concentre à √d avec un écart relatif → 0 (coquille fine) ; basse dimension = fort contraste (honnêteté) ; l'ABSTENTION.
Pur Python, rng seedé.
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import malediction_dimension as MD
from malediction_dimension import ABSTENTION, ANALYSE

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


st, info = MD.analyse(dims=(2, 10, 100, 1000), rng=random.Random(122))
courbe = dict(info["courbe"])

# ─── 1. Le contraste relatif décroît vers 0 ───
print("=== Concentration des distances ===")
contrastes = [courbe[d]["contraste"] for d in (2, 10, 100, 1000)]
print(f"   contraste : {[round(c,3) for c in contrastes]}")
check("le contraste relatif décroît strictement avec d", contrastes[0] > contrastes[1] > contrastes[2] > contrastes[3])
check("à très haute dimension, le contraste est quasi nul", contrastes[-1] < 0.2)

# ─── 2. D_min/D_max → 1 (plus proche ≈ plus lointain) ───
print("=== Plus proche ≈ plus lointain ===")
ratios = [courbe[d]["ratio_min_max"] for d in (2, 10, 100, 1000)]
print(f"   D_min/D_max : {[round(r,3) for r in ratios]}")
check("D_min/D_max croît vers 1 avec d", ratios[0] < ratios[1] < ratios[2] < ratios[3])
check("à d=1000, le plus proche voisin est presque aussi loin que le plus lointain", ratios[-1] > 0.85)

# ─── 3. La norme gaussienne se concentre à √d ───
print("=== Coquille gaussienne à √d ===")
for d in (100, 1000):
    m = courbe[d]
    print(f"   d={d}: norme moyenne={m['norme_moy']:.2f} (√d={m['sqrt_d']:.2f})")
    check(f"la norme gaussienne ≈ √d à d={d}", abs(m["norme_moy"] - m["sqrt_d"]) < 0.3)

# ─── 4. L'écart relatif de la norme → 0 (coquille fine) ───
print("=== Coquille de plus en plus fine ===")
ecarts = [courbe[d]["ecart_relatif"] for d in (2, 10, 100, 1000)]
print(f"   écart relatif de la norme : {[round(e,3) for e in ecarts]}")
check("l'écart relatif de la norme décroît avec d (coquille fine)", ecarts[0] > ecarts[2] > ecarts[3])
check("à d=1000, presque tous les points sont à la même distance du centre", ecarts[-1] < 0.05)

# ─── 5. Honnêteté : basse dimension = fort contraste ───
print("=== Honnêteté : basse dimension informative ===")
check("à d=2, le contraste des distances est fort (distances informatives)", courbe[2]["contraste"] > 3.0)
check("formule signale la sur-confiance du kNN en haute dimension", "sur-confiant" in MD.formule((st, info)))

# ─── 6. ABSTENTION ───
print("=== ABSTENTION ===")
check("rng manquant → ABSTENTION", MD.analyse(rng=None)[0] == ABSTENTION)
check("dimension < 1 → ABSTENTION", MD.analyse(dims=(0,), rng=random.Random(0))[0] == ABSTENTION)
check("cas valide → ANALYSE", st == ANALYSE)

print(f"\nRÉSULTAT malediction_dimension : {ok}/{total}")
assert ok == total
