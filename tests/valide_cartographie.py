"""
VALIDE cartographie.py — held-out ADVERSE. Ancres CONNUES calculées indépendamment (échelle 1:25000 / 4 cm ->
1 km ; 1:50000 / 2 cm -> 1 km ; DMS 48°51′12″ -> 48,8533° ; tour Eiffel 48°51′30″ -> 48,8583° ; -2°30′00″ ->
-2,5° ; numérisation 300 dpi à 1:25000 -> 211,667 cm) + SOUNDNESS (échelle ≤ 0, minutes/secondes hors [0,60),
degrés/minutes non entiers, entrée invalide -> ValueError) + déterminisme. Aucun de ces cas n'est dans __main__.
"""
import cartographie as C

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def _leve(fn, *a, **k):
    """True ssi fn(*a, **k) lève ValueError (abstention), False sinon."""
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


EPS = 1e-9

# ── 1) ÉCHELLE — ancres calculées à la main ──
check(C.echelle_distance_reelle(4, 25000) == 100000, "1:25000, 4 cm -> 100000 cm (1 km)")
check(abs(C.cm_en_km(C.echelle_distance_reelle(4, 25000)) - 1.0) < EPS, "1:25000, 4 cm -> 1 km")
check(abs(C.cm_en_m(C.echelle_distance_reelle(4, 25000)) - 1000.0) < EPS, "1:25000, 4 cm -> 1000 m")
check(C.echelle_distance_reelle(2, 50000) == 100000, "1:50000, 2 cm -> 1 km")
check(C.echelle_distance_reelle(0, 25000) == 0, "0 cm sur carte -> 0 réel")
# distance_carte = inverse exact
check(C.distance_carte(100000, 25000) == 4, "inverse : 100000 cm réel à 1:25000 -> 4 cm carte")
check(abs(C.distance_carte(C.echelle_distance_reelle(7.3, 12345), 12345) - 7.3) < 1e-6,
      "round-trip échelle (7.3 cm)")

# ── 2) RÉSOLUTION AU SOL ──
check(C.resolution_au_sol(0.01, 25000).valeur_cm == 250.0, "pixel 0.01 cm à 1:25000 -> 250 cm")
# 300 dpi -> taille pixel = 2.54/300 cm ; × 25000 = 211.6666… cm
attendu = (2.54 / 300) * 25000
check(abs(C.resolution_au_sol_depuis_dpi(300, 25000).valeur_cm - attendu) < 1e-6,
      "300 dpi à 1:25000 -> ~211.667 cm")
check(abs(C.resolution_au_sol_depuis_dpi(300, 25000).valeur_cm - 211.6666667) < 1e-3,
      "300 dpi à 1:25000 -> 211.667 cm (ancre numérique)")

# ── 3) DMS -> DD — ancres connues ──
check(abs(C.conversion_dms_dd(48, 51, 12) - 48.8533333333) < 1e-7, "48°51′12″ -> 48.8533°")
check(abs(C.conversion_dms_dd(48, 51, 30) - 48.8583333333) < 1e-7, "48°51′30″ (Tour Eiffel) -> 48.8583°")
check(C.conversion_dms_dd(0, 0, 0) == 0.0, "0°0′0″ -> 0")
check(abs(C.conversion_dms_dd(2, 30, 0) - 2.5) < EPS, "2°30′00″ -> 2.5°")
check(abs(C.conversion_dms_dd(-2, 30, 0) - (-2.5)) < EPS, "-2°30′00″ -> -2.5° (signe par les degrés)")
check(abs(C.conversion_dms_dd(90, 0, 0) - 90.0) < EPS, "90°0′0″ -> 90 (pôle)")
check(abs(C.conversion_dms_dd(1, 0, 36) - 1.01) < EPS, "1°0′36″ -> 1.01°")

# ── 4) SOUNDNESS — échelle invalide -> ValueError ──
check(_leve(C.echelle_distance_reelle, 4, 0), "échelle dénominateur 0 -> ValueError")
check(_leve(C.echelle_distance_reelle, 4, -25000), "échelle dénominateur négatif -> ValueError")
check(_leve(C.distance_carte, 100000, 0), "distance_carte échelle 0 -> ValueError")
check(_leve(C.resolution_au_sol, 0.01, 0), "résolution échelle 0 -> ValueError")
check(_leve(C.resolution_au_sol_depuis_dpi, 0, 25000), "dpi 0 -> ValueError")
check(_leve(C.resolution_au_sol_depuis_dpi, -300, 25000), "dpi négatif -> ValueError")
check(_leve(C.echelle_distance_reelle, -4, 25000), "distance carte négative -> ValueError")
check(_leve(C.resolution_au_sol, 0, 25000), "taille pixel 0 -> ValueError")

# ── 5) SOUNDNESS — minutes/secondes hors [0, 60) -> ValueError ──
check(_leve(C.conversion_dms_dd, 48, 60, 0), "minutes 60 -> ValueError")
check(_leve(C.conversion_dms_dd, 48, -1, 0), "minutes négatives -> ValueError")
check(_leve(C.conversion_dms_dd, 48, 51, 60), "secondes 60 -> ValueError")
check(_leve(C.conversion_dms_dd, 48, 51, 60.0001), "secondes > 60 -> ValueError")
check(_leve(C.conversion_dms_dd, 48, 51, -0.5), "secondes négatives -> ValueError")
check(_leve(C.conversion_dms_dd, 48, 51.5, 0), "minutes non entières -> ValueError")
check(_leve(C.conversion_dms_dd, 48.5, 51, 0), "degrés non entiers -> ValueError")

# ── 6) SOUNDNESS — entrée non numérique / non finie / booléenne -> ValueError ──
check(_leve(C.echelle_distance_reelle, "4", 25000), "distance str -> ValueError")
check(_leve(C.echelle_distance_reelle, 4, "25000"), "échelle str -> ValueError")
check(_leve(C.conversion_dms_dd, True, 0, 0), "degrés booléen -> ValueError")
check(_leve(C.conversion_dms_dd, 48, 51, float("nan")), "secondes NaN -> ValueError")
check(_leve(C.echelle_distance_reelle, float("inf"), 25000), "distance inf -> ValueError")
check(_leve(C.cm_en_km, None), "cm None -> ValueError")

# ── 7) DÉTERMINISME ──
check(C.echelle_distance_reelle(4, 25000) == C.echelle_distance_reelle(4, 25000), "échelle déterministe")
check(C.conversion_dms_dd(48, 51, 12) == C.conversion_dms_dd(48, 51, 12), "DMS déterministe")
check(C.resolution_au_sol_depuis_dpi(300, 25000).valeur_cm
      == C.resolution_au_sol_depuis_dpi(300, 25000).valeur_cm, "résolution déterministe")

# ── 8) BORNES VALIDES juste sous la limite (ne lèvent PAS) ──
check(abs(C.conversion_dms_dd(48, 59, 59.999) - (48 + 59 / 60 + 59.999 / 3600)) < 1e-9,
      "59′59.999″ valide (juste sous 60)")
check(C.conversion_dms_dd(48, 0, 0) == 48.0, "0′0″ borne basse valide")

print(f"\n=== valide_cartographie : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
