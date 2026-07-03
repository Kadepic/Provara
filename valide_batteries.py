"""VALIDE batteries.py — held-out ADVERSE.

Ancres EXTERNES connues du domaine du stockage (non recalculées par la même expression du module) :
  • batterie 12 V / 100 Ah -> 1200 Wh = 1.2 kWh (chiffre catalogue universel) ;
  • cellule 18650 type 3.7 V / 2.6 Ah -> ~9.62 Wh (datasheet) ;
  • 100 Ah à 2C -> 200 A ; 100 Ah à 0.5C -> 50 A (définition du C-rate) ;
  • 100 Ah chargés à 50 A -> 2 h ; à 100 A (1C) -> 1 h ;
  • Li-ion aller-retour ~90 % -> 0.9.
+ SOUNDNESS : grandeur ≤ 0, type bool/str, rendement > 1 (sur-unité) -> ValueError (jamais un faux). + déterminisme.
"""
import batteries as B

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def approx(x, attendu, tol=1e-6):
    return abs(x - attendu) <= tol * max(1.0, abs(attendu))


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True


# ── 1) ANCRES — énergie stockée V·Ah ──
check(B.energie_wh(12, 100) == 1200, "12 V · 100 Ah = 1200 Wh (1.2 kWh)")
check(approx(B.energie_wh(3.7, 2.6), 9.62), "cellule 18650 3.7 V · 2.6 Ah ≈ 9.62 Wh")
check(B.energie_wh(48, 200) == 9600, "48 V · 200 Ah = 9600 Wh (9.6 kWh)")
check(approx(B.energie_wh(3.2, 280), 896.0), "LiFePO4 3.2 V · 280 Ah = 896 Wh")

# ── 2) ANCRES — capacité depuis énergie (inverse) ──
check(B.capacite_Ah_depuis_energie(1200, 12) == 100, "1200 Wh / 12 V = 100 Ah")
check(approx(B.capacite_Ah_depuis_energie(9600, 48), 200.0), "9600 Wh / 48 V = 200 Ah")
# cohérence aller-retour V·Ah puis ÷V
check(approx(B.capacite_Ah_depuis_energie(B.energie_wh(24, 75), 24), 75.0), "inverse exact (24 V, 75 Ah)")

# ── 3) ANCRES — C-rate -> courant ──
check(B.courant_c_rate(100, 2) == 200, "100 Ah à 2C = 200 A")
check(B.courant_c_rate(100, 0.5) == 50, "100 Ah à 0.5C = 50 A")
check(B.courant_c_rate(100, 1) == 100, "100 Ah à 1C = 100 A")
check(approx(B.courant_c_rate(2.6, 0.5), 1.3), "cellule 2.6 Ah à 0.5C = 1.3 A")

# ── 4) ANCRES — temps de charge Ah/I ──
check(B.temps_charge(100, 50) == 2, "100 Ah à 50 A = 2 h")
check(B.temps_charge(100, 100) == 1, "100 Ah à 100 A (1C) = 1 h")
check(approx(B.temps_charge(100, 40), 2.5), "100 Ah à 40 A = 2.5 h")

# ── 5) ANCRES — rendement ──
check(B.rendement_energetique(90, 100) == 0.9, "rendement 90/100 = 0.9")
check(approx(B.rendement_energetique(95, 100), 0.95), "Li-ion ~95 % aller-retour")
check(B.rendement_energetique(100, 100) == 1.0, "rendement idéal limite = 1.0")

# ── 6) SOUNDNESS — grandeurs ≤ 0 -> ValueError ──
check(leve(B.energie_wh, 0, 100), "tension 0 -> ValueError")
check(leve(B.energie_wh, -12, 100), "tension < 0 -> ValueError")
check(leve(B.energie_wh, 12, 0), "capacité 0 -> ValueError")
check(leve(B.energie_wh, 12, -100), "capacité < 0 -> ValueError")
check(leve(B.capacite_Ah_depuis_energie, 1200, 0), "tension 0 (division) -> ValueError")
check(leve(B.capacite_Ah_depuis_energie, -1200, 12), "énergie < 0 -> ValueError")
check(leve(B.courant_c_rate, 100, 0), "C-rate 0 -> ValueError")
check(leve(B.courant_c_rate, -100, 2), "capacité < 0 -> ValueError")
check(leve(B.temps_charge, 100, 0), "courant 0 (division) -> ValueError")
check(leve(B.temps_charge, 100, -50), "courant < 0 -> ValueError")

# ── 7) SOUNDNESS — rendement hors domaine ──
check(leve(B.rendement_energetique, 110, 100), "rendement > 1 (sur-unité) -> ValueError")
check(leve(B.rendement_energetique, 0, 100), "e_out 0 -> ValueError")
check(leve(B.rendement_energetique, 90, 0), "e_in 0 -> ValueError")
check(leve(B.rendement_energetique, 100.0000001, 100), "rendement à peine > 1 -> ValueError")

# ── 8) SOUNDNESS — types invalides (bool/str) -> ValueError ──
check(leve(B.energie_wh, True, 100), "bool n'est pas un nombre -> ValueError")
check(leve(B.energie_wh, "12", 100), "str -> ValueError")
check(leve(B.courant_c_rate, 100, False), "bool C-rate -> ValueError")

# ── 9) DÉTERMINISME ──
check(B.energie_wh(12, 100) == B.energie_wh(12, 100), "déterminisme")

print(f"\n=== valide_batteries : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
