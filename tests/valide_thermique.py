"""
VALIDE thermique.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (valeurs connues ou calculées À LA MAIN, PAS recalculées par la
formule testée) :
  • 1 kg d'eau de 20 à 100 °C : Q = 1 × 4185 × 80 = 334 800 J (multiplication posée à la main).
  • Fondre 1 kg de glace à 0 °C : Q = 334 000 J (chaleur latente de fusion de l'eau, valeur de manuel).
  • Mélange 1 kg d'eau à 80 °C + 1 kg d'eau à 20 °C -> 50 °C EXACTEMENT (SYMÉTRIE : mêmes masses,
    même matériau, la moyenne (80+20)/2 doit tomber juste — argument physique indépendant de la formule).
  • BILAN NON CIRCULAIRE : chaleur cédée par le corps chaud = chaleur reçue par le corps froid,
    calculées par DEUX appels SÉPARÉS à chaleur_sensible (second chemin de code, conservation de
    l'énergie comme juge).
  • Catalogue : valeurs de manuel écrites EN DUR (eau 4185, glace 2090, vapeur 2010, aluminium 897,
    fer 449, cuivre 385, plomb 129, verre 840, air 1005 J·kg⁻¹·K⁻¹).

SOUNDNESS : m≤0, c≤0, L≤0, matériau hors catalogue, bool/str/NaN/inf, mauvaise arité -> ValueError ;
OVERFLOW en sortie (produit qui déborde le flottant -> inf, ou inf/inf -> nan) -> ValueError,
jamais un nan/inf rendu (garde de finitude en SORTIE, prouvée en adverse section 11).
"""
import math

import thermique as TH

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


# ── 1) ANCRES IMPOSÉES — chaleur sensible et latente (calculs À LA MAIN) ──
# 1 kg d'eau de 20 à 100 °C : 1 × 4185 × 80 = 334 800 J (posé à la main : 4185×8=33480, ×10)
check(proche(TH.chaleur_sensible(1.0, 4185.0, 80.0), 334800.0), "1 kg eau 20->100 °C = 334800 J")
# Fondre 1 kg de glace à 0 °C : 334 000 J (valeur de manuel, chaleur latente de fusion)
check(proche(TH.chaleur_latente(1.0, 334000.0), 334000.0), "fondre 1 kg glace = 334000 J")
check(proche(TH.chaleur_latente(1.0, TH.CHALEUR_LATENTE_FUSION_EAU), 334000.0),
      "constante fusion eau = 334000 J/kg")
# Vaporiser 2 kg d'eau : 2 × 2 257 000 = 4 514 000 J (doublement à la main)
check(proche(TH.chaleur_latente(2.0, TH.CHALEUR_LATENTE_VAPORISATION_EAU), 4514000.0),
      "vaporiser 2 kg eau = 4514000 J")
# 0.5 kg d'aluminium chauffé de 10 K : 0.5 × 897 × 10 = 4485 J (à la main : 897×5=4485)
check(proche(TH.chaleur_sensible(0.5, 897.0, 10.0), 4485.0), "0.5 kg alu +10 K = 4485 J")
# 2 kg de cuivre chauffés de 5 K : 2 × 385 × 5 = 3850 J (à la main : 385×10=3850)
check(proche(TH.chaleur_sensible(2.0, 385.0, 5.0), 3850.0), "2 kg cuivre +5 K = 3850 J")
# Refroidissement (ΔT<0) : 1 kg d'eau −30 K -> Q = −125 550 J (à la main : 4185×3=12555, ×10, signe −)
check(proche(TH.chaleur_sensible(1.0, 4185.0, -30.0), -125550.0), "1 kg eau -30 K = -125550 J (cédée)")

# ── 2) ANCRE IMPOSÉE — mélange symétrique : 1 kg 80 °C + 1 kg 20 °C (même eau) -> 50 °C EXACT ──
# Symétrie physique : masses égales, même matériau -> l'équilibre est la moyenne (80+20)/2 = 50,
# connue INDÉPENDAMMENT de la formule barycentrique.
T_eq_sym = TH.temperature_equilibre(1.0, 4185.0, 80.0, 1.0, 4185.0, 20.0)
check(T_eq_sym == 50.0, "mélange symétrique 80/20 °C -> 50 °C EXACTEMENT")
# Invariance par échange des deux corps (aucun rôle privilégié) :
check(TH.temperature_equilibre(1.0, 4185.0, 20.0, 1.0, 4185.0, 80.0) == 50.0,
      "échange des corps -> même équilibre 50 °C")

