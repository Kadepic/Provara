"""
VALIDE cycle_eau.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (valeurs connues ou calculées À LA MAIN, PAS recalculées par le module) :
  • Les océans contiennent ≈ 96,5 % de l'eau terrestre (fait mesuré, USGS/Gleick) — écrit EN DUR ici.
  • Temps de résidence ATMOSPHÉRIQUE très court, ≈ 9 jours : V_atm = 12 900 km³, flux global
    505 000 km³/an -> 12900/505000 = 0.0255445544... an ≈ 9,33 jours (division posée à la main ci-dessous,
    indépendante du module ; 0.02554 an = 9,3 jours).
  • Temps de résidence OCÉANIQUE de l'ordre de 3000 ans : 1 338 000 000 / 413 000 = 3239,7 ans (à la main).
  • CONSERVATION GLOBALE (ancre forte) : évaporation totale = 413 000 (océan) + 73 000 (continent)
    = 486 000 km³/an ; précipitation totale = 373 000 (océan) + 113 000 (continent) = 486 000 km³/an —
    DEUX SOMMES INDÉPENDANTES écrites en dur ici, qui doivent coïncider entre elles ET avec le module.
  • changement_etat('condensation') = gaz vers liquide (la vapeur se condense en gouttelettes, PAS l'inverse).

SOUNDNESS : étape/réservoir hors catalogue, non-str, bool, NaN, inf, volume/flux ≤ 0 -> ValueError.
"""
import math

import cycle_eau as C

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


# ── 1) ANCRE : les océans ≈ 96,5 % de l'eau terrestre (fait mesuré, écrit en dur) ──
vol_ocean, pct_ocean = C.reservoir("oceans")
check(pct_ocean == 96.5, "océans = 96.5 % de l'eau terrestre (fait USGS/Gleick)")
check(proche(vol_ocean, 1.338e9, tol=1e3), "volume océans ≈ 1.338e9 km³ (fait USGS/Gleick)")
# Cohérence interne volume/pourcentage vs total (valeurs publiées arrondies -> tolérance large mais serrée) :
check(abs(vol_ocean / C.VOLUME_TOTAL_KM3 * 100.0 - pct_ocean) < 0.1,
      "volume océans / total ≈ 96.5 % (cohérence des faits publiés)")

# ── 2) ANCRE : temps de résidence atmosphérique ≈ 9 jours (calcul à la main) ──
# À la main : 12900 / 505000 = 129/5050 = 0.0255445544... an. 0.0255445544 × 365.25 = 9.33 jours.
t_atm = C.temps_residence(12_900, 505_000)
check(proche(t_atm, 0.0255445544, tol=1e-8), "résidence atmosphère = 0.02554 an (12900/505000, à la main)")
jours_atm = t_atm * 365.25
check(9.0 <= jours_atm <= 9.6, f"résidence atmosphère ≈ 9.3 jours (obtenu {jours_atm})")
# Le volume atmosphérique catalogué EST celui de l'ancre (12 900 km³, USGS) :
vol_atm, pct_atm = C.reservoir("atmosphere")
check(vol_atm == 12_900, "volume atmosphère = 12 900 km³ (fait USGS)")
check(pct_atm == 0.001, "atmosphère = 0.001 % (fait USGS)")

# ── 3) ANCRE : temps de résidence océanique de l'ordre de 3000 ans (calcul à la main) ──
# À la main : 1 338 000 000 / 413 000 = 3239.709... ans (413000 × 3239.7 = 1 337 996 100 ≈ 1.338e9).
t_ocean = C.temps_residence(1_338_000_000, 413_000)
check(proche(t_ocean, 3239.709443, tol=1e-3), "résidence océan = 3239.7 ans (division à la main)")
check(3000.0 <= t_ocean <= 3500.0, "résidence océan de l'ordre de 3000 ans")

# Bonus indépendant : rivières 2120 km³ / débit fleuves 40 000 km³/an = 0.053 an ≈ 19 jours (à la main).
t_riv = C.temps_residence(2_120, 40_000)
check(proche(t_riv, 0.053, tol=1e-9), "résidence rivières = 0.053 an (2120/40000, à la main)")

