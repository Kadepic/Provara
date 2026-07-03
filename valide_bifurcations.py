"""
VALIDE bifurcations.py — held-out ADVERSE. Ancres EXTERNES connues de la théorie des systèmes dynamiques
(stabilité d'un puits/source, carte logistique r=2 stable / r=3.5 chaotique, doublement de période à r=3,
formes normales pli/fourche) + cross-checks NON re-calculés par la même expression (μ via r·(1-2x*) plutôt
que 2-r) + SOUNDNESS (entrée non numérique / r=0 / NaN -> ValueError) + déterminisme.
"""
import bifurcations as B

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


def proche(x, attendu, tol=1e-9):
    return isinstance(x, float) and abs(x - attendu) <= tol


# ── 1) STABILITÉ CONTINUE (signe de f'(x*)) — ancres : puits x'=-x stable, source x'=x instable ──
check(B.stabilite_point_fixe(-2.0) == "stable", "f'=-2 < 0 -> stable")
check(B.stabilite_point_fixe(-1e-9) == "stable", "f' légèrement <0 -> stable")
check(B.stabilite_point_fixe(0.5) == "instable", "f'=0.5 > 0 -> instable (flot continu)")
check(B.stabilite_point_fixe(3.0) == "instable", "f'=3 > 0 -> instable")
check(B.stabilite_point_fixe(0.0) == "marginal", "f'=0 -> marginal (linéarisation muette)")

# ── 2) STABILITÉ DISCRÈTE (module du multiplicateur) ──
check(B.stabilite_point_fixe_discret(0.5) == "stable", "|μ|=0.5 < 1 -> stable (carte)")
check(B.stabilite_point_fixe_discret(-0.5) == "stable", "|μ|=0.5 (négatif) < 1 -> stable")
check(B.stabilite_point_fixe_discret(-2.0) == "instable", "|μ|=2 > 1 -> instable")
check(B.stabilite_point_fixe_discret(1.5) == "instable", "|μ|=1.5 > 1 -> instable")
check(B.stabilite_point_fixe_discret(1.0) == "marginal", "|μ|=1 -> marginal (bifurcation)")
check(B.stabilite_point_fixe_discret(-1.0) == "marginal", "|μ|=1 (μ=-1) -> marginal (doublement)")

# ── 3) CARTE LOGISTIQUE — ancres dynamiques connues ──
check(B.bifurcation_logistique(2.0) == "stable", "r=2 -> point fixe stable (x*=0.5)")
check(B.bifurcation_logistique(2.5) == "stable", "r=2.5 -> stable (1<r<3)")
check(B.bifurcation_logistique(1.5) == "stable", "r=1.5 -> stable")
check(B.bifurcation_logistique(3.5) == "instable", "r=3.5 -> point fixe instable (régime périodique/chaos)")
check(B.bifurcation_logistique(4.0) == "instable", "r=4 -> instable (μ=-2)")
check(B.bifurcation_logistique(0.5) == "instable", "r=0.5 -> instable (μ=1.5)")
check(B.bifurcation_logistique(3.0) == "marginal", "r=3 -> marginal (μ=-1, doublement de période)")
check(B.bifurcation_logistique(1.0) == "marginal", "r=1 -> marginal (μ=+1, transcritique)")

# Point fixe non trivial x* = 1 - 1/r (ancres exactes connues)
check(proche(B.point_fixe_logistique(2.0), 0.5), "x*(r=2) = 0.5")
check(proche(B.point_fixe_logistique(4.0), 0.75), "x*(r=4) = 0.75")
check(proche(B.point_fixe_logistique(1.0), 0.0), "x*(r=1) = 0 (fusion avec point fixe trivial)")

# Cross-check du multiplicateur : μ = 2-r ET μ = r·(1-2·x*) calculés INDÉPENDAMMENT doivent coïncider.
for r in (1.5, 2.0, 2.5, 3.0, 3.5, 4.0):
    xstar = 1.0 - 1.0 / r
    mu_independant = r * (1.0 - 2.0 * xstar)          # définition g'(x*), pas l'expression 2-r du module
    check(proche(B.multiplicateur_logistique(r), mu_independant, 1e-9),
          f"μ(r={r}) = r·(1-2x*) = {mu_independant:.6f}")
check(proche(B.multiplicateur_logistique(4.0), -2.0), "μ(r=4) = -2 (ancre)")
check(proche(B.multiplicateur_logistique(3.0), -1.0), "μ(r=3) = -1 (seuil de stabilité)")

# ── 4) FORMES NORMALES (catastrophes élémentaires) ──
check(B.nb_points_fixes_pli(-1.0) == 2, "pli μ=-1 -> 2 points fixes (±1)")
check(B.nb_points_fixes_pli(0.0) == 1, "pli μ=0 -> 1 (bifurcation nœud-col)")
check(B.nb_points_fixes_pli(1.0) == 0, "pli μ=1 -> 0 point fixe réel")
check(B.nb_points_fixes_fourche(-1.0) == 1, "fourche μ=-1 -> 1 (x=0 seul)")
check(B.nb_points_fixes_fourche(0.0) == 1, "fourche μ=0 -> 1 (bifurcation)")
check(B.nb_points_fixes_fourche(2.0) == 3, "fourche μ=2 -> 3 (x=0, ±√2)")

# ── 5) SOUNDNESS — entrée non numérique / hors-domaine / non finie -> ValueError (abstention, jamais un faux) ──
check(leve(B.stabilite_point_fixe, "x"), "stabilite_point_fixe('x') -> ValueError")
check(leve(B.stabilite_point_fixe, None), "stabilite_point_fixe(None) -> ValueError")
check(leve(B.stabilite_point_fixe, True), "bool rejeté -> ValueError")
check(leve(B.stabilite_point_fixe, float("nan")), "NaN rejeté -> ValueError")
check(leve(B.stabilite_point_fixe, float("inf")), "inf rejeté -> ValueError")
check(leve(B.stabilite_point_fixe_discret, "a"), "stabilite_point_fixe_discret('a') -> ValueError")
check(leve(B.bifurcation_logistique, None), "bifurcation_logistique(None) -> ValueError")
check(leve(B.bifurcation_logistique, "r"), "bifurcation_logistique('r') -> ValueError")
check(leve(B.point_fixe_logistique, 0), "point_fixe_logistique(0) -> ValueError (1/r)")
check(leve(B.point_fixe_logistique, 0.0), "point_fixe_logistique(0.0) -> ValueError")
check(leve(B.point_fixe_logistique, "a"), "point_fixe_logistique('a') -> ValueError")
check(leve(B.multiplicateur_logistique, None), "multiplicateur_logistique(None) -> ValueError")
check(leve(B.nb_points_fixes_pli, None), "nb_points_fixes_pli(None) -> ValueError")
check(leve(B.nb_points_fixes_fourche, "x"), "nb_points_fixes_fourche('x') -> ValueError")

# ── 6) DÉTERMINISME ──
check(B.bifurcation_logistique(2.0) == B.bifurcation_logistique(2.0), "déterminisme logistique")
check(B.stabilite_point_fixe(-2.0) == B.stabilite_point_fixe(-2.0), "déterminisme stabilité")
check(B.point_fixe_logistique(4.0) == B.point_fixe_logistique(4.0), "déterminisme point fixe")

print(f"\n=== valide_bifurcations : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
