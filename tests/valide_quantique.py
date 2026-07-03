"""
VALIDE quantique.py — held-out ADVERSE. Exactitude des relations quantiques (ancrées sur des valeurs PHYSIQUES
CONNUES, non recalculées par la même expression : h en eV·s = 4.135667696e-15, ħ = 1.054571817e-34, énergie de
l'état fondamental d'un électron dans un puits de 1 nm ≈ 0.376 eV, λ_de Broglie d'un objet de p = 1 kg·m/s = h…)
+ SOUNDNESS (f≤0, p≤0, n<1 non entier, L≤0, m≤0, type/bool -> ValueError, jamais un faux) + déterminisme.
Aucun de ces cas n'est codé en dur dans quantique.py.
"""
import math

import quantique as Q

ok = 0
ko = 0

# constantes de référence INDÉPENDANTES (sources externes, pas tirées de quantique.py)
E_CHARGE = 1.602_176_634e-19        # C — EXACTE (SI 2019), pour convertir J -> eV
H_EN_EV_S = 4.135_667_696e-15       # eV·s — constante de Planck en eV·s (CODATA, connue)
HBAR_REF = 1.054_571_817e-34        # J·s — constante de Planck réduite (CODATA, connue)
C = 299_792_458.0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def approx(val, attendu, rel=1e-6):
    return val is not None and abs(val - attendu) <= rel * abs(attendu) + 1e-40


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) energie_photon : ANCRES EXTERNES (h en eV·s connue, non recalculée) ──
check(approx(Q.energie_photon(1.0), 6.62607015e-34, rel=1e-12), "E = h·1 = h = 6.62607015e-34 J")
# E(1 PHz) / e doit redonner h en eV·s = 4.135667696 eV (constante indépendante)
check(approx(Q.energie_photon(1e15) / E_CHARGE, H_EN_EV_S * 1e15, rel=1e-6),
      "E(1 PHz)/e = 4.135668 eV (h en eV·s connu)")
check(approx(Q.energie_photon(5e14), 3.313035075e-19, rel=1e-9), "E = h·5e14 Hz")
# linéarité en ν (mécanisme E ∝ f) : E(2f) = 2·E(f)
check(approx(Q.energie_photon(2e14), 2 * Q.energie_photon(1e14), rel=1e-9), "E(2ν) = 2·E(ν) (linéarité)")

# ── 2) longueur_onde_broglie : ANCRES EXTERNES ──
# objet macroscopique p = 1 kg·m/s -> λ = h (≈ h mètres, valeur de manuel)
check(approx(Q.longueur_onde_broglie(1.0), 6.62607015e-34, rel=1e-12), "p=1 kg·m/s -> λ = h")
# λ = h/h = 1 m exactement (cas pivot)
check(approx(Q.longueur_onde_broglie(6.62607015e-34), 1.0, rel=1e-9), "p = h -> λ = 1 m")
# cohérence onde-corpuscule : pour un photon, p = h·f/c et λ = h/p doit égaler c/f (longueur d'onde indépendante)
f_ph = 5e14
p_ph = 6.62607015e-34 * f_ph / C
check(approx(Q.longueur_onde_broglie(p_ph), C / f_ph, rel=1e-9), "λ_deBroglie(p_photon) = c/f (cohérence)")
# inverse en p : λ(2p) = λ(p)/2
check(approx(Q.longueur_onde_broglie(2.0), Q.longueur_onde_broglie(1.0) / 2, rel=1e-9), "λ ∝ 1/p")

# ── 3) niveaux_puits_infini : ANCRE EXTERNE (électron dans 1 nm ≈ 0.376 eV) ──
E1 = Q.niveaux_puits_infini(1, 1e-9, 9.109e-31)
check(approx(E1 / E_CHARGE, 0.3760, rel=2e-3), "E₁ électron puits 1 nm ≈ 0.376 eV (manuel)")
# quantification en n² : E₂ = 4·E₁, E₃ = 9·E₁
check(approx(Q.niveaux_puits_infini(2, 1e-9, 9.109e-31), 4 * E1, rel=1e-9), "E₂ = 4·E₁ (∝ n²)")
check(approx(Q.niveaux_puits_infini(3, 1e-9, 9.109e-31), 9 * E1, rel=1e-9), "E₃ = 9·E₁ (∝ n²)")
# proton (≈1836× plus lourd) dans le même puits : énergie ≈ 1836× plus faible (∝ 1/m)
check(approx(Q.niveaux_puits_infini(1, 1e-9, 9.109e-31 * 1836.0), E1 / 1836.0, rel=1e-9), "E ∝ 1/m")

