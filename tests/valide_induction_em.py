"""
VALIDE induction_em.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (valeurs posées À LA MAIN, jamais recalculées par la fonction testée) :
  • Φ = B·A·cosθ : B=0.5 T, A=0.2 m², θ=0 -> Φ = 0.5·0.2·1 = 0.1 Wb (multiplication à la main).
    θ=π/2 -> cosθ=0 -> Φ = 0 (champ DANS le plan de la surface : rien ne la traverse — fait géométrique).
    θ=π   -> cosθ=−1 -> Φ = −0.1 Wb. θ=π/3 -> cos=1/2 -> B=1,A=2 -> Φ = 1 Wb.
  • Faraday : bobine N=100 spires, ΔΦ=0.01 Wb, Δt=0.1 s -> |ε| = 100·0.01/0.1 = 10 V (à la main),
    et ε = −10 V (signe de Lenz : flux croissant -> fem négative).
  • Fem de déplacement : barre L=0.5 m, v=2 m/s, B=0.4 T -> ε = 0.4·0.5·2 = 0.4 V (à la main).
  • LENZ (énoncé classique, 1834) : le courant induit s'oppose à la cause qui lui donne naissance ;
    flux croissant -> le courant induit crée un flux OPPOSÉ à l'augmentation.
  • SECOND CHEMIN (croisement de deux fonctions distinctes) : une barre sur rails balaie ΔA = L·v·Δt,
    donc ΔΦ = B·L·v·Δt et |ε| = ΔΦ/Δt ; fem_faraday(1, ΔΦ, Δt) doit redonner fem_deplacement(B, L, v)
    au signe près — deux chemins de code indépendants qui doivent coïncider.

SOUNDNESS : Δt≤0, N<1 / non entier / bool, θ hors [0,π], A≤0, B<0, L≤0, v<0, str/NaN/inf -> ValueError.
"""
import math

import induction_em as I

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
    """True ssi fn(*a) lève ValueError (abstention structurelle)."""
    try:
        fn(*a)
        return False
    except ValueError:
        return True


def proche(x, attendu, tol=1e-9):
    return x is not None and abs(x - attendu) <= tol


PI = math.pi

# ── 1) ANCRES FLUX Φ = B·A·cosθ (calculs à la main) ──
check(proche(I.flux_magnetique(0.5, 0.2, 0.0), 0.1), "Φ(B=0.5,A=0.2,θ=0) = 0.1 Wb (0.5·0.2·1 à la main)")
check(proche(I.flux_magnetique(0.5, 0.2, PI / 2), 0.0, tol=1e-15),
      "Φ(θ=π/2) = 0 (champ dans le plan, cos machine ≈ 6e-17 toléré)")
check(proche(I.flux_magnetique(0.5, 0.2, PI), -0.1), "Φ(θ=π) = −0.1 Wb (normale opposée au champ)")
check(proche(I.flux_magnetique(1.0, 2.0, PI / 3), 1.0), "Φ(B=1,A=2,θ=π/3) = 2·cos60° = 1 Wb")
check(proche(I.flux_magnetique(2.0, 3.0, 0.0), 6.0), "Φ(B=2,A=3,θ=0) = 6 Wb")
check(I.flux_magnetique(0.5, 0.2, 2.0) < 0, "θ ∈ ]π/2, π] -> flux négatif (cos<0)")
check(proche(I.flux_magnetique(0.0, 1.0, 0.0), 0.0), "B=0 -> Φ=0 (pas de champ, pas de flux)")

# ── 2) ANCRES FARADAY ε = −N·ΔΦ/Δt ──
fem = I.fem_faraday(100, 0.01, 0.1)
check(proche(abs(fem), 10.0), "|ε|(N=100, ΔΦ=0.01 Wb, Δt=0.1 s) = 10 V (100·0.01/0.1 à la main)")
check(fem < 0, "LENZ : ΔΦ>0 (flux croissant) -> ε NÉGATIVE (le signe − de Faraday)")
check(proche(fem, -10.0), "ε(N=100, ΔΦ=0.01, Δt=0.1) = −10 V exactement")
check(proche(I.fem_faraday(1, 1.0, 1.0), -1.0), "ε(N=1, ΔΦ=1, Δt=1) = −1 V (à la main)")
check(proche(I.fem_faraday(500, 0.002, 0.5), -2.0), "ε(N=500, ΔΦ=0.002, Δt=0.5) = −500·0.004 = −2 V")
check(proche(I.fem_faraday(100, -0.01, 0.1), 10.0),
      "ΔΦ<0 (flux décroissant) -> ε POSITIVE : ε(ΔΦ=−0.01) = +10 V")
