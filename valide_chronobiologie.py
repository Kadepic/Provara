"""
VALIDE chronobiologie.py — held-out ADVERSE.

Ancres CONNUES (faits de chronobiologie + arithmétique vérifiée à la main) :
  • période circadienne intrinsèque ≈ 24.2 h (> 24 h ; Czeisler 1999 = 24.18 h)
  • cycle de sommeil ≈ 90 min ; 8 h = 480 min / 90 = 16/3 ≈ 5.333 cycles
  • 5 cycles = 450 min = 7.5 h ; inverse cohérent avec nombre_cycles_sommeil
  • pic de mélatonine la nuit (~2-4 h) ; jour [6,22) ; nuit sinon
SOUNDNESS : duree<0, cycle<=0, n_cycles<0, heure hors [0,24), non fini -> ValueError.
DÉTERMINISME : mêmes entrées -> mêmes sorties.
"""

import chronobiologie as C

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


# ── 1) ANCRE — période circadienne (fait : ~24.2 h, > 24 h) ──
p = C.periode_circadienne()
check(approx(p, 24.2), f"période circadienne = 24.2 h (obtenu {p})")
check(24.0 < p < 24.5, "période circadienne dans ]24.0, 24.5[ (légèrement > 24 h)")
check(p > 24.0, "période intrinsèque strictement > 24 h (fait clé)")

# ── 2) ANCRE — nombre de cycles de sommeil (arithmétique) ──
c8 = C.nombre_cycles_sommeil(480)
check(approx(c8, 16.0 / 3.0), f"8 h = 480/90 = 16/3 ≈ 5.333 cycles (obtenu {c8})")
check(5.3 < c8 < 5.4, "8 h ≈ 5.3 cycles")
check(approx(C.nombre_cycles_sommeil(450), 5.0), "450 min -> 5.0 cycles")
check(approx(C.nombre_cycles_sommeil(90), 1.0), "90 min -> 1.0 cycle")
check(approx(C.nombre_cycles_sommeil(0), 0.0), "0 min -> 0.0 cycle")
check(approx(C.nombre_cycles_sommeil(540), 6.0), "9 h (540 min) -> 6.0 cycles")
# cycle personnalisé
check(approx(C.nombre_cycles_sommeil(360, 120), 3.0), "360 min, cycle 120 -> 3.0 cycles")
check(approx(C.nombre_cycles_sommeil(480, cycle_min=90), 16.0 / 3.0), "kwarg cycle_min=90 ok")

# ── 3) ANCRE — durée pour n cycles (inverse) ──
check(approx(C.duree_pour_cycles(5), 450.0), "5 cycles -> 450 min")
check(approx(C.duree_pour_cycles(5) / 60.0, 7.5), "5 cycles -> 7.5 h")
check(approx(C.duree_pour_cycles(0), 0.0), "0 cycle -> 0 min")
check(approx(C.duree_pour_cycles(1), 90.0), "1 cycle -> 90 min")
# Cohérence inverse exacte.
check(approx(C.nombre_cycles_sommeil(C.duree_pour_cycles(5)), 5.0),
      "inverse cohérent : cycles(duree(5)) == 5")
check(approx(C.duree_pour_cycles(C.nombre_cycles_sommeil(480)), 480.0),
      "inverse cohérent : duree(cycles(480)) == 480")

