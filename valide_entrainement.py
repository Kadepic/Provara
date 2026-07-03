"""
VALIDE entrainement.py — held-out ADVERSE (FAUX=0).

Ancres CONNUES NON circulaires (recalculées à la main, indépendamment de l'implémentation) :
  • Epley : 100 kg / 5 reps -> 100·(35/30) ≈ 116.67 kg ; 100 kg / 10 reps -> 133.33 ; 60/10 -> 80.0.
  • Haskell : FCmax(30) = 190 ; FCmax(40) = 180 ; FCmax(0) = 220 ; FCmax(120) = 100.
  • Karvonen : croisements conceptuels — intensité 0 -> FCrepos, intensité 1 -> FCmax (=220−age) ;
      FCrepos 70, 40 ans, 0.5 -> 70 + 0.5·110 = 125 ; FCrepos 60, 30 ans, 0.7 -> 151.
  • Uth (VO2max) : 200/50 -> 15.3·4 = 61.2 ; 180/60 -> 45.9 ; 190/50 -> 58.14.
SOUNDNESS : poids<=0, reps<1, age<0/>120, intensité hors [0,1], fc_repos invalide, non fini/bool/str -> ValueError.
DÉTERMINISME : mêmes entrées -> mêmes sorties.
"""

import entrainement as E

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


# ── 1) ANCRE — 1RM Epley (recalcul à la main) ──
check(approx(E.un_rep_max_epley(100, 5), 116.67), "Epley 100kg/5reps ≈ 116.67")
check(approx(E.un_rep_max_epley(100, 10), 133.33), "Epley 100kg/10reps = 133.33")
check(approx(E.un_rep_max_epley(60, 10), 80.0), "Epley 60kg/10reps = 80.0")
check(approx(E.un_rep_max_epley(50, 1), 51.67), "Epley 50kg/1rep = 51.67 (Epley ≠ poids à 1 rep)")
check(approx(E.un_rep_max_epley(100, 1), 103.33), "Epley 100kg/1rep = 103.33")
# Monotonie : plus de reps -> 1RM estimé plus grand (à charge égale).
check(E.un_rep_max_epley(100, 10) > E.un_rep_max_epley(100, 5), "1RM croît avec les reps")
check(E.un_rep_max_epley(120, 5) > E.un_rep_max_epley(100, 5), "1RM croît avec la charge")

# ── 2) ANCRE — FCmax Haskell (220 − âge) ──
check(approx(E.frequence_cardiaque_max(30), 190.0), "FCmax(30) = 190")
check(approx(E.frequence_cardiaque_max(40), 180.0), "FCmax(40) = 180")
check(approx(E.frequence_cardiaque_max(0), 220.0), "FCmax(0) = 220")
check(approx(E.frequence_cardiaque_max(120), 100.0), "FCmax(120) = 100 (borne haute incluse)")
check(approx(E.frequence_cardiaque_max(50), 170.0), "FCmax(50) = 170")
check(E.frequence_cardiaque_max(20) > E.frequence_cardiaque_max(60), "FCmax décroît avec l'âge")

# ── 3) ANCRE — Karvonen (réserve de FC) + croisements conceptuels ──
check(approx(E.zone_cible_karvonen(60, 30, 0.7), 151.0), "Karvonen 60/30ans/0.7 = 151")
check(approx(E.zone_cible_karvonen(70, 40, 0.5), 125.0), "Karvonen 70/40ans/0.5 = 125")
# intensité 0 -> FCrepos exact ; intensité 1 -> FCmax exact (cross-check NON circulaire avec FCmax).
check(approx(E.zone_cible_karvonen(70, 40, 0.0), 70.0), "Karvonen i=0 -> FCrepos (70)")
check(approx(E.zone_cible_karvonen(70, 40, 1.0), 180.0), "Karvonen i=1 -> FCmax (180)")
check(approx(E.zone_cible_karvonen(70, 40, 1.0), E.frequence_cardiaque_max(40)),
      "Karvonen i=1 == frequence_cardiaque_max(age) (cohérence inter-fonctions)")
check(approx(E.zone_cible_karvonen(60, 30, 0.0), 60.0), "Karvonen i=0 -> FCrepos (60)")
check(approx(E.zone_cible_karvonen(60, 30, 1.0), E.frequence_cardiaque_max(30)),
      "Karvonen i=1 == FCmax(30) = 190")
# La cible est bornée entre FCrepos et FCmax, et croît avec l'intensité.
check(E.zone_cible_karvonen(60, 30, 0.7) > E.zone_cible_karvonen(60, 30, 0.5),
      "cible Karvonen croît avec l'intensité")
check(60.0 <= E.zone_cible_karvonen(60, 30, 0.3) <= 190.0, "cible dans [FCrepos, FCmax]")

# ── 4) ANCRE — VO2max Uth (15.3 · FCmax/FCrepos) ──
check(approx(E.vo2max_estime(200, 50), 61.2), "VO2max Uth 200/50 = 61.2")
check(approx(E.vo2max_estime(180, 60), 45.9), "VO2max Uth 180/60 = 45.9")
check(approx(E.vo2max_estime(190, 50), 58.14), "VO2max Uth 190/50 = 58.14")
check(approx(E.vo2max_estime(190, 60), 48.45), "VO2max Uth 190/60 = 48.45")
check(E.vo2max_estime(200, 40) > E.vo2max_estime(200, 60), "VO2max décroît si FCrepos monte (meilleure forme = FCrepos bas)")

