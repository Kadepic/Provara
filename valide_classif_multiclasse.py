"""
VALIDATION de la CLASSIFICATION CALIBRÉE MULTI-CLASSE (classif_multiclasse.py) — jugée par calibration.py.
Classifieur SUR-CONFIANT (softmax à température T<1) ; on sépare calibration / test et on prouve :
  • AVANT : la confiance de la classe gagnante est SUR-CONFIANTE (top-label).
  • APRÈS isotonique un-contre-tous : top-label non sur-confiant, ECE par classe RÉDUIT, Brier multi-classe RÉDUIT,
    HORS-ÉCHANTILLON. + abstention (justesse des décisions retenues > globale) + refus si trop peu de données.
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import classif_multiclasse as MC
from classif_multiclasse import DECISION, ABSTENTION
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


def softmax(zs, T=1.0):
    m = max(zs)
    es = [math.exp((z - m) / T) for z in zs]
    s = sum(es)
    return [e / s for e in es]


def jeu(n, graine, T_brut=0.5):
    """n exemples : vraie loi = softmax(z, 1) ; scores bruts = softmax(z, T_brut) (T<1 -> sur-confiant)."""
    rng = random.Random(graine)
    ex, lab = [], []
    for _ in range(n):
        zs = [rng.gauss(0, 1.5) for _ in CLASSES]
        pv = softmax(zs, 1.0)
        u = rng.random(); cum = 0.0; y = CLASSES[-1]
        for i, p in enumerate(pv):
            cum += p
            if u < cum:
                y = CLASSES[i]; break
        pb = softmax(zs, T_brut)
        ex.append({c: pb[i] for i, c in enumerate(CLASSES)})
        lab.append(y)
    return ex, lab


def top_label(probas_list, labels):
    """(confiances = proba de la classe gagnante, justesses = la gagnante est-elle la vraie classe)."""
    conf, just = [], []
    for probas, y in zip(probas_list, labels):
        g = max(probas, key=probas.get)
        conf.append(probas[g])
        just.append(1 if g == y else 0)
    return conf, just


def ece_par_classe(probas_list, labels):
    """ECE moyenne sur les classes (chaque P(classe=c) jugée comme un forecast binaire)."""
    tot = 0.0
    for c in CLASSES:
        pc = [probas[c] for probas in probas_list]
        yc = [1 if y == c else 0 for y in labels]
        tot += CAL.ece(*CAL.depuis_probas(pc, yc))
    return tot / len(CLASSES)


ex_cal, y_cal = jeu(6000, graine=1)
ex_test, y_test = jeu(6000, graine=2)

print("=== AVANT : top-label des scores bruts -> SUR-CONFIANT ===")
v_av, i_av = CAL.est_calibre(*top_label(ex_test, y_test))
print("   ", CAL.formule((v_av, i_av), "forecast"))
check(f"top-label brut -> SURCONFIANT (ece={i_av['ece']:.3f})", v_av == SURCONFIANT)

print("=== APRÈS isotonique un-contre-tous (hors-échantillon) -> non sur-confiant, ECE/Brier réduits ===")
cal = MC.ajuste_multiclasse(ex_cal, y_cal)
probas_test = [cal.applique(e) for e in ex_test]
v_ap, i_ap = CAL.est_calibre(*top_label(probas_test, y_test))
print("   ", CAL.formule((v_ap, i_ap), "forecast"))
check(f"top-label calibré -> NON surconfiant (ece={i_ap['ece']:.3f})", v_ap != SURCONFIANT)
check(f"top-label ECE réduit ({i_av['ece']:.3f} -> {i_ap['ece']:.3f})", i_ap["ece"] < i_av["ece"])
ece_brut = ece_par_classe(ex_test, y_test)
ece_cal = ece_par_classe(probas_test, y_test)
check(f"ECE moyenne PAR CLASSE réduite ({ece_brut:.3f} -> {ece_cal:.3f})", ece_cal < ece_brut)
b_brut = MC.brier_multiclasse(ex_test, y_test)
b_cal = MC.brier_multiclasse(probas_test, y_test)
check(f"Brier multi-classe réduit ({b_brut:.3f} -> {b_cal:.3f})", b_cal < b_brut)

print("=== PROBAS VALIDES : somme 1, dans [0,1] ===")
check("chaque vecteur de probas calibrées somme à 1", all(abs(sum(p.values()) - 1.0) < 1e-9 for p in probas_test))
check("toutes les probas dans [0,1]", all(0.0 <= v <= 1.0 for p in probas_test for v in p.values()))

print("=== ABSTENTION : sous le seuil, décisions retenues PLUS JUSTES ===")
seuil = 0.6
dec = [MC.predit(cal, e, seuil_abstention=seuil) for e in ex_test]
acc_tout = sum(1 for i in range(len(ex_test))
               if max(probas_test[i], key=probas_test[i].get) == y_test[i]) / len(ex_test)
retenues = [(d[1], y_test[i]) for i, d in enumerate(dec) if d[0] == DECISION]
acc_ret = sum(1 for (g, y) in retenues if g == y) / len(retenues)
print(f"   justesse globale = {acc_tout:.3f} ; sur les décisions retenues (conf>={seuil}) = {acc_ret:.3f} (n={len(retenues)})")
check(f"justesse retenue ({acc_ret:.3f}) > globale ({acc_tout:.3f})", acc_ret > acc_tout)

print("=== REFUS HONNÊTE : trop peu de données ===")
check("trop peu d'exemples -> None", MC.ajuste_multiclasse([{"A": 0.9, "B": 0.1}], ["A"]) is None)
check("predit(None) -> ABSTENTION", MC.predit(None, {"A": 0.9})[0] == ABSTENTION)

print(f"\nCLASSIF MULTI-CLASSE VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
