"""
VALIDE elasticite_prix.py — held-out ADVERSE.

ANCRES EXTERNES NON CIRCULAIRES (calculées À LA MAIN ci-dessous, PAS par la formule testée) :
  • p 10->12, q 100->80 (formule des arcs, à la main) :
        Δq/moy_q = −20/90 = −2/9 ≈ −0.2222 ;  Δp/moy_p = 2/11 ≈ 0.18182 ;
        e = (−2/9)/(2/11) = −11/9 = −1.2222… -> ÉLASTIQUE.
  • SYMÉTRIE (ancre forte) : elasticite_arc(10,100,12,80) == elasticite_arc(12,80,10,100) EXACTEMENT —
    la formule des arcs est symétrique ; la formule NAÏVE des pourcentages simples ne l'est PAS
    (avant: (−20/100)/(2/10) = −1.0 ; arrière: (20/80)/(−2/12) = −1.5 — calcul à la main dans la gate,
    SECOND chemin de code : un module qui utiliserait la naïve échouerait ces tests).
  • p 4->6, q 60->40 : (−20/50)/(2/5) = −1 exactement -> UNITAIRE, recette INCHANGÉE (à la main).
  • Ponctuelle sur demande linéaire q = 100 − 2p (à la main) : p=10,q=80 -> e = −2·10/80 = −0.25 ;
    p=25,q=50 -> e = −2·25/50 = −1 (point de recette maximale, fait classique des manuels).
  • Revenu 1000->1200, q 50->60 : (10/55)/(200/1100) = (2/11)/(2/11) = 1 exactement (à la main).
  • Croisée thé/café : prix café 2->3, qté thé 100->120 : (20/110)/(1/2.5) = (2/11)/(2/5) = 5/11
    ≈ 0.4545454545 (à la main) -> SUBSTITUABLE. Essence/voitures : signe négatif -> COMPLÉMENTAIRE.
  • q constant -> e = 0 -> 'parfaitement inélastique'.
  • RECETTE, e > 0 = ABSTENTION (contre-exemples à la main) : arc p 10->12, q 100->150 = +2.2 alors que
    R monte de 1000 à 1800 ('baisse' serait FAUX) ; arc p 10->12, q 100->120 = +1 alors que R monte de
    1000 à 1440 ('inchangée' serait FAUX) -> recette_totale_variation exige e SIGNÉ ≤ 0, ValueError sinon.

SOUNDNESS : p≤0, q≤0, p1==p2, r1==r2, pB1==pB2, e>0 (recette), bool, str, NaN, ±inf -> ValueError.
DÉTERMINISME : ×2.
"""
import math

import elasticite_prix as E

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


def proche(x, attendu, tol=1e-8):
    return x is not None and abs(x - attendu) <= tol


# ── 1) ANCRE IMPOSÉE : p 10->12, q 100->80 -> e = −11/9 = −1.2222… (calcul à la main en tête de gate) ──
e_arc = E.elasticite_arc(10, 100, 12, 80)
check(proche(e_arc, -1.222222222, tol=1e-8), f"arc(10,100,12,80) = -1.2222… (à la main -11/9), reçu {e_arc}")
check(E.classe(e_arc) == "élastique", "arc -11/9 -> classe 'élastique'")

# ── 2) SYMÉTRIE EXACTE (ancre forte) : la formule des arcs ne dépend pas du sens du parcours ──
check(E.elasticite_arc(10, 100, 12, 80) == E.elasticite_arc(12, 80, 10, 100),
      "symétrie EXACTE arc(10,100,12,80) == arc(12,80,10,100)")
# La formule NAÏVE donnerait −1.0 (aller : (−20/100)/(2/10)) ou −1.5 (retour : (20/80)/(−2/12)) — à la main.
naive_aller = (-20 / 100) / (2 / 10)      # second chemin de code, calculé ici même
naive_retour = (20 / 80) / (-2 / 12)
check(proche(naive_aller, -1.0) and proche(naive_retour, -1.5), "calcul manuel naïf : −1.0 / −1.5 (asymétrique)")
check(abs(e_arc - naive_aller) > 0.1 and abs(e_arc - naive_retour) > 0.1,
      "l'arc n'est PAS la formule naïve (≠ −1.0 et ≠ −1.5)")
# Autre paire, symétrie encore exacte :
check(E.elasticite_arc(4, 60, 6, 40) == E.elasticite_arc(6, 40, 4, 60), "symétrie exacte arc(4,60,6,40)")

