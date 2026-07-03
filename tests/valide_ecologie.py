"""VALIDE ecologie.py — held-out ADVERSE, FAUX=0. Ancres EXTERNES connues (règle des 10 % de Lindeman ; équilibre
de l'exemple canonique de Lotka-Volterra α=1.1, β=0.4, γ=0.4, δ=0.1 -> proie*=4, prédateur*=2.75 ; dérivées nulles
à l'équilibre) NON recalculées par la même expression + SOUNDNESS : entrée hors domaine -> ValueError (jamais faux).
"""
import ecologie as E

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
    return x is not None and abs(x - attendu) <= tol


def leve(fn, *a, **k):
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) RÈGLE DES 10 % (Lindeman) — ancre : 10000 J -> 1000 -> 100 -> 10 ──
check(approx(E.energie_niveau(10000, 1), 10000), "niveau 1 (producteur) = energie_base = 10000 J")
check(approx(E.energie_niveau(10000, 2), 1000), "niveau 2 = 10 % de 10000 = 1000 J")
check(approx(E.energie_niveau(10000, 3), 100), "niveau 3 = 1 % de 10000 = 100 J")
check(approx(E.energie_niveau(10000, 4), 10), "niveau 4 = 0.1 % de 10000 = 10 J")
check(approx(E.energie_niveau(10000, 5), 1), "niveau 5 = 1 J")
check(approx(E.energie_niveau(0, 3), 0), "énergie nulle reste nulle à tout niveau")
# efficacité personnalisée (20 %) — externe à la valeur par défaut
check(approx(E.energie_niveau(1000, 3, 0.2), 40), "efficacité 20 % : 1000·0.2² = 40")

# ── efficacité écologique : rendement entre maillons ~10 % ──
check(approx(E.efficacite_ecologique(1000, 10000), 0.1), "rendement niveau2/niveau1 = 0.1 (10 %)")
check(approx(E.efficacite_ecologique(100, 1000), 0.1), "rendement niveau3/niveau2 = 0.1")
check(approx(E.efficacite_ecologique(250, 1000), 0.25), "rendement = 250/1000 = 0.25")
check(approx(E.efficacite_ecologique(0, 5000), 0), "rendement nul si niveau supérieur vide")

# ── 2) LOTKA-VOLTERRA — exemple canonique (Wikipedia) α=1.1 β=0.4 γ=0.4 δ=0.1 ──
px, py = E.equilibre_lotka_volterra(1.1, 0.4, 0.4, 0.1)
check(approx(px, 4.0), "proie* = γ/δ = 0.4/0.1 = 4")
check(approx(py, 2.75), "prédateur* = α/β = 1.1/0.4 = 2.75")
check(approx(E.proie_equilibre(1.1, 0.4, 0.4, 0.1), 4.0), "proie_equilibre = 4")
check(approx(E.predateur_equilibre(1.1, 0.4, 0.4, 0.1), 2.75), "predateur_equilibre = 2.75")
# équilibre simple α=β=γ=δ=1 -> (1,1)
check(approx(E.proie_equilibre(1, 1, 1, 1), 1) and approx(E.predateur_equilibre(1, 1, 1, 1), 1),
      "paramètres unitaires -> équilibre (1,1)")

# dérivées : NULLES au point d'équilibre (définition externe de l'équilibre) ──
check(approx(E.derivee_proie(1.1, 0.4, 4.0, 2.75), 0), "dproie/dt = 0 à l'équilibre")
check(approx(E.derivee_predateur(0.4, 0.1, 4.0, 2.75), 0), "dpredateur/dt = 0 à l'équilibre")
# dérivées hors équilibre : valeurs connues calculées à la main ──
check(approx(E.derivee_proie(1.0, 0.5, 10, 2), 0.0), "dproie = 1·10 − 0.5·10·2 = 10−10 = 0")
check(approx(E.derivee_proie(2.0, 0.5, 10, 1), 15.0), "dproie = 2·10 − 0.5·10·1 = 20−5 = 15")
check(approx(E.derivee_predateur(1.0, 0.5, 10, 2), 8.0), "dpredateur = 0.5·10·2 − 1·2 = 10−2 = 8")
# extinction des prédateurs : proie nulle -> dpredateur = −γ·predateur ──
check(approx(E.derivee_predateur(1.0, 0.5, 0, 4), -4.0), "sans proie : dpredateur = −γ·predateur = −4")

# ── 3) DÉTERMINISME ──
check(E.energie_niveau(10000, 3) == E.energie_niveau(10000, 3), "déterminisme énergie")
check(E.equilibre_lotka_volterra(1.1, 0.4, 0.4, 0.1) == E.equilibre_lotka_volterra(1.1, 0.4, 0.4, 0.1),
      "déterminisme équilibre")

# ── 4) SOUNDNESS — entrée hors domaine -> ValueError (jamais un faux) ──
check(leve(E.energie_niveau, 10000, 0), "niveau 0 -> ValueError (< 1)")
check(leve(E.energie_niveau, 10000, -2), "niveau négatif -> ValueError")
check(leve(E.energie_niveau, 10000, 2.5), "niveau non entier -> ValueError")
check(leve(E.energie_niveau, 10000, True), "niveau booléen -> ValueError")
check(leve(E.energie_niveau, -5, 2), "énergie_base < 0 -> ValueError")
check(leve(E.energie_niveau, "x", 2), "énergie_base non réelle -> ValueError")
check(leve(E.energie_niveau, 10000, 2, 0), "efficacité 0 -> ValueError")
check(leve(E.energie_niveau, 10000, 2, 1.5), "efficacité > 1 -> ValueError")
check(leve(E.efficacite_ecologique, 100, 0), "e_inf = 0 -> ValueError (division)")
check(leve(E.efficacite_ecologique, 100, -10), "e_inf < 0 -> ValueError")
check(leve(E.efficacite_ecologique, -5, 100), "e_sup < 0 -> ValueError")
check(leve(E.equilibre_lotka_volterra, 0, 1, 1, 1), "alpha = 0 -> ValueError")
check(leve(E.equilibre_lotka_volterra, 1, 0, 1, 1), "beta = 0 -> ValueError")
check(leve(E.equilibre_lotka_volterra, 1, 1, -1, 1), "gamma < 0 -> ValueError")
check(leve(E.equilibre_lotka_volterra, 1, 1, 1, 0), "delta = 0 -> ValueError")
check(leve(E.proie_equilibre, 1, 1, 1, 0), "proie_equilibre delta = 0 -> ValueError")
check(leve(E.predateur_equilibre, 0, 1, 1, 1), "predateur_equilibre alpha = 0 -> ValueError")
check(leve(E.derivee_proie, 0, 1, 10, 2), "derivee_proie alpha ≤ 0 -> ValueError")
check(leve(E.derivee_proie, 1, 1, -1, 2), "derivee_proie proie < 0 -> ValueError")
check(leve(E.derivee_predateur, 1, 1, 10, -2), "derivee_predateur predateur < 0 -> ValueError")
check(leve(E.derivee_predateur, 1, 0, 10, 2), "derivee_predateur delta ≤ 0 -> ValueError")

print(f"\n=== valide_ecologie : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
