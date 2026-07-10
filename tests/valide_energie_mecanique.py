"""
VALIDE energie_mecanique.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (valeurs connues/calculées à la main, PAS recalculées par la formule testée) :
  • Chute libre h=1 m, g=9.80665 : v = √(2·9.80665) = √19.6133 = 4.428690551 m/s.
    Vérification INDÉPENDANTE par élévation au carré (à la main) : 4.428690551² = 19.61330000… = 2·9.80665. ✓
    (NB : l'ancre initialement imposée « 4.4290518 » était FAUSSE : 4.4290518² = 19.6164998 ≠ 19.6133 ;
     corrigée ici — l'ancre corrigée est prouvée par le carré, chemin de calcul distinct de sqrt.)
  • m=2 kg, v=3 m/s : Ec = ½·2·9 = 9 J EXACTEMENT (arithmétique à la main).
  • m=1 kg, h=1 m, g=9.80665 : Ep = 9.80665 J exactement (g normal, 3e CGPM 1901, valeur conventionnelle).
  • Cas EXACTS sans flottant douteux : g=2, h=1 -> v = √4 = 2 ; g=8, h=4 -> v = √64 = 8 ;
    v=14, g=9.8 -> h = 196/19.6 = 10 (divisions à la main).
  • PENDULE (ancre croisée, DEUX formules distinctes) : m=1.5 kg lâché de h=2 m ;
    Ep sommet = 1.5·9.80665·2 = 29.41995 J (multiplication à la main) doit égaler Ec en bas
    calculée par ½·m·v² avec v issu de √(2gh) — deux chemins de code différents.
  • FROTTEMENT : Em2 < Em1 (10 m de chute -> seulement 12 m/s au lieu de 14.0) -> conserve = False,
    PAS une exception (constat physique, pas une entrée mal posée).
  • ANTI-ABSORPTION ULP (contre-exemples d'AUDIT, écarts calculés à la main) : m=1, v=10⁶, g=10 :
    Em ≈ 5·10¹¹ J, ulp(float64) ≈ 6·10⁻⁵ J ; l'écart RÉEL m·g·h₂ = 1·10·10⁻⁶ = 10⁻⁵ J passait sous
    l'ulp en float64 brut et donnait True à tol=10⁻⁹ (faux positif). Le calcul EXACT (Fraction sur les
    entrées) doit rendre False. Idem v=10⁹, h₂=10⁻⁹, tol=0 : écart exact = 10·10⁻⁹ = 10⁻⁸ J -> False.
    CONTRÔLE (pas de faux négatif introduit) : même écart 10⁻⁵ J accepté à tol=10⁻⁴ -> True.

SOUNDNESS : m≤0, h<0, g≤0, tol<0, bool/str/NaN/inf, état mal structuré -> ValueError.
"""
import math

import energie_mecanique as E

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


# ── 1) ANCRE : chute libre h=1 m, g normal ──
# √(2·9.80665) = 4.428690551 (vérifié à la main par le carré : 4.428690551² = 19.6133000…)
check(proche(E.vitesse_depuis_hauteur(1.0, 9.80665), 4.428690551, tol=1e-8),
      "v(h=1, g=9.80665) = 4.428690551 m/s")
# g par défaut = g normal
check(proche(E.vitesse_depuis_hauteur(1.0), 4.428690551, tol=1e-8), "g par défaut = 9.80665")
check(E.G_NORMAL == 9.80665, "G_NORMAL = 9.80665 (3e CGPM 1901)")

# ── 2) ANCRE : Ec = 9 J exactement (m=2, v=3 : ½·2·9 = 9, à la main) ──
check(E.energie_cinetique(2.0, 3.0) == 9.0, "Ec(2 kg, 3 m/s) = 9 J exactement")
check(E.energie_cinetique(2.0, -3.0) == 9.0, "Ec(2 kg, −3 m/s) = 9 J (le signe de v est indifférent)")
check(E.energie_cinetique(1.0, 1.0) == 0.5, "Ec(1,1) = 0.5 J (½·1·1, à la main)")
check(E.energie_cinetique(80.0, 10.0) == 4000.0, "Ec(80 kg, 10 m/s) = 4000 J (½·80·100, à la main)")
check(E.energie_cinetique(2.0, 0.0) == 0.0, "Ec(v=0) = 0 J (repos)")

