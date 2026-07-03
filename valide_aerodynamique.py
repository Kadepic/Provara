"""
VALIDE aerodynamique.py — held-out ADVERSE.

Ancres = valeurs d'aérodynamique CALCULÉES À LA MAIN (non re-dérivées par le module) :
  • portance/traînée ½·ρ·v²·S·C posées numériquement ;
  • finesse Cz/Cx exacte ; Reynolds ρ·v·L/μ exact ;
  • vol en palier vérifié par ROUND-TRIP (portance à v_eq == poids) — propriété, non circulaire ;
  • loi d'échelle portance ∝ v² (×2 vitesse -> ×4 portance) ;
  • cohérence croisée finesse == portance/traînée à ρ,v,S communs.
+ SOUNDNESS (ρ≤0, S≤0, v<0, Cx≤0, μ≤0, L≤0, Cz≤0, poids≤0, non numérique/booléen/non fini -> ValueError)
+ DÉTERMINISME.
"""
import math
import aerodynamique as A

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def _leve_v(fn, *a, **k) -> bool:
    """True ssi fn(*a, **k) lève ValueError (abstention), False sinon."""
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


TOL = 1e-9          # ancres exactes (produits/quotients propres)
RTOL = 1e-5         # ancres flottantes (arrondi 6 sig. figs)


def proche(got, exp, rel=RTOL):
    return abs(got - exp) <= abs(exp) * rel + 1e-9


# ── 1) ANCRES PORTANCE — L = ½·ρ·v²·S·Cz, posées à la main ──
# 0.5·1.225·100²·10·1.0 = 0.5·1.225·10000·10 = 61250 N
check(abs(A.portance(1.225, 100, 10, 1.0) - 61250.0) < TOL, "portance(1.225,100,10,1) = 61250 N")
# 0.5·1.225·50²·10·1.0 = 0.5·1.225·2500·10 = 15312.5 N
check(abs(A.portance(1.225, 50, 10, 1.0) - 15312.5) < TOL, "portance(1.225,50,10,1) = 15312.5 N")
# 0.5·1.0·1²·1·1 = 0.5 N
check(abs(A.portance(1.0, 1.0, 1.0, 1.0) - 0.5) < TOL, "portance(1,1,1,1) = 0.5 N")
# v = 0 -> portance nulle (formule exacte, pas une abstention)
check(A.portance(1.225, 0.0, 10, 1.0) == 0.0, "portance à v=0 = 0 N")
# Cz négatif = déportance (downforce) ADMISE : 0.5·1.0·10²·2·(-0.5) = -50 N
check(abs(A.portance(1.0, 10, 2.0, -0.5) - (-50.0)) < TOL, "portance Cz<0 (déportance) = -50 N")

# Loi d'échelle : portance ∝ v² (×2 vitesse -> ×4 portance)
check(abs(A.portance(1.225, 100, 10, 1.0) - 4.0 * A.portance(1.225, 50, 10, 1.0)) < TOL,
      "portance ∝ v² : L(2v) = 4·L(v)")

# ── 2) ANCRES TRAÎNÉE — D = ½·ρ·v²·S·Cx ──
# 0.5·1.225·100²·10·0.05 = 61250·0.05 = 3062.5 N
check(abs(A.trainee(1.225, 100, 10, 0.05) - 3062.5) < TOL, "trainee(1.225,100,10,0.05) = 3062.5 N")
# 0.5·1.0·2²·1·0.1 = 0.5·4·0.1 = 0.2 N
check(abs(A.trainee(1.0, 2.0, 1.0, 0.1) - 0.2) < TOL, "trainee(1,2,1,0.1) = 0.2 N")

# ── 3) ANCRES FINESSE — f = Cz/Cx ──
check(abs(A.finesse(1.0, 0.05) - 20.0) < TOL, "finesse(1.0,0.05) = 20")
check(abs(A.finesse(1.2, 0.08) - 15.0) < TOL, "finesse(1.2,0.08) = 15")
check(abs(A.finesse(0.0, 0.05) - 0.0) < TOL, "finesse(0,0.05) = 0")
check(abs(A.finesse(-0.5, 0.1) - (-5.0)) < TOL, "finesse Cz<0 = -5 (signe préservé)")
# Cohérence croisée : finesse Cz/Cx == portance/traînée à ρ,v,S communs
check(abs(A.finesse(1.0, 0.05) - A.portance(1.225, 100, 10, 1.0) / A.trainee(1.225, 100, 10, 0.05)) < TOL,
      "finesse == portance/traînée (ρ,v,S communs)")

# ── 4) ANCRES REYNOLDS — Re = ρ·v·L/μ ──
check(abs(A.reynolds(1.0, 1.0, 1.0, 1.0) - 1.0) < TOL, "reynolds(1,1,1,1) = 1")
# 1.2·10·2/2e-5 = 24/2e-5 = 1.2e6
check(abs(A.reynolds(1.2, 10, 2.0, 2e-5) - 1_200_000.0) < TOL, "reynolds(1.2,10,2,2e-5) = 1.2e6")
# 1.225·20·1.0/1.81e-5 = 24.5/1.81e-5 = 1353591.16 (arrondi 6 sig -> 1353590)
check(proche(A.reynolds(1.225, 20, 1.0, 1.81e-5), 24.5 / 1.81e-5), "reynolds(1.225,20,1,1.81e-5) ≈ 1.35359e6")
check(A.reynolds(1.225, 0.0, 1.0, 1.81e-5) == 0.0, "reynolds à v=0 = 0")

