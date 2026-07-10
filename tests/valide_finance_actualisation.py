"""
VALIDE finance_actualisation.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (valeurs connues ou calculées À LA MAIN, jamais recalculées par la fonction testée) :
  • VAN [-1000, 500, 500, 500] à 10 % = -1000 + 500/1.1 + 500/1.21 + 500/1.331 (puissances de 1.1 posées à la
    main : 1.1² = 1.21, 1.1³ = 1.331) = 243.4259954... ≈ 243.4260 — arithmétique écrite EN DUR dans la gate.
  • TRI de [-100, 110] = 10 % EXACTEMENT : VAN(0.1) = -100 + 110/1.1 = -100 + 100 = 0 (vérifiable de tête).
  • TRI de [-1000, 500, 500, 500] ≈ 23.375 % (racine de x³+x²+x = 2, x = 1/(1+i)) ; encadrement à la main :
    VAN(0.23) = -1000 + 500/1.23 + 500/1.5129 + 500/1.860867 ≈ +5.69 > 0 et
    VAN(0.24) = -1000 + 500/1.24 + 500/1.5376 + 500/1.906624 ≈ -9.35 < 0  -> racine dans ]0.23, 0.24[.
  • TRI NON UNIQUE : [-1, 5, -6] a DEUX changements de signe ; les deux racines de -1+5x-6x² = 0 sont
    x = 1/2 et x = 1/3, soit i = 100 % et i = 200 % (résolu à la main : 6x²-5x+1 = (2x-1)(3x-1)) ->
    ABSTENTION obligatoire (ancre d'abstention capitale).
  • Annuité 100 000 à 5 % sur 20 ans = 8 024.26 €/an (valeur bancaire standard, ±0.01).
  • Mensualité 1 200 à 1 %/mois sur 12 mois ≈ 106.6185 (1.01¹² = 1.126825030 : constante bancaire classique).
  • Taux actuariel d'un nominal 12 % capitalisé mensuellement = 1.01¹² − 1 = 12.6825030 % (constante bancaire).
  • Taux actuariel d'un nominal 10 % semestriel = 1.05² − 1 = 0.1025 EXACT (1.05² = 1.1025 à la main).
  • Taux semestriel équivalent à 10 % annuel = √1.1 − 1 ≈ 0.04880884817 ; SECOND CHEMIN : (1+r)² doit
    redonner 1.1 (mise au carré = chemin de code indépendant de la racine).
  • Amortissement : Σ principaux = capital emprunté (chemin indépendant : addition des lignes) ; 1ʳᵉ ligne
    d'intérêt = capital × taux (produit posé à la main).

SOUNDNESS : bool/str/NaN/±inf, taux ≤ −1, n ≤ 0 ou non entier, capital ≤ 0, flux vide/même signe/multi-signes,
tol hors ]0, 0.1] -> ValueError. DÉTERMINISME : deux appels identiques -> résultats égaux.
"""
import math

import finance_actualisation as F

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


def message(fn, *a):
    """Le message du ValueError levé, ou None si rien n'est levé."""
    try:
        fn(*a)
        return None
    except ValueError as e:
        return str(e)


def proche(x, attendu, tol=1e-6):
    return x is not None and abs(x - attendu) <= tol


# ── 1) VAN — ancre arithmétique à la main ──
# -1000 + 500/1.1 + 500/1.21 + 500/1.331 (1.1²=1.21, 1.1³=1.331 posés à la main), soit
# -1000 + 454.5454545 + 413.2231405 + 375.6574004 = 243.4259954
VAN_MAIN = -1000.0 + 500.0 / 1.1 + 500.0 / 1.21 + 500.0 / 1.331   # arithmétique indépendante de F.van
check(proche(F.van([-1000, 500, 500, 500], 0.10), VAN_MAIN, tol=1e-6),
      "VAN [-1000,500,500,500] @10% = calcul à la main (243.4259954...)")
check(proche(F.van([-1000, 500, 500, 500], 0.10), 243.4260, tol=1e-3),
      "VAN [-1000,500,500,500] @10% ≈ 243.4260 (valeur en dur)")
