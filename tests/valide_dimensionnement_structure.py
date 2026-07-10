"""
VALIDE dimensionnement_structure.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (valeurs connues INDÉPENDAMMENT de la formule testée) :
  • Acier doux S235 : Re_min = 235 MPa (EN 10025-2). γ = 1.5 -> σ_adm = 235/1.5 = 156.666… MPa
    (division posée À LA MAIN, pas via la fonction testée).
  • Poutre rectangulaire, M = 10 kN·m = 1e7 N·mm, b = 100 mm :
        h = sqrt(6·1e7 / (100·156.6667)) = sqrt(3829.79) = 61.885 mm  (calcul À LA MAIN).
    BOUCLE FERMÉE : σ = 6·M/(b·h²) réinjectée doit revaloir 156.667 MPa à 0.1 % près, par un SECOND chemin
    (arithmétique de la gate + structures_genie en SI), jamais par la fonction de dimensionnement.
  • verifie_section : 50 MPa -> 'sûr' (50 < 235/1.5) ; 900 MPa -> 'insuffisant' (900 > 630/1.5 = 420) ;
    200 MPa -> 'indéterminé' (156.67 ≤ 200 ≤ 420, l'intervalle de Re ne tranche pas).
  • Flambement d'un poteau acier carré 50 mm, L = 3 m, appuis rotulés, E = 210 GPa :
        I = 0.05⁴/12 = 5.2083e-7 m⁴ (À LA MAIN) ; P_cr = π²·E·I/L² ≈ 1.199e5 N ≈ 120 kN
        (ordre de grandeur d'ingénieur connu : ~100 kN). Coefficient de sécurité = P_cr/force.
    Ratios de mode NON CIRCULAIRES : encastré-encastré (K=0.5) -> ×4 ; encastré-libre (K=2) -> ÷4.
  • Flèche : critère de SERVICE L/300 (convention normative) : flèche 10 mm sur portée 3000 mm -> pile L/300
    -> 'conforme' ; 11 mm -> 'non conforme'.

ABSTENTIONS : matériau fragile (béton/verre/fonte/bois), γ ≤ 1, M ≤ 0, b ≤ 0, force/L/E/I ≤ 0, portée ≤ 0,
limite_relative ≤ 0, mode inconnu, types bool/str/NaN/inf -> ValueError. DÉTERMINISME vérifié.
"""
import math

import dimensionnement_structure as D
import structures_genie as R

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


def proche(x, attendu, tol):
    return x is not None and abs(x - attendu) <= tol


# ══ 1) CONTRAINTE ADMISSIBLE = Re_min/γ (ancre : 235/1.5 posé à la main) ══════════════════════════════════════════
SIGMA_ADM = 235.0 / 1.5                                   # = 156.6666667 MPa, À LA MAIN
check(proche(D.contrainte_admissible("acier doux", 1.5), SIGMA_ADM, 1e-4),
      "σ_adm acier doux γ=1.5 = 235/1.5 = 156.667 MPa")
# aluminium 6061 : Re_min = 55 MPa (catalogue), γ=2 -> 27.5 MPa (à la main)
check(proche(D.contrainte_admissible("aluminium 6061", 2.0), 55.0 / 2.0, 1e-4),
      "σ_adm alu6061 γ=2 = 55/2 = 27.5 MPa")
# titane Ti-6Al-4V : Re_min = 828 MPa, γ=3 -> 276 MPa
check(proche(D.contrainte_admissible("titane ti-6al-4v", 3.0), 828.0 / 3.0, 1e-4),
      "σ_adm titane γ=3 = 828/3 = 276 MPa")
# on utilise BIEN le MIN (pas le max 630) : sinon on obtiendrait 630/1.5=420, distinct
check(not proche(D.contrainte_admissible("acier doux", 1.5), 630.0 / 1.5, 1e-4),
      "σ_adm prend le MIN (156.67), pas le max (420) — posture sûre")