# ── 4) ANCRE FORTE : conservation globale, deux sommes indépendantes écrites en dur ──
EVAP_TOTALE_MAIN = 413_000 + 73_000     # = 486 000 (somme posée à la main)
PRECIP_TOTALE_MAIN = 373_000 + 113_000  # = 486 000 (somme posée à la main)
check(EVAP_TOTALE_MAIN == 486_000, "évaporation totale à la main = 486 000 km³/an")
check(PRECIP_TOTALE_MAIN == 486_000, "précipitation totale à la main = 486 000 km³/an")
check(EVAP_TOTALE_MAIN == PRECIP_TOTALE_MAIN, "conservation : les deux sommes indépendantes coïncident")
evap_mod, precip_mod = C.bilan_global()
check(evap_mod == EVAP_TOTALE_MAIN, "bilan module : évaporation = somme à la main")
check(precip_mod == PRECIP_TOTALE_MAIN, "bilan module : précipitation = somme à la main")
# L'écart océanique revient par les fleuves : 413 000 − 373 000 = 40 000 (à la main).
check(413_000 - 373_000 == C.FLUX_FLEUVES_KM3_AN, "déficit océanique 40 000 km³/an = flux des fleuves")
check(C.verifie_invariants() is True, "verifie_invariants() passe (Σ% ≈ 100 et conservation)")
# Somme des pourcentages à la main : 96.5+1.74+1.69+0.013+0.001+0.0002 = 99.9442 (dans 100 ± 0.1).
somme_pct_main = 96.5 + 1.74 + 1.69 + 0.013 + 0.001 + 0.0002
check(abs(somme_pct_main - 100.0) <= 0.1, "Σ% à la main = 99.9442, dans 100 ± 0.1")
check(proche(sum(C.reservoir(n)[1] for n in C.reservoirs()), somme_pct_main, tol=1e-9),
      "Σ% du catalogue = Σ% à la main")

# ── 5) ANCRE : changements d'état (sens physique, écrits en dur) ──
check(C.changement_etat("condensation") == "gaz->liquide", "condensation = gaz -> liquide (PAS l'inverse)")
check(C.changement_etat("evaporation") == "liquide->gaz", "évaporation = liquide -> gaz")
check(C.changement_etat("evapotranspiration") == "liquide->gaz", "évapotranspiration = liquide -> gaz")
check(C.changement_etat("sublimation") == "solide->gaz", "sublimation = solide -> gaz")
check(C.changement_etat("fonte") == "solide->liquide", "fonte = solide -> liquide")
check(C.changement_etat("precipitation") == "aucun", "précipitation : transport, pas de changement d'état")
check(C.changement_etat("infiltration") == "aucun", "infiltration : pas de changement d'état")

# ── 6) MOTEURS ÉNERGÉTIQUES (faits physiques écrits en dur) ──
check(C.moteur("evaporation") == "energie_solaire", "moteur évaporation = énergie solaire")
check(C.moteur("condensation") == "refroidissement", "moteur condensation = refroidissement")
check(C.moteur("precipitation") == "gravite", "moteur précipitation = gravité")
check(C.moteur("ruissellement") == "gravite", "moteur ruissellement = gravité")
check(C.moteur("ecoulement_souterrain") == "gravite", "moteur écoulement souterrain = gravité")
check(C.moteur("sublimation") == "energie_solaire", "moteur sublimation = énergie solaire")

# ── 7) ÉTAPES : catalogue ordonné + enchaînement ──
et = C.etapes()
check(isinstance(et, tuple) and len(et) == 9, "etapes() = tuple de 9 étapes")
check(et[0] == "evaporation" and et[2] == "condensation" and et[3] == "precipitation",
      "ordre : évaporation avant condensation avant précipitation")
check(set(et) == {"evaporation", "evapotranspiration", "condensation", "precipitation", "infiltration",
                  "ruissellement", "ecoulement_souterrain", "sublimation", "fonte"},
      "catalogue complet des 9 étapes")
check(C.suivante("evaporation") == ("condensation",), "évaporation -> condensation")
check(C.suivante("condensation") == ("precipitation",), "condensation -> précipitation")
check(set(C.suivante("precipitation")) == {"infiltration", "ruissellement"},
      "précipitation -> infiltration OU ruissellement (bifurcation rendue, pas choisie)")
