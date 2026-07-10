"""
VALIDE ajustement_causal.py — held-out ADVERSE.

ANCRES NON CIRCULAIRES (valeurs connues INDÉPENDAMMENT de la formule testée) :
  • CAS D'ÉCOLE DES CALCULS RÉNAUX (Charig et al., BMJ 1986). Les 8 nombres sont écrits EN DUR :
        A : 81/87 (petits), 192/263 (gros) ; total 273/350 = 78 %.
        B : 234/270 (petits), 55/80 (gros) ; total 289/350 = 83 %.
    PARADOXE vérifié : B gagne en AGRÉGÉ (289/350 > 273/350) mais A gagne DANS CHAQUE STRATE
    (81/87 > 234/270 ET 192/263 > 55/80). L'ajustement sur la taille (confondeur) rétablit A.
    L'effet ajusté est recalculé par un SECOND chemin (arithmétique Fraction à la main dans la gate),
    jamais par la fonction testée.
  • INDÉPENDANCE : sur un DAG X→Y sans confondeur, l'effet ajusté avec Z=∅ égale l'association brute.
  • COLLIDER / M-BIAS : conditionner un collider OUVRE une porte dérobée (Z alors INADMISSIBLE) ;
    ajuster sur un DESCENDANT de X -> ValueError explicite.

SOUNDNESS : DAG cyclique, strate nulle, descendant dans Z, Z inadmissible, bool/str/NaN/float, arité -> ValueError.
"""
from fractions import Fraction

import causalite
import simpson
import ajustement_causal as AC

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


def leve_msg(fn, *a, fragment="", **k):
    """True ssi fn lève ValueError DONT le message contient `fragment`."""
    try:
        fn(*a, **k)
        return False
    except ValueError as e:
        return fragment in str(e)


def rows_charig():
    """Reconstruit les 700 observations depuis les 8 comptes EN DUR (Charig 1986)."""
    counts = [("A", "petit", 81, 87), ("A", "gros", 192, 263),
              ("B", "petit", 234, 270), ("B", "gros", 55, 80)]
    rows = []
    for x, z, s, t in counts:
        rows += [{"X": x, "Z": z, "Y": 1} for _ in range(s)]
        rows += [{"X": x, "Z": z, "Y": 0} for _ in range(t - s)]
    return rows


# ── DAG confondeur de Charig : taille(Z) → traitement(X), taille(Z) → succès(Y), X → Y ──
dag = causalite.GrapheCausal()
dag.ajoute_cause("Z", "X")
dag.ajoute_cause("Z", "Y")
dag.ajoute_cause("X", "Y")
rows = rows_charig()

# ── 1) LE PARADOXE (ancre EN DUR, arithmétique indépendante) ──
brut_A = Fraction(273, 350)         # 81+192 / 87+263
brut_B = Fraction(289, 350)         # 234+55 / 270+80
check(brut_B > brut_A, "AGRÉGÉ : B (289/350) > A (273/350)")
check(Fraction(81, 87) > Fraction(234, 270), "STRATE petits : A (81/87) > B (234/270)")
check(Fraction(192, 263) > Fraction(55, 80), "STRATE gros : A (192/263) > B (55/80)")

# ── 2) EFFET AJUSTÉ = SECOND chemin de code (hand-Fraction) vs module ──
P_petit = Fraction(87 + 270, 700)   # #(Z=petit)/N = 357/700
P_gros = Fraction(263 + 80, 700)    # 343/700
adjA_attendu = Fraction(81, 87) * P_petit + Fraction(192, 263) * P_gros
adjB_attendu = Fraction(234, 270) * P_petit + Fraction(55, 80) * P_gros
adjA = AC.effet_causal_backdoor(dag, rows, "X", "Y", {"Z"}, "A", 1)
adjB = AC.effet_causal_backdoor(dag, rows, "X", "Y", {"Z"}, "B", 1)
check(adjA == adjA_attendu, f"P(succès|do(A)) exact = {adjA_attendu}")
check(adjB == adjB_attendu, f"P(succès|do(B)) exact = {adjB_attendu}")
check(adjA > adjB, "RENVERSEMENT rétabli : effet ajusté A > B (A est causalement meilleur)")
check(adjA_attendu > adjB_attendu, "cohérence : le second chemin confirme A > B ajusté")
# valeurs exactes en dur (calcul manuel indépendant)
check(adjA == Fraction(27, 29) * Fraction(357, 700) + Fraction(192, 263) * Fraction(343, 700),
      "P(succès|do(A)) = 27/29·357/700 + 192/263·343/700")

