"""
VALIDATION de la NÉGLIGENCE DU TAUX DE BASE (taux_de_base.py). Vérifie : la VPP de Bayes confirmée par SIMULATION ; la
négligence du taux de base (naïf=sens ≫ VPP à faible prévalence) ; le paradoxe du faux positif (la plupart des positifs
sont faux) ; la dépendance monotone à la prévalence et VPP→0 quand prév→0 ; la mauvaise calibration du forecaster naïf
(Brier/log-loss) ; l'honnêteté à forte prévalence ; l'ABSTENTION. Pur Python, rng seedé.
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import taux_de_base as TB
from taux_de_base import ABSTENTION, ANALYSE

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


rng = random.Random(103)
sens, spec = 0.99, 0.99


def simule_positifs(sens, spec, prev, n):
    """Renvoie la liste des issues 'malade' (0/1) parmi les individus TEST-POSITIFS."""
    out = []
    for _ in range(n):
        malade = rng.random() < prev
        test = (rng.random() < sens) if malade else (rng.random() < 1 - spec)
        if test:
            out.append(1 if malade else 0)
    return out


# ─── 1. VPP de Bayes confirmée par simulation ───
print("=== VPP : théorie vs simulation ===")
prev = 0.01
issues = simule_positifs(sens, spec, prev, 2_000_000)
vpp_emp = sum(issues) / len(issues)
vpp_theo = TB.vpp(sens, spec, prev)
print(f"   VPP empirique={vpp_emp:.3f} ; théorie={vpp_theo:.3f}")
check("la VPP de Bayes colle à la simulation", abs(vpp_emp - vpp_theo) < 0.01)

# ─── 2. Négligence du taux de base : naïf ≫ VPP à faible prévalence ───
print("=== Négligence du taux de base ===")
st, info = TB.analyse(sens, spec, 0.001)
print(f"   prév=0.001 : VPP={info['vpp']:.3f} ; naïf(sens)={info['naive']:.2f} ; écart={info['ecart']:.3f}")
check("le naïf (=sensibilité) sur-estime massivement la VPP", info["naive"] > 5 * info["vpp"])

# ─── 3. Paradoxe du faux positif : la plupart des positifs sont faux ───
print("=== Paradoxe du faux positif ===")
check("à prév=0.001, >80 % des positifs sont faux (test pourtant excellent)", info["frac_faux_positifs"] > 0.8)

# ─── 4. Dépendance monotone à la prévalence ; VPP→0 quand prév→0 ───
print("=== Dépendance à la prévalence ===")
vpps = [TB.vpp(sens, spec, p) for p in (0.0001, 0.001, 0.01, 0.1, 0.5)]
print(f"   VPP par prévalence : {[round(v,3) for v in vpps]}")
check("la VPP croît strictement avec la prévalence", all(vpps[i] < vpps[i + 1] for i in range(len(vpps) - 1)))
check("la VPP → 0 quand la prévalence → 0", TB.vpp(sens, spec, 1e-7) < 1e-3)

# ─── 5. Calibration : le forecaster naïf est mal calibré (Brier & log-loss) ───
print("=== Mauvaise calibration du naïf (prév faible) ===")
bn, bb = info["brier_naif"], info["brier_bayes"]
print(f"   Brier : naïf={bn:.4f} ; bayésien(VPP)={bb:.4f}")
check("le Brier du naïf est bien pire que celui du bayésien", bn > bb + 0.01)
# log-loss empirique parmi les positifs simulés à prév=0.001
iss = simule_positifs(sens, spec, 0.001, 3_000_000)
def logloss(ys, p):
    p = min(max(p, 1e-9), 1 - 1e-9)
    return sum(-(y * math.log(p) + (1 - y) * math.log(1 - p)) for y in ys) / len(ys)
ll_naif = logloss(iss, TB.estimation_naive(sens))
ll_bayes = logloss(iss, TB.vpp(sens, spec, 0.001))
print(f"   log-loss : naïf={ll_naif:.3f} ; bayésien={ll_bayes:.3f}")
check("le log-loss du bayésien est meilleur que celui du naïf", ll_bayes < ll_naif)
check("formule signale la sur-confiance de 'positif = malade'", "sur-confiant" in TB.formule((st, info)))

# ─── 6. Honnêteté : à forte prévalence, le naïf ≈ VPP (pas de fausse accusation) ───
print("=== Honnêteté : à forte prévalence l'écart s'annule ===")
info_haut = TB.analyse(sens, spec, 0.5)[1]
print(f"   prév=0.5 : VPP={info_haut['vpp']:.3f} ; écart au naïf={info_haut['ecart']:.4f}")
check("à prév=0.5, le naïf et la VPP coïncident (écart ~0)", abs(info_haut["ecart"]) < 0.01)

# ─── 7. VPN sanité ───
print("=== VPN sanité ===")
check("la VPN est élevée à faible prévalence (les négatifs sont fiables)", TB.vpn(sens, spec, 0.001) > 0.99)

# ─── 8. ABSTENTION ───
print("=== ABSTENTION ===")
check("entrée hors [0,1] → ABSTENTION", TB.analyse(1.2, 0.9, 0.1)[0] == ABSTENTION)
check("cas valide → ANALYSE", st == ANALYSE)

print(f"\nRÉSULTAT taux_de_base : {ok}/{total}")
assert ok == total