# ── 3) ANCRE — mélange asymétrique calculé À LA MAIN (même eau) ──
# 2 kg à 80 °C + 1 kg à 20 °C : (2×80 + 1×20)/3 = 180/3 = 60 °C (les c s'annulent, division posée)
check(proche(TH.temperature_equilibre(2.0, 4185.0, 80.0, 1.0, 4185.0, 20.0), 60.0),
      "2 kg 80 °C + 1 kg 20 °C -> 60 °C (180/3 à la main)")
# 3 kg à 30 °C + 2 kg à 80 °C : (3×30 + 2×80)/5 = (90+160)/5 = 250/5 = 50 °C (à la main)
check(proche(TH.temperature_equilibre(3.0, 4185.0, 30.0, 2.0, 4185.0, 80.0), 50.0),
      "3 kg 30 °C + 2 kg 80 °C -> 50 °C (250/5 à la main)")

# ── 4) BILAN NON CIRCULAIRE — conservation de l'énergie par DEUX appels séparés ──
# Cas eau/eau : chaud 2 kg 80 °C, froid 3 kg 30 °C -> T_eq = 50 °C (ancre ci-dessus).
# Q_chaud = 2×4185×(50−80) = −251 100 J ; Q_froid = 3×4185×(50−30) = +251 100 J (à la main).
Q_chaud = TH.chaleur_sensible(2.0, 4185.0, 50.0 - 80.0)
Q_froid = TH.chaleur_sensible(3.0, 4185.0, 50.0 - 30.0)
check(proche(Q_chaud, -251100.0), "Q cédée par le chaud = -251100 J (à la main)")
check(proche(Q_froid, 251100.0), "Q reçue par le froid = +251100 J (à la main)")
check(proche(Q_chaud + Q_froid, 0.0), "bilan : Q_chaud + Q_froid = 0 (conservation)")

# Cas MATÉRIAUX DIFFÉRENTS : 1 kg d'eau à 20 °C + 0.5 kg de fer à 200 °C.
# Juge = conservation de l'énergie (second chemin) : m1c1(Teq−T1) + m2c2(Teq−T2) ≈ 0.
T_eq_fer = TH.temperature_equilibre(1.0, 4185.0, 20.0, 0.5, 449.0, 200.0)
Q_eau = TH.chaleur_sensible(1.0, 4185.0, T_eq_fer - 20.0)
Q_fer = TH.chaleur_sensible(0.5, 449.0, T_eq_fer - 200.0)
check(proche(Q_eau + Q_fer, 0.0, tol=1e-3), "bilan eau/fer : somme des chaleurs ≈ 0 (conservation)")
check(Q_eau > 0 and Q_fer < 0, "l'eau reçoit (Q>0), le fer cède (Q<0)")
# Encadrement physique : T_eq strictement entre les deux températures initiales
check(20.0 < T_eq_fer < 200.0, "T_eq entre T_froid et T_chaud (barycentre)")
# L'eau domine (m·c eau = 4185 >> m·c fer = 224.5) : T_eq proche de 20 °C, sous la moyenne 110 °C
check(T_eq_fer < 110.0, "grande capacité de l'eau -> T_eq tirée vers l'eau")

# ── 5) CHAÎNE glace -> vapeur, sous-totaux À LA MAIN ──
# 2 kg de glace de −10 °C jusqu'à vapeur à 100 °C :
#   chauffer la glace : 2×2090×10 = 41 800 J ; fondre : 2×334000 = 668 000 J ;
#   chauffer l'eau 0->100 : 2×4185×100 = 837 000 J ; vaporiser : 2×2257000 = 4 514 000 J.
#   TOTAL (somme posée à la main) = 41800 + 668000 + 837000 + 4514000 = 6 060 800 J.
q1 = TH.chaleur_sensible(2.0, 2090.0, 10.0)
q2 = TH.chaleur_latente(2.0, 334000.0)
q3 = TH.chaleur_sensible(2.0, 4185.0, 100.0)
q4 = TH.chaleur_latente(2.0, 2257000.0)
check(proche(q1, 41800.0), "chauffer 2 kg glace +10 K = 41800 J")
check(proche(q2, 668000.0), "fondre 2 kg glace = 668000 J")
check(proche(q3, 837000.0), "chauffer 2 kg eau 0->100 = 837000 J")
check(proche(q4, 4514000.0), "vaporiser 2 kg eau = 4514000 J")
check(proche(q1 + q2 + q3 + q4, 6060800.0), "chaîne glace->vapeur totale = 6060800 J (somme à la main)")

