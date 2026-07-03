"""
VALIDATION de l'ESTIMATION PONDÉRÉE (echantillon_pondere.py) — jugée par calibration.py. L'estimateur de Hájek est
~sans biais et son intervalle COUVRE la vraie moyenne ~confiance ; l'estimateur BRUT (biaisé) sous-couvre (SURCONFIANT).
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import echantillon_pondere as E
from echantillon_pondere import ESTIMATION, ABSTENTION
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


MU_VRAI = 15.0          # population : 50% ~10, 50% ~20 -> moyenne 15
P_SUR = 0.75            # on sur-échantillonne le groupe "20"
Z = 1.6449


def echantillon(n, rng):
    """Échantillon BIAISÉ : groupe '20' inclus avec proba 0.75, groupe '10' avec 0.25. Renvoie (valeurs, poids)."""
    v, w = [], []
    for _ in range(n):
        if rng.random() < P_SUR:
            v.append(rng.gauss(20, 2)); w.append(1.0 / P_SUR)
        else:
            v.append(rng.gauss(10, 2)); w.append(1.0 / (1.0 - P_SUR))
    return v, w


print("=== SANS BIAIS : l'estimateur pondéré retrouve la vraie moyenne (le brut est biaisé) ===")
rng = random.Random(1)
ests_pond, ests_brut = [], []
for _ in range(300):
    v, w = echantillon(200, rng)
    ests_pond.append(E.estime_hajek(v, w))
    ests_brut.append(sum(v) / len(v))
moy_pond = sum(ests_pond) / len(ests_pond)
moy_brut = sum(ests_brut) / len(ests_brut)
print(f"   pondéré moyen = {moy_pond:.2f} ; brut moyen = {moy_brut:.2f} ; vrai = {MU_VRAI}")
check(f"pondéré ≈ vrai (|{moy_pond:.2f}−15| < 0.2)", abs(moy_pond - MU_VRAI) < 0.2)
check(f"brut nettement biaisé (|{moy_brut:.2f}−15| > 1.5)", abs(moy_brut - MU_VRAI) > 1.5)

print("=== COUVERTURE : l'IC pondéré couvre la vraie moyenne ~90% ; le brut SOUS-couvre (SURCONFIANT) ===")
inter_pond, inter_brut, ver = [], [], []
rng = random.Random(2)
for t in range(2000):
    v, w = echantillon(200, rng)
    st, res, _ = E.intervalle_hajek(v, w, 0.90, n_boot=400, seed=t)
    if st != ESTIMATION:
        continue
    inter_pond.append(res[1])
    mu = sum(v) / len(v)
    sd = math.sqrt(sum((x - mu) ** 2 for x in v) / (len(v) - 1))
    se = sd / math.sqrt(len(v))
    inter_brut.append((mu - Z * se, mu + Z * se))
    ver.append(MU_VRAI)
vp, ip = CAL.verdict_couverture(inter_pond, ver, 0.90)
vb, ib = CAL.verdict_couverture(inter_brut, ver, 0.90)
print("   pondéré :", CAL.formule((vp, ip), "couverture"))
print("   brut    :", CAL.formule((vb, ib), "couverture"))
check(f"IC pondéré @90% : couverture {ip['couverture']:.3f} >= 0.85 et NON surconfiant",
      ip["couverture"] >= 0.85 and vp != SURCONFIANT)
check(f"IC brut @90% : SOUS-COUVRE {ib['couverture']:.3f} -> SURCONFIANT (biais ignoré)", vb == SURCONFIANT)

print("=== Horvitz-Thompson (moyenne de population) cohérent + n_effectif + ABSTENTION ===")
rng = random.Random(3)
v, w = echantillon(400, rng)
pi = [1.0 / x for x in w]         # π = 1/poids
N = sum(w)                        # estimation de la taille de population = Σ 1/π
ht = E.estime_ht(v, pi, N)
check(f"HT ≈ Hájek ≈ vrai ({ht:.2f})", abs(ht - MU_VRAI) < 0.8)
check("n_effectif ≤ n", E.n_effectif(w) <= len(w))
check("poids égaux -> n_effectif = n", abs(E.n_effectif([2.0] * 50) - 50) < 1e-9)
check("échantillon trop petit -> ABSTENTION", E.intervalle_hajek([1, 2, 3], [1, 1, 1])[0] == ABSTENTION)
# poids dégénérés : un poids écrasant -> taille effective < 5
check("poids ultra-déséquilibrés -> ABSTENTION",
      E.intervalle_hajek([1.0] * 20, [1e6] + [1.0] * 19)[0] == ABSTENTION)

print(f"\nÉCHANTILLON PONDÉRÉ VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
