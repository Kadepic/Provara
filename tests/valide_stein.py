"""
VALIDATION du PARADOXE DE STEIN (stein.py). Vérifie : le risque MLE = d ; James-Stein DOMINE le MLE en risque total pour
d≥3 (tirages appariés) ; la domination tient pour θ loin de 0 (gain qui s'amenuise mais jamais négatif) ; le seuil d<3
(ABSTENTION, MLE admissible) ; le paradoxe par coordonnée (JS empire certaines coordonnées mais gagne au total) ;
l'ABSTENTION. Pur Python, rng seedé.
"""
from __future__ import annotations

import random

from garde_ressources import borne
import stein as S
from stein import ABSTENTION, ANALYSE

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


# ─── 1. Risque MLE = d ; James-Stein domine à d=3 ───
print("=== d=3 : James-Stein domine le MLE ===")
st, info = S.analyse([-2.0, 0.0, 2.0], T=40000, rng=random.Random(114))
print(f"   risque MLE={info['risque_mle']:.3f} (≈d=3) ; JS={info['risque_js']:.3f} ; gain {100*info['gain_relatif']:.0f} %")
check("le risque du MLE ≈ d", abs(info["risque_mle"] - 3) < 0.1)
check("James-Stein domine le MLE (risque total strictement inférieur)", info["risque_js"] < info["risque_mle"])
check("la façade marque domine=True", info["domine"])

# ─── 2. Gain plus fort en grande dimension ───
print("=== d=10 : gain accru ===")
st10, info10 = S.analyse([(i % 5) - 2 for i in range(10)], T=40000, rng=random.Random(2))
print(f"   d=10 : MLE={info10['risque_mle']:.2f} JS={info10['risque_js']:.2f} gain {100*info10['gain_relatif']:.0f} %")
check("James-Stein domine aussi à d=10", info10["risque_js"] < info10["risque_mle"])
check("le gain relatif est plus grand qu'à d=3", info10["gain_relatif"] > info["gain_relatif"])

# ─── 3. Domination même pour θ loin de 0 (gain → 0 mais jamais négatif) ───
print("=== Domination uniforme : θ loin de 0 ===")
grand = [50.0, -30.0, 12.0, 0.0, 7.0, -8.0, 21.0, 3.0, -15.0, 40.0]
stg, infog = S.analyse(grand, T=40000, rng=random.Random(3))
print(f"   ‖θ‖ grand : MLE={infog['risque_mle']:.2f} JS={infog['risque_js']:.2f} gain {100*infog['gain_relatif']:.1f} %")
check("la domination tient (JS ≤ MLE) même loin de la cible", infog["risque_js"] <= infog["risque_mle"] + 0.1)
check("le gain s'amenuise quand ‖θ‖ est grand (≈ MLE)", infog["gain_relatif"] < 0.05)

# ─── 4. Seuil d<3 : ABSTENTION (MLE admissible) ───
print("=== Seuil d<3 ===")
check("d=2 → ABSTENTION (MLE admissible, pas de domination)", S.analyse([1.0, 2.0], rng=random.Random(0))[0] == ABSTENTION)
check("d=1 → ABSTENTION", S.analyse([1.0], rng=random.Random(0))[0] == ABSTENTION)

# ─── 5. Paradoxe par coordonnée : JS empire certaines, gagne au total ───
print("=== Paradoxe par coordonnée ===")
# θ avec une coordonnée loin de 0 (sera empirée par le rétrécissement vers 0) et des zéros (très améliorés)
theta_mix = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 8.0]
stm, infom = S.analyse(theta_mix, T=40000, rng=random.Random(4))
cm, cj = infom["coord_mle"], infom["coord_js"]
pire = [k for k in range(len(cm)) if cj[k] > cm[k] + 1e-9]
print(f"   coordonnée 'loin' (θ=8) : MLE={cm[9]:.2f} → JS={cj[9]:.2f} ; total MLE={infom['risque_mle']:.2f} → JS={infom['risque_js']:.2f}")
check("au moins une coordonnée est EMPIRÉE par James-Stein", len(pire) >= 1)
check("mais le risque TOTAL est meilleur", infom["risque_js"] < infom["risque_mle"])
check("formule signale la sur-confiance du MLE à d≥3", "sur-confiant" in S.formule((st, info)))

# ─── 6. ABSTENTION rng ───
print("=== ABSTENTION ===")
check("rng manquant → ABSTENTION", S.analyse([1.0, 2.0, 3.0], rng=None)[0] == ABSTENTION)
check("cas valide → ANALYSE", st == ANALYSE)

print(f"\nRÉSULTAT stein : {ok}/{total}")
assert ok == total
