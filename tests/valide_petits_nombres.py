"""
VALIDATION de la LOI DES PETITS NOMBRES (petits_nombres.py). Vérifie que les extrêmes du classement par taux brut sont
dominés par les PETITS échantillons, que la variance du taux ∝ 1/n, que l'EB estime κ grand quand la variation est du
bruit (et plus petit quand il y a un vrai signal), que le rétrécissement RÉDUIT l'erreur et compresse les extrêmes,
le DÉMASQUE (top brut ≠ top rétréci), et l'ABSTENTION. Pur Python, rng seedé.
"""
from __future__ import annotations

import random
import statistics

from garde_ressources import borne
import petits_nombres as PN
from petits_nombres import ABSTENTION, ANALYSE

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


rng = random.Random(94)


def genere(n_entites, taux, tailles):
    ns = [rng.choice(tailles) for _ in range(n_entites)]
    ks = [sum(1 for _ in range(n) if rng.random() < (taux if isinstance(taux, float) else taux[i])) for i, n in enumerate(ns)]
    return ks, ns


TAILLES = [20, 50, 100, 500, 2000, 10000]
p = 0.05
ks, ns = genere(300, p, TAILLES)
bruts = [PN.taux_brut(k, n) for k, n in zip(ks, ns)]

# ─── 1. Extrêmes dominés par les petits échantillons ───
print("=== Extrêmes du classement par taux brut = petits échantillons ===")
ordre = sorted(range(len(ns)), key=lambda i: bruts[i])
bas5 = ordre[:10]; haut5 = ordre[-10:]
n_moy = statistics.mean(ns)
n_extremes = statistics.mean([ns[i] for i in bas5 + haut5])
print(f"   n moyen global={n_moy:.0f} ; n moyen des extrêmes (haut+bas)={n_extremes:.0f}")
check("les extrêmes ont un n bien plus petit que la moyenne", n_extremes < n_moy / 2)

# ─── 2. Variance du taux ∝ 1/n ───
print("=== Variance du taux brut ∝ 1/n ===")
def var_taux(n, reps=2000):
    return statistics.pvariance([sum(1 for _ in range(n) if rng.random() < p) / n for _ in range(reps)])
v_petit, v_grand = var_taux(20), var_taux(2000)
print(f"   var(n=20)={v_petit:.5f} ; var(n=2000)={v_grand:.6f} (ratio≈{v_petit/v_grand:.0f}, attendu ≈100)")
check("la variance du taux décroît comme 1/n (petits n bruités)", v_petit > 30 * v_grand)

# ─── 3. EB : κ grand quand tout est bruit ; plus petit avec un vrai signal ───
print("=== EB : κ s'adapte au signal réel ===")
mu = PN.moyenne_globale(ks, ns)
kap_bruit = PN.kappa_optimal(ks, ns, mu)
# vrais taux VARIABLES (vrai signal) : κ doit être plus petit (moins de rétrécissement)
taux_var = [rng.uniform(0.01, 0.2) for _ in range(300)]
ks2, ns2 = genere(300, taux_var, TAILLES)
kap_signal = PN.kappa_optimal(ks2, ns2, PN.moyenne_globale(ks2, ns2))
print(f"   κ (tout bruit)={kap_bruit:g} ; κ (vrai signal)={kap_signal:g}")
check("κ grand quand la variation est du bruit (fort rétrécissement)", kap_bruit >= 300)
check("κ plus petit quand il y a un vrai signal (moins de rétrécissement)", kap_signal < kap_bruit)

# ─── 4. Le rétrécissement réduit l'erreur (taux vrais égaux) ───
print("=== Le rétrécissement réduit l'erreur ===")
retr = [PN.retrecissement(k, n, mu, kap_bruit) for k, n in zip(ks, ns)]
err_brut = sum((b - p) ** 2 for b in bruts)
err_retr = sum((r - p) ** 2 for r in retr)
print(f"   erreur quadratique : brut={err_brut:.3f} ; rétréci={err_retr:.4f}")
check("le rétrécissement réduit fortement l'erreur (taux vrais égaux)", err_retr < err_brut / 3)

# ─── 5. Le rétrécissement compresse les extrêmes ───
print("=== Le rétrécissement compresse les extrêmes ===")
etendue_brut = max(bruts) - min(bruts); etendue_retr = max(retr) - min(retr)
print(f"   étendue : brut={etendue_brut:.3f} ; rétréci={etendue_retr:.3f}")
check("les extrêmes rétrécis sont bien moins étendus", etendue_retr < etendue_brut / 2)

# ─── 6. DÉMASQUE : top brut ≠ top rétréci (le 'gagnant' brut est du bruit) ───
print("=== Mode d'échec : top brut = bruit de petit échantillon ===")
st, info = PN.analyse(ks, ns)
top_brut = max(range(len(ks)), key=lambda i: info["bruts"][i])
print(f"   entité top par taux brut : n={ns[top_brut]}, brut={info['bruts'][top_brut]:.3f} → rétréci={info['retrecis'][top_brut]:.3f} (μ={info['mu']:.3f})")
check("le 'top' brut a un petit n et son taux rétréci revient près de μ", ns[top_brut] <= 100 and abs(info["retrecis"][top_brut] - info["mu"]) < 0.03)
check("formule signale la sur-confiance du classement brut", "sur-confiant" in PN.formule((st, info)))

# ─── 7. ABSTENTION ───
print("=== ABSTENTION ===")
st1, _ = PN.analyse([1, 2], [10, 20])
st2, _ = PN.analyse([1, 2, 3, 4, 5], [10, 20, 0, 5, 5])
check("< 5 entités → ABSTENTION", st1 == ABSTENTION)
check("n ≤ 0 → ABSTENTION", st2 == ABSTENTION)
st3, _ = PN.analyse(ks, ns)
check("cas valide → ANALYSE", st3 == ANALYSE)

print(f"\nRÉSULTAT petits_nombres : {ok}/{total}")
assert ok == total
