"""
VALIDATION de la PROPAGATION D'INCERTITUDE (propagation.py) — l'intervalle propagé est-il CALIBRÉ ? Jugé par
calibration.py. Monde connu : les entrées suivent leurs lois déclarées ; la vraie sortie z = f(entrées tirées) doit
tomber dans l'intervalle propagé ~`confiance` du temps.

Cœur : la propagation MONTE-CARLO reste calibrée même pour un f NON LINÉAIRE (z=x·y, z=x²), là où la propagation
au PREMIER ORDRE devient SUR-CONFIANTE (z=x² en x̄=0 : gradient nul -> σ_z≈0 -> intervalle quasi vide = mensonge).
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import propagation as PR
from propagation import ESTIMATION, ABSTENTION
import calibration as CAL
from calibration import CALIBRE, SURCONFIANT

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


def couverture(f, entrees, methode, confiance, M, graine):
    """Construit l'intervalle propagé une fois, tire M vérités z=f(entrées échantillonnées), juge la couverture."""
    if methode == "mc":
        st, val, _ = PR.propage_mc(f, entrees, confiance, n=40000, seed=7)
    else:
        st, val, _ = PR.intervalle_lineaire(f, [m for (m, _) in entrees], [s for (_, s) in entrees], confiance)
    if st != ESTIMATION:
        return None
    inter = val[1]
    rng = random.Random(graine)
    verites = [f(*[rng.gauss(m, s) for (m, s) in entrees]) for _ in range(M)]
    return CAL.verdict_couverture([inter] * M, verites, confiance)


print("=== f LINÉAIRE (z=2x+3y) : MC calibré + accord avec le 1er ordre ===")
lin = lambda x, y: 2 * x + 3 * y
vmc, imc = couverture(lin, [(5.0, 1.0), (2.0, 0.5)], "mc", 0.90, 4000, graine=1)
print("   MC :", CAL.formule((vmc, imc), "couverture"))
check(f"MC @90% (linéaire) -> CALIBRE (couv={imc['couverture']:.3f})", vmc == CALIBRE)
# σ analytique = sqrt((2·1)² + (3·0.5)²) = sqrt(4+2.25)
_, (zl, sl), _ = PR.propage_lineaire(lin, [5.0, 2.0], [1.0, 0.5])
check(f"1er ordre : σ_z = {sl:.4f} == analytique {math.sqrt(4+2.25):.4f}", abs(sl - math.sqrt(6.25)) < 1e-3)
vlin, ilin = couverture(lin, [(5.0, 1.0), (2.0, 0.5)], "lineaire", 0.90, 4000, graine=2)
check(f"1er ordre @90% (linéaire) -> CALIBRE (couv={ilin['couverture']:.3f})", vlin == CALIBRE)

print("=== f NON LINÉAIRE z=x·y : MC reste CALIBRÉ ===")
prod = lambda x, y: x * y
vp, ip = couverture(prod, [(0.0, 1.0), (0.0, 1.0)], "mc", 0.90, 5000, graine=3)
print("   MC :", CAL.formule((vp, ip), "couverture"))
check(f"MC @90% (z=x·y) -> CALIBRE (couv={ip['couverture']:.3f})", vp == CALIBRE)

print("=== f NON LINÉAIRE z=x² en x̄=0 : MC CALIBRÉ, 1er ordre SUR-CONFIANT (démasqué) ===")
carre = lambda x: x * x
vmc2, imc2 = couverture(carre, [(0.0, 1.0)], "mc", 0.90, 5000, graine=4)
vlin2, ilin2 = couverture(carre, [(0.0, 1.0)], "lineaire", 0.90, 5000, graine=4)
print("   MC       :", CAL.formule((vmc2, imc2), "couverture"))
print("   1er ordre:", CAL.formule((vlin2, ilin2), "couverture"))
check(f"MC @90% (z=x²) -> CALIBRE (couv={imc2['couverture']:.3f})", vmc2 == CALIBRE)
check(f"1er ordre @90% (z=x²) -> SURCONFIANT (σ≈0, couv={ilin2['couverture']:.3f})", vlin2 == SURCONFIANT)

print("=== MONOTONIE : 99% plus large que 90% (MC) ===")
_, (_, (b90, h90)), _ = PR.propage_mc(prod, [(1.0, 0.5), (2.0, 0.5)], 0.90, n=40000, seed=9)
_, (_, (b99, h99)), _ = PR.propage_mc(prod, [(1.0, 0.5), (2.0, 0.5)], 0.99, n=40000, seed=9)
check("intervalle MC 99% plus large que 90%", (h99 - b99) > (h90 - b90))

print("=== ABSTENTION : incertitude invalide ===")
check("σ<0 -> ABSTENTION (MC)", PR.propage_mc(prod, [(1.0, -0.5), (2.0, 0.5)])[0] == ABSTENTION)
check("σ<0 -> ABSTENTION (1er ordre)", PR.propage_lineaire(prod, [1.0, 2.0], [-0.5, 0.5])[0] == ABSTENTION)

print("=== ACCORD MC ↔ 1er ordre sur un cas linéaire (cohérence des deux moteurs) ===")
_, (_, (lb, lh)), _ = PR.intervalle_lineaire(lin, [5.0, 2.0], [1.0, 0.5], 0.90)
_, (_, (mb, mh)), _ = PR.propage_mc(lin, [(5.0, 1.0), (2.0, 0.5)], 0.90, n=40000, seed=11)
check("largeurs MC et 1er ordre proches (<5%) sur f linéaire", abs((mh - mb) - (lh - lb)) / (lh - lb) < 0.05)

print(f"\nPROPAGATION VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
