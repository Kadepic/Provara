"""
VALIDE mesures_sociales.py — held-out ADVERSE.

Ancres = valeurs CALCULÉES INDÉPENDAMMENT (non re-dérivées par le module) :
  • Gini ancré sur la DOUBLE SOMME des écarts absolus  G = Σ_iΣ_j|x_i−x_j| / (2n²x̄)  (algorithme distinct
    de la formule des rangs employée par le module — vérification non circulaire) ;
  • Gini d'une distribution constante = 0 ; Gini de [0,…,0,c] = (n−1)/n posé à la main ;
  • invariance par permutation et par mise à l'échelle positive ;
  • Lorenz : aire trapézoïdale posée à la main (quintiles 0.05/0.15/0.30/0.55/1.0 -> 0.38) ;
  • seuil de pauvreté 60 % / 50 % posé numériquement ; médiane pair/impair ;
  • IDH = racine cubique du produit, et propriété IDH ≤ min des sous-indices.
+ SOUNDNESS (revenu négatif, total nul, liste vide, population ≤ 0, pauvres > population, effectif non entier,
  fraction ∉ (0,1], médian négatif, Lorenz mal formée, bornes invalides, sous-indice ∉ [0,1],
  non numérique / booléen / non fini -> ValueError)
+ DÉTERMINISME.
"""
import math
import mesures_sociales as S

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
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception as e:  # toute autre exception = échec de soundness
        print(f"  (exception inattendue {type(e).__name__}: {e})")
        return False


def gini_double_somme(x):
    """Gini par la DOUBLE SOMME des écarts absolus — algorithme INDÉPENDANT de la formule des rangs."""
    n = len(x)
    moy = sum(x) / n
    s = 0.0
    for xi in x:
        for xj in x:
            s += abs(xi - xj)
    return s / (2 * n * n * moy)


# ── 1) GINI — ancré sur l'algorithme indépendant (double somme) ──
for ech in ([1, 2], [3, 7, 9], [2, 4, 4, 8, 10], [100, 200, 300, 400], [5, 5, 6, 1000], [1, 1, 1, 1, 1, 9]):
    attendu = gini_double_somme(ech)
    check(abs(S.gini(ech) - attendu) < 1e-12, f"gini {ech} == double-somme {attendu:.6f}")

# ── 2) GINI — bornes structurelles ──
check(S.gini([10, 10, 10]) == 0.0, "gini distribution constante = 0")
check(S.gini([7]) == 0.0, "gini d'un seul individu = 0")
check(abs(S.gini([0, 0, 0, 10]) - 3 / 4) < 1e-12, "gini [0,0,0,c] = (n-1)/n = 0.75")
check(abs(S.gini([0, 0, 0, 0, 0, 99]) - 5 / 6) < 1e-12, "gini concentration max n=6 -> 5/6")
check(0.0 <= S.gini([3, 1, 4, 1, 5, 9, 2, 6]) < 1.0, "gini ∈ [0,1)")

# ── 3) GINI — invariances (propriétés non circulaires) ──
check(abs(S.gini([1, 2, 3, 4]) - S.gini([4, 1, 3, 2])) < 1e-12, "gini invariant par permutation")
check(abs(S.gini([1, 2, 3, 4]) - S.gini([10, 20, 30, 40])) < 1e-12, "gini invariant par mise à l'échelle (×10)")
check(abs(S.gini([2, 5, 9]) - S.gini([2000, 5000, 9000])) < 1e-12, "gini invariant par mise à l'échelle (×1000)")
check(S.gini([1, 2]) > 0.0, "gini distribution inégale > 0")
check(S.gini([1, 100]) > S.gini([1, 2]), "gini croît avec l'inégalité")

# ── 4) COEFFICIENT_GINI (Lorenz) — aire trapézoïdale posée à la main ──
check(S.coefficient_gini([0.2, 0.4, 0.6, 0.8, 1.0]) == 0.0, "Lorenz diagonale -> Gini 0")
check(abs(S.coefficient_gini([0.05, 0.15, 0.30, 0.55, 1.0]) - 0.38) < 1e-12, "Lorenz quintiles -> 0.38")
check(abs(S.coefficient_gini([0.0, 1.0]) - 0.5) < 1e-12, "Lorenz 2 groupes [0,1] -> 0.5 = (n-1)/n")
check(abs(S.coefficient_gini([1.0]) - 0.0) < 1e-12, "Lorenz 1 groupe -> 0")
check(0.0 <= S.coefficient_gini([0.1, 0.25, 0.45, 0.7, 1.0]) < 1.0, "coefficient_gini ∈ [0,1)")

