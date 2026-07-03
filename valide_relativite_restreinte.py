"""
VALIDE relativite_restreinte.py — held-out ADVERSE.

ANCRES EXTERNES (valeurs physiques connues, PAS recalculées par la même expression du module) :
  γ(0)=1, γ(0.6c)=1.25, γ(0.8c)=5/3 (facteurs de Lorentz tabulés) ; dilatation à 0.6c = ×1.25 ;
  contraction à 0.8c = ×0.6 ; addition(0.5c,0.5c)=0.8c ; addition(c,c)=c ; limite galiléenne (v≪c → u+w) ;
  E_repos(1 kg) ≈ 8.98755e16 J ; énergie de masse de l'ÉLECTRON ≈ 0.511 MeV et du PROTON ≈ 938.272 MeV
  (converties via e=1.602176634e-19 C, source indépendante du module).
SOUNDNESS : v≥c, v<0, masse/longueur/temps négatifs, |u|>c, dénominateur nul, type non réel/booléen -> ValueError.
DÉTERMINISME : deux appels identiques renvoient la même valeur.
"""
import math

import relativite_restreinte as R

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
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


c = R.C_LUMIERE
e_charge = 1.602176634e-19   # C — charge élémentaire (SI 2019), source EXTERNE au module
J_par_MeV = e_charge * 1e6   # 1 MeV en joules


def rel(x, attendu, tol=1e-9):
    return abs(x - attendu) <= tol * abs(attendu) + 1e-12


# ── 1) FACTEUR DE LORENTZ — ancres tabulées ──
check(rel(R.facteur_lorentz(0.0), 1.0), "γ(0) = 1")
check(rel(R.facteur_lorentz(0.6 * c), 1.25), "γ(0.6c) = 1.25")
check(rel(R.facteur_lorentz(0.8 * c), 5.0 / 3.0), "γ(0.8c) = 5/3")
check(rel(R.facteur_lorentz(0.99 * c), 7.088812050), "γ(0.99c) ≈ 7.08881")   # ancre externe tabulée
check(R.facteur_lorentz(0.5 * c) > 1.0, "γ(0.5c) > 1 (toujours ≥ 1)")

# ── 2) DILATATION DU TEMPS ──
check(rel(R.dilatation_temps(1.0, 0.6 * c), 1.25), "Δt(0.6c, 1s) = 1.25 s")
check(rel(R.dilatation_temps(2.0, 0.0), 2.0), "Δt(0, 2s) = 2 s (pas de dilatation au repos)")
check(rel(R.dilatation_temps(3.0, 0.8 * c), 5.0), "Δt(0.8c, 3s) = 3·5/3 = 5 s")

# ── 3) CONTRACTION DES LONGUEURS ──
check(rel(R.contraction_longueur(1.0, 0.8 * c), 0.6), "L(0.8c, 1m) = 0.6 m")
check(rel(R.contraction_longueur(1.0, 0.6 * c), 0.8), "L(0.6c, 1m) = 0.8 m")
check(rel(R.contraction_longueur(10.0, 0.0), 10.0), "L(0, 10m) = 10 m (au repos)")

# ── 4) ADDITION RELATIVISTE DES VITESSES ──
check(rel(R.addition_vitesses(0.5 * c, 0.5 * c), 0.8 * c), "0.5c ⊕ 0.5c = 0.8c")
check(R.addition_vitesses(c, c) == c, "c ⊕ c = c (invariance)")
check(rel(R.addition_vitesses(c, 0.3 * c), c), "c ⊕ 0.3c = c")
check(R.addition_vitesses(0.9 * c, 0.9 * c) < c, "0.9c ⊕ 0.9c < c (jamais > c)")
check(rel(R.addition_vitesses(3.0, 4.0), 7.0, tol=1e-9), "limite galiléenne : 3 ⊕ 4 ≈ 7 m/s")
check(rel(R.addition_vitesses(0.6 * c, -0.6 * c), 0.0), "0.6c ⊕ (−0.6c) = 0 (symétrie)")

# ── 5) ÉNERGIE ──
check(rel(R.energie_repos(1.0), 8.98755179e16, tol=1e-6), "E_repos(1 kg) ≈ 8.98755e16 J")
check(rel(R.energie_repos(0.0), 0.0), "E_repos(0) = 0")
check(rel(R.energie_totale(2.0, 0.0), R.energie_repos(2.0)), "E_totale(m,0) = E_repos(m)")
check(rel(R.energie_totale(1.0, 0.6 * c), 1.25 * R.energie_repos(1.0)), "E_totale(0.6c) = γ·mc² = 1.25·mc²")
# Ancres particules (externes, converties en MeV via la charge élémentaire) :
check(rel(R.energie_repos(9.1093837015e-31) / J_par_MeV, 0.51099895, tol=1e-6),
      "masse de l'électron ≈ 0.511 MeV")
check(rel(R.energie_repos(1.67262192369e-27) / J_par_MeV, 938.27208, tol=1e-5),
      "masse du proton ≈ 938.272 MeV")

# ── 6) SOUNDNESS — abstention (jamais un faux) ──
check(leve(R.facteur_lorentz, c), "γ(c) -> ValueError (luminale)")
check(leve(R.facteur_lorentz, 1.5 * c), "γ(1.5c) -> ValueError (supraluminique)")
check(leve(R.facteur_lorentz, -1.0), "γ(v<0) -> ValueError")
check(leve(R.facteur_lorentz, "0.5c"), "γ(str) -> ValueError")
check(leve(R.facteur_lorentz, True), "γ(bool) -> ValueError")
check(leve(R.facteur_lorentz, float("inf")), "γ(inf) -> ValueError")
check(leve(R.dilatation_temps, -1.0, 0.5 * c), "Δt(t<0) -> ValueError")
check(leve(R.dilatation_temps, 1.0, c), "Δt(v=c) -> ValueError")
check(leve(R.contraction_longueur, -2.0, 0.5 * c), "L(L0<0) -> ValueError")
check(leve(R.energie_repos, -1.0), "E_repos(m<0) -> ValueError")
check(leve(R.energie_totale, -1.0, 0.5 * c), "E_totale(m<0) -> ValueError")
check(leve(R.energie_totale, 1.0, c), "E_totale(v=c) -> ValueError")
check(leve(R.addition_vitesses, 1.1 * c, 0.0), "addition(|u|>c) -> ValueError")
check(leve(R.addition_vitesses, 0.0, 2.0 * c), "addition(|w|>c) -> ValueError")
check(leve(R.addition_vitesses, c, -c), "addition(c,−c) -> ValueError (0/0)")
check(leve(R.addition_vitesses, None, 0.0), "addition(None) -> ValueError")

# ── 7) DÉTERMINISME ──
check(R.facteur_lorentz(0.73 * c) == R.facteur_lorentz(0.73 * c), "déterministe γ")
check(R.addition_vitesses(0.4 * c, 0.5 * c) == R.addition_vitesses(0.4 * c, 0.5 * c), "déterministe addition")

print(f"\n=== valide_relativite_restreinte : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
