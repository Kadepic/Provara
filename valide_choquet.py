"""
VALIDATION de l'INTÉGRALE DE CHOQUET (choquet.py) — jugée par calibration.py. Vérifie : Choquet w.r.t. additif =
moyenne pondérée, idempotence/bornes/monotonie, comonotone-additivité, l'INTERACTION (synergie vs redondance), et
surtout le théorème de Schmeidler — C_ν = espérance INFÉRIEURE sur le crédal M(ν) d'une croyance (0 violation, atteint
par l'allocation gloutonne) — puis DÉMASQUE la sur-confiance : s'engager sur un prior additif unique (pignistique)
donne un point qui RATE l'espérance vraie (SUR-CONFIANT) là où l'encadrement de Choquet la contient. Pur Python,
léger (pas de lecteur).
"""
from __future__ import annotations

import random

from garde_ressources import borne
import choquet as Q
from choquet import ABSTENTION, VALEUR
import croyance_dempster_shafer as DS
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


rng = random.Random(55)
LABELS = ["a", "b", "c", "d"]


def masse_aleatoire(rng, labels, nf=4):
    import itertools
    subs = []
    for r in range(1, len(labels) + 1):
        subs += [tuple(c) for c in itertools.combinations(labels, r)]
    ch = rng.sample(subs, min(nf, len(subs)))
    w = {s: rng.random() + 0.05 for s in ch}
    tot = sum(w.values())
    return {s: v / tot for s, v in w.items()}


def proba_credal(rng, masse, labels):
    """P ≥ ν : alloue chaque masse focale m(B) aléatoirement entre les éléments de B."""
    P = {l: 0.0 for l in labels}
    for B, m in masse.items():
        elts = list(B)
        coupe = sorted(rng.random() for _ in range(len(elts) - 1))
        bornes = [0.0] + coupe + [1.0]
        for i, e in enumerate(elts):
            P[e] += m * (bornes[i + 1] - bornes[i])
    return P


def esperance(P, x):
    return sum(P[l] * x[l] for l in x)


# ─── 1. Choquet w.r.t. additif = moyenne pondérée ───
print("=== Choquet (additif) = moyenne arithmétique pondérée ===")
add_ok = True
for _ in range(3000):
    w = [rng.random() for _ in LABELS]; sw = sum(w); w = {LABELS[i]: w[i] / sw for i in range(len(LABELS))}
    x = {l: rng.uniform(-5, 5) for l in LABELS}
    c = Q.choquet(Q.capacite_additive(w), x)
    moy = sum(w[l] * x[l] for l in LABELS)
    if abs(c - moy) > 1e-9:
        add_ok = False; break
check("Choquet additif = Σ wᵢ xᵢ (3000 cas)", add_ok)

# ─── 2. Idempotence, bornes, monotonie ───
print("=== Idempotence / bornes / monotonie ===")
idem_ok = bornes_ok = mono_ok = True
for _ in range(2000):
    masse = masse_aleatoire(rng, LABELS)
    nu = Q.capacite_croyance(masse)
    cst = rng.uniform(-3, 3)
    if abs(Q.choquet(nu, {l: cst for l in LABELS}) - cst) > 1e-9:
        idem_ok = False
    x = {l: rng.uniform(-5, 5) for l in LABELS}
    cx = Q.choquet(nu, x)
    if not (min(x.values()) - 1e-9 <= cx <= max(x.values()) + 1e-9):
        bornes_ok = False
    y = {l: x[l] + rng.uniform(0, 2) for l in LABELS}     # y ≥ x partout
    if Q.choquet(nu, y) < cx - 1e-9:
        mono_ok = False
check("idempotence : C(c,…,c) = c", idem_ok)
check("bornes : min(x) ≤ C(x) ≤ max(x)", bornes_ok)
check("monotonie : x ≤ y ⇒ C(x) ≤ C(y)", mono_ok)

# ─── 3. Théorème de Schmeidler : C_ν = espérance INFÉRIEURE sur le crédal ───
print("=== Schmeidler : C_ν(x) = min_{P∈M(ν)} E_P[x] (croyance) ===")
viol_low = viol_up = 0
tight_max_err = 0.0
for _ in range(800):
    masse = masse_aleatoire(rng, LABELS)
    nu = Q.capacite_croyance(masse)
    nub = Q.conjuguee(nu, LABELS)
    x = {l: rng.uniform(-5, 5) for l in LABELS}
    inf = Q.choquet(nu, x); sup = Q.choquet(nub, x)
    # allocation gloutonne -> atteint le min (chaque masse au plus PETIT x de B)
    Pmin = {l: 0.0 for l in LABELS}
    for B, m in masse.items():
        amin = min(B, key=lambda e: x[e]); Pmin[amin] += m
    tight_max_err = max(tight_max_err, abs(esperance(Pmin, x) - inf))
    for _ in range(8):
        P = proba_credal(rng, masse, LABELS)
        e = esperance(P, x)
        if e < inf - 1e-9:
            viol_low += 1
        if e > sup + 1e-9:
            viol_up += 1
