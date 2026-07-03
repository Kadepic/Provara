"""
VALIDATION des COPULES (copules.py). Vérifie les bornes de Fréchet-Hoeffding (W ≤ C ≤ M), les conditions de bord, la
DÉPENDANCE DE QUEUE (indépendance ≈ 0, Clayton > 0 → λ théorique), le DÉMASQUE (présumer l'indépendance sous-estime
massivement le risque conjoint extrême sous dépendance, alors qu'elle est correcte sous vraie indépendance), la
monotonie du risque conjoint en θ, et l'ABSTENTION. Pur Python, léger (pas de lecteur).
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import copules as K
from copules import ABSTENTION, ANALYSE

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


rng = random.Random(72)

# ─── 1. Bornes de Fréchet-Hoeffding : W ≤ C ≤ M ───
print("=== Bornes de Fréchet-Hoeffding W ≤ C ≤ M ===")
frechet_ok = True
for _ in range(5000):
    u, v = rng.random(), rng.random()
    theta = rng.uniform(0.1, 5)
    for C in (K.independance(u, v), K.clayton(u, v, theta)):
        if not (K.borne_inf(u, v) - 1e-9 <= C <= K.borne_sup(u, v) + 1e-9):
            frechet_ok = False
check("max(u+v−1,0) ≤ C(u,v) ≤ min(u,v) (indépendance & Clayton)", frechet_ok)

# ─── 2. Conditions de bord ───
print("=== Conditions de bord C(u,0)=0, C(u,1)=u, C(1,v)=v ===")
bord_ok = True
for _ in range(3000):
    u, v = rng.random(), rng.random(); th = rng.uniform(0.2, 4)
    if abs(K.clayton(u, 1, th) - u) > 1e-9 or abs(K.clayton(1, v, th) - v) > 1e-9 or K.clayton(u, 0, th) != 0.0:
        bord_ok = False
    if abs(K.independance(u, 1) - u) > 1e-12 or K.independance(u, 0) != 0.0:
        bord_ok = False
check("conditions de bord (Clayton & indépendance)", bord_ok)

# ─── 3. Dépendance de queue : indépendance ≈ 0, Clayton → λ théorique ───
print("=== Dépendance de queue inférieure λ ===")
q = 0.02; N = 200000
ech_ind = [(rng.random(), rng.random()) for _ in range(N)]
lam_ind = K.tail_inf_empirique(ech_ind, q)
ech_cl = K.echantillon_clayton(rng, N, 2.0)
lam_cl = K.tail_inf_empirique(ech_cl, q)
print(f"   λ indépendance={lam_ind:.3f} (≈0) ; λ Clayton θ=2={lam_cl:.3f} (théo {K.lambda_inf_clayton(2.0):.3f})")
check("indépendance : λ ≈ 0 (pas de dépendance de queue)", lam_ind < 0.1)
check("Clayton θ=2 : λ > 0 et proche de 2^{−1/θ}", abs(lam_cl - K.lambda_inf_clayton(2.0)) < 0.1)

# ─── 4. DÉMASQUE : l'indépendance sous-estime le risque conjoint sous dépendance ───
print("=== Mode d'échec : présumer l'indépendance sous dépendance de queue ===")
qd = 0.05
info_cl = K.analyse(K.echantillon_clayton(rng, 150000, 2.0), qd)[1]
print(f"   Clayton : P_jointe={info_cl['jointe_empirique']:.4f} vs indép {info_cl['jointe_independance']:.4f} (×{info_cl['facteur']:.1f})")
check("sous dépendance, le risque conjoint réel ≫ estimation indépendante (sur-confiance démasquée)", info_cl["facteur"] > 5)
# l'empirique ≈ la valeur de la copule C(q,q)
check("P_jointe empirique ≈ C(q,q) de Clayton (le bon modèle)", abs(info_cl["jointe_empirique"] - K.clayton(qd, qd, 2.0)) < 0.005)

# ─── 5. Sous VRAIE indépendance, l'estimation indépendante est correcte ───
print("=== Sous vraie indépendance : P_jointe ≈ q² ===")
info_ind = K.analyse([(rng.random(), rng.random()) for _ in range(150000)], qd)[1]
print(f"   P_jointe={info_ind['jointe_empirique']:.4f} vs q²={info_ind['jointe_independance']:.4f} (×{info_ind['facteur']:.2f})")
check("sous vraie indépendance, l'estimation indépendante est calibrée (facteur ≈ 1)", abs(info_ind["facteur"] - 1) < 0.25)

# ─── 6. Monotonie : θ↑ ⇒ risque conjoint ↑ ───
print("=== Monotonie : dépendance plus forte ⇒ risque conjoint plus grand ===")
pj_faible = K.proba_jointe_extreme(K.echantillon_clayton(rng, 150000, 0.5), qd)
pj_fort = K.proba_jointe_extreme(K.echantillon_clayton(rng, 150000, 5.0), qd)
print(f"   P_jointe θ=0.5 : {pj_faible:.4f} ; θ=5 : {pj_fort:.4f}")
check("θ plus grand (plus de dépendance) ⇒ risque conjoint plus grand", pj_fort > pj_faible)

# ─── 7. ABSTENTION ───
print("=== ABSTENTION ===")
st1, _ = K.analyse([], 0.05)
st2, _ = K.analyse([(0.5, 0.5)], 1.5)
check("échantillon vide → ABSTENTION", st1 == ABSTENTION)
check("q hors (0,1) → ABSTENTION", st2 == ABSTENTION)
st3, _ = K.analyse([(0.1, 0.2), (0.3, 0.05)], 0.1)
check("cas valide → ANALYSE", st3 == ANALYSE)

print(f"\nRÉSULTAT copules : {ok}/{total}")
assert ok == total
