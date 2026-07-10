"""
VALIDE datation_radiocarbone.py — held-out ADVERSE.

ANCRES NON CIRCULAIRES (valeurs connues INDÉPENDAMMENT de la formule testée) :
  • f = 0.5 (une demi-vie écoulée) avec la demi-vie de CAMBRIDGE 5730 -> âge = 5730 ans EXACT (log2(2)=1).
  • f = 0.25 (deux demi-vies) avec 5730 -> âge = 11460 ans EXACT (2·5730).
  • f = 0.5 (K-Ar, T=1.248e9) -> âge = 1.248e9 (une demi-vie = la demi-vie elle-même) ; idem U-238 = 4.468e9.
  • CONVENTION LIBBY : f = 0.5 -> âge BP = 8033·ln(2) ≈ 5568 ans (constante de convention, calculée à la main
    par une expression DISTINCTE de la fonction : 8033.0*math.log(2.0)).
  • BOUCLE FERMÉE : fraction_restante(age_reel_demi_vie(f, T), T) == f à 1e-9 près pour 100 valeurs de f.
  • LIMITE : f = 0.001 (âge ≈ 55 000 ans) -> ValueError (hors portée) ; f = 1.5 -> ValueError.
  • CALIBRATION : age_calendaire(...) -> ValueError TOUJOURS ; calibration_disponible() -> False.

SOUNDNESS : f≤0, f>1, demi_vie≤0, âge<0, types (bool/str/NaN/inf), mauvaise arité -> ValueError.
"""
import math

import datation_radiocarbone as D

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


# ── 1) ANCRE EXACTE : une demi-vie de Cambridge -> 5730 ans ──
check(proche(D.age_reel_demi_vie(0.5, 5730.0), 5730.0), "f=0.5, T=5730 -> 5730 ans (log2(2)=1)")
check(proche(D.age_reel_demi_vie(0.25, 5730.0), 11460.0), "f=0.25, T=5730 -> 11460 ans (2 demi-vies)")
check(proche(D.age_reel_demi_vie(0.125, 5730.0), 17190.0), "f=0.125, T=5730 -> 17190 ans (3 demi-vies)")
check(proche(D.age_reel_demi_vie(1.0, 5730.0), 0.0), "f=1 -> âge 0 (rien décru)")

# ── 2) ANCRE : demi-vie = la demi-vie elle-même à f=0.5 (K-Ar, U-238) ──
check(proche(D.age_reel_demi_vie(0.5, D.DEMI_VIE_K_AR), 1.248e9, tol=1.0), "f=0.5 K-Ar -> 1.248e9 ans")
check(proche(D.age_reel_demi_vie(0.5, D.DEMI_VIE_U238), 4.468e9, tol=1.0), "f=0.5 U-238 -> 4.468e9 ans")

# ── 3) CONVENTION LIBBY : âge BP = 8033·ln(2) ≈ 5568 (expression DISTINCTE de la fonction) ──
libby_demi = 8033.0 * math.log(2.0)          # ancre calculée à la main, chemin distinct
check(proche(D.age_radiocarbone(0.5), libby_demi, tol=1e-3), "f=0.5 -> âge BP = 8033·ln2 ≈ 5568")
check(abs(D.age_radiocarbone(0.5) - 5568.0) < 1.0, "âge BP à f=0.5 ≈ 5568 (convention publiée)")
# Libby ≠ Cambridge : à f=0.5, l'âge BP (5568) diffère de l'âge réel (5730)
check(D.age_radiocarbone(0.5) < D.age_reel_demi_vie(0.5, D.DEMI_VIE_C14_CAMBRIDGE),
      "âge BP Libby < âge réel Cambridge (les deux conventions diffèrent)")
# f=1 -> âge BP 0
check(proche(D.age_radiocarbone(1.0), 0.0), "f=1 -> âge BP 0")

# ── 4) LES DEUX DEMI-VIES EXPOSÉES ──
check(D.DEMI_VIE_C14_CAMBRIDGE == 5730.0, "demi-vie Cambridge exposée = 5730")
check(D.DEMI_VIE_C14_LIBBY == 5568.0, "demi-vie Libby exposée = 5568")
check(D.DEMI_VIE_K_AR == 1.248e9, "demi-vie K-Ar exposée")
check(D.DEMI_VIE_U238 == 4.468e9, "demi-vie U-238 exposée")

# ── 5) BOUCLE FERMÉE : fraction_restante(age_reel(f,T),T) == f à 1e-9 pour 100 valeurs ──
loop_ok = True
for k in range(1, 101):
    f = k / 100.0                     # f de 0.01 à 1.00
    for T in (5730.0, 1.248e9):
        rt = D.fraction_restante(D.age_reel_demi_vie(f, T), T)
        if not (rt is not None and abs(rt - f) <= 1e-9):
            loop_ok = False
check(loop_ok, "boucle fermée fraction_restante∘age_reel_demi_vie == id (100 valeurs, 1e-9)")

