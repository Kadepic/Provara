"""
VALIDE psychometrie.py — held-out ADVERSE.

Ancres CONNUES (définitions de manuel + arithmétique / table normale vérifiées À LA MAIN, NON circulaires) :
  • qi_standardise        : score = moyenne -> QI 100 ; +1σ -> 115 ; +2σ -> 130 ; −1σ -> 85 ; −2σ -> 70 ;
                            étalonnage arbitraire (moyenne 50, σ 10) : 60 -> 115, 70 -> 130, 45 -> 92.5.
  • rang_percentile_qi    : table de la loi normale standard (Φ), valeurs externes connues :
                            QI 100 -> 50.0 ; 115 -> 84.1345 (Φ(1)) ; 130 -> 97.7250 (Φ(2)) ;
                            85 -> 15.8655 (Φ(−1)) ; 145 -> 99.8650 (Φ(3)) ; 107.5 -> 69.1462 (Φ(0.5)).
  • alpha_cronbach        : k=10, v̄=1.1, σ²ₜ=50 -> (10/9)(1−11/50) = 0.866667 ;
                            k=5, v̄=2, σ²ₜ=20 -> (5/4)(1−10/20) = 0.625 ;
                            k=4, v̄=1, σ²ₜ=16 -> (4/3)(1−4/16) = 1.0 (items parfaitement corrélés) ;
                            k=20, v̄=0.75, σ²ₜ=60 -> (20/19)(0.75) = 0.789474 ;
                            k=3, v̄=4, σ²ₜ=9 -> (3/2)(1−12/9) = −0.5 (échelle incohérente, réel).
  • erreur_standard_mesure: SD 15, fiab 0.75 -> 7.5 ; 0.91 -> 4.5 ; 0.84 -> 6.0 ; 0.96 -> 3.0 ;
                            SD 10, fiab 0.75 -> 5.0 ; fiab 1 -> 0.0 ; fiab 0 -> SD.
SOUNDNESS : σ<=0, k<2, k non entier, variance_totale<=0, variance_moyenne_item<0, fiabilite hors [0,1],
            ecart_type_test<0, valeur non finie / non numérique / booléenne -> ValueError (jamais un faux).
DÉTERMINISME : mêmes entrées -> mêmes sorties.
Aucune de ces ancres ni aucun de ces cas n'est codé en dur dans psychometrie.py.
"""

import psychometrie as M

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def approx(a, b, tol=1e-6):
    return abs(a - b) <= tol


def _leve_v(fn, *a, **k):
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# ── 1) qi_standardise — score = moyenne -> 100 ; +kσ -> 100 + 15k ──
check(approx(M.qi_standardise(50, 50, 10), 100.0), "score = moyenne -> QI 100")
check(approx(M.qi_standardise(60, 50, 10), 115.0), "score = moyenne + 1σ -> QI 115")
check(approx(M.qi_standardise(70, 50, 10), 130.0), "score = moyenne + 2σ -> QI 130")
check(approx(M.qi_standardise(40, 50, 10), 85.0), "score = moyenne − 1σ -> QI 85")
check(approx(M.qi_standardise(30, 50, 10), 70.0), "score = moyenne − 2σ -> QI 70")
check(approx(M.qi_standardise(45, 50, 10), 92.5), "score 45 (−0.5σ) -> QI 92.5")
# étalonnage différent (moyenne 100, σ 16 type Cattell) : 116 -> 115 sur l'échelle Wechsler
check(approx(M.qi_standardise(116, 100, 16), 115.0), "étalonnage σ=16 : 116 -> 115")
# QI peut descendre sous 0 si le score est très bas (résultat réel, non tronqué)
check(approx(M.qi_standardise(0, 100, 10), 100.0 + 15.0 * (0 - 100) / 10), "score très bas -> QI < 0 réel")

# ── 2) rang_percentile_qi — table de la loi normale standard (ancres externes Φ) ──
check(M.rang_percentile_qi(100) == 50.0, "QI 100 -> 50e percentile (Φ(0)=0.5)")
check(approx(M.rang_percentile_qi(115), 84.134475, 1e-4), "QI 115 -> ≈84.13 (Φ(1))")
check(approx(M.rang_percentile_qi(130), 97.724987, 1e-4), "QI 130 -> ≈97.72 (Φ(2))")
check(approx(M.rang_percentile_qi(85), 15.865525, 1e-4), "QI 85 -> ≈15.87 (Φ(−1))")
check(approx(M.rang_percentile_qi(145), 99.865010, 1e-4), "QI 145 -> ≈99.87 (Φ(3))")
check(approx(M.rang_percentile_qi(107.5), 69.146246, 1e-4), "QI 107.5 -> ≈69.15 (Φ(0.5))")
check(approx(M.rang_percentile_qi(70), 2.275013, 1e-4), "QI 70 -> ≈2.28 (Φ(−2))")
# monotonie stricte + bornes (0,100)
check(M.rang_percentile_qi(130) > M.rang_percentile_qi(115) > M.rang_percentile_qi(100)
      > M.rang_percentile_qi(85), "rang percentile strictement croissant avec le QI")
check(0.0 < M.rang_percentile_qi(55) and M.rang_percentile_qi(160) < 100.0, "rang percentile dans (0,100)")