# ══ 2) VERIFIE_SECTION : 'sûr' | 'insuffisant' | 'indéterminé' ════════════════════════════════════════════════════
check(D.verifie_section("acier doux", 50, 1.5) == "sûr", "section acier 50 MPa γ=1.5 -> sûr")
check(D.verifie_section("acier doux", 900, 1.5) == "insuffisant", "section acier 900 MPa -> insuffisant (>420)")
check(D.verifie_section("acier doux", 200, 1.5) == "indéterminé", "section acier 200 MPa -> indéterminé (156.67..420)")
# bornes conservatrices : à σ_adm_min exactement -> pas 'sûr' (strict) -> 'indéterminé'
check(D.verifie_section("acier doux", 235.0 / 1.5, 1.5) == "indéterminé", "section pile σ_adm_min -> indéterminé (borne incluse)")
# à σ_adm_max = 630/1.5 = 420 exactement -> pas 'insuffisant' -> 'indéterminé'
check(D.verifie_section("acier doux", 630.0 / 1.5, 1.5) == "indéterminé", "section pile σ_adm_max=420 -> indéterminé")
# aluminium : adm_min=55/1.5=36.67, adm_max=350/1.5=233.33
check(D.verifie_section("aluminium 6061", 30, 1.5) == "sûr", "section alu 30 MPa -> sûr (<36.67)")
check(D.verifie_section("aluminium 6061", 300, 1.5) == "insuffisant", "section alu 300 MPa -> insuffisant (>233.33)")
check(D.verifie_section("aluminium 6061", 100, 1.5) == "indéterminé", "section alu 100 MPa -> indéterminé")

# ══ 3) DIMENSIONNEMENT + BOUCLE FERMÉE (ancre 61.885 mm à la main, réinjection indépendante) ══════════════════════
h = D.dimensionne_poutre_rectangulaire(1e7, "acier doux", 1.5, 100)
check(proche(h, 61.885, 0.01), f"h dimensionnée = 61.885 mm (à la main), obtenu {h}")
check(proche(h, 61.9, 0.1), "h ≈ 61.9 mm (ancre imposée)")

# BOUCLE FERMÉE #1 : σ = 6M/(b·h²) recalculée par la GATE (chemin indépendant) ≈ σ_adm à 0.1 %
sigma_reinj = 6.0 * 1e7 / (100.0 * h * h)                # MPa, arithmétique de la gate
check(proche(sigma_reinj, SIGMA_ADM, 1e-3 * SIGMA_ADM),
      f"σ réinjectée (gate) {sigma_reinj} ≈ σ_adm {SIGMA_ADM} MPa à 0.1 %")

# BOUCLE FERMÉE #2 : via structures_genie en SI (encore un autre chemin de code)
M_Nm = 1e7 / 1000.0                                       # 1e4 N·m
b_m, h_m = 100.0 / 1000.0, h / 1000.0
I_m4 = R.moment_quadratique_rectangle(b_m, h_m)
sigma_SI_MPa = R.contrainte_flexion(M_Nm, I_m4, h_m / 2.0) / 1e6
check(proche(sigma_SI_MPa, SIGMA_ADM, 1e-3 * SIGMA_ADM),
      f"σ réinjectée (structures_genie SI) {sigma_SI_MPa} ≈ σ_adm à 0.1 %")
# et σ réinjectée NE DÉPASSE PAS σ_adm (garde FAUX=0)
check(sigma_SI_MPa <= SIGMA_ADM * (1 + 1e-6), "σ réinjectée ≤ σ_adm (invariant respecté)")

# monotonie : moment plus grand -> hauteur plus grande
h2 = D.dimensionne_poutre_rectangulaire(4e7, "acier doux", 1.5, 100)   # M ×4 -> h ×2 (σ∝M/h²)
check(proche(h2, 2.0 * h, 0.02), f"M×4 -> h×2 (61.885->{h2})")

