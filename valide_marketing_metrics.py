"""
VALIDE marketing_metrics.py — held-out ADVERSE.

Ancres CONNUES (définitions standard + arithmétique vérifiée à la main, non circulaires) :
  • taux_conversion : 50/1000 = 0.05 (5 %) ; 1/4 = 0.25 ; 0/100 = 0.0 ; 250/250 = 1.0 (borne)
  • ctr            : 10/1000 = 0.01 (1 %) ; 5/20 = 0.25 ; 1000/1000 = 1.0 (borne)
  • roi            : (150-100)/100 = 0.5 ; (200-100)/100 = 1.0 ; (50-100)/100 = -0.5 (perte) ;
                     (0-100)/100 = -1.0 (perte totale) ; (100-100)/100 = 0.0
  • cac            : 1000/50 = 20.0 ; 300/4 = 75.0 ; 0/10 = 0.0
  • roas           : 400/100 = 4.0 ; 250/100 = 2.5 ; 0/100 = 0.0
SOUNDNESS : dénominateur <= 0, entrée < 0, conversions>visiteurs / clics>impressions,
            valeur non finie / non numérique -> ValueError (jamais un faux).
DÉTERMINISME : mêmes entrées -> mêmes sorties.
"""

import marketing_metrics as M

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


# ── 1) ANCRE — taux de conversion (50/1000 = 5 %) ──
tc = M.taux_conversion(50, 1000)
check(approx(tc, 0.05), f"50 conv / 1000 visiteurs = 0.05 (obtenu {tc})")
check(approx(M.taux_conversion(1, 4), 0.25), "1/4 = 0.25")
check(approx(M.taux_conversion(0, 100), 0.0), "0 conversion = 0.0")
check(approx(M.taux_conversion(250, 250), 1.0), "tous convertis = 1.0 (borne haute)")
check(0.0 <= tc <= 1.0, "taux de conversion dans [0, 1]")

# ── 2) ANCRE — CTR (10/1000 = 1 %) ──
c = M.ctr(10, 1000)
check(approx(c, 0.01), f"CTR 10/1000 = 0.01 (obtenu {c})")
check(approx(M.ctr(5, 20), 0.25), "CTR 5/20 = 0.25")
check(approx(M.ctr(1000, 1000), 1.0), "CTR tous cliqués = 1.0 (borne haute)")
check(approx(M.ctr(0, 500), 0.0), "CTR 0 clic = 0.0")

# ── 3) ANCRE — ROI ((150-100)/100 = 0.5) ──
r = M.roi(150, 100)
check(approx(r, 0.5), f"ROI (150-100)/100 = 0.5 (obtenu {r})")
check(approx(M.roi(200, 100), 1.0), "ROI (200-100)/100 = 1.0")
check(approx(M.roi(100, 100), 0.0), "ROI seuil de rentabilité = 0.0")
check(approx(M.roi(50, 100), -0.5), "ROI (50-100)/100 = -0.5 (perte)")
check(approx(M.roi(0, 100), -1.0), "ROI gain nul = -1.0 (perte totale)")

# ── 4) ANCRE — CAC (1000/50 = 20) ──
ca = M.cac(1000, 50)
check(approx(ca, 20.0), f"CAC 1000/50 = 20.0 (obtenu {ca})")
check(approx(M.cac(300, 4), 75.0), "CAC 300/4 = 75.0")
check(approx(M.cac(0, 10), 0.0), "CAC coût nul = 0.0")

# ── 5) ANCRE — ROAS (400/100 = 4) ──
ro = M.roas(400, 100)
check(approx(ro, 4.0), f"ROAS 400/100 = 4.0 (obtenu {ro})")
check(approx(M.roas(250, 100), 2.5), "ROAS 250/100 = 2.5")
check(approx(M.roas(0, 100), 0.0), "ROAS revenu nul = 0.0")

# ── 6) SOUNDNESS — dénominateurs <= 0 (abstention) ──
check(_leve_v(M.taux_conversion, 50, 0), "visiteurs = 0 -> ValueError")
check(_leve_v(M.taux_conversion, 50, -1000), "visiteurs < 0 -> ValueError")
check(_leve_v(M.ctr, 10, 0), "impressions = 0 -> ValueError")
check(_leve_v(M.ctr, 10, -5), "impressions < 0 -> ValueError")
check(_leve_v(M.roi, 150, 0), "cout = 0 -> ValueError")
check(_leve_v(M.roi, 150, -100), "cout < 0 -> ValueError")
check(_leve_v(M.cac, 1000, 0), "clients_acquis = 0 -> ValueError")
check(_leve_v(M.cac, 1000, -50), "clients_acquis < 0 -> ValueError")
check(_leve_v(M.roas, 400, 0), "depense_pub = 0 -> ValueError")
check(_leve_v(M.roas, 400, -100), "depense_pub < 0 -> ValueError")

# ── 7) SOUNDNESS — numérateurs négatifs (abstention) ──
check(_leve_v(M.taux_conversion, -1, 1000), "conversions < 0 -> ValueError")
check(_leve_v(M.ctr, -1, 1000), "clics < 0 -> ValueError")
check(_leve_v(M.roi, -1, 100), "gain < 0 -> ValueError")
check(_leve_v(M.cac, -1, 50), "cout_total < 0 -> ValueError")
check(_leve_v(M.roas, -1, 100), "revenu < 0 -> ValueError")

# ── 8) SOUNDNESS — taux impossible > 1 (ratio borné par définition) ──
check(_leve_v(M.taux_conversion, 1001, 1000), "conversions > visiteurs -> ValueError")
check(_leve_v(M.ctr, 1001, 1000), "clics > impressions -> ValueError")

# ── 9) SOUNDNESS — valeurs non finies / non numériques (abstention) ──
check(_leve_v(M.taux_conversion, float("nan"), 1000), "conversions NaN -> ValueError")
check(_leve_v(M.taux_conversion, 50, float("inf")), "visiteurs inf -> ValueError")
check(_leve_v(M.ctr, "dix", 1000), "clics non numérique -> ValueError")
check(_leve_v(M.roi, 150, None), "cout None -> ValueError")
check(_leve_v(M.roas, float("inf"), 100), "revenu non fini -> ValueError")

# ── 10) DÉTERMINISME ──
check(M.taux_conversion(50, 1000) == M.taux_conversion(50, 1000), "taux_conversion déterministe")
check(M.ctr(10, 1000) == M.ctr(10, 1000), "ctr déterministe")
check(M.roi(150, 100) == M.roi(150, 100), "roi déterministe")
check(M.cac(1000, 50) == M.cac(1000, 50), "cac déterministe")
check(M.roas(400, 100) == M.roas(400, 100), "roas déterministe")

print(f"\n=== valide_marketing_metrics : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
