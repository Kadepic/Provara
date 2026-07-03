"""VALIDE rayonnement_thermique.py — held-out ADVERSE, FAUX=0. Ancres EXTERNES connues du corps noir (pics du fond
diffus cosmologique 1.063 mm / 160.2 GHz, pic solaire 501 nm, émittances 459 W·m⁻² à 300 K et 6.32e7 W·m⁻² au
Soleil) NON recalculées par la même expression + SOUNDNESS : entrée invalide (T≤0, λ≤0, bool, str) -> ValueError.
"""
import rayonnement_thermique as R

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


def proche(x, attendu, rel=1e-2):
    return abs(x - attendu) <= rel * abs(attendu)


# ── 1) LOI DE WIEN (longueur d'onde) — ancres externes ──
# CMB : T = 2.725 K -> pic micro-ondes ~ 1.063 mm (valeur de référence du fond diffus cosmologique).
check(proche(R.longueur_onde_max(2.725), 1.063e-3, rel=1e-2), "Wien CMB 2.725 K -> λ_max ≈ 1.063 mm (tol 1%)")
# Soleil : T = 5778 K -> pic dans le visible ~ 501 nm (vert-jaune).
check(proche(R.longueur_onde_max(5778), 501e-9, rel=1e-2), "Wien Soleil 5778 K -> λ_max ≈ 501 nm (tol 1%)")
# Le pic est inversement proportionnel à T : doubler T -> moitié de λ.
check(proche(R.longueur_onde_max(5450) * 2, R.longueur_onde_max(2725), rel=1e-9), "Wien : λ(T) = 2·λ(2T)")

# ── 2) INVERSE — température depuis le pic ──
# Pic à 501 nm -> ~5780 K (ordre du Soleil). Ancre : T·λ = b doit redonner ~5784 K.
check(proche(R.temperature_depuis_pic(501e-9), 5784.0, rel=1e-3), "T depuis 501 nm ≈ 5784 K")
# Cohérence inverse (sur valeur arrondie) : T -> λ -> T à mieux que 1e-6 relatif.
check(proche(R.temperature_depuis_pic(R.longueur_onde_max(3000.0)), 3000.0, rel=1e-6), "Wien inverse cohérent")

# ── 3) LOI DE WIEN (fréquence) — ancre externe ──
# CMB : pic en fréquence ~ 160.2 GHz (valeur mesurée du fond diffus, distincte du pic en longueur d'onde).
check(proche(R.frequence_max(2.725), 160.2e9, rel=1e-2), "Wien fréq CMB 2.725 K -> ν_max ≈ 160.2 GHz (tol 1%)")
# Le pic en fréquence et le pic en longueur d'onde ne coïncident PAS (λ_max·ν_max ≠ c) :
check(R.longueur_onde_max(2.725) * R.frequence_max(2.725) < 299_792_458.0 * 0.9,
      "λ_max·ν_max ≠ c (subtilité corps noir)")

# ── 4) LOI DE STEFAN-BOLTZMANN — ancres externes ──
# Corps noir à 300 K : ~459 W·m⁻² (valeur de référence en thermique du bâtiment).
check(proche(R.loi_stefan_boltzmann(300), 459.3, rel=1e-3), "Stefan-Boltzmann 300 K ≈ 459 W·m⁻²")
# Surface solaire (5778 K) : ~6.32e7 W·m⁻².
check(proche(R.loi_stefan_boltzmann(5778), 6.32e7, rel=1e-2), "Stefan-Boltzmann Soleil 5778 K ≈ 6.32e7 W·m⁻²")
# À T = 100 K : σ·100⁴ = σ·1e8 = σ·10⁸ -> 5.6704 W·m⁻² (lecture directe de la constante, ancre propre).
check(proche(R.loi_stefan_boltzmann(100), 5.670374419, rel=1e-6), "Stefan-Boltzmann 100 K = σ·10⁸ ≈ 5.6704 W·m⁻²")
# Loi en T⁴ : multiplier T par 2 multiplie M par 16.
check(proche(R.loi_stefan_boltzmann(600), 16 * R.loi_stefan_boltzmann(300), rel=1e-9), "M(2T) = 16·M(T)")
# Puissance = émittance × surface (A = 1 m² redonne l'émittance ; A = 2 m² la double).
check(proche(R.puissance_rayonnee(300, 2.0), 2 * R.loi_stefan_boltzmann(300), rel=1e-9), "P = σT⁴·A (A=2)")

# ── 5) SOUNDNESS — entrées invalides -> ValueError (jamais un faux) ──
check(leve(R.longueur_onde_max, 0), "T = 0 K (Wien) -> ValueError")
check(leve(R.longueur_onde_max, -5), "T < 0 K (Wien) -> ValueError")
check(leve(R.longueur_onde_max, True), "bool (Wien) -> ValueError")
check(leve(R.longueur_onde_max, "2.725"), "str (Wien) -> ValueError")
check(leve(R.frequence_max, 0), "T = 0 K (fréq) -> ValueError")
check(leve(R.frequence_max, -1), "T < 0 K (fréq) -> ValueError")
check(leve(R.loi_stefan_boltzmann, 0), "T = 0 K (Stefan) -> ValueError")
check(leve(R.loi_stefan_boltzmann, -300), "T < 0 K (Stefan) -> ValueError")
check(leve(R.loi_stefan_boltzmann, True), "bool (Stefan) -> ValueError")
check(leve(R.temperature_depuis_pic, 0), "λ = 0 m -> ValueError")
check(leve(R.temperature_depuis_pic, -1e-6), "λ < 0 m -> ValueError")
check(leve(R.temperature_depuis_pic, None), "None (inverse) -> ValueError")
check(leve(R.puissance_rayonnee, 300, 0), "surface = 0 m² -> ValueError")
check(leve(R.puissance_rayonnee, 300, -2), "surface < 0 m² -> ValueError")
check(leve(R.puissance_rayonnee, -300, 2), "T < 0 K (puissance) -> ValueError")

# ── 6) DÉTERMINISME ──
check(R.longueur_onde_max(2.725) == R.longueur_onde_max(2.725), "déterminisme Wien")
check(R.loi_stefan_boltzmann(5778) == R.loi_stefan_boltzmann(5778), "déterminisme Stefan-Boltzmann")

print(f"\n=== valide_rayonnement_thermique : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