# ── 5) SOUNDNESS — abstention (ValueError), faux positif INTERDIT ──
# Epley
check(_leve_v(E.un_rep_max_epley, 0, 5), "poids = 0 -> ValueError")
check(_leve_v(E.un_rep_max_epley, -10, 5), "poids < 0 -> ValueError")
check(_leve_v(E.un_rep_max_epley, 100, 0), "repetitions = 0 (<1) -> ValueError")
check(_leve_v(E.un_rep_max_epley, 100, 0.5), "repetitions 0.5 (<1) -> ValueError")
check(_leve_v(E.un_rep_max_epley, 100, -3), "repetitions < 0 -> ValueError")
check(_leve_v(E.un_rep_max_epley, float("inf"), 5), "poids non fini -> ValueError")
check(_leve_v(E.un_rep_max_epley, float("nan"), 5), "poids NaN -> ValueError")
check(_leve_v(E.un_rep_max_epley, 100, float("inf")), "reps non fini -> ValueError")
check(_leve_v(E.un_rep_max_epley, "cent", 5), "poids non numérique -> ValueError")
check(_leve_v(E.un_rep_max_epley, True, 5), "poids booléen -> ValueError")
check(_leve_v(E.un_rep_max_epley, 100, True), "reps booléen -> ValueError")
# FCmax
check(_leve_v(E.frequence_cardiaque_max, -1), "age < 0 -> ValueError")
check(_leve_v(E.frequence_cardiaque_max, 121), "age > 120 -> ValueError")
check(_leve_v(E.frequence_cardiaque_max, 120.0001), "age 120.0001 -> ValueError")
check(_leve_v(E.frequence_cardiaque_max, float("nan")), "age NaN -> ValueError")
check(_leve_v(E.frequence_cardiaque_max, float("inf")), "age non fini -> ValueError")
check(_leve_v(E.frequence_cardiaque_max, "trente"), "age non numérique -> ValueError")
check(_leve_v(E.frequence_cardiaque_max, False), "age booléen -> ValueError")
# Karvonen
check(_leve_v(E.zone_cible_karvonen, 60, -1, 0.5), "Karvonen age < 0 -> ValueError")
check(_leve_v(E.zone_cible_karvonen, 60, 121, 0.5), "Karvonen age > 120 -> ValueError")
check(_leve_v(E.zone_cible_karvonen, 60, 30, 1.5), "intensité > 1 -> ValueError")
check(_leve_v(E.zone_cible_karvonen, 60, 30, -0.1), "intensité < 0 -> ValueError")
check(_leve_v(E.zone_cible_karvonen, 0, 30, 0.5), "fc_repos = 0 -> ValueError")
check(_leve_v(E.zone_cible_karvonen, -5, 30, 0.5), "fc_repos < 0 -> ValueError")
check(_leve_v(E.zone_cible_karvonen, 190, 30, 0.5), "fc_repos = FCmax(30) -> ValueError (réserve nulle)")
check(_leve_v(E.zone_cible_karvonen, 200, 30, 0.5), "fc_repos > FCmax -> ValueError")
check(_leve_v(E.zone_cible_karvonen, 60, 30, float("nan")), "intensité NaN -> ValueError")
check(_leve_v(E.zone_cible_karvonen, 60, 30, True), "intensité booléenne -> ValueError")
check(_leve_v(E.zone_cible_karvonen, "soixante", 30, 0.5), "fc_repos non numérique -> ValueError")
# VO2max
check(_leve_v(E.vo2max_estime, 0, 50), "fc_max = 0 -> ValueError")
check(_leve_v(E.vo2max_estime, -200, 50), "fc_max < 0 -> ValueError")
check(_leve_v(E.vo2max_estime, 200, 0), "fc_repos = 0 -> ValueError")
check(_leve_v(E.vo2max_estime, 200, -50), "fc_repos < 0 -> ValueError")
check(_leve_v(E.vo2max_estime, 50, 50), "fc_max = fc_repos (ratio impossible) -> ValueError")
check(_leve_v(E.vo2max_estime, 40, 60), "fc_max < fc_repos -> ValueError")
check(_leve_v(E.vo2max_estime, float("inf"), 50), "fc_max non fini -> ValueError")
check(_leve_v(E.vo2max_estime, 200, "cinquante"), "fc_repos non numérique -> ValueError")
check(_leve_v(E.vo2max_estime, 200, True), "fc_repos booléen -> ValueError")

# ── 6) DÉTERMINISME ──
check(E.un_rep_max_epley(100, 5) == E.un_rep_max_epley(100, 5), "Epley déterministe")
check(E.frequence_cardiaque_max(30) == E.frequence_cardiaque_max(30), "FCmax déterministe")
check(E.zone_cible_karvonen(60, 30, 0.7) == E.zone_cible_karvonen(60, 30, 0.7), "Karvonen déterministe")
check(E.vo2max_estime(200, 50) == E.vo2max_estime(200, 50), "VO2max déterministe")

# ── 7) SORTIE arrondie 2 décimales (précision honnête) ──
check(E.un_rep_max_epley(100, 5) == round(E.un_rep_max_epley(100, 5), 2), "Epley arrondi 2 décimales")
check(E.vo2max_estime(190, 50) == round(E.vo2max_estime(190, 50), 2), "VO2max arrondi 2 décimales")

print(f"\n=== valide_entrainement : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
