"""VALIDATION cas_limites.py (Vague 6). FAUX=0 : tests factuels ; non concluant -> False (pas d'optimisme)."""
from __future__ import annotations
import math
from cas_limites import limite_en, monotone, bornee, parite, homogene_degre

ok = 0; total = 0
def check(nom, cond):
    global ok, total; total += 1
    print(f"  [{'OK ' if cond else 'XXX'}] {nom}", flush=True)
    if cond: ok += 1
    else: raise AssertionError(nom)

# Énergie cinétique Ec(v) = ½ v² : nulle en 0, croissante pour v>0, paire, homogène degré 2.
Ec = lambda v: 0.5 * v * v
check("Ec(0)=0 (limite en 0)", limite_en(Ec, 0.0, 0.0))
check("Ec croissante pour v>=0", monotone(Ec, 0.0, 10.0, croissante=True))
check("Ec paire (Ec(-v)=Ec(v))", parite(Ec, paire=True))
check("Ec homogène de degré 2 (loi en v²)", homogene_degre(Ec, 2))
check("Ec N'EST PAS de degré 3 (test réfute honnêtement)", not homogene_degre(Ec, 3))

# Une probabilité logistique reste dans [0,1]
sig = lambda x: 1 / (1 + math.exp(-x))
check("sigmoïde bornée dans [0,1]", bornee(sig, -20, 20, bas=0.0, haut=1.0))
check("sigmoïde croissante", monotone(sig, -10, 10, croissante=True))
check("fonction impaire : x³", parite(lambda x: x ** 3, paire=False))

# FAUX=0 : non concluant -> False
check("valeur non finie (1/x en 0) -> limite False, pas d'optimisme", not limite_en(lambda x: 1 / x, 0.0, 0.0))
check("bornée False si dépasse la borne", not bornee(lambda x: x, 0, 10, haut=5))
check("monotone False si non monotone (x²) sur [-1,1]", not monotone(lambda x: x * x, -1, 1, croissante=True))
check("parité False si ni paire ni la relation demandée", not parite(lambda x: x + 1, paire=True))

print(f"\n=== valide_cas_limites : {ok}/{total} checks OK ===")
if ok != total: raise SystemExit(1)
