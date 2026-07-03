"""
VALIDE hydrologie.py — held-out ADVERSE.

Ancres = cas CONNUS de l'hydraulique des eaux continentales, calculés INDÉPENDAMMENT (arithmétique brute
math.sqrt/** ou valeurs entières évidentes), JAMAIS re-dérivés en appelant la fonction du module testé :
  • continuité Q = A·v (entiers exacts : 2 m²·3 m/s = 6 m³/s) ;
  • méthode rationnelle Q = (1/360)·C·i·A (cas étalon C=1,i=360 mm/h,A=1 ha = 1 m³/s exact, démontre le 1/360) ;
  • Manning v = (1/n)·R^(2/3)·√S (cas étalon n=0,01,R=1,S=1e-4 = 1 m/s exact, + cas béton n=0,013) ;
  • Kirpich t_c = 0,0195·L^0,77·S^(−0,385).
+ SOUNDNESS (section ≤ 0, C hors [0,1], n ≤ 0, R ≤ 0, longueur/pente invalides, booléen, str, NaN -> ValueError)
+ DÉTERMINISME (mêmes entrées -> mêmes sorties).
"""
import math

import hydrologie as M

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def _leve_v(fn, *a, **k) -> bool:
    """True ssi fn(*a, **k) lève ValueError (abstention), False sinon."""
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


def _sig(x, n=6):
    """Réplique l'arrondi à n chiffres significatifs du module, pour comparer en non-circulaire."""
    if x == 0:
        return 0.0
    return float(f"{x:.{n}g}")


TOL = 1e-9   # comparaison après arrondi 6 sig identique des deux côtés

# ── 1) CONTINUITÉ Q = A·v (ancres entières exactes, vérifiables à la main) ──
check(M.debit(2, 3) == 6.0, "continuité : 2 m²·3 m/s = 6 m³/s")
check(M.debit(10, 0.5) == 5.0, "continuité : 10·0,5 = 5 m³/s")
check(M.debit(0.5, 1.2) == _sig(0.5 * 1.2), "continuité : 0,5·1,2 = 0,6 m³/s")
check(M.debit(3, 0) == 0.0, "continuité : v=0 -> Q=0 (pas de flux, valide)")
check(abs(M.debit(4.2, 1.75) - _sig(4.2 * 1.75)) < TOL, "continuité : 4,2·1,75 = 7,35 m³/s")

# ── 2) MÉTHODE RATIONNELLE Q = (1/360)·C·i·A ──
check(abs(M.methode_rationnelle(1.0, 360.0, 1.0) - 1.0) < TOL,
      "rationnelle étalon : C=1,i=360,A=1 -> (1/360)·360 = 1 m³/s exact")
check(abs(M.methode_rationnelle(0.5, 50.0, 10.0) - _sig((1 / 360) * 0.5 * 50 * 10)) < TOL,
      "rationnelle : C=0,5,i=50,A=10 -> 0,694444 m³/s")
check(abs(M.methode_rationnelle(0.8, 120.0, 25.0) - _sig((1 / 360) * 0.8 * 120 * 25)) < TOL,
      "rationnelle : C=0,8,i=120,A=25 -> 6,66667 m³/s")
check(M.methode_rationnelle(0, 100, 5) == 0.0, "rationnelle : C=0 -> Q=0 (sol totalement perméable)")
check(M.ruissellement(0.5, 50.0, 10.0) == M.methode_rationnelle(0.5, 50.0, 10.0),
      "alias ruissellement == methode_rationnelle")
# bornes admissibles de C
check(abs(M.methode_rationnelle(1.0, 100.0, 2.0) - _sig((1 / 360) * 1.0 * 100 * 2)) < TOL, "rationnelle : C=1 admis")

# ── 3) MANNING v = (1/n)·R^(2/3)·√S ──
check(abs(M.manning_vitesse(0.01, 1.0, 1e-4) - 1.0) < TOL,
      "Manning étalon : n=0,01,R=1,S=1e-4 -> (1/0,01)·1·0,01 = 1 m/s exact")
check(abs(M.manning_vitesse(0.013, 1.0, 0.001) - _sig((1 / 0.013) * 1.0 ** (2 / 3) * math.sqrt(0.001))) < TOL,
      "Manning béton : n=0,013,R=1,S=0,001 -> 2,43252 m/s")
check(abs(M.manning_vitesse(0.015, 0.5, 0.0004) - _sig((1 / 0.015) * 0.5 ** (2 / 3) * math.sqrt(0.0004))) < TOL,
      "Manning : n=0,015,R=0,5,S=4e-4 -> 0,839947 m/s")