# ── 3) P(échec|do(x)) = 1 − P(succès|do(x)) (cohérence des probabilités) ──
echecA = AC.effet_causal_backdoor(dag, rows, "X", "Y", {"Z"}, "A", 0)
check(echecA == 1 - adjA, "P(échec|do(A)) = 1 − P(succès|do(A))")

# ── 4) EFFET MOYEN (ATE) via espérance = adjA − adjB (Y binaire 0/1) ──
ate = AC.effet_moyen_traitement(dag, rows, "X", "Y", {"Z"}, "A", "B")
check(ate == adjA - adjB, "ATE(A vs B) = E[Y|do(A)] − E[Y|do(B)] = adjA − adjB")
check(ate > 0, "ATE(A vs B) > 0 : A augmente causalement le succès")
check(AC.esperance_do(dag, rows, "X", "Y", {"Z"}, "A") == adjA, "E[Y|do(A)] = P(succès|do(A)) (Y binaire)")

# ── 5) SIMPSON + AJUSTEMENT : détecte le renversement PUIS nomme le causal ──
res = AC.simpson_et_ajustement(dag, rows, "X", "Y", {"Z"}, "A", "B", 1)
check(res["renversement"] is True, "simpson_et_ajustement : renversement DÉTECTÉ")
check(res["simpson"] == simpson.SIMPSON, "diagnostic = SIMPSON")
check(res["gagnant_brut"] == "B", "gagnant BRUT (agrégé) = B")
check(res["gagnant_ajuste"] == "A" and res["causal"] == "A", "gagnant AJUSTÉ / CAUSAL = A")
check(res["ajuste"]["A"] == adjA_attendu and res["brut"]["B"] == brut_B, "valeurs brut/ajusté exactes")

# ── 6) ENSEMBLES D'AJUSTEMENT (Charig) : seul {Z} est admissible ──
ens = AC.ensembles_ajustement(dag, "X", "Y")
check(frozenset({"Z"}) in ens, "ensembles_ajustement : {Z} admissible")
check(frozenset() not in ens, "ensembles_ajustement : ∅ NON admissible (porte dérobée ouverte)")
check(len(ens) == 1, "ensembles_ajustement Charig : exactement 1 ensemble valide")
check(AC.critere_backdoor(dag, "X", "Y", {"Z"}) is True, "critère backdoor {Z} = True")
check(AC.critere_backdoor(dag, "X", "Y", set()) is False, "critère backdoor ∅ = False (confusion ouverte)")

# ── 7) INDÉPENDANCE : DAG X→Y sans confondeur, Z=∅ -> ajusté = association brute ──
g_ind = causalite.GrapheCausal()
g_ind.ajoute_cause("X", "Y")
rows_ind = ([{"X": 1, "Y": 1}] * 3 + [{"X": 1, "Y": 0}] * 1    # P(Y=1|X=1)=3/4
            + [{"X": 0, "Y": 1}] * 1 + [{"X": 0, "Y": 0}] * 3)  # P(Y=1|X=0)=1/4
check(AC.critere_backdoor(g_ind, "X", "Y", set()) is True, "X→Y : ∅ admissible (aucune porte dérobée)")
check(AC.effet_causal_backdoor(g_ind, rows_ind, "X", "Y", set(), 1, 1) == Fraction(3, 4),
      "sans confondeur : P(Y=1|do(X=1))=3/4 = association brute")
