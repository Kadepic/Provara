"""
VALIDE inference_classique.py — held-out ADVERSE.

ANCRES NON CIRCULAIRES (valeurs connues INDÉPENDAMMENT de la formule testée) :
  • phi(0) = 0.5 exactement ; phi(1.96) ≈ 0.975 ; phi(−1.96) ≈ 0.025 (table normale universelle).
  • phi_inverse(0.975) ≈ 1.959964 (quantile normal tabulé).
  • test_z : x̄=105, μ₀=100, σ=15, n=36 -> z = 5/(15/6) = 2.0 EXACTEMENT (calcul à la main) ;
    p bilatérale = 0.0455 (2×0.02275, valeur de table) ; p unilatérale = 0.02275.
  • IC 95 % σ connu : 105 ± 1.959964×2.5 = [100.10, 109.90] (calcul à la main).
  • Student ν=1 (loi de CAUCHY, forme fermée) : P(T>t) = 0.5 − arctan(t)/π. Échantillon [0,2], μ₀=0 -> t=1,
    ν=1 ; p bilatérale = 2×(0.5 − arctan(1)/π) = 0.5 ; p unilatérale = 0.25. (INDÉPENDANT de Simpson.)
  • Student ν=2 (forme fermée) : P(T>t) = 0.5 − t/(2√(2+t²)). Échantillon [−√3,0,√3], μ₀=−1 -> t=1, ν=2 ;
    p bilatérale = 2×(0.5 − 1/(2√3)) = 0.4226497.
  • Quantile de Student t_{0.975,1} = tan(π×0.475) = 12.70620 (forme fermée Cauchy). IC de [0,2] à 95 % =
    1 ± 12.70620 = [−11.7062, 13.7062].
  • WILSON 0 succès sur 10 (95 %) : intervalle ⊂ [0,1], borne basse ≈ 0, borne haute ≈ 0.2776 > 0 :
    ANCRE DISCRIMINANTE (Wald donnerait [0,0], absurde).
  • χ² : [10,10,10,10,10,10] vs attendus 10 -> statistique = 0, p = 1 ; [30,6,6,6,6,6] vs 10 ->
    statistique = 20²/10 + 5×4²/10 = 40 + 8 = 48 (calcul à la main), p < 0.001. Effectif attendu 2 -> ValueError.

SOUNDNESS : bool/str/NaN/inf, n<2, σ≤0, niveau hors ]0,1[, variance nulle (Student), attendu<5 (χ²), arité.
"""
import math

import inference_classique as I

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve(fn, *a, **k):
    """True ssi fn lève ValueError (abstention structurelle)."""
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True


def proche(x, attendu, tol=1e-6):
    return x is not None and abs(x - attendu) <= tol


def chi2_tail_exact(x, k):
    """P(χ²_k > x) EXACT — chemin de code TOTALEMENT INDÉPENDANT du module.

    Récurrence analytique de la gamma incomplète supérieure Q(a+1,y) = Q(a,y) + y^a·e^{−y}/Γ(a+1),
    y = x/2, a = k/2 ; bases exactes Q(1/2,y)=erfc(√y) (k impair) et Q(1,y)=e^{−y} (k pair). Ceci
    n'utilise NI la série NI la fraction continue du module (algorithme différent : erfc + récurrence).
    Vérifié ci-dessous contre des valeurs critiques χ² universellement tabulées."""
    y = x / 2.0
    if k % 2 == 0:
        a = 1.0
        q = math.exp(-y)              # Q(1, y) = P(χ²_2 > x)
        ki = 2
    else:
        a = 0.5
        q = math.erfc(math.sqrt(y))   # Q(1/2, y) = P(χ²_1 > x)
        ki = 1
    while ki < k:
        q = q + math.exp(a * math.log(y) - y - math.lgamma(a + 1.0))
        a += 1.0
        ki += 2
    return q


PI = math.pi