check(M.manning_vitesse(0.02, 2.0, 0) == 0.0, "Manning : pente=0 -> v=0 (chenal horizontal, dégénéré mais défini)")
check(abs(M.manning_vitesse(0.03, 4.0, 0.0025) - _sig((1 / 0.03) * 4.0 ** (2 / 3) * math.sqrt(0.0025))) < TOL,
      "Manning : n=0,03,R=4,S=2,5e-3")

# ── 4) KIRPICH t_c = 0,0195·L^0,77·S^(−0,385) ──
check(abs(M.temps_concentration(300.0, 0.01) - _sig(0.0195 * 300.0 ** 0.77 * 0.01 ** (-0.385))) < TOL,
      "Kirpich : L=300 m,S=0,01 -> 9,27722 min")
check(abs(M.temps_concentration(1000.0, 0.005) - _sig(0.0195 * 1000.0 ** 0.77 * 0.005 ** (-0.385))) < TOL,
      "Kirpich : L=1000 m,S=0,005")
check(abs(M.temps_concentration(50.0, 0.02) - _sig(0.0195 * 50.0 ** 0.77 * 0.02 ** (-0.385))) < TOL,
      "Kirpich : L=50 m,S=0,02")

# ── 5) SOUNDNESS — entrée invalide -> ValueError (abstention, jamais un faux) ──
check(_leve_v(M.debit, 0, 3), "débit : section=0 -> ValueError")
check(_leve_v(M.debit, -2, 3), "débit : section<0 -> ValueError")
check(_leve_v(M.debit, 2, -1), "débit : vitesse<0 -> ValueError")
check(_leve_v(M.debit, True, 3), "débit : section booléen -> ValueError")
check(_leve_v(M.debit, "2", 3), "débit : section str -> ValueError")
check(_leve_v(M.debit, float("nan"), 3), "débit : section NaN -> ValueError")
check(_leve_v(M.debit, float("inf"), 3), "débit : section inf -> ValueError")
check(_leve_v(M.methode_rationnelle, -0.1, 50, 10), "rationnelle : C<0 -> ValueError")
check(_leve_v(M.methode_rationnelle, 1.0001, 50, 10), "rationnelle : C>1 -> ValueError")
check(_leve_v(M.methode_rationnelle, 0.5, -50, 10), "rationnelle : i<0 -> ValueError")
check(_leve_v(M.methode_rationnelle, 0.5, 50, 0), "rationnelle : A=0 -> ValueError")
check(_leve_v(M.methode_rationnelle, 0.5, 50, -10), "rationnelle : A<0 -> ValueError")
check(_leve_v(M.methode_rationnelle, True, 50, 10), "rationnelle : C booléen -> ValueError")
check(_leve_v(M.ruissellement, 2.0, 50, 10), "alias ruissellement propage C>1 -> ValueError")
check(_leve_v(M.manning_vitesse, 0, 1, 0.001), "Manning : n=0 -> ValueError")
check(_leve_v(M.manning_vitesse, -0.013, 1, 0.001), "Manning : n<0 -> ValueError")
check(_leve_v(M.manning_vitesse, 0.013, 0, 0.001), "Manning : R=0 -> ValueError")
check(_leve_v(M.manning_vitesse, 0.013, -1, 0.001), "Manning : R<0 -> ValueError")
check(_leve_v(M.manning_vitesse, 0.013, 1, -0.001), "Manning : pente<0 -> ValueError")
check(_leve_v(M.manning_vitesse, True, 1, 0.001), "Manning : n booléen -> ValueError")
check(_leve_v(M.temps_concentration, 0, 0.01), "Kirpich : L=0 -> ValueError")
check(_leve_v(M.temps_concentration, -300, 0.01), "Kirpich : L<0 -> ValueError")
check(_leve_v(M.temps_concentration, 300, 0), "Kirpich : pente=0 -> ValueError")
check(_leve_v(M.temps_concentration, 300, -0.01), "Kirpich : pente<0 -> ValueError")

# ── 6) DÉTERMINISME — fonctions pures, mêmes entrées -> mêmes sorties ──
check(M.debit(2, 3) == M.debit(2, 3), "débit déterministe")
check([M.manning_vitesse(0.013, 1.0, 0.001) for _ in range(5)].count(M.manning_vitesse(0.013, 1.0, 0.001)) == 5,
      "Manning : 5 appels identiques")
check(M.temps_concentration(300.0, 0.01) == M.temps_concentration(300.0, 0.01), "Kirpich déterministe")
check(M.methode_rationnelle(0.5, 50, 10) == M.methode_rationnelle(0.5, 50, 10), "rationnelle déterministe")

print(f"\n=== valide_hydrologie : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