# ── 3) ANCRE À LA MAIN : p 4->6, q 60->40 -> (−20/50)/(2/5) = −1 -> unitaire, recette inchangée ──
check(proche(E.elasticite_arc(4, 60, 6, 40), -1.0, tol=0), "arc(4,60,6,40) = -1 exactement (à la main)")
check(E.classe(-1.0) == "unitaire", "classe(-1) = 'unitaire'")
check(E.recette_totale_variation(-1.0) == "inchangée", "|e|=1 -> recette inchangée")

# ── 4) q CONSTANT -> e = 0 -> parfaitement inélastique ──
check(E.elasticite_arc(10, 100, 12, 100) == 0.0, "q constant -> e = 0")
check(E.classe(0.0) == "parfaitement inélastique", "classe(0) = 'parfaitement inélastique'")
check(E.classe(0) == "parfaitement inélastique", "classe(0 entier) = 'parfaitement inélastique'")

# ── 5) ANCRE inélastique : p 10->12, q 100->96 -> (−4/98)/(2/11) = −11/49 ≈ −0.2244897959 (à la main) ──
check(proche(E.elasticite_arc(10, 100, 12, 96), -0.2244897959, tol=1e-9),
      "arc(10,100,12,96) = -11/49 ≈ -0.2244897959 (à la main)")
check(E.classe(-0.2244897959) == "inélastique", "classe(-11/49) = 'inélastique'")

# ── 6) PONCTUELLE sur demande linéaire q = 100 − 2p (pente −2, à la main) ──
check(proche(E.elasticite_ponctuelle(-2, 10, 80), -0.25, tol=0), "ponctuelle(-2,10,80) = -0.25 (à la main)")
check(proche(E.elasticite_ponctuelle(-2, 25, 50), -1.0, tol=0), "ponctuelle(-2,25,50) = -1 (recette max, classique)")
check(proche(E.elasticite_ponctuelle(-2, 40, 20), -4.0, tol=0), "ponctuelle(-2,40,20) = -4 (à la main)")
check(proche(E.elasticite_ponctuelle(2, 5, 10), 1.0, tol=0), "ponctuelle pente positive : 2·5/10 = 1")
check(E.elasticite_ponctuelle(0, 10, 80) == 0.0, "pente nulle -> e = 0")

# ── 7) REVENU : 1000->1200, q 50->60 -> (10/55)/(200/1100) = 1 exactement (à la main) ──
check(proche(E.elasticite_revenu(50, 60, 1000, 1200), 1.0, tol=0), "revenu(50,60,1000,1200) = 1 (à la main)")
# Bien inférieur : q 60->50 quand r 1000->1200 -> même grandeur, signe opposé -> −1 (à la main)
check(proche(E.elasticite_revenu(60, 50, 1000, 1200), -1.0, tol=0), "bien inférieur -> e_revenu = -1")
check(E.elasticite_revenu(50, 60, 1000, 1200) == E.elasticite_revenu(60, 50, 1200, 1000),
      "symétrie exacte de l'arc revenu")

# ── 8) CROISÉE : thé/café (substituables) et essence/voitures (complémentaires) ──
e_the_cafe = E.elasticite_croisee(100, 120, 2, 3)
check(proche(e_the_cafe, 0.4545454545, tol=1e-9), f"croisée thé/café = 5/11 ≈ 0.4545454545 (à la main), reçu {e_the_cafe}")
check(E.relation_biens(e_the_cafe) == "substituable", "croisée > 0 -> 'substituable' (thé/café)")
# Essence 1->2, voitures 100->80 : (−20/90)/(1/1.5) = (−2/9)·(3/2) = −1/3 ≈ −0.3333333333 (à la main)
e_ess = E.elasticite_croisee(100, 80, 1, 2)
check(proche(e_ess, -0.3333333333, tol=1e-9), f"croisée essence/voitures = -1/3 (à la main), reçu {e_ess}")
check(E.relation_biens(e_ess) == "complémentaire", "croisée < 0 -> 'complémentaire'")
check(E.relation_biens(0.0) == "indépendants", "croisée = 0 -> 'indépendants'")
check(E.elasticite_croisee(100, 120, 2, 3) == E.elasticite_croisee(120, 100, 3, 2), "symétrie exacte croisée")

