"""
VALIDATION du SOPHISME DE LA CONJONCTION (conjonction.py). Vérifie : les bornes de Fréchet ; la détection du sophisme
P(A∧B)>P(A) ; le LIVRE HOLLANDAIS (perte sûre de l'agent dans TOUS les états, vérifiée explicitement) ; l'absence de
livre pour un jugement cohérent ; la monotonie sur des triplets aléatoires cohérents/incohérents (rng seedé) ;
l'ABSTENTION. Pur Python, rng seedé.
"""
from __future__ import annotations

import random

from garde_ressources import borne
import conjonction as CJ
from conjonction import ABSTENTION, ANALYSE

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


# ─── 1. Bornes de Fréchet ───
print("=== Bornes de Fréchet ===")
lo, hi = CJ.bornes_frechet(0.2, 0.7)
print(f"   P(A)=0.2, P(B)=0.7 → P(A∧B) ∈ [{lo:.2f}, {hi:.2f}]")
check("borne haute = min(pA,pB)", abs(hi - 0.2) < 1e-9)
check("borne basse = max(0, pA+pB−1)", abs(lo - 0.0) < 1e-9)
lo2, hi2 = CJ.bornes_frechet(0.8, 0.7)
check("borne basse non triviale = pA+pB−1 quand >0", abs(lo2 - 0.5) < 1e-9)

# ─── 2. Détection du sophisme ───
print("=== Détection du sophisme de Linda ===")
st, info = CJ.analyse(0.2, 0.7, 0.4)
check("P(A∧B)=0.4 > P(A)=0.2 détecté comme sophisme", info["sophisme"])
check("le jugement est jugé incohérent", not info["coherent"])

# ─── 3. Livre hollandais : perte sûre dans TOUS les états ───
print("=== Livre hollandais : perte sûre ===")
pA, pAB = 0.2, 0.4
profit = CJ.livre_hollandais(pA, pAB)
print(f"   profit garanti du teneur = {profit:.2f}")
check("le profit garanti du teneur = pAB − pA > 0", abs(profit - (pAB - pA)) < 1e-9 and profit > 0)
# reconstruction explicite : perte de l'agent dans chaque état ≥ profit
cash = pA - pAB
etats = {"A∧B": 1 - 1, "A∧¬B": 0 - 1, "¬A": 0}
pertes = {e: -(cash + d) for e, d in etats.items()}
print(f"   perte de l'agent par état : {({e: round(v,2) for e,v in pertes.items()})}")
check("l'agent perd au moins le profit garanti dans CHAQUE état", all(v >= profit - 1e-9 for v in pertes.values()))

# ─── 4. Jugement cohérent : aucun livre hollandais ───
print("=== Jugement cohérent : pas de livre hollandais ===")
stc, infoc = CJ.analyse(0.2, 0.7, 0.15)
check("jugement cohérent (pAB ≤ pA, dans Fréchet)", infoc["coherent"] and not infoc["sophisme"])
check("aucun profit garanti pour le teneur (≤ 0)", infoc["profit_livre_hollandais"] <= 1e-9)

# ─── 5. Monotonie sur triplets aléatoires (rng seedé) ───
print("=== Monotonie sur triplets aléatoires ===")
rng = random.Random(110)
incoherents_detectes = coherents_ok = 0
for _ in range(5000):
    pA = rng.random()
    pB = rng.random()
    lo, hi = CJ.bornes_frechet(pA, pB)
    # triplet cohérent : pAB dans les bornes
    pAB_ok = rng.uniform(lo, hi)
    if not CJ.coherent(pA, pB, pAB_ok):
        raise AssertionError("triplet dans Fréchet jugé incohérent")
    coherents_ok += 1
    # triplet incohérent : pAB au-dessus de min(pA,pB)
    if hi < 1:
        pAB_bad = rng.uniform(hi + 1e-6, 1.0)
        if CJ.coherent(pA, pB, pAB_bad):
            raise AssertionError("triplet hors Fréchet jugé cohérent")
        incoherents_detectes += 1
print(f"   {coherents_ok} cohérents acceptés ; {incoherents_detectes} incohérents rejetés")
check("tous les triplets dans Fréchet sont acceptés", coherents_ok == 5000)
check("tous les triplets au-dessus de min(pA,pB) sont rejetés", incoherents_detectes > 4000)

# ─── 6. Façade & ABSTENTION ───
print("=== Façade & ABSTENTION ===")
check("formule signale la sur-confiance du sophisme", "sur-confiant" in CJ.formule((st, info)))
check("probabilité hors [0,1] → ABSTENTION", CJ.analyse(1.2, 0.5, 0.3)[0] == ABSTENTION)
check("cas valide → ANALYSE", st == ANALYSE)

print(f"\nRÉSULTAT conjonction : {ok}/{total}")
assert ok == total
