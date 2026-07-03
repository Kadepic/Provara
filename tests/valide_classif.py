"""
VALIDATION de la CLASSIFICATION CALIBRÉE (classif_calibree.py) — la réparation de calibration est-elle RÉELLE et
HORS-ÉCHANTILLON ? Preuve jugée par calibration.py.

Monde connu : vraie proba q = sigmoid(z), z ~ U(−3,3), y ~ Bernoulli(q). Classifieur SUR-CONFIANT : score = sigmoid(2z)
(plus extrême que q). On SÉPARE calibration / test. On montre :
  • AVANT (scores bruts sur le test) -> SURCONFIANT (calibration.py le démasque).
  • APRÈS (isotonique apprise sur calibration, appliquée au TEST) -> CALIBRE, ECE fortement réduit. HORS-ÉCHANTILLON
    (pas d'overfit : la calibration est apprise sur d'autres points que ceux jugés).
  • Monotonie préservée, abstention sous seuil augmente la justesse des décisions retenues, refus si trop peu de données.
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import classif_calibree as CC
from classif_calibree import DECISION, ABSTENTION
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


def sigmoid(x):
    return 1.0 / (1.0 + math.exp(-x))


def jeu(n, graine, k=2.0):
    """n couples (score sur-confiant = sigmoid(k·z), issue ~ Bernoulli(sigmoid(z)))."""
    rng = random.Random(graine)
    scores, issues = [], []
    for _ in range(n):
        z = rng.uniform(-3, 3)
        issues.append(1 if rng.random() < sigmoid(z) else 0)
        scores.append(sigmoid(k * z))
    return scores, issues


s_cal, y_cal = jeu(4000, graine=1)
s_test, y_test = jeu(4000, graine=2)

print("=== AVANT : scores bruts sur-confiants -> SURCONFIANT (démasqué) ===")
v_av, i_av = CAL.est_calibre(*CAL.depuis_probas(s_test, y_test))
print("   ", CAL.formule((v_av, i_av), "forecast"))
check(f"scores bruts -> SURCONFIANT (ece={i_av['ece']:.3f})", v_av == SURCONFIANT)

print("=== APRÈS : isotonique (apprise sur CALIBRATION, jugée sur TEST) -> CALIBRE, ECE réduit ===")
cal = CC.ajuste_isotonique(s_cal, y_cal)
probas_cal = [cal.applique(s) for s in s_test]
v_ap, i_ap = CAL.est_calibre(*CAL.depuis_probas(probas_cal, y_test))
print("   ", CAL.formule((v_ap, i_ap), "forecast"))
check(f"après isotonique -> CALIBRE (hors-échantillon, ece={i_ap['ece']:.3f})", v_ap == CALIBRE)
check(f"ECE fortement réduit ({i_av['ece']:.3f} -> {i_ap['ece']:.3f})", i_ap["ece"] < i_av["ece"] / 2)

print("=== MONOTONIE : la calibration préserve l'ordre du classifieur ===")
grille = [i / 100 for i in range(101)]
sortie = [cal.applique(s) for s in grille]
check("score -> proba calibrée est non décroissante", all(sortie[i] <= sortie[i + 1] + 1e-12 for i in range(len(sortie) - 1)))
check("proba calibrée dans [0,1]", all(0.0 <= p <= 1.0 for p in sortie))

print("=== ABSTENTION : sous le seuil, on retient des décisions PLUS JUSTES ===")
seuil = 0.75
acc_tout = sum(1 for i in range(len(s_test)) if (probas_cal[i] >= 0.5) == bool(y_test[i])) / len(s_test)
retenues = [(probas_cal[i], y_test[i]) for i in range(len(s_test)) if max(probas_cal[i], 1 - probas_cal[i]) >= seuil]
acc_ret = sum(1 for (p, y) in retenues if (p >= 0.5) == bool(y)) / len(retenues)
print(f"   justesse sur TOUT = {acc_tout:.3f} ; sur les décisions retenues (conf>={seuil}) = {acc_ret:.3f} (n={len(retenues)})")
check(f"justesse sur les décisions retenues ({acc_ret:.3f}) > sur tout ({acc_tout:.3f})", acc_ret > acc_tout)
st, _ = CC.predit(cal, 0.5, seuil_abstention=0.9)        # score ~milieu, confiance faible
check("confiance faible + seuil élevé -> ABSTENTION", st == ABSTENTION)
st2, _ = CC.predit(cal, 0.99, seuil_abstention=0.6)
check("confiance forte -> DECISION", st2 == DECISION)

print("=== REFUS HONNÊTE : trop peu de données -> pas de calibrateur ===")
check("n<30 -> ajuste_isotonique renvoie None", CC.ajuste_isotonique([0.1, 0.9, 0.5], [0, 1, 1]) is None)
check("predit(None) -> ABSTENTION", CC.predit(None, 0.9)[0] == ABSTENTION)

print("=== le calibrateur ne fabrique pas de sur-confiance même sur un classifieur DÉJÀ calibré ===")
s_ok, y_ok = jeu(4000, graine=3, k=1.0)            # k=1 : déjà bien calibré
cal_ok = CC.ajuste_isotonique(s_ok, y_ok)
s_t, y_t = jeu(4000, graine=4, k=1.0)
v_ok, i_ok = CAL.est_calibre(*CAL.depuis_probas([cal_ok.applique(s) for s in s_t], y_t))
check(f"classifieur déjà calibré -> reste CALIBRE après isotonique (ece={i_ok['ece']:.3f})", v_ok == CALIBRE)

print(f"\nCLASSIF VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
