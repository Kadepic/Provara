"""
VALIDATION du PRÉDICTEUR DE VENN-ABERS (venn_abers.py) — jugé par calibration.py. Score brut SUR-CONFIANT ;
on prouve : la proba fusionnée est CALIBRÉE hors-échantillon, [p0,p1] encadre la proba, l'écart RÉTRÉCIT quand la
calibration grandit, et le score propre s'améliore vs le brut.
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import venn_abers as VA
from venn_abers import ESTIMATION, ABSTENTION
import calibration as CAL
from calibration import CALIBRE, SURCONFIANT
import scores_propres as S

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
        sc.append(sig(k * z))            # score brut sur-confiant
    return sc, lb


sc_cal, y_cal = jeu(1500, graine=1)
sc_test, y_test = jeu(2000, graine=2)
va = VA.VennAbers(sc_cal, y_cal)
sorties = [va.predit(s) for s in sc_test]
p0s = [r[1][0] for r in sorties]
p1s = [r[1][1] for r in sorties]
ps = [r[1][2] for r in sorties]

print("=== AVANT : score brut sur-confiant -> SURCONFIANT ===")
v_av, i_av = CAL.est_calibre(*CAL.depuis_probas(sc_test, y_test))
check(f"score brut -> SURCONFIANT (ece={i_av['ece']:.3f})", v_av == SURCONFIANT)

print("=== APRÈS Venn-Abers : proba fusionnée CALIBRÉE (hors-échantillon) ===")
v_ap, i_ap = CAL.est_calibre(*CAL.depuis_probas(ps, y_test))
print("   ", CAL.formule((v_ap, i_ap), "forecast"))
check(f"Venn-Abers fusionné -> CALIBRE (ece={i_ap['ece']:.3f})", v_ap == CALIBRE)
check(f"ECE réduit ({i_av['ece']:.3f} -> {i_ap['ece']:.3f})", i_ap["ece"] < i_av["ece"] / 2)

print("=== ENCADREMENT : p0 <= p <= p1 toujours ===")
check("p0 <= p <= p1 pour tous les cas", all(p0s[i] <= ps[i] + 1e-9 and ps[i] <= p1s[i] + 1e-9 for i in range(len(ps))))
check("p0 <= p1 (intervalle valide)", all(p0s[i] <= p1s[i] + 1e-9 for i in range(len(ps))))

print("=== LARGEUR de l'encadrement DÉCROÎT quand la calibration grandit ===")
va_petit = VA.VennAbers(*jeu(60, graine=3))
va_grand = VA.VennAbers(*jeu(3000, graine=4))
sondes = [0.1, 0.3, 0.5, 0.7, 0.9]
larg_petit = sum(va_petit.predit(s)[1][1] - va_petit.predit(s)[1][0] for s in sondes) / len(sondes)
larg_grand = sum(va_grand.predit(s)[1][1] - va_grand.predit(s)[1][0] for s in sondes) / len(sondes)
print(f"   largeur moyenne : n=60 -> {larg_petit:.3f} ; n=3000 -> {larg_grand:.3f}")
check(f"largeur(n=3000) {larg_grand:.3f} < largeur(n=60) {larg_petit:.3f}", larg_grand < larg_petit)

print("=== SCORE PROPRE amélioré vs brut + MONOTONIE ===")
check(f"Brier Venn-Abers ({S.brier(ps, y_test):.3f}) < brut ({S.brier(sc_test, y_test):.3f})",
      S.brier(ps, y_test) < S.brier(sc_test, y_test))
check("monotone : score plus haut -> proba fusionnée >=", va.predit(0.95)[1][2] >= va.predit(0.05)[1][2])

print("=== ABSTENTION : calibration trop courte ===")
check("n<30 -> ABSTENTION", VA.VennAbers([0.1, 0.9, 0.5], [0, 1, 1]).predit(0.5)[0] == ABSTENTION)

print(f"\nVENN-ABERS VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
