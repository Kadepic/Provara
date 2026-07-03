"""
VALIDE proprietes_materiaux.py — held-out ADVERSE. Exactitude des formules de la mécanique des matériaux ancrée sur
des valeurs CONNUES (acier E≈210 GPa, 210 MPa donne 0.1 % de déformation, allongement 2 mm d'une barre de 2 m…),
vérifiées par DIFFÉRENTES fonctions (cohérence croisée de Hooke σ=E·ε : la contrainte issue de F/A doit coïncider
avec E·ε et le module reconstruit doit redonner E) — donc jamais re-calculées par la même expression.
+ SOUNDNESS : aire/longueur/module ≤ 0, déformation nulle, argument non numérique/booléen/non fini -> ValueError.
+ DÉTERMINISME.
"""
import proprietes_materiaux as M

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def approx(v, attendu, rel=1e-9):
    return v is not None and abs(v - attendu) <= rel * abs(attendu) + 1e-12


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) EXACTITUDE — cas simples à résultat connu ──
check(approx(M.contrainte(100, 4), 25.0), "σ = 100/4 = 25 Pa")
check(approx(M.deformation(3, 6), 0.5), "ε = 3/6 = 0.5")
check(approx(M.module_young(50, 0.5), 100.0), "E = 50/0.5 = 100 Pa")
check(approx(M.hooke_contrainte(200, 0.01), 2.0), "Hooke σ = 200·0.01 = 2 Pa")
check(approx(M.hooke_deformation(2, 200), 0.01), "Hooke ε = 2/200 = 0.01")
check(approx(M.allongement(10, 2, 1, 5), 4.0), "ΔL = 10·2/(1·5) = 4 m")

# ── 2) ANCRE PHYSIQUE — barre d'acier (E ≈ 210 GPa, valeur de référence externe) ──
# Section A = 1 cm² = 1e-4 m², force F = 21000 N -> σ = 210 MPa (contrainte connue).
check(approx(M.contrainte(21000, 1e-4), 2.1e8), "σ = 21000/1e-4 = 210 MPa")
# Sous 210 MPa avec E = 210 GPa, la déformation est 0.001 (= 0.1 %), valeur de référence bien connue.
check(approx(M.hooke_deformation(2.1e8, 2.1e11), 1e-3), "210 MPa sur acier 210 GPa -> ε = 0.001")
# Le module reconstruit à partir de (σ, ε) redonne 210 GPa (acier) — cohérence croisée, autre fonction.
check(approx(M.module_young(2.1e8, 1e-3), 2.1e11), "E reconstruit = 210e6/0.001 = 210 GPa")
# Hooke direct : E·ε redonne σ = 210 MPa (cohérence croisée).
check(approx(M.hooke_contrainte(2.1e11, 1e-3), 2.1e8), "Hooke E·ε = 210e9·0.001 = 210 MPa")
# Barre de L0 = 2 m -> allongement ΔL = ε·L0 = 0.002 m = 2 mm (référence), via formule directe F·L0/(A·E).
check(approx(M.allongement(21000, 2.0, 1e-4, 2.1e11), 2.0e-3), "ΔL acier = F·L0/(A·E) = 2 mm")
# ΔL/L0 redonne la déformation 0.001 (boucle de cohérence par une autre fonction).
check(approx(M.deformation(M.allongement(21000, 2.0, 1e-4, 2.1e11), 2.0), 1e-3), "ΔL/L0 = 0.001")

# ── 3) SIGNE PHYSIQUE — compression conserve le signe (pas de valeur absolue cachée) ──
check(approx(M.contrainte(-21000, 1e-4), -2.1e8), "compression : σ < 0")
check(approx(M.deformation(-1.0, 4.0), -0.25), "raccourcissement : ε < 0")
check(approx(M.hooke_contrainte(2.1e11, -1e-3), -2.1e8), "Hooke compression σ < 0")

# ── 4) COHÉRENCE CROISÉE GÉNÉRALE — Hooke σ = E·ε pour un 2e matériau (alu E = 70 GPa) ──
sig_alu = M.hooke_contrainte(7.0e10, 2e-3)         # 70 GPa · 0.002 = 140 MPa
check(approx(sig_alu, 1.4e8), "alu : σ = 70e9·0.002 = 140 MPa")
check(approx(M.module_young(sig_alu, 2e-3), 7.0e10), "alu : E reconstruit = 70 GPa")
check(approx(M.hooke_deformation(sig_alu, 7.0e10), 2e-3), "alu : ε reconstruit = 0.002")

# ── 5) SOUNDNESS — domaine invalide -> ValueError (jamais un nombre faux) ──
check(leve(M.contrainte, 100, 0), "aire A = 0 -> ValueError")
check(leve(M.contrainte, 100, -1e-4), "aire A < 0 -> ValueError")
check(leve(M.deformation, 0.002, 0), "L0 = 0 -> ValueError")
check(leve(M.deformation, 0.002, -2), "L0 < 0 -> ValueError")
check(leve(M.module_young, 2.1e8, 0), "ε = 0 (module indéterminé) -> ValueError")
check(leve(M.hooke_contrainte, 0, 1e-3), "E = 0 -> ValueError")
check(leve(M.hooke_contrainte, -2.1e11, 1e-3), "E < 0 -> ValueError")
check(leve(M.hooke_deformation, 2.1e8, 0), "E = 0 (Hooke inv) -> ValueError")
check(leve(M.allongement, 21000, 2.0, 0, 2.1e11), "A = 0 (allongement) -> ValueError")
check(leve(M.allongement, 21000, 0, 1e-4, 2.1e11), "L0 = 0 (allongement) -> ValueError")
check(leve(M.allongement, 21000, 2.0, 1e-4, 0), "E = 0 (allongement) -> ValueError")
check(leve(M.allongement, 21000, 2.0, 1e-4, -5), "E < 0 (allongement) -> ValueError")

# ── 6) SOUNDNESS — type / booléen / non fini -> ValueError ──
check(leve(M.contrainte, "100", 4), "F non numérique (str) -> ValueError")
check(leve(M.contrainte, True, 4), "F booléen -> ValueError")
check(leve(M.contrainte, 100, None), "A None -> ValueError")
check(leve(M.contrainte, float("inf"), 4), "F = inf -> ValueError")
check(leve(M.contrainte, float("nan"), 4), "F = nan -> ValueError")
check(leve(M.module_young, 2.1e8, False), "ε booléen False -> ValueError")

# ── 7) DÉTERMINISME ──
check(M.contrainte(21000, 1e-4) == M.contrainte(21000, 1e-4), "contrainte déterministe")
check(M.allongement(21000, 2.0, 1e-4, 2.1e11) == M.allongement(21000, 2.0, 1e-4, 2.1e11), "allongement déterministe")

print(f"\n=== valide_proprietes_materiaux : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
