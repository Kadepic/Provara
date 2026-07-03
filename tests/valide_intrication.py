"""
VALIDE intrication.py — held-out ADVERSE. Ancres sur des FAITS quantiques CONNUS (bornes Bell=2 / Tsirelson=2√2,
corrélations singulet aux angles remarquables, violation maximale = 2√2), JAMAIS re-calculées par la même
expression triviale + SOUNDNESS : corrélation hors [−1,1] / S hors [0,4] / type invalide -> ValueError + déterminisme.
"""
import math
import intrication as M

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve_v(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


SQRT2 = math.sqrt(2)

# ── 1) BORNES (théorèmes) ──
check(M.borne_classique_chsh() == 2.0, "borne classique CHSH = 2 (Bell)")
check(abs(M.borne_quantique_chsh() - 2.8284271247461903) < 1e-12, "borne Tsirelson = 2√2 ≈ 2.8284271247")
check(M.borne_quantique_chsh() > M.borne_classique_chsh(), "quantique dépasse strictement le classique")
check(abs(M.borne_quantique_chsh() - 2 * SQRT2) < 1e-12, "2√2 numérique cohérent")

# ── 2) VALEUR CHSH — violation maximale = 2√2 (angles standard 0,90 / 45,135 sur l'état singulet) ──
# E(a,b)=−1/√2, E(a,b')=+1/√2, E(a',b)=−1/√2, E(a',b')=−1/√2  ->  |−1/√2 −1/√2 −1/√2 −1/√2| = 4/√2 = 2√2
inv = 1 / SQRT2
check(abs(M.valeur_chsh(-inv, inv, -inv, -inv) - 2 * SQRT2) < 1e-12, "CHSH max (singulet) = 2√2")
# valeur classique exacte = 2 (corrélations déterministes ±1)
check(abs(M.valeur_chsh(1.0, -1.0, 0.0, 0.0) - 2.0) < 1e-12, "CHSH = 2 (cas classique limite)")
# tout nul -> 0
check(M.valeur_chsh(0.0, 0.0, 0.0, 0.0) == 0.0, "CHSH = 0 (aucune corrélation)")
# max algébrique 4
check(abs(M.valeur_chsh(1.0, -1.0, 1.0, 1.0) - 4.0) < 1e-12, "CHSH = 4 (max algébrique)")

# ── 3) CROISÉ : construire S depuis etat_bell_correlation (angles entre directions) -> 2√2 ──
# différences d'angle : 45°,135°,45°,45°  ->  E=−cos de chaque
d45 = math.radians(45)
d135 = math.radians(135)
S_croise = M.valeur_chsh(M.etat_bell_correlation(d45), M.etat_bell_correlation(d135),
                         M.etat_bell_correlation(d45), M.etat_bell_correlation(d45))
check(abs(S_croise - 2 * SQRT2) < 1e-12, "S reconstruit via etat_bell_correlation = 2√2 (cohérence inter-fonctions)")

# ── 4) VIOLATION DE BELL (cas du sujet) ──
check(M.viole_inegalite_bell(2 * SQRT2) is True, "S=2√2 viole Bell")
check(M.viole_inegalite_bell(2.0) is False, "S=2 (limite classique) ne viole PAS (strict)")
check(M.viole_inegalite_bell(1.5) is False, "S=1.5 ne viole pas")
check(M.viole_inegalite_bell(2.0000001) is True, "S juste au-dessus de 2 viole")
check(M.viole_inegalite_bell(0.0) is False, "S=0 ne viole pas")
check(M.viole_inegalite_bell(4.0) is True, "S=4 viole")

# ── 5) CORRÉLATION SINGULET aux angles remarquables : E=−cos(angle) ──
check(abs(M.etat_bell_correlation(0.0) - (-1.0)) < 1e-12, "angle=0 -> E=−1 (anti-corrélation parfaite)")
check(abs(M.etat_bell_correlation(math.pi) - 1.0) < 1e-12, "angle=π -> E=+1 (corrélation parfaite)")
check(abs(M.etat_bell_correlation(math.pi / 2) - 0.0) < 1e-12, "angle=π/2 -> E=0")
check(abs(M.etat_bell_correlation(math.pi / 3) - (-0.5)) < 1e-12, "angle=π/3 (60°) -> E=−0.5")
check(abs(M.etat_bell_correlation(2 * math.pi / 3) - 0.5) < 1e-12, "angle=120° -> E=+0.5")

# ── 6) SOUNDNESS — corrélation hors [−1,1] -> ValueError ──
check(leve_v(M.valeur_chsh, 1.5, 0.0, 0.0, 0.0), "E=1.5 > 1 -> ValueError")
check(leve_v(M.valeur_chsh, 0.0, -2.0, 0.0, 0.0), "E=−2 < −1 -> ValueError")
check(leve_v(M.valeur_chsh, 1.0000001, 0.0, 0.0, 0.0), "E juste au-dessus de 1 -> ValueError")
check(leve_v(M.valeur_chsh, 0.0, 0.0, 0.0, -1.0001), "E juste en dessous de −1 -> ValueError")

# ── 7) SOUNDNESS — S de CHSH hors [0,4] -> ValueError ──
check(leve_v(M.viole_inegalite_bell, -0.5), "S<0 impossible -> ValueError")
check(leve_v(M.viole_inegalite_bell, 4.5), "S>4 (max algébrique dépassé) -> ValueError")

# ── 8) SOUNDNESS — types invalides (bool / str / NaN / inf) -> ValueError ──
check(leve_v(M.valeur_chsh, True, 0.0, 0.0, 0.0), "bool n'est pas une corrélation -> ValueError")
check(leve_v(M.valeur_chsh, "0.5", 0.0, 0.0, 0.0), "str -> ValueError")
check(leve_v(M.valeur_chsh, float("nan"), 0.0, 0.0, 0.0), "NaN -> ValueError")
check(leve_v(M.viole_inegalite_bell, float("inf")), "inf -> ValueError")
check(leve_v(M.viole_inegalite_bell, "2"), "str S -> ValueError")
check(leve_v(M.etat_bell_correlation, float("nan")), "angle NaN -> ValueError")
check(leve_v(M.etat_bell_correlation, "x"), "angle str -> ValueError")
check(leve_v(M.etat_bell_correlation, True), "angle bool -> ValueError")

# ── 9) DÉTERMINISME ──
check(M.valeur_chsh(-inv, inv, -inv, -inv) == M.valeur_chsh(-inv, inv, -inv, -inv), "déterminisme valeur_chsh")
check(M.etat_bell_correlation(1.0) == M.etat_bell_correlation(1.0), "déterminisme etat_bell_correlation")

print(f"\n=== valide_intrication : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
