"""
VALIDE probabilites_elementaires.py — held-out ADVERSE.

ANCRES NON CIRCULAIRES (valeurs connues INDÉPENDAMMENT de la formule testée, écrites EN DUR) :
  • Dé équilibré {1..6} : P(pair) = 1/2 (issues {2,4,6}) ; P(>4) = 1/3 (issues {5,6}) — comptés à la main.
  • Deux dés : P(somme = 7) = 6/36 = 1/6 (les 6 couples (1,6)(2,5)(3,4)(4,3)(5,2)(6,1) comptés à la main).
  • Binomiale(10,1/2) : E = 5, Var = 5/2 (formules np et np(1−p) posées à la main).
  • Bernoulli(1/3) : E = 1/3, Var = 2/9.
  • Géométrique(1/4) : E = 4, Var = 12 (E = 1/p, Var = (1−p)/p²) ; E[X²] = 28, E[X³] = 292 (Stirling à la main).
  • Uniforme {1..6} : E = 7/2, Var = 35/12 (forme classique (n²−1)/12 = 35/12).
  • Faux positif médical (ancre de Bayes / taux de base) : sensibilité 0.99, spécificité 0.99, prévalence 1/1000
      P(malade|test+) = 0.99·0.001 / (0.99·0.001 + 0.01·0.999) = 99/1098 = 11/122 ≈ 0.0902
      (un module qui rendrait ≈ 0,99 serait FAUX : c'est le piège du taux de base).
  • INVARIANT Var = E[X²] − E[X]² sur 20 jeux de paramètres (exact, en Fraction).

SOUNDNESS : p hors [0,1], flottant pour loi exacte, n<0/non entier, P(B)=0, poids≠1, ordre<0, bool/str/NaN/inf,
mauvaise arité -> ValueError.
"""
from fractions import Fraction as F

import probabilites_elementaires as P

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
    return x is not None and abs(float(x) - float(attendu)) <= tol


# ══ 1) MODÈLE FINI : dé équilibré ═══════════════════════════════════════════════════════════════════════════════
de = P.Modele((1, 2, 3, 4, 5, 6))
check(P.probabilite(de, {2, 4, 6}) == F(1, 2), "dé P(pair) = 1/2 (ensemble)")
check(P.probabilite(de, lambda x: x % 2 == 0) == F(1, 2), "dé P(pair) = 1/2 (prédicat)")
check(P.probabilite(de, {5, 6}) == F(1, 3), "dé P(>4) = 1/3 (ensemble)")
check(P.probabilite(de, lambda x: x > 4) == F(1, 3), "dé P(>4) = 1/3 (prédicat)")
check(P.probabilite(de, set()) == F(0), "dé P(∅) = 0")
check(P.probabilite(de, {1, 2, 3, 4, 5, 6}) == F(1), "dé P(Ω) = 1")

# Deux dés : P(somme = 7) = 6/36 = 1/6 (compté à la main)
deux = P.Modele(tuple((i, j) for i in range(1, 7) for j in range(1, 7)))
check(P.probabilite(deux, lambda c: c[0] + c[1] == 7) == F(1, 6), "deux dés P(somme=7) = 6/36 = 1/6")
check(P.probabilite(deux, lambda c: c[0] + c[1] == 2) == F(1, 36), "deux dés P(somme=2) = 1/36")
check(P.probabilite(deux, lambda c: c[0] + c[1] == 12) == F(1, 36), "deux dés P(somme=12) = 1/36")

# Modèle à poids explicites (dé pipé), Σ = 1 exact
pipe = P.Modele((1, 2), (F(1, 3), F(2, 3)))
check(P.probabilite(pipe, {2}) == F(2, 3), "dé pipé P(2) = 2/3")