check(proche(I.fem_faraday(1, 0.0, 1.0), 0.0), "ΔΦ=0 -> ε=0 (pas de variation, pas de fem)")
# proportionnalité en N (2 appels, valeurs attendues posées à la main : 3·0.5/0.25=6, 6·0.5/0.25=12)
check(proche(I.fem_faraday(3, 0.5, 0.25), -6.0), "ε(N=3, ΔΦ=0.5, Δt=0.25) = −6 V")
check(proche(I.fem_faraday(6, 0.5, 0.25), -12.0), "ε(N=6) = −12 V (doubler N double la fem)")

# ── 3) ANCRES LENZ (sens qualitatif) ──
check(I.sens_courant_induit(0.1, 0.3) == "oppose_a_l_augmentation",
      "flux croissant (0.1→0.3 Wb) -> courant induit crée un flux OPPOSÉ à l'augmentation")
check(I.sens_courant_induit(0.3, 0.1) == "oppose_a_la_diminution",
      "flux décroissant (0.3→0.1 Wb) -> courant induit s'oppose à la diminution")
check(I.sens_courant_induit(0.2, 0.2) == "aucun", "flux constant -> aucun courant induit")
check(I.sens_courant_induit(-0.5, -0.2) == "oppose_a_l_augmentation",
      "flux négatif qui remonte (−0.5→−0.2) est une AUGMENTATION algébrique")
check(I.sens_courant_induit(0.0, -0.1) == "oppose_a_la_diminution", "0→−0.1 : diminution algébrique")
check("oppose" in I.LENZ or "s'oppose" in I.LENZ, "la phrase de Lenz (référence) est présente dans le module")
# cohérence Lenz <-> signe de Faraday : croissant -> ε<0 ; décroissant -> ε>0
check(I.sens_courant_induit(0.1, 0.3) == "oppose_a_l_augmentation" and I.fem_faraday(1, 0.2, 1.0) < 0,
      "cohérence : flux croissant -> sens 'oppose_a_l_augmentation' ET ε<0")
check(I.sens_courant_induit(0.3, 0.1) == "oppose_a_la_diminution" and I.fem_faraday(1, -0.2, 1.0) > 0,
      "cohérence : flux décroissant -> sens 'oppose_a_la_diminution' ET ε>0")

# ── 4) ANCRES FEM DE DÉPLACEMENT ε = B·L·v ──
check(proche(I.fem_deplacement(0.4, 0.5, 2.0), 0.4), "ε(B=0.4 T, L=0.5 m, v=2 m/s) = 0.4 V (à la main)")
check(proche(I.fem_deplacement(1.0, 1.0, 1.0), 1.0), "ε(1 T, 1 m, 1 m/s) = 1 V")
check(proche(I.fem_deplacement(0.5, 2.0, 3.0), 3.0), "ε(0.5, 2, 3) = 3 V (0.5·2·3 à la main)")
check(proche(I.fem_deplacement(0.4, 0.5, 0.0), 0.0), "v=0 -> ε=0 (barre immobile)")

# ── 5) SECOND CHEMIN : barre sur rails, |ε| via Faraday = ε via déplacement ──
B, L, v, dt = 0.4, 0.5, 2.0, 0.25
delta_phi = B * L * v * dt        # ΔΦ = B·ΔA = B·L·v·Δt, calculé ICI (pas par le module) = 0.1 Wb
check(proche(delta_phi, 0.1), "ΔΦ balayé (B=0.4, L=0.5, v=2, Δt=0.25) = 0.1 Wb (à la main)")
check(proche(abs(I.fem_faraday(1, delta_phi, dt)), I.fem_deplacement(B, L, v)),
      "second chemin : |ε| Faraday (flux balayé) = ε déplacement = 0.4 V")
B2, L2, v2, dt2 = 1.2, 0.3, 5.0, 2.0
check(proche(abs(I.fem_faraday(1, B2 * L2 * v2 * dt2, dt2)), I.fem_deplacement(B2, L2, v2)),
      "second chemin (jeu 2) : Faraday et déplacement coïncident")

# ── 6) SOUNDNESS — Δt ──
check(leve(I.fem_faraday, 100, 0.01, 0.0), "Δt=0 -> ValueError")
check(leve(I.fem_faraday, 100, 0.01, -0.1), "Δt<0 -> ValueError")

