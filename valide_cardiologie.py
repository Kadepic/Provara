"""
VALIDE cardiologie.py — held-out ADVERSE. Ancres sur des valeurs cardiologiques CONNUES (FCmax 40 ans = 180,
FE 60/120 = 50 %, QTc de Bazett ancré indépendamment, seuils de fréquence) + SOUNDNESS (âge hors [0,120],
RR ≤ 0, volumes ≤ 0, fréquence ≤ 0, types non numériques -> ValueError) + DÉTERMINISME.
"""
import math

import cardiologie as C

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve(fn, *a, **k):
    """True si fn(*a, **k) lève ValueError (abstention de soundness)."""
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True


def approx(x, y, tol=1e-9):
    return abs(x - y) <= tol * max(1.0, abs(y))


# ── 1) ANCRES — fréquence cardiaque maximale = 220 − âge ──
check(C.frequence_cardiaque_max(40) == 180.0, "FCmax(40) = 180")
check(C.frequence_cardiaque_max(0) == 220.0, "FCmax(0) = 220 (borne basse valide)")
check(C.frequence_cardiaque_max(120) == 100.0, "FCmax(120) = 100 (borne haute valide)")
check(C.frequence_cardiaque_max(20) == 200.0, "FCmax(20) = 200")
check(C.frequence_cardiaque_max(70) == 150.0, "FCmax(70) = 150")

# ── 2) ANCRES — fraction d'éjection = VE/VTD·100 ──
check(C.fraction_ejection(60, 120) == 50.0, "FE 60/120 = 50 %")
check(C.fraction_ejection(70, 100) == 70.0, "FE 70/100 = 70 % (limite haute de la normale)")
check(approx(C.fraction_ejection(35, 100), 35.0), "FE 35/100 = 35 % (dysfonction)")
check(C.fraction_ejection(120, 120) == 100.0, "FE 120/120 = 100 %")

# ── 3) ANCRES — QTc de Bazett = QT / sqrt(RR), ancré indépendamment ──
# RR = 1 s -> sqrt(1) = 1 -> QTc == QT (ancre indépendante de l'implémentation)
check(C.qt_corrige_bazett(400, 1.0) == 400.0, "QTc Bazett RR=1s -> QTc = QT = 400 ms")
# RR = 0.64 s -> sqrt = 0.8 -> 400/0.8 = 500
check(approx(C.qt_corrige_bazett(400, 0.64), 500.0), "QTc Bazett QT=400 RR=0.64 -> 500 ms")
# FC 75/min -> RR = 0.8 s, QT 360 -> 360/sqrt(0.8) ~ 402.49
check(approx(C.qt_corrige_bazett(360, 0.8), 360 / math.sqrt(0.8)), "QTc Bazett QT=360 RR=0.8s")
check(C.qt_corrige_bazett(400, 1.0) > C.qt_corrige_bazett(400, 1.2), "QTc décroît quand RR croît")

# ── 4) ANCRES — classe de fréquence au repos ──
check(C.classe_fc_repos(50) == C.BRADYCARDIE, "FC 50 = bradycardie")
check(C.classe_fc_repos(59) == C.BRADYCARDIE, "FC 59 = bradycardie (juste sous 60)")
check(C.classe_fc_repos(60) == C.NORMAL, "FC 60 = normal (borne incluse)")
check(C.classe_fc_repos(75) == C.NORMAL, "FC 75 = normal")
check(C.classe_fc_repos(100) == C.NORMAL, "FC 100 = normal (borne incluse)")
check(C.classe_fc_repos(101) == C.TACHYCARDIE, "FC 101 = tachycardie (juste au-dessus de 100)")
check(C.classe_fc_repos(140) == C.TACHYCARDIE, "FC 140 = tachycardie")

# ── 5) SOUNDNESS — domaine invalide -> ValueError ──
check(leve(C.frequence_cardiaque_max, -1), "âge < 0 -> ValueError")
check(leve(C.frequence_cardiaque_max, 121), "âge > 120 -> ValueError")
check(leve(C.frequence_cardiaque_max, 200), "âge 200 (absurde) -> ValueError")
check(leve(C.qt_corrige_bazett, 400, 0), "RR = 0 -> ValueError")
check(leve(C.qt_corrige_bazett, 400, -0.5), "RR < 0 -> ValueError")
check(leve(C.qt_corrige_bazett, 0, 1.0), "QT = 0 -> ValueError")
check(leve(C.qt_corrige_bazett, -10, 1.0), "QT < 0 -> ValueError")
check(leve(C.fraction_ejection, 0, 120), "VE = 0 -> ValueError")
check(leve(C.fraction_ejection, 60, 0), "VTD = 0 -> ValueError")
check(leve(C.fraction_ejection, -60, 120), "VE < 0 -> ValueError")
check(leve(C.fraction_ejection, 60, -120), "VTD < 0 -> ValueError")
check(leve(C.classe_fc_repos, 0), "FC = 0 -> ValueError")
check(leve(C.classe_fc_repos, -10), "FC < 0 -> ValueError")

# ── 6) SOUNDNESS — types non numériques (bool/str/None) -> ValueError ──
check(leve(C.frequence_cardiaque_max, True), "bool n'est pas un âge -> ValueError")
check(leve(C.frequence_cardiaque_max, "quarante"), "str âge -> ValueError")
check(leve(C.frequence_cardiaque_max, None), "None âge -> ValueError")
check(leve(C.qt_corrige_bazett, "400", 1.0), "str QT -> ValueError")
check(leve(C.qt_corrige_bazett, 400, "1.0"), "str RR -> ValueError")
check(leve(C.fraction_ejection, True, 120), "bool VE -> ValueError")
check(leve(C.classe_fc_repos, "soixante"), "str FC -> ValueError")
check(leve(C.classe_fc_repos, None), "None FC -> ValueError")

# ── 7) DÉTERMINISME ──
check(C.frequence_cardiaque_max(40) == C.frequence_cardiaque_max(40), "déterminisme FCmax")
check(C.qt_corrige_bazett(400, 0.64) == C.qt_corrige_bazett(400, 0.64), "déterminisme QTc")
check(C.fraction_ejection(60, 120) == C.fraction_ejection(60, 120), "déterminisme FE")
check(C.classe_fc_repos(75) == C.classe_fc_repos(75), "déterminisme classe FC")

print(f"\n=== valide_cardiologie : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