# ── 3) ANCRE : Ep = m·g·h ──
check(proche(E.energie_potentielle(1.0, 1.0, 9.80665), 9.80665, tol=1e-12),
      "Ep(1 kg, 1 m, g normal) = 9.80665 J")
check(E.energie_potentielle(2.0, 5.0, 10.0) == 100.0, "Ep(2 kg, 5 m, g=10) = 100 J (2·10·5, à la main)")
check(E.energie_potentielle(3.0, 0.0, 9.80665) == 0.0, "Ep(h=0) = 0 J (référence)")

# ── 4) ANCRE : Em = Ec + Ep ──
check(E.energie_mecanique(2.0, 3.0, 0.0, 9.80665) == 9.0, "Em(h=0) = Ec = 9 J")
check(E.energie_mecanique(1.0, 0.0, 1.0, 10.0) == 10.0, "Em(repos, h=1, g=10) = Ep = 10 J")
# ½·2·9 + 2·10·5 = 9 + 100 = 109 (à la main)
check(E.energie_mecanique(2.0, 3.0, 5.0, 10.0) == 109.0, "Em(2,3,5,g=10) = 109 J (9+100, à la main)")

# ── 5) CAS EXACTS chute libre / réciproque (arithmétique à la main, sans flottant douteux) ──
check(E.vitesse_depuis_hauteur(1.0, 2.0) == 2.0, "v(h=1, g=2) = √4 = 2")
check(E.vitesse_depuis_hauteur(4.0, 8.0) == 8.0, "v(h=4, g=8) = √64 = 8")
check(E.vitesse_depuis_hauteur(0.0, 9.80665) == 0.0, "v(h=0) = 0 (départ = arrivée)")
check(E.hauteur_depuis_vitesse(14.0, 9.8) == 10.0, "h(v=14, g=9.8) = 196/19.6 = 10 m")
check(E.hauteur_depuis_vitesse(10.0, 10.0) == 5.0, "h(v=10, g=10) = 100/20 = 5 m")
check(E.hauteur_depuis_vitesse(-10.0, 10.0) == 5.0, "h(v=−10) = h(v=10) (seul v² compte)")
# saut de 20 m : √(2·9.80665·20) = √392.266 = 19.80570625 (vérifié : 19.80570625² = 392.2660…)
check(proche(E.vitesse_depuis_hauteur(20.0, 9.80665), 19.80570625, tol=1e-7),
      "v(h=20, g normal) = 19.80570625 m/s")

# ── 6) PENDULE : Ep au sommet = Ec en bas (ancre croisée, deux formules distinctes) ──
ep_sommet = E.energie_potentielle(1.5, 2.0, 9.80665)
check(proche(ep_sommet, 29.41995, tol=1e-9), "Ep sommet = 1.5·9.80665·2 = 29.41995 J (à la main)")
v_bas = E.vitesse_depuis_hauteur(2.0, 9.80665)
ec_bas = E.energie_cinetique(1.5, v_bas)
check(proche(ec_bas, 29.41995, tol=1e-6), "Ec bas (½mv², v=√(2gh)) = 29.41995 J = Ep sommet")
check(proche(ep_sommet, ec_bas, tol=1e-6), "ancre croisée : Ep(sommet) == Ec(bas)")
check(E.conserve((1.5, 0.0, 2.0), (1.5, v_bas, 0.0), 1e-6, 9.80665) is True,
      "pendule : Em conservée entre sommet et bas")

# ── 7) CONSERVATION / NON-CONSERVATION ──
check(E.conserve((1.0, 3.0, 5.0), (1.0, 3.0, 5.0), 0.0, 9.80665) is True,
      "états identiques : conservé même à tol=0")
# chute libre m=1, h=10, g=10 : Em1 = 100 J ; en bas v=√200 -> Em2 = 100 J (à la main)
check(E.conserve((1.0, 0.0, 10.0), (1.0, math.sqrt(200.0), 0.0), 1e-9, 10.0) is True,
      "chute libre (g=10) : 100 J = 100 J")
# FROTTEMENT : Em1 = 1·9.80665·10 = 98.0665 J ; Em2 = ½·1·12² = 72 J < Em1 -> False, PAS d'exception
frotte = E.conserve((1.0, 0.0, 10.0), (1.0, 12.0, 0.0), 1e-6, 9.80665)
check(frotte is False, "frottement (98.0665 J -> 72 J) : détecté NON conservé (False)")
check(isinstance(frotte, bool), "conserve renvoie bien un bool, pas une exception")
# GAIN d'énergie (moteur) : Em2 > Em1 -> False aussi (le théorème est une égalité)
check(E.conserve((1.0, 0.0, 1.0), (1.0, 100.0, 0.0), 1e-6, 9.80665) is False,
      "apport d'énergie : NON conservé (False)")
