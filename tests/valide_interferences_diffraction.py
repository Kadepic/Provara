"""
VALIDE interferences_diffraction.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (valeurs écrites EN DUR, jamais recalculées par la fonction testée) :
  • YOUNG (manuel de TP classique) : λ=500 nm, D=2 m, a=0.5 mm
        i = 500e-9 · 2 / 0.5e-3 = 2e-3 m = 2 mm   (calcul à la main : 1000e-9/0.5e-3 = 2e-3).
  • COHÉRENCE inter-formules : la frange brillante d'ordre 1 est en x = 1·λD/a = i — DEUX fonctions
    distinctes (position_frange_brillante vs interfrange_young) doivent donner la MÊME valeur.
  • RÉSEAU 600 traits/mm (d = 1 mm/600), λ=500 nm, ordre 1 : sin θ = mλ/d = 500e-9·600/1e-3 = 0.3
        θ = arcsin(0.3) ≈ 17.4576°  (valeur tabulée ; contre-vérifiée ici par le CHEMIN INVERSE
        sin(θ_rendu) ≈ 0.3, qui n'utilise pas arcsin). Ordre 4 : 4·0.3 = 1.2 > 1 -> ABSTENTION.
  • FENTE SIMPLE, cas EXACTS de trigonométrie (indépendants de toute formule d'optique) :
        a = 2λ, m=1 -> sin θ = 1/2 -> θ = 30° exactement (sin 30° = 1/2, valeur classique) ;
        a = λ,  m=1 -> sin θ = 1   -> θ = 90° (étalement rasant, cas limite connu).
  • RÉSEAU ordre 2 : sin θ = 0.6 -> θ ≈ 36.8699° (angle du triangle 3-4-5, valeur classique).

SOUNDNESS : λ/D/a/d ≤ 0, ordre non entier (float/bool/str), m=0 sur fente simple (maximum central),
|mλ/pas| > 1 (ordre inexistant), NaN/inf -> ValueError. DÉTERMINISME : double appel identique.

EXISTENCE DES FRANGES D'YOUNG (audit adverse) : la frange d'ordre m n'existe sur un écran que si
|m·λ/a| < 1 (|(m+½)·λ/a| < 1 pour une sombre) — au-delà sin θ est impossible, à 1 exactement le
rayon est RASANT (θ=90°, n'atteint jamais l'écran alors que la formule rendrait x fini = FAUX).
Contre-exemples de l'auditeur repris tels quels : brillante(2, 500e-9, 2.0, 800e-9) où m·λ/a = 1.25
et sombre(0, 500e-9, 1.0, 200e-9) où (m+½)·λ/a = 1.25 -> ValueError exigé (ratios calculés à la
main : 2·500/800 = 1.25 ; 0.5·500/200 = 1.25).
"""
import math

import interferences_diffraction as I

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
    """True ssi fn(*a) lève ValueError (abstention structurelle)."""
    try:
        fn(*a)
        return False
    except ValueError:
        return True


def proche(x, attendu, tol=1e-9):
    return x is not None and abs(x - attendu) <= tol


# Paramètres du TP d'Young de référence (ancre manuelle)
LAM = 500e-9   # 500 nm
D = 2.0        # 2 m
A = 0.5e-3     # 0.5 mm

# ── 1) ANCRE YOUNG : i = 2e-3 m, calculé À LA MAIN dans la docstring ──
check(proche(I.interfrange_young(LAM, D, A), 2e-3), "interfrange λ=500nm,D=2m,a=0.5mm = 2 mm (main)")
# Second jeu (He-Ne, TP classique) : λ=633 nm, D=1 m, a=1 mm -> i = 633e-9·1/1e-3 = 6.33e-4 m (main)
check(proche(I.interfrange_young(633e-9, 1.0, 1e-3), 6.33e-4), "interfrange He-Ne 633nm/1m/1mm = 0.633 mm")
# Proportionnalités physiques (pas de valeur recalculée : rapports exacts attendus en dur)
check(proche(I.interfrange_young(LAM, 2 * D, A), 4e-3), "i double si D double (4 mm)")
check(proche(I.interfrange_young(LAM, D, 2 * A), 1e-3), "i moitié si a double (1 mm)")