check(C.suivante("infiltration") == ("ecoulement_souterrain",), "infiltration -> écoulement souterrain")
check(C.suivante("ruissellement") == ("evaporation",), "ruissellement -> retour à l'évaporation (boucle)")
check(C.suivante("sublimation") == ("condensation",), "sublimation -> condensation")
# Le graphe boucle : depuis chaque étape, on ré-atteint 'evaporation' (le cycle est fermé).
for depart in et:
    vus, front = set(), {depart}
    while front:
        courant = front.pop()
        if courant in vus:
            continue
        vus.add(courant)
        front.update(C.suivante(courant))
    check("evaporation" in vus, f"le cycle boucle depuis {depart}")

# ── 8) NOMS ACCENTUÉS / VARIANTES acceptés (normalisation, pas d'invention) ──
check(C.changement_etat("Évaporation") == "liquide->gaz", "nom accentué/majuscule accepté (étape)")
check(C.changement_etat("écoulement souterrain") == "aucun", "espace + accents acceptés (étape)")
check(C.reservoir("océans") == C.reservoir("oceans"), "nom accentué accepté (réservoir)")
check(C.reservoir("Atmosphère")[0] == 12_900, "réservoir 'Atmosphère' -> 12 900 km³")

# ── 9) RÉSERVOIRS : autres faits mesurés (écrits en dur, USGS/Gleick) ──
check(C.reservoir("glaciers") == (2.4064e7, 1.74), "glaciers/calottes = 24 064 000 km³, 1.74 %")
check(C.reservoir("eaux_souterraines") == (2.34e7, 1.69), "eaux souterraines = 23 400 000 km³, 1.69 %")
check(C.reservoir("lacs") == (1.764e5, 0.013), "lacs = 176 400 km³, 0.013 %")
check(C.reservoir("rivieres") == (2.12e3, 0.0002), "rivières = 2 120 km³, 0.0002 %")
check(len(C.reservoirs()) == 6, "6 réservoirs catalogués")

# ── 10) SOUNDNESS — étapes/réservoirs hors catalogue ou mal typés ──
check(leve(C.changement_etat, "ebullition"), "étape inconnue -> ValueError")
check(leve(C.moteur, "nuage"), "moteur d'étape inconnue -> ValueError")
check(leve(C.suivante, ""), "étape vide -> ValueError")
check(leve(C.changement_etat, 3), "étape non-str (int) -> ValueError")
check(leve(C.moteur, True), "étape bool -> ValueError")
check(leve(C.suivante, None), "étape None -> ValueError")
check(leve(C.reservoir, "mers"), "réservoir inconnu -> ValueError")
check(leve(C.reservoir, "nuages"), "réservoir 'nuages' hors catalogue -> ValueError")
check(leve(C.reservoir, 12), "réservoir non-str -> ValueError")

# ── 11) SOUNDNESS — temps_residence ──
check(leve(C.temps_residence, 0, 505_000), "volume=0 -> ValueError")
check(leve(C.temps_residence, -1.0, 505_000), "volume<0 -> ValueError")
check(leve(C.temps_residence, 12_900, 0), "flux=0 -> ValueError")
check(leve(C.temps_residence, 12_900, -40_000), "flux<0 -> ValueError")
check(leve(C.temps_residence, True, 505_000), "volume bool -> ValueError")
check(leve(C.temps_residence, 12_900, True), "flux bool -> ValueError")
check(leve(C.temps_residence, "12900", 505_000), "volume str -> ValueError")
check(leve(C.temps_residence, float("nan"), 505_000), "volume NaN -> ValueError")
check(leve(C.temps_residence, float("inf"), 505_000), "volume inf -> ValueError")
check(leve(C.temps_residence, 12_900, float("nan")), "flux NaN -> ValueError")
check(leve(C.temps_residence, 12_900, float("inf")), "flux inf -> ValueError")

# ── 12) DÉTERMINISME ──
check(C.temps_residence(12_900, 505_000) == C.temps_residence(12_900, 505_000), "déterminisme résidence")
check(C.etapes() == C.etapes(), "déterminisme etapes()")
check(C.reservoir("oceans") == C.reservoir("oceans"), "déterminisme reservoir()")
check(C.bilan_global() == C.bilan_global(), "déterminisme bilan_global()")

print(f"\n=== valide_cycle_eau : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
