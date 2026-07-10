"""
VALIDE optique_geometrique.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (valeurs connues, PAS recalculées par la formule testée) :
  • Air -> eau à 30° : sin(30°) = 0.5 EXACT (trigonométrie classique), donc sin(θ2) = 1.000293·0.5/1.333
    et θ2 ≈ 22.03° — valeur de référence des manuels d'optique, écrite EN DUR ci-dessous (22.0369°,
    calcul à la main : arcsin(0.500147/1.333) = arcsin(0.375204)).
  • Incidence NORMALE θ1 = 0 -> θ2 = 0 pour TOUT couple d'indices (le rayon n'est pas dévié) — fait
    physique indépendant de la formule.
  • Angle critique eau -> air ≈ 48.6° et diamant -> air ≈ 24.4° : valeurs de RÉFÉRENCE connues des
    tables d'optique (±0.1°), écrites en dur.
  • RÉVERSIBILITÉ (ancre forte, second chemin) : réfracter n1 -> n2 puis n2 -> n1 redonne θ1
    (principe du retour inverse du rayon) — testée sur plusieurs couples, tolérance 1e-8 rad
    (le module arrondit à 10 chiffres significatifs, il le dit).
  • Milieu identique n1 = n2 -> θ2 = θ1 (aucune déviation) — fait physique indépendant.
  • Catalogue : indices à λ ≈ 589 nm confrontés aux valeurs des tables (CRC/Hecht) écrites en dur.

SOUNDNESS : n < 1, θ hors [0, π/2], réflexion totale (sin θ2 > 1), angle critique avec n1 ≤ n2,
milieu hors catalogue, types (bool/str/NaN/inf) -> ValueError.
"""
import math

import optique_geometrique as O

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


def proche(x, attendu, tol=1e-6):
    return x is not None and abs(x - attendu) <= tol


PI = math.pi
DEG = PI / 180.0

# ── 1) ANCRE : air -> eau à 30° (sin 30° = 0.5 exact) -> θ2 ≈ 22.03° ──
# Référence manuels : 22.0369° (calcul à la main : arcsin(1.000293·0.5/1.333) = arcsin(0.3752037))
t2 = O.angle_refraction(1.000293, 30.0 * DEG, 1.333)
check(proche(t2 / DEG, 22.0369, tol=0.01), f"air->eau 30° : θ2 = {t2/DEG:.4f}° ≈ 22.0369°")
check(proche(t2 / DEG, 22.03, tol=0.05), "air->eau 30° : θ2 ≈ 22.03° (ancre imposée)")
# le même via le catalogue (indice('air'), indice('eau')) doit donner la même chose
check(proche(O.angle_refraction(O.indice("air"), 30.0 * DEG, O.indice("eau")), t2, tol=1e-12),
      "catalogue air/eau cohérent avec les indices en dur")

# ── 2) ANCRE : incidence normale θ1 = 0 -> θ2 = 0 pour TOUT couple ──
for n1, n2 in ((1.0, 1.333), (1.333, 1.0), (2.417, 1.52), (1.000293, 2.417), (1.473, 1.473)):
    check(O.angle_refraction(n1, 0.0, n2) == 0.0, f"incidence normale : θ2=0 pour ({n1},{n2})")

# ── 3) ANCRE : angles critiques de référence (tables d'optique, ±0.1°) ──
# eau -> air : ≈ 48.6° ; diamant -> air : ≈ 24.4° (valeurs classiques connues)
c_eau = O.angle_critique(1.333, 1.000293)
check(proche(c_eau / DEG, 48.6, tol=0.1), f"θc eau->air = {c_eau/DEG:.3f}° ≈ 48.6°")
c_diam = O.angle_critique(2.417, 1.000293)
check(proche(c_diam / DEG, 24.4, tol=0.1), f"θc diamant->air = {c_diam/DEG:.3f}° ≈ 24.4°")
# eau -> vide : arcsin(1/1.333) ≈ 48.61° (calcul à la main : 1/1.333 = 0.750188)
check(proche(O.angle_critique(1.333, 1.0) / DEG, 48.607, tol=0.01), "θc eau->vide ≈ 48.607°")
# juste SOUS l'angle critique, le rayon réfracté est rasant : θ2 -> π/2 (définition physique de θc).
# (θc est arrondi à 10 chiffres significatifs par le module ; à θc pile l'arrondi peut basculer d'un
#  ulp au-dessus et le module ABSTIENT — comportement FAUX=0 voulu, donc on teste θc − 1e-9.)
check(proche(O.angle_refraction(1.333, c_eau - 1e-9, 1.000293), PI / 2, tol=1e-4),
      "réfraction juste sous θc -> θ2 ≈ π/2 (rayon rasant)")

