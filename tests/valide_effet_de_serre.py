"""
VALIDE effet_de_serre.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (valeurs connues indépendamment des fonctions testées) :
  • T_eq de la Terre sans atmosphère ≈ 254 K (−19 °C) — valeur classique des manuels ; recalcul à la
    main : 1361·(1−0.306) = 944.534 ; /4 = 236.1335 W/m² ; /5.670374419e-8 = 4.16434e9 ; ^(1/4) ≈ 254.03 K.
  • SECOND CHEMIN (inverse) : l'équilibre exige σ·T⁴ = S(1−α)/4 ; on vérifie σ·T_eq⁴ ≈ 236.1335 W/m²
    (nombre posé EN DUR, calculé à la main ci-dessus) — chemin de code DISTINCT de la formule directe.
  • Température de surface OBSERVÉE ≈ 288 K (15 °C) : fait MESURÉ, indépendant de tout modèle.
    L'écart 288 − 254 ≈ 33 K EST l'effet de serre (fait).
  • Modèle à une couche : 254.03 · 2^0.25 = 254.03 · 1.1892071 ≈ 302.1 K — à la main. Ce modèle
    SURESTIME (302 > 288) : le module doit le DIRE (ancre d'honnêteté).
  • Forçage d'un DOUBLEMENT du CO₂ : 5.35·ln 2 = 5.35·0.6931472 = 3.708337 W/m² — à la main.
    ΔF(280 -> 420 ppm) = 5.35·ln 1.5 = 5.35·0.4054651 = 2.169238 W/m² — à la main.
  • GIEC AR6 : réchauffement « likely » pour un doublement dans [2.5, 4.0] K ; la valeur centrale
    usuelle 0.8·3.708 ≈ 2.97 K doit tomber DANS l'intervalle rendu.
  • PRG(CH₄) = 28 > PRG(CO₂) = 1 (fait, GIEC AR5) ; PRG(N₂O) = 265.

SOUNDNESS : albédo hors [0,1], S ≤ 0, C ≤ 0, C₀ ≤ 0, bool, str, NaN, ±inf -> ValueError ;
la sensibilité est un INTERVALLE ordonné, jamais un scalaire ; catalogue rendu par copie ; déterminisme.
"""
import math

import effet_de_serre as E

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


# ── 1) ANCRE : T_eq Terre ≈ 254 K (valeur classique, −19 °C ; à la main : 254.03) ──
t_eq = E.temperature_equilibre_sans_atmosphere(1361.0, 0.306)
check(proche(t_eq, 254.0, tol=0.5), f"T_eq Terre ≈ 254 K (valeur classique) — obtenu {t_eq}")
check(proche(t_eq, 254.03, tol=0.05), f"T_eq Terre ≈ 254.03 K (calcul à la main) — obtenu {t_eq}")
# SECOND CHEMIN (inverse, distinct de la formule directe) : σ·T_eq⁴ doit valoir S(1−α)/4 = 236.1335 W/m²
flux_retour = 5.670374419e-8 * t_eq ** 4
check(proche(flux_retour, 236.1335, tol=0.01),
      f"inverse : σ·T_eq⁴ ≈ 236.1335 W/m² (à la main) — obtenu {flux_retour}")
# T_eq en Celsius ≈ −19 °C (fait classique)
check(proche(t_eq - 273.15, -19.0, tol=0.5), "T_eq ≈ −19 °C")

# ── 2) MONOTONIE PHYSIQUE de T_eq (plus d'albédo -> plus froid ; plus de flux -> plus chaud) ──
check(E.temperature_equilibre_sans_atmosphere(1361.0, 0.5)
      < E.temperature_equilibre_sans_atmosphere(1361.0, 0.306), "albédo plus grand -> T_eq plus basse")
check(E.temperature_equilibre_sans_atmosphere(2000.0, 0.306)
      > E.temperature_equilibre_sans_atmosphere(1361.0, 0.306), "S plus grand -> T_eq plus haute")
# albédo = 1 : tout est réfléchi -> T_eq = 0 K (cas limite exact du modèle)
check(E.temperature_equilibre_sans_atmosphere(1361.0, 1.0) == 0.0, "albédo=1 -> T_eq = 0 K")

# ── 3) MODÈLE UNE COUCHE : T_surface = 2^(1/4)·T_eq ≈ 302.1 K (à la main : 254.03·1.1892071) ──
t_couche = E.temperature_surface_une_couche(1361.0, 0.306)
check(proche(t_couche, 302.1, tol=0.2), f"une couche : T_surface ≈ 302.1 K (à la main) — obtenu {t_couche}")
# rapport EXACT 2^(1/4) entre les deux fonctions (propriété structurelle du modèle)
check(proche(t_couche / t_eq, 2.0 ** 0.25, tol=1e-6), "T_surface / T_eq = 2^(1/4)")