# ── 5) ANCRES VOL EN PALIER — v = √(2·poids/(ρ·S·Cz)) ──
# √(2·61250/(1.225·10·1)) = √(122500/12.25) = √10000 = 100 m/s
check(abs(A.vol_equilibre(1.225, 10, 1.0, 61250.0) - 100.0) < TOL, "vol_equilibre -> 100 m/s")
# √(2·100/(1·2·0.5)) = √(200/1) = √200 = 14.1421...
check(proche(A.vol_equilibre(1.0, 2.0, 0.5, 100.0), math.sqrt(200.0)), "vol_equilibre -> √200")
# ROUND-TRIP (propriété, non circulaire) : à v_eq, portance == poids
for (rho, S, cz, poids) in [(1.225, 10, 1.0, 61250.0), (1.0, 2.0, 0.5, 100.0), (1.225, 16, 1.5, 9806.65)]:
    v_eq = A.vol_equilibre(rho, S, cz, poids)
    check(proche(A.portance(rho, v_eq, S, cz), poids), f"round-trip portance(v_eq)=poids ({poids} N)")

# ── 6) SOUNDNESS — entrée invalide -> ValueError (abstention, JAMAIS un faux) ──
check(_leve_v(A.portance, 0.0, 100, 10, 1.0), "portance rho=0 -> ValueError")
check(_leve_v(A.portance, -1.0, 100, 10, 1.0), "portance rho<0 -> ValueError")
check(_leve_v(A.portance, 1.225, 100, 0.0, 1.0), "portance S=0 -> ValueError")
check(_leve_v(A.portance, 1.225, 100, -2.0, 1.0), "portance S<0 -> ValueError")
check(_leve_v(A.portance, 1.225, -5.0, 10, 1.0), "portance v<0 -> ValueError")
check(_leve_v(A.trainee, 1.225, 100, 10, 0.0), "trainee Cx=0 -> ValueError")
check(_leve_v(A.trainee, 1.225, 100, 10, -0.05), "trainee Cx<0 -> ValueError")
check(_leve_v(A.trainee, -1.0, 100, 10, 0.05), "trainee rho<0 -> ValueError")
check(_leve_v(A.trainee, 1.225, -1.0, 10, 0.05), "trainee v<0 -> ValueError")
check(_leve_v(A.finesse, 1.0, 0.0), "finesse Cx=0 -> ValueError")
check(_leve_v(A.finesse, 1.0, -0.05), "finesse Cx<0 -> ValueError")
check(_leve_v(A.reynolds, 0.0, 20, 1.0, 1.81e-5), "reynolds rho=0 -> ValueError")
check(_leve_v(A.reynolds, 1.225, -1.0, 1.0, 1.81e-5), "reynolds v<0 -> ValueError")
check(_leve_v(A.reynolds, 1.225, 20, 0.0, 1.81e-5), "reynolds L=0 -> ValueError")
check(_leve_v(A.reynolds, 1.225, 20, -1.0, 1.81e-5), "reynolds L<0 -> ValueError")
check(_leve_v(A.reynolds, 1.225, 20, 1.0, 0.0), "reynolds mu=0 -> ValueError")
check(_leve_v(A.reynolds, 1.225, 20, 1.0, -1.81e-5), "reynolds mu<0 -> ValueError")
check(_leve_v(A.vol_equilibre, 0.0, 10, 1.0, 61250.0), "vol_equilibre rho=0 -> ValueError")
check(_leve_v(A.vol_equilibre, 1.225, 0.0, 1.0, 61250.0), "vol_equilibre S=0 -> ValueError")
check(_leve_v(A.vol_equilibre, 1.225, 10, 0.0, 61250.0), "vol_equilibre Cz=0 -> ValueError")
check(_leve_v(A.vol_equilibre, 1.225, 10, -1.0, 61250.0), "vol_equilibre Cz<0 -> ValueError")
check(_leve_v(A.vol_equilibre, 1.225, 10, 1.0, 0.0), "vol_equilibre poids=0 -> ValueError")
check(_leve_v(A.vol_equilibre, 1.225, 10, 1.0, -10.0), "vol_equilibre poids<0 -> ValueError")

# Non numérique / booléen / non fini -> ValueError (jamais une coercition silencieuse)
check(_leve_v(A.portance, True, 100, 10, 1.0), "portance booléen -> ValueError")
check(_leve_v(A.portance, 1.225, 100, 10, False), "portance Cz booléen -> ValueError")
check(_leve_v(A.portance, "1.225", 100, 10, 1.0), "portance str -> ValueError")
check(_leve_v(A.portance, None, 100, 10, 1.0), "portance None -> ValueError")
check(_leve_v(A.portance, float("nan"), 100, 10, 1.0), "portance NaN -> ValueError")
check(_leve_v(A.portance, float("inf"), 100, 10, 1.0), "portance inf -> ValueError")
check(_leve_v(A.finesse, float("inf"), 0.05), "finesse Cz inf -> ValueError")
check(_leve_v(A.reynolds, 1.225, 20, 1.0, "1.81e-5"), "reynolds mu str -> ValueError")

# ── 7) DÉTERMINISME — fonctions pures, mêmes entrées -> mêmes sorties ──
check(A.portance(1.225, 100, 10, 1.0) == A.portance(1.225, 100, 10, 1.0), "portance déterministe")
check(A.finesse(1.2, 0.08) == A.finesse(1.2, 0.08), "finesse déterministe")
check([A.reynolds(1.2, 10, 2.0, 2e-5) for _ in range(5)] == [1_200_000.0] * 5, "reynolds 5 appels identiques")
check(A.vol_equilibre(1.225, 10, 1.0, 61250.0) == A.vol_equilibre(1.225, 10, 1.0, 61250.0),
      "vol_equilibre déterministe")

print(f"\n=== valide_aerodynamique : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
