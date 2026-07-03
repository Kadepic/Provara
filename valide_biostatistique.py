"""
VALIDE biostatistique.py — held-out ADVERSE.

Trois fronts :
  (1) EXACTITUDE sur ancres CONNUES, indépendantes (valeurs d'épidémiologie classiques, pas re-dérivées par la même
      expression que le module) : Se=0.9, Sp=0.8, VPP, prévalence, RV+...
  (2) SOUNDNESS : effectifs négatifs, dénominateurs nuls, types invalides, proba hors [0,1], malades>total -> ValueError.
  (3) DÉTERMINISME : deux appels identiques rendent exactement la même valeur.
"""
import biostatistique as B

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def approx(a, b, rel=1e-12):
    return abs(a - b) <= rel * abs(b) + 1e-15


def leve(fn, *a, **k):
    """Vrai si fn(*a, **k) lève bien ValueError (abstention)."""
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── (1) EXACTITUDE — ancres connues ─────────────────────────────────────────────────────────────────────────────
# CAS de la spéc : VP=90, FN=10 -> Se=0.9
check(approx(B.sensibilite(90, 10), 0.9), "Se(90,10)=0.9")
# VN=80, FP=20 -> Sp=0.8
check(approx(B.specificite(80, 20), 0.8), "Sp(80,20)=0.8")
# VPP sur le même tableau VP=90, FP=20 -> 90/110
check(approx(B.valeur_predictive_positive(90, 20), 90 / 110), "VPP(90,20)=90/110")
# VPN VN=80, FN=10 -> 80/90
check(approx(B.valeur_predictive_negative(80, 10), 80 / 90), "VPN(80,10)=80/90")

# Tableau « parfait » (test idéal) : Se=Sp=VPP=VPN=1
check(B.sensibilite(50, 0) == 1.0, "Se test parfait = 1")
check(B.specificite(50, 0) == 1.0, "Sp test parfait = 1")
check(B.valeur_predictive_positive(50, 0) == 1.0, "VPP test parfait = 1")
check(B.valeur_predictive_negative(50, 0) == 1.0, "VPN test parfait = 1")

# Test inutile (ne détecte personne) : VP=0 -> Se=0
check(B.sensibilite(0, 30) == 0.0, "Se(0,30)=0")
check(B.specificite(0, 30) == 0.0, "Sp(0,30)=0")

# Prévalence connue : 200 malades / 1000 -> 0.2
check(approx(B.prevalence(200, 1000), 0.2), "prevalence(200,1000)=0.2")
check(B.prevalence(0, 10) == 0.0, "prevalence(0,10)=0")
check(B.prevalence(10, 10) == 1.0, "prevalence(10,10)=1")

# Rapport de vraisemblance positif : Se=0.9, Sp=0.8 -> 0.9/0.2 = 4.5
check(approx(B.rapport_vraisemblance_positif(0.9, 0.8), 4.5), "RV+(0.9,0.8)=4.5")
# RV- : (1-0.9)/0.8 = 0.125
check(approx(B.rapport_vraisemblance_negatif(0.9, 0.8), 0.125), "RV-(0.9,0.8)=0.125")
# Test sans valeur (Se=Sp=0.5) -> RV+ = 1 (n'apporte rien)
check(approx(B.rapport_vraisemblance_positif(0.5, 0.5), 1.0), "RV+(0.5,0.5)=1")

# Exactitude : (90+80)/(90+80+20+10) = 170/200 = 0.85
check(approx(B.exactitude(90, 80, 20, 10), 0.85), "exactitude=0.85")

# Cohérence : VPP par formule == VPP recalculé à la main sur un autre tableau
check(approx(B.valeur_predictive_positive(15, 5), 0.75), "VPP(15,5)=0.75")

# ── (2) SOUNDNESS — effectifs négatifs -> ValueError ────────────────────────────────────────────────────────────
check(leve(B.sensibilite, -1, 10), "VP<0 -> ValueError")
check(leve(B.sensibilite, 10, -1), "FN<0 -> ValueError")
check(leve(B.specificite, -5, 5), "VN<0 -> ValueError")
check(leve(B.valeur_predictive_positive, 10, -2), "FP<0 -> ValueError")
check(leve(B.prevalence, -1, 10), "malades<0 -> ValueError")
check(leve(B.exactitude, -1, 1, 1, 1), "exactitude effectif<0 -> ValueError")

# ── SOUNDNESS — dénominateurs nuls -> ValueError ────────────────────────────────────────────────────────────────
check(leve(B.sensibilite, 0, 0), "Se : VP+FN=0 -> ValueError")
check(leve(B.specificite, 0, 0), "Sp : VN+FP=0 -> ValueError")
check(leve(B.valeur_predictive_positive, 0, 0), "VPP : VP+FP=0 -> ValueError")
check(leve(B.valeur_predictive_negative, 0, 0), "VPN : VN+FN=0 -> ValueError")
check(leve(B.prevalence, 0, 0), "prevalence : total=0 -> ValueError")
check(leve(B.exactitude, 0, 0, 0, 0), "exactitude : effectif total=0 -> ValueError")
check(leve(B.rapport_vraisemblance_positif, 0.9, 1.0), "RV+ : Sp=1 (1-Sp=0) -> ValueError")
check(leve(B.rapport_vraisemblance_negatif, 0.9, 0.0), "RV- : Sp=0 -> ValueError")

# ── SOUNDNESS — probabilités hors [0,1] -> ValueError ───────────────────────────────────────────────────────────
check(leve(B.rapport_vraisemblance_positif, 1.2, 0.8), "RV+ : Se>1 -> ValueError")
check(leve(B.rapport_vraisemblance_positif, 0.9, -0.1), "RV+ : Sp<0 -> ValueError")
check(leve(B.rapport_vraisemblance_negatif, -0.5, 0.8), "RV- : Se<0 -> ValueError")

# ── SOUNDNESS — malades > total -> ValueError ───────────────────────────────────────────────────────────────────
check(leve(B.prevalence, 11, 10), "malades>total -> ValueError")

# ── SOUNDNESS — types invalides (bool, str, None, NaN, inf) -> ValueError ───────────────────────────────────────
check(leve(B.sensibilite, True, 10), "bool VP -> ValueError")
check(leve(B.sensibilite, 10, False), "bool FN -> ValueError")
check(leve(B.specificite, "80", 20), "str VN -> ValueError")
check(leve(B.valeur_predictive_positive, None, 5), "None VP -> ValueError")
check(leve(B.sensibilite, float("nan"), 10), "NaN -> ValueError")
check(leve(B.sensibilite, float("inf"), 10), "inf -> ValueError")
check(leve(B.rapport_vraisemblance_positif, "0.9", 0.8), "str proba -> ValueError")

# ── (3) DÉTERMINISME ────────────────────────────────────────────────────────────────────────────────────────────
check(B.sensibilite(90, 10) == B.sensibilite(90, 10), "déterminisme Se")
check(B.rapport_vraisemblance_positif(0.9, 0.8) == B.rapport_vraisemblance_positif(0.9, 0.8), "déterminisme RV+")

# valeurs dans [0,1] pour les indices de proportion
check(0.0 <= B.sensibilite(37, 13) <= 1.0, "Se dans [0,1]")
check(0.0 <= B.specificite(37, 13) <= 1.0, "Sp dans [0,1]")

print(f"\n=== valide_biostatistique : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
