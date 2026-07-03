"""
VALIDATION des CALIBRATEURS PARAMÉTRIQUES (calibrateurs.py) — jugés par calibration.py. Pour CHAQUE méthode (Platt,
histogramme, beta) sur un classifieur SUR-confiant : ECE réduit hors-échantillon, verdict non sur-confiant, abstention
si trop peu de données.
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import calibrateurs as K
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


def sig(x):
    return 1.0 / (1.0 + math.exp(-x))


def jeu(n, graine, k=2.5):
    rng = random.Random(graine)
    sc, lb = [], []
    for _ in range(n):
        z = rng.uniform(-3, 3)
        lb.append(1 if rng.random() < sig(z) else 0)
        sc.append(sig(k * z))
    return sc, lb


sc_cal, y_cal = jeu(4000, graine=1)
sc_test, y_test = jeu(4000, graine=2)

v_brut, i_brut = CAL.est_calibre(*CAL.depuis_probas(sc_test, y_test))
check(f"score brut -> SURCONFIANT (ece={i_brut['ece']:.3f})", v_brut == SURCONFIANT)

for methode in ("platt", "histogramme", "beta"):
    print(f"=== {methode.upper()} : ECE réduit + non sur-confiant (hors-échantillon) ===")
    cal = K.ajuste(sc_cal, y_cal, methode)
    probas = [cal.applique(s) for s in sc_test]
    v, i = CAL.est_calibre(*CAL.depuis_probas(probas, y_test))
    print("   ", CAL.formule((v, i), "forecast"))
    check(f"{methode} : ECE réduit ({i_brut['ece']:.3f} -> {i['ece']:.3f})", i["ece"] < i_brut["ece"] / 2)
    check(f"{methode} : non sur-confiant", v != SURCONFIANT)
    check(f"{methode} : probas dans [0,1]", all(0.0 <= p <= 1.0 for p in probas))

print("=== MONOTONIE (Platt, beta) + ABSTENTION ===")
cp = K.ajuste(sc_cal, y_cal, "platt")
cb = K.ajuste(sc_cal, y_cal, "beta")
check("Platt monotone (score haut -> proba haute)", cp.applique(0.95) > cp.applique(0.05))
check("Beta monotone", cb.applique(0.95) > cb.applique(0.05))
check("Platt n<30 -> None", K.ajuste([0.1, 0.9], [0, 1], "platt") is None)
check("histogramme n<30 -> None", K.ajuste([0.1, 0.9], [0, 1], "histogramme") is None)
check("beta n<30 -> None", K.ajuste([0.1, 0.9], [0, 1], "beta") is None)

print("=== les 3 méthodes battent le score brut au Brier ===")
import scores_propres as S
br_brut = S.brier(sc_test, y_test)
for methode in ("platt", "histogramme", "beta"):
    cal = K.ajuste(sc_cal, y_cal, methode)
    br = S.brier([cal.applique(s) for s in sc_test], y_test)
    check(f"{methode} : Brier ({br:.3f}) < brut ({br_brut:.3f})", br < br_brut)

print(f"\nCALIBRATEURS VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
