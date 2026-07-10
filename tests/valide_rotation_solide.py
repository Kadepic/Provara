"""
VALIDE rotation_solide.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (valeurs écrites EN DUR, calculées À LA MAIN, jamais recalculées par la
fonction testée) :
  • Disque m=2 kg, r=0.5 m : I = ½·2·0.25 = 0.25 kg·m² (à la main).
  • Sphère pleine m=1, r=1 : I = 2/5 = 0.4 kg·m² (coefficient classique 2/5).
  • Patineuse : I₁=5, ω₁=2, I₂=1 -> ω₂ = 5·2/1 = 10 rad/s (à la main) ; et L = I·ω vaut 10 kg·m²/s dans les
    DEUX états (L₁ = 5·2, L₂ = 1·10), calculé par moment_cinetique SÉPARÉMENT de la conservation.
  • HUYGENS NON CIRCULAIRE : deux entrées de catalogue INDÉPENDANTES doivent coïncider —
    I_tige_extremite = I_tige_centre + m·(L/2)² = (1/12)mL² + (1/4)mL² = (1/3)mL². Pour m=3, L=2 :
    centre = 1.0, extrémité = 4.0, Huygens(1.0, 3, 1) = 4.0 (tous trois calculés à la main).
  • Anneau m=2, r=3 -> 18 ; masse ponctuelle m=1.5, r=2 -> 6 ; sphère creuse m=3, r=1 -> 2 ;
    cylindre m=4, r=0.5 -> 0.5 ; tige centre m=12, L=1 -> 1 (à la main, coefficients classiques).
  • τ = I·α : I=2, α=3 -> 6 N·m ; E = ½·I·ω² : I=0.25, ω=4 -> 2 J (à la main).

SOUNDNESS : forme hors catalogue, masse/dimension/I ≤ 0, I₂ = 0, d < 0, bool/str/NaN/inf -> ValueError.
GARDE DE SORTIE : overflow (résultat ou produit intermédiaire -> ±inf, y compris débordement à l'arrondi
10 chiffres) et underflow (0.0 alors que le résultat mathématique est non nul) -> ValueError ; les zéros
EXACTS (ω = 0 ou α = 0) restent légaux ; les valeurs extrêmes REPRÉSENTABLES sont rendues (ancres à la main).
"""
import math

import rotation_solide as RS

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


# ── 1) ANCRES IMPOSÉES — moment d'inertie (valeurs à la main) ──
check(proche(RS.moment_inertie("disque_plein", 2.0, 0.5), 0.25), "disque m=2 r=0.5 -> 0.25 (½·2·0.25 à la main)")
check(proche(RS.moment_inertie("sphere_pleine", 1.0, 1.0), 0.4), "sphère pleine m=1 r=1 -> 0.4 (2/5)")

# ── 2) CATALOGUE — chaque forme contre une valeur à la main ──
check(proche(RS.moment_inertie("masse_ponctuelle", 1.5, 2.0), 6.0), "ponctuelle m=1.5 r=2 -> 1.5·4 = 6")
check(proche(RS.moment_inertie("cylindre_plein", 4.0, 0.5), 0.5), "cylindre m=4 r=0.5 -> ½·4·0.25 = 0.5")
check(proche(RS.moment_inertie("sphere_creuse", 3.0, 1.0), 2.0), "sphère creuse m=3 r=1 -> (2/3)·3 = 2")
check(proche(RS.moment_inertie("tige_axe_centre", 12.0, 1.0), 1.0), "tige centre m=12 L=1 -> 12/12 = 1")
check(proche(RS.moment_inertie("tige_axe_extremite", 3.0, 1.0), 1.0), "tige extrémité m=3 L=1 -> 3/3 = 1")
check(proche(RS.moment_inertie("anneau", 2.0, 3.0), 18.0), "anneau m=2 r=3 -> 2·9 = 18")
# ordre physique : à m,r égaux, creuse (2/3) > pleine (2/5) — la masse d'une coque est plus loin de l'axe
check(RS.moment_inertie("sphere_creuse", 1.0, 1.0) > RS.moment_inertie("sphere_pleine", 1.0, 1.0),
      "sphère creuse > sphère pleine (masse plus loin de l'axe)")
# ordre physique : anneau (1) > disque (½) à m,r égaux
check(RS.moment_inertie("anneau", 1.0, 1.0) > RS.moment_inertie("disque_plein", 1.0, 1.0),
      "anneau > disque plein à m,r égaux")

