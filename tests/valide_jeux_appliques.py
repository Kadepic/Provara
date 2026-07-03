"""
VALIDE jeux_appliques.py — held-out ADVERSE.

Ancres : les TROIS jeux classiques vérifiés par leurs propriétés CONNUES et indépendantes (dilemme du prisonnier =
1 équilibre pur dominant Pareto-dominé ; bataille des sexes = 2 ; matching pennies = 0). SOUNDNESS : matrices mal
formées -> ValueError. CROISEMENT INDÉPENDANT : un brute-force « aucune déviation profitable » recodé ici (chemin de
code différent) doit coïncider avec equilibre_nash_pur sur des jeux aléatoires déterministes. DÉTERMINISME : deux
appels identiques renvoient la même chose. Aucun de ces cas n'est en dur dans le module.
"""
import random
import jeux_appliques as M

ok = 0
ko = 0


def check(cond, label):
    global ok, ko
    if cond:
        ok += 1
    else:
        ko += 1
        print(f"  FAIL: {label}")


def leve_valueerror(fn, *a, **k):
    try:
        fn(*a, **k)
        return False
    except ValueError:
        return True
    except Exception:
        return False


# Brute-force INDÉPENDANT : (i,j) est Nash ssi aucun joueur ne gagne en déviant unilatéralement.
def nash_brute(g1, g2):
    m, n = len(g1), len(g1[0])
    res = []
    for i in range(m):
        for j in range(n):
            dev1 = any(g1[k][j] > g1[i][j] for k in range(m))   # J1 améliore en changeant de ligne
            dev2 = any(g2[i][l] > g2[i][j] for l in range(n))   # J2 améliore en changeant de colonne
            if not dev1 and not dev2:
                res.append((i, j))
    return sorted(res)


# ─── 1) DILEMME DU PRISONNIER ───
print("=== DILEMME DU PRISONNIER ===")
dp = M.dilemme_prisonnier()
check(dp["equilibres_nash"] == [(1, 1)], "DP : équilibre Nash pur UNIQUE = (trahir,trahir)=(1,1)")
check(dp["equilibre"] == (M.TRAHIR, M.TRAHIR), "DP : équilibre = (TRAHIR,TRAHIR)")
check(dp["strategie_dominante_J1"] == M.TRAHIR, "DP : trahir est strictement dominant pour J1")
check(dp["strategie_dominante_J2"] == M.TRAHIR, "DP : trahir est strictement dominant pour J2")
check(dp["equilibre_pareto_domine"] is True, "DP : équilibre Pareto-DOMINÉ par (coopérer,coopérer)")
check(dp["profil_pareto_superieur"] == (0, 0), "DP : profil Pareto-supérieur = (coopérer,coopérer)")
check(dp["gain_equilibre"] == (1, 1) and dp["gain_cooperation"] == (3, 3),
      "DP : gains équilibre (1,1) < coopération (3,3)")
# l'équilibre coïncide avec le profil des stratégies dominantes
check(dp["equilibre"] == (dp["strategie_dominante_J1"], dp["strategie_dominante_J2"]),
      "DP : équilibre = profil des dominantes")
# cohérence avec le brute-force indépendant
check(M.equilibre_nash_pur(dp["gains_J1"], dp["gains_J2"]) == nash_brute(dp["gains_J1"], dp["gains_J2"]),
      "DP : equilibre_nash_pur == brute-force")

# ─── 2) BATAILLE DES SEXES ───
print("=== BATAILLE DES SEXES ===")
bs = M.bataille_des_sexes()
check(M.equilibre_nash_pur(bs["gains_J1"], bs["gains_J2"]) == [(0, 0), (1, 1)],
      "BS : 2 équilibres purs = {(0,0),(1,1)}")
check(len(bs["equilibres_nash"]) == 2, "BS : exactement 2 équilibres purs")
check(M.equilibre_nash_pur(bs["gains_J1"], bs["gains_J2"]) == nash_brute(bs["gains_J1"], bs["gains_J2"]),
      "BS : equilibre_nash_pur == brute-force")
# pas de stratégie strictement dominante dans la bataille des sexes
check(M.strategie_dominante(bs["gains_J1"], stricte=True) is None, "BS : aucune dominante stricte J1")

