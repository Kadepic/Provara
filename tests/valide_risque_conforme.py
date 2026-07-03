"""
VALIDATION du CONTRÔLE DE RISQUE CONFORME (risque_conforme.py). On prouve la GARANTIE : le risque réel sur des
données FRAÎCHES reste ≤ la cible, pour le FNR d'ensembles ET pour une perte bornée monotone générique. + ensemble
informatif + repli prudent.
"""
from __future__ import annotations

import random

from garde_ressources import borne
import risque_conforme as RC

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


print("=== CONTRÔLE DU FNR : le vrai label sort de l'ensemble ≤ cible (sur test frais) ===")
for cible in (0.05, 0.10, 0.20):
    rng = random.Random(int(cible * 100))
    sc_cal = [rng.random() for _ in range(600)]                 # scores de la vraie classe (calibration)
    t = RC.controle_fnr(sc_cal, cible)
    sc_test = [rng.random() for _ in range(8000)]               # vraies classes fraîches
    fnr = sum(1 for s in sc_test if s < t) / len(sc_test)       # manqué si score < seuil
    print(f"   cible={cible} : seuil={t:.3f}, FNR réel={fnr:.3f}")
    check(f"FNR réel ({fnr:.3f}) <= cible+tol ({cible}+0.02)", fnr <= cible + 0.02)

print("=== ENSEMBLE INFORMATIF : cible plus stricte -> seuil plus bas -> ensemble plus grand ===")
rng = random.Random(7)
sc_cal = [rng.random() for _ in range(600)]
t_strict = RC.controle_fnr(sc_cal, 0.02)
t_large = RC.controle_fnr(sc_cal, 0.30)
check(f"seuil(2%) {t_strict:.3f} < seuil(30%) {t_large:.3f}", t_strict < t_large)
test = {"A": 0.95, "B": 0.6, "C": 0.3, "D": 0.05}
ens_strict = RC.ensemble_au_seuil(test, t_strict)
ens_large = RC.ensemble_au_seuil(test, t_large)
check(f"ensemble strict ({len(ens_strict)}) ⊇ ensemble large ({len(ens_large)})", ens_large <= ens_strict)
check("l'ensemble strict reste informatif (pas toutes les classes triviales si scores bas exclus)", len(ens_large) < 4)

print("=== CRC GÉNÉRIQUE : perte bornée monotone, E[risque] ≤ cible sur test frais ===")
# difficulté d~U(0,1) ; perte(λ,d)=1 si d>λ (échec si la difficulté dépasse le budget λ), décroissante en λ.
rng = random.Random(11)
d_cal = [rng.random() for _ in range(800)]
lambdas = [i / 100 for i in range(101)]                         # 0 (informatif/risqué) -> 1 (prudent)
risques = [sum(1 for d in d_cal if d > lam) / len(d_cal) for lam in lambdas]   # non croissant
cible = 0.10
lam_hat = RC.seuil_crc(lambdas, risques, cible, n=len(d_cal), B=1.0)
d_test = [rng.random() for _ in range(8000)]
risque_reel = sum(1 for d in d_test if d > lam_hat) / len(d_test)
print(f"   λ̂={lam_hat:.2f} ; risque réel={risque_reel:.3f} (cible {cible})")
check(f"CRC générique : risque réel ({risque_reel:.3f}) <= cible+tol ({cible}+0.02)", risque_reel <= cible + 0.02)
check("λ̂ informatif (pas le plus prudent) : λ̂ < 1.0", lam_hat < 1.0)

print("=== REPLI PRUDENT : cible impossible -> λ le plus prudent (jamais de fausse promesse) ===")
# cible 0 inatteignable avec correction (B/(n+1) > 0) -> renvoie le dernier (plus prudent)
lam_prud = RC.seuil_crc(lambdas, risques, 0.0, n=len(d_cal), B=1.0)
check("cible=0 -> λ le plus prudent (=1.0)", lam_prud == lambdas[-1])
check("controle_fnr cible trop petite -> -inf (inclure tout, FNR=0)", RC.controle_fnr([0.5] * 10, 0.001) == float("-inf"))

print(f"\nRISQUE CONFORME VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
