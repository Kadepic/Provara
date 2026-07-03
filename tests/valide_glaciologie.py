"""
VALIDE glaciologie.py — held-out ADVERSE (ancres CONNUES non circulaires + soundness + déterminisme).

Ancres calculées À LA MAIN / indépendamment (pas par une fonction sœur du module) :
  • bilan +2 −1 = +1 (croît) ; 5−5 = 0 ; 1−3 = −2 (décroît).
  • iceberg : 1 − 917/1025 = 0.10536585365853657 ≈ 0.105 (≈10 % émergé).
  • loi de Glen : ε̇ = A·σⁿ ; A=2.4e-24, n=3, σ=1e5 -> 2.4e-9 ; σ=2e5 -> 1.92e-8.
  • épaisseur d'équilibre : h = τ0/(ρ·g·sin α) ; α=30°, τ0=1e5, ρ=917, g=9.81 -> 22.232671... m,
    et le contrôle physique ρ·g·h·sin α redonne τ0 (cohérence de la plasticité parfaite).
SOUNDNESS : densités <= 0, rho_glace>=rho_eau, accumulation/ablation<0, σ<0, A<=0, n<=0,
            angle hors ]0,90[, valeurs non finies -> ValueError (jamais un faux).
DÉTERMINISME : mêmes entrées -> mêmes sorties.
"""

import math
import glaciologie as G

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


# ── 1) ANCRE — bilan massique (identité comptable) ──
check(approx(G.bilan_massique(2, 1), 1.0), "bilan +2−1 = +1 (croît)")
check(G.bilan_massique(2, 1) > 0, "bilan +1 > 0 -> le glacier croît")
check(approx(G.bilan_massique(5, 5), 0.0), "bilan 5−5 = 0 (stable)")
check(approx(G.bilan_massique(1, 3), -2.0), "bilan 1−3 = −2 (décroît)")
check(G.bilan_massique(1, 3) < 0, "bilan −2 < 0 -> le glacier décroît")
check(approx(G.bilan_massique(0, 0), 0.0), "bilan 0−0 = 0")
check(approx(G.bilan_massique(3.5, 1.2), 2.3), "bilan 3.5−1.2 = 2.3")
check(approx(G.bilan_massique(2.5, 0), 2.5), "bilan 2.5−0 = 2.5")

# ── 2) ANCRE — fraction émergée de l'iceberg (Archimède) ──
attendu_ice = 1.0 - 917.0 / 1025.0  # = 0.10536585365853657
f = G.fraction_emergee_iceberg()
check(approx(f, attendu_ice, tol=1e-6), f"iceberg défaut = 1−917/1025 ≈ 0.105366 (obtenu {f})")
check(approx(f, 0.105, tol=1e-3), "iceberg ≈ 0.105 (≈10 % émergé)")
check(0.10 < f < 0.11, "fraction émergée dans ]0.10, 0.11[")
# eau douce : ρ_eau = 1000 -> 1 − 917/1000 = 0.083
check(approx(G.fraction_emergee_iceberg(917, 1000), 1.0 - 917.0 / 1000.0, tol=1e-6),
      "iceberg eau douce (1000) = 0.083")
# valeurs simples vérifiables
check(approx(G.fraction_emergee_iceberg(500, 1000), 0.5, tol=1e-9),
      "iceberg ρ=500/1000 -> 0.5 émergé")
check(approx(G.fraction_emergee_iceberg(900, 1000), 0.1, tol=1e-9),
      "iceberg ρ=900/1000 -> 0.1 émergé")
# fraction immergée = 1 − émergée (cohérence Archimède)
check(approx((1.0 - f), 917.0 / 1025.0, tol=1e-6), "fraction immergée = ρ_glace/ρ_eau")

# ── 3) ANCRE — loi de Glen ε̇ = A·σⁿ ──
check(approx(G.vitesse_deformation_glace(1e5), 2.4e-9, tol=1e-15),
      "Glen σ=1e5 -> 2.4e-9 s⁻¹")
check(approx(G.vitesse_deformation_glace(2e5), 1.92e-8, tol=1e-14),
      "Glen σ=2e5 -> 1.92e-8 (×8 quand σ ×2, exposant 3)")
check(approx(G.vitesse_deformation_glace(0), 0.0), "Glen σ=0 -> 0")
# σ ×2 -> ε̇ ×8 (n=3)
r1 = G.vitesse_deformation_glace(1e5)
r2 = G.vitesse_deformation_glace(2e5)
check(approx(r2 / r1, 8.0, tol=1e-6), "n=3 : σ doublée -> ε̇ ×8")
# A et n explicites
check(approx(G.vitesse_deformation_glace(1e5, A=2.4e-24, n=3), 2.4e-9, tol=1e-15),
      "Glen A,n explicites")
check(approx(G.vitesse_deformation_glace(10.0, A=1.0, n=2), 100.0, tol=1e-6),
      "Glen A=1,n=2,σ=10 -> 100 (vérif pure σⁿ)")
check(approx(G.vitesse_deformation_glace(5.0, A=2.0, n=1), 10.0, tol=1e-6),
      "Glen A=2,n=1,σ=5 -> 10")