# ── 3) ANCRE IMPOSÉE — patineuse (conservation + L identique dans les DEUX états) ──
w2 = RS.conservation_moment_cinetique(5.0, 2.0, 1.0)
check(proche(w2, 10.0), "patineuse I1=5 w1=2 I2=1 -> w2 = 10 rad/s (5·2/1 à la main)")
L1 = RS.moment_cinetique(5.0, 2.0)      # état 1, calculé indépendamment de la conservation
L2 = RS.moment_cinetique(1.0, 10.0)     # état 2, avec le w2 attendu EN DUR (10), pas w2 recalculé
check(proche(L1, 10.0), "L1 = I1·w1 = 5·2 = 10 kg·m²/s (à la main)")
check(proche(L2, 10.0), "L2 = I2·w2 = 1·10 = 10 kg·m²/s (à la main)")
check(proche(L1, L2), "conservation : L1 = L2 dans les deux états")
# énergie de la patineuse : E1 = ½·5·4 = 10 J, E2 = ½·1·100 = 50 J (le travail musculaire l'augmente)
check(proche(RS.energie_rotation(5.0, 2.0), 10.0), "E1 patineuse = ½·5·4 = 10 J (à la main)")
check(proche(RS.energie_rotation(1.0, 10.0), 50.0), "E2 patineuse = ½·1·100 = 50 J (à la main)")
# autre conservation à la main : I1=2, w1=3, I2=6 -> w2 = 1
check(proche(RS.conservation_moment_cinetique(2.0, 3.0, 6.0), 1.0), "I1=2 w1=3 I2=6 -> w2 = 1")
# ω négatif (sens de rotation) conservé : I1=4, w1=-2, I2=8 -> w2 = -1
check(proche(RS.conservation_moment_cinetique(4.0, -2.0, 8.0), -1.0), "w1<0 -> w2 = -1 (sens conservé)")

# ── 4) HUYGENS-STEINER — ANCRE NON CIRCULAIRE (deux entrées de catalogue indépendantes coïncident) ──
# m=3, L=2 : centre = (1/12)·3·4 = 1.0 ; extrémité = (1/3)·3·4 = 4.0 ; Huygens(1.0, 3, L/2=1) = 1+3·1 = 4.0
I_centre = RS.moment_inertie("tige_axe_centre", 3.0, 2.0)
I_bout = RS.moment_inertie("tige_axe_extremite", 3.0, 2.0)
check(proche(I_centre, 1.0), "tige centre m=3 L=2 -> 1.0 ((1/12)·3·4 à la main)")
check(proche(I_bout, 4.0), "tige extrémité m=3 L=2 -> 4.0 ((1/3)·3·4 à la main)")
check(proche(RS.inertie_axe_parallele(I_centre, 3.0, 1.0), 4.0),
      "Huygens : I_centre + m(L/2)² = 1 + 3·1 = 4 = I_extrémité (entrées de catalogue indépendantes)")
check(proche(RS.inertie_axe_parallele(I_centre, 3.0, 1.0), I_bout),
      "Huygens recoupe le catalogue : centre + m·d² = extrémité")
# second cas indépendant : m=6, L=1 : centre = 0.5, extrémité = 2.0, Huygens(0.5, 6, 0.5) = 0.5 + 6·0.25 = 2.0
check(proche(RS.inertie_axe_parallele(0.5, 6.0, 0.5), 2.0), "Huygens m=6 L=1 : 0.5 + 6·0.25 = 2.0 (à la main)")
check(proche(RS.moment_inertie("tige_axe_extremite", 6.0, 1.0), 2.0), "tige extrémité m=6 L=1 -> 2.0 (catalogue)")
# d = 0 : même axe, I inchangé
check(proche(RS.inertie_axe_parallele(0.7, 2.0, 0.0), 0.7), "Huygens d=0 -> I_centre inchangé")
# Huygens à la main hors tige : disque m=2 r=0.5 (I=0.25 ancré plus haut) décalé de d=1 -> 0.25 + 2·1 = 2.25
check(proche(RS.inertie_axe_parallele(0.25, 2.0, 1.0), 2.25), "Huygens disque décalé d=1 -> 2.25 (à la main)")

# ── 5) COUPLE ET ÉNERGIE (valeurs à la main) ──
check(proche(RS.couple(2.0, 3.0), 6.0), "τ = 2·3 = 6 N·m (à la main)")
check(proche(RS.couple(0.25, -4.0), -1.0), "τ = 0.25·(−4) = −1 N·m (freinage, signe respecté)")
check(proche(RS.energie_rotation(0.25, 4.0), 2.0), "E = ½·0.25·16 = 2 J (à la main)")
check(proche(RS.energie_rotation(0.25, -4.0), 2.0), "E(−ω) = E(ω) : l'énergie ignore le sens")
check(proche(RS.moment_cinetique(0.25, -4.0), -1.0), "L = 0.25·(−4) = −1 (signe respecté)")
check(proche(RS.moment_cinetique(3.0, 0.0), 0.0), "ω=0 -> L=0 (solide immobile)")

