"""VALIDE seismologie.py — lois exactes (oracle re-dérivé), réciproques, invariants d'échelle, FAUX=0.

Ancres : Mw d'un moment connu, énergie d'une magnitude, +1 magnitude = ×10 amplitude / ×~31.6 énergie. Réciproques
round-trip. Négatifs : moment/énergie ≤ 0, hors échelle -> ValueError.
"""
import math

import seismologie as S

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def proche(a, b, rel=1e-9, abs_=1e-9):
    return abs(a - b) <= rel * abs(b) + abs_


def leve(fn, *a, **k):
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) magnitude_moment (oracle re-dérivé) ──
m0 = 1e22
attendu = (2 / 3) * (math.log10(m0) - 9.1)
check(proche(S.magnitude_moment(m0), attendu), "Mw(1e22 N·m) = (2/3)(22−9.1) ≈ 8.6")
check(proche(S.magnitude_moment(m0), 8.6, rel=1e-3), "Mw(1e22) ≈ 8.6 (grand séisme)")

# ── 2) réciproque moment<->magnitude (round-trip) ──
for mw in (5.0, 6.5, 7.8, 9.0):
    check(proche(S.magnitude_moment(S.moment_depuis_magnitude(mw)), mw), f"round-trip Mw={mw}")

# ── 3) énergie (Gutenberg-Richter) + réciproque ──
attendu_e = 10 ** (1.5 * 6.0 + 4.8)
check(proche(S.energie_joules(6.0), attendu_e), "E(M6) = 10^(1.5·6+4.8) J")
for m in (4.0, 5.5, 7.0):
    check(proche(S.magnitude_depuis_energie(S.energie_joules(m)), m), f"round-trip énergie M={m}")

# ── 4) invariants d'échelle re-dérivés ──
check(proche(S.rapport_amplitude(6, 5), 10.0), "+1 magnitude -> ×10 amplitude")
check(proche(S.rapport_energie(6, 5), 10 ** 1.5) and proche(S.rapport_energie(6, 5), 31.6227766, rel=1e-6), "+1 magnitude -> ×~31.6 énergie")
check(proche(S.rapport_energie(7, 5), 1000.0), "+2 magnitudes -> ×1000 énergie")

# ── 5) classification USGS (référentiel fermé) ──
check(S.classe(1.0) == "micro" and S.classe(3.0) == "mineur" and S.classe(4.5) == "léger", "classes basses")
check(S.classe(5.5) == "modéré" and S.classe(6.5) == "fort" and S.classe(7.5) == "majeur" and S.classe(9.0) == "exceptionnel", "classes hautes")
check(S.classe(2.0) == "mineur", "borne inclusive : 2.0 -> mineur (pas micro)")

# ── 6) FAUX=0 ──
check(leve(S.magnitude_moment, 0), "moment nul -> ValueError")
check(leve(S.magnitude_moment, -1e10), "moment négatif -> ValueError")
check(leve(S.magnitude_depuis_energie, 0), "énergie nulle -> ValueError")
check(leve(S.classe, 20), "magnitude hors échelle -> ValueError")
check(leve(S.energie_joules, float("nan")), "argument NaN -> ValueError")
check(leve(S.magnitude_moment, True), "booléen -> ValueError")

print(f"\n=== valide_seismologie : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
