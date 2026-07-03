"""
VALIDATION du PARADOXE DE BOREL-KOLMOGOROV (borel_kolmogorov.py). Vérifie : la bande de longitude donne une latitude
∝ cos θ (concentrée à l'équateur, E|θ|≈π/2−1) ; la bande perpendiculaire donne une latitude UNIFORME (E|θ|≈π/4) ; les
deux lois sur le MÊME grand cercle DIFFÈRENT ; chacune colle à sa théorie ; le conditionnement non spécifié → ABSTENTION.
Pur Python, rng seedé.
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import borel_kolmogorov as BK
from borel_kolmogorov import ABSTENTION, ANALYSE

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


N = 2000000

# ─── 1. Bande de longitude → ∝ cos θ ───
print("=== Bande de longitude → loi ∝ cos θ ===")
e_lon = BK.e_abs_latitude("longitude", N, random.Random(120))
print(f"   E|θ|={e_lon:.3f} ; théorie π/2−1={math.pi/2-1:.3f}")
check("la bande de longitude donne E|θ| ≈ π/2−1 (cos-pondérée)", abs(e_lon - (math.pi / 2 - 1)) < 0.02)
check("la latitude est concentrée près de l'équateur (E|θ| < π/4)", e_lon < math.pi / 4 - 0.1)

# ─── 2. Bande perpendiculaire → uniforme ───
print("=== Bande perpendiculaire → loi uniforme ===")
e_perp = BK.e_abs_latitude("perpendiculaire", N, random.Random(2))
print(f"   E|θ|={e_perp:.3f} ; théorie π/4={math.pi/4:.3f}")
check("la bande perpendiculaire donne E|θ| ≈ π/4 (uniforme)", abs(e_perp - math.pi / 4) < 0.02)

# ─── 3. Les deux lois DIFFÈRENT sur le même grand cercle ───
print("=== Même grand cercle, deux lois différentes ===")
print(f"   E|θ| longitude={e_lon:.3f} vs perpendiculaire={e_perp:.3f}")
check("les deux procédures donnent des lois conditionnelles NETTEMENT différentes", abs(e_lon - e_perp) > 0.15)

# ─── 4. Façade & théorie ───
print("=== Façade ===")
st, info = BK.analyse("longitude", N, random.Random(3))
check("la façade renvoie ANALYSE pour une procédure spécifiée", st == ANALYSE)
check("E|θ| simulé colle à la théorie de la procédure", abs(info["e_abs"] - info["theorique"]) < 0.02)
check("formule signale la sur-confiance de « la » loi conditionnelle", "sur-confiant" in BK.formule((st, info)))

# ─── 5. Conditionnement non spécifié → ABSTENTION ───
print("=== Conditionnement non spécifié → ABSTENTION ===")
check("procédure=None → ABSTENTION (loi non définie sur mesure nulle)", BK.analyse(None)[0] == ABSTENTION)
check("procédure inconnue → ABSTENTION", BK.analyse("autre", rng=random.Random(0))[0] == ABSTENTION)
check("rng manquant → ABSTENTION", BK.analyse("longitude", rng=None)[0] == ABSTENTION)

print(f"\nRÉSULTAT borel_kolmogorov : {ok}/{total}")
assert ok == total