# ── 5) TAUX & SEUIL DE PAUVRETÉ ──
check(S.taux_pauvrete(15, 100) == 0.15, "taux pauvreté 15/100")
check(S.taux_pauvrete(0, 50) == 0.0, "taux pauvreté 0/50 = 0")
check(S.taux_pauvrete(50, 50) == 1.0, "taux pauvreté 50/50 = 1")
check(S.seuil_pauvrete(20000) == 12000.0, "seuil 60 % de 20000 = 12000")
check(S.seuil_pauvrete(25000, 0.6) == 15000.0, "seuil 60 % de 25000 = 15000")
check(S.seuil_pauvrete(2000, 0.5) == 1000.0, "seuil OCDE 50 % de 2000 = 1000")
check(S.seuil_pauvrete(1000, 0.4) == 400.0, "seuil OCDE 40 % de 1000 = 400")
check(S.seuil_pauvrete(0) == 0.0, "seuil de médian 0 = 0")

# ── 6) MÉDIANE ──
check(S.mediane([1, 2, 3]) == 2.0, "médiane impaire = centrale")
check(S.mediane([1, 2, 3, 4]) == 2.5, "médiane paire = moyenne des 2 centrales")
check(S.mediane([7]) == 7.0, "médiane singleton")
check(S.mediane([5, 1, 3, 2, 4]) == 3.0, "médiane non triée")

# ── 7) INDICE DE DIMENSION & IDH ──
check(S.indice_dimension(50, 0, 100) == 0.5, "dimension (50-0)/(100-0)=0.5")
check(S.indice_dimension(0, 0, 100) == 0.0, "dimension valeur=min -> 0")
check(S.indice_dimension(100, 0, 100) == 1.0, "dimension valeur=max -> 1")
check(abs(S.indice_dimension(75, 25, 85) - (75 - 25) / (85 - 25)) < 1e-12, "dimension bornes décalées")
check(abs(S.idh(0.8, 0.8, 0.8) - 0.8) < 1e-12, "IDH égal = 0.8")
check(S.idh(1.0, 1.0, 1.0) == 1.0, "IDH parfait = 1")
check(S.idh(0.0, 0.5, 0.9) == 0.0, "IDH avec un zéro = 0 (moyenne géométrique)")
check(abs(S.idh(0.729, 0.729, 0.729) - 0.729) < 1e-12, "IDH cube parfait")
check(abs(S.idh(0.2, 0.5, 0.8) - (0.2 * 0.5 * 0.8) ** (1 / 3)) < 1e-12, "IDH = racine cubique du produit")
check(min(0.4, 0.6, 0.9) - 1e-12 <= S.idh(0.4, 0.6, 0.9) <= max(0.4, 0.6, 0.9) + 1e-12, "IDH ∈ [min, max] des sous-indices")
check(S.idh(0.3, 0.9, 0.9) < (0.3 + 0.9 + 0.9) / 3 + 1e-12, "IDH géométrique <= moyenne arithmétique (pénalise déséquilibre)")

# ── 8) SOUNDNESS — Gini ──
check(_leve_v(S.gini, []), "gini liste vide -> ValueError")
check(_leve_v(S.gini, [-1, 2, 3]), "gini revenu négatif -> ValueError")
check(_leve_v(S.gini, [0, 0, 0]), "gini total nul -> ValueError")
check(_leve_v(S.gini, [1, 2, float("nan")]), "gini NaN -> ValueError")
check(_leve_v(S.gini, [1, 2, float("inf")]), "gini inf -> ValueError")
check(_leve_v(S.gini, [1, True, 3]), "gini booléen -> ValueError")
check(_leve_v(S.gini, [1, "2", 3]), "gini str dans liste -> ValueError")
check(_leve_v(S.gini, "123"), "gini chaîne -> ValueError")
check(_leve_v(S.gini, 42), "gini scalaire non itérable -> ValueError")