# ── 4) ANCRE FORTE : réversibilité (retour inverse du rayon) ──
for n1, n2, t1 in ((1.000293, 1.333, 30.0 * DEG), (1.52, 1.333, 40.0 * DEG),
                   (1.0, 2.417, 75.0 * DEG), (1.473, 1.52, 55.0 * DEG),
                   (1.333, 1.000293, 20.0 * DEG)):
    aller = O.angle_refraction(n1, t1, n2)
    retour = O.angle_refraction(n2, aller, n1)
    check(proche(retour, t1, tol=1e-8), f"réversibilité ({n1}->{n2}, θ1={t1/DEG:.0f}°) : retour = θ1")

# ── 5) ANCRE : milieu identique -> aucune déviation (θ2 = θ1) ──
check(proche(O.angle_refraction(1.333, 0.7, 1.333), 0.7, tol=1e-9), "n1=n2 : θ2 = θ1 (eau->eau)")
check(proche(O.angle_refraction(1.0, 1.2, 1.0), 1.2, tol=1e-9), "n1=n2 : θ2 = θ1 (vide->vide)")

# ── 6) SENS PHYSIQUE : vers plus réfringent le rayon se RAPPROCHE de la normale, et inversement ──
check(O.angle_refraction(1.000293, 0.9, 1.52) < 0.9, "air->verre : θ2 < θ1 (rapprochement normale)")
check(O.angle_refraction(1.333, 0.3, 1.000293) > 0.3, "eau->air : θ2 > θ1 (éloignement normale)")

# ── 7) RÉFLEXION : θr = θ1 ──
check(O.angle_reflexion(0.0) == 0.0, "réflexion θ1=0 -> 0")
check(O.angle_reflexion(0.5) == 0.5, "réflexion θ1=0.5 -> 0.5")
check(O.angle_reflexion(PI / 2) == PI / 2, "réflexion θ1=π/2 -> π/2 (rasant)")

# ── 8) RÉFLEXION TOTALE (bool) ──
# eau -> air à 60° > θc≈48.6° -> True ; à 30° < θc -> False (valeurs de référence, pas la formule)
check(O.reflexion_totale(1.333, 60.0 * DEG, 1.000293) is True, "eau->air 60° > 48.6° : totale")
check(O.reflexion_totale(1.333, 30.0 * DEG, 1.000293) is False, "eau->air 30° < 48.6° : pas totale")
check(O.reflexion_totale(2.417, 30.0 * DEG, 1.000293) is True, "diamant->air 30° > 24.4° : totale")
# vers un milieu PLUS réfringent : jamais de réflexion totale, même à incidence rasante
check(O.reflexion_totale(1.000293, PI / 2, 1.333) is False, "air->eau rasant : jamais totale")
check(O.reflexion_totale(1.0, 89.0 * DEG, 2.417) is False, "vide->diamant : jamais totale")
# juste sous θc : rayon rasant existe encore -> False (inégalité stricte ; θc arrondi, cf. section 3)
check(O.reflexion_totale(1.333, c_eau - 1e-9, 1.000293) is False, "θ1 juste sous θc : pas encore totale")
# juste au-dessus de θc : totale -> True (encadrement de θc par les deux côtés)
check(O.reflexion_totale(1.333, c_eau + 1e-6, 1.000293) is True, "θ1 juste sur θc : totale")

# ── 9) CATALOGUE (valeurs des tables λ≈589 nm, écrites en dur) ──
check(O.indice("vide") == 1.0, "indice vide = 1.0")
check(O.indice("air") == 1.000293, "indice air = 1.000293")
check(O.indice("eau") == 1.333, "indice eau = 1.333")
check(O.indice("verre crown") == 1.52, "indice verre crown = 1.52")
check(O.indice("diamant") == 2.417, "indice diamant = 2.417")
check(O.indice("glycérine") == 1.473, "indice glycérine = 1.473")
check(O.indice("  EAU  ") == 1.333, "indice insensible casse/espaces")

