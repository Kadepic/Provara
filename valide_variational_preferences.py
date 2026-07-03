"""
VALIDATION des PRÉFÉRENCES VARIATIONNELLES / MULTIPLIER (variational_preferences.py). Vérifie la DUALITÉ de
Donsker-Varadhan (forme close = min sur P avec distribution adverse optimale, 0 violation, tight), l'inclinaison de la
pire-distribution vers les mauvais états, les limites θ→∞ (EU) et θ→0 (pire état), la PRIME DE ROBUSTESSE
(V_θ ≤ E_{P₀}, décroissante en robustesse), le DÉMASQUE (faire confiance au modèle = sur-confiant, acte fragile sous
mauvaise spécification), et le pont entropique vers la CARA (brique 61). Pur Python, léger (pas de lecteur).
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import variational_preferences as V
from variational_preferences import ROBUSTE, ABSTENTION
import smooth_ambiguity as S

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


rng = random.Random(62)
ETATS = ["s1", "s2", "s3", "s4"]


def simplexe(rng, n):
    v = [rng.random() + 0.05 for _ in range(n)]
    s = sum(v)
    return [x / s for x in v]


def scenario(rng):
    P0 = dict(zip(ETATS, simplexe(rng, len(ETATS))))
    u = {s: rng.uniform(-5, 5) for s in ETATS}
    theta = rng.uniform(0.2, 4.0)
    return P0, u, theta


# ─── 1. Dualité : forme close = min_P {E_P[u] + θKL}, tight + minimiseur ───
print("=== Dualité Donsker-Varadhan : forme close = problème variationnel ===")
dual_ok = True
viol = 0
for _ in range(2500):
    P0, u, theta = scenario(rng)
    vr = V.valeur_robuste(P0, u, theta)
    if abs(vr - V.valeur_directe(P0, u, theta)) > 1e-9:
        dual_ok = False
    # P* est le minimiseur : P aléatoires donnent ≥ vr
    for _ in range(4):
        P = dict(zip(ETATS, simplexe(rng, len(ETATS))))
        if V.eu(P, u) + theta * V.kl(P, P0) < vr - 1e-9:
            viol += 1
check("−θ ln E_{P₀}[e^{−u/θ}] = E_{P*}[u] + θKL(P*‖P₀) (forme close = variationnel)", dual_ok)
check("P* est le minimiseur : tout P donne E_P[u]+θKL ≥ V_θ (0 violation)", viol == 0)

# ─── 2. La pire-distribution incline vers les mauvais états ───
print("=== Distribution adverse P* ∝ P₀ e^{−u/θ} (penche vers faible utilité) ===")
tilt_ok = True
for _ in range(2500):
    P0, u, theta = scenario(rng)
    Ps = V.pire_distribution(P0, u, theta)
    smin = min(ETATS, key=lambda s: u[s]); smax = max(ETATS, key=lambda s: u[s])
    # ratio P*/P0 plus grand sur le pire état que sur le meilleur
    if Ps[smin] / P0[smin] < Ps[smax] / P0[smax] - 1e-9:
        tilt_ok = False
check("P*/P₀ plus grand sur l'état de plus faible utilité (inclinaison adverse)", tilt_ok)

# ─── 3. Limites θ→∞ (EU) et θ→0 (pire état) ───
print("=== Limites θ→∞ (EU sous P₀) et θ→0 (min_s u) ===")
lim_inf = lim_zero = True
for _ in range(800):
    P0, u, _ = scenario(rng)
    if abs(V.valeur_robuste(P0, u, 5000.0) - V.eu(P0, u)) > 1e-2:
        lim_inf = False
    vz = V.valeur_robuste(P0, u, 0.01)
    mn = min(u.values())
    if vz < mn - 1e-9 or vz - mn > 0.1:
        lim_zero = False
check("θ→∞ : V_θ → E_{P₀}[u] (confiance au modèle)", lim_inf)
check("θ→0 : V_θ → min_s u (robustesse totale, pire état)", lim_zero)

# ─── 4. Prime de robustesse : V_θ ≤ E_{P₀}, décroissante en 1/θ ───
print("=== Prime de robustesse : V_θ ≤ E_{P₀}, ↓ avec la robustesse ===")
prime_ok = mono_ok = True
for _ in range(2000):
    P0, u, _ = scenario(rng)
    base = V.eu(P0, u)
    vals = [V.valeur_robuste(P0, u, th) for th in (8.0, 2.0, 0.8, 0.3)]   # robustesse croissante (θ↓)
    if any(v > base + 1e-9 for v in vals):
        prime_ok = False
    if not all(vals[i] >= vals[i+1] - 1e-9 for i in range(len(vals)-1)):
        mono_ok = False
check("V_θ(u) ≤ E_{P₀}[u] (la valeur robuste ne dépasse jamais l'EU naïve)", prime_ok)
check("V_θ décroît quand θ↓ (plus de robustesse = valeur plus prudente)", mono_ok)

# ─── 5. DÉMASQUE : confiance au modèle (EU) = acte fragile ───
print("=== Mode d'échec : faire confiance au modèle de référence ===")
P0 = {"calme": 0.9, "crise": 0.1}
risque = {"calme": 2.0, "crise": -8.0}; prudent = {"calme": 0.3, "crise": 0.3}
a_eu = max({"risqué": risque, "prudent": prudent}, key=lambda a: V.eu(P0, {"risqué": risque, "prudent": prudent}[a]))
_, a_rob, tbl = V.choisir(P0, {"risqué": risque, "prudent": prudent}, 0.5)
print(f"   EU choisit '{a_eu}' ; robuste (θ=0.5) choisit '{a_rob}'")
check("EU (confiance au modèle) choisit l'acte risqué", a_eu == "risqué")
check("robuste choisit le prudent (≠ EU)", a_rob == "prudent")
# l'acte EU sur-promet : E_P0 >> sa valeur robuste (pire-cas anticipé)
check("l'acte EU sur-promet : E_{P₀} > sa valeur robuste", V.eu(P0, risque) > V.valeur_robuste(P0, risque, 0.5) + 0.5)
# sous mauvaise spécification (pire-distrib), l'acte EU s'effondre sous le prudent
Ps = V.pire_distribution(P0, risque, 0.5)
check("sous la pire spécification, l'acte EU < l'acte prudent", V.eu(Ps, risque) < V.eu(Ps, prudent))

# ─── 6. Pont entropique : V_θ = certain-équivalent CARA (brique 61) ───
print("=== Pont : V_θ(P₀,u) = certain-équivalent CARA λ=1/θ (smooth_ambiguity) ===")
pont_ok = True
for _ in range(800):
    P0, u, theta = scenario(rng)
    # priors dégénérés δ_s, mu = P0, λ = 1/θ
    priors = [{s: (1.0 if s == t else 0.0) for s in ETATS} for t in ETATS]
    mu = [P0[t] for t in ETATS]
    act = {s: u[s] for s in ETATS}
    if abs(V.valeur_robuste(P0, u, theta) - S.equiv_certain_cara(priors, mu, act, 1.0 / theta)) > 1e-7:
        pont_ok = False; break
check("V_θ = equiv_certain_cara(δ-priors, P₀, u, 1/θ) (forme entropique commune)", pont_ok)

# ─── 7. ABSTENTION ───
print("=== ABSTENTION ===")
st1, _, _ = V.choisir({"a": 1.0}, {"x": {"a": 1}}, -1.0)
st2, _, _ = V.choisir({"a": 0.5}, {"x": {"a": 1}}, 1.0)   # P0 ne somme pas à 1
check("θ ≤ 0 → ABSTENTION", st1 == ABSTENTION)
check("P₀ non normalisé → ABSTENTION", st2 == ABSTENTION)

print(f"\nRÉSULTAT variational_preferences : {ok}/{total}")
assert ok == total
