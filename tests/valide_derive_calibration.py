"""
VALIDATION du DÉTECTEUR DE DÉRIVE DE CALIBRATION (derive_calibration.py). Invariant : sous H0 (calibration stable),
les FAUSSES ALARMES sont rares ; sous SUR-CONFIANCE apparaissant en cours de flux, l'alarme se lève (détection) ;
la SOUS-confiance (sûre) ne déclenche PAS d'alarme.
"""
from __future__ import annotations

import random

from garde_ressources import borne
import derive_calibration as DD
from derive_calibration import ALERTE, STABLE

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


def flux_alarme(shift, T, M, base):
    """M flux : confiance c~U(0.5,1), justesse ~ Bernoulli(c − shift) (shift>0 = sur-confiant). Renvoie
    (fraction de flux qui alarment, délai moyen de détection)."""
    nb, delai = 0, 0
    for r in range(M):
        rng = random.Random(base + r)
        d = DD.DetecteurDerive()
        a = None
        for t in range(T):
            c = 0.5 + 0.5 * rng.random()
            j = 1 if rng.random() < max(0.0, min(1.0, c - shift)) else 0
            if d.observe(c, j)[0] == ALERTE:
                a = t
                break
        if a is not None:
            nb += 1
            delai += a
    return nb / M, (delai / nb if nb else None)


print("=== H0 (calibration STABLE) : fausses alarmes RARES sur 1000 pas ===")
fa, _ = flux_alarme(0.0, 1000, 400, base=0)
print(f"   fausses alarmes / 1000 pas = {fa:.3f}")
check(f"fausses alarmes ({fa:.3f}) <= 0.05", fa <= 0.05)

print("=== SUR-CONFIANCE apparue : détection fiable + délai raisonnable ===")
for shift in (0.15, 0.25, 0.40):
    dr, delai = flux_alarme(shift, 800, 300, base=1000)
    print(f"   sur-confiance {shift} : détection={dr:.3f}, délai moyen={delai:.0f}")
    check(f"sur-confiance {shift} : détection {dr:.3f} >= 0.95", dr >= 0.95)

print("=== sur-confiance PLUS FORTE -> détection PLUS RAPIDE (monotonie du délai) ===")
_, d15 = flux_alarme(0.15, 800, 300, base=2000)
_, d40 = flux_alarme(0.40, 800, 300, base=2000)
check(f"délai(0.40)={d40:.0f} < délai(0.15)={d15:.0f}", d40 < d15)

print("=== SOUS-CONFIANCE (sûre) : PAS d'alarme (on ne flagge que la ligne rouge) ===")
fa_sous, _ = flux_alarme(-0.25, 1000, 400, base=3000)     # justesse > confiance = prudent
print(f"   alarmes sous sous-confiance = {fa_sous:.3f}")
check(f"sous-confiance : alarmes ({fa_sous:.3f}) <= 0.05 (direction sûre ignorée)", fa_sous <= 0.05)

print("=== DÉTECTION APRÈS le point de bascule (pas avant) ===")
# flux calibré 1500 pas puis sur-confiant : l'alarme doit tomber APRÈS 1500 dans la grande majorité des cas
apres = 0
M = 300
for r in range(M):
    rng = random.Random(4000 + r)
    d = DD.DetecteurDerive()
    a = None
    for t in range(2300):
        c = 0.5 + 0.5 * rng.random()
        p = c if t < 1500 else max(0.0, c - 0.25)
        j = 1 if rng.random() < p else 0
        if d.observe(c, j)[0] == ALERTE:
            a = t
            break
    if a is not None and a >= 1500:
        apres += 1
check(f"alarme après la bascule (1500) dans >= 95% des cas : {apres/M:.3f}", apres / M >= 0.95)

print("=== réinitialisation ===")
d = DD.DetecteurDerive(k=0.10, h=2.0)
for _ in range(200):
    d.observe(1.0, 0)       # sur-confiance maximale -> alarme
check("alarme levée", d.statut() == ALERTE)
d.reinitialise()
check("après reinitialise -> STABLE", d.statut() == STABLE)

print(f"\nDÉRIVE CALIBRATION VALIDÉ — {ok}/{total}." if ok == total else f"\nÉCHEC {ok}/{total}")
