"""
VALIDATION de la CALIBRATION MULTI-LABEL (multilabel.py) — jugée par calibration.py + risque_conforme. Chaque label :
brut SUR-confiant -> calibré CALIBRE hors-échantillon. Seuil à rappel contrôlé : rappel macro ≥ cible sur test frais.
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import multilabel as ML
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


LABELS = ["sport", "politique", "tech", "culture"]


def sig(x):
    return 1.0 / (1.0 + math.exp(-x))


def jeu(n, graine, k=2.5):
    rng = random.Random(graine)
    sx, sp = [], []
    for _ in range(n):
        presents = set(); d = {}
        for j in LABELS:
            z = rng.gauss(0, 1.5)
            if rng.random() < sig(z):
                presents.add(j)
            d[j] = sig(k * z)
        sx.append(d); sp.append(presents)
    return sx, sp


sx_cal, sp_cal = jeu(5000, graine=1)
sx_test, sp_test = jeu(5000, graine=2)
cal = ML.ajuste_multilabel(sx_cal, sp_cal)

print("=== CALIBRATION PAR LABEL : brut SURCONFIANT -> calibré CALIBRE (hors-échantillon) ===")
for j in LABELS:
    sc_test = [d[j] for d in sx_test]
    pres_test = [1 if j in s else 0 for s in sp_test]
    v_brut, i_brut = CAL.est_calibre(*CAL.depuis_probas(sc_test, pres_test))
    pc = [cal.applique(d).get(j, 0.0) for d in sx_test]
    v_cal, i_cal = CAL.est_calibre(*CAL.depuis_probas(pc, pres_test))
    print(f"   '{j}' : brut ece={i_brut['ece']:.3f} ({v_brut}) -> calibré ece={i_cal['ece']:.3f} ({v_cal})")
    check(f"label '{j}' : brut SURCONFIANT, calibré non sur-confiant + ECE réduit",
          v_brut == SURCONFIANT and v_cal != SURCONFIANT and i_cal["ece"] < i_brut["ece"])

print("=== SEUIL À RAPPEL CONTRÔLÉ : rappel macro ≥ cible sur test frais ===")
for cible in (0.10, 0.20):
    tau = ML.seuil_rappel(cal, sx_cal, sp_cal, cible)
    retrouves, totaux = 0, 0
    for d, presents in zip(sx_test, sp_test):
        pred = cal.predit(d, tau)
        for j in presents:
            totaux += 1
            if j in pred:
                retrouves += 1
    rappel = retrouves / totaux
    print(f"   cible manques={cible} : seuil τ={tau:.3f}, rappel réel={rappel:.3f}")
    check(f"rappel ({rappel:.3f}) >= 1−cible−tol ({1-cible-0.03})", rappel >= 1 - cible - 0.03)

print("=== probas valides + ABSTENTION ===")
p = cal.applique(sx_test[0])
check("probas par label dans [0,1]", all(0.0 <= v <= 1.0 for v in p.values()))
check("trop peu de données -> None", ML.ajuste_multilabel([{"a": 0.9}], [{"a"}]) is None)

print(f"\nMULTI-LABEL VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
