"""VALIDE tectonique_plaques.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (géodésie/géologie, valeurs connues INDÉPENDAMMENT du module) :
  • L'Atlantique s'ouvre d'environ 2.5 cm/an (mesure géodésique classique) ; à ce rythme, en 100 millions
    d'années : 2.5 cm/an × 1e8 an = 2.5e8 cm = 2500 km (CALCUL À LA MAIN, écrit en dur ci-dessous).
  • La dorsale est-Pacifique (≈ 15 cm/an) est la PLUS RAPIDE au monde — donc strictement plus rapide que
    la médio-atlantique (fait mesuré, pas déduit du module).
  • L'Himalaya résulte d'une CONVERGENCE Inde/Eurasie (collision continentale), PAS d'une divergence.
  • San Andreas est TRANSFORMANTE (Pacifique/Amérique du Nord) : PAS de volcanisme associé — ancre
    DISCRIMINANTE : un module qui y prédirait du volcanisme serait FAUX.
  • Fosse du Japon = CONVERGENTE (subduction Pacifique sous Okhotsk) ; rift est-africain = DIVERGENT.
  • Une plaque INVENTÉE (Atlantide, Mu) -> ValueError (abstention structurelle).

SOUNDNESS : plaque/frontière/type hors catalogue, même plaque des deux côtés, vitesse/durée/distance ≤ 0,
bool, str là où un nombre est requis, non-str là où un nom est requis, NaN, ±inf -> ValueError.
"""
from fractions import Fraction

import tectonique_plaques as T

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


# ── 1) ANCRES : TYPES DE FRONTIÈRES (faits géologiques établis) ──
check(T.type_frontiere("Amérique du Nord", "Eurasie") == "divergente",
      "dorsale médio-atlantique : Amérique du Nord/Eurasie = divergente")
check(T.type_frontiere("Eurasie", "Amérique du Nord") == "divergente",
      "ordre des plaques indifférent (symétrie)")
check(T.type_frontiere("Inde", "Eurasie") == "convergente",
      "Himalaya : Inde/Eurasie = CONVERGENTE (collision, pas divergence)")
check(T.type_frontiere("Inde", "Eurasie") != "divergente",
      "Himalaya n'est PAS une divergence (ancre discriminante)")
check(T.type_frontiere("Pacifique", "Okhotsk") == "convergente",
      "fosse du Japon : Pacifique/Okhotsk = convergente (subduction)")
check(T.type_frontiere("Pacifique", "Amérique du Nord") == "transformante",
      "San Andreas : Pacifique/Amérique du Nord = transformante")
check(T.type_frontiere("Nubie", "Somalie") == "divergente",
      "rift est-africain : Nubie/Somalie = divergente")
check(T.type_frontiere("Pacifique", "Nazca") == "divergente",
      "dorsale est-Pacifique : Pacifique/Nazca = divergente")
# normalisation : accents/casse/traits
check(T.type_frontiere("amerique du nord", "EURASIE") == "divergente",
      "normalisation accents/casse (amerique du nord / EURASIE)")
check(T.frontiere_entre("Pacifique", "Amérique du Nord") == "faille de san andreas",
      "frontiere_entre Pacifique/Amérique du Nord = faille de san andreas")
check(T.frontiere_entre("Inde", "Eurasie") == "himalaya", "frontiere_entre Inde/Eurasie = himalaya")

# ── 2) ANCRES : VITESSES MESURÉES (géodésie, cm/an, en dur) ──
check(proche(T.vitesse_mesuree("dorsale médio-atlantique"), 2.5),
      "expansion atlantique = 2.5 cm/an (mesure géodésique, en dur)")
check(proche(T.vitesse_mesuree("dorsale est-Pacifique"), 15.0),
      "dorsale est-Pacifique = 15 cm/an (en dur)")
check(proche(T.vitesse_mesuree("Himalaya"), 5.0), "convergence Inde-Eurasie = 5 cm/an (en dur)")
check(proche(T.vitesse_mesuree("faille de San Andreas"), 3.4), "San Andreas = 3.4 cm/an (en dur)")
# FAIT : la dorsale est-Pacifique est PLUS RAPIDE que la médio-atlantique (15 > 2.5 connu indépendamment)
check(T.vitesse_mesuree("dorsale est-Pacifique") > T.vitesse_mesuree("dorsale médio-atlantique"),
      "est-Pacifique PLUS RAPIDE que médio-atlantique (fait géodésique)")
