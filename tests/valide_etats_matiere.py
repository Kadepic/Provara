"""VALIDE etats_matiere.py — ADVERSE, FAUX=0. États physiques connus (eau, azote, fer), conversions d'échelles
(points fixes) + SOUNDNESS (points incohérents, sous le zéro absolu -> ValueError)."""
import etats_matiere as E

ok = 0
ko = 0


def check(c, l):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {l}")


def proche(a, b, t=1e-6):
    return abs(a - b) <= t


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ÉTATS PHYSIQUES (eau : 0/100 °C)
check(E.etat_physique(-10, 0, 100) == "solide", "eau -10 °C -> solide")
check(E.etat_physique(0, 0, 100) == "liquide", "eau 0 °C -> liquide (fusion)")
check(E.etat_physique(25, 0, 100) == "liquide", "eau 25 °C -> liquide")
check(E.etat_physique(100, 0, 100) == "gaz", "eau 100 °C -> gaz (ébullition)")
check(E.etat_physique(150, 0, 100) == "gaz", "eau 150 °C -> gaz")
# azote (fusion -210, ébullition -196 °C) : à 20 °C c'est un gaz
check(E.etat_physique(20, -210, -196) == "gaz", "azote à 20 °C -> gaz")
check(E.etat_physique(-200, -210, -196) == "liquide", "azote -200 °C -> liquide")
# fer (fusion 1538, ébullition 2862 °C) : solide à 20 °C
check(E.etat_physique(20, 1538, 2862) == "solide", "fer à 20 °C -> solide")
check(E.etat_physique(2000, 1538, 2862) == "liquide", "fer 2000 °C -> liquide")

# CONVERSIONS (points fixes connus)
check(E.celsius_vers_kelvin(0) == 273.15 and E.celsius_vers_kelvin(100) == 373.15, "°C -> K")
check(E.kelvin_vers_celsius(273.15) == 0.0 and E.kelvin_vers_celsius(0) == -273.15, "K -> °C")
check(E.celsius_vers_fahrenheit(100) == 212.0 and E.celsius_vers_fahrenheit(0) == 32.0, "°C -> °F")
check(E.fahrenheit_vers_celsius(32) == 0.0 and E.fahrenheit_vers_celsius(212) == 100.0, "°F -> °C")
check(E.celsius_vers_fahrenheit(-40) == -40.0, "−40 : même valeur en °C et °F")
# aller-retour
check(proche(E.kelvin_vers_celsius(E.celsius_vers_kelvin(37)), 37), "aller-retour °C↔K")

# SOUNDNESS
check(leve(E.etat_physique, 25, 100, 0), "fusion ≥ ébullition -> ValueError")
check(leve(E.celsius_vers_kelvin, -300), "sous le zéro absolu -> ValueError")
check(leve(E.kelvin_vers_celsius, -1), "Kelvin négatif -> ValueError")
check(leve(E.etat_physique, "chaud", 0, 100), "température non numérique -> ValueError")

# DÉTERMINISME
check(E.etat_physique(25, 0, 100) == E.etat_physique(25, 0, 100), "déterminisme")

print(f"\n=== valide_etats_matiere : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
