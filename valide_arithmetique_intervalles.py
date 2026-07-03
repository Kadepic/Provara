"""
VALIDATION de l'ARITHMÉTIQUE D'INTERVALLES (arithmetique_intervalles.py) — jugée par calibration.py. Le théorème
fondamental (Moore) dit que l'évaluation par intervalles ENCADRE toujours l'image réelle : couverture empirique = 1
(jamais sur-confiante). La méthode « point » (milieu) jette l'incertitude → couverture ≈ 0 = SUR-CONFIANTE. Vérifie
aussi : arrondi EXTÉRIEUR rigoureux (vs vérité rationnelle exacte), problème de dépendance (côté sûr), inclusion
isotone, ABSTENTION sur ÷ par 0. Pur Python, léger (pas de lecteur).
"""
from __future__ import annotations

import random
from fractions import Fraction

from garde_ressources import borne
import arithmetique_intervalles as A
from arithmetique_intervalles import Intervalle, ABSTENTION, INTERVALLE
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


# Fonctions test (composées de +,−,×,÷)
FONCTIONS = [
    ("a·b − a + 2·b", lambda a, b: a * b - a + 2 * b),
    ("(a·b + 1)/(a + 3)", lambda a, b: (a * b + 1) / (a + 3)),   # a≥0 -> a+3>0
    ("a·a − b", lambda a, b: a * a - b),                          # dépendance sur a
]

rng = random.Random(31)

# ─── 1 & 2. Couverture : interval = garanti (1.0), point = sur-confiant (≈0) ───
print("=== Théorème fondamental : l'intervalle ENCADRE toujours ; le point SUR-CONFIE ===")
enc_int, enc_pt, verites = [], [], []
for _ in range(2400):
    nom, f = rng.choice(FONCTIONS)
    a0 = rng.uniform(0.1, 4.0); aw = rng.uniform(0.1, 2.0)
    b0 = rng.uniform(-3.0, 3.0); bw = rng.uniform(0.1, 2.0)
    Ia, Ib = Intervalle(a0, a0 + aw), Intervalle(b0, b0 + bw)
    st, res = A.evalue(f, Ia, Ib)
    if st != INTERVALLE:
        continue
    asamp = rng.uniform(Ia.bas, Ia.haut); bsamp = rng.uniform(Ib.bas, Ib.haut)
    vrai = f(asamp, bsamp)
    enc_int.append(tuple(res))
    pt = A.plugin_point(f, Ia, Ib)
    enc_pt.append((pt, pt))
    verites.append(vrai)

vInt, iInt = CAL.verdict_couverture(enc_int, verites, 0.90)
vPt, iPt = CAL.verdict_couverture(enc_pt, verites, 0.90)
print(f"   intervalle : couverture {iInt['couverture']:.4f} ({vInt})")
print(f"   point      : couverture {iPt['couverture']:.4f} ({vPt})")
check("intervalle : couverture = 1.0 (encadrement garanti)", iInt["couverture"] == 1.0)
check("intervalle : JAMAIS sur-confiant (côté sûr)", vInt != SURCONFIANT)
check("point (milieu) : SUR-CONFIANT (couverture s'effondre)", vPt == SURCONFIANT and iPt["couverture"] < 0.2)

# ─── 3. Arrondi EXTÉRIEUR rigoureux : l'intervalle contient la vérité RATIONNELLE exacte ───
print("=== Arrondi extérieur : encadre la vérité rationnelle exacte (soundness flottante) ===")
viol_round = 0
for _ in range(20000):
    a = rng.uniform(-1e6, 1e6); b = rng.uniform(-1e6, 1e6)
    Ia, Ib = Intervalle(a), Intervalle(b)
    for op, exact in ((Ia + Ib, Fraction(a) + Fraction(b)),
                      (Ia - Ib, Fraction(a) - Fraction(b)),
                      (Ia * Ib, Fraction(a) * Fraction(b))):
        if not (Fraction(op.bas) <= exact <= Fraction(op.haut)):
            viol_round += 1
check("aucune violation d'encadrement de la vérité exacte (0/60000 ops, ±,×)", viol_round == 0)