# FAIT : la plus rapide du catalogue tout entier
vitesses = []
for nom in T.frontieres_cataloguees():
    try:
        vitesses.append((T.vitesse_mesuree(nom), nom))
    except ValueError:
        pass  # vitesse non consolidée = abstention attendue
check(max(vitesses)[1] == "dorsale est pacifique",
      "la dorsale est-Pacifique est LA plus rapide du catalogue")
# abstention : frontières cataloguées SANS vitesse consolidée -> ValueError, jamais un chiffre inventé
check(leve(T.vitesse_mesuree, "fosse du Japon"), "vitesse fosse du Japon non consolidée -> ValueError")
check(leve(T.vitesse_mesuree, "rift est-africain"), "vitesse rift est-africain non consolidée -> ValueError")

# ── 3) MÉCANISME : distance/âge — ANCRES CALCULÉES À LA MAIN (en dur) ──
# 2.5 cm/an × 100 Ma = 2.5 × 1e8 an = 2.5e8 cm = 2500 km  (calcul à la main)
check(proche(T.distance_parcourue(2.5, 100), 2500.0), "2.5 cm/an × 100 Ma = 2500 km (main)")
# 15 cm/an × 1 Ma = 1.5e7 cm = 150 km  (main)
check(proche(T.distance_parcourue(15, 1), 150.0), "15 cm/an × 1 Ma = 150 km (main)")
# 1 cm/an × 1 Ma = 1e6 cm = 10 km  (main)
check(proche(T.distance_parcourue(1, 1), 10.0), "1 cm/an × 1 Ma = 10 km (main)")
# 3.4 cm/an × 10 Ma = 3.4e7 cm = 340 km  (main)
check(proche(T.distance_parcourue(3.4, 10), 340.0), "3.4 cm/an × 10 Ma = 340 km (main)")
# ouverture atlantique depuis ~180 Ma à 2.5 cm/an -> 4500 km : ordre de grandeur de la largeur atlantique
check(proche(T.distance_parcourue(2.5, 180), 4500.0), "2.5 cm/an × 180 Ma = 4500 km (main)")
# âges : inverses calculés à la main
check(proche(T.age_depuis_distance(2.5, 2500), 100.0), "2500 km à 2.5 cm/an = 100 Ma (main)")
check(proche(T.age_depuis_distance(5, 50), 1.0), "50 km à 5 cm/an = 1 Ma (main)")
check(proche(T.age_depuis_distance(15, 150), 1.0), "150 km à 15 cm/an = 1 Ma (main)")
check(proche(T.age_depuis_distance(2.5, 25), 1.0), "25 km à 2.5 cm/an = 1 Ma (main)")
# Fraction en entrée : exactitude (1/4 cm/an × 4 Ma = 1e6 cm = 10 km, main)
check(proche(T.distance_parcourue(Fraction(1, 4), 4), 10.0), "Fraction 1/4 cm/an × 4 Ma = 10 km (main)")

# ── 4) PHÉNOMÈNES ATTENDUS par type ──
p_div = T.phenomene_attendu("divergente")
check("dorsale" in p_div, "divergente -> dorsale")
check("volcanisme effusif" in p_div, "divergente -> volcanisme effusif")
p_conv = T.phenomene_attendu("convergente")
check("subduction" in p_conv, "convergente -> subduction")
check("séisme profond" in p_conv, "convergente -> séisme profond")
check("chaîne de montagnes" in p_conv, "convergente -> chaîne de montagnes")
p_transf = T.phenomene_attendu("transformante")
check("séisme superficiel" in p_transf, "transformante -> séisme superficiel")
# ANCRE DISCRIMINANTE : San Andreas (transformante) SANS volcanisme — 'volcanisme' n'apparaît que nié
p_sa = T.phenomene_attendu(T.type_frontiere("Pacifique", "Amérique du Nord"))
check("pas de volcanisme" in p_sa, "San Andreas (transformante) -> pas de volcanisme")
check(p_sa.count("volcanisme") == 1 and "pas de volcanisme" in p_sa,
      "transformante : 'volcanisme' n'apparaît QUE nié (jamais prédit)")
