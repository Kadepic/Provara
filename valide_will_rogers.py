"""
VALIDATION du PHÉNOMÈNE DE WILL ROGERS (will_rogers.py). Vérifie : les DEUX moyennes de groupe montent après migration ;
la moyenne GROUPÉE est strictement invariante ; conservation du multiset (aucune valeur changée/créée) ; robustesse sur
500 instances aléatoires (rng seedé) ; l'analogie de migration de stade médicale ; la distinction d'avec Simpson (pooled
invariant, pas de renversement) ; l'ABSTENTION. Pur Python, rng seedé.
"""
from __future__ import annotations

import random

from garde_ressources import borne
import will_rogers as WR
from will_rogers import ABSTENTION, ANALYSE

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


# ─── 1. Exemple déterministe : les deux moyennes montent, le groupé est invariant ───
print("=== Les deux moyennes montent, le groupé est invariant ===")
A = [50, 60, 70, 80, 90]
B = [10, 20, 30, 40]
st, info = WR.analyse(A, B)
av, ap = info["avant"], info["apres"]
print(f"   A : {av['mA']:.2f}→{ap['mA']:.2f} ; B : {av['mB']:.2f}→{ap['mB']:.2f} ; groupé : {av['groupe']:.2f}→{ap['groupe']:.2f}")
check("la moyenne de A monte", ap["mA"] > av["mA"])
check("la moyenne de B monte", ap["mB"] > av["mB"])
check("la moyenne groupée est strictement invariante", abs(ap["groupe"] - av["groupe"]) < 1e-12)

# ─── 2. Conservation du multiset (aucune valeur changée/créée/détruite) ───
print("=== Conservation : rien n'a réellement changé ===")
A2, B2, mig = WR.migration(A, B)
check("le multiset total est conservé", sorted(A2 + B2) == sorted(A + B))
check("le nombre total d'éléments est conservé", len(A2) + len(B2) == len(A) + len(B))
check("les migrants viennent bien de A et vont vers B", all(m in A for m in mig) and all(m in B2 for m in mig))

# ─── 3. Robustesse sur 500 instances aléatoires (rng seedé) ───
print("=== Robustesse sur instances aléatoires ===")
rng = random.Random(101)
n_valides = 0
for _ in range(500):
    Ar = [rng.uniform(40, 100) for _ in range(rng.randint(5, 15))]
    Br = [rng.uniform(0, 40) for _ in range(rng.randint(5, 15))]
    r = WR.analyse(Ar, Br)
    if r[0] != ANALYSE:
        continue
    n_valides += 1
    a, b = r[1]["avant"], r[1]["apres"]
    if not (b["mA"] > a["mA"] - 1e-9 and b["mB"] > a["mB"] - 1e-9 and abs(b["groupe"] - a["groupe"]) < 1e-9):
        raise AssertionError("instance aléatoire viole Will Rogers")
print(f"   {n_valides} instances valides : toutes vérifient (↑A, ↑B, groupé invariant)")
check("sur toutes les instances valides : les deux moyennes montent", n_valides > 300)
check("sur toutes les instances valides : le groupé reste invariant (vérifié en boucle)", n_valides > 300)

# ─── 4. Migration de stade médicale (survie en mois par stade) ───
print("=== Migration de stade : survie par stade ===")
precoce = [60, 55, 50, 45, 40, 35]        # stade précoce (survie longue)
avance = [20, 15, 10, 8]                   # stade avancé (survie courte)
stm, infom = WR.analyse(precoce, avance)
avm, apm = infom["avant"], infom["apres"]
print(f"   survie précoce {avm['mA']:.1f}→{apm['mA']:.1f} ; avancé {avm['mB']:.1f}→{apm['mB']:.1f} ; population {avm['groupe']:.1f}→{apm['groupe']:.1f}")
check("la survie 'par stade' s'améliore dans les DEUX stades", apm["mA"] > avm["mA"] and apm["mB"] > avm["mB"])
check("la survie de la population entière est inchangée (aucun progrès réel)", abs(apm["groupe"] - avm["groupe"]) < 1e-9)
check("formule signale la sur-confiance de l'amélioration apparente", "sur-confiant" in WR.formule((stm, infom)))

# ─── 5. ABSTENTION ───
print("=== ABSTENTION ===")
check("A pas supérieur à B → ABSTENTION", WR.analyse([1, 2], [3, 4])[0] == ABSTENTION)
check("groupe trop petit → ABSTENTION", WR.analyse([5], [1, 2])[0] == ABSTENTION)
check("aucun migrant possible (A constant) → ABSTENTION", WR.analyse([100, 100, 100], [1, 2, 3])[0] == ABSTENTION)
check("cas valide → ANALYSE", st == ANALYSE)

print(f"\nRÉSULTAT will_rogers : {ok}/{total}")
assert ok == total