# ══ 2) AXIOMES ET RÈGLES ════════════════════════════════════════════════════════════════════════════════════════
# union : A=pair {2,4,6} (1/2), B=>3 {4,5,6} (1/2), A∩B={4,6} (1/3) -> P(A∪B)=1/2+1/2-1/3=2/3 (à la main)
check(P.union(F(1, 2), F(1, 2), F(1, 3)) == F(2, 3), "union 1/2+1/2-1/3 = 2/3")
# union disjoints : 1/6+1/6-0 = 1/3
check(P.union(F(1, 6), F(1, 6), F(0)) == F(1, 3), "union disjoints 1/6+1/6 = 1/3")
# conditionnelle : P(pair | >3) = P({4,6})/P({4,5,6}) = (1/3)/(1/2) = 2/3 (à la main)
check(P.conditionnelle(F(1, 3), F(1, 2)) == F(2, 3), "P(pair|>3) = (1/3)/(1/2) = 2/3")
# indépendance : deux dés, 1er pair (1/2) ⊥ 2e pair (1/2), inter = 9/36 = 1/4 == 1/2·1/2
check(P.independants(F(1, 2), F(1, 2), F(1, 4)) is True, "indépendants 1/4 == 1/2·1/2")
check(P.independants(F(1, 2), F(1, 2), F(1, 3)) is False, "dépendants 1/3 ≠ 1/4")
# probabilités totales : urne — P(rouge) via deux boîtes équiprobables (1/2·1/2 + 1/2·1/4 = 3/8) à la main
check(P.probabilite_totale(((F(1, 2), F(1, 2)), (F(1, 2), F(1, 4)))) == F(3, 8),
      "probas totales 1/2·1/2 + 1/2·1/4 = 3/8")

# ══ 3) BAYES — faux positif médical (piège du taux de base) ═════════════════════════════════════════════════════
sens = F(99, 100)      # sensibilité 0.99 = P(test+|malade)
spec = F(99, 100)      # spécificité 0.99 -> P(test+|sain) = 1 - spec = 1/100
prev = F(1, 1000)      # prévalence 1/1000 = P(malade)
p_test = P.probabilite_totale(((prev, sens), (1 - prev, 1 - spec)))   # P(test+) = 1098/100000
check(p_test == F(1098, 100000), "P(test+) = 0.99·0.001 + 0.01·0.999 = 1098/100000")
p_malade_pos = P.bayes(sens, prev, p_test)
check(p_malade_pos == F(99, 1098), "Bayes P(malade|test+) = 99/1098 (EXACT)")
check(p_malade_pos == F(11, 122), "Bayes P(malade|test+) = 11/122 (forme réduite)")
check(proche(p_malade_pos, 0.09016393, tol=1e-6), "Bayes ≈ 0.0902 (PAS 0.99 : taux de base)")
check(p_malade_pos < F(1, 10), "Bayes < 0.1 : le faux positif domine (anti-piège)")

# ══ 4) LOIS — Bernoulli(1/3) ════════════════════════════════════════════════════════════════════════════════════
be = P.bernoulli(F(1, 3))
check(P.esperance(be) == F(1, 3), "Bernoulli(1/3) E = 1/3")
check(P.variance(be) == F(2, 9), "Bernoulli(1/3) Var = 2/9")
check(P.moment(be, 1) == F(1, 3), "Bernoulli moment(1) = p")
check(P.moment(be, 3) == F(1, 3), "Bernoulli moment(3) = p (x^k = x sur {0,1})")
check(P.moment(be, 0) == F(1), "Bernoulli moment(0) = 1 (convention)")

# ══ 5) LOIS — Binomiale(10,1/2) ═════════════════════════════════════════════════════════════════════════════════
bi = P.binomiale(10, F(1, 2))
check(P.esperance(bi) == F(5), "Binomiale(10,1/2) E = np = 5")
check(P.variance(bi) == F(5, 2), "Binomiale(10,1/2) Var = np(1-p) = 5/2")
# 3e moment centré binomial = np(1-p)(1-2p) ; p=1/2 -> 0 (symétrique)
check(P.moment_centre(bi, 3) == F(0), "Binomiale(10,1/2) 3e moment centré = 0 (symétrique)")
# p=1/3 : np(1-p)(1-2p) = 10/3·2/3·1/3 = 20/27 (à la main)
bi2 = P.binomiale(10, F(1, 3))
check(P.moment_centre(bi2, 3) == F(20, 27), "Binomiale(10,1/3) 3e moment centré = 20/27")
check(P.esperance(bi2) == F(10, 3), "Binomiale(10,1/3) E = 10/3")

# ══ 6) LOIS — Géométrique(1/4) ══════════════════════════════════════════════════════════════════════════════════
ge = P.geometrique(F(1, 4))
check(P.esperance(ge) == F(4), "Géométrique(1/4) E = 1/p = 4")
check(P.variance(ge) == F(12), "Géométrique(1/4) Var = (1-p)/p² = 12")
check(P.moment(ge, 2) == F(28), "Géométrique(1/4) E[X²] = 28 (Stirling à la main)")
check(P.moment(ge, 3) == F(292), "Géométrique(1/4) E[X³] = 292 (Stirling à la main)")
# géométrique déterministe p=1 : X=1 p.s., E=1, Var=0
g1 = P.geometrique(F(1))
check(P.esperance(g1) == F(1) and P.variance(g1) == F(0), "Géométrique(1) E=1, Var=0")

