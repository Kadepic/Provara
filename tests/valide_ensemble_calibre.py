"""
VALIDATION de l'ENSEMBLE CALIBRÉ (ensemble_calibre.py). Jugé par scores_propres.py + calibration.py. On prouve, HORS
ÉCHANTILLON : l'ensemble (combiné + recalibré) a un MEILLEUR score propre que CHAQUE membre, et il est CALIBRÉ.
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import ensemble_calibre as E
from ensemble_calibre import DECISION, ABSTENTION
import scores_propres as S
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


def jeu(n, graine):
    """Membres DIVERS et imparfaits : A sur-confiant, B sous-confiant, C bruité. Vraie proba = sig(z)."""
    rng = random.Random(graine)
    sorties = {"A": [], "B": [], "C": []}
    issues = []
    for _ in range(n):
        z = rng.uniform(-3, 3)
        issues.append(1 if rng.random() < sig(z) else 0)
        sorties["A"].append(sig(2.2 * z + rng.gauss(0, 1.0)))
        sorties["B"].append(sig(0.5 * z + rng.gauss(0, 1.0)))
        sorties["C"].append(sig(z + rng.gauss(0, 1.8)))
    return sorties, issues


cal_s, cal_y = jeu(6000, graine=1)
test_s, test_y = jeu(6000, graine=2)

for pond in ("uniforme", "inverse_perte"):
    print(f"=== ENSEMBLE ({pond}) bat CHAQUE membre (log-loss & Brier, hors-échantillon) ===")
    ens = E.ajuste_ensemble(cal_s, cal_y, pond)
    proba_ens = [ens.applique({m: test_s[m][i] for m in test_s}) for i in range(len(test_y))]
    ll_ens = S.log_loss(proba_ens, test_y)
    br_ens = S.brier(proba_ens, test_y)
    lls = {m: S.log_loss(test_s[m], test_y) for m in test_s}
    brs = {m: S.brier(test_s[m], test_y) for m in test_s}
    print(f"   log-loss ensemble={ll_ens:.4f} vs membres " + ", ".join(f"{m}={lls[m]:.4f}" for m in lls))
    check(f"[{pond}] log-loss ensemble < chaque membre", all(ll_ens < lls[m] for m in lls))
    check(f"[{pond}] Brier ensemble < chaque membre", all(br_ens < brs[m] for m in brs))
    v, i = CAL.est_calibre(*CAL.depuis_probas(proba_ens, test_y))
    print("   ", CAL.formule((v, i), "forecast"))
    check(f"[{pond}] ensemble CALIBRE (ece={i['ece']:.3f}, jamais SURCONFIANT)", v == CALIBRE)

print("=== PONDÉRATION inverse_perte : au moins aussi bonne que l'uniforme ===")
e_u = E.ajuste_ensemble(cal_s, cal_y, "uniforme")
e_w = E.ajuste_ensemble(cal_s, cal_y, "inverse_perte")
ll_u = S.log_loss([e_u.applique({m: test_s[m][i] for m in test_s}) for i in range(len(test_y))], test_y)
ll_w = S.log_loss([e_w.applique({m: test_s[m][i] for m in test_s}) for i in range(len(test_y))], test_y)
check(f"inverse_perte ({ll_w:.4f}) <= uniforme ({ll_u:.4f}) + marge", ll_w <= ll_u + 0.01)

print("=== ABSTENTION sous seuil : décisions retenues plus justes ; refus si trop peu ===")
ens = E.ajuste_ensemble(cal_s, cal_y, "inverse_perte")
seuil = 0.75
probas = [ens.applique({m: test_s[m][i] for m in test_s}) for i in range(len(test_y))]
acc_tout = sum(1 for i in range(len(test_y)) if (probas[i] >= 0.5) == bool(test_y[i])) / len(test_y)
ret = [(probas[i], test_y[i]) for i in range(len(test_y)) if max(probas[i], 1 - probas[i]) >= seuil]
acc_ret = sum(1 for (p, y) in ret if (p >= 0.5) == bool(y)) / len(ret)
check(f"justesse retenue ({acc_ret:.3f}) > globale ({acc_tout:.3f})", acc_ret > acc_tout)
check("predit sous seuil élevé -> ABSTENTION possible",
      ens.predit({m: 0.5 for m in test_s}, 0.9)[0] == ABSTENTION)
check("trop peu de données -> None", E.ajuste_ensemble({"A": [0.5, 0.6]}, [0, 1]) is None)

print(f"\nENSEMBLE CALIBRÉ VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
