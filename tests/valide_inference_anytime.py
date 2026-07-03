"""
VALIDATION de l'INFÉRENCE ANYTIME-VALID (inference_anytime.py). Invariant : P(∃t : μ hors IC) ≤ α (couverture
UNIFORME EN TEMPS), là où un IC à instant FIXE regardé à chaque pas (peeking) sous-couvre fortement.
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import inference_anytime as A
from inference_anytime import ESTIMATION, ABSTENTION

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


MU, SIGMA, T, TMIN = 0.0, 1.0, 1200, 2
Z = 1.96


def jamais_exclu_cs(alpha, M, graine):
    """Fraction de flux où μ est EXCLU à un moment de la séquence de confiance (devrait être ≤ α)."""
    exclu = 0
    for s in range(M):
        rng = random.Random(graine + s)
        somme = 0.0
        dehors = False
        for t in range(1, T + 1):
            somme += rng.gauss(MU, SIGMA)
            if t < TMIN:
                continue
            moy = somme / t
            r = A.rayon_cs(t, SIGMA, alpha)
            if not (moy - r <= MU <= moy + r):
                dehors = True
                break
        exclu += dehors
    return exclu / M


def jamais_exclu_fixe(alpha, M, graine):
    """Même chose avec un IC à instant FIXE (z·σ/√t) regardé à CHAQUE pas (peeking) -> doit EXPLOSER."""
    z = Z
    exclu = 0
    for s in range(M):
        rng = random.Random(graine + s)
        somme = 0.0
        dehors = False
        for t in range(1, T + 1):
            somme += rng.gauss(MU, SIGMA)
            if t < TMIN:
                continue
            moy = somme / t
            r = z * SIGMA / math.sqrt(t)
            if not (moy - r <= MU <= moy + r):
                dehors = True
                break
        exclu += dehors
    return exclu / M


print("=== COUVERTURE UNIFORME EN TEMPS : la séquence de confiance n'exclut μ qu'avec proba ≤ α ===")
for alpha in (0.05, 0.10):
    fa = jamais_exclu_cs(alpha, 1500, graine=alpha and 1)
    print(f"   alpha={alpha} : P(jamais exclu sur {T} pas) = {fa:.3f}")
    check(f"séquence de confiance : exclusion {fa:.3f} <= alpha ({alpha})", fa <= alpha)

print("=== PEEKING : un IC à instant fixe regardé à chaque pas SOUS-COUVRE largement ===")
fa_fixe = jamais_exclu_fixe(0.05, 1500, graine=777)
print(f"   IC fixe (z/√t) regardé en continu : exclusion = {fa_fixe:.3f} (cible 0.05 EXPLOSÉE)")
check(f"peeking gonfle l'erreur bien au-delà de α ({fa_fixe:.3f} > 0.2)", fa_fixe > 0.2)

print("=== le rayon RÉTRÉCIT avec t (mais plus large que l'IC fixe : prix de la validité anytime) ===")
r10 = A.rayon_cs(10, 1.0, 0.05)
r1000 = A.rayon_cs(1000, 1.0, 0.05)
check(f"rayon décroît ({r1000:.3f} < {r10:.3f})", r1000 < r10)
check("rayon -> petit quand t grand", r1000 < 0.2)
check("rayon anytime > IC fixe au même t (prix de l'anytime)", A.rayon_cs(100, 1.0, 0.05) > Z * 1.0 / math.sqrt(100))

print("=== usage en ligne + ABSTENTION ===")
cs = A.SequenceConfiance(1.0, 0.05)
rng = random.Random(3)
for _ in range(500):
    cs.observe(rng.gauss(0.5, 1.0))
st, (moy, (b, h)), _ = cs.intervalle()
check("usage en ligne : moyenne ≈ 0.5 et μ dans l'IC", abs(moy - 0.5) < 0.2 and b <= 0.5 <= h)
check("aucune observation -> ABSTENTION", A.SequenceConfiance(1.0).intervalle()[0] == ABSTENTION)

print(f"\nINFÉRENCE ANYTIME VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
