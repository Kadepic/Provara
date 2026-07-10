"""
VALIDE pyramide_ages.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (valeurs connues ou calculées À LA MAIN ci-dessous, JAMAIS
recalculées par la fonction testée) :
  • Pyramide RECTANGULAIRE parfaite (toutes tranches égales) : par définition les flancs sont
    parallèles -> 'stationnaire', rapport base/milieu = 100+100 / 100+100 = 1.0 EXACTEMENT (à la main).
  • Pyramide TRIANGULAIRE (base 1000 puis 800, 600, 400, 200) : base large, décroissance rapide,
    la forme classique des populations jeunes -> 'expansive' ; rapport à la main = 1000/600 = 1.666666667.
  • Pyramide INVERSÉE (base 200 puis 400, 600, 800) : base plus étroite que le milieu -> 'regressive' ;
    rapport à la main = 200/600 = 0.3333333333.
  • sex_ratio : 500 hommes / 500 femmes -> 100.0 EXACTEMENT (définition H/F×100 ; 500/500×100 = 100) ;
    105 hommes / 100 femmes -> 105.0 (le sex-ratio à la naissance classique ≈ 105 garçons pour 100 filles).
  • age_median d'une population UNIFORME 0-100 par tranches de 10 -> 50.0 (symétrie : la moitié de la
    population est sous 50 ans, valeur connue sans aucune interpolation).
  • age_median d'une tranche unique (0,10) uniforme -> 5.0 (milieu de la tranche, à la main :
    0 + (100/2 − 0)/100 × 10 = 5).
  • taux de dépendance : 200 jeunes + 100 âgés / 700 actifs -> 300/700×100 = 42.85714286 (division
    posée à la main : 300/7 = 42.857142857...).
  • Tranches (0,10) puis (20,30) -> ValueError nommant le TROU entre 10 et 20 ;
    (0,10) puis (5,15) -> ValueError nommant le RECOUVREMENT.
  • effectif_total : sommes d'entiers posées à la main (5×200 = 1000, etc.).
  • part_tranche : rectangulaire 5 tranches égales -> une tranche = 1/5 = 20.0 %, deux = 40.0 % (à la main).

SOUNDNESS : liste vide, bornes inversées, effectif négatif/flottant/bool, bornes NaN/inf/str/bool,
arité de tranche, trou, recouvrement, 0 femme (sex_ratio), bornes non alignées (part_tranche,
taux_dependance), 0 actif, milieu vide, population nulle -> ValueError.
"""
import math

import pyramide_ages as P

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


# ── Populations de référence (construites une fois, réutilisées) ──
# RECTANGULAIRE : 5 tranches de 10 ans, 100 H + 100 F chacune (total à la main : 5×200 = 1000).
RECT = P.Pyramide([(0, 10, 100, 100), (10, 20, 100, 100), (20, 30, 100, 100),
                   (30, 40, 100, 100), (40, 50, 100, 100)])
# TRIANGULAIRE : base 1000 (500 H + 500 F) puis 800, 600, 400, 200 (total à la main : 3000).
TRI = P.Pyramide([(0, 10, 500, 500), (10, 20, 400, 400), (20, 30, 300, 300),
                  (30, 40, 200, 200), (40, 50, 100, 100)])
# INVERSÉE : base 200 puis 400, 600, 800 (total à la main : 2000).
INV = P.Pyramide([(0, 10, 100, 100), (10, 20, 200, 200), (20, 30, 300, 300), (30, 40, 400, 400)])
# UNIFORME 0-100 par tranches de 10 : 50 H + 50 F par tranche (total à la main : 10×100 = 1000).
UNIF = P.Pyramide([(d, d + 10, 50, 50) for d in range(0, 100, 10)])
# DÉPENDANCE : 200 jeunes (0-15), 700 actifs (15-65), 100 âgés (65-100).
DEP = P.Pyramide([(0, 15, 100, 100), (15, 65, 350, 350), (65, 100, 50, 50)])

