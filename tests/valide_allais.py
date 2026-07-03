"""
VALIDATION du PARADOXE D'ALLAIS (allais.py). Vérifie : AUCUN agent à utilité espérée n'exhibe le schéma d'Allais (scan
aléatoire d'utilités) ; les préférences EU des deux paires sont déterminées par le MÊME signe (A−B) ⇒ cohérence forcée ;
un agent à effet de certitude (rang-dépendant) le reproduit ; la décomposition à conséquence commune ; l'ABSTENTION.
Pur Python, rng seedé.
"""
from __future__ import annotations

import random

from garde_ressources import borne
import allais as AL
from allais import ABSTENTION, ANALYSE

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


rng = random.Random(118)


def util_aleatoire():
    u1 = rng.random()
    u5 = u1 + rng.random()           # 0 < u(1) < u(5), u(0)=0
    return lambda x: {0: 0.0, 1: u1, 5: u5}[x]


# ─── 1. Aucun agent EU n'exhibe Allais ───
print("=== Aucun agent à utilité espérée n'exhibe Allais ===")
exhibe = 0
for _ in range(100000):
    u = util_aleatoire()
    if AL.schema_allais(AL.eu(AL.G1A, u), AL.eu(AL.G1B, u), AL.eu(AL.G2A, u), AL.eu(AL.G2B, u)):
        exhibe += 1
print(f"   agents EU exhibant Allais sur 100000 utilités = {exhibe}")
check("aucune utilité espérée n'exhibe le schéma d'Allais (impossibilité)", exhibe == 0)

# ─── 2. Les deux paires EU sont gouvernées par le MÊME signe (A−B) ───
print("=== Cohérence EU : même signe sur les deux paires ===")
meme_signe = 0
for _ in range(50000):
    u = util_aleatoire()
    d1 = AL.eu(AL.G1A, u) - AL.eu(AL.G1B, u)
    d2 = AL.eu(AL.G2A, u) - AL.eu(AL.G2B, u)
    if (d1 > 0) == (d2 > 0):
        meme_signe += 1
print(f"   paires de même signe = {meme_signe}/50000")
check("eu(1A)−eu(1B) et eu(2A)−eu(2B) ont toujours le même signe (= A−B)", meme_signe == 50000)
# vérif algébrique exacte
u = AL.analyse()[1]  # juste pour exercer ; recalcule A,B
A, B = AL.contradiction_eu(lambda x: {0: 0.0, 1: 1.0, 5: 1.8}[x])
uu = lambda x: {0: 0.0, 1: 1.0, 5: 1.8}[x]
check("eu(1A)−eu(1B) = A−B exactement", abs((AL.eu(AL.G1A, uu) - AL.eu(AL.G1B, uu)) - (A - B)) < 1e-12)
check("eu(2A)−eu(2B) = A−B exactement", abs((AL.eu(AL.G2A, uu) - AL.eu(AL.G2B, uu)) - (A - B)) < 1e-12)

# ─── 3. Le schéma d'Allais impose deux inégalités contradictoires ───
print("=== Contradiction : A>B ET B>A ===")
# 1A≻1B ⟺ A>B ; 2B≻2A ⟺ B>A → impossible
check("1A≻1B équivaut à A>B", (AL.eu(AL.G1A, uu) > AL.eu(AL.G1B, uu)) == (A > B))
check("2B≻2A équivaut à B>A", (AL.eu(AL.G2B, uu) > AL.eu(AL.G2A, uu)) == (B > A))

# ─── 4. Un agent à effet de certitude (rang-dépendant) reproduit Allais ───
print("=== Effet de certitude (non-EU) reproduit Allais ===")
st, info = AL.analyse(gamma=0.5)
print(f"   eu_allais={info['eu_allais']} ; rdu_allais={info['rdu_allais']}")
check("l'agent EU n'exhibe pas Allais", not info["eu_allais"])
check("l'agent à pondération de probabilité (γ=0.5) exhibe Allais", info["rdu_allais"])

# ─── 5. Décomposition à conséquence commune ───
print("=== Décomposition à conséquence commune ===")
# 1B = 0.89·$1M + 0.11·(10/11 $5M, 1/11 $0) ; reconstruire et comparer à G1B
def melange(commun_p, commun_x, sub):
    d = {}
    d[commun_x] = d.get(commun_x, 0) + commun_p
    for p, x in sub:
        d[x] = d.get(x, 0) + 0.11 * p
    return d
sub = [(10 / 11, 5), (1 / 11, 0)]
rec1B = melange(0.89, 1, sub)
ref1B = {1: 0.89, 5: 0.10, 0: 0.01}
check("1B = 89 % de 1M + 11 % du sous-choix (conséquence commune)", all(abs(rec1B.get(k, 0) - v) < 1e-9 for k, v in ref1B.items()))
rec2B = melange(0.89, 0, sub)
ref2B = {0: 0.90, 5: 0.10}
check("2B = 89 % de 0 + le MÊME 11 % du sous-choix", all(abs(rec2B.get(k, 0) - v) < 1e-9 for k, v in ref2B.items()))
check("formule signale la sur-confiance de l'axiome d'indépendance", "sur-confiant" in AL.formule((st, info)))

# ─── 6. ABSTENTION ───
print("=== ABSTENTION ===")
check("gamma hors ]0,1] → ABSTENTION", AL.analyse(gamma=1.5)[0] == ABSTENTION)
check("cas valide → ANALYSE", st == ANALYSE)

print(f"\nRÉSULTAT allais : {ok}/{total}")
assert ok == total
