"""
THÉORIE DES JEUX APPLIQUÉE — équilibres de jeux classiques en stratégies PURES (bimatrice m×n, focus 2×2).

Un jeu bimatriciel est donné par deux matrices de gains de même forme :
    gains_J1[i][j] = utilité du joueur 1 (joueur-LIGNE) quand il joue la ligne i et le joueur 2 la colonne j ;
    gains_J2[i][j] = utilité du joueur 2 (joueur-COLONNE) dans le même profil (i, j).
Plus le gain est ÉLEVÉ, mieux c'est (utilités, pas des coûts).

ÉQUILIBRE DE NASH PUR : un profil (i, j) tel qu'aucun joueur n'a intérêt à dévier UNILATÉRALEMENT —
    la ligne i est une meilleure réponse à la colonne j :  gains_J1[i][j] ≥ gains_J1[k][j]  pour toute ligne k ;
    la colonne j est une meilleure réponse à la ligne i :  gains_J2[i][j] ≥ gains_J2[i][l]  pour toute colonne l.
(Inégalités LARGES : un profil avec ex æquo de meilleure réponse est bien un équilibre de Nash pur — définition
standard.) Le calcul est EXACT et déterministe : on énumère les profils et on vérifie la condition de non-déviation.

STRATÉGIE DOMINANTE : pour la matrice de gains PROPRE d'un joueur (lignes = ses propres actions, colonnes = actions
adverses), une action a domine STRICTEMENT si elle donne un gain strictement supérieur à toute autre action quelle que
soit l'action adverse ; FAIBLEMENT si ≥ partout et > au moins une fois.

CAS DE RÉFÉRENCE (ancres) :
  • Dilemme du prisonnier (T>R>P>S) : (trahir, trahir) est l'UNIQUE équilibre de Nash pur, c'est l'équilibre en
    stratégies strictement dominantes, et il est Pareto-DOMINÉ par (coopérer, coopérer).
  • Bataille des sexes : 2 équilibres de Nash purs (les deux profils de coordination).
  • Matching pennies (somme nulle) : 0 équilibre de Nash pur.

SOUNDNESS : toute matrice mal formée (vide, non rectangulaire, formes incompatibles, entrée non numérique) lève
ValueError — on n'invente jamais de réponse. Pur Python, fonctions pures déterministes.
"""
from __future__ import annotations

COOPERER, TRAHIR = 0, 1  # conventions d'indices pour le dilemme du prisonnier