# ── 4) ANCRE — épaisseur d'équilibre h = τ0/(ρ·g·sin α) ──
attendu_h30 = 1e5 / (917.0 * 9.81 * math.sin(math.radians(30.0)))  # 22.232671577...
h30 = G.epaisseur_equilibre(30.0)
check(approx(h30, attendu_h30, tol=1e-3), f"h(30°) = τ0/(ρg sin30°) ≈ 22.2327 m (obtenu {h30})")
check(22.0 < h30 < 22.5, "h(30°) dans ]22.0, 22.5[")
# Contrôle PHYSIQUE indépendant : ρ·g·h·sin α doit redonner τ0 (plasticité parfaite).
tau_recalc = 917.0 * 9.81 * h30 * math.sin(math.radians(30.0))
check(approx(tau_recalc, 1e5, tol=1.0), "ρ·g·h·sin α redonne τ0 = 1e5 Pa (cohérence)")
# pente plus forte -> glacier plus mince
h10 = G.epaisseur_equilibre(10.0)
check(h10 > h30, "pente plus faible (10°) -> glace plus épaisse que 30°")
attendu_h10 = 1e5 / (917.0 * 9.81 * math.sin(math.radians(10.0)))
check(approx(h10, attendu_h10, tol=1e-2), "h(10°) conforme à la formule")
# τ0 doublé -> épaisseur doublée
check(approx(G.epaisseur_equilibre(30.0, tau0=2e5), 2.0 * attendu_h30, tol=1e-2),
      "τ0 ×2 -> h ×2")

# ── 5) SOUNDNESS — abstention (ValueError), faux positif INTERDIT ──
check(_leve_v(G.bilan_massique, -1, 0), "accumulation < 0 -> ValueError")
check(_leve_v(G.bilan_massique, 1, -1), "ablation < 0 -> ValueError")
check(_leve_v(G.bilan_massique, float("inf"), 1), "accumulation non finie -> ValueError")
check(_leve_v(G.bilan_massique, 1, float("nan")), "ablation NaN -> ValueError")
check(_leve_v(G.bilan_massique, "x", 1), "accumulation non numérique -> ValueError")

check(_leve_v(G.vitesse_deformation_glace, -1), "contrainte < 0 -> ValueError")
check(_leve_v(G.vitesse_deformation_glace, 1e5, 0), "A = 0 -> ValueError")
check(_leve_v(G.vitesse_deformation_glace, 1e5, -1), "A < 0 -> ValueError")
check(_leve_v(G.vitesse_deformation_glace, 1e5, 2.4e-24, 0), "n = 0 -> ValueError")
check(_leve_v(G.vitesse_deformation_glace, 1e5, 2.4e-24, -1), "n < 0 -> ValueError")
check(_leve_v(G.vitesse_deformation_glace, float("inf")), "σ non finie -> ValueError")
check(_leve_v(G.vitesse_deformation_glace, 1e300, 1.0, 3), "débordement -> ValueError")

check(_leve_v(G.epaisseur_equilibre, 0), "angle = 0 -> ValueError")
check(_leve_v(G.epaisseur_equilibre, 90), "angle = 90 -> ValueError")
check(_leve_v(G.epaisseur_equilibre, -5), "angle < 0 -> ValueError")
check(_leve_v(G.epaisseur_equilibre, 95), "angle > 90 -> ValueError")
check(_leve_v(G.epaisseur_equilibre, 30, 0), "tau0 = 0 -> ValueError")
check(_leve_v(G.epaisseur_equilibre, 30, 1e5, -1), "rho_glace < 0 -> ValueError")
check(_leve_v(G.epaisseur_equilibre, 30, 1e5, 917, 0), "g = 0 -> ValueError")
check(_leve_v(G.epaisseur_equilibre, float("nan")), "angle NaN -> ValueError")

check(_leve_v(G.fraction_emergee_iceberg, 0, 1025), "rho_glace = 0 -> ValueError")
check(_leve_v(G.fraction_emergee_iceberg, -1, 1025), "rho_glace < 0 -> ValueError")
check(_leve_v(G.fraction_emergee_iceberg, 917, 0), "rho_eau = 0 -> ValueError")
check(_leve_v(G.fraction_emergee_iceberg, 917, -1025), "rho_eau < 0 -> ValueError")
check(_leve_v(G.fraction_emergee_iceberg, 1025, 1025), "rho_glace = rho_eau -> ValueError (ne flotte pas)")
check(_leve_v(G.fraction_emergee_iceberg, 1100, 1025), "rho_glace > rho_eau -> ValueError (coule)")
check(_leve_v(G.fraction_emergee_iceberg, float("inf"), 1025), "rho_glace non fini -> ValueError")

# ── 6) DÉTERMINISME ──
check(G.bilan_massique(2, 1) == G.bilan_massique(2, 1), "bilan_massique déterministe")
check(G.fraction_emergee_iceberg() == G.fraction_emergee_iceberg(), "fraction_emergee déterministe")
check(G.vitesse_deformation_glace(1e5) == G.vitesse_deformation_glace(1e5),
      "vitesse_deformation déterministe")
check(G.epaisseur_equilibre(30.0) == G.epaisseur_equilibre(30.0), "epaisseur_equilibre déterministe")

print(f"\n=== valide_glaciologie : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