# ── 2) FRANGES BRILLANTES x = mλD/a (valeurs en dur : multiples de 2 mm) ──
check(proche(I.position_frange_brillante(0, LAM, D, A), 0.0), "brillante m=0 : frange centrale x=0")
check(proche(I.position_frange_brillante(1, LAM, D, A), 2e-3), "brillante m=1 : x=2 mm (main)")
check(proche(I.position_frange_brillante(2, LAM, D, A), 4e-3), "brillante m=2 : x=4 mm")
check(proche(I.position_frange_brillante(3, LAM, D, A), 6e-3), "brillante m=3 : x=6 mm")
check(proche(I.position_frange_brillante(-1, LAM, D, A), -2e-3), "brillante m=-1 : x=-2 mm (symétrie)")

# ── 3) FRANGES SOMBRES x = (m+½)λD/a (valeurs en dur : demi-entiers de 2 mm) ──
check(proche(I.position_frange_sombre(0, LAM, D, A), 1e-3), "sombre m=0 : x=1 mm = i/2 (main)")
check(proche(I.position_frange_sombre(1, LAM, D, A), 3e-3), "sombre m=1 : x=3 mm")
check(proche(I.position_frange_sombre(-1, LAM, D, A), -1e-3), "sombre m=-1 : x=-1 mm")

# ── 4) COHÉRENCE INTER-FORMULES (deux chemins de code distincts, même physique) ──
check(proche(I.position_frange_brillante(1, LAM, D, A), I.interfrange_young(LAM, D, A)),
      "COHÉRENCE : brillante d'ordre 1 = interfrange (x=i)")
check(proche(I.position_frange_brillante(2, LAM, D, A) - I.position_frange_brillante(1, LAM, D, A),
             I.interfrange_young(LAM, D, A)),
      "COHÉRENCE : écart entre brillantes consécutives = i")
check(proche(I.position_frange_sombre(0, LAM, D, A) * 2.0, I.interfrange_young(LAM, D, A)),
      "COHÉRENCE : première sombre = i/2")
# La sombre m est à mi-chemin entre les brillantes m et m+1
check(proche(I.position_frange_sombre(1, LAM, D, A),
             (I.position_frange_brillante(1, LAM, D, A) + I.position_frange_brillante(2, LAM, D, A)) / 2.0),
      "COHÉRENCE : sombre m=1 à mi-chemin des brillantes 1 et 2")

# ── 4bis) EXISTENCE DES FRANGES D'YOUNG — abstention sur frange inexistante ou rasante ──
# Contre-exemple AUDITEUR : m=2, λ=500 nm, a=800 nm -> m·λ/a = 1000/800 = 1.25 > 1 (main) -> ValueError
check(leve(I.position_frange_brillante, 2, 500e-9, 2.0, 800e-9),
      "brillante m=2, λ/a tel que m·λ/a=1.25>1 : frange inexistante -> ValueError (auditeur)")
check(leve(I.position_frange_brillante, -2, 500e-9, 2.0, 800e-9),
      "brillante m=-2 symétrique : |m·λ/a|=1.25>1 -> ValueError")
# Contre-exemple AUDITEUR : sombre m=0, λ=500 nm, a=200 nm -> (0+½)·500/200 = 1.25 > 1 (main)
check(leve(I.position_frange_sombre, 0, 500e-9, 1.0, 200e-9),
      "sombre m=0, (m+½)λ/a=1.25>1 : frange inexistante -> ValueError (auditeur)")
check(leve(I.position_frange_sombre, -1, 500e-9, 1.0, 200e-9),
      "sombre m=-1 : |(m+½)λ/a|=1.25>1 -> ValueError")
# Cas RASANT sin θ = 1 exactement : la position serait finie mais le rayon n'atteint JAMAIS l'écran
check(leve(I.position_frange_brillante, 1, 500e-9, 2.0, 500e-9),
      "brillante m=1, a=λ : sinθ=1 rasant, aucune position sur écran -> ValueError")
check(leve(I.position_frange_sombre, 0, 500e-9, 1.0, 250e-9),
      "sombre m=0, a=2λ·½ : (m+½)λ/a=1 rasant -> ValueError")
# Interfrange : λ/a ≥ 1 -> aucune frange latérale n'existe, l'interfrange n'est pas observable
check(leve(I.interfrange_young, 500e-9, 1.0, 400e-9), "interfrange λ/a=1.25>1 -> ValueError")
check(leve(I.interfrange_young, 500e-9, 1.0, 500e-9), "interfrange λ/a=1 (rasant) -> ValueError")
# La frange CENTRALE (m=0) existe TOUJOURS, même quand λ > a (sin θ = 0)
check(proche(I.position_frange_brillante(0, 500e-9, 2.0, 200e-9), 0.0),
      "brillante m=0 existe toujours (x=0), même à λ>a")
