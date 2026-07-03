"""
VALIDATION de la GRANDEUR TYPÉE (grandeur.py) — Vague 1. Dépend de dimensions.py.

FAUX=0 :
  • Arithmétique dimensionnellement correcte (5 N × 2 m = 10 J ; distance/temps = vitesse).
  • Addition/comparaison HÉTÉROGÈNE -> IncoherenceDimensionnelle (jamais un nombre faux).
  • Conversions cohérentes avec dimensions.py ; incommensurable -> None.
  • Propagation d'incertitude 1er ordre saine (somme quadratique / relative).
"""
from __future__ import annotations

import math

import dimensions as D
from grandeur import Grandeur, IncoherenceDimensionnelle, homogene

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


def leve(fn):
    try:
        fn()
        return False
    except IncoherenceDimensionnelle:
        return True


# ── Construction & conversion ───────────────────────────────────────────────────────────
d = Grandeur.depuis(5, "km")
check("5 km stocké en SI = 5000 m", d.valeur == 5000 and d.dim == D.LONGUEUR)
check("5 km relu en km = 5", d.en("km") == 5)
check("5 km relu en m = 5000", d.en("m") == 5000)
check("conversion incommensurable (longueur en s) -> None", d.en("s") is None)
t = Grandeur.depuis(0, "°C")
check("0 °C stocké = 273.15 K", abs(t.valeur - 273.15) < 1e-9 and t.dim == D.TEMPERATURE)

# ── Arithmétique dimensionnellement correcte ─────────────────────────────────────────────
F = Grandeur.depuis(5, "N")
L = Grandeur.depuis(2, "m")
E = F * L
check("5 N × 2 m = 10 J (dimension énergie)", E.dim == D.ENERGIE and abs(E.en("J") - 10) < 1e-9)
dist = Grandeur.depuis(100, "m")
temps = Grandeur.depuis(10, "s")
v = dist / temps
check("100 m / 10 s = 10 m/s (dimension vitesse)", v.dim == D.VITESSE and abs(v.en("m/s") - 10) < 1e-9)
m = Grandeur.depuis(2, "kg")
vit = Grandeur.depuis(3, "m/s")
Ec = Grandeur(0.5, D.SANS) * m * vit ** 2
check("½·m·v² a la dimension d'une énergie", Ec.dim == D.ENERGIE and abs(Ec.en("J") - 9) < 1e-9)
check("aire = m × m = m² (L²)", (L * L).dim == D.AIRE)
check("scalaire × grandeur conserve la dimension", (3 * F).dim == D.FORCE and (3 * F).en("N") == 15)

# ── Le filtre FAUX=0 : opérations hétérogènes REFUSÉES ───────────────────────────────────
check("REJET : additionner une longueur et un temps lève IncoherenceDimensionnelle",
      leve(lambda: Grandeur.depuis(1, "m") + Grandeur.depuis(1, "s")))
check("REJET : comparer une énergie et une force lève",
      leve(lambda: Grandeur.depuis(1, "J").compare(Grandeur.depuis(1, "N"))))
check("addition homogène autorisée (2 m + 3 m = 5 m)",
      (Grandeur.depuis(2, "m") + Grandeur.depuis(3, "m")).en("m") == 5)
check("comparaison homogène : 2 km > 500 m",
      Grandeur.depuis(2, "km").compare(Grandeur.depuis(500, "m")) == 1)
check("homogene() vrai/faux",
      homogene(Grandeur.depuis(1, "m"), Grandeur.depuis(1, "km"))
      and not homogene(Grandeur.depuis(1, "m"), Grandeur.depuis(1, "s")))

# ── Propagation d'incertitude 1er ordre ──────────────────────────────────────────────────
a = Grandeur.depuis(10, "m", u=0.3)
b = Grandeur.depuis(20, "m", u=0.4)
s = a + b
check("somme : u = √(0.3²+0.4²) = 0.5", abs(s.u - 0.5) < 1e-9)
p = Grandeur.depuis(4, "m", u=0.4) * Grandeur.depuis(5, "m", u=1.0)   # u_rel 10% et 20%
# u_rel_result = √(0.1²+0.2²) ≈ 0.2236 -> u ≈ 0.2236*20 = 4.472
check("produit : u relative combinée (√(0.1²+0.2²))", abs(p.u - 20 * math.hypot(0.1, 0.2)) < 1e-9)
check("valeur exacte (u=0) reste exacte après ×scalaire", (Grandeur.depuis(3, "m") * 2).u == 0)
check("incertitude convertie d'unité (0.3 m -> mm = 300)",
      abs(Grandeur.depuis(10, "m", u=0.3).incertitude_en("mm") - 300) < 1e-9)

# ── Rendu ────────────────────────────────────────────────────────────────────────────────
check("formule lisible dans une unité", Grandeur.depuis(72, "km/h").formule("m/s") == "20 m/s")
check("formule dans unité incommensurable -> None", Grandeur.depuis(1, "m").formule("s") is None)

print(f"\n=== valide_grandeur : {ok}/{total} checks OK ===")
if ok != total:
    raise SystemExit(1)