# ── 9) RECETTE TOTALE (fait économique exact : dR/dp = q·(1+e), demande SIGNÉE e ≤ 0 uniquement) ──
check(E.recette_totale_variation(-2.0) == "baisse", "e=-2 (élastique) -> hausse de prix -> recette baisse")
check(E.recette_totale_variation(-0.5) == "hausse", "e=-0.5 (inélastique) -> hausse de prix -> recette monte")
check(E.recette_totale_variation(0) == "hausse", "e=0 (parfaitement inélastique) -> recette monte")
# e > 0 -> ABSTENTION (ValueError), jamais un verdict. Contre-exemple à la main qui l'IMPOSE :
# p 10->12, q 100->150 : arc = (50/125)/(2/11) = (2/5)·(11/2) = +2.2 ; R passe de 10·100=1000 à
# 12·150=1800 -> la recette MONTE alors que |2.2|>1 aurait dit 'baisse'. e>0 est donc ambigu
# (signé positif vs |e| d'une demande) : le module DOIT s'abstenir.
e_pos = E.elasticite_arc(10, 100, 12, 150)
check(proche(e_pos, 2.2, tol=1e-9), f"arc(10,100,12,150) = +2.2 (à la main (50/125)/(2/11)), reçu {e_pos}")
check(10 * 100 < 12 * 150, "R monte 1000 -> 1800 (à la main) : verdict 'baisse' pour e=+2.2 serait FAUX")
check(leve(E.recette_totale_variation, e_pos), "recette(+2.2) -> ValueError (abstention, e>0 ambigu)")
check(leve(E.recette_totale_variation, 2.0), "recette(2.0) -> ValueError (e>0, jamais 'baisse')")
check(leve(E.recette_totale_variation, 0.5), "recette(0.5) -> ValueError (e>0, jamais 'hausse')")
check(leve(E.recette_totale_variation, 1.0), "recette(1.0) -> ValueError (e>0, jamais 'inchangée')")
check(leve(E.recette_totale_variation, 1e-9), "recette(1e-9) -> ValueError (tout e>0 refusé)")
# Second contre-exemple à la main : p 10->12, q 100->120 -> arc = (20/110)/(2/11) = +1 exactement ;
# R passe de 1000 à 12·120=1440 (+44%) -> 'inchangée' pour e=+1 serait FAUX. Abstention prouvée ci-dessus.
check(proche(E.elasticite_arc(10, 100, 12, 120), 1.0, tol=0), "arc(10,100,12,120) = +1 exactement (à la main)")
check(10 * 100 < 12 * 120, "R monte 1000 -> 1440 (à la main) : 'inchangée' pour e=+1 serait FAUX")
check(E.recette_totale_variation(-1.0) == "inchangée", "e=-1 (unitaire, signé) -> inchangée")
# Vérification NUMÉRIQUE indépendante (second chemin) : demande q = 100 − 2p.
# p=40 (e=−4, élastique) : R(40)=40·20=800 ; R(41)=41·18=738 -> BAISSE (à la main).
check(40 * 20 > 41 * 18 and E.recette_totale_variation(-4.0) == "baisse",
      "R(40)=800 > R(41)=738 confirme 'baisse' pour e=-4")
# p=10 (e=−0.25, inélastique) : R(10)=10·80=800 ; R(11)=11·78=858 -> HAUSSE (à la main).
check(10 * 80 < 11 * 78 and E.recette_totale_variation(-0.25) == "hausse",
      "R(10)=800 < R(11)=858 confirme 'hausse' pour e=-0.25")

# ── 10) CLASSES — frontières ──
check(E.classe(-5.0) == "élastique", "classe(-5) élastique")
check(E.classe(1.5) == "élastique", "classe(1.5) élastique")
check(E.classe(-0.99) == "inélastique", "classe(-0.99) inélastique")
check(E.classe(1) == "unitaire", "classe(1 entier) unitaire")

# ── 11) SOUNDNESS — arc : prix/quantités ≤ 0, p1==p2 ──
check(leve(E.elasticite_arc, 0, 100, 12, 80), "p1=0 -> ValueError")
check(leve(E.elasticite_arc, -10, 100, 12, 80), "p1<0 -> ValueError")
check(leve(E.elasticite_arc, 10, 0, 12, 80), "q1=0 -> ValueError")
check(leve(E.elasticite_arc, 10, 100, 12, -80), "q2<0 -> ValueError")
check(leve(E.elasticite_arc, 10, 100, 10, 80), "p1==p2 -> ValueError (élasticité indéfinie)")