# Juste EN DESSOUS de la limite : sin θ < 1, la frange existe, position rendue (imprécise loin de
# l'axe — réserve petits angles assumée — mais EXISTANTE). Calculs à la main dans les labels.
check(proche(I.position_frange_brillante(1, 500e-9, 1.0, 800e-9), 0.625),
      "brillante m=1, m·λ/a=0.625<1 : existe, x=0.625 m (main : 500/800)")
check(proche(I.position_frange_sombre(0, 500e-9, 1.0, 800e-9), 0.3125),
      "sombre m=0, (m+½)λ/a=0.3125<1 : existe, x=0.3125 m (main : 250/800)")

# ── 5) RÉSEAU 600 traits/mm : d = 1 mm / 600 ──
D_RESEAU = 1e-3 / 600.0
theta1 = I.angle_reseau(D_RESEAU, 1, LAM)
check(proche(theta1, 17.4576, tol=1e-3), "réseau 600 tr/mm, ordre 1 : θ ≈ 17.4576° (arcsin 0.3, tabulé)")
# Contre-vérification par le CHEMIN INVERSE (sin, pas arcsin) : sin(θ) doit redonner mλ/d = 0.3
check(proche(math.sin(math.radians(theta1)), 0.3, tol=1e-9), "réseau ordre 1 : sin(θ rendu) = 0.3 (inverse)")
theta2 = I.angle_reseau(D_RESEAU, 2, LAM)
check(proche(theta2, 36.8699, tol=1e-3), "réseau ordre 2 : θ ≈ 36.8699° (sin=0.6, angle du 3-4-5)")
check(proche(math.sin(math.radians(theta2)), 0.6, tol=1e-9), "réseau ordre 2 : sin(θ rendu) = 0.6 (inverse)")
check(proche(I.angle_reseau(D_RESEAU, 0, LAM), 0.0), "réseau ordre 0 : θ=0 (axe optique)")
check(proche(I.angle_reseau(D_RESEAU, -1, LAM), -17.4576, tol=1e-3), "réseau ordre -1 : θ ≈ -17.4576° (symétrie)")
# Cas limite |sinθ| = 1 exactement : rasant à 90°, PAS une abstention (sin=1 est atteignable)
check(proche(I.angle_reseau(1e-6, 2, 500e-9), 90.0), "réseau sinθ=1 exactement : θ=90° (rasant)")

# ── 6) ABSTENTION RÉSEAU : ordre 4 -> 4·0.3 = 1.2 > 1 -> ValueError (ancre d'abstention imposée) ──
check(leve(I.angle_reseau, D_RESEAU, 4, LAM), "réseau ordre 4 : |mλ/d|=1.2>1 -> ValueError")
check(leve(I.angle_reseau, D_RESEAU, -4, LAM), "réseau ordre -4 : |mλ/d|=1.2>1 -> ValueError")

# ── 7) FENTE SIMPLE : cas trigonométriques EXACTS ──
# a = 2λ -> sinθ = 1/2 -> θ = 30° exactement (sin 30° = 1/2, trigonométrie classique)
check(proche(I.angle_minimum_fente(1000e-9, 1, 500e-9), 30.0), "fente a=2λ, m=1 : θ=30° (sin=1/2 exact)")
# a = λ -> sinθ = 1 -> θ = 90° (étalement rasant, cas limite connu)
check(proche(I.angle_minimum_fente(500e-9, 1, 500e-9), 90.0), "fente a=λ, m=1 : θ=90° (rasant)")
check(proche(I.angle_minimum_fente(1000e-9, -1, 500e-9), -30.0), "fente m=-1 : θ=-30° (symétrie)")
# a = 4λ, m=2 -> sinθ = 1/2 -> 30° aussi (deux chemins vers le même sinus)
check(proche(I.angle_minimum_fente(2000e-9, 2, 500e-9), 30.0), "fente a=4λ, m=2 : θ=30°")
# Contre-vérification chemin inverse : a=0.1 mm, λ=500 nm, m=1 -> sin(θ rendu) = 0.005
th_f = I.angle_minimum_fente(1e-4, 1, 500e-9)
check(proche(math.sin(math.radians(th_f)), 0.005, tol=1e-9), "fente 0.1mm : sin(θ rendu)=0.005 (inverse)")
check(0.0 < th_f < 1.0, "fente 0.1mm : petit angle (< 1°), ordre de grandeur physique")

