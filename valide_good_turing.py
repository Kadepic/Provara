"""
VALIDATION de GOOD-TURING (good_turing.py). Vérifie : la masse manquante N₁/N ≈ masse vraie (simulation) ; la PRÉDICTION
calibrée (la fraction de tirages FRAIS inédits ≈ N₁/N) ; le log-loss naïf INFINI (proba 0 à l'inédit) vs Good-Turing fini ;
Chao1 corrige la richesse vers le haut (proche du vrai S) ; la consistance (masse → 0 avec N) ; l'ABSTENTION. rng seedé.
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import good_turing as GT
from good_turing import ABSTENTION, ANALYSE

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


rng = random.Random(109)
S, s = 5000, 1.1

# ─── 1. Masse manquante de Good-Turing ≈ masse vraie ───
print("=== Masse manquante N₁/N ≈ vraie ===")
comptes, probs = GT.echantillon_zipf(S, s, 3000, rng)
gt = GT.masse_manquante(comptes)
vraie = sum(probs[k] for k in range(len(probs)) if k not in comptes)
print(f"   Good-Turing={gt:.4f} ; vraie={vraie:.4f}")
check("N₁/N estime bien la masse manquante", abs(gt - vraie) < 0.02)

# ─── 2. Prédiction calibrée : fraction de tirages FRAIS inédits ≈ N₁/N ───
print("=== Prédiction calibrée sur des tirages frais ===")
import bisect
cum = []
c = 0.0
for p in probs:
    c += p
    cum.append(c)
vus = set(comptes)
frais = 50000
inedits = 0
for _ in range(frais):
    k = bisect.bisect_left(cum, rng.random())
    if k not in vus:
        inedits += 1
taux_inedit = inedits / frais
print(f"   fraction de tirages frais inédits={taux_inedit:.4f} ; prédiction Good-Turing={gt:.4f}")
check("Good-Turing prédit bien le taux d'inédit sur de nouveaux tirages", abs(taux_inedit - gt) < 0.02)

# ─── 3. Log-loss : naïf INFINI, Good-Turing fini ───
print("=== Log-loss sur l'inédit : naïf infini vs Good-Turing fini ===")
ll_naif = GT.logloss_inedit(comptes, "naive")
ll_gt = GT.logloss_inedit(comptes, "good_turing")
ll_lap = GT.logloss_inedit(comptes, "laplace")
print(f"   log-loss : naïf={ll_naif} ; Good-Turing={ll_gt:.2f} ; Laplace={ll_lap:.2f}")
check("le log-loss naïf (proba 0) est INFINI (sur-confiance maximale)", ll_naif == float("inf"))
check("le log-loss Good-Turing est fini", math.isfinite(ll_gt))
check("le log-loss Laplace est fini", math.isfinite(ll_lap))

# ─── 4. Chao1 corrige la richesse vers le haut ───
print("=== Chao1 corrige la sous-estimation de richesse ===")
S_obs = len(comptes)
chao = GT.richesse_chao1(comptes)
print(f"   espèces vues={S_obs} ; Chao1={chao:.0f} ; vrai S={S}")
check("Chao1 estime plus d'espèces que le nombre observé", chao > S_obs)
check("Chao1 réduit l'écart au vrai S", abs(chao - S) < abs(S_obs - S))

# ─── 5. Consistance : masse manquante → 0 quand N grandit ───
print("=== Consistance : masse manquante décroît avec N ===")
masses = []
for N in (1000, 5000, 20000):
    cN, _ = GT.echantillon_zipf(S, s, N, random.Random(N))
    masses.append(GT.masse_manquante(cN))
print(f"   masse manquante : {[round(m,3) for m in masses]}")
check("la masse manquante décroît quand l'échantillon grandit", masses[0] > masses[1] > masses[2])
check("formule signale la sur-confiance du « proba 0 à l'inédit »", "sur-confiant" in GT.formule(GT.analyse(comptes)))

# ─── 6. ABSTENTION ───
print("=== ABSTENTION ===")
check("échantillon trop petit → ABSTENTION", GT.analyse({0: 3, 1: 2})[0] == ABSTENTION)
check("cas valide → ANALYSE", GT.analyse(comptes)[0] == ANALYSE)

print(f"\nRÉSULTAT good_turing : {ok}/{total}")
assert ok == total
