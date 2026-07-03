"""
VALIDATION de la PRÉVISION AUTO-RÉGRESSIVE (serie_autoregressive.py) — jugée par calibration.py. Sur un AR(1) connu,
l'intervalle à h pas (variance d'erreur qui croît avec l'horizon) couvre la vraie valeur future ~confiance à CHAQUE
horizon, là où l'intervalle NAÏF (largeur fixe d'un seul pas) sous-couvre aux horizons lointains (sur-confiance).
"""
from __future__ import annotations

import random

from garde_ressources import borne
import serie_autoregressive as S
from serie_autoregressive import ESTIMATION, ABSTENTION
import calibration as CAL
from calibration import SURCONFIANT

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


PHI, C, SIG = 0.7, 1.0, 1.0
MU = C / (1.0 - PHI)


def simule(rng, T):
    s = [MU]
    for _ in range(T):
        s.append(C + PHI * s[-1] + rng.gauss(0, SIG))
    return s


def couverture(rng, h, naif):
    inter, ver = [], []
    for _ in range(600):
        s = simule(rng, 120 + h)
        res = S.prevoit(s[:120], h, 0.90, naif=naif)
        if res[0] == ESTIMATION:
            inter.append(res[1][1]); ver.append(s[120 + h - 1])
    return CAL.verdict_couverture(inter, ver, 0.90)


print("=== Couverture par horizon : AR calibré, NAÏF sur-confiant aux horizons lointains ===")
rng = random.Random(1)
for h in (1, 5, 12):
    vA, iA = couverture(rng, h, False)
    vN, iN = couverture(rng, h, True)
    print(f"   h={h:2d} : AR={iA['couverture']:.3f} ({vA}) ; NAÏF={iN['couverture']:.3f} ({vN})")
    check(f"h={h} : AR couvre ~0.90 (>=0.85) et NON surconfiant", iA["couverture"] >= 0.85 and vA != SURCONFIANT)
    if h >= 5:
        check(f"h={h} : NAÏF SUR-CONFIANT (largeur fixe sous-couvre, <0.82)", vN == SURCONFIANT and iN["couverture"] < 0.82)

print("=== La largeur de l'intervalle CROÎT avec l'horizon (puis sature) ===")
rng = random.Random(2)
mod = S.ar1_fit(simule(rng, 400))
l1 = S.prevoit_h(mod, 1, 0.90); l5 = S.prevoit_h(mod, 5, 0.90); l20 = S.prevoit_h(mod, 20, 0.90)
w1 = l1[1][1] - l1[1][0]; w5 = l5[1][1] - l5[1][0]; w20 = l20[1][1] - l20[1][0]
print(f"   largeur h=1:{w1:.2f}  h=5:{w5:.2f}  h=20:{w20:.2f}")
check("largeur croissante h1 < h5 < h20", w1 < w5 < w20)

print("=== Estimation cohérente de φ ===")
print(f"   φ̂={mod['phi']:.3f} (vrai {PHI})")
check("φ estimé proche du vrai (|φ̂−0.7|<0.1)", abs(mod["phi"] - PHI) < 0.1)

print("=== ABSTENTION si série trop courte ===")
st, _, raison = S.prevoit([1.0, 2.0, 1.5, 2.5, 2.0], 3, 0.90)
print(f"   {st} : {raison}")
check("ABSTENTION sous N_MIN points", st == ABSTENTION)

print(f"\nRÉSULTAT serie_autoregressive : {ok}/{total}")
assert ok == total
