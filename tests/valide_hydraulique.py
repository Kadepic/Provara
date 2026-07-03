"""VALIDE hydraulique.py — ADVERSE, FAUX=0. Débit (Q=vA), continuité (v₁A₁=v₂A₂ vérifié), nombre de Reynolds,
régimes laminaire/turbulent + SOUNDNESS (section/viscosité ≤ 0 -> ValueError)."""
import hydraulique as H

ok = 0
ko = 0


def check(c, l):
    global ok, ko
    if c:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {l}")


def proche(a, b, rel=1e-4):
    return abs(a - b) <= rel * abs(b) + 1e-9


def leve(fn, *a):
    try:
        fn(*a)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# DÉBIT
check(H.debit_volumique(2, 0.5) == 1.0, "Q = v·A = 1 m³/s")
check(H.debit_volumique(0, 5) == 0.0, "v=0 -> Q=0")

# CONTINUITÉ (+ conservation indépendante v₁A₁ = v₂A₂)
check(H.vitesse_continuite(2, 1, 0.5) == 4.0, "section ÷2 -> vitesse ×2")
check(proche(2 * 1, H.vitesse_continuite(2, 1, 0.5) * 0.5), "v₁A₁ = v₂A₂ (conservation)")
check(H.vitesse_continuite(3, 2, 6) == 1.0, "section ×3 -> vitesse ÷3")
# le débit se conserve le long de la conduite
check(proche(H.debit_volumique(2, 1), H.debit_volumique(H.vitesse_continuite(2, 1, 0.5), 0.5)), "débit conservé")

# REYNOLDS / RÉGIME
check(H.nombre_reynolds(1000, 1, 0.1, 0.001) == 100000.0, "Re eau = 100000")
check(proche(H.nombre_reynolds(1000, 0.01, 0.01, 0.001), 100), "Re faible = 100")
check(H.regime_ecoulement(500) == "laminaire", "Re<2000 -> laminaire")
check(H.regime_ecoulement(3000) == "transitoire", "2000<Re<4000 -> transitoire")
check(H.regime_ecoulement(100000) == "turbulent", "Re>4000 -> turbulent")
check(H.regime_ecoulement(1999) == "laminaire" and H.regime_ecoulement(2000) == "transitoire"
      and H.regime_ecoulement(4000) == "transitoire" and H.regime_ecoulement(4001) == "turbulent", "bornes de régime")

# BERNOULLI
check(proche(H.charge_bernoulli(0, 0, 5), 5.0), "charge statique = hauteur")
check(H.charge_bernoulli(0, 9806.65, 0) > 0.99 and H.charge_bernoulli(0, 9806.65, 0) < 1.01, "charge de pression ≈ 1 m")

# SOUNDNESS
check(leve(H.debit_volumique, 2, 0), "A=0 -> ValueError")
check(leve(H.vitesse_continuite, 2, 1, 0), "A2=0 -> ValueError")
check(leve(H.nombre_reynolds, 1000, 1, 0.1, 0), "μ=0 -> ValueError")
check(leve(H.debit_volumique, -1, 5), "vitesse<0 -> ValueError")
check(leve(H.regime_ecoulement, "x"), "non-numérique -> ValueError")

# DÉTERMINISME
check(H.nombre_reynolds(1000, 1, 0.1, 0.001) == H.nombre_reynolds(1000, 1, 0.1, 0.001), "déterminisme")

print(f"\n=== valide_hydraulique : {ok}/{ok + ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
