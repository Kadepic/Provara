"""
VALIDE mobilite_sociale.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (valeurs connues ou calculées À LA MAIN, PAS recalculées par le code testé) :
  • MOBILITÉ PARFAITE (indépendance statistique) : matrice dont toutes les lignes sont identiques ->
    TOUS les odds ratios valent 1 EXACTEMENT (théorème : sous indépendance, les chances relatives sont
    égales, OR = 1). Ancre théorique forte, indépendante de l'implémentation.
  • IMMOBILITÉ TOTALE : matrice diagonale -> taux_immobilite = 1, ascendante = descendante = 0 (évident
    par définition, aucune cellule hors diagonale).
  • Matrice [[80,20],[20,80]] : immobilité = 160/200 = 0.8 ; OR = (80·80)/(20·20) = 6400/400 = 16
    (calculé à la main) ; ascendante = descendante = 20/200 = 1/10.
  • Matrice 3×3 [[50,30,20],[20,50,30],[10,30,60]] (total 300, à la main) : diagonale 50+50+60 = 160 ->
    immobilité 160/300 = 8/15 ; au-dessus 30+20+30 = 80 -> 80/300 = 4/15 ; au-dessous 20+10+30 = 60 ->
    60/300 = 1/5 ; OR(0,1) = 2500/600 = 25/6 ; OR(1,2) = 3000/900 = 10/3 ; OR(0,2) = 3000/200 = 15.
  • INVARIANCE AUX MARGES (le point théorique) : [[70,30],[20,80]] -> OR = 5600/600 = 28/3 ; on double la
    ligne 0 -> [[140,60],[20,80]] : OR = 11200/1200 = 28/3 INCHANGÉ, mais l'immobilité brute passe de
    150/200 = 3/4 à 220/300 = 11/15 (les taux bruts confondent structure et fluidité, pas l'OR) ; idem en
    triplant la colonne 1 -> [[70,90],[20,240]] : OR = 16800/1800 = 28/3.
  • ÉLASTICITÉ : y_enfant = y_parent^0.5 exactement (parents 1,4,16,64 -> enfants 1,2,4,8) : la pente
    log-log vaut 0.5 (construction exacte, vérifiable à la main : log(y_e) = 0.5·log(y_p)) à 1e-9 près.
    y_enfant = 3·y_parent -> pente 1 (reproduction totale) ; y_enfant constant -> pente 0 (mobilité
    parfaite) ; y_enfant = 1/y_parent -> pente −1 et corrélation −1 ; 2 points (1, e) -> (2, 2·e^0.4) :
    logs (0,1) -> (ln2, ln2+0.4), pente = 0.4 à la main.

SOUNDNESS : matrice non carrée, effectif négatif/float/bool, ligne nulle, classes dupliquées ou < 2,
odds_ratio i==j / hors bornes / cellule croisée nulle, listes de tailles différentes, revenus ≤ 0,
NaN/inf/str/bool, variance nulle -> ValueError. DÉTERMINISME : deux appels = même résultat.
"""
import math
from fractions import Fraction

import mobilite_sociale as M

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


CL2 = ["ouvriers", "cadres"]
CL3 = ["populaire", "moyenne", "superieure"]

# ── 1) ANCRE THÉORIQUE : indépendance (lignes identiques) -> TOUS les OR = 1 EXACTEMENT ──
indep = M.MatriceTransition(CL3, [[10, 20, 30], [10, 20, 30], [10, 20, 30]])
check(indep.odds_ratio(0, 1) == Fraction(1), "indépendance : OR(0,1) = 1 exactement")
check(indep.odds_ratio(0, 2) == Fraction(1), "indépendance : OR(0,2) = 1 exactement")
check(indep.odds_ratio(1, 2) == Fraction(1), "indépendance : OR(1,2) = 1 exactement")
# matrice ligne de l'indépendance : chaque ligne = (10/60, 20/60, 30/60) = (1/6, 1/3, 1/2), à la main
ml = indep.matrice_ligne()
check(ml[0] == (Fraction(1, 6), Fraction(1, 3), Fraction(1, 2)), "P(dest|origine 0) = (1/6, 1/3, 1/2)")
check(ml[2] == (Fraction(1, 6), Fraction(1, 3), Fraction(1, 2)), "P(dest|origine 2) = (1/6, 1/3, 1/2)")
check(all(sum(ligne) == 1 for ligne in ml), "invariant : chaque ligne de probas somme à 1 exactement")

