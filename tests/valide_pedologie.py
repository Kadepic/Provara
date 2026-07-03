"""
VALIDE pedologie.py — held-out ADVERSE.

Ancres CONNUES (faits/définitions de pédologie + arithmétique vérifiée à la main) :
  • Triangle USDA simplifié : argile>40 -> 'argileux' ; sable>70 -> 'sableux' ; sinon 'limoneux'.
      - 80 % sable (10 limon, 10 argile, somme 100) -> 'sableux'.
      - 50 % argile (30 sable, 20 limon, somme 100) -> 'argileux'.
      - 33/34/33 (somme 100, aucune fraction dominante) -> 'limoneux'.
  • Porosité = 1 − da/dr. da=1.3, dr=2.65 :
      1.3/2.65 = 0.490566037735…  ->  1 − 0.490566… = 0.509433962264…  ->  arrondi 0.509434.
SOUNDNESS : fractions ne sommant pas à 100, fraction hors [0,100], densités<=0,
            da>dr, valeurs non finies/non numériques -> ValueError.
DÉTERMINISME : mêmes entrées -> mêmes sorties.
"""

import pedologie as P

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def approx(a, b, tol=1e-9):
    return abs(a - b) <= tol


def _leve_v(fn, *a, **k):
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) ANCRE — classe sableuse (sable > 70) ──
check(P.classe_texture(80, 10, 10) == "sableux", "80 % sable -> sableux (cas spéc)")
check(P.classe_texture(71, 29, 0) == "sableux", "71 % sable (borne >70) -> sableux")
check(P.classe_texture(90, 5, 5) == "sableux", "90 % sable -> sableux")
check(P.classe_texture(75, 10, 15) == "sableux", "75 % sable, 15 argile -> sableux")

# ── 2) ANCRE — classe argileuse (argile > 40) ──
check(P.classe_texture(30, 20, 50) == "argileux", "50 % argile -> argileux (cas spéc)")
check(P.classe_texture(10, 49, 41) == "argileux", "41 % argile (borne >40) -> argileux")
check(P.classe_texture(0, 30, 70) == "argileux", "70 % argile -> argileux")
# Priorité argile sur sable impossible en pratique (somme>100), mais argile prime à somme=100 :
check(P.classe_texture(45, 0, 55) == "argileux",
      "45 sable / 55 argile : argile>40 prime (et 45 sable <70 de toute façon) -> argileux")

# ── 3) ANCRE — classe limoneuse (ni argile>40 ni sable>70) ──
check(P.classe_texture(33, 34, 33) == "limoneux", "33/34/33 -> limoneux")
check(P.classe_texture(40, 40, 20) == "limoneux", "40 sable / 40 limon / 20 argile -> limoneux")
check(P.classe_texture(70, 10, 20) == "limoneux", "70 % sable (=70, NON >70) -> limoneux")
check(P.classe_texture(30, 30, 40) == "limoneux", "40 % argile (=40, NON >40) -> limoneux")
check(P.classe_texture(0, 100, 0) == "limoneux", "100 % limon -> limoneux")

# ── 4) ANCRE — bornes strictes (argile=40, sable=70 NON inclus) ──
check(P.classe_texture(70, 30, 0) == "limoneux", "sable=70 exact -> limoneux (strict)")
check(P.classe_texture(60, 0, 40) == "limoneux", "argile=40 exact -> limoneux (strict)")
check(P.classe_texture(69.999, 30, 0.001) == "limoneux", "sable=69.999 -> limoneux")
check(P.classe_texture(70.001, 29.999, 0) == "sableux", "sable=70.001 -> sableux")
check(P.classe_texture(0, 59.999, 40.001) == "argileux", "argile=40.001 -> argileux")

# ── 5) ANCRE — tolérance de somme (float ~100) ──
check(P.classe_texture(33.33, 33.34, 33.33) == "limoneux", "33.33+33.34+33.33=100 -> limoneux")
check(P.classe_texture(80, 9.9999995, 10.0000005) == "sableux", "somme à 1e-6 près acceptée")

