"""
VALIDATION des IC SIMULTANÉS MULTINOMIAUX (multinomial_simultane.py) — jugés par calibration.py. Multinomial à K=6
parts, n=200, tirages répétés : la couverture CONJOINTE (toutes les vraies parts dans leurs intervalles à la fois) des
K intervalles MARGINAUX à 1−α S'EFFONDRE (sur-confiance par multiplicité) ; celle des intervalles SIMULTANÉS
(Bonferroni, Quesenberry-Hurst) ≈/≥ nominal. Marginalement, chaque intervalle marginal couvre bien sa part (~1−α) : le
défaut est CONJOINT, pas individuel.
"""
from __future__ import annotations

import random

from garde_ressources import borne
import multinomial_simultane as M
from multinomial_simultane import ESTIMATION, ABSTENTION
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


P_VRAI = [0.30, 0.25, 0.18, 0.12, 0.10, 0.05]      # K = 6
N = 200
NOM = 0.95
N_REP = 3000


def tire_multinomial(rng):
    comptes = [0] * len(P_VRAI)
    cum = []
    s = 0.0
    for p in P_VRAI:
        s += p; cum.append(s)
    for _ in range(N):
        u = rng.random()
        for k, c in enumerate(cum):
            if u <= c:
                comptes[k] += 1
                break
        else:
            comptes[-1] += 1
    return comptes


def joint_couvre(intervalles_, p_vrai):
    return all(lo <= p_vrai[k] <= hi for k, (lo, hi) in enumerate(intervalles_))


def couverture_conjointe(methode, rng):
    """Renvoie (verdict, couverture) de l'événement CONJOINT, et la couverture marginale de la 1ʳᵉ catégorie."""
    sc, ver = [], []
    marg0_couv = 0
    for _ in range(N_REP):
        c = tire_multinomial(rng)
        ivs = M.intervalles(c, NOM, methode)[1]
        sc.append((0.0, 1.0))
        ver.append(0.0 if joint_couvre(ivs, P_VRAI) else 2.0)   # 0 si conjoint couvert, 2 sinon
        if ivs[0][0] <= P_VRAI[0] <= ivs[0][1]:
            marg0_couv += 1
    v, i = CAL.verdict_couverture(sc, ver, NOM)
    return v, i["couverture"], marg0_couv / N_REP


print(f"=== K={len(P_VRAI)} parts, n={N}, nominal {NOM} — couverture CONJOINTE ===")
rng = random.Random(4)
vM, cM, marg_m = couverture_conjointe("marginaux", rng)
vB, cB, marg_b = couverture_conjointe("bonferroni", rng)
vQ, cQ, _ = couverture_conjointe("quesenberry_hurst", rng)
print(f"   marginaux : conjoint={cM:.3f} ({vM}) ; Bonferroni : conjoint={cB:.3f} ({vB}) ; "
      f"Ques.-Hurst : conjoint={cQ:.3f} ({vQ})")
check("marginaux à 1−α : SUR-CONFIANTS sur l'événement conjoint (<0.92)", vM == SURCONFIANT and cM < 0.92)
check("Bonferroni : couverture conjointe ~/≥ nominal (>=0.93) et NON sur-confiant", cB >= 0.93 and vB != SURCONFIANT)
check("Quesenberry-Hurst : couverture conjointe ≥ nominal (>=0.93) et NON sur-confiant", cQ >= 0.93 and vQ != SURCONFIANT)
check("simultané couvre strictement mieux que marginal", cB > cM)

print("=== Le défaut est CONJOINT : chaque intervalle MARGINAL couvre bien sa part (~1−α) ===")
print(f"   couverture marginale (catégorie 0), méthode marginaux = {marg_m:.3f}")
check("intervalle marginal correct individuellement (~0.95, >=0.93)", marg_m >= 0.93)

print("=== Largeurs : marginal < Bonferroni < Quesenberry-Hurst ===")
comptes = [60, 50, 36, 24, 20, 10]
lm = sum(hi - lo for lo, hi in M.marginaux(comptes, NOM)) / len(comptes)
lb = sum(hi - lo for lo, hi in M.simultanes_bonferroni(comptes, NOM)) / len(comptes)
lq = sum(hi - lo for lo, hi in M.simultanes_quesenberry_hurst(comptes, NOM)) / len(comptes)
print(f"   largeurs moyennes : marginal={lm:.3f} < Bonferroni={lb:.3f} < QH={lq:.3f}")
check("largeur marginal < Bonferroni < Quesenberry-Hurst", lm < lb < lq)

print("=== ABSTENTION si n=0 ou < 2 catégories ===")
st0, _, r0 = M.intervalles([0, 0], NOM)
st1, _, r1 = M.intervalles([10], NOM)
print(f"   n=0 -> {st0} ; 1 cat -> {st1}")
check("ABSTENTION sur n=0", st0 == ABSTENTION)
check("ABSTENTION sur < 2 catégories", st1 == ABSTENTION)

print(f"\nRÉSULTAT multinomial_simultane : {ok}/{total}")
assert ok == total
