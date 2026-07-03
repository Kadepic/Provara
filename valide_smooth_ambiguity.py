"""
VALIDATION de l'AMBIGUÏTÉ LISSE (smooth_ambiguity.py). Vérifie : φ linéaire = EU sous prior réduit (ambiguïté
neutre) ; φ concave ⇒ Jensen (V ≤ φ(E_réduit), prime d'ambiguïté) ; le DÉMASQUE — deux actes de même espérance
réduite mais d'ambiguïté différente sont ÉGAUX pour l'EU (sur-confiant) alors qu'un φ concave préfère STRICTEMENT le
moins ambigu ; la séparation risque/ambiguïté (λ↑ pénalise l'ambigu sans toucher l'espérance réduite) ; les limites
λ→0 (EU) et λ→∞ (maxmin, pont brique 60) ; et Ellsberg. Pur Python, léger (pas de lecteur).
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import smooth_ambiguity as S
from smooth_ambiguity import ROBUSTE, ABSTENTION
import decision_ambiguite as AMB

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


rng = random.Random(61)
ETATS = ["s1", "s2", "s3"]


def simplexe(rng, n):
    v = [rng.random() + 1e-3 for _ in range(n)]
    s = sum(v)
    return [x / s for x in v]


def scenario(rng):
    priors = [dict(zip(ETATS, simplexe(rng, len(ETATS)))) for _ in range(rng.randint(2, 5))]
    mu = simplexe(rng, len(priors))
    acts = {f"a{i}": {s: rng.uniform(0, 5) for s in ETATS} for i in range(rng.randint(2, 4))}
    return priors, mu, acts


# ─── 1. φ linéaire = EU sous prior réduit ───
print("=== φ linéaire ⇒ EU sous prior réduit (ambiguïté neutre) ===")
lin_ok = red_ok = True
for _ in range(3000):
    priors, mu, acts = scenario(rng)
    Pbar = S.prior_reduit(priors, mu)
    for u in acts.values():
        if abs(S.valeur(priors, mu, u, S.phi_lineaire) - S.eu_reduit(priors, mu, u)) > 1e-9:
            lin_ok = False
        if abs(S.eu_reduit(priors, mu, u) - S.eu(Pbar, u)) > 1e-9:
            red_ok = False
check("V(φ linéaire) = E_μ[E_P] (= EU)", lin_ok)
check("E_μ[E_P[act]] = E_{P̄}[act] (réduction)", red_ok)

# ─── 2. φ concave ⇒ Jensen : V ≤ φ(E_réduit) ───
print("=== φ concave ⇒ Jensen (prime d'ambiguïté) ===")
jensen_ok = eq_ok = True
for _ in range(3000):
    priors, mu, acts = scenario(rng)
    phi = S.phi_cara(rng.uniform(0.5, 3))
    for u in acts.values():
        v = S.valeur(priors, mu, u, phi)
        bound = phi(S.eu_reduit(priors, mu, u))
        if v > bound + 1e-9:
            jensen_ok = False
# égalité si E_P constant sur le support
priors2 = [{"s1": 0.5, "s2": 0.5, "s3": 0.0}, {"s1": 0.3, "s2": 0.3, "s3": 0.4}]
mu2 = [0.6, 0.4]
const_act = {"s1": 2.0, "s2": 2.0, "s3": 2.0}   # E_P=2 partout
phi = S.phi_cara(1.5)
eq_ok = abs(S.valeur(priors2, mu2, const_act, phi) - phi(S.eu_reduit(priors2, mu2, const_act))) < 1e-9
check("V ≤ φ(E_réduit) (Jensen, φ concave)", jensen_ok)
check("égalité ssi E_P constant sur le support (pas d'ambiguïté)", eq_ok)

# ─── 3. DÉMASQUE : EU indifférent, φ concave préfère le moins ambigu ───
print("=== Mode d'échec : EU aveugle à l'ambiguïté ===")
priors = [{"s1": 0.8, "s2": 0.2}, {"s1": 0.2, "s2": 0.8}]
mu = [0.5, 0.5]
sur = {"s1": 1.0, "s2": 1.0}      # E_P=1 partout
amb = {"s1": 2.0, "s2": 0.0}      # E_P ∈ {1.6,0.4}, moyenne réduite 1.0
print(f"   E_réduit : sûr={S.eu_reduit(priors,mu,sur):.2f}, ambigu={S.eu_reduit(priors,mu,amb):.2f}")
check("EU (φ linéaire) INDIFFÉRENT entre sûr et ambigu", abs(S.eu_reduit(priors, mu, sur) - S.eu_reduit(priors, mu, amb)) < 1e-9)
_, best_av, _ = S.choisir(priors, mu, {"sur": sur, "amb": amb}, lam=2.0)
check("φ concave (averse) préfère STRICTEMENT le sûr (moins ambigu)", best_av == "sur")
check("CE(ambigu) < CE(sûr) sous aversion", S.equiv_certain_cara(priors, mu, amb, 2.0) < S.equiv_certain_cara(priors, mu, sur, 2.0))

# ─── 4. Séparation : λ↑ pénalise l'ambigu, espérance réduite inchangée ───
print("=== Séparation risque/ambiguïté : λ↑ ⇒ CE(ambigu)↓, E_réduit constant ===")
ces = [S.equiv_certain_cara(priors, mu, amb, lam) for lam in (0.1, 1.0, 3.0, 8.0)]
print(f"   CE(ambigu) pour λ croissant : {[round(c,3) for c in ces]}")
check("CE(ambigu) décroît avec λ (aversion croissante)", all(ces[i] >= ces[i+1] - 1e-9 for i in range(len(ces)-1)))
check("CE(sûr) reste = 1 (pas d'ambiguïté à pénaliser)", abs(S.equiv_certain_cara(priors, mu, sur, 8.0) - 1.0) < 1e-9)

# ─── 5. Limites : λ→0 ⇒ E_réduit ; λ→∞ ⇒ maxmin (pont brique 60) ───
print("=== Limites λ→0 (EU) et λ→∞ (maxmin) ===")
lim0_ok = limInf_ok = choix_ok = True
for _ in range(800):
    priors, mu, acts = scenario(rng)
    for u in acts.values():
        if abs(S.equiv_certain_cara(priors, mu, u, 1e-4) - S.eu_reduit(priors, mu, u)) > 1e-3:
            lim0_ok = False
        mn = min(S.eu(P, u) for P in priors)
        ce_inf = S.equiv_certain_cara(priors, mu, u, 400.0)
        if ce_inf < mn - 1e-9 or ce_inf - mn > 0.05:   # CE ≥ min toujours ; écart O(ln(1/μ_min)/λ) → 0
            limInf_ok = False
    # choix λ grand ≈ maxmin (sur le crédal = support de μ) : plancher du choix lisse proche du plancher maxmin (= max des planchers)
    _, c_smooth, _ = S.choisir(priors, mu, acts, lam=400.0)
    _, c_maxmin, _ = AMB.choisir(priors, acts, "maxmin")
    plancher_smooth = min(S.eu(P, acts[c_smooth]) for P in priors)
    plancher_maxmin = min(S.eu(P, acts[c_maxmin]) for P in priors)
    if plancher_maxmin - plancher_smooth > 0.05:   # maxmin = plancher MAX ; lisse y converge quand λ→∞
        choix_ok = False
check("λ→0 : CE → E_réduit (EU)", lim0_ok)
check("λ→∞ : CE → min_j E_{P_j} (maxmin)", limInf_ok)
check("choix λ grand a le même plancher que maxmin (pont brique 60)", choix_ok)

# ─── 6. Ellsberg avec φ concave ───
print("=== Ellsberg avec φ concave ===")
priorsE = [{"R": 1/3, "B": 0.0, "Y": 2/3}, {"R": 1/3, "B": 2/3, "Y": 0.0}]
muE = [0.5, 0.5]
A = {"R": 1, "B": 0, "Y": 0}; B = {"R": 0, "B": 1, "Y": 0}
C = {"R": 1, "B": 0, "Y": 1}; Dd = {"R": 0, "B": 1, "Y": 1}
phiE = S.phi_cara(2.0)
check("A ≻ B (averse à l'ambiguïté)", S.valeur(priorsE, muE, A, phiE) > S.valeur(priorsE, muE, B, phiE))
check("D ≻ C (averse à l'ambiguïté)", S.valeur(priorsE, muE, Dd, phiE) > S.valeur(priorsE, muE, C, phiE))

# ─── 7. ABSTENTION ───
print("=== ABSTENTION ===")
st1, _, _ = S.choisir([{"s1": 1.0}], [0.5], {"a": {"s1": 1}}, lam=1.0)   # μ ne somme pas à 1
st2, _, _ = S.choisir([], [], {}, lam=1.0)
check("μ ne somme pas à 1 → ABSTENTION", st1 == ABSTENTION)
check("priors/actes vides → ABSTENTION", st2 == ABSTENTION)

print(f"\nRÉSULTAT smooth_ambiguity : {ok}/{total}")
assert ok == total