# écart 0.5 J : rejeté à tol=1e-3, accepté à tol=1.0 (la tolérance fait foi)
check(E.conserve((1.0, 0.0, 10.0), (1.0, 0.0, 10.05), 1e-3, 10.0) is False,
      "écart 0.5 J > tol=1e-3 : False")
check(E.conserve((1.0, 0.0, 10.0), (1.0, 0.0, 10.05), 1.0, 10.0) is True,
      "écart 0.5 J ≤ tol=1 J : True")

# ── 7bis) ANTI-ABSORPTION ULP (contre-exemples de l'AUDIT — le float64 brut rendait True à tort) ──
# Em ≈ 5e11 J (½·1·(1e6)²) ; écart réel m·g·h2 = 1·10·1e-6 = 1e-5 J (à la main), 10 000× tol=1e-9.
# En float64 brut : ulp(5e11) ≈ 6.1e-5 > 1e-5 -> écart absorbé -> True (FAUX POSITIF démontré).
# En exact (Fraction) : 1e-5 > 1e-9 -> False obligatoire.
check(E.conserve((1.0, 1e6, 0.0), (1.0, 1e6, 1e-6), 1e-9, 10.0) is False,
      "audit : écart exact 1e-5 J > tol=1e-9 malgré Em ~ 5e11 J -> False")
# Idem à tol=0 avec v=1e9 : Em ≈ 5e17 J ; écart réel = 1·10·1e-9 = 1e-8 J (à la main) > 0 -> False.
check(E.conserve((1.0, 1e9, 0.0), (1.0, 1e9, 1e-9), 0.0, 10.0) is False,
      "audit : écart exact 1e-8 J > tol=0 malgré Em ~ 5e17 J -> False")
# Symétrie de |Em1 − Em2| : l'ordre des états ne change pas le verdict.
check(E.conserve((1.0, 1e6, 1e-6), (1.0, 1e6, 0.0), 1e-9, 10.0) is False,
      "audit : même écart, états permutés -> False aussi")
# CONTRÔLE faux négatif : le MÊME écart 1e-5 J est ≤ tol=1e-4 -> True (la tolérance fait foi).
check(E.conserve((1.0, 1e6, 0.0), (1.0, 1e6, 1e-6), 1e-4, 10.0) is True,
      "contrôle : écart 1e-5 J ≤ tol=1e-4 -> True (pas de faux négatif introduit)")
# tol=0 et états STRICTEMENT identiques à grande magnitude : égalité exacte -> True.
check(E.conserve((1.0, 1e9, 0.0), (1.0, 1e9, 0.0), 0.0, 10.0) is True,
      "contrôle : états identiques (Em ~ 5e17 J), tol=0 -> True (égalité exacte)")
# Écart sous l'ulp mais AU-DESSUS de tol=0 dans les deux sens (gain d'énergie masqué) : False.
check(E.conserve((2.0, 1e6, 1e-7), (2.0, 1e6, 0.0), 1e-9, 9.80665) is False,
      "audit : perte 2·9.80665·1e-7 ≈ 1.96e-6 J > tol=1e-9 -> False (g normal)")

# ── 8) SOUNDNESS — masse ──
check(leve(E.energie_cinetique, 0.0, 3.0), "Ec m=0 -> ValueError")
check(leve(E.energie_cinetique, -2.0, 3.0), "Ec m<0 -> ValueError")
check(leve(E.energie_potentielle, 0.0, 1.0, 9.80665), "Ep m=0 -> ValueError")
check(leve(E.energie_mecanique, -1.0, 1.0, 1.0, 9.80665), "Em m<0 -> ValueError")
check(leve(E.conserve, (0.0, 1.0, 1.0), (1.0, 1.0, 1.0), 1e-9), "conserve m=0 -> ValueError")

# ── 9) SOUNDNESS — hauteur ──
check(leve(E.energie_potentielle, 1.0, -0.5, 9.80665), "Ep h<0 -> ValueError")
check(leve(E.energie_mecanique, 1.0, 1.0, -1.0, 9.80665), "Em h<0 -> ValueError")
check(leve(E.vitesse_depuis_hauteur, -1.0, 9.80665), "v h<0 -> ValueError")
check(leve(E.conserve, (1.0, 1.0, -1.0), (1.0, 1.0, 1.0), 1e-9), "conserve h<0 -> ValueError")