# ── 1) ANCRE : effectif_total = sommes posées à la main ──
check(RECT.effectif_total() == 1000, "effectif_total rectangulaire = 1000 (5×200 à la main)")
check(TRI.effectif_total() == 3000, "effectif_total triangulaire = 3000 (1000+800+600+400+200)")
check(INV.effectif_total() == 2000, "effectif_total inversée = 2000 (200+400+600+800)")
check(DEP.effectif_total() == 1000, "effectif_total dépendance = 1000 (200+700+100)")

# ── 2) ANCRE : sex_ratio (définition H/F×100) ──
check(P.Pyramide([(0, 100, 500, 500)]).sex_ratio() == 100.0,
      "sex_ratio 500 H / 500 F = 100.0 exactement")
check(P.Pyramide([(0, 1, 105, 100)]).sex_ratio() == 105.0,
      "sex_ratio 105 H / 100 F = 105.0 (sex-ratio à la naissance classique)")
check(P.Pyramide([(0, 1, 50, 100)]).sex_ratio() == 50.0, "sex_ratio 50 H / 100 F = 50.0")
check(RECT.sex_ratio() == 100.0, "sex_ratio rectangulaire (500 H / 500 F) = 100.0")

# ── 3) ANCRE : type_pyramide — verdict + rapport rendu, jamais nu ──
verdict_rect, rapport_rect = RECT.type_pyramide()
check(verdict_rect == "stationnaire", "rectangulaire parfaite -> 'stationnaire'")
check(rapport_rect == 1.0, "rectangulaire : rapport base/milieu = 1.0 exactement (200/200)")

verdict_tri, rapport_tri = TRI.type_pyramide()
check(verdict_tri == "expansive", "triangulaire (1000,800,600,400,200) -> 'expansive'")
check(proche(rapport_tri, 1.666666667, tol=1e-6), "triangulaire : rapport = 1000/600 ≈ 1.666666667")

verdict_inv, rapport_inv = INV.type_pyramide()
check(verdict_inv == "regressive", "inversée (200,400,600,800) -> 'regressive'")
check(proche(rapport_inv, 0.3333333333, tol=1e-6), "inversée : rapport = 200/600 ≈ 0.3333333333")

# Cas frontières du critère explicite (calculés à la main) : 110/100 = 1.1 -> stationnaire (pas >),
# 90/100 = 0.9 -> stationnaire (pas <), 111/100 = 1.11 -> expansive, 89/100 = 0.89 -> regressive.
v, r = P.Pyramide([(0, 10, 110, 0), (10, 20, 100, 0), (20, 30, 100, 0)]).type_pyramide()
check(v == "stationnaire" and proche(r, 1.1), "rapport = 1.1 pile -> stationnaire (seuil strict)")
v, r = P.Pyramide([(0, 10, 90, 0), (10, 20, 100, 0), (20, 30, 100, 0)]).type_pyramide()
check(v == "stationnaire" and proche(r, 0.9), "rapport = 0.9 pile -> stationnaire (seuil strict)")
v, r = P.Pyramide([(0, 10, 111, 0), (10, 20, 100, 0), (20, 30, 100, 0)]).type_pyramide()
check(v == "expansive" and proche(r, 1.11), "rapport = 1.11 -> expansive")
v, r = P.Pyramide([(0, 10, 89, 0), (10, 20, 100, 0), (20, 30, 100, 0)]).type_pyramide()
check(v == "regressive" and proche(r, 0.89), "rapport = 0.89 -> regressive")

# ── 4) ANCRE : age_median ──
check(UNIF.age_median() == 50.0, "âge médian population uniforme 0-100 = 50.0 (symétrie)")
check(P.Pyramide([(0, 10, 50, 50)]).age_median() == 5.0,
      "âge médian tranche unique (0,10) = 5.0 (milieu, à la main)")
# À la main sur TRI (total 3000, moitié 1500) : cumul 1000 après (0,10) ; la 1500e personne est
# dans (10,20) qui compte 800 -> 10 + (1500-1000)/800 × 10 = 10 + 6.25 = 16.25.
check(TRI.age_median() == 16.25, "âge médian triangulaire = 16.25 (interpolation posée à la main)")
# À la main sur INV (total 2000, moitié 1000) : cumul 200+400=600 après (10,20) ; la 1000e est dans
# (20,30) qui compte 600 -> 20 + (1000-600)/600 × 10 = 20 + 6.666... = 26.66666667.
check(proche(INV.age_median(), 26.66666667, tol=1e-6),
      "âge médian inversée = 26.66666667 (interpolation posée à la main)")