# VAN(0.1) de [-100, 110] = -100 + 110/1.1 = 0 (de tête)
check(proche(F.van([-100, 110], 0.10), 0.0, tol=1e-9), "VAN [-100,110] @10% = 0 (110/1.1 = 100)")
# 121/1.21 = 100 (1.1² = 1.21 à la main)
check(proche(F.van([0, 0, 121], 0.10), 100.0, tol=1e-9), "VAN [0,0,121] @10% = 100 (121/1.21)")
# F_0 seul : pas d'actualisation au temps 0
check(proche(F.van([100], 0.05), 100.0), "VAN [100] = 100 (t=0 non actualisé)")
# taux nul : VAN = somme brute
check(proche(F.van([-50, 30, 30], 0.0), 10.0), "VAN @0% = somme des flux (10)")
check(proche(F.van([-1000, 500, 500, 500], 0.0), 500.0), "VAN @0% [-1000,500×3] = 500")

# ── 2) TRI — ancre EXACTE [-100, 110] -> 10 % ──
r = F.tri([-100, 110])
check(proche(r["valeur"], 0.10, tol=1e-8), "TRI [-100,110] ≈ 0.10 (ancre exacte VAN(0.1)=0)")
check(r["lo"] <= 0.10 <= r["hi"], "0.10 est DANS l'encadrement [lo, hi]")
check(r["hi"] - r["lo"] <= 1e-9, "largeur d'encadrement ≤ tol (1e-9 par défaut)")
check(r["approchee"] is True, "TRI marqué approché (approchee=True)")
# flux miroir (prêt puis remboursement) : 100 - 110/1.1 = 0 -> TRI = 10 % aussi
r_miroir = F.tri([100, -110])
check(proche(r_miroir["valeur"], 0.10, tol=1e-8), "TRI [100,-110] ≈ 0.10 (1 changement de signe, sens inverse)")

# ── 3) TRI — [-1000, 500, 500, 500] ≈ 23.375 % ──
# Encadrement à la main : VAN(0.23) ≈ +5.69 > 0 ; VAN(0.24) ≈ -9.35 < 0 (dénominateurs 1.23, 1.5129=1.23²,
# 1.860867=1.23³ et 1.24, 1.5376=1.24², 1.906624=1.24³ posés à la main) -> racine dans ]0.23, 0.24[.
r3 = F.tri([-1000, 500, 500, 500])
check(0.23 < r3["valeur"] < 0.24, "TRI [-1000,500×3] dans ]0.23, 0.24[ (encadrement à la main)")
check(proche(r3["valeur"], 0.23375, tol=5e-5), "TRI [-1000,500×3] ≈ 23.375 % (ancre de l'énoncé)")
check(r3["hi"] - r3["lo"] <= 1e-9, "largeur encadrement TRI ≤ 1e-9")
check(r3["lo"] <= r3["valeur"] <= r3["hi"], "valeur dans [lo, hi]")
check(r3["approchee"] is True, "TRI marqué approché")
# SECOND CHEMIN : la VAN (fonction distincte de la bissection) change bien de signe entre lo et hi
van_lo = F.van([-1000, 500, 500, 500], r3["lo"])
van_hi = F.van([-1000, 500, 500, 500], r3["hi"])
check(van_lo * van_hi <= 0.0, "VAN(lo) et VAN(hi) de signes opposés (encadrement prouvé par F.van)")
# tol explicite plus lâche : largeur respectée
r3b = F.tri([-1000, 500, 500, 500], 1e-6)
check(r3b["hi"] - r3b["lo"] <= 1e-6, "tol=1e-6 : largeur ≤ 1e-6")
check(r3b["lo"] <= r3["valeur"] <= r3b["hi"], "l'encadrement lâche contient la racine fine")

# ── 4) TRI — ABSTENTIONS D'EXISTENCE/UNICITÉ (le cœur FAUX=0) ──
# [-1, 5, -6] : 2 changements de signe ; racines à la main 6x²-5x+1=(2x-1)(3x-1) -> i=100 % ET i=200 %.
check(leve(F.tri, [-1, 5, -6]), "TRI [-1,5,-6] (2 racines : 100 % et 200 %) -> ValueError")
m = message(F.tri, [-1, 5, -6])
check(m is not None and "2 changements de signe" in m and "arbitraire" in m,
      "message exact : 'TRI non unique : 2 changements de signe, la valeur serait arbitraire'")
