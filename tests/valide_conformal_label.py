"""
VALIDATION du CONFORME LABEL-CONDITIONAL (conformal_label.py). Invariant : la couverture du vrai label ≥ 1−α POUR
CHAQUE classe (y compris les rares), là où le conforme MARGINAL sous-couvre la classe rare.
"""
from __future__ import annotations

import random

from garde_ressources import borne
import conformal_label as CL
import conformal as CF

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


CLASSES = ["frequent", "moyen", "rare"]
POIDS = [0.8, 0.15, 0.05]


def instance(rng):
    """Renvoie (probas_dict, vraie_classe). La classe rare est plus DURE (proba vraie plus basse) -> piège du marginal."""
    u = rng.random(); cum = 0.0; y = CLASSES[-1]
    for c, w in zip(CLASSES, POIDS):
        cum += w
        if u < cum:
            y = c; break
    base = {"frequent": 0.75, "moyen": 0.6, "rare": 0.5}[y]
    pv = max(0.2, min(0.95, random_gauss(rng, base, 0.15)))
    reste = 1 - pv
    d = {c: 0.0 for c in CLASSES}
    d[y] = pv
    autres = [c for c in CLASSES if c != y]
    d[autres[0]] = reste * rng.random()
    d[autres[1]] = reste - d[autres[0]]
    return d, y


def random_gauss(rng, mu, sd):
    return rng.gauss(mu, sd)


def jeu(n, graine):
    rng = random.Random(graine)
    P, Y = [], []
    for _ in range(n):
        d, y = instance(rng)
        P.append(d); Y.append(y)
    return P, Y


P_cal, Y_cal = jeu(6000, graine=1)
P_test, Y_test = jeu(8000, graine=2)

print("=== LABEL-CONDITIONAL : couverture du vrai label ≥ 90% POUR CHAQUE classe ===")
seuils = CL.ajuste_label(P_cal, Y_cal, 0.10)
# couverture par classe = P(vrai ∈ ensemble | vrai = c)
cov_lc = {c: [0, 0] for c in CLASSES}
for d, y in zip(P_test, Y_test):
    ens = CL.ensemble_label(seuils, d)
    cov_lc[y][1] += 1
    if y in ens:
        cov_lc[y][0] += 1
for c in CLASSES:
    cov = cov_lc[c][0] / cov_lc[c][1]
    print(f"   classe '{c}' (n={cov_lc[c][1]}) : couverture {cov:.3f}")
    check(f"label-conditional '{c}' : couverture {cov:.3f} >= 0.87", cov >= 0.87)

print("=== MARGINAL : sous-couvre la classe RARE (l'injustice que label-conditional corrige) ===")
probas_vrai_cal = [d[y] for d, y in zip(P_cal, Y_cal)]
cov_marg = {c: [0, 0] for c in CLASSES}
for d, y in zip(P_test, Y_test):
    st, ens, _ = CF.ensemble_conforme(probas_vrai_cal, d, 0.10)
    cov_marg[y][1] += 1
    if y in ens:
        cov_marg[y][0] += 1
cov_rare_marg = cov_marg["rare"][0] / cov_marg["rare"][1]
cov_rare_lc = cov_lc["rare"][0] / cov_lc["rare"][1]
print(f"   classe 'rare' : marginal {cov_rare_marg:.3f} vs label-conditional {cov_rare_lc:.3f}")
check(f"marginal sous-couvre la rare ({cov_rare_marg:.3f} < label-conditional {cov_rare_lc:.3f})",
      cov_rare_marg < cov_rare_lc)

print("=== ENSEMBLE INFORMATIF + PRUDENCE ===")
tailles = [len(CL.ensemble_label(seuils, d)) for d in P_test[:2000]]
check("taille moyenne d'ensemble < 3 (informatif)", sum(tailles) / len(tailles) < 3.0)
check("classe non calibrée -> incluse (prudence)", "inconnue" in CL.ensemble_label({"a": 0.5}, {"a": 0.9, "inconnue": 0.0}))
check("classe à <10 exemples -> pas de seuil",
      CL.ajuste_label([{"x": 0.9}, {"x": 0.8}], ["x", "x"], 0.1).get("x") is None)

print(f"\nCONFORME LABEL VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