# ── 6) CATALOGUE — valeurs de manuel EN DUR (J·kg⁻¹·K⁻¹, ~25 °C) ──
check(TH.capacite_massique("eau") == 4185.0, "c eau = 4185")
check(TH.capacite_massique("glace") == 2090.0, "c glace = 2090")
check(TH.capacite_massique("vapeur") == 2010.0, "c vapeur = 2010")
check(TH.capacite_massique("aluminium") == 897.0, "c aluminium = 897")
check(TH.capacite_massique("fer") == 449.0, "c fer = 449")
check(TH.capacite_massique("cuivre") == 385.0, "c cuivre = 385")
check(TH.capacite_massique("plomb") == 129.0, "c plomb = 129")
check(TH.capacite_massique("verre") == 840.0, "c verre = 840")
check(TH.capacite_massique("air") == 1005.0, "c air (cp) = 1005")
# Normalisation d'écriture (même clé, pas une devinette) :
check(TH.capacite_massique("  EAU ") == 4185.0, "catalogue insensible casse/espaces")
# Ordre physique connu : c_eau > c_verre > c_fer > c_plomb (classement de manuel)
check(TH.capacite_massique("eau") > TH.capacite_massique("verre")
      > TH.capacite_massique("fer") > TH.capacite_massique("plomb"),
      "ordre des capacités : eau > verre > fer > plomb")

# ── 7) SOUNDNESS — masses ──
check(leve(TH.chaleur_sensible, 0.0, 4185.0, 10.0), "m=0 -> ValueError")
check(leve(TH.chaleur_sensible, -1.0, 4185.0, 10.0), "m<0 -> ValueError")
check(leve(TH.chaleur_latente, 0.0, 334000.0), "latente m=0 -> ValueError")
check(leve(TH.temperature_equilibre, -2.0, 4185.0, 80.0, 1.0, 4185.0, 20.0), "équilibre m1<0 -> ValueError")
check(leve(TH.temperature_equilibre, 1.0, 4185.0, 80.0, 0.0, 4185.0, 20.0), "équilibre m2=0 -> ValueError")

# ── 8) SOUNDNESS — capacités / chaleur latente ──
check(leve(TH.chaleur_sensible, 1.0, 0.0, 10.0), "c=0 -> ValueError")
check(leve(TH.chaleur_sensible, 1.0, -449.0, 10.0), "c<0 -> ValueError")
check(leve(TH.chaleur_latente, 1.0, 0.0), "L=0 -> ValueError")
check(leve(TH.chaleur_latente, 1.0, -334000.0), "L<0 -> ValueError")
check(leve(TH.temperature_equilibre, 1.0, -1.0, 80.0, 1.0, 4185.0, 20.0), "équilibre c1<0 -> ValueError")

# ── 9) SOUNDNESS — matériau hors catalogue (abstention, catalogue CLOS) ──
check(leve(TH.capacite_massique, "bois"), "matériau 'bois' hors catalogue -> ValueError")
check(leve(TH.capacite_massique, "or"), "matériau 'or' hors catalogue -> ValueError")
check(leve(TH.capacite_massique, ""), "matériau vide -> ValueError")
check(leve(TH.capacite_massique, 4185.0), "matériau non-str -> ValueError")
check(leve(TH.capacite_massique, None), "matériau None -> ValueError")