# ── 6) SOUNDNESS — forme hors catalogue / type de forme ──
check(leve(RS.moment_inertie, "cube_plein", 1.0, 1.0), "forme hors catalogue -> ValueError")
check(leve(RS.moment_inertie, "tige", 1.0, 1.0), "forme ambiguë (axe non précisé) -> ValueError")
check(leve(RS.moment_inertie, 3, 1.0, 1.0), "forme non-str -> ValueError")
check(leve(RS.moment_inertie, "", 1.0, 1.0), "forme vide -> ValueError")

# ── 7) SOUNDNESS — masse / dimension ≤ 0 ──
check(leve(RS.moment_inertie, "disque_plein", 0.0, 1.0), "masse=0 -> ValueError")
check(leve(RS.moment_inertie, "disque_plein", -2.0, 1.0), "masse<0 -> ValueError")
check(leve(RS.moment_inertie, "disque_plein", 2.0, 0.0), "dimension=0 -> ValueError")
check(leve(RS.moment_inertie, "disque_plein", 2.0, -0.5), "dimension<0 -> ValueError")

# ── 8) SOUNDNESS — inerties ≤ 0 (dont I2=0 : division interdite) ──
check(leve(RS.conservation_moment_cinetique, 5.0, 2.0, 0.0), "I2=0 -> ValueError (jamais de division par 0)")
check(leve(RS.conservation_moment_cinetique, 5.0, 2.0, -1.0), "I2<0 -> ValueError")
check(leve(RS.conservation_moment_cinetique, 0.0, 2.0, 1.0), "I1=0 -> ValueError")
check(leve(RS.moment_cinetique, 0.0, 2.0), "L : I=0 -> ValueError")
check(leve(RS.moment_cinetique, -1.0, 2.0), "L : I<0 -> ValueError")
check(leve(RS.couple, 0.0, 3.0), "τ : I=0 -> ValueError")
check(leve(RS.energie_rotation, -0.5, 3.0), "E : I<0 -> ValueError")
check(leve(RS.inertie_axe_parallele, 0.0, 1.0, 1.0), "Huygens I_centre=0 -> ValueError")
check(leve(RS.inertie_axe_parallele, 1.0, 0.0, 1.0), "Huygens m=0 -> ValueError")
check(leve(RS.inertie_axe_parallele, 1.0, 1.0, -0.5), "Huygens d<0 -> ValueError")

# ── 9) SOUNDNESS — types invalides (bool / str / NaN / inf) ──
check(leve(RS.moment_inertie, "disque_plein", True, 1.0), "masse bool -> ValueError")
check(leve(RS.moment_inertie, "disque_plein", 1.0, True), "dimension bool -> ValueError")
check(leve(RS.moment_inertie, "disque_plein", "2", 1.0), "masse str -> ValueError")
check(leve(RS.moment_inertie, "disque_plein", float("nan"), 1.0), "masse NaN -> ValueError")
check(leve(RS.moment_inertie, "disque_plein", float("inf"), 1.0), "masse inf -> ValueError")
check(leve(RS.moment_cinetique, 1.0, float("nan")), "ω NaN -> ValueError")
check(leve(RS.moment_cinetique, 1.0, float("inf")), "ω inf -> ValueError")
check(leve(RS.moment_cinetique, 1.0, True), "ω bool -> ValueError")
check(leve(RS.moment_cinetique, 1.0, "2"), "ω str -> ValueError")
check(leve(RS.couple, 1.0, float("nan")), "α NaN -> ValueError")
check(leve(RS.couple, True, 1.0), "τ : I bool -> ValueError")
check(leve(RS.energie_rotation, 1.0, float("-inf")), "E : ω=−inf -> ValueError")
check(leve(RS.energie_rotation, "1", 2.0), "E : I str -> ValueError")
check(leve(RS.conservation_moment_cinetique, 5.0, float("nan"), 1.0), "w1 NaN -> ValueError")
check(leve(RS.conservation_moment_cinetique, True, 2.0, 1.0), "I1 bool -> ValueError")
check(leve(RS.inertie_axe_parallele, 1.0, 1.0, float("inf")), "Huygens d=inf -> ValueError")
check(leve(RS.inertie_axe_parallele, 1.0, 1.0, True), "Huygens d bool -> ValueError")

