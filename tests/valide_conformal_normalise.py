"""
VALIDATION du CONFORME HÉTÉROSCÉDASTIQUE (conformal_normalise.py) — la couverture CONDITIONNELLE, jugée par
calibration.py. Données à deux régimes (facile σ=1 / dur σ=5). On prouve :
  • Le conforme MARGINAL (largeur unique) est conditionnellement SUR-CONFIANT sur le régime DUR (sous-couvre) et
    trop prudent sur le facile — marginalement honnête, localement trompeur.
  • MONDRIAN (quantile par groupe) et NORMALISÉ (score/σ̂) couvrent ~1−α DANS CHAQUE régime (non sur-confiant localement).
"""
from __future__ import annotations

import random

from garde_ressources import borne
import conformal as CF
import conformal_normalise as CN
from conformal_normalise import ESTIMATION, ABSTENTION
import calibration as CAL
from calibration import CALIBRE, SURCONFIANT, SOUSCONFIANT

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


SIGMA = {"facile": 1.0, "dur": 5.0}


def calibration_set(n, graine):
    rng = random.Random(graine)
    groupes, residus = [], []
    for _ in range(n):
        for g in ("facile", "dur"):
            groupes.append(g)
            residus.append(rng.gauss(0, SIGMA[g]))
    return groupes, residus


def test_points(g, M, graine):
    rng = random.Random(graine)
    return [rng.gauss(0, SIGMA[g]) for _ in range(M)]


groupes, residus = calibration_set(400, graine=1)
q_marg = CF.quantile_conforme([abs(r) for r in residus], 0.10)      # quantile MARGINAL (pooled)
mond = CN.ConformeMondrian(0.10).ajuste(groupes, residus)
sig_cal = [SIGMA[g] for g in groupes]

print("=== MARGINAL : conditionnellement SUR-CONFIANT sur le régime DUR, trop prudent sur le facile ===")
for g, attendu in [("dur", "surconfiant"), ("facile", "tropprudent")]:
    vt = test_points(g, 4000, graine=10 + len(g))
    inter = [(-q_marg, q_marg)] * len(vt)
    v, i = CAL.verdict_couverture(inter, vt, 0.90)
    print(f"   marginal sur '{g}' : couverture {i['couverture']:.3f} -> {v}")
    if attendu == "surconfiant":
        check(f"marginal sous-couvre le régime DUR -> SURCONFIANT ({i['couverture']:.3f})", v == SURCONFIANT)
    else:
        check(f"marginal sur-couvre le régime FACILE -> SOUSCONFIANT ({i['couverture']:.3f})", v == SOUSCONFIANT)

print("=== MONDRIAN : couvre ~90% DANS CHAQUE régime (non sur-confiant localement) ===")
for g in ("facile", "dur"):
    vt = test_points(g, 4000, graine=20 + len(g))
    st, inter_g, _ = mond.intervalle(g, 0.0)
    assert st == ESTIMATION
    v, i = CAL.verdict_couverture([inter_g] * len(vt), vt, 0.90)
    print(f"   mondrian sur '{g}' : couverture {i['couverture']:.3f} -> {v}")
    check(f"mondrian '{g}' : couverture {i['couverture']:.3f} >= 0.87 et NON surconfiant",
          i["couverture"] >= 0.87 and v != SURCONFIANT)

print("=== NORMALISÉ : couvre ~90% dans chaque régime via score/σ̂ ===")
for g in ("facile", "dur"):
    vt = test_points(g, 4000, graine=30 + len(g))
    st, inter_g, _ = CN.intervalle_normalise(residus, sig_cal, 0.0, SIGMA[g], 0.10)
    assert st == ESTIMATION
    v, i = CAL.verdict_couverture([inter_g] * len(vt), vt, 0.90)
    print(f"   normalisé sur '{g}' : couverture {i['couverture']:.3f} -> {v}")
    check(f"normalisé '{g}' : couverture {i['couverture']:.3f} >= 0.87 et NON surconfiant",
          i["couverture"] >= 0.87 and v != SURCONFIANT)

print("=== les largeurs s'ADAPTENT : dur >> facile ===")
_, (bf, hf), _ = mond.intervalle("facile", 0.0)
_, (bd, hd), _ = mond.intervalle("dur", 0.0)
check(f"largeur mondrian dur ({hd-bd:.1f}) > facile ({hf-bf:.1f})", (hd - bd) > 2 * (hf - bf))

print("=== ABSTENTION : groupe inconnu, σ̂ invalide, trop peu ===")
check("groupe inconnu -> ABSTENTION", mond.intervalle("inexistant", 0.0)[0] == ABSTENTION)
check("σ̂<=0 -> ABSTENTION", CN.intervalle_normalise([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], [1, 1, 1, 1, 1, 1, 1, 1, 1, -1], 0.0, 1.0)[0] == ABSTENTION)
check("σ_pred<=0 -> ABSTENTION", CN.intervalle_normalise([1.0]*12, [1.0]*12, 0.0, 0.0)[0] == ABSTENTION)
mond_petit = CN.ConformeMondrian(0.10).ajuste(["x"] * 3, [1.0, 2.0, 3.0])
check("groupe à 3 points pour 90% -> ABSTENTION", mond_petit.intervalle("x", 0.0)[0] == ABSTENTION)

print(f"\nCONFORME NORMALISÉ VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