# ── 10) SOUNDNESS — pesanteur ──
check(leve(E.energie_potentielle, 1.0, 1.0, 0.0), "Ep g=0 -> ValueError")
check(leve(E.energie_potentielle, 1.0, 1.0, -9.8), "Ep g<0 -> ValueError")
check(leve(E.vitesse_depuis_hauteur, 1.0, 0.0), "v g=0 -> ValueError")
check(leve(E.hauteur_depuis_vitesse, 1.0, -1.0), "h g<0 -> ValueError")
check(leve(E.conserve, (1.0, 1.0, 1.0), (1.0, 1.0, 1.0), 1e-9, 0.0), "conserve g=0 -> ValueError")

# ── 11) SOUNDNESS — tolérance ──
check(leve(E.conserve, (1.0, 1.0, 1.0), (1.0, 1.0, 1.0), -1e-9), "tol<0 -> ValueError")
check(leve(E.conserve, (1.0, 1.0, 1.0), (1.0, 1.0, 1.0), float("nan")), "tol=NaN -> ValueError")
check(leve(E.conserve, (1.0, 1.0, 1.0), (1.0, 1.0, 1.0), True), "tol=bool -> ValueError")

# ── 12) SOUNDNESS — types (bool / str / NaN / inf) ──
check(leve(E.energie_cinetique, True, 3.0), "m=bool -> ValueError")
check(leve(E.energie_cinetique, 2.0, "3"), "v=str -> ValueError")
check(leve(E.energie_cinetique, 2.0, float("nan")), "v=NaN -> ValueError")
check(leve(E.energie_cinetique, 2.0, float("inf")), "v=inf -> ValueError")
check(leve(E.energie_potentielle, float("nan"), 1.0, 9.80665), "m=NaN -> ValueError")
check(leve(E.energie_potentielle, 1.0, float("inf"), 9.80665), "h=inf -> ValueError")
check(leve(E.vitesse_depuis_hauteur, True, 9.80665), "h=bool -> ValueError")
check(leve(E.vitesse_depuis_hauteur, "1", 9.80665), "h=str -> ValueError")
check(leve(E.hauteur_depuis_vitesse, float("-inf"), 9.80665), "v=−inf -> ValueError")
check(leve(E.energie_mecanique, 1.0, 1.0, 1.0, float("nan")), "g=NaN -> ValueError")

# ── 13) SOUNDNESS — structure d'état ──
check(leve(E.conserve, (1.0, 1.0), (1.0, 1.0, 1.0), 1e-9), "état à 2 champs -> ValueError")
check(leve(E.conserve, (1.0, 1.0, 1.0, 1.0), (1.0, 1.0, 1.0), 1e-9), "état à 4 champs -> ValueError")
check(leve(E.conserve, 5.0, (1.0, 1.0, 1.0), 1e-9), "état non-séquence -> ValueError")
check(leve(E.conserve, (1.0, True, 1.0), (1.0, 1.0, 1.0), 1e-9), "v=bool dans l'état -> ValueError")
check(leve(E.conserve, (1.0, 1.0, 1.0), (1.0, float("nan"), 1.0), 1e-9), "NaN dans l'état 2 -> ValueError")

# ── 14) DÉTERMINISME ──
check(E.energie_cinetique(2.0, 3.0) == E.energie_cinetique(2.0, 3.0), "déterminisme Ec")
check(E.energie_potentielle(1.5, 2.0, 9.80665) == E.energie_potentielle(1.5, 2.0, 9.80665), "déterminisme Ep")
check(E.energie_mecanique(2.0, 3.0, 5.0, 10.0) == E.energie_mecanique(2.0, 3.0, 5.0, 10.0), "déterminisme Em")
check(E.vitesse_depuis_hauteur(1.0, 9.80665) == E.vitesse_depuis_hauteur(1.0, 9.80665), "déterminisme v(h)")
check(E.conserve((1.0, 0.0, 10.0), (1.0, 12.0, 0.0), 1e-6, 9.80665)
      == E.conserve((1.0, 0.0, 10.0), (1.0, 12.0, 0.0), 1e-6, 9.80665), "déterminisme conserve")

print(f"\n=== valide_energie_mecanique : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