# ── 10) GARDE DE SORTIE — overflow (jamais inf) ──
# Cas de l'audit : I1=1e308, w1=10, I2=1e308 — la vraie réponse est 10.0 mais le produit intermédiaire
# I1·w1 = 1e309 déborde en float ; abstention exigée, JAMAIS inf.
check(leve(RS.conservation_moment_cinetique, 1e308, 10.0, 1e308),
      "conservation : produit intermédiaire 1e309 déborde -> ValueError (jamais inf)")
check(leve(RS.moment_inertie, "anneau", 1e300, 1e200), "I = 1e300·1e400 déborde -> ValueError")
check(leve(RS.moment_cinetique, 1e308, 1e10), "L = 1e318 déborde -> ValueError")
check(leve(RS.couple, 1e200, 1e200), "τ = 1e400 déborde -> ValueError")
check(leve(RS.energie_rotation, 1.0, 1e200), "E : ω² = 1e400 déborde -> ValueError")
check(leve(RS.inertie_axe_parallele, 1.0, 1e308, 1e10), "Huygens : m·d² = 1e328 déborde -> ValueError")
# Débordement À L'ARRONDI : max double = 1.7976931348623157e308 (IEEE 754), fini, mais son arrondi à
# 10 chiffres significatifs (1.797693135e308) excède le max représentable -> abstention.
check(leve(RS.moment_cinetique, 1.7976931348623157e308, 1.0),
      "L : l'arrondi 10 chiffres du max double déborde -> ValueError")

# ── 11) GARDE DE SORTIE — underflow (jamais un 0 faussement exact) ──
# Cas de l'audit : anneau m=1e-200, r=1e-100 — vraie valeur 1e-400 > 0, non représentable
# (min denormal IEEE 754 ≈ 4.9e-324) ; 0.0 serait faux ET refusé ensuite comme entrée par le module.
check(leve(RS.moment_inertie, "anneau", 1e-200, 1e-100), "I vrai = 1e-400 > 0 non représentable -> ValueError")
check(leve(RS.moment_cinetique, 1e-300, 1e-300), "L vrai = 1e-600 != 0 s'écrase à 0 -> ValueError")
check(leve(RS.couple, 1e-200, -1e-200), "τ vrai = -1e-400 != 0 s'écrase à 0 -> ValueError")
check(leve(RS.energie_rotation, 1.0, 1e-200), "E vrai = 5e-401 > 0 s'écrase à 0 -> ValueError")
check(leve(RS.conservation_moment_cinetique, 1e-300, 1e-100, 1e5),
      "conservation : w2 vrai = 1e-405 != 0 s'écrase à 0 -> ValueError")
# Les zéros EXACTS restent légaux (le résultat mathématique EST 0, pas un underflow) :
check(proche(RS.couple(5.0, 0.0), 0.0), "α=0 -> τ=0 exact, toujours légal")
check(proche(RS.energie_rotation(2.0, 0.0), 0.0), "ω=0 -> E=0 exact, toujours légal")
check(proche(RS.conservation_moment_cinetique(5.0, 0.0, 2.0), 0.0), "ω1=0 -> ω2=0 exact, toujours légal")
# Les extrêmes REPRÉSENTABLES sont rendus, pas refusés (comparaison RELATIVE, à la main) :
I_tiny = RS.moment_inertie("anneau", 1e-100, 1e-100)     # 1·1e-100·(1e-100)² = 1e-300 (à la main)
check(I_tiny > 0 and abs(I_tiny / 1e-300 - 1.0) <= 1e-9, "I = 1e-300 représentable -> rendu (pas d'abstention)")
L_big = RS.moment_cinetique(1e150, 1e150)                 # 1e150·1e150 = 1e300 (à la main)
check(math.isfinite(L_big) and abs(L_big / 1e300 - 1.0) <= 1e-9, "L = 1e300 représentable -> rendu")

# ── 12) DÉTERMINISME ──
check(RS.moment_inertie("sphere_pleine", 7.3, 2.1) == RS.moment_inertie("sphere_pleine", 7.3, 2.1),
      "déterminisme moment_inertie")
check(RS.conservation_moment_cinetique(5.0, 2.0, 1.0) == RS.conservation_moment_cinetique(5.0, 2.0, 1.0),
      "déterminisme conservation")
check(RS.energie_rotation(0.25, 4.0) == RS.energie_rotation(0.25, 4.0), "déterminisme énergie")
check(RS.inertie_axe_parallele(1.0, 3.0, 1.0) == RS.inertie_axe_parallele(1.0, 3.0, 1.0),
      "déterminisme Huygens")

print(f"\n=== valide_rotation_solide : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
