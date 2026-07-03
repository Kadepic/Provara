"""
VALIDATION du BILAN DE CONSERVATION (conservation.py) — Vague 3.
FAUX=0 : bilan équilibré -> conserve ; sortie>entrée -> violation détectée (mouvement perpétuel refusé) ;
dimensions hétérogènes -> HORS.
"""
from __future__ import annotations

import dimensions as D
from grandeur import Grandeur
from conservation import bilan, viole_conservation, rendement

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


J = lambda x: Grandeur.depuis(x, "J")

# ── Bilan équilibré : 100 J entrent, 60 J sortent utiles + 40 J pertes ───────────────────
b = bilan(entrees=[J(100)], sorties=[J(60), J(40)])
check("bilan équilibré (100 = 60 + 40) -> conserve", b["conserve"])
check("déséquilibre nul", abs(b["desequilibre"].en("J")) < 1e-9)
check("pas de violation détectée sur un bilan équilibré", not viole_conservation([J(100)], [J(60), J(40)]))

# ── Avec accumulation : 100 entrent, 70 sortent, 30 stockés ──────────────────────────────
b2 = bilan(entrees=[J(100)], sorties=[J(70)], accumulation=J(30))
check("bilan avec accumulation (100 = 70 + 30 stockés) -> conserve", b2["conserve"])

# ── FAUX=0 : mouvement perpétuel — sortie > entrée ───────────────────────────────────────
b3 = bilan(entrees=[J(100)], sorties=[J(150)])
check("sortie 150 J > entrée 100 J -> NON conservé", not b3["conserve"])
check("déséquilibre négatif (50 J créés du néant)", b3["desequilibre"].en("J") < 0)
check("viole_conservation = True (machine à mouvement perpétuel rejetée)",
      viole_conservation([J(100)], [J(150)]))
check("un déficit d'entrée (entrée>sortie) n'est PAS une violation (pertes possibles)",
      not viole_conservation([J(150)], [J(100)]))

# ── FAUX=0 : dimensions hétérogènes -> HORS ──────────────────────────────────────────────
check("mélanger énergie et masse dans un bilan -> None (HORS)",
      bilan(entrees=[J(100)], sorties=[Grandeur.depuis(1, "kg")]) is None)
check("bilan vide -> None (HORS)", bilan(entrees=[], sorties=[]) is None)

# ── Rendement ────────────────────────────────────────────────────────────────────────────
check("rendement utile/fourni = 0.6", abs(rendement(J(60), J(100)) - 0.6) < 1e-9)
check("rendement dimensions différentes -> None", rendement(J(60), Grandeur.depuis(1, "kg")) is None)
check("rendement fourni nul -> None", rendement(J(60), J(0)) is None)
check("rendement > 1 calculé (à confronter à un bilan) : 120/100 = 1.2", abs(rendement(J(120), J(100)) - 1.2) < 1e-9)

print(f"\n=== valide_conservation : {ok}/{total} checks OK ===")
if ok != total:
    raise SystemExit(1)
