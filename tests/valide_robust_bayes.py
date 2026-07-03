"""
VALIDATION du BAYES ROBUSTE par ε-contamination (robust_bayes.py) — jugé par calibration.py. Vérifie que la forme
close [min_θ r(θ), max_θ r(θ)] encadre la moyenne a posteriori pour TOUT prior de Γ (0 violation sur q aléatoires) et
que les bornes sont ATTEINTES par des masses de Dirac (tight) ; que l'intervalle dégénère en point à ε=0, s'élargit
avec ε, RÉTRÉCIT quand les données sont informatives (l'évidence achète la robustesse) ; et DÉMASQUE la sur-confiance
du posterior à prior unique (couverture s'effondre = SUR-CONFIANT). Pur Python, léger (pas de lecteur).
"""
from __future__ import annotations

import random

from garde_ressources import borne
import robust_bayes as RB
from robust_bayes import ABSTENTION, INTERVALLE
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


rng = random.Random(56)


def simplexe(rng, n):
    v = [rng.random() + 1e-3 for _ in range(n)]
    s = sum(v)
    return [x / s for x in v]


def probleme(rng, kmin=2, kmax=6):
    K = rng.randint(kmin, kmax)
    thetas = [f"t{i}" for i in range(K)]
    p0 = dict(zip(thetas, simplexe(rng, K)))
    L = {t: rng.random() for t in thetas}        # vraisemblance ∈ [0,1)
    A = set(rng.sample(thetas, rng.randint(1, K)))
    g = RB.indicatrice(A, thetas)
    return thetas, p0, L, g


def posterior_sous(p0, L, g, eps, q):
    """Moyenne a posteriori sous π=(1−ε)π₀+εq (q dict θ→poids)."""
    thetas = list(p0)
    pis = {t: (1 - eps) * p0[t] + eps * q[t] for t in thetas}
    num = sum(g[t] * L[t] * pis[t] for t in thetas)
    den = sum(L[t] * pis[t] for t in thetas)
    return num / den


# ─── 1. Forme close encadre TOUT prior de Γ + bornes tight (Dirac) ───
print("=== [inf,sup] encadre la moyenne a posteriori ∀ prior de Γ + tight ===")
viol = 0
tight_err = 0.0
for _ in range(1500):
    thetas, p0, L, g = probleme(rng)
    eps = rng.choice([0.1, 0.2, 0.35])
    inf, sup = RB.posterieur_contamine(p0, L, g, eps)
    # q aléatoires
    for _ in range(6):
        q = dict(zip(thetas, simplexe(rng, len(thetas))))
        val = posterior_sous(p0, L, g, eps, q)
        if not (inf - 1e-9 <= val <= sup + 1e-9):
            viol += 1
    # tightness : q = Dirac à l'argmax/argmin de r(θ)
    rs = {t: ((1 - eps) * sum(g[u]*L[u]*p0[u] for u in thetas) + eps * g[t]*L[t]) /
             ((1 - eps) * sum(L[u]*p0[u] for u in thetas) + eps * L[t]) for t in thetas}
    tmax = max(rs, key=rs.get); tmin = min(rs, key=rs.get)
    dmax = posterior_sous(p0, L, g, eps, {t: 1.0 if t == tmax else 0.0 for t in thetas})
    dmin = posterior_sous(p0, L, g, eps, {t: 1.0 if t == tmin else 0.0 for t in thetas})
    tight_err = max(tight_err, abs(dmax - sup), abs(dmin - inf))
check("0 violation d'encadrement (q aléatoires)", viol == 0)
check("bornes ATTEINTES par des masses de Dirac (tight)", tight_err < 1e-9)

# ─── 2. ε=0 → point = nominal ; intervalle ⊆ [0,1] (proba) ───
print("=== ε=0 dégénère ; intervalle dans [0,1] ===")
deg_ok = unit_ok = True
for _ in range(1500):
    thetas, p0, L, g = probleme(rng)
    i0, s0 = RB.posterieur_contamine(p0, L, g, 0.0)
    if abs(i0 - s0) > 1e-12 or abs(i0 - RB.posterieur_nominal(p0, L, g)) > 1e-12:
        deg_ok = False
    inf, sup = RB.posterieur_contamine(p0, L, g, rng.choice([0.1, 0.3]))
    if not (-1e-9 <= inf <= sup <= 1 + 1e-9):
        unit_ok = False