# ── 4) ANCRE D'HONNÊTETÉ : 302 K SURESTIME les 288 K observés ; écart observé−T_eq ≈ 33 K = effet de serre ──
bilan = E.bilan_effet_de_serre_terre()
check(bilan["t_observee_K"] == 288.0, "T surface observée = 288 K (fait mesuré)")
check(bilan["modele_surestime"] is True, "le module DIT que le modèle une couche surestime (302 > 288)")
check(bilan["t_une_couche_K"] > bilan["t_observee_K"], "302 K (modèle) > 288 K (observé)")
check(33.0 <= bilan["ecart_effet_de_serre_K"] <= 35.0,
      f"effet de serre = observée − T_eq ≈ 33-34 K — obtenu {bilan['ecart_effet_de_serre_K']}")
check(proche(bilan["ecart_effet_de_serre_K"], 288.0 - 254.03, tol=0.1),
      "écart ≈ 288 − 254.03 = 33.97 K (à la main)")
check(proche(bilan["t_eq_K"], 254.03, tol=0.05), "bilan : t_eq_K ≈ 254.03 K")
check("surestime" in bilan["note"].lower(), "la note du bilan avoue la surestimation")

# ── 5) FORÇAGE CO₂ (Myhre 1998) : doublement = 3.708337 W/m² ; 280->420 ppm = 2.169238 W/m² (à la main) ──
f2x = E.forcage_radiatif_co2(560.0, 280.0)
check(proche(f2x, 3.708337, tol=1e-3), f"ΔF doublement = 5.35·ln2 ≈ 3.708 W/m² — obtenu {f2x}")
f_actuel = E.forcage_radiatif_co2(420.0, 280.0)
check(proche(f_actuel, 2.169238, tol=1e-3), f"ΔF(280->420) = 5.35·ln1.5 ≈ 2.169 W/m² — obtenu {f_actuel}")
# propriétés structurelles du logarithme (vérité mathématique, pas la fonction elle-même)
check(E.forcage_radiatif_co2(280.0, 280.0) == 0.0, "C = C₀ -> ΔF = 0")
check(E.forcage_radiatif_co2(140.0, 280.0) < 0.0, "C < C₀ -> ΔF < 0 (refroidissement)")
check(proche(E.forcage_radiatif_co2(140.0, 280.0), -3.708337, tol=1e-3),
      "ΔF(moitié) = −5.35·ln2 (symétrie du log)")
# additivité : ΔF(280->560) = ΔF(280->420) + ΔF(420->560) (propriété du log, chemin distinct)
check(proche(f2x, f_actuel + E.forcage_radiatif_co2(560.0, 420.0), tol=1e-6),
      "additivité du forçage logarithmique")

# ── 6) SENSIBILITÉ : INTERVALLE, jamais un scalaire ; doublement dans la fourchette GIEC [2.5, 4.0] K ──
inter = E.sensibilite_climatique(f2x)
check(isinstance(inter, tuple) and len(inter) == 2, "sensibilité = un intervalle (tuple de 2 bornes)")
basse, haute = inter
check(basse < haute, "bornes ordonnées et distinctes (pas un point)")
check(2.4 <= basse <= 2.6 and 3.9 <= haute <= 4.1,
      f"doublement CO₂ : intervalle ≈ [2.5, 4.0] K (GIEC AR6 likely) — obtenu [{basse}, {haute}]")
check(basse <= 0.8 * 3.708337 <= haute, "la valeur centrale 0.8·ΔF ≈ 2.97 K est DANS l'intervalle")
check(basse <= 3.0 <= haute, "3 K (ordre de grandeur GIEC pour un doublement) est DANS l'intervalle")
# ΔF négatif : intervalle négatif, bornes toujours ordonnées
b_neg, h_neg = E.sensibilite_climatique(-3.708337)
check(b_neg < h_neg <= 0.0, "ΔF < 0 -> intervalle négatif ordonné (basse < haute ≤ 0)")
check(proche(b_neg, -haute, tol=1e-6) and proche(h_neg, -basse, tol=1e-6),
      "antisymétrie : intervalle(−ΔF) = −intervalle(ΔF) renversé")
check(E.sensibilite_climatique(0.0) == (0.0, 0.0), "ΔF = 0 -> (0, 0)")
check("APPROCHE" in E.SENSIBILITE_STATUT, "la sensibilité est MARQUÉE approchée (statut)")

# ── 7) CATALOGUE DES GAZ : PRG 100 ans (GIEC AR5) ──
gaz = E.gaz_a_effet_de_serre()
for symbole in ("H2O", "CO2", "CH4", "N2O", "O3"):
    check(symbole in gaz, f"catalogue contient {symbole}")