# ── 4) borne_heisenberg : ANCRE EXTERNE (ħ connu) ──
check(approx(Q.borne_heisenberg(1.0), HBAR_REF / 2.0, rel=1e-6), "Δp_min(Δx=1) = ħ/2 (ħ connu)")
# produit Δp·Δx = ħ/2 constant (saturation de l'inégalité)
check(approx(Q.borne_heisenberg(2e-9) * 2e-9, HBAR_REF / 2.0, rel=1e-6), "Δp·Δx = ħ/2 (constant)")
check(approx(Q.borne_heisenberg(1.0) * 1.0, Q.borne_heisenberg(5.0) * 5.0, rel=1e-9), "Δp·Δx invariant")
# valeur de la constante réduite exposée ≈ ħ connu
check(approx(Q.HBAR, HBAR_REF, rel=1e-6), "ħ exposée = h/2π ≈ 1.054571817e-34")

# ── 5) SOUNDNESS — domaine invalide -> ValueError (jamais un nombre faux) ──
check(leve(Q.energie_photon, 0), "f = 0 -> ValueError")
check(leve(Q.energie_photon, -1e14), "f < 0 -> ValueError")
check(leve(Q.longueur_onde_broglie, 0), "p = 0 -> ValueError")
check(leve(Q.longueur_onde_broglie, -1.0), "p < 0 -> ValueError")
check(leve(Q.borne_heisenberg, 0), "Δx = 0 -> ValueError")
check(leve(Q.borne_heisenberg, -1e-9), "Δx < 0 -> ValueError")
check(leve(Q.niveaux_puits_infini, 0, 1e-9, 9.109e-31), "n = 0 (< 1) -> ValueError")
check(leve(Q.niveaux_puits_infini, -1, 1e-9, 9.109e-31), "n < 1 -> ValueError")
check(leve(Q.niveaux_puits_infini, 1, 0, 9.109e-31), "L = 0 -> ValueError")
check(leve(Q.niveaux_puits_infini, 1, -1e-9, 9.109e-31), "L < 0 -> ValueError")
check(leve(Q.niveaux_puits_infini, 1, 1e-9, 0), "m = 0 -> ValueError")
check(leve(Q.niveaux_puits_infini, 1, 1e-9, -9.109e-31), "m < 0 -> ValueError")

# ── 6) SOUNDNESS — quantification : n non entier -> ValueError (un niveau est quantifié) ──
check(leve(Q.niveaux_puits_infini, 1.5, 1e-9, 9.109e-31), "n = 1.5 non entier -> ValueError")
check(leve(Q.niveaux_puits_infini, 2.0, 1e-9, 9.109e-31), "n = 2.0 float -> ValueError (entier requis)")

# ── 7) SOUNDNESS — types invalides (bool / str / inf / nan) -> ValueError ──
check(leve(Q.energie_photon, True), "bool n'est pas un réel -> ValueError")
check(leve(Q.energie_photon, "1e14"), "str -> ValueError")
check(leve(Q.energie_photon, float("inf")), "inf -> ValueError")
check(leve(Q.energie_photon, float("nan")), "nan -> ValueError")
check(leve(Q.niveaux_puits_infini, True, 1e-9, 9.109e-31), "n bool -> ValueError")
check(leve(Q.longueur_onde_broglie, None), "None -> ValueError")

# ── 8) DÉTERMINISME ──
check(Q.energie_photon(3e14) == Q.energie_photon(3e14), "déterminisme energie_photon")
check(Q.niveaux_puits_infini(2, 1e-9, 9.109e-31) == Q.niveaux_puits_infini(2, 1e-9, 9.109e-31),
      "déterminisme niveaux_puits_infini")
check(Q.borne_heisenberg(1e-10) == Q.borne_heisenberg(1e-10), "déterminisme borne_heisenberg")

print(f"\n=== valide_quantique : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
