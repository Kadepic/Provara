"""
VALIDATION de l'INTERVALLE DE PROPORTION BINOMIALE (proportion_binomiale.py) — jugé par calibration.py. Par Monte-Carlo
sur des régimes DIFFICILES (n petit, p extrême), la couverture EMPIRIQUE de WILSON et AGRESTI-COULL ≈ nominal (non
sur-confiants), tandis que WALD s'effondre sous le nominal (SUR-CONFIANT). À grand n / p modéré, les trois convergent
(le défaut de Wald est spécifique au petit effectif / extrême). Cas dégénéré k=0 : Wald donne la fausse certitude [0,0].
"""
from __future__ import annotations

import random

from garde_ressources import borne
import proportion_binomiale as P
from proportion_binomiale import ESTIMATION, ABSTENTION
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


def tire_k(rng, n, p):
    return sum(1 for _ in range(n) if rng.random() < p)


def couverture_empirique(methode, n, p, confiance, reps, rng):
    """Renvoie (verdict, infos) de calibration.verdict_couverture pour la méthode sur (n,p)."""
    inter, ver = [], []
    fn = getattr(P, methode)
    for _ in range(reps):
        k = tire_k(rng, n, p)
        inter.append(fn(k, n, confiance))
        ver.append(p)
    return CAL.verdict_couverture(inter, ver, confiance)


REPS = 12000
rng = random.Random(7)

print("=== Régime DIFFICILE n=20, p=0.10, nominal 0.95 ===")
vWi, iWi = couverture_empirique("wilson", 20, 0.10, 0.95, REPS, rng)
vAc, iAc = couverture_empirique("agresti_coull", 20, 0.10, 0.95, REPS, rng)
vWa, iWa = couverture_empirique("wald", 20, 0.10, 0.95, REPS, rng)
print(f"   Wilson={iWi['couverture']:.3f} ({vWi}) ; Agresti-Coull={iAc['couverture']:.3f} ({vAc}) ; "
      f"Wald={iWa['couverture']:.3f} ({vWa})")
check("Wilson : couverture ~nominal (>=0.93) et NON sur-confiant", iWi["couverture"] >= 0.93 and vWi != SURCONFIANT)
check("Agresti-Coull : couverture ~nominal (>=0.93) et NON sur-confiant", iAc["couverture"] >= 0.93 and vAc != SURCONFIANT)
check("Wald : SUR-CONFIANT (sous-couvre, <0.93)", vWa == SURCONFIANT and iWa["couverture"] < 0.93)

print("=== 2ᵉ régime difficile n=30, p=0.05 : Wald s'effondre encore plus ===")
vWi2, iWi2 = couverture_empirique("wilson", 30, 0.05, 0.95, REPS, rng)
vWa2, iWa2 = couverture_empirique("wald", 30, 0.05, 0.95, REPS, rng)
print(f"   Wilson={iWi2['couverture']:.3f} ({vWi2}) ; Wald={iWa2['couverture']:.3f} ({vWa2})")
check("Wilson tient (>=0.92, non sur-confiant)", iWi2["couverture"] >= 0.92 and vWi2 != SURCONFIANT)
check("Wald sur-confiant au 2ᵉ régime", vWa2 == SURCONFIANT)

print("=== Grand n / p modéré (n=400, p=0.40) : les trois convergent (Wald OK ici) ===")
vWa3, iWa3 = couverture_empirique("wald", 400, 0.40, 0.95, 6000, rng)
print(f"   Wald={iWa3['couverture']:.3f} ({vWa3})")
check("Wald NON sur-confiant à grand n / p modéré (défaut spécifique au petit effectif)", vWa3 != SURCONFIANT)

print("=== Cas dégénéré k=0/n=10 : Wald = certitude factice [0,0], Wilson honnête ===")
w0 = P.wald(0, 10); wi0 = P.wilson(0, 10)
print(f"   Wald={w0} ; Wilson={wi0}")
check("Wald k=0 dégénère en [0,0] (fausse certitude)", w0[0] == 0.0 and w0[1] == 0.0)
check("Wilson k=0 borne haute > 0 (honnête) et <=1", wi0[0] == 0.0 and 0.0 < wi0[1] <= 1.0)

print("=== Bornes toujours dans [0,1] (Wilson, Agresti-Coull) sur cas extrêmes ===")
bornes_ok = True
for k, n in [(0, 5), (5, 5), (1, 3), (9, 10)]:
    for m in ("wilson", "agresti_coull"):
        lo, hi = getattr(P, m)(k, n)
        if not (0.0 <= lo <= hi <= 1.0):
            bornes_ok = False
check("Wilson & Agresti-Coull restent dans [0,1] (cas extrêmes)", bornes_ok)

print("=== ABSTENTION si n=0 ou k hors plage ===")
st0, _, r0 = P.intervalle(0, 0)
stx, _, rx = P.intervalle(5, 3)
print(f"   n=0 -> {st0} ({r0}) ; k>n -> {stx} ({rx})")
check("ABSTENTION sur n=0", st0 == ABSTENTION)
check("ABSTENTION sur k hors [0,n]", stx == ABSTENTION)

print(f"\nRÉSULTAT proportion_binomiale : {ok}/{total}")
assert ok == total