# 3 changements de signe
m3 = message(F.tri, [-1, 3, -3, 1])
check(m3 is not None and "3 changements de signe" in m3, "3 changements de signe détectés et refusés")
# aucun changement de signe : TRI inexistant
check(leve(F.tri, [-100, -50]), "flux tous négatifs -> ValueError (TRI inexistant)")
check(leve(F.tri, [100, 50, 25]), "flux tous positifs -> ValueError (TRI inexistant)")
check(leve(F.tri, [0.0, 0.0]), "flux tous nuls -> ValueError")
check(leve(F.tri, [-100]), "flux unique -> ValueError (aucun changement de signe)")
# les zéros sont ignorés dans le comptage : [-100, 0, 110] = 1 changement -> TRI calculé
r0 = F.tri([-100, 0, 121])   # -100 + 121/(1+i)² = 0 -> (1+i)² = 1.21 -> i = 10 % (1.1²=1.21 à la main)
check(proche(r0["valeur"], 0.10, tol=1e-8), "TRI [-100,0,121] = 10 % (zéro ignoré, 1.21=1.1²)")

# ── 5) ANNUITÉ CONSTANTE — ancre bancaire ──
check(proche(F.annuite_constante(100000, 0.05, 20), 8024.26, tol=0.01),
      "annuité 100000 @5% 20 ans = 8024.26 (valeur bancaire standard)")
check(proche(F.annuite_constante(1200, 0.01, 12), 106.6185, tol=1e-3),
      "mensualité 1200 @1%/mois 12 mois ≈ 106.6185 (1.01^12=1.126825030)")
check(proche(F.annuite_constante(1000, 0.0, 4), 250.0), "annuité à taux nul = capital/n (250, exact)")
# sanité indépendante : à taux > 0, le total payé excède le capital (les intérêts sont positifs)
check(F.annuite_constante(100000, 0.05, 20) * 20 > 100000, "total payé (20 annuités) > capital à taux > 0")
# emprunt 1 période : a = C(1+i) -> 1000 @10% -> 1100 (produit posé à la main)
check(proche(F.annuite_constante(1000, 0.10, 1), 1100.0, tol=1e-6), "annuité 1 période = C(1+i) = 1100")

# ── 6) TABLEAU D'AMORTISSEMENT — invariants (chemins indépendants) ──
tab = F.tableau_amortissement(100000, 0.05, 20)
check(len(tab) == 20, "tableau : 20 lignes")
# Σ principaux = capital (chemin indépendant : addition des lignes)
somme_principaux = sum(p for (_, p, _) in tab)
check(proche(somme_principaux, 100000.0, tol=1e-5), "Σ principaux = capital emprunté (100000)")
# invariant dur : restant final nul à 1e-6
check(abs(tab[-1][2]) <= 1e-6, "restant final = 0 à 1e-6 près")
# 1ʳᵉ ligne : intérêt = 100000 × 0.05 = 5000 (produit à la main)
check(proche(tab[0][0], 5000.0, tol=1e-9), "intérêt 1ʳᵉ échéance = 5000 (100000×0.05)")
# 1ʳᵉ ligne : principal = annuité − 5000 ≈ 8024.2587 − 5000 = 3024.2587
check(proche(tab[0][1], 3024.2587, tol=1e-3), "principal 1ʳᵉ échéance ≈ 3024.2587 (8024.2587−5000)")
# chaque ligne : intérêt + principal = annuité constante (8024.26 ±0.01, ancre bancaire)
check(all(proche(i + p, 8024.26, tol=0.01) for (i, p, _) in tab),
      "intérêt+principal = annuité constante sur TOUTES les lignes")