# ── 5) ANCRE : taux_dependance (définition ONU) ──
check(proche(DEP.taux_dependance(), 42.85714286, tol=1e-6),
      "taux de dépendance (200+100)/700×100 = 42.85714286 (300/7 posé à la main)")
# 100 jeunes + 100 âgés / 200 actifs = 100.0 exactement (à la main).
DEP2 = P.Pyramide([(0, 15, 50, 50), (15, 65, 100, 100), (65, 90, 50, 50)])
check(DEP2.taux_dependance() == 100.0, "taux de dépendance 200/200×100 = 100.0 exactement")
# Pyramide entièrement active (20-60) : jeunes=0, âgés=0 -> taux = 0.0 (à la main).
check(P.Pyramide([(20, 60, 100, 100)]).taux_dependance() == 0.0,
      "pyramide 20-60 uniquement : taux de dépendance = 0.0")

# ── 6) ANCRE : part_tranche (proportions posées à la main) ──
check(RECT.part_tranche(0, 10) == 20.0, "part 0-10 rectangulaire = 20.0 % (200/1000)")
check(RECT.part_tranche(0, 20) == 40.0, "part 0-20 rectangulaire = 40.0 % (400/1000)")
check(RECT.part_tranche(0, 50) == 100.0, "part 0-50 rectangulaire = 100.0 % (tout)")
check(proche(TRI.part_tranche(0, 10), 33.33333333, tol=1e-6),
      "part 0-10 triangulaire = 1000/3000 ≈ 33.33333333 %")

# ── 7) INVARIANT DUR : contiguïté — trou et recouvrement NOMMÉS ──
check(leve(P.Pyramide, [(0, 10, 1, 1), (20, 30, 1, 1)]), "trou (0,10)+(20,30) -> ValueError")
try:
    P.Pyramide([(0, 10, 1, 1), (20, 30, 1, 1)])
    check(False, "trou : ValueError attendue")
except ValueError as e:
    msg = str(e)
    check("trou" in msg and "10" in msg and "20" in msg,
          "le message du trou NOMME le trou entre 10 et 20")
check(leve(P.Pyramide, [(0, 10, 1, 1), (5, 15, 1, 1)]), "recouvrement (0,10)+(5,15) -> ValueError")
try:
    P.Pyramide([(0, 10, 1, 1), (5, 15, 1, 1)])
    check(False, "recouvrement : ValueError attendue")
except ValueError as e:
    check("recouvrement" in str(e), "le message du recouvrement le NOMME")
check(leve(P.Pyramide, [(10, 20, 1, 1), (0, 10, 1, 1)]),
      "tranches en ordre décroissant -> ValueError (recouvrement/contiguïté violée)")

# ── 8) SOUNDNESS — construction ──
check(leve(P.Pyramide, []), "liste vide -> ValueError")
check(leve(P.Pyramide, "pas une liste"), "str -> ValueError")
check(leve(P.Pyramide, [(10, 0, 1, 1)]), "bornes inversées (10,0) -> ValueError")
check(leve(P.Pyramide, [(-10, 0, 10, 10), (0, 10, 10, 10)]),
      "borne_basse négative (-10) -> ValueError (un âge est ≥ 0 par nature)")