check(AC.effet_causal_backdoor(g_ind, rows_ind, "X", "Y", set(), 0, 1) == Fraction(1, 4),
      "sans confondeur : P(Y=1|do(X=0))=1/4 = association brute")
check(AC.effet_moyen_traitement(g_ind, rows_ind, "X", "Y", set(), 1, 0) == Fraction(1, 2),
      "sans confondeur : ATE = 3/4 − 1/4 = 1/2")

# ── 8) M-BIAS : conditionner un COLLIDER ouvre une porte dérobée ──
#     U1→X, U1→M, U2→M, U2→Y, X→Y : backdoor X←U1→M←U2→Y (collider M)
g_m = causalite.GrapheCausal()
g_m.ajoute_cause("U1", "X")
g_m.ajoute_cause("U1", "M")
g_m.ajoute_cause("U2", "M")
g_m.ajoute_cause("U2", "Y")
g_m.ajoute_cause("X", "Y")
check(AC.critere_backdoor(g_m, "X", "Y", set()) is True, "M-bias : ∅ admissible (collider fermé bloque)")
check(AC.critere_backdoor(g_m, "X", "Y", {"M"}) is False, "M-bias : {M} INADMISSIBLE (collider ouvert)")
check(AC.critere_backdoor(g_m, "X", "Y", {"U1"}) is True, "M-bias : {U1} admissible (fourche bloque)")
check(AC.critere_backdoor(g_m, "X", "Y", {"U2"}) is True, "M-bias : {U2} admissible (fourche bloque)")
ens_m = AC.ensembles_ajustement(g_m, "X", "Y")
check(frozenset() in ens_m, "M-bias : ∅ ∈ ensembles d'ajustement")
check(frozenset({"M"}) not in ens_m, "M-bias : {M} ∉ ensembles d'ajustement")

# ── 9) COLLIDER / DESCENDANT DE X dans Z -> ValueError EXPLICITE ──
g_desc = causalite.GrapheCausal()
g_desc.ajoute_cause("X", "Y")
g_desc.ajoute_cause("X", "W")          # W = descendant de X
rows_desc = ([{"X": 1, "Y": 1, "W": 1}] * 2 + [{"X": 0, "Y": 0, "W": 0}] * 2)
check(AC.critere_backdoor(g_desc, "X", "Y", {"W"}) is False, "descendant W dans Z -> critère False")
check(leve_msg(AC.effet_causal_backdoor, g_desc, rows_desc, "X", "Y", {"W"}, 1, 1,
               fragment="descendant"), "ajuster sur descendant W -> ValueError explicite")

# ── 10) Z INADMISSIBLE (Charig sans ajuster) -> message d'honnêteté capital ──
check(leve_msg(AC.effet_causal_backdoor, dag, rows, "X", "Y", set(), "A", 1,
               fragment="n'est pas l'effet causal"),
      "Z=∅ confondu -> ValueError « ... n'est pas l'effet causal »")

# ── 11) STRATE D'EFFECTIF NUL -> ValueError ──
rows_nul = ([{"X": "A", "Z": "petit", "Y": 1}] * 5          # A seulement en 'petit'
            + [{"X": "B", "Z": "petit", "Y": 1}] * 3
            + [{"X": "B", "Z": "gros", "Y": 0}] * 4)         # 'gros' existe (via B) mais pas pour A
check(leve_msg(AC.effet_causal_backdoor, dag, rows_nul, "X", "Y", {"Z"}, "A", 1,
               fragment="effectif nul"), "strate (A,gros) vide -> ValueError effectif nul")

