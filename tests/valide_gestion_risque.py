"""
VALIDE gestion_risque.py — held-out ADVERSE.

Ancres CONNUES (définitions standard + arithmétique vérifiée à la main, NON circulaires) :
  • esperance_perte : 0.01·100000 = 1000 ; 0.5·200 = 100 ; 0·100000 = 0 ; 1·750 = 750 (bornes) ;
                      0.25·4000 = 1000.
  • value_at_risk_parametrique :
        normale standard 95 %  : moy 0, σ 1, z 1.645  -> 1.645  (= z, quantile connu) ;
        normale standard 99 %  : moy 0, σ 1, z 2.326  -> 2.326 ;
        moy 0.1, σ 0.2, z 1.645 -> -(0.1 - 0.329) = 0.229 ;
        moy 1000, σ 500, z 1.645 -> -(1000 - 822.5) = -177.5  (VaR négative = pas de perte au seuil).
  • ratio_sharpe : (0.10-0.02)/0.15 = 0.533333 ; (0.10-0.10)/0.20 = 0.0 ; (0.05-0.08)/0.10 = -0.3 (négatif).
  • variance / écart-type portefeuille 2 actifs (diversification, poids 0.5/0.5, σ 0.2/0.2) :
        ρ = +1 -> Var 0.04, σ 0.2          (corrélation parfaite : aucune diversification) ;
        ρ =  0 -> Var 0.02, σ 0.141421     (indépendants : risque réduit sous 0.2) ;
        ρ = -1 -> Var 0.0,  σ 0.0          (couverture parfaite : risque annulé) ;
        cas asymétrique 0.6/0.4, σ 0.3/0.1, ρ 0.5 -> Var 0.0412 (calculé à la main).
  • prime_pure : 0.05·2000 = 100 ; 2·500 = 1000 ; 0·1000 = 0 ; 1.5·400 = 600.
SOUNDNESS : probabilité hors [0,1], σ<=0 (VaR/Sharpe), σ<0 (portefeuille), ρ hors [-1,1],
            z<=0, montant/fréquence/coût < 0, valeur non finie / non numérique / bool -> ValueError.
DÉTERMINISME : mêmes entrées -> mêmes sorties.
"""

import gestion_risque as M

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


# ── 1) ANCRE — espérance de perte (E[perte] = 0.01·100000 = 1000) ──
ep = M.esperance_perte(0.01, 100000)
check(approx(ep, 1000.0), f"E[perte] = 0.01·100000 = 1000 (obtenu {ep})")
check(approx(M.esperance_perte(0.5, 200), 100.0), "0.5·200 = 100")
check(approx(M.esperance_perte(0.0, 100000), 0.0), "proba 0 -> perte attendue 0 (borne)")
check(approx(M.esperance_perte(1.0, 750), 750.0), "proba 1 -> perte = montant (borne)")
check(approx(M.esperance_perte(0.25, 4000), 1000.0), "0.25·4000 = 1000")

# ── 2) ANCRE — VaR paramétrique (quantiles normaux connus, non recalculés) ──
v95 = M.value_at_risk_parametrique(0.0, 1.0, 1.645)
check(approx(v95, 1.645), f"VaR normale standard 95 % = z = 1.645 (obtenu {v95})")
check(approx(M.value_at_risk_parametrique(0.0, 1.0, 2.326), 2.326), "VaR normale standard 99 % = 2.326")
check(approx(M.value_at_risk_parametrique(0.0, 1.0), 1.645), "z par défaut = 1.645 (95 %)")
check(approx(M.value_at_risk_parametrique(0.1, 0.2, 1.645), 0.229), "-(0.1 - 1.645·0.2) = 0.229")
check(approx(M.value_at_risk_parametrique(1000, 500, 1.645), -177.5), "VaR négative (gain au seuil) = -177.5")