# ══ 7) LOIS — Uniforme {1..6} ═══════════════════════════════════════════════════════════════════════════════════
un = P.uniforme_intervalle(1, 6)
check(P.esperance(un) == F(7, 2), "Uniforme{1..6} E = 7/2")
check(P.variance(un) == F(35, 12), "Uniforme{1..6} Var = (n²-1)/12 = 35/12")
check(P.moment(un, 2) == F(91, 6), "Uniforme{1..6} E[X²] = 91/6")
# uniforme sur valeurs arbitraires {0,2,4,6} : E = 3, E[X²]=(0+4+16+36)/4=14, Var=14-9=5 (à la main)
un2 = P.uniforme((0, 2, 4, 6))
check(P.esperance(un2) == F(3) and P.variance(un2) == F(5), "Uniforme{0,2,4,6} E=3, Var=5")

# ══ 8) LOIS — Poisson(λ) : moments EXACTS, masse ponctuelle APPROCHÉE ═══════════════════════════════════════════
po = P.poisson(F(3))
check(P.esperance(po) == F(3), "Poisson(3) E = λ = 3 (exact)")
check(P.variance(po) == F(3), "Poisson(3) Var = λ = 3 (exact)")
check(P.moment(po, 2) == F(12), "Poisson(3) E[X²] = λ²+λ = 12 (Touchard, exact)")
po2 = P.poisson(F(5, 2))
check(P.variance(po2) == F(5, 2), "Poisson(5/2) Var = λ = 5/2 (exact)")
# masse ponctuelle P(X=0) = e^{-3} ≈ 0.04978707 (APPROCHÉ, ancre = table)
check(proche(P.proba_poisson(F(3), 0), 0.04978707, tol=1e-6), "Poisson(3) P(X=0) = e^-3 ≈ 0.0498 (approché)")
check(isinstance(P.proba_poisson(F(3), 0), float), "proba_poisson renvoie un flottant (approché)")

# ══ 9) ÉCART-TYPE (approché) ════════════════════════════════════════════════════════════════════════════════════
check(proche(P.ecart_type(bi), 1.58113883, tol=1e-7), "σ Binomiale(10,1/2) = √(5/2) ≈ 1.5811")
check(proche(P.ecart_type(ge), 3.46410161, tol=1e-7), "σ Géométrique(1/4) = √12 ≈ 3.4641")
check(isinstance(P.ecart_type(bi), float), "ecart_type renvoie un flottant (approché)")

# ══ 10) INVARIANT Var = E[X²] − E[X]² sur 20 jeux de paramètres (EXACT) ═════════════════════════════════════════
lois_20 = [
    P.bernoulli(F(1, 3)), P.bernoulli(F(1, 2)), P.bernoulli(F(1, 4)), P.bernoulli(F(2, 5)), P.bernoulli(F(1, 10)),
    P.binomiale(10, F(1, 2)), P.binomiale(5, F(1, 3)), P.binomiale(8, F(1, 4)), P.binomiale(3, F(2, 3)),
    P.binomiale(12, F(1, 6)),
    P.geometrique(F(1, 4)), P.geometrique(F(1, 2)), P.geometrique(F(1, 3)), P.geometrique(F(2, 5)),
    P.geometrique(F(1, 10)),
    P.uniforme_intervalle(1, 6), P.uniforme_intervalle(1, 10), P.uniforme((0, 2, 4, 6)),
    P.uniforme_intervalle(1, 3), P.uniforme_intervalle(2, 8),
]
check(len(lois_20) == 20, "20 jeux de paramètres")
for idx, loi in enumerate(lois_20):
    v = P.variance(loi)
    v2 = P.moment(loi, 2) - P.moment(loi, 1) ** 2
    check(v == v2, f"[{idx}] Var == E[X²]-E[X]² ({loi.famille})")
    check(isinstance(v, F), f"[{idx}] Var exacte (Fraction)")
# Poisson aussi (exact)
check(P.variance(po) == P.moment(po, 2) - P.moment(po, 1) ** 2, "Poisson Var == E[X²]-E[X]²")

