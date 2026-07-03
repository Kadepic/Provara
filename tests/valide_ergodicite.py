"""
VALIDATION de l'ERGODICITÉ (ergodicite.py). Vérifie moyenne d'ensemble (arithmétique) et taux temporel (géométrique),
l'inégalité géo ≤ arithm, le caractère NON-ERGODIQUE du processus multiplicatif (E[X] croît mais la trajectoire typique
décroît vers 0 ; le taux empirique d'une trajectoire ≈ taux temporel), l'ergodicité du processus ADDITIF (moyenne
temporelle ≈ moyenne d'ensemble), le DÉMASQUE (décider sur E[X] = sur-confiant), et l'ABSTENTION. Pur Python, rng seedé.
"""
from __future__ import annotations

import math
import random
import statistics

from garde_ressources import borne
import ergodicite as ER
from ergodicite import ABSTENTION, ERGO

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


rng = random.Random(93)
fac, pr = [1.5, 0.6], [0.5, 0.5]

# ─── 1. Moyenne d'ensemble et taux temporel ───
print("=== Moyenne d'ensemble (arithm.) et taux temporel (géom.) ===")
me = ER.moyenne_ensemble(fac, pr); tt = ER.taux_croissance_temporel(fac, pr)
print(f"   ensemble={me:.4f} ; temporel={tt:.4f}")
check("moyenne d'ensemble = Σ p·f = 1.05", abs(me - 1.05) < 1e-9)
check("taux temporel = exp(Σ p·ln f) = √0.9 ≈ 0.9487", abs(tt - math.sqrt(0.9)) < 1e-9)
check("géométrique ≤ arithmétique (Jensen/AM-GM)", tt <= me)

# ─── 2. NON-ergodique : E[X] croît mais la trajectoire typique décroît ───
print("=== Multiplicatif NON-ergodique : moyenne croît, médiane → 0 ===")
finals = [ER.trajectoire_multiplicative(rng, fac, pr, 150) for _ in range(6000)]
moy = statistics.mean(finals); med = statistics.median(finals)
print(f"   après 150 pas : moyenne={moy:.2e} (>1, croît) ; médiane={med:.2e} (→0, ruine)")
check("moyenne d'ensemble (richesse) CROÎT (>1)", moy > 1)
check("médiane (trajectoire typique) → 0 (ruine)", med < 0.01)

# ─── 3. Le taux empirique d'une trajectoire ≈ taux temporel ───
print("=== Taux empirique d'une trajectoire ≈ taux temporel ===")
T = 4000
taux_emp = statistics.median(ER.trajectoire_multiplicative(rng, fac, pr, T) ** (1 / T) for _ in range(40))
print(f"   taux empirique (w_T^(1/T)) ≈ {taux_emp:.4f} vs théorie {tt:.4f}")
check("le taux vécu par une trajectoire ≈ taux temporel (≠ ensemble)", abs(taux_emp - tt) < 0.02)

# ─── 4. Processus ADDITIF : ERGODIQUE (temps ≈ ensemble) ───
print("=== Additif : ergodique (moyenne temporelle ≈ moyenne d'ensemble) ===")
inc, pri = [+2.0, -1.0], [0.5, 0.5]
ens_add = sum(p * d for p, d in zip(pri, inc))      # = 0.5
T2 = 50000
moy_temp = statistics.median(ER.trajectoire_additive(rng, inc, pri, T2) / T2 for _ in range(20))
print(f"   ensemble (E[incrément])={ens_add} ; moyenne temporelle (x_T/T)≈{moy_temp:.3f}")
check("processus additif : moyenne temporelle ≈ moyenne d'ensemble (ergodique)", abs(moy_temp - ens_add) < 0.03)

# ─── 5. DÉMASQUE : E[X] croît mais trajectoire décroît (signes opposés) ───
print("=== Mode d'échec : décider sur l'espérance d'ensemble ===")
st, info = ER.analyse(fac, pr)
check("ensemble croît (>1) MAIS temps décroît (<1) : signes opposés", info["ensemble_croit"] and not info["temps_croit"])
check("processus jugé NON-ergodique", info["non_ergodique"])
check("formule signale la sur-confiance de l'espérance", "sur-confiant" in ER.formule((st, info)))

# ─── 6. Cas ergodique dégénéré (volatilité nulle) → ensemble = temps ───
print("=== Sans volatilité : ensemble = temps ===")
st2, info2 = ER.analyse([1.1, 1.1], [0.5, 0.5])
check("facteur constant → moyenne ensemble = taux temporel", abs(info2["moyenne_ensemble"] - info2["taux_temporel"]) < 1e-9)

# ─── 7. ABSTENTION ───
print("=== ABSTENTION ===")
st3, _ = ER.analyse([1.5, -0.6], [0.5, 0.5])     # facteur négatif
st4, _ = ER.analyse([1.5, 0.6], [0.7, 0.7])      # probas non normalisées
check("facteur ≤ 0 → ABSTENTION", st3 == ABSTENTION)
check("probas non normalisées → ABSTENTION", st4 == ABSTENTION)
st5, _ = ER.analyse(fac, pr)
check("cas valide → ERGO", st5 == ERGO)

print(f"\nRÉSULTAT ergodicite : {ok}/{total}")
assert ok == total