# ─── 3) MATCHING PENNIES ───
print("=== MATCHING PENNIES ===")
mp = M.matching_pennies()
check(M.equilibre_nash_pur(mp["gains_J1"], mp["gains_J2"]) == [], "MP : 0 équilibre pur")
check(len(mp["equilibres_nash"]) == 0, "MP : aucun équilibre pur")
check(M.equilibre_nash_pur(mp["gains_J1"], mp["gains_J2"]) == nash_brute(mp["gains_J1"], mp["gains_J2"]),
      "MP : equilibre_nash_pur == brute-force")

# ─── 4) MEILLEURES RÉPONSES & PROFILS PARTICULIERS ───
print("=== MEILLEURES RÉPONSES ===")
g1 = [[3, 0], [5, 1]]
g2 = [[3, 5], [0, 1]]
check(M.meilleure_reponse_J1(g1, 0) == [1], "MR J1 à colonne 0 = ligne 1 (5>3)")
check(M.meilleure_reponse_J1(g1, 1) == [1], "MR J1 à colonne 1 = ligne 1 (1>0)")
check(M.meilleure_reponse_J2(g2, 0) == [1], "MR J2 à ligne 0 = colonne 1 (5>3)")
check(M.meilleure_reponse_J2(g2, 1) == [1], "MR J2 à ligne 1 = colonne 1 (1>0)")
# ex æquo : meilleure réponse multiple
egal = [[2, 2], [1, 0]]
check(M.meilleure_reponse_J1(egal, 0) == [0], "MR : argmax sur colonne 0 = ligne 0")
# coordination pure : (0,0) et (1,1) symétriques
coord1 = [[1, 0], [0, 1]]
coord2 = [[1, 0], [0, 1]]
check(M.equilibre_nash_pur(coord1, coord2) == [(0, 0), (1, 1)], "coordination : 2 équilibres en diagonale")

# ─── 5) STRATÉGIE DOMINANTE (stricte vs faible) ───
print("=== STRATÉGIE DOMINANTE ===")
# ligne 1 strictement dominante (5>3, 1>0)
check(M.strategie_dominante([[3, 0], [5, 1]], stricte=True) == 1, "ligne 1 strictement dominante")
check(M.strategie_dominante([[5, 1], [3, 0]], stricte=True) == 0, "ligne 0 strictement dominante")
# dominance FAIBLE (≥ partout, > au moins une fois) mais PAS stricte
faible = [[2, 1], [2, 0]]   # ligne 0 : 2≥2 et 1>0
check(M.strategie_dominante(faible, stricte=False) == 0, "ligne 0 faiblement dominante")
check(M.strategie_dominante(faible, stricte=True) is None, "pas de dominante STRICTE (ex æquo en colonne 0)")
# aucune dominance (cyclique)
check(M.strategie_dominante([[1, 0], [0, 1]], stricte=True) is None, "aucune dominante stricte")
check(M.strategie_dominante([[1, 0], [0, 1]], stricte=False) is None, "aucune dominante faible")
# lignes identiques : aucune dominance faible
check(M.strategie_dominante([[1, 1], [1, 1]], stricte=False) is None, "lignes égales -> aucune dominante")

# ─── 6) PARETO ───
print("=== PARETO ===")
check(M.pareto_domine(g1, g2, (0, 0), (1, 1)) is True, "(C,C) Pareto-domine (D,D)")
check(M.pareto_domine(g1, g2, (1, 1), (0, 0)) is False, "(D,D) ne Pareto-domine pas (C,C)")
check(M.pareto_domine(g1, g2, (0, 0), (0, 0)) is False, "un profil ne se Pareto-domine pas lui-même")
# amélioration d'un seul joueur suffit
check(M.pareto_domine([[2, 0], [1, 0]], [[1, 0], [1, 0]], (0, 0), (1, 0)) is True,
      "amélioration d'un seul joueur (à gain égal pour l'autre) = Pareto-domination")

# ─── 7) CROISEMENT ALÉATOIRE INDÉPENDANT (equilibre_nash_pur == brute-force) ───
print("=== CROISEMENT ALÉATOIRE ===")
rng = random.Random(12345)
accord = 0
for _ in range(2000):
    m = rng.choice([2, 2, 3])
    n = rng.choice([2, 2, 3])
    A = [[rng.randint(-3, 3) for _ in range(n)] for _ in range(m)]
    B = [[rng.randint(-3, 3) for _ in range(n)] for _ in range(m)]
    if M.equilibre_nash_pur(A, B) == nash_brute(A, B):
        accord += 1