# ── 12) DAG CYCLIQUE -> ValueError ──
g_cyc = causalite.GrapheCausal()
g_cyc.ajoute_cause("A", "B")
g_cyc._effets.setdefault("B", set()).add("A")   # force un cycle en contournant la garde
g_cyc._causes.setdefault("A", set()).add("B")
check(leve_msg(AC.critere_backdoor, g_cyc, "A", "B", set(), fragment="cyclique"),
      "DAG cyclique -> ValueError")
check(leve(AC.ensembles_ajustement, g_cyc, "A", "B"), "DAG cyclique (ensembles) -> ValueError")

# ── 13) SOUNDNESS : types invalides, arité, nœuds inconnus ──
check(leve(AC.effet_causal_backdoor, dag, rows, "X", "Y", {"Z"}, True, 1), "valeur_traitement bool -> ValueError")
check(leve(AC.effet_causal_backdoor, dag, rows, "X", "Y", {"Z"}, "A", float("nan")), "valeur_resultat NaN -> ValueError")
check(leve(AC.effet_causal_backdoor, dag, rows, "X", "Y", "Z", "A", 1), "ensemble_Z str -> ValueError")
check(leve(AC.effet_causal_backdoor, dag, rows, "X", "Y", {"Z"}, 1.5, 1), "valeur float -> ValueError")
check(leve(AC.effet_causal_backdoor, dag, [], "X", "Y", set(), "A", 1), "donnees vide -> ValueError")
check(leve(AC.effet_causal_backdoor, dag, rows, "X", "X", {"Z"}, "A", 1), "traitement==resultat -> ValueError")
check(leve(AC.effet_causal_backdoor, dag, rows, "X", "INCONNU", {"Z"}, "A", 1), "resultat hors DAG -> ValueError")
check(leve(AC.critere_backdoor, dag, "X", "Y", {"INCONNU"}), "Z hors DAG -> ValueError")
check(leve(AC.effet_causal_backdoor, "pas_un_dag", rows, "X", "Y", set(), "A", 1), "dag invalide -> ValueError")
# donnée booléenne dans une ligne (True n'est pas 1)
rows_bool = [{"X": 1, "Y": True}, {"X": 0, "Y": 1}]
check(leve(AC.effet_causal_backdoor, g_ind, rows_bool, "X", "Y", set(), 1, 1), "valeur Y bool dans données -> ValueError")
# esperance_do exige Y entier
rows_str = [{"X": 1, "Y": "oui"}, {"X": 0, "Y": "non"}]
check(leve(AC.esperance_do, g_ind, rows_str, "X", "Y", set(), 1), "esperance_do Y non entier -> ValueError")
# simpson_et_ajustement : Z doit être UNE variable
check(leve(AC.simpson_et_ajustement, dag, rows, "X", "Y", {"Z", "X"}, "A", "B", 1), "simpson : |Z|≠1 -> ValueError")
check(leve(AC.effet_moyen_traitement, dag, rows, "X", "Y", {"Z"}, "A", "A"), "ATE traité==contrôle -> ValueError")

# ── 14) |V| > 10 -> ValueError (borne exhaustive) ──
g_big = causalite.GrapheCausal()
for i in range(11):
    g_big.ajoute_cause(f"n{i}", "cible")
check(leve(AC.ensembles_ajustement, g_big, "n0", "cible"), "|V|>10 -> ValueError (énumération bornée)")

# ── 15) DÉTERMINISME ──
check(AC.effet_causal_backdoor(dag, rows, "X", "Y", {"Z"}, "A", 1)
      == AC.effet_causal_backdoor(dag, rows, "X", "Y", {"Z"}, "A", 1), "déterminisme effet ajusté")
check(AC.ensembles_ajustement(dag, "X", "Y") == AC.ensembles_ajustement(dag, "X", "Y"), "déterminisme ensembles")
check(AC.critere_backdoor(g_m, "X", "Y", {"M"}) == AC.critere_backdoor(g_m, "X", "Y", {"M"}), "déterminisme critère")

print(f"\n=== valide_ajustement_causal : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
