"""
VALIDATION du MOYENNAGE BAYÉSIEN DE MODÈLES (bma.py) — jugé par calibration.py. Vrai modèle LINÉAIRE, candidats
polynomiaux deg 1/2/3 re-sélectionnés à chaque jeu. À l'EXTRAPOLATION (où les modèles divergent), l'intervalle du
« meilleur modèle unique » SOUS-couvre (incertitude de sélection ignorée = sur-confiance) ; l'intervalle BMA (variance
intra+inter) couvre ≈ nominal. En interpolation, les deux sont corrects (le défaut est spécifique à l'incertitude de
modèle). Quand un modèle domine nettement (gros n, faible bruit), BMA ≈ meilleur (aucun prix superflu).
"""
from __future__ import annotations

import random

from garde_ressources import borne
import bma as B
from bma import ESTIMATION, ABSTENTION
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


A, PENTE, SIGMA = 2.0, 1.5, 1.0


def vrai(x):
    return A + PENTE * x


def jeu(rng, n):
    xs = [rng.uniform(0, 2) for _ in range(n)]
    ys = [vrai(x) + rng.gauss(0, SIGMA) for x in xs]
    return xs, ys


NOM = 0.90
N_DATA = 1000
n = 30


def couverture_a(x0, rng):
    iv_bma, iv_best, ver = [], [], []
    for _ in range(N_DATA):
        xs, ys = jeu(rng, n)
        st, etat, _ = B.ajuste(xs, ys, (1, 2, 3))
        if st != ESTIMATION:
            continue
        iv_bma.append(B.intervalle_bma(etat, x0, NOM)[1])
        iv_best.append(B.intervalle_meilleur(etat, x0, NOM)[1])
        ver.append(vrai(x0) + rng.gauss(0, SIGMA))     # fresh y0
    vB, iB = CAL.verdict_couverture(iv_bma, ver, NOM)
    vS, iS = CAL.verdict_couverture(iv_best, ver, NOM)
    return (vB, iB["couverture"]), (vS, iS["couverture"])


print("=== EXTRAPOLATION x0=2.8 : meilleur-modèle SOUS-couvre, BMA couvre ===")
rng = random.Random(5)
(vB, cB), (vS, cS) = couverture_a(2.8, rng)
print(f"   BMA={cB:.3f} ({vB}) ; meilleur modèle={cS:.3f} ({vS})")
check("BMA : couverture ~nominal (>=0.87) et NON sur-confiant", cB >= 0.87 and vB != SURCONFIANT)
check("meilleur modèle unique : SUR-CONFIANT à l'extrapolation (<0.87)", vS == SURCONFIANT and cS < 0.87)
check("BMA couvre strictement mieux que le meilleur unique", cB > cS)

print("=== INTERPOLATION x0=1.0 : les deux corrects (défaut spécifique à l'incertitude de modèle) ===")
rng2 = random.Random(6)
(vB2, cB2), (vS2, cS2) = couverture_a(1.0, rng2)
print(f"   BMA={cB2:.3f} ({vB2}) ; meilleur modèle={cS2:.3f} ({vS2})")
check("en interpolation, le meilleur modèle n'est PAS sur-confiant", vS2 != SURCONFIANT)
check("en interpolation, BMA reste calibré", vB2 != SURCONFIANT)

print("=== Modèle DOMINANT (gros n, faible bruit) : BMA ≈ meilleur (aucun prix superflu) ===")
rng3 = random.Random(8)
xs = [rng3.uniform(0, 2) for _ in range(300)]
ys = [vrai(x) + rng3.gauss(0, 0.3) for x in xs]
st, etat, _ = B.ajuste(xs, ys, (1, 2, 3))
wmax = max(etat["poids"])
mb, ib = B.intervalle_bma(etat, 2.8, NOM)
mu, iu = B.intervalle_meilleur(etat, 2.8, NOM)
larg_bma, larg_best = ib[1] - ib[0], iu[1] - iu[0]
print(f"   poids={[round(w,3) for w in etat['poids']]} ; largeur BMA={larg_bma:.2f} vs meilleur={larg_best:.2f}")
check("un modèle domine (poids max > 0.8)", wmax > 0.8)
check("BMA ≈ meilleur quand un modèle domine (largeurs proches, <1.5×)", larg_bma < 1.5 * larg_best)

print("=== ABSTENTION si trop peu de points ===")
st2, _, raison = B.ajuste([0, 1, 2], [0, 1, 2])
print(f"   {st2} : {raison}")
check("ABSTENTION sous N_MIN", st2 == ABSTENTION)

print(f"\nRÉSULTAT bma : {ok}/{total}")
assert ok == total
