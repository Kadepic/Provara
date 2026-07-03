"""VALIDE controle_qualite.py — held-out ADVERSE. Ancres EXTERNES connues (non recalculées par la même
expression : Cp=20/12=1.6667 du sujet, table Six Sigma 6σ→3.4 / 3σ→66807 DPMO, procédé ±3σ centré ≈ 2700 ppm,
Φ(1.96)=0.975 des tables statistiques) + SOUNDNESS (σ≤0, LSS≤LSI, n≤0, type invalide -> ValueError) + déterminisme.
"""
import controle_qualite as M

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def approx(v, attendu, tol=1e-6):
    return v is not None and abs(v - attendu) <= tol * (1 + abs(attendu))


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True


# ── 1) Cp — ancre du sujet : LSS=110, LSI=90, σ=2 -> 20/12 ≈ 1.6667 ──
check(approx(M.indice_capabilite_cp(110, 90, 2), 20.0 / 12.0), "Cp = (110-90)/(6·2) = 20/12 ≈ 1.6667")
check(approx(M.indice_capabilite_cp(110, 90, 2), 1.6666666667, 1e-9), "Cp valeur décimale connue")
check(approx(M.indice_capabilite_cp(100, 70, 5), 1.0), "Cp = 30/(6·5) = 1.0 (cas pile capable)")

# ── 2) Cpk centré = Cp ; Cpk décentré < Cp ──
check(approx(M.cpk(100, 110, 90, 2), M.indice_capabilite_cp(110, 90, 2)), "Cpk centré (moy=100) = Cp")
check(approx(M.cpk(105, 110, 90, 2), 5.0 / 6.0), "Cpk décentré (moy=105) = min(5/6,15/6) = 0.8333")
check(M.cpk(105, 110, 90, 2) < M.indice_capabilite_cp(110, 90, 2), "Cpk décentré < Cp")
check(M.cpk(99, 110, 90, 2) < M.cpk(100, 110, 90, 2), "plus décentré -> Cpk plus petit")
check(approx(M.cpk(95, 110, 90, 2), 5.0 / 6.0), "Cpk symétrique (moy=95) = 0.8333 (côté bas limitant)")

# ── 3) Limites de contrôle ──
check(M.limites_controle(100, 2, 3) == (94.0, 106.0), "limites ±3σ = (94, 106)")
check(M.limites_controle(50, 5) == (35.0, 65.0), "limites par défaut n=3 = (35, 65)")
check(M.limites_controle(0, 1, 1) == (-1.0, 1.0), "limites ±1σ = (-1, 1)")

# ── 4) Loi normale Φ — ancres des TABLES statistiques (non recalculées ici) ──
check(approx(M.phi(0), 0.5), "Φ(0) = 0.5 (symétrie)")
check(approx(M.phi(1), 0.8413447461, 1e-7), "Φ(1) = 0.8413 (table)")
check(approx(M.phi(2), 0.9772498681, 1e-7), "Φ(2) = 0.9772 (table)")
check(approx(M.phi(1.96), 0.9750021049, 1e-7), "Φ(1.96) = 0.9750 (intervalle 95%)")
check(approx(M.phi(-1) + M.phi(1), 1.0), "Φ(-z)+Φ(z) = 1 (symétrie)")

# ── 5) PPM hors specs — procédé centré ±3σ ≈ 2700 ppm (99.73% conforme), valeur de référence SPC ──
check(approx(M.ppm_hors_specs(0, 3, -3, 1), 2699.796063, 1e-3), "±3σ centré ≈ 2700 ppm")
check(approx(M.ppm_hors_specs(0, 6, -6, 1), 0.001973175, 1e-6), "±6σ centré ≈ 0.002 ppm (court terme)")
check(M.ppm_hors_specs(5, 110, 90, 2) > M.ppm_hors_specs(100, 110, 90, 2),
      "procédé hors centre -> beaucoup plus de défauts")

# ── 6) six_sigma_ppm — TABLE Six Sigma classique (dérive 1.5σ), ancres mémorisées de l'industrie ──
check(approx(M.six_sigma_ppm(6), 3.4, 0.05), "6σ -> 3.4 DPMO (le nombre emblématique)")
check(approx(M.six_sigma_ppm(3), 66807.0, 1.0), "3σ -> 66807 DPMO (table)")
check(approx(M.six_sigma_ppm(4.5), 1350.0, 1.0), "4.5σ -> 1350 DPMO (table)")
check(approx(M.six_sigma_ppm(5), 233.0, 1.0), "5σ -> 233 DPMO (table)")
check(M.six_sigma_ppm(6) < M.six_sigma_ppm(3), "niveau sigma plus haut -> moins de défauts")

# ── 7) SOUNDNESS — entrée invalide -> ValueError (jamais un faux) ──
check(leve(M.indice_capabilite_cp, 110, 90, 0), "σ=0 -> ValueError")
check(leve(M.indice_capabilite_cp, 110, 90, -2), "σ<0 -> ValueError")
check(leve(M.indice_capabilite_cp, 90, 110, 2), "LSS<LSI -> ValueError")
check(leve(M.indice_capabilite_cp, 100, 100, 2), "LSS=LSI -> ValueError")
check(leve(M.cpk, 100, 90, 110, 2), "Cpk LSS<LSI -> ValueError")
check(leve(M.cpk, 100, 110, 90, 0), "Cpk σ=0 -> ValueError")
check(leve(M.limites_controle, 100, -1), "limites σ<0 -> ValueError")
check(leve(M.limites_controle, 100, 2, 0), "limites n=0 -> ValueError")
check(leve(M.limites_controle, 100, 2, -3), "limites n<0 -> ValueError")
check(leve(M.ppm_hors_specs, 0, -3, 3, 1), "ppm LSS<LSI -> ValueError")
check(leve(M.ppm_hors_specs, 0, 3, -3, 0), "ppm σ=0 -> ValueError")
check(leve(M.six_sigma_ppm, 0), "niveau sigma=0 -> ValueError")
check(leve(M.six_sigma_ppm, 6, -1), "dérive<0 -> ValueError")

# ── 8) SOUNDNESS — types invalides (bool / str / non fini) -> ValueError ──
check(leve(M.indice_capabilite_cp, 110, 90, True), "bool n'est pas un nombre -> ValueError")
check(leve(M.cpk, "cent", 110, 90, 2), "str -> ValueError")
check(leve(M.phi, float("nan")), "NaN -> ValueError")
check(leve(M.phi, float("inf")), "inf -> ValueError")

# ── 9) DÉTERMINISME ──
check(M.cpk(105, 110, 90, 2) == M.cpk(105, 110, 90, 2), "déterminisme Cpk")
check(M.phi(1.96) == M.phi(1.96), "déterminisme Φ")

print(f"\n=== valide_controle_qualite : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
