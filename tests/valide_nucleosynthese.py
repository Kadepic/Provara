"""
VALIDE nucleosynthese.py — held-out ADVERSE.

Exactitude ancrée sur des VALEURS NUCLÉAIRES CONNUES, indépendantes (pas re-calculées par la même expression) :
  • énergie de liaison de ⁴He ≈ 28.3 MeV et 7.07 MeV/nucléon (table de masses) ;
  • liaison du deutéron ≈ 2.224 MeV (Δm = 0.002388 u) ;
  • fusion D+T → ⁴He+n libère ≈ 17.6 MeV (Q>0, exothermique) ;
  • branche D+D → ³He+n libère ≈ 3.27 MeV ;
  • pic de fer ⁵⁶Fe ≈ 8.79 MeV/nucléon.
SOUNDNESS : Δm<0, masses ≤0, A non entier-positif, E_liaison<0, entrée non numérique / NaN / inf -> ValueError.
Aucun de ces cas n'est codé en dur dans nucleosynthese.py.
"""
import math

import nucleosynthese as N

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def approx(a, b, rel=1e-4, abs_=1e-9):
    return abs(a - b) <= rel * abs(b) + abs_


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) ÉNERGIE DE LIAISON — ancres ⁴He et deutéron ─────────────────────────────────────────────────────────────
E_he4 = N.energie_liaison(0.0304)                 # Δm(⁴He) ≈ 0.0304 u
check(approx(E_he4, 28.3174, rel=1e-4), f"E_l(⁴He) = 0.0304·931.494 ≈ 28.32 MeV (obtenu {E_he4})")
check(approx(E_he4, 28.3, rel=2e-3), "E_l(⁴He) ≈ 28.3 MeV (valeur nucléaire connue)")
check(approx(N.energie_liaison(0.002388), 2.224, rel=2e-3),
      "liaison du deutéron ≈ 2.224 MeV (Δm = 0.002388 u)")
check(N.energie_liaison(0.0) == 0.0, "Δm = 0 -> E_l = 0 (cas limite valide)")
check(approx(N.energie_liaison(1.0), 931.494, rel=1e-9), "1 u -> 931.494 MeV (constante d'équivalence)")

# ── 2) ÉNERGIE PAR NUCLÉON — ⁴He et pic de fer ─────────────────────────────────────────────────────────────────
e_par = N.energie_liaison_par_nucleon(E_he4, 4)
check(approx(e_par, 7.0794, rel=1e-4), f"E_l/A(⁴He) = 28.32/4 ≈ 7.08 MeV/nucléon (obtenu {e_par})")
check(approx(e_par, 7.07, rel=3e-3), "⁴He ≈ 7.07 MeV/nucléon (valeur connue)")
check(approx(N.energie_liaison_par_nucleon(492.254, 56), 8.7903, rel=1e-4),
      "⁵⁶Fe = 492.254/56 ≈ 8.79 MeV/nucléon (pic de fer)")
# ⁴He (7.07) est SOUS le pic de fer (8.79) — cohérence de la courbe d'Aston
check(e_par < N.pic_fer()["energie_par_nucleon_MeV"], "⁴He sous le pic de ⁵⁶Fe (courbe d'Aston)")

# ── 3) Q DE RÉACTION — fusion exothermique (ancres D-T, D-D) ────────────────────────────────────────────────────
# D+T → ⁴He+n : 2.014102 + 3.016049  ->  4.002602 + 1.008665 (masses atomiques u)
Q_dt = N.q_reaction(2.014102 + 3.016049, 4.002602 + 1.008665)
check(Q_dt > 0, "fusion D+T : Q>0 -> exothermique (H→He libère de l'énergie)")
check(approx(Q_dt, 17.59, rel=3e-3), f"fusion D+T libère ≈ 17.6 MeV (obtenu {Q_dt})")
# D+D → ³He+n : 2·2.014102 -> 3.016029 + 1.008665
Q_dd = N.q_reaction(2 * 2.014102, 3.016029 + 1.008665)
check(approx(Q_dd, 3.27, rel=5e-3), f"fusion D+D→³He+n ≈ 3.27 MeV (obtenu {Q_dd})")
# au-delà du pic de fer : produits plus lourds -> Q<0 (endothermique)
Q_endo = N.q_reaction(4.0, 4.001)
check(Q_endo < 0, "produits plus lourds que réactifs -> Q<0 (endothermique)")
check(approx(Q_endo, -0.931494, rel=1e-6), "Q = (4.0−4.001)·931.494 ≈ −0.9315 MeV")

# ── 4) PIC DE FER — fait établi ────────────────────────────────────────────────────────────────────────────────
pf = N.pic_fer()
check(pf["nuclide"] == "Fe-56" and pf["A"] == 56 and pf["Z"] == 26, "pic_fer = ⁵⁶Fe (Z=26, A=56)")
check(approx(pf["energie_par_nucleon_MeV"], 8.79, rel=2e-3), "pic_fer ≈ 8.79 MeV/nucléon")
check(approx(pf["energie_liaison_MeV"] / pf["A"], pf["energie_par_nucleon_MeV"], rel=1e-3),
      "cohérence interne pic_fer : E_l/A == énergie par nucléon")
pf["nuclide"] = "MUTÉ"  # la copie ne doit pas altérer le fait interne
check(N.pic_fer()["nuclide"] == "Fe-56", "pic_fer() renvoie une copie (fait immuable)")

# ── 5) DÉTERMINISME ────────────────────────────────────────────────────────────────────────────────────────────
check(N.energie_liaison(0.0304) == N.energie_liaison(0.0304), "energie_liaison déterministe")
check(N.q_reaction(5.0, 4.9) == N.q_reaction(5.0, 4.9), "q_reaction déterministe")

# ── 6) SOUNDNESS — abstention (ValueError), jamais un faux ──────────────────────────────────────────────────────
check(leve(N.energie_liaison, -0.01), "Δm < 0 -> ValueError")
check(leve(N.energie_liaison, "x"), "Δm non numérique -> ValueError")
check(leve(N.energie_liaison, True), "Δm bool -> ValueError")
check(leve(N.energie_liaison, float("nan")), "Δm NaN -> ValueError")
check(leve(N.energie_liaison, float("inf")), "Δm inf -> ValueError")
check(leve(N.energie_liaison_par_nucleon, 28.3, 0), "A = 0 -> ValueError")
check(leve(N.energie_liaison_par_nucleon, 28.3, -4), "A < 0 -> ValueError")
check(leve(N.energie_liaison_par_nucleon, 28.3, 4.5), "A non entier -> ValueError")
check(leve(N.energie_liaison_par_nucleon, 28.3, True), "A bool -> ValueError")
check(leve(N.energie_liaison_par_nucleon, -1.0, 4), "E_liaison < 0 -> ValueError")
check(leve(N.q_reaction, 0, 1), "masse réactifs = 0 -> ValueError")
check(leve(N.q_reaction, -1, 1), "masse réactifs < 0 -> ValueError")
check(leve(N.q_reaction, 1, 0), "masse produits = 0 -> ValueError")
check(leve(N.q_reaction, 1, -1), "masse produits < 0 -> ValueError")
check(leve(N.q_reaction, "a", 1), "masse non numérique -> ValueError")

print(f'\n=== valide_nucleosynthese : {ok}/{ok+ko} ===')
import sys
sys.exit(0 if ko == 0 else 1)