# monotonies : intérêts décroissants, principaux croissants, restants décroissants
check(all(tab[k][0] > tab[k + 1][0] for k in range(19)), "intérêts strictement décroissants")
check(all(tab[k][1] < tab[k + 1][1] for k in range(19)), "principaux strictement croissants")
check(all(tab[k][2] > tab[k + 1][2] for k in range(19)), "capital restant strictement décroissant")
# cas 1 période : 1000 @10% -> intérêt 100, principal 1000, restant 0 (tout à la main)
tab1 = F.tableau_amortissement(1000, 0.10, 1)
check(len(tab1) == 1 and proche(tab1[0][0], 100.0) and proche(tab1[0][1], 1000.0)
      and abs(tab1[0][2]) <= 1e-6, "tableau 1 période : (100, 1000, 0)")
# taux nul : 900 sur 3 -> principal 300 constant, restants 600/300/0 (à la main)
tab0 = F.tableau_amortissement(900, 0.0, 3)
check(all(proche(i, 0.0) for (i, _, _) in tab0), "taux nul : intérêt = 0 partout")
check(proche(tab0[0][2], 600.0) and proche(tab0[1][2], 300.0) and abs(tab0[2][2]) <= 1e-6,
      "taux nul : restants 600, 300, 0")

# ── 7) TAUX ÉQUIVALENT / ACTUARIEL — constantes bancaires ──
check(proche(F.taux_actuariel(0.12, 12), 0.126825030, tol=1e-8),
      "taux actuariel nominal 12 % mensuel = 12.6825030 % (1.01^12−1, constante bancaire)")
check(proche(F.taux_actuariel(0.10, 2), 0.1025, tol=1e-10),
      "taux actuariel nominal 10 % semestriel = 0.1025 EXACT (1.05²=1.1025)")
check(proche(F.taux_actuariel(0.08, 1), 0.08), "p=1 : taux actuariel = taux nominal")
te = F.taux_equivalent(0.10, 2)
check(proche(te, 0.04880884817, tol=1e-9), "taux semestriel équivalent à 10 % = √1.1−1 ≈ 0.04880884817")
# SECOND CHEMIN : remettre au carré doit redonner 1.1 (chemin indépendant de la racine)
check(proche((1.0 + te) ** 2, 1.10, tol=1e-9), "(1+taux_équivalent)² = 1.1 (vérif par mise au carré)")
check(proche(F.taux_equivalent(0.1025, 2), 0.05, tol=1e-9),
      "taux semestriel équivalent à 10.25 % = 5 % (1.05²=1.1025 à la main)")
check(proche(F.taux_equivalent(0.10, 1), 0.10), "p=1 : taux équivalent = taux annuel")
# aller-retour équivalent<->actuariel sur l'ancre bancaire 1 %/mois
check(proche(F.taux_equivalent(0.126825030, 12), 0.01, tol=1e-8),
      "taux mensuel équivalent à 12.6825030 % = 1 % (constante bancaire)")
# taux négatif légal (> -1) : (0.9)² − 1... équivalent semestriel de −19 % : √0.81−1 = −0.10 (0.9²=0.81)
check(proche(F.taux_equivalent(-0.19, 2), -0.10, tol=1e-9), "taux équivalent négatif : √0.81−1 = −0.10")

# ── 8) SOUNDNESS — taux ≤ −1 ──
check(leve(F.van, [-100, 110], -1.0), "van taux=-1 -> ValueError")
check(leve(F.van, [-100, 110], -1.5), "van taux<-1 -> ValueError")
check(leve(F.annuite_constante, 1000, -1.0, 5), "annuité taux=-1 -> ValueError")
check(leve(F.tableau_amortissement, 1000, -2.0, 5), "tableau taux<-1 -> ValueError")
check(leve(F.taux_equivalent, -1.0, 2), "taux_equivalent taux=-1 -> ValueError")
check(leve(F.taux_actuariel, -2.0, 2), "taux_actuariel i_n/p ≤ -1 -> ValueError")

# ── 9) SOUNDNESS — n / périodes ──
check(leve(F.annuite_constante, 1000, 0.05, 0), "n=0 -> ValueError")
check(leve(F.annuite_constante, 1000, 0.05, -3), "n<0 -> ValueError")
check(leve(F.annuite_constante, 1000, 0.05, 2.5), "n non entier -> ValueError")
check(leve(F.tableau_amortissement, 1000, 0.05, 0), "tableau n=0 -> ValueError")
check(leve(F.taux_equivalent, 0.10, 0), "périodes=0 -> ValueError")
check(leve(F.taux_actuariel, 0.10, -1), "périodes<0 -> ValueError")

