"""
VALIDATION du PROCESSUS DE POISSON NON-HOMOGÈNE (poisson_nonhomogene.py) — jugée par calibration.py. Sur une
intensité λ(t) connue (pic en milieu de journée), l'intervalle de comptage NON-HOMOGÈNE (taux local, prédictif
Gamma-Poisson) couvre le comptage réel ~confiance, là où l'hypothèse HOMOGÈNE (taux global) SOUS-couvre fortement
dans les fenêtres chargées (et sur-couvre les calmes — taux faux).
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import poisson_nonhomogene as P
from poisson_nonhomogene import ESTIMATION, ABSTENTION
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


T, NB = 24.0, 24


def lam_vrai(t):
    return 2.0 + 8.0 * math.exp(-((t - 14.0) ** 2) / 8.0)      # calme la nuit, pic vers t=14


def _pois(rng, m):
    k = 0
    L = math.exp(-m); p = 1.0
    while True:
        p *= rng.random()
        if p <= L:
            break
        k += 1
    return k


def simule(rng):
    evt = []
    for b in range(NB):
        for _ in range(_pois(rng, lam_vrai(b + 0.5))):
            evt.append(b + rng.random())
    return evt


def vrai_compte(rng, a, b):
    tot = 0
    for bb in range(int(a), int(b)):
        tot += _pois(rng, lam_vrai(bb + 0.5))
    return tot


def couverture(rng, a, b, homogene):
    inter, ver = [], []
    for _ in range(500):
        temps = simule(rng)
        res = P.predit_fenetre(temps, T, NB, a, b, 0.90, homogene=homogene)
        actual = vrai_compte(rng, a, b)
        if res[0] == ESTIMATION:
            inter.append(res[1][1]); ver.append(actual)
    return CAL.verdict_couverture(inter, ver, 0.90)


print("=== Fenêtre CHARGÉE [13,15] : NON-HOMOGÈNE calibré, HOMOGÈNE sur-confiant ===")
rng = random.Random(3)
vN, iN = couverture(rng, 13, 15, False)
vH, iH = couverture(rng, 13, 15, True)
print(f"   NHPP={iN['couverture']:.3f} ({vN}) ; HOMOGÈNE={iH['couverture']:.3f} ({vH})")
check("NHPP : couverture ~0.90 (>=0.86) et NON surconfiant", iN["couverture"] >= 0.86 and vN != SURCONFIANT)
check("HOMOGÈNE : SUR-CONFIANT dans la fenêtre chargée (< 0.50)", vH == SURCONFIANT and iH["couverture"] < 0.50)

print("=== Fenêtre CALME [1,4] : NON-HOMOGÈNE calibré (l'homogène se trompe aussi) ===")
vNc, iNc = couverture(rng, 1, 4, False)
vHc, iHc = couverture(rng, 1, 4, True)
print(f"   NHPP={iNc['couverture']:.3f} ({vNc}) ; HOMOGÈNE={iHc['couverture']:.3f} ({vHc})")
check("NHPP : calme aussi calibré (>=0.86, non surconfiant)", iNc["couverture"] >= 0.86 and vNc != SURCONFIANT)
check("HOMOGÈNE : taux faux aussi en zone calme (verdict != calibre)", vHc != "calibre")

print("=== La largeur de l'intervalle NHPP SUIT l'intensité (chargée > calme) ===")
rng = random.Random(5)
temps = simule(rng)
ch = P.predit_fenetre(temps, T, NB, 13, 15, 0.90, False)
ca = P.predit_fenetre(temps, T, NB, 1, 3, 0.90, False)
larg_ch = ch[1][1][1] - ch[1][1][0]
larg_ca = ca[1][1][1] - ca[1][1][0]
print(f"   largeur chargée={larg_ch} ; calme={larg_ca}")
check("intervalle plus large dans la fenêtre chargée", larg_ch > larg_ca)

print("=== ABSTENTION si trop peu d'événements ===")
st, _, raison = P.predit_fenetre([0.5, 1.5, 2.5], T, NB, 1, 3, 0.90)
print(f"   {st} : {raison}")
check("ABSTENTION sous N_MIN_EVT", st == ABSTENTION)

print(f"\nRÉSULTAT poisson_nonhomogene : {ok}/{total}")
assert ok == total
