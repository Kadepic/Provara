"""
VALIDE conservation_aliments.py — held-out ADVERSE. Ancres établies (congélation -18 °C, zone de danger 4-63 °C,
pasteurisation 72 °C/15 s, UHT 135 °C, seuil aw 0.91) + distinctions microbiologiques (pasteurisation laisse les
spores, stérilisation les détruit) + SOUNDNESS (méthode inconnue / entrée invalide / aw hors [0,1] -> ValueError)
+ déterminisme. Aucun de ces cas n'est dans __main__ du module.
"""
import conservation_aliments as C

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def _leve(fn, *a, **k):
    """True ssi fn(*a, **k) lève ValueError (abstention), False sinon."""
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


EPS = 1e-12

# 1) ANCRE — CONGÉLATION -18 °C.
mc = C.methode("congelation")
check(mc.temperature_c == -18.0, "congélation -> -18 °C")
check(mc.nom == "congelation", "congélation : nom canonique")
check("arr" in mc.principe.lower() or "stop" in mc.principe.lower(), "congélation : croissance arrêtée")

# 2) ANCRE — ZONE DE DANGER 4-63 °C (fait HACCP).
z = C.zone_danger_temperature()
check(z == (4, 63), "zone de danger == (4, 63)")
check(z.min_c == 4 and z.max_c == 63, "zone de danger : bornes 4 et 63")
check(C.dans_zone_danger(20) is True, "20 °C dans la zone de danger")
check(C.dans_zone_danger(2) is False, "2 °C hors zone (froid)")
check(C.dans_zone_danger(70) is False, "70 °C hors zone (chaud)")
check(C.dans_zone_danger(4) is False, "4 °C borne -> hors (exclue)")
check(C.dans_zone_danger(63) is False, "63 °C borne -> hors (exclue)")

# 3) ANCRE — PASTEURISATION 72 °C / 15 s (HTST).
mp = C.methode("pasteurisation")
check(mp.temperature_c == 72.0, "pasteurisation -> 72 °C")
check(mp.duree_s == 15.0, "pasteurisation -> 15 s")
check("vege" in mp.principe.lower().replace("é", "e") or "spore" in mp.principe.lower(),
      "pasteurisation : formes végétatives / spores survivent")

# 4) ANCRE — STÉRILISATION / UHT 135 °C, détruit les spores.
ms = C.methode("sterilisation/UHT")
check(ms.temperature_c == 135.0, "UHT -> 135 °C")
check("spore" in ms.principe.lower(), "UHT : détruit les spores")
check(C.methode("uht") == ms, "alias 'uht' -> sterilisation/UHT")
check(C.methode("Stérilisation/UHT") == ms, "casse + accents normalisés")

# 5) ANCRE — RÉFRIGÉRATION 0-4 °C.
mr = C.methode("refrigeration")
check(mr.plage_c == (0.0, 4.0), "réfrigération -> plage 0 à 4 °C")
check(mr.temperature_c is None, "réfrigération : pas de température unique (plage)")
check(C.methode("réfrigération") == mr, "accents tolérés sur réfrigération")

# 6) MÉTHODES SANS TEMPÉRATURE — séchage / salaison / fumage / appertisation : principe + paramètre non vides.
for nom in ("sechage", "salaison", "fumage", "appertisation"):
    m = C.methode(nom)
    check(m.nom == nom, f"{nom} : nom canonique")
    check(isinstance(m.principe, str) and len(m.principe) > 0, f"{nom} : principe renseigné")
    check(isinstance(m.parametre, str) and len(m.parametre) > 0, f"{nom} : paramètre renseigné")
check("aw" in C.methode("sechage").principe.lower(), "séchage : repose sur l'activité de l'eau")
check("sel" in C.methode("salaison").parametre.lower(), "salaison : apport de sel")

# 7) CATALOGUE COMPLET — exactement les 8 méthodes attendues.
attendues = ("appertisation", "congelation", "fumage", "pasteurisation",
             "refrigeration", "salaison", "sechage", "sterilisation/uht")
check(C.methodes() == attendues, "catalogue = 8 méthodes attendues")
check(len(C.methodes()) == 8, "8 méthodes")

# 8) ANCRE — ACTIVITÉ DE L'EAU : seuil 0.91, bactéries inhibées si aw < 0.91 (strict).
check(C.activite_eau_limite() == 0.91, "seuil aw = 0.91")
check(C.bacteries_inhibees(0.90) is True, "aw=0.90 -> bactéries inhibées")
check(C.bacteries_inhibees(0.85) is True, "aw=0.85 -> inhibées")
check(C.bacteries_inhibees(0.95) is False, "aw=0.95 -> non inhibées (croissance possible)")
check(C.bacteries_inhibees(0.91) is False, "aw=0.91 -> non inhibées (seuil strict)")
check(C.bacteries_inhibees(0.0) is True, "aw=0 -> inhibées")
check(C.bacteries_inhibees(1.0) is False, "aw=1 -> non inhibées")

# 9) SOUNDNESS — méthode hors catalogue / entrée invalide -> ValueError (jamais devinée).
check(_leve(C.methode, "lyophilisation"), "méthode inconnue 'lyophilisation' -> ValueError")
check(_leve(C.methode, "irradiation"), "méthode inconnue 'irradiation' -> ValueError")
check(_leve(C.methode, "sterilisation"), "ambigu 'sterilisation' seul -> ValueError")
check(_leve(C.methode, ""), "chaîne vide -> ValueError")
check(_leve(C.methode, "   "), "espaces seuls -> ValueError")
check(_leve(C.methode, 123), "nom non textuel -> ValueError")
check(_leve(C.methode, None), "nom None -> ValueError")
check(_leve(C.methode, True), "nom booléen -> ValueError")

# 10) SOUNDNESS — activité de l'eau hors [0,1] / invalide -> ValueError (jamais un faux).
check(_leve(C.bacteries_inhibees, 1.5), "aw=1.5 hors [0,1] -> ValueError")
check(_leve(C.bacteries_inhibees, -0.1), "aw=-0.1 hors [0,1] -> ValueError")
check(_leve(C.bacteries_inhibees, "0.9"), "aw chaîne -> ValueError")
check(_leve(C.bacteries_inhibees, None), "aw None -> ValueError")
check(_leve(C.bacteries_inhibees, True), "aw booléen -> ValueError")
check(_leve(C.bacteries_inhibees, float("nan")), "aw NaN -> ValueError")
check(_leve(C.bacteries_inhibees, float("inf")), "aw inf -> ValueError")

# 11) SOUNDNESS — température dans_zone_danger invalide -> ValueError.
check(_leve(C.dans_zone_danger, "20"), "température chaîne -> ValueError")
check(_leve(C.dans_zone_danger, None), "température None -> ValueError")
check(_leve(C.dans_zone_danger, True), "température booléenne -> ValueError")
check(_leve(C.dans_zone_danger, float("nan")), "température NaN -> ValueError")

# 12) DÉTERMINISME.
check(C.methode("congelation") == C.methode("congelation"), "déterminisme methode")
check(C.zone_danger_temperature() == C.zone_danger_temperature(), "déterminisme zone_danger")
check(C.bacteries_inhibees(0.80) == C.bacteries_inhibees(0.80), "déterminisme bacteries_inhibees")
check(C.activite_eau_limite() == C.activite_eau_limite(), "déterminisme activite_eau_limite")

print(f"\n=== valide_conservation_aliments : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