# ── 12) SOUNDNESS — arc : types (bool/str/NaN/inf) ──
check(leve(E.elasticite_arc, True, 100, 12, 80), "p1 bool -> ValueError")
check(leve(E.elasticite_arc, 10, 100, 12, True), "q2 bool -> ValueError")
check(leve(E.elasticite_arc, "10", 100, 12, 80), "p1 str -> ValueError")
check(leve(E.elasticite_arc, 10, float("nan"), 12, 80), "q1 NaN -> ValueError")
check(leve(E.elasticite_arc, 10, 100, float("inf"), 80), "p2 inf -> ValueError")
check(leve(E.elasticite_arc, 10, 100, 12, float("-inf")), "q2 -inf -> ValueError")

# ── 13) SOUNDNESS — ponctuelle ──
check(leve(E.elasticite_ponctuelle, -2, 0, 80), "p=0 -> ValueError")
check(leve(E.elasticite_ponctuelle, -2, 10, 0), "q=0 -> ValueError")
check(leve(E.elasticite_ponctuelle, -2, 10, -5), "q<0 -> ValueError")
check(leve(E.elasticite_ponctuelle, float("nan"), 10, 80), "dq_dp NaN -> ValueError")
check(leve(E.elasticite_ponctuelle, float("inf"), 10, 80), "dq_dp inf -> ValueError")
check(leve(E.elasticite_ponctuelle, True, 10, 80), "dq_dp bool -> ValueError")
check(leve(E.elasticite_ponctuelle, -2, "10", 80), "p str -> ValueError")

# ── 14) SOUNDNESS — revenu / croisée ──
check(leve(E.elasticite_revenu, 50, 60, 1000, 1000), "r1==r2 -> ValueError")
check(leve(E.elasticite_revenu, 50, 60, 0, 1200), "r1=0 -> ValueError")
check(leve(E.elasticite_revenu, -50, 60, 1000, 1200), "q1<0 -> ValueError")
check(leve(E.elasticite_revenu, 50, 60, True, 1200), "r1 bool -> ValueError")
check(leve(E.elasticite_croisee, 100, 120, 2, 2), "pB1==pB2 -> ValueError")
check(leve(E.elasticite_croisee, 0, 120, 2, 3), "qA1=0 -> ValueError")
check(leve(E.elasticite_croisee, 100, 120, -2, 3), "pB1<0 -> ValueError")
check(leve(E.elasticite_croisee, 100, float("nan"), 2, 3), "qA2 NaN -> ValueError")
check(leve(E.elasticite_croisee, 100, 120, 2, "3"), "pB2 str -> ValueError")

# ── 15) SOUNDNESS — classe / relation_biens / recette ──
check(leve(E.classe, True), "classe(bool) -> ValueError")
check(leve(E.classe, "1"), "classe(str) -> ValueError")
check(leve(E.classe, float("nan")), "classe(NaN) -> ValueError")
check(leve(E.classe, float("inf")), "classe(inf) -> ValueError")
check(leve(E.relation_biens, True), "relation_biens(bool) -> ValueError")
check(leve(E.relation_biens, float("nan")), "relation_biens(NaN) -> ValueError")
check(leve(E.relation_biens, "0.5"), "relation_biens(str) -> ValueError")
check(leve(E.recette_totale_variation, True), "recette(bool) -> ValueError")
check(leve(E.recette_totale_variation, "2"), "recette(str) -> ValueError")
check(leve(E.recette_totale_variation, float("nan")), "recette(NaN) -> ValueError")
check(leve(E.recette_totale_variation, float("-inf")), "recette(-inf) -> ValueError")

# ── 16) DÉTERMINISME (deux appels identiques -> même valeur) ──
check(E.elasticite_arc(10, 100, 12, 80) == E.elasticite_arc(10, 100, 12, 80), "déterminisme arc")
check(E.elasticite_ponctuelle(-2, 10, 80) == E.elasticite_ponctuelle(-2, 10, 80), "déterminisme ponctuelle")
check(E.elasticite_revenu(50, 60, 1000, 1200) == E.elasticite_revenu(50, 60, 1000, 1200), "déterminisme revenu")
check(E.elasticite_croisee(100, 120, 2, 3) == E.elasticite_croisee(100, 120, 2, 3), "déterminisme croisée")

print(f"\n=== valide_elasticite_prix : {ok}/{ok+ko} ===")
import sys; sys.exit(0 if ko == 0 else 1)
