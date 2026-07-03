"""
VALIDATION de l'INÉGALITÉ DE JENSEN (jensen.py). Vérifie : f convexe → E[f]>f(E) (brancher la moyenne sous-estime) ;
f concave → E[f]<f(E) (sur-estime) ; f linéaire → écart ≈ 0 (exact) ; pour x² l'écart vaut EXACTEMENT σ² et croît avec
la variance ; σ=0 → écart nul (honnêteté) ; l'ABSTENTION. Pur Python, rng seedé.
"""
from __future__ import annotations

import math
import random

from garde_ressources import borne
import jensen as J
from jensen import ABSTENTION, ANALYSE

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


carre = lambda x: x * x
racine = lambda x: math.sqrt(max(x, 0))
lin = lambda x: 3 * x

# ─── 1. Convexe : E[f] > f(E) ───
print("=== Convexe : brancher la moyenne sous-estime ===")
st, info = J.analyse(carre, 10.0, 3.0, "convexe", rng=random.Random(129))
print(f"   x² : E[f]={info['e_f']:.3f} ; f(E)={info['f_e']:.3f} ; écart={info['ecart']:+.3f}")
check("f convexe : E[f(X)] > f(E[X]) (écart > 0)", info["ecart"] > 0.5)
check("le signe de l'écart correspond à la convexité", info["signe_attendu_ok"])

# ─── 2. Concave : E[f] < f(E) ───
print("=== Concave : brancher la moyenne sur-estime ===")
stc, infoc = J.analyse(racine, 10.0, 3.0, "concave", rng=random.Random(2))
print(f"   √x : E[f]={infoc['e_f']:.3f} ; f(E)={infoc['f_e']:.3f} ; écart={infoc['ecart']:+.3f}")
check("f concave : E[f(X)] < f(E[X]) (écart < 0)", infoc["ecart"] < 0)
check("le signe correspond à la concavité", infoc["signe_attendu_ok"])

# ─── 3. Linéaire : écart ≈ 0 ───
print("=== Linéaire : brancher la moyenne est exact ===")
stl, infol = J.analyse(lin, 10.0, 3.0, "lineaire", rng=random.Random(3))
print(f"   3x : écart={infol['ecart']:+.4f}")
check("f linéaire : écart ≈ 0 (plug-in exact)", abs(infol["ecart"]) < 0.05)

# ─── 4. Pour x², l'écart vaut EXACTEMENT σ² ───
print("=== Écart de x² = σ² ===")
for s in (1.0, 3.0, 6.0):
    _, _, g = J.gap_jensen(carre, 10.0, s, random.Random(int(s * 10)), n=400000)
    print(f"   σ={s} : écart={g:.2f} ; σ²={s*s:.2f}")
    check(f"écart(x²) ≈ σ² à σ={s}", abs(g - s * s) < 0.15 * s * s + 0.1)

# ─── 5. L'écart croît avec la variance ───
print("=== L'écart croît avec la variance ===")
_, _, g1 = J.gap_jensen(carre, 10.0, 1.0, random.Random(5))
_, _, g5 = J.gap_jensen(carre, 10.0, 5.0, random.Random(6))
check("l'écart de Jensen croît avec la variance de l'entrée", g5 > g1)

# ─── 6. Honnêteté : sans incertitude (σ=0), pas d'écart ───
print("=== Honnêteté : σ=0 → écart nul ===")
_, _, g0 = J.gap_jensen(carre, 10.0, 0.0, random.Random(7), n=1000)
check("sans incertitude, brancher la moyenne est exact", abs(g0) < 1e-9)
check("formule signale la sur-confiance du flaw of averages", "sur-confiant" in J.formule((st, info)))

# ─── 7. ABSTENTION ───
print("=== ABSTENTION ===")
check("rng manquant → ABSTENTION", J.analyse(carre, 10.0, 3.0, "convexe", rng=None)[0] == ABSTENTION)
check("sigma < 0 → ABSTENTION", J.analyse(carre, 10.0, -1.0, "convexe", rng=random.Random(0))[0] == ABSTENTION)
check("cas valide → ANALYSE", st == ANALYSE)

print(f"\nRÉSULTAT jensen : {ok}/{total}")
assert ok == total