# ── 2) ANCRE : immobilité totale (matrice diagonale) ──
diag = M.MatriceTransition(CL2, [[5, 0], [0, 7]])
check(diag.taux_immobilite() == Fraction(1), "matrice diagonale : immobilité = 1 exactement")
check(diag.mobilite_ascendante() == Fraction(0), "matrice diagonale : ascendante = 0")
check(diag.mobilite_descendante() == Fraction(0), "matrice diagonale : descendante = 0")
check(leve(diag.odds_ratio, 0, 1), "matrice diagonale : OR indéfini (cellule croisée nulle) -> ValueError")

# ── 3) ANCRE À LA MAIN : [[80,20],[20,80]] ──
m2 = M.MatriceTransition(CL2, [[80, 20], [20, 80]])
check(m2.taux_immobilite() == Fraction(4, 5), "immobilité [[80,20],[20,80]] = 160/200 = 0.8")
check(m2.odds_ratio(0, 1) == Fraction(16), "OR [[80,20],[20,80]] = (80·80)/(20·20) = 16 (à la main)")
check(m2.mobilite_ascendante() == Fraction(1, 10), "ascendante = 20/200 = 1/10")
check(m2.mobilite_descendante() == Fraction(1, 10), "descendante = 20/200 = 1/10")
check(m2.matrice_ligne()[0] == (Fraction(4, 5), Fraction(1, 5)), "P(·|origine 0) = (4/5, 1/5)")
check(m2.odds_ratio(0, 1) == m2.odds_ratio(1, 0), "OR symétrique : OR(0,1) = OR(1,0)")

# ── 4) ANCRE À LA MAIN : 3×3 [[50,30,20],[20,50,30],[10,30,60]] (total 300) ──
m3 = M.MatriceTransition(CL3, [[50, 30, 20], [20, 50, 30], [10, 30, 60]])
check(m3.taux_immobilite() == Fraction(8, 15), "immobilité 3×3 = 160/300 = 8/15 (à la main)")
check(m3.mobilite_ascendante() == Fraction(4, 15), "ascendante 3×3 = 80/300 = 4/15 (à la main)")
check(m3.mobilite_descendante() == Fraction(1, 5), "descendante 3×3 = 60/300 = 1/5 (à la main)")
check(m3.taux_immobilite() + m3.mobilite_ascendante() + m3.mobilite_descendante() == 1,
      "identité structurelle : immobilité + ascendante + descendante = 1")
check(m3.odds_ratio(0, 1) == Fraction(25, 6), "OR(0,1) 3×3 = 2500/600 = 25/6 (à la main)")
check(m3.odds_ratio(1, 2) == Fraction(10, 3), "OR(1,2) 3×3 = 3000/900 = 10/3 (à la main)")
check(m3.odds_ratio(0, 2) == Fraction(15), "OR(0,2) 3×3 = 3000/200 = 15 (à la main)")

# ── 5) POINT THÉORIQUE : OR invariant aux marges, taux brut NON ──
base = M.MatriceTransition(CL2, [[70, 30], [20, 80]])
ligne_x2 = M.MatriceTransition(CL2, [[140, 60], [20, 80]])      # ligne 0 doublée
col_x3 = M.MatriceTransition(CL2, [[70, 90], [20, 240]])        # colonne 1 triplée
check(base.odds_ratio(0, 1) == Fraction(28, 3), "OR base = 5600/600 = 28/3 (à la main)")
check(ligne_x2.odds_ratio(0, 1) == Fraction(28, 3), "OR INVARIANT après doublement d'une ligne")
check(col_x3.odds_ratio(0, 1) == Fraction(28, 3), "OR INVARIANT après triplement d'une colonne")
check(base.taux_immobilite() == Fraction(3, 4), "immobilité base = 150/200 = 3/4 (à la main)")
check(ligne_x2.taux_immobilite() == Fraction(11, 15),
      "immobilité APRÈS doublement = 220/300 = 11/15 ≠ 3/4 (le taux brut dépend des marges)")