# ── 1) LOI NORMALE phi ── ancres de table ──
check(I.phi(0.0) == 0.5, "phi(0) = 0.5 exactement")
check(proche(I.phi(1.96), 0.975, 1e-4), "phi(1.96) ≈ 0.975")
check(proche(I.phi(-1.96), 0.025, 1e-4), "phi(−1.96) ≈ 0.025")
check(proche(I.phi(1.96) + I.phi(-1.96), 1.0, 1e-12), "symétrie phi(z)+phi(−z)=1")
check(proche(I.phi(2.0), 0.9772498681, 1e-9), "phi(2) ≈ 0.97724987 (table)")

# ── 2) QUANTILE NORMAL phi_inverse ── valeur tabulée ──
check(proche(I.phi_inverse(0.975), 1.959964, 1e-4), "phi_inverse(0.975) ≈ 1.959964")
check(proche(I.phi_inverse(0.5), 0.0, 1e-9), "phi_inverse(0.5) = 0")
# round-trip croisé (deux fonctions distinctes)
check(proche(I.phi(I.phi_inverse(0.9)), 0.9, 1e-9), "phi(phi_inverse(0.9)) = 0.9")
lo, hi = I.quantile_normal_encadrement(0.975)
check((hi - lo) <= 1e-13 and proche(0.5 * (lo + hi), 1.959964, 1e-4) and I.phi(lo) < 0.975 <= I.phi(hi),
      "encadrement quantile serré et correct autour de 1.959964")

# ── 3) TEST Z ── z = 2.0 exact, p de table ──
rz = I.test_z(105.0, 100.0, 15.0, 36)  # z = 5/(15/6) = 5/2.5 = 2.0
check(proche(rz["statistique"], 2.0, 1e-12), "test_z statistique = 2.0 (calcul main)")
check(proche(rz["p_valeur"], 0.0455, 1e-3), "test_z p bilatérale ≈ 0.0455 (table)")
check(proche(rz["p_valeur"], 2.0 * (1.0 - 0.9772498681), 1e-6), "test_z p = 2×0.02275 (second chemin)")
rzu = I.test_z(105.0, 100.0, 15.0, 36, bilateral=False)
check(proche(rzu["p_valeur"], 0.02275, 1e-3), "test_z p unilatérale ≈ 0.02275 (table)")
# écart nul -> p = 1
r0 = I.test_z(100.0, 100.0, 15.0, 36)
check(proche(r0["statistique"], 0.0, 1e-12) and proche(r0["p_valeur"], 1.0, 1e-9), "test_z x̄=μ₀ -> z=0, p=1")

# ── 4) IC MOYENNE σ CONNU ── 105 ± 1.959964×2.5 ──
bas, haut = I.ic_moyenne_sigma_connu(105.0, 15.0, 36, 0.95)
check(proche(bas, 100.10, 1e-2), "IC σ connu bas ≈ 100.10 (calcul main)")
check(proche(haut, 109.90, 1e-2), "IC σ connu haut ≈ 109.90 (calcul main)")
check(proche(0.5 * (bas + haut), 105.0, 1e-6), "IC centré sur la moyenne 105")
# demi-largeur = z×σ/√n = 1.959964×2.5
check(proche(haut - bas, 2.0 * 1.959964 * 2.5, 1e-3), "IC largeur = 2×1.959964×2.5")

# ── 5) STUDENT ν=1 (CAUCHY, forme fermée P(T>t)=0.5−arctan(t)/π) ──
rt1 = I.test_t_student([0.0, 2.0], 0.0)  # x̄=1, s=√2, se=1, t=1, ν=1
check(proche(rt1["statistique"], 1.0, 1e-9), "Student [0,2] t = 1")
check(rt1["ddl"] == 1, "Student [0,2] ddl = 1")
cauchy_bilat = 2.0 * (0.5 - math.atan(1.0) / PI)  # = 0.5, forme fermée INDÉPENDANTE
check(proche(rt1["p_valeur"], cauchy_bilat, 1e-4), "Student ν=1 p bilatérale = 0.5 (Cauchy)")
check(proche(rt1["p_valeur"], 0.5, 1e-4), "Student ν=1 p = 0.5 (valeur explicite)")
rt1u = I.test_t_student([0.0, 2.0], 0.0, bilateral=False)
check(proche(rt1u["p_valeur"], 0.25, 1e-4), "Student ν=1 p unilatérale = 0.25 (Cauchy)")
check(rt1["borne_erreur"] < 1e-6, "Student borne d'erreur numérique petite")

