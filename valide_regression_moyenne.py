"""
VALIDATION de la RÉGRESSION VERS LA MOYENNE (regression_moyenne.py). Vérifie que le groupe extrême régresse vers la
moyenne, que l'ampleur correspond à la théorie X̄₂≈μ+ρ(X̄₁−μ), les limites ρ=1 (aucune régression) et ρ=0 (totale),
le DÉMASQUE (le « rebond » observé ≈ ce que prédit la RTM sans cause), l'inversion louange/punition, et l'ABSTENTION.
Pur Python, léger.
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import regression_moyenne as RM
from regression_moyenne import ABSTENTION, RTM

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


rng = random.Random(86)


def echantillon(n, s_theta, s_eps):
    x1, x2 = [], []
    for _ in range(n):
        th = rng.gauss(0, s_theta)
        x1.append(th + rng.gauss(0, s_eps)); x2.append(th + rng.gauss(0, s_eps))
    return x1, x2


# ─── 1. Le groupe extrême régresse vers la moyenne ───
print("=== Le groupe extrême régresse vers la moyenne ===")
x1, x2 = echantillon(5000, 1, 1)
i = RM.regression_vers_moyenne(x1, x2, 0.1, "bas")
print(f"   pires 10% : |X̄₁−μ|={i['ecart_x1']:.2f} → |X̄₂−μ|={i['ecart_x2']:.2f} (ρ={i['rho']:.2f})")
check("la 2ᵉ mesure est PLUS PROCHE de la moyenne (régression)", i["ecart_x2"] < i["ecart_x1"])

# ─── 2. Ampleur conforme à la théorie X̄₂ ≈ μ + ρ(X̄₁−μ) ───
print("=== Ampleur conforme à la théorie ===")
print(f"   X̄₂ observé={i['moy_x2_sel']:.3f} vs RTM attendu={i['attendu_rtm']:.3f}")
check("X̄₂ ≈ μ + ρ(X̄₁−μ) (théorie de la RTM)", abs(i["moy_x2_sel"] - i["attendu_rtm"]) < 0.15)

# ─── 3. ρ=1 (pas de bruit) → aucune régression ───
print("=== ρ=1 (pas de bruit) → aucune régression ===")
x1b, x2b = echantillon(4000, 1, 0.001)
ib = RM.regression_vers_moyenne(x1b, x2b, 0.1, "bas")
check("ρ ≈ 1", ib["rho"] > 0.99)
check("aucune régression : X̄₂ ≈ X̄₁", abs(ib["moy_x2_sel"] - ib["moy_x1_sel"]) < 0.05)

# ─── 4. ρ≈0 (tout bruit) → régression totale vers μ ───
print("=== ρ≈0 (tout bruit) → régression totale ===")
x1c, x2c = echantillon(4000, 0.001, 1)
ic = RM.regression_vers_moyenne(x1c, x2c, 0.1, "bas")
check("ρ ≈ 0", abs(ic["rho"]) < 0.1)
check("régression totale : X̄₂ ≈ μ malgré X̄₁ extrême", abs(ic["moy_x2_sel"] - ic["mu"]) < 0.1 and ic["moy_x1_sel"] < -1)

# ─── 5. DÉMASQUE : le rebond observé ≈ ce que prédit la RTM (sans cause) ───
print("=== Mode d'échec : le 'rebond' = RTM, pas un effet ===")
chgmt = i["changement"]
rtm_attendu = i["attendu_rtm"] - i["moy_x1_sel"]
print(f"   changement observé={chgmt:+.3f} ; changement prédit par RTM={rtm_attendu:+.3f}")
check("le 'rebond' observé ≈ la RTM (attribuer à une cause serait sur-confiant)", abs(chgmt - rtm_attendu) < 0.15)
check("changement non nul (le piège : ça ressemble à un effet)", chgmt > 0.3)

# ─── 6. Inversion louange/punition ───
print("=== Inversion : meilleurs régressent vers le BAS, pires vers le HAUT ===")
haut = RM.regression_vers_moyenne(x1, x2, 0.1, "haut")
bas = RM.regression_vers_moyenne(x1, x2, 0.1, "bas")
print(f"   meilleurs : {haut['moy_x1_sel']:+.2f}→{haut['moy_x2_sel']:+.2f} ; pires : {bas['moy_x1_sel']:+.2f}→{bas['moy_x2_sel']:+.2f}")
check("les MEILLEURS régressent vers le bas (changement < 0 = 'la louange nuit')", haut["changement"] < 0)
check("les PIRES régressent vers le haut (changement > 0 = 'la punition marche')", bas["changement"] > 0)

# ─── 7. ABSTENTION ───
print("=== ABSTENTION ===")
st1, _ = RM.analyse([1, 2, 3], [1, 2, 3])
st2, _ = RM.analyse(list(range(20)), list(range(19)))
check("n<10 → ABSTENTION", st1 == ABSTENTION)
check("tailles différentes → ABSTENTION", st2 == ABSTENTION)
st3, _ = RM.analyse(x1, x2, 0.1, "bas")
check("cas valide → RTM", st3 == RTM)

print(f"\nRÉSULTAT regression_moyenne : {ok}/{total}")
assert ok == total
