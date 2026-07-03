"""
VALIDATION de la MULTICALIBRATION (multicalibration.py) — jugée par calibration.py appliquée PAR GROUPE. Modèle calibré
GLOBALEMENT mais sur-confiant sur le groupe B (et sous-confiant sur A, ça s'annule en moyenne) : le brut passe « calibré »
au global tout en TROMPANT le groupe B. Après multicalibration (apprise sur un jeu de calibration, évaluée sur un jeu de
test séparé), AUCUN groupe n'est sur-confiant, et le global reste calibré. ABSTENTION si un groupe est trop petit.
"""
from __future__ import annotations

import random

from garde_ressources import borne
import multicalibration as MC
from multicalibration import ESTIMATION, ABSTENTION
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


def echantillon(rng, n):
    probs, ys, grp = [], [], []
    for _ in range(n):
        g = "A" if rng.random() < 0.5 else "B"
        p = rng.uniform(0.2, 0.8)
        taux = min(1.0, p + 0.1) if g == "A" else max(0.0, p - 0.1)   # A sous-confiant, B sur-confiant
        probs.append(p); ys.append(1.0 if rng.random() < taux else 0.0); grp.append(g)
    return probs, ys, grp


def cal_par_groupe(probs, ys, grp, groupe, n_bins=10):
    pp = [probs[i] for i in range(len(grp)) if grp[i] == groupe]
    yy = [ys[i] for i in range(len(grp)) if grp[i] == groupe]
    return CAL.est_calibre(pp, yy, n_bins=n_bins)


rng = random.Random(2)
ptr, ytr, gtr = echantillon(rng, 6000)
pte, yte, gte = echantillon(rng, 6000)

print("=== Modèle BRUT : calibré GLOBALEMENT ===")
vG, iG = CAL.est_calibre(pte, yte, n_bins=10)
print(f"   global brut : {vG}, ECE={iG['ece']:.3f}, écart signé={iG['ecart_signe']:.3f}")
check("modèle brut calibré au GLOBAL (non sur-confiant)", vG != SURCONFIANT)

print("=== Modèle BRUT : SUR-CONFIANT sur le groupe B (sous-confiant sur A) ===")
vB, iB = cal_par_groupe(pte, yte, gte, "B")
vA, iA = cal_par_groupe(pte, yte, gte, "A")
print(f"   groupe B : {vB} (écart {iB['ecart_signe']:.3f}) ; groupe A : {vA} (écart {iA['ecart_signe']:.3f})")
check("groupe B SUR-CONFIANT malgré la calibration globale", vB == SURCONFIANT)

print("=== Après MULTICALIBRATION : aucun groupe sur-confiant ===")
st, modele, _ = MC.ajuste(ptr, ytr, gtr, n_bins=10)
pte_mc = MC.applique_lot(modele, pte, gte)
vBm, iBm = cal_par_groupe(pte_mc, yte, gte, "B")
vAm, iAm = cal_par_groupe(pte_mc, yte, gte, "A")
print(f"   groupe B multicalibré : {vBm} (ECE {iBm['ece']:.3f}) ; groupe A : {vAm} (ECE {iAm['ece']:.3f})")
check("groupe B NON sur-confiant après multicalibration", vBm != SURCONFIANT)
check("groupe A NON sur-confiant après multicalibration", vAm != SURCONFIANT)
check("ECE du groupe B réduit par la multicalibration", iBm["ece"] < iB["ece"])

print("=== Global reste calibré après multicalibration ===")
vGm, iGm = CAL.est_calibre(pte_mc, yte, n_bins=10)
print(f"   global multicalibré : {vGm}, ECE={iGm['ece']:.3f}")
check("global non sur-confiant après multicalibration", vGm != SURCONFIANT)

print("=== ABSTENTION si un groupe est trop petit ===")
pp = [0.5] * 60 + [0.5] * 10
yy = [1.0, 0.0] * 30 + [1.0] * 10
gg = ["A"] * 60 + ["C"] * 10            # C n'a que 10 exemples
st2, _, raison = MC.ajuste(pp, yy, gg, n_bins=10)
print(f"   {st2} : {raison}")
check("ABSTENTION si un sous-groupe < N_MIN_GROUPE", st2 == ABSTENTION)

print(f"\nRÉSULTAT multicalibration : {ok}/{total}")
assert ok == total
