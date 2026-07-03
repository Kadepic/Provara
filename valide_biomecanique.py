"""
VALIDE biomecanique.py — held-out ADVERSE.

Exactitude ANCRÉE sur des propriétés PHYSIQUES CONNUES, non sur la même expression :
  • portée v0=20 m/s à 45° = 40.77 m (cas de référence) ;
  • angle optimal = 45° ;
  • SYMÉTRIE des angles complémentaires : R(θ) = R(90°−θ) (identité balistique) ;
  • IDENTITÉ « à 45°, H = R/4 » (relation dérivée, deux fonctions distinctes) ;
  • tir VERTICAL (90°) : portée nulle, H = v0²/(2g) (formule du jet vertical) ;
  • impulse–momentum : J = F·t ; couple = F·d.
+ SOUNDNESS : v0<0, angle∉[0,90], g≤0, bras<0, durée≤0, non-fini -> ValueError (aucun dans le module).
"""
import biomecanique as B

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


def approx(x, attendu, rel=1e-3):
    return x is not None and abs(x - attendu) <= rel * abs(attendu) + 1e-9


TOL = 1e-9

# ── 1) CAS DE RÉFÉRENCE (énoncé) ──────────────────────────────────────────────────────────────────────────────
check(approx(B.portee_projectile(20, 45), 40.77, rel=2e-4), "portée v0=20 @45° = 40.77 m")
check(approx(B.hauteur_max(20, 45), 10.1937, rel=1e-4), "hauteur max v0=20 @45° = 10.1937 m")
check(B.angle_optimal_portee() == 45.0, "angle optimal portée = 45°")

# ── 2) ANCRES NON CIRCULAIRES (propriétés physiques connues) ──────────────────────────────────────────────────
# Symétrie des angles complémentaires : R(30°) == R(60°).
check(approx(B.portee_projectile(20, 30), B.portee_projectile(20, 60), rel=1e-9),
      "symétrie complémentaire R(30°)=R(60°)")
# 45° est bien le MAXIMUM de portée (≥ tout autre angle), confirmé sur un balayage.
pmax = B.portee_projectile(25, 45)
check(all(B.portee_projectile(25, a) <= pmax + 1e-9 for a in range(0, 91)),
      "R(45°) est le maximum sur 0..90°")
# Identité « à 45° : H = R/4 » (deux fonctions distinctes).
check(approx(B.hauteur_max(20, 45), B.portee_projectile(20, 45) / 4.0, rel=1e-4),
      "à 45° : H = R/4")
# Tir vertical (90°) : portée nulle, H = v0²/(2g) (jet vertical classique).
check(approx(B.portee_projectile(20, 90), 0.0, rel=0) or abs(B.portee_projectile(20, 90)) < 1e-6,
      "tir vertical 90° -> portée nulle")
check(approx(B.hauteur_max(20, 90), 20.0 * 20.0 / (2 * 9.81), rel=1e-4),
      "tir vertical 90° -> H = v0²/2g = 20.3874 m")
# Tir horizontal (0°) : portée nulle (sin 0 = 0) et hauteur nulle.
check(abs(B.portee_projectile(20, 0)) < 1e-9 and abs(B.hauteur_max(20, 0)) < 1e-9,
      "tir horizontal 0° -> portée et hauteur nulles")
# Temps de vol vertical : t = 2v0/g.
check(approx(B.temps_de_vol(20, 90), 2 * 20 / 9.81, rel=1e-6), "temps de vol vertical = 2v0/g")
# Mise à l'échelle quadratique en v0 : R(2v0)=4·R(v0).
check(approx(B.portee_projectile(40, 37), 4.0 * B.portee_projectile(20, 37), rel=1e-4),
      "R quadratique en v0 : R(2v0)=4R(v0)")

# ── 3) LEVIER / IMPULSION (anchors exacts) ────────────────────────────────────────────────────────────────────
check(abs(B.moment_force(10, 0.5) - 5.0) < TOL, "moment = 10·0.5 = 5 N·m")
check(abs(B.moment_force(100, 2) - 200.0) < TOL, "moment = 100·2 = 200 N·m")
check(abs(B.couple(10, 0.5) - 5.0) < TOL, "couple alias = moment_force")
check(abs(B.moment_force(50, 0) - 0.0) < TOL, "bras nul -> moment nul (valide)")
check(abs(B.impulsion(50, 2) - 100.0) < TOL, "impulsion = 50·2 = 100 N·s")
check(abs(B.impulsion(20, 3) - 60.0) < TOL, "impulsion = 20·3 = 60 N·s")

# ── 4) DÉTERMINISME ───────────────────────────────────────────────────────────────────────────────────────────
check(B.portee_projectile(33.3, 41.2) == B.portee_projectile(33.3, 41.2), "portée déterministe")
check(B.hauteur_max(33.3, 41.2) == B.hauteur_max(33.3, 41.2), "hauteur déterministe")
check(B.moment_force(7.1, 0.31) == B.moment_force(7.1, 0.31), "moment déterministe")
check(B.impulsion(7.1, 0.31) == B.impulsion(7.1, 0.31), "impulsion déterministe")

# ── 5) SOUNDNESS — abstention (ValueError), jamais un faux ────────────────────────────────────────────────────
check(_leve_v(B.portee_projectile, -1, 45), "portée v0<0 -> ValueError")
check(_leve_v(B.portee_projectile, 20, -5), "portée angle<0 -> ValueError")
check(_leve_v(B.portee_projectile, 20, 95), "portée angle>90 -> ValueError")
check(_leve_v(B.portee_projectile, 20, 45, 0), "portée g=0 -> ValueError")
check(_leve_v(B.portee_projectile, 20, 45, -9.81), "portée g<0 -> ValueError")
check(_leve_v(B.hauteur_max, -1, 45), "hauteur v0<0 -> ValueError")
check(_leve_v(B.hauteur_max, 20, 91), "hauteur angle>90 -> ValueError")
check(_leve_v(B.hauteur_max, 20, 45, 0), "hauteur g=0 -> ValueError")
check(_leve_v(B.temps_de_vol, 20, -1), "temps angle<0 -> ValueError")
check(_leve_v(B.temps_de_vol, 20, 45, 0), "temps g=0 -> ValueError")
check(_leve_v(B.moment_force, -1, 0.5), "moment force<0 -> ValueError")
check(_leve_v(B.moment_force, 10, -0.5), "moment bras<0 -> ValueError")
check(_leve_v(B.couple, -1, 0.5), "couple force<0 -> ValueError")
check(_leve_v(B.impulsion, 50, 0), "impulsion durée=0 -> ValueError")
check(_leve_v(B.impulsion, 50, -2), "impulsion durée<0 -> ValueError")
check(_leve_v(B.impulsion, -5, 2), "impulsion force<0 -> ValueError")
# Non-fini / bool / non-numérique.
check(_leve_v(B.portee_projectile, float("nan"), 45), "portée v0=NaN -> ValueError")
check(_leve_v(B.portee_projectile, float("inf"), 45), "portée v0=inf -> ValueError")
check(_leve_v(B.portee_projectile, 20, 45, float("nan")), "portée g=NaN -> ValueError")
check(_leve_v(B.moment_force, True, 0.5), "moment force=bool -> ValueError")
check(_leve_v(B.impulsion, "5", 2), "impulsion force=str -> ValueError")
check(_leve_v(B.hauteur_max, 20, None), "hauteur angle=None -> ValueError")

print(f"\n=== valide_biomecanique : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