# ── 6) STUDENT ν=2 (forme fermée P(T>t)=0.5−t/(2√(2+t²))) ──
r3 = math.sqrt(3.0)
rt2 = I.test_t_student([-r3, 0.0, r3], -1.0)  # x̄=0, s=√3, se=1, t=1, ν=2
check(rt2["ddl"] == 2 and proche(rt2["statistique"], 1.0, 1e-9), "Student [−√3,0,√3] t=1, ddl=2")
nu2_bilat = 2.0 * (0.5 - 1.0 / (2.0 * math.sqrt(2.0 + 1.0)))  # forme fermée ν=2
check(proche(rt2["p_valeur"], nu2_bilat, 1e-4), "Student ν=2 p bilatérale = 0.42265 (forme fermée)")
check(proche(nu2_bilat, 0.4226497, 1e-6), "ancre ν=2 = 0.4226497 (contrôle de l'ancre)")

# ── 7) IC MOYENNE σ INCONNU (Student), quantile t_{0.975,1}=tan(0.475π)=12.7062 ──
tq1 = math.tan(PI * 0.475)  # ≈ 12.70620, forme fermée Cauchy
b2, h2 = I.ic_moyenne_sigma_inconnu([0.0, 2.0], 0.95)  # x̄=1, se=1 -> 1 ± tq1
check(proche(0.5 * (b2 + h2), 1.0, 1e-3), "IC Student centré sur 1")
check(proche(h2 - b2, 2.0 * tq1, 5e-2), "IC Student largeur = 2×t_{0.975,1}=2×12.7062")
check(proche(h2, 1.0 + tq1, 5e-2), "IC Student haut ≈ 13.706")

# ── 8) WILSON 0/10 — ANCRE DISCRIMINANTE (Wald=[0,0] absurde) ──
wlo, whi = I.ic_proportion_wilson(0, 10, 0.95)
check(0.0 <= wlo <= 1e-6, "Wilson 0/10 borne basse ≈ 0 (dans [0,1])")
check(0.0 <= whi <= 1.0, "Wilson 0/10 borne haute dans [0,1]")
check(whi > 0.2, "Wilson 0/10 borne haute > 0.2 (Wald donnerait 0 : DISCRIMINANT)")
check(proche(whi, 0.2776, 5e-3), "Wilson 0/10 borne haute ≈ 0.2776")
# symétrie : 10/10 -> [≈0.7224, 1]
wlo2, whi2 = I.ic_proportion_wilson(10, 10, 0.95)
check(proche(whi2, 1.0, 1e-9) and proche(wlo2, 1.0 - 0.2776, 5e-3), "Wilson 10/10 = symétrique de 0/10")
# 50/100 -> centré ≈ 0.5, inclus dans [0,1]
wlo3, whi3 = I.ic_proportion_wilson(50, 100, 0.95)
check(0.0 < wlo3 < 0.5 < whi3 < 1.0, "Wilson 50/100 encadre 0.5 dans [0,1]")