check(leve(P.Pyramide, [(-5, 5, 1, 1)]), "tranche unique à borne négative -> ValueError")
check(leve(P.Pyramide, [(-2, -1, 1, 1)]), "tranche entièrement négative -> ValueError")
check(leve(P.Pyramide, [(5, 5, 1, 1)]), "tranche de largeur nulle -> ValueError")
check(leve(P.Pyramide, [(0, 10, -1, 1)]), "hommes négatif -> ValueError")
check(leve(P.Pyramide, [(0, 10, 1, -1)]), "femmes négatif -> ValueError")
check(leve(P.Pyramide, [(0, 10, 1.5, 1)]), "effectif flottant -> ValueError")
check(leve(P.Pyramide, [(0, 10, True, 1)]), "effectif bool -> ValueError (True n'est pas 1)")
check(leve(P.Pyramide, [(0, 10, "1", 1)]), "effectif str -> ValueError")
check(leve(P.Pyramide, [(float("nan"), 10, 1, 1)]), "borne NaN -> ValueError")
check(leve(P.Pyramide, [(0, float("inf"), 1, 1)]), "borne inf -> ValueError")
check(leve(P.Pyramide, [(True, 10, 1, 1)]), "borne bool -> ValueError")
check(leve(P.Pyramide, [("0", 10, 1, 1)]), "borne str -> ValueError")
check(leve(P.Pyramide, [(0, 10, 1)]), "tranche à 3 éléments -> ValueError (arité)")
check(leve(P.Pyramide, [(0, 10, 1, 1, 1)]), "tranche à 5 éléments -> ValueError (arité)")
check(leve(P.Pyramide, [42]), "tranche non-séquence -> ValueError")

# ── 9) SOUNDNESS — sex_ratio, type, âge médian ──
check(leve(P.Pyramide([(0, 10, 100, 0)]).sex_ratio), "0 femme -> ValueError (pas d'infini)")
check(leve(P.Pyramide([(0, 10, 100, 100), (10, 20, 0, 0), (20, 30, 50, 50)]).type_pyramide),
      "tranche du milieu vide -> ValueError (rapport indéfini)")
check(leve(P.Pyramide([(0, 10, 0, 0)]).age_median), "population nulle -> age_median ValueError")
check(leve(P.Pyramide([(0, 10, 0, 0)]).sex_ratio), "population nulle -> sex_ratio ValueError")

# ── 10) SOUNDNESS — part_tranche (alignement + types) ──
check(leve(RECT.part_tranche, 0, 15), "haut=15 hors frontières -> ValueError (pas de découpe)")
check(leve(RECT.part_tranche, 5, 20), "bas=5 hors frontières -> ValueError")
check(leve(RECT.part_tranche, 20, 10), "bas ≥ haut -> ValueError")
check(leve(RECT.part_tranche, 10, 10), "bas = haut -> ValueError")
check(leve(RECT.part_tranche, float("nan"), 10), "bas NaN -> ValueError")
check(leve(RECT.part_tranche, 0, float("inf")), "haut inf -> ValueError")
check(leve(RECT.part_tranche, True, 10), "bas bool -> ValueError")
check(leve(P.Pyramide([(0, 10, 0, 0)]).part_tranche, 0, 10),
      "population nulle -> part_tranche ValueError")

# ── 11) SOUNDNESS — taux_dependance (coupes 15/65 non alignées, 0 actif) ──
check(leve(P.Pyramide([(0, 20, 100, 100), (20, 65, 100, 100), (65, 90, 10, 10)]).taux_dependance),
      "l'âge 15 coupe la tranche (0,20) -> ValueError (pas d'hypothèse de répartition)")
check(leve(P.Pyramide([(0, 15, 100, 100), (15, 60, 100, 100), (60, 90, 10, 10)]).taux_dependance),
      "l'âge 65 coupe la tranche (60,90) -> ValueError")
check(leve(P.Pyramide([(0, 15, 100, 100), (15, 65, 0, 0), (65, 90, 10, 10)]).taux_dependance),
      "0 actif (15-64) -> ValueError (division par zéro)")

# ── 12) DÉTERMINISME — deux appels, mêmes résultats ──
check(RECT.type_pyramide() == RECT.type_pyramide(), "déterminisme type_pyramide")
check(UNIF.age_median() == UNIF.age_median(), "déterminisme age_median")
check(DEP.taux_dependance() == DEP.taux_dependance(), "déterminisme taux_dependance")
check(RECT.sex_ratio() == RECT.sex_ratio(), "déterminisme sex_ratio")
check(RECT.part_tranche(0, 20) == RECT.part_tranche(0, 20), "déterminisme part_tranche")

print(f"\n=== valide_pyramide_ages : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
