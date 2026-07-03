"""
VALIDATION de l'AUC + IC (roc_auc.py) — jugée par calibration.py. Positifs ~ N(μ,1), négatifs ~ N(0,1) -> vraie AUC =
Φ(μ/√2). Sur des tirages répétés à petits effectifs : l'intervalle de HANLEY-McNEIL couvre la vraie AUC ≈ nominal, tandis
que l'intervalle « paires indépendantes » (naïf) SOUS-couvre largement (sur-confiant). Contrôles : AUC≈0.5 pour des scores
aléatoires (ne bat pas le hasard), AUC>0.5 détecté quand le signal est fort, ABSTENTION si une classe est vide.
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import roc_auc as R
from roc_auc import ESTIMATION, ABSTENTION
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


def _Phi(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


MU = 1.19
AUC_VRAIE = _Phi(MU / math.sqrt(2))
NOM = 0.95
NPOS = NNEG = 15
N_DATA = 1500


def echantillon(rng):
    scores, labels = [], []
    for _ in range(NPOS):
        scores.append(rng.gauss(MU, 1.0)); labels.append(1)
    for _ in range(NNEG):
        scores.append(rng.gauss(0.0, 1.0)); labels.append(0)
    return scores, labels


print(f"=== Vraie AUC = Φ(μ/√2) = {AUC_VRAIE:.3f} ; n₊=n₋={NPOS} ===")
rng = random.Random(4)
iv_h, iv_n, aucs, ver = [], [], [], []
for _ in range(N_DATA):
    sc, la = echantillon(rng)
    iv_h.append(R.ic_hanley(sc, la, NOM))
    iv_n.append(R.ic_naif(sc, la, NOM))
    aucs.append(R.auc(sc, la))
    ver.append(AUC_VRAIE)
vH, iH = CAL.verdict_couverture(iv_h, ver, NOM)
vN, iN = CAL.verdict_couverture(iv_n, ver, NOM)
print(f"   couverture : Hanley={iH['couverture']:.3f} ({vH}) ; naïf={iN['couverture']:.3f} ({vN})")
print(f"   AUC moyenne estimée = {sum(aucs)/len(aucs):.3f}")
check("AUC estimée ~ vraie (|biais|<0.02)", abs(sum(aucs) / len(aucs) - AUC_VRAIE) < 0.02)
check("Hanley : couverture ~nominal (>=0.91) et NON sur-confiant", iH["couverture"] >= 0.91 and vH != SURCONFIANT)
check("IC naïf (paires indépendantes) : SUR-CONFIANT (sous-couvre)", vN == SURCONFIANT and iN["couverture"] < 0.90)
check("Hanley couvre strictement mieux que le naïf", iH["couverture"] > iN["couverture"])

print("=== Scores ALÉATOIRES (sans signal) : AUC≈0.5, ne bat pas le hasard ===")
rng2 = random.Random(20)
sc = [rng2.gauss(0, 1) for _ in range(40)]
la = [rng2.randint(0, 1) for _ in range(40)]
a0 = R.auc(sc, la)
print(f"   AUC aléatoire = {a0:.3f} ; borne basse Hanley = {R.ic_hanley(sc, la, 0.95)[0]:.3f}")
check("scores aléatoires : ne bat PAS le hasard (IC inclut 0.5)", R.bat_le_hasard(sc, la, 0.95) is False)

print("=== Signal FORT et gros effectifs : AUC détectée > 0.5 ===")
rng3 = random.Random(21)
sc2, la2 = [], []
for _ in range(120):
    sc2.append(rng3.gauss(1.5, 1.0)); la2.append(1)
    sc2.append(rng3.gauss(0.0, 1.0)); la2.append(0)
print(f"   AUC={R.auc(sc2, la2):.3f} ; bat le hasard = {R.bat_le_hasard(sc2, la2, 0.95)}")
check("signal fort : bat le hasard (borne basse > 0.5)", R.bat_le_hasard(sc2, la2, 0.95) is True)

print("=== AUC parfaite si séparation totale ===")
check("séparation parfaite -> AUC=1.0", R.auc([3, 4, 5, 1, 2], [1, 1, 1, 0, 0]) == 1.0)

print("=== ABSTENTION si une classe est vide ===")
st, _, raison = R.evalue([1.0, 2.0, 3.0], [1, 1, 1])
print(f"   {st} : {raison}")
check("ABSTENTION si pas de négatifs", st == ABSTENTION)

print(f"\nRÉSULTAT roc_auc : {ok}/{total}")
assert ok == total