# ── 3) ANCRE — ratio de Sharpe ((0.10-0.02)/0.15 ≈ 0.533) ──
sh = M.ratio_sharpe(0.10, 0.02, 0.15)
check(approx(sh, 0.533333), f"Sharpe (0.10-0.02)/0.15 = 0.533333 (obtenu {sh})")
check(approx(M.ratio_sharpe(0.10, 0.10, 0.20), 0.0), "Sharpe excès nul = 0.0")
check(approx(M.ratio_sharpe(0.05, 0.08, 0.10), -0.3), "Sharpe sous le sans-risque = -0.3 (négatif)")

# ── 4) ANCRE — diversification : variance & écart-type d'un portefeuille 2 actifs ──
check(approx(M.variance_portefeuille_2_actifs(0.5, 0.5, 0.2, 0.2, 1.0), 0.04),
      "ρ=+1 : Var = 0.04 (aucune diversification)")
check(approx(M.ecart_type_portefeuille_2_actifs(0.5, 0.5, 0.2, 0.2, 1.0), 0.2),
      "ρ=+1 : σ_p = 0.2 (= risque d'un actif)")
check(approx(M.variance_portefeuille_2_actifs(0.5, 0.5, 0.2, 0.2, 0.0), 0.02),
      "ρ=0 : Var = 0.02 (risque réduit)")
check(approx(M.ecart_type_portefeuille_2_actifs(0.5, 0.5, 0.2, 0.2, 0.0), 0.141421),
      "ρ=0 : σ_p = sqrt(0.02) = 0.141421 (< 0.2 : diversification)")
check(approx(M.variance_portefeuille_2_actifs(0.5, 0.5, 0.2, 0.2, -1.0), 0.0),
      "ρ=-1 : Var = 0.0 (couverture parfaite)")
check(approx(M.ecart_type_portefeuille_2_actifs(0.5, 0.5, 0.2, 0.2, -1.0), 0.0),
      "ρ=-1 : σ_p = 0.0 (risque annulé)")
check(approx(M.variance_portefeuille_2_actifs(0.6, 0.4, 0.3, 0.1, 0.5), 0.0412),
      "cas asymétrique : Var = 0.0412 (calcul manuel)")
# diversification stricte : σ_p < moyenne pondérée des σ quand ρ < 1
check(M.ecart_type_portefeuille_2_actifs(0.5, 0.5, 0.2, 0.2, 0.0) < 0.2,
      "diversification : σ_p (ρ=0) strictement < 0.2")

# ── 5) ANCRE — prime pure (assurance : fréquence × sévérité) ──
pp = M.prime_pure(0.05, 2000)
check(approx(pp, 100.0), f"prime pure 0.05·2000 = 100 (obtenu {pp})")
check(approx(M.prime_pure(2, 500), 1000.0), "2 sinistres · 500 = 1000 (fréquence > 1 admise)")
check(approx(M.prime_pure(0.0, 1000), 0.0), "fréquence nulle -> prime 0")
check(approx(M.prime_pure(1.5, 400), 600.0), "1.5·400 = 600")

# ── 6) SOUNDNESS — probabilité hors [0, 1] (abstention) ──
check(_leve_v(M.esperance_perte, 1.5, 100000), "probabilité > 1 -> ValueError")
check(_leve_v(M.esperance_perte, -0.1, 100000), "probabilité < 0 -> ValueError")

# ── 7) SOUNDNESS — écart-type (risque) <= 0 où il est dénominateur strict ──
check(_leve_v(M.ratio_sharpe, 0.10, 0.02, 0.0), "Sharpe σ = 0 -> ValueError")
check(_leve_v(M.ratio_sharpe, 0.10, 0.02, -0.15), "Sharpe σ < 0 -> ValueError")
check(_leve_v(M.value_at_risk_parametrique, 0.1, 0.0), "VaR σ = 0 -> ValueError")
check(_leve_v(M.value_at_risk_parametrique, 0.1, -1.0), "VaR σ < 0 -> ValueError")