# ══ 4) FLAMBEMENT D'EULER : coefficient de sécurité = P_cr/force ══════════════════════════════════════════════════
I_carre = 0.05 ** 4 / 12.0                                # 5.2083e-7 m⁴, À LA MAIN
P_cr_hand = math.pi ** 2 * 210e9 * I_carre / (3.0 ** 2)   # ≈ 1.199e5 N, formule d'Euler posée à la main
force = 100e3
coef = D.verifie_flambement(force, 3.0, 210e9, I_carre, "rotulé-rotulé")
check(proche(coef, P_cr_hand / force, 1e-3), f"coef flambement = P_cr/force (hand {P_cr_hand/force:.5f}) obtenu {coef}")
# ordre de grandeur d'ingénieur connu : P_cr entre 100 et 140 kN
check(1.0e5 <= coef * force <= 1.4e5, f"P_cr ≈ 120 kN (ordre de grandeur), obtenu {coef*force:.0f} N")
# ratios de MODE non circulaires : K=0.5 -> ×4 ; K=2 -> ÷4  (P_cr ∝ 1/K²)
coef_ee = D.verifie_flambement(force, 3.0, 210e9, I_carre, "encastré-encastré")
coef_el = D.verifie_flambement(force, 3.0, 210e9, I_carre, "encastré-libre")
check(proche(coef_ee, 4.0 * coef, 1e-3 * 4 * coef), "encastré-encastré (K=0.5) -> P_cr ×4")
check(proche(coef_el, coef / 4.0, 1e-3 * coef), "encastré-libre (K=2) -> P_cr ÷4")
# coefficient > 1 => stable ici
check(coef > 1.0, "poteau 50mm/3m/100kN : stable (coef > 1)")

# ══ 5) FLÈCHE : critère de service L/300 (convention normative) ═══════════════════════════════════════════════════
check(D.verifie_fleche(10, 3000, 300) == "conforme", "flèche 10mm = L/300 -> conforme (borne incluse)")
check(D.verifie_fleche(11, 3000, 300) == "non conforme", "flèche 11mm > L/300 -> non conforme")
check(D.verifie_fleche(5, 3000, 300) == "conforme", "flèche 5mm < L/300 -> conforme")
check(D.verifie_fleche(0, 3000, 300) == "conforme", "flèche nulle -> conforme")
check(D.verifie_fleche(6, 3000, 500) == "conforme", "flèche 6mm = L/500 -> conforme (borne incluse)")
check(D.verifie_fleche(7, 3000, 500) == "non conforme", "flèche 7mm > L/500=6mm -> non conforme")

# ══ 6) ABSTENTIONS — matériaux fragiles / sans limite conventionnelle ═════════════════════════════════════════════
check(leve(D.contrainte_admissible, "béton", 1.5), "béton -> ValueError (pas de limite élastique)")
check(leve(D.contrainte_admissible, "verre", 1.5), "verre -> ValueError (fragile)")
check(leve(D.contrainte_admissible, "fonte", 1.5), "fonte -> ValueError (fragile)")
check(leve(D.contrainte_admissible, "bois de pin", 1.5), "bois -> ValueError (anisotrope)")
check(leve(D.verifie_section, "béton", 50, 1.5), "verifie_section béton -> ValueError")
check(leve(D.dimensionne_poutre_rectangulaire, 1e7, "verre", 1.5, 100), "dimensionne verre -> ValueError")
check(leve(D.contrainte_admissible, "inconnu", 1.5), "matériau hors catalogue -> ValueError")

# ══ 7) ABSTENTIONS — γ ≤ 1 (pas une sécurité) ════════════════════════════════════════════════════════════════════
check(leve(D.contrainte_admissible, "acier doux", 0.9), "γ=0.9 -> ValueError")
check(leve(D.contrainte_admissible, "acier doux", 1.0), "γ=1.0 -> ValueError (pas de marge)")
check(leve(D.verifie_section, "acier doux", 50, 1.0), "verifie_section γ=1 -> ValueError")
check(leve(D.dimensionne_poutre_rectangulaire, 1e7, "acier doux", 1.0, 100), "dimensionne γ=1 -> ValueError")