# ── 8) ABSTENTIONS FENTE SIMPLE ──
check(leve(I.angle_minimum_fente, 1000e-9, 0, 500e-9), "fente m=0 : maximum central -> ValueError")
check(leve(I.angle_minimum_fente, 1000e-9, 3, 500e-9), "fente m=3, a=2λ : |mλ/a|=1.5>1 -> ValueError")
check(leve(I.angle_minimum_fente, 400e-9, 1, 500e-9), "fente a<λ : |λ/a|>1 -> ValueError (pas de minimum)")

# ── 9) SOUNDNESS — grandeurs positives (zéro / négatif) ──
check(leve(I.interfrange_young, 0.0, D, A), "λ=0 -> ValueError")
check(leve(I.interfrange_young, -500e-9, D, A), "λ<0 -> ValueError")
check(leve(I.interfrange_young, LAM, 0.0, A), "D=0 -> ValueError")
check(leve(I.interfrange_young, LAM, D, -0.5e-3), "a<0 -> ValueError")
check(leve(I.position_frange_brillante, 1, LAM, -2.0, A), "brillante D<0 -> ValueError")
check(leve(I.position_frange_sombre, 0, LAM, D, 0.0), "sombre a=0 -> ValueError")
check(leve(I.angle_reseau, 0.0, 1, LAM), "réseau d=0 -> ValueError")
check(leve(I.angle_reseau, -1e-6, 1, LAM), "réseau d<0 -> ValueError")
check(leve(I.angle_minimum_fente, 0.0, 1, LAM), "fente a=0 -> ValueError")

# ── 10) SOUNDNESS — ordres non entiers (float refusé, même 1.0) / bool / str ──
check(leve(I.position_frange_brillante, 1.0, LAM, D, A), "brillante m=1.0 (float) -> ValueError")
check(leve(I.position_frange_sombre, 0.5, LAM, D, A), "sombre m=0.5 -> ValueError")
check(leve(I.angle_reseau, D_RESEAU, 1.0, LAM), "réseau m float -> ValueError")
check(leve(I.angle_minimum_fente, 1000e-9, 1.5, 500e-9), "fente m=1.5 -> ValueError")
check(leve(I.position_frange_brillante, True, LAM, D, A), "brillante m=True -> ValueError")
check(leve(I.angle_reseau, D_RESEAU, "1", LAM), "réseau m str -> ValueError")

# ── 11) SOUNDNESS — bool / str / NaN / inf sur les grandeurs ──
check(leve(I.interfrange_young, True, D, A), "λ bool -> ValueError")
check(leve(I.interfrange_young, "500e-9", D, A), "λ str -> ValueError")
check(leve(I.interfrange_young, float("nan"), D, A), "λ NaN -> ValueError")
check(leve(I.interfrange_young, LAM, float("inf"), A), "D inf -> ValueError")
check(leve(I.interfrange_young, LAM, D, float("-inf")), "a -inf -> ValueError")
check(leve(I.angle_reseau, float("nan"), 1, LAM), "réseau d NaN -> ValueError")
check(leve(I.angle_reseau, D_RESEAU, 1, float("inf")), "réseau λ inf -> ValueError")
check(leve(I.angle_minimum_fente, float("inf"), 1, LAM), "fente a inf -> ValueError")
check(leve(I.angle_minimum_fente, 1000e-9, 1, True), "fente λ bool -> ValueError")
check(leve(I.position_frange_sombre, 1, LAM, float("nan"), A), "sombre D NaN -> ValueError")

# ── 12) DÉTERMINISME (double appel, égalité stricte) ──
check(I.interfrange_young(LAM, D, A) == I.interfrange_young(LAM, D, A), "déterminisme interfrange")
check(I.position_frange_brillante(2, LAM, D, A) == I.position_frange_brillante(2, LAM, D, A),
      "déterminisme brillante")
check(I.position_frange_sombre(1, LAM, D, A) == I.position_frange_sombre(1, LAM, D, A),
      "déterminisme sombre")
check(I.angle_reseau(D_RESEAU, 1, LAM) == I.angle_reseau(D_RESEAU, 1, LAM), "déterminisme réseau")
check(I.angle_minimum_fente(1000e-9, 1, 500e-9) == I.angle_minimum_fente(1000e-9, 1, 500e-9),
      "déterminisme fente")

print(f"\n=== valide_interferences_diffraction : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