def _est_nombre(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _valide_matrice(g, nom="matrice"):
    """Valide qu'une matrice est une liste rectangulaire NON vide de nombres ; renvoie (m, n). Sinon ValueError."""
    if not isinstance(g, (list, tuple)) or len(g) == 0:
        raise ValueError(f"{nom} vide ou de type invalide")
    if not all(isinstance(r, (list, tuple)) for r in g):
        raise ValueError(f"{nom} : lignes de type invalide")
    n = len(g[0])
    if n == 0:
        raise ValueError(f"{nom} : lignes vides")
    if any(len(r) != n for r in g):
        raise ValueError(f"{nom} non rectangulaire")
    if any(not _est_nombre(x) for r in g for x in r):
        raise ValueError(f"{nom} : entrée non numérique")
    return len(g), n


def _valide_bimatrice(gains_J1, gains_J2):
    """Valide les deux matrices et l'égalité des formes ; renvoie (m, n). Sinon ValueError."""
    m1, n1 = _valide_matrice(gains_J1, "gains_J1")
    m2, n2 = _valide_matrice(gains_J2, "gains_J2")
    if (m1, n1) != (m2, n2):
        raise ValueError("gains_J1 et gains_J2 ont des formes différentes")
    return m1, n1


def meilleure_reponse_J1(gains_J1, j):
    """Lignes meilleures réponses du joueur 1 à la colonne j (argmax sur la colonne j de gains_J1)."""
    m, n = _valide_matrice(gains_J1, "gains_J1")
    if not (0 <= j < n):
        raise ValueError("colonne j hors bornes")
    meilleur = max(gains_J1[i][j] for i in range(m))
    return [i for i in range(m) if gains_J1[i][j] == meilleur]


def meilleure_reponse_J2(gains_J2, i):
    """Colonnes meilleures réponses du joueur 2 à la ligne i (argmax sur la ligne i de gains_J2)."""
    m, n = _valide_matrice(gains_J2, "gains_J2")
    if not (0 <= i < m):
        raise ValueError("ligne i hors bornes")
    meilleur = max(gains_J2[i][j] for j in range(n))
    return [j for j in range(n) if gains_J2[i][j] == meilleur]


def equilibre_nash_pur(gains_J1, gains_J2):
    """Liste TRIÉE des équilibres de Nash en stratégies pures (i, j) de la bimatrice (gains_J1, gains_J2).

    (i, j) est un équilibre ssi la ligne i maximise gains_J1[·][j] ET la colonne j maximise gains_J2[i][·].
    Matrices mal formées -> ValueError.
    """
    m, n = _valide_bimatrice(gains_J1, gains_J2)
    eqs = []
    for j in range(n):
        max1 = max(gains_J1[k][j] for k in range(m))
        for i in range(m):
            if gains_J1[i][j] != max1:
                continue  # le joueur 1 dévierait
            max2 = max(gains_J2[i][l] for l in range(n))
            if gains_J2[i][j] == max2:  # le joueur 2 ne dévie pas non plus
                eqs.append((i, j))
    return sorted(eqs)


def strategie_dominante(gains, stricte=True):
    """Indice de l'action dominante dans la matrice de gains PROPRE d'un joueur (lignes = ses actions,
    colonnes = actions adverses), ou None s'il n'y en a pas.

    stricte=True  : a > toute autre action pour CHAQUE action adverse ;
    stricte=False : a ≥ toute autre action partout, et > au moins une fois (dominance faible).
    Matrice mal formée -> ValueError.
    """
    m, n = _valide_matrice(gains, "gains")
    for a in range(m):
        domine = True
        au_moins_un_strict = False
        for b in range(m):
            if b == a:
                continue
            for opp in range(n):
                if gains[a][opp] > gains[b][opp]:
                    au_moins_un_strict = True
                elif gains[a][opp] == gains[b][opp]:
                    if stricte:
                        domine = False
                        break
                else:  # gains[a][opp] < gains[b][opp]
                    domine = False
                    break
            if not domine:
                break
        if domine and (stricte or au_moins_un_strict):
            return a
    return None


def pareto_domine(gains_J1, gains_J2, profil_a, profil_b):
    """True si profil_a Pareto-domine profil_b : gain ≥ pour LES DEUX joueurs et > pour au moins un.

    profil = (ligne, colonne). Matrices/profils invalides -> ValueError.
    """
    m, n = _valide_bimatrice(gains_J1, gains_J2)
    for (i, j) in (profil_a, profil_b):
        if not (0 <= i < m and 0 <= j < n):
            raise ValueError("profil hors bornes")
    ia, ja = profil_a
    ib, jb = profil_b
    u1a, u2a = gains_J1[ia][ja], gains_J2[ia][ja]
    u1b, u2b = gains_J1[ib][jb], gains_J2[ib][jb]
    return (u1a >= u1b and u2a >= u2b) and (u1a > u1b or u2a > u2b)


def dilemme_prisonnier():
    """Le dilemme du prisonnier (conventions COOPERER=0, TRAHIR=1, utilités T=5>R=3>P=1>S=0).

    Renvoie un dict décrivant : l'équilibre de Nash UNIQUE (trahir, trahir), les stratégies strictement dominantes
    (trahir pour chaque joueur) et le profil (coopérer, coopérer) qui Pareto-DOMINE l'équilibre.
    """
    # gains_J1[i][j] : i = action du J1 (ligne), j = action du J2 (colonne)
    gains_J1 = [[3, 0],   # J1 coopère : (C,C)=R=3 ; (C,D)=S=0
                [5, 1]]   # J1 trahit  : (D,C)=T=5 ; (D,D)=P=1
    gains_J2 = [[3, 5],   # symétrique pour J2 (colonne)
                [0, 1]]
    eqs = equilibre_nash_pur(gains_J1, gains_J2)
    dom_J1 = strategie_dominante(gains_J1, stricte=True)               # propre à J1 (lignes = actions J1)
    propre_J2 = [list(col) for col in zip(*gains_J2)]                  # transposée : lignes = actions J2
    dom_J2 = strategie_dominante(propre_J2, stricte=True)
    equilibre = eqs[0]
    profil_cooperation = (COOPERER, COOPERER)
    return {
        "actions": ("cooperer", "trahir"),
        "gains_J1": gains_J1,
        "gains_J2": gains_J2,
        "equilibres_nash": eqs,                                        # [(1, 1)]
        "equilibre": equilibre,                                        # (TRAHIR, TRAHIR) = (1, 1)
        "strategie_dominante_J1": dom_J1,                              # TRAHIR = 1
        "strategie_dominante_J2": dom_J2,                              # TRAHIR = 1
        "profil_pareto_superieur": profil_cooperation,                # (COOPERER, COOPERER) = (0, 0)
        "equilibre_pareto_domine": pareto_domine(
            gains_J1, gains_J2, profil_cooperation, equilibre),        # True
        "gain_equilibre": (gains_J1[1][1], gains_J2[1][1]),            # (1, 1)
        "gain_cooperation": (gains_J1[0][0], gains_J2[0][0]),          # (3, 3)
    }


def bataille_des_sexes():
    """La bataille des sexes (jeu de coordination) : 2 équilibres de Nash purs (les deux profils coordonnés)."""
    gains_J1 = [[2, 0],
                [0, 1]]
    gains_J2 = [[1, 0],
                [0, 2]]
    return {"gains_J1": gains_J1, "gains_J2": gains_J2,
            "equilibres_nash": equilibre_nash_pur(gains_J1, gains_J2)}  # [(0, 0), (1, 1)]


def matching_pennies():
    """Matching pennies (jeu à somme nulle) : AUCUN équilibre de Nash pur (équilibre seulement en mixte)."""
    gains_J1 = [[1, -1],
                [-1, 1]]
    gains_J2 = [[-1, 1],
                [1, -1]]
    return {"gains_J1": gains_J1, "gains_J2": gains_J2,
            "equilibres_nash": equilibre_nash_pur(gains_J1, gains_J2)}  # []


if __name__ == "__main__":
    print("=== THÉORIE DES JEUX APPLIQUÉE — équilibres purs ===\n")
    dp = dilemme_prisonnier()
    print(f"  Dilemme du prisonnier : équilibres Nash purs = {dp['equilibres_nash']} "
          f"(unique = trahir,trahir) ; dominante J1/J2 = {dp['strategie_dominante_J1']}/"
          f"{dp['strategie_dominante_J2']} ; équilibre Pareto-dominé par (C,C) = {dp['equilibre_pareto_domine']}")
    print(f"   gains : équilibre {dp['gain_equilibre']} vs coopération {dp['gain_cooperation']}")
    bs = bataille_des_sexes()
    print(f"\n  Bataille des sexes : équilibres Nash purs = {bs['equilibres_nash']} ({len(bs['equilibres_nash'])})")
    mp = matching_pennies()
    print(f"  Matching pennies   : équilibres Nash purs = {mp['equilibres_nash']} ({len(mp['equilibres_nash'])})")
