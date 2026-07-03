"""
VALIDATION de la MÉTA-ANALYSE (meta_analyse.py) — jugée par calibration.py. Sous HÉTÉROGÉNÉITÉ, l'IC à effets
ALÉATOIRES couvre le vrai effet ~confiance ; l'effet FIXE sous-couvre (SURCONFIANT). τ²/I² détectent l'hétérogénéité.
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import meta_analyse as M
from meta_analyse import ESTIMATION, ABSTENTION
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


MU = 0.5


def etudes(k, tau, rng):
    """k études : effet vrai μ_i = μ + N(0,τ) (inter-études), observé θ_i = μ_i + N(0, se_i)."""
    effets, se = [], []
    for _ in range(k):
        s = 0.08 + 0.22 * rng.random()
        mu_i = MU + rng.gauss(0, tau)
        effets.append(mu_i + rng.gauss(0, s))
        se.append(s)
    return effets, se


def couverture(tau, modele, conf, M_runs, graine):
    rng = random.Random(graine)
    inter, ver = [], []
    for _ in range(M_runs):
        eff, se = etudes(20, tau, rng)
        st, infos = M.meta_analyse(eff, se, conf, modele)
        if st == ESTIMATION:
            inter.append(infos["ic"]); ver.append(MU)
    return CAL.verdict_couverture(inter, ver, conf)


print("=== HÉTÉROGÉNÉITÉ (τ=0.2) : ALÉATOIRE couvre, FIXE sous-couvre (SURCONFIANT) ===")
v_re, i_re = couverture(0.2, "aleatoire", 0.95, 3000, graine=1)
v_fe, i_fe = couverture(0.2, "fixe", 0.95, 3000, graine=1)
print(f"   aléatoire couverture={i_re['couverture']:.3f} ({v_re}) ; fixe={i_fe['couverture']:.3f} ({v_fe})")
check(f"effets aléatoires : couverture {i_re['couverture']:.3f} >= 0.91 et NON surconfiant",
      i_re["couverture"] >= 0.91 and v_re != SURCONFIANT)
check(f"effet fixe sous hétérogénéité : SOUS-COUVRE {i_fe['couverture']:.3f} -> SURCONFIANT", v_fe == SURCONFIANT)

print("=== HOMOGÈNE (τ=0) : les deux couvrent, τ²≈0 ===")
v_h, i_h = couverture(0.0, "aleatoire", 0.95, 2000, graine=2)
check(f"homogène aléatoire : couverture {i_h['couverture']:.3f} >= 0.92, NON surconfiant",
      i_h["couverture"] >= 0.92 and v_h != SURCONFIANT)

print("=== τ² et I² DÉTECTENT l'hétérogénéité ===")
rng = random.Random(3)
# fortement hétérogène
tau2_het = sum(M.meta_analyse(*etudes(20, 0.3, rng)[:2], 0.95)[1]["tau2"] for _ in range(30)) / 30
# homogène
tau2_hom = sum(M.meta_analyse(*etudes(20, 0.0, rng)[:2], 0.95)[1]["tau2"] for _ in range(30)) / 30
print(f"   τ² moyen : hétérogène={tau2_het:.4f} ; homogène={tau2_hom:.4f}")
check(f"τ² hétérogène >> homogène ({tau2_het:.4f} > {tau2_hom:.4f})", tau2_het > tau2_hom + 0.02)
eff, se = etudes(20, 0.3, random.Random(9))
infos = M.meta_analyse(eff, se, 0.95)[1]
check(f"I² élevé sous forte hétérogénéité ({infos['I2']:.2f} > 0.3)", infos["I2"] > 0.3)

print("=== effet global ≈ vrai μ + ABSTENTION ===")
moy_eff = sum(M.meta_analyse(*etudes(20, 0.2, random.Random(s))[:2], 0.95)[1]["effet"] for s in range(50)) / 50
check(f"effet global moyen ≈ μ ({moy_eff:.3f} ≈ {MU})", abs(moy_eff - MU) < 0.05)
check("< 2 études -> ABSTENTION", M.meta_analyse([0.5], [0.1])[0] == ABSTENTION)
check("erreur-type ≤ 0 -> ABSTENTION", M.meta_analyse([0.5, 0.3], [0.1, 0.0])[0] == ABSTENTION)

print(f"\nMÉTA-ANALYSE VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
