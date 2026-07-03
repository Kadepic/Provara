"""
VALIDATION de la LIMITE THÉORIQUE & ÉCART (limite.py) — Vague 3.
FAUX=0 : borne via loi sound ; marge correcte ; réel qui viole la borne -> impossible ; dimensions incompatibles -> HORS.
Exemple canonique : COP de Carnot (le fil de la discussion « refroidir en consommant moins »).
"""
from __future__ import annotations

import math

import dimensions as D
from grandeur import Grandeur
from loi import Loi
from limite import Limite

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


# ── Borne de Carnot : COP_max = T_froid / (T_chaud − T_froid), sans dimension (Θ/Θ) ──────
carnot = Loi("COP_Carnot",
             variables={"COP": D.SANS, "T_froid": D.TEMPERATURE, "T_chaud": D.TEMPERATURE},
             solveurs={"COP": lambda T_froid, T_chaud: T_froid / (T_chaud - T_froid) if T_chaud > T_froid else None})
lim = Limite("COP_Carnot", carnot, cible="COP", sens="max",
             description="le COP d'une pompe à chaleur ne peut dépasser celui de Carnot")

Tf = Grandeur.depuis(295, "K")     # ~22 °C intérieur
Tc = Grandeur.depuis(310, "K")     # ~37 °C extérieur
b = lim.borne(T_froid=Tf, T_chaud=Tc)
check("borne de Carnot = 295/15 ≈ 19.67 (sans dimension)",
      b is not None and b.dim == D.SANS and abs(b.valeur - 295 / 15) < 1e-9)

# COP d'un climatiseur réel ≈ 3.5 -> respecte la borne, grosse marge
reel = Grandeur(3.5, D.SANS)
r = lim.evalue(reel, T_froid=Tf, T_chaud=Tc)
check("un COP réel de 3.5 RESPECTE la borne de Carnot", r["respecte"] and not r["impossible"])
check("facteur de marge ≈ 19.67/3.5 ≈ 5.6× (il reste ×5,6 à gagner)", abs(r["facteur_marge"] - (295 / 15) / 3.5) < 1e-9)
check("marge() renvoie le facteur quand la borne est respectée", abs(lim.marge(reel, T_froid=Tf, T_chaud=Tc) - (295 / 15) / 3.5) < 1e-9)

# ── FAUX=0 : un réel qui VIOLE la borne physique -> impossible (jamais accepté comme marge) ──
impossible = Grandeur(25.0, D.SANS)                       # COP 25 > Carnot 19.67 = physiquement impossible
ri = lim.evalue(impossible, T_froid=Tf, T_chaud=Tc)
check("COP réel 25 > Carnot 19.67 -> impossible=True (incohérence détectée)", ri["impossible"] and not ri["respecte"])
check("marge() renvoie None sur un réel impossible (pas de marge fabriquée)",
      lim.marge(impossible, T_froid=Tf, T_chaud=Tc) is None)

# ── Borne 'min' : un plancher (ex. énergie minimale, réel ≥ borne) ───────────────────────
mini = Loi("plancher",
           variables={"E": D.ENERGIE, "n": D.SANS},
           solveurs={"E": lambda n: n * 1.0})              # borne = n joules (schématique)
limin = Limite("plancher_energie", mini, cible="E", sens="min")
reel_E = Grandeur.depuis(10, "J")
rm = limin.evalue(reel_E, n=Grandeur(4, D.SANS))           # borne 4 J, réel 10 J -> respecte, réductible ×2.5
check("borne 'min' : réel 10 J ≥ plancher 4 J respecté", rm["respecte"])
check("facteur de réduction possible = 10/4 = 2.5×", abs(rm["facteur_marge"] - 2.5) < 1e-9)
below = Grandeur.depuis(2, "J")                            # 2 J < plancher 4 J = impossible
check("réel 2 J < plancher 4 J -> impossible", limin.evalue(below, n=Grandeur(4, D.SANS))["impossible"])

# ── FAUX=0 : dimensions / paramètres incompatibles -> HORS ───────────────────────────────
check("réel de mauvaise dimension (énergie vs sans-dim) -> None",
      lim.evalue(Grandeur.depuis(5, "J"), T_froid=Tf, T_chaud=Tc) is None)
check("borne inapplicable (T_chaud ≤ T_froid) -> None",
      lim.borne(T_froid=Grandeur.depuis(310, "K"), T_chaud=Grandeur.depuis(295, "K")) is None)
check("paramètre de mauvaise dimension -> None (via la loi)",
      lim.borne(T_froid=Grandeur.depuis(295, "J"), T_chaud=Tc) is None)

print(f"\n=== valide_limite : {ok}/{total} checks OK ===")
if ok != total:
    raise SystemExit(1)
