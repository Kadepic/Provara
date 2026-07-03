"""
VALIDATION des PRÉVISIONS INFÉRIEURES/SUPÉRIEURES de Walley (prevision_walley.py) — jugée par calibration.py.
Vérifie la conjugaison, les axiomes de COHÉRENCE (bornes, homogénéité, super-additivité), le théorème d'ENVELOPPE
(P̲=min sur le crédal, 0 violation, tight), la PERTE SÛRE (pari hollandais d'une assessment sur-confiante) que la
cohérente évite, la SUR-CONFIANCE d'un prix précis unique (SUR-CONFIANT vs l'intervalle), et la connexion à
l'intégrale de Choquet (lower d'une croyance = Choquet). Pur Python, léger (pas de lecteur).
"""
from __future__ import annotations

import random

from garde_ressources import borne
import prevision_walley as W
from prevision_walley import ABSTENTION, PREVISION
import croyance_dempster_shafer as DS
import choquet as Q
import calibration as CAL
from calibration import SURCONFIANT

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


rng = random.Random(58)
ETATS = ["w1", "w2", "w3", "w4"]


def simplexe(rng, n):
    v = [rng.random() + 1e-3 for _ in range(n)]
    s = sum(v)
    return [x / s for x in v]


def credal_aleatoire(rng, etats, k=4):
    return [dict(zip(etats, simplexe(rng, len(etats)))) for _ in range(k)]


def gamble(rng, etats):
    return {w: rng.uniform(-5, 5) for w in etats}


# ─── 1. Conjugaison + lower=min / upper=max ───
print("=== Conjugaison P̄(X) = −P̲(−X) ===")
conj_ok = mm_ok = True
for _ in range(3000):
    cr = credal_aleatoire(rng, ETATS, rng.randint(2, 6))
    X = gamble(rng, ETATS)
    negX = {w: -X[w] for w in ETATS}
    if abs(W.upper(cr, X) - (-W.lower(cr, negX))) > 1e-9:
        conj_ok = False
    if abs(W.lower(cr, X) - min(W._esp(P, X) for P in cr)) > 1e-12:
        mm_ok = False
check("P̄(X) = −P̲(−X) (conjugaison)", conj_ok)
check("P̲ = min sur les sommets du crédal", mm_ok)

# ─── 2. Axiomes de cohérence ───
print("=== Axiomes de cohérence ===")
born_ok = cst_ok = homo_ok = supadd_ok = True
for _ in range(3000):
    cr = credal_aleatoire(rng, ETATS, rng.randint(2, 5))
    X = gamble(rng, ETATS); Y = gamble(rng, ETATS)
    lo, hi = W.intervalle(cr, X)
    if not (min(X.values()) - 1e-9 <= lo <= hi <= max(X.values()) + 1e-9):
        born_ok = False
    c = rng.uniform(-3, 3)
    if abs(W.lower(cr, {w: c for w in ETATS}) - c) > 1e-9:
        cst_ok = False
    lam = rng.uniform(0, 3)
    if abs(W.lower(cr, {w: lam * X[w] for w in ETATS}) - lam * lo) > 1e-9:
        homo_ok = False
    if W.lower(cr, {w: X[w] + Y[w] for w in ETATS}) < lo + W.lower(cr, Y) - 1e-9:
        supadd_ok = False
check("bornes : min(X) ≤ P̲(X) ≤ P̄(X) ≤ max(X)", born_ok)
check("constante : P̲(c) = c", cst_ok)
check("homogénéité positive : P̲(λX) = λP̲(X), λ≥0", homo_ok)
check("super-additivité : P̲(X+Y) ≥ P̲(X) + P̲(Y)", supadd_ok)

# ─── 3. Théorème d'enveloppe : E_P[X] ∈ [P̲,P̄] ∀P∈M, tight ───
print("=== Enveloppe : E_P[X] ∈ [P̲,P̄] pour tout P du crédal, atteint ===")
viol = 0
tight_err = 0.0
for _ in range(2000):
    cr = credal_aleatoire(rng, ETATS, rng.randint(2, 6))
    X = gamble(rng, ETATS)
    lo, hi = W.intervalle(cr, X)
    # P = combinaison convexe aléatoire des sommets
    for _ in range(6):
        wts = simplexe(rng, len(cr))
        P = {w: sum(wts[j] * cr[j][w] for j in range(len(cr))) for w in ETATS}
        e = W._esp(P, X)
        if not (lo - 1e-9 <= e <= hi + 1e-9):
            viol += 1
    # tight : un sommet atteint lo
    tight_err = max(tight_err, abs(min(W._esp(P, X) for P in cr) - lo))
