"""
VALIDATION de la THÉORIE DES POSSIBILITÉS (possibilite.py) — jugée par calibration.py. Vérifie les invariants
algébriques exacts (dualité N=1−Π(Aᶜ), N≤Π, max-additivité de Π, N>0⇒Π=1), l'ENCADREMENT garanti N(A)≤P(A)≤Π(A)
pour toute probabilité dominée par π (Dubois-Prade, 0 violation sur tous les sous-ensembles), et DÉMASQUE le mode
d'échec : lire Π(A) comme une probabilité est SUR-CONFIANT, lire N(A) est SOUS-CONFIANT, seul l'intervalle [N,Π]
reste calibré (couvre la fréquence empirique). Pur Python, léger (pas de lecteur).
"""
from __future__ import annotations

import itertools
import random

from garde_ressources import borne
import possibilite as P
from possibilite import ABSTENTION, MESURE
import calibration as CAL
from calibration import SURCONFIANT, SOUSCONFIANT

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


def pi_aleatoire(rng, elements):
    """Distribution de possibilité normalisée : valeurs dans [0,1], au moins un élément à 1 (sup π = 1)."""
    pi = {x: round(rng.random(), 3) for x in elements}
    gagnant = rng.choice(elements)
    pi[gagnant] = 1.0
    return pi


def proba_dominee(rng, pi, essais=400):
    """Tire une probabilité DOMINÉE par π (rejet : P(A) ≤ Π(A) ∀A). None si non trouvée."""
    elements = list(pi.keys())
    for _ in range(essais):
        brut = {x: rng.random() ** 2 for x in elements}
        s = sum(brut.values())
        Pp = {x: v / s for x, v in brut.items()}
        if P.domine(pi, Pp):
            return Pp
    return None


elements = ["a", "b", "c", "d", "e"]
rng = random.Random(23)

# ─── 1. Dualité exacte N(A) = 1 − Π(Aᶜ) ───
print("=== Dualité N(A) = 1 − Π(Aᶜ) (exacte) ===")
dual_ok = True
for _ in range(3000):
    pi = pi_aleatoire(rng, elements)
    r = rng.randint(1, len(elements) - 1)
    A = set(rng.sample(elements, r))
    comp = set(elements) - A
    if abs(P.necessite(pi, A) - (1.0 - P.possibilite(pi, comp))) > 1e-9:
        dual_ok = False
        break
check("N(A) = 1 − Π(Aᶜ) sur 3000 cas", dual_ok)

# ─── 2. N(A) ≤ Π(A) toujours ───
print("=== N(A) ≤ Π(A) (toujours) ===")
viol_np = 0
for _ in range(3000):
    pi = pi_aleatoire(rng, elements)
    A = set(rng.sample(elements, rng.randint(1, len(elements))))
    if P.necessite(pi, A) > P.possibilite(pi, A) + 1e-9:
        viol_np += 1
check("aucune violation N ≤ Π (0/3000)", viol_np == 0)

# ─── 3. Max-additivité Π(A∪B) = max(Π(A), Π(B)) ───
print("=== Max-additivité de Π (≠ somme : la possibilité n'est PAS une probabilité) ===")
maxadd_ok = True
for _ in range(3000):
    pi = pi_aleatoire(rng, elements)
    A = set(rng.sample(elements, rng.randint(1, 3)))
    B = set(rng.sample(elements, rng.randint(1, 3)))
    if abs(P.possibilite(pi, A | B) - max(P.possibilite(pi, A), P.possibilite(pi, B))) > 1e-9:
        maxadd_ok = False
        break
check("Π(A∪B) = max(Π(A),Π(B)) sur 3000 cas", maxadd_ok)

# ─── 4. N(A) > 0 ⇒ Π(A) = 1 ───
print("=== N(A) > 0 ⇒ Π(A) = 1 (la nécessité présuppose la pleine possibilité) ===")
impl_ok = True
for _ in range(3000):
    pi = pi_aleatoire(rng, elements)
    A = set(rng.sample(elements, rng.randint(1, len(elements))))
    if P.necessite(pi, A) > 1e-9 and abs(P.possibilite(pi, A) - 1.0) > 1e-9:
        impl_ok = False
        break
check("N(A)>0 ⇒ Π(A)=1 sur 3000 cas", impl_ok)