# ══ 8) ABSTENTIONS — géométrie/chargement non physiques ══════════════════════════════════════════════════════════
check(leve(D.dimensionne_poutre_rectangulaire, 0, "acier doux", 1.5, 100), "M=0 -> ValueError")
check(leve(D.dimensionne_poutre_rectangulaire, -1e7, "acier doux", 1.5, 100), "M<0 -> ValueError")
check(leve(D.dimensionne_poutre_rectangulaire, 1e7, "acier doux", 1.5, 0), "b=0 -> ValueError")
check(leve(D.dimensionne_poutre_rectangulaire, 1e7, "acier doux", 1.5, -100), "b<0 -> ValueError")
check(leve(D.verifie_section, "acier doux", -50, 1.5), "σ appliquée < 0 -> ValueError")
check(leve(D.verifie_flambement, 0, 3.0, 210e9, I_carre, "rotulé-rotulé"), "force=0 -> ValueError")
check(leve(D.verifie_flambement, force, 0, 210e9, I_carre, "rotulé-rotulé"), "L=0 -> ValueError")
check(leve(D.verifie_flambement, force, 3.0, 0, I_carre, "rotulé-rotulé"), "E=0 -> ValueError")
check(leve(D.verifie_flambement, force, 3.0, 210e9, 0, "rotulé-rotulé"), "I=0 -> ValueError")
check(leve(D.verifie_flambement, force, 3.0, 210e9, I_carre, "hélicoïdal"), "mode inconnu -> ValueError")
check(leve(D.verifie_fleche, 10, 0, 300), "portée=0 -> ValueError")
check(leve(D.verifie_fleche, 10, 3000, 0), "limite_relative=0 -> ValueError")
check(leve(D.verifie_fleche, -1, 3000, 300), "flèche<0 -> ValueError")

# ══ 9) ABSTENTIONS — types invalides (bool / str / NaN / inf) ═════════════════════════════════════════════════════
check(leve(D.contrainte_admissible, "acier doux", True), "γ bool -> ValueError")
check(leve(D.contrainte_admissible, "acier doux", "1.5"), "γ str -> ValueError")
check(leve(D.contrainte_admissible, "acier doux", float("nan")), "γ NaN -> ValueError")
check(leve(D.contrainte_admissible, "acier doux", float("inf")), "γ inf -> ValueError")
check(leve(D.contrainte_admissible, True, 1.5), "matériau bool -> ValueError")
check(leve(D.dimensionne_poutre_rectangulaire, True, "acier doux", 1.5, 100), "M bool -> ValueError")
check(leve(D.dimensionne_poutre_rectangulaire, float("inf"), "acier doux", 1.5, 100), "M inf -> ValueError")
check(leve(D.dimensionne_poutre_rectangulaire, 1e7, "acier doux", 1.5, float("nan")), "b NaN -> ValueError")
check(leve(D.verifie_section, "acier doux", True, 1.5), "σ bool -> ValueError")
check(leve(D.verifie_flambement, force, 3.0, 210e9, I_carre, True), "mode bool -> ValueError")
check(leve(D.verifie_flambement, True, 3.0, 210e9, I_carre, "rotulé-rotulé"), "force bool -> ValueError")
check(leve(D.verifie_fleche, float("inf"), 3000, 300), "flèche inf -> ValueError")
check(leve(D.verifie_fleche, "10", 3000, 300), "flèche str -> ValueError")

# ══ 10) DÉTERMINISME ═════════════════════════════════════════════════════════════════════════════════════════════
check(D.contrainte_admissible("acier doux", 1.5) == D.contrainte_admissible("acier doux", 1.5), "déterminisme σ_adm")
check(D.dimensionne_poutre_rectangulaire(1e7, "acier doux", 1.5, 100)
      == D.dimensionne_poutre_rectangulaire(1e7, "acier doux", 1.5, 100), "déterminisme h")
check(D.verifie_flambement(force, 3.0, 210e9, I_carre, "rotulé-rotulé")
      == D.verifie_flambement(force, 3.0, 210e9, I_carre, "rotulé-rotulé"), "déterminisme flambement")
check(D.verifie_section("acier doux", 200, 1.5) == D.verifie_section("acier doux", 200, 1.5), "déterminisme section")

print(f"\n=== valide_dimensionnement_structure : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