check("E_P[X] ∈ [P̲,P̄] ∀P (0 violation)", viol == 0)
check("P̲ atteint par un sommet (tight)", tight_err < 1e-12)

# ─── 4. DÉMASQUE : un prix précis unique est SUR-CONFIANT ───
print("=== Mode d'échec : prix précis unique (prévision linéaire) ===")
int_env, int_pt, verites = [], [], []
for _ in range(1500):
    cr = credal_aleatoire(rng, ETATS, rng.randint(3, 6))
    X = gamble(rng, ETATS)
    lo, hi = W.intervalle(cr, X)
    P0 = cr[0]                                  # on s'engage sur un sommet (proba précise)
    ept = W._esp(P0, X)
    wts = simplexe(rng, len(cr))
    Pstar = {w: sum(wts[j] * cr[j][w] for j in range(len(cr))) for w in ETATS}  # vraie proba inconnue
    int_env.append((lo, hi)); int_pt.append((ept, ept)); verites.append(W._esp(Pstar, X))
covE = sum(1 for (lo, hi), v in zip(int_env, verites) if lo - 1e-9 <= v <= hi + 1e-9) / len(verites)
covP = CAL.couverture(int_pt, verites)[0]
vP, iP = CAL.verdict_couverture(int_pt, verites, 0.80)
print(f"   couverture enveloppe={covE:.3f} ; prix unique={covP:.3f} ({vP})")
check("l'intervalle [P̲,P̄] couvre l'espérance vraie (=1.0)", covE == 1.0)
check("le prix précis unique est SUR-CONFIANT", vP == SURCONFIANT and covP < 0.6)

# ─── 5. Perte sûre / pari hollandais ───
print("=== Éviter la perte sûre (pari hollandais) ===")
cr = credal_aleatoire(rng, ETATS, 4)
sans_perte = True
for _ in range(2000):
    X = gamble(rng, ETATS)
    p_coherent = W.lower(cr, X)            # prix cohérent
    if W.perte_sure(X, p_coherent) < -1e-9:  # devrait être ≥ 0 (pas de perte sûre)
        sans_perte = False; break
check("acheter au prix cohérent P̲(X) n'incurre JAMAIS de perte sûre", sans_perte)
Xsl = {"w1": 1.0, "w2": 0.0, "w3": 0.5, "w4": -1.0}
p_excessif = max(Xsl.values()) + 0.3        # prix > max -> sur-confiance
print(f"   prix excessif {p_excessif} > max(X)={max(Xsl.values())} : pire net = {W.perte_sure(Xsl, p_excessif):.2f}")
check("prix > max(X) ⇒ PERTE SÛRE (net < 0 partout)", W.perte_sure(Xsl, p_excessif) < 0)

# ─── 6. Connexion à Choquet : lower d'une croyance = intégrale de Choquet ───
print("=== Connexion : P̲ d'une croyance = intégrale de Choquet ===")
chq_ok = True
for _ in range(400):
    import itertools
    subs = []
    for r in range(1, len(ETATS) + 1):
        subs += [tuple(c) for c in itertools.combinations(ETATS, r)]
    ch = rng.sample(subs, rng.randint(2, 5))
    w = {s: rng.random() + 0.05 for s in ch}; tot = sum(w.values())
    masse = {s: v / tot for s, v in w.items()}
    credal = W.credal_depuis_croyance(masse, ETATS)
    X = {w_: rng.uniform(0, 10) for w_ in ETATS}
    if abs(W.lower(credal, X) - Q.choquet(Q.capacite_croyance(masse), X)) > 1e-9:
        chq_ok = False; break
check("P̲_croyance(X) = C_Bel(X) (Schmeidler, pont vers brique 55)", chq_ok)

# ─── 7. ABSTENTION sur crédal vide ───
print("=== ABSTENTION ===")
st, r = W.encadre_gamble([], {"w1": 1.0})
print(f"   crédal vide -> {st} ({r})")
check("crédal vide → ABSTENTION", st == ABSTENTION)
st2, _ = W.encadre_gamble(credal_aleatoire(rng, ETATS, 3), gamble(rng, ETATS))
check("crédal valide → PREVISION", st2 == PREVISION)

print(f"\nRÉSULTAT prevision_walley : {ok}/{total}")
assert ok == total
