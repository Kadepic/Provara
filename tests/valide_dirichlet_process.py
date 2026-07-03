"""
VALIDATION du PROCESSUS DE DIRICHLET (dirichlet_process.py). Vérifie la prédictive CRP (réserve α/(n+α) au neuf, somme=1,
rich-get-richer), la croissance E[K]~α·ln n, la récupération du vrai K par mélange DP (mode a posteriori), la monotonie
K↗ avec α, le DÉMASQUE de sur-confiance (K fixé assigne un point atypique à proba ~1 sans masse de nouveauté, le DP non),
et l'ABSTENTION. Pur Python, rng seedé.
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import dirichlet_process as DP
from dirichlet_process import ABSTENTION, ANALYSE

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


# ─── 1. Prédictive CRP : normalisée, réserve α/(n+α) au neuf, rich-get-richer ───
print("=== Prédictive du restaurant chinois (CRP) ===")
tailles = [5, 3, 1]
alpha = 1.0
ex, neuf = DP.crp_predictive(tailles, alpha)
print(f"   tables {tailles}, α={alpha} → existantes={[round(p,3) for p in ex]}, neuve={neuf:.3f}")
check("la prédictive CRP somme à 1", abs(sum(ex) + neuf - 1.0) < 1e-12)
check("réserve exactement α/(n+α) à une table NEUVE", abs(neuf - alpha / (sum(tailles) + alpha)) < 1e-12)
check("rich-get-richer : la plus grande table est la plus probable", ex[0] > ex[1] > ex[2])
check("la masse de nouveauté croît avec α", DP.crp_predictive(tailles, 5.0)[1] > neuf)

# ─── 2. E[nb tables] croît ~ α·ln(n) ───
print("=== E[nb tables] croît avec n ===")
e10, e100, e1000 = (DP.esperance_nb_tables(n, 1.0) for n in (10, 100, 1000))
print(f"   E[K] : n=10→{e10:.2f}, n=100→{e100:.2f}, n=1000→{e1000:.2f}")
check("E[nb tables] croît strictement avec n", e10 < e100 < e1000)
check("E[nb tables] ≈ α·ln(n) (ordre logarithmique)", e1000 < 1.0 * math.log(1000) + 2)

# ─── 3. Le mélange DP récupère le vrai K (mode a posteriori) ───
print("=== Le mélange DP récupère le vrai nombre de groupes ===")
rng = random.Random(95)
xs = ([rng.gauss(-6, 1) for _ in range(20)] + [rng.gauss(0, 1) for _ in range(20)]
      + [rng.gauss(6, 1) for _ in range(20)])
st, info = DP.analyse(xs, rng=random.Random(1))
print(f"   3 vrais groupes → K estimé (mode a posteriori) = {info['k_estime']}")
check("le DP récupère K=3 (±1) sans qu'on le lui fixe", abs(info["k_estime"] - 3) <= 1)
check("la trace post-burn-in est non vide", len(info["k_trace"]) > 0)

# ─── 4. Monotonie : la concentration α pilote le nombre de classes ───
print("=== α pilote le nombre de classes (monotone) ===")
def k_moyen(a):
    tr = []
    DP.gibbs_dp(xs, a, 1.0, 0.0, 25.0, 120, random.Random(7), trace_k=tr)
    return sum(tr) / len(tr)
k_petit, k_grand = k_moyen(0.1), k_moyen(2.0)
print(f"   K moyen : α=0.1 → {k_petit:.2f} ; α=2.0 → {k_grand:.2f}")
check("plus α est grand, plus il y a de classes", k_grand > k_petit)

# ─── 5. DÉMASQUE : K fixé sur-confiant sur un point atypique, DP réserve la nouveauté ───
print("=== Mode d'échec : K fixé force un point atypique avec certitude ===")
centres = [-6.0, 0.0, 6.0]
j, p = DP.assignation_k_fixe(15.0, centres, 1.0)
masse_neuf = DP.masse_nouveaute_dp(15.0, xs, info["z"], info["alpha"], 1.0, 0.0, 25.0)
print(f"   x=15 atypique : K=3 fixé → cluster {j} proba {p:.3f} ; DP masse 'classe NEUVE' = {masse_neuf:.3f}")
check("K fixé assigne le point atypique avec quasi-certitude (sur-confiant)", p > 0.99)
check("le DP réserve une forte masse de nouveauté au point atypique", masse_neuf > 0.5)
# un point au CŒUR d'un groupe : pas de fausse alarme de nouveauté
masse_centre = DP.masse_nouveaute_dp(0.0, xs, info["z"], info["alpha"], 1.0, 0.0, 25.0)
print(f"   x=0 (cœur d'un groupe) : DP masse 'classe NEUVE' = {masse_centre:.3f}")
check("pas de fausse nouveauté pour un point typique", masse_centre < 0.1)
check("formule signale la sur-confiance du K fixé", "sur-confiant" in DP.formule((st, info)))

# ─── 6. ABSTENTION ───
print("=== ABSTENTION ===")
check("< 6 points → ABSTENTION", DP.analyse([1.0, 2.0, 3.0], rng=random.Random(0))[0] == ABSTENTION)
check("rng manquant → ABSTENTION", DP.analyse(xs, rng=None)[0] == ABSTENTION)
check("cas valide → ANALYSE", st == ANALYSE)

print(f"\nRÉSULTAT dirichlet_process : {ok}/{total}")
assert ok == total