# ── 9) KHI-DEUX ── stat calculée à la main ──
rc0 = I.test_khi2_conformite([10, 10, 10, 10, 10, 10], [10, 10, 10, 10, 10, 10])
check(proche(rc0["statistique"], 0.0, 1e-12), "χ² observés=attendus -> statistique 0")
check(proche(rc0["p_valeur"], 1.0, 1e-9), "χ² statistique 0 -> p = 1")
check(rc0["ddl"] == 5, "χ² 6 catégories -> 5 ddl")
rc1 = I.test_khi2_conformite([30, 6, 6, 6, 6, 6], [10, 10, 10, 10, 10, 10])
check(proche(rc1["statistique"], 48.0, 1e-9), "χ² [30,6×5] statistique = 48 (calcul main)")
check(0.0 < rc1["p_valeur"] < 1e-3, "χ² statistique 48, 5 ddl -> p < 0.001")
# χ²_2 : P(χ²_2 > x) = exp(−x/2) (forme fermée) ; x=2 -> e^{-1}=0.367879
rc2 = I.test_khi2_conformite([12, 8, 10], [10, 10, 10])  # stat = 4/10+4/10+0 = 0.8, ddl=2
check(rc2["ddl"] == 2 and proche(rc2["statistique"], 0.8, 1e-9), "χ² [12,8,10] stat=0.8, ddl=2")
check(proche(rc2["p_valeur"], math.exp(-0.8 / 2.0), 1e-4), "χ²_2 p = e^{−stat/2} (forme fermée)")

# ── 9bis) CONTRÔLE DE L'ANCRE chi2_tail_exact contre des VALEURS CRITIQUES χ² TABULÉES (non circulaire) ──
# Quantiles 0.95 universellement tabulés : P(χ²_k > q_{0.95}) = 0.05.  (Tables χ² standard.)
check(proche(chi2_tail_exact(3.841, 1), 0.05, 5e-4), "ancre: P(χ²_1 > 3.841) ≈ 0.05 (table)")
check(proche(chi2_tail_exact(18.307, 10), 0.05, 5e-4), "ancre: P(χ²_10 > 18.307) ≈ 0.05 (table)")
check(proche(chi2_tail_exact(31.410, 20), 0.05, 5e-4), "ancre: P(χ²_20 > 31.410) ≈ 0.05 (table)")
check(proche(chi2_tail_exact(42.557, 29), 0.05, 5e-4), "ancre: P(χ²_29 > 42.557) ≈ 0.05 (table)")
# cohérence avec la forme fermée déjà utilisée (ddl=2 : e^{−x/2}) : double contrôle interne de l'ancre
check(proche(chi2_tail_exact(0.8, 2), math.exp(-0.4), 1e-12), "ancre: P(χ²_2>0.8)=e^{−0.4} (cohérence)")

# ── 9ter) ZONE DE PANNE — PETITE STATISTIQUE, ddl ≥ 11 (le bug bloquant d'origine) ──
# Reproduction EXACTE de l'audit : [11]+[10]*20 vs [10]*21 -> stat=0.1, ddl=20. Vrai p ≈ 0.99999999 (>0.99).
# L'ancien code renvoyait p ≈ 3.29e-13 (faux « significatif ») -> ce bloc l'aurait ATTRAPÉ.
rc_bug = I.test_khi2_conformite([11] + [10] * 20, [10] * 21)
check(proche(rc_bug["statistique"], 0.1, 1e-9) and rc_bug["ddl"] == 20, "panne: stat=0.1, ddl=20")
check(proche(rc_bug["p_valeur"], chi2_tail_exact(0.1, 20), 1e-9),
      "panne: p(stat=0.1,ddl=20) = Q exact (chemin indépendant)")
check(rc_bug["p_valeur"] > 0.99, "panne: p > 0.99 (JAMAIS rejeter — anti-faux-positif)")
check(rc_bug["borne_erreur"] < 1e-9, "panne: borne_erreur χ² petite ET résultat correct")
# end-to-end : interprete NE DOIT PAS rejeter H0 (le bug faisait 'REJETTE H0 ... significatif')
check("NE REJETTE PAS" in I.interprete(rc_bug["p_valeur"], 0.05),
      "panne: interprete(p,0.05) = NE REJETTE PAS (fin-à-fin)")

# ddl=12 (pair), petite stat : obs un cran à 12, reste 10 -> stat = 4/10 = 0.4
rc12 = I.test_khi2_conformite([12] + [10] * 12, [10] * 13)
check(proche(rc12["statistique"], 0.4, 1e-9) and rc12["ddl"] == 12, "panne: stat=0.4, ddl=12")
check(proche(rc12["p_valeur"], chi2_tail_exact(0.4, 12), 1e-9), "panne: p(ddl=12) = Q exact")
check(rc12["p_valeur"] > 0.999, "panne: p(ddl=12) > 0.999 (queue quasi pleine)")

