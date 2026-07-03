"""
VALIDE automobile.py — held-out ADVERSE.

Ancres CONNUES (non circulaires — recoupées par physique/arithmétique indépendante) :
  • freinage 100 km/h (27.8 m/s) sur µ=0.8 -> ≈ 49 m (référence code de la route / TP physique).
  • doubler la vitesse quadruple la distance d'arrêt : d(2v) = 4·d(v) (loi v²).
  • freinage sur verglas (µ=0.1) >> freinage sur sec (µ=0.8) : rapport exact 8×.
  • puissance : F=3000 N à 30 m/s -> 90 000 W = 90 kW ; P = F·v homogène.
  • rapport 40/10 dents -> 4 (réduction) ; produit régime×rapport conservé.
  • régime : 4000 tr/min moteur, réduction 4 -> 1000 tr/min roue.
  • conso : 40 L sur 500 km -> 8 L/100 km ; 6 L sur 100 km -> 6 L/100 km.
SOUNDNESS : µ<=0, g<=0, vitesse<0, km<=0, litres<0, dents<=0/non entières, rapport<=0,
            entrée booléenne / non numérique / non finie -> ValueError (abstention).
DÉTERMINISME : mêmes entrées -> sorties identiques.
"""

import automobile as A

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def approx(a, b, tol=1e-6):
    return abs(a - b) <= tol


def _leve_v(fn, *a, **k):
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) ANCRES — distance de freinage v²/(2µg) ──
d100 = A.distance_freinage(27.8, 0.8)
check(47.0 < d100 < 51.0, f"100 km/h µ=0.8 -> ≈49 m (obtenu {d100})")
# Recoupement indépendant (calcul main).
check(approx(d100, 27.8 ** 2 / (2 * 0.8 * 9.81)), "d = v²/(2µg) exact")
# Loi v² : doubler la vitesse quadruple la distance.
dv = A.distance_freinage(20.0, 0.8)
d2v = A.distance_freinage(40.0, 0.8)
check(approx(d2v, 4.0 * dv, tol=1e-3), "d(2v) = 4·d(v) (loi v²)")
# Verglas (µ=0.1) vs sec (µ=0.8) : rapport 8×.
sec = A.distance_freinage(27.8, 0.8)
verglas = A.distance_freinage(27.8, 0.1)
check(approx(verglas, 8.0 * sec, tol=1e-3), "µ÷8 -> distance ×8")
# Vitesse nulle -> distance nulle (voiture déjà à l'arrêt).
check(approx(A.distance_freinage(0.0, 0.8), 0.0), "v=0 -> distance 0")
# g personnalisé : sur la Lune (g≈1.62) la distance est plus longue.
check(A.distance_freinage(27.8, 0.8, g=1.62) > d100, "g plus faible -> distance plus longue")
# Valeur exacte simple : v=10, µ=0.5, g=10 -> 100/(2*0.5*10)=10.
check(approx(A.distance_freinage(10.0, 0.5, g=10.0), 10.0), "v=10 µ=0.5 g=10 -> 10 m")

# ── 2) ANCRES — puissance F·v ──
check(approx(A.puissance(3000.0, 30.0), 90000.0), "F=3000 N v=30 -> 90 kW")
check(approx(A.puissance(1000.0, 20.0), 20000.0), "F=1000 N v=20 -> 20 kW")
check(approx(A.puissance(0.0, 30.0), 0.0), "F=0 -> P=0")
check(approx(A.puissance(500.0, 0.0), 0.0), "v=0 -> P=0")
# Force résistante négative (freinage) -> puissance négative admise.
check(approx(A.puissance(-200.0, 10.0), -2000.0), "force négative -> P négative")
# Linéarité.
check(approx(A.puissance(250.0, 12.0), 250.0 * 12.0), "P linéaire en F·v")

# ── 3) ANCRES — rapport de transmission ──
check(approx(A.rapport_transmission(40, 10), 4.0), "40/10 dents -> 4")
check(approx(A.rapport_transmission(13, 39), 1.0 / 3.0), "13/39 -> 1/3 (surmultiplication)")
check(approx(A.rapport_transmission(40.0, 10.0), 4.0), "dents float entières -> 4")
check(approx(A.rapport_transmission(37, 37), 1.0), "dents égales -> rapport 1")
# Inverse exact.
check(approx(A.rapport_transmission(10, 40) * A.rapport_transmission(40, 10), 1.0),
      "rapport(a,b)·rapport(b,a) = 1")