# ── 10) SOUNDNESS — capital ──
check(leve(F.annuite_constante, 0, 0.05, 10), "capital=0 -> ValueError")
check(leve(F.annuite_constante, -1000, 0.05, 10), "capital<0 -> ValueError")
check(leve(F.tableau_amortissement, 0.0, 0.05, 10), "tableau capital=0 -> ValueError")

# ── 11) SOUNDNESS — flux ──
check(leve(F.van, [], 0.10), "flux vide -> ValueError")
check(leve(F.van, "flux", 0.10), "flux str -> ValueError")
check(leve(F.van, 100, 0.10), "flux non-séquence -> ValueError")
check(leve(F.van, [-100, "110"], 0.10), "flux avec str -> ValueError")
check(leve(F.van, [-100, True], 0.10), "flux avec bool -> ValueError")
check(leve(F.van, [-100, float("nan")], 0.10), "flux avec NaN -> ValueError")
check(leve(F.van, [-100, float("inf")], 0.10), "flux avec inf -> ValueError")
check(leve(F.tri, [], 1e-9), "tri flux vide -> ValueError")
check(leve(F.tri, [-100, float("-inf")]), "tri flux avec -inf -> ValueError")

# ── 12) SOUNDNESS — types (bool/str/NaN/inf) sur les scalaires ──
check(leve(F.van, [-100, 110], True), "taux bool -> ValueError")
check(leve(F.van, [-100, 110], "0.1"), "taux str -> ValueError")
check(leve(F.van, [-100, 110], float("nan")), "taux NaN -> ValueError")
check(leve(F.van, [-100, 110], float("inf")), "taux inf -> ValueError")
check(leve(F.annuite_constante, True, 0.05, 10), "capital bool -> ValueError")
check(leve(F.annuite_constante, float("nan"), 0.05, 10), "capital NaN -> ValueError")
check(leve(F.annuite_constante, 1000, float("inf"), 10), "taux inf (annuité) -> ValueError")
check(leve(F.annuite_constante, 1000, 0.05, True), "n bool -> ValueError")
check(leve(F.taux_equivalent, float("nan"), 2), "taux_equivalent NaN -> ValueError")
check(leve(F.taux_equivalent, "0.1", 2), "taux_equivalent str -> ValueError")
check(leve(F.taux_actuariel, float("inf"), 2), "taux_actuariel inf -> ValueError")
check(leve(F.taux_actuariel, 0.10, True), "périodes bool -> ValueError")

# ── 13) SOUNDNESS — tol du TRI ──
check(leve(F.tri, [-100, 110], 0.0), "tol=0 -> ValueError")
check(leve(F.tri, [-100, 110], -1e-9), "tol<0 -> ValueError")
check(leve(F.tri, [-100, 110], 0.5), "tol>0.1 -> ValueError")
check(leve(F.tri, [-100, 110], True), "tol bool -> ValueError")
check(leve(F.tri, [-100, 110], float("nan")), "tol NaN -> ValueError")

# ── 14) DÉTERMINISME ──
check(F.van([-1000, 500, 500, 500], 0.10) == F.van([-1000, 500, 500, 500], 0.10), "déterminisme van")
check(F.tri([-1000, 500, 500, 500]) == F.tri([-1000, 500, 500, 500]), "déterminisme tri (dict complet)")
check(F.annuite_constante(100000, 0.05, 20) == F.annuite_constante(100000, 0.05, 20), "déterminisme annuité")
check(F.tableau_amortissement(1000, 0.10, 5) == F.tableau_amortissement(1000, 0.10, 5), "déterminisme tableau")
check(F.taux_equivalent(0.10, 2) == F.taux_equivalent(0.10, 2), "déterminisme taux_equivalent")
check(F.taux_actuariel(0.12, 12) == F.taux_actuariel(0.12, 12), "déterminisme taux_actuariel")

print(f"\n=== valide_finance_actualisation : {ok}/{ok+ko} ===")
import sys; sys.exit(0 if ko == 0 else 1)
