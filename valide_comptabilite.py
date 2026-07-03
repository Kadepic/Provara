"""
VALIDE comptabilite.py — held-out ADVERSE.

Ancres CONNUES (règles comptables standard + arithmétique vérifiée à la main, non circulaires) :
  • equation_bilan : Actif 100 = Passif 60 + CP 40 -> True ; 100 ≠ 60+30=90 -> False ;
                     100 ≠ 70+40=110 -> False ; tolérance flottante 0.1+0.2 == 0.3 -> True ;
                     écart d'un centime 100.01 ≠ 100.00 -> False.
  • resultat_net  : 150-120 = 30 (bénéfice) ; 100-100 = 0 ; 100-150 = -50 (perte autorisée).
  • fonds_roulement : 100-60 = 40 ; 50-80 = -30 (BFR, négatif autorisé) ; 50-50 = 0.
  • ratio_liquidite : 100/50 = 2.0 ; 150/100 = 1.5 ; 60/60 = 1.0 ; 0/50 = 0.0.
  • partie_double : [100]/[100] -> True ; [60,40]/[100] -> True ; [100]/[60,40] -> True ;
                    [100]/[90] -> False ; [100,50]/[100] (150≠100) -> False ;
                    tolérance [0.1,0.2]/[0.3] -> True.
SOUNDNESS : valeur négative, non numérique, non finie -> ValueError ; passif_circulant<=0 (ratio)
            -> ValueError ; partie_double liste vide / non-itérable -> ValueError. Jamais un faux.
DÉTERMINISME : mêmes entrées -> mêmes sorties.
"""

import comptabilite as M

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


# ── 1) ANCRE — équation du bilan (Actif = Passif + Capitaux propres) ──
check(M.equation_bilan(100, 60, 40) is True, "bilan 100 = 60 + 40 -> True (CAS)")
check(M.equation_bilan(0, 0, 0) is True, "bilan 0 = 0 + 0 -> True")
check(M.equation_bilan(250, 150, 100) is True, "bilan 250 = 150 + 100 -> True")
check(M.equation_bilan(100, 60, 30) is False, "bilan 100 ≠ 90 -> False (déséquilibre)")
check(M.equation_bilan(100, 70, 40) is False, "bilan 100 ≠ 110 -> False (déséquilibre)")
check(M.equation_bilan(0.3, 0.1, 0.2) is True, "bilan tolérance flottante 0.1+0.2 = 0.3 -> True")
check(M.equation_bilan(100.01, 100.0, 0.0) is False, "écart d'un centime -> False (déséquilibre réel)")

# ── 2) ANCRE — résultat net (produits - charges) ──
check(M.resultat_net(150, 120) == 30.0, "résultat 150-120 = 30 (CAS, bénéfice)")
check(M.resultat_net(100, 100) == 0.0, "résultat 100-100 = 0")
check(M.resultat_net(100, 150) == -50.0, "résultat 100-150 = -50 (perte autorisée)")
check(M.resultat_net(0, 0) == 0.0, "résultat 0-0 = 0")

# ── 3) ANCRE — fonds de roulement (AC - PC) ──
check(M.fonds_roulement(100, 60) == 40.0, "FR 100-60 = 40")
check(M.fonds_roulement(50, 80) == -30.0, "FR 50-80 = -30 (négatif autorisé, BFR)")
check(M.fonds_roulement(50, 50) == 0.0, "FR 50-50 = 0")

# ── 4) ANCRE — ratio de liquidité (AC / PC) ──
check(approx(M.ratio_liquidite(100, 50), 2.0), "ratio 100/50 = 2.0")
check(approx(M.ratio_liquidite(150, 100), 1.5), "ratio 150/100 = 1.5")
check(approx(M.ratio_liquidite(60, 60), 1.0), "ratio 60/60 = 1.0")
check(approx(M.ratio_liquidite(0, 50), 0.0), "ratio 0/50 = 0.0")