# ── 4) ANCRES — régime de la roue ──
check(approx(A.regime_roue(4000.0, 4.0), 1000.0), "4000 tr/min ÷ 4 -> 1000")
check(approx(A.regime_roue(3000.0, 4.0), 750.0), "3000 ÷ 4 -> 750")
# Cohérence chaîne : N_roue = N_moteur / rapport(menee,menante).
r = A.rapport_transmission(40, 10)
check(approx(A.regime_roue(4000.0, r), 1000.0), "chaîne moteur→engrenage→roue cohérente")
check(approx(A.regime_roue(0.0, 3.5), 0.0), "moteur à 0 tr/min -> roue 0")

# ── 5) ANCRES — consommation L/100 km ──
check(approx(A.consommation_100km(40.0, 500.0), 8.0), "40 L / 500 km -> 8 L/100km")
check(approx(A.consommation_100km(6.0, 100.0), 6.0), "6 L / 100 km -> 6 L/100km")
check(approx(A.consommation_100km(5.5, 110.0), 5.0), "5.5 L / 110 km -> 5 L/100km")
check(approx(A.consommation_100km(0.0, 100.0), 0.0), "0 L consommé -> 0 L/100km")

# ── 6) SOUNDNESS — abstention (ValueError), faux positif INTERDIT ──
check(_leve_v(A.distance_freinage, 27.8, 0.0), "µ=0 -> ValueError")
check(_leve_v(A.distance_freinage, 27.8, -0.5), "µ<0 -> ValueError")
check(_leve_v(A.distance_freinage, -5.0, 0.8), "vitesse<0 -> ValueError")
check(_leve_v(A.distance_freinage, 27.8, 0.8, 0.0), "g=0 -> ValueError")
check(_leve_v(A.distance_freinage, 27.8, 0.8, -9.81), "g<0 -> ValueError")
check(_leve_v(A.distance_freinage, float("inf"), 0.8), "vitesse non finie -> ValueError")
check(_leve_v(A.distance_freinage, float("nan"), 0.8), "vitesse NaN -> ValueError")
check(_leve_v(A.distance_freinage, True, 0.8), "vitesse booléenne -> ValueError")
check(_leve_v(A.distance_freinage, "27.8", 0.8), "vitesse chaîne -> ValueError")

check(_leve_v(A.puissance, 1000.0, -1.0), "puissance vitesse<0 -> ValueError")
check(_leve_v(A.puissance, "x", 10.0), "force non numérique -> ValueError")
check(_leve_v(A.puissance, 1000.0, float("inf")), "vitesse infinie -> ValueError")
check(_leve_v(A.puissance, True, 10.0), "force booléenne -> ValueError")

check(_leve_v(A.rapport_transmission, 40, 0), "dents_menante=0 -> ValueError")
check(_leve_v(A.rapport_transmission, 0, 40), "dents_menee=0 -> ValueError")
check(_leve_v(A.rapport_transmission, 40, -10), "dents<0 -> ValueError")
check(_leve_v(A.rapport_transmission, 40.5, 10), "dents non entières -> ValueError")
check(_leve_v(A.rapport_transmission, True, 10), "dents booléen -> ValueError")
check(_leve_v(A.rapport_transmission, "40", 10), "dents chaîne -> ValueError")

check(_leve_v(A.regime_roue, 4000.0, 0.0), "rapport=0 -> ValueError")
check(_leve_v(A.regime_roue, 4000.0, -4.0), "rapport<0 -> ValueError")
check(_leve_v(A.regime_roue, -100.0, 4.0), "régime moteur<0 -> ValueError")
check(_leve_v(A.regime_roue, 4000.0, float("nan")), "rapport NaN -> ValueError")
check(_leve_v(A.regime_roue, True, 4.0), "régime booléen -> ValueError")

check(_leve_v(A.consommation_100km, 40.0, 0.0), "km=0 -> ValueError")
check(_leve_v(A.consommation_100km, 40.0, -500.0), "km<0 -> ValueError")
check(_leve_v(A.consommation_100km, -1.0, 100.0), "litres<0 -> ValueError")
check(_leve_v(A.consommation_100km, "40", 100.0), "litres chaîne -> ValueError")
check(_leve_v(A.consommation_100km, 40.0, True), "km booléen -> ValueError")

# ── 7) DÉTERMINISME ──
check(A.distance_freinage(27.8, 0.8) == A.distance_freinage(27.8, 0.8), "freinage déterministe")
check(A.puissance(1234.5, 21.7) == A.puissance(1234.5, 21.7), "puissance déterministe")
check(A.rapport_transmission(41, 13) == A.rapport_transmission(41, 13), "rapport déterministe")
check(A.regime_roue(3210.0, 3.7) == A.regime_roue(3210.0, 3.7), "régime déterministe")
check(A.consommation_100km(7.3, 137.0) == A.consommation_100km(7.3, 137.0), "conso déterministe")

print(f"\n=== valide_automobile : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
