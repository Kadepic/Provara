"""
VALIDE pib.py — held-out ADVERSE.

Ancres CONNUES non circulaires : valeurs définitionnelles calculées À LA MAIN (pas re-dérivées par l'expression
du module dans le test), p.ex. la croissance 100→103 = 3 % (énoncé), un déflateur en année de base (100) rend
le PIB réel = nominal, X−M négatif diminue le PIB. + SOUNDNESS (population/déflateur ≤ 0, base nulle/négative,
NaN/inf, type non numérique, bool -> ValueError) + DÉTERMINISME (deux appels identiques).
"""
import math

import pib as M

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def approx(val, attendu, tol=1e-9):
    return isinstance(val, float) and abs(val - attendu) <= tol * (1 + abs(attendu))


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) PIB par les dépenses : C + I + G + (X − M) ──
check(approx(M.pib_depenses(60, 20, 25, 15, 12), 108.0), "PIB = 60+20+25+(15-12) = 108")
check(approx(M.pib_depenses(11000, 3500, 3800, 2500, 3100), 17700.0), "PIB = 11000+3500+3800-600 = 17700")
check(approx(M.pib_depenses(100, 50, 30, 10, 40), 150.0), "X−M<0 : 100+50+30+(10-40) = 150")
check(approx(M.pib_depenses(0, 0, 0, 0, 0), 0.0), "PIB nul = 0")
check(approx(M.pib_depenses(200, -10, 30, 5, 5), 220.0), "I<0 (déstockage) : 200-10+30+0 = 220")

# ── 2) Taux de croissance : (final − initial)/initial · 100 ──
check(approx(M.taux_croissance(100, 103), 3.0), "100→103 = 3 % (énoncé)")
check(approx(M.taux_croissance(200, 210), 5.0), "200→210 = 5 %")
check(approx(M.taux_croissance(100, 95), -5.0), "100→95 = −5 % (récession)")
check(approx(M.taux_croissance(50, 50), 0.0), "stagnation = 0 %")
check(approx(M.taux_croissance(2, 3), 50.0), "2→3 = 50 %")
check(approx(M.taux_croissance(80, 100), 25.0), "80→100 = 25 %")

# ── 3) PIB par habitant : PIB / population ──
check(approx(M.pib_par_habitant(1000000, 200), 5000.0), "1 000 000 / 200 = 5000")
check(approx(M.pib_par_habitant(21000000, 1000), 21000.0), "21 000 000 / 1000 = 21000")
check(approx(M.pib_par_habitant(7.5, 3), 2.5), "7.5 / 3 = 2.5")

# ── 4) PIB réel : nominal · 100 / déflateur ──
check(approx(M.pib_reel(120, 100), 120.0), "déflateur=100 (base) -> réel = nominal = 120")
check(approx(M.pib_reel(110, 110), 100.0), "nominal 110 / déflateur 110 -> réel = 100")
check(approx(M.pib_reel(220, 110), 200.0), "220·100/110 = 200")
check(approx(M.pib_reel(90, 120), 75.0), "90·100/120 = 75 (inflation -> réel < nominal)")

# ── 5) DÉTERMINISME ──
check(M.pib_depenses(60, 20, 25, 15, 12) == M.pib_depenses(60, 20, 25, 15, 12), "déterministe pib_depenses")
check(M.taux_croissance(100, 103) == M.taux_croissance(100, 103), "déterministe taux_croissance")
check(M.pib_reel(220, 110) == M.pib_reel(220, 110), "déterministe pib_reel")

# ── 6) SOUNDNESS — domaines invalides -> ValueError (abstention, jamais un faux) ──
check(leve(M.pib_par_habitant, 1000, 0), "population = 0 -> ValueError")
check(leve(M.pib_par_habitant, 1000, -5), "population < 0 -> ValueError")
check(leve(M.pib_reel, 1000, 0), "déflateur = 0 -> ValueError")
check(leve(M.pib_reel, 1000, -10), "déflateur < 0 -> ValueError")
check(leve(M.taux_croissance, 0, 50), "base de croissance = 0 -> ValueError")
check(leve(M.taux_croissance, -100, 50), "base de croissance < 0 -> ValueError")

# ── 7) SOUNDNESS — entrées non numériques / non finies -> ValueError ──
check(leve(M.pib_depenses, float("nan"), 0, 0, 0, 0), "NaN -> ValueError")
check(leve(M.pib_depenses, float("inf"), 0, 0, 0, 0), "inf -> ValueError")
check(leve(M.pib_depenses, "60", 0, 0, 0, 0), "chaîne -> ValueError")
check(leve(M.pib_par_habitant, 1000, True), "bool population (True) -> ValueError")
check(leve(M.pib_reel, None, 100), "None nominal -> ValueError")
check(leve(M.taux_croissance, 100, float("nan")), "final NaN -> ValueError")

print(f"\n=== valide_pib : {ok}/{ok+ko} ===")
import sys; sys.exit(0 if ko == 0 else 1)