# ── 6) ÉLASTICITÉ INTERGÉNÉRATIONNELLE (ancres construites, vérifiables à la main) ──
parents = [1.0, 4.0, 16.0, 64.0]
check(proche(M.elasticite_intergenerationnelle(parents, [1.0, 2.0, 4.0, 8.0]), 0.5),
      "y_e = y_p^0.5 -> pente log-log = 0.5 (à 1e-9)")
check(proche(M.elasticite_intergenerationnelle(parents, [3.0, 12.0, 48.0, 192.0]), 1.0),
      "y_e = 3·y_p -> pente 1 (reproduction totale)")
check(proche(M.elasticite_intergenerationnelle(parents, [5.0, 5.0, 5.0, 5.0]), 0.0),
      "y_e constant -> pente 0 (mobilité parfaite)")
check(proche(M.elasticite_intergenerationnelle(parents, [1.0, 0.25, 0.0625, 0.015625]), -1.0),
      "y_e = 1/y_p -> pente −1")
# 2 points : parents (1, e) -> logs (0, 1) ; enfants (2, 2·e^0.4) -> logs (ln2, ln2+0.4) ; pente = 0.4
check(proche(M.elasticite_intergenerationnelle([1.0, math.e], [2.0, 2.0 * math.e ** 0.4]), 0.4),
      "2 points construits -> pente 0.4 (à la main)")
# entiers acceptés comme revenus (réels > 0)
check(proche(M.elasticite_intergenerationnelle([1, 4, 16, 64], [1, 2, 4, 8]), 0.5),
      "revenus entiers acceptés, pente 0.5")

# ── 7) CORRÉLATION des log-revenus ──
check(proche(M.correlation_log_revenus(parents, [1.0, 2.0, 4.0, 8.0]), 1.0),
      "relation log-linéaire parfaite croissante -> r = 1")
check(proche(M.correlation_log_revenus(parents, [1.0, 0.25, 0.0625, 0.015625]), -1.0),
      "relation log-linéaire parfaite décroissante -> r = −1")
check(-1.0 <= M.correlation_log_revenus([1.0, 2.0, 3.0], [5.0, 4.0, 9.0]) <= 1.0,
      "corrélation bornée dans [−1, 1] (Cauchy-Schwarz)")

# ── 8) SOUNDNESS — construction de la table ──
check(leve(M.MatriceTransition, CL2, [[1, 2], [3, 4], [5, 6]]), "3 lignes pour 2 classes -> ValueError")
check(leve(M.MatriceTransition, CL2, [[1, 2, 3], [4, 5, 6]]), "lignes de longueur 3 pour 2 classes -> ValueError")
check(leve(M.MatriceTransition, CL2, [[1, 2], [3]]), "matrice en escalier (ligne courte) -> ValueError")
check(leve(M.MatriceTransition, CL2, [[1, -2], [3, 4]]), "effectif négatif -> ValueError")
check(leve(M.MatriceTransition, CL2, [[1.0, 2], [3, 4]]), "effectif flottant -> ValueError")
check(leve(M.MatriceTransition, CL2, [[True, 2], [3, 4]]), "effectif bool -> ValueError")
check(leve(M.MatriceTransition, CL2, [["1", 2], [3, 4]]), "effectif str -> ValueError")
check(leve(M.MatriceTransition, CL2, [[0, 0], [3, 4]]), "ligne entièrement nulle -> ValueError")
check(leve(M.MatriceTransition, ["a", "a"], [[1, 2], [3, 4]]), "classes dupliquées -> ValueError")
check(leve(M.MatriceTransition, ["a"], [[5]]), "une seule classe -> ValueError")
check(leve(M.MatriceTransition, [1, 2], [[1, 2], [3, 4]]), "étiquettes non-str -> ValueError")
check(leve(M.MatriceTransition, CL2, "pas une matrice"), "effectifs non-séquence -> ValueError")