check(accord == 2000, f"2000 jeux aléatoires : equilibre_nash_pur == brute-force ({accord}/2000)")

# propriété : un jeu avec deux stratégies STRICTEMENT dominantes a un équilibre pur UNIQUE = leur profil
dom_accord = 0
for _ in range(500):
    # construit un J1 où la ligne 1 domine strictement et un J2 où la colonne 1 domine strictement
    base = rng.randint(0, 3)
    A = [[base, base], [base + 1 + rng.randint(0, 2), base + 1 + rng.randint(0, 2)]]
    Bt = [[base, base], [base + 1 + rng.randint(0, 2), base + 1 + rng.randint(0, 2)]]  # propre à J2
    B = [list(col) for col in zip(*Bt)]  # gains_J2 dans le repère (ligne J1, colonne J2)
    eqs = M.equilibre_nash_pur(A, B)
    if eqs == [(1, 1)] and M.strategie_dominante(A, True) == 1 and M.strategie_dominante(Bt, True) == 1:
        dom_accord += 1
check(dom_accord == 500, f"jeux à dominantes strictes : équilibre unique = profil dominant ({dom_accord}/500)")

# ─── 8) DÉTERMINISME ───
print("=== DÉTERMINISME ===")
check(M.equilibre_nash_pur(g1, g2) == M.equilibre_nash_pur(g1, g2), "equilibre_nash_pur déterministe")
check(M.dilemme_prisonnier() == M.dilemme_prisonnier(), "dilemme_prisonnier déterministe")
check(M.strategie_dominante(g1, True) == M.strategie_dominante(g1, True), "strategie_dominante déterministe")

# ─── 9) SOUNDNESS — matrices mal formées -> ValueError ───
print("=== SOUNDNESS ===")
check(leve_valueerror(M.equilibre_nash_pur, [], []), "bimatrice vide -> ValueError")
check(leve_valueerror(M.equilibre_nash_pur, [[1, 2], [3]], [[1, 2], [3, 4]]), "matrice non rectangulaire -> ValueError")
check(leve_valueerror(M.equilibre_nash_pur, [[1, 2]], [[1, 2], [3, 4]]), "formes incompatibles -> ValueError")
check(leve_valueerror(M.equilibre_nash_pur, [[1, "x"], [3, 4]], [[1, 2], [3, 4]]), "entrée non numérique -> ValueError")
check(leve_valueerror(M.equilibre_nash_pur, [[1, True], [3, 4]], [[1, 2], [3, 4]]), "booléen rejeté -> ValueError")
check(leve_valueerror(M.equilibre_nash_pur, [[]], [[]]), "lignes vides -> ValueError")
check(leve_valueerror(M.equilibre_nash_pur, "pasunematrice", [[1]]), "type invalide -> ValueError")
check(leve_valueerror(M.strategie_dominante, [[1, 2], [3]]), "strategie_dominante non rect. -> ValueError")
check(leve_valueerror(M.meilleure_reponse_J1, g1, 9), "meilleure_reponse_J1 colonne hors bornes -> ValueError")
check(leve_valueerror(M.meilleure_reponse_J2, g2, 9), "meilleure_reponse_J2 ligne hors bornes -> ValueError")
check(leve_valueerror(M.pareto_domine, g1, g2, (5, 5), (0, 0)), "pareto_domine profil hors bornes -> ValueError")
# un cas BIEN formé ne lève pas
try:
    # jeu d'anti-coordination : équilibres purs hors diagonale (0,1) et (1,0)
    _r = M.equilibre_nash_pur([[0, 1], [1, 0]], [[0, 1], [1, 0]])
    check(_r == [(0, 1), (1, 0)], "bimatrice valide -> pas d'erreur, résultat correct")
except Exception:
    check(False, "bimatrice valide -> pas d'erreur")

print(f"\n=== valide_jeux_appliques : {ok}/{ok+ko} ===")
import sys
sys.exit(0 if ko == 0 else 1)