# ── 6) ANCRE — porosité (1 − da/dr) ──
po = P.porosite(1.3)
check(approx(po, 0.509434, 1e-9), f"porosité da=1.3 -> 0.509434 (obtenu {po})")
check(approx(po, 1.0 - 1.3 / 2.65, 1e-6), "porosité ≈ 1 − 1.3/2.65 (formule)")
check(0.50 < po < 0.52, "porosité da=1.3 dans ]0.50, 0.52[")
check(approx(P.porosite(1.3, 2.65), po), "dr=2.65 explicite identique au défaut")
check(approx(P.porosite(1.325), 0.5), "da=1.325 (=dr/2) -> porosité 0.5")
check(approx(P.porosite(2.65, 2.65), 0.0), "da=dr -> porosité 0 (no pores), accepté")
check(approx(P.porosite(1.0, 2.0), 0.5), "da=1.0, dr=2.0 -> 0.5")
check(approx(P.porosite(0.265), 0.9), "da=0.265, dr=2.65 -> 0.9")
# Monotonie : porosité décroît quand da croît (dr fixe).
check(P.porosite(1.0) > P.porosite(1.5) > P.porosite(2.0), "porosité décroît avec da")

# ── 7) SOUNDNESS — abstention (ValueError), faux positif INTERDIT ──
# somme ≠ 100
check(_leve_v(P.classe_texture, 80, 10, 5), "somme = 95 ≠ 100 -> ValueError")
check(_leve_v(P.classe_texture, 50, 30, 30), "somme = 110 ≠ 100 -> ValueError")
check(_leve_v(P.classe_texture, 33.3, 33.3, 33.3), "somme = 99.9 (hors tol) -> ValueError")
check(_leve_v(P.classe_texture, 0, 0, 0), "somme = 0 -> ValueError")
# fraction hors [0, 100] / non finie / non numérique
check(_leve_v(P.classe_texture, -10, 60, 50), "sable négatif -> ValueError")
check(_leve_v(P.classe_texture, 110, -5, -5), "sable > 100 -> ValueError")
check(_leve_v(P.classe_texture, float("nan"), 50, 50), "fraction NaN -> ValueError")
check(_leve_v(P.classe_texture, float("inf"), 0, 0), "fraction non finie -> ValueError")
check(_leve_v(P.classe_texture, "sableux", 10, 10), "fraction non numérique -> ValueError")
check(_leve_v(P.classe_texture, None, 10, 10), "fraction None -> ValueError")
check(_leve_v(P.classe_texture, 80, 10, 10, -1.0), "tol négatif -> ValueError")
# densités
check(_leve_v(P.porosite, 1.3, 0), "densite_reelle = 0 -> ValueError")
check(_leve_v(P.porosite, 1.3, -2.65), "densite_reelle < 0 -> ValueError")
check(_leve_v(P.porosite, 0), "densite_apparente = 0 -> ValueError")
check(_leve_v(P.porosite, -1.3), "densite_apparente < 0 -> ValueError")
check(_leve_v(P.porosite, 3.0, 2.65), "da > dr (porosité négative) -> ValueError")
check(_leve_v(P.porosite, float("inf")), "densite_apparente non finie -> ValueError")
check(_leve_v(P.porosite, float("nan"), 2.65), "densite_apparente NaN -> ValueError")
check(_leve_v(P.porosite, 1.3, float("nan")), "densite_reelle NaN -> ValueError")
check(_leve_v(P.porosite, "léger"), "densite_apparente non numérique -> ValueError")
check(_leve_v(P.porosite, None), "densite_apparente None -> ValueError")

# ── 8) DÉTERMINISME ──
check(P.classe_texture(80, 10, 10) == P.classe_texture(80, 10, 10), "classe_texture déterministe")
check(P.porosite(1.3) == P.porosite(1.3), "porosite déterministe")
check(P.classe_texture(30, 20, 50) == P.classe_texture(30, 20, 50),
      "classe_texture déterministe (argileux)")

print(f"\n=== valide_pedologie : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