# ddl=16 (pair) : obs un cran à 13, stat = 9/10 = 0.9
rc16 = I.test_khi2_conformite([13] + [10] * 16, [10] * 17)
check(proche(rc16["statistique"], 0.9, 1e-9) and rc16["ddl"] == 16, "panne: stat=0.9, ddl=16")
check(proche(rc16["p_valeur"], chi2_tail_exact(0.9, 16), 1e-9), "panne: p(ddl=16) = Q exact")
check(rc16["p_valeur"] > 0.99, "panne: p(ddl=16) > 0.99")

# ddl=11 (IMPAIR) : obs un cran à 13, stat = 9/10 = 0.9 -> exerce la branche série + base erfc de l'ancre
rc11 = I.test_khi2_conformite([13] + [10] * 11, [10] * 12)
check(proche(rc11["statistique"], 0.9, 1e-9) and rc11["ddl"] == 11, "panne: stat=0.9, ddl=11 (impair)")
check(proche(rc11["p_valeur"], chi2_tail_exact(0.9, 11), 1e-9), "panne: p(ddl=11 impair) = Q exact")
check(rc11["p_valeur"] > 0.99, "panne: p(ddl=11) > 0.99")

# ddl=29 (IMPAIR, borne haute du scan de l'audit) : stat=0.9
rc29 = I.test_khi2_conformite([13] + [10] * 29, [10] * 30)
check(proche(rc29["statistique"], 0.9, 1e-9) and rc29["ddl"] == 29, "panne: stat=0.9, ddl=29 (impair)")
check(proche(rc29["p_valeur"], chi2_tail_exact(0.9, 29), 1e-9), "panne: p(ddl=29 impair) = Q exact")
check(rc29["p_valeur"] > 0.9999, "panne: p(ddl=29) > 0.9999")

# monotonie de la queue en x (à ddl fixé) + accord module/ancre à GRANDE stat (au-dessus du mode)
rc_gros = I.test_khi2_conformite([40] + [10] * 20, [10] * 21)  # stat = 900/10 = 90, ddl=20
check(proche(rc_gros["statistique"], 90.0, 1e-9), "panne: grande stat=90, ddl=20")
check(rc_gros["p_valeur"] < rc_bug["p_valeur"], "panne: queue décroissante en x (90 < 0.1 en p)")
check(proche(rc_gros["p_valeur"], chi2_tail_exact(90.0, 20), 1e-12),
      "panne: p(stat=90,ddl=20) = Q exact (branche fraction continue)")

# ── 10) INTERPRÉTATION HONNÊTE ──
s_signif = I.interprete(0.01, 0.05)
check("REJETTE H0" in s_signif and "H1" in s_signif, "interprete p<α : rejet H0 mentionné")
check("pas la" in s_signif.lower() or "n'est pas" in s_signif.lower() or "PAS la" in s_signif,
      "interprete rappelle que p ≠ P(H0 vraie)")
s_ns = I.interprete(0.20, 0.05)
check("NE REJETTE PAS" in s_ns, "interprete p>α : non-rejet")
check("H1 est vraie" not in s_ns and "H1 est vraie" not in s_signif, "interprete ne dit jamais 'H1 est vraie'")

# ── 11) DÉTERMINISME ──
check(I.test_z(105.0, 100.0, 15.0, 36) == I.test_z(105.0, 100.0, 15.0, 36), "déterminisme test_z")
check(I.test_t_student([0.0, 2.0], 0.0) == I.test_t_student([0.0, 2.0], 0.0), "déterminisme test_t")
check(I.ic_proportion_wilson(0, 10, 0.95) == I.ic_proportion_wilson(0, 10, 0.95), "déterminisme Wilson")
check(I.phi(1.234) == I.phi(1.234), "déterminisme phi")

