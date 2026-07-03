"""
VALIDATION de l'IC BOOTSTRAP (bootstrap.py) — jugé par calibration.py. Pour une statistique sans formule simple (la
MÉDIANE), l'IC NAÏF qui plaque l'erreur-type de la MOYENNE (s/√n) est trop étroit → SUR-CONFIANT ; le bootstrap
(percentile & BCa) capte la variabilité RÉELLE de la statistique → couverture ≈ nominal. Sur la MOYENNE elle-même (où la
formule naïve est correcte), les trois coïncident (le défaut est spécifique aux statistiques à variabilité ≠ moyenne).
Le BCa respecte aussi les bornes naturelles (corrélation ∈ [−1,1]).
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import bootstrap as BS
from bootstrap import ESTIMATION, ABSTENTION
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


def mediane(xs):
    s = sorted(xs); n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def moyenne(xs):
    return sum(xs) / len(xs)


NOM = 0.90
N_DATA = 700
B = 700
n = 40

print("=== MÉDIANE (n=40, vraie=0) : IC naïf (SE moyenne) SUR-CONFIANT, bootstrap CALIBRÉ ===")
rng = random.Random(4)
iv_naif, iv_pct, iv_bca, ver = [], [], [], []
for s in range(N_DATA):
    data = [rng.gauss(0.0, 1.0) for _ in range(n)]
    boot = BS.repliques(data, mediane, B, random.Random(1000 + s))
    iv_naif.append(BS.ic_naif_moyenne(data, mediane, NOM))
    iv_pct.append(BS.ic_percentile(boot, NOM))
    iv_bca.append(BS.ic_bca(data, mediane, boot, NOM))
    ver.append(0.0)
vNa, iNa = CAL.verdict_couverture(iv_naif, ver, NOM)
vP, iP = CAL.verdict_couverture(iv_pct, ver, NOM)
vC, iC = CAL.verdict_couverture(iv_bca, ver, NOM)
print(f"   couverture : naïf={iNa['couverture']:.3f} ({vNa}) ; percentile={iP['couverture']:.3f} ({vP}) ; "
      f"BCa={iC['couverture']:.3f} ({vC})")
check("IC naïf (SE moyenne sur médiane) : SUR-CONFIANT (<0.86)", vNa == SURCONFIANT and iNa["couverture"] < 0.86)
check("bootstrap percentile : couverture ~nominal (>=0.87) et NON sur-confiant", iP["couverture"] >= 0.87 and vP != SURCONFIANT)
check("bootstrap BCa : couverture ~nominal (>=0.87) et NON sur-confiant", iC["couverture"] >= 0.87 and vC != SURCONFIANT)
check("le bootstrap couvre strictement mieux que le naïf", iP["couverture"] > iNa["couverture"])

print("=== MOYENNE (n=40) : la formule naïve est CORRECTE ici -> tout le monde calibré ===")
rng2 = random.Random(8)
ivn2, ivp2, ver2 = [], [], []
for s in range(N_DATA):
    data = [rng2.gauss(3.0, 1.0) for _ in range(n)]
    boot = BS.repliques(data, moyenne, B, random.Random(6000 + s))
    ivn2.append(BS.ic_naif_moyenne(data, moyenne, NOM))
    ivp2.append(BS.ic_percentile(boot, NOM))
    ver2.append(3.0)
vNa2, iNa2 = CAL.verdict_couverture(ivn2, ver2, NOM)
vP2, iP2 = CAL.verdict_couverture(ivp2, ver2, NOM)
print(f"   couverture : naïf={iNa2['couverture']:.3f} ({vNa2}) ; percentile={iP2['couverture']:.3f} ({vP2})")
check("sur la moyenne, le naïf est calibré (défaut spécifique aux autres statistiques)", vNa2 != SURCONFIANT)
check("sur la moyenne, le bootstrap est calibré", vP2 != SURCONFIANT)

print("=== BCa respecte les bornes : corrélation ∈ [−1,1] ===")
rng3 = random.Random(2)
def corr(pairs):
    nn = len(pairs); mx = sum(p[0] for p in pairs) / nn; my = sum(p[1] for p in pairs) / nn
    sxy = sum((p[0] - mx) * (p[1] - my) for p in pairs)
    sxx = sum((p[0] - mx) ** 2 for p in pairs); syy = sum((p[1] - my) ** 2 for p in pairs)
    d = math.sqrt(sxx * syy)
    return sxy / d if d > 0 else 0.0
RHO = 0.9
pairs = []
for _ in range(20):
    z1 = rng3.gauss(0, 1); z2 = rng3.gauss(0, 1)
    pairs.append((z1, RHO * z1 + math.sqrt(1 - RHO ** 2) * z2))
bootc = BS.repliques(pairs, corr, 1500, random.Random(3))
loC, hiC = BS.ic_bca(pairs, corr, bootc, 0.90)
print(f"   BCa corrélation = [{loC:.3f}, {hiC:.3f}]")
check("BCa garde la corrélation dans [−1, 1]", -1.0 <= loC <= hiC <= 1.0)

print("=== ABSTENTION si trop peu de points ===")
st, _, raison = BS.intervalle([1.0, 2.0, 3.0], mediane)
print(f"   {st} : {raison}")
check("ABSTENTION sous N_MIN", st == ABSTENTION)

print(f"\nRÉSULTAT bootstrap : {ok}/{total}")
assert ok == total