# ─── 5. Encadrement Dubois-Prade : N(A) ≤ P(A) ≤ Π(A) pour TOUTE proba dominée, tout A ───
print("=== Encadrement garanti N(A) ≤ P(A) ≤ Π(A) (toute proba dominée, tout sous-ensemble) ===")
viol_enc = 0
tests = 0
for _ in range(400):
    pi = pi_aleatoire(rng, elements)
    Pp = proba_dominee(rng, pi)
    if Pp is None:
        continue
    for r in range(1, len(elements) + 1):
        for combo in itertools.combinations(elements, r):
            A = set(combo)
            N, Pi = P.intervalle_proba(pi, A)
            pa = sum(Pp[x] for x in A)
            tests += 1
            if not (N - 1e-9 <= pa <= Pi + 1e-9):
                viol_enc += 1
print(f"   {tests} encadrements testés, {viol_enc} violations")
check("aucune violation de N ≤ P ≤ Π (Dubois-Prade)", viol_enc == 0 and tests > 1000)

# ─── 6. DÉMASQUE : Π-comme-proba SUR-CONFIANT, N-comme-proba SOUS-CONFIANT, bracket calibré ───
print("=== Mode d'échec : lire Π(A) (ou N(A)) comme une probabilité ===")
# Scénario contrôlé : deux causes pleinement possibles, A = {a,b} -> N=0.7, Π=1 ; P(A) dans [0.7,1].
pi_fix = {"a": 1.0, "b": 1.0, "c": 0.3, "d": 0.3, "e": 0.3}
A = {"a", "b"}
N_A, Pi_A = P.intervalle_proba(pi_fix, A)
print(f"   π fixe, A={A} : encadrement [N={N_A:.2f}, Π={Pi_A:.2f}]")
conf_Pi, conf_N, juste, freqs = [], [], [], []
rng2 = random.Random(99)
n_ok = 0
for _ in range(4000):
    Pp = proba_dominee(rng2, pi_fix)
    if Pp is None:
        continue
    n_ok += 1
    pa = Pp["a"] + Pp["b"]
    arrive = 1 if rng2.random() < pa else 0
    juste.append(arrive)
    conf_Pi.append(Pi_A)   # « possibilité-comme-proba »
    conf_N.append(N_A)     # « nécessité-comme-proba »
    freqs.append(pa)
freq_emp = sum(juste) / len(juste)
vPi, iPi = CAL.est_calibre(conf_Pi, juste)
vN, iN = CAL.est_calibre(conf_N, juste)
print(f"   {n_ok} tirages ; fréquence empirique de A = {freq_emp:.3f}")
print(f"   Π-comme-proba (conf={Pi_A:.2f}) -> {vPi} (écart-signe {iPi['ecart_signe']:+.3f})")
print(f"   N-comme-proba (conf={N_A:.2f}) -> {vN} (écart-signe {iN['ecart_signe']:+.3f})")
check("fréquence empirique de A DANS l'encadrement [N, Π]", N_A - 1e-6 <= freq_emp <= Pi_A + 1e-6)
check("lire Π(A) comme proba = SUR-CONFIANT", vPi == SURCONFIANT)
check("lire N(A) comme proba = SOUS-CONFIANT", vN == SOUSCONFIANT)

# ─── 7. depuis_emboitees : la π consonante DOMINE la loi sous-jacente ───
print("=== π depuis ensembles de confiance emboîtés : domine la vraie loi ===")
# Vraie loi concentrée sur x ; ensembles emboîtés {x} (c=0.5) ⊂ {x,y,z} (c=0.9) ⊂ tout (c=1)
niveaux = [(0.0, {"x"}), (0.5, {"x", "y", "z"}), (0.9, {"x", "y", "z", "w"})]
pi_c = P.depuis_emboitees(niveaux)
print(f"   π consonante = {pi_c}")
check("π consonante normalisée (sup=1 sur le plus petit ensemble)", P.normalisee(pi_c))
# une loi dominée : tout sur x
check("loi {x:1.0} dominée par π consonante", P.domine(pi_c, {"x": 1.0, "y": 0.0, "z": 0.0, "w": 0.0}))
check("Π({x}) = 1 (pleinement plausible)", abs(P.possibilite(pi_c, {"x"}) - 1.0) < 1e-9)

# ─── 8. ABSTENTION sur π sous-normalisée ───
print("=== ABSTENTION si π non normalisée (sup π < 1) ===")
st, _, raison = P.encadre({"a": 0.6, "b": 0.4}, {"a"})
print(f"   sup π = 0.6 -> {st} ({raison})")
check("π sous-normalisée -> ABSTENTION", st == ABSTENTION)
st2, val2, _ = P.encadre(pi_fix, A)
check("π normalisée -> MESURE avec encadrement", st2 == MESURE and val2 == (N_A, Pi_A))

print(f"\nRÉSULTAT possibilite : {ok}/{total}")
assert ok == total