# ── 9) SOUNDNESS — coefficient_gini (Lorenz) ──
check(_leve_v(S.coefficient_gini, []), "coefficient_gini vide -> ValueError")
check(_leve_v(S.coefficient_gini, [0.2, 0.4]), "coefficient_gini dernière != 1 -> ValueError")
check(_leve_v(S.coefficient_gini, [0.5, 0.3, 1.0]), "coefficient_gini non croissante -> ValueError")
check(_leve_v(S.coefficient_gini, [-0.1, 0.5, 1.0]), "coefficient_gini part < 0 -> ValueError")
check(_leve_v(S.coefficient_gini, [0.5, 1.2, 1.0]), "coefficient_gini part > 1 -> ValueError")
check(_leve_v(S.coefficient_gini, [0.2, 0.4, float("nan")]), "coefficient_gini NaN -> ValueError")

# ── 10) SOUNDNESS — taux & seuil ──
check(_leve_v(S.taux_pauvrete, 150, 100), "taux pauvres > population -> ValueError")
check(_leve_v(S.taux_pauvrete, 10, 0), "taux population 0 -> ValueError")
check(_leve_v(S.taux_pauvrete, 10, -5), "taux population négative -> ValueError")
check(_leve_v(S.taux_pauvrete, -1, 100), "taux effectif négatif -> ValueError")
check(_leve_v(S.taux_pauvrete, 1.5, 100), "taux effectif non entier -> ValueError")
check(_leve_v(S.taux_pauvrete, True, 100), "taux effectif booléen -> ValueError")
check(_leve_v(S.seuil_pauvrete, -1), "seuil médian négatif -> ValueError")
check(_leve_v(S.seuil_pauvrete, 1000, 0), "seuil fraction 0 -> ValueError")
check(_leve_v(S.seuil_pauvrete, 1000, -0.5), "seuil fraction négative -> ValueError")
check(_leve_v(S.seuil_pauvrete, 1000, 1.5), "seuil fraction > 1 -> ValueError")
check(_leve_v(S.seuil_pauvrete, float("inf")), "seuil médian inf -> ValueError")
check(_leve_v(S.seuil_pauvrete, "1000"), "seuil médian str -> ValueError")

# ── 11) SOUNDNESS — médiane / dimension / IDH ──
check(_leve_v(S.mediane, []), "médiane vide -> ValueError")
check(_leve_v(S.mediane, [1, None, 3]), "médiane None dans liste -> ValueError")
check(_leve_v(S.indice_dimension, 5, 10, 10), "dimension max == min -> ValueError")
check(_leve_v(S.indice_dimension, 5, 100, 10), "dimension max < min -> ValueError")
check(_leve_v(S.indice_dimension, 150, 0, 100), "dimension valeur > max -> ValueError")
check(_leve_v(S.indice_dimension, -5, 0, 100), "dimension valeur < min -> ValueError")
check(_leve_v(S.idh, 1.2, 0.5, 0.5), "IDH sous-indice > 1 -> ValueError")
check(_leve_v(S.idh, -0.1, 0.5, 0.5), "IDH sous-indice < 0 -> ValueError")
check(_leve_v(S.idh, 0.5, float("nan"), 0.5), "IDH NaN -> ValueError")
check(_leve_v(S.idh, 0.5, True, 0.5), "IDH booléen -> ValueError")

# ── 12) DÉTERMINISME — fonctions pures ──
check(S.gini([3, 1, 4, 1, 5]) == S.gini([3, 1, 4, 1, 5]), "gini déterministe")
check([S.coefficient_gini([0.05, 0.15, 0.30, 0.55, 1.0]) for _ in range(5)] == [0.38] * 5, "coefficient_gini 5 appels identiques")
check(S.idh(0.4, 0.6, 0.9) == S.idh(0.4, 0.6, 0.9), "IDH déterministe")
check(S.seuil_pauvrete(20000) == S.seuil_pauvrete(20000), "seuil déterministe")

# ── 13) PREUVE auto-portée intégrée ──
check(S._p_mesures_sociales() is True, "_p_mesures_sociales() == True")

print(f"\n=== valide_mesures_sociales : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
