"""
VALIDATION des SCORES PROPRES (scores_propres.py) — la PROPERNESS (un score minimisé en espérance par la VRAIE
probabilité) + le classement de forecasters + les propriétés du CRPS.
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
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


def durcis(p, k):
    return p ** k / (p ** k + (1 - p) ** k)


print("=== PROPERNESS (exacte) : l'espérance du score est minimisée à p = vraie proba q ===")
# espérance log-loss pour vraie q en annonçant p : −[q ln p + (1−q) ln(1−p)] -> min en p=q.
def esp_logloss(q, p):
    return -(q * math.log(p) + (1 - q) * math.log(1 - p))
def esp_brier(q, p):
    return q * (1 - p) ** 2 + (1 - q) * p ** 2
for q in (0.2, 0.5, 0.8):
    autres = [p for p in [q - 0.2, q - 0.1, q + 0.1, q + 0.2] if 0 < p < 1]
    check(f"log-loss q={q} : min à p=q (vs {len(autres)} alternatives)",
          all(esp_logloss(q, q) < esp_logloss(q, p) for p in autres))
    check(f"Brier q={q} : min à p=q", all(esp_brier(q, q) < esp_brier(q, p) for p in autres))

print("=== PROPERNESS (empirique, l'implémentation) : annoncer q bat annoncer q±0.2 ===")
rng = random.Random(1)
q0 = 0.35
y = [1 if rng.random() < q0 else 0 for _ in range(40000)]
ll_vrai = S.log_loss([q0] * len(y), y)
ll_haut = S.log_loss([q0 + 0.2] * len(y), y)
ll_bas = S.log_loss([q0 - 0.2] * len(y), y)
check(f"log-loss(q={q0}) {ll_vrai:.4f} < log-loss(q+0.2) {ll_haut:.4f} et < log-loss(q-0.2) {ll_bas:.4f}",
      ll_vrai < ll_haut and ll_vrai < ll_bas)

print("=== CLASSEMENT : le forecaster CALIBRÉ arrive en tête (log-loss, Brier) ; sphérique le récompense ===")
q = [rng.random() for _ in range(6000)]
yy = [1 if rng.random() < qi else 0 for qi in q]
sorties = {"calibré": q,
           "sur-confiant": [durcis(p, 3) for p in q],
           "sous-confiant": [durcis(p, 0.4) for p in q],
           "ignorant": [0.5] * len(q)}
for regle in ("log_loss", "brier"):
    classement = S.classe_forecasters(sorties, yy, regle)
    print(f"   {regle}: " + " < ".join(f"{n}({s:.3f})" for n, s in classement))
    check(f"{regle} : 'calibré' est le meilleur (1er)", classement[0][0] == "calibré")
spher = S.classe_forecasters(sorties, yy, "spherique")
check("sphérique (récompense) : 'calibré' est le meilleur (1er)", spher[0][0] == "calibré")

print("=== CRPS : le prédictif CALIBRÉ bat le TROP ÉTROIT et le BIAISÉ (properness, sous-dispersion punie) ===")
rng = random.Random(2)
vt = [rng.gauss(0, 1) for _ in range(3000)]
def ech(mu, sd):
    return [[rng.gauss(mu, sd) for _ in range(60)] for _ in range(len(vt))]
c_cal = S.crps(ech(0, 1), vt)
c_etroit = S.crps(ech(0, 0.3), vt)        # trop sûr de lui (sous-dispersé)
c_biais = S.crps(ech(1.5, 1), vt)         # bien dispersé mais décalé
print(f"   CRPS calibré={c_cal:.3f} ; trop_étroit={c_etroit:.3f} ; biaisé={c_biais:.3f}")
check(f"CRPS calibré < trop étroit ({c_cal:.3f} < {c_etroit:.3f})", c_cal < c_etroit)
check(f"CRPS calibré < biaisé ({c_cal:.3f} < {c_biais:.3f})", c_cal < c_biais)
check("CRPS d'un point unique = |prévision − vérité| (MAE)", abs(S.crps([[3.0]], [5.0]) - 2.0) < 1e-9)
check("CRPS d'un Dirac sur la vérité = 0", abs(S.crps([[7.0] * 5], [7.0])) < 1e-9)

print("=== CAS LIMITES : forecaster parfait, clamp anti-log(0) ===")
check("log-loss parfait (p=y) ≈ 0", S.log_loss([1.0, 0.0, 1.0, 0.0], [1, 0, 1, 0]) < 1e-10)
check("Brier parfait = 0", S.brier([1.0, 0.0, 1.0], [1, 0, 1]) == 0.0)
check("log-loss(p=1, y=0) fini (clamp)", math.isfinite(S.log_loss([1.0], [0])))

print(f"\nSCORES PROPRES VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