# ── 7) SOUNDNESS — N (spires) ──
check(leve(I.fem_faraday, 0, 0.01, 0.1), "N=0 -> ValueError")
check(leve(I.fem_faraday, -3, 0.01, 0.1), "N<0 -> ValueError")
check(leve(I.fem_faraday, 2.5, 0.01, 0.1), "N non entier (2.5) -> ValueError")
check(leve(I.fem_faraday, 100.0, 0.01, 0.1), "N flottant (100.0) -> ValueError (entier exigé)")
check(leve(I.fem_faraday, True, 0.01, 0.1), "N=True -> ValueError (bool n'est pas 1 spire)")

# ── 8) SOUNDNESS — angle hors [0, π] ──
check(leve(I.flux_magnetique, 0.5, 0.2, -0.1), "θ<0 -> ValueError")
check(leve(I.flux_magnetique, 0.5, 0.2, PI + 0.1), "θ>π -> ValueError")
check(leve(I.flux_magnetique, 0.5, 0.2, 7.0), "θ=7 rad -> ValueError")

# ── 9) SOUNDNESS — aire / champ / barre ──
check(leve(I.flux_magnetique, 0.5, 0.0, 0.0), "A=0 -> ValueError")
check(leve(I.flux_magnetique, 0.5, -1.0, 0.0), "A<0 -> ValueError")
check(leve(I.flux_magnetique, -0.5, 0.2, 0.0), "B<0 -> ValueError (norme ; le signe se porte sur θ)")
check(leve(I.fem_deplacement, -0.4, 0.5, 2.0), "déplacement B<0 -> ValueError")
check(leve(I.fem_deplacement, 0.4, 0.0, 2.0), "L=0 -> ValueError")
check(leve(I.fem_deplacement, 0.4, -0.5, 2.0), "L<0 -> ValueError")
check(leve(I.fem_deplacement, 0.4, 0.5, -2.0), "v<0 -> ValueError (norme de vitesse)")

# ── 10) SOUNDNESS — types invalides (bool / str / NaN / inf) ──
check(leve(I.flux_magnetique, True, 0.2, 0.0), "B bool -> ValueError")
check(leve(I.flux_magnetique, "0.5", 0.2, 0.0), "B str -> ValueError")
check(leve(I.flux_magnetique, float("nan"), 0.2, 0.0), "B NaN -> ValueError")
check(leve(I.flux_magnetique, float("inf"), 0.2, 0.0), "B inf -> ValueError")
check(leve(I.flux_magnetique, 0.5, float("nan"), 0.0), "A NaN -> ValueError")
check(leve(I.flux_magnetique, 0.5, 0.2, float("inf")), "θ inf -> ValueError")
check(leve(I.fem_faraday, 100, float("nan"), 0.1), "ΔΦ NaN -> ValueError")
check(leve(I.fem_faraday, 100, float("inf"), 0.1), "ΔΦ inf -> ValueError")
check(leve(I.fem_faraday, 100, "0.01", 0.1), "ΔΦ str -> ValueError")
check(leve(I.fem_faraday, 100, 0.01, float("nan")), "Δt NaN -> ValueError")
check(leve(I.sens_courant_induit, float("nan"), 0.1), "Lenz flux_avant NaN -> ValueError")
check(leve(I.sens_courant_induit, 0.1, float("inf")), "Lenz flux_après inf -> ValueError")
check(leve(I.sens_courant_induit, True, 0.1), "Lenz bool -> ValueError")
check(leve(I.sens_courant_induit, "0.1", 0.2), "Lenz str -> ValueError")
check(leve(I.fem_deplacement, 0.4, True, 2.0), "L bool -> ValueError")
check(leve(I.fem_deplacement, 0.4, 0.5, float("nan")), "v NaN -> ValueError")

# ── 11) DÉTERMINISME ──
check(I.flux_magnetique(0.5, 0.2, 0.7) == I.flux_magnetique(0.5, 0.2, 0.7), "déterminisme flux")
check(I.fem_faraday(100, 0.01, 0.1) == I.fem_faraday(100, 0.01, 0.1), "déterminisme Faraday")
check(I.sens_courant_induit(0.1, 0.3) == I.sens_courant_induit(0.1, 0.3), "déterminisme Lenz")
check(I.fem_deplacement(0.4, 0.5, 2.0) == I.fem_deplacement(0.4, 0.5, 2.0), "déterminisme déplacement")

print(f"\n=== valide_induction_em : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
