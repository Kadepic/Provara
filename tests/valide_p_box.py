"""
VALIDATION des P-BOXES (p_box.py) — jugée par calibration.py. Vérifie que la p-box construite depuis des données
intervalles ENCADRE la vraie CDF empirique (0 violation), borne correctement l'espérance et les quantiles, que
F̲≤F̄, que l'imprécision → 0 quand les intervalles se resserrent, et DÉMASQUE la sur-confiance de la CDF « précise »
(milieu des intervalles) dont le point rate la vraie probabilité (SUR-CONFIANT). Pur Python, léger (pas de lecteur).
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import p_box as PB
from p_box import ABSTENTION, PBOX
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


rng = random.Random(57)


def echantillon(rng, n):
    """n données intervalles + la vraie valeur cachée vᵢ ∈ [aᵢ,bᵢ]."""
    inter, vrais = [], []
    for _ in range(n):
        a = rng.uniform(-5, 5); w = rng.uniform(0, 4); b = a + w
        v = rng.uniform(a, b)
        inter.append((a, b)); vrais.append(v)
    return inter, vrais


def Fn(vrais, x):
    return sum(1 for v in vrais if v <= x) / len(vrais)


# ─── 1. Encadrement de la vraie CDF empirique (garantie) + F̲≤F̄ ───
print("=== La p-box encadre la vraie CDF empirique (∀x) ===")
viol = 0
order_ok = unit_ok = True
for _ in range(2000):
    inter, vrais = echantillon(rng, rng.randint(3, 12))
    st, pb = PB.depuis_intervalles(inter)
    pts = sorted(set([a for a, _ in inter] + [b for _, b in inter] + [rng.uniform(-6, 6) for _ in range(3)]))
    for x in pts:
        lo, hi = pb.proba_seuil(x)
        if not (lo <= Fn(vrais, x) + 1e-12 and Fn(vrais, x) <= hi + 1e-12):
            viol += 1
        if lo > hi + 1e-12:
            order_ok = False
        if not (-1e-12 <= lo <= 1 + 1e-12 and -1e-12 <= hi <= 1 + 1e-12):
            unit_ok = False
check("F̲(x) ≤ F_n(x) ≤ F̄(x) ∀x (0 violation)", viol == 0)
check("F̲ ≤ F̄ partout", order_ok)
check("F̲, F̄ ∈ [0,1]", unit_ok)

# ─── 2. Espérance bracketée ───
print("=== E[X] ∈ [E_bas, E_haut] contient la vraie moyenne ===")
e_viol = 0
for _ in range(3000):
    inter, vrais = echantillon(rng, rng.randint(3, 12))
    _, pb = PB.depuis_intervalles(inter)
    elo, ehi = pb.esperance()
    vraie_moy = sum(vrais) / len(vrais)
    if not (elo - 1e-12 <= vraie_moy <= ehi + 1e-12):
        e_viol += 1
check("vraie moyenne ∈ [E_bas, E_haut] (0 violation)", e_viol == 0)

# ─── 3. Quantiles bracketés + q_bas ≤ q_haut ───
print("=== Quantile q_p ∈ [q_bas, q_haut] contient le vrai quantile ===")
q_viol = qorder = 0
for _ in range(3000):
    inter, vrais = echantillon(rng, rng.randint(4, 12))
    _, pb = PB.depuis_intervalles(inter)
    sv = sorted(vrais); n = len(sv)
    for p in (0.25, 0.5, 0.75):
        qlo, qhi = pb.quantile(p)
        vrai_q = sv[min(n, max(1, math.ceil(p * n))) - 1]
        if not (qlo - 1e-12 <= vrai_q <= qhi + 1e-12):
            q_viol += 1
        if qlo > qhi + 1e-12:
            qorder += 1
check("vrai quantile ∈ [q_bas, q_haut] (0 violation)", q_viol == 0)
check("q_bas ≤ q_haut", qorder == 0)

# ─── 4. DÉMASQUE : la CDF « précise » (milieu) est SUR-CONFIANTE ───
print("=== Mode d'échec : CDF du milieu des intervalles (précise) ===")
int_pbox, int_mid, verites = [], [], []
for _ in range(1500):
    inter, vrais = echantillon(rng, rng.randint(5, 12))
    _, pb = PB.depuis_intervalles(inter)
    fmid = PB.cdf_precise(inter)
    for _ in range(3):
        x = rng.uniform(-6, 6)
        lo, hi = pb.proba_seuil(x)
        int_pbox.append((lo, hi)); int_mid.append((fmid(x), fmid(x))); verites.append(Fn(vrais, x))
covP = sum(1 for (lo, hi), v in zip(int_pbox, verites) if lo - 1e-12 <= v <= hi + 1e-12) / len(verites)
covM = CAL.couverture(int_mid, verites)[0]
vM, iM = CAL.verdict_couverture(int_mid, verites, 0.80)
print(f"   couverture p-box={covP:.3f} ; CDF milieu (point)={covM:.3f} ({vM})")
check("la p-box encadre la vraie probabilité (couverture = 1.0)", covP == 1.0)
check("la CDF précise (milieu) est SUR-CONFIANTE et couvre bien moins que la p-box", vM == SURCONFIANT and covP - covM > 0.2)

# ─── 5. Imprécision → 0 quand les intervalles se resserrent ───
print("=== Imprécision → 0 quand les données deviennent précises ===")
inter_larges = [(rng.uniform(0, 5), None) for _ in range(8)]
inter_larges = [(a, a + 3) for a, _ in inter_larges]
inter_fins = [(a, a + 0.05) for a, _ in inter_larges]
_, pbL = PB.depuis_intervalles(inter_larges)
_, pbF = PB.depuis_intervalles(inter_fins)
print(f"   imprécision large={pbL.largeur_max():.3f} ; fine={pbF.largeur_max():.3f}")
check("intervalles fins → imprécision bien plus petite", pbF.largeur_max() < pbL.largeur_max() - 0.2)

# ─── 6. ABSTENTION : a>b, liste vide ───
print("=== ABSTENTION ===")
st1, r1 = PB.depuis_intervalles([(3, 1)])
st2, r2 = PB.depuis_intervalles([])
print(f"   a>b -> {st1} ; vide -> {st2}")
check("a>b → ABSTENTION", st1 == ABSTENTION)
check("liste vide → ABSTENTION", st2 == ABSTENTION)
st3, _ = PB.depuis_intervalles([(1, 2), (2, 3)])
check("cas valide → PBOX", st3 == PBOX)

print(f"\nRÉSULTAT p_box : {ok}/{total}")
assert ok == total
