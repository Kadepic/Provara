"""
VALIDATION du MAXIMUM D'ENTROPIE (maximum_entropie.py). Vérifie : sans contrainte → uniforme (H=ln K), la maxent
respecte la contrainte E[f]=μ et est dans la famille exponentielle, qu'elle MAXIMISE l'entropie (toute perturbation
respectant la contrainte baisse H ; la loi 2-points a H plus faible), le DÉMASQUE (une loi de plus faible entropie
assigne 0 à des issues possibles → surprise/KL infinie = sur-confiance), que chaque contrainte réduit l'entropie, et
l'ABSTENTION. Pur Python, léger.
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import maximum_entropie as ME
from maximum_entropie import ABSTENTION, MAXENT

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


rng = random.Random(80)
fs = [0, 1, 2, 3, 4, 5]
K = len(fs)


def moyenne(p):
    return sum(pi * f for pi, f in zip(p, fs))


# ─── 1. Sans contrainte → uniforme (H = ln K) ───
print("=== Sans contrainte → uniforme, H = ln K ===")
st, info = ME.analyse(fs, None)
check("maxent sans contrainte = uniforme", all(abs(pi - 1 / K) < 1e-12 for pi in info["p"]))
check("H = ln K (entropie maximale)", abs(info["entropie"] - math.log(K)) < 1e-9)

# ─── 2. Maxent respecte la contrainte + famille exponentielle ───
print("=== Maxent respecte E[f]=μ et est exponentielle ===")
mu = 3.7
p = ME.maxent_moyenne(fs, mu)
check("E[f] = μ (contrainte satisfaite)", abs(moyenne(p) - mu) < 1e-6)
# ln pᵢ = λ fᵢ + c → pente (ln pᵢ − ln p₀)/(fᵢ − f₀) constante
pentes = [(math.log(p[i]) - math.log(p[0])) / (fs[i] - fs[0]) for i in range(1, K)]
check("famille exponentielle : ln pᵢ linéaire en fᵢ (pente constante = λ)", max(pentes) - min(pentes) < 1e-6)

# ─── 3. Maxent MAXIMISE l'entropie : toute perturbation admissible baisse H ───
print("=== Maxent maximise H : perturbations respectant la contrainte baissent H ===")
def perturbation(rng):
    r = [rng.gauss(0, 1) for _ in range(K)]
    # projeter r hors de span{1, f} : δ = r − α·1 − β·f avec Σδ=0 et Σδf=0
    S1, Sf, Sff = float(K), float(sum(fs)), float(sum(x * x for x in fs))
    Sr, Srf = sum(r), sum(r[i] * fs[i] for i in range(K))
    det = S1 * Sff - Sf * Sf
    alpha = (Sr * Sff - Srf * Sf) / det
    beta = (S1 * Srf - Sf * Sr) / det
    return [r[i] - alpha - beta * fs[i] for i in range(K)]
viol = 0
for _ in range(3000):
    d = perturbation(rng)
    nd = max(abs(x) for x in d)
    eps = 0.05 / nd if nd > 0 else 0
    q = [p[i] + eps * d[i] for i in range(K)]
    if all(qi > 0 for qi in q):
        if ME.entropie(q) > info["entropie"] + 1e-12 and abs(moyenne(q) - mu) < 1e-9:
            # q viole la contrainte ? non par construction. H(q) ne doit pas dépasser H(maxent)
            pass
        if ME.entropie(q) > ME.entropie(p) + 1e-9:
            viol += 1
check("aucune perturbation admissible n'augmente H au-dessus du maxent (0 violation)", viol == 0)
check("la loi 2-points (même μ) a une entropie plus faible", ME.entropie(ME.deux_points(fs, mu)) < ME.entropie(p))

# ─── 4. DÉMASQUE : une loi plus piquée assigne 0 à des issues possibles (surprise infinie) ───
print("=== Mode d'échec : loi de plus faible entropie = sur-confiance punie ===")
p2 = ME.deux_points(fs, mu)
zeros = [i for i in range(K) if p2[i] == 0 and p[i] > 0]
print(f"   loi 2-points : H={ME.entropie(p2):.3f} (< maxent {ME.entropie(p):.3f}) ; issues à proba 0 mais possibles : {zeros}")
check("la loi sur-confiante assigne 0 à des issues que la maxent juge possibles", len(zeros) > 0)
# KL(maxent ‖ 2-points) = ∞ (surprise infinie si une de ces issues survient)
def kl(a, b):
    s = 0.0
    for ai, bi in zip(a, b):
        if ai > 0:
            s += ai * math.log(ai / bi) if bi > 0 else math.inf
    return s
check("KL(maxent ‖ 2-points) = ∞ (adopter la loi piquée = surprise infinie possible)", math.isinf(kl(p, p2)))
check("KL(maxent ‖ uniforme) fini (maxent ne ferme aucune issue)", math.isfinite(kl(p, ME.uniforme(K))))

# ─── 5. Chaque contrainte réduit l'entropie ; μ extrême → H → 0 ───
print("=== Information = entropie qui baisse ; μ extrême → H → 0 ===")
H_libre = ME.entropie(ME.uniforme(K))
H_mu = ME.entropie(ME.maxent_moyenne(fs, 3.5))
H_extreme = ME.entropie(ME.maxent_moyenne(fs, 4.9))
print(f"   H : libre={H_libre:.3f} > μ=3.5 → {H_mu:.3f} > μ=4.9 → {H_extreme:.3f}")
check("une contrainte réduit l'entropie (information gagnée)", H_mu < H_libre)
check("μ proche de l'extrême → entropie → 0", H_extreme < 0.5)

# ─── 6. ABSTENTION ───
print("=== ABSTENTION ===")
st1, _ = ME.analyse([], None)
st2, _ = ME.analyse(fs, 10.0)
check("support vide → ABSTENTION", st1 == ABSTENTION)
check("μ hors [min f, max f] → ABSTENTION", st2 == ABSTENTION)
st3, _ = ME.analyse(fs, 2.0)
check("cas valide → MAXENT", st3 == MAXENT)

print(f"\nRÉSULTAT maximum_entropie : {ok}/{total}")
assert ok == total