# fraction_restante ancres directes
check(proche(D.fraction_restante(5730.0, 5730.0), 0.5), "fraction après 1 demi-vie = 0.5")
check(proche(D.fraction_restante(11460.0, 5730.0), 0.25), "fraction après 2 demi-vies = 0.25")
check(proche(D.fraction_restante(0.0, 5730.0), 1.0), "fraction à t=0 = 1")

# ── 6) LIMITE ENFORCÉE : au-delà de ~50 000 ans -> ValueError ──
check(leve(D.age_radiocarbone, 0.001), "f=0.001 (âge ~55000) -> ValueError (hors portée)")
check(leve(D.age_radiocarbone, 0.0018), "f=0.0018 (âge >50000) -> ValueError")
# juste sous le seuil : encore accepté (âge ≈ 49923 ans < 50000)
check(proche(D.age_radiocarbone(0.002), -8033.0 * math.log(0.002), tol=1e-3),
      "f=0.002 (âge ≈49923 < 50000) -> accepté")
check(D.age_radiocarbone(0.002) < D.PORTEE_MAX_ANS, "âge à f=0.002 sous la portée max")

# ── 7) CALIBRATION — abstention structurelle (la plus importante) ──
check(D.calibration_disponible() is False, "calibration_disponible() = False")
check(leve(D.age_calendaire, 5568.0), "age_calendaire(5568) -> ValueError (IntCal absente)")
check(leve(D.age_calendaire, 0.0), "age_calendaire(0) -> ValueError")
check(leve(D.age_calendaire, 40000.0), "age_calendaire(40000) -> ValueError TOUJOURS")

# ── 8) SOUNDNESS — fraction hors ]0, 1] ──
check(leve(D.age_radiocarbone, 1.5), "age_radiocarbone f=1.5 -> ValueError")
check(leve(D.age_radiocarbone, 0.0), "age_radiocarbone f=0 -> ValueError")
check(leve(D.age_radiocarbone, -0.5), "age_radiocarbone f<0 -> ValueError")
check(leve(D.age_reel_demi_vie, 1.5, 5730.0), "age_reel f=1.5 -> ValueError")
check(leve(D.age_reel_demi_vie, 0.0, 5730.0), "age_reel f=0 -> ValueError")
check(leve(D.age_reel_demi_vie, -0.1, 5730.0), "age_reel f<0 -> ValueError")

# ── 9) SOUNDNESS — demi-vie / âge illégaux ──
check(leve(D.age_reel_demi_vie, 0.5, 0.0), "demi_vie=0 -> ValueError")
check(leve(D.age_reel_demi_vie, 0.5, -5730.0), "demi_vie<0 -> ValueError")
check(leve(D.fraction_restante, 5730.0, 0.0), "fraction_restante T=0 -> ValueError")
check(leve(D.fraction_restante, -1.0, 5730.0), "fraction_restante âge<0 -> ValueError")

# ── 10) SOUNDNESS — types invalides (bool / str / NaN / inf) ──
check(leve(D.age_radiocarbone, True), "age_radiocarbone bool -> ValueError")
check(leve(D.age_radiocarbone, "0.5"), "age_radiocarbone str -> ValueError")
check(leve(D.age_radiocarbone, float("nan")), "age_radiocarbone NaN -> ValueError")
check(leve(D.age_radiocarbone, float("inf")), "age_radiocarbone inf -> ValueError")
check(leve(D.age_reel_demi_vie, True, 5730.0), "age_reel f bool -> ValueError")
check(leve(D.age_reel_demi_vie, 0.5, True), "age_reel T bool -> ValueError")
check(leve(D.age_reel_demi_vie, 0.5, "5730"), "age_reel T str -> ValueError")
check(leve(D.age_reel_demi_vie, 0.5, float("nan")), "age_reel T NaN -> ValueError")
check(leve(D.fraction_restante, float("inf"), 5730.0), "fraction_restante âge inf -> ValueError")
check(leve(D.fraction_restante, 5730.0, float("nan")), "fraction_restante T NaN -> ValueError")

# ── 11) SOUNDNESS — fraction restante complexe / str refusée ──
check(leve(D.fraction_restante, "0", 5730.0), "fraction_restante âge str -> ValueError")
check(leve(D.fraction_restante, 100.0, True), "fraction_restante T bool -> ValueError")

# ── 12) DÉTERMINISME ──
check(D.age_radiocarbone(0.5) == D.age_radiocarbone(0.5), "déterminisme age_radiocarbone")
check(D.age_reel_demi_vie(0.5, 5730.0) == D.age_reel_demi_vie(0.5, 5730.0), "déterminisme age_reel")
check(D.fraction_restante(5730.0, 5730.0) == D.fraction_restante(5730.0, 5730.0), "déterminisme fraction")
check(D.calibration_disponible() == D.calibration_disponible(), "déterminisme calibration_disponible")

print(f"\n=== valide_datation_radiocarbone : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
