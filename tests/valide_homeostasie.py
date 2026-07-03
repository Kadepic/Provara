"""
VALIDE homeostasie.py — held-out ADVERSE. Exactitude de la rétroaction négative (écart / correction de signe
opposé / bande de tolérance) + consignes physiologiques de référence + SOUNDNESS (gain<0, tolerance<0, entrée
non numérique/NaN -> ValueError) + DÉTERMINISME. Ancres recalculées à la main.
"""
import homeostasie as H

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve_v(fn, *a, **k):
    """True ssi fn(*a, **k) lève ValueError (abstention attendue)."""
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


EPS = 1e-9

# 1) ÉCART À LA CONSIGNE = valeur − consigne (signe = sens du déséquilibre).
check(abs(H.ecart_consigne(39, 37) - 2.0) < EPS, "écart 39/37 = +2 (trop chaud)")
check(abs(H.ecart_consigne(35, 37) - (-2.0)) < EPS, "écart 35/37 = -2 (trop froid)")
check(abs(H.ecart_consigne(37, 37)) < EPS, "écart 37/37 = 0 (à la consigne)")
check(abs(H.ecart_consigne(1.3, 1.0) - 0.3) < EPS, "écart glycémie 1.3/1.0 = +0.3")
check(abs(H.ecart_consigne(7.45, 7.4) - 0.05) < EPS, "écart pH 7.45/7.4 = +0.05")

# 2) CORRECTION = −gain·(valeur − consigne) : de signe OPPOSÉ à l'écart (rétroaction NÉGATIVE).
#    valeur 39, consigne 37, gain 0.5 -> -0.5 * (+2) = -1.0 (correction négative = refroidir).
check(abs(H.correction(39, 37, 0.5) - (-1.0)) < EPS, "correction 39/37 gain0.5 = -1 (refroidir)")
#    valeur 35, consigne 37, gain 2 -> -2 * (-2) = +4.0 (correction positive = réchauffer).
check(abs(H.correction(35, 37, 2) - 4.0) < EPS, "correction 35/37 gain2 = +4 (réchauffer)")
#    à la consigne -> correction nulle quel que soit le gain.
check(abs(H.correction(37, 37, 10)) < EPS, "correction nulle à la consigne")
#    gain nul -> correction nulle.
check(abs(H.correction(39, 37, 0)) < EPS, "correction gain nul = 0")
#    glycémie : valeur 1.3, consigne 1.0, gain 1 -> -1 * (+0.3) = -0.3 (abaisser, ~insuline).
check(abs(H.correction(1.3, 1.0, 1) - (-0.3)) < EPS, "correction glycémie 1.3 gain1 = -0.3")

# 2b) SIGNE OPPOSÉ garanti (propriété de la rétroaction négative) : sur un balayage, correction·écart <= 0.
for v in [-5, -1.5, 0, 0.7, 37, 40.2, 100]:
    e = H.ecart_consigne(v, 37)
    c = H.correction(v, 37, 0.8)
    check(c * e <= EPS, f"correction de signe opposé à l'écart (v={v})")

# 3) EST_REGULE : |valeur − consigne| <= tolerance.
check(H.est_regule(37.3, 37, 0.5) is True, "37.3/37 tol0.5 -> régulé")
check(H.est_regule(39, 37, 0.5) is False, "39/37 tol0.5 -> NON régulé")
check(H.est_regule(39, 37, 2) is True, "39/37 tol2 (bord) -> régulé")
check(H.est_regule(35, 37, 2) is True, "35/37 tol2 (bord bas) -> régulé")
check(H.est_regule(37, 37, 0) is True, "exactement à la consigne, tol0 -> régulé")
check(H.est_regule(7.45, 7.4, 0.05) is True, "pH 7.45/7.4 tol0.05 -> régulé")
check(H.est_regule(7.6, 7.4, 0.05) is False, "pH 7.6/7.4 tol0.05 -> NON régulé (acidose/alcalose)")

# 4) CONSIGNES PHYSIOLOGIQUES DE RÉFÉRENCE (données sourcées).
check(abs(H.consigne_reference("glycemie_g_par_L") - 1.0) < EPS, "consigne glycémie = 1 g/L")
check(abs(H.consigne_reference("temperature_corporelle_C") - 37.0) < EPS, "consigne température = 37 °C")
check(abs(H.consigne_reference("pH_sang") - 7.4) < EPS, "consigne pH = 7.4")

# 5) SOUNDNESS — abstention (ValueError), JAMAIS un faux.
check(leve_v(H.correction, 39, 37, -1), "gain < 0 -> ValueError (rétroaction positive interdite)")
check(leve_v(H.est_regule, 39, 37, -0.5), "tolerance < 0 -> ValueError")
check(leve_v(H.ecart_consigne, "x", 37), "valeur non numérique -> ValueError")
check(leve_v(H.ecart_consigne, 39, None), "consigne None -> ValueError")
check(leve_v(H.correction, 39, 37, "fort"), "gain non numérique -> ValueError")
check(leve_v(H.ecart_consigne, float("nan"), 37), "NaN -> ValueError")
check(leve_v(H.ecart_consigne, float("inf"), 37), "inf -> ValueError")
check(leve_v(H.ecart_consigne, True, 37), "booléen refusé -> ValueError")
check(leve_v(H.consigne_reference, "tension_arterielle"), "consigne inconnue -> ValueError (hors référentiel)")
check(leve_v(H.consigne_reference, None), "consigne non-str -> ValueError")

# 6) gain = 0 et tolerance = 0 sont ACCEPTÉS (bornes valides, pas d'erreur).
check(abs(H.correction(50, 37, 0) - 0.0) < EPS, "gain = 0 accepté")
check(H.est_regule(37, 37, 0) is True, "tolerance = 0 acceptée")

# 7) DÉTERMINISME (fonctions pures).
check(H.correction(39, 37, 0.5) == H.correction(39, 37, 0.5), "déterminisme correction")
check(H.ecart_consigne(1.3, 1.0) == H.ecart_consigne(1.3, 1.0), "déterminisme écart")
check(H.est_regule(39, 37, 2) == H.est_regule(39, 37, 2), "déterminisme est_regule")

print(f"\n=== valide_homeostasie : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
