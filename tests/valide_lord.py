"""
VALIDATION du PARADOXE DE LORD (lord.py). Vérifie : le score de changement ne voit AUCUNE différence (gains égaux) tandis
que l'ANCOVA en voit une SIGNIFICATIVE (mêmes données, conclusions opposées) ; la réconciliation ANCOVA = changement +
(1−b)·écart des baselines ; HONNÊTETÉ : avec pente intra b=1 les deux s'accordent, et un VRAI écart de gain est vu par les
deux ; l'ABSTENTION. Pur Python, rng seedé.
"""
from __future__ import annotations

import random

from garde_ressources import borne
import lord as L
from lord import ABSTENTION, ANALYSE

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


rng = random.Random(119)

# ─── 1. Divergence : changement ≈ 0, ANCOVA significatif ───
print("=== Score de changement vs ANCOVA : divergence ===")
A = L.genere_groupe(70, 0.6, 4000, rng)        # baseline 70, pente 0.6, gain 0
B = L.genere_groupe(60, 0.6, 4000, rng)        # baseline 60, pente 0.6, gain 0
st, info = L.analyse(A, B)
print(f"   changement={info['diff_changement']:.2f} ; ANCOVA={info['diff_ancova']:.2f} ; pente={info['pente_intra']:.2f}")
check("le score de changement ne voit AUCUNE différence (≈0)", abs(info["diff_changement"]) < 0.5)
check("l'ANCOVA voit une différence SIGNIFICATIVE", abs(info["diff_ancova"]) > 2.0)
check("les deux conclusions s'opposent (divergence)", info["divergence"])

# ─── 2. Réconciliation : ANCOVA = changement + (1−b)·écart des baselines ───
print("=== Réconciliation algébrique ===")
mXA = sum(x for x, _ in A) / len(A)
mXB = sum(x for x, _ in B) / len(B)
attendu = info["diff_changement"] + (1 - info["pente_intra"]) * (mXA - mXB)
print(f"   ANCOVA={info['diff_ancova']:.2f} ; changement + (1−b)·écart baselines={attendu:.2f}")
check("ANCOVA ≈ changement + (1−b)·(écart des baselines)", abs(info["diff_ancova"] - attendu) < 0.3)

# ─── 3. Honnêteté : pente intra b=1 → les deux s'accordent (pas de paradoxe) ───
print("=== Honnêteté : b=1, pas de paradoxe ===")
A1 = L.genere_groupe(70, 1.0, 4000, random.Random(7))
B1 = L.genere_groupe(60, 1.0, 4000, random.Random(8))
st1, info1 = L.analyse(A1, B1)
print(f"   b=1 : changement={info1['diff_changement']:.2f} ; ANCOVA={info1['diff_ancova']:.2f}")
check("avec b=1, l'ANCOVA et le changement s'accordent (≈ même valeur)", abs(info1["diff_ancova"] - info1["diff_changement"]) < 0.5)
check("avec b=1, pas de divergence détectée", not info1["divergence"])

# ─── 4. Honnêteté : un VRAI écart de gain est vu par les DEUX ───
print("=== Honnêteté : vrai écart de gain ===")
Ag = L.genere_groupe(70, 0.6, 4000, random.Random(9), gain=6.0)   # gain réel +6
Bg = L.genere_groupe(60, 0.6, 4000, random.Random(10), gain=0.0)
stg, infog = L.analyse(Ag, Bg)
print(f"   vrai gain A +6 : changement={infog['diff_changement']:.2f} ; ANCOVA={infog['diff_ancova']:.2f}")
check("le score de changement détecte le vrai écart de gain", infog["diff_changement"] > 4.0)
check("l'ANCOVA aussi détecte un écart (les deux voient un effet réel)", infog["diff_ancova"] > 4.0)
check("formule signale la sur-confiance d'annoncer « l'effet » sans modèle causal", "sur-confiant" in L.formule((st, info)))

# ─── 5. ABSTENTION ───
print("=== ABSTENTION ===")
check("groupes trop petits → ABSTENTION", L.analyse(A[:5], B[:5])[0] == ABSTENTION)
check("cas valide → ANALYSE", st == ANALYSE)

print(f"\nRÉSULTAT lord : {ok}/{total}")
assert ok == total