# ─── 4. Opérations correctes sur cas connus (à 1 ULP près : l'arrondi extérieur élargit légèrement, côté SÛR) ───
print("=== Opérations sur cas connus (encadrent les bornes attendues à ~1 ULP) ===")
x, y = Intervalle(2, 3), Intervalle(-1, 1)
def cadre(I, lo, hi, eps=1e-9):
    """L'intervalle calculé CONTIENT [lo,hi] et n'en déborde que de l'arrondi extérieur (≤ eps)."""
    return I.bas <= lo + eps and I.haut >= hi - eps and abs(I.bas - lo) <= eps and abs(I.haut - hi) <= eps
check("[2,3]+[-1,1] ≈ [1,4]", cadre(x + y, 1, 4))
check("[2,3]-[-1,1] ≈ [1,4]", cadre(x - y, 1, 4))
check("[2,3]*[-1,1] ≈ [-3,3]", cadre(x * y, -3, 3))
check("[2,3]/[1,2] ≈ [1,3]", cadre(Intervalle(2, 3) / Intervalle(1, 2), 1, 3))
check("coercition scalaire : 5 + [2,3] ≈ [7,8]", cadre(5 + x, 7, 8))

# ─── 5. Problème de dépendance : x − x ⊇ 0, largeur > 0 (conservateur, côté SÛR) ───
print("=== Dépendance : x − x surestime la largeur mais CONTIENT 0 (jamais sur-confiant) ===")
dd = x - x
print(f"   [2,3] − [2,3] = {dd}")
check("x − x contient 0", dd.contient(0.0))
check("x − x a une largeur > 0 (surestimation conservatrice, pas 0)", dd.largeur > 0)

# ─── 6. ABSTENTION sur division par un intervalle contenant 0 ───
print("=== ÷ par intervalle contenant 0 → ABSTENTION ===")
st0, r0 = A.evalue(lambda a: 1 / a, Intervalle(-1, 1))
print(f"   1/[-1,1] -> {st0} ({r0})")
check("÷ par 0∈[.] → ABSTENTION", st0 == ABSTENTION)
leve = False
try:
    _ = Intervalle(1, 2) / Intervalle(-1, 1)
except ZeroDivisionError:
    leve = True
check("division directe par 0∈[.] lève ZeroDivisionError", leve)

# ─── 7. Inclusion isotone : [x']⊆[x] ⇒ [f]([x'])⊆[f]([x]) ───
print("=== Inclusion isotone (monotonie de l'extension par intervalles) ===")
iso_ok = True
for _ in range(3000):
    nom, f = rng.choice(FONCTIONS[:1] + FONCTIONS[2:])  # éviter ÷ (sous-intervalle pourrait franchir 0)
    a0 = rng.uniform(0.5, 4.0); aw = rng.uniform(0.5, 2.0)
    b0 = rng.uniform(-3.0, 3.0); bw = rng.uniform(0.5, 2.0)
    Ia, Ib = Intervalle(a0, a0 + aw), Intervalle(b0, b0 + bw)
    # sous-intervalles
    sa0 = rng.uniform(Ia.bas, Ia.haut); sa1 = rng.uniform(sa0, Ia.haut)
    sb0 = rng.uniform(Ib.bas, Ib.haut); sb1 = rng.uniform(sb0, Ib.haut)
    st1, big = A.evalue(f, Ia, Ib)
    st2, small = A.evalue(f, Intervalle(sa0, sa1), Intervalle(sb0, sb1))
    if st1 == INTERVALLE and st2 == INTERVALLE:
        if not (big[0] - 1e-9 <= small[0] and small[1] <= big[1] + 1e-9):
            iso_ok = False
            break
check("[f] est inclusion-isotone (sous-intervalle → sous-résultat)", iso_ok)

# ─── 8. Intervalle vide / NaN rejetés ───
print("=== Intervalles invalides rejetés ===")
def leve_val(fn):
    try:
        fn(); return False
    except ValueError:
        return True
check("bas > haut → ValueError", leve_val(lambda: Intervalle(3, 2)))
check("NaN → ValueError", leve_val(lambda: Intervalle(float("nan"))))

print(f"\nRÉSULTAT arithmetique_intervalles : {ok}/{total}")
assert ok == total
