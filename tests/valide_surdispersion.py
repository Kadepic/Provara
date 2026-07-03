"""
VALIDATION de la SUR-DISPERSION (surdispersion.py) — jugée par calibration.py. Sur des comptages sur-dispersés connus
(mélange Poisson-Gamma = NegBin), l'intervalle NegBin couvre un nouveau comptage ~confiance, là où l'intervalle
Poisson SOUS-couvre. Le test détecte la sur-dispersion ; sur des comptages Poisson purs, NegBin se réduit à Poisson.
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import surdispersion as D
from surdispersion import ESTIMATION, ABSTENTION
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


def tire_negbin(rng, mu, phi):
    p = 1.0 / phi
    r = mu / (phi - 1.0)
    lam = rng.gammavariate(r, (1 - p) / p)
    k = 0; L = math.exp(-lam); q = 1.0
    while True:
        q *= rng.random()
        if q <= L:
            break
        k += 1
    return k


def tire_poisson(rng, mu):
    k = 0; L = math.exp(-mu); q = 1.0
    while True:
        q *= rng.random()
        if q <= L:
            break
        k += 1
    return k


MU, PHI = 8.0, 3.0

print("=== Comptages SUR-DISPERSÉS : NegBin calibré, Poisson sous-couvre ===")
rng = random.Random(1)
inb, vnb, ipo, vpo = [], [], [], []
for _ in range(400):
    ech = [tire_negbin(rng, MU, PHI) for _ in range(60)]
    nb = D.intervalle_negbin(ech, 0.90)
    po = D.intervalle_poisson(ech, 0.90)
    nouveau = tire_negbin(rng, MU, PHI)
    if nb[0] == ESTIMATION:
        inb.append(nb[1][1]); vnb.append(nouveau)
    ipo.append(po[1]); vpo.append(nouveau)
vN, iN = CAL.verdict_couverture(inb, vnb, 0.90)
vP, iP = CAL.verdict_couverture(ipo, vpo, 0.90)
print(f"   NegBin={iN['couverture']:.3f} ({vN}) ; Poisson={iP['couverture']:.3f} ({vP})")
check("NegBin : couverture ~0.90 (>=0.86) et NON surconfiant", iN["couverture"] >= 0.86 and vN != SURCONFIANT)
check("Poisson : SUR-CONFIANT sur comptages sur-dispersés (< 0.80)", vP == SURCONFIANT and iP["couverture"] < 0.80)

print("=== Le TEST détecte la sur-dispersion ===")
rng = random.Random(2)
ech = [tire_negbin(rng, MU, PHI) for _ in range(200)]
phi, z, sur = D.test_surdispersion(ech)
print(f"   φ̂={phi:.2f} ; z={z:.1f} ; surdisperse={sur}")
check("sur-dispersion détectée (z>2, φ̂>1.5)", sur and phi > 1.5)

print("=== Comptages POISSON purs : pas de fausse alarme, couverture OK ===")
rng = random.Random(3)
ipp, vpp = [], []
faux_pos = 0
for _ in range(200):
    ech = [tire_poisson(rng, MU) for _ in range(60)]
    _, z, sur = D.test_surdispersion(ech)
    faux_pos += sur
    nb = D.intervalle_negbin(ech, 0.90)
    nouveau = tire_poisson(rng, MU)
    if nb[0] == ESTIMATION:
        ipp.append(nb[1][1]); vpp.append(nouveau)
vPP, iPP = CAL.verdict_couverture(ipp, vpp, 0.90)
print(f"   faux positifs du test={faux_pos}/200 ; couverture NegBin(≈Poisson)={iPP['couverture']:.3f} ({vPP})")
check("peu de fausses alarmes de sur-dispersion (<15/200)", faux_pos < 15)
check("sur Poisson pur, l'intervalle reste calibré (>=0.86, non surconfiant)", iPP["couverture"] >= 0.86 and vPP != SURCONFIANT)

print("=== ABSTENTION si trop peu de données ===")
st, _, raison = D.intervalle_negbin([1, 2, 3, 2, 1], 0.90)
print(f"   {st} : {raison}")
check("ABSTENTION sous N_MIN", st == ABSTENTION)

print(f"\nRÉSULTAT surdispersion : {ok}/{total}")
assert ok == total