check(gaz["CO2"]["prg_100"] == 1.0, "PRG(CO2) = 1 (référence, par définition)")
check(gaz["CH4"]["prg_100"] == 28.0, "PRG(CH4) = 28 (GIEC AR5)")
check(gaz["N2O"]["prg_100"] == 265.0, "PRG(N2O) = 265 (GIEC AR5)")
check(gaz["CH4"]["prg_100"] > gaz["CO2"]["prg_100"], "PRG(CH4) > PRG(CO2) (fait)")
check(gaz["N2O"]["prg_100"] > gaz["CH4"]["prg_100"], "PRG(N2O) > PRG(CH4) (fait)")
check(gaz["H2O"]["prg_100"] is None, "H2O : PRG NON DÉFINI -> None (abstention, pas d'invention)")
check(gaz["O3"]["prg_100"] is None, "O3 : PRG NON DÉFINI -> None (abstention, pas d'invention)")
# copie : muter le catalogue rendu ne corrompt pas le module
gaz["CO2"]["prg_100"] = 999.0
check(E.gaz_a_effet_de_serre()["CO2"]["prg_100"] == 1.0, "catalogue rendu par copie (pas d'état mutable)")

# ── 8) SOUNDNESS — albédo hors [0, 1] ──
check(leve(E.temperature_equilibre_sans_atmosphere, 1361.0, -0.01), "albédo < 0 -> ValueError")
check(leve(E.temperature_equilibre_sans_atmosphere, 1361.0, 1.01), "albédo > 1 -> ValueError")
check(leve(E.temperature_surface_une_couche, 1361.0, 2.0), "une couche : albédo > 1 -> ValueError")

# ── 9) SOUNDNESS — flux solaire ──
check(leve(E.temperature_equilibre_sans_atmosphere, 0.0, 0.306), "S = 0 -> ValueError")
check(leve(E.temperature_equilibre_sans_atmosphere, -1361.0, 0.306), "S < 0 -> ValueError")
check(leve(E.temperature_surface_une_couche, 0.0, 0.306), "une couche : S = 0 -> ValueError")

# ── 10) SOUNDNESS — concentrations CO₂ ──
check(leve(E.forcage_radiatif_co2, 0.0, 280.0), "C = 0 -> ValueError")
check(leve(E.forcage_radiatif_co2, -420.0, 280.0), "C < 0 -> ValueError")
check(leve(E.forcage_radiatif_co2, 420.0, 0.0), "C₀ = 0 -> ValueError")
check(leve(E.forcage_radiatif_co2, 420.0, -280.0), "C₀ < 0 -> ValueError")

# ── 11) SOUNDNESS — types invalides (bool / str / NaN / inf) ──
check(leve(E.temperature_equilibre_sans_atmosphere, True, 0.306), "S bool -> ValueError")
check(leve(E.temperature_equilibre_sans_atmosphere, 1361.0, True), "albédo bool -> ValueError")
check(leve(E.temperature_equilibre_sans_atmosphere, "1361", 0.306), "S str -> ValueError")
check(leve(E.temperature_equilibre_sans_atmosphere, float("nan"), 0.306), "S NaN -> ValueError")
check(leve(E.temperature_equilibre_sans_atmosphere, float("inf"), 0.306), "S inf -> ValueError")
check(leve(E.temperature_equilibre_sans_atmosphere, 1361.0, float("nan")), "albédo NaN -> ValueError")
check(leve(E.forcage_radiatif_co2, True, 280.0), "C bool -> ValueError")
check(leve(E.forcage_radiatif_co2, "420", 280.0), "C str -> ValueError")
check(leve(E.forcage_radiatif_co2, float("nan"), 280.0), "C NaN -> ValueError")
check(leve(E.forcage_radiatif_co2, float("inf"), 280.0), "C inf -> ValueError")
check(leve(E.forcage_radiatif_co2, 420.0, float("nan")), "C₀ NaN -> ValueError")
check(leve(E.sensibilite_climatique, True), "sensibilité bool -> ValueError")
check(leve(E.sensibilite_climatique, "3.7"), "sensibilité str -> ValueError")
check(leve(E.sensibilite_climatique, float("nan")), "sensibilité NaN -> ValueError")
check(leve(E.sensibilite_climatique, float("inf")), "sensibilité inf -> ValueError")
check(leve(E.sensibilite_climatique, float("-inf")), "sensibilité -inf -> ValueError")

# ── 12) DÉTERMINISME ──
check(E.temperature_equilibre_sans_atmosphere(1361.0, 0.306)
      == E.temperature_equilibre_sans_atmosphere(1361.0, 0.306), "déterminisme T_eq")
check(E.forcage_radiatif_co2(560.0, 280.0) == E.forcage_radiatif_co2(560.0, 280.0), "déterminisme forçage")
check(E.sensibilite_climatique(3.708337) == E.sensibilite_climatique(3.708337), "déterminisme sensibilité")
check(E.bilan_effet_de_serre_terre() == E.bilan_effet_de_serre_terre(), "déterminisme bilan")
check(E.gaz_a_effet_de_serre() == E.gaz_a_effet_de_serre(), "déterminisme catalogue")

print(f"\n=== valide_effet_de_serre : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
