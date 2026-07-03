"""
VALIDATION de l'INTERVALLE DE TOLÉRANCE (intervalle_tolerance.py) — jugé par calibration.py. Population N(71,5), n=20,
tirages répétés. Le CONTENU d'un intervalle = proportion de la population qu'il couvre. Garantie (β=0.90, γ=0.95) : la
fraction d'échantillons où le contenu ≥ β doit être ≥ γ. L'intervalle de TOLÉRANCE tient cette garantie ; le naïf
x̄±z_β·s tombe sous β trop souvent (SUR-CONFIANT) ; l'IC de la MOYENNE a un contenu dérisoire (il ne borne pas les
individus).
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import intervalle_tolerance as T
from intervalle_tolerance import ESTIMATION, ABSTENTION
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


MU, SIGMA = 71.0, 5.0
BETA, GAMMA = 0.90, 0.95
N = 20
N_REP = 3000


def contenu(lo, hi):
    """Proportion de la vraie population N(MU,SIGMA) dans [lo, hi]."""
    return T._Phi((hi - MU) / SIGMA) - T._Phi((lo - MU) / SIGMA)


rng = random.Random(4)
inter_tol, inter_naif, inter_moy, ct_tol, ct_naif, ct_moy = [], [], [], [], [], []
for _ in range(N_REP):
    data = [rng.gauss(MU, SIGMA) for _ in range(N)]
    _, (lo, hi), _ = T.intervalle_tolerance(data, BETA, GAMMA)
    ln, hn = T.intervalle_naif(data, BETA)
    lm, hm = T.ic_moyenne(data, GAMMA)
    inter_tol.append((BETA, 1.0)); ct_tol.append(contenu(lo, hi))
    inter_naif.append((BETA, 1.0)); ct_naif.append(contenu(ln, hn))
    inter_moy.append((BETA, 1.0)); ct_moy.append(contenu(lm, hm))

vT, iT = CAL.verdict_couverture(inter_tol, ct_tol, GAMMA)
vN, iN = CAL.verdict_couverture(inter_naif, ct_naif, GAMMA)
vM, iM = CAL.verdict_couverture(inter_moy, ct_moy, GAMMA)

print(f"=== Garantie (β={BETA}, γ={GAMMA}) : P(contenu ≥ β) doit être ≥ γ ===")
print(f"   tolérance : P(contenu≥β)={iT['couverture']:.3f} ({vT}) ; naïf : {iN['couverture']:.3f} ({vN}) ; "
      f"IC moyenne : {iM['couverture']:.3f} ({vM})")
check("intervalle de tolérance : tient la garantie (P≥γ, >=0.93) et NON sur-confiant", iT["couverture"] >= 0.93 and vT != SURCONFIANT)
check("naïf x̄±z_β·s : SUR-CONFIANT (tombe sous β trop souvent, P<0.93)", vN == SURCONFIANT and iN["couverture"] < 0.93)
check("IC de la moyenne : catastrophiquement SUR-CONFIANT pour les individus", vM == SURCONFIANT and iM["couverture"] < 0.5)

print("=== Contenu MOYEN : tolérance ≥ β ; IC moyenne ≪ β ===")
moy_tol = sum(ct_tol) / len(ct_tol)
moy_moy = sum(ct_moy) / len(ct_moy)
print(f"   contenu moyen : tolérance={moy_tol:.3f} ; IC moyenne={moy_moy:.3f} (β={BETA})")
check("contenu moyen de la tolérance ≥ β", moy_tol >= BETA)
check("contenu moyen de l'IC moyenne ≪ β (ne borne pas les individus)", moy_moy < 0.6)

print("=== Facteur k > z_β (la tolérance est plus large que le naïf) ===")
k = T.facteur_tolerance(N, BETA, GAMMA)
zb = T._invnorm((1 + BETA) / 2)
print(f"   k={k:.3f} vs z_β={zb:.3f}")
check("facteur de tolérance k > z_β", k > zb)

print("=== k DÉCROÎT avec n (moins d'incertitude d'estimation) ===")
check("k(n=10) > k(n=100) (l'incertitude d'estimation se réduit)", T.facteur_tolerance(10, BETA, GAMMA) > T.facteur_tolerance(100, BETA, GAMMA))

print("=== ABSTENTION si trop peu de points ===")
st, _, raison = T.intervalle_tolerance([1.0, 2.0, 3.0], BETA, GAMMA)
print(f"   {st} : {raison}")
check("ABSTENTION sous N_MIN", st == ABSTENTION)

print(f"\nRÉSULTAT intervalle_tolerance : {ok}/{total}")
assert ok == total
