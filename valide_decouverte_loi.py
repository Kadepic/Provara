"""VALIDATION decouverte_loi.py (Vague 4). FAUX=0 : loi retournée colle à TOUS les points (dont held-out) ; sinon None."""
from __future__ import annotations
from decouverte_loi import decouvre

ok = 0; total = 0
def check(nom, cond):
    global ok, total; total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}", flush=True)
    if cond: ok += 1
    else: raise AssertionError(nom)

# y = 2x  (proportionnel)
r = decouvre([(1, 2), (2, 4), (3, 6), (5, 10)])
check("découvre proportionnel y=2x", r is not None and r["forme"] == "proportionnel" and abs(r["params"]["a"] - 2) < 1e-9)
check("la loi prédit correctement un point neuf (x=10 -> 20)", abs(r["predit"](10) - 20) < 1e-9)

# y = 3x²  (carré) -- Galilée : distance ∝ temps²
r2 = decouvre([(1, 3), (2, 12), (3, 27), (4, 48)])
check("découvre carré y=3x²", r2 is not None and r2["forme"] == "carré" and abs(r2["params"]["a"] - 3) < 1e-9)

# y = a/x  (inverse) -- Boyle : P·V = cste
r3 = decouvre([(1, 12), (2, 6), (3, 4), (4, 3)])
check("découvre inverse y=12/x (loi de Boyle)", r3 is not None and r3["forme"] == "inverse" and abs(r3["params"]["a"] - 12) < 1e-9)

# y = 2x + 1  (linéaire)
r4 = decouvre([(0, 1), (1, 3), (2, 5), (10, 21)])
check("découvre linéaire y=2x+1", r4 is not None and r4["forme"] == "linéaire"
      and abs(r4["params"]["a"] - 2) < 1e-9 and abs(r4["params"]["b"] - 1) < 1e-9)

# constante
check("découvre constante y=7", decouvre([(1, 7), (5, 7), (9, 7)])["forme"] == "constante")

# FAUX=0 : données sans loi simple -> None (abstention, jamais une loi plaquée)
check("données bruitées/sans loi simple -> None", decouvre([(1, 2), (2, 4.5), (3, 5), (4, 100)]) is None)
check("un seul point -> None (indéterminable)", decouvre([(1, 2)]) is None)

# FAUX=0 : held-out — 2 points collent en linéaire mais le 3e réfute -> pas de loi linéaire trompeuse
check("3e point réfute la droite ajustée sur 2 -> None", decouvre([(0, 0), (1, 1), (2, 5)]) is None)

print(f"\n=== valide_decouverte_loi : {ok}/{total} checks OK ===")
if ok != total: raise SystemExit(1)