# ── 10) SOUNDNESS — types invalides (bool / str / NaN / inf) ──
check(leve(TH.chaleur_sensible, True, 4185.0, 10.0), "m bool -> ValueError")
check(leve(TH.chaleur_sensible, 1.0, True, 10.0), "c bool -> ValueError")
check(leve(TH.chaleur_sensible, 1.0, 4185.0, True), "ΔT bool -> ValueError")
check(leve(TH.chaleur_sensible, "1", 4185.0, 10.0), "m str -> ValueError")
check(leve(TH.chaleur_sensible, float("nan"), 4185.0, 10.0), "m NaN -> ValueError")
check(leve(TH.chaleur_sensible, 1.0, 4185.0, float("nan")), "ΔT NaN -> ValueError")
check(leve(TH.chaleur_sensible, 1.0, 4185.0, float("inf")), "ΔT inf -> ValueError")
check(leve(TH.chaleur_sensible, 1.0, float("inf"), 10.0), "c inf -> ValueError")
check(leve(TH.chaleur_latente, 1.0, float("nan")), "L NaN -> ValueError")
check(leve(TH.chaleur_latente, float("inf"), 334000.0), "latente m inf -> ValueError")
check(leve(TH.temperature_equilibre, 1.0, 4185.0, float("nan"), 1.0, 4185.0, 20.0),
      "équilibre T1 NaN -> ValueError")
check(leve(TH.temperature_equilibre, 1.0, 4185.0, 80.0, 1.0, 4185.0, float("inf")),
      "équilibre T2 inf -> ValueError")
check(leve(TH.temperature_equilibre, 1.0, 4185.0, True, 1.0, 4185.0, 20.0),
      "équilibre T1 bool -> ValueError")
check(leve(TH.temperature_equilibre, 1.0, 4185.0, 80.0, True, 4185.0, 20.0),
      "équilibre m2 bool -> ValueError")

# ── 11) SOUNDNESS — OVERFLOW en sortie : jamais un nan/inf rendu (abstention structurelle) ──
# Entrées finies mais dont le PRODUIT déborde le flottant (max ~1.8e308) :
#   1e300 × 1e300 = 1e600 -> inf ; l'équilibre donne inf/inf -> nan. FAUX=0 exige ValueError,
#   pas une valeur non finie qui violerait « T_eq entre min(T1,T2) et max(T1,T2) ».
check(leve(TH.chaleur_sensible, 1e300, 1e300, 10.0), "overflow m·c·ΔT -> ValueError (pas inf)")
check(leve(TH.chaleur_latente, 1e300, 1e300), "overflow m·L -> ValueError (pas inf)")
check(leve(TH.temperature_equilibre, 1e200, 1e200, 80.0, 1.0, 4185.0, 20.0),
      "overflow équilibre (inf/inf -> nan) -> ValueError (pas nan)")
check(leve(TH.temperature_equilibre, 1e300, 1e300, 80.0, 1e300, 1e300, 20.0),
      "overflow équilibre des deux corps -> ValueError")
check(leve(TH.chaleur_sensible, 1e155, 1e155, -1e10), "overflow négatif (-inf) -> ValueError")
# Contrôle : de GRANDES valeurs qui ne débordent PAS restent servies (pas de sur-abstention) :
# 1e10 × 4185 × 80 = 3.348e15 J (posé à la main : 4185×8=33480 -> 3348e12)
check(proche(TH.chaleur_sensible(1e10, 4185.0, 80.0), 3.348e15, tol=1e6),
      "grande masse finie : 1e10 kg d'eau +80 K = 3.348e15 J (servi, pas d'abstention abusive)")

# ── 12) DÉTERMINISME ──
check(TH.chaleur_sensible(1.0, 4185.0, 80.0) == TH.chaleur_sensible(1.0, 4185.0, 80.0),
      "déterminisme chaleur_sensible")
check(TH.chaleur_latente(1.0, 334000.0) == TH.chaleur_latente(1.0, 334000.0),
      "déterminisme chaleur_latente")
check(TH.temperature_equilibre(1.0, 4185.0, 80.0, 1.0, 4185.0, 20.0)
      == TH.temperature_equilibre(1.0, 4185.0, 80.0, 1.0, 4185.0, 20.0),
      "déterminisme temperature_equilibre")
check(TH.capacite_massique("cuivre") == TH.capacite_massique("cuivre"), "déterminisme catalogue")

print(f"\n=== valide_thermique : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
