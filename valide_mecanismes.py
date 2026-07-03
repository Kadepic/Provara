"""
VALIDE mecanismes.py — held-out ADVERSE. Exactitude des formules de transmission, ancrées sur des valeurs
MÉCANIQUES CONNUES non recalculées par la même expression (réducteur 10→40 : i=4, vitesse ÷4, couple ×4 ;
levier 4/1 : AM=4 ; cohérence ω_sortie·i = ω_entree), + SOUNDNESS : dents/bras/rapport ≤ 0, type non numérique,
bool, inf/NaN -> ValueError (jamais un faux). Aucun de ces résultats n'est codé en dur dans mecanismes.py.
"""
import math

import mecanismes as M

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def approx(v, attendu, tol=1e-9):
    return v is not None and abs(v - attendu) <= tol


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) EXACTITUDE — cas de référence du sujet (10→40 dents) ──
check(approx(M.rapport_engrenages(10, 40), 4.0), "i = 40/10 = 4 (réducteur)")
check(approx(M.vitesse_sortie(1200, 10, 40), 300.0), "ω_sortie = 1200·10/40 = 300 (÷4)")
check(approx(M.couple_sortie(5.0, 4.0), 20.0), "C_sortie = 5·4 = 20 (×4)")
check(approx(M.avantage_mecanique_levier(4, 1), 4.0), "AM levier 4/1 = 4")

# ── 2) AUTRES ANCRES CONNUES (valeurs externes, pas re-dérivées) ──
check(approx(M.rapport_engrenages(20, 60), 3.0), "i = 60/20 = 3")
check(approx(M.rapport_engrenages(40, 10), 0.25), "i = 10/40 = 0.25 (multiplicateur)")
check(approx(M.rapport_engrenages(12, 12), 1.0), "i = 12/12 = 1 (prise directe)")
check(approx(M.vitesse_sortie(3000, 12, 36), 1000.0), "ω = 3000·12/36 = 1000")
check(approx(M.vitesse_sortie(100, 25, 25), 100.0), "prise directe : ω inchangée")
check(approx(M.couple_sortie(10.0, 3.0), 30.0), "C = 10·3 = 30")
check(approx(M.avantage_mecanique_levier(2.0, 0.5), 4.0), "AM = 2/0.5 = 4")
check(approx(M.avantage_mecanique_levier(0.3, 0.3), 1.0), "AM = 1 (bras égaux)")

# ── 3) COHÉRENCE CROISÉE (deux fonctions, identité physique) ──
#     ω_sortie = ω_entree / i  ⇔  ω_sortie · i = ω_entree (conservation de Z·ω)
i = M.rapport_engrenages(10, 40)
ws = M.vitesse_sortie(1500, 10, 40)
check(approx(ws * i, 1500.0), "ω_sortie · i = ω_entree (cohérence cinématique)")
#     réducteur idéal : la puissance se conserve, donc C_sortie/C_entree = ω_entree/ω_sortie = i
check(approx(M.couple_sortie(7.0, i) / 7.0, M.rapport_engrenages(10, 40)), "C_sortie/C_entree = i (puissance conservée)")

# ── 4) SIGNES (vitesse/couple peuvent être négatifs = sens de rotation) ──
check(approx(M.vitesse_sortie(-800, 10, 40), -200.0), "ω négative propagée (sens inverse)")
check(approx(M.couple_sortie(-6.0, 2.0), -12.0), "couple négatif propagé")
check(approx(M.vitesse_sortie(0, 10, 40), 0.0), "ω entrée nulle -> sortie nulle")

# ── 5) DÉTERMINISME ──
check(M.rapport_engrenages(10, 40) == M.rapport_engrenages(10, 40), "déterministe (rapport)")
check(M.couple_sortie(5.0, 4.0) == M.couple_sortie(5.0, 4.0), "déterministe (couple)")

# ── 6) SOUNDNESS — dents ≤ 0 -> ValueError ──
check(leve(M.rapport_engrenages, 0, 40), "dents_menante = 0 -> ValueError")
check(leve(M.rapport_engrenages, 10, 0), "dents_menee = 0 -> ValueError")
check(leve(M.rapport_engrenages, -10, 40), "dents_menante < 0 -> ValueError")
check(leve(M.rapport_engrenages, 10, -40), "dents_menee < 0 -> ValueError")
check(leve(M.vitesse_sortie, 1200, 0, 40), "dents_men = 0 -> ValueError")
check(leve(M.vitesse_sortie, 1200, 10, 0), "dents_mene = 0 -> ValueError")
check(leve(M.vitesse_sortie, 1200, -10, 40), "dents_men < 0 -> ValueError")

# ── 7) SOUNDNESS — bras ≤ 0, rapport ≤ 0 ──
check(leve(M.avantage_mecanique_levier, 0, 1), "bras_force = 0 -> ValueError")
check(leve(M.avantage_mecanique_levier, 4, 0), "bras_charge = 0 -> ValueError")
check(leve(M.avantage_mecanique_levier, -4, 1), "bras_force < 0 -> ValueError")
check(leve(M.couple_sortie, 5.0, 0), "rapport = 0 -> ValueError")
check(leve(M.couple_sortie, 5.0, -4), "rapport < 0 -> ValueError")

# ── 8) SOUNDNESS — type non numérique / bool / non-fini ──
check(leve(M.rapport_engrenages, "10", 40), "dents str -> ValueError")
check(leve(M.rapport_engrenages, None, 40), "dents None -> ValueError")
check(leve(M.rapport_engrenages, True, 40), "dents bool -> ValueError (bool rejeté)")
check(leve(M.couple_sortie, float("inf"), 4.0), "couple inf -> ValueError")
check(leve(M.couple_sortie, float("nan"), 4.0), "couple NaN -> ValueError")
check(leve(M.vitesse_sortie, float("nan"), 10, 40), "vitesse NaN -> ValueError")
check(leve(M.avantage_mecanique_levier, float("inf"), 1), "bras inf -> ValueError")

print(f"\n=== valide_mecanismes : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