# ── 4) ANCRE — phase circadienne (jour / nuit / pic de mélatonine) ──
check(C.phase_circadienne(3) == "pic_melatonine", "3 h -> pic_melatonine (~2-4 h)")
check(C.phase_circadienne(2) == "pic_melatonine", "2 h (borne basse incluse) -> pic_melatonine")
check(C.phase_circadienne(3.999) == "pic_melatonine", "3.999 h -> pic_melatonine")
check(C.phase_circadienne(4) == "nuit", "4 h (borne haute exclue) -> nuit")
check(C.phase_circadienne(0) == "nuit", "minuit -> nuit")
check(C.phase_circadienne(1.9) == "nuit", "1.9 h -> nuit (avant le pic)")
check(C.phase_circadienne(5) == "nuit", "5 h -> nuit")
check(C.phase_circadienne(5.999) == "nuit", "5.999 h -> nuit")
check(C.phase_circadienne(6) == "jour", "6 h (borne incluse) -> jour")
check(C.phase_circadienne(12) == "jour", "midi -> jour")
check(C.phase_circadienne(15) == "jour", "15 h -> jour")
check(C.phase_circadienne(21.999) == "jour", "21.999 h -> jour")
check(C.phase_circadienne(22) == "nuit", "22 h (borne incluse) -> nuit")
check(C.phase_circadienne(23) == "nuit", "23 h -> nuit")
check(C.phase_circadienne(23.999) == "nuit", "23.999 h -> nuit")
# Le pic est bien un sous-ensemble de la nuit (cohérence conceptuelle).
for hh in (2.0, 2.5, 3.0, 3.5):
    check(C.phase_circadienne(hh) == "pic_melatonine", f"{hh} h dans le pic")

# ── 5) SOUNDNESS — abstention (ValueError), faux positif INTERDIT ──
check(_leve_v(C.nombre_cycles_sommeil, -1), "duree_min < 0 -> ValueError")
check(_leve_v(C.nombre_cycles_sommeil, -0.0001), "duree_min très petite < 0 -> ValueError")
check(_leve_v(C.nombre_cycles_sommeil, 480, 0), "cycle_min = 0 -> ValueError")
check(_leve_v(C.nombre_cycles_sommeil, 480, -90), "cycle_min < 0 -> ValueError")
check(_leve_v(C.nombre_cycles_sommeil, float("inf")), "duree_min non fini -> ValueError")
check(_leve_v(C.nombre_cycles_sommeil, float("nan")), "duree_min NaN -> ValueError")
check(_leve_v(C.nombre_cycles_sommeil, 480, float("nan")), "cycle_min NaN -> ValueError")
check(_leve_v(C.nombre_cycles_sommeil, "abc"), "duree_min non numérique -> ValueError")
check(_leve_v(C.duree_pour_cycles, -1), "n_cycles < 0 -> ValueError")
check(_leve_v(C.duree_pour_cycles, 5, 0), "duree_pour_cycles cycle_min=0 -> ValueError")
check(_leve_v(C.duree_pour_cycles, 5, -1), "duree_pour_cycles cycle_min<0 -> ValueError")
check(_leve_v(C.duree_pour_cycles, float("inf")), "n_cycles non fini -> ValueError")
check(_leve_v(C.phase_circadienne, 24), "heure 24 hors [0,24) -> ValueError")
check(_leve_v(C.phase_circadienne, -1), "heure négative -> ValueError")
check(_leve_v(C.phase_circadienne, 24.5), "heure 24.5 -> ValueError")
check(_leve_v(C.phase_circadienne, 100), "heure 100 -> ValueError")
check(_leve_v(C.phase_circadienne, float("nan")), "heure NaN -> ValueError")
check(_leve_v(C.phase_circadienne, float("inf")), "heure non finie -> ValueError")
check(_leve_v(C.phase_circadienne, "minuit"), "heure non numérique -> ValueError")

# ── 6) DÉTERMINISME ──
check(C.periode_circadienne() == C.periode_circadienne(), "periode_circadienne déterministe")
check(C.nombre_cycles_sommeil(480) == C.nombre_cycles_sommeil(480),
      "nombre_cycles_sommeil déterministe")
check(C.duree_pour_cycles(5) == C.duree_pour_cycles(5), "duree_pour_cycles déterministe")
check(C.phase_circadienne(3.0) == C.phase_circadienne(3.0), "phase_circadienne déterministe")
check(C.phase_circadienne(13.7) == C.phase_circadienne(13.7), "phase_circadienne déterministe (jour)")

print(f"\n=== valide_chronobiologie : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