# ── 5) ANCRE — partie double (Σ débits = Σ crédits) ──
check(M.partie_double([100], [100]) is True, "partie double [100]/[100] -> True (CAS)")
check(M.partie_double([60, 40], [100]) is True, "partie double [60,40]/[100] (Σ=100) -> True")
check(M.partie_double([100], [60, 40]) is True, "partie double [100]/[60,40] (Σ=100) -> True")
check(M.partie_double((100, 50), (75, 75)) is True, "partie double tuples (150=150) -> True")
check(M.partie_double([100], [90]) is False, "partie double [100]/[90] -> False (déséquilibre)")
check(M.partie_double([100, 50], [100]) is False, "partie double 150 ≠ 100 -> False")
check(M.partie_double([0.1, 0.2], [0.3]) is True, "partie double tolérance flottante -> True")
check(M.partie_double([100.0], [100.01]) is False, "partie double écart d'un centime -> False")

# ── 6) SOUNDNESS — valeurs négatives -> ValueError (jamais un faux) ──
check(_leve_v(M.equation_bilan, -100, 60, 40), "actif négatif -> ValueError")
check(_leve_v(M.equation_bilan, 100, -60, 40), "passif négatif -> ValueError")
check(_leve_v(M.equation_bilan, 100, 60, -40), "capitaux propres négatifs -> ValueError")
check(_leve_v(M.resultat_net, -1, 0), "produits négatifs -> ValueError")
check(_leve_v(M.resultat_net, 100, -1), "charges négatives -> ValueError")
check(_leve_v(M.fonds_roulement, -1, 0), "actif circulant négatif -> ValueError")
check(_leve_v(M.fonds_roulement, 0, -1), "passif circulant négatif -> ValueError")
check(_leve_v(M.ratio_liquidite, -1, 50), "actif circulant négatif (ratio) -> ValueError")
check(_leve_v(M.partie_double, [-1], [100]), "débit négatif -> ValueError")
check(_leve_v(M.partie_double, [100], [-1]), "crédit négatif -> ValueError")

# ── 7) SOUNDNESS — dénominateur du ratio <= 0 -> ValueError ──
check(_leve_v(M.ratio_liquidite, 100, 0), "passif_circulant=0 (ratio) -> ValueError")
check(_leve_v(M.ratio_liquidite, 100, -50), "passif_circulant<0 (ratio) -> ValueError")

# ── 8) SOUNDNESS — partie double : itérable vide / non-itérable -> ValueError ──
check(_leve_v(M.partie_double, [], [100]), "débits vides -> ValueError")
check(_leve_v(M.partie_double, [100], []), "crédits vides -> ValueError")
check(_leve_v(M.partie_double, 100, [100]), "débits non-itérable -> ValueError")
check(_leve_v(M.partie_double, [100], "100"), "crédits str (non liste/tuple) -> ValueError")

# ── 9) SOUNDNESS — non numérique / non fini / booléen -> ValueError ──
check(_leve_v(M.equation_bilan, "cent", 60, 40), "actif str -> ValueError")
check(_leve_v(M.resultat_net, None, 0), "produits None -> ValueError")
check(_leve_v(M.ratio_liquidite, float("inf"), 50), "actif circulant inf -> ValueError")
check(_leve_v(M.ratio_liquidite, float("nan"), 50), "actif circulant nan -> ValueError")
check(_leve_v(M.equation_bilan, True, 60, 40), "booléen n'est pas un montant -> ValueError")
check(_leve_v(M.partie_double, [True], [100]), "booléen dans débits -> ValueError")

# ── 10) DÉTERMINISME — mêmes entrées, mêmes sorties ──
check(M.equation_bilan(100, 60, 40) == M.equation_bilan(100, 60, 40), "equation_bilan déterministe")
check(M.resultat_net(150, 120) == M.resultat_net(150, 120), "resultat_net déterministe")
check(M.fonds_roulement(100, 60) == M.fonds_roulement(100, 60), "fonds_roulement déterministe")
check(M.ratio_liquidite(100, 50) == M.ratio_liquidite(100, 50), "ratio_liquidite déterministe")
check(M.partie_double([60, 40], [100]) == M.partie_double([60, 40], [100]), "partie_double déterministe")

print(f"\n=== valide_comptabilite : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
