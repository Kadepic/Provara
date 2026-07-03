"""
VALIDATION du TEMPERATURE SCALING (temperature.py) — jugé par calibration.py. Classifieur multi-classe SUR-confiant :
T̂ > 1, ECE top-label RÉDUIT hors-échantillon, JUSTESSE (argmax) PRÉSERVÉE, abstention si trop peu.
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import temperature as T
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


CLASSES = ["A", "B", "C", "D"]


def jeu(n, graine, gain=3.0):
    """Vraie loi softmax(z) ; logits OBSERVÉS = z·gain (gain>1 -> sur-confiant)."""
    rng = random.Random(graine)
    lg, lab = [], []
    for _ in range(n):
        z = {c: rng.gauss(0, 1.5) for c in CLASSES}
        p = T.softmax_temp(z, 1.0)
        u = rng.random(); cum = 0.0; y = CLASSES[-1]
        for c in CLASSES:
            cum += p[c]
            if u < cum:
                y = c; break
        lg.append({c: z[c] * gain for c in CLASSES})
        lab.append(y)
    return lg, lab


def top_label(probas_list, labels):
    conf, just = [], []
    for p, y in zip(probas_list, labels):
        g = max(p, key=p.get)
        conf.append(p[g]); just.append(1 if g == y else 0)
    return conf, just


lg_cal, y_cal = jeu(5000, graine=1)
lg_test, y_test = jeu(5000, graine=2)
ts = T.ajuste_temperature(lg_cal, y_cal)
print(f"=== T̂ = {ts.T:.2f} > 1 (sur-confiance détectée) ===")
check("T̂ > 1", ts.T > 1.0)

print("=== AVANT (brut T=1) -> SURCONFIANT ; APRÈS -> non sur-confiant, ECE réduit ===")
brut = [T.softmax_temp(lg, 1.0) for lg in lg_test]
calib = [ts.applique(lg) for lg in lg_test]
v_av, i_av = CAL.est_calibre(*top_label(brut, y_test))
v_ap, i_ap = CAL.est_calibre(*top_label(calib, y_test))
print("   brut   :", CAL.formule((v_av, i_av), "forecast"))
print("   calibré:", CAL.formule((v_ap, i_ap), "forecast"))
check(f"brut -> SURCONFIANT (ece={i_av['ece']:.3f})", v_av == SURCONFIANT)
check(f"calibré -> non sur-confiant (ece={i_ap['ece']:.3f})", v_ap != SURCONFIANT)
check(f"ECE top-label réduit ({i_av['ece']:.3f} -> {i_ap['ece']:.3f})", i_ap["ece"] < i_av["ece"] / 2)

print("=== JUSTESSE (argmax) PRÉSERVÉE : la température ne change pas les décisions ===")
acc_brut = sum(1 for i in range(len(y_test)) if max(brut[i], key=brut[i].get) == y_test[i]) / len(y_test)
acc_cal = sum(1 for i in range(len(y_test)) if max(calib[i], key=calib[i].get) == y_test[i]) / len(y_test)
check(f"justesse inchangée (brut {acc_brut:.4f} == calibré {acc_cal:.4f})", abs(acc_brut - acc_cal) < 1e-9)

print("=== SOUS-CONFIANCE -> T̂ < 1 ; déjà calibré -> T̂ ≈ 1 ===")
lg_sous, y_sous = jeu(5000, graine=3, gain=0.4)
ts_sous = T.ajuste_temperature(lg_sous, y_sous)
check(f"sous-confiant (gain 0.4) -> T̂={ts_sous.T:.2f} < 1", ts_sous.T < 1.0)
lg_ok, y_ok = jeu(5000, graine=4, gain=1.0)
ts_ok = T.ajuste_temperature(lg_ok, y_ok)
check(f"déjà calibré -> T̂={ts_ok.T:.2f} ≈ 1 (∈[0.8,1.25])", 0.8 <= ts_ok.T <= 1.25)

print("=== applique_probas (depuis des probabilités) + ABSTENTION ===")
p_calib = ts.applique_probas(T.softmax_temp(lg_test[0], 1.0))
check("applique_probas renvoie une distribution (somme≈1)", abs(sum(p_calib.values()) - 1.0) < 1e-9)
check("n<30 -> None", T.ajuste_temperature([{"A": 1.0, "B": 0.0}], ["A"]) is None)

print(f"\nTEMPERATURE VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