check("ε=0 → intervalle dégénéré = posterior nominal", deg_ok)
check("intervalle de probabilité ⊆ [0,1]", unit_ok)

# ─── 3. Largeur croît avec ε ───
print("=== Largeur croissante en ε ===")
mono_ok = True
for _ in range(1500):
    thetas, p0, L, g = probleme(rng)
    larg = [RB.posterieur_contamine(p0, L, g, e)[1] - RB.posterieur_contamine(p0, L, g, e)[0]
            for e in (0.0, 0.1, 0.25, 0.5)]
    if not all(larg[i] <= larg[i+1] + 1e-9 for i in range(len(larg)-1)):
        mono_ok = False; break
check("largeur de l'intervalle non-décroissante en ε", mono_ok)

# ─── 4. L'évidence achète la robustesse : données piquées → intervalle plus étroit (ε fixé) ───
print("=== Données informatives → intervalle plus étroit (à ε fixé) ===")
thetas = ["a", "b", "c"]
p0 = {"a": 0.4, "b": 0.35, "c": 0.25}
g = RB.indicatrice(["a"], thetas)
L_plate = {"a": 0.5, "b": 0.5, "c": 0.5}
L_piquee = {"a": 0.95, "b": 0.03, "c": 0.02}
w_plate = (lambda r: r[1]-r[0])(RB.posterieur_contamine(p0, L_plate, g, 0.2))
w_piquee = (lambda r: r[1]-r[0])(RB.posterieur_contamine(p0, L_piquee, g, 0.2))
print(f"   largeur données plates={w_plate:.3f} ; piquées={w_piquee:.3f}")
check("données informatives → intervalle nettement plus étroit", w_piquee < w_plate - 0.1)

# ─── 5. DÉMASQUE : posterior à prior unique = SUR-CONFIANT ───
print("=== Mode d'échec : le posterior à prior unique sous-couvre ===")
int_rob, int_nom, verites = [], [], []
for _ in range(1500):
    thetas, p0, L, g = probleme(rng)
    eps = 0.25
    inf, sup = RB.posterieur_contamine(p0, L, g, eps)
    nom = RB.posterieur_nominal(p0, L, g)
    q = dict(zip(thetas, simplexe(rng, len(thetas))))    # contaminant inconnu
    vrai = posterior_sous(p0, L, g, eps, q)
    int_rob.append((inf, sup)); int_nom.append((nom, nom)); verites.append(vrai)
covR = sum(1 for (lo, hi), v in zip(int_rob, verites) if lo - 1e-9 <= v <= hi + 1e-9) / len(verites)
covN = CAL.couverture(int_nom, verites)[0]
vN, iN = CAL.verdict_couverture(int_nom, verites, 0.80)
print(f"   couverture robuste={covR:.3f} ; point nominal={covN:.3f} ({vN})")
check("l'intervalle robuste couvre tout posterior de Γ (=1.0)", covR == 1.0)
check("le posterior à prior unique est SUR-CONFIANT", vN == SURCONFIANT and covN < 0.6)

# ─── 6. ABSTENTION : ε hors [0,1] ; vraisemblance nulle ───
print("=== ABSTENTION ===")
st1, _, r1 = RB.estime({"a": 1.0}, {"a": 0.5}, {"a": 1.0}, eps=1.5)
st2, _, r2 = RB.estime({"a": 0.5, "b": 0.5}, {"a": 0.0, "b": 0.0}, {"a": 1.0, "b": 0.0}, eps=0.2)
print(f"   ε=1.5 -> {st1} ; vraisemblance nulle -> {st2}")
check("ε hors [0,1] → ABSTENTION", st1 == ABSTENTION)
check("vraisemblance nulle partout → ABSTENTION", st2 == ABSTENTION)
st3, _, _ = RB.estime({"a": 0.5, "b": 0.5}, {"a": 0.6, "b": 0.4}, {"a": 1.0, "b": 0.0}, eps=0.2)
check("cas valide → INTERVALLE", st3 == INTERVALLE)

print(f"\nRÉSULTAT robust_bayes : {ok}/{total}")
assert ok == total