# ── 12) SOUNDNESS — types invalides ──
check(leve(I.phi, True), "phi(bool) -> ValueError")
check(leve(I.phi, "1"), "phi(str) -> ValueError")
check(leve(I.phi, float("nan")), "phi(NaN) -> ValueError")
check(leve(I.phi, float("inf")), "phi(inf) -> ValueError")
check(leve(I.phi_inverse, 0.0), "phi_inverse(0) -> ValueError")
check(leve(I.phi_inverse, 1.0), "phi_inverse(1) -> ValueError")
check(leve(I.phi_inverse, -0.1), "phi_inverse(<0) -> ValueError")

# ── 13) SOUNDNESS — test_z ──
check(leve(I.test_z, 105.0, 100.0, 15.0, 1), "test_z n<2 -> ValueError")
check(leve(I.test_z, 105.0, 100.0, 0.0, 36), "test_z σ=0 -> ValueError")
check(leve(I.test_z, 105.0, 100.0, -5.0, 36), "test_z σ<0 -> ValueError")
check(leve(I.test_z, True, 100.0, 15.0, 36), "test_z moyenne bool -> ValueError")
check(leve(I.test_z, 105.0, 100.0, 15.0, 36, bilateral="oui"), "test_z bilateral non-bool -> ValueError")
check(leve(I.test_z, 105.0, 100.0, 15.0, 3.0), "test_z n float -> ValueError")

# ── 14) SOUNDNESS — test_t_student ──
check(leve(I.test_t_student, [5.0], 0.0), "test_t n<2 -> ValueError")
check(leve(I.test_t_student, [3.0, 3.0, 3.0], 0.0), "test_t variance nulle -> ValueError")
check(leve(I.test_t_student, 5.0, 0.0), "test_t échantillon non-séquence -> ValueError")
check(leve(I.test_t_student, [1.0, float("nan")], 0.0), "test_t NaN dans échantillon -> ValueError")

# ── 15) SOUNDNESS — khi-deux ──
check(leve(I.test_khi2_conformite, [10, 10, 10], [2, 10, 10]), "χ² attendu 2 (<5) -> ValueError")
check(leve(I.test_khi2_conformite, [10, 10], [10, 10, 10]), "χ² longueurs différentes -> ValueError")
check(leve(I.test_khi2_conformite, [-1, 10, 10], [10, 10, 10]), "χ² observé négatif -> ValueError")
check(leve(I.test_khi2_conformite, [10], [10]), "χ² une seule catégorie -> ValueError")

# ── 16) SOUNDNESS — IC ──
check(leve(I.ic_moyenne_sigma_connu, 105.0, 15.0, 36, 1.5), "IC niveau>1 -> ValueError")
check(leve(I.ic_moyenne_sigma_connu, 105.0, 15.0, 36, 0.0), "IC niveau=0 -> ValueError")
check(leve(I.ic_moyenne_sigma_connu, 105.0, -1.0, 36, 0.95), "IC σ<0 -> ValueError")
check(leve(I.ic_moyenne_sigma_inconnu, [5.0, 5.0], 0.95), "IC Student variance nulle -> ValueError")
check(leve(I.ic_proportion_wilson, 11, 10, 0.95), "Wilson succes>n -> ValueError")
check(leve(I.ic_proportion_wilson, -1, 10, 0.95), "Wilson succes<0 -> ValueError")
check(leve(I.ic_proportion_wilson, 3, 10, 1.2), "Wilson niveau>1 -> ValueError")
check(leve(I.ic_proportion_wilson, 3.0, 10, 0.95), "Wilson succes float -> ValueError")

# ── 17) SOUNDNESS — interprete ──
check(leve(I.interprete, 1.5, 0.05), "interprete p>1 -> ValueError")
check(leve(I.interprete, -0.1, 0.05), "interprete p<0 -> ValueError")
check(leve(I.interprete, 0.01, 0.0), "interprete α=0 -> ValueError")
check(leve(I.interprete, 0.01, 1.0), "interprete α=1 -> ValueError")
check(leve(I.interprete, True, 0.05), "interprete p bool -> ValueError")

print(f"\n=== valide_inference_classique : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