# ══ 11) SOUNDNESS — probabilités hors [0,1] / flottants pour l'exact ════════════════════════════════════════════
check(leve(P.bernoulli, F(3, 2)), "Bernoulli p>1 -> ValueError")
check(leve(P.bernoulli, F(-1, 2)), "Bernoulli p<0 -> ValueError")
check(leve(P.bernoulli, 0.5), "Bernoulli flottant -> ValueError (loi exacte)")
check(leve(P.binomiale, 10, 0.5), "Binomiale p flottant -> ValueError")
check(leve(P.geometrique, 0.25), "Géométrique flottant -> ValueError")
check(leve(P.geometrique, F(0)), "Géométrique p=0 -> ValueError (E=1/p indéfini)")
check(leve(P.geometrique, F(5, 4)), "Géométrique p>1 -> ValueError")

# ══ 12) SOUNDNESS — n / ordre k ════════════════════════════════════════════════════════════════════════════════
check(leve(P.binomiale, -1, F(1, 2)), "Binomiale n<0 -> ValueError")
check(leve(P.binomiale, F(5, 2), F(1, 2)), "Binomiale n non entier -> ValueError")
check(leve(P.binomiale, 10.0, F(1, 2)), "Binomiale n flottant -> ValueError")
check(leve(P.moment, bi, -1), "moment ordre<0 -> ValueError")
check(leve(P.moment, bi, 2.0), "moment ordre flottant -> ValueError")
check(P.moment(bi, 0) == F(1), "moment ordre 0 = 1 (convention)")
check(P.moment_centre(bi, 0) == F(1), "moment centré ordre 0 = 1 (convention)")

# ══ 13) SOUNDNESS — conditionnelle / Bayes P(B)=0 ══════════════════════════════════════════════════════════════
check(leve(P.conditionnelle, F(0), F(0)), "conditionnelle P(B)=0 -> ValueError")
check(leve(P.bayes, F(1, 2), F(1, 2), F(0)), "Bayes P(B)=0 -> ValueError")
check(leve(P.conditionnelle, F(1, 2), F(1, 4)), "conditionnelle P(A∩B)>P(B) -> ValueError")
check(leve(P.union, F(1, 2), F(1, 2), F(3, 4)), "union P(A∩B)>min -> ValueError")
check(leve(P.bayes, 0.5, F(1, 2), F(1, 2)), "Bayes flottant -> ValueError")

# ══ 14) SOUNDNESS — Modèle (poids, univers) ════════════════════════════════════════════════════════════════════
check(leve(P.Modele, (1, 2, 3), (F(1, 2), F(1, 2), F(1, 2))), "poids Σ≠1 -> ValueError")
check(leve(P.Modele, (1, 2, 3), (F(1, 2), F(1, 2))), "poids longueur ≠ univers -> ValueError")
check(leve(P.Modele, ()), "univers vide -> ValueError")
check(leve(P.Modele, (1, 1, 2)), "univers avec doublon -> ValueError")
check(leve(P.probabilite, de, {7}), "événement hors univers -> ValueError")
check(leve(P.probabilite, de, 42), "événement ni prédicat ni ensemble -> ValueError")
check(leve(P.probabilite, de, lambda x: x), "prédicat non booléen -> ValueError")

# ══ 15) SOUNDNESS — types (bool / str / NaN / inf / arité) ══════════════════════════════════════════════════════
check(leve(P.bernoulli, True), "Bernoulli bool -> ValueError (True n'est pas 1)")
check(leve(P.binomiale, True, F(1, 2)), "Binomiale n bool -> ValueError")
check(leve(P.bernoulli, "1/2"), "Bernoulli str -> ValueError")
check(leve(P.bernoulli, float("nan")), "Bernoulli NaN -> ValueError")
check(leve(P.bernoulli, float("inf")), "Bernoulli inf -> ValueError")
check(leve(P.poisson, F(0)), "Poisson λ=0 -> ValueError")
check(leve(P.poisson, F(-1)), "Poisson λ<0 -> ValueError")
check(leve(P.esperance, "pas une loi"), "esperance sur non-loi -> ValueError")
check(leve(P.probabilite_totale, ((F(1, 2), F(1, 2)),)), "partition Σ P(B_i)≠1 -> ValueError")
check(leve(P.probabilite_totale, ()), "partition vide -> ValueError")

# ══ 16) DÉTERMINISME ═══════════════════════════════════════════════════════════════════════════════════════════
check(P.variance(ge) == P.variance(ge), "déterminisme variance")
check(P.moment(ge, 3) == P.moment(ge, 3), "déterminisme moment")
check(P.bayes(sens, prev, p_test) == P.bayes(sens, prev, p_test), "déterminisme Bayes")
check(P.probabilite(deux, lambda c: c[0] + c[1] == 7)
      == P.probabilite(deux, lambda c: c[0] + c[1] == 7), "déterminisme probabilite")

print(f"\n=== valide_probabilites_elementaires : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
