"""
VALIDATION du QUARTET D'ANSCOMBE (anscombe.py). Vérifie : les 4 jeux ont des stats résumées IDENTIQUES ; les diagnostics
les DISTINGUENT (II non-linéaire, III aberrant, IV fort levier, I propre) ; que retirer le point aberrant/levier change
la conclusion ; l'ABSTENTION. Pur Python déterministe.
"""
from __future__ import annotations

from garde_ressources import borne
import anscombe as A
from anscombe import ABSTENTION, ANALYSE

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


st, info = A.analyse()
S = info["stats"]
D = info["diagnostics"]

# ─── 1. Stats résumées identiques ───
print("=== Stats résumées identiques ===")
print(f"   tuple commun = {S['I']}")
check("les 4 jeux ont des stats résumées strictement identiques", info["stats_identiques"])
check("la droite de régression commune est y = 3 + 0.5x", S["I"][5] == 3.0 and S["I"][6] == 0.5)
check("la corrélation commune ≈ 0.82", S["I"][4] == 0.82)

# ─── 2. Les diagnostics distinguent les jeux ───
print("=== Les diagnostics distinguent les 4 structures ===")
print(f"   résidu_max : I={D['I']['residu_max']:.2f} III={D['III']['residu_max']:.2f}")
print(f"   gain_quad  : I={D['I']['gain_quadratique']:.2f} II={D['II']['gain_quadratique']:.2f}")
print(f"   levier_max : I={D['I']['levier_max']:.2f} IV={D['IV']['levier_max']:.2f}")
check("II est détecté NON-LINÉAIRE (gain quadratique élevé)", D["II"]["gain_quadratique"] > 0.9)
check("I n'est PAS détecté non-linéaire (gain quadratique faible)", D["I"]["gain_quadratique"] < 0.2)
check("III a une VALEUR ABERRANTE (résidu max élevé)", D["III"]["residu_max"] > 3.0)
check("I/II n'ont pas de gros résidu aberrant", D["I"]["residu_max"] < 2.5 and D["II"]["residu_max"] < 2.5)
check("IV a un point à FORT LEVIER (≈1)", D["IV"]["levier_max"] > 0.95)
check("I/II/III ont un levier modéré", all(D[k]["levier_max"] < 0.5 for k in ("I", "II", "III")))

# ─── 3. Chaque pathologie est isolée par UN diagnostic différent ───
print("=== Chaque jeu a sa signature ===")
check("la signature de II (non-linéarité) est unique", D["II"]["gain_quadratique"] > 0.9 and all(D[k]["gain_quadratique"] < 0.2 for k in ("I", "III", "IV")))
check("la signature de IV (levier) est unique", D["IV"]["levier_max"] > 0.95 and all(D[k]["levier_max"] < 0.5 for k in ("I", "II", "III")))

# ─── 4. Retirer le point aberrant de III change radicalement la corrélation ───
print("=== Sensibilité au point aberrant (III) ===")
xs3, ys3 = A.QUARTET["III"]
# retirer le point au plus gros résidu
a, b, _ = A.regression(xs3, ys3)
k = max(range(len(xs3)), key=lambda i: abs(ys3[i] - (a + b * xs3[i])))
xs3b = [xs3[i] for i in range(len(xs3)) if i != k]
ys3b = [ys3[i] for i in range(len(ys3)) if i != k]
_, _, r_sans = A.regression(xs3b, ys3b)
print(f"   corr III avec aberrant={S['III'][4]} ; sans={r_sans:.3f}")
check("retirer la valeur aberrante de III rend la corrélation quasi parfaite", r_sans > 0.99)
check("formule signale la sur-confiance des stats résumées", "sur-confiant" in A.formule((st, info)))

# ─── 5. ABSTENTION ───
print("=== ABSTENTION ===")
check("jeu trop petit → ABSTENTION", A.analyse({"x": ([1, 2], [1, 2])})[0] == ABSTENTION)
check("cas valide → ANALYSE", st == ANALYSE)

print(f"\nRÉSULTAT anscombe : {ok}/{total}")
assert ok == total