check("E_P[x] ≥ C_ν(x) pour tout P du crédal (espérance inférieure, 0 violation)", viol_low == 0)
check("E_P[x] ≤ C_ν̄(x) (espérance supérieure, 0 violation)", viol_up == 0)
check("C_ν atteint par l'allocation gloutonne (borne TIGHT)", tight_max_err < 1e-9)

# ─── 4. DÉMASQUE : un prior additif unique (pignistique) est SUR-CONFIANT ───
print("=== Mode d'échec : s'engager sur un prior unique vs l'encadrement de Choquet ===")
int_choq, int_point, verites = [], [], []
for _ in range(1200):
    masse = masse_aleatoire(rng, LABELS, nf=rng.randint(2, 5))
    nu = Q.capacite_croyance(masse)
    nub = Q.conjuguee(nu, LABELS)
    x = {l: rng.uniform(0, 10) for l in LABELS}
    inf, sup = Q.choquet(nu, x), Q.choquet(nub, x)
    # prior pignistique BetP(i)=Σ_{B∋i} m(B)/|B|
    BetP = {l: 0.0 for l in LABELS}
    for B, m in masse.items():
        for e in B:
            BetP[e] += m / len(B)
    ept = esperance(BetP, x)
    # "vraie" espérance = un P* du crédal (inconnu)
    Pstar = proba_credal(rng, masse, LABELS)
    vrai = esperance(Pstar, x)
    int_choq.append((inf, sup)); int_point.append((ept, ept)); verites.append(vrai)
# couverture tolérante au flottant (P* peut tomber EXACTEMENT sur une borne, arrondi ~1e-15)
covC = sum(1 for (lo, hi), v in zip(int_choq, verites) if lo - 1e-9 <= v <= hi + 1e-9) / len(verites)
covP = CAL.couverture(int_point, verites)[0]
vP, iP = CAL.verdict_couverture(int_point, verites, 0.80)
print(f"   couverture Choquet={covC:.3f} ; point pignistique={covP:.3f} ({vP})")
check("l'encadrement de Choquet contient l'espérance vraie (couverture = 1.0 à tol. flottante)", covC == 1.0)
check("le prior unique est SUR-CONFIANT (sous-couvre)", vP == SURCONFIANT and covP < 0.6)

# ─── 5. Comonotone-additivité : C(x+y)=C(x)+C(y) si x,y comonotones ───
print("=== Comonotone-additivité ===")
como_ok = True
base = {l: i for i, l in enumerate(LABELS)}     # ordre fixe
for _ in range(2000):
    masse = masse_aleatoire(rng, LABELS)
    nu = Q.capacite_croyance(masse)
    x = {l: base[l] + rng.uniform(0, 0.3) for l in LABELS}   # même ordre que base
    y = {l: 2 * base[l] + rng.uniform(0, 0.3) for l in LABELS}  # comonotone à x
    s = {l: x[l] + y[l] for l in LABELS}
    if abs(Q.choquet(nu, s) - (Q.choquet(nu, x) + Q.choquet(nu, y))) > 1e-9:
        como_ok = False; break
check("C(x+y) = C(x)+C(y) pour x,y comonotones", como_ok)

# ─── 6. Interaction : synergie (marginal fort) vs redondance (marginal faible) ───
print("=== Interaction : synergie vs redondance ===")
syn = lambda A: {frozenset(): 0., frozenset({"a"}): .1, frozenset({"b"}): .1, frozenset({"a", "b"}): 1.}[frozenset(A)]
red = lambda A: {frozenset(): 0., frozenset({"a"}): .7, frozenset({"b"}): .7, frozenset({"a", "b"}): 1.}[frozenset(A)]
marg_syn = Q.choquet(syn, {"a": 1, "b": 1}) - Q.choquet(syn, {"a": 1, "b": 0})
marg_red = Q.choquet(red, {"a": 1, "b": 1}) - Q.choquet(red, {"a": 1, "b": 0})
print(f"   gain du 2ᵉ critère : synergie={marg_syn:.2f}  redondance={marg_red:.2f}")
check("synergie valide (capacités)", Q.est_capacite(syn, ["a", "b"]) and Q.est_capacite(red, ["a", "b"]))
check("synergie : 2ᵉ critère apporte BEAUCOUP plus que sous redondance", marg_syn > marg_red + 0.4)

# ─── 7. ABSTENTION sur capacité invalide ───
print("=== ABSTENTION si capacité invalide ===")
# masse mal formée -> belief non normalisé sur labels -> est_capacite False via encadre_esperance
st, raison = Q.encadre_esperance({("a",): 0.5}, {"a": 1.0, "b": 0.0})   # ν(Ω)=Bel({a,b})=0.5≠1
print(f"   masse incomplète -> {st} ({raison})")
check("capacité avec μ(Ω)≠1 → ABSTENTION", st == ABSTENTION)
st2, _ = Q.encadre_esperance({("a", "b"): 1.0}, {"a": 1.0, "b": 0.0})
check("masse valide → VALEUR", st2 == VALEUR)

print(f"\nRÉSULTAT choquet : {ok}/{total}")
assert ok == total
