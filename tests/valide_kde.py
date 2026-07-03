"""
VALIDATION du KDE (kde.py). Vérifie que f̂ est une densité valide (≥0, intègre à ~1), que les modes-fantômes
explosent quand h est trop petit, que la vraisemblance leave-one-out est MAXIMALE à un h intermédiaire (h petit =
catastrophe = sur-confiance démasquée), que le h optimal recouvre la bonne structure (uni/bimodale) et est proche de
Silverman, et l'ABSTENTION. Pur Python, léger (n modéré).
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import kde as K
from kde import ABSTENTION, DENSITE

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


rng = random.Random(81)
xs = [rng.gauss(0, 1) for _ in range(100)]
h_s = K.silverman(xs)

# ─── 1. Densité valide (≥0, intègre à ~1) ───
print("=== f̂ est une densité valide ===")
grille = [-6 + 12 * k / 600 for k in range(601)]
vals = [K.densite(xs, x, h_s) for x in grille]
integ = sum(vals) * (12 / 600)
check("f̂ ≥ 0 partout", all(v >= 0 for v in vals))
check("∫ f̂ ≈ 1", abs(integ - 1) < 0.02)

# ─── 2. Modes-fantômes : n_modes ↓ avec h ───
print("=== Modes-fantômes : trop de modes si h trop petit ===")
m_petit = K.n_modes(xs, h_s / 6)
m_opt = K.n_modes(xs, h_s)
print(f"   n_modes : h petit={m_petit} ; h Silverman={m_opt}")
check("h trop petit → beaucoup de modes-fantômes (>5)", m_petit > 5)
check("h Silverman → ~1 mode (vraie densité unimodale)", m_opt <= 2)
check("n_modes décroît quand h grandit", K.n_modes(xs, h_s / 6) >= K.n_modes(xs, h_s) >= K.n_modes(xs, h_s * 4) - 1)

# ─── 3. Vraisemblance LOO maximale à h intermédiaire ; h petit catastrophique ───
print("=== Vraisemblance leave-one-out : maximale à h intermédiaire ===")
hopt = K.h_optimal(xs)
loo_opt = K.log_vraisemblance_loo(xs, hopt)
loo_petit = K.log_vraisemblance_loo(xs, h_s / 8)
loo_grand = K.log_vraisemblance_loo(xs, h_s * 8)
print(f"   LOO : h_opt={loo_opt:.1f} ; h petit={loo_petit:.1f} ; h grand={loo_grand:.1f}")
check("h optimal (LOO) bat un h trop petit", loo_opt > loo_petit)
check("h optimal (LOO) bat un h trop grand", loo_opt > loo_grand)
check("h trop petit = catastrophe (sur-confiance démasquée par held-out)", loo_petit < loo_opt - 5)

# ─── 4. h optimal ≈ Silverman, recouvre la bonne structure (unimodale) ───
print("=== h optimal ≈ Silverman ; structure correcte ===")
print(f"   Silverman={h_s:.3f} ; h optimal={hopt:.3f}")
check("h optimal du même ordre que Silverman (×0.4–2.5)", 0.4 * h_s <= hopt <= 2.5 * h_s)
check("au h optimal : densité unimodale (1 mode) recouvrée", K.n_modes(xs, hopt) == 1)

# ─── 5. Bimodale : ne pas laver la vraie structure ───
print("=== Données bimodales : recouvrer les 2 modes ===")
bim = [rng.gauss(-3, 0.5) for _ in range(60)] + [rng.gauss(3, 0.5) for _ in range(60)]
hb = K.h_optimal(bim)
nb = K.n_modes(bim, hb)
print(f"   bimodale : h optimal={hb:.3f}, n_modes={nb}")
check("le h optimal recouvre 2 modes (vraie structure bimodale)", nb == 2)

# ─── 6. ABSTENTION ───
print("=== ABSTENTION ===")
st1, _ = K.analyse([1.0, 2.0])
st2, _ = K.analyse([1.0, 2.0, 3.0], h=-1.0)
check("n<3 → ABSTENTION", st1 == ABSTENTION)
check("h≤0 → ABSTENTION", st2 == ABSTENTION)
st3, _ = K.analyse(xs)
check("cas valide → DENSITE", st3 == DENSITE)

print(f"\nRÉSULTAT kde : {ok}/{total}")
assert ok == total
