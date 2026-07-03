"""
VALIDATION du BANDIT CONTEXTUEL (bandit_contextuel.py). Vérifie : (1) LinUCB a un regret SUBLINÉAIRE (regret/tour tardif
<< précoce) ; (2) ignorer le contexte (context-free) est battu quand le meilleur bras dépend du contexte ; (3) le GLOUTON
(ε=0) se VERROUILLE sur un bras sous-optimal → regret linéaire, LinUCB non ; (4) la largeur de confiance RÉTRÉCIT avec le
nombre de tirages (calibration) ; (5) ABSTENTION. Pur Python, rng seedé.
"""
from __future__ import annotations

import random

from garde_ressources import borne
import bandit_contextuel as BC
from bandit_contextuel import ABSTENTION, ANALYSE, Agent

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


# ─── 1. LinUCB : regret SUBLINÉAIRE (regret/tour tardif << précoce) ───
print("=== LinUCB : regret sublinéaire ===")
thetas = [[1.0, 0.0], [0.0, 1.0], [0.6, 0.6]]
rng = random.Random(97)
contextes = [[1.0, 0.0] if rng.random() < 0.5 else [0.0, 1.0] for _ in range(600)]
reg, courbe, _ = BC.simule(thetas, contextes, random.Random(1), alpha=1.0)
# regret marginal sur la 1ʳᵉ moitié vs la dernière moitié
demi = len(courbe) // 2
marg_tot = courbe[demi - 1] / demi
marg_tardif = (courbe[-1] - courbe[demi - 1]) / (len(courbe) - demi)
print(f"   regret/tour précoce={marg_tot:.4f} ; tardif={marg_tardif:.4f}")
check("le regret marginal de LinUCB décroît (sublinéaire)", marg_tardif < marg_tot * 0.6)

# ─── 2. Ignorer le contexte = sur-confiant quand le meilleur bras dépend du contexte ───
print("=== Context-free battu par contextuel ===")
thetas2 = [[1.0, 0.0], [0.0, 1.0]]                       # bras 0 ↔ contexte [1,0] ; bras 1 ↔ [0,1]
ctx2 = [[1.0, 0.0] if i % 2 == 0 else [0.0, 1.0] for i in range(400)]
reg_ctx, _, _ = BC.simule(thetas2, ctx2, random.Random(2), alpha=1.0)
reg_sans, _, _ = BC.simule(thetas2, ctx2, random.Random(2), alpha=1.0, sans_contexte=True)
print(f"   regret contextuel={reg_ctx:.1f} ; context-free={reg_sans:.1f}")
check("ignorer le contexte coûte un regret bien plus élevé", reg_sans > 4 * reg_ctx + 10)
check("le contextuel garde un regret faible", reg_ctx < 0.1 * len(ctx2))

# ─── 3. Le GLOUTON (ε=0) se verrouille sur un bras sous-optimal ───
print("=== Mode d'échec : verrouillage glouton ===")
# faible diversité (contexte ~constant) : pas d'exploration gratuite. bras 0 sous-optimal, bras 1 optimal.
thetas3 = [[0.2, 0.2], [0.3, 0.3]]                       # ·[1,1] : bras0=0.4, bras1=0.6 (optimal)
ctx3 = [[1.0, 1.0] for _ in range(400)]
reg_glouton, courbe_g, ag_g = BC.simule(thetas3, ctx3, random.Random(3), alpha=0.0)
reg_ucb, courbe_u, _ = BC.simule(thetas3, ctx3, random.Random(3), alpha=1.0)
print(f"   regret GLOUTON={reg_glouton:.1f} ({reg_glouton/len(ctx3):.3f}/tour) ; LinUCB={reg_ucb:.1f} ({reg_ucb/len(ctx3):.3f}/tour)")
check("le glouton subit un regret ~linéaire (verrouillage)", reg_glouton > 0.15 * len(ctx3))
check("LinUCB explore et obtient un regret bien moindre", reg_ucb < reg_glouton / 3)
# le regret marginal du glouton NE décroît PAS (verrouillé) ; celui de LinUCB si
demi3 = len(courbe_g) // 2
marg_g_tardif = (courbe_g[-1] - courbe_g[demi3 - 1]) / (len(courbe_g) - demi3)
marg_u_tardif = (courbe_u[-1] - courbe_u[demi3 - 1]) / (len(courbe_u) - demi3)
print(f"   regret/tour tardif : glouton={marg_g_tardif:.4f} ; LinUCB={marg_u_tardif:.4f}")
check("le regret marginal du glouton reste élevé (ne se corrige pas)", marg_g_tardif > 0.15)
check("le regret marginal de LinUCB s'effondre (se corrige)", marg_u_tardif < marg_g_tardif / 3)

# ─── 4. La largeur de confiance RÉTRÉCIT avec le nombre de tirages (calibration) ───
print("=== La largeur de confiance rétrécit avec les données ===")
ag = Agent(2, 2, alpha=1.0)
x = [1.0, 0.0]
l0 = ag.largeur(0, x)
for _ in range(50):
    ag.maj(0, x, 0.5)
l50 = ag.largeur(0, x)
print(f"   largeur(bras 0, x) : 0 tirage={l0:.3f} → 50 tirages={l50:.3f}")
check("la largeur de confiance décroît avec le nombre de tirages", l50 < l0 / 3)
check("la largeur reste grande pour un bras NON tiré", ag.largeur(1, x) > l50 * 3)

# ─── 5. ABSTENTION ───
print("=== ABSTENTION ===")
check("séquence trop courte → ABSTENTION", BC.analyse(thetas, contextes[:5], random.Random(0))[0] == ABSTENTION)
check("rng manquant → ABSTENTION", BC.analyse(thetas, contextes, None)[0] == ABSTENTION)
check("cas valide → ANALYSE", BC.analyse(thetas, contextes, random.Random(0))[0] == ANALYSE)

print(f"\nRÉSULTAT bandit_contextuel : {ok}/{total}")
assert ok == total
