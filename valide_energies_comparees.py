"""
VALIDE energies_comparees.py — held-out ADVERSE.

Ancres CONNUES (non circulaires — valeurs d'ingénierie énergétique de référence) :
  • facteur de charge solaire PV ≈ 0.15 (1314 MWh / an pour 1 MW installé)
  • facteur de charge nucléaire ≈ 0.9 (7884 MWh / an pour 1 MW installé)
  • EROI = sortie / entrée ; > 1 viable, < 1 non viable
  • facteurs d'émission GIEC AR5 : charbon 820, éolien 11, nucléaire 12 gCO2eq/kWh
  • PCI : gaz naturel ≈ 50 MJ/kg, hydrogène ≈ 120 MJ/kg (produit masse·PCI)
SOUNDNESS : puissance<=0, heures<=0, énergie<0, cf>1, PCI<=0, masse<0,
            énergie investie<=0, facteur<0, source inconnue, non fini -> ValueError.
DÉTERMINISME : mêmes entrées -> mêmes sorties.
"""

import energies_comparees as M

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def approx(a, b, tol=1e-9):
    return abs(a - b) <= tol


def _leve_v(fn, *a, **k):
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) ANCRES — facteur de charge (capacity factor) ──
# Solaire PV : 1 MW produisant 1314 MWh/an -> 1314/8760 = 0.15.
check(approx(M.facteur_charge(1314, 1), 0.15), "solaire PV ≈ 0.15")
# Nucléaire : 1 MW produisant 7884 MWh/an -> 7884/8760 = 0.9.
check(approx(M.facteur_charge(7884, 1), 0.9), "nucléaire ≈ 0.9")
# Définition E/(P·h) sur période arbitraire.
check(approx(M.facteur_charge(4380, 1), 0.5), "demi-charge annuelle = 0.5")
check(approx(M.facteur_charge(12, 1, 24), 0.5), "12 MWh / (1 MW·24 h) = 0.5")
check(approx(M.facteur_charge(0, 5), 0.0), "production nulle -> cf 0")
check(approx(M.facteur_charge(8760, 1), 1.0), "fonctionnement continu -> cf 1")
# Non-circularité : valeur calculée = E/(P·h) explicite.
check(approx(M.facteur_charge(2628, 2, 8760), 2628.0 / (2.0 * 8760.0)),
      "cf = E/(P·h) littéral")
# Bornage [0,1].
for (e, p, h) in [(1314, 1, 8760), (12, 1, 24), (0, 5, 8760), (8760, 1, 8760)]:
    cf = M.facteur_charge(e, p, h)
    check(0.0 <= cf <= 1.0, f"cf dans [0,1] @ ({e},{p},{h})")
# Solaire < nucléaire (ordre physique).
check(M.facteur_charge(1314, 1) < M.facteur_charge(7884, 1),
      "cf solaire < cf nucléaire")

# ── 2) ANCRES — contenu énergétique = masse·PCI (MJ) ──
check(approx(M.contenu_energetique(1, 120), 120.0), "1 kg H2 (120 MJ/kg) -> 120 MJ")
check(approx(M.contenu_energetique(2, 50), 100.0), "2 kg gaz (50 MJ/kg) -> 100 MJ")
check(approx(M.contenu_energetique(1000, 30), 30000.0), "1 t charbon (30 MJ/kg) -> 30000 MJ")
check(approx(M.contenu_energetique(0, 42), 0.0), "masse nulle -> 0 MJ")
# Non-circularité : produit littéral.
check(approx(M.contenu_energetique(3.5, 42.6), 3.5 * 42.6), "contenu = masse·PCI littéral")
# Monotonie : plus de masse -> plus d'énergie.
check(M.contenu_energetique(1, 50) < M.contenu_energetique(2, 50), "énergie croît avec la masse")

# ── 3) ANCRES — EROI / retour énergétique ──
check(approx(M.retour_energetique(10, 1), 10.0), "EROI = 10/1 = 10")
check(approx(M.retour_energetique(20, 1), 20.0), "EROI = 20")
check(approx(M.retour_energetique(15, 3), 5.0), "EROI = 15/3 = 5")
check(approx(M.retour_energetique(2, 4), 0.5), "EROI = 0.5 (< 1, non viable)")
check(approx(M.retour_energetique(1, 1), 1.0), "EROI = 1 (seuil de viabilité)")
check(approx(M.retour_energetique(0, 5), 0.0), "production nulle -> EROI 0")
# Alias eroi == retour_energetique.
check(M.eroi(15, 3) == M.retour_energetique(15, 3), "alias eroi == retour_energetique")
# Sémantique > 1 viable.
check(M.retour_energetique(20, 1) > 1.0 and M.retour_energetique(2, 4) < 1.0,
      "viable > 1, non viable < 1")
# Non-circularité : ratio littéral.
check(approx(M.retour_energetique(7, 11), round(7.0 / 11.0, 6)), "EROI = sortie/entrée littéral")