# ── 3) alpha_cronbach — Σσ²ᵢ = k·v̄, formule exacte ──
check(approx(M.alpha_cronbach(10, 1.1, 50), 0.866667, 1e-6), "k=10, v̄=1.1, σ²ₜ=50 -> 0.866667")
check(approx(M.alpha_cronbach(5, 2, 20), 0.625), "k=5, v̄=2, σ²ₜ=20 -> 0.625")
check(approx(M.alpha_cronbach(4, 1, 16), 1.0), "k=4, v̄=1, σ²ₜ=16 -> α max = 1 (items parfaits)")
check(approx(M.alpha_cronbach(3, 2, 18), 1.0), "k=3, v̄=2, σ²ₜ=18 -> α = 1")
check(approx(M.alpha_cronbach(20, 0.75, 60), 0.789474, 1e-6), "k=20, v̄=0.75, σ²ₜ=60 -> 0.789474")
check(approx(M.alpha_cronbach(3, 4, 9), -0.5), "k=3, v̄=4, σ²ₜ=9 -> α = −0.5 (incohérent, réel non tronqué)")
check(approx(M.alpha_cronbach(10.0, 1.1, 50), 0.866667, 1e-6), "k entier en float (10.0) accepté")

# ── 4) erreur_standard_mesure — SEM = SD·√(1−fiab) ──
check(approx(M.erreur_standard_mesure(15, 0.75), 7.5), "SD 15, fiab 0.75 -> 7.5")
check(approx(M.erreur_standard_mesure(15, 0.91), 4.5), "SD 15, fiab 0.91 -> 4.5")
check(approx(M.erreur_standard_mesure(15, 0.84), 6.0), "SD 15, fiab 0.84 -> 6.0")
check(approx(M.erreur_standard_mesure(15, 0.96), 3.0), "SD 15, fiab 0.96 -> 3.0")
check(approx(M.erreur_standard_mesure(10, 0.75), 5.0), "SD 10, fiab 0.75 -> 5.0")
check(approx(M.erreur_standard_mesure(15, 1.0), 0.0), "fiab 1 -> SEM 0 (fiabilité parfaite)")
check(approx(M.erreur_standard_mesure(15, 0.0), 15.0), "fiab 0 -> SEM = SD")

# ── 5) SOUNDNESS qi_standardise — écart-type / valeurs invalides ──
check(_leve_v(M.qi_standardise, 60, 50, 0), "ecart_type = 0 -> ValueError")
check(_leve_v(M.qi_standardise, 60, 50, -10), "ecart_type < 0 -> ValueError")
check(_leve_v(M.qi_standardise, float("nan"), 50, 10), "score_brut NaN -> ValueError")
check(_leve_v(M.qi_standardise, 60, float("inf"), 10), "moyenne inf -> ValueError")
check(_leve_v(M.qi_standardise, 60, 50, "dix"), "ecart_type non numérique -> ValueError")
check(_leve_v(M.qi_standardise, True, 50, 10), "score_brut booléen -> ValueError")

# ── 6) SOUNDNESS rang_percentile_qi — valeurs invalides ──
check(_leve_v(M.rang_percentile_qi, float("nan")), "qi NaN -> ValueError")
check(_leve_v(M.rang_percentile_qi, float("inf")), "qi inf -> ValueError")
check(_leve_v(M.rang_percentile_qi, "cent"), "qi non numérique -> ValueError")
check(_leve_v(M.rang_percentile_qi, True), "qi booléen -> ValueError")

# ── 7) SOUNDNESS alpha_cronbach — k / variances invalides ──
check(_leve_v(M.alpha_cronbach, 1, 1.0, 10), "k = 1 (< 2) -> ValueError")
check(_leve_v(M.alpha_cronbach, 0, 1.0, 10), "k = 0 -> ValueError")
check(_leve_v(M.alpha_cronbach, -3, 1.0, 10), "k < 0 -> ValueError")
check(_leve_v(M.alpha_cronbach, 2.5, 1.0, 10), "k non entier (2.5) -> ValueError")
check(_leve_v(M.alpha_cronbach, 10, 1.0, 0), "variance_totale = 0 -> ValueError")
check(_leve_v(M.alpha_cronbach, 10, 1.0, -5), "variance_totale < 0 -> ValueError")
check(_leve_v(M.alpha_cronbach, 10, -1.0, 50), "variance_moyenne_item < 0 (impossible) -> ValueError")
check(_leve_v(M.alpha_cronbach, 10, float("nan"), 50), "variance_moyenne_item NaN -> ValueError")
check(_leve_v(M.alpha_cronbach, True, 1.0, 10), "k booléen -> ValueError")

# ── 8) SOUNDNESS erreur_standard_mesure — domaine fiabilité / SD ──
check(_leve_v(M.erreur_standard_mesure, 15, 1.5), "fiabilite > 1 -> ValueError (√ négatif)")
check(_leve_v(M.erreur_standard_mesure, 15, -0.1), "fiabilite < 0 -> ValueError")
check(_leve_v(M.erreur_standard_mesure, -5, 0.5), "ecart_type_test < 0 -> ValueError")
check(_leve_v(M.erreur_standard_mesure, 15, float("nan")), "fiabilite NaN -> ValueError")
check(_leve_v(M.erreur_standard_mesure, float("inf"), 0.5), "ecart_type_test inf -> ValueError")
check(_leve_v(M.erreur_standard_mesure, 15, "haute"), "fiabilite non numérique -> ValueError")
check(_leve_v(M.erreur_standard_mesure, 15, True), "fiabilite booléenne -> ValueError")

# ── 9) DÉTERMINISME — mêmes entrées -> mêmes sorties ──
check(M.qi_standardise(60, 50, 10) == M.qi_standardise(60, 50, 10), "qi_standardise déterministe")
check(M.rang_percentile_qi(115) == M.rang_percentile_qi(115), "rang_percentile_qi déterministe")
check(M.alpha_cronbach(10, 1.1, 50) == M.alpha_cronbach(10, 1.1, 50), "alpha_cronbach déterministe")
check(M.erreur_standard_mesure(15, 0.75) == M.erreur_standard_mesure(15, 0.75), "SEM déterministe")

print(f"\n=== valide_psychometrie : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
