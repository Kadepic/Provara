"""
VALIDE analyse_chimique.py — held-out ADVERSE.

ANCRES EXTERNES CONNUES (non recalculées par la même expression du module) :
  • Beer-Lambert : A = ε·l·c ; valeurs de manuel (T=10^(−A) -> A=1→T=0.1, A=2→T=0.01, A=3→T=0.001 ; A=0→T=1).
  • Relation inverse exacte A = −log₁₀(T) (vérifiée par cohérence croisée, pas par 10^(−A)).
  • Chromatographie CCM : Rf = 2/5 = 0.4 (cas de référence de l'énoncé), 3/4 = 0.75, 5/5 = 1.0.
SOUNDNESS : ε≤0, l≤0, c<0, A<0, distances≤0, soluté>solvant, type non numérique/booléen -> ValueError (jamais un faux).
DÉTERMINISME : double appel identique.
"""
import math

import analyse_chimique as A

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def approx(x, attendu, tol=1e-9):
    return x is not None and abs(x - attendu) <= tol


def leve(fn, *args):
    try:
        fn(*args)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) BEER-LAMBERT : A = ε·l·c (ancres numériques connues) ──
check(approx(A.absorbance(1, 1, 1), 1.0), "A = 1·1·1 = 1")
check(approx(A.absorbance(2, 1, 0.5), 1.0), "A = 2·1·0.5 = 1")
check(approx(A.absorbance(200, 1, 0.0005), 0.1), "A = 200·1·5e-4 = 0.1")
check(approx(A.absorbance(1, 1, 0), 0.0), "c = 0 -> A = 0 (limite admise)")
check(approx(A.absorbance(1500, 2, 0.001), 3.0), "A = 1500·2·1e-3 = 3")

# ── 2) CONCENTRATION DEPUIS L'ABSORBANCE : c = A/(ε·l) ──
check(approx(A.concentration_depuis_absorbance(1, 200, 1), 0.005), "c = 1/(200·1) = 0.005")
check(approx(A.concentration_depuis_absorbance(2, 2, 1), 1.0), "c = 2/(2·1) = 1")
check(approx(A.concentration_depuis_absorbance(0, 100, 1), 0.0), "A = 0 -> c = 0")
check(approx(A.concentration_depuis_absorbance(0.1, 200, 1), 0.0005), "c = 0.1/200 = 5e-4")

# ── 3) TRANSMITTANCE : T = 10^(−A), T ∈ ]0,1] (ancres de manuel) ──
check(approx(A.transmittance(1), 0.1), "A = 1 -> T = 0.1")
check(approx(A.transmittance(2), 0.01), "A = 2 -> T = 0.01")
check(approx(A.transmittance(3), 0.001), "A = 3 -> T = 0.001")
check(approx(A.transmittance(0), 1.0), "A = 0 -> T = 1")
check(0 < A.transmittance(0.3) <= 1.0, "T ∈ ]0,1] pour A = 0.3")

# ── 4) COHÉRENCE CROISÉE inverse A = −log₁₀(T) (anti-circulaire) ──
for a in (0.0, 0.5, 1.0, 2.0, 4.0):
    t = A.transmittance(a)
    check(approx(-math.log10(t), a, tol=1e-7), f"A = −log10(T) pour A = {a}")

# ── 5) CHROMATOGRAPHIE : Rf = ds/df ∈ ]0,1] ──
check(approx(A.facteur_retention_rf(2, 5), 0.4), "Rf = 2/5 = 0.4 (énoncé)")
check(approx(A.facteur_retention_rf(3, 4), 0.75), "Rf = 3/4 = 0.75")
check(approx(A.facteur_retention_rf(5, 5), 1.0), "Rf = 5/5 = 1 (front atteint)")
check(approx(A.facteur_retention_rf(1.2, 4.8), 0.25), "Rf = 1.2/4.8 = 0.25")

# ── 6) SOUNDNESS — domaine invalide -> ValueError ──
check(leve(A.absorbance, 0, 1, 1), "epsilon = 0 -> ValueError")
check(leve(A.absorbance, -1, 1, 1), "epsilon < 0 -> ValueError")
check(leve(A.absorbance, 1, 0, 1), "l = 0 -> ValueError")
check(leve(A.absorbance, 1, -2, 1), "l < 0 -> ValueError")
check(leve(A.absorbance, 1, 1, -0.1), "c < 0 -> ValueError")
check(leve(A.concentration_depuis_absorbance, -0.1, 1, 1), "A < 0 -> ValueError")
check(leve(A.concentration_depuis_absorbance, 1, 0, 1), "epsilon = 0 (conc) -> ValueError")
check(leve(A.concentration_depuis_absorbance, 1, 1, 0), "l = 0 (conc) -> ValueError")
check(leve(A.transmittance, -0.5), "A < 0 (transmittance) -> ValueError")
check(leve(A.facteur_retention_rf, 0, 5), "distance_solute = 0 -> ValueError")
check(leve(A.facteur_retention_rf, 2, 0), "distance_solvant = 0 -> ValueError")
check(leve(A.facteur_retention_rf, -1, 5), "distance_solute < 0 -> ValueError")
check(leve(A.facteur_retention_rf, 6, 5), "soluté > solvant -> ValueError")

# ── 7) SOUNDNESS — type non numérique / booléen -> ValueError ──
check(leve(A.absorbance, "1", 1, 1), "epsilon str -> ValueError")
check(leve(A.absorbance, None, 1, 1), "epsilon None -> ValueError")
check(leve(A.absorbance, True, 1, 1), "epsilon booléen -> ValueError")
check(leve(A.transmittance, float("nan")), "A NaN -> ValueError")
check(leve(A.transmittance, float("inf")), "A inf -> ValueError")
check(leve(A.facteur_retention_rf, 2, "5"), "distance_solvant str -> ValueError")

# ── 8) DÉTERMINISME ──
check(A.absorbance(123, 1.7, 0.0042) == A.absorbance(123, 1.7, 0.0042), "absorbance déterministe")
check(A.transmittance(1.23456) == A.transmittance(1.23456), "transmittance déterministe")
check(A.facteur_retention_rf(2, 5) == A.facteur_retention_rf(2, 5), "Rf déterministe")

print(f'\n=== valide_analyse_chimique : {ok}/{ok+ko} ===')
import sys
sys.exit(0 if ko == 0 else 1)