# ── 8) SOUNDNESS — z <= 0 pour la VaR (seuil de confiance impossible) ──
check(_leve_v(M.value_at_risk_parametrique, 0.0, 1.0, 0.0), "VaR z = 0 -> ValueError")
check(_leve_v(M.value_at_risk_parametrique, 0.0, 1.0, -1.645), "VaR z < 0 -> ValueError")

# ── 9) SOUNDNESS — portefeuille : σ < 0 et ρ hors [-1, 1] (abstention) ──
check(_leve_v(M.variance_portefeuille_2_actifs, 0.5, 0.5, -0.2, 0.2, 0.0), "portefeuille σ1 < 0 -> ValueError")
check(_leve_v(M.variance_portefeuille_2_actifs, 0.5, 0.5, 0.2, -0.2, 0.0), "portefeuille σ2 < 0 -> ValueError")
check(_leve_v(M.variance_portefeuille_2_actifs, 0.5, 0.5, 0.2, 0.2, 1.5), "ρ > 1 -> ValueError")
check(_leve_v(M.variance_portefeuille_2_actifs, 0.5, 0.5, 0.2, 0.2, -1.5), "ρ < -1 -> ValueError")
check(_leve_v(M.ecart_type_portefeuille_2_actifs, 0.5, 0.5, 0.2, 0.2, 2.0), "σ_p : ρ > 1 -> ValueError")
# σ = 0 (actif sans risque) est LÉGITIME pour le portefeuille (pas une abstention)
check(approx(M.variance_portefeuille_2_actifs(1.0, 0.0, 0.0, 0.2, 0.0), 0.0),
      "portefeuille 100 % actif sans risque (σ=0) -> Var 0 (valide, pas d'abstention)")

# ── 10) SOUNDNESS — montant / fréquence / coût négatifs (abstention) ──
check(_leve_v(M.esperance_perte, 0.5, -100), "montant < 0 -> ValueError")
check(_leve_v(M.prime_pure, -1, 500), "fréquence < 0 -> ValueError")
check(_leve_v(M.prime_pure, 2, -500), "coût moyen < 0 -> ValueError")

# ── 11) SOUNDNESS — valeurs non finies / non numériques / bool (abstention) ──
check(_leve_v(M.esperance_perte, float("nan"), 100000), "proba NaN -> ValueError")
check(_leve_v(M.esperance_perte, 0.01, float("inf")), "montant inf -> ValueError")
check(_leve_v(M.value_at_risk_parametrique, float("inf"), 1.0), "moyenne inf -> ValueError")
check(_leve_v(M.ratio_sharpe, "dix", 0.02, 0.15), "rendement non numérique -> ValueError")
check(_leve_v(M.value_at_risk_parametrique, 0.1, None), "ecart_type None -> ValueError")
check(_leve_v(M.esperance_perte, True, 100000), "proba booléenne -> ValueError")
check(_leve_v(M.prime_pure, 2, False), "coût booléen -> ValueError")
check(_leve_v(M.variance_portefeuille_2_actifs, 0.5, 0.5, 0.2, 0.2, float("nan")), "ρ NaN -> ValueError")

# ── 12) DÉTERMINISME ──
check(M.esperance_perte(0.01, 100000) == M.esperance_perte(0.01, 100000), "esperance_perte déterministe")
check(M.value_at_risk_parametrique(0.1, 0.2, 1.645) == M.value_at_risk_parametrique(0.1, 0.2, 1.645),
      "VaR déterministe")
check(M.ratio_sharpe(0.10, 0.02, 0.15) == M.ratio_sharpe(0.10, 0.02, 0.15), "ratio_sharpe déterministe")
check(M.variance_portefeuille_2_actifs(0.6, 0.4, 0.3, 0.1, 0.5)
      == M.variance_portefeuille_2_actifs(0.6, 0.4, 0.3, 0.1, 0.5), "variance portefeuille déterministe")
check(M.prime_pure(0.05, 2000) == M.prime_pure(0.05, 2000), "prime_pure déterministe")

print(f"\n=== valide_gestion_risque : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