check("subduction" not in p_sa, "transformante : pas de subduction prédite")

# ── 5) SOUNDNESS — plaques/frontières hors catalogue (abstention) ──
check(leve(T.type_frontiere, "Atlantide", "Eurasie"), "plaque inventée (Atlantide) -> ValueError")
check(leve(T.type_frontiere, "Mu", "Lémurie"), "deux plaques inventées -> ValueError")
check(leve(T.type_frontiere, "Inde", "Nazca"), "paire réelle mais frontière non cataloguée -> ValueError")
check(leve(T.type_frontiere, "Eurasie", "Eurasie"), "même plaque des deux côtés -> ValueError")
check(leve(T.frontiere_entre, "Atlantide", "Eurasie"), "frontiere_entre plaque inventée -> ValueError")
check(leve(T.vitesse_mesuree, "faille imaginaire"), "frontière inventée -> ValueError")
check(leve(T.phenomene_attendu, "oblique"), "type de frontière inconnu -> ValueError")

# ── 6) SOUNDNESS — types invalides sur les noms ──
check(leve(T.type_frontiere, 3, "Eurasie"), "plaque non-str -> ValueError")
check(leve(T.type_frontiere, True, "Eurasie"), "plaque bool -> ValueError")
check(leve(T.type_frontiere, "", "Eurasie"), "plaque chaîne vide -> ValueError")
check(leve(T.vitesse_mesuree, None), "nom None -> ValueError")
check(leve(T.phenomene_attendu, 1.0), "type non-str -> ValueError")

# ── 7) SOUNDNESS — cinématique (vitesse/durée/distance illégales) ──
check(leve(T.distance_parcourue, 0, 100), "vitesse=0 -> ValueError")
check(leve(T.distance_parcourue, -2.5, 100), "vitesse<0 -> ValueError")
check(leve(T.distance_parcourue, 2.5, 0), "durée=0 -> ValueError")
check(leve(T.distance_parcourue, 2.5, -1), "durée<0 -> ValueError")
check(leve(T.age_depuis_distance, 2.5, 0), "distance=0 -> ValueError")
check(leve(T.age_depuis_distance, 0, 2500), "âge vitesse=0 -> ValueError")
check(leve(T.age_depuis_distance, -1, 2500), "âge vitesse<0 -> ValueError")
check(leve(T.distance_parcourue, True, 100), "vitesse bool -> ValueError")
check(leve(T.distance_parcourue, 2.5, True), "durée bool -> ValueError")
check(leve(T.distance_parcourue, "2.5", 100), "vitesse str -> ValueError")
check(leve(T.distance_parcourue, float("nan"), 100), "vitesse NaN -> ValueError")
check(leve(T.distance_parcourue, float("inf"), 100), "vitesse inf -> ValueError")
check(leve(T.distance_parcourue, 2.5, float("nan")), "durée NaN -> ValueError")
check(leve(T.age_depuis_distance, 2.5, float("inf")), "distance inf -> ValueError")

# ── 8) CATALOGUE clos et cohérent ──
noms = T.frontieres_cataloguees()
check(len(noms) == 6, "catalogue = 6 frontières majeures")
check("dorsale medio atlantique" in noms and "himalaya" in noms, "frontières attendues présentes")
plaques = T.plaques_cataloguees()
check("pacifique" in plaques and "eurasie" in plaques and "nazca" in plaques, "plaques attendues présentes")
check(all(T.phenomene_attendu(t) for t in ("divergente", "convergente", "transformante")),
      "les 3 types géologiques ont un phénomène attendu")

# ── 9) DÉTERMINISME ──
check(T.type_frontiere("Inde", "Eurasie") == T.type_frontiere("Inde", "Eurasie"), "déterminisme type")
check(T.distance_parcourue(2.5, 100) == T.distance_parcourue(2.5, 100), "déterminisme distance")
check(T.age_depuis_distance(2.5, 2500) == T.age_depuis_distance(2.5, 2500), "déterminisme âge")
check(T.vitesse_mesuree("himalaya") == T.vitesse_mesuree("himalaya"), "déterminisme vitesse")

print(f"\n=== valide_tectonique_plaques : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