# ── 10) SOUNDNESS — réflexion totale dans angle_refraction ──
try:
    O.angle_refraction(1.333, 60.0 * DEG, 1.000293)
    check(False, "eau->air 60° aurait dû lever ValueError")
except ValueError as e:
    check("réflexion totale" in str(e), "message contient « réflexion totale »")
check(leve(O.angle_refraction, 2.417, PI / 2, 1.0), "diamant->vide rasant -> ValueError (totale)")

# ── 11) SOUNDNESS — indices invalides (n < 1, types) ──
check(leve(O.angle_refraction, 0.5, 0.3, 1.333), "n1<1 -> ValueError")
check(leve(O.angle_refraction, 1.333, 0.3, 0.99), "n2<1 -> ValueError")
check(leve(O.angle_critique, 0.9, 0.5), "critique n<1 -> ValueError")
check(leve(O.reflexion_totale, 1.333, 0.3, 0.0), "totale n2=0 -> ValueError")
check(leve(O.angle_refraction, True, 0.3, 1.333), "n1 bool -> ValueError")
check(leve(O.angle_refraction, 1.333, 0.3, "1.0"), "n2 str -> ValueError")
check(leve(O.angle_refraction, float("nan"), 0.3, 1.333), "n1 NaN -> ValueError")
check(leve(O.angle_refraction, 1.333, 0.3, float("inf")), "n2 inf -> ValueError")

# ── 12) SOUNDNESS — angles hors [0, π/2] / types ──
check(leve(O.angle_refraction, 1.0, -0.1, 1.333), "θ1<0 -> ValueError")
check(leve(O.angle_refraction, 1.0, PI / 2 + 0.01, 1.333), "θ1>π/2 -> ValueError")
check(leve(O.angle_reflexion, -0.5), "réflexion θ1<0 -> ValueError")
check(leve(O.angle_reflexion, 2.0), "réflexion θ1>π/2 -> ValueError")
check(leve(O.angle_reflexion, True), "réflexion bool -> ValueError")
check(leve(O.angle_reflexion, float("nan")), "réflexion NaN -> ValueError")
check(leve(O.angle_reflexion, float("inf")), "réflexion inf -> ValueError")
check(leve(O.angle_reflexion, "0.5"), "réflexion str -> ValueError")
check(leve(O.reflexion_totale, 1.333, float("nan"), 1.0), "totale θ NaN -> ValueError")
check(leve(O.reflexion_totale, 1.333, True, 1.0), "totale θ bool -> ValueError")

# ── 13) SOUNDNESS — angle critique inexistant (n1 ≤ n2) ──
check(leve(O.angle_critique, 1.000293, 1.333), "critique air->eau (n1<n2) -> ValueError")
check(leve(O.angle_critique, 1.333, 1.333), "critique n1=n2 -> ValueError")
check(leve(O.angle_critique, 1.0, 2.417), "critique vide->diamant -> ValueError")

# ── 14) SOUNDNESS — catalogue ──
check(leve(O.indice, "plutonium"), "milieu inconnu -> ValueError")
check(leve(O.indice, ""), "milieu vide -> ValueError")
check(leve(O.indice, 1.333), "milieu non-str -> ValueError")
check(leve(O.indice, True), "milieu bool -> ValueError")
check(leve(O.indice, None), "milieu None -> ValueError")

# ── 15) DÉTERMINISME ──
check(O.angle_refraction(1.000293, 30.0 * DEG, 1.333)
      == O.angle_refraction(1.000293, 30.0 * DEG, 1.333), "déterminisme réfraction")
check(O.angle_critique(1.333, 1.000293) == O.angle_critique(1.333, 1.000293), "déterminisme critique")
check(O.reflexion_totale(1.333, 60.0 * DEG, 1.000293)
      == O.reflexion_totale(1.333, 60.0 * DEG, 1.000293), "déterminisme totale")
check(O.indice("diamant") == O.indice("diamant"), "déterminisme indice")

print(f"\n=== valide_optique_geometrique : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