# ── 4) ANCRES — émissions CO2 = énergie·facteur ──
check(approx(M.emissions_co2(1, 820), 820.0), "charbon 1 kWh -> 820 g")
check(approx(M.emissions_co2(1, 11), 11.0), "éolien 1 kWh -> 11 g")
check(approx(M.emissions_co2(1000, 820), 820000.0), "charbon 1 MWh -> 820 kg (820000 g)")
check(approx(M.emissions_co2(2, 490), 980.0), "gaz 2 kWh -> 980 g")
check(approx(M.emissions_co2(0, 820), 0.0), "énergie nulle -> 0 g")
check(approx(M.emissions_co2(5, 0), 0.0), "facteur nul -> 0 g")
# Non-circularité : produit littéral.
check(approx(M.emissions_co2(3.3, 48), 3.3 * 48.0), "émissions = énergie·facteur littéral")
# Charbon >> éolien (ordre physique).
check(M.emissions_co2(1, 820) > M.emissions_co2(1, 11) * 50,
      "charbon émet > 50× l'éolien")

# ── 5) ANCRES — facteurs d'émission de référence (GIEC AR5) ──
check(approx(M.facteur_co2_reference("charbon"), 820.0), "ref charbon = 820")
check(approx(M.facteur_co2_reference("eolien"), 11.0), "ref éolien = 11")
check(approx(M.facteur_co2_reference("nucleaire"), 12.0), "ref nucléaire = 12")
check(approx(M.facteur_co2_reference("gaz"), 490.0), "ref gaz = 490")
check(approx(M.facteur_co2_reference("Charbon"), 820.0), "ref insensible à la casse")
# Cohérence : combinaison référence -> émissions.
check(approx(M.emissions_co2(1, M.facteur_co2_reference("charbon")), 820.0),
      "émissions charbon via référence = 820 g/kWh")
# Ordre des sources fossile > renouvelable.
check(M.facteur_co2_reference("charbon") > M.facteur_co2_reference("solaire_pv")
      > M.facteur_co2_reference("eolien"), "charbon > solaire > éolien (émissions)")

# ── 6) SOUNDNESS — abstention (ValueError), faux positif INTERDIT ──
check(_leve_v(M.facteur_charge, 100, 0), "puissance 0 -> ValueError")
check(_leve_v(M.facteur_charge, 100, -1), "puissance < 0 -> ValueError")
check(_leve_v(M.facteur_charge, 100, 1, 0), "heures 0 -> ValueError")
check(_leve_v(M.facteur_charge, 100, 1, -5), "heures < 0 -> ValueError")
check(_leve_v(M.facteur_charge, -5, 1), "énergie produite < 0 -> ValueError")
check(_leve_v(M.facteur_charge, 9000, 1), "cf > 1 impossible -> ValueError")
check(_leve_v(M.facteur_charge, 8761, 1, 8760), "cf juste > 1 -> ValueError")
check(_leve_v(M.facteur_charge, float("inf"), 1), "énergie non finie -> ValueError")
check(_leve_v(M.facteur_charge, 100, float("nan")), "puissance NaN -> ValueError")
check(_leve_v(M.contenu_energetique, 1, 0), "PCI 0 -> ValueError")
check(_leve_v(M.contenu_energetique, 1, -5), "PCI < 0 -> ValueError")
check(_leve_v(M.contenu_energetique, -1, 30), "masse < 0 -> ValueError")
check(_leve_v(M.contenu_energetique, float("inf"), 30), "masse non finie -> ValueError")
check(_leve_v(M.retour_energetique, 10, 0), "énergie investie 0 -> ValueError")
check(_leve_v(M.retour_energetique, 10, -2), "énergie investie < 0 -> ValueError")
check(_leve_v(M.retour_energetique, -10, 5), "énergie produite < 0 -> ValueError")
check(_leve_v(M.eroi, 10, 0), "alias eroi : investie 0 -> ValueError")
check(_leve_v(M.emissions_co2, -1, 820), "énergie < 0 -> ValueError")
check(_leve_v(M.emissions_co2, 1, -5), "facteur < 0 -> ValueError")
check(_leve_v(M.emissions_co2, 1, float("inf")), "facteur non fini -> ValueError")
check(_leve_v(M.facteur_co2_reference, "inconnu"), "source inconnue -> ValueError")
check(_leve_v(M.facteur_co2_reference, ""), "source vide -> ValueError")
check(_leve_v(M.facteur_co2_reference, 42), "source non textuelle -> ValueError")

# ── 7) DÉTERMINISME ──
check(M.facteur_charge(1314, 1) == M.facteur_charge(1314, 1), "facteur_charge déterministe")
check(M.contenu_energetique(2, 50) == M.contenu_energetique(2, 50), "contenu déterministe")
check(M.retour_energetique(15, 3) == M.retour_energetique(15, 3), "EROI déterministe")
check(M.emissions_co2(1000, 820) == M.emissions_co2(1000, 820), "émissions déterministe")
check(M.facteur_co2_reference("gaz") == M.facteur_co2_reference("gaz"), "référence déterministe")

print(f"\n=== valide_energies_comparees : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
