"""
VALIDE eclipses.py — held-out ADVERSE.

Ancres CONNUES (valeurs astronomiques de référence, PAS recalculées par la même expression triviale) :
  • mois synodique ≈ 29.53 j (Lune 27.32 / Soleil-apparent 365.25)
  • période synodique Terre–Mars ≈ 780 j (365.25 / 686.98)
  • pleine lune (180°) -> fraction illuminée = 1 ; nouvelle (0°) -> 0 ; quartier (90°) -> 0.5
  • symétrie periode_synodique(T1,T2) == periode_synodique(T2,T1)
SOUNDNESS : T<=0, T1==T2, angle hors [0,360), latitude hors [-90,90], seuil<=0 -> ValueError.
DÉTERMINISME : mêmes entrées -> mêmes sorties.
"""

import eclipses as E

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


def _leve_v(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) ANCRES — période synodique (valeurs astronomiques connues) ──
mois = E.periode_synodique(27.32, 365.25)
check(29.4 < mois < 29.6, f"mois synodique ≈ 29.53 j (obtenu {mois:.4f})")
check(approx(mois, 1.0 / abs(1 / 27.32 - 1 / 365.25)), "période synodique = 1/|1/T1−1/T2|")
mars = E.periode_synodique(365.25, 686.98)
check(770.0 < mars < 790.0, f"synodique Terre–Mars ≈ 780 j (obtenu {mars:.2f})")
# Symétrie des arguments.
check(approx(E.periode_synodique(27.32, 365.25), E.periode_synodique(365.25, 27.32)),
      "periode_synodique symétrique")
# Cas trivial : T2 -> très grand -> période ~ T1 (Soleil immobile).
check(E.periode_synodique(10.0, 1e12) > 9.9 and E.periode_synodique(10.0, 1e12) < 10.1,
      "T2 immense -> période ≈ T1")

# ── 2) ANCRES — phases lunaires (cardinaux + intervalles) ──
check(E.phase_lune(0) == "nouvelle", "0° -> nouvelle")
check(E.phase_lune(90) == "premier_quartier", "90° -> premier_quartier")
check(E.phase_lune(180) == "pleine", "180° -> pleine")
check(E.phase_lune(270) == "dernier_quartier", "270° -> dernier_quartier")
check(E.phase_lune(90.0) == "premier_quartier", "90.0 (float) -> premier_quartier")
check(E.phase_lune(45) == "premier_croissant", "45° -> premier_croissant")
check(E.phase_lune(135) == "gibbeuse_croissante", "135° -> gibbeuse_croissante")
check(E.phase_lune(225) == "gibbeuse_decroissante", "225° -> gibbeuse_decroissante")
check(E.phase_lune(315) == "dernier_croissant", "315° -> dernier_croissant")
check(E.phase_lune(359.999) == "dernier_croissant", "359.999° -> dernier_croissant")

# ── 3) ANCRES — fraction illuminée (1−cos)/2 ──
check(approx(E.fraction_illuminee(0), 0.0), "nouvelle -> fraction 0")
check(approx(E.fraction_illuminee(180), 1.0), "pleine -> fraction 1")
check(approx(E.fraction_illuminee(90), 0.5), "quartier (90°) -> fraction 0.5")
check(approx(E.fraction_illuminee(270), 0.5), "quartier (270°) -> fraction 0.5")
check(approx(E.fraction_illuminee(60), 0.25), "60° -> fraction 0.25")
check(approx(E.fraction_illuminee(120), 0.75), "120° -> fraction 0.75")
# Bornage [0,1].
for ang in (0, 33, 77, 181, 250, 359.9):
    fr = E.fraction_illuminee(ang)
    check(0.0 <= fr <= 1.0, f"fraction dans [0,1] @ {ang}")
# Monotonie croissante sur [0,180].
check(E.fraction_illuminee(30) < E.fraction_illuminee(60) < E.fraction_illuminee(90)
      < E.fraction_illuminee(150), "fraction croît sur [0,180]")

# ── 4) ANCRES — condition d'éclipse ──
check(E.condition_eclipse(0.0) is True, "lat 0° -> éclipse possible")
check(E.condition_eclipse(1.0) is True, "lat 1° < 1.5 -> possible")
check(E.condition_eclipse(-1.0) is True, "lat −1° -> possible (|lat|)")
check(E.condition_eclipse(1.5) is False, "lat 1.5° = seuil -> impossible (strict <)")
check(E.condition_eclipse(5.0) is False, "lat 5° -> impossible")
check(E.condition_eclipse(4.0, seuil=5.0) is True, "seuil 5° : lat 4° -> possible")
check(E.condition_eclipse(6.0, seuil=5.0) is False, "seuil 5° : lat 6° -> impossible")

# ── 5) SOUNDNESS — abstention (ValueError), faux positif INTERDIT ──
check(_leve_v(E.periode_synodique, 0, 365.25), "T1=0 -> ValueError")
check(_leve_v(E.periode_synodique, 27.32, -3), "T2<0 -> ValueError")
check(_leve_v(E.periode_synodique, 30.0, 30.0), "T1==T2 -> ValueError (synodique infinie)")
check(_leve_v(E.periode_synodique, float("inf"), 10), "T1 non fini -> ValueError")
check(_leve_v(E.phase_lune, 360), "angle 360 hors [0,360) -> ValueError")
check(_leve_v(E.phase_lune, -1), "angle négatif -> ValueError")
check(_leve_v(E.phase_lune, 720), "angle 720 -> ValueError")
check(_leve_v(E.phase_lune, float("nan")), "angle NaN -> ValueError")
check(_leve_v(E.fraction_illuminee, 400), "fraction angle 400 -> ValueError")
check(_leve_v(E.fraction_illuminee, -10), "fraction angle négatif -> ValueError")
check(_leve_v(E.condition_eclipse, 100.0), "latitude 100° hors [-90,90] -> ValueError")
check(_leve_v(E.condition_eclipse, -91.0), "latitude −91° -> ValueError")
check(_leve_v(E.condition_eclipse, 1.0, 0), "seuil 0 -> ValueError")
check(_leve_v(E.condition_eclipse, 1.0, -2), "seuil négatif -> ValueError")

# ── 6) DÉTERMINISME ──
check(E.periode_synodique(27.32, 365.25) == E.periode_synodique(27.32, 365.25),
      "periode_synodique déterministe")
check(E.phase_lune(123.4) == E.phase_lune(123.4), "phase_lune déterministe")
check(E.fraction_illuminee(123.4) == E.fraction_illuminee(123.4), "fraction déterministe")
check(E.condition_eclipse(0.7) == E.condition_eclipse(0.7), "condition_eclipse déterministe")

print(f"\n=== valide_eclipses : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
