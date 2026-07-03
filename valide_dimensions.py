"""
VALIDATION de l'ALGÈBRE DIMENSIONNELLE (dimensions.py) — brique fondatrice Vague 1.

Trois exigences, toutes FAUX=0 :
  • ALGÈBRE EXACTE : les dérivées se construisent correctement (force = M·L·T⁻², etc.), exposants fractionnaires OK.
  • HOMOGÉNÉITÉ = LE FILTRE : une équation homogène passe, une non-homogène (force = masse × vitesse) est REJETÉE.
  • CONVERSION SOUND : exacte quand définie (1 km = 1000 m, 0 °C = 273.15 K), et None (HORS) si incommensurable.
Léger (aucun lecteur). EXIT 0 = tout passe.
"""
from __future__ import annotations

from fractions import Fraction

import dimensions as D

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


# ── 1. Algèbre exacte des dimensions ────────────────────────────────────────────────────
check("force = masse·accélération = M·L·T⁻²",
      D.FORCE == D.MASSE * D.LONGUEUR / D.TEMPS ** 2 and D.FORCE.formule() == "M·L·T⁻²")
check("énergie = force·longueur = M·L²·T⁻²", D.ENERGIE == D.FORCE * D.LONGUEUR)
check("puissance = énergie/temps = M·L²·T⁻³", D.PUISSANCE == D.ENERGIE / D.TEMPS)
check("pression = force/aire = M·L⁻¹·T⁻²", D.PRESSION == D.FORCE / D.AIRE)
check("(vitesse)² a la dimension L²·T⁻²", (D.VITESSE ** 2) == (D.LONGUEUR ** 2) / (D.TEMPS ** 2))
check("énergie/masse = (vitesse)²  [cohérence E=mc²]", D.ENERGIE / D.MASSE == D.VITESSE ** 2)
check("sans dimension : force/force = 1", (D.FORCE / D.FORCE).sans_dimension())
check("exposant fractionnaire exact : (L²)^(1/2) = L",
      (D.LONGUEUR ** 2) ** Fraction(1, 2) == D.LONGUEUR)
check("hachable (utilisable comme clé)", len({D.FORCE, D.ENERGIE, D.FORCE}) == 2)

# ── 2. Homogénéité = le filtre anti-absurdité ───────────────────────────────────────────
check("F = m·a est homogène (loi valide)",
      D.verifie_egalite(D.FORCE, D.MASSE * D.ACCELERATION))
check("REJET : « force = masse × vitesse » NON homogène",
      not D.verifie_egalite(D.FORCE, D.MASSE * D.VITESSE))
check("E_c = ½·m·v² homogène à une énergie",
      D.verifie_egalite(D.ENERGIE, D.MASSE * D.VITESSE ** 2))
check("REJET : additionner une longueur et un temps -> HORS (None)",
      D.verifie_somme(D.LONGUEUR, D.TEMPS) is None)
check("addition homogène (longueur+longueur) -> longueur",
      D.verifie_somme(D.LONGUEUR, D.LONGUEUR) == D.LONGUEUR)
check("homogene() : vrai si toutes égales, faux sinon",
      D.homogene(D.ENERGIE, D.ENERGIE) and not D.homogene(D.ENERGIE, D.PUISSANCE))

# ── 3. Conversion : exacte, et HORS si incommensurable ──────────────────────────────────
check("1 km = 1000 m EXACT", D.convertit(1, "km", "m") == 1000)
check("1 pouce = 0.0254 m EXACT (Fraction)", D.convertit(1, "pouce", "m") == Fraction(254, 10000))
check("1 h = 3600 s EXACT", D.convertit(1, "h", "s") == 3600)
check("1 kWh = 3.6e6 J EXACT", D.convertit(1, "kWh", "J") == 3600000)
check("72 km/h = 20 m/s EXACT", D.convertit(72, "km/h", "m/s") == 20)
check("0 °C = 273.15 K EXACT (affine)", D.convertit(0, "°C", "K") == Fraction(27315, 100))
check("100 °C = 373.15 K EXACT", D.convertit(100, "°C", "K") == Fraction(37315, 100))
check("32 °F = 273.15 K EXACT (0 °C)", D.convertit(32, "°F", "K") == Fraction(27315, 100))
check("212 °F = 373.15 K EXACT (100 °C)", D.convertit(212, "°F", "K") == Fraction(37315, 100))
check("aller-retour m->km->m identité", D.convertit(D.convertit(1234, "m", "km"), "km", "m") == 1234)
check("REJET : convertir mètre -> seconde = HORS (None)", D.convertit(1, "m", "s") is None)
check("REJET : convertir joule -> newton = HORS (None)", D.convertit(1, "J", "N") is None)
check("REJET : unité inconnue -> HORS (None)", D.convertit(1, "m", "parsec") is None)
check("commensurables(km, mile) et non(km, kg)",
      D.commensurables("km", "mile") and not D.commensurables("km", "kg"))
check("dimension_de('N') == FORCE ; inconnue -> None",
      D.dimension_de("N") == D.FORCE and D.dimension_de("xyz") is None)

print(f"\n=== valide_dimensions : {ok}/{total} checks OK ===")
if ok != total:
    raise SystemExit(1)
