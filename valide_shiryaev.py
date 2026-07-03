"""
VALIDATION de la DÉTECTION AU PLUS TÔT (shiryaev.py) — jugée par calibration.py. Vérifie : posteriors ∈ [0,1], le
CONTRÔLE DE FAUSSE ALARME (P(alarme avant τ) ≤ α via A=1−α), la CALIBRATION du posterior pₜ (≈ P(changement déjà
survenu)), le DÉMASQUE d'un détecteur naïf SUR-CONFIANT (fausse alarme ≫ α), le compromis délai/fausse-alarme, et la
détection effective (posterior → 1 après le changement). Pur Python, léger (pas de lecteur).
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import shiryaev as S
from shiryaev import ABSTENTION, DETECTION
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


rng = random.Random(67)
f0, f1 = S.gaussienne(0, 1), S.gaussienne(1.5, 1)
rho = 0.02
H = 500


def run(rng):
    """Tire τ ~ géométrique(ρ) et génère un flux : f0 avant τ, f1 à partir de τ (horizon H)."""
    tau = 1
    while rng.random() > rho and tau < H:
        tau += 1
    xs = [rng.gauss(0, 1) if t < tau else rng.gauss(1.5, 1) for t in range(1, H + 1)]
    return tau, xs


# ─── 1. Posteriors ∈ [0,1] + croissance après changement ───
print("=== Posteriors ∈ [0,1] ; → 1 après le changement ===")
tau, xs = run(rng)
ps = S.posteriors(xs, f0, f1, rho)
check("pₜ ∈ [0,1] partout", all(0 <= p <= 1 + 1e-12 for p in ps))
check("posterior → ~1 bien après le changement", ps[min(H, tau + 80) - 1] > 0.9)

# ─── 2. CONTRÔLE DE FAUSSE ALARME : P(alarme avant τ) ≤ α ───
print("=== Contrôle de fausse alarme (A = 1−α) ===")
alpha = 0.10
A = S.seuil_pour_alpha(alpha)
TR = 3000
fausses = 0
delais = []
for _ in range(TR):
    tau, xs = run(rng)
    T = S.detecte(xs, f0, f1, rho, A)
    if T is not None and T < tau:
        fausses += 1
    elif T is not None and T >= tau:
        delais.append(T - tau)
fa = fausses / TR
print(f"   taux de fausse alarme = {fa:.3f} (≤ α={alpha}) ; délai médian de détection = {sorted(delais)[len(delais)//2]}")
check("P(fausse alarme) ≤ α (garantie de Shiryaev)", fa <= alpha + 0.02)

# ─── 3. DÉMASQUE : détecteur naïf sur-confiant (fausse alarme ≫ α) ───
print("=== Détecteur naïf (|x|>1.96) : fausse alarme incontrôlée ===")
fausses_naif = 0
for _ in range(TR):
    tau, xs = run(rng)
    Tn = next((t for t, x in enumerate(xs, 1) if abs(x) > 1.96), None)
    if Tn is not None and Tn < tau:
        fausses_naif += 1
fan = fausses_naif / TR
print(f"   fausse alarme naïf = {fan:.3f} (≫ α={alpha})")
check("le détecteur naïf est SUR-CONFIANT (fausse alarme ≫ α)", fan > 3 * alpha)
check("Shiryaev contrôle bien mieux que le naïf", fa < fan / 2)

# ─── 4. CALIBRATION du posterior pₜ (≈ proba que le changement a eu lieu) ───
print("=== Calibration du posterior pₜ ===")
conf, just = [], []
for _ in range(1500):
    tau, xs = run(rng)
    ps = S.posteriors(xs, f0, f1, rho)
    for t in range(0, H, 17):                  # sous-échantillonne les instants
        conf.append(ps[t]); just.append(1 if (t + 1) >= tau else 0)
verdict, info = CAL.est_calibre(conf, just)
print(f"   ECE={info['ece']:.3f} écart-signe={info['ecart_signe']:+.3f} -> {verdict}")
check("posterior de Shiryaev CALIBRÉ (non sur-confiant)", verdict != SURCONFIANT and info["ece"] < 0.1)

# ─── 5. Compromis délai / fausse alarme ───
print("=== Compromis : A↑ ⇒ délai ↑, fausse alarme ↓ ===")
def mesure(A, reps=1500):
    fal = 0; dl = []
    for _ in range(reps):
        tau, xs = run(rng)
        T = S.detecte(xs, f0, f1, rho, A)
        if T is None:
            continue
        if T < tau:
            fal += 1
        else:
            dl.append(T - tau)
    return fal / reps, (sum(dl) / len(dl) if dl else 0)
fa_bas, d_bas = mesure(0.80)
fa_haut, d_haut = mesure(0.99)
print(f"   A=0.80 : fausse alarme={fa_bas:.3f} délai_moy={d_bas:.1f} ; A=0.99 : {fa_haut:.3f} délai_moy={d_haut:.1f}")
check("A↑ ⇒ moins de fausses alarmes", fa_haut <= fa_bas + 1e-9)
check("A↑ ⇒ délai de détection plus long", d_haut > d_bas)

# ─── 6. ABSTENTION ───
print("=== ABSTENTION ===")
st1, _ = S.analyse([], f0, f1, rho, alpha)
st2, _ = S.analyse([1.0, 2.0], f0, f1, 1.5, alpha)
st3, _ = S.analyse([1.0, 2.0], f0, f1, rho, 2.0)
check("données vides → ABSTENTION", st1 == ABSTENTION)
check("ρ hors (0,1) → ABSTENTION", st2 == ABSTENTION)
check("α hors (0,1) → ABSTENTION", st3 == ABSTENTION)
st4, _ = S.analyse([0.0] * 5 + [3.0] * 20, f0, f1, rho, alpha)
check("cas valide → DETECTION", st4 == DETECTION)

print(f"\nRÉSULTAT shiryaev : {ok}/{total}")
assert ok == total
