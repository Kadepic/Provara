"""
VALIDATION de la CALIBRATION DE SÉQUENCE (calibration_sequence.py) — jugée par calibration.py. Un modèle sur-confiant
PAR ÉTAPE produit une confiance de SÉQUENCE (produit) massivement sur-confiante (le biais se compose) ; la
recalibration isotonique par étape restaure une confiance de séquence calibrée (P(tout correct) ≈ confiance annoncée).
"""
from __future__ import annotations

import random

from garde_ressources import borne
import calibration_sequence as S
from calibration_sequence import ESTIMATION, ABSTENTION
import calibration as CAL
from calibration import SURCONFIANT, CALIBRE

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


L = 5
T_OVER = 0.45               # confiance rapportée c = q**T_OVER > q  (sur-confiance par étape)


def fabrique(rng, n):
    seqs = []
    for _ in range(n):
        confs, justes = [], []
        for _ in range(L):
            q = rng.uniform(0.6, 0.98)
            confs.append(q ** T_OVER)
            justes.append(1 if rng.random() < q else 0)
        seqs.append((confs, justes))
    return seqs


rng = random.Random(1)
calib = fabrique(rng, 500)
plates_c = [c for confs, _ in calib for c in confs]
plates_j = [j for _, justes in calib for j in justes]
cal = S.ajuste_par_etape(plates_c, plates_j)
test = fabrique(rng, 3000)

cb, jb, ck, jk, cf, jf = [], [], [], [], [], []
for confs, justes in test:
    seq_ok = 1.0 if all(justes) else 0.0
    cb.append(S.confiance_sequence(confs)); jb.append(seq_ok)
    ck.append(S.confiance_sequence_calibree(cal, confs)[1]); jk.append(seq_ok)
    cf.append(confs[0]); jf.append(seq_ok)            # confiance d'UNE seule étape comme proxy de séquence

vB, iB = CAL.est_calibre(cb, jb)
vK, iK = CAL.est_calibre(ck, jk)
vF, iF = CAL.est_calibre(cf, jf)

print("=== Confiance de séquence BRUTE (produit de confiances sur-confiantes) = SUR-CONFIANTE ===")
print(f"   brut : verdict={vB}, ECE={iB['ece']:.3f}")
check("confiance de séquence brute SUR-CONFIANTE", vB == SURCONFIANT and iB["ece"] > 0.10)

print("=== Recalibration par étape -> confiance de séquence CALIBRÉE ===")
print(f"   recalibré : verdict={vK}, ECE={iK['ece']:.3f}")
check("confiance de séquence recalibrée NON surconfiante et ECE faible (<0.06)", vK != SURCONFIANT and iK["ece"] < 0.06)
check("recalibration réduit fortement l'ECE (>2x)", iK["ece"] < iB["ece"] / 2)

print("=== Prendre UNE étape pour la séquence est aussi SUR-CONFIANT (ignore que tout doit être juste) ===")
print(f"   1ʳᵉ étape comme proxy : verdict={vF}, ECE={iF['ece']:.3f}")
check("confiance d'une seule étape : SUR-CONFIANTE pour la séquence", vF == SURCONFIANT)

print("=== Cohérence : produit de probas calibrées <= chaque proba d'étape ===")
confs = [0.9, 0.85, 0.8]
pc = 1.0
for c in confs:
    pc *= cal.applique(c)
check("confiance de séquence <= plus petite confiance d'étape calibrée", pc <= min(cal.applique(c) for c in confs) + 1e-9)

print("=== ABSTENTION si jeu de calibration trop petit ===")
res = S.confiance_sequence_calibree(None, [0.9, 0.9])
print(f"   {res[0]}")
check("ABSTENTION sans calibrateur", res[0] == ABSTENTION)

print(f"\nRÉSULTAT calibration_sequence : {ok}/{total}")
assert ok == total
