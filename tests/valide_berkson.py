"""
VALIDATION du PARADOXE DE BERKSON (berkson.py). Vérifie que des traits INDÉPENDANTS deviennent NÉGATIVEMENT corrélés
après sélection sur un collisionneur (et que l'effet se renforce avec le seuil), la version BINAIRE (admis si A ou B →
P(B|A) baisse), la symétrie, l'absence d'effet sans sélection, et l'ABSTENTION. Pur Python, rng seedé.
"""
from __future__ import annotations

import random

from garde_ressources import borne
import berkson as BK
from berkson import ABSTENTION, BERKSON

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


rng = random.Random(92)
A = [rng.gauss(0, 1) for _ in range(8000)]
B = [rng.gauss(0, 1) for _ in range(8000)]      # indépendants

# ─── 1. Population : indépendants (corr ≈ 0) ───
print("=== Population : A, B indépendants ===")
cp = BK.correlation(A, B)
print(f"   corr population = {cp:+.3f}")
check("corr(A,B) ≈ 0 en population", abs(cp) < 0.05)

# ─── 2. Sélection sur collisionneur → corr négative (Berkson) ───
print("=== Sélection sur collisionneur (A+B > seuil) → corr négative ===")
cs = BK.correlation_selectionnee(A, B, 1.5)
print(f"   corr sélectionnée = {cs:+.3f}")
check("corr SÉLECTIONNÉE nettement négative (biais de collision)", cs < -0.3)
# se renforce avec le seuil
c1, c2 = BK.correlation_selectionnee(A, B, 0.5), BK.correlation_selectionnee(A, B, 2.0)
print(f"   seuil 0.5 → {c1:+.3f} ; seuil 2.0 → {c2:+.3f}")
check("l'anti-corrélation se renforce avec un seuil plus sévère", c2 < c1)

# ─── 3. Version BINAIRE : admis si A ou B → P(B|A) baisse ───
print("=== Version binaire (admis si A ou B) ===")
nA = [1 if rng.random() < 0.3 else 0 for _ in range(20000)]
nB = [1 if rng.random() < 0.3 else 0 for _ in range(20000)]
admis = [i for i in range(20000) if nA[i] == 1 or nB[i] == 1]
pB_pop = sum(nB) / len(nB)
pB_A1 = sum(nB[i] for i in admis if nA[i] == 1) / max(1, sum(1 for i in admis if nA[i] == 1))
pB_A0 = sum(nB[i] for i in admis if nA[i] == 0) / max(1, sum(1 for i in admis if nA[i] == 0))
print(f"   P(B)={pB_pop:.2f} (pop) ; chez les admis : P(B|A=1)={pB_A1:.2f}, P(B|A=0)={pB_A0:.2f}")
check("chez les admis, P(B|A=1) < P(B|A=0) (association négative induite)", pB_A1 < pB_A0 - 0.2)
check("P(B|A=0, admis) = 1 (il a FALLU B pour être admis)", abs(pB_A0 - 1.0) < 1e-9)

# ─── 4. Symétrie : sélection sur A+B < seuil aussi → corr négative ───
print("=== Symétrie : sélection sur A+B < seuil ===")
idx_bas = [i for i in range(len(A)) if A[i] + B[i] < -1.5]
cs_bas = BK.correlation([A[i] for i in idx_bas], [B[i] for i in idx_bas])
print(f"   corr (A+B < −1.5) = {cs_bas:+.3f}")
check("sélection à l'autre extrême → aussi corr négative", cs_bas < -0.3)

# ─── 5. Sans sélection → pas d'effet ───
print("=== Sans sélection (tout l'échantillon) → corr ≈ 0 ===")
st, info = BK.analyse(A, B, -1e9)        # seuil très bas → tout sélectionné
print(f"   corr sélectionnée (tout) = {info['corr_sel']:+.3f}")
check("sans sélection effective → corr ≈ population (pas de biais)", abs(info["corr_sel"] - info["corr_pop"]) < 0.05)

# ─── 6. Biais quantifié ───
print("=== Biais quantifié ===")
st2, info2 = BK.analyse(A, B, 1.5)
check("biais = corr_sel − corr_pop fortement négatif", info2["biais"] < -0.3)
check("formule signale la sur-confiance", "sur-confiant" in BK.formule((st2, info2)))

# ─── 7. ABSTENTION ───
print("=== ABSTENTION ===")
st3, _ = BK.analyse([1, 2], [1, 2], 0)
st4, _ = BK.analyse(A, B, 100.0)         # personne sélectionné
check("données insuffisantes → ABSTENTION", st3 == ABSTENTION)
check("trop peu de sélectionnés → ABSTENTION", st4 == ABSTENTION)
st5, _ = BK.analyse(A, B, 1.0)
check("cas valide → BERKSON", st5 == BERKSON)

print(f"\nRÉSULTAT berkson : {ok}/{total}")
assert ok == total
