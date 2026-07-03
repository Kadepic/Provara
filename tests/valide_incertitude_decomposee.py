"""
VALIDATION de la DÉCOMPOSITION ÉPISTÉMIQUE/ALÉATOIRE (incertitude_decomposee.py) — jugée par calibration.py.
L'épistémique DÉCROÎT ∝ 1/n, l'aléatoire reste ~constant ; l'intervalle prédictif couvre une nouvelle observation
~confiance ; l'ensemble respecte la loi de la variance totale.
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import incertitude_decomposee as D
from incertitude_decomposee import ESTIMATION, ABSTENTION
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


SIGMA = 2.0


def epi_ale_moyen(n, runs, graine):
    rng = random.Random(graine)
    epi, ale = 0.0, 0.0
    for _ in range(runs):
        ech = [rng.gauss(5, SIGMA) for _ in range(n)]
        _, infos = D.decompose_echantillon(ech)
        epi += infos["epistemique"]; ale += infos["aleatoire"]
    return epi / runs, ale / runs


print("=== ÉPISTÉMIQUE ∝ 1/n (réductible) ; ALÉATOIRE ~constant (irréductible) ===")
epi20, ale20 = epi_ale_moyen(20, 400, 1)
epi200, ale200 = epi_ale_moyen(200, 400, 2)
print(f"   épistémique : n=20 -> {epi20:.4f} ; n=200 -> {epi200:.4f} (ratio {epi20/epi200:.1f})")
print(f"   aléatoire   : n=20 -> {ale20:.4f} ; n=200 -> {ale200:.4f} (vrai σ²={SIGMA**2})")
check(f"épistémique décroît ~×10 quand n ×10 (ratio {epi20/epi200:.1f} ∈ [7,13])", 7 <= epi20 / epi200 <= 13)
check(f"aléatoire ~constant ≈ σ² ({ale20:.2f}, {ale200:.2f} ≈ {SIGMA**2})",
      abs(ale20 - SIGMA**2) < 0.5 and abs(ale200 - SIGMA**2) < 0.5)

print("=== INTERVALLE PRÉDICTIF (aléatoire+épistémique) couvre une nouvelle observation ===")
inter, ver = [], []
rng = random.Random(3)
for _ in range(4000):
    ech = [rng.gauss(5, SIGMA) for _ in range(80)]
    st, res, _ = D.intervalle_predictif(ech, 0.90)
    if st == ESTIMATION:
        inter.append(res[1]); ver.append(rng.gauss(5, SIGMA))   # nouvelle obs
v, i = CAL.verdict_couverture(inter, ver, 0.90)
print("   ", CAL.formule((v, i), "couverture"))
check(f"intervalle prédictif @90% : couverture {i['couverture']:.3f} >= 0.86 et NON surconfiant",
      i["couverture"] >= 0.86 and v != SURCONFIANT)

print("=== ENSEMBLE : loi de la variance totale (épistémique=désaccord, aléatoire=bruit moyen) ===")
rng = random.Random(4)
thetas = [rng.gauss(0, 1.5) for _ in range(8)]          # prédictions des 8 membres
variances = [0.5 + rng.random() for _ in range(8)]      # variance prédite par chaque membre
_, dec = D.decompose_ensemble(thetas, variances)
# vérité simulée : choisir un membre, Y = theta_m + N(0, v_m)
ys = []
for _ in range(40000):
    m = rng.randrange(8)
    ys.append(thetas[m] + rng.gauss(0, math.sqrt(variances[m])))
moy = sum(ys) / len(ys)
var_totale_emp = sum((y - moy) ** 2 for y in ys) / len(ys)
print(f"   épistémique={dec['epistemique']:.3f} + aléatoire={dec['aleatoire']:.3f} = {dec['total']:.3f} ; Var(Y) empirique={var_totale_emp:.3f}")
check(f"total décomposé ≈ Var(Y) empirique ({dec['total']:.3f} ≈ {var_totale_emp:.3f})", abs(dec["total"] - var_totale_emp) < 0.1)
check("épistémique = variance des prédictions membres",
      abs(dec["epistemique"] - sum((t - sum(thetas)/8)**2 for t in thetas)/8) < 1e-9)

print("=== ABSTENTION ===")
check("échantillon trop petit -> ABSTENTION", D.decompose_echantillon([1, 2])[0] == ABSTENTION)
check("ensemble < 2 membres -> ABSTENTION", D.decompose_ensemble([0.5])[0] == ABSTENTION)
check("intervalle prédictif trop peu -> ABSTENTION", D.intervalle_predictif([1, 2])[0] == ABSTENTION)

print(f"\nINCERTITUDE DÉCOMPOSÉE VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