# ── 9) SOUNDNESS — odds_ratio ──
check(leve(m2.odds_ratio, 0, 0), "OR(i,i) -> ValueError (classes distinctes exigées)")
check(leve(m2.odds_ratio, 0, 5), "indice hors bornes -> ValueError")
check(leve(m2.odds_ratio, -1, 1), "indice négatif -> ValueError")
check(leve(m2.odds_ratio, True, 1), "indice bool -> ValueError")
check(leve(m2.odds_ratio, 0.0, 1), "indice flottant -> ValueError")
m_zero = M.MatriceTransition(CL2, [[10, 0], [5, 5]])
check(leve(m_zero.odds_ratio, 0, 1), "cellule croisée nulle -> OR indéfini -> ValueError")

# ── 10) SOUNDNESS — élasticité / corrélation ──
check(leve(M.elasticite_intergenerationnelle, [1.0, 2.0], [1.0, 2.0, 3.0]), "tailles différentes -> ValueError")
check(leve(M.elasticite_intergenerationnelle, [1.0], [2.0]), "une seule paire -> ValueError")
check(leve(M.elasticite_intergenerationnelle, [1.0, 0.0], [2.0, 3.0]), "revenu = 0 -> ValueError (log)")
check(leve(M.elasticite_intergenerationnelle, [1.0, -5.0], [2.0, 3.0]), "revenu < 0 -> ValueError")
check(leve(M.elasticite_intergenerationnelle, [1.0, True], [2.0, 3.0]), "revenu bool -> ValueError")
check(leve(M.elasticite_intergenerationnelle, [1.0, "2"], [2.0, 3.0]), "revenu str -> ValueError")
check(leve(M.elasticite_intergenerationnelle, [1.0, float("nan")], [2.0, 3.0]), "revenu NaN -> ValueError")
check(leve(M.elasticite_intergenerationnelle, [1.0, float("inf")], [2.0, 3.0]), "revenu inf -> ValueError")
check(leve(M.elasticite_intergenerationnelle, [4.0, 4.0, 4.0], [1.0, 2.0, 3.0]),
      "variance nulle des parents -> pente indéfinie -> ValueError")
check(leve(M.elasticite_intergenerationnelle, 7, [1.0, 2.0]), "parents non-liste -> ValueError")
check(leve(M.correlation_log_revenus, [1.0, 2.0, 4.0], [5.0, 5.0, 5.0]),
      "variance nulle des enfants -> corrélation indéfinie -> ValueError")
check(leve(M.correlation_log_revenus, [3.0, 3.0], [1.0, 2.0]),
      "variance nulle des parents -> corrélation indéfinie -> ValueError")
# NB : pente 0 est DÉFINIE (enfants constants), corrélation NON — asymétrie voulue
check(proche(M.elasticite_intergenerationnelle([1.0, 2.0, 4.0], [5.0, 5.0, 5.0]), 0.0)
      and leve(M.correlation_log_revenus, [1.0, 2.0, 4.0], [5.0, 5.0, 5.0]),
      "enfants constants : pente 0 définie MAIS corrélation abstenue")

# ── 11) DÉTERMINISME ──
check(m3.taux_immobilite() == m3.taux_immobilite(), "déterminisme taux_immobilite")
check(m3.odds_ratio(0, 2) == m3.odds_ratio(0, 2), "déterminisme odds_ratio")
check(m3.matrice_ligne() == m3.matrice_ligne(), "déterminisme matrice_ligne")
check(M.elasticite_intergenerationnelle(parents, [1.0, 2.0, 4.0, 8.0])
      == M.elasticite_intergenerationnelle(parents, [1.0, 2.0, 4.0, 8.0]), "déterminisme élasticité")

# ── 12) EXACTITUDE des types (Fraction pour la table, float approché pour l'IGE) ──
check(isinstance(m3.taux_immobilite(), Fraction), "taux_immobilite rend une Fraction exacte")
check(isinstance(m3.odds_ratio(0, 1), Fraction), "odds_ratio rend une Fraction exacte")
check(isinstance(M.elasticite_intergenerationnelle(parents, [1.0, 2.0, 4.0, 8.0]), float),
      "élasticité rend un float (approché, 10 chiffres significatifs)")

print(f"\n=== valide_mobilite_sociale : {ok}/{ok+ko} ===")
import sys; sys.exit(0 if ko == 0 else 1)
